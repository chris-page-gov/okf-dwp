"""Offline integrity controls using synthetic artefacts, not browser acceptance."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from check_household_reader_observations import digest, verify_files, validate, MAX_MANIFEST_BYTES, MAX_MEMBER_BYTES


class HouseholdObservationIntegrity(unittest.TestCase):
    def fixture(self, root):
        (root / "fixture").write_bytes(b"original")
        return {"files": [{"path": "fixture", "bytes": 8, "sha256": digest(b"original")}]}

    def test_changed_or_unlisted_bytes_are_rejected(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "fixture").write_bytes(b"original")
            manifest = {"files": [{"path": "fixture", "bytes": 8, "sha256": digest(b"original")}]}
            verify_files(root, manifest)
            (root / "fixture").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "bytes differ"):
                verify_files(root, manifest)
            (root / "fixture").write_bytes(b"original")
            (root / "unexpected").write_bytes(b"extra")
            with self.assertRaisesRegex(ValueError, "inventory differs"):
                verify_files(root, manifest)

    def test_unsafe_duplicate_and_symlink_paths_are_rejected(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "fixture").write_bytes(b"original")
            manifest = {"files": [{"path": "fixture", "bytes": 8, "sha256": digest(b"original")}]}
            for path in ["../outside", "/absolute", "dir/../fixture"]:
                changed = deepcopy(manifest); changed["files"][0]["path"] = path
                with self.assertRaisesRegex(ValueError, "Unsafe"):
                    verify_files(root, changed)
            with self.assertRaisesRegex(ValueError, "Repeated"):
                verify_files(root, {"files": manifest["files"] * 2})
            (root / "link").symlink_to(root / "fixture")
            changed = deepcopy(manifest); changed["files"][0]["path"] = "link"
            with self.assertRaisesRegex(ValueError, "regular file"):
                verify_files(root, changed)

    def test_root_and_parent_symlinks_are_rejected_before_read(self):
        for mode in ["root", "parent"]:
            with self.subTest(mode=mode), TemporaryDirectory() as tmp:
                base = Path(tmp); actual = base / "actual"; actual.mkdir()
                child = actual / "child"; child.mkdir()
                link = base / "linked"; link.symlink_to(actual, target_is_directory=True)
                target = link if mode == "root" else link / "child"
                with patch("check_household_reader_observations.os.open") as opened:
                    with self.assertRaisesRegex(ValueError, "must not be symlinks"):
                        validate(target)
                    opened.assert_not_called()

    def test_manifest_symlink_and_member_parent_symlink_are_rejected(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            public = root / "public.json"; public.write_text("{}")
            (root / "artifact-manifest.json").symlink_to(public)
            with self.assertRaisesRegex(ValueError, "regular file"):
                validate(root)
            actual = root / "actual"; actual.mkdir(); manifest = self.fixture(actual)
            (root / "linked").symlink_to(actual, target_is_directory=True)
            manifest["files"][0]["path"] = "linked/fixture"
            with self.assertRaisesRegex(ValueError, "must not be symlinks"):
                verify_files(root, manifest)

    def test_oversized_manifest_and_member_are_rejected_before_open(self):
        for name, limit in [("artifact-manifest.json", MAX_MANIFEST_BYTES), ("fixture", MAX_MEMBER_BYTES)]:
            with self.subTest(name=name), TemporaryDirectory() as tmp:
                root = Path(tmp); manifest = self.fixture(root)
                with (root / name).open("wb") as stream:
                    stream.truncate(limit + 1)
                with patch("check_household_reader_observations.os.open") as opened:
                    with self.assertRaisesRegex(ValueError, "exceeds byte limit"):
                        if name == "artifact-manifest.json":
                            validate(root)
                        else:
                            verify_files(root, manifest)
                    opened.assert_not_called()


if __name__ == "__main__":
    unittest.main()
