"""Reject changed source bindings and unsafe graph authoring before projection."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from build_evidence_route_graph import ROOT, POLICY, OUTPUT, build, digest


class EvidenceRouteGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = json.loads((ROOT / OUTPUT).read_text())

    def copied_inputs(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for binding in self.graph['source_bindings']:
            target = root / binding['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / binding['path'], target)
        return root

    def test_rebuild_preserves_frozen_bytes_and_declared_sources(self):
        self.assertEqual(build(), (ROOT / OUTPUT).read_text())
        for binding in self.graph['source_bindings']:
            raw = (ROOT / binding['path']).read_bytes()
            self.assertEqual(len(raw), binding['bytes'])
            self.assertEqual(digest(raw), binding['sha256'])
        frozen = json.loads((ROOT / 'combined/context/assembly-index.json').read_text())
        actual = {row['id']: row for row in self.graph['index']['requirements']}
        for requirement in frozen['requirements']:
            self.assertEqual(actual[requirement['id']], requirement)

    def test_changed_source_is_rejected_instead_of_silently_rebinding(self):
        root = self.copied_inputs()
        path = root / 'combined/context/assembly-index.json'
        path.write_text(path.read_text() + ' ')
        with self.assertRaisesRegex(ValueError, 'Graph input drift'):
            build(root)

    def test_policy_cannot_raise_work_ceilings(self):
        root = self.copied_inputs()
        path = root / POLICY
        policy = json.loads(path.read_text())
        policy['limits']['records'] += 1
        path.write_text(json.dumps(policy))
        with self.assertRaisesRegex(ValueError, 'hard ceilings'):
            build(root)

    def test_new_concept_meaning_conflict_is_rejected_even_with_rebound_file(self):
        root = self.copied_inputs()
        variant = self.graph['concept_variants'][0]
        path = root / variant['origin']
        index = json.loads(path.read_text())
        record = next(row for row in index['records'] if row['id'] == variant['id'])
        record['text'] += ' Unreviewed replacement meaning.'
        path.write_text(json.dumps(index))
        policy_path = root / POLICY
        policy = json.loads(policy_path.read_text())
        next(row for row in policy['inputs'] if row['path'] == variant['origin'])['sha256'] = digest(path.read_bytes())
        policy_path.write_text(json.dumps(policy))
        with self.assertRaisesRegex(ValueError, 'Conflicting graph evidence or assertion'):
            build(root)

    def test_authoring_cannot_escape_the_input_root(self):
        root = self.copied_inputs()
        path = root / POLICY
        policy = json.loads(path.read_text())
        policy['inputs'].insert(0, {'path': '../outside.json', 'sha256': '0' * 64})
        path.write_text(json.dumps(policy))
        with self.assertRaisesRegex(ValueError, 'Unsafe or oversized'):
            build(root)


if __name__ == '__main__':
    unittest.main()
