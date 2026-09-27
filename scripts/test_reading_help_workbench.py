"""Exact-identity and tamper checks for additive workbench reading help."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import build_reading_help_workbench as producer


class WorkbenchHelpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.record = {'id': 'https://example.test/unit/exact', 'kind': 'evidence',
            'evidence_unit': {'spans': [{'source_sha256': 'a' * 64, 'extraction_sha256': 'b' * 64}]}}
        package = self.write('evaluation/evidence-workbench/packages/staff-001.json',
            {'selected': [{'record': self.record}]})
        self.original_manifest = {'calculation_models': [{'id':'preserved-calculation'}], 'interaction_proposals': [{'id':'preserved-interaction'}], 'questions': [{'id': 'staff-001', 'package': {
            'url': 'packages/staff-001.json', 'bytes': len(package), 'sha256': producer.sha(package)}}]}
        self.write(producer.BASE_MANIFEST, self.original_manifest)
        self.index = {'source': {'sha256': 'a' * 64}, 'extraction': {'sha256': 'b' * 64},
            'passages': [{'unit_id': self.record['id']}]}
        self.rebind()

    def write(self, path, value):
        raw = json.dumps(value).encode()
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        return raw

    def rebind(self):
        raw = self.write('reading-help-corpus/documents/doc.json', self.index)
        catalogue = self.write('reading-help-corpus/manifest.json', {'documents': [{
            'family': 'dmg', 'document_id': 'doc', 'path': 'reading-help-corpus/documents/doc.json',
            'bytes': len(raw), 'sha256': producer.sha(raw)}]})
        self.write(producer.CONFIG, {'catalogue_revision': '1' * 40,
            'catalogue_sha256': producer.sha(catalogue)})

    def test_exact_link_preserves_frozen_manifest_and_packages(self):
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*.json')}
        outputs, report = producer.build(self.root)
        self.assertEqual(report['exact_reading_help_targets'], 1)
        manifest = json.loads(outputs[producer.OUTPUT])
        self.assertEqual({k:v for k,v in manifest.items() if k!='reading_help'},self.original_manifest)
        ref = manifest['reading_help']['targets_by_case'][0]
        sidecar = outputs['evaluation/evidence-workbench/' + ref['url']]
        self.assertEqual(producer.sha(sidecar), ref['sha256'])
        self.assertEqual(len(sidecar), ref['bytes'])
        self.assertEqual(json.loads(sidecar)['targets'][0]['unit_id'], self.record['id'])
        self.assertEqual(before, {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*.json')})

    def test_wrong_source_hash_rejected_even_with_rebound_index(self):
        self.index['source']['sha256'] = 'c' * 64
        self.rebind()
        with self.assertRaisesRegex(ValueError, 'different source identity'):
            producer.build(self.root)

    def test_hash_tampering_rejected(self):
        (self.root / 'reading-help-corpus/documents/doc.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Document index differs'):
            producer.build(self.root)

    def test_frozen_package_tampering_rejected(self):
        (self.root / 'evaluation/evidence-workbench/packages/staff-001.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Frozen package differs'):
            producer.build(self.root)

    def test_unknown_unit_is_reported_without_paragraph_guessing(self):
        self.index['passages'][0]['unit_id'] += '-different'
        self.rebind()
        outputs, report = producer.build(self.root)
        self.assertEqual(report['unmatched_records'], [self.record['id']])
        self.assertEqual(json.loads(outputs['evaluation/evidence-workbench/reading-help/staff-001.json'])['targets'], [])

    def test_conflicting_record_across_questions_is_rejected(self):
        different = json.loads(json.dumps(self.record))
        different['evidence_unit']['spans'][0]['source_sha256'] = 'c' * 64
        raw = self.write('evaluation/evidence-workbench/packages/staff-002.json',
                         {'selected': [{'record': different}]})
        self.original_manifest['questions'].append({'id': 'staff-002', 'package': {
            'url': 'packages/staff-002.json', 'bytes': len(raw), 'sha256': producer.sha(raw)}})
        self.write(producer.BASE_MANIFEST, self.original_manifest)
        with self.assertRaisesRegex(ValueError, 'Conflicting retained records'):
            producer.build(self.root)

    def test_path_escape_and_mutable_revision_rejected(self):
        with self.assertRaisesRegex(ValueError, 'escapes'):
            producer.read(self.root, '../outside.json')
        self.write(producer.CONFIG, {'catalogue_revision': 'main', 'catalogue_sha256': '0' * 64})
        with self.assertRaisesRegex(ValueError, 'Pin the reviewed'):
            producer.build(self.root)


if __name__ == '__main__':
    unittest.main()
