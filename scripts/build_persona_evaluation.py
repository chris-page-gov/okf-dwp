#!/usr/bin/env python3
"""Build a provenance-checked projected-persona retrieval and boundary suite."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
AUTHORING = Path('domain-profile/staff-needs/persona-evaluation.json')
QUESTIONS = Path('evaluation/staff-questions/cases.json')
MATRIX = Path('evaluation/staff-needs/matrix.json')
JOURNEYS = Path('domain-profile/staff-needs/journeys.json')
INDEX = Path('combined/context/corpus/base-index.json')
EVIDENCE_DIR = Path('evaluation/staff-review/evidence')
SOURCE_PAGES_DIR = Path('source/pages')
OUT = Path('evaluation/retrieval-gate')
EXPECTED_PERSONAS = {
    'persona/welfare-rights-adviser', 'persona/pensions-specialist',
    'persona/knowledge-engineer', 'persona/policy-law-reviewer',
    'persona/rules-architect', 'persona/evidence-assurance-reviewer',
    'persona/applicant-change-reporter', 'persona/assisted-support',
}
KINDS = {'retrieval', 'boundary', 'ui', 'integrity'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def _route_personas(text):
    import re
    return set(re.findall(r'^\s*route:\s*(persona/[a-z0-9-]+)\s*$', text, re.M))


def _validate_source_pins(spec, matrix):
    for path, expected in spec['source_files'].items():
        actual = sha((ROOT / path).read_bytes())
        if actual != expected:
            raise ValueError(f'Persona source hash changed: {path}')
    union = set()
    for path in ('knowledge/guided-discovery.yamlld', 'knowledge/evaluation-journeys.yamlld'):
        union |= _route_personas((ROOT / path).read_text(encoding='utf-8'))
    union |= {p['id'] for p in matrix['personas']}
    if union != EXPECTED_PERSONAS:
        raise ValueError(f'Persona inventory differs: missing={sorted(EXPECTED_PERSONAS-union)} extra={sorted(union-EXPECTED_PERSONAS)}')
    seen = set()
    for persona in spec['personas']:
        if persona['id'] not in EXPECTED_PERSONAS or persona['status'] != 'projected':
            raise ValueError(f'Unknown or mislabelled projected persona: {persona.get("id")}')
        for area in persona['areas']:
            if area['id'] in seen:
                raise ValueError(f'Duplicate persona area: {area["id"]}')
            seen.add(area['id'])
            source = area['source']
            if source['file'] not in spec['source_files']:
                raise ValueError(f'Area source is not hash-pinned: {area["id"]}')
            if source.get('sha256') != spec['source_files'][source['file']]:
                raise ValueError(f'Area source hash differs from pinned input: {area["id"]}')
            start, end = source['lines']
            lines = (ROOT / source['file']).read_text(encoding='utf-8').splitlines()
            if start < 1 or end < start or end > len(lines):
                raise ValueError(f'Invalid source line locator for area: {area["id"]}')
            excerpt = '\n'.join(lines[start - 1:end])
            anchor = source['locator'].split(';', 1)[0]
            if (not anchor or not excerpt.strip()
                    or anchor not in excerpt
                    or persona['id'] not in (ROOT / source['file']).read_text(encoding='utf-8')):
                raise ValueError(f'Area source line locator does not contain its authored anchor: {area["id"]}')
    authored = {p['id'] for p in spec['personas']}
    if authored != EXPECTED_PERSONAS:
        raise ValueError(f'Authored persona inventory differs: missing={sorted(EXPECTED_PERSONAS-authored)} extra={sorted(authored-EXPECTED_PERSONAS)}')
    return matrix


def _record_map(index):
    records = index['records']
    ids = {r['id']: r for r in records}
    routes = {}
    for record in records:
        routes.setdefault(record['route'], []).append(record)
    if len(ids) != len(records):
        raise ValueError('Duplicate combined corpus record identity')
    return ids, routes


def _verify_candidate(candidate_id, candidates, record_ids, review_cache):
    candidate = candidates.get(candidate_id)
    if not candidate:
        raise ValueError(f'Unknown source candidate: {candidate_id}')
    rid = candidate['record_id']
    record = record_ids.get(rid)
    if not record:
        raise ValueError(f'Candidate record absent from combined corpus: {candidate_id}')
    review_path = EVIDENCE_DIR / f'{candidate_id}.json'
    review = review_cache.get(candidate_id)
    if review is None:
        review = json.loads((ROOT / review_path).read_text(encoding='utf-8'))
        review_cache[candidate_id] = review
    if review.get('record_id') != rid or review.get('selection', {}).get('status') != 'source-candidate-only-not-complete-answer':
        raise ValueError(f'Candidate is not an exact assessor-only candidate: {candidate_id}')
    if sha(review.get('excerpt', {}).get('text', '').encode('utf-8')) != review.get('excerpt', {}).get('sha256'):
        raise ValueError(f'Candidate excerpt hash mismatch: {candidate_id}')
    prov = review.get('provenance', {})
    if prov.get('page_literal_sha256') != candidate.get('literal_sha256'):
        raise ValueError(f'Candidate page literal hash differs: {candidate_id}')
    matches = [p for p in record.get('provenance', [])
               if p.get('literal_sha256') == candidate.get('literal_sha256')
               and p.get('source_sha256') == candidate.get('source_sha256')]
    if not matches:
        raise ValueError(f'Candidate source hashes do not match combined index: {candidate_id}')
    for field, pathfield in (('source_sha256', 'source_pdf'), ('pages_sha256', 'pages_path')):
        source_path = ROOT / candidate[pathfield]
        if not source_path.is_file() or sha(source_path.read_bytes()) != candidate[field]:
            raise ValueError(f'Candidate {field} does not match frozen source file: {candidate_id}')
    return {'id': rid, 'route': candidate['route'], 'candidate_id': candidate_id,
            'source_sha256': candidate['source_sha256'], 'literal_sha256': candidate['literal_sha256'],
            'pages_file_sha256': candidate['pages_sha256'],
            'locator': candidate['locator'], 'review_status': 'unreviewed-source-candidate'}


def _resolve_route(route, routes):
    found = routes.get(route, [])
    if len(found) != 1:
        raise ValueError(f'Expected exactly one combined corpus record for route: {route}')
    record = found[0]
    provenance = record.get('provenance', [])
    if not provenance or not any(p.get('source_sha256') and p.get('literal_sha256') for p in provenance):
        raise ValueError(f'Target route lacks source and literal hash provenance: {route}')
    p = next(p for p in provenance if p.get('source_sha256') and p.get('literal_sha256'))
    source_page_refs = [entry for entry in provenance
                        if re.search(r'/source/pages/[^/#?]+\.json(?:$|[?#])', entry.get('url', ''))]
    if not source_page_refs or not route.startswith('page/'):
        raise ValueError(f'Target route lacks a locally verifiable page-source identity: {route}')
    source_entry = source_page_refs[0]
    filename = re.search(r'/source/pages/([^/#?]+\.json)', source_entry['url']).group(1)
    source_path = ROOT / SOURCE_PAGES_DIR / filename
    if not source_path.is_file() or sha(source_path.read_bytes()) != source_entry.get('source_sha256'):
        raise ValueError(f'Target route page-source file hash mismatch: {route}')
    pages = json.loads(source_path.read_text(encoding='utf-8')).get('pages', [])
    page_number = int(route.rsplit('/', 1)[1])
    page = next((item for item in pages if item.get('page') == page_number), None)
    if (not page or page.get('text') != record.get('text')
            or sha(page['text'].encode('utf-8')) != source_entry.get('literal_sha256')
            or source_entry.get('literal_sha256') != p.get('literal_sha256')):
        raise ValueError(f'Target route page text or literal hash is not verified by frozen source: {route}')
    return {'id': record['id'], 'route': route, 'source_sha256': p['source_sha256'],
            'literal_sha256': p['literal_sha256'], 'pages_file_sha256': source_entry['source_sha256'],
            'locator': p.get('locator'),
            'review_status': record.get('review_status', 'unreviewed')}


def build(spec, question_registry, matrix, index, journey_spec):
    _validate_source_pins(spec, matrix)
    record_ids, routes = _record_map(index)
    registry_cases = question_registry['cases']
    registry_by_id = {c['id']: c for c in registry_cases}
    if len(registry_by_id) != 40 or len(registry_by_id) != len(registry_cases):
        raise ValueError('Frozen 40-question occurrence set changed')
    if (len({c['question'] for c in registry_cases}) != 39
            or len(registry_cases) != question_registry['occurrence_count']):
        raise ValueError('Frozen question wording or occurrence count changed')
    candidates = {c['id']: c for c in question_registry['source_candidates']}
    areas = {}
    for persona in spec['personas']:
        for area in persona['areas']:
            areas[area['id']] = {'id': area['id'], 'persona_id': persona['id'],
                                 'interest': area['interest'], 'source': area['source'],
                                 'case_ids': list(area['case_ids'])}
    authored_cases = {c['id']: c for c in spec['additional_cases']}
    if len(authored_cases) != len(spec['additional_cases']):
        raise ValueError('Duplicate additional evaluation case')
    all_case_ids = set(registry_by_id) | set(authored_cases)
    if set(authored_cases) & set(registry_by_id):
        raise ValueError('Additional cases may not replace frozen question cases')
    area_map = {cid: [] for cid in all_case_ids}
    for area in areas.values():
        if not area['case_ids']:
            raise ValueError(f'Persona area has no test case: {area["id"]}')
        for cid in area['case_ids']:
            if cid not in all_case_ids:
                raise ValueError(f'Persona area references unknown case: {area["id"]} -> {cid}')
            area_map[cid].append(area['id'])
    if any(not values for values in area_map.values()):
        missing = sorted(cid for cid, values in area_map.items() if not values)
        raise ValueError(f'Evaluation cases are not mapped to persona interests: {missing}')
    if set(registry_by_id) != {c['id'] for c in matrix['cases']}:
        raise ValueError('Staff-needs matrix no longer maps all frozen question occurrences')
    matrix_by_id = {c['id']: c for c in matrix['cases']}
    for cid, row in registry_by_id.items():
        if row['question'] != matrix_by_id[cid]['question']:
            raise ValueError(f'Question wording changed in staff-needs matrix: {cid}')

    review_cache = {}
    cases = []
    for row in registry_cases:
        expected = [_verify_candidate(cid, candidates, record_ids, review_cache)
                    for cid in row['candidate_ids']]
        # Source-candidate targets are assessor evidence only; the evaluation host
        # must send only the question to the runtime.
        cases.append({'id': row['id'], 'origin': 'frozen-staff-question',
                      'personas': matrix_by_id[row['id']]['personas'], 'area_ids': sorted(area_map[row['id']]),
                      'prompt': {'question': row['question']},
                      'evaluation': {'kind': 'retrieval', 'expected_records': [r['id'] for r in expected],
                                     'target_provenance': expected,
                                     'required_evidence': row['required_evidence'],
                                     'expected_gaps': row['scope_gaps'] + row['ambiguities'],
                                     'source_candidates_are_assessor_targets': True,
                                     'recall_eligible': True, 'execution_status': 'not-run'},
                      'runtime_target_leakage': 'forbidden'})

    for row in spec['additional_cases']:
        if row['kind'] not in KINDS:
            raise ValueError(f'Unknown evaluation case kind: {row["id"]}')
        if not row.get('gaps') or not row.get('negative_control'):
            raise ValueError(f'Case requires explicit gap and negative control: {row["id"]}')
        if row.get('review_decision'):
            decision = row['review_decision']
            if not decision.get('status') or not decision.get('rationale') or not decision.get('source_context'):
                raise ValueError(f'Incomplete target-validity review decision: {row["id"]}')
            context = decision['source_context']
            if not all(context.get(field) for field in ('file', 'locator', 'sha256')):
                raise ValueError(f'Incomplete source context for target-validity decision: {row["id"]}')
            context_path = ROOT / context['file']
            if not context_path.is_file() or sha(context_path.read_bytes()) != context['sha256']:
                raise ValueError(f'Source context hash changed for target-validity decision: {row["id"]}')
            if decision['status'] == 'original-retained-as-scope-boundary':
                if row['kind'] != 'boundary' or row.get('target_routes') or row.get('candidate_ids'):
                    raise ValueError(f'Unscoped original must remain a target-free boundary case: {row["id"]}')
                if row.get('source_question') != row['question']:
                    raise ValueError(f'Original boundary wording is not preserved verbatim: {row["id"]}')
            if decision['status'] == 'positive-target-justified-by-authored-source-context':
                if row['kind'] != 'retrieval' or not row.get('source_question') or not row.get('adaptation_note'):
                    raise ValueError(f'Adapted positive needs a retrieval target and source wording: {row["id"]}')
                if not decision.get('original_question_preserved_verbatim') or not decision.get('paired_original_case_id'):
                    raise ValueError(f'Adapted positive lacks its paired original case: {row["id"]}')
        for aid in row['area_ids']:
            if aid not in areas:
                raise ValueError(f'Unknown persona area in case: {row["id"]} -> {aid}')
        known_journeys = {journey['id'] for journey in journey_spec['journeys']}
        if not set(row.get('primary_journeys', [])) <= known_journeys:
            raise ValueError(f'Unknown primary journey in case: {row["id"]}')
        if set(row['area_ids']) - set(area_map[row['id']]):
            raise ValueError(f'Case and persona-area inverse map disagree: {row["id"]}')
        if 'candidate_ids' in row and 'target_routes' in row:
            raise ValueError(f'Choose either candidate IDs or target routes: {row["id"]}')
        if row['kind'] == 'retrieval':
            if not row.get('candidate_ids') and not row.get('target_routes'):
                raise ValueError(f'Retrieval case needs at least one verified target: {row["id"]}')
            expected = [_verify_candidate(cid, candidates, record_ids, review_cache)
                        for cid in row.get('candidate_ids', [])]
            expected += [_resolve_route(route, routes) for route in row.get('target_routes', [])]
            if not expected:
                raise ValueError(f'Retrieval case has no expected records: {row["id"]}')
            recall_eligible = True
        else:
            if row.get('candidate_ids'):
                raise ValueError(f'Non-retrieval case may not define recall candidates: {row["id"]}')
            expected = []
            supporting = []
            for route in row.get('target_routes', []):
                supporting.append(_resolve_route(route, routes))
            recall_eligible = False
        if len({r['id'] for r in expected}) != len(expected):
            raise ValueError(f'Duplicate expected target: {row["id"]}')
        built_case = {'id': row['id'], 'origin': row['origin'], 'personas': sorted({areas[a]['persona_id'] for a in row['area_ids']}),
                      'area_ids': sorted(row['area_ids']), 'prompt': {'question': row['question']},
                      'primary_journeys': sorted(row.get('primary_journeys', [])),
                      'evaluation': {'kind': row['kind'],
                                     'expected_records': [r['id'] for r in expected] if row['kind'] == 'retrieval' else [],
                                     'target_provenance': expected if row['kind'] == 'retrieval' else [],
                                     'supporting_records': supporting if row['kind'] != 'retrieval' else [],
                                     'required_gaps': row['gaps'], 'negative_control': row['negative_control'],
                                     'source_candidates_are_assessor_targets': row.get('origin') != 'new-paraphrase',
                                     'recall_eligible': recall_eligible, 'execution_status': 'not-run'},
                      'runtime_target_leakage': 'forbidden'}
        for field in ('source_question', 'adaptation_note', 'review_decision'):
            if field in row:
                built_case[field] = row[field]
        cases.append(built_case)
    built_by_id = {case['id']: case for case in cases}
    for row in spec['additional_cases']:
        decision = row.get('review_decision', {})
        if decision.get('status') == 'original-retained-as-scope-boundary':
            positive = built_by_id.get(decision.get('paired_positive_case_id'))
            if not positive or positive.get('source_question') != row['question']:
                raise ValueError(f'Original boundary lacks its text-matched adapted positive: {row["id"]}')
            if positive['review_decision'].get('paired_original_case_id') != row['id']:
                raise ValueError(f'Adapted positive does not refer back to original boundary: {row["id"]}')
            if positive['evaluation']['target_provenance']:
                if [item['route'] for item in positive['evaluation']['target_provenance']] != decision.get('candidate_target_routes_not_scored'):
                    raise ValueError(f'Adapted positive source target differs from the reviewed candidate route: {row["id"]}')
        elif decision.get('status') == 'positive-target-justified-by-authored-source-context':
            original = built_by_id.get(decision.get('paired_original_case_id'))
            if not original or original.get('prompt', {}).get('question') != row.get('source_question'):
                raise ValueError(f'Adapted positive does not preserve its original wording: {row["id"]}')
    for journey in journey_spec['journeys']:
        fresh = [case for case in cases
                 if case['origin'] == 'new-paraphrase'
                 and case.get('primary_journeys') and journey['id'] in case['primary_journeys']
                 and case['evaluation']['kind'] == 'retrieval'
                 and case['evaluation']['expected_records']]
        if len(fresh) < 2:
            raise ValueError(f'Primary journey lacks two unhinted positive retrieval cases: {journey["id"]}')
    expected_ids = {c['id'] for c in spec['additional_cases']} | set(registry_by_id)
    if {c['id'] for c in cases} != expected_ids:
        raise ValueError('Generated persona case set is incomplete')
    coverage = []
    for persona in spec['personas']:
        coverage.append({'id': persona['id'], 'status': persona['status'],
                         'areas': [{'id': area['id'], 'interest': area['interest'], 'source': area['source'],
                                    'case_ids': sorted(area['case_ids']),
                                    'case_kinds': sorted({next(c['evaluation']['kind'] for c in cases if c['id'] == cid)
                                                          for cid in area['case_ids']}),
                                    'coverage_status': 'mapped-not-executed'}
                                   for area in persona['areas']]})
    kinds = {kind: sum(c['evaluation']['kind'] == kind for c in cases) for kind in sorted(KINDS)}
    recall_cases = [c for c in cases if c['evaluation']['recall_eligible']]
    result_coverage = {'schema': 'okf-persona-coverage.v1', 'review_status': spec['review_status'],
                       'personas': coverage, 'counts': {'personas': len(coverage), 'areas': sum(len(p['areas']) for p in coverage),
                                                        'cases': len(cases), 'frozen_question_occurrences': len(registry_cases),
                                                        'additional_cases': len(spec['additional_cases']), 'cases_by_kind': kinds,
                                                        'recall_eligible_cases': len(recall_cases),
                                                        'expected_record_targets': sum(len(c['evaluation']['expected_records']) for c in recall_cases)},
                       'recall_metric': {'status': 'not-run', 'population': 'retrieval cases only',
                                         'non_retrieval_cases_excluded': True},
                       'limitations': spec['limitations']}
    result_cases = {'schema': 'okf-persona-evaluation-cases.v1', 'review_status': spec['review_status'],
                    'runtime_input_contract': 'prompt.question only; expected targets and gap criteria are assessor-only',
                    'cases': cases, 'counts': result_coverage['counts'],
                    'recall_metric': result_coverage['recall_metric'], 'limitations': spec['limitations']}
    return result_coverage, result_cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='compare generated files without writing')
    args = parser.parse_args()
    inputs = [AUTHORING, QUESTIONS, MATRIX, INDEX, JOURNEYS]
    raw = {str(path): (ROOT / path).read_bytes() for path in inputs}
    spec = json.loads(raw[str(AUTHORING)])
    coverage, cases = build(spec, json.loads(raw[str(QUESTIONS)]), json.loads(raw[str(MATRIX)]),
                            json.loads(raw[str(INDEX)]), json.loads(raw[str(JOURNEYS)]))
    input_hashes = [{'path': str(path), 'sha256': sha(raw[str(path)]), 'bytes': len(raw[str(path)])} for path in inputs]
    coverage['inputs'] = input_hashes
    cases['inputs'] = input_hashes
    outputs = {
        'persona-coverage.json': json.dumps(coverage, ensure_ascii=False, indent=2) + '\n',
        'persona-cases.json': json.dumps(cases, ensure_ascii=False, indent=2) + '\n',
    }
    out_dir = ROOT / OUT
    if not args.check:
        out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        path = out_dir / name
        if args.check:
            if not path.is_file() or path.read_text(encoding='utf-8') != content:
                raise SystemExit(f'Persona evaluation projection differs: {name}')
        else:
            path.write_text(content, encoding='utf-8')
    print(json.dumps({'status': 'checked' if args.check else 'generated',
                      'personas': coverage['counts']['personas'], 'areas': coverage['counts']['areas'],
                      'cases': coverage['counts']['cases'], 'cases_by_kind': coverage['counts']['cases_by_kind'],
                      'recall_eligible_cases': coverage['counts']['recall_eligible_cases'],
                      'expected_record_targets': coverage['counts']['expected_record_targets'],
                      'recall_metric': 'not-run'}))


if __name__ == '__main__':
    main()
