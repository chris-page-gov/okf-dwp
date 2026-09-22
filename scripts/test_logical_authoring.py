"""Admission controls for additive logical authoring; no source/network mutation."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from build_logical_units import Inputs, canonical, check_override, sha
from logical_unit_authoring import PREFIX, REGISTRY, extensions, load_overrides, load_semantics

ROOT = Path(__file__).resolve().parents[1]
DEPENDENCY = PREFIX + 'closure-dependencies.yamlld'
PIP = PREFIX + 'closure-pip-transition.yamlld'


class ReplacedInputs:
    def __init__(self, replacements):
        self.real = Inputs(ROOT)
        self.replacements = replacements
        self.files = self.real.files

    def read(self, path, *args, **kwargs):
        if path in self.replacements:
            return canonical(self.replacements[path])
        return self.real.read(path, *args, **kwargs)


class LogicalAuthoringTests(unittest.TestCase):
    def mutate(self, path, fn):
        value = json.loads((ROOT / path).read_bytes())
        fn(value)
        return ReplacedInputs({path: value})

    def test_every_registered_file_and_loader_are_hash_bound(self):
        inputs = Inputs(ROOT)
        ext = extensions(inputs)
        self.assertIn(REGISTRY, inputs.files)
        self.assertIn('scripts/logical_unit_authoring.py', inputs.files)
        self.assertEqual(len(ext), len(json.loads((ROOT / REGISTRY).read_bytes())['extensions']))
        for path, _ in ext:
            self.assertEqual(inputs.files[path]['sha256'], sha((ROOT / path).read_bytes()))

    def test_registry_rejects_arbitrary_paths_duplicates_and_order(self):
        cases = [['../private.yamlld'], ['/tmp/closure-test.yamlld'], ['https://example.org/closure-test.yamlld'],
                 ['closure-dependencies.yamlld', 'closure-dependencies.yamlld'],
                 ['closure-pip-transition.yamlld', 'closure-dependencies.yamlld']]
        for paths in cases:
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                extensions(self.mutate(REGISTRY, lambda x: x.update(extensions=paths)))

    def test_unregistered_declarations_are_not_loaded(self):
        inputs = self.mutate(REGISTRY, lambda x: x.update(extensions=[]))
        result = load_overrides(inputs)
        original = json.loads((ROOT / (PREFIX + 'overrides.json')).read_bytes())
        self.assertEqual(sum(len(d['units']) for d in result['documents']), sum(len(d['units']) for d in original['documents']))
        self.assertNotIn(DEPENDENCY, inputs.files)

    def test_symlink_and_duplicate_json_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'scripts').mkdir()
            (root / 'scripts/logical_unit_authoring.py').write_text('fixture')
            (root / PREFIX).mkdir(parents=True)
            (root / REGISTRY).write_text('{"schema":"x","schema":"y","extensions":[]}')
            with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'):
                extensions(Inputs(root))
            (root / REGISTRY).write_bytes(canonical({'schema': 'okf-dwp-logical-authoring-registry.v1', 'extensions': ['closure-test.yamlld']}))
            (root / PREFIX / 'closure-test.yamlld').symlink_to(ROOT / DEPENDENCY)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                extensions(Inputs(root))

    def test_document_binding_conflict_fails_closed(self):
        def change(x):
            x['documents'][0]['source_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Conflicting immutable document binding'):
            load_overrides(self.mutate(DEPENDENCY, change))

    def test_global_unit_keys_cannot_shadow_another_document(self):
        def change(x):
            row = next(d for d in x['documents'] if d['units'])
            row['units'][0]['key'] = 'spc-077001'
        with self.assertRaisesRegex(ValueError, 'Duplicate global authored unit key'):
            load_overrides(self.mutate(DEPENDENCY, change))

    def test_registered_source_assigns_provenance_not_input(self):
        def change(x):
            row = next(d for d in x['documents'] if d['units'])
            row['units'][0]['authoring_path'] = 'official-source'
        with self.assertRaisesRegex(ValueError, 'provenance'):
            load_overrides(self.mutate(DEPENDENCY, change))
        merged = load_overrides(Inputs(ROOT))
        original = next(u for d in merged['documents'] for u in d['units'] if u['key'] == 'spc-077001')
        target = next(u for d in merged['documents'] for u in d['units'] if u['key'] == 'spc-supersession-04642')
        self.assertEqual(original['authoring_path'], PREFIX + 'overrides.json')
        self.assertEqual(target['authoring_path'], DEPENDENCY)

    def test_authority_upgrade_unknown_fields_and_profile_replacement_rejected(self):
        for change in [lambda x: x.update(specialist_review='approved'), lambda x: x.update(review_status='official'),
                       lambda x: x.update(execute='instructions are inert'),
                       lambda x: x['profiles'][0].update(id='logical-pc-abroad')]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                load_semantics(self.mutate(PIP, change))

    def test_original_requirements_and_unresolved_notes_are_retained(self):
        _, _, profiles, refs, dispositions = load_semantics(Inputs(ROOT))
        original = json.loads((ROOT / (PREFIX + 'profiles.json')).read_bytes())
        for row in original['profiles']:
            new = next(p for p in profiles['profiles'] if p['id'] == row['id'])
            for field in ['required_unit_keys', 'required_paths', 'missing_obligations']:
                for value in row[field]:
                    self.assertIn(value, new[field])
            for field in ['when_all', 'covers', 'scope']:
                self.assertEqual(row[field], new[field])
        old_refs = json.loads((ROOT / (PREFIX + 'reference-review.json')).read_bytes())['references']
        for row in old_refs:
            self.assertIn(row, refs['references'])
        self.assertEqual(len(dispositions), len(old_refs))
        self.assertTrue(all(r['legal_effect_status'] == 'unresolved' for r in dispositions))

    def test_profile_addition_cannot_reuse_an_obligation_id_with_a_new_meaning(self):
        original = json.loads((ROOT / (PREFIX + 'profiles.json')).read_bytes())['profiles'][0]
        def change(x):
            x['profile_additions'] = [{'id': original['id'], 'missing_obligations': [
                {**original['missing_obligations'][0], 'label': 'Different obligation'}]}]
        with self.assertRaisesRegex(ValueError, 'Conflicting obligation identity'):
            load_semantics(self.mutate(DEPENDENCY, change))

    def test_disposition_cannot_rewrite_source_spans_or_resolve_legal_effect(self):
        for change in [lambda x: x['reference_dispositions'][0].update(status='resolved'),
                       lambda x: x['reference_dispositions'][0].update(legal_effect_status='resolved'),
                       lambda x: x['reference_dispositions'][0].update(evidence_spans=[])]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                load_semantics(self.mutate(DEPENDENCY, change))

    def test_all_additions_are_admitted_as_one_non_overlapping_source_partition(self):
        merged = load_overrides(Inputs(ROOT))
        for document in merged['documents']:
            inventory = json.loads((ROOT / document['inventory_path']).read_bytes())
            source = next(d for d in inventory['documents'] if d['id'] == document['document_id'])
            pages = json.loads((ROOT / document['pages_path']).read_bytes())['pages']
            check_override(source, pages, document, document['inventory_sha256'])
        p5 = next(d for d in merged['documents'] if d['document_id'] == 'adm-chapter-p5')
        damaged = deepcopy(p5)
        damaged['units'].append({**deepcopy(damaged['units'][0]), 'key': 'overlapping-new-unit'})
        source = next(d for d in json.loads((ROOT / p5['inventory_path']).read_bytes())['documents'] if d['id'] == p5['document_id'])
        with self.assertRaisesRegex(ValueError, 'overlap'):
            check_override(source, json.loads((ROOT / p5['pages_path']).read_bytes())['pages'], damaged, p5['inventory_sha256'])


if __name__ == '__main__':
    unittest.main()
