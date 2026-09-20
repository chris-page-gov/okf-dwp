"""Reject altered publication evidence even when its outer digest is regenerated."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from check_learning_site_observation import DIRECTORY, MAX_MANIFEST_BYTES, MAX_MEMBER_BYTES, sha, verify


class LearningPublicationEvidence(unittest.TestCase):
    def copy_fixture(self, root):
        for path in DIRECTORY.iterdir():
            if path.is_file():
                shutil.copyfile(path, root / path.name)

    def test_retained_publication(self):
        self.assertEqual(verify()["matched_requests"], 109)

    def test_altered_url_or_missing_request_is_rejected(self):
        for change in ["url", "census"]:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                for path in DIRECTORY.iterdir():
                    if path.is_file():
                        shutil.copyfile(path, root / path.name)
                receipt = json.loads((root / "observation.json").read_bytes())
                if change == "url":
                    receipt["requests"][0]["response_url"] = "https://example.invalid/"
                else:
                    receipt["requests"].pop()
                raw = json.dumps(receipt).encode()
                (root / "observation.json").write_bytes(raw)
                inventory = json.loads((root / "artifact-manifest.json").read_bytes())
                row = next(x for x in inventory["files"] if x["path"] == "observation.json")
                row.update(bytes=len(raw), sha256=sha(raw))
                (root / "artifact-manifest.json").write_text(json.dumps(inventory))
                with self.assertRaises(ValueError):
                    verify(root)

    def test_root_and_parent_symlinks_are_rejected_before_read(self):
        for mode in ["root", "parent"]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp); actual = base / "actual"; actual.mkdir()
                child = actual / "child"; child.mkdir()
                link = base / "linked"; link.symlink_to(actual, target_is_directory=True)
                target = link if mode == "root" else link / "child"
                with patch("check_learning_site_observation.os.open") as opened:
                    with self.assertRaisesRegex(ValueError, "must not be symlinks"):
                        verify(target)
                    opened.assert_not_called()

    def test_manifest_and_member_symlinks_are_rejected(self):
        for name in ["artifact-manifest.json", "observation.json"]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); self.copy_fixture(root)
                original = root / name; saved = root / "public-copy.json"
                original.rename(saved); original.symlink_to(saved)
                with self.assertRaisesRegex(ValueError, "regular file"):
                    verify(root)

    def test_oversized_manifest_and_member_are_rejected_before_open(self):
        for name, limit in [("artifact-manifest.json", MAX_MANIFEST_BYTES), ("observation.json", MAX_MEMBER_BYTES)]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); self.copy_fixture(root)
                with (root / name).open("wb") as stream:
                    stream.truncate(limit + 1)
                import os
                original = os.open
                def guarded(path, *args, **kwargs):
                    self.assertNotEqual(Path(path), root / name, "Oversized file must not be opened")
                    return original(path, *args, **kwargs)
                with patch("check_learning_site_observation.os.open", side_effect=guarded):
                    with self.assertRaisesRegex(ValueError, "exceeds byte limit"):
                        verify(root)


if __name__ == "__main__":
    unittest.main()
