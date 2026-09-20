#!/usr/bin/env python3
"""Bind projected personas and journeys to every supplied question occurrence."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORING = Path('domain-profile/staff-needs/journeys.json')
QUESTIONS = Path('evaluation/staff-questions/cases.json')
OUT = Path('evaluation/staff-needs')


def sha(value):
    return hashlib.sha256(value).hexdigest()


def build(spec, registry):
    cases = registry['cases']
    by_id = {c['id']: c for c in cases}
    if (len(by_id) != len(cases) or len(cases) != registry['occurrence_count']
            or len({c['question'] for c in cases}) != registry['unique_question_count']):
        raise ValueError('Question occurrence or unique wording count differs')
    personas = {p['id'] for p in spec['personas']}
    if len(personas) != len(spec['personas']):
        raise ValueError('Duplicate persona identity')
    journeys = spec['journeys'] + spec['cross_cutting_journeys']
    if len({j['id'] for j in journeys}) != len(journeys):
        raise ValueError('Duplicate journey identity')
    for journey in journeys:
        if not journey['personas'] or not set(journey['personas']) <= personas:
            raise ValueError('Unknown journey persona')
    assigned = {}
    for journey in spec['journeys']:
        if not set(journey['personas']) <= personas:
            raise ValueError('Unknown journey persona')
        for cid in journey['cases']:
            if cid not in by_id or cid in assigned:
                raise ValueError('Unknown or multiply assigned primary case')
            assigned[cid] = journey
    if set(assigned) != set(by_id):
        raise ValueError('Some supplied questions have no primary journey')
    rows = []
    for case in cases:
        journey = assigned[case['id']]
        rows.append({'id': case['id'], 'question': case['question'], 'duplicate_of': case['duplicate_of'],
                     'section': case['section'], 'journey': journey['id'], 'personas': journey['personas'],
                     'intended_decision': journey['decision'], 'ambiguities': case['ambiguities'],
                     'required_evidence': case['required_evidence'], 'source_candidate_ids': case['candidate_ids'],
                     'negative_control': journey['negative_control'],
                     'acceptance_dimensions': [r['id'] for r in registry['rubric_stages']],
                     'user_validation': 'not-run', 'specialist_acceptance': 'not-reviewed',
                     'execution': {'mapping_integrity': 'passed', 'behavioural_negative_control': 'not-run'},
                     'review_pack': f'../staff-review/cases/{case["id"]}.md'})
    for row in rows:
        if row['duplicate_of']:
            original = by_id.get(row['duplicate_of'])
            if not original or original['question'] != row['question']:
                raise ValueError('Duplicate wording is not preserved')
    return {'schema': 'okf-staff-needs-matrix.v1', 'review_status': 'projected-not-user-validated',
            'occurrences': len(rows), 'unique_questions': len({r['question'] for r in rows}),
            'primary_journeys': len(spec['journeys']), 'personas': spec['personas'],
            'cross_cutting_journeys': spec['cross_cutting_journeys'], 'cases': rows,
            'limitations': ['Mappings are project-authored hypotheses, not completed user research.',
                           'Behavioural negative controls are specified here; their execution needs separately retained evidence.',
                           'No claimant data, entitlement decisions or award calculations are required.']}


def render(result):
    lines = ['# Staff questions, projected personas and journeys', '',
             f'All **{result["occurrences"]} occurrences / {result["unique_questions"]} distinct questions** are mapped to {result["primary_journeys"]} primary journeys.',
             f'{len(result["personas"])} personas are projected from existing project roles; no user-research validation is claimed.',
             'Source-audit and assisted-reading journeys apply across the matrix.', '',
             '[Machine-readable matrix](matrix.json) · [Authoring](../../domain-profile/staff-needs/journeys.json)', '',
             '| Case | Supplied question | Primary journey | Evidence |', '| --- | --- | --- | --- |']
    for r in result['cases']:
        q = r['question'].replace('|', '\\|')
        lines.append(f'| {r["id"]} | {q} | {r["journey"]} | [Review pack]({r["review_pack"]}) |')
    lines += ['', '## What is checked and what remains open', '',
              'The producer rejects missing/multiple primary mappings, unknown personas and altered duplicate wording.',
              'Each matrix row retains source requirements, ambiguity, a negative scenario and A–H evaluation dimensions.',
              'Mapping integrity passing does not execute the scenario or approve the persona.',
              'Independent user and specialist review remains visible in every row.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    raw = {str(p): (ROOT / p).read_bytes() for p in (AUTHORING, QUESTIONS)}
    result = build(json.loads(raw[str(AUTHORING)]), json.loads(raw[str(QUESTIONS)]))
    result['inputs'] = [{'path': p, 'sha256': sha(b), 'bytes': len(b)} for p, b in raw.items()]
    outputs = {'matrix.json': json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'README.md': render(result)}
    (ROOT / OUT).mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        path = ROOT / OUT / name
        if args.check:
            if not path.is_file() or path.read_text() != content:
                raise SystemExit(f'Staff needs projection differs: {name}')
        else:
            path.write_text(content)
    print(json.dumps({'status': 'checked' if args.check else 'generated', 'occurrences': result['occurrences'],
                      'unique_questions': result['unique_questions'], 'user_validation': 'not-run'}))


if __name__ == '__main__':
    main()
