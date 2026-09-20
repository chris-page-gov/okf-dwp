#!/usr/bin/env python3
"""Compile additive, source-bound staff semantics without modifying frozen releases."""
from __future__ import annotations
import argparse
from collections import Counter, deque
from copy import deepcopy
import json
import re
from urllib.parse import urlsplit
from pathlib import Path

from build_bundle import ROOT, BASE, REPO, OGL, canonical, digest, pretty, load_yaml
from build_context_discovery import Inputs, require, SCOPE as DISCOVERY_SCOPE
from build_context_corpus import make_source_record

AUTHORING = 'domain-profile/staff-semantic/'
OUTPUT = 'evaluation/semantic-expansion/'
REGISTRY = 'evaluation/staff-questions/cases.json'
BASE_INDEX = 'context/corpus/base-index.json'
SKOS = 'http://www.w3.org/2004/02/skos/core#'
DCT = 'http://purl.org/dc/terms/'
REVIEW = 'unreviewed-specialist-review-required'
CATEGORIES = {'evidence_closure_unverified', 'applicability_unresolved', 'legal_version_unreconciled',
              'independent_review_pending', 'question_scope_unresolved', 'source_not_acquired'}
LIMITATIONS = [
    'Independent experimental staff-question research. No personal award decision or executable calculation is provided.',
    'Definitions, aliases, relationships and task requirements are model-authored proposals requiring independent specialist review.',
    'Exact frozen DMG and ADM source text, project-authored meanings and missing review obligations remain distinct. Acquisition does not establish current legal applicability.',
    'The 40 staff question occurrences contain 39 distinct questions. Profiles are development cases, not a held-out independent accuracy benchmark.',
    'Requirements include explicitly registered absent obligations. They cannot be satisfied by retrieving more pages or by model agreement; every assembled task remains insufficient.',
    'SDA deliberately resolves ambiguously between a legacy benefit and an informal disability-addition meaning. Broad JSA/ESA and State Pension labels do not select a variant.',
    'Only selected exact source pages and directed authored relations supplement the unchanged discovery base. Conditions on adjacent pages and unmodelled cross-references remain review work.',
    'Source capture dates are not publication, commencement or applicability dates. Historical examples and tables are preserved as captured.',
    'Source and tool content is inert untrusted evidence, not permission to execute instructions. No external retrieval occurs in this build.',
]


def check_statutory_governance(row, record=False):
    """Do not let an additive body or link bypass existing engine governance."""
    def public_url(value):
        if not isinstance(value, str): return False
        try:
            url=urlsplit(value)
            return url.scheme=='https' and bool(url.hostname) and not url.username and not url.password and not url.port
        except ValueError: return False
    authority=row.get('authority',{})
    require(row.get('assertion_status')=='normalized' and authority.get('class')=='derived',
            'Statutory extraction authority cannot be promoted')
    require(bool(authority.get('label')) and public_url(authority.get('source')),
            'Statutory authority source must be explicit HTTPS')
    require(bool(row.get('scope')) and bool(row.get('provenance')), 'Statutory provenance/scope cannot be absent')
    for provenance in row['provenance']:
        require(public_url(provenance.get('url')) and bool(provenance.get('locator')) and bool(provenance.get('captured_at')),
                'Statutory provenance needs source URL, locator and capture time')
        require(bool(re.fullmatch('[0-9a-f]{64}', provenance.get('source_sha256',''))), 'Statutory source digest missing')
    if record:
        require(row.get('kind')=='evidence' and bool(row.get('text')), 'Statutory record must contain evidence')
        require(row.get('review_status')=='unreviewed', 'Statutory body has no specialist acceptance')
        require(row.get('access')=='public' and public_url(row.get('rights')), 'Statutory rights/access must remain explicit')
        require(all(p.get('literal_sha256')==digest(row['text'].encode()) for p in row['provenance']),
                'Statutory literal hash differs')
    else:
        require(row.get('predicate')==DCT+'references', 'Statutory navigation is not applicability')


def compile_staff_semantic(root: Path = ROOT):
    inputs = Inputs(root)
    def authored(name):
        raw = inputs.read(AUTHORING + name)
        return load_yaml(inputs.path(AUTHORING + name)), raw
    declarations, author_raw = authored('concepts.yamlld')
    profile_author, profile_raw = authored('profiles.yamlld')
    require(declarations.get('schema') == 'okf-dwp-staff-semantic-authoring.v1', 'Unknown staff semantic authoring')
    require(profile_author.get('schema') == 'okf-dwp-staff-task-profiles.v1', 'Unknown staff task profiles')
    require(declarations['assertion_status'] == 'model-derived', 'Authored semantics cannot acquire official authority')
    registry = json.loads(inputs.read(REGISTRY))
    old = json.loads(inputs.read(BASE_INDEX))
    records = {row['id']: deepcopy(row) for row in old['records']}
    assertions = {row['id']: deepcopy(row) for row in old['assertions']}
    # Compact only the repeated generic discovery scope in this new view.
    # Specialised custody scopes and all evidence records remain byte-equivalent.
    compact_scope = 'Unreviewed DMG research; no legal completeness, current applicability or individual entitlement assurance.'
    compacted=[]
    for row in assertions.values():
        if row['scope']==DISCOVERY_SCOPE:
            row['scope']=compact_scope;compacted.append(row['id'])
    source_candidates = {c['id']: c for c in registry['source_candidates']}
    inventories = {}
    documents = {}
    for family, inventory_path in [('dmg','source/full-dmg-2026-09-15/inventory.json'), ('adm','source/adm-2026-09-19/inventory.json')]:
        inventories[family] = json.loads(inputs.read(inventory_path))
        for doc in inventories[family]['documents']:
            documents[family,doc['id']] = doc
    routes = {row['id']: row for row in json.loads(inputs.read('full-dmg/data/source-documents.json'))['documents']}
    page_cache, bound_pages = {}, {}
    def page(family, doc_id, number, anchor=None):
        doc = documents[family,doc_id]
        if (family,doc_id) not in page_cache:
            inputs.read(doc['pdf_path'], doc['sha256'], doc['size_bytes'])
            parsed = json.loads(inputs.read(doc['pages_path'],doc['pages_sha256']))
            require(parsed['source_sha256'] == doc['sha256'] and len(parsed['pages']) == doc['pages'], 'Source extraction identity changed')
            page_cache[family,doc_id] = parsed['pages']
        source = page_cache[family,doc_id][number-1]
        require(source['page'] == number and source['url'] == doc['url'] + f'#page={number}', 'Page locator mismatch')
        require(bool(source['text'].strip()), 'Empty source cannot be evidence')
        require(anchor is None or anchor in source['text'], 'Source anchor absent from exact page')
        route = routes[doc_id]['page_routes'][number-1] if family == 'dmg' else f'page/adm/{doc_id}/{number:04d}'
        record = make_source_record(family,doc,source,route)
        if record['id'] in records:
            require(records[record['id']]['kind']=='evidence' and records[record['id']]['text']==source['text'], 'Preserved source evidence differs')
        else: records[record['id']]=record
        binding = {'id':record['id'],'route':route,'family':family,'document_id':doc_id,'source_url':source['url'],
                   'source_sha256':doc['sha256'],'pages_path':doc['pages_path'],'pages_sha256':doc['pages_sha256'],
                   'page':number,'literal_sha256':digest(source['text'].encode()),'captured_at':doc['observed_at'],
                   'source_dates':doc['document_dates'],'source_role':doc['role'],'legal_status':doc['legal_status']}
        bound_pages[record['id']]=binding
        return records[record['id']], binding
    candidate_records={}
    for key,c in source_candidates.items():
        rec,binding=page('dmg',c['document_id'],c['page'],c['anchor'])
        require(rec['id']==c['record_id'] and binding['source_sha256']==c['source_sha256'] and binding['literal_sha256']==c['literal_sha256'], 'Candidate differs from frozen evidence')
        candidate_records[key]=rec['id']
    concepts={}; catalogue=[]; replacements=[]
    for node in declarations['@graph']:
        require(node['key'] not in concepts and node['@id']==BASE+'id/'+node['route'], 'Duplicate/invalid concept identity')
        require(node['review_status']==REVIEW and node['source_candidates'] or node.get('additional_sources'), 'Concept needs source evidence')
        require(node['review_status']==REVIEW, 'Concept review status cannot be promoted')
        support=[candidate_records[c] for c in node['source_candidates']]
        for extra in node.get('additional_sources',[]):
            rec,_=page(extra['family'],extra['document_id'],extra['page'],extra['anchor']); support.append(rec['id'])
        concepts[node['key']]=node['@id']
        old_record=records.get(node['@id'])
        text=node['definition']
        provenance=[{'url':REPO+'/blob/main/'+AUTHORING+'concepts.yamlld','source_sha256':digest(author_raw),
                     'locator':'@graph/'+node['key']+'/definition','captured_at':declarations['authored_at'],'literal_sha256':digest(text.encode())}]
        record={'id':node['@id'],'route':node['route'],'label':node['label'],'kind':'concept','text':text,
                'aliases':node['aliases'],'assertion_status':'model-derived','authority':{'class':'model-assisted','label':'Staff-domain meaning proposal; specialist review required','source':REPO},
                'scope':declarations['scope']+' Concept role: '+node['@type'][1]+'.','provenance':provenance,
                'rights':REPO+'/blob/main/NOTICE.md','access':'public','review_status':REVIEW}
        if old_record: replacements.append({'id':node['@id'],'reason':'Refined neutral definition/aliases in additive projection only','previous_record_sha256':digest(canonical(old_record))})
        records[node['@id']]=record
        catalogue.append({**node,'evidence_ids':sorted(set(support)),'assertion_status':'model-derived','authority':'model-assisted'})
    alias_changes=[]
    for route,labels in declarations['alias_reassignments'].items():
        row=records[BASE+'id/'+route]; before=deepcopy(row.get('aliases',[]))
        row['aliases']=[a for a in before if (a if isinstance(a,str) else a['label']) not in labels]
        require(len(before)-len(row['aliases'])==len(labels), 'Alias reassignment must exactly match frozen source')
        alias_changes.append({'record_id':row['id'],'removed_aliases':labels,'reason':'Resolve neutral benefit first; custody-specific meanings retain their own labels and evidence.'})
    added=[]
    def edge(source,target,predicate,label,evidence_ids,locator):
        require(source in records and target in records and source!=target and evidence_ids, 'Invalid semantic association')
        require(predicate in {SKOS+'broader',SKOS+'related',DCT+'references',DCT+'requires'}, 'Unsupported predicate')
        for identifier in evidence_ids:require(records[identifier]['kind']=='evidence', 'Association must cite source evidence')
        identity=BASE+'id/assertion/staff-semantic/'+digest(canonical([source,predicate,target,label]))
        prov=[{'url':REPO+'/blob/main/'+AUTHORING+'concepts.yamlld','source_sha256':digest(author_raw),'locator':locator,'captured_at':declarations['authored_at']}]
        prov += [deepcopy(records[i]['provenance'][0]) for i in evidence_ids[:5]]
        row={'id':identity,'source':source,'target':target,'predicate':predicate,'label':label,'assertion_status':'model-derived',
             'authority':{'class':'model-assisted','label':'Source-backed conceptual association proposal, not a legal implication','source':REPO},
             'scope':declarations['scope'],'provenance':prov}
        require(identity not in assertions,'Duplicate generated assertion');assertions[identity]=row;added.append(identity)
        return row
    for node in catalogue:
        for ev in node['evidence_ids']:
            edge(node['@id'],ev,DCT+'references','Inspect the exact source context for '+node['label'],[ev],'@graph/'+node['key']+'/source-selection')
    for i,r in enumerate(declarations['relationships']):
        evidence_ids=[candidate_records[c] for c in r['source_candidates']]
        if r.get('source_concept_evidence'):
            evidence_ids += next(n['evidence_ids'] for n in catalogue if n['key']==r['source_concept_evidence'])
        edge(concepts[r['source']],concepts[r['target']],SKOS+r['predicate'].split(':')[1],r['statement'],evidence_ids,f'relationships/{i}')
    # Adjacent-page locators remain explicit in the review catalogue. The small
    # semantic base does not add every neighbour: the full corpus still contains
    # them, and the unverified closure obligations prevent a completeness claim.
    for binding in bound_pages.values():
        doc=documents[binding['family'],binding['document_id']]
        binding['adjacent_pages']=[{'page':n,'url':doc['url']+f'#page={n}',
                                   'status':'available-in-full-corpus-not-assumed-selected'}
                                  for n in (binding['page']-1,binding['page']+1) if 1<=n<=doc['pages']]
    # Only verified provision references enter this index. They are scope
    # metadata, never statutory-body evidence or a satisfied legal requirement.
    legal_path='evaluation/legal-reconciliation/assertions.json'
    legal_raw=inputs.read(legal_path)
    legal=json.loads(legal_raw)['assertions']
    legal_nodes={};legal_groups={};legal_by_case={}
    for item in legal:
        source=BASE+'id/'+item['source'];target=BASE+'id/'+item['target'];e=item['evidence']
        require(source in records and records[source]['kind']=='evidence','Legal reference lacks selected source')
        require(records[source]['text'][e['start']:e['end']]==e['literal'] and digest(e['literal'].encode())==e['literal_sha256'],'Legal citation exact span differs')
        require(digest(records[source]['text'].encode())==e['page_literal_sha256'],'Legal citation page hash differs')
        metadata_raw=inputs.read(e['observation_path']);metadata=json.loads(metadata_raw)
        require(metadata['status']=='identifier-verified' and metadata['metadata']['target_identifier_observed'] is True,'Legal target is not verified')
        require(metadata['target']==item['target'].removeprefix('legal/'),'Legal target identity differs')
        legal_nodes[target]=(item,metadata,metadata_raw)
        legal_groups.setdefault((source,target),[]).append(item)
        for cid in item['case_ids']:legal_by_case.setdefault(cid,set()).add(target)
    for target,(item,metadata,metadata_raw) in legal_nodes.items():
        observed=metadata['receipt']['observed_at']
        url=metadata['receipt']['requested_url'].removesuffix('/data.xml')
        records[target]={'id':target,'route':item['target'],'label':metadata['metadata']['title']+' — '+metadata['target'].split('/',3)[-1],
            'kind':'scope','text':'Verified provision reference: '+metadata['metadata']['document_identifier']+'. Metadata only; statutory text and applicability are not established.',
            'assertion_status':'normalized','authority':{'class':'derived','label':'Reference metadata only','source':url},
            'scope':'Citation navigation; not statutory evidence or legal applicability.','rights':OGL,'access':'public','review_status':'reference-only-unreviewed',
            'provenance':[{'url':REPO+'/blob/main/'+item['evidence']['observation_path'],'source_sha256':digest(metadata_raw),
                'locator':'metadata/document_identifier','captured_at':observed,'source_date':metadata['requested_version_date'],
                'source_date_kind':'Requested version; not commencement or applicability'}]}
    legal_edges=[]
    for (source,target),items in sorted(legal_groups.items()):
        identity=BASE+'id/assertion/staff-legal/'+digest(canonical([source,DCT+'references',target]))
        source_binding=records[source]['provenance'][0]
        assertions[identity]={'id':identity,'source':source,'target':target,'predicate':DCT+'references','label':'Cites verified provision reference; applicability unreviewed',
            'assertion_status':'normalized','authority':{'class':'derived','label':'Literal citation normalisation','source':REPO},
            'scope':'Citation identity only; no legal implication.',
            'provenance':[{**source_binding,'locator':'Exact footnote spans '+', '.join(str(i['evidence']['start'])+':'+str(i['evidence']['end']) for i in items)}]}
        legal_edges.append(identity)
    # This additive release also carries selected statutory bodies. Verify the
    # separate producer and its retained source projections before admitting them;
    # reference metadata and actual body evidence remain different records.
    from build_legal_body_evidence import build as compile_legal_bodies
    body_outputs = compile_legal_bodies(root)
    body_path = 'domain-profile/legal-bodies/context-overlay.json'
    for path, expected in body_outputs.items():
        require(inputs.read(path) == expected, 'Stale legal body projection: ' + path)
    body = json.loads(body_outputs[body_path])
    require(body['schema'] == 'okf-legal-body-context-overlay.v1', 'Unknown legal body projection')
    for binding in body['bindings']:
        inputs.read(binding['path'], binding['sha256'])
    body_coverage = json.loads(body_outputs['domain-profile/legal-bodies/coverage.json'])
    body_ids = []
    for record in body['records']:
        require(record['id'] not in records and record['kind'] == 'evidence', 'Duplicate or non-evidence statutory record')
        check_statutory_governance(record, record=True)
        records[record['id']] = deepcopy(record); body_ids.append(record['id'])
    # A newly acquired cited provision can have verified metadata authoring but
    # no earlier staff-citation edge. Admit only its exact, source-bound metadata
    # identity as a separate scope record; never invent arbitrary graph endpoints.
    body_reference_ids=[]
    body_units={unit['record_id']:unit for unit in body_coverage['units']}
    body_sources={source['path']:source for source in body_coverage['source_responses']}
    for assertion in body['assertions']:
        if assertion['source'] in records: continue
        require(assertion['target'] in body_units, 'Missing statutory endpoint has no verified unit')
        unit=body_units[assertion['target']]
        source=body_sources[unit['source_projection']]
        require(assertion['source']==BASE+'id/legal/'+source['target'], 'Missing statutory endpoint is not the verified provision identity')
        metadata_raw=inputs.read(source['path'],source['sha256'])
        projection=json.loads(metadata_raw);metadata=projection['metadata'];observed=projection['receipt']['observed_at']
        require(metadata['target_identifier_observed'] is True and projection['target']==source['target'], 'Supplementary legal reference is not verified')
        identity=assertion['source'];url=projection['receipt']['requested_url'].removesuffix('/data.xml')
        records[identity]={'id':identity,'route':'legal/'+source['target'],
            'label':metadata['title']+' — '+source['target'].split('/',3)[-1],
            'kind':'scope','text':'Verified provision identity: '+metadata['document_identifier']+'. Metadata reference only; the statutory body is separately linked. Legal applicability remains unestablished.',
            'assertion_status':'normalized','authority':{'class':'derived','label':'Supplementary provision reference metadata only','source':url},
            'scope':'Source identity navigation, not a substantive legal proposition or applicability assessment.',
            'rights':OGL,'access':'public','review_status':'reference-only-unreviewed',
            'provenance':[{'url':REPO+'/blob/main/'+source['path'],'source_sha256':source['sha256'],
                'locator':'metadata/document_identifier','captured_at':observed,'source_date':projection['requested_version_date'],
                'source_date_kind':'Observed requested version identity; not commencement or applicability'}]}
        body_reference_ids.append(identity)
    body_edges = []
    for assertion in body['assertions']:
        require(assertion['id'] not in assertions and assertion['source'] in records and assertion['target'] in records, 'Invalid statutory body relationship')
        check_statutory_governance(assertion)
        assertions[assertion['id']] = deepcopy(assertion); body_edges.append(assertion['id'])
    body_by_case = {case['case_id']: case['selected_body_ids'] for case in body_coverage['cases']}
    require(len(body_by_case)==len(body_coverage['cases']) and set(body_by_case)<={case['id'] for case in registry['cases']}, 'Unknown or duplicate statutory case coverage')
    require(all(set(ids)<=set(body_ids) for ids in body_by_case.values()), 'Statutory profile references absent evidence')
    require(all(case['evidence_status']=='insufficient' for case in body_coverage['cases']), 'Statutory coverage cannot close staff obligations')
    outgoing={}
    for e in assertions.values():outgoing.setdefault(e['source'],[]).append(e)
    def route_path(seeds,target):
        queue=deque((seed,[seed],[]) for seed in sorted(seeds));visited=set()
        while queue:
            here,rs,es=queue.popleft()
            if here==target:return {'seed':rs[0],'records':rs,'assertions':es}
            if here in visited or len(es)>=3:continue
            visited.add(here)
            for e in sorted(outgoing.get(here,[]),key=lambda e:e['id']):queue.append((e['target'],rs+[e['target']],es+[e['id']]))
        return None
    expected_ids={c['id'] for c in registry['cases']}
    require({p['id'] for p in profile_author['profiles']}==expected_ids and len(profile_author['profiles'])==40, 'Profiles must cover all question occurrences exactly')
    profiles=[];requirements=[];obligations=[]
    cases={c['id']:c for c in registry['cases']}
    for spec in profile_author['profiles']:
        case=cases[spec['id']]
        require(spec['candidate_ids']==case['candidate_ids'] and spec['duplicate_of']==case['duplicate_of'] and spec['ambiguities']==case['ambiguities'], 'Profile rewrites source question register')
        require(spec['when_all'] and len(set(spec['when_all']))==len(spec['when_all']) and set(spec['when_all'])<=set(concepts), 'Unknown/duplicate profile trigger')
        seeds=[concepts[key] for key in spec['when_all']]
        missing=[]
        for obligation in spec['obligations']:
            require(obligation['category'] in CATEGORIES and obligation['status'] in {'candidate-evidence-only','not-established','not-reviewed'}, 'Unknown or promoted obligation')
            iri=BASE+'id/obligation/staff/'+spec['id']+'/'+obligation['category']+'/'+obligation['id']
            require(iri not in records,'Unresolved obligation must not masquerade as evidence')
            missing.append(iri);obligations.append({'@id':iri,'case_id':spec['id'],**obligation,'is_source_evidence':False})
        require(any(o['category']=='independent_review_pending' for o in spec['obligations']), 'Profile cannot silently close independent review')
        required=[candidate_records[c] for c in spec['candidate_ids']]
        paths=[p for target in required if (p:=route_path(seeds,target)) and p['assertions']]
        requirement={'id':BASE+'id/requirement/staff/'+spec['id'],'label':spec['id']+': '+case['required_evidence'][0],
                     'when_all':seeds,'required':required+missing,'required_paths':paths,
                     'scope':'Proposed review scope for '+spec['id']+'. '+case['question'],
                     'limitations':[o['category']+': '+o['label'] for o in spec['obligations']]+case['ambiguities']}
        requirements.append(requirement)
        profiles.append({'id':spec['id'],'question':case['question'],'duplicate_of':case['duplicate_of'],'section':case['section'],
                         'review_status':REVIEW,'evidence_status':'insufficient','when_all':seeds,
                         'candidate_ids':spec['candidate_ids'],'source_evidence_ids':required,'requirement_id':requirement['id'],
                         'obligation_ids':missing,'ambiguities':case['ambiguities'],'scope_gaps':case['scope_gaps'],
                         'required_evidence':case['required_evidence'],'measured_paths':paths,
                         'legal_reference_ids':sorted(legal_by_case.get(spec['id'],set())),
                         'legal_reference_status':'Verified identities only; legal-version and applicability obligations remain open',
                         'statutory_body_ids':body_by_case.get(spec['id'],[]),
                         'statutory_body_status':'Selected units acquired; version applicability, dependencies and specialist acceptance remain unresolved',
                         'assessment_boundary':'Development profile derived from known staff cases; candidate overlap is not an independent answer-accuracy test.'})
    inputs.read('scripts/build_staff_semantic.py')
    snapshot='dwp-staff-semantics-'+digest(canonical(sorted(inputs.files.values(),key=lambda x:x['path'])))[:20]
    index={'schema':'okf-context-index.v1','bundle':{**old['bundle'],'snapshot':snapshot},'scope':declarations['scope'],
           'limitations':LIMITATIONS + body['limitations'],'records':sorted(records.values(),key=lambda x:x['id']),
           'assertions':sorted(assertions.values(),key=lambda x:x['id']),'requirements':requirements}
    raw=canonical(index)
    require(len(raw)<=8*1024*1024,f'Additive staff index {len(raw)} exceeds Explorer 8 MiB semantic-index bound; split a new governed projection')
    outputs={OUTPUT+'assembly-index.json':raw,
             OUTPUT+'catalogue.json':pretty({'schema':'okf-dwp-staff-semantic-catalogue.v1','concepts':catalogue,'source_pages':sorted(bound_pages.values(),key=lambda x:x['id']),
                                            'new_assertion_ids':added,'legal_reference_ids':sorted(legal_nodes),'legal_assertion_ids':legal_edges,
                                            'statutory_body_ids':sorted(body_ids),'statutory_body_assertion_ids':sorted(body_edges),
                                            'statutory_supplementary_reference_ids':sorted(body_reference_ids),
                                            'scope_compaction':{'before':DISCOVERY_SCOPE,'after':compact_scope,'assertion_ids':compacted},
                                            'alias_reassignments':alias_changes,'refined_records':replacements,'limitations':LIMITATIONS}),
             OUTPUT+'profiles.json':pretty({'schema':'okf-dwp-staff-evidence-profiles.v1','question_occurrences':40,'unique_questions':39,'profiles':profiles,'obligations':obligations,'limitations':LIMITATIONS})}
    counts={'concepts_authored':len(concepts),'selected_source_pages':len(bound_pages),'new_assertions':len(added),'legal_reference_nodes':len(legal_nodes),'legal_reference_edges':len(legal_edges),
            'statutory_body_records':len(body_ids),'statutory_body_relationships':len(body_edges),
            'statutory_supplementary_references':len(body_reference_ids),
            'task_profiles':len(profiles),'open_obligations':len(obligations),'by_obligation_category':dict(sorted(Counter(o['category'] for o in obligations).items())),
            'base_records':len(old['records']),'records':len(records),'assertions':len(assertions),'index_bytes':len(raw)}
    outputs[OUTPUT+'build.json']=pretty({'schema':'okf-dwp-staff-semantic-build.v1','snapshot':snapshot,'counts':counts,
                'inputs':sorted(inputs.files.values(),key=lambda x:x['path']),
                'outputs':[{'path':p,'bytes':len(b),'sha256':digest(b)} for p,b in sorted(outputs.items())],
                'frozen_input_policy':'Preserve all frozen source and projection bytes; all refinements and alias reassignments are additive view changes only.'})
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    outputs=compile_staff_semantic()
    for name,raw in outputs.items():
        path=ROOT/name
        if args.check:require(path.is_file() and path.read_bytes()==raw,'Stale staff semantic output: '+name)
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    print(json.dumps({'status':'verified' if args.check else 'built',**json.loads(outputs[OUTPUT+'build.json'])['counts']}))


if __name__=='__main__':main()
