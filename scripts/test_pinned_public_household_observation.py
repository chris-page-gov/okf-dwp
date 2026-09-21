"""Admission and integrity controls; no browser, network or provider calls."""
import copy
import gzip
import io
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory, gettempdir
import unittest
from unittest.mock import Mock, patch

import check_pinned_public_household_observation as check


class PinnedPublicObservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = check.BASE / check.ATTEMPT
        cls.approval = check.APPROVED[check.RELEASE]
        cls.observation = check.parse(check.bounded_read(cls.directory / 'observation.json'))
        cls.app_raw = check.bounded_read(cls.directory / 'app-manifest.json')
        cls.cache = {}
        def reader(commit, path):
            if path not in cls.cache:
                cls.cache[path] = check.git_blob(commit, path)
            return cls.cache[path]
        cls.result = check.validate(reader=reader)
        cls.manifest = check.parse(cls.cache['combined/context/corpus/manifest.json'])
        cls.index, cls.records = check.source_records(cls.cache, cls.manifest)
        cls.assertions = {r['id']: r for r in cls.index['assertions']}
        cls.context = check.parse(check.bounded_read(cls.directory / 'care-home-context.json'))

    def fixture(self, base):
        directory = base / check.ATTEMPT; directory.mkdir()
        for name in check.FILES:
            (directory / name).write_bytes(b'\x89PNG\r\n\x1a\n' if name.endswith('.png') else b'{}')
        return directory

    def verify_context(self, context, records=None, observed=None):
        return check.verify_context(context, observed or self.observation['checks']['care_home'],
            self.manifest, self.context['binding'], self.records if records is None else records,
            self.assertions, self.context['question'])

    def rebind(self, value):
        basis = copy.deepcopy(value); basis.pop('context_id'); basis['budget'].pop('used_bytes')
        value['context_id'] = 'urn:sha256:' + check.sha(check.canonical(basis))
        for _ in range(4): value['budget']['used_bytes'] = len(check.canonical(value))
        observed = copy.deepcopy(self.observation['checks']['care_home'])
        observed.update(context_id=value['context_id'], budget=value['budget'], compact_json_bytes=value['budget']['used_bytes'])
        return observed

    def test_actual_approved_observation_and_every_source_byte(self):
        self.assertEqual(self.result['source_files_verified_against_git'], 273)
        self.assertEqual(self.result['app_material_observations_verified'], 21)
        self.assertEqual(self.result['source_commit'], self.approval['source_commit'])
        self.assertFalse(self.result['source_authority_or_completeness_upgraded'])
        self.assertEqual(self.result['new_network_or_model_calls'], 0)
        self.assertEqual((self.result['cases']['care_home']['selected_records'], self.result['cases']['care_home']['relationships']), (62, 124))
        self.assertEqual((self.result['cases']['sda']['selected_records'], self.result['cases']['sda']['relationships']), (64, 99))
        self.assertTrue(all(row['evidence_literal_digests'] for row in self.result['cases'].values()))
        for case, paths, requirements in [('care_home', 108, 39), ('sda', 128, 12)]:
            row = self.result['cases'][case]
            self.assertEqual((row['selected_path_references'], row['selected_paths_fully_retained']), (paths, paths))
            self.assertEqual((row['returned_required_path_occurrences'], row['returned_required_paths_fully_retained']), (requirements, requirements))

    def test_inventory_requires_exact_files_and_regular_bounded_members(self):
        with TemporaryDirectory(dir=Path(gettempdir()).resolve()) as tmp:
            base = Path(tmp); directory = self.fixture(base)
            self.assertEqual(len(check.inventory(base)), 11)
            extra = directory / 'extra.json'; extra.write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'inventory differs'): check.inventory(base)
            extra.unlink(); member = directory / 'observation.json'; member.unlink()
            with self.assertRaisesRegex(ValueError, 'inventory differs'): check.inventory(base)
            member.symlink_to(directory / 'app-manifest.json')
            with self.assertRaisesRegex(ValueError, 'regular file'): check.inventory(base)

    def test_root_parent_and_attempt_symlinks_reject_before_read(self):
        for kind in ['root', 'parent', 'attempt']:
            with self.subTest(kind=kind), TemporaryDirectory(dir=Path(gettempdir()).resolve()) as tmp:
                root = Path(tmp); actual = root / 'actual'; actual.mkdir(); self.fixture(actual)
                link = root / 'link'; link.symlink_to(actual, target_is_directory=True)
                if kind == 'root': target = link
                elif kind == 'parent': target = link / check.ATTEMPT
                else:
                    linked = root / 'linked'; linked.mkdir()
                    (linked / check.ATTEMPT).symlink_to(actual / check.ATTEMPT, target_is_directory=True)
                    target = linked
                with patch('check_household_reader_observations.os.open') as opened:
                    with self.assertRaisesRegex(ValueError, 'symlinks'): check.inventory(target)
                    opened.assert_not_called()

    def test_oversized_member_and_metadata_symlink_rejected(self):
        with TemporaryDirectory(dir=Path(gettempdir()).resolve()) as tmp:
            root = Path(tmp); directory = self.fixture(root)
            target = directory / 'app-manifest.json'
            with target.open('wb') as stream: stream.truncate(check.MAX_MEMBER + 1)
            with patch('check_household_reader_observations.os.open') as opened:
                with self.assertRaisesRegex(ValueError, 'byte limit'): check.inventory(root)
                opened.assert_not_called()
            target.write_bytes(b'{}')
            (root / 'approval-manifest.json').symlink_to(target)
            with self.assertRaisesRegex(ValueError, 'symlinks'): check.inventory(root)

    def test_source_path_and_commit_admission_precedes_git(self):
        with patch.object(check.subprocess, 'check_output') as called:
            for path in ['.email.md', '../combined/x', 'combined/../x', 'combined/.email.md', '/combined/x',
                         'combined/x//y', 'combined/x?url=evil', 'evaluation/private.json', 'domain-profile/other.json']:
                with self.subTest(path=path), self.assertRaises(ValueError):
                    check.git_blob(self.approval['source_commit'], path)
            with self.assertRaises(ValueError): check.git_blob('main', 'combined/x.json')
            called.assert_not_called()

    def test_rewritten_observation_cannot_self_approve_with_new_inventory(self):
        with TemporaryDirectory(dir=Path(gettempdir()).resolve()) as tmp:
            base = Path(tmp)
            shutil.copytree(self.directory, base / check.ATTEMPT)
            value = copy.deepcopy(self.observation); value['browser_version'] = 'invented'
            (base / check.ATTEMPT / 'observation.json').write_bytes(check.encoded(value))
            # A fully consistent adjacent inventory is not an approval source.
            (base / 'artifact-manifest.json').write_bytes(check.encoded({'files': check.inventory(base)}))
            reader = Mock()
            with self.assertRaisesRegex(ValueError, 'approved retained bytes'):
                check.validate(base=base, reader=reader)
            reader.assert_not_called()

    def test_git_size_admission_and_bounded_capture(self):
        with patch.object(check.subprocess, 'check_output', return_value=str(check.MAX_GIT_BLOB + 1).encode()), patch.object(check.subprocess, 'Popen') as proc:
            with self.assertRaisesRegex(ValueError, 'Git blob exceeds'): check.git_blob(self.approval['source_commit'], 'combined/x.json')
            proc.assert_not_called()
        process = Mock(); process.stdout = io.BytesIO(b'12345'); process.poll.return_value = 0; process.wait.return_value = 0
        with patch.object(check, 'MAX_GIT_BLOB', 4), patch.object(check.subprocess, 'check_output', return_value=b'4'), patch.object(check.subprocess, 'Popen', return_value=process):
            with self.assertRaisesRegex(ValueError, 'capture exceeds'): check.git_blob(self.approval['source_commit'], 'combined/x.json')

    def test_app_rejects_duplicate_missing_modified_or_unapproved_materials(self):
        for kind in ['duplicate', 'missing', 'bytes', 'url', 'manifest']:
            with self.subTest(kind=kind):
                value = copy.deepcopy(self.observation)
                if kind == 'duplicate': value['app']['verified_materials'][-1] = value['app']['verified_materials'][0]
                elif kind == 'missing': value['app']['verified_materials'].pop()
                elif kind == 'bytes': value['browser_loaded_app_materials'][0]['bytes'] += 1
                elif kind == 'url': value['browser_loaded_app_materials'][0]['url'] = 'https://example.test/code.js'
                else: value['expected_app_manifest_sha256'] = '0' * 64
                with self.assertRaises(ValueError): check.verify_app(self.app_raw, value, self.approval)

    def test_source_inventory_duplicate_path_tamper_and_response_binding(self):
        value = copy.deepcopy(self.observation); value['inputs'].append(value['inputs'][0])
        reader = Mock()
        with self.assertRaisesRegex(ValueError, 'Repeated source'): check.verify_sources(value, self.approval['source_commit'], reader)
        reader.assert_not_called()
        value = copy.deepcopy(self.observation); value['inputs'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Source input differs'):
            check.verify_sources(value, self.approval['source_commit'], lambda c, p: self.cache[p])
        value = copy.deepcopy(self.observation); value['corpus_requests'][0]['url'] = 'https://example.test/replaced'
        with self.assertRaisesRegex(ValueError, 'Non-canonical corpus'):
            check.verify_sources(value, self.approval['source_commit'], lambda c, p: self.cache[p])

    def test_complete_package_id_and_answer_or_budget_boundary(self):
        for kind in ['id', 'answer', 'status', 'budget']:
            with self.subTest(kind=kind):
                value = copy.deepcopy(self.context)
                if kind == 'id': value['context_id'] = 'urn:sha256:' + '0' * 64
                elif kind == 'answer': value['ai_answer'] = {'invented': True}
                elif kind == 'status': value['evidence_status'] = 'sufficient'
                else: value['budget']['max_bytes'] = 524289
                observed = self.rebind(value) if kind == 'budget' else None
                with self.assertRaises(ValueError): self.verify_context(value, observed=observed)

    def test_rehashed_package_cannot_change_source_text_or_authority(self):
        for field, replacement in [('text', 'invented whole page'), ('assertion_status', 'official')]:
            with self.subTest(field=field):
                value = copy.deepcopy(self.context)
                record = next(x['record'] for x in value['selected'] if x['record']['kind'] == 'evidence')
                record[field] = replacement
                with self.assertRaisesRegex(ValueError, 'complete immutable source'):
                    self.verify_context(value, observed=self.rebind(value))

    def test_literal_digest_and_directed_path_checked_independently(self):
        value = copy.deepcopy(self.context)
        record = next(x['record'] for x in value['selected'] if x['record']['kind'] == 'evidence')
        record['provenance'][0]['literal_sha256'] = '0' * 64
        records = {**self.records, record['id']: record}
        with self.assertRaisesRegex(ValueError, 'literal digest'):
            self.verify_context(value, records=records, observed=self.rebind(value))
        value = copy.deepcopy(self.context)
        path = next(p for x in value['selected'] for p in x['paths'] if p['assertions'])
        path['assertions'][0] = 'https://example.test/invented-assertion'
        with self.assertRaisesRegex(ValueError, 'directed path'):
            self.verify_context(value, observed=self.rebind(value))

    def test_unselected_edge_target_requires_explicit_budget_omission(self):
        value = copy.deepcopy(self.context)
        selected = {x['record']['id'] for x in value['selected']}
        target = next(x['target'] for x in value['relationships'] if x['target'] not in selected)
        value['budget']['omissions'] = [x for x in value['budget']['omissions'] if target not in x.get('ids', [])]
        with self.assertRaisesRegex(ValueError, 'lacks a budget omission'):
            self.verify_context(value, observed=self.rebind(value))

    def test_gzip_bounds_and_strict_json(self):
        self.assertEqual(check.decode_gzip(gzip.compress(b'abc'), 3), b'abc')
        with self.assertRaisesRegex(ValueError, 'Decoded source size'): check.decode_gzip(gzip.compress(b'x' * 10000), 3)
        for value in [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}']:
            with self.assertRaises(ValueError): check.parse(value)


if __name__ == '__main__': unittest.main()
