"""Negative controls for trial evidence bindings; no model response grading."""
from copy import deepcopy
import unittest

from verify_full_dmg_trials import BASE, REGISTRY, TrialReplay, digest, pointer, unique


class TrialReplayTests(unittest.TestCase):
    def setUp(self):
        self.replay = TrialReplay()

    def test_pointer_handles_escaped_keys_and_rejects_non_indices(self):
        self.assertEqual(pointer({"a/b": {"~x": [17]}}, "/a~1b/~0x/0"), 17)
        for path in ("/00", "/-", "/2", "/~2"):
            with self.assertRaises(ValueError):
                pointer([17], path)

    def test_duplicate_case_identity_cannot_inflate_denominator(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            unique([{"case_id": "a"}, {"case_id": "a"}], "case_id", "trials")

    def test_retargeted_original_pointer_fails_even_with_valid_packet_hash(self):
        case = deepcopy(self.replay.read(REGISTRY)["cases"][0])
        case["source_packet"]["json_pointer"] = "/retrieval_cases/1"
        with self.assertRaisesRegex(ValueError, "Original case pointer mismatch"):
            self.replay.registry_case(case)

    def test_changed_response_cannot_reuse_original_hash(self):
        case = deepcopy(self.replay.read(BASE + "esa-trials.json")["cases"][0])
        registry = next(c for c in self.replay.read(REGISTRY)["cases"] if c["registry_id"] == case["case_id"])
        case["answer"] += " Unrecorded extra assertion."
        with self.assertRaisesRegex(ValueError, "Observed response hash"):
            self.replay.observed_case(case, registry, "answer", "answer_sha256")

    def test_quote_cannot_move_to_another_valid_page_with_its_real_hash(self):
        ev = self.replay.read(BASE + "esa-trials.json")["cases"][0]["evidence"][0]
        doc, page = self.replay.source_page("dmg-vol8-ch41", 6)
        with self.assertRaisesRegex(ValueError, "not at the cited page"):
            self.replay.evidence(doc["id"], 6, route="page/dmg-vol8-ch41/0006", url=page["url"],
                                 pdf_hash=doc["sha256"], page_hash=digest(page["text"].encode()),
                                 text=ev["quote"], text_hash=ev["quote_sha256"])

    def test_wrong_source_hash_fails_even_if_quote_matches(self):
        ev = self.replay.read(BASE + "esa-trials.json")["cases"][0]["evidence"][0]
        with self.assertRaisesRegex(ValueError, "source identity"):
            self.replay.evidence("dmg-vol8-ch41", 5, route=ev["route"], url=ev["url"],
                                 pdf_hash="0" * 64, page_hash=ev["page_text_sha256"],
                                 text=ev["quote"], text_hash=ev["quote_sha256"])

    def test_unsupported_assessment_promotion_fails(self):
        assessment = deepcopy(self.replay.read(BASE + "esa-assessment.json"))
        trial = self.replay.read(BASE + "esa-trials.json")
        assessment["cases"][0]["specialist_accepted"] = True
        with self.assertRaisesRegex(ValueError, "specialist promotion"):
            self.replay.assessment_cases("esa", assessment, unique(trial["cases"], "case_id", "ESA"), {})

    def test_unrecognised_grade_is_not_silently_counted_as_success(self):
        assessment = deepcopy(self.replay.read(BASE + "esa-assessment.json"))
        trial = self.replay.read(BASE + "esa-trials.json")
        assessment["cases"][0]["assessment"] = "looks-good"
        with self.assertRaisesRegex(ValueError, "Unrecognised recorded grade"):
            self.replay.assessment_cases("esa", assessment, unique(trial["cases"], "case_id", "ESA"), {})

    def test_portable_reader_rejects_paths_outside_repository(self):
        for path in ("../outside.json", "/tmp/outside.json"):
            with self.assertRaises(ValueError):
                self.replay.path(path)

    def test_missing_locator_is_not_invented_from_a_different_number(self):
        with self.assertRaisesRegex(ValueError, "Locator token missing"):
            self.replay.locator("01002 An actual paragraph.", "DMG 01001")


if __name__ == "__main__":
    unittest.main()
