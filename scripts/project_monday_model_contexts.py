#!/usr/bin/env python3
"""Losslessly factor repeated JSON values; no evidence selection or model calls."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/'evaluation/model-comparison/household-2026-09-21/frozen'
CANDIDATE=ROOT/'evaluation/model-comparison/household-compact-v2-candidate'
REF='$okf_value_ref'


def raw(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def sha(value):return hashlib.sha256(value).hexdigest()


def frozen_bytes(relative,limit):
    path=ORIGINAL/relative
    if path.is_symlink() or not path.resolve().is_relative_to(ORIGINAL.resolve()) or not path.is_file() or path.stat().st_size>limit:
        raise ValueError('Unsafe or oversized frozen input')
    with path.open('rb') as stream:value=stream.read(limit+1)
    if len(value)>limit:raise ValueError('Frozen input exceeds bound')
    return value


def factor(value):
    counts=Counter();values={}
    def count(v):
        if isinstance(v,dict):
            if REF in v:raise ValueError('Reserved reference key occurs in original input')
            for child in v.values():count(child)
        elif isinstance(v,list):
            for child in v:count(child)
        if isinstance(v,(dict,list,str)):
            encoded=raw(v)
            if len(encoded)>=128:
                key=sha(encoded);counts[key]+=1;values[key]=v
    count(value)
    selected=sorted(k for k,n in counts.items() if n>=2 and (n-1)*len(raw(values[k]))>n*45+80)
    ids={k:f'v{i:04d}' for i,k in enumerate(selected)}
    def encode(v,own=None):
        if isinstance(v,(dict,list,str)):
            key=sha(raw(v))
            if key in ids and key!=own:return {REF:ids[key]}
        if isinstance(v,dict):return {k:encode(x) for k,x in v.items()}
        if isinstance(v,list):return [encode(x) for x in v]
        return v
    context=encode(value);pool={ids[k]:encode(values[k],k) for k in selected};needed=set()
    def visit(v):
        if isinstance(v,dict):
            if set(v)=={REF}:
                key=v[REF]
                if key not in needed:needed.add(key);visit(pool[key])
            else:
                for child in v.values():visit(child)
        elif isinstance(v,list):
            for child in v:visit(child)
    visit(context)
    return context,{k:pool[k] for k in sorted(needed)}


def expand(context,pool):
    seen=set();used=set()
    def decode(v,depth=0):
        if depth>96:raise ValueError('Reference nesting exceeds bound')
        if isinstance(v,dict):
            if REF in v:
                if set(v)!={REF} or v[REF] not in pool:raise ValueError('Invalid or missing reference')
                key=v[REF]
                if key in seen:raise ValueError('Reference cycle')
                seen.add(key);used.add(key);result=decode(pool[key],depth+1);seen.remove(key);return result
            return {k:decode(x,depth+1) for k,x in v.items()}
        if isinstance(v,list):return [decode(x,depth+1) for x in v]
        return v
    value=decode(context)
    if used!=set(pool):raise ValueError('Unreferenced extra dictionary material')
    return value


def produce():
    manifest_raw=frozen_bytes('manifest.json',262144);manifest=json.loads(manifest_raw)
    case_ids=[c['id'] for c in manifest['cases']]
    if len(case_ids)!=6 or len(set(case_ids))!=6:raise ValueError('Unexpected frozen case set')
    outputs={};census=[];bindings=[]
    for case in manifest['cases']:
        if not re.fullmatch(r'staff-\d{3}|control-unknown',case['id']) or case['path']!='contexts/'+case['id']+'.json':raise ValueError('Unsafe frozen case path')
        path=ORIGINAL/case['path'];source=frozen_bytes(case['path'],262144)
        if sha(source)!=case['sha256'] or len(source)!=case['bytes']:raise ValueError('Frozen context changed')
        value=json.loads(source);context,pool=factor(value)
        packet={'schema':'okf-lossless-model-context.v1','audit':{'path':str(path.relative_to(ROOT)),'path_kind':'repository-relative-existing-file','sha256':sha(source),'bytes':len(source),'context_id':value['context_id'],'manifest_path':str((ORIGINAL/'manifest.json').relative_to(ROOT)),'manifest_sha256':sha(manifest_raw),'public_immutable_url_status':'not-yet-published'},
                'reference_policy':'Replace each object containing only $okf_value_ref with the exact value under that ID in values; apply recursively. This preserves every original field and literal. The audit package is authoritative for byte identity; no external fetch is required to read this dictionary.',
                'values':pool,'context':context}
        reconstructed=raw(expand(context,pool))
        if reconstructed!=source:raise ValueError('Projection did not reconstruct exact frozen bytes')
        packet_raw=raw(packet);name='packets/'+case['id']+'.json';outputs[name]=packet_raw
        bindings.append({'id':case['id'],'path':name,'sha256':sha(packet_raw),'bytes':len(packet_raw),'original_context_sha256':sha(source),'exact_roundtrip':True,'dictionary_values':len(pool)})
        components={k:len(raw(v)) for k,v in sorted(value.items())}
        # Top-level keys/delimiters sit outside value encodings; nested measures
        # below are labelled as subsets and must not be added to these totals.
        census.append({'case_id':case['id'],'context_sha256':sha(source),'whole_package_bytes':len(source),'top_level_value_bytes':components,'top_level_keys_and_punctuation_bytes':len(source)-sum(components.values()),
            'nested_non_additive_subsets':{'selected_record_text_utf8_bytes':sum(len(x['record']['text'].encode()) for x in value['selected']),'selected_evidence_text_utf8_bytes':sum(len(x['record']['text'].encode()) for x in value['selected'] if x['record']['kind']=='evidence')},
            'projection_bytes':len(packet_raw),'byte_reduction':len(source)-len(packet_raw),'roundtrip_equal':True})
    summary={'schema':'okf-frozen-context-byte-census.v1','source_manifest_sha256':sha(manifest_raw),'producer_sha256':sha(Path(__file__).read_bytes()),'measurement':'UTF-8 compact canonical JSON. Top-level value bytes plus key/punctuation overhead equal whole-package bytes. Nested raw-text measures overlap selected value bytes and are not additive; JSON escaping also changes their representation size. Reduction includes the model packet dictionary and audit envelope. No token count or latency claim.','cases':census}
    outputs['byte-census.json']=json.dumps(summary,indent=2,ensure_ascii=False).encode()+b'\n'
    outputs['candidate-manifest.json']=json.dumps({'schema':'okf-lossless-model-projection-candidate.v1','phase':'unfrozen-awaiting-independent-review-and-root-approval','producer_sha256':sha(Path(__file__).read_bytes()),'original_manifest_sha256':sha(manifest_raw),'original_dwp_commit':manifest['dwp_commit'],'original_explorer_commit':manifest['explorer_commit'],'selection_or_summarisation':'none; exact reversible JSON-value interning only','packets':bindings},indent=2).encode()+b'\n'
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args();outputs=produce()
    if args.write:
        for name,data in outputs.items():
            target=CANDIDATE/name;target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists() and target.read_bytes()!=data:raise ValueError('Changed candidate exists; preserve it before a new projection')
            if not target.exists():target.write_bytes(data)
    else:
        for name,data in outputs.items():
            if (CANDIDATE/name).read_bytes()!=data:raise ValueError('Candidate projection differs: '+name)
    print(json.dumps({'status':'candidate-written' if args.write else 'candidate-verified','cases':6,'model_calls':0}))


if __name__=='__main__':main()
