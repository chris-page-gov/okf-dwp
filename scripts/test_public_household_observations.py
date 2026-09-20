"""Synthetic local-read boundaries; no browser, provider or network call."""
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
import check_public_household_observations as check


class PublicObservationTests(unittest.TestCase):
    def fixture(self, root):
        directory = root/'attempt-01-chrome'; directory.mkdir()
        member = directory/'executed-harness.mjs'; member.write_bytes(b'original')
        manifest = {'files':[{'path':'attempt-01-chrome/executed-harness.mjs','bytes':8,'sha256':check.sha(b'original')}]}
        (root/'artifact-manifest.json').write_text(json.dumps(manifest))
        return member, manifest

    def test_valid_inventory_and_changed_missing_or_added_member(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp); member,manifest=self.fixture(root); check.load_inventory(root)
            member.write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError,'bytes differ'):check.load_inventory(root)
            member.unlink()
            with self.assertRaises(FileNotFoundError):check.load_inventory(root)
            member.write_bytes(b'original'); (member.parent/'extra.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'inventory differs'):check.load_inventory(root)

    def test_root_and_parent_symlinks_rejected_before_read(self):
        for mode in ['root','parent']:
            with self.subTest(mode=mode), TemporaryDirectory() as tmp:
                base=Path(tmp); actual=base/'actual'; actual.mkdir(); child=actual/'child';child.mkdir()
                link=base/'link';link.symlink_to(actual,target_is_directory=True)
                target=link if mode=='root' else link/'child'
                with patch('check_household_reader_observations.os.open') as opened:
                    with self.assertRaisesRegex(ValueError,'must not be symlinks'):check.load_inventory(target)
                    opened.assert_not_called()

    def test_manifest_member_and_member_parent_symlinks_rejected(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);member,manifest=self.fixture(root)
            original=root/'retained-manifest.json';(root/'artifact-manifest.json').rename(original)
            (root/'artifact-manifest.json').symlink_to(original)
            with self.assertRaisesRegex(ValueError,'regular file'):check.load_inventory(root)
            (root/'artifact-manifest.json').unlink();original.rename(root/'artifact-manifest.json')
            member.unlink(); member.symlink_to(root/'artifact-manifest.json')
            with self.assertRaisesRegex(ValueError,'regular file'):check.load_inventory(root)
            member.unlink();member.parent.rmdir()
            actual=root/'actual';actual.mkdir();(actual/member.name).write_bytes(b'original')
            member.parent.symlink_to(actual,target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'must not be symlinks'):check.load_inventory(root)

    def test_oversized_manifest_or_member_rejected_before_open(self):
        for kind in ['manifest','member']:
            with self.subTest(kind=kind), TemporaryDirectory() as tmp:
                root=Path(tmp);member,manifest=self.fixture(root)
                target=root/'artifact-manifest.json' if kind=='manifest' else member
                limit=check.MAX_MANIFEST if kind=='manifest' else check.MAX_MEMBER
                with target.open('wb') as stream:stream.truncate(limit+1)
                with patch('check_household_reader_observations.os.open') as opened:
                    with self.assertRaisesRegex(ValueError,'exceeds byte limit'):
                        if kind=='manifest':check.load_inventory(root)
                        else:check.verify_inventory(root,manifest)
                    opened.assert_not_called()

    def test_oversized_immutable_git_blob_rejected_before_capture(self):
        with patch.object(check.subprocess,'check_output',return_value=str(check.MAX_GIT_BLOB+1).encode()),patch.object(check.subprocess,'Popen') as capture:
            with self.assertRaisesRegex(ValueError,'Git blob exceeds'):check.git_blob('combined/input.json')
            capture.assert_not_called()

    def test_git_capture_is_capped_and_size_checked(self):
        proc=Mock();proc.stdout=io.BytesIO(b'12345');proc.poll.return_value=0;proc.wait.return_value=0
        with patch.object(check,'MAX_GIT_BLOB',4),patch.object(check.subprocess,'check_output',return_value=b'4'),patch.object(check.subprocess,'Popen',return_value=proc):
            with self.assertRaisesRegex(ValueError,'capture exceeds'):check.git_blob('combined/input.json')
        proc=Mock();proc.stdout=io.BytesIO(b'123');proc.poll.return_value=0;proc.wait.return_value=0
        with patch.object(check.subprocess,'check_output',return_value=b'4'),patch.object(check.subprocess,'Popen',return_value=proc):
            with self.assertRaisesRegex(ValueError,'size or result differs'):check.git_blob('combined/input.json')

    def test_unsafe_inventory_and_git_paths_rejected(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);member,manifest=self.fixture(root)
            for name in ['/absolute','../escape','attempt-01-chrome/../file']:
                changed={'files':[{**manifest['files'][0],'path':name}]}
                with self.assertRaisesRegex(ValueError,'Unsafe'):check.verify_inventory(root,changed)
        for name in ['combined/../secret','.email.md','/absolute']:
            with self.assertRaisesRegex(ValueError,'Unsafe Git'):check.git_blob(name)


if __name__ == '__main__':unittest.main()
