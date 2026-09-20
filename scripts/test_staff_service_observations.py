import copy
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest
from check_staff_service_observations import inventory, verify_manifest, check_outcomes, MAX_FILE_BYTES, MAX_MANIFEST_BYTES


class ObservationIntegrity(unittest.TestCase):
    def fixture(self, directory):
        (directory / 'receipt.json').write_text('{"status":"failed"}\n')
        (directory / 'artifacts.json').write_text(json.dumps({'schema': 'okf-compact-delivery-artifact-manifest.v1', 'files': inventory(directory)}))

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


if __name__ == '__main__': unittest.main()
