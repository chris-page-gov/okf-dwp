import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("learning_public_verifier", HERE / "verify_public.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class PublicationChecks(unittest.TestCase):
    def manifest(self):
        row = lambda path: {"path": path, "bytes": 0, "sha256": "0" * 64}
        return {"schema": "okf-dwp-learning-site.v1", "source_commit": verifier.COMMIT,
                "source_pages": [row("docs/learning-path.md")], "page_count": 1,
                "files": [row(name) for name in ("docs/learning-path.html", "index.html", "assets/learning.css", ".nojekyll")],
                "scope": "Public documentation"}

    def test_manifest_counts_are_derived_and_duplicate_or_extra_paths_are_rejected(self):
        manifest = self.manifest()
        self.assertEqual(len(verifier.validate_manifest(manifest)[1]), 4)
        manifest["files"].append(manifest["files"][0])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            verifier.validate_manifest(manifest)
        manifest = self.manifest()
        manifest["files"][0]["path"] = "unexpected.html"
        with self.assertRaisesRegex(ValueError, "Unexpected generated"):
            verifier.validate_manifest(manifest)

    def test_private_source_wrong_commit_and_oversized_member_are_rejected(self):
        for source in (".email.md", "research/private.md", "docs/../private.md"):
            manifest = self.manifest()
            manifest["source_pages"][0]["path"] = source
            with self.assertRaises(ValueError):
                verifier.validate_manifest(manifest)
        manifest = self.manifest()
        manifest["source_commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "identity"):
            verifier.validate_manifest(manifest)
        manifest = self.manifest()
        manifest["files"][0]["bytes"] = verifier.MAX_MEMBER + 1
        with self.assertRaisesRegex(ValueError, "byte bound"):
            verifier.validate_manifest(manifest)

    def test_local_reads_reject_oversized_files_and_root_parent_or_file_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            actual = root / "actual"
            actual.mkdir()
            file = actual / "file"
            file.write_bytes(b"bound")
            self.assertEqual(verifier.bounded_read(file, 5), b"bound")
            with self.assertRaises(ValueError):
                verifier.bounded_read(file, 4)
            (root / "linked").symlink_to(actual, target_is_directory=True)
            with self.assertRaises(ValueError):
                verifier.bounded_read(root / "linked/file", 5)
            (actual / "alias").symlink_to(file)
            with self.assertRaises(ValueError):
                verifier.bounded_read(actual / "alias", 5)

    def test_internal_targets_and_decoded_fragments_include_base_paths_and_home_alias(self):
        materials = {"index.html": b'<a href="/okf-dwp/docs/page.html#some%20id">Go</a>',
                     "docs/page.html": b'<h1 id="some id">Page</h1><a href="../">Home</a><a href="https://example.test/old#missing">Historical</a>'}
        result = verifier.audit_links(materials)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["internal_links"], 2)
        self.assertEqual(result["external_links_not_fetched"], 1)

    def test_audit_retains_missing_target_missing_fragment_and_duplicate_ids(self):
        result = verifier.audit_links({"index.html": b'<a href="missing.html">X</a><a href="#unknown">Y</a><i id="repeated"></i><i id="repeated"></i>'})
        self.assertEqual({row["kind"] for row in result["errors"]}, {"missing-target", "missing-fragment", "duplicate-id"})

    def test_existing_output_is_preserved_before_source_or_network_access(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            output = root / "retained.json"
            output.write_bytes(b"previous observation")
            with patch("sys.argv", ["verify_public.py", "--dwp-root", str(root), "--expected-manifest", str(root / "missing"), "--output", str(output)]), \
                 patch.object(verifier, "verify_sources", side_effect=AssertionError("Source read attempted")), \
                 patch.object(verifier, "fetch_one", side_effect=AssertionError("Network attempted")):
                with self.assertRaises(FileExistsError):
                    verifier.main()
            self.assertEqual(output.read_bytes(), b"previous observation")


if __name__ == "__main__":
    unittest.main()
