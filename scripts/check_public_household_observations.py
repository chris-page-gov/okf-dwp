#!/usr/bin/env python3
"""Check retained public Reader bytes and immutable-source bindings; no network."""
import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path
import subprocess

from check_household_reader_observations import bounded_read, checked_directory

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'validation/household-reader-public/3ef0e786'
COMMIT = '3ef0e786e9a18e76fa17c7d925ff509d6d6c9f84'
MAX_MANIFEST = 128 * 1024
MAX_MEMBER = 10 * 1024 * 1024
MAX_GIT_BLOB = 8 * 1024 * 1024
APP = 'a551e1601d7722cea6edfe4e613a4fcc44191d8dfc74a0368b67b6a33f8d6f0c'

def sha(value): return hashlib.sha256(value).hexdigest()
def encoded(value): return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
def require(condition, message):
    if not condition: raise ValueError(message)

def execution_paths(base):
    base = checked_directory(base)
    result = []
    for entry in base.iterdir():
        require(not entry.is_symlink(), 'Observation entries must not be symlinks')
        if entry.name in {'README.md','artifact-manifest.json','local-comparison.json','.DS_Store'}:
            require(stat.S_ISREG(entry.lstat().st_mode), 'Metadata must be a regular file')
            continue
        require(re.fullmatch(r'attempt-[0-9]{2}-chrome', entry.name) and stat.S_ISDIR(entry.lstat().st_mode), 'Unexpected observation entry')
        for member in entry.iterdir():
            if member.name == '.DS_Store': continue
            require(stat.S_ISREG(member.lstat().st_mode), 'Observation member must be a regular file, never a symlink')
            result.append(member)
    require(len(result) <= 64, 'Too many observation files')
    return sorted(result)


def inventory(base=None):
    base = BASE if base is None else base
    result = []
    for path in execution_paths(base):
        raw = bounded_read(path, MAX_MEMBER)
        result.append({'path': path.relative_to(base).as_posix(), 'bytes': len(raw), 'sha256': sha(raw)})
    require(sum(row['bytes'] for row in result) <= 32 * 1024 * 1024, 'Observation total byte bound exceeded')
    return result


def verify_inventory(base, manifest):
    checked_directory(base)
    rows = manifest.get('files')
    require(isinstance(rows,list) and 0 < len(rows) <= 64, 'Invalid observation inventory')
    seen = set()
    for row in rows:
        require(isinstance(row,dict) and isinstance(row.get('path'),str) and re.fullmatch(r'attempt-[0-9]{2}-chrome/[a-z0-9-]+\.(?:json|mjs|png)',row['path']), 'Unsafe observation path')
        require(row['path'] not in seen, 'Repeated observation path'); seen.add(row['path'])
        require(type(row.get('bytes')) is int and 0 <= row['bytes'] <= MAX_MEMBER and re.fullmatch(r'[a-f0-9]{64}',row.get('sha256','')), 'Invalid observation size or hash')
        raw = bounded_read(base/row['path'], MAX_MEMBER)
        require(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Observation bytes differ')
    require(sum(row['bytes'] for row in rows) <= 32 * 1024 * 1024, 'Observation total byte bound exceeded')
    require({p.relative_to(base).as_posix() for p in execution_paths(base)} == seen, 'Observation inventory differs')


def load_inventory(base):
    base = checked_directory(base)
    manifest = json.loads(bounded_read(base/'artifact-manifest.json', MAX_MANIFEST))
    verify_inventory(base, manifest)
    return manifest


def git_blob(relative):
    require(isinstance(relative,str) and re.fullmatch(r'(?:combined|evaluation|domain-profile)/[a-zA-Z0-9_./-]+',relative) and '..' not in Path(relative).parts, 'Unsafe Git source path')
    ref = COMMIT + ':' + relative
    size_text = subprocess.check_output(['git','cat-file','-s',ref],cwd=ROOT,timeout=10,stderr=subprocess.DEVNULL)
    require(len(size_text) <= 24 and size_text.strip().isdigit(), 'Invalid Git blob size')
    size = int(size_text)
    require(size <= MAX_GIT_BLOB, 'Git blob exceeds byte limit')
    proc = subprocess.Popen(['git','cat-file','blob',ref],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    try:
        raw = proc.stdout.read(MAX_GIT_BLOB + 1)
        require(len(raw) <= MAX_GIT_BLOB, 'Git capture exceeds byte limit')
        require(proc.wait(timeout=10) == 0 and len(raw) == size, 'Git capture size or result differs')
        return raw
    finally:
        if proc.poll() is None: proc.kill(); proc.wait(timeout=5)
        proc.stdout.close()


def validate(base=None):
    base = checked_directory(BASE if base is None else base)
    old = json.loads(bounded_read(base/'attempt-01-chrome/failure.json', MAX_MEMBER))
    require(old['status'] == 'failed' and '20,044 in scope' in old['error'], 'Original failure must remain explicit')
    current = json.loads(bounded_read(base/'attempt-02-chrome/observation.json', MAX_MEMBER))
    require(current['status'] == 'passed' and current['content_commit'] == COMMIT, 'Public identity/status differs')
    require(current['network_mode'] == 'real-https-no-interception', 'Public mode differs')
    require(not current['network_errors'] and not current['console_errors'], 'Passing observation contains errors')
    cache = {}
    for name, observation in [('attempt-01-chrome', old), ('attempt-02-chrome', current)]:
        directory = base/name
        require(sha(bounded_read(directory/'executed-harness.mjs', MAX_MEMBER)) == observation['harness_sha256'], 'Executed harness differs')
        app_raw = bounded_read(directory/'app-manifest.json', MAX_MANIFEST); app = json.loads(app_raw)
        require(sha(app_raw) == APP == observation['app']['manifest_sha256'], 'Application differs')
        expected = {'https://chris-page-gov.github.io/okf-explorer/' + r['path']:r for r in app['materials']}
        require(len(expected) == 21 and len(observation['app']['verified_materials']) == 21, 'Full application verification absent')
        for row in observation['app']['verified_materials'] + observation['browser_loaded_app_materials']:
            require(row['url'] in expected and row['status'] == 200, 'Unknown application response')
            require(all(row[k] == expected[row['url']][k] for k in ['bytes','sha256']), 'Application material differs')
        require(any(row['url'].endswith('.js') for row in observation['browser_loaded_app_materials']), 'No actual loaded script')
        inputs = {r['path']:r for r in observation['inputs']}
        for relative, row in inputs.items():
            require(relative.startswith(('combined/','evaluation/','domain-profile/')) and '..' not in Path(relative).parts, 'Unsafe source path')
            if relative not in cache:
                raw = git_blob(relative)
                cache[relative] = {'sha256':sha(raw),'bytes':len(raw)}
            require(all(row[k] == cache[relative][k] for k in ['sha256','bytes']), 'Source input differs: '+relative)
        for row in observation['corpus_requests']:
            require(row['status'] == 200 and row['url'] == f'https://raw.githubusercontent.com/chris-page-gov/okf-dwp/{COMMIT}/combined/'+row['path'], 'Non-canonical corpus response')
            require(all(row[k] == inputs['combined/'+row['path']][k] for k in ['bytes','sha256']), 'Response/source mismatch')
    require(current['checks']['concept_facet']['count'] == 8, 'Concept count differs')
    require(current['checks']['source_family_and_timeline']['count'] == 20, 'Legislation count differs')
    require(current['checks']['source_family_and_timeline']['source_series'] == 0, 'Requested version became publication')
    require(current['checks']['care_home']['controlling_heading']['visible'], 'Controlling heading absent')
    require(current['checks']['statutory_graph']['incoming_and_outgoing_visible'], 'Graph path absent')
    comparison = []
    for name, key in [('care-home','care_home'),('sda','sda')]:
        raw = bounded_read(base/'attempt-02-chrome'/f'{name}-context.json', MAX_MEMBER); context = json.loads(raw)
        local_path = ROOT/'validation/household-reader/attempt-03-chrome'/f'{name}-context.json'
        local_raw = bounded_read(local_path, MAX_MEMBER); local = json.loads(local_raw)
        require(context['evidence_status'] == 'insufficient' and context['ai_answer'] is None and context['budget']['truncated'], 'Answer boundary changed')
        require(len(context['selected']) == current['checks'][key]['selected_records'] and len(context['relationships']) == current['checks'][key]['relationships'], 'Package counts differ')
        require(len(json.dumps(context,ensure_ascii=False,separators=(',',':')).encode()) <= context['budget']['max_bytes'], 'Package exceeds byte budget')
        require(context['context_id'] == current['checks'][key]['context_id'], 'Package identity differs')
        if key == 'sda':
            ambiguity = next(x for x in context['ambiguities'] if x['phrase'] == 'SDA')
            require(len(ambiguity['candidates']) == 2 and all(x not in {r['id'] for r in context['resolved_concepts']} for x in ambiguity['candidates']), 'SDA ambiguity lost')
        ignored = ['/binding/index_url','/budget/used_bytes','/context_id']
        record = {'case':name,'public_path':f'attempt-02-chrome/{name}-context.json','public_sha256':sha(raw),
                  'local_path':local_path.relative_to(ROOT).as_posix(),'local_sha256':sha(local_raw),
                  'public_context_id':context['context_id'],'local_context_id':local['context_id'],
                  'different_fields':ignored,'public_extra_bytes':context['budget']['used_bytes']-local['budget']['used_bytes']}
        for value in [context,local]:
            value.pop('context_id'); value['binding'].pop('index_url'); value['budget'].pop('used_bytes')
        require(context == local, 'Source or semantic content differs beyond the disclosed binding URL/derived identity')
        comparison.append(record)
    return {'schema':'okf-public-household-local-comparison.v1','method':'Offline exact JSON comparison; excludes only the three listed public-versus-fixture binding and derived fields. Does not change either original package.','cases':comparison}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write-manifest',action='store_true');args=parser.parse_args()
    checked_directory(BASE)
    if not args.write_manifest:
        load_inventory(BASE)
    comparison=encoded(validate()); manifest=encoded({'schema':'okf-public-household-artefacts.v1','files':inventory(),'comparison_sha256':sha(comparison)})
    outputs={'local-comparison.json':comparison,'artifact-manifest.json':manifest}
    for name,value in outputs.items():
        target=BASE/name
        if args.write_manifest:
            if target.exists():require(bounded_read(target,MAX_MANIFEST)==value,'Existing evidence differs; preserve before replacement')
            else:
                with target.open('xb') as stream:stream.write(value)
        else:require(bounded_read(target,MAX_MANIFEST)==value,'Retained inventory/comparison differs: '+name)
    print(json.dumps({'status':'verified','retained_execution_files':len(inventory()),'passed_public_journeys':1,'failed_harness_attempts_preserved':1,'model_or_network_calls':0}))
if __name__ == '__main__':main()
