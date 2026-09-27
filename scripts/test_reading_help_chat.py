#!/usr/bin/env python3
"""Bounded local Chat pack path controls."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import reading_help_chat as chat


class ChatPathControls(unittest.TestCase):
    def test_authorised_root_and_exclusive_write(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(chat, 'CHAT_TMP_ROOT', Path(folder)):
            path = chat.safe_output(Path(folder) / 'pack.json')
            chat.write_new(path, b'{}')
            self.assertEqual(path.read_bytes(), b'{}')
            with self.assertRaises(ValueError):
                chat.safe_output(Path(folder) / 'pack.json')

    def test_parent_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'authorised'
            root.mkdir()
            with patch.object(chat, 'CHAT_TMP_ROOT', root):
                with self.assertRaisesRegex(ValueError, 'Output must stay'):
                    chat.safe_output(root / '..' / 'escape.json')

    def test_authorised_parent_symlink_route(self):
        with tempfile.TemporaryDirectory() as folder:
            real = Path(folder) / 'real'
            real.mkdir()
            shortcut = Path(folder) / 'shortcut'
            shortcut.symlink_to(real, target_is_directory=True)
            with patch.object(chat, 'CHAT_TMP_ROOT', shortcut):
                path = chat.safe_output(shortcut / 'pack.json')
                self.assertEqual(path, real / 'pack.json')
                chat.write_new(path, b'{}')
                self.assertEqual((real / 'pack.json').read_bytes(), b'{}')

    def test_symlink_leaf_rejected(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(chat, 'CHAT_TMP_ROOT', Path(folder)):
            target = Path(folder) / 'target'
            target.write_bytes(b'old')
            link = Path(folder) / 'link'
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                chat.safe_output(link)
            self.assertEqual(target.read_bytes(), b'old')

    def test_bounded_input_before_allocation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'input'
            path.write_bytes(b'x' * 12)
            with self.assertRaises(ValueError):
                chat.bounded_file(path, 10)
            self.assertEqual(chat.bounded_file(path, 12), b'x' * 12)


if __name__ == '__main__':
    unittest.main()
