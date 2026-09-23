"""Restore an explicitly bound historical acceptance profile into unit navigation.

The original page requirements stay unchanged. New requirements are labelled
translations, not semantic equivalence or legal acceptance. Whole source units
are never edited and page-level dependency edges are not multiplied into units.
"""
from copy import deepcopy
import re

from build_bundle import BASE, REPO, canonical, digest
from build_logical_units import require, strict_json

AUTHORING = 'domain-profile/structured-units/custody-restoration.yamlld'
SCHEMA = 'okf-dwp-structured-custody-restoration.v1'
CONTEXT = {'@vocab': BASE + 'vocab/structured-custody-restoration/',
           'dct': 'http://purl.org/dc/terms/', 'prov': 'http://www.w3.org/ns/prov#'}
REVIEW = 'unreviewed-specialist-review-required'
DCT = 'http://purl.org/dc/terms/'
LEGACY_INPUTS = {
    'full-dmg/context/assembly-index.json',
    'knowledge/full-dmg/imprisonment/context-profile.yamlld',
    'evaluation/context-assembly/imprisonment-case.json',
    'evaluation/context-assembly/source-selectors.json',
    'evaluation/remote-mcp/hospital-case.json',
}


def compile_restoration(author, semantic, records, units, legacy, source_pages):
    """Pure admission with separate inherited requirements and translated routes."""
    require(set(author) == {'@context', '@id', 'schema', 'scope', 'review_status', 'specialist_review',
                            'legacy_inputs', 'source_units', 'page_mappings', 'profiles', 'scope_records',
                            'dependencies', 'chapter_routes', 'unresolved_selectors', 'limitations'},
            'Unknown custody restoration fields')
    require(author['schema'] == SCHEMA and author['@context'] == CONTEXT
            and author['@id'] == BASE + 'id/authoring/structured-units/custody-restoration',
            'Custody authoring identity or context differs')
    require(author['review_status'] == REVIEW and author['specialist_review'] == 'not-reviewed',
            'Custody review cannot be upgraded')
    require(isinstance(author['scope'], str) and author['scope'].strip(), 'Custody scope absent')
    require(0 < len(author['source_units']) <= 256 and 0 < len(author['profiles']) <= 8,
            'Unbounded custody restoration')
    result = deepcopy(semantic)
    by_id = {r['id']: r for r in records}
    original = {r['id']: r for r in legacy['records']}
    old_requirements = {r['id']: r for r in legacy['requirements']}
    require(len(by_id) == len(records), 'Duplicate input evidence')
    concepts = {r['id'] for r in semantic['records'] if r['kind'] == 'concept'}
    selected = {}; extractions={}
    for entry in author['source_units']:
        require(set(entry) == {'id', 'record_sha256', 'source_sha256', 'pages_sha256', 'spans', 'paragraph_labels'},
                'Unknown custody unit binding fields')
        identifier = entry['id']
        require(identifier not in selected and identifier in by_id and identifier in units,
                'Missing or duplicate custody unit')
        record, unit = by_id[identifier], units[identifier]
        require(record['kind'] == 'evidence' and record['assertion_status'] == 'normalized'
                and record['authority']['class'] == 'derived', 'Custody source authority differs')
        require(digest(canonical(record)) == entry['record_sha256'] == unit['record_sha256']
                and unit['spans'] == entry['spans'] and unit['paragraph_labels'] == entry['paragraph_labels'],
                'Custody whole-unit identity differs')
        require(record['text']==unit['text'], 'Custody record text differs from catalogue')
        require(record['evidence_unit']['completeness']==unit['completeness']
                and record['evidence_unit']['boundary_status']==('author-declared' if unit.get('authored') else 'machine-detected'),
                'Custody source boundary status differs')
        extraction_sha=entry['pages_sha256']
        if extraction_sha not in extractions:
            require(extraction_sha in source_pages and digest(source_pages[extraction_sha])==extraction_sha,
                    'Custody original extraction bytes differ')
            pages=strict_json(source_pages[extraction_sha])
            require(pages['source_sha256']==entry['source_sha256'], 'Custody extraction source differs')
            extractions[extraction_sha]={p['page']:p for p in pages['pages']}
        spans = record['evidence_unit']['spans']
        require(len(spans) == len(entry['spans']), 'Custody span count differs')
        pieces=[]
        for span, declared in zip(spans, entry['spans']):
            require(span['source_sha256'] == entry['source_sha256']
                    and span['extraction_sha256'] == entry['pages_sha256']
                    and span['source_start'] == declared['start_utf8']
                    and span['source_end'] == declared['end_utf8']
                    and span['literal_sha256'] == declared['literal_sha256']
                    and span['source_url'].endswith('#page=' + str(declared['page'])),
                    'Custody source span differs')
            original_page=extractions[extraction_sha].get(declared['page'])
            require(original_page is not None,'Custody continuation source page absent')
            raw=original_page['text'].encode();start,end=declared['start_utf8'],declared['end_utf8']
            require(isinstance(start,int) and isinstance(end,int) and 0<=start<end<=len(raw)
                    and digest(raw[start:end])==declared['literal_sha256'], 'Custody literal source span differs')
            pieces.append(raw[start:end])
        require(record['evidence_unit']['joiner']=='\n' and b'\n'.join(pieces)==record['text'].encode(),
                'Custody complete unit differs from original source spans')
        selected[identifier] = record
    mappings = {}
    for entry in author['page_mappings']:
        require(set(entry) == {'original_id', 'original_record_sha256', 'unit_ids', 'mapping_status'},
                'Unknown custody page mapping fields')
        oid = entry['original_id']; old = original.get(oid)
        require(old and oid not in mappings and old['kind'] == 'evidence' and '/id/page/' in oid
                and digest(canonical(old)) == entry['original_record_sha256'], 'Custody original page differs')
        require(entry['mapping_status'] == 'exact-source-location-overlap-only'
                and entry['unit_ids'] and len(set(entry['unit_ids'])) == len(entry['unit_ids'])
                and set(entry['unit_ids']) <= selected.keys(), 'Invalid custody page mapping')
        source = old['provenance'][0]
        for uid in entry['unit_ids']:
            require(any(p['url'] == source['url'] and p['source_sha256'] == source['source_sha256']
                        for p in selected[uid]['provenance']), 'Custody page/unit source identity differs')
        mappings[oid] = entry['unit_ids']
    require(set(selected) == {uid for values in mappings.values() for uid in values}, 'Unmapped custody unit')
    for row in author['unresolved_selectors']:
        require(set(row)=={'original_page_id','original_declared_label','status','limitation'}
                and row['original_page_id'] in mappings
                and row['status']=='not-a-matched-governing-paragraph-label'
                and isinstance(row['original_declared_label'],str)
                and row['limitation'].strip(), 'Custody unresolved selector upgraded')

    # Exact historic scope records keep their identities. A catalogue excerpt
    # gets a distinct scope identity, never the identity of a PDF evidence unit.
    scope_map = {}; present = {r['id']: r for r in result['records']}; scope_ids=set()
    added_scope = []
    for entry in author['scope_records']:
        require(set(entry) == {'original_id', 'original_record_sha256', 'id', 'mode'}, 'Unknown custody scope fields')
        old = original.get(entry['original_id'])
        require(entry['original_id'] not in scope_map and entry['id'] not in scope_ids,
                'Duplicate custody scope declaration')
        require(old and digest(canonical(old)) == entry['original_record_sha256'], 'Custody original scope differs')
        record = deepcopy(old)
        if entry['mode'] == 'exact-historical-scope':
            require(old['kind'] == 'scope' and entry['id'] == old['id'], 'Scope identity changed')
        else:
            require(entry['mode'] == 'dated-catalogue-observation' and old['kind'] == 'evidence'
                    and old['route'].startswith('evidence/imprisonment-')
                    and re.fullmatch(re.escape(BASE) + r'id/scope/custody-capture/[a-z0-9-]+', entry['id']),
                    'Unsupported catalogue scope transformation')
            record.update(id=entry['id'], route=entry['id'].removeprefix(BASE+'id/'), kind='scope',
                          label='Frozen catalogue observation: ' + old['label'],
                          scope='Exact captured catalogue text from the original 15 September 2026 source profile. '
                                'This is a dated navigation/scope observation, not the absent memo body, current law '
                                'or a claim that ADM bodies are absent from the later corpus. ' + old['scope'])
        require(record['id'] not in present or present[record['id']] == record, 'Custody scope collision')
        if record['id'] not in present:
            result['records'].append(record); present[record['id']] = record; added_scope.append(record)
        scope_map[old['id']] = record['id']
        scope_ids.add(record['id'])

    requirement_ids = {r['id'] for r in result['requirements']}
    for old in legacy['requirements']:
        require(old['id'] not in requirement_ids, 'Custody restoration already applied')
        result['requirements'].append(deepcopy(old)); requirement_ids.add(old['id'])
    edge_ids = {r['id'] for r in result['assertions']}; emitted = []; profile_ledger = []

    def edge(source, target, predicate, scope, guards, provenance, binding):
        require(source in concepts | selected.keys() | present.keys()
                and target in concepts | selected.keys() | present.keys(), 'Custody edge endpoint absent')
        eid = BASE + 'id/assertion/custody-restoration/' + digest(canonical([source, target, predicate, guards, binding]))
        require(eid not in edge_ids, 'Custody edge collision'); edge_ids.add(eid)
        row = {'id': eid, 'source': source, 'target': target, 'predicate': predicate,
               'label': 'references translated source selection' if predicate == DCT+'references' else 'requires source context',
               'context_guard': {'when_all': list(guards)}, 'assertion_status': 'model-derived',
               'authority': {'class': 'model-assisted', 'label': 'Bound historical source-profile translation; specialist review pending',
                             'source': REPO + '/blob/main/' + AUTHORING},
               'scope': scope, 'provenance': deepcopy(provenance)}
        emitted.append(row); return eid

    for profile in author['profiles']:
        require(set(profile) == {'id', 'legacy_requirement_id', 'when_all', 'covers', 'label', 'missing_obligations',
                                 'selected_unit_ids', 'source_read_note'},
                'Unknown translated custody profile fields')
        rid = profile['id']; old = old_requirements.get(profile['legacy_requirement_id'])
        require(old and rid not in requirement_ids and re.fullmatch(re.escape(BASE)+r'id/requirement/custody-units/[a-z0-9-]+', rid),
                'Invalid custody profile identity')
        guards = profile['when_all']
        require(1 <= len(guards) <= 8 and len(set(guards)) == len(guards) and set(guards) <= concepts
                and set(profile['covers']) <= set(guards), 'Custody guard or coverage differs')
        mapped = {uid for oid in old['required'] for uid in mappings.get(oid, [])}
        needed = profile['selected_unit_ids']
        require(isinstance(needed,list) and needed and len(set(needed))==len(needed)
                and set(needed)<=mapped and isinstance(profile['source_read_note'],str)
                and profile['source_read_note'].strip(), 'Custody source-read selection not explicitly scoped')
        targets = needed + sorted({scope_map[oid] for oid in old['required'] if oid in scope_map})
        require(needed and profile['missing_obligations'], 'Custody profile cannot imply completeness')
        paths=[]; seed=guards[-1]
        for uid in targets:
            target = selected.get(uid, present.get(uid))
            eid=edge(seed, uid, DCT+'references', author['scope']+' '+old['scope']+' '+profile['source_read_note'], guards,
                     target['provenance'], [rid, old['id']])
            paths.append({'seed': seed, 'records': [seed,uid], 'assertions': [eid]})
        obligations=[]
        for o in profile['missing_obligations']:
            require(set(o)=={'key','label','status'} and re.fullmatch(r'[a-z0-9-]+',o['key'])
                    and o['status']=='unresolved' and o['label'].strip(), 'Custody obligation closed or invalid')
            oid=BASE+'id/obligation/custody-units/'+rid.rsplit('/',1)[-1]+'/'+o['key']
            require(oid not in present and oid not in by_id and oid not in obligations, 'Custody obligation collision')
            obligations.append(oid)
        result['requirements'].append({'id':rid,'label':profile['label'],'when_all':deepcopy(guards),
            'covers':deepcopy(profile['covers']),'required':targets+obligations,'required_paths':paths,
            'scope':author['scope']+' '+old['scope']+' '+profile['source_read_note'],
            'limitations':author['limitations']+[o['label'] for o in profile['missing_obligations']]})
        requirement_ids.add(rid);profile_ledger.append({'id':rid,'original_requirement_id':old['id'],
            'unit_ids':needed,'scope_ids':[u for u in targets if u not in selected], 'required_paths':paths,
            'source_read_note':profile['source_read_note'],
            'mapped_but_not_selected_unit_ids':sorted(mapped-set(needed)),
            'open_obligation_ids':obligations,'status':'translated-selection-not-equivalent-legal-support'})
    for row in author['dependencies']:
        require(set(row)=={'source','target','literal','reason','when_all'}, 'Unknown custody dependency fields')
        require(row['source'] in selected and row['target'] in selected and row['literal'] in selected[row['source']]['text'],
                'Custody contextual dependency source absent')
        require(isinstance(row['when_all'],list) and 1<=len(row['when_all'])<=8
                and len(set(row['when_all']))==len(row['when_all']) and set(row['when_all'])<=concepts,
                'Unknown or duplicate custody dependency guard')
        edge(row['source'],row['target'],DCT+'requires',row['reason'],row['when_all'],selected[row['source']]['provenance'],row)
    for row in author['chapter_routes']:
        require(set(row)=={'source','target','original_assertion_id','literal','when_all'}, 'Unknown custody chapter route fields')
        original_edge=next((v for v in legacy['assertions'] if v['id']==row['original_assertion_id']),None)
        require(original_edge and original_edge['target']==row['target'] and original_edge['predicate']==DCT+'references'
                and row['source'] in selected and row['target'] in present
                and row['source'] in mappings.get(original_edge['source'],[])
                and row['literal'] in selected[row['source']]['text'], 'Custody chapter route lacks source support')
        require(isinstance(row['when_all'],list) and 1<=len(row['when_all'])<=8
                and len(set(row['when_all']))==len(row['when_all']) and set(row['when_all'])<=concepts,
                'Unknown or duplicate custody chapter guard')
        eid=edge(row['source'],row['target'],DCT+'references',
             'Literal chapter navigation translated from the original source-backed assertion '+original_edge['id']+'. '
             'The reference names a chapter, not a destination paragraph or a legal outcome.',row['when_all'],
             selected[row['source']]['provenance'],row)
        for entry in profile_ledger:
            if row['target'] not in entry['scope_ids'] or row['source'] not in entry['unit_ids']:
                continue
            prior=next(p for p in entry['required_paths'] if p['records'][-1]==row['source'])
            path={'seed':prior['seed'],'records':[*prior['records'],row['target']],
                  'assertions':[*prior['assertions'],eid]}
            entry['required_paths'].append(path)
            # The same list is deliberately shared with its generated requirement.
    result['assertions'].extend(emitted)
    result['records'].sort(key=lambda r:r['id']);result['assertions'].sort(key=lambda r:r['id']);result['requirements'].sort(key=lambda r:r['id'])
    require(all(next(v for v in result['records'] if v['id']==old['id'])==old for old in semantic['records']), 'Inherited concept changed')
    ledger={'schema':'okf-dwp-custody-unit-translation.v1','scope':author['scope'],
            'original_requirements':deepcopy(legacy['requirements']),'page_mappings':deepcopy(author['page_mappings']),
            'unresolved_selectors':deepcopy(author['unresolved_selectors']),'profiles':profile_ledger,
            'added_scope_records':added_scope,'chapter_routes':deepcopy(author['chapter_routes']),
            'dependencies':deepcopy(author['dependencies']),'limitations':deepcopy(author['limitations']),
            'original_obligations_closed':0}
    return result,ledger


def project(inputs, semantic, records, units):
    inputs.read('scripts/structured_custody_restoration.py',limit=1024*1024)
    author=strict_json(inputs.read(AUTHORING,limit=2*1024*1024))
    require({r['path'] for r in author['legacy_inputs']} == LEGACY_INPUTS,
            'Custody legacy input registration differs')
    bound={}
    for entry in author['legacy_inputs']:
        require(set(entry)=={'path','sha256','bytes'} and entry['path'] not in bound,
                'Duplicate or malformed custody input binding')
        bound[entry['path']]=inputs.read(entry['path'],entry['sha256'],entry['bytes'])
    require('full-dmg/context/assembly-index.json' in bound, 'Custody original index not bound')
    by_id={r['id']:r for r in records};pages={}
    for entry in author['source_units']:
        record=by_id.get(entry['id']);require(record is not None,'Missing custody record')
        for span in record['evidence_unit']['spans']:
            path=span['extraction_url'].removeprefix(REPO+'/blob/main/')
            require(re.fullmatch(r'source/(?:full-dmg-2026-09-15/)?pages/[a-z0-9-]+\.json',path),
                    'Unregistered custody extraction path')
            require(span['extraction_sha256']==entry['pages_sha256'],'Custody extraction binding differs')
            if entry['pages_sha256'] not in pages:
                pages[entry['pages_sha256']]=inputs.read(path,entry['pages_sha256'],limit=16*1024*1024)
    return compile_restoration(author,semantic,records,units,strict_json(bound['full-dmg/context/assembly-index.json']),pages)
