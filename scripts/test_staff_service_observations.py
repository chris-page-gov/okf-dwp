import copy
import hashlib
import json
import shutil
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest
from check_staff_service_observations import (inventory, verify_manifest, verify_observations,
    observation_layout, check_outcomes, DEFAULT, LAYOUT_SCHEMA, MAX_FILE_BYTES, MAX_MANIFEST_BYTES)


class ObservationIntegrity(unittest.TestCase):
    def fixture(self, directory):
        (directory / 'receipt.json').write_text('{"status":"failed"}\n')
        (directory / 'artifacts.json').write_text(json.dumps({'schema': 'okf-compact-delivery-artifact-manifest.v1', 'files': inventory(directory)}))

    def release_fixture(self, directory):
        """Temporary layout control using copied historical bytes, never new acceptance."""
        for name in ['sdk-receipt.json', 'deployment.json']:
            shutil.copyfile(DEFAULT / name, directory / name)
        shutil.copytree(DEFAULT / 'browser/staff-native', directory / 'browser/staff')
        manifest = {'schema': 'okf-compact-delivery-artifact-manifest.v1',
                    'observation_layout': {'schema': LAYOUT_SCHEMA, 'staff_attempts': ['staff'], 'historical_suite': 'not_run'},
                    'files': inventory(directory)}
        (directory / 'artifacts.json').write_text(json.dumps(manifest))
        return manifest

    def test_failed_receipt_bytes_are_verified_without_promoting_outcome(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp); self.fixture(directory)
            self.assertEqual(len(verify_manifest(directory)['files']), 1)
            (directory / 'receipt.json').write_text('{"status":"passed"}\n')
            with self.assertRaises(AssertionError): verify_manifest(directory)

    def test_added_or_missing_files_are_rejected(self):
        for mode in ['added', 'missing']:
            with tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp); self.fixture(directory)
                if mode == 'added': (directory / 'extra.json').write_text('{}')
                else: (directory / 'receipt.json').unlink()
                with self.assertRaises(AssertionError): verify_manifest(directory)

    def test_path_escape_and_duplicate_binding_are_rejected(self):
        for mode in ['escape', 'absolute', 'duplicate']:
            with tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp); self.fixture(directory)
                data = json.loads((directory / 'artifacts.json').read_text())
                if mode == 'duplicate': data['files'].append(copy.deepcopy(data['files'][0]))
                else: data['files'][0]['path'] = '../receipt.json' if mode == 'escape' else '/receipt.json'
                (directory / 'artifacts.json').write_text(json.dumps(data))
                with self.assertRaises(AssertionError): verify_manifest(directory)

    def test_symlinks_are_rejected_before_reading(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp); self.fixture(directory)
            (directory / 'linked.json').symlink_to('/etc/hosts')
            with self.assertRaises(AssertionError): verify_manifest(directory)

    def test_manifest_and_directory_symlinks_are_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / 'observations'; directory.mkdir(); self.fixture(directory)
            linked_directory = Path(tmp) / 'linked-directory'; linked_directory.symlink_to(directory, target_is_directory=True)
            with self.assertRaises(AssertionError): verify_manifest(linked_directory)
            (directory / 'artifacts.json').unlink()
            (directory / 'artifacts.json').symlink_to('/etc/hosts')
            with self.assertRaises(AssertionError): verify_manifest(directory)

    def test_oversized_files_and_manifest_are_rejected_before_open(self):
        for name, limit in [('000-oversized.json', MAX_FILE_BYTES), ('artifacts.json', MAX_MANIFEST_BYTES)]:
            with tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp); self.fixture(directory)
                with (directory / name).open('wb') as stream: stream.truncate(limit + 1)
                with patch('check_staff_service_observations.os.open', side_effect=AssertionError('must not open oversized file')) as opened:
                    if name == 'artifacts.json':
                        with self.assertRaisesRegex(AssertionError, 'exceeds byte limit'): verify_manifest(directory)
                    else:
                        with self.assertRaisesRegex(AssertionError, 'exceeds byte limit'): inventory(directory)
                    opened.assert_not_called()

    def test_summary_cannot_hide_console_failure(self):
        receipt = {'functional_status': 'passed', 'strict_console_status': 'failed',
                   'overall_clean_browser_acceptance': False, 'console_errors': [{'type': 'console'}]}
        summary = {'results': [{'browser': 'firefox', 'receipt': 'firefox-receipt.json', **{k: receipt[k] for k in ['functional_status', 'strict_console_status', 'overall_clean_browser_acceptance']}}],
                   'all_requested_engines_passed': False}
        check_outcomes(summary, {'firefox': receipt})
        summary['results'][0]['strict_console_status'] = 'passed'
        with self.assertRaises(AssertionError): check_outcomes(summary, {'firefox': receipt})

    def test_historical_default_outcomes_remain_exactly_unchanged(self):
        manifest = verify_manifest(DEFAULT)
        self.assertEqual(verify_observations(DEFAULT, manifest), {
            'staff_attempts': [
                {'attempt': 'staff', 'functional_passes': 2, 'strict_console_passes': 2, 'overall_clean_pass': False},
                {'attempt': 'staff-native', 'functional_passes': 3, 'strict_console_passes': 2, 'overall_clean_pass': False}],
            'historical_functional_passes': 12, 'historical_strict_passes': 8, 'historical_strict_status': 'failed'})

    def test_declared_single_attempt_reports_historical_not_run_not_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp); self.release_fixture(directory)
            outcome = verify_observations(directory, verify_manifest(directory))
            self.assertEqual(outcome['historical_strict_status'], 'not_run')
            self.assertIsNone(outcome['historical_functional_passes'])
            self.assertIsNone(outcome['historical_strict_passes'])
            self.assertEqual(outcome['staff_attempts'], [
                {'attempt': 'staff', 'functional_passes': 3, 'strict_console_passes': 2, 'overall_clean_pass': False}])

    def test_unknown_manifest_and_layout_or_unsafe_attempts_fail_closed(self):
        layout = {'schema': LAYOUT_SCHEMA, 'staff_attempts': ['staff'], 'historical_suite': 'not_run'}
        changes = [
            {'schema': 'unknown'}, {'staff_attempts': []}, {'staff_attempts': ['../escape']},
            {'staff_attempts': ['/absolute']}, {'staff_attempts': ['nested/child']},
            {'staff_attempts': ['staff', 'staff']}, {'staff_attempts': ['historical']},
            {'staff_attempts': ['a' * 65]}, {'staff_attempts': ['staff'] * 9},
            {'historical_suite': 'passed'}, {'unknown': True}]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(AssertionError):
                observation_layout({'observation_layout': {**layout, **change}})
        for change in [{'schema': 'unknown'}, {'unknown': True}]:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp); self.fixture(directory)
                manifest = json.loads((directory / 'artifacts.json').read_text()); manifest.update(change)
                (directory / 'artifacts.json').write_text(json.dumps(manifest))
                with self.assertRaises(AssertionError): verify_manifest(directory)

    def test_unlisted_attempt_and_claimed_missing_history_cannot_pass(self):
        for mode in ['undeclared', 'missing-history', 'missing-engine']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp); manifest = self.release_fixture(directory)
                if mode == 'undeclared':
                    extra = directory / 'browser/failed-attempt'; extra.mkdir()
                    (extra / 'run-summary.json').write_text('{}')
                elif mode == 'missing-history':
                    manifest['observation_layout']['historical_suite'] = 'present'
                else:
                    (directory / 'browser/staff/firefox-receipt.json').unlink()
                manifest['files'] = inventory(directory)
                (directory / 'artifacts.json').write_text(json.dumps(manifest))
                with self.assertRaises(AssertionError):
                    verify_observations(directory, verify_manifest(directory))

    def test_changed_deployment_is_rejected_even_if_outer_manifest_is_rebound(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp); manifest = self.release_fixture(directory)
            deployment = json.loads((directory / 'deployment.json').read_text())
            deployment['runtime_worker_sha256'] = '0' * 64
            (directory / 'deployment.json').write_text(json.dumps(deployment))
            manifest['files'] = inventory(directory)
            (directory / 'artifacts.json').write_text(json.dumps(manifest))
            with self.assertRaises(AssertionError):
                verify_observations(directory, verify_manifest(directory))

    def test_parent_symlinks_are_rejected_before_reading(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); actual = base / 'actual'; actual.mkdir()
            directory = actual / 'release'; directory.mkdir(); self.fixture(directory)
            linked = base / 'link'; linked.symlink_to(actual, target_is_directory=True)
            with patch('check_staff_service_observations.os.open') as opened:
                with self.assertRaisesRegex(AssertionError, 'parents must not be symlinks'):
                    verify_manifest(linked / 'release')
                opened.assert_not_called()

    def test_oversized_declared_member_is_rejected_before_member_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp); self.fixture(directory)
            manifest = json.loads((directory / 'artifacts.json').read_text())
            manifest['files'][0]['bytes'] = MAX_FILE_BYTES + 1
            (directory / 'artifacts.json').write_text(json.dumps(manifest))
            original = __import__('os').open
            def guarded(path, *args, **kwargs):
                self.assertEqual(Path(path).name, 'artifacts.json', 'Invalid binding must fail before member read')
                return original(path, *args, **kwargs)
            with patch('check_staff_service_observations.os.open', side_effect=guarded):
                with self.assertRaises(AssertionError): verify_manifest(directory)


if __name__ == '__main__': unittest.main()
