#!/usr/bin/env python3
"""Report exact staff/profile/unit coverage from one retained logical evaluation.

Read-only source analysis, with no acquisition, model call or answer grading.
Write a fresh output directory; never replace retained observations.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path

from build_bundle import load_yaml
from build_logical_units import Inputs, strict_json
from logical_unit_authoring import load_semantics

ROOT = Path(__file__).resolve().parents[1]
PLAN = 'domain-profile/logical-units/coverage-plan.json'
RUN = 'evaluation/logical-units/run/summary.json'
QUESTIONS = 'evaluation/staff-questions/cases.json'
MANIFEST = 'logical-units/manifest.json'
CONTEXT = 'logical-context/manifest.json'


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pretty(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def load(inputs, path):
    return strict_json(inputs.read(path, limit=16 * 1024 * 1024))


def require_binding(inputs, ref):
    return inputs.read(ref['path'], ref['sha256'], ref['bytes'])


def observed_staff_rows(summary, case_ids):
    rows = [r for r in summary['rows'] if r['stage'] == 'units' and r['case_id'] in case_ids]
    by_key = {(r['case_id'], r['max_bytes']): r for r in rows}
    require(len(by_key) == len(rows), 'Duplicate observed staff budget row')
    require(set(by_key) == {(case, budget) for case in case_ids for budget in (32768, 524288)},
            'Incomplete retained staff/budget observations')
    return by_key


def canonical_obligations(case_id, obligations, required_ids):
    prefix = 'https://chris-page-gov.github.io/okf-dwp/id/obligation/staff/' + case_id + '/'
    result = [{**row, 'authored_id': row['id'],
               'id': prefix + row['category'] + '/' + row['id']} for row in obligations]
    identifiers = [row['id'] for row in result]
    expected = {identifier for identifier in required_ids if identifier.startswith(prefix)}
    require(len(set(identifiers)) == len(identifiers), 'Duplicate canonical legacy obligation identity')
    require(set(identifiers) == expected,
            'Canonical legacy obligation identity differs from the recorded required set')
    return result


def compile_report(root=ROOT):
    inputs = Inputs(root)
    inputs.read('scripts/build_semantic_coverage.py')
    plan, registry, summary = (load(inputs, p) for p in (PLAN, QUESTIONS, RUN))
    require(plan['schema'] == 'okf-dwp-semantic-coverage-plan.v1', 'Unknown coverage plan')
    require(sha(inputs.read(QUESTIONS)) == plan['question_registry_sha256'], 'Question wording differs from reviewed plan')
    retained = {r['path']: r for r in summary['inputs']}
    for path in (QUESTIONS, CONTEXT, 'logical-context/base-index.json'):
        require(path in retained, 'Evaluation lacks coverage input: ' + path)
        require_binding(inputs, retained[path])
    context = load(inputs, CONTEXT)
    admitted = {r['path']: r for r in context['inputs']}
    require(MANIFEST in admitted, 'Context lacks unit producer binding')
    require_binding(inputs, admitted[MANIFEST])
    unit_manifest = load(inputs, MANIFEST)
    overrides, _, profiles, _, _ = load_semantics(inputs)
    # Current authoring cannot be read as though it belonged to an older replay.
    for path in list(inputs.files):
        if path.startswith('domain-profile/logical-units/') and path != PLAN:
            require(path in admitted, 'Context does not bind current authoring: ' + path)
            require_binding(inputs, admitted[path])
    profile_map = {p['id']: p for p in profiles['profiles']}
    legacy_path = 'domain-profile/staff-semantic/profiles.yamlld'
    inputs.read(legacy_path)
    legacy = {p['id']: p for p in load_yaml(Path(root) / legacy_path)['profiles']}
    old_requirements = {p['id'].rsplit('/', 1)[-1]: p for p in load(inputs, 'evaluation/semantic-expansion/assembly-index.json')['requirements']}
    lessons = {r['case_id']: r for r in load(inputs, 'docs/learning/question-coverage.json')}
    programme = load(inputs, 'domain-profile/learning/programme.yamlld')
    steps = {s['id']: s for p in programme['paths'] for s in p['steps']}
    cases = registry['cases']
    case_ids = {c['id'] for c in cases}
    require(len(case_ids) == len(cases) == 40, 'Staff occurrence census differs')
    observed = observed_staff_rows(summary, case_ids)
    clusters = {}
    for cluster in plan['clusters']:
        for case in cluster['case_ids']:
            require(case not in clusters, 'Repeated primary coverage cluster')
            clusters[case] = cluster
    require(set(clusters) == case_ids, 'Coverage plan must include every staff occurrence exactly once')

    catalogues, authored = {}, {}
    for ref in unit_manifest['documents']:
        path = 'logical-units/' + ref['path']
        raw = inputs.read(path, ref['sha256'], ref['bytes'], limit=4 * 1024 * 1024)
        require(0 < ref['decoded_bytes'] <= 4 * 1024 * 1024, 'Catalogue decoded limit')
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
            decoded = stream.read(ref['decoded_bytes'] + 1)
        require(len(decoded) == ref['decoded_bytes'] and sha(decoded) == ref['decoded_sha256'], 'Catalogue integrity differs')
        doc = strict_json(decoded)
        catalogues[doc['document_id']] = path, doc
        for unit in doc['units']:
            if unit['boundary_status'] == 'author-declared':
                require(unit['key'] not in authored, 'Duplicate authored unit')
                authored[unit['key']] = {**unit, 'catalogue': path, 'document_id': doc['document_id']}
    candidates = []
    for candidate in registry['source_candidates']:
        evidence_path = 'evaluation/staff-review/evidence/' + candidate['id'] + '.json'
        evidence = load(inputs, evidence_path)
        path, doc = catalogues[candidate['document_id']]
        source = doc['source']
        require(source['sha256'] == candidate['source_sha256'] and source['pages_sha256'] == candidate['pages_sha256'], 'Candidate source version differs')
        raw = inputs.read(source['pages_path'], source['pages_sha256'])
        pages = strict_json(raw)['pages']
        text = next(p['text'] for p in pages if p['page'] == candidate['page'])
        excerpt = evidence['excerpt']
        require(text[excerpt['start']:excerpt['end']] == excerpt['text'] and sha(excerpt['text'].encode()) == excerpt['sha256'], 'Candidate literal differs')
        low = len(text[:excerpt['start']].encode())
        high = len(text[:excerpt['end']].encode())
        overlapping = [u for u in doc['units'] if any(s['page'] == candidate['page'] and s['start_utf8'] < high and low < s['end_utf8'] for s in u['spans'])]
        candidates.append({'id': candidate['id'], 'review_evidence_path': evidence_path, 'document_id': candidate['document_id'], 'record_id': candidate['record_id'], 'route': candidate['route'], 'page': candidate['page'], 'anchor': candidate['anchor'], 'source': source, 'catalogue': path, 'excerpt_utf8_span': {'start': low, 'end': high, 'sha256': excerpt['sha256']}, 'overlapping_units': [{k: u[k] for k in ('id', 'key', 'boundary_status', 'completeness', 'spans', 'text_sha256')} for u in overlapping], 'status': 'candidate-only; geometric overlap is not semantic equivalence or legal applicability'})
    for location in plan['reviewed_source_locations']:
        pages = load(inputs, location['pages_path'])['pages']
        text = next(p['text'] for p in pages if p['page'] == location['page'])
        require(sha(text.encode()) == location['text_sha256'], 'Previously inspected source text differs')

    def unit_refs(keys):
        return [{k: authored[key][k] for k in ('key', 'id', 'document_id', 'catalogue', 'label', 'paragraph_labels', 'spans', 'boundary_status', 'completeness', 'review_status', 'specialist_review')} for key in sorted(set(keys))]

    rows = []
    for case in cases:
        identifier = case['id']
        current = observed[identifier, 524288]
        active = [profile_map[p.rsplit('/', 1)[-1]] for p in current['active_requirements']]
        active_keys = [key for p in active for key in p['required_unit_keys']]
        cluster = clusters[identifier]
        lesson = lessons[identifier]
        require(lesson['question_sha256'] == sha(case['question'].encode()), 'Learning question hash differs')
        preserved = canonical_obligations(identifier, legacy[identifier]['obligations'],
                                          old_requirements[identifier]['required'])
        rows.append({'case_id': identifier, 'question': case['question'], 'question_sha256': sha(case['question'].encode()), 'duplicate_of': case['duplicate_of'], 'section_context_not_silently_injected': case['section'], 'current_unit_profile_status': 'partial-profile-active' if active else 'no-unit-profile-active', 'active_profile_ids': current['active_requirements'], 'active_profile_scopes': [p['scope'] for p in active], 'active_profile_missing_obligations': [{'profile': p['id'], 'obligations': p['missing_obligations']} for p in active], 'active_profile_authored_source_units': unit_refs(active_keys), 'present_contextual_authored_units': unit_refs(cluster['present_authored_unit_keys']), 'authored_relevance_limit': 'Presence or declared requirement does not assert actual retention, complete task coverage or applicability.', 'legacy_page_profile_id': old_requirements[identifier]['id'], 'legacy_page_profile_source': legacy_path, 'legacy_concept_ids': old_requirements[identifier]['when_all'], 'missing_legacy_obligations_preserved': preserved, 'candidate_only_source_ids': case['candidate_ids'], 'candidate_source_register': '#/candidate_sources', 'required_evidence': case['required_evidence'], 'ambiguities': case['ambiguities'], 'historical_scope_gaps': case['scope_gaps'], 'historical_scope_caution': 'Older source-not-acquired wording is not a current census. ADM is now acquired in the frozen source family.', 'observed_logical_runs': [observed[identifier, budget] for budget in (32768, 524288)], 'primary_cluster': cluster['id'], 'next_work': cluster['next_work'], 'learning_preservation': {'primary_path': lesson['primary_path'], 'lesson_ids': lesson['lesson_ids'], 'lessons': [{'id': steps[s]['id'], 'semantic_id': steps[s]['@id'], 'route': steps[s]['route'], 'evidence_routes': steps[s]['evidence_routes']} for s in lesson['lesson_ids']], 'candidate_routes': lesson['candidate_routes'], 'policy': 'Keep old question and lesson IDs, hashes and page routes. Add unit references; do not silently replace frozen assessments.'}})
    full = [observed[c, 524288] for c in case_ids]
    counts = {'staff_occurrences': len(rows), 'unique_questions': len({r['question'] for r in rows}), 'active_logical_profiles_on_staff_questions': sum(bool(r['active_requirements']) for r in full), 'no_active_logical_profile': sum(not r['active_requirements'] for r in full), 'staff_contexts_insufficient_512KiB': sum(r['evidence_status'] == 'insufficient' for r in full), 'staff_contexts_with_no_returned_relationships_512KiB': sum(r['relationships'] == 0 for r in full), 'all_source_units': unit_manifest['counts']['records'], 'authored_units': unit_manifest['counts']['authored_units'], 'machine_uncertain_units': unit_manifest['counts']['machine_uncertain_units'], 'legacy_obligations_preserved': sum(len(r['missing_legacy_obligations_preserved']) for r in rows), 'legacy_source_candidates': len(candidates)}
    bindings = sorted(inputs.files.values(), key=lambda r: r['path'])
    result = {'schema': 'okf-dwp-semantic-coverage-triage.v2', 'snapshot': 'dwp-semantic-coverage-' + sha(pretty(bindings))[:20], 'authority': 'Deterministic coverage census over model-authored triage; no source acquisition, model call or specialist acceptance.', 'evaluation_path': RUN, 'counts': counts, 'input_bindings': bindings, 'prioritised_clusters': plan['clusters'], 'candidate_sources': candidates, 'source_locations_read_for_triage': plan['reviewed_source_locations'], 'cases': rows, 'limitations': plan['boundaries']}
    lines = ['# Staff-question semantic coverage', '', f"{counts['active_logical_profiles_on_staff_questions']} of 40 occurrences activate a bounded logical-unit profile; {counts['no_active_logical_profile']} do not. {counts['staff_contexts_insufficient_512KiB']} retained 512 KiB contexts are insufficient. This is a coverage census, not legal answer grading.", '', f"{counts['authored_units']} authored boundaries and {counts['machine_uncertain_units']} uncertain machine candidates are different denominators. All {counts['legacy_obligations_preserved']} legacy obligations remain recorded.", '', 'The machine-readable [audit](audit.json) binds every input, exact candidate source location, profile, open obligation and lesson route.', '', '| Staff case | Active profiles | Primary next cluster |', '|---|---|---|']
    for row in rows:
        lines.append('| ' + row['case_id'] + ' | ' + (', '.join(p.rsplit('/', 1)[-1] for p in row['active_profile_ids']) or 'None') + ' | ' + row['primary_cluster'] + ' |')
    lines += ['', '## Boundaries', '', *['- ' + s for s in result['limitations']], '', 'Retain page locations and existing lesson/question IDs. New source units and graphs do not silently satisfy previous legal or learning obligations.', '']
    return {'audit.json': pretty(result), 'audit.md': '\n'.join(lines).encode()}


def write_outputs(output, outputs, check=False):
    output = Path(output)
    if check:
        require(output.is_dir() and not output.is_symlink(), 'Missing regular output directory')
        require({p.name for p in output.iterdir()} == set(outputs), 'Coverage output census differs')
        for name, raw in outputs.items():
            path = output / name
            require(path.is_file() and not path.is_symlink() and path.read_bytes() == raw, 'Coverage output differs: ' + name)
    else:
        output.mkdir(parents=True, exist_ok=False)
        for name, raw in outputs.items():
            with (output / name).open('xb') as handle:
                handle.write(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='Fresh evidence directory, or retained directory with --check')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    outputs = compile_report()
    write_outputs(args.output, outputs, args.check)
    print('Verified 40 staff occurrences, exact source candidates, open obligations and learning references.')


if __name__ == '__main__':
    main()
