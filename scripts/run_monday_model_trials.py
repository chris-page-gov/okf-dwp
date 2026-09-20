#!/usr/bin/env python3
"""New paired trial; offline preflight by default and one explicit call per --run.

Historical harness and receipt bytes are never changed. Shared sanitisation and
literal checks are imported from the old harness and hash-bound in this release.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import threading
import time

from run_staff_model_trials import (command, encoded, forbidden_tool_events, mechanical,
    parse_answer, sanitise_claude, sanitise_codex, sha)

ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/'evaluation/model-comparison/household-2026-09-21'
OUT=ROOT/'validation/model-comparison/household-2026-09-21'
LOADED_HARNESS_SHA=sha(Path(__file__).read_bytes())
DEPENDENCIES=['scripts/run_monday_model_trials.py','scripts/run_staff_model_trials.py','scripts/evaluate_fixed_answers.py']
SUPPORT=['scripts/export_monday_trial_contexts.mjs',*DEPENDENCIES]
LOADED_DEPENDENCY_SHA={name:sha((ROOT/name).read_bytes()) for name in DEPENDENCIES}
ALLOWED_ENV={'HOME','PATH','USER','LOGNAME','SHELL','LANG','TMPDIR','TERM','COLORTERM','NO_COLOR','CODEX_HOME','CLAUDE_CONFIG_DIR'}
SAFE_ITEMS={'agent_message','reasoning'}
CODEX_EVENTS={'thread.started','turn.started','item.started','item.updated','item.completed','turn.completed','turn.failed','error'}
CLAUDE_EVENTS={'system','assistant','user','result'}
SAFE_CONTENT={'text','thinking','redacted_thinking'}


def environment():
    """Permit CLI/keychain auth paths but no API, provider, proxy or model overrides."""
    return {k:v for k,v in os.environ.items() if k in ALLOWED_ENV or k.startswith('LC_')}


def bounded(path,limit):
    path=Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>limit:
        raise ValueError('Not a bounded regular trial file')
    raw=path.read_bytes()
    if len(raw)>limit:raise ValueError('Trial file exceeds bound')
    return raw


def relative(value):
    if not isinstance(value,str) or not value or '\\' in value or '\0' in value or value.startswith('/') or any(x in {'','..','.'} for x in value.split('/')):
        raise ValueError('Unsafe trial path')
    return value


def read_in(root,name,limit):
    path=Path(root)/relative(name)
    if not path.resolve().is_relative_to(Path(root).resolve()):raise ValueError('Trial path escaped root')
    return bounded(path,limit)


def protocol():
    raw=bounded(SPEC/'protocol.json',65536);p=json.loads(raw)
    if p.get('schema')!='okf-fixed-monday-model-protocol.v1' or p.get('context_budget')!={'max_nodes':64,'max_relationships':128,'max_depth':6,'max_bytes':262144}:
        raise ValueError('Unexpected trial protocol or budget')
    if p.get('providers')!=['claude-subscription','codex-subscription'] or len(p.get('selected_cases',[]))!=6 or len(set(p['selected_cases']))!=6:
        raise ValueError('Unexpected provider or case set')
    if p.get('timeout_seconds')!=240 or p.get('max_stdout_bytes')!=2097152 or p.get('max_stderr_bytes')!=524288:
        raise ValueError('Unexpected execution bounds')
    return p,raw


def load_frozen(p,protocol_raw):
    base=SPEC/'frozen';manifest_raw=bounded(base/'manifest.json',262144);m=json.loads(manifest_raw)
    if m.get('schema')!='okf-fixed-monday-contexts.v1':raise ValueError('Unknown frozen context manifest')
    for key in ['dwp_commit','explorer_commit']:
        if not re.fullmatch('[a-f0-9]{40}',m.get(key,'')):raise ValueError('Missing immutable release identity')
    prefix='evaluation/model-comparison/household-2026-09-21/'
    allowed_inputs={prefix+'protocol.json',prefix+p['system_prompt'],prefix+p['user_prompt'],p['answer_schema'],*SUPPORT,'evaluation/semantic-expansion/assembly-index.json','context/corpus/manifest.json','evaluation/staff-questions/cases.json'}
    entries={}
    for item in m['inputs']:
        name=relative(item['path'])
        if name not in allowed_inputs or name in entries:raise ValueError('Unregistered or duplicate frozen input')
        raw=read_in(base,item['snapshot'],8*1024*1024)
        if len(raw)!=item['bytes'] or sha(raw)!=item['sha256']:raise ValueError('Frozen input hash or size differs')
        blob=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
        expected=subprocess.check_output(['git','rev-parse',m['dwp_commit']+':'+name],cwd=ROOT,text=True,stderr=subprocess.DEVNULL,timeout=10).strip()
        if blob!=expected:raise ValueError('Frozen input differs from declared source commit')
        entries[name]=(item,raw)
    if set(entries)!=allowed_inputs:raise ValueError('Incomplete frozen input set')
    public_prefix='evaluation/model-comparison/household-2026-09-21/'
    for path,expected in [(public_prefix+'protocol.json',protocol_raw),
                          (public_prefix+p['system_prompt'],bounded(SPEC/p['system_prompt'],65536)),
                          (public_prefix+p['user_prompt'],bounded(SPEC/p['user_prompt'],65536))]:
        if entries[path][1]!=expected:raise ValueError('Preregistered input changed after freeze')
    for name in DEPENDENCIES+[p['answer_schema']]:
        if entries[name][1]!=read_in(ROOT,name,1024*1024):raise ValueError('Trial helper or schema differs from frozen version')
    for name,loaded in LOADED_DEPENDENCY_SHA.items():
        if entries[name][0]['sha256']!=loaded:raise ValueError('Loaded trial helper differs from frozen version')
    if entries['scripts/run_monday_model_trials.py'][0]['sha256']!=LOADED_HARNESS_SHA:raise ValueError('Loaded harness differs from frozen version')
    if [c['id'] for c in m['cases']]!=p['selected_cases']:raise ValueError('Frozen case order or coverage differs')
    return m,manifest_raw,entries


def fixed_input(case,p,protocol_raw,manifest_raw,entries):
    raw=read_in(SPEC/'frozen',case['path'],p['context_budget']['max_bytes'])
    if case['path']!='contexts/'+case['id']+'.json' or sha(raw)!=case['sha256'] or len(raw)!=case['bytes']:
        raise ValueError('Context identity differs')
    context=json.loads(raw)
    if context.get('schema')!='okf-governed-context.v1' or context.get('ai_answer') is not None or context.get('context_id')!=case['context_id'] or context.get('evidence_status')!='insufficient':
        raise ValueError('Unexpected context boundary')
    if context.get('question')!=case['question']:raise ValueError('Question differs from frozen catalogue')
    selected=context['selected']
    if case['id']=='control-unknown' and selected:raise ValueError('Unknown control unexpectedly has evidence')
    if case['id']!='control-unknown' and not any(x['record']['kind']=='evidence' for x in selected):raise ValueError('Substantive case has no evidence')
    prefix='evaluation/model-comparison/household-2026-09-21/'
    system=entries[prefix+p['system_prompt']][1].decode();template=entries[prefix+p['user_prompt']][1].decode()
    if template.count('{{CONTEXT_JSON}}')!=1:raise ValueError('Prompt marker differs')
    prompt=template.replace('{{CONTEXT_JSON}}',raw.decode());schema=entries[p['answer_schema']][1].decode()
    binding={'context_sha256':sha(raw),'context_id':case['context_id'],'context_bytes':len(raw),
             'system_prompt_sha256':sha(system.encode()),'prompt_sha256':sha(prompt.encode()),'schema_sha256':sha(schema.encode()),
             'protocol_sha256':sha(protocol_raw),'context_manifest_sha256':sha(manifest_raw)}
    return context,system,prompt,schema,binding


def subscription_auth(provider,binary,env):
    """Read CLI status, retaining no account, email, keychain or token data."""
    args=[binary,'auth','status','--json'] if provider=='claude-subscription' else [binary,'login','status']
    result=subprocess.run(args,capture_output=True,text=True,timeout=15,env=env)
    if provider=='claude-subscription':
        try:d=json.loads(result.stdout)
        except json.JSONDecodeError:d={}
        accepted=result.returncode==0 and d.get('loggedIn') is True and d.get('authMethod')=='claude.ai' and d.get('apiProvider')=='firstParty'
    else:accepted=result.returncode==0 and 'Logged in using ChatGPT' in result.stdout+result.stderr and 'API key' not in result.stdout+result.stderr
    return {'status':'subscription-auth-observed' if accepted else 'subscription-auth-not-established','accepted':accepted,'exit_code':result.returncode}


def capture(args,prompt,directory,env,p):
    """Bound both private output streams and runtime; never persist raw streams."""
    proc=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=directory,env=env)
    chunks=[bytearray(),bytearray()];exceeded=threading.Event()
    def drain(stream,index,limit):
        while True:
            data=stream.read(65536)
            if not data:break
            if len(chunks[index])+len(data)>limit:
                exceeded.set()
                try:proc.kill()
                except ProcessLookupError:pass
                break
            chunks[index].extend(data)
    readers=[threading.Thread(target=drain,args=(proc.stdout,0,p['max_stdout_bytes']),daemon=True),threading.Thread(target=drain,args=(proc.stderr,1,p['max_stderr_bytes']),daemon=True)]
    for thread in readers:thread.start()
    def write():
        try:proc.stdin.write(prompt.encode());proc.stdin.close()
        except (BrokenPipeError,OSError):pass
    writer=threading.Thread(target=write,daemon=True);writer.start()
    timed_out=False
    try:proc.wait(timeout=p['timeout_seconds'])
    except subprocess.TimeoutExpired:timed_out=True;proc.kill();proc.wait()
    for thread in [writer,*readers]:thread.join(timeout=5)
    for stream in [proc.stdin,proc.stdout,proc.stderr]:
        try:stream.close()
        except OSError:pass
    if any(t.is_alive() for t in [writer,*readers]):raise ValueError('CLI stream did not terminate')
    return {'returncode':proc.returncode,'stdout':bytes(chunks[0]),'stderr':bytes(chunks[1]),'timed_out':timed_out,'output_bound_exceeded':exceeded.is_set()}


def sanitise(provider,raw):
    text=raw.decode()
    events=[json.loads(x) for x in text.splitlines() if x.strip()]
    if not events or any(not isinstance(e,dict) for e in events):raise ValueError('No complete event-object stream')
    if any('item' in e and not isinstance(e['item'],dict) for e in events):raise ValueError('Malformed item event')
    result=sanitise_claude(text) if provider=='claude-subscription' else sanitise_codex(text)
    extra=[]
    unknown=0
    def category(prefix,value):
        nonlocal unknown
        unknown+=1
        label=value if isinstance(value,str) and re.fullmatch(r'[a-zA-Z0-9_.-]{1,80}',value) else 'invalid-type'
        extra.append(prefix+label)
    for event in events:
        kind=event.get('type')
        allowed=CODEX_EVENTS if provider=='codex-subscription' else CLAUDE_EVENTS
        if kind not in allowed:category('unrecognised-event:',kind)
        if provider=='claude-subscription' and kind=='system' and event.get('subtype')!='init':
            category('unrecognised-system-event:',event.get('subtype'))
        item=event.get('item',{})
        if provider=='codex-subscription' and kind in {'item.started','item.updated','item.completed'}:
            if not isinstance(item,dict):category('unrecognised-item:',None)
            elif item.get('type') not in SAFE_ITEMS and item.get('type') not in result['tool_event_names']:
                category('unrecognised-item:',item.get('type'))
        if provider=='claude-subscription' and kind in {'assistant','user'}:
            message=event.get('message')
            content=message.get('content') if isinstance(message,dict) else None
            if not isinstance(content,list):category('unrecognised-content:',None)
            else:
                for part in content:
                    part_type=part.get('type') if isinstance(part,dict) else None
                    if part_type=='tool_use':continue  # Independently enumerated by the retained helper.
                    if part_type in {'server_tool_use','tool_result'}:extra.append('external-tool-event:'+part_type)
                    elif part_type not in SAFE_CONTENT:category('unrecognised-content:',part_type)
    result['tool_event_names']+=extra
    terminal={'result'} if provider=='claude-subscription' else {'turn.completed','turn.failed'}
    result['stream_completed']=events[-1].get('type') in terminal and sum(e.get('type') in terminal for e in events)==1
    result['unrecognised_event_count']=unknown
    result['tool_event_census_status']=('unknown-incomplete-stream' if not result['stream_completed'] else
        'unknown-unrecognised-event' if unknown else 'retained-completed-stream')
    if provider=='codex-subscription' and any(e.get('type') in {'turn.failed','error'} for e in events):result['is_error']=True
    if provider=='claude-subscription':
        result['response_models']=sorted({e['message']['model'] for e in events if e.get('type')=='assistant' and isinstance(e.get('message'),dict) and isinstance(e['message'].get('model'),str)})
        result['accounting_models']=sorted(result.get('model_usage',{}))
    else:
        result['response_models']=result['reported_models'];result['accounting_models']=[]
    result['model_identity_boundary']='Reported response/accounting identities only; no inferred model identity and no controlled single-model claim.'
    return result


def run_one(provider,case,p,protocol_raw,m,manifest_raw,entries,attempt,run=False):
    context,system,prompt,schema,binding=fixed_input(case,p,protocol_raw,manifest_raw,entries)
    if provider not in p['providers'] or not re.fullmatch(r'attempt-[0-9]{2}',attempt):raise ValueError('Unregistered provider or attempt')
    out=OUT/provider/case['id']/attempt
    if out.is_symlink():raise ValueError('Attempt must not be a symlink')
    if out.exists():
        receipt=json.loads(bounded(out/'receipt.json',262144))
        if receipt['inputs']!=binding or receipt['provider']!=provider or receipt['case_id']!=case['id'] or receipt['attempt']!=attempt:raise ValueError('Existing attempt identity differs')
        for name,expected in receipt['artefacts'].items():
            if name not in {'model-output.json','answer.json'} or sha(read_in(out,name,2097152))!=expected:raise ValueError('Retained artefact differs')
        if receipt.get('answer_present') and mechanical(json.loads(bounded(out/'answer.json',2097152)),context)!=receipt['mechanical_assessment']:raise ValueError('Retained assessment differs')
        return receipt
    if not run:raise ValueError('No retained attempt')
    out.mkdir(parents=True,exist_ok=False)
    receipt={'schema':'okf-paired-monday-model-attempt.v1','provider':provider,'case_id':case['id'],'attempt':attempt,
             'started_at':datetime.now(timezone.utc).isoformat(),'inputs':binding,'harness_sha256':LOADED_HARNESS_SHA,'helper_sha256':LOADED_DEPENDENCY_SHA,
             'source_commit':m['dwp_commit'],'explorer_commit':m['explorer_commit'],'model_override':None,'fallback_override':None,
             'tools_requested':[],'mcp_servers':[],'answer_present':False,'human_review':'pending','specialist_accepted':False,
             'comparative_accuracy_or_affordability_established':False,'artefacts':{}}
    tick=time.monotonic()
    def retain(name,value):
        raw=encoded(value)
        with (out/name).open('xb') as f:f.write(raw)
        receipt['artefacts'][name]=sha(raw)
    try:
        with tempfile.TemporaryDirectory(prefix='okf-monday-trial-') as directory:
            args,controls=command(provider,directory,system,schema);env=environment();receipt['isolation']=controls
            receipt['environment_policy']='Allowlisted locale, executable and subscription-auth paths; no ambient API/provider/model overrides.'
            auth=subscription_auth(provider,args[0],env);receipt['auth_observation']=auth
            if not auth['accepted']:
                receipt['status']='blocked-subscription-auth-not-established'
            else:
                version=subprocess.run([args[0],'--version'],text=True,capture_output=True,env=env,timeout=10)
                receipt['cli_version']=version.stdout.strip().splitlines()[0][:100] if version.stdout.strip() else 'not-observed'
                result=capture(args,prompt,directory,env,p)
                receipt.update(exit_code=result['returncode'],stdout_sha256=sha(result['stdout']),stderr_sha256=sha(result['stderr']))
                if result['timed_out']:receipt['status']='provider-timeout';receipt['tool_event_census_status']='unknown-incomplete-stream'
                elif result['output_bound_exceeded']:receipt['status']='provider-output-bound-exceeded';receipt['tool_event_census_status']='unknown-incomplete-stream'
                else:
                    receipt['tool_event_census_status']='unknown-incomplete-stream'
                    output=sanitise(provider,result['stdout']);retain('model-output.json',output)
                    receipt.update(reported_models=output.get('reported_models',[]),usage=output.get('usage',{}),observed_tool_events=output.get('tool_event_names',[]),formatting_events=[e for e in output.get('tool_events',[]) if e['name']=='StructuredOutput'],tool_event_census_status=output['tool_event_census_status'])
                    if result['returncode'] or output.get('is_error'):receipt['status']='provider-call-failed'
                    elif not output['stream_completed']:receipt['status']='rejected-incomplete-output-stream'
                    elif output['unrecognised_event_count']:receipt['status']='rejected-unrecognised-output-event'
                    elif forbidden_tool_events(provider,output,p):receipt['status']='rejected-observed-tool-event'
                    else:
                        answer=output.get('structured_output')
                        if answer is None:answer=parse_answer(output.get('provider_result') or '')
                        retain('answer.json',answer);receipt.update(answer_present=True,mechanical_assessment=mechanical(answer,context),status='actual-model-response-retained')
    except (ValueError,OSError,KeyError,TypeError,subprocess.TimeoutExpired) as error:
        receipt.update(status='provider-or-output-error',error_category=type(error).__name__)
    receipt.update(finished_at=datetime.now(timezone.utc).isoformat(),elapsed_seconds=round(time.monotonic()-tick,3))
    with (out/'receipt.json').open('xb') as f:f.write(encoded(receipt))
    return receipt


def report(p,protocol_raw,m,manifest_raw,entries):
    cases={c['id']:c for c in m['cases']};attempts=[]
    for file in sorted(OUT.glob('*/*/attempt-*/receipt.json')):
        provider,cid,attempt=file.parts[-4:-1]
        if cid not in cases:raise ValueError('Unregistered retained case')
        r=run_one(provider,cases[cid],p,protocol_raw,m,manifest_raw,entries,attempt)
        attempts.append({'provider':provider,'case_id':cid,'attempt':attempt,'receipt':str(file.relative_to(ROOT)),
                         'receipt_sha256':sha(file.read_bytes()),'status':r['status'],'answer_present':r['answer_present'],
                         'inputs':r['inputs'],'reported_models':r.get('reported_models',[]),'mechanical_assessment':r.get('mechanical_assessment')})
    pairs=[]
    for cid in p['selected_cases']:
        chosen={provider:next((r for r in reversed(attempts) if r['case_id']==cid and r['provider']==provider and r['answer_present']),None) for provider in p['providers']}
        complete=all(chosen.values())
        if complete and len({json.dumps(r['inputs'],sort_keys=True) for r in chosen.values()})!=1:raise ValueError('Paired public inputs differ')
        pairs.append({'case_id':cid,'both_responses_retained':complete,'same_public_inputs':complete,'attempts':{k:v['attempt'] if v else None for k,v in chosen.items()}})
    return {'schema':'okf-paired-monday-results.v1','context_manifest_sha256':sha(manifest_raw),'attempts':attempts,'pairs':pairs,
            'human_review':'pending','specialist_accepted':False,'comparative_accuracy_or_affordability_established':False,
            'historical_comparison':p['historical_comparison']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true');parser.add_argument('--provider',choices=['claude-subscription','codex-subscription'])
    parser.add_argument('--case');parser.add_argument('--attempt');parser.add_argument('--manifest-sha256');parser.add_argument('--report',action='store_true');parser.add_argument('--check-report',action='store_true')
    args=parser.parse_args();p,praw=protocol()
    if args.run and (not args.provider or not args.case or not args.attempt or not args.manifest_sha256 or args.report or args.check_report):parser.error('--run requires one provider, case, unused attempt and reviewed frozen manifest SHA-256')
    if args.case and args.case not in p['selected_cases']:parser.error('Case is not preregistered')
    if not (SPEC/'frozen').exists():
        if args.run or args.report or args.check_report:raise ValueError('Immutable inputs have not been frozen; no model call permitted')
        print(json.dumps({'status':'preregistered-awaiting-immutable-inputs','cases':p['selected_cases'],'model_calls':0}));return
    m,mraw,entries=load_frozen(p,praw)
    if args.manifest_sha256 and (not re.fullmatch('[a-f0-9]{64}',args.manifest_sha256) or sha(mraw)!=args.manifest_sha256):raise ValueError('Frozen manifest differs from explicitly selected input')
    for c in m['cases']:fixed_input(c,p,praw,mraw,entries)
    if args.report or args.check_report:
        raw=encoded(report(p,praw,m,mraw,entries));target=OUT/'results.json'
        if args.check_report:
            if bounded(target,2097152)!=raw:raise ValueError('Results ledger differs')
        else:
            OUT.mkdir(parents=True,exist_ok=True)
            if target.exists() and target.read_bytes()!=raw:raise ValueError('Preserve previous results ledger before publishing a changed report')
            if not target.exists():target.write_bytes(raw)
        print(json.dumps({'status':'report-verified' if args.check_report else 'report-written','model_calls':0}));return
    if args.provider or args.case or args.attempt:
        if not all([args.provider,args.case,args.attempt]):parser.error('Select all of provider, case and attempt')
        c=next(c for c in m['cases'] if c['id']==args.case)
        r=run_one(args.provider,c,p,praw,m,mraw,entries,args.attempt,args.run)
        print(json.dumps({'provider':args.provider,'case':args.case,'status':r['status'],'mechanical':r.get('mechanical_assessment',{}).get('status')}));return
    print(json.dumps({'status':'frozen-inputs-verified','cases':len(m['cases']),'model_calls':0}))


if __name__=='__main__':main()
