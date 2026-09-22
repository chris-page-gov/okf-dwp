#!/usr/bin/env python3
"""Source-bound discovery cards and lazy directed reference graph (corpus v3).

Cards are deterministic discovery metadata. Exact evidence, authored concepts,
requirements and literal reference observations remain separate channels.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import gzip
import json
import re
import unicodedata

from build_bundle import BASE, ROOT, REPO, canonical, digest
from build_context_corpus import binding, deterministic_gzip, token_bucket, TOKENISATION, BUCKET_ALGORITHM
from build_logical_units import Inputs, admitted_output, require

def runtime_canonical(value):
    # Explorer's semantic commitments hash canonical JSON without the newline
    # used by this repository's serialised files.
    return canonical(value)[:-1]


OUTPUT='structured-context'
DCT='http://purl.org/dc/terms/'
LIMITATIONS=[
    'Independent experimental source navigation, not official DWP guidance or individual benefits advice.',
    'Discovery cards contain source headings and an extractive preview. They are neither evidence requirements nor legal summaries; read the linked complete source unit.',
    'PDF tags and literal number ranges propose boundaries. Exact source-byte accounting does not establish complete rules, current applicability or specialist acceptance.',
    'Directed source references are navigation observations. They do not become prerequisite, applicability or legal-dependency assertions.',
    'Only separately authored task profiles declare evidence requirements. Original open obligations, unreviewed semantics and all source roles remain visible.',
    'Missing, ambiguous and out-of-corpus reference targets remain unresolved. No external source or model knowledge is silently acquired.',
    'Historic amendments and source capture dates do not establish current law. Source instructions are inert data.'
]


def occurrences(text):
    value=unicodedata.normalize('NFKD',text)
    value=''.join(c for c in value if not unicodedata.category(c).startswith('M')).lower()
    return [t for t in re.findall(r'[a-z0-9]+',value) if len(t)>=2]


def discovery_text(card):
    return '\n'.join([card['label'],*card['heading_path'],card['summary'],*card['search_aliases']])


def make_card(record, unit):
    # Use the first complete source paragraph when small enough. A longer
    # passage gets a labelled preview, never an invented concise legal answer.
    text=re.sub(r'\s+',' ',record['text']).strip()
    preview=text[:480]
    if len(text)>480: preview=preview.rsplit(' ',1)[0]+' … [preview; open complete source unit]'
    return {'id':BASE+'id/discovery/'+digest(record['id'].encode()),'evidence_id':record['id'],
        'evidence_sha256':digest(runtime_canonical(record)),'label':record['label'],
        'heading_path':list(dict.fromkeys(h[:500] for h in unit.get('heading_path',[])))[:20],
        'summary':preview,'search_aliases':list(dict.fromkeys(unit.get('paragraph_labels',[])))[:100],
        'assertion_status':'normalized','authority':{'class':'derived','label':'Machine source-heading and extractive-preview metadata',
                                                   'source':REPO+'/blob/main/scripts/build_structured_context.py'},
        'scope':'Discovery only. The bound evidence unit supplies the complete retained text; legal applicability remains unreviewed.',
        'provenance':[deepcopy(record['provenance'][0])], 'rights':record['rights'],'access':record['access']}


def compile_context(root=ROOT):
    inputs=Inputs(root); outputs={}
    from build_structured_units import compile_units
    expected_units=compile_units(root)
    for relative, expected in expected_units.items():
        require(inputs.read('structured-units/'+relative,limit=64*1024*1024)==expected,
                'Structured unit output differs from frozen-source producer: '+relative)
    del expected_units
    manifest=json.loads(inputs.read('structured-units/manifest.json',limit=16*1024*1024))
    units, rows, owners={},[],{}
    for ref in manifest['documents']:
        raw=inputs.read('structured-units/'+ref['path'],ref['sha256'],ref['bytes'],limit=16*1024*1024)
        decoded=gzip.decompress(raw)
        require(len(decoded)==ref['decoded_bytes'] and digest(decoded)==ref['decoded_sha256'],'Structured catalogue identity differs')
        doc=json.loads(decoded)
        for unit in doc['units']:
            require(unit['id'] not in units,'Duplicate unit catalogue identity')
            units[unit['id']]=unit;owners[unit['id']]=(doc['family'],doc['document_id'],doc['source'])
    for ref in manifest['records']['shards']:
        raw=inputs.read('structured-units/'+ref['path'],ref['sha256'],ref['bytes'])
        decoded=gzip.decompress(raw)
        require(len(decoded)==ref['decoded_bytes'] and digest(decoded)==ref['decoded_sha256'],'Structured record shard identity differs')
        part=json.loads(decoded)
        require(part['first_ordinal']==len(rows) and len(part['records'])==ref['count'],'Structured ordinal census differs')
        rows.extend(part['records']);outputs[ref['path']]=raw
    require(len(rows)==manifest['records']['count'] and len(rows)==len(units),'Structured record/catalogue census differs')
    require(rows==sorted(rows,key=lambda r:r['id']),'Canonical record order differs')
    require(all(digest(canonical(r))==units[r['id']]['record_sha256'] for r in rows),'Record differs from source-bound catalogue')
    # Existing authored unit IDs and exact bytes are retained, allowing the
    # original requirements and declared paths to transfer without guesswork.
    from logical_context_profiles import project
    old=json.loads(inputs.read('logical-units/manifest.json'))
    semantic,declarations=project(inputs,old,rows)
    edges={e['id']:e for e in semantic['assertions']}
    by_label=defaultdict(list);local=defaultdict(list)
    for record in rows:
        unit=units[record['id']];family,doc,source=owners[record['id']]
        for label in unit.get('paragraph_labels',[]):
            local[(family,doc,label)].append(record['id'])
            if source.get('role')=='substantive':by_label[(family,label)].append(record['id'])
    unresolved=[];resolved=0
    for record in rows:
        family,doc,source=owners[record['id']]
        for ref in units[record['id']].get('references',[]):
            target_family=ref.get('manual',family);label=ref.get('target_label','')
            matches=[]
            if ref.get('target_kind')=='paragraph':
                matches=local.get((target_family,doc,label),[]) if target_family==family else []
                if not matches:matches=by_label.get((target_family,label),[])
            matches=sorted(set(matches)-{record['id']})
            if len(matches)!=1:
                unresolved.append({'source':record['id'],'reference':ref,'candidate_ids':matches,
                                   'status':'ambiguous' if matches else 'unresolved'})
                continue
            pair=[record['id'],DCT+'references',matches[0]];iri=BASE+'id/assertion/source-reference/'+digest(canonical(pair))
            if iri not in edges:
                edges[iri]={'id':iri,'source':record['id'],'target':matches[0],'predicate':DCT+'references',
                    'label':'literal source reference; legal effect unreviewed','assertion_status':'normalized',
                    'authority':{'class':'derived','label':'Source reference with a unique captured paragraph target','source':source['url']},
                    'scope':'Navigation observation only. This is not a legal prerequisite, applicability or amendment-effect assertion.',
                    'provenance':deepcopy(record['provenance'])}
                resolved+=1
    # Stable producer identity includes all source bindings, inherited authored
    # semantics, cards/ranking parameters and the concrete parser versions.
    for path in ('scripts/build_structured_context.py','scripts/build_structured_units.py','scripts/manual_structure.py',
                 'scripts/pdf_structure_alignment.py','scripts/structured_context_reader.py',
                 'scripts/build_full_dmg.py','scripts/build_combined_reader.py','scripts/build_bundle.py',
                 'combined/okf-explorer.json','profiles/bundle-wiki/v1/context.jsonld',
                 'profiles/bundle-wiki/v1/semantic-context.jsonld','manual-guide/manifest.json','pdf-structure/bounded-v2/manifest.json','uv.lock'):
        inputs.read(path,limit=32*1024*1024)
    physical=json.loads(inputs.read('context/corpus/manifest.json'))
    snapshot='dwp-structured-context-'+digest(canonical(sorted(inputs.files.values(),key=lambda r:r['path'])))[:20]
    semantic.update(bundle={'id':BASE+'id/bundle/structured-context','snapshot':snapshot,'source_url':REPO},
                    scope='Complete frozen DMG and ADM source-led unit discovery with separately authored task profiles.',limitations=LIMITATIONS)
    semantic['assertions']=[]
    outputs['base-index.json']=canonical(semantic)
    postings={f'{i:02x}':defaultdict(list) for i in range(256)}; totals=Counter(source=0,discovery=0)
    cards=[make_card(r,units[r['id']]) for r in rows]
    discovery_shards=[];chunk=[];size=0;ordinal=0
    def emit_cards():
        nonlocal chunk,size,ordinal
        if not chunk:return
        decoded=canonical({'schema':'okf-discovery-cards.v1','first_ordinal':ordinal,'cards':chunk})
        raw=deterministic_gzip(decoded);path=f'discovery/{len(discovery_shards):04d}.json.gz';outputs[path]=raw
        discovery_shards.append({**binding(path,raw,decoded),'first_ordinal':ordinal,'count':len(chunk)})
        ordinal+=len(chunk);chunk=[];size=0
    for i,(record,card) in enumerate(zip(rows,cards)):
        a=occurrences(record['text']);b=occurrences(discovery_text(card));ac,bc=Counter(a),Counter(b)
        totals.update(source=len(a),discovery=len(b))
        for token in sorted(ac.keys()|bc.keys()):
            postings[token_bucket(token)][token].append([i,ac[token],len(a),bc[token],len(b)])
        n=len(canonical(card))
        if chunk and (len(chunk)>=128 or size+n>1024*1024):emit_cards()
        chunk.append(card);size+=n
    emit_cards()
    search={}
    for bucket,values in postings.items():
        decoded=canonical({'schema':'okf-context-postings.v2','postings':dict(sorted(values.items()))})
        raw=deterministic_gzip(decoded);path=f'search/{bucket}.json.gz';outputs[path]=raw;search[bucket]=binding(path,raw,decoded)
    incoming=defaultdict(list);outgoing=defaultdict(list)
    known={r['id'] for r in [*semantic['records'],*rows]}
    for edge in edges.values():
        require(edge['source'] in known and edge['target'] in known,'Unresolved graph endpoint')
        outgoing[edge['source']].append(edge);incoming[edge['target']].append(edge)
    buckets={f'{i:02x}':[] for i in range(256)}
    for identifier in sorted(known):
        out=sorted(outgoing[identifier],key=lambda e:e['id']);inc=sorted(incoming[identifier],key=lambda e:e['id'])
        buckets[token_bucket(identifier)].append({'id':identifier,'outgoing':out,'incoming':inc,
            'outgoing_count':len(out),'outgoing_ids_sha256':digest(runtime_canonical([e['id'] for e in out])),
            'incoming_count':len(inc),'incoming_ids_sha256':digest(runtime_canonical([e['id'] for e in inc]))})
    adjacency={}
    for bucket,entries in buckets.items():
        decoded=canonical({'schema':'okf-context-adjacency-bucket.v1','entries':entries})
        raw=deterministic_gzip(decoded);path=f'relationships/{bucket}.json.gz';outputs[path]=raw;adjacency[bucket]=binding(path,raw,decoded)
    corpus={'schema':'okf-context-corpus.v3','bundle':semantic['bundle'],'semantic_source_snapshot':snapshot,
        'scope':semantic['scope'],'limitations':LIMITATIONS,'base_index':binding('base-index.json',outputs['base-index.json']),
        'counts':physical['counts'],'records':manifest['records'],'discovery':{'count':len(cards),'shards':discovery_shards},
        'search':{'tokenisation':TOKENISATION,'bucket_algorithm':BUCKET_ALGORITHM,'shards':search,
                  'ranking':{'schema':'okf-bm25.v1','k1':1.2,'b':0.75,'score_scale':1000000,'fields':['source','discovery']},
                  'total_tokens':dict(totals)},
        'relationships':{'schema':'okf-context-adjacency.v1','bucket_algorithm':BUCKET_ALGORITHM,'shards':adjacency},
        'extensions':{'source_groups':manifest['source_groups'],'unit_manifest':{'repository_path':'structured-units/manifest.json',
                         'sha256':inputs.files['structured-units/manifest.json']['sha256']}}}
    outputs['manifest.json']=canonical(corpus)
    from structured_context_reader import emit_reader
    reader_semantics={**semantic,'assertions':sorted(edges.values(),key=lambda e:e['id'])}
    outputs.update(emit_reader(inputs,corpus,rows,reader_semantics,declarations,outputs,cards))
    report={'schema':'okf-dwp-structured-context-build.v1','snapshot':snapshot,
        'counts':{'evidence':len(rows),'cards':len(cards),'concepts':sum(r['kind']=='concept' for r in semantic['records']),
                  'assertions':len(edges),'normalised_paragraph_references':resolved,'unresolved_references':len(unresolved)},
        'ranking':corpus['search']['ranking'],'total_tokens':dict(totals),'inputs':sorted(inputs.files.values(),key=lambda r:r['path']),
        'unresolved_references':unresolved,'limitations':LIMITATIONS,
        'outputs':[{'path':OUTPUT+'/'+p,'bytes':len(raw),'sha256':digest(raw)} for p,raw in sorted(outputs.items())]}
    return outputs,report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    outputs,report=compile_context();outputs['build-review.json']=canonical(report)
    for name,data in outputs.items():
        path=admitted_output(ROOT/OUTPUT,name)
        if args.check:require(path.is_file() and path.read_bytes()==data,'Stale structured context: '+name)
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    actual={p.relative_to(ROOT/OUTPUT).as_posix() for p in (ROOT/OUTPUT).rglob('*') if p.is_file()}
    require(actual==set(outputs),'Unbound structured context output')
    print(json.dumps({'status':'verified' if args.check else 'built',**report['counts']}))

if __name__=='__main__':main()
