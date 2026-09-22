"""Preserve old research requirements; add guarded location-only unit navigation.

Geometric overlap does not satisfy the old page requirements, required paths or
open obligations. Complete units are navigation destinations, never substitute
proof. This module does not edit any source, unit, legacy profile or record.
"""
from copy import deepcopy
import re

from ruamel.yaml import YAML
from ruamel.yaml.tokens import AliasToken, AnchorToken, TagToken

from build_bundle import BASE, REPO, canonical, digest
from build_logical_units import require, strict_json

AUTHORING = 'domain-profile/structured-units/legacy-location-policy.yamlld'
SCHEMA = 'okf-dwp-location-migration-policy.v1'
CONTROLS = {'preserve_legacy_requirement_bytes': True, 'substitute_old_required_ids': False,
            'close_obligations': False, 'promote_boundary_review': False,
            'guard_all_profile_concepts': True, 'source_mapping': 'exact-frozen-byte-overlap-only',
            'legal_effect': 'not-established', 'missing_locations': 'report-unresolved',
            'infer_missing_route_from_profile_selection': True, 'infer_legal_support': False}
PAGE_PATH = re.compile(r'source/(?:pages|(?:full-dmg-[0-9-]+|adm-[0-9-]+)/pages)/[a-z0-9-]+\.json')
REVIEW = 'unreviewed-specialist-review-required'


def decode_profiles(raw):
    yaml = YAML(typ='safe'); yaml.version = (1, 2); yaml.allow_duplicate_keys = False
    text = raw.decode('utf-8')
    require(not any(isinstance(t, (AliasToken, AnchorToken, TagToken)) for t in yaml.scan(text)), 'Legacy profile aliases, anchors and tags are prohibited')
    result = yaml.load(text)
    require(isinstance(result, dict) and result.get('schema') == 'okf-dwp-staff-task-profiles.v1', 'Unexpected legacy authoring')
    return result


def compile_migration(policy, semantic, legacy, profiles, candidates, page_documents, evidence_records, unit_catalogue):
    """Return additive semantics and an inspectable, separate overlap ledger."""
    require(set(policy) == {'@context', '@id', 'schema', 'scope', 'assertion_status', 'review_status',
                            'specialist_review', 'legacy_index', 'legacy_profiles', 'expected', 'candidates', 'controls'}, 'Unknown migration policy fields')
    require(policy['@context'] == {'@vocab': BASE+'vocab/location-migration/'}
            and policy['@id'] == BASE+'id/authoring/structured-units/legacy-location-policy', 'Migration authoring identity/context differs')
    require(policy['schema'] == SCHEMA and policy['controls'] == CONTROLS, 'Unsupported or weakened location policy')
    require(policy['assertion_status'] == 'model-derived' and policy['review_status'] == REVIEW
            and policy['specialist_review'] == 'not-reviewed', 'Migration authority upgrade')
    require(isinstance(policy['scope'], str) and 0 < len(policy['scope']) <= 5000, 'Missing migration scope')
    expect = policy['expected']
    require(expect == {'requirements': 40, 'obligations': 203, 'candidates': 42}, 'Legacy research census changed; separate review required')
    require(len(legacy['requirements']) == expect['requirements'] and len(profiles['profiles']) == expect['requirements'], 'Legacy requirement count differs')
    obligations = [i for r in legacy['requirements'] for i in r['required'] if i.startswith(BASE+'id/obligation/staff/')]
    require(len(obligations) == len(set(obligations)) == expect['obligations'], 'Legacy obligation identity/count differs')
    declarations = {r['id']: r for r in profiles['profiles']}
    require(len(declarations) == len(profiles['profiles']), 'Duplicate legacy profile')
    declared_candidates = [r['id'] for r in policy['candidates']]
    require(len(declared_candidates) == len(set(declared_candidates)) == expect['candidates']
            and set(declared_candidates) == set(candidates)
            and set(candidates) == {i for r in profiles['profiles'] for i in r['candidate_ids']}, 'Candidate registration differs')
    result = deepcopy(semantic)
    record_map = {r['id']: r for r in evidence_records}
    require(len(record_map) == len(evidence_records), 'Duplicate source record identity')
    concepts = {r['id'] for r in result['records'] if r['kind'] == 'concept'}
    require(not concepts.intersection(record_map), 'Evidence collides with concept identity')
    require(not set(obligations).intersection(record_map) and not set(obligations).intersection(concepts), 'A legacy open obligation became available')
    existing = {r['id'] for r in result['requirements']}
    require(not existing.intersection(r['id'] for r in legacy['requirements']), 'Legacy requirements already present')
    result['requirements'].extend(deepcopy(legacy['requirements']))
    mapped = {}
    for candidate_id in declared_candidates:
        candidate = candidates[candidate_id]; p = candidate['provenance']; excerpt = candidate['excerpt']
        require(candidate['id'] == candidate_id and candidate['schema'] == 'okf-review-evidence.v1'
                and candidate['selection']['status'] == 'source-candidate-only-not-complete-answer', 'Candidate scope changed')
        require(excerpt['offset_encoding'] == 'Unicode code points; zero-based start-inclusive/end-exclusive', 'Unknown legacy offset encoding')
        pages = page_documents[candidate_id]
        require(pages['document_id'] == candidate['document_id'] and pages['source_sha256'] == p['source_sha256'], 'Candidate extraction source differs')
        page_rows = {r['page']: r for r in pages['pages']}
        require(len(page_rows) == len(pages['pages']) and p['page'] in page_rows, 'Duplicate or missing source page')
        text = page_rows[p['page']]['text']; literal = excerpt['text']
        start, end = excerpt['start'], excerpt['end']
        require(isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(text), 'Invalid legacy excerpt extent')
        require(text[start:end] == literal and digest(literal.encode()) == excerpt['sha256']
                and digest(text.encode()) == p['page_literal_sha256'], 'Legacy excerpt is not exact frozen source')
        lower, upper = len(text[:start].encode()), len(text[:end].encode())
        matches = []
        prefix = BASE+'id/unit/'
        for identifier, unit in unit_catalogue.items():
            record = record_map.get(identifier)
            if not record or not identifier.startswith(prefix):
                continue
            route = record['route'].split('/')
            if len(route) < 4 or route[2] != candidate['document_id']:
                continue
            overlaps = []
            for span in unit['spans']:
                if span['page'] == p['page']:
                    a, b = max(lower, span['start_utf8']), min(upper, span['end_utf8'])
                    if a < b: overlaps.append((a,b))
            if not overlaps:
                continue
            require(record['kind'] == 'evidence' and record['assertion_status'] == 'normalized'
                    and record['authority']['class'] == 'derived', 'Location mapping cannot promote source authority')
            require(digest(canonical(record)) == unit['record_sha256'], 'Location source record hash differs')
            expected_boundary = 'author-declared' if unit.get('authored') else 'machine-detected'
            require(unit['boundary_status'] in ({'author-declared'} if unit.get('authored') else {'source-structure-candidate','bounded-fragment'})
                    and record['evidence_unit']['boundary_status'] == expected_boundary
                    and record['evidence_unit']['completeness'] == unit['completeness'], 'Location mapping cannot change boundary review')
            require(len(record['evidence_unit']['spans']) == len(unit['spans']), 'Source span count differs')
            pieces=[]
            for bound, span in zip(record['evidence_unit']['spans'], unit['spans']):
                require(bound['source_sha256'] == p['source_sha256'] and bound['extraction_sha256'] == p['pages_sha256'], 'Location mapping source version differs')
                require(bound['source_start'] == span['start_utf8'] and bound['source_end'] == span['end_utf8']
                        and bound['source_url'] == pages['source_url']+'#page='+str(span['page']), 'Location span identity differs')
                require(span['page'] in page_rows, 'Full unit continuation source is absent')
                original = page_rows[span['page']]['text'].encode()
                a,b=span['start_utf8'],span['end_utf8']
                require(0 <= a <= b <= len(original) and digest(original[a:b]) == span['literal_sha256'] == bound['literal_sha256'], 'Full unit span is not exact source')
                pieces.append(original[a:b])
            require(record['evidence_unit']['joiner'] == '\n' and b'\n'.join(pieces) == record['text'].encode(), 'Complete unit text differs from source spans')
            matches.append({'id':identifier,'record_sha256':unit['record_sha256'], 'paragraph_labels':deepcopy(unit['paragraph_labels']),
                            'spans':deepcopy(unit['spans']), 'overlap_spans':[{'page':p['page'],'start_utf8':a,'end_utf8':b} for a,b in overlaps],
                            'overlap_bytes':sum(b-a for a,b in overlaps),'boundary_status':record['evidence_unit']['boundary_status'],
                            'catalogue_boundary_status':unit['boundary_status'],
                            'boundary_completeness':unit['completeness'],'mapping_status':'exact-location-overlap-only'})
        require(len(matches) <= 512, 'Candidate location expansion exceeds explicit bound')
        matches.sort(key=lambda r:r['id'])
        intervals=sorted((s['start_utf8'],s['end_utf8']) for r in matches for s in r['overlap_spans'])
        require(all(a[1] <= b[0] for a,b in zip(intervals,intervals[1:])), 'Mapped source units overlap each other')
        covered=sum(b-a for a,b in intervals)
        require(covered <= upper-lower, 'Mapped location coverage exceeds excerpt')
        unmapped=[]; cursor=lower
        for a,b in intervals+[(upper,upper)]:
            if cursor<a:
                gap=text.encode()[cursor:a]
                unmapped.append({'page':p['page'],'start_utf8':cursor,'end_utf8':a,'literal_sha256':digest(gap),'whitespace_only':not gap.decode('utf-8').strip()})
            cursor=max(cursor,b)
        mapped[candidate_id]={'candidate_id':candidate_id,'candidate_path':'evaluation/staff-review/evidence/'+candidate_id+'.json',
            'old_page_record_id':candidate['record_id'],'document_id':candidate['document_id'],
            'source_sha256':p['source_sha256'],'pages_path':p['pages_path'],'pages_sha256':p['pages_sha256'],
            'source_url':p['source_url'],'source_page_literal_sha256':p['page_literal_sha256'],
            'original_excerpt':{'offset_encoding':excerpt['offset_encoding'],'start':start,'end':end,'sha256':excerpt['sha256']},
            'utf8_location':{'page':p['page'],'start_utf8':lower,'end_utf8':upper},'new_units':matches,
            'location_bytes':upper-lower,'mapped_bytes':covered,'unmapped_spans':unmapped,
            'status':'location-fully-mapped' if covered==upper-lower else 'location-partly-mapped' if covered else 'location-unresolved',
            'semantic_equivalence':'not-established','requirement_support':'not-established','legal_effect':'not-established'}
    routes, rows = {}, []
    old_assertions={e['id']:e for e in legacy['assertions']}
    existing_rows={e['id']:e for e in result['assertions']}
    existing_edges=set(existing_rows)
    for req in legacy['requirements']:
        pid=req['id'].rsplit('/',1)[-1]
        require(pid in declarations, 'Unknown legacy requirement/profile association')
        profile=declarations[pid]; triggers=req['when_all']
        require(isinstance(triggers,list) and 0 < len(triggers) <= 8 and len(set(triggers)) == len(triggers)
                and set(triggers) <= concepts, 'Unknown or unbounded legacy trigger concept')
        require(len(set(profile['candidate_ids'])) == len(profile['candidate_ids']), 'Duplicate candidate within legacy profile')
        navigation=[]; unresolved=[]; missing_routes=[]; unresolved_prefixes=[]
        for candidate_id in profile['candidate_ids']:
            mapping=mapped[candidate_id]; page_id=mapping['old_page_record_id']
            require(page_id in req['required'], 'Candidate page not required by preserved profile')
            paths=[r for r in req.get('required_paths',[]) if r['records'][-1]==page_id]
            if not paths:
                missing_routes.append({'candidate_id':candidate_id,'old_page_record_id':page_id,'status':'no-original-profile-route',
                                       'inferred_route_created':bool(mapping['new_units'])})
                paths=[{'seed':triggers[-1],'records':[triggers[-1],page_id],'assertions':[]}]
            for path in paths:
                inferred=not path['assertions']
                if not inferred:
                    require(1 <= len(path['assertions']) <= 8 and len(path['records'])==len(path['assertions'])+1
                            and path['seed'] in triggers and path['records'][0]==path['seed']
                            and set(path['records'][:-1]) <= concepts, 'Legacy route has unsupported scope')
                    for i,eid in enumerate(path['assertions']):
                        old=old_assertions.get(eid)
                        require(old and [old['source'],old['target']]==path['records'][i:i+2], 'Original route does not match preserved assertions')
                missing_prefix=[]
                if not inferred:
                    missing_prefix=[eid for eid in path['assertions'][:-1] if existing_rows.get(eid)!=old_assertions[eid]]
                    if missing_prefix:
                        unresolved_prefixes.append({'candidate_id':candidate_id,'original_path':deepcopy(path),
                            'status':'unresolved-prefix','missing_or_changed_assertion_ids':missing_prefix,'route_emitted':False})
                        continue
                derivation='inferred-profile-candidate-route' if inferred else 'restored-original-route'
                source=path['records'][-2]
                for unit in mapping['new_units']:
                    identity=[req['id'],candidate_id,derivation,source,path['assertions'],unit['id'],triggers]
                    eid=BASE+'id/assertion/location-migration/'+digest(canonical(identity))
                    require(eid not in existing_edges,'Migration assertion collision')
                    if eid not in routes:
                        routes[eid]={'id':eid,'source':source,'target':unit['id'],'predicate':'http://purl.org/dc/terms/references',
                            'label':('inferred profile association' if inferred else 'restored candidate location')+' overlaps complete source unit; support unreviewed',
                            'context_guard':{'when_all':deepcopy(triggers)},
                            'assertion_status':'model-derived','authority':{'class':'model-assisted','label':'Location-only '+derivation+' under an authored research policy',
                                'source':REPO+'/blob/main/'+AUTHORING},
                            'scope':policy['scope']+' Original candidate '+candidate_id+' for '+pid+'. Derivation: '+derivation+'. This edge does not replace original required page/path '+page_id+'; it establishes neither semantic equivalence nor applicability.',
                            'provenance':deepcopy(record_map[unit['id']]['provenance'])}
                    navigation.append({'assertion_id':eid,'seed':path['seed'],'source':source,'target':unit['id'],
                        'records':[*path['records'][:-1],unit['id']], 'assertions':[*path['assertions'][:-1],eid] if not inferred else [eid],
                        'context_guard':{'when_all':deepcopy(triggers)},'candidate_id':candidate_id,
                        'original_assertion_ids':deepcopy(path['assertions']), 'derivation':derivation,'support_status':'navigation-only'})
            if mapping['status']!='location-fully-mapped':unresolved.append(candidate_id)
        rows.append({'requirement_id':req['id'],'original_requirement_sha256':digest(canonical(req)),
                     'when_all':deepcopy(triggers),'candidate_ids':deepcopy(profile['candidate_ids']),
                     'navigation_routes':navigation,'unresolved_candidate_locations':unresolved,'missing_original_routes':missing_routes,'unresolved_original_prefixes':unresolved_prefixes,
                     'original_required_ids_preserved':True,'original_required_paths_preserved':True,
                     'legacy_obligation_ids':[r for r in req['required'] if r.startswith(BASE+'id/obligation/staff/')],
                     'requirement_support':'not-established-by-migration'})
    result['assertions'].extend(routes[k] for k in sorted(routes))
    require(result['records']==semantic['records'] and result['assertions'][:len(semantic['assertions'])]==semantic['assertions'], 'Inherited semantic content changed')
    require(result['requirements'][:len(semantic['requirements'])]==semantic['requirements']
            and result['requirements'][len(semantic['requirements']):]==legacy['requirements'], 'Legacy or inherited requirements changed')
    ledger={'schema':'okf-dwp-location-migration-ledger.v1','scope':policy['scope'],
            'counts':{'legacy_requirements':len(rows),'original_obligations':len(obligations),'candidates':len(mapped),
                      'locations_fully_mapped':sum(r['status']=='location-fully-mapped' for r in mapped.values()),
                      'locations_unresolved_or_partial':sum(r['status']!='location-fully-mapped' for r in mapped.values()),
                      'location_navigation_assertions':len(routes),'missing_original_profile_candidate_routes':sum(len(r['missing_original_routes']) for r in rows),
                      'profiles_with_location_navigation':sum(bool(r['navigation_routes']) for r in rows),
                      'unresolved_original_prefixes':sum(len(r['unresolved_original_prefixes']) for r in rows),
                      'restored_navigation_routes':sum(n['derivation']=='restored-original-route' for r in rows for n in r['navigation_routes']),
                      'inferred_navigation_routes':sum(n['derivation']=='inferred-profile-candidate-route' for r in rows for n in r['navigation_routes']),
                      'requirements_closed_by_migration':0},
            'source_maps':[mapped[k] for k in sorted(mapped)],'profiles':rows,
            'limitations':['Location overlap is not semantic equivalence, relevance, legal applicability or source completeness.',
                           'All original page requirements, paths and 203 obligations remain unchanged; new unit routes cannot satisfy them.',
                           'A retrieved whole unit can include surrounding material and may exceed an assembly budget; delivery must report that limit.',
                           'Original profile activation and navigation-location coverage must not be reported as reviewed requirement support.']}
    return result,ledger


def project(inputs, semantic, evidence_records, unit_catalogue):
    inputs.read('scripts/structured_location_migration.py',limit=1024*1024)
    policy=strict_json(inputs.read(AUTHORING,limit=1024*1024))
    for key,path in (('legacy_index','combined/context/corpus/base-index.json'),('legacy_profiles','domain-profile/staff-semantic/profiles.yamlld')):
        require(set(policy[key])=={'path','sha256'} and policy[key]['path']==path,'Unregistered legacy source path')
    legacy=strict_json(inputs.read(policy['legacy_index']['path'],policy['legacy_index']['sha256'],limit=16*1024*1024))
    profiles=decode_profiles(inputs.read(policy['legacy_profiles']['path'],policy['legacy_profiles']['sha256'],limit=1024*1024))
    candidates={};pages={}
    for ref in policy['candidates']:
        require(set(ref)=={'id','path','sha256'} and re.fullmatch(r'source-c[0-9]{3}',ref['id'])
                and ref['path']=='evaluation/staff-review/evidence/'+ref['id']+'.json','Unregistered candidate path')
        candidate=strict_json(inputs.read(ref['path'],ref['sha256'],limit=1024*1024))
        p=candidate['provenance'];require(PAGE_PATH.fullmatch(p['pages_path']),'Unregistered page extraction path')
        candidates[ref['id']]=candidate
        pages[ref['id']]=strict_json(inputs.read(p['pages_path'],p['pages_sha256'],limit=16*1024*1024))
    return compile_migration(policy,semantic,legacy,profiles,candidates,pages,evidence_records,unit_catalogue)
