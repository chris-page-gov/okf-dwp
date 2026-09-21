#!/usr/bin/env python3
"""Verify four retained direct-v4 attempts offline; never call a provider.

Exact receipt hashes preserve recorded outcomes. Full input admission checks
immutable Git and source/service identities. Mechanical claim checks are replayed;
raw streams are unavailable, so event projections are not rerun or reclassified.
Independent claim review is separate and never equivalent to specialist acceptance.
"""
from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
SPEC = 'evaluation/model-comparison/household-direct-v4/'
OUTPUT = 'validation/model-comparison/household-direct-v4'
FREEZE = SPEC + 'frozen/manifest.json'
FREEZE_SHA = '6463e054b034d7f33df7fcad61be337f01136f996f2a00da7e428acbbae8d934'
PROVIDERS = ('claude-subscription','codex-subscription')
CASES = ('control-unknown','staff-012')
CODE = ('scripts/run_monday_direct_v4_trials.py','scripts/monday_direct_events_v4.py')
RECEIPTS = {
 ('claude-subscription','control-unknown'):'9cfb25e493cad4b5abe31b8224df551fcdbc398e457ab8ee3b620a2650c5c783',
 ('codex-subscription','control-unknown'):'27069fa993b34faa0a0736dc50dbb4392586eccdd5be859f41c57a72ebbd00e4',
 ('claude-subscription','staff-012'):'adc79b1946a46b06b81743a90e284de73ae9c7c743aea173f4ced99bc121ac90',
 ('codex-subscription','staff-012'):'821f530a195934fefef62418d8cc641d075d1f91a7b76c795a8a29e21ec80752'}
OPTIONAL_REVIEW_FILES = {'README.md','independent-claim-review.json','independent-claim-review.md'}

def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def directory(path):
    path = Path(os.path.abspath(path))
    for part in [*reversed(path.parents), path]:
        require(stat.S_ISDIR(part.lstat().st_mode), 'Directory or parent must be real; symlinks forbidden')
    return path


def bounded(path, cap=65536):
    path = Path(path); directory(path.parent)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_size <= cap, 'File must be bounded and regular')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        require(stat.S_ISREG(opened.st_mode) and (before.st_dev, before.st_ino, before.st_size)
                == (opened.st_dev, opened.st_ino, opened.st_size), 'Opened file changed')
        raw = stream.read(cap + 1)
    require(len(raw) == opened.st_size and len(raw) <= cap, 'File changed or exceeded bound')
    return raw


def load_frozen(root):
    """Execute only the two exact reviewed modules after bounded hash admission."""
    root = directory(root)
    freeze_raw = bounded(root / FREEZE)
    require(sha(freeze_raw) == FREEZE_SHA, 'Approved freeze fingerprint differs')
    freeze = json.loads(freeze_raw)
    refs = {r['path']: r for r in freeze['inputs']}
    code = {}
    for name in CODE:
        raw = bounded(root / name)
        require(len(raw) == refs[name]['bytes'] and sha(raw) == refs[name]['sha256'], 'Frozen code differs')
        code[name] = raw
    helper = types.ModuleType('monday_direct_events_v4')
    helper.__file__ = str(root / CODE[1])
    exec(compile(code[CODE[1]], helper.__file__, 'exec'), helper.__dict__)
    old = sys.modules.get(helper.__name__)
    sys.modules[helper.__name__] = helper
    try:
        trial = types.ModuleType('_verified_monday_direct_v4')
        trial.__file__ = str(root / CODE[0])
        exec(compile(code[CODE[0]], trial.__file__, 'exec'), trial.__dict__)
    finally:
        if old is None:
            del sys.modules[helper.__name__]
        else:
            sys.modules[helper.__name__] = old
    require(trial.LOADED == {name: sha(raw) for name, raw in code.items()}, 'Loaded code differs')
    return trial, freeze_raw, freeze


def exact_directory(path, expected):
    directory(path)
    names = set()
    with os.scandir(path) as entries:
        for entry in entries:
            require(len(names) < len(expected), 'Unexpected experiment entry')
            require(entry.name in expected and entry.name not in names, 'Unexpected experiment entry')
            mode = entry.stat(follow_symlinks=False).st_mode
            require(stat.S_ISDIR(mode) if expected[entry.name] == 'directory' else stat.S_ISREG(mode),
                    'Experiment entry is symlinked or special')
            names.add(entry.name)
    require(names == set(expected), 'Missing experiment entry')

def census(root):
    out=root/OUTPUT; directory(out)
    names=set()
    with os.scandir(out) as entries:
        for entry in entries:
            require(entry.name in set(PROVIDERS)|OPTIONAL_REVIEW_FILES and entry.name not in names,
                    'Unexpected experiment entry')
            mode=entry.stat(follow_symlinks=False).st_mode
            require(stat.S_ISDIR(mode) if entry.name in PROVIDERS else stat.S_ISREG(mode),
                    'Experiment entry is symlinked or special')
            if entry.name in OPTIONAL_REVIEW_FILES: bounded(out/entry.name,262144)
            names.add(entry.name)
    require(set(PROVIDERS)<=names,'Missing provider')
    for provider in PROVIDERS:
        exact_directory(out/provider,{c:'directory' for c in CASES})
        for case in CASES:
            exact_directory(out/provider/case,{'attempt-01':'directory'})


def check_attempt(receipt, projection, answer, provider, case, expected, loaded, protocol, assessment):
    common={'answer_present','artefacts','attempt','auth','capture_complete','captured_stderr_bytes',
        'captured_stdout_bytes','case_id','cli','elapsed_seconds','exit_code','fallback_override',
        'finished_at','inputs','isolation','loaded_code_sha256','model_override','process_group_kill_unavailable',
        'provider','schema','specialist_accepted','started_at','status','stderr_sha256','stdout_sha256',
        'tool_event_census'}
    require(common<=set(receipt)<=common|{'mechanical_assessment'},'Receipt fields differ')
    require(provider in PROVIDERS and case in CASES and receipt['provider']==provider and receipt['case_id']==case
        and receipt['attempt']=='attempt-01' and receipt['schema']=='okf-direct-attempt.v4','Unregistered attempt')
    require(receipt['inputs']==expected and receipt['loaded_code_sha256']==loaded,'Attempt input/code binding differs')
    require(receipt['specialist_accepted'] is False and receipt['model_override'] is None
        and receipt['fallback_override'] is None,'Authority or model boundary differs')
    require(receipt['auth']=={'accepted':True,'category':'subscription-observed'},'Subscription observation differs')
    require(type(receipt['answer_present']) is bool and receipt['answer_present']==(answer is not None),'Answer presence differs')
    require(receipt['capture_complete'] is True and receipt['process_group_kill_unavailable'] is False
        and type(receipt['exit_code']) is int and receipt['exit_code']==0,'Completed capture differs')
    for name,cap in [('captured_stdout_bytes',protocol['max_stdout_bytes']),('captured_stderr_bytes',protocol['max_stderr_bytes'])]:
        require(type(receipt[name]) is int and 0<=receipt[name]<=cap,'Capture exceeds frozen bound')
    for name in ('stdout_sha256','stderr_sha256'):
        require(isinstance(receipt[name],str) and re.fullmatch('[a-f0-9]{64}',receipt[name]),'Invalid capture digest')
    start=datetime.fromisoformat(receipt['started_at']); end=datetime.fromisoformat(receipt['finished_at'])
    require(start.tzinfo is not None and end.tzinfo is not None and start<=end,'Invalid attempt timestamps')
    elapsed=receipt['elapsed_seconds']
    require(type(elapsed) in (int,float) and math.isfinite(elapsed) and elapsed>=0
        and abs((end-start).total_seconds()-elapsed)<1,'Elapsed/timestamp discrepancy')
    require(projection['schema']=='okf-direct-cli-events.v4'
        and projection['tool_event_census']==receipt['tool_event_census'],'Recorded census differs')
    require(type(projection['event_count']) is int and 0<projection['event_count']<=8192,'Event count differs')
    require(set(receipt['artefacts'])==({'model-output.json','answer.json'} if answer is not None else {'model-output.json'}),
        'Artefact set differs')
    status=receipt['status']
    if status=='rejected-events-or-answer-json':
        require(answer is None and assessment is None and 'mechanical_assessment' not in receipt
            and isinstance(projection['issues'],list) and bool(projection['issues']),'Rejected format upgraded')
        require(projection['tool_event_census'] in {'unknown','complete-zero-observed-tools'},'Invalid rejected census')
        if projection['tool_event_census']=='unknown': require(projection['stream_completed'] is False,'Unknown census upgraded')
        else: require(projection['stream_completed'] is True and projection['observed_tool_events']==0,'Completed census differs')
        return {'accepted':False,'claims':0,'citations':0,'unknown':projection['tool_event_census']=='unknown'}
    require(status in {'accepted-mechanical-only','rejected-mechanical-controls'},'Unregistered recorded status')
    require(answer is not None and assessment is not None and receipt.get('mechanical_assessment')==assessment,
        'Replayed mechanical assessment differs')
    require(projection['issues']==[] and projection['stream_completed'] is True
        and projection['tool_event_census']=='complete-zero-observed-tools'
        and type(projection['observed_tool_events']) is int and projection['observed_tool_events']==0,
        'Accepted event format or zero-tool census differs')
    require(assessment['specialist_accepted'] is False and assessment['claim_entailment_review']=='pending',
        'Mechanical check promoted to specialist review')
    require((status=='accepted-mechanical-only') is assessment['passed'],'Mechanical acceptance differs')
    require(projection['assistant_confirmation']==('canonical-values-agree' if provider=='claude-subscription'
        else 'sole-completed-agent-message'),'Answer confirmation differs')
    return {'accepted':assessment['passed'],'claims':len(answer['claims']),
        'citations':assessment['citations_checked'],'unknown':False}


def outcomes(root,trial,protocol,bound,packages,freeze_raw):
    root=directory(root);census(root)
    schema_raw=bound[SPEC+'answer.schema.json'];schema=trial.events.strict_json(schema_raw)
    rows=[]; starts={}; ends={}
    for case in CASES:
        raw,context=packages[case]
        prompt=trial.fixed_prompt(case,raw,bound)
        expected=trial.binding(case,raw,prompt,schema_raw,freeze_raw)
        for provider in PROVIDERS:
            base=root/OUTPUT/provider/case/'attempt-01'
            receipt_raw=bounded(base/'receipt.json')
            require(sha(receipt_raw)==RECEIPTS[(provider,case)],'Recorded receipt fingerprint differs')
            receipt=trial.events.strict_json(receipt_raw)
            require(isinstance(receipt.get('artefacts'),dict) and set(receipt['artefacts'])<={'model-output.json','answer.json'},
                'Unregistered artefact')
            exact_directory(base,{'receipt.json':'file',**{n:'file' for n in receipt['artefacts']}})
            artefacts={}
            for name,digest in receipt['artefacts'].items():
                data=bounded(base/name,16384 if name=='answer.json' else 65536)
                require(sha(data)==digest,'Retained artefact fingerprint differs')
                artefacts[name]=trial.events.strict_json(data)
            require('model-output.json' in artefacts,'Recorded parser projection absent')
            answer=artefacts.get('answer.json')
            assessment=trial.mechanical(answer,context,case,schema) if answer is not None else None
            row=check_attempt(receipt,artefacts['model-output.json'],answer,provider,case,expected,trial.LOADED,protocol,assessment)
            row.update(provider=provider,case_id=case,status=receipt['status']);rows.append(row)
            starts[(provider,case)]=datetime.fromisoformat(receipt['started_at'])
            ends[(provider,case)]=datetime.fromisoformat(receipt['finished_at'])
            if case=='control-unknown':
                # Frozen gate reads only the retained control/answer/projection.
                trial.verify_control(provider,expected,context,schema)
    require(max(ends[(p,'control-unknown')] for p in PROVIDERS)
        <=min(starts[(p,'staff-012')] for p in PROVIDERS),'Substantive attempt preceded both completed controls')
    return {'schema':'okf-direct-observation-check.v2','passed':True,'freeze_sha256':FREEZE_SHA,
        'recorded_attempts':len(rows),'accepted_answers':sum(r['accepted'] for r in rows),
        'rejected_attempts':sum(not r['accepted'] for r in rows),'substantive_attempts':2,
        'unknown_tool_census_attempts':sum(r['unknown'] for r in rows),
        'mechanically_checked_claims':sum(r['claims'] for r in rows),'literal_citations_checked':sum(r['citations'] for r in rows),
        'both_control_gates_verified':True,'both_controls_preceded_substantive_attempts':True,'attempts':rows,
        'basis':'Recorded parser projections only; raw streams were not retained. Exact quotation/locator checks are replayed.',
        'claim_entailment_review':'Separate model review, not established by this integrity checker.',
        'provider_calls':0,'network_calls':0,'specialist_accepted':False}


def validate(root=ROOT,explorer_root=None):
    require(explorer_root is not None,'Full frozen input admission requires --explorer-root')
    trial,freeze_raw,freeze=load_frozen(root)
    protocol,_=trial.protocol()
    bound,packages=trial.inputs(protocol,freeze,directory(explorer_root))
    result=outcomes(root,trial,protocol,bound,packages,freeze_raw)
    result['full_frozen_input_admission']=True
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--explorer-root',required=True,type=Path)
    args=parser.parse_args();print(json.dumps(validate(explorer_root=args.explorer_root),sort_keys=True))


if __name__=='__main__':main()
