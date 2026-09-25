"""Checks for the additive passage review projection and its source boundaries."""
import json
from pathlib import Path
import unittest

from build_passage_boundary_review import OUT, build, digest, overlap_bytes, source_ranges


class PassageBoundaryReviewTests(unittest.TestCase):
    def test_all_cases_bind_exact_source_and_candidate_coverage(self):
        outputs = build()
        manifest = json.loads(outputs["manifest.json"])
        self.assertEqual(len(manifest["cases"]), 28)
        self.assertEqual(manifest["impact"]["changed_documents"], 134)
        self.assertEqual(len(manifest["impact"]["substantive_chapters_changed"]), 9)
        self.assertEqual(manifest["impact"]["authored_units_exact"], 75)
        for ref in manifest["cases"]:
            raw = outputs[ref["url"]]
            self.assertEqual(digest(raw), ref["sha256"])
            case = json.loads(raw)
            extraction = outputs[case["document"]["extraction"]["url"]]
            self.assertEqual(digest(extraction), case["document"]["extraction"]["sha256"])
            for unit in case["before"] + case["after"]:
                parts = []
                for span in unit["spans"]:
                    literal = extraction[span["start_utf8"]:span["end_utf8"]]
                    self.assertEqual(digest(literal), span["literal_sha256"])
                    parts.append(literal)
                rebuilt = unit["joiner"].encode().join(parts)
                self.assertEqual(rebuilt.decode("utf-8"), unit["text"])
                self.assertEqual(digest(rebuilt), unit["text_sha256"])
            self.assertEqual(case["coverage"]["old_passage_bytes"], case["coverage"]["covered_once_bytes"])
            self.assertEqual(case["review"]["status"], "pending-independent-review")

    def test_lost_or_duplicated_candidate_bytes_are_rejected(self):
        before = [{"page": 1, "start_utf8": 0, "end_utf8": 10}]
        for after in ([{"page": 1, "start_utf8": 0, "end_utf8": 9}],
                      [{"page": 1, "start_utf8": 0, "end_utf8": 6},
                       {"page": 1, "start_utf8": 5, "end_utf8": 10}]):
            with self.assertRaises(ValueError):
                overlap_bytes(before, after)

    def test_wrong_source_hash_is_rejected(self):
        raw = {1: b"source"}
        ranges = {1: (0, 6)}
        span = [{"page": 1, "start_utf8": 0, "end_utf8": 6,
                 "literal_sha256": digest(b"wrong!")}]
        with self.assertRaisesRegex(ValueError, "Source span hash differs"):
            source_ranges(span, ranges, raw)

    def test_checked_outputs_match_generated_bytes(self):
        outputs = build()
        existing = {p.relative_to(OUT).as_posix(): p.read_bytes() for p in OUT.rglob("*") if p.is_file()}
        self.assertEqual(existing, outputs)


if __name__ == "__main__":
    unittest.main()
