"""Validate teaching references and fail-closed producer bounds."""
import json
import unittest
from copy import deepcopy
from unittest.mock import patch
from build_bundle import ROOT, load_yaml
from build_learning_paths import SOURCE, add_learning
from build_context_discovery import Inputs

class LearningPathsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_yaml(ROOT / SOURCE)
        cls.routes = {r for p in cls.doc['paths'] for s in p['steps'] for r in s['evidence_routes']} | {r for p in cls.doc['paths'] for r in p['persona_routes']}

    def compile(self, doc):
        records = [{'route': r} for r in self.routes]
        with patch('build_learning_paths.load_yaml', return_value=doc):
            result = add_learning(Inputs(ROOT), records, {}, '2026-09-22T00:00:00Z')
        return result, records

    def test_all_lessons_and_question_occurrences(self):
        presentation, records = self.compile(self.doc)
        self.assertEqual(len(presentation['paths']), 12)
        self.assertEqual(sum(len(p['steps']) for p in presentation['paths']), 112)
        self.assertEqual(len(records) - len(self.routes), 112)
        self.assertLessEqual(max(len(p['steps']) for p in presentation['paths']), 24)

    def test_missing_source_cycle_registry_change_and_overlong_outcome_fail(self):
        for change in ('missing', 'cycle', 'registry', 'oversize'):
            doc = deepcopy(self.doc)
            if change == 'missing': doc['paths'][0]['steps'][0]['evidence_routes'] = ['page/missing']
            if change == 'cycle': doc['paths'][0]['prerequisites'] = ['p12']
            if change == 'registry': doc['question_registry_sha256'] = '0'*64
            if change == 'oversize': doc['paths'][0]['steps'][0]['outcome'] = 'x'*801
            with self.subTest(change=change), self.assertRaises(ValueError): self.compile(doc)

    def test_generated_descriptor_contains_authored_routes_and_source_bound_version(self):
        descriptor = json.loads((ROOT/'combined/okf-explorer.json').read_bytes())
        expected, _ = self.compile(self.doc)
        self.assertEqual(descriptor['learning_presentation'], expected)
        self.assertEqual(descriptor['counts']['records'], 20158)

if __name__ == '__main__': unittest.main()
