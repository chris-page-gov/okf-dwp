"""Frozen P5 transition boundary and profile controls; no legal answer grading."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from test_logical_unit_sources import reconstruct, validate_phrases

ROOT = Path(__file__).resolve().parents[1]
AUTHOR = ROOT / 'domain-profile/logical-units'
BASE = 'https://chris-page-gov.github.io/okf-dwp/id/'
REVIEW = 'unreviewed-specialist-review-required'
DCT = 'http://purl.org/dc/terms/'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def bounded_json(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 32 * 1024 * 1024:
        raise ValueError('Unadmitted source fixture')
    return json.loads(path.read_bytes())


class PipTransitionClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.closure = bounded_json(AUTHOR / 'closure-pip-transition.yamlld')
        cls.original = bounded_json(AUTHOR / 'overrides.json')
        cls.targets = bounded_json(AUTHOR / 'closure-dependencies.yamlld')
        cls.document = cls.closure['documents'][0]
        cls.pages = bounded_json(ROOT / cls.document['pages_path'])['pages']
        cls.units = {u['key']: u for u in cls.document['units']}
        cls.controls = {c['unit_key']: c for c in cls.closure['controls']}

    def text(self, key):
        return reconstruct(self.document, self.units[key], self.pages)

    def test_frozen_document_and_extraction_bindings(self):
        d = self.document
        inv = ROOT / d['inventory_path']
        self.assertEqual(digest(inv.read_bytes()), d['inventory_sha256'])
        source = next(s for s in bounded_json(inv)['documents'] if s['id'] == d['document_id'])
        self.assertEqual(digest((ROOT / d['pdf_path']).read_bytes()), source['sha256'])
        self.assertEqual(digest((ROOT / d['pages_path']).read_bytes()), source['pages_sha256'])
        self.assertEqual(d['source_sha256'], source['sha256'])
        self.assertEqual(d['pages_sha256'], source['pages_sha256'])
        self.assertEqual(d['observed_at'], source['observed_at'])
        self.assertEqual(d['source_dates']['document'], source['document_dates'])
        self.assertIsNone(d['source_dates']['document']['published_at'])

    def test_all_spans_are_exact_contiguous_and_do_not_replace_old_units(self):
        seen = {}
        units = [u for d in self.original['documents'] if d['document_id'] == self.document['document_id'] for u in d['units']]
        units += list(self.units.values())
        self.assertEqual(len({u['key'] for u in units}), len(units))
        for u in units:
            self.assertTrue(reconstruct(self.document, u, self.pages).strip())
            for s in u['spans']:
                for start, end in seen.get(s['page'], []):
                    self.assertTrue(s['end_utf8'] <= start or end <= s['start_utf8'])
                seen.setdefault(s['page'], []).append((s['start_utf8'], s['end_utf8']))

    def test_source_conditions_examples_and_end_of_section_are_retained(self):
        for key, control in self.controls.items():
            with self.subTest(key=key):
                validate_phrases(self.text(key), control)
        self.assertNotIn('P5093', self.text('pip-transfer-invitations-p5016-5023'))

    def test_stopping_at_a_page_boundary_is_detected(self):
        for key in ['pip-transfer-invitations-p5016-5023', 'pip-transfer-no-claim-p5046-5052',
                    'pip-transfer-terminal-p5065', 'pip-transfer-fixedterm-p5066-5070']:
            truncated = copy.deepcopy(self.units[key])
            truncated['spans'].pop()
            text = reconstruct(self.document, truncated, self.pages)
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_phrases(text, self.controls[key])

    def test_altered_literal_and_skipped_continuation_are_rejected(self):
        unit = copy.deepcopy(self.units['pip-transfer-invitations-p5016-5023'])
        unit['spans'][0]['end_utf8'] -= 1
        with self.assertRaisesRegex(ValueError, 'Altered source span'):
            reconstruct(self.document, unit, self.pages)
        unit = copy.deepcopy(self.units['pip-transfer-invitations-p5016-5023'])
        unit['spans'].pop(1)
        with self.assertRaisesRegex(ValueError, 'Incomplete cross-page continuation'):
            reconstruct(self.document, unit, self.pages)

    def test_profile_paths_use_actual_declared_edges(self):
        documents = self.original['documents'] + self.targets['documents'] + self.closure['documents']
        units = {u['key']: u for d in documents for u in d['units']}
        pairs = set()
        for u in units.values():
            pairs.update((cid, u['key']) for cid in u.get('concept_ids', []))
            pairs.update((u['key'], key) for k in ['support_unit_keys', 'reference_unit_keys'] for key in u.get(k, []))
        for d in documents:
            pairs.update((p['source_unit_key'], p['target_unit_key']) for p in d['proposals'])
        for profile in self.closure['profiles']:
            self.assertTrue(set(profile['required_unit_keys']) <= set(units))
            for path in profile['required_paths']:
                self.assertIn(path['seed'], profile['when_all'])
                route = [path['seed'], *path['unit_keys']]
                for edge in zip(route, route[1:]):
                    self.assertIn(edge, pairs)
        age = next(p for p in self.closure['profiles'] if p['id'] == 'logical-pip-pension-age')
        self.assertIn('pip-relevant-age-p4076-086', age['required_unit_keys'])
        self.assertNotIn('pip-p4016', age['required_unit_keys'])

    def test_open_references_retain_exact_source_spans(self):
        for ref in self.closure['reference_additions']:
            self.assertEqual(ref['status'], 'unresolved')
            self.assertEqual(ref['document_id'], self.document['document_id'])
            self.assertEqual(ref['evidence_spans'], self.units[ref['source_unit_key']]['spans'])
            self.assertIn(ref['literal_reference'], self.text(ref['source_unit_key']))
        self.assertTrue(any(r['literal_reference'] == 'ADM Chapter P3' for r in self.closure['reference_additions']))

    def test_no_boundary_or_profile_claims_specialist_acceptance(self):
        self.assertEqual(self.closure['specialist_review'], 'not-reviewed')
        self.assertFalse(self.closure['concept_additions'])
        self.assertFalse(self.closure['alias_additions'])
        for u in self.units.values():
            self.assertEqual(u['review_status'], 'agent-reviewed-boundary-only')
            self.assertEqual(u['specialist_review'], 'not-reviewed')
        for p in self.document['proposals']:
            self.assertEqual(p['assertion_status'], 'model-derived')
            self.assertEqual(p['review_status'], REVIEW)
            self.assertIn(p['predicate'], [DCT + 'references', DCT + 'requires'])
        for p in self.closure['profiles']:
            self.assertEqual(p['assertion_status'], 'model-derived')
            self.assertEqual(p['review_status'], REVIEW)
            self.assertEqual(p['answerability'], 'insufficient-until-open-obligations-resolved')
            self.assertTrue({'legal-version', 'applicability', 'specialist-review'} <= {o['id'] for o in p['missing_obligations']})

    def test_staff_duplicates_and_learning_evidence_remain_identical(self):
        cases = {r['id']: r for r in bounded_json(ROOT / 'evaluation/staff-questions/cases.json')['cases']}
        self.assertEqual(cases['staff-026']['question'], cases['staff-033']['question'])
        lessons = {r['case_id']: r for r in bounded_json(ROOT / 'docs/learning/question-coverage.json')}
        self.assertEqual(lessons['staff-026']['question_sha256'], lessons['staff-033']['question_sha256'])
        for case in ['staff-026', 'staff-032', 'staff-033']:
            self.assertTrue(lessons[case]['candidate_routes'])
            self.assertTrue(lessons[case]['lesson_ids'])
            self.assertEqual(lessons[case]['question_sha256'], digest(cases[case]['question'].encode()))


if __name__ == '__main__':
    unittest.main()
