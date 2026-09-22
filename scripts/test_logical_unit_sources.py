"""Source-bound controls for authored logical boundaries; no legal answer grading.

Run: python3 -m unittest discover -s scripts -p 'test_logical_unit_sources.py'
The selected examples are purposive, not a corpus-wide accuracy sample.
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUTHOR = ROOT / 'domain-profile/logical-units'
BASE = 'https://chris-page-gov.github.io/okf-dwp/id/'
REQUIRES = 'http://purl.org/dc/terms/requires'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, cap=16 * 1024 * 1024):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > cap:
        raise ValueError('Not an admitted bounded regular fixture')
    raw = path.read_bytes()
    if len(raw) > cap:
        raise ValueError('Fixture exceeds limit')
    return raw


def fold(text):
    return ' '.join(text.split())


def reconstruct(doc, unit, pages):
    fragments = []
    previous = None
    for span in unit['spans']:
        number, start, end = span['page'], span['start_utf8'], span['end_utf8']
        raw = pages[number - 1]['text'].encode('utf-8')
        if pages[number - 1]['page'] != number or not 0 <= start < end <= len(raw):
            raise ValueError('Invalid source interval')
        if previous:
            old_page, old_end, old_size = previous
            if not ((number == old_page and start == old_end) or
                    (number == old_page + 1 and old_end == old_size and start == 0)):
                raise ValueError('Incomplete cross-page continuation')
        literal = raw[start:end]
        if digest(literal) != span['literal_sha256']:
            raise ValueError('Altered source span')
        fragments.append(literal.decode('utf-8'))
        previous = number, end, len(raw)
    # Joiner is presentation-only; spans bind the source and no synthetic newline is source evidence.
    return '\n'.join(fragments)


def validate_phrases(text, control):
    normal = fold(text)
    for term in control['must_contain']:
        if fold(term) not in normal:
            raise ValueError('Missing reviewed source qualifier: ' + term)
    for term in control['must_not_contain']:
        if fold(term) in normal:
            raise ValueError('Crossed reviewed source boundary: ' + term)
    if 'numbered_examples' in control:
        if len(re.findall(r'^Example \d+\s*$', text, re.M)) != control['numbered_examples']:
            raise ValueError('Incomplete attached examples')


class LogicalSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.author = json.loads(read(AUTHOR / 'overrides.json'))
        cls.controls = json.loads(read(AUTHOR / 'source-controls.json'))
        cls.profiles = json.loads(read(AUTHOR / 'profiles.json'))['profiles']
        cls.concepts = json.loads(read(AUTHOR / 'concepts.yamlld'))['@graph']
        cls.documents = {d['document_id']: d for d in cls.author['documents']}
        cls.pages = {d['document_id']: json.loads(read(ROOT / d['pages_path']))['pages'] for d in cls.author['documents']}
        cls.units = {u['key']: (d, u) for d in cls.author['documents'] for u in d['units']}

    def text(self, key):
        d, u = self.units[key]
        return reconstruct(d, u, self.pages[d['document_id']])

    def test_all_sources_bind_frozen_inventory_pdf_pages_and_date_roles(self):
        for d in self.documents.values():
            inv_raw = read(ROOT / d['inventory_path'])
            self.assertEqual(digest(inv_raw), d['inventory_sha256'])
            source = next(s for s in json.loads(inv_raw)['documents'] if s['id'] == d['document_id'])
            self.assertEqual(d['source_sha256'], source['sha256'])
            self.assertEqual(digest(read(ROOT / d['pdf_path'])), source['sha256'])
            self.assertEqual(digest(read(ROOT / d['pages_path'])), source['pages_sha256'])
            self.assertEqual(d['observed_at'], source['observed_at'])
            self.assertEqual(d['source_dates']['document'], source['document_dates'])
            self.assertIsNone(d['source_dates']['document']['published_at'])
            self.assertIn('not document publication or legal effective dates', d['source_dates']['role_note'])

    def test_every_authored_span_is_exact_contiguous_and_disjoint(self):
        self.assertEqual(len(self.units), sum(len(d['units']) for d in self.documents.values()))
        for d in self.documents.values():
            seen = {}
            for u in d['units']:
                text = self.text(u['key'])
                self.assertTrue(text.strip())
                for label in u['paragraph_labels']:
                    self.assertRegex(text, r'(?m)^' + re.escape(label) + r'\s+')
                for s in u['spans']:
                    for a, b in seen.get(s['page'], []):
                        self.assertTrue(s['end_utf8'] <= a or s['start_utf8'] >= b)
                    seen.setdefault(s['page'], []).append((s['start_utf8'], s['end_utf8']))

    def test_reviewed_examples_notes_footnotes_and_qualifiers_survive(self):
        for control in self.controls['checks']:
            with self.subTest(unit=control['unit_key']):
                validate_phrases(self.text(control['unit_key']), control)

    def test_rehashed_missing_footnote_still_fails_source_expectation(self):
        d, u = self.units['spc-077004']
        altered = copy.deepcopy(u)
        last = altered['spans'][-1]
        raw = self.pages[d['document_id']][last['page'] - 1]['text'].encode()
        last['end_utf8'] = raw.index(b'1 SPC Regs')
        last['literal_sha256'] = digest(raw[last['start_utf8']:last['end_utf8']])
        text = reconstruct(d, altered, self.pages[d['document_id']])
        control = next(c for c in self.controls['checks'] if c['unit_key'] == u['key'])
        with self.assertRaisesRegex(ValueError, 'qualifier'):
            validate_phrases(text, control)

    def test_skipped_continuation_and_changed_hash_are_rejected(self):
        d, u = self.units['uc-c1988']
        altered = copy.deepcopy(u)
        altered['spans'][1]['start_utf8'] = 1
        with self.assertRaisesRegex(ValueError, 'continuation'):
            reconstruct(d, altered, self.pages[d['document_id']])
        altered = copy.deepcopy(u)
        altered['spans'][0]['literal_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Altered'):
            reconstruct(d, altered, self.pages[d['document_id']])

    def test_duplicate_number_and_reserved_range_are_not_global_identity(self):
        a, b = (self.units[k] for k in ('state-pension-077030', 'bereavement-077030'))
        self.assertEqual(a[1]['paragraph_labels'], b[1]['paragraph_labels'])
        self.assertNotEqual(a[1]['key'], b[1]['key'])
        self.assertNotEqual(a[1]['spans'], b[1]['spans'])
        for anomaly in self.controls['source_anomalies']:
            self.assertIn(anomaly['literal'], self.pages[anomaly['document_id']][anomaly['page'] - 1]['text'])
        self.assertIn('P5096', self.units['pip-transfer-p5093-5097'][1]['paragraph_labels'])
        self.assertNotIn('P5096 – P5105', self.text('pip-transfer-p5093-5097'))

    def test_required_paths_are_real_directed_declared_edges(self):
        for p in self.profiles:
            self.assertEqual(p['answerability'], 'insufficient-until-open-obligations-resolved')
            for path in p['required_paths']:
                self.assertIn(path['seed'], p['when_all'])
                first = self.units[path['unit_keys'][0]][1]
                self.assertIn(path['seed'], first['concept_ids'])
                for a, b in zip(path['unit_keys'], path['unit_keys'][1:]):
                    d, u = self.units[a]
                    self.assertIn(b, u['support_unit_keys'])
                    self.assertTrue(any(e['source_unit_key'] == a and e['target_unit_key'] == b and e['predicate'] == REQUIRES for e in d['proposals']))
                self.assertTrue(set(path['unit_keys']) <= set(p['required_unit_keys']))
            categories = {o['category'] for o in p['missing_obligations']}
            self.assertTrue({'legal_version_unreconciled', 'applicability_unresolved', 'independent_review_pending'} <= categories)

    def test_payment_claimant_household_and_benefit_regimes_do_not_collapse(self):
        pc = next(p for p in self.profiles if p['id'] == 'logical-pc-abroad')
        uc = next(p for p in self.profiles if p['id'] == 'logical-uc-temporary-absence')
        self.assertTrue(all(k.startswith('spc-') for k in pc['required_unit_keys']))
        self.assertFalse(any(k in pc['required_unit_keys'] for k in ['spc-077005', 'spc-077006', 'spc-077007', 'spc-qyp-077008-014']))
        self.assertTrue(all(k.startswith('uc-') for k in uc['required_unit_keys']))
        self.assertIn('4 weeks', self.text('spc-077001'))
        self.assertIn('one month', self.text('uc-c1986'))
        self.assertIn('does not exceed', self.text('uc-c1986'))
        for p in self.profiles:
            self.assertNotEqual(p['when_all'], [BASE + 'staff-domain/abroad'])
        self.assertIn('until they', self.text('spc-077015'))
        self.assertIn('not go abroad for the sole purpose', self.text('uc-c1988'))

    def test_temporary_permanent_and_institution_branches_stay_separate(self):
        temp = next(p for p in self.profiles if p['id'] == 'logical-pc-temporary-care')
        perm = next(p for p in self.profiles if p['id'] == 'logical-pc-care-home-alternatives')
        self.assertTrue(set(temp['required_unit_keys']) < set(perm['required_unit_keys']))
        self.assertIn('temporary-or-permanent', {o['id'] for o in perm['missing_obligations']})
        self.assertIn('without deciding which applies', perm['scope'])
        self.assertIn('spc-temporary-78086', self.units['spc-temporary-78085'][1]['support_unit_keys'])
        self.assertIn('under 18 years of age', self.text('pip-p4016'))
        self.assertIn('not more than 1 year', self.text('pip-p4020'))
        self.assertIn('not more than 28 days', self.text('pip-p4021'))
        self.assertIn('although entitlement continues', self.text('pip-transfer-p5093-5097'))

    def test_missing_current_update_effect_remains_open(self):
        refs = json.loads(read(AUTHOR / 'reference-review.json'))['references']
        memo = next(r for r in refs if r['source_unit_key'] == 'uc-c1988')
        self.assertEqual(memo['status'], 'unresolved')
        self.assertIn('acquired', memo['note'])
        self.assertIn('not reconciled', memo['note'])
        uc = next(p for p in self.profiles if p['id'] == 'logical-uc-temporary-absence')
        self.assertIn('memo-adm-09-25', {o['id'] for o in uc['missing_obligations']})
        self.assertTrue(any(r['literal_reference'] == 'falls within 12 above' for r in refs))

    def test_source_concepts_are_bounded_proposals_without_global_alias_claims(self):
        existing = {r['id'] for r in json.loads(read(ROOT / 'evaluation/semantic-expansion/assembly-index.json'))['records']}
        novel = {c['@id'] for c in self.concepts}
        self.assertEqual(len(novel), 2)
        for c in self.concepts:
            self.assertEqual(c['assertion_status'], 'model-derived')
            self.assertEqual(c['review_status'], 'unreviewed-specialist-review-required')
            self.assertTrue(c['provenance'])
        uc = next(c for c in self.concepts if c['label'] == 'Universal Credit')
        self.assertEqual(uc['aliases'], [{'label': 'UC', 'case_sensitive': True}])
        for d, u in self.units.values():
            self.assertTrue(set(u['concept_ids']) <= existing | novel)
            self.assertEqual(u['review_status'], 'agent-reviewed-boundary-only')
            self.assertEqual(u['specialist_review'], 'not-reviewed')

    def test_table_contents_blank_and_historical_rollout_have_distinct_roles(self):
        for doc in ('dmg-vol13-ch78', 'adm-chapter-p1'):
            self.assertEqual(self.documents[doc]['units'][0]['kind'], 'navigation')
        e = self.author['page_expectations'][0]
        self.assertEqual(e['expected_text_bytes'], 0)
        self.assertEqual(self.pages[e['document_id']][e['page'] - 1]['text'], '')
        self.assertFalse(any(s['page'] == e['page'] for u in self.documents[e['document_id']]['units'] for s in u['spans']))
        self.assertIn('July 2015', self.text('pip-rollout-appendix2'))
        self.assertIn('Rates from 8.4.24', self.text('spc-deductions-2024'))
        self.assertNotIn('£126.65', self.text('spc-deductions-2024'))


if __name__ == '__main__':
    unittest.main()
