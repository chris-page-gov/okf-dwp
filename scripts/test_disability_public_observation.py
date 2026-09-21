"""Offline admission controls for the separate disability observation checker."""
import os
from pathlib import Path
import tempfile
import unittest

import check_disability_public_observation as check


class CheckerAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve())
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in check.CHECKERS:
            (self.root / name).write_bytes((check.ROOT / 'scripts' / name).read_bytes())
        self.first = self.root / next(iter(check.CHECKERS))

    def test_exact_reviewed_bytes_are_returned(self):
        admitted = check.admit_checker_sources(self.root)
        self.assertEqual(set(admitted), set(check.CHECKERS))
        self.assertEqual(admitted[self.first.name], self.first.read_bytes())

    def test_changed_source_is_rejected(self):
        self.first.write_bytes(self.first.read_bytes() + b'\n# changed\n')
        with self.assertRaisesRegex(ValueError, 'differs'):
            check.admit_checker_sources(self.root)

    def test_symlink_is_rejected(self):
        original = self.first.read_bytes()
        self.first.unlink()
        target = self.root / 'target.py'
        target.write_bytes(original)
        self.first.symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'type or size'):
            check.admit_checker_sources(self.root)

    def test_oversized_file_is_rejected(self):
        self.first.write_bytes(b' ' * (1024 * 1024 + 1))
        with self.assertRaisesRegex(ValueError, 'type or size'):
            check.admit_checker_sources(self.root)

    def test_fifo_is_rejected_without_opening(self):
        self.first.unlink()
        os.mkfifo(self.first)
        with self.assertRaisesRegex(ValueError, 'type or size'):
            check.admit_checker_sources(self.root)

    def test_symlinked_directory_is_rejected(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'directory'):
            check.admit_checker_sources(alias)


if __name__ == '__main__':
    unittest.main()
