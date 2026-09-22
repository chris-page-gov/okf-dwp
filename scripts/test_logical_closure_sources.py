"""Independent regression controls for the bounded dependency-source review.

Frozen DWP extracts are the evidence; author declarations are untrusted proposals.
These tests check passage boundaries and retained qualifications, never entitlement.
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest

from build_logical_units import check_override

ROOT = Path(__file__).resolve().parents[1]
AUTHOR = ROOT / 'domain-profile/logical-units/closure-dependencies.yamlld'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class ClosureSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(AUTHOR.read_text())
        cls.old = json.loads((ROOT / 'domain-profile/logical-units/overrides.json').read_text())
        cls.documents = {d['document_id']: d for d in cls.data['documents']}
        cls.units = {u['key']: (d, u) for d in cls.data['documents'] for u in d['units']}
        cls.pages = {d['document_id']: json.loads((ROOT / d['pages_path']).read_text())['pages'] for d in cls.data['documents']}

    def literal(self, key):
        doc, unit = self.units[key]
        return '\n'.join(self.pages[doc['document_id']][s['page'] - 1]['text'].encode()[s['start_utf8']:s['end_utf8']].decode() for s in unit['spans'])

    def test_original_source_bindings_and_non_overlapping_units(self):
        old_docs = {d['document_id']: d for d in self.old['documents']}
        for doc in self.data['documents']:
            with self.subTest(document=doc['document_id']):
                inventory_raw = (ROOT / doc['inventory_path']).read_bytes()
                self.assertEqual(digest(inventory_raw), doc['inventory_sha256'])
                source = next(d for d in json.loads(inventory_raw)['documents'] if d['id'] == doc['document_id'])
                self.assertEqual(digest((ROOT / source['pdf_path']).read_bytes()), doc['source_sha256'])
                self.assertEqual(digest((ROOT / source['pages_path']).read_bytes()), doc['pages_sha256'])
                merged = copy.deepcopy(doc)
                merged['units'] = old_docs.get(doc['document_id'], {}).get('units', []) + doc['units']
                check_override(source, self.pages[doc['document_id']], merged, doc['inventory_sha256'])

    def test_new_slice_is_bounded_and_not_specialist_accepted(self):
        self.assertEqual(len(self.units), 20)
        self.assertEqual(sum(bool(d['units']) for d in self.data['documents']), 6)
        self.assertEqual(sum(len(u['spans']) > 1 for _, u in self.units.values()), 12)
        self.assertEqual(sum(s['end_utf8'] - s['start_utf8'] for _, u in self.units.values() for s in u['spans']), 51900)
        for _, unit in self.units.values():
            self.assertEqual(unit['specialist_review'], 'not-reviewed')
            self.assertEqual(unit['review_status'], 'agent-reviewed-boundary-only')

    def test_independently_declared_source_phrases_remain(self):
        self.assertEqual(len(self.data['controls']), 14)
        for control in self.data['controls']:
            with self.subTest(unit=control['unit_key']):
                text = self.literal(control['unit_key'])
                for phrase in control['must_contain']:
                    self.assertIn(phrase, text)

    def test_supersession_keeps_late_notification_continuation_and_citations(self):
        rule = self.literal('spc-supersession-04642')
        self.assertIn('Except where DMG 04643 - 04644 apply', rule)
        self.assertIn('where SPC is paid in advance', rule)
        self.assertIn('where SPC is paid in arrears', rule)
        exception = self.literal('spc-supersession-04643-044')
        self.assertIn('04204 -\n04218', exception)
        self.assertIn('2.2 the date of notification', exception)
        self.assertIn('reg 7(2)(b)(ii)', exception)
        self.assertEqual([s['page'] for s in self.units['spc-supersession-04643-044'][1]['spans']], [102, 103])

    def test_memo_keeps_all_conditions_notes_and_complete_uc_example(self):
        text = self.literal('adm-memo-09-25-absence')
        for number in range(1, 6):
            self.assertRegex(text, rf'(?m)^\s+{number}\. ')
        self.assertIn('Note 1.', text)
        self.assertIn('Note 2.', text)
        self.assertIn('52 weeks', text)
        self.assertIn('6 months in Universal', text)
        self.assertIn('26 weeks for all other benefts', text)
        example = self.literal('adm-memo-09-25-example-uc')
        self.assertIn('2 months before the evacuation', example)
        self.assertIn('11.10.2025', example)
        self.assertTrue(example.rstrip().endswith('only allowable to that date.'))
        self.assertNotIn('Example 3', example)

    def test_memo_route_is_supported_by_both_source_and_annotation(self):
        old = next(u for d in self.old['documents'] for u in d['units'] if u['key'] == 'uc-c1988')
        pages = self.pages['adm-chapter-c1']
        source = '\n'.join(pages[s['page'] - 1]['text'].encode()[s['start_utf8']:s['end_utf8']].decode() for s in old['spans'])
        self.assertIn('[See Memo ADM 09-25]', source)
        self.assertIn('C1988', self.literal('adm-memo-09-25-annotations'))
        self.assertIn('18.07.2025', self.literal('adm-memo-09-25-introduction'))
        self.assertIn('do not impact any other entitlement conditions', self.literal('adm-memo-09-25-introduction'))
        # The earlier claim-date wording is retained, not corrected to hide a possible tension.
        self.assertIn('17.07.2025', self.literal('adm-memo-09-25-example-hrt'))

    def test_missing_f1093_is_not_substituted_with_a_different_definition(self):
        pages = self.pages['adm-chapter-f1']
        self.assertFalse(any(re.search(r'(?m)^F1093\s', p['text']) for p in pages))
        self.assertEqual(self.literal('uc-f1085-099-reserved').strip(), 'F1085 – F1099')
        row = next(r for r in self.data['reference_dispositions'] if r['literal_reference'] == 'ADM E2092 and F1093')
        self.assertEqual(row['target_status'], 'partially-identified-source-mismatch')
        self.assertIn('intended target remains unresolved', row['note'])

    def test_p4051_scope_mismatch_is_exposed(self):
        text = self.literal('pip-mobility-p4051-052')
        self.assertIn('overlapping benefit', text)
        self.assertIn('Mobility component is payable if the claimant is in a care home.', text)
        self.assertNotIn('P4053 Motability', text)
        row = next(r for r in self.data['reference_dispositions'] if r['literal_reference'] == 'P4051')
        self.assertEqual(row['target_status'], 'identified-source-scope-mismatch')
        self.assertIn('hospital qualification', row['note'])
        self.assertEqual(row['legal_effect_status'], 'unresolved')

    def test_cross_document_routes_bind_exact_owners_and_original_source_spans(self):
        combined = dict(self.units)
        combined.update({u['key']: (d, u) for d in self.old['documents'] for u in d['units']})
        seen = set()
        for document in self.data['documents']:
            for route in document['proposals']:
                a, b = route['source_unit_key'], route['target_unit_key']
                self.assertEqual(combined[a][0]['document_id'], document['document_id'])
                self.assertEqual(combined[b][0]['document_id'], route['target_document_id'])
                self.assertEqual(route['evidence_spans'], combined[a][1]['spans'])
                self.assertIn(route['predicate'], ['http://purl.org/dc/terms/requires', 'http://purl.org/dc/terms/references'])
                key = (a, b, route['predicate'])
                self.assertNotIn(key, seen)
                seen.add(key)
        self.assertEqual(len(seen), 16)

    def test_every_old_unknown_remains_distinct_from_target_identification(self):
        original = json.loads((ROOT / 'domain-profile/logical-units/reference-review.json').read_text())['references']
        self.assertEqual(len(self.data['reference_dispositions']), len(original))
        for old, reviewed in zip(original, self.data['reference_dispositions']):
            self.assertEqual(reviewed['literal_reference'], old['literal_reference'])
            self.assertEqual(reviewed['evidence_spans'], old['evidence_spans'])
            self.assertEqual(reviewed['status'], 'unresolved')
            self.assertEqual(reviewed['legal_effect_status'], 'unresolved')
            self.assertEqual(reviewed['specialist_review'], 'not-reviewed')
        pip = self.literal('pip-relevant-age-p4076-086')
        self.assertIn('[See memo ADM 6/25]', pip)
        self.assertIn('[See Memo ADM 11-25]', self.literal('pip-absence-c2056-069'))


if __name__ == '__main__':
    unittest.main()
