#!/usr/bin/env python3
"""Separate tiny CLI-shape diagnostic; never accepts an experiment answer."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import tempfile

from run_monday_model_trials import capture, command, environment, subscription_auth
from run_staff_model_trials import encoded, sha

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'validation/model-comparison/household-2026-09-21/diagnostics'
SYSTEM='This is a synthetic CLI event-format diagnostic. No evidence is supplied. Do not use tools or external knowledge. Return the required JSON with outcome no_evidence.'
PROMPT='No evidence is available. Return {"outcome":"no_evidence"}.'
SCHEMA=json.dumps({'type':'object','additionalProperties':False,'required':['outcome'],'properties':{'outcome':{'type':'string','enum':['no_evidence']}}})
BOUNDS={'timeout_seconds':90,'max_stdout_bytes':2097152,'max_stderr_bytes':524288}
KEYS={'type','subtype','item','id','text','message','content','rate_limit_info','thinking_tokens','num_tokens','session_id','uuid','model','usage','result','structured_output','is_error','name','input','tool_use_id','parent_tool_use_id','timestamp','status','rateLimitType','resetsAt','isUsingOverage','surpassedThreshold','duration_ms','duration_api_ms','num_turns','total_cost_usd','modelUsage','permission_denials','stop_reason','apiKeySource','tools','mcp_servers','cwd','output_style','agents','skills','plugins','slash_commands','claude_code_version','permissionMode','betas','fast_mode_state','compact_metadata','token_budget'}


def redacted_message(value):
    if not isinstance(value,str):return None
    text=value[:4000]
    text=re.sub(r'https?://\S+','[URL]',text)
    text=re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}','[email]',text)
    text=re.sub(r'(?:[A-Za-z]:\\|/)(?:[^\s,;"\']+/)*[^\s,;"\']+','[path]',text)
    text=re.sub(r'(?i)\b(?:sk-|sess-|tok-)[A-Za-z0-9_-]+','[credential]',text)
    text=re.sub(r'(?i)\b(?:api[_ -]?key|token|authorization|secret)\s*[:=]\s*\S+','[credential field]',text)
    text=re.sub(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F-]{20,}\b|\b[0-9a-fA-F]{16,}\b|\b[A-Za-z0-9_-]{48,}\b','[opaque identifier]',text)
    return text


def label(value):
    return value if isinstance(value,str) and re.fullmatch(r'[a-zA-Z0-9_.-]{1,80}',value) else 'unknown'


def shape(value,depth=0):
    if depth>=4:return type(value).__name__
    if isinstance(value,dict):
        out={k:shape(v,depth+1) for k,v in value.items() if k in KEYS}
        out['unlisted_key_count']=sum(k not in KEYS for k in value)
        return out
    if isinstance(value,list):return {'array_length':len(value),'item_shapes':[shape(x,depth+1) for x in value[:4]]}
    return type(value).__name__


def census(raw):
    events=[json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    if not events or any(not isinstance(e,dict) for e in events):raise ValueError('Invalid diagnostic event stream')
    rows=[];errors=[];models=set();formatters={};results=[]
    for event in events:
        kind=label(event.get('type'));row={'type':kind,'shape':shape(event)}
        if 'subtype' in event:row['subtype']=label(event['subtype'])
        item=event.get('item',{})
        if isinstance(item,dict) and item.get('type'):
            row['item_type']=label(item['type'])
            if item['type']=='error':errors.append({'location':'item.error','message':redacted_message(item.get('message') or item.get('text'))})
        if kind in {'error','turn.failed'}:errors.append({'location':kind,'message':redacted_message(event.get('message') or (event.get('error',{}) if isinstance(event.get('error'),dict) else {}).get('message'))})
        message=event.get('message',{})
        if isinstance(message,dict):
            model=message.get('model')
            if isinstance(model,str) and re.fullmatch(r'[a-zA-Z0-9_.:/-]{1,100}',model):models.add(model)
            for part in message.get('content',[]) if isinstance(message.get('content'),list) else []:
                if not isinstance(part,dict):continue
                if part.get('type')=='tool_use' and part.get('name')=='StructuredOutput' and isinstance(part.get('id'),str):
                    formatters[part['id']]=sha(encoded(part.get('input',{})))
                if part.get('type')=='tool_result':
                    prior=formatters.get(part.get('tool_use_id'))
                    results.append({'matches_preceding_structured_output':prior is not None,'formatter_input_sha256':prior,'is_error':part.get('is_error') is True,'content_sha256':sha(encoded(part.get('content')))})
        rows.append(row)
    return {'event_count':len(events),'events':rows,'sanitised_error_messages':errors,'formatter_results':results,'response_models':sorted(models)}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--provider',required=True,choices=['codex-subscription','claude-subscription']);parser.add_argument('--run',action='store_true');args=parser.parse_args()
    if not args.run:raise ValueError('Explicit --run required; this is a new diagnostic call, not a frozen-case retry')
    target=OUT/args.provider
    target.mkdir(parents=True,exist_ok=False)
    receipt={'schema':'okf-cli-shape-diagnostic.v1','provider':args.provider,'started_at':datetime.now(timezone.utc).isoformat(),'runner_sha256':sha(Path(__file__).read_bytes()),'system_sha256':sha(SYSTEM.encode()),'prompt_sha256':sha(PROMPT.encode()),'schema_sha256':sha(SCHEMA.encode()),'model_override':None,'experiment_answer_accepted':False,'scope':'Separate tiny synthetic diagnostic; does not replace or reinterpret frozen experiment outcomes. Raw streams, account/session identifiers, paths and reasoning are not retained.'}
    try:
        with tempfile.TemporaryDirectory(prefix='okf-cli-diagnostic-') as directory:
            command_args,controls=command(args.provider,directory,SYSTEM,SCHEMA);env=environment()
            receipt['auth_observation']=subscription_auth(args.provider,command_args[0],env);receipt['isolation']=controls
            if not receipt['auth_observation']['accepted']:raise ValueError('Subscription authentication not established')
            version=subprocess.run([command_args[0],'--version'],capture_output=True,text=True,env=env,timeout=10)
            receipt['cli_version']=version.stdout.strip()[:100]
            result=capture(command_args,PROMPT,directory,env,BOUNDS)
            receipt.update(exit_code=result['returncode'],stdout_sha256=sha(result['stdout']),stderr_sha256=sha(result['stderr']),timed_out=result['timed_out'],output_bound_exceeded=result['output_bound_exceeded'])
            if result['timed_out'] or result['output_bound_exceeded']:receipt['census_status']='unknown-incomplete-stream'
            else:receipt.update(census(result['stdout']),census_status='diagnostic-shapes-only')
    except (ValueError,OSError,KeyError,TypeError,subprocess.TimeoutExpired) as error:
        receipt.update(census_status='diagnostic-error',error_category=type(error).__name__)
    receipt['finished_at']=datetime.now(timezone.utc).isoformat()
    (target/'receipt.json').write_bytes(encoded(receipt))
    print(json.dumps({'provider':args.provider,'census_status':receipt['census_status'],'path':str((target/'receipt.json').relative_to(ROOT))}))


if __name__=='__main__':main()
