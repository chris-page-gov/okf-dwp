"""Reject altered publication evidence even when its outer digest is regenerated."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from check_learning_site_observation import DIRECTORY, sha, verify


class LearningPublicationEvidence(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
