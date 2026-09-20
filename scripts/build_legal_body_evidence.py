#!/usr/bin/env python3
"""Build additive statutory-unit evidence offline; never establish legal applicability."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
from acquire_legal_bodies import body_text, OPAQUE, pretty, validate_url
from build_bundle import yaml_bytes

ROOT = Path(__file__).resolve().parents[1]
AUTHORING = 'domain-profile/legal-bodies'
SOURCE = 'source/legal-bodies-2026-09-21-v2'
PRIOR = 'source/legal-bodies-2026-09-21'
BASE = 'https://chris-page-gov.github.io/okf-dwp/id/'
REPO = 'https://github.com/chris-page-gov/okf-dwp/blob/main/'
OGL = 'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'
PREDICATE = 'http://purl.org/dc/terms/references'
LIMITATIONS = [
    'Independent machine extraction of official statutory units, not specialist legal acceptance or an entitlement decision.',
    'Complete selected units are not a complete statute, dependency closure, consolidated amendment history or complete answer to any staff question.',
    'The requested version date is distinct from capture time, commencement and temporal or territorial applicability; missing extent remains unknown.',
    'Projected XML trees and normalised text are retained and hash checked; original HTTP response bodies are not retained and cannot be reconstructed from the lossy projection.',
    'Editorial commentary, omitted opaque attribute digests and restriction attributes remain separately inspectable in each source projection; absence of effect metadata does not mean no amendments.',
    'Literal SPC Regs s5 and s12(2)(d) remain unresolved; R(IS)1/99 judgment body and complete qualifying-benefit funding/timing rules are not supplied.',
    'Source text and links are inert evidence, not instructions or authority to execute code.',
]


def sha(data): return hashlib.sha256(data).hexdigest()


def read_safe(root: Path, relative: str, cap=10*1024*1024):
    name = PurePosixPath(relative)
    if name.is_absolute() or not name.parts or any(p in ('..', '.') for p in name.parts):
        raise ValueError('Unsafe relative path')
    path = root
    for part in name.parts:
        path /= part
        if path.is_symlink(): raise ValueError('Symlink rejected')
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > cap: raise ValueError('File type/byte limit rejected')
    data = path.read_bytes()
    if len(data) != info.st_size or len(data) > cap: raise ValueError('File changed/byte limit exceeded')
    return data


def json_file(root, relative): return json.loads(read_safe(root, relative))


def verify_manifest(root, source):
    manifest = json_file(root, source + '/manifest.json')
    seen = set()
    for row in manifest['files']:
        if row['path'] in seen: raise ValueError('Duplicate manifest path')
        seen.add(row['path'])
        raw = read_safe(root, source + '/' + row['path'])
        if len(raw) != row['bytes'] or sha(raw) != row['sha256']: raise ValueError('Source manifest binding mismatch')
        if OPAQUE.search(raw.decode()): raise ValueError('Opaque source identifier leaked')
    files = set()
    for p in (root/source).rglob('*'):
        if p.is_symlink(): raise ValueError('Source snapshot symlink rejected')
        # Finder housekeeping is not acquisition evidence and is gitignored.
        if p.is_file() and p.name != '.DS_Store': files.add(p.relative_to(root/source).as_posix())
    if files != seen | {'manifest.json'}: raise ValueError('Source snapshot census mismatch')
    return manifest


def verify_unit(unit):
    recomputed = body_text(unit['body_tree'])
    if recomputed != unit['body_text'] or sha(recomputed.encode()) != unit['body_text_sha256']:
        raise ValueError('Statutory body text/tree binding mismatch')
    if unit['canonical_identifier'] != 'http://www.legislation.gov.uk/id/' + unit['target']:
        raise ValueError('Unit identity mismatch')
    if not recomputed or len(recomputed) > 50000: raise ValueError('Unit text budget exceeded')


def verify_version(document, expected_date):
    expected='http://www.legislation.gov.uk/'+document['target']+'/'+expected_date
    if document['requested_version_date'] != expected_date or document['metadata']['document_identifier'] != expected:
        raise ValueError('Observed source version identity mismatch')
    for unit in document['units']:
        expected_unit='http://www.legislation.gov.uk/'+unit['target']+'/'+expected_date
        if unit['body_tree']['attributes'].get('DocumentURI') != expected_unit or unit['version_url'] != expected_unit.replace('http:','https:',1):
            raise ValueError('Observed unit version identity mismatch')


def extent(unit):
    return sorted({r['attributes']['RestrictExtent'] for r in unit['target_and_ancestor_restrictions'] if r['attributes'].get('RestrictExtent')})


def build(root=ROOT):
    seeds = json_file(root, AUTHORING + '/seeds.json')
    previous = verify_manifest(root, PRIOR)
    manifest = verify_manifest(root, SOURCE)
    if manifest['prior_snapshot'] != PRIOR or manifest['prior_manifest_sha256'] != sha(read_safe(root, PRIOR+'/manifest.json')):
        raise ValueError('Prior acquisition binding mismatch')
    for item in [previous, manifest]:
        if item['seed_sha256'] != sha(read_safe(root, AUTHORING+'/seeds.json')): raise ValueError('Seed binding mismatch')
        script = 'scripts/acquire_legal_bodies.py'
        if sha(read_safe(root, script)) != item['acquisition_script_sha256']:
            script = AUTHORING+'/acquisition-attempts/acquire-'+item['acquisition_script_sha256']+'.py'
        if sha(read_safe(root, script)) != item['acquisition_script_sha256']: raise ValueError('Acquisition producer binding mismatch')
        if sha(read_safe(root, 'scripts/acquire_legal_reconciliation.py')) != item['metadata_parser_sha256']: raise ValueError('Metadata parser binding mismatch')
    census = json_file(root, SOURCE+'/request-census.json')
    for reused in census['reused_prior_projections']:
        before = read_safe(root, PRIOR+'/'+reused['path'])
        after = read_safe(root, SOURCE+'/'+reused['path'])
        if before != after or sha(after) != reused['sha256']: raise ValueError('Reused projection changed')
    if census['count'] != len(census['requests']) or census['count'] > seeds['max_provision_requests'] + seeds['max_rights_requests']:
        raise ValueError('Request census/budget mismatch')
    registry = json_file(root, 'evaluation/staff-questions/cases.json')
    candidates = {x['id']:x for x in registry['source_candidates']}
    cases = {x['id']:x for x in registry['cases']}
    for q in seeds['questions']:
        if q['question'] != cases[q['id']]['question']: raise ValueError('Question changed')
    records, assertions, unit_rows, source_rows = [], [], [], []
    verified_page_files = {}
    known_ids = {x['@id'] for x in __import__('build_bundle').load_yaml(root/'domain-profile/legal-reconciliation/references.yamlld')['@graph']}
    def assertion(source, target, label, provenance, scope):
        ident = BASE+'legal-body-link/'+sha((source+'\0'+target+'\0'+label).encode())[:24]
        if any(x['id'] == ident for x in assertions): return
        assertions.append({'id':ident,'source':source,'target':target,'predicate':PREDICATE,'label':label,
            'assertion_status':'normalized','authority':{'class':'derived','label':'Project-authored source navigation; legal applicability unreviewed','source':'https://github.com/chris-page-gov/okf-dwp'},
            'scope':scope,'provenance':provenance})
    for seed in seeds['requests']:
        path = SOURCE+'/provisions/'+seed['target'].replace('/','--')+'.json'
        raw = read_safe(root,path); document=json.loads(raw)
        if document['target'] != seed['target'] or document['requested_version_date'] != seeds['requested_version_date']: raise ValueError('Requested target/version mismatch')
        verify_version(document,seeds['requested_version_date'])
        if document['status'] != 'selected-units-observed' or document['missing_units']: raise ValueError('Selected statutory units not complete')
        if [x['target'] for x in document['units']] != seed['units']: raise ValueError('Selected unit census mismatch')
        receipt=document['receipt']; validate_url(receipt['requested_url']); validate_url(receipt['resolved_url'])
        source_rows.append({'path':path,'sha256':sha(raw),'target':seed['target'],'receipt':receipt,
                            'selection_status':seed['selection_status'],'citation_links':seed['citation_links'],
                            'missing_commentary_ids':document['missing_commentary_ids'],'selected_commentary_count':len(document['selected_commentaries'])})
        for unit in document['units']:
            verify_unit(unit)
            observed_extent=extent(unit)
            record_id=BASE+'legal-body/'+unit['target']
            title=' / '.join(reversed(unit['ancestor_headings_nearest_first'])) or unit['target']
            label=unit['target']+' — '+title
            scope='Requested source version '+seeds['requested_version_date']+'. Observed extent attributes: '+(', '.join(observed_extent) or 'unknown')+'. Complete selected unit with whitespace-normalised numbered blocks; editorial commentary and amendment structure remain in the linked projection. Legal applicability, commencement, complete effects and specialist review remain unestablished.'
            provenance=[{'url':unit['version_url'],'source_sha256':receipt['response_sha256'],
                'literal_sha256':unit['body_text_sha256'],'locator':unit['canonical_identifier']+'; HTTP body hash observed, original response not retained publicly',
                'captured_at':receipt['observed_at'],'source_date':seeds['requested_version_date'],'source_date_kind':'requested point-in-time version; not commencement'},
                {'url':REPO+path,'source_sha256':sha(raw),'literal_sha256':unit['body_text_sha256'],
                'locator':'Retained lossy XML-tree projection; units target '+unit['target'],'captured_at':receipt['observed_at']}]
            records.append({'id':record_id,'route':'legal-body/'+unit['target'],'label':label,'kind':'evidence',
                'text':unit['body_text'],'assertion_status':'normalized',
                'authority':{'class':'derived','label':'Machine extraction from official legislation publication; unreviewed','source':unit['version_url']},
                'scope':scope,'provenance':provenance,'rights':OGL,'access':'public','review_status':'unreviewed'})
            parent_id=BASE+'legal/'+seed['target']
            if parent_id in known_ids:
                assertion(parent_id,record_id,'Official provision reference to selected statutory body',provenance,scope)
            links=[]
            for citation in seed['citation_links']:
                if sha(citation['literal'].encode()) != citation['literal_sha256']: raise ValueError('Literal citation hash mismatch')
                c=candidates[citation['source_candidate_id']]
                if c['literal_sha256'] != citation['page_literal_sha256'] or c['url'] != citation['source_url']: raise ValueError('Frozen citation page mismatch')
                if c['pages_path'] not in verified_page_files:
                    page_bytes=read_safe(root,c['pages_path'])
                    if sha(page_bytes) != c['pages_sha256']: raise ValueError('Frozen extracted-pages file binding mismatch')
                    verified_page_files[c['pages_path']]=json.loads(page_bytes)
                page_doc=verified_page_files[c['pages_path']]
                page=next(x for x in page_doc['pages'] if x['page']==c['page'])
                page_text=page['text']
                if citation['literal'] not in page_text or sha(page_text.encode()) != c['literal_sha256']: raise ValueError('Literal citation not found in frozen page')
                source_provenance=[{'url':c['url'],'source_sha256':c['source_sha256'],'literal_sha256':citation['literal_sha256'],
                    'locator':c['locator']+'; citation '+citation['citation_id'],'captured_at':c['captured_at']},provenance[1]]
                label_link='Literal DWP citation to provision; selected complete unit for inspection'
                if '/schedule/' in seed['target']:
                    label_link='Literal DWP citation to schedule; selected paragraph context, not an exact subparagraph mapping'
                assertion(c['record_id'],record_id,label_link,source_provenance,
                    'Navigation from preserved literal citation. '+seed['selection_status']+'. '+scope)
                links.append(citation['source_candidate_id'])
            unit_rows.append({'record_id':record_id,'target':unit['target'],'canonical_identifier':unit['canonical_identifier'],
                'version_url':unit['version_url'],'source_projection':path,'body_text_sha256':unit['body_text_sha256'],
                'body_text_characters':len(unit['body_text']),'observed_extent_attributes':observed_extent,
                'extent_status':'observed-attributes-only' if observed_extent else 'unknown',
                'target_and_ancestor_restrictions':unit['target_and_ancestor_restrictions'],
                'commentary_ids':unit['commentary_ids'],'citation_source_candidate_ids':sorted(set(links)),
                'case_ids':sorted({case for c in seed['citation_links'] for case in c['case_ids']}),
                'selection_status':seed['selection_status'],'applicability_review':'unreviewed'})
    navigation=json_file(root, AUTHORING+'/navigation.json')
    by_id={r['id']:r for r in records}
    for route in navigation['routes']:
        source=by_id[BASE+'legal-body/'+route['source']]
        target=by_id[BASE+'legal-body/'+route['target']]
        if route['literal_anchor'] not in source['text']: raise ValueError('Legal navigation literal anchor absent')
        assertion(source['id'],target['id'],'Statutory text explicitly references selected provision context',source['provenance'],
            'Preserved literal routing anchor: '+route['literal_anchor']+'. Navigation only; specialist applicability remains unreviewed.')
    bindings=[{'path':p,'sha256':sha(read_safe(root,p))} for p in [SOURCE+'/manifest.json',PRIOR+'/manifest.json',AUTHORING+'/seeds.json',
        'evaluation/staff-questions/cases.json','domain-profile/legal-reconciliation/references.yamlld',AUTHORING+'/navigation.json','scripts/build_legal_body_evidence.py']]
    overlay={'schema':'okf-legal-body-context-overlay.v1','records':records,'assertions':assertions,'bindings':bindings,'limitations':LIMITATIONS}
    coverage={'schema':'okf-legal-body-coverage.v1','requested_version_date':seeds['requested_version_date'],
        'engineering_status':'bounded-body-acquisition-and-offline-projection-complete','legal_acceptance':'pending-specialist-review',
        'requested_provisions':len(seeds['requests']),'selected_units':len(records),'assertions':len(assertions),
        'body_text_characters':sum(u['body_text_characters'] for u in unit_rows),
        'source_snapshots':[PRIOR,SOURCE],'source_responses':source_rows,'units':unit_rows,
        'unresolved_literal_policy':seeds['unresolved_literal_policy'],'additional_context_rationale':seeds['additional_context_rationale'],
        'cases':[{'case_id':q['id'],'question':q['question'],'evidence_status':'insufficient',
            'selected_body_ids':[u['record_id'] for u in unit_rows if q['id'] in u['case_ids']],
            'required_evidence':q['required_evidence'],'ambiguities':q['ambiguities'],
            'remaining':['Legal applicability and temporal/territorial reconciliation require specialist review.',
                         'Qualifying-benefit continuation, funding, transition and judicial dependencies are not closed.',
                         'No claimant circumstances or individual entitlement decision are established.']} for q in seeds['questions']],
        'limitations':LIMITATIONS,'bindings':bindings}
    graph=[]
    for record in records:
        graph.append({'@id':record['id'],'@type':'schema:CreativeWork','route':record['route'],'title':record['label'],
            'type':'Statutory body evidence','status':'draft','authority':record['authority']['label'],'review_status':'unreviewed',
            'resource':record['provenance'][0]['url'],'license':OGL,'description':record['scope'],'body':record['text'],
            'context_assembly':{'kind':'evidence','text':record['text'],'scope':record['scope']},
            'schema:about':{'@id':next(u['canonical_identifier'] for u in unit_rows if u['record_id']==record['id'])},
            'provenance':record['provenance']})
    for a in assertions:
        graph.append({'@id':a['id'],'@type':'rdf:Statement','rdf:subject':{'@id':a['source']},
                      'rdf:predicate':{'@id':a['predicate']},'rdf:object':{'@id':a['target']},
                      'rdfs:label':a['label'],'assertion_status':'normalized','scope':a['scope'],'provenance':a['provenance']})
    # A reified rdf:Statement describes a triple but does not assert it.
    # Emit matching direct navigation triples so the standalone graph is usable.
    direct={}
    for assertion_row in assertions:
        direct.setdefault(assertion_row['source'],set()).add(assertion_row['target'])
    for source,targets in sorted(direct.items()):
        graph.append({'@id':source,PREDICATE:[{'@id':target} for target in sorted(targets)]})
    return {AUTHORING+'/context-overlay.json':pretty(overlay),AUTHORING+'/coverage.json':pretty(coverage),
        AUTHORING+'/evidence.yamlld':yaml_bytes({'@context':'https://chris-page-gov.github.io/okf-explorer/profile/bundle-wiki/v1/context.jsonld','@graph':graph})}


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--check',action='store_true');args=parser.parse_args()
    outputs=build()
    for path,raw in outputs.items():
        if args.check:
            if read_safe(ROOT,path) != raw: raise SystemExit('STALE '+path)
        else: (ROOT/path).write_bytes(raw)
    print('PASS legal body evidence: 16 provision projections, 20 complete selected units, six staff cases; legal acceptance pending')

if __name__=='__main__': main()
