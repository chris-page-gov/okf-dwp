"""Frozen-source and scope controls for the benefit-interaction selection proposal.

These are admission and retained-evidence controls, not legal answer scoring.
No model, acquisition, corpus regeneration or runtime assembly is performed.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from structured_context_profiles import compile_selection
from test_structured_context_profiles import fixture

ROOT = Path(__file__).resolve().parents[1]
AUTHORING = 'domain-profile/structured-units/benefit-interactions.yamlld'
BASE = 'https://chris-page-gov.github.io/okf-dwp/id/'


class BenefitInteractionsSelection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args = fixture(AUTHORING)
        cls.result = compile_selection(*cls.args, authoring_path=AUTHORING)
        cls.by_label = {entry['paragraph_labels'][0]: entry for entry in cls.args[0]['source_units']}
        cls.units = cls.args[3]

    def text(self, label):
        return self.units[self.by_label[label]['id']]['text']

    def test_all_complete_units_bind_frozen_pdf_and_exact_extraction_spans(self):
        documents = {}
        manifest = json.loads((ROOT / 'structured-units/manifest.json').read_bytes())
        inventory = {}
        for group in manifest['source_groups']:
            bound = group['inventory']
            raw = (ROOT / bound['repository_path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), bound['sha256'])
            for doc in json.loads(raw)['documents']:
                inventory[group['id'], doc['id']] = doc
        for entry in self.args[0]['source_units']:
            key = entry['family'], entry['document_id']
            if key not in documents:
                doc = inventory[key]
                pdf = (ROOT / doc['pdf_path']).read_bytes()
                raw = (ROOT / doc['pages_path']).read_bytes()
                extracted = json.loads(raw)
                self.assertEqual(hashlib.sha256(pdf).hexdigest(), entry['source_sha256'])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['pages_sha256'])
                self.assertEqual(extracted['source_sha256'], entry['source_sha256'])
                self.assertEqual(extracted['document_id'], key[1])
                documents[key] = extracted
            chunks = []
            for span in entry['spans']:
                literal = documents[key]['pages'][span['page']-1]['text'].encode()[span['start_utf8']:span['end_utf8']]
                self.assertEqual(hashlib.sha256(literal).hexdigest(), span['literal_sha256'])
                chunks.append(literal.decode())
            self.assertEqual('\n'.join(chunks), self.units[entry['id']]['text'])
        self.assertEqual(len(documents), 10)
        self.assertEqual(len(self.args[0]['source_units']), 78)

    def test_routes_require_the_exact_declared_conjunction_and_preserve_inheritance(self):
        before = deepcopy(self.args)
        result = compile_selection(*self.args, authoring_path=AUTHORING)
        self.assertEqual(before, self.args)
        self.assertEqual(result['records'], self.args[1]['records'])
        self.assertEqual(result['assertions'][:len(self.args[1]['assertions'])], self.args[1]['assertions'])
        self.assertEqual(result['requirements'][:len(self.args[1]['requirements'])], self.args[1]['requirements'])
        additions = result['assertions'][len(self.args[1]['assertions']):]
        profiles = self.args[0]['profiles']
        self.assertEqual(len(additions), 132)
        declared = {tuple(p['when_all']) for p in profiles}
        self.assertTrue(all(tuple(a['context_guard']['when_all']) in declared for a in additions))
        for p in profiles:
            for removed in p['when_all']:
                reduced = set(p['when_all']) - {removed}
                self.assertFalse(set(p['when_all']) <= reduced)
        pair = next(p for p in profiles if p['id'].endswith('/iidb-jsa-income-and-overlap'))
        self.assertEqual(pair['when_all'], [BASE+'staff-domain/iidb', BASE+'staff-domain/jsa'])
        self.assertNotIn(BASE+'staff-domain/esa', pair['when_all'])
        self.assertTrue(all(a['assertion_status'] == 'model-derived' for a in additions))

    def test_complete_cross_page_examples_and_distinct_care_cases_survive(self):
        rea = self.text('71776')
        self.assertEqual([s['page'] for s in self.by_label['71776']['spans']], [122, 123, 124])
        for n in range(1, 7):
            self.assertIn('Example '+str(n), rea)
        self.assertIn('has not given up regular employment and remains', rea)
        self.assertIn('first claim for REA after reaching pensionable age', self.text('71766'))
        self.assertIn('do not apply to people receiving “frozen” REA', self.text('71773'))
        self.assertIn('19.11.92 to 16.8.93', self.text('60043'))
        self.assertIn('From 17.8.93', self.text('60044'))
        self.assertIn('hours spent in caring are not added together', self.text('60044'))
        self.assertIn('two or more people are caring for the same', self.text('60026'))
        self.assertIn('Example', self.text('60026'))
        self.assertIn('Exceptions', self.text('60069'))
        self.assertIn('Example', self.text('60069'))

    def test_table_scope_source_discrepancy_and_unknown_amounts_remain_visible(self):
        table = self.text('17085')
        self.assertEqual([s['page'] for s in self.by_label['17085']['spans']], [10, 11])
        self.assertIn('PIP daily', table)
        self.assertIn('18092', table)
        self.assertIn('17092', self.text('17086'))
        self.assertIn('Service pensions instrument', self.text('17092'))
        self.assertIn('fully disregard', self.text('28356'))
        self.assertIn('daily living component', self.text('51233'))
        self.assertIn('may be entitled to CA even if it is not payable', self.text('78105'))
        self.assertIn('has to actually be in payment', self.text('78057'))
        self.assertIn('8.4.87', self.text('64020'))
        self.assertIn('6.4.87', self.text('28065'))
        self.assertIn('6.4.87', self.text('51033'))
        for profile in self.args[0]['profiles']:
            if profile['id'].rsplit('/', 1)[1] in {'iidb-additional-benefit-routes', 'iidb-jsa-income-and-overlap', 'iidb-esa-income-and-overlap'}:
                self.assertIn('us-date-wording', {o['key'] for o in profile['missing_obligations']})
        known = {r['id'] for r in self.args[2]+self.result['records']}
        for profile in self.result['requirements'][len(self.args[1]['requirements']):]:
            self.assertTrue(set(profile['required']) - known)
        war = next(p for p in self.args[0]['profiles'] if p['id'].endswith('/pip-war-attendance-adjustment'))
        self.assertIn('all-rates', {o['key'] for o in war['missing_obligations']})
        self.assertIn('scheme-name', {o['key'] for o in war['missing_obligations']})
        self.assertTrue(all(p['answerability'] == 'insufficient-until-open-obligations-resolved' for p in self.args[0]['profiles']))


if __name__ == '__main__':
    unittest.main()
