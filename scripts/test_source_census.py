#!/usr/bin/env python3
"""Source refresh mutation controls; no network or PDF downloads."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from compare_source_census import ROOT, SOURCE, api_url, build, compare, identity, keyed, refreshed, synthetic_controls


class SourceCensusTests(unittest.TestCase):
    def setUp(self):
        self.row = {"id": "a", "family": "fixture", "publication_url": "https://www.gov.uk/government/publications/a",
                    "attachment_id": "1", "url": "https://example.invalid/a.pdf", "title": "A", "content_sha256": "a",
                    "extraction_sha256": "x", "publication_updated_at": "2026-01-01", "source_publication_date": None,
                    "classification": "chapter"}

    def test_metadata_match_does_not_mean_content_match(self):
        result = compare([self.row], [{**self.row, "content_sha256": None, "extraction_sha256": None}], {self.row["publication_url"]})
        self.assertEqual(result["documents"][0]["content"], "unknown")
        self.assertEqual(result["documents"][0]["metadata"], "no-change-in-comparable-fields")

    def test_unobserved_publication_does_not_report_removed(self):
        result = compare([self.row], [], set())
        self.assertEqual(result["presence_counts"], {"unknown": 1})

    def test_successful_complete_publication_can_report_removed(self):
        result = compare([self.row], [], {self.row["publication_url"]})
        self.assertEqual(result["presence_counts"], {"removed": 1})

    def test_duplicate_attachment_identity_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            keyed([self.row, {**self.row, "url": "https://example.invalid/b.pdf"}])

    def test_attachment_id_scoped_to_publication(self):
        other = {**self.row, "publication_url": "https://www.gov.uk/government/publications/b"}
        self.assertNotEqual(identity(self.row), identity(other))

    def test_content_and_extraction_changes_are_separate(self):
        result = compare([self.row], [{**self.row, "content_sha256": "b"}], {self.row["publication_url"]})
        self.assertEqual(result["documents"][0]["content"], "changed")
        self.assertEqual(result["documents"][0]["extraction"], "unchanged")

    def test_unknown_date_not_substituted_with_publication_update(self):
        result = compare([self.row], [self.row], {self.row["publication_url"]})
        self.assertIn("source_publication_date", result["documents"][0]["unknown_metadata_fields"])

    def test_classification_change_reported_separately(self):
        result = compare([self.row], [{**self.row, "classification": "memo"}], {self.row["publication_url"]})
        self.assertIn("classification", result["documents"][0]["changes"])

    def test_pdf_urls_not_accepted_as_acquisition_routes(self):
        for value in ["https://assets.publishing.service.gov.uk/media/a.pdf", "https://example.invalid/government/publications/a", "file:///tmp/a"]:
            with self.assertRaisesRegex(ValueError, "Only declared"):
                api_url(value)

    def test_synthetic_mutations_retain_all_expected_outcomes(self):
        controls = synthetic_controls()
        self.assertTrue(controls["synthetic"])
        self.assertEqual(controls["added_and_removed"]["presence_counts"], {"added": 1, "removed": 1})
        self.assertEqual(controls["failed_publication_is_unknown"]["presence_counts"], {"unknown": 1})

    def test_actual_observation_accounts_for_both_manuals_without_content_claim(self):
        result = json.loads(build()["evaluation/source-refresh/observed-comparison.json"])
        self.assertEqual(result["before_documents"], 513)
        self.assertEqual(sum(result["presence_counts"].values()), 513)
        self.assertEqual(result["content_counts"], {"unknown": 513})
        self.assertEqual(result["publications"]["successfully_observed"], 12)
        self.assertEqual({r["family"] for r in result["documents"]}, {"dmg", "adm"})

    def test_raw_metadata_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / SOURCE, root / SOURCE)
            manifest = json.loads((root / SOURCE / "manifest.json").read_text())
            p = next((root / SOURCE / "api").glob("*.json"))
            p.write_text(p.read_text() + " ")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                refreshed(root, [], manifest)

    def test_unbound_acquisition_receipts_rejected_before_interpretation(self):
        manifest = json.loads((ROOT / SOURCE / "manifest.json").read_text())
        manifest["files"] = [row for row in manifest["files"] if row["path"] != "receipts.json"]
        # All official API files still match their bindings. The unbound receipt
        # must not be allowed to supply observation dates or publication coverage.
        with self.assertRaisesRegex(ValueError, "receipts must have a verified manifest binding"):
            refreshed(ROOT, [], manifest)


if __name__ == "__main__":
    unittest.main()
