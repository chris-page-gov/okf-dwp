"""Guard projection retirement against unknown files and symlink targets."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from structured_projection_output import install_projection


class ProjectionOutputControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'structured-units'
        (self.root / 'records').mkdir(parents=True)
        self.old = b'old generated shard'
        (self.root / 'records/0001.json.gz').write_bytes(self.old)
        self.manifest = json.dumps({'schema': 'okf-dwp-structured-units.v1', 'documents': [], 'records': {'shards': [
            {'path': 'records/0001.json.gz', 'bytes': len(self.old), 'sha256': hashlib.sha256(self.old).hexdigest()}]}}).encode()
        (self.root / 'manifest.json').write_bytes(self.manifest)
        self.new = {'manifest.json': b'new declaration', 'records/0000.json.gz': b'new shard'}

    def test_only_hash_bound_obsolete_shard_is_retired(self):
        retired = install_projection(self.root, self.new, check=False, mode='units')
        self.assertEqual([r['path'] for r in retired], ['records/0001.json.gz'])
        self.assertFalse((self.root / 'records/0001.json.gz').exists())
        install_projection(self.root, self.new, check=True, mode='units')

    def test_unknown_surplus_refuses_before_overwriting_existing_projection(self):
        (self.root / 'notes.txt').write_text('unrecognised content')
        with self.assertRaisesRegex(ValueError, 'Unknown surplus'):
            install_projection(self.root, self.new, check=False, mode='units')
        self.assertEqual((self.root / 'manifest.json').read_bytes(), self.manifest)
        self.assertEqual((self.root / 'records/0001.json.gz').read_bytes(), self.old)
        self.assertFalse((self.root / 'records/0000.json.gz').exists())

    def test_changed_surplus_is_not_removed_or_overwritten(self):
        (self.root / 'records/0001.json.gz').write_bytes(b'changed bytes')
        with self.assertRaisesRegex(ValueError, 'Changed surplus'):
            install_projection(self.root, self.new, check=False, mode='units')
        self.assertEqual((self.root / 'manifest.json').read_bytes(), self.manifest)

    def test_check_never_retires_an_old_shard(self):
        with self.assertRaisesRegex(ValueError, 'obsolete'):
            install_projection(self.root, self.new, check=True, mode='units')
        self.assertEqual((self.root / 'records/0001.json.gz').read_bytes(), self.old)

    def test_unlisted_directory_symlink_is_rejected(self):
        outside = Path(self.temp.name) / 'outside'; outside.mkdir()
        (self.root / 'linked').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            install_projection(self.root, self.new, check=False, mode='units')
        self.assertEqual((self.root / 'manifest.json').read_bytes(), self.manifest)

    def test_previous_context_paths_cannot_escape_root(self):
        context = Path(self.temp.name) / 'structured-context'; context.mkdir()
        (context / 'build-review.json').write_text(json.dumps({'schema': 'okf-dwp-structured-context-build.v1', 'outputs': [{'path': 'other/old', 'bytes': 0, 'sha256': '0'*64}]}))
        with self.assertRaisesRegex(ValueError, 'leave projection root'):
            install_projection(context, {'build-review.json': b'new'}, check=False, mode='context')


if __name__ == '__main__':
    unittest.main()
