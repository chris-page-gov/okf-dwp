"""Strict observed CLI event recognition for a new, separately frozen experiment."""
import json
import math

from run_staff_model_trials import encoded,sha,sanitise_claude,sanitise_codex

SKILL_WARNING='Skill descriptions were shortened to fit the 2% skills context budget. Codex can still see every skill, but some descriptions are shorter. Disable unused skills or plugins to leave more room for the rest.'
CODEX_EVENTS={'thread.started','turn.started','turn.completed','turn.failed','item.started','item.updated','item.completed','error'}
CLAUDE_EVENTS={'system','assistant','user','result','rate_limit_event'}
THINKING={'type':str,'subtype':str,'session_id':str,'uuid':str,'estimated_tokens':int,'estimated_tokens_delta':int}
RATE={'type':str,'session_id':str,'uuid':str,'rate_limit_info':{'isUsingOverage':bool,'overageResetsAt':int,'overageStatus':str,'rateLimitType':str,'resetsAt':int,'status':str,'unifiedWindows':{'five_hour':{'resetsAt':int,'utilization':'number'},'seven_day':{'resetsAt':int,'utilization':'number'}}}}


def shape_matches(value,schema):
    if isinstance(schema,dict):return isinstance(value,dict) and set(value)==set(schema) and all(shape_matches(value[k],s) for k,s in schema.items())
    if schema=='number':return type(value) in (int,float) and math.isfinite(value) and value>=0
    if type(value) is not schema:return False
    if schema is str:return len(value)<=512
    if schema is int:return value>=0
    return True


def sanitise(provider,raw):
    events=[json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    if not events or any(not isinstance(e,dict) for e in events):raise ValueError('Invalid event-object stream')
    issues=[];warnings=[];telemetry=[];uses={};results=set();result_records=[];models=set()
    allowed=CODEX_EVENTS if provider=='codex-subscription' else CLAUDE_EVENTS
    terminal={'turn.completed','turn.failed'} if provider=='codex-subscription' else {'result'}
    completed=events[-1].get('type') in terminal and sum(e.get('type') in terminal for e in events)==1
    if not completed:issues.append('incomplete-terminal-stream')
    for event in events:
        kind=event.get('type')
        if kind not in allowed:issues.append('unrecognised-event');continue
        if provider=='codex-subscription':
            if kind in {'error','turn.failed'}:issues.append('provider-error-event')
            if kind.startswith('item.'):
                item=event.get('item')
                if not isinstance(item,dict):issues.append('invalid-item');continue
                item_type=item.get('type')
                if item_type=='error':
                    # No prefix/fuzzy match and no arbitrary error text retained.
                    if kind=='item.completed' and set(item)=={'id','type','message'} and isinstance(item['id'],str) and item['message']==SKILL_WARNING:
                        warnings.append({'category':'skill-catalogue-shortening','message':SKILL_WARNING,'boundary':'Host/system skill catalogue remains visible; identical provider system contexts are not established.'})
                    else:issues.append('unknown-error-item')
                elif item_type not in {'agent_message','reasoning'}:issues.append('forbidden-or-unknown-item')
            continue
        if kind=='system':
            if event.get('subtype')=='init':continue
            if event.get('subtype')=='thinking_tokens' and shape_matches(event,THINKING):telemetry.append('validated-thinking-token-counter')
            else:issues.append('unknown-system-shape')
            continue
        if kind=='rate_limit_event':
            if shape_matches(event,RATE):telemetry.append('validated-rate-limit-telemetry')
            else:issues.append('unknown-rate-limit-shape')
            continue
        if kind not in {'assistant','user'}:continue
        message=event.get('message')
        if not isinstance(message,dict) or not isinstance(message.get('content'),list):issues.append('invalid-message-content');continue
        if isinstance(message.get('model'),str):models.add(message['model'])
        for part in message['content']:
            if not isinstance(part,dict):issues.append('invalid-content-block');continue
            typ=part.get('type')
            if typ in {'text','thinking','redacted_thinking'}:continue
            if typ=='tool_use':
                tool_id=part.get('id')
                if kind!='assistant' or part.get('name')!='StructuredOutput' or not isinstance(tool_id,str) or not 1<=len(tool_id)<=256 or tool_id in uses or not isinstance(part.get('input'),dict):
                    issues.append('forbidden-or-reused-tool-use');continue
                uses[tool_id]=sha(encoded(part['input']))
            elif typ=='tool_result':
                tool_id=part.get('tool_use_id');flag=part.get('is_error')
                if kind!='user' or not isinstance(tool_id,str) or tool_id not in uses or tool_id in results or ('is_error' in part and type(flag) is not bool) or flag is True:
                    issues.append('unmatched-duplicate-or-error-tool-result');continue
                results.add(tool_id);result_records.append({'formatter_input_sha256':uses[tool_id],'result_sha256':sha(encoded(part.get('content'))),'error_flag_presence':'explicit-false' if 'is_error' in part else 'absent','single_preceding_formatter_match':True})
            else:issues.append('unknown-content-block')
    if provider=='claude-subscription' and set(uses)!=results:issues.append('formatter-result-missing')
    if provider=='claude-subscription':
        output=sanitise_claude(raw.decode())
        if uses and (output.get('structured_output') is None or sha(encoded(output['structured_output'])) not in {uses[k] for k in results}):
            issues.append('final-output-differs-from-successful-formatter')
        # Every actual tool was enumerated above; no original identifier retained.
        output['response_models']=sorted(models);output['accounting_models']=sorted(output.get('model_usage',{}))
    else:
        if any('item' in e and not isinstance(e['item'],dict) for e in events):raise ValueError('Malformed item event')
        output=sanitise_codex(raw.decode());output['response_models']=output['reported_models'];output['accounting_models']=[]
    output['tool_event_names']=['StructuredOutput']*len(uses) if provider=='claude-subscription' else []
    output['tool_events']=[{'name':'StructuredOutput','input_sha256':digest} for digest in uses.values()]
    output.update(stream_completed=completed,recognition_issues=sorted(set(issues)),recognised_warnings=warnings,recognised_telemetry=telemetry,formatter_results=result_records,
        tool_event_census_status='retained-validated-completed-stream' if not issues else 'unknown-or-rejected-stream',
        model_identity_boundary='Reported identities only; no inferred identity or controlled single-model claim.')
    return output
