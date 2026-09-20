#!/usr/bin/env python3
"""Separately frozen successor: exact reversible evidence and observed CLI shapes."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time

import monday_cli_events_v2 as event_parser
from project_monday_model_contexts import expand,raw as canonical
from run_monday_model_trials import capture,command,environment,subscription_auth
from run_staff_model_trials import encoded,sha,parse_answer,mechanical

ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/'evaluation/model-comparison/household-compact-v2-candidate'
OUT=ROOT/'validation/model-comparison/household-compact-v2'
CODE=['scripts/run_monday_compact_trials.py','scripts/monday_cli_events_v2.py','scripts/project_monday_model_contexts.py','scripts/run_monday_model_trials.py','scripts/run_staff_model_trials.py','scripts/evaluate_fixed_answers.py']
LOADED={p:sha((ROOT/p).read_bytes()) for p in CODE}


def read(name,limit=1048576):
    if not isinstance(name,str) or name.startswith('/') or '\\' in name or any(p in {'','..','.'} for p in name.split('/')):raise ValueError('Unsafe input path')
    path=ROOT/name
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()) or not path.is_file() or path.stat().st_size>limit:raise ValueError('Unsafe or oversized input')
    with path.open('rb') as stream:value=stream.read(limit+1)
    if len(value)>limit:raise ValueError('Input exceeds bound')
    return value


def inputs():
    prefix=str(SPEC.relative_to(ROOT))+'/'
    protocol=json.loads(read(prefix+'protocol.json'));candidate=json.loads(read(prefix+'candidate-manifest.json'))
    if protocol.get('schema')!='okf-compact-paired-model-protocol.v2' or protocol.get('timeout_seconds')!=240 or protocol.get('providers')!=['claude-subscription','codex-subscription']:raise ValueError('Unexpected successor protocol')
    if protocol['selected_cases']!=[p['id'] for p in candidate['packets']]:raise ValueError('Case set differs')
    names=[prefix+p for p in ['protocol.json','system-prompt.txt','user-prompt.txt','candidate-manifest.json','byte-census.json']]+CODE+['evaluation/answer-review/answer.schema.json']
    cases=[]
    for case in candidate['packets']:
        if not re.fullmatch(r'staff-\d{3}|control-unknown',case['id']) or case['path']!='packets/'+case['id']+'.json':raise ValueError('Unsafe packet path')
        name=prefix+case['path'];packet_raw=read(name,262144)
        if len(packet_raw)!=case['bytes'] or sha(packet_raw)!=case['sha256']:raise ValueError('Candidate packet changed')
        packet=json.loads(packet_raw);audit=packet['audit'];source=read(audit['path'],262144)
        if packet.get('schema')!='okf-lossless-model-context.v1' or sha(source)!=audit['sha256'] or sha(source)!=case['original_context_sha256'] or len(source)!=audit['bytes']:raise ValueError('Audit binding differs')
        context=expand(packet['context'],packet['values'])
        if canonical(context)!=source:raise ValueError('Lossless roundtrip failed')
        if context['context_id']!=audit['context_id'] or context['evidence_status']!='insufficient' or context['ai_answer'] is not None:raise ValueError('Unexpected original context boundary')
        original_manifest=read(audit['manifest_path'],262144)
        if sha(original_manifest)!=audit['manifest_sha256'] or sha(original_manifest)!=candidate['original_manifest_sha256']:raise ValueError('Original experiment binding differs')
        names.extend([name,audit['path'],audit['manifest_path']]);cases.append({**case,'packet_raw':packet_raw,'context':context})
    bound={name:read(name) for name in sorted(set(names))}
    if any(sha(bound[name])!=loaded for name,loaded in LOADED.items()):raise ValueError('Loaded helper differs from current bytes')
    return protocol,cases,bound


def verify_commit(commit,bound):
    if not re.fullmatch('[a-f0-9]{40}',commit or ''):raise ValueError('Exact source commit required')
    for name,value in bound.items():
        expected=subprocess.check_output(['git','rev-parse',commit+':'+name],cwd=ROOT,stderr=subprocess.DEVNULL,text=True,timeout=10).strip()
        if hashlib.sha1(f'blob {len(value)}\0'.encode()+value).hexdigest()!=expected:raise ValueError('Input differs from selected commit: '+name)


def load_frozen(bound):
    path=str((SPEC/'frozen-manifest.json').relative_to(ROOT));manifest_raw=read(path,262144);manifest=json.loads(manifest_raw)
    if manifest.get('schema')!='okf-compact-model-trial-freeze.v2':raise ValueError('Unknown freeze manifest')
    verify_commit(manifest['source_commit'],bound)
    expected=[{'path':p,'bytes':len(b),'sha256':sha(b)} for p,b in bound.items()]
    if manifest['inputs']!=expected:raise ValueError('Frozen inputs differ')
    return manifest,manifest_raw


def run_one(provider,case,p,bound,freeze,freeze_raw,attempt,run=False):
    prefix=str(SPEC.relative_to(ROOT))+'/'
    system=bound[prefix+'system-prompt.txt'].decode();template=bound[prefix+'user-prompt.txt'].decode()
    if template.count('{{PACKET_JSON}}')!=1:raise ValueError('Prompt marker differs')
    prompt=template.replace('{{PACKET_JSON}}',case['packet_raw'].decode());schema=bound['evaluation/answer-review/answer.schema.json'].decode()
    binding={'freeze_manifest_sha256':sha(freeze_raw),'packet_sha256':sha(case['packet_raw']),'original_context_sha256':case['original_context_sha256'],'context_id':case['context']['context_id'],'system_prompt_sha256':sha(system.encode()),'prompt_sha256':sha(prompt.encode()),'schema_sha256':sha(schema.encode())}
    if provider not in p['providers'] or not re.fullmatch('attempt-[0-9]{2}',attempt):raise ValueError('Invalid provider/attempt')
    target=OUT/provider/case['id']/attempt
    if target.is_symlink():raise ValueError('Attempt path is a symlink')
    if target.exists():
        receipt=json.loads(read(str((target/'receipt.json').relative_to(ROOT)),262144))
        if receipt['inputs']!=binding or receipt['provider']!=provider or receipt['case_id']!=case['id'] or receipt['attempt']!=attempt or receipt['source_commit']!=freeze['source_commit'] or receipt['loaded_helper_sha256']!=LOADED:raise ValueError('Retained attempt identity differs')
        for file,digest in receipt['artefacts'].items():
            if file not in {'model-output.json','answer.json'} or sha(read(str((target/file).relative_to(ROOT)),2097152))!=digest:raise ValueError('Retained output differs')
        if receipt['answer_present'] and mechanical(json.loads((target/'answer.json').read_bytes()),case['context'])!=receipt['mechanical_assessment']:raise ValueError('Retained assessment differs')
        return receipt
    if not run:raise ValueError('Missing retained attempt')
    target.mkdir(parents=True,exist_ok=False);tick=time.monotonic()
    receipt={'schema':'okf-compact-model-attempt.v2','provider':provider,'case_id':case['id'],'attempt':attempt,'source_commit':freeze['source_commit'],'inputs':binding,'loaded_helper_sha256':LOADED,'started_at':datetime.now(timezone.utc).isoformat(),'answer_present':False,'artefacts':{},'specialist_accepted':False,'human_review':'pending','comparative_accuracy_established':False,'model_override':None,'fallback_override':None}
    def retain(name,value):
        value_raw=encoded(value)
        with (target/name).open('xb') as stream:stream.write(value_raw)
        receipt['artefacts'][name]=sha(value_raw)
    try:
        with tempfile.TemporaryDirectory(prefix='okf-compact-trial-') as directory:
            args,controls=command(provider,directory,system,schema);env=environment();receipt['isolation']=controls
            receipt['auth_observation']=subscription_auth(provider,args[0],env)
            if not receipt['auth_observation']['accepted']:receipt['status']='blocked-subscription-auth-not-established'
            else:
                version=subprocess.run([args[0],'--version'],capture_output=True,text=True,timeout=10,env=env);receipt['cli_version']=version.stdout.strip()[:100]
                result=capture(args,prompt,directory,env,p);receipt.update(exit_code=result['returncode'],stdout_sha256=sha(result['stdout']),stderr_sha256=sha(result['stderr']))
                receipt['tool_event_census_status']='unknown-incomplete-stream'
                if result['timed_out']:receipt['status']='provider-timeout'
                elif result['output_bound_exceeded']:receipt['status']='provider-output-bound-exceeded'
                else:
                    output=event_parser.sanitise(provider,result['stdout']);retain('model-output.json',output)
                    receipt.update(tool_event_census_status=output['tool_event_census_status'],recognition_issues=output['recognition_issues'],response_models=output['response_models'],accounting_models=output['accounting_models'],usage=output.get('usage',{}),recognised_warnings=output['recognised_warnings'])
                    if result['returncode'] or output.get('is_error'):receipt['status']='provider-call-failed'
                    elif output['recognition_issues']:receipt['status']='rejected-event-recognition'
                    else:
                        answer=output.get('structured_output')
                        if answer is None:answer=parse_answer(output.get('provider_result') or '')
                        retain('answer.json',answer);receipt.update(answer_present=True,status='actual-model-response-retained',mechanical_assessment=mechanical(answer,case['context']))
    except (ValueError,OSError,KeyError,TypeError,subprocess.TimeoutExpired) as error:receipt.update(status='provider-or-output-error',error_category=type(error).__name__)
    receipt.update(finished_at=datetime.now(timezone.utc).isoformat(),elapsed_seconds=round(time.monotonic()-tick,3))
    with (target/'receipt.json').open('xb') as stream:stream.write(encoded(receipt))
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--freeze',action='store_true');parser.add_argument('--source-commit');parser.add_argument('--run',action='store_true');parser.add_argument('--provider');parser.add_argument('--case');parser.add_argument('--attempt');parser.add_argument('--manifest-sha256');parser.add_argument('--report',action='store_true');parser.add_argument('--check-report',action='store_true');args=parser.parse_args();p,cases,bound=inputs()
    if sum([args.freeze,args.run,args.report,args.check_report])>1:raise ValueError('Choose only one operation')
    target=SPEC/'frozen-manifest.json'
    if args.freeze:
        if args.run:raise ValueError('Freeze and call are separate operations')
        verify_commit(args.source_commit,bound)
        value={'schema':'okf-compact-model-trial-freeze.v2','source_commit':args.source_commit,'inputs':[{'path':name,'bytes':len(data),'sha256':sha(data)} for name,data in bound.items()],'historical_contexts_unchanged':True,'model_calls':0}
        with target.open('xb') as stream:stream.write(encoded(value))
        print(json.dumps({'status':'frozen','manifest_sha256':sha(target.read_bytes()),'model_calls':0}));return
    if not target.exists():
        if args.run or args.report or args.check_report:raise ValueError('Candidate is not frozen; no call permitted')
        print(json.dumps({'status':'candidate-verified-not-frozen','cases':len(cases),'model_calls':0}));return
    freeze,freeze_raw=load_frozen(bound)
    if args.report or args.check_report:
        by_id={c['id']:c for c in cases};attempts=[]
        for path in sorted(OUT.glob('*/*/attempt-*/receipt.json')):
            provider,case_id,attempt=path.parts[-4:-1]
            if case_id not in by_id:raise ValueError('Unknown retained case')
            row=run_one(provider,by_id[case_id],p,bound,freeze,freeze_raw,attempt)
            attempts.append({'provider':provider,'case_id':case_id,'attempt':attempt,'receipt':str(path.relative_to(ROOT)),'receipt_sha256':sha(path.read_bytes()),'status':row['status'],'answer_present':row['answer_present'],'inputs':row['inputs'],'mechanical_assessment':row.get('mechanical_assessment')})
        pairs=[]
        for case in cases:
            chosen={provider:next((r for r in reversed(attempts) if r['case_id']==case['id'] and r['provider']==provider and r['answer_present']),None) for provider in p['providers']}
            complete=all(chosen.values())
            if complete and len({json.dumps(r['inputs'],sort_keys=True) for r in chosen.values()})!=1:raise ValueError('Paired public inputs differ')
            pairs.append({'case_id':case['id'],'both_responses_retained':complete,'same_public_inputs':complete})
        value=encoded({'schema':'okf-compact-model-results.v2','freeze_manifest_sha256':sha(freeze_raw),'attempts':attempts,'pairs':pairs,'specialist_accepted':False,'comparative_accuracy_established':False})
        path=OUT/'results.json'
        if args.check_report:
            if path.read_bytes()!=value:raise ValueError('Results ledger differs')
        else:
            OUT.mkdir(parents=True,exist_ok=True)
            if path.exists() and path.read_bytes()!=value:raise ValueError('Preserve previous results ledger before replacing it')
            if not path.exists():path.write_bytes(value)
        print(json.dumps({'status':'report-verified' if args.check_report else 'report-written','attempts':len(attempts),'model_calls':0}));return
    if not args.run:print(json.dumps({'status':'frozen-inputs-verified','cases':len(cases),'model_calls':0}));return
    if args.manifest_sha256!=sha(freeze_raw) or not args.provider or not args.case or not args.attempt:raise ValueError('Explicit reviewed manifest/provider/case/attempt required')
    case=next((c for c in cases if c['id']==args.case),None)
    if case is None:raise ValueError('Unregistered case')
    result=run_one(args.provider,case,p,bound,freeze,freeze_raw,args.attempt,True)
    print(json.dumps({'provider':args.provider,'case':args.case,'status':result['status'],'answer_present':result['answer_present']}))


if __name__=='__main__':main()
