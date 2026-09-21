"""Strict direct-answer event recogniser. Never imports a historical trial parser."""
import hashlib
import json
import math
import re

MAX_STDOUT = 2 * 1024 * 1024
MAX_ANSWER = 16 * 1024
MAX_NUMBER = 2 ** 53 - 1
SKILL_WARNING = ('Skill descriptions were shortened to fit the 2% skills context budget. '
    'Codex can still see every skill, but some descriptions are shorter. Disable unused skills '
    'or plugins to leave more room for the rest.')
THINKING = {'type': str, 'subtype': str, 'session_id': str, 'uuid': str,
            'estimated_tokens': int, 'estimated_tokens_delta': int}
RATE = {'type': str, 'session_id': str, 'uuid': str, 'rate_limit_info': {
    'isUsingOverage': bool, 'overageResetsAt': int, 'overageStatus': str,
    'rateLimitType': str, 'resetsAt': int, 'status': str, 'unifiedWindows': {
        'five_hour': {'resetsAt': int, 'utilization': 'number'},
        'seven_day': {'resetsAt': int, 'utilization': 'number'}}}}
USAGE = {'input_tokens', 'output_tokens', 'cached_input_tokens', 'cache_creation_input_tokens',
    'cache_read_input_tokens', 'cache_creation', 'ephemeral_5m_input_tokens',
    'ephemeral_1h_input_tokens', 'server_tool_use', 'web_search_requests', 'web_fetch_requests',
    'inputTokens', 'outputTokens', 'cacheReadInputTokens', 'cacheCreationInputTokens', 'costUSD',
    'contextWindow', 'maxOutputTokens', 'input_tokens_details', 'cached_tokens',
    'output_tokens_details', 'reasoning_tokens', 'service_tier', 'inference_geo', 'iterations',
    'speed', 'cache_write_input_tokens', 'reasoning_output_tokens', 'thinking_tokens',
    'thinkingTokens', 'webSearchRequests', 'canonicalModel', 'provider', 'costBasis'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw, limit=MAX_STDOUT):
    if isinstance(raw, str):
        raw = raw.encode('utf-8')
    if not isinstance(raw, bytes) or len(raw) > limit:
        raise ValueError('json-byte-bound')
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate-json-key')
            result[key] = value
        return result
    def constant(_):
        raise ValueError('nonfinite-json-number')
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)
    def finite(item):
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError('nonfinite-json-number')
        if isinstance(item, str):
            item.encode('utf-8')  # Reject unpaired surrogate escapes.
        if isinstance(item, dict):
            for key, child in item.items(): finite(key); finite(child)
        elif isinstance(item, list):
            for child in item: finite(child)
    finite(value)
    return value


def shape(value, spec):
    if spec == 'effort': return value is None or value in ('low','medium','high','xhigh','max')
    if spec == 'strings': return isinstance(value, list) and len(value) <= 128 and all(shape(v, str) for v in value)
    if spec == 'empty-list': return type(value) is list and value == []
    if spec == 'empty-dict': return type(value) is dict and value == {}
    if spec == 'plugins':
        return isinstance(value, list) and len(value) <= 32 and all(isinstance(v, dict) and {'name','path'} <= set(v) <= {'name','path','source','version'} and all(shape(x, str) for x in v.values()) for v in value)
    if isinstance(spec, dict):
        return (isinstance(value, dict) and set(value) == set(spec)
                and all(shape(value[k], t) for k, t in spec.items()))
    if spec == 'number':
        return (type(value) is int and 0 <= value <= MAX_NUMBER) or (
            type(value) is float and math.isfinite(value) and 0 <= value <= MAX_NUMBER)
    return (type(value) is spec and (spec is not int or 0 <= value <= MAX_NUMBER)
            and (spec is not str or len(value) <= 4096))


def fields(value, required, optional=None):
    optional = optional or {}
    if not isinstance(value, dict) or not set(required) <= set(value) <= set(required) | set(optional):
        raise ValueError('unknown-or-missing-wrapper-field')
    for key, spec in {**required, **optional}.items():
        if key in value and not shape(value[key], spec):
            raise ValueError('invalid-wrapper-field-type')


STRUCTURED_USAGE = {
    'cache_creation': {'ephemeral_5m_input_tokens', 'ephemeral_1h_input_tokens'},
    'server_tool_use': {'web_search_requests', 'web_fetch_requests'},
    'input_tokens_details': {'cached_tokens'},
    'output_tokens_details': {'reasoning_tokens', 'thinking_tokens'},
}


def numeric_usage(value):
    if not isinstance(value, dict) or not set(value) <= USAGE:
        raise ValueError('unrecognised-usage-shape')
    result = {}
    for key, item in value.items():
        if key in {'service_tier', 'inference_geo', 'speed', 'canonicalModel', 'provider', 'costBasis'}:
            if item is not None and not shape(item, str): raise ValueError('invalid-usage-metadata')
            continue  # Accounting labels do not establish the response model.
        if key == 'iterations':
            if not isinstance(item, list) or len(item) > 64: raise ValueError('unrecognised-usage-iterations')
            result[key] = []
            for row in item:
                allowed = {'type', 'input_tokens', 'output_tokens', 'cache_creation_input_tokens',
                           'cache_read_input_tokens', 'cache_creation'}
                if not isinstance(row, dict) or not set(row) <= allowed or not shape(row.get('type'), str):
                    raise ValueError('unrecognised-usage-iteration')
                result[key].append(numeric_usage({k:v for k,v in row.items() if k != 'type'}))
            continue
        if item is None and key in {'cache_creation_input_tokens', 'cache_read_input_tokens',
                                    'cache_creation', 'server_tool_use', 'output_tokens_details'}:
            result[key] = None; continue
        if key in STRUCTURED_USAGE:
            if not isinstance(item, dict) or not set(item) <= STRUCTURED_USAGE[key]:
                raise ValueError('invalid-structured-usage')
            if any(not shape(v, 'number') for v in item.values()):
                raise ValueError('invalid-structured-usage-number')
            if key == 'server_tool_use' and any(v != 0 for v in item.values()):
                raise ValueError('provider-reports-tool-use')
            result[key] = dict(item)
        elif shape(item, 'number'):
            result[key] = item
            if key in {'web_search_requests', 'web_fetch_requests', 'webSearchRequests', 'server_tool_use'} and item != 0:
                raise ValueError('provider-reports-tool-use')
        else: raise ValueError('invalid-usage-number')
    return result


SUBAGENTS = {'spawned': int, 'requested': {'background': int, 'foreground': int, 'unset': int},
    'started_in_background': int, 'by_type': 'empty-dict', 'max_depth': int,
    'spawned_by_subagents': int, 'completed': int, 'failed': int,
    'killed': {'parent': int, 'user': int, 'system': int},
    'refused': {'depth_limit': int, 'concurrency_limit': int, 'budget': int}}
INIT_EXTRA = {'betas':'strings', 'capabilities':'strings', 'analytics_disabled':bool,
    'product_feedback_disabled':bool, 'fast_mode_disabled_reason':str, 'messaging_socket_path':str,
    'terminal_slash_commands':'empty-list', 'scratchpad_path':str, 'worker_epoch':int,
    'powershell_path':str, 'effort':'effort', 'plugin_errors':'empty-list',
    'plugin_warnings':'empty-list', 'mcp_server_errors':'empty-list'}
RESULT_EXTRA = {k:int for k in ('ttft_ms','ttft_stream_ms','time_to_request_ms',
    'first_content_frame_ms','first_stream_post_ms','first_stream_post_ack_ms',
    'first_stream_post_queue_wait_ms','queued_turn_count','result_index')}
RESULT_EXTRA.update({'fast_mode_state':str, 'fast_mode_disabled_reason':str,
    'api_error_status':type(None), 'terminal_reason':str, 'subagent_stats':SUBAGENTS})
FAST_STATES = {'off','cooldown','on'}
FAST_REASONS = {'free','preference','extra_usage_disabled','network_error','unknown',
    'not_first_party','disabled_by_env','model_not_allowed','sdk_opt_in_required','pending'}


def compatibility_metadata(event):
    if 'fast_mode_state' in event and event['fast_mode_state'] not in FAST_STATES:
        raise ValueError('unknown-fast-mode-state')
    if 'fast_mode_disabled_reason' in event and event['fast_mode_disabled_reason'] not in FAST_REASONS:
        raise ValueError('unknown-fast-mode-reason')
    if 'terminal_reason' in event and event['terminal_reason'] != 'completed':
        raise ValueError('noncompleted-terminal-reason')
    if event.get('queued_turn_count',0) != 0: raise ValueError('additional-turns-queued')
    if 'subagent_stats' in event:
        def zero(v): return all(zero(c) for c in v.values()) if isinstance(v,dict) else type(v) is int and v == 0
        if not zero(event['subagent_stats']): raise ValueError('provider-reports-subagent-use')


# Fixed public field names only. Unknown/dynamic keys are represented by digests,
# never copied as purported schema names. Scalars expose types, never values.
SHAPE_KEYS = set(USAGE) | set(INIT_EXTRA) | set(RESULT_EXTRA) | set(THINKING) | set(RATE) | {
 'type','subtype','id','uuid','session_id','thread_id','item','message','content','text','thinking',
 'signature','data','model','usage','role','stop_reason','stop_sequence','stop_details','container',
 'context_management','diagnostics','input_transformations','timestamp','request_id','parent_tool_use_id',
 'error','is_error','result','modelUsage','duration_ms','duration_api_ms','num_turns','total_cost_usd',
 'permission_denials','cwd','tools','mcp_servers','permissionMode','slash_commands','apiKeySource',
 'claude_code_version','output_style','agents','skills','plugins','fast_mode_state','name','path',
 'source','version','rate_limit_info','isUsingOverage','overageResetsAt','overageStatus','rateLimitType',
 'resetsAt','status','unifiedWindows','five_hour','seven_day','utilization','spawned','requested',
 'background','foreground','unset','started_in_background','by_type','max_depth','spawned_by_subagents',
 'completed','failed','killed','parent','user','system','refused','depth_limit','concurrency_limit','budget'}
DYNAMIC_MAPS = {'modelUsage','wire_tool_inputs','wire_ingest_context','by_type'}


def structural_diagnostic(events):
    nodes = 0; truncated = False
    def visit(value, depth=0, dynamic=False):
        nonlocal nodes,truncated
        nodes += 1
        if depth > 8 or nodes > 2048: truncated=True; return {'cutoff':True}
        if isinstance(value,dict):
            result={}
            for key,child in list(value.items())[:64]:
                label=key if key in SHAPE_KEYS and not dynamic else 'key_sha256_'+sha(key.encode())
                result[label]=visit(child,depth+1,key in DYNAMIC_MAPS or key not in SHAPE_KEYS)
            if len(value)>64: truncated=True
            return {'object_fields':result,'field_count':len(value)}
        if isinstance(value,list):
            if len(value)>8: truncated=True
            return {'array_length':len(value),'item_shapes':[visit(v,depth+1,dynamic) for v in value[:8]]}
        return type(value).__name__
    result={'schema':'okf-cli-value-free-shapes.v1','events':[visit(e) for e in events[:128]],
            'event_count':len(events),'truncated':len(events)>128}
    result['truncated'] = result['truncated'] or truncated
    raw=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2).encode()
    if len(raw)>32768:
        return {'schema':'okf-cli-value-free-shapes.v1','event_count':len(events),
                'truncated':True,'shape_sha256':sha(raw),'retention':'shape-byte-cap'}
    return result


def identity(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 128:
        raise ValueError('invalid-model-identity')
    # Never turn arbitrary dynamic object keys into public telemetry keys.
    accepted = re.fullmatch(r'(?:claude-(?:opus|sonnet|haiku)-[0-9][A-Za-z0-9._-]*|gpt-[0-9A-Za-z][A-Za-z0-9._-]*|o[0-9][A-Za-z0-9._-]*)', value)
    return {'value': value if accepted else None, 'sha256': sha(value.encode()),
            'status': 'reported' if accepted else 'unrecognised-identity-withheld'}


def recognise(provider, raw):
    """Return public census and an in-memory candidate; reject tools without exceptions."""
    public = {'schema': 'okf-direct-cli-events.v4', 'event_count': 0, 'issues': [],
        'stream_completed': False, 'tool_event_census': 'unknown', 'observed_tool_events': 0,
        'response_models': [], 'accounting_models': [], 'usage': {},
        'model_identity_status': 'not-reported',
        'warnings': [], 'telemetry': [], 'assistant_confirmation': 'absent',
        'model_identity_boundary': 'Reported identities only; no inferred or controlled single-model identity.'}
    if provider not in {'claude-subscription', 'codex-subscription'}:
        raise ValueError('unregistered-provider')
    texts = []; finals = []; models = []; terminal = None
    try:
        if len(raw) > MAX_STDOUT: raise ValueError('stdout-byte-bound')
        lines = raw.decode('utf-8').splitlines()
        if not lines or len(lines) > 8192: raise ValueError('event-count-bound')
        events = [strict_json(line) for line in lines if line.strip()]
        if not events or any(not isinstance(e, dict) for e in events):
            raise ValueError('invalid-event-object')
        public['event_count'] = len(events)
        public['structural_diagnostic'] = structural_diagnostic(events)
        terminals = {'result'} if provider == 'claude-subscription' else {'turn.completed', 'turn.failed'}
        if sum(e.get('type') in terminals for e in events) != 1 or events[-1].get('type') not in terminals:
            raise ValueError('incomplete-or-duplicate-terminal')
        for event_index, event in enumerate(events):
            public['last_validated_event_index'] = event_index - 1
            public['failure_event_index'] = event_index
            kind = event.get('type')
            if provider == 'codex-subscription':
                if kind == 'thread.started': fields(event, {'type': str, 'thread_id': str})
                elif kind == 'turn.started': fields(event, {'type': str})
                elif kind == 'turn.completed':
                    fields(event, {'type': str, 'usage': dict}, {'model': str})
                    public['usage'] = numeric_usage(event['usage']); terminal = event
                    if 'model' in event: models.append(identity(event['model']))
                elif kind in {'error', 'turn.failed'}:
                    raise ValueError('provider-error-event')
                elif kind in {'item.started', 'item.updated', 'item.completed'}:
                    fields(event, {'type': str, 'item': dict})
                    item = event['item']; typ = item.get('type')
                    if typ == 'error':
                        fields(item, {'id': str, 'type': str, 'message': str})
                        if kind != 'item.completed' or item['message'] != SKILL_WARNING:
                            raise ValueError('unrecognised-error-item')
                        public['warnings'].append('skill-catalogue-shortening-host-context-still-visible')
                    elif typ in {'agent_message', 'reasoning'}:
                        # Text is bounded by the stream limit, not the short wrapper-string bound.
                        if set(item) != {'id', 'type', 'text'} or not isinstance(item['id'], str) or not isinstance(item['text'], str):
                            raise ValueError('invalid-message-item')
                        if typ == 'agent_message' and kind == 'item.completed': texts.append(item['text'])
                    else:
                        if typ in {'command_execution', 'file_change', 'mcp_tool_call', 'web_search',
                                   'collab_tool_call', 'tool_call', 'function_call'}:
                            public['observed_tool_events'] += 1
                        raise ValueError('forbidden-or-unknown-item')
                else: raise ValueError('unknown-event')
                continue
            if kind == 'system':
                if event.get('subtype') == 'thinking_tokens':
                    if not shape(event, THINKING): raise ValueError('unknown-thinking-telemetry')
                    public['telemetry'].append('thinking-token-counter')
                elif event.get('subtype') == 'init':
                    fields(event, {'type': str, 'subtype': str}, {
                        'cwd': str, 'session_id': str, 'uuid': str, 'tools': list, 'mcp_servers': list,
                        'model': str, 'permissionMode': str, 'slash_commands': list, 'apiKeySource': str,
                        'claude_code_version': str, 'output_style': str, 'agents': 'strings', 'skills': 'strings',
                        'plugins': 'plugins', 'fast_mode_state': str, **INIT_EXTRA})
                    if any(event.get(k, []) for k in ('tools', 'mcp_servers')):
                        raise ValueError('nonempty-tool-configuration')
                    if 'permissionMode' in event and event['permissionMode'] != 'dontAsk':
                        raise ValueError('unexpected-permission-mode')
                    for k in ('slash_commands', 'skills'):
                        if event.get(k, []): raise ValueError('nonempty-customisation-configuration')
                    compatibility_metadata(event)
                    public['advertised_catalogue'] = {k:{'count':len(event.get(k,[])),
                        'sha256':sha(json.dumps(event.get(k,[]),sort_keys=True,separators=(',',':')).encode())}
                        for k in ('agents','plugins','capabilities')}
                    public['host_context_boundary'] = 'Advertised agents/plugins are catalogues, not observed calls; safe mode does not prove identical or empty provider system context.'
                    # Init model is configuration, not a response model identity.
                else: raise ValueError('unknown-system-shape')
            elif kind == 'rate_limit_event':
                if not shape(event, RATE): raise ValueError('unknown-rate-limit-shape')
                public['telemetry'].append('rate-limit-counter')
            elif kind == 'assistant':
                fields(event, {'type': str, 'message': dict}, {'parent_tool_use_id': type(None),
                    'session_id': str, 'uuid': str, 'error': type(None), 'timestamp':str, 'request_id':str})
                msg = event['message']
                fields(msg, {'content': list}, {'id': str, 'type': str, 'role': str, 'model': str,
                    'stop_reason': str if msg.get('stop_reason') is not None else type(None),
                    'stop_sequence': type(None), 'usage': dict, 'context_management': type(None),
                    'container':type(None), 'stop_details':type(None), 'diagnostics':type(None),
                    'input_transformations':'empty-list'})
                if msg.get('role', 'assistant') != 'assistant' or msg.get('type', 'message') != 'message':
                    raise ValueError('invalid-assistant-role')
                if msg.get('stop_reason') not in {None, 'end_turn', 'stop_sequence'}:
                    raise ValueError('nonfinal-assistant-stop-reason')
                if 'usage' in msg: numeric_usage(msg['usage'])
                if 'model' in msg: models.append(identity(msg['model']))
                chunks = []
                for part in msg['content']:
                    if not isinstance(part, dict): raise ValueError('invalid-content-block')
                    typ = part.get('type')
                    if typ == 'text':
                        if set(part) != {'type', 'text'} or not isinstance(part['text'], str):
                            raise ValueError('invalid-text-block')
                        chunks.append(part['text'])
                    elif typ == 'thinking':
                        if set(part) - {'type', 'thinking', 'signature'} or not isinstance(part.get('thinking'), str) or ('signature' in part and not isinstance(part['signature'], str)):
                            raise ValueError('invalid-thinking-block')
                    elif typ == 'redacted_thinking': fields(part, {'type': str, 'data': str})
                    else:
                        if typ in {'tool_use', 'server_tool_use', 'tool_result'}:
                            public['observed_tool_events'] += 1
                        raise ValueError('forbidden-or-unknown-content')
                if chunks: texts.append(''.join(chunks))
            elif kind == 'user':
                msg = event.get('message')
                if isinstance(msg, dict) and isinstance(msg.get('content'), list):
                    public['observed_tool_events'] += sum(isinstance(p, dict) and p.get('type') == 'tool_result'
                                                         for p in msg['content'])
                raise ValueError('forbidden-user-or-tool-result')
            elif kind == 'result':
                # result is answer-sized, so validate its type separately.
                if not isinstance(event.get('result'), str): raise ValueError('missing-direct-result')
                fields({k: v for k, v in event.items() if k != 'result'},
                    {'type': str, 'subtype': str, 'is_error': bool}, {
                        'session_id': str, 'uuid': str, 'duration_ms': 'number', 'duration_api_ms': 'number',
                        'num_turns': int, 'total_cost_usd': 'number', 'usage': dict, 'modelUsage': dict,
                        'permission_denials': list, 'stop_reason': str if event.get('stop_reason') is not None else type(None), **RESULT_EXTRA})
                compatibility_metadata(event)
                if event['is_error'] or event['subtype'] != 'success': raise ValueError('provider-error-result')
                if event.get('permission_denials', []): raise ValueError('permission-denial-observed')
                if event.get('stop_reason') not in {None, 'end_turn', 'stop_sequence'}:
                    raise ValueError('nonfinal-result-stop-reason')
                public['usage'] = numeric_usage(event.get('usage', {}))
                for name, data in event.get('modelUsage', {}).items():
                    public['accounting_models'].append({'model': identity(name), 'usage': numeric_usage(data)})
                terminal = event; finals.append(event['result'])
            else: raise ValueError('unknown-event')
        if terminal is None: raise ValueError('missing-successful-terminal')
        public.pop('failure_event_index',None)
        public['last_validated_event_index'] = len(events)-1
        public['stream_completed'] = True
        public['tool_event_census'] = 'complete-zero-observed-tools'
        public['response_models'] = list({m['sha256']: m for m in models}.values())
        identities = {m['sha256'] for m in public['response_models']}
        identities.update(m['model']['sha256'] for m in public['accounting_models'])
        if len(identities) > 1: public['model_identity_status'] = 'multiple-reported-identities'
        elif identities: public['model_identity_status'] = 'reported-identity-see-response-and-accounting-roles'
        if len(texts) > 1: raise ValueError('ambiguous-assistant-answers')
        candidate = finals[0] if provider == 'claude-subscription' else texts[0] if texts else None
        if candidate is None: raise ValueError('missing-answer')
        answer = strict_json(candidate, MAX_ANSWER)
        if not isinstance(answer, dict): raise ValueError('answer-not-object')
        if provider == 'claude-subscription' and texts:
            if strict_json(texts[0], MAX_ANSWER) != answer: raise ValueError('assistant-terminal-disagreement')
            public['assistant_confirmation'] = 'canonical-values-agree'
        elif provider == 'codex-subscription': public['assistant_confirmation'] = 'sole-completed-agent-message'
        public['answer_text_sha256'] = sha(candidate.encode())
        public['answer_text_bytes'] = len(candidate.encode())
        return public, answer
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError) as error:
        category = str(error) if type(error) is ValueError and re.fullmatch(r'[a-z][a-z-]{1,70}', str(error)) else 'invalid-stream-or-json'
        public['issues'] = [category]
        # A recognised answer-format failure does not erase a completed tool census.
        if not public['stream_completed']: public['tool_event_census'] = 'unknown'
        return public, None
