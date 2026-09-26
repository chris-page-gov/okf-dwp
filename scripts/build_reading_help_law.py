#!/usr/bin/env python3
"""Validate and compile a small citation bridge; never decide applicability."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from acquire_legal_bodies import pretty, sha, OGL, OPAQUE
from build_legal_body_evidence import read_safe, verify_manifest
from project_reading_help_law import complete_text

ROOT=Path(__file__).resolve().parents[1]
AUTHORING='domain-profile/reading-help-law'
SOURCE='source/reading-help-law-2026-09-26'
PROJECTED=SOURCE+'-v2'
BASE='https://chris-page-gov.github.io/okf-dwp/id/'
REPO='https://github.com/chris-page-gov/okf-dwp/blob/main/'
DCT='http://purl.org/dc/terms/references'
LIMITATIONS=[
 'Navigation identifies cited sources, not legal applicability or satisfaction of an evidence requirement.',
 'The requested comparison date is 20 September 2026; capture date, commencement and case applicability are different.',
 'All observed section 70 geographical variants are separate. Selecting the applicable variant requires review.',
 'Selected complete provision text is not a complete dependency set, legal answer or specialist-reviewed explanation.',
 'Exact raw responses are hash-bound and cached locally. Public XML-tree projections omit opaque attributes with digests and are lossy.',
 'Malformed printed citations and unsupported benefit-rule explanations remain unresolved.',
 'The frozen earlier Pension Credit projections and their known limitations remain unchanged.',
]

def load(root,path):return json.loads(read_safe(root,path))

def source_support(root,support):
    raw=read_safe(root,support['pages_path'])
    if sha(raw)!=support['pages_sha256']:raise ValueError('Source pages hash mismatch')
    text=next(p['text'] for p in json.loads(raw)['pages'] if p['page']==support['page']).encode()
    a,b=support['start_utf8'],support['end_utf8']
    if not (0<=a<b<=len(text)):raise ValueError('Source span outside page')
    literal=text[a:b]
    if literal.decode()!=support['quote'] or sha(literal)!=support['literal_sha256']:raise ValueError('Source span binding mismatch')

def build(root=ROOT):
    seeds=load(root,AUTHORING+'/seeds.json');date=seeds['comparison_date']
    first=verify_manifest(root,SOURCE);second=verify_manifest(root,PROJECTED)
    if first['seed_sha256']!=sha(read_safe(root,AUTHORING+'/seeds.json')):raise ValueError('Seed hash mismatch')
    for field,path in [('acquisition_script_sha256','scripts/acquire_reading_help_law.py'),('projection_script_sha256','scripts/acquire_legal_bodies.py'),('metadata_parser_sha256','scripts/acquire_legal_reconciliation.py')]:
        if first[field]!=sha(read_safe(root,path)):raise ValueError('Acquisition method binding mismatch')
    if second['projector_sha256']!=sha(read_safe(root,'scripts/project_reading_help_law.py')):raise ValueError('Projector binding mismatch')
    if second['prior_snapshot']!=SOURCE or second['prior_manifest_sha256']!=sha(read_safe(root,SOURCE+'/manifest.json')):raise ValueError('Prior snapshot binding mismatch')
    census=load(root,SOURCE+'/request-census.json')
    if census['request_count']!=5 or len(census['requests'])!=5 or census['received_bytes']>33554432:raise ValueError('Acquisition budget differs')
    if any(r.get('response_bytes',r.get('received_bytes',0))>8388608 for r in census['requests']):raise ValueError('Response exceeds cap')
    rights=[load(root,SOURCE+'/rights/'+str(i)+'.json') for i in [1,2]]
    if not all(r['notice_observed'] and r['receipt']['status']=='observed' for r in rights):raise ValueError('Rights notices unresolved')
    records=[];assertions=[];work_ids={};bindings=[]
    def edge(source,target,label,provenance):
        assertions.append({'id':BASE+'reading-help-law-link/'+sha((source+'\0'+target).encode())[:24],
            'source':source,'target':target,'predicate':DCT,'label':label,'assertion_status':'normalized',
            'authority':{'class':'derived','label':'Source-backed citation navigation; applicability unresolved','source':REPO},
            'scope':'Navigation only; not an applicability assertion or a closed evidence requirement.','provenance':provenance})
    mappings=[]
    for work in seeds['works']:
        source_support(root,work['support']);ident=BASE+'reading-help-law/work/'+work['target'];work_ids[work['target']]=ident
        s=work['support'];provenance=[{'url':REPO+s['pages_path'],'source_sha256':s['pages_sha256'],'literal_sha256':s['literal_sha256'],
            'locator':f"PDF page {s['page']}, UTF-8 bytes {s['start_utf8']}:{s['end_utf8']}"}]
        mappings.append({**work,'record_id':ident,'assertion_status':'normalized','applicability':'unresolved'})
        records.append({'id':ident,'route':'reading-help-law/work/'+work['target'],'label':work['title'],'kind':'scope',
            'text':work['abbreviation']+' — '+work['title'],'assertion_status':'normalized',
            'authority':{'class':'derived','label':'Source-backed abbreviation and work identity; unreviewed applicability','source':work['dated_official_url']},
            'scope':'Work identity and citation navigation only; full title comes from the frozen DWP abbreviation table.',
            'provenance':provenance,'review_status':'unreviewed','access':'public'})
    projections=[]
    for target in seeds['targets']:
        path=PROJECTED+'/provisions/'+target.replace('/','--')+'.json';raw=read_safe(root,path);d=json.loads(raw)
        original=load(root,SOURCE+'/provisions/'+target.replace('/','--')+'.json')
        if d['receipt']!=original['receipt'] or d['response_sha256']!=original['receipt']['response_sha256']:raise ValueError('Raw response identity mismatch')
        if d['metadata']['document_identifier']!='http://www.legislation.gov.uk/'+target+'/'+date:raise ValueError('Requested version mismatch')
        if d['target']!=target or d['status']!='all-observed-target-variants-retained' or not d['units']:raise ValueError('Incomplete projection')
        seen=set()
        for unit in d['units']:
            uri=unit['source_native_document_uri'];canonical='http://www.legislation.gov.uk/id/'+target
            expected='http://www.legislation.gov.uk/'+target+('' if unit['variant']=='unqualified-source-route' else '/'+unit['variant'])+'/'+date
            if uri!=expected or uri in seen or unit['canonical_identifier']!=canonical:raise ValueError('Variant identity mismatch')
            seen.add(uri)
            if unit['body_tree']['attributes'].get('DocumentURI')!=uri:raise ValueError('Source-native unit URI mismatch')
            text=complete_text(unit['body_tree'])
            if text!=unit['body_text'] or sha(text.encode())!=unit['body_text_sha256']:raise ValueError('Complete text/tree hash mismatch')
            ident=BASE+'reading-help-law/body/'+target+'/'+unit['variant']
            provenance=[{'url':unit['version_url'],'source_sha256':d['response_sha256'],'literal_sha256':unit['body_text_sha256'],
                'locator':canonical+'; observed variant '+unit['variant'],'captured_at':d['receipt']['observed_at'],
                'source_date':date,'source_date_kind':'requested point-in-time version; not applicability'},
                {'url':REPO+path,'source_sha256':sha(raw),'locator':'Retained tree at source XML target ordinal '+str(unit['source_xml_ordinal'])}]
            work='/'.join(target.split('/')[:3]);label=next(w['title'] for w in seeds['works'] if w['target']==work)+' — '+target.split('/',3)[-1]+' ('+unit['variant']+')'
            records.append({'id':ident,'route':'reading-help-law/body/'+target+'/'+unit['variant'],'label':label,'kind':'evidence','text':text,
                'assertion_status':'normalized','authority':{'class':'derived','label':'Machine extraction of official source; applicability unreviewed','source':unit['version_url']},
                'scope':'Complete observed variant; not a complete legal dependency set. '+unit['applicability'],
                'provenance':provenance,'rights':OGL,'review_status':'unreviewed','access':'public'})
            edge(work_ids[work],ident,'Work contains observed provision variant; review applicability',provenance)
            projections.append({'record_id':ident,'target':target,'variant':unit['variant'],'url':unit['version_url'],'body_text_sha256':unit['body_text_sha256'],
                'characters':len(text),'projection_path':path,'dependency_status':'incomplete','review_status':'unreviewed'})
    # Reuse identities and bytes already admitted by the separate statutory producer.
    prior=load(root,'domain-profile/legal-bodies/context-overlay.json')
    if len(prior['records'])!=20 or len(prior['assertions'])!=43:raise ValueError('Existing statutory baseline changed; review reuse')
    reused=[]
    for record in prior['records']:
        target=record['id'].split('/legal-body/',1)[1];work='/'.join(target.split('/')[:3])
        if work in work_ids:
            edge(work_ids[work],record['id'],'Work contains previously retained statutory unit',record['provenance']);reused.append(record['id'])
    for path in [AUTHORING+'/seeds.json',SOURCE+'/manifest.json',PROJECTED+'/manifest.json','domain-profile/legal-bodies/context-overlay.json','scripts/build_reading_help_law.py']:
        bindings.append({'path':path,'sha256':sha(read_safe(root,path))})
    overlay={'schema':'okf-legal-body-context-overlay.v1','records':records,'assertions':assertions,'bindings':bindings,'external_record_ids':reused,'limitations':LIMITATIONS}
    catalogue={'schema':'okf-reading-help-law-bridge.v1','comparison_date':date,'work_mappings':mappings,'new_units':projections,
        'reuse':{'retained_units':20,'retained_provisions':16,'retained_relationships':43,'linked_existing_record_ids':reused},
        'requests':{'count':5,'bytes':census['received_bytes'],'additional_projection_requests':0},
        'applicability':'unresolved','evidence_requirement_status':'unchanged','deployment_status':'candidate-overlay; explicit consumer admission required',
        'bindings':bindings,'limitations':LIMITATIONS}
    return {AUTHORING+'/bridge.json':pretty(catalogue),AUTHORING+'/context-overlay.json':pretty(overlay)}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    for path,raw in build().items():
        if args.check:
            if read_safe(ROOT,path)!=raw:raise ValueError('Stale output: '+path)
        else:(ROOT/path).write_bytes(raw)
    print('PASS: four work mappings, four observed variants from three targets; earlier 20 statutory units preserved; applicability unresolved')
if __name__=='__main__':main()
