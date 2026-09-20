#!/usr/bin/env python3
"""One separately authorised synthetic reasoning diagnostic, never a trial retry."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import tempfile

from diagnose_monday_cli_events import BOUNDS, ROOT
from run_monday_model_trials import capture, command, environment, subscription_auth
from run_staff_model_trials import encoded, sha

WARNING='Skill descriptions were shortened to fit the 2% skills context budget. Codex can still see every skill, but some descriptions are shorter. Disable unused skills or plugins to leave more room for the rest.'
SYSTEM='Synthetic arithmetic diagnostic only. Do not use tools or external sources. Return the requested JSON; do not include reasoning in the final answer.'
PROMPT='Calculate the sum of the squares of integers from 1 to 137 inclusive that are divisible by neither 3 nor 5, then take its remainder modulo 97. Return outcome no_evidence and that checksum. This is a synthetic event-format diagnostic, not a benefits question.'
SCHEMA=json.dumps({'type':'object','additionalProperties':False,'required':['outcome','checksum'],'properties':{'outcome':{'type':'string','enum':['no_evidence']},'checksum':{'type':'integer'}}})


def fields(value,depth=0):
    if depth>=6:return type(value).__name__
    if isinstance(value,dict):return {(k if re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,60}',k) else 'key_sha256_'+sha(k.encode())[:16]):fields(v,depth+1) for k,v in value.items()}
    if isinstance(value,list):return {'array_length':len(value),'item_shapes':[fields(v,depth+1) for v in value[:4]]}
    return type(value).__name__


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');args=parser.parse_args()
    if not args.run:raise ValueError('Explicit --run required')
    out=ROOT/'validation/model-comparison/household-2026-09-21/diagnostics/claude-synthetic-reasoning';out.mkdir(parents=True,exist_ok=False)
    dependencies=['scripts/diagnose_monday_reasoning_events.py','scripts/diagnose_monday_cli_events.py','scripts/run_monday_model_trials.py','scripts/run_staff_model_trials.py']
    receipt={'schema':'okf-cli-reasoning-shape-diagnostic.v1','provider':'claude-subscription','started_at':datetime.now(timezone.utc).isoformat(),'source_sha256':{p:sha((ROOT/p).read_bytes()) for p in dependencies},'system':SYSTEM,'prompt':PROMPT,'answer_schema':json.loads(SCHEMA),'answer_accepted':False,'scope':'Separate synthetic arithmetic call. Event field names and types only; no raw bodies, reasoning, account/session values or credentials retained. No historical event is reclassified.'}
    with tempfile.TemporaryDirectory(prefix='okf-reasoning-diagnostic-') as directory:
        command_args,controls=command('claude-subscription',directory,SYSTEM,SCHEMA);env=environment()
        receipt['auth_observation']=subscription_auth('claude-subscription',command_args[0],env)
        if not receipt['auth_observation']['accepted']:raise ValueError('Subscription authentication not established')
        result=capture(command_args,PROMPT,directory,env,BOUNDS)
        receipt.update(exit_code=result['returncode'],stdout_sha256=sha(result['stdout']),stderr_sha256=sha(result['stderr']),timed_out=result['timed_out'],output_bound_exceeded=result['output_bound_exceeded'])
        events=[]
        if not result['timed_out'] and not result['output_bound_exceeded']:
            for line in result['stdout'].decode().splitlines():
                event=json.loads(line);row={'fields':fields(event)}
                for key in ['type','subtype']:
                    if isinstance(event.get(key),str) and re.fullmatch('[a-zA-Z0-9_.-]{1,80}',event[key]):row[key]=event[key]
                events.append(row)
        receipt.update(event_count=len(events),events=events,census_status='diagnostic-shapes-only' if events else 'unknown-incomplete-stream')
    receipt['finished_at']=datetime.now(timezone.utc).isoformat();(out/'receipt.json').write_bytes(encoded(receipt));print(json.dumps({'event_count':len(events),'census_status':receipt['census_status']}))


if __name__=='__main__':main()
