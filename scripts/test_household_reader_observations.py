"""Offline integrity controls using synthetic artefacts, not browser acceptance."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from check_household_reader_observations import digest, verify_files


class HouseholdObservationIntegrity(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
