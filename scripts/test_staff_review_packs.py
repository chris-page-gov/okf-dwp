"""Bounded excerpts, source identities and independent review inputs stay separate."""
import json
import unittest

from build_bundle import ROOT, digest
from build_staff_review_packs import OUTPUT, bounded_excerpt, compile_review_packs


class StaffReviewTests(unittest.TestCase):
    def test_rebuild_matches_generated_outputs(self):
        for path, expected in compile_review_packs().items():
            self.assertEqual((ROOT / path).read_bytes(), expected)

    def test_all_occurrences_preserve_wording_and_duplicates(self):
        registry = json.loads((ROOT / "evaluation/staff-questions/cases.json").read_bytes())
        manifest = json.loads((ROOT / OUTPUT / "manifest.json").read_bytes())
        self.assertEqual(len(manifest["cases"]), 40)
        self.assertEqual(manifest["unique_questions"], 39)
        for old, new in zip(registry["cases"], manifest["cases"]):
            self.assertEqual(old["id"], new["id"])
            self.assertEqual(old["question"], new["question"])
            self.assertEqual(old["duplicate_of"], new["duplicate_of"])

    def test_rejects_missing_anchor(self):
        with self.assertRaisesRegex(ValueError, "anchor is absent"):
            bounded_excerpt("Original page", "invented")

    def test_rejects_limit_smaller_than_anchor(self):
        with self.assertRaises(ValueError):
            bounded_excerpt("A long anchor", "long anchor", 4)

    def test_span_round_trip_with_unicode_and_omissions(self):
        text = "£ prefix\n12345 this is the anchor\n" + "tail " * 1000
        row = bounded_excerpt(text, "12345", 150)
        self.assertEqual(row["text"], text[row["start"]:row["end"]])
        self.assertEqual(digest(row["text"].encode()), row["sha256"])
        self.assertGreater(row["omitted_before"], 0)
        self.assertGreater(row["omitted_after"], 0)

    def test_pack_links_are_bound_and_no_sufficiency(self):
        manifest = json.loads((ROOT / OUTPUT / "manifest.json").read_bytes())
        for row in manifest["cases"]:
            path = ROOT / OUTPUT / row["path"]
            raw = path.read_bytes()
            self.assertEqual(digest(raw), row["sha256"])
            self.assertLessEqual(len(raw), 16384)
            pack = json.loads(raw)
            self.assertEqual(pack["evidence_status"], "insufficient")
            self.assertIsNone(pack["ai_answer"])
            self.assertTrue(all(x["status"] == "not-yet-established" for x in pack["required_evidence"]))
            for source in pack["candidate_evidence"]:
                target = (path.parent / source["path"]).resolve()
                self.assertTrue(target.is_relative_to(ROOT / OUTPUT / "evidence"))
                evidence = target.read_bytes()
                self.assertEqual(len(evidence), source["bytes"])
                self.assertEqual(digest(evidence), source["sha256"])
                self.assertEqual(json.loads(evidence)["id"], source["id"])

    def test_all_shared_excerpts_match_frozen_source_and_neighbours(self):
        for path in (ROOT / OUTPUT / "evidence").glob("*.json"):
            source = json.loads(path.read_bytes())
            p = source["provenance"]
            pages = json.loads((ROOT / p["pages_path"]).read_bytes())["pages"]
            page = pages[p["page"] - 1]
            e = source["excerpt"]
            self.assertEqual(e["text"], page["text"][e["start"]:e["end"]])
            self.assertEqual(p["page_literal_sha256"], digest(page["text"].encode()))
            self.assertLessEqual(len(e["text"]), 1800)
            for adjacent in source["adjacent_pages"]:
                self.assertEqual(pages[adjacent["page"] - 1]["url"], adjacent["url"])


if __name__ == "__main__":
    unittest.main()
