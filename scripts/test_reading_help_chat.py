#!/usr/bin/env python3
"""Bounded local Chat pack path controls."""
from pathlib import Path
import tempfile
import unittest

from reading_help_chat import bounded_file, safe_output, write_new


class ChatPathControls(unittest.TestCase):
    def test_authorised_tmp_relocation_and_exclusive_write(self):
        with tempfile.TemporaryDirectory(dir='/Users/crpage/tmp') as folder:
            path = safe_output(Path(folder) / 'pack.json')
            write_new(path, b'{}')
            self.assertEqual(path.read_bytes(), b'{}')
            with self.assertRaises(ValueError):
                safe_output(Path(folder) / 'pack.json')

    def test_parent_traversal_rejected(self):
        with tempfile.TemporaryDirectory(dir='/Users/crpage/tmp') as folder:
            escape = Path(folder) / '..' / '..' / 'repos' / 'escape.json'
            with self.assertRaises(ValueError):
                safe_output(escape)

    def test_symlink_leaf_rejected(self):
        with tempfile.TemporaryDirectory(dir='/Users/crpage/tmp') as folder:
            target = Path(folder) / 'target'
            target.write_bytes(b'old')
            link = Path(folder) / 'link'
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                safe_output(link)
            self.assertEqual(target.read_bytes(), b'old')

    def test_bounded_input_before_allocation(self):
        with tempfile.TemporaryDirectory(dir='/Users/crpage/tmp') as folder:
            path = Path(folder) / 'input'
            path.write_bytes(b'x' * 12)
            with self.assertRaises(ValueError):
                bounded_file(path, 10)
            self.assertEqual(bounded_file(path, 12), b'x' * 12)


if __name__ == '__main__':
    unittest.main()
