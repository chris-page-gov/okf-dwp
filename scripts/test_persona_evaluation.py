"""Mutation and integration checks for persona retrieval and boundary evaluation."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from build_persona_evaluation import ROOT, build, read_json


class PersonaEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.spec = read_json(Path('domain-profile/staff-needs/persona-evaluation.json'))
        self.questions = read_json(Path('evaluation/staff-questions/cases.json'))
        self.matrix = read_json(Path('evaluation/staff-needs/matrix.json'))
        self.index = read_json(Path('combined/context/corpus/base-index.json'))
        self.journey_spec = read_json(Path('domain-profile/staff-needs/journeys.json'))

    def make(self, spec=None, questions=None, matrix=None, index=None):
        return build(spec or self.spec, questions or self.questions,
                     matrix or self.matrix, index or self.index, self.journey_spec)

    def test_eight_personas_all_areas_and_question_cases_are_integrated(self):
        coverage, cases = self.make()
        self.assertEqual(coverage['counts']['personas'], 8)
        self.assertEqual(coverage['counts']['areas'], 21)
        self.assertEqual(coverage['counts']['frozen_question_occurrences'], 40)
        self.assertEqual(coverage['counts']['cases'], 75)
        self.assertEqual(coverage['counts']['recall_eligible_cases'], 62)
        self.assertEqual(coverage['counts']['expected_record_targets'], 263)
        self.assertEqual({row['id'] for row in cases['cases'] if row['origin'] == 'frozen-staff-question'},
                         {row['id'] for row in self.questions['cases']})
        self.assertEqual(coverage['recall_metric']['status'], 'not-run')

    def test_expected_targets_are_exact_records_with_verified_source_hashes(self):
        _, cases = self.make()
        by_id = {record['id']: record for record in self.index['records']}
        retrieval = [row for row in cases['cases'] if row['evaluation']['kind'] == 'retrieval']
        self.assertTrue(retrieval)
        for case in retrieval:
            self.assertEqual(case['evaluation']['expected_records'],
                             [entry['id'] for entry in case['evaluation']['target_provenance']])
            for provenance in case['evaluation']['target_provenance']:
                self.assertIn(provenance['id'], by_id)
                if provenance.get('candidate_id'):
                    self.assertEqual(provenance['review_status'], 'unreviewed-source-candidate')

    def test_every_retrieval_case_has_verified_source_evidence_targets(self):
        _, result = self.make()
        retrieval = [case for case in result['cases'] if case['evaluation']['kind'] == 'retrieval']
        self.assertTrue(retrieval)
        for case in retrieval:
            self.assertTrue(case['evaluation']['expected_records'], case['id'])
            self.assertTrue(case['evaluation']['target_provenance'], case['id'])
            self.assertTrue(all(record['route'].startswith('page/') for record in case['evaluation']['target_provenance']))

    def test_empty_recall_case_is_rejected(self):
        spec = copy.deepcopy(self.spec)
        case = next(row for row in spec['additional_cases'] if row['kind'] == 'retrieval')
        case.pop('candidate_ids', None)
        case['target_routes'] = []
        with self.assertRaisesRegex(ValueError, 'Retrieval case needs at least one verified target'):
            self.make(spec=spec)

    def test_non_retrieval_cases_are_excluded_from_recall_and_have_no_targets(self):
        coverage, cases = self.make()
        non_retrieval = [row for row in cases['cases'] if row['evaluation']['kind'] != 'retrieval']
        self.assertTrue(non_retrieval)
        self.assertTrue(all(not row['evaluation']['recall_eligible'] for row in non_retrieval))
        self.assertTrue(all(row['evaluation']['expected_records'] == [] for row in non_retrieval))
        self.assertTrue(all(row['evaluation']['required_gaps'] for row in non_retrieval))
        self.assertTrue(coverage['recall_metric']['non_retrieval_cases_excluded'])

    def test_all_additional_interest_cases_are_unhinted_or_authored_stage_two(self):
        _, result = self.make()
        by_id = {row['id']: row for row in result['cases']}
        for n in range(1, 7):
            self.assertEqual(by_id[f'stage2-{n:03d}']['origin'],
                             f'knowledge/evaluation-journeys.yamlld#question/stage2-{n:03d}')
        fresh = [row for row in result['cases'] if row['origin'] == 'new-paraphrase'
                 and row.get('primary_journeys') and row['evaluation']['kind'] == 'retrieval']
        for journey in self.journey_spec['journeys']:
            self.assertGreaterEqual(sum(journey['id'] in row['primary_journeys'] for row in fresh), 2)

    def test_area_without_case_is_rejected(self):
        spec = copy.deepcopy(self.spec)
        spec['personas'][0]['areas'][0]['case_ids'] = []
        with self.assertRaisesRegex(ValueError, 'has no test case'):
            self.make(spec=spec)

    def test_missing_area_registration_is_rejected(self):
        spec = copy.deepcopy(self.spec)
        spec['personas'][0]['areas'].pop()
        with self.assertRaisesRegex(ValueError, 'Unknown persona area'):
            self.make(spec=spec)

    def test_unknown_case_area_is_rejected(self):
        spec = copy.deepcopy(self.spec)
        spec['additional_cases'][0]['area_ids'].append('area/not-authored')
        with self.assertRaisesRegex(ValueError, 'Unknown persona area'):
            self.make(spec=spec)

    def test_unknown_target_route_is_rejected(self):
        spec = copy.deepcopy(self.spec)
        case = next(c for c in spec['additional_cases'] if c['id'] == 'stage2-001-pc-context')
        case['target_routes'] = ['page/not-in-corpus']
        with self.assertRaisesRegex(ValueError, 'exactly one combined corpus record'):
            self.make(spec=spec)

    def test_candidate_literal_hash_mutation_is_rejected(self):
        questions = copy.deepcopy(self.questions)
        questions['source_candidates'][0]['literal_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Candidate page literal hash differs|source hashes do not match combined index'):
            self.make(questions=questions)

    def test_source_file_hash_mutation_is_rejected(self):
        spec = copy.deepcopy(self.spec)
        spec['source_files']['knowledge/evaluation-journeys.yamlld'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Persona source hash changed'):
            self.make(spec=spec)

    def test_area_source_line_mutation_is_rejected(self):
        spec = copy.deepcopy(self.spec)
        spec['personas'][0]['areas'][0]['source']['lines'] = [1, 1]
        with self.assertRaisesRegex(ValueError, 'line locator does not contain'):
            self.make(spec=spec)

    def test_direct_target_provenance_mutation_is_rejected(self):
        index = copy.deepcopy(self.index)
        target = next(record for record in index['records'] if record['route'] == 'page/84/0035')
        target['provenance'][1]['literal_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'page text or literal hash is not verified'):
            self.make(index=index)

    def test_original_question_registry_is_not_modified_by_projection(self):
        before = (ROOT / 'evaluation/staff-questions/cases.json').read_bytes()
        self.make()
        after = (ROOT / 'evaluation/staff-questions/cases.json').read_bytes()
        self.assertEqual(before, after)

    def test_underspecified_originals_are_boundaries_and_adapted_positives_keep_targets(self):
        _, result = self.make()
        by_id = {row['id']: row for row in result['cases']}
        authored_source = ' '.join((ROOT / 'knowledge/evaluation-journeys.yamlld').read_text(encoding='utf-8').split())
        pairs = {
            'stage2-001': ('stage2-001-pc-context', ['page/84/0035']),
            'stage2-002': ('stage2-002-pc-context', ['page/84/0035']),
            'stage2-003': ('stage2-003-pc-context', ['page/77/0026']),
            'stage2-004': ('stage2-004-pc-context', ['page/77/0026']),
            'unhinted-legal-hierarchy': ('unhinted-pc-legal-hierarchy', ['page/84/0035']),
        }
        for original_id, (positive_id, routes) in pairs.items():
            original = by_id[original_id]
            positive = by_id[positive_id]
            self.assertEqual(original['evaluation']['kind'], 'boundary')
            self.assertEqual(original['evaluation']['expected_records'], [])
            self.assertEqual(original['prompt']['question'], original['source_question'])
            if original_id.startswith('stage2-'):
                self.assertIn(' '.join(original['source_question'].split()), authored_source)
            self.assertEqual(original['review_decision']['status'], 'original-retained-as-scope-boundary')
            self.assertEqual(positive['evaluation']['kind'], 'retrieval')
            self.assertEqual(positive['source_question'], original['prompt']['question'])
            self.assertEqual(positive['review_decision']['paired_original_case_id'], original_id)
            self.assertTrue(positive['review_decision']['original_question_preserved_verbatim'])
            self.assertEqual([entry['route'] for entry in positive['evaluation']['target_provenance']], routes)
            self.assertTrue(positive['evaluation']['expected_records'])

    def test_target_validity_decision_source_pin_is_checked(self):
        spec = copy.deepcopy(self.spec)
        row = next(c for c in spec['additional_cases'] if c['id'] == 'stage2-001-pc-context')
        row['review_decision']['source_context']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Source context hash changed'):
            self.make(spec=spec)

    def test_deterministic_check_passes_generated_files(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/build_persona_evaluation.py'), '--check'],
                                cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary['recall_metric'], 'not-run')


if __name__ == '__main__':
    unittest.main()
