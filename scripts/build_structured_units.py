#!/usr/bin/env python3
"""Build an additive source-led unit catalogue; earlier releases stay frozen."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path

from build_bundle import ROOT, canonical
from build_context_corpus import binding, deterministic_gzip
from build_logical_units import Inputs, check_override, make_record, require, sha, admitted_output
from logical_unit_authoring import load_overrides
from manual_structure import segment_source, VERSION
from build_pdf_structure import DEFAULT_OUTPUT as STRUCTURE_OUTPUT, run as verify_pdf_structure

OUTPUT = 'structured-units'
KINDS = {'reference-table':'table', 'example-group':'compound', 'reserved':'section',
         'contents':'section', 'annotation':'cross-reference', 'contact':'section',
         'document-notice':'section', 'reference-material':'section'}


def compile_units(root=ROOT):
    inputs = Inputs(root)
    verify_pdf_structure(root=root,output=STRUCTURE_OUTPUT)
    config = json.loads(inputs.read('context/corpus-sources.json'))
    overrides = load_overrides(inputs)
    specs = {(d['family'], d['document_id']): d for d in overrides['documents']}
    for path in ('scripts/build_structured_units.py','scripts/manual_structure.py',
                 'scripts/pdf_structure_alignment.py','scripts/build_logical_units.py',
                 'scripts/build_context_corpus.py','manual-guide/manifest.json',STRUCTURE_OUTPUT+'/manifest.json','uv.lock'):
        inputs.read(path)
    outputs, records, documents, groups = {}, [], [], []
    for source in config['sources']:
        family=source['id']; inventory_raw=inputs.read(source['inventory'], limit=16*1024*1024)
        inventory=json.loads(inventory_raw); counts=Counter()
        require(not inventory.get('failures'), 'Incomplete frozen source inventory')
        for doc in sorted(inventory['documents'],key=lambda d:d['id']):
            inputs.read(doc['pdf_path'],doc['sha256'],doc['size_bytes'])
            extracted=json.loads(inputs.read(doc['pages_path'],doc['pages_sha256'],limit=32*1024*1024))
            require(extracted['source_sha256']==doc['sha256'],'Extraction/PDF identity differs')
            pages=extracted['pages']
            require(len(pages)==doc['pages'] and all(p['url']==doc['url']+f"#page={p['page']}" for p in pages),'Source page census/URL mismatch')
            # Actual source-declared structure and its retained tool observation
            # are separate from both the original acquisition and this parser.
            sidecar_path=f"{STRUCTURE_OUTPUT}/{family}/{doc['id']}.structure.json"
            sidecar=json.loads(inputs.read(sidecar_path,limit=64*1024*1024))
            for field in ('tree','stderr'):
                ref=sidecar[field]
                inputs.read(ref['path'],ref['sha256'],ref['bytes'],limit=16*1024*1024)
            spec=specs.get((family,doc['id']))
            authored=check_override(doc,pages,spec,sha(inventory_raw)) if spec else []
            units, structure=segment_source(family,doc,pages,authored)
            catalogue=[]; empty_text_spans=[]
            for unit in units:
                if not unit['text'].strip():
                    empty_text_spans.extend(unit['spans'])
                    continue
                if not unit.get('authored'):
                    heading=unit['heading_path'][-1] if unit['heading_path'] else unit['role'].replace('-',' ')
                    labels=', '.join(unit['paragraph_labels'])
                    unit['label']=(labels+' — '+heading if labels else heading)[:max(30,495-len(doc['title']))]
                    unit['kind']=KINDS.get(unit['role'],unit['role'])
                    if unit['kind'] not in {'paragraph','section','table','compound','cross-reference','unresolved-fragment'}:
                        unit['kind']='unresolved-fragment'
                record=make_record(family,doc,pages,unit,('v1-'+sha(canonical({'pdf':doc['sha256'],'pages':doc['pages_sha256']}))[:16]) if unit.get('authored') else VERSION)
                records.append(record)
                catalogue.append({**unit,'id':record['id'],'record_sha256':sha(canonical(record))})
            count=Counter(documents=1,pages=len(pages),nonempty_pages=sum(bool(p['text'].strip()) for p in pages),
                          empty_pages=sum(not p['text'].strip() for p in pages),source_text_bytes=sum(len(p['text'].encode()) for p in pages),
                          units=len(catalogue),empty_text_spans=len(empty_text_spans),authored_units=sum(bool(u.get('authored')) for u in units),
                          tagged_blocks_matched=structure.get('pdf_structure',{}).get('matched_count',0),
                          tagged_blocks_unmatched=len(structure.get('pdf_structure',{}).get('unmatched',[])))
            for unit in units: count['role_'+unit['role']]+=1
            counts.update(count)
            value={'schema':'okf-dwp-structured-document.v1','family':family,'document_id':doc['id'],
                   'source':{'url':doc['url'],'sha256':doc['sha256'],'pages_sha256':doc['pages_sha256'],
                             'role':doc.get('role'),'kind':doc.get('kind'),'chapter':doc.get('chapter')},
                   'counts':dict(count),'units':catalogue,'empty_text_spans':empty_text_spans,'structure':structure,
                   'limitations':['Complete source-byte accounting is not complete legal applicability or specialist acceptance.']}
            decoded=canonical(value); raw=deterministic_gzip(decoded)
            path=f"documents/{family}/{doc['id']}.json.gz"
            outputs[path]=raw
            # A catalogue is a build/review artefact, not a runtime shard. Large
            # catalogues retain bounded input enforcement but do not masquerade
            # as transport records.
            ref={'path':path,'bytes':len(raw),'sha256':sha(raw),'encoding':'gzip',
                 'decoded_bytes':len(decoded),'decoded_sha256':sha(decoded)}
            documents.append({'family':family,'document_id':doc['id'],**ref,'counts':dict(count)})
        groups.append({'id':family,'inventory':{'repository_path':source['inventory'],'sha256':sha(inventory_raw)},
                       'source_collection_url':source['collection_url'],'counts':dict(counts)})
    records.sort(key=lambda r:r['id'])
    require(len(records)==len({r['id'] for r in records}),'Duplicate structured record identity')
    shards=[]; chunk=[]; size=0; ordinal=0
    def emit():
        nonlocal chunk,size,ordinal
        if not chunk:return
        decoded=canonical({'schema':'okf-context-records.v1','first_ordinal':ordinal,'records':chunk})
        raw=deterministic_gzip(decoded);path=f'records/{len(shards):04d}.json.gz';outputs[path]=raw
        shards.append({**binding(path,raw,decoded),'first_ordinal':ordinal,'count':len(chunk),
                       'first_id':chunk[0]['id'],'last_id':chunk[-1]['id']})
        ordinal+=len(chunk);chunk=[];size=0
    for record in records:
        n=len(canonical(record))
        if chunk and (len(chunk)>=128 or size+n>1024*1024):emit()
        chunk.append(record);size+=n
    emit()
    totals=Counter()
    for group in groups:totals.update(group['counts'])
    identity={'version':VERSION,'inputs':sorted(inputs.files.values(),key=lambda r:r['path'])}
    manifest={'schema':'okf-dwp-structured-units.v1','snapshot':'dwp-structured-units-'+sha(canonical(identity))[:20],
              'source_groups':groups,'counts':dict(totals),'documents':documents,'records':{'count':len(records),'shards':shards},
              'inputs':identity['inputs'],'source_instructions_inert':True,
              'review':{'specialist_accepted':False,'legal_answerability':'not-established'},
              'accounting':'Exact non-overlapping original UTF-8 bytes; PDF tags propose roles and headings, not legal effects.'}
    outputs['manifest.json']=canonical(manifest)
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    outputs=compile_units();directory=ROOT/OUTPUT
    for name,data in outputs.items():
        path=admitted_output(directory,name)
        if args.check:require(path.is_file() and path.read_bytes()==data,'Stale structured unit output: '+name)
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    actual={p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}
    require(actual==set(outputs),'Unbound structured unit output')
    print(json.dumps({'status':'verified' if args.check else 'built',**json.loads(outputs['manifest.json'])['counts']}))

if __name__=='__main__':main()
