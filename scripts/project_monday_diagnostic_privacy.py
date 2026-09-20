#!/usr/bin/env python3
"""Publish a labelled privacy projection; retain original only in task-private tmp."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'validation/model-comparison/household-2026-09-21/diagnostics/claude-synthetic-reasoning/receipt.json'
DYNAMIC={'wire_tool_inputs','modelUsage','tool_inputs','tool_results'}


def sha(raw):return hashlib.sha256(raw).hexdigest()


def redact(value,parent=None):
    if isinstance(value,list):return [redact(x,parent) for x in value]
    if not isinstance(value,dict):return value
    return {(('key_sha256_'+sha(k.encode())) if parent in DYNAMIC or k.startswith('toolu_') else k):redact(v,k) for k,v in value.items()}


def produce(original):
    value=redact(json.loads(original))
    value['privacy_projection']={'schema':'okf-diagnostic-privacy-projection.v1','producer_sha256':sha(Path(__file__).read_bytes()),'original_sha256':sha(original),'original_bytes':len(original),'original_retained_publicly':False,'transformation':'Dynamic tool/model map keys are hashed; scalar values were already type-only. Original observation retained only outside the public repository. This is a derived projection, not the unchanged diagnostic receipt.'}
    return (json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');parser.add_argument('--private-original',type=Path,required=True);args=parser.parse_args();private=args.private_original
    if private.resolve().is_relative_to(ROOT.resolve()):raise ValueError('Original must remain outside the public repository')
    if args.write:
        if private.exists():raise ValueError('Private original already exists; do not overwrite')
        raw=PUBLIC.read_bytes();private.parent.mkdir(parents=True,exist_ok=True)
        with private.open('xb') as stream:stream.write(raw)
        PUBLIC.write_bytes(produce(raw))
    else:
        if PUBLIC.read_bytes()!=produce(private.read_bytes()):raise ValueError('Privacy projection differs')
    print(json.dumps({'status':'privacy-projected' if args.write else 'privacy-projection-verified','original_retained_publicly':False}))


if __name__=='__main__':main()
