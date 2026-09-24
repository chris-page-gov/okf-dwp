"""Exercise successor isolation without changing the frozen projection producer."""
from pathlib import Path
import tempfile
import unittest

from check_structured_context_with_successor import check_base_with_successor


class SuccessorIsolationTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.base = self.root / 'structured-context'
        (self.base / 'evidence-connect').mkdir(parents=True)
        self.outputs = {
            'evidence-connect-manifest.json': b'{"successor":true}',
            'evidence-connect/records.json.gz': b'source-bound bytes',
        }
        for name, raw in self.outputs.items():
            path = self.base / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        (self.base / 'base-index.json').write_bytes(b'frozen base')

    def test_base_sees_only_its_files_and_successor_returns_unchanged(self):
        def base_check(_root):
            self.assertFalse((self.base / 'evidence-connect-manifest.json').exists())
            self.assertFalse((self.base / 'evidence-connect/records.json.gz').exists())
            self.assertEqual((self.base / 'base-index.json').read_bytes(), b'frozen base')
        check_base_with_successor(self.root, outputs=self.outputs, base_check=base_check)
        for name, raw in self.outputs.items():
            self.assertEqual((self.base / name).read_bytes(), raw)

    def test_drift_refuses_before_any_move(self):
        target = self.base / 'evidence-connect-manifest.json'
        target.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'drift'):
            check_base_with_successor(self.root, outputs=self.outputs, base_check=lambda _root: self.fail('base ran'))
        self.assertEqual(target.read_bytes(), b'changed')
        self.assertEqual((self.base / 'evidence-connect/records.json.gz').read_bytes(),
                         self.outputs['evidence-connect/records.json.gz'])

    def test_symlink_refuses_before_any_move(self):
        target = self.base / 'evidence-connect-manifest.json'
        target.unlink()
        target.symlink_to(self.base / 'base-index.json')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            check_base_with_successor(self.root, outputs=self.outputs, base_check=lambda _root: self.fail('base ran'))
        self.assertTrue(target.is_symlink())

    def test_base_failure_is_primary_and_restores_successor(self):
        def fail(_root):
            raise RuntimeError('base projection failed')
        with self.assertRaisesRegex(RuntimeError, 'base projection failed'):
            check_base_with_successor(self.root, outputs=self.outputs, base_check=fail)
        for name, raw in self.outputs.items():
            self.assertEqual((self.base / name).read_bytes(), raw)

    def test_unexpected_file_is_never_moved(self):
        extra = self.base / 'unknown.json'
        extra.write_bytes(b'unknown')
        def base_check(_root):
            self.assertEqual(extra.read_bytes(), b'unknown')
            raise ValueError('unknown surplus')
        with self.assertRaisesRegex(ValueError, 'unknown surplus'):
            check_base_with_successor(self.root, outputs=self.outputs, base_check=base_check)
        self.assertEqual(extra.read_bytes(), b'unknown')


if __name__ == '__main__':
    unittest.main()
