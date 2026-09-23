"""Integration controls for the separately generated Chapter 84 experiment."""
import gzip
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CapitalPilotControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.author = json.loads((ROOT / 'domain-profile/capital-pilot/capital.yamlld').read_text())
        cls.arms = {arm: json.loads((ROOT / f'capital-pilot/{arm}/index.json').read_text())
                    for arm in ['baseline', 'candidate']}
        cls.groups = json.loads((ROOT / 'capital-pilot/groups.json').read_text())['groups']

    def test_baseline_is_the_exact_frozen_record_set(self):
        catalogue = json.loads(gzip.decompress((ROOT / 'structured-units/documents/dmg/dmg-vol14-ch84.json.gz').read_bytes()))
        expected = {unit['id']: unit['record_sha256'] for unit in catalogue['units']}
        actual = {record['id']: hashlib.sha256((json.dumps(record, ensure_ascii=False, sort_keys=True,
                  separators=(',', ':')) + '\n').encode()).hexdigest()
                  for record in self.arms['baseline']['records'] if record['kind'] == 'evidence'}
        self.assertEqual(actual, expected)

    def test_comparison_preserves_the_same_topic_vocabulary(self):
        select = lambda arm: [r for r in self.arms[arm]['records'] if r['kind'] == 'concept']
        self.assertEqual(select('baseline'), select('candidate'))

    def test_authored_summaries_bind_their_own_literal_and_author_file(self):
        path = ROOT / 'domain-profile/capital-pilot/capital.yamlld'
        records = {r['id']: r for r in self.arms['candidate']['records']}
        for i, group in enumerate(self.author['groups']):
            concept = records[group['concept_id']]
            self.assertEqual(concept['text'], group['summary'])
            self.assertEqual(len(concept['provenance']), 1)
            provenance = concept['provenance'][0]
            self.assertEqual(provenance['source_sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(provenance['literal_sha256'], hashlib.sha256(concept['text'].encode()).hexdigest())
            self.assertEqual(provenance['locator'], f'/groups/{i}/summary')
            self.assertNotIn('PDF page', provenance['locator'])
            self.assertTrue(concept['rights'].endswith('/LICENSE'))

    def test_reserved_ranges_are_not_substantive_group_labels(self):
        groups = {g['key']: g for g in self.author['groups']}
        self.assertEqual(groups['pc-capital-u10']['paragraph_labels'], ['84911', '84921', '84922', '84923', '84924'])
        self.assertNotIn('84700', groups['pc-capital-u06']['paragraph_labels'])
        self.assertNotIn('84693', groups['pc-capital-u06']['paragraph_labels'])
        parts = {part['key']: part for repair in self.author['repairs'] for part in repair['parts']}
        self.assertEqual(parts['capital-reserved-84700']['role'], 'reserved')
        self.assertEqual(parts['capital-valuation-contents']['role'], 'contents')

    def test_corrected_paragraphs_exclude_following_contents(self):
        by_id = {r['id']: r for r in self.arms['candidate']['records']}
        first = next(r for r in by_id.values() if '/capital-84356-' in r['id'])
        second = next(r for r in by_id.values() if '/capital-84699-' in r['id'])
        self.assertEqual([s['source_url'].split('#page=')[1] for s in first['evidence_unit']['spans']], ['36'])
        self.assertNotIn('Life interest or life rent', first['text'])
        self.assertNotIn('Further guidance on valuation', second['text'])
        self.assertNotIn('84700', second['text'])
        self.assertTrue(any('Further guidance on valuation' in r['text'] for r in by_id.values()))

    def test_discovery_summaries_never_replace_source_evidence(self):
        root = ROOT / 'capital-pilot/candidate'
        manifest = json.loads((root / 'manifest.json').read_text())
        records = {r['id']: r for r in self.arms['candidate']['records']}
        group_ids = {g['id'] for g in self.groups}
        summaries = {g['summary'] for g in self.author['groups']}
        count = 0
        for shard in manifest['discovery']['shards']:
            raw = (root / shard['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), shard['sha256'])
            for card in json.loads(gzip.decompress(raw))['cards']:
                if card['evidence_id'] not in group_ids: continue
                count += 1
                self.assertEqual(card['assertion_status'], 'model-derived')
                self.assertIn(card['summary'], summaries)
                record = records[card['evidence_id']]
                self.assertEqual(record['assertion_status'], 'normalized')
                self.assertNotEqual(record['text'], card['summary'])
        self.assertEqual(count, 10)

    def test_groups_keep_notices_separate_and_do_not_claim_completeness(self):
        records = {r['id']: r for r in self.arms['candidate']['records']}
        for group in self.groups:
            record = records[group['id']]
            self.assertEqual(record['evidence_unit']['completeness'], 'unresolved')
            self.assertNotIn('84925 - 84999', record['text'])
            self.assertNotIn('illustrative purposes', record['text'])
        self.assertTrue(any('illustrative purposes' in r['text'] for r in records.values()))

    def test_appendix_reference_is_source_bound_and_typing_is_separate(self):
        index = self.arms['candidate']; records = {r['id']: r for r in index['records']}
        links = [e for e in index['assertions'] if e['label'].startswith('Printed reference to Appendix')]
        self.assertEqual(len(links), 1)
        edge = links[0]
        self.assertIn('Appendix 1', records[edge['source']]['text'])
        self.assertEqual(records[edge['target']]['evidence_unit']['kind'], 'table')
        self.assertEqual(edge['predicate'], 'http://purl.org/dc/terms/references')
        self.assertEqual(edge['assertion_status'], 'normalized')
        self.assertNotEqual(edge['authority']['class'], 'official')
        table = json.loads((ROOT / 'capital-pilot/appendix-1.json').read_text())
        self.assertEqual(len(table['rows']), 21)
        self.assertIsNotNone(table['continuation'])

    def test_every_requirement_keeps_an_open_obligation(self):
        for index in self.arms.values():
            present = {r['id'] for r in index['records']}
            for need in index['requirements']:
                self.assertTrue(any('/open-obligation/' in identifier and identifier not in present
                                    for identifier in need['required']))


if __name__ == '__main__':
    unittest.main()
