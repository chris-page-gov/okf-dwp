"""Independent synthetic controls for source preservation and uncertain boundaries."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build_logical_units as b


def fixture(texts, family="dmg", chapter=7):
    doc = {"id": "test-document", "title": "Synthetic manual", "url": "https://example.test/manual.pdf",
           "sha256": "a" * 64, "pages_sha256": "b" * 64, "pages_path": "source/pages/test.json",
           "pages": len(texts), "chapter": chapter, "observed_at": "2026-09-15T00:00:00Z",
           "role": "synthetic-test", "quality": {"flagged_pages": []}}
    extracted = {"pages": [{"page": n, "url": doc["url"] + f"#page={n}", "text": text} for n, text in enumerate(texts, 1)]}
    return doc, extracted


def override(doc, extracted, first=0, last=None):
    total = sum(len(p["text"].encode()) for p in extracted["pages"])
    spans = b.source_spans(extracted["pages"], first, total if last is None else last)
    return {"family": "dmg", "document_id": doc["id"], "source_sha256": doc["sha256"],
            "pages_sha256": doc["pages_sha256"], "inventory_sha256": "c" * 64,
            "units": [{"key": "reviewed-rule", "label": "Reviewed source boundary", "kind": "rule",
                       "paragraph_labels": ["077001"], "spans": spans,
                       "review_status": "agent-reviewed-boundary-only", "specialist_review": "not-reviewed",
                       "review_note": "Synthetic fixture, no real-world applicability claim.",
                       "completeness": "complete-within-declared-boundary"}]}


class LogicalUnits(unittest.TestCase):
    def test_cross_page_examples_lists_notes_and_citations_are_preserved(self):
        texts = ["Introduction\n077001 The condition applies if\n1. the first condition; and\nExample 1\n",
                 "the continuation of the example.\nNote: subject to the exception.\n1 Reg 5; 2 Reg 6\n077002 A different rule.\n"]
        doc, extracted = fixture(texts)
        records, catalogue = b.segment_document("dmg", doc, extracted, "c" * 64)
        first = next(r for r in records if "guidance-077001" in r["id"])
        self.assertIn("Example 1\n\nthe continuation", first["text"])
        self.assertIn("1 Reg 5; 2 Reg 6", first["text"])
        self.assertNotIn("077002", first["text"])
        self.assertEqual(first["evidence_unit"]["completeness"], "unresolved")
        self.assertEqual(catalogue["counts"]["source_bytes_accounted"], sum(len(t.encode()) for t in texts))
        self.assertEqual(catalogue["counts"]["unassigned_bytes"], 0)

    def test_adm_alphanumeric_body_and_contents_are_distinct(self):
        doc, extracted = fixture(["Contents\nC1986 One month ........... 120\n",
                                  "One month\nC1986 A condition.\nC1987 An exception.\n"], "adm", "C1")
        records, catalogue = b.segment_document("adm", doc, extracted, "c" * 64)
        selected = [r for r in records if "guidance-c1986" in r["id"]]
        self.assertEqual(len(selected), 1)
        self.assertTrue(catalogue["structure_candidates"][0]["contents_candidate"])
        self.assertIn("Contents", records[0]["text"])
        self.assertEqual(catalogue["counts"]["contents_candidate_pages"], 1)

    def test_duplicate_labels_have_distinct_occurrence_and_section_ids(self):
        doc, extracted = fixture(["State Pension Credit\n077030 One branch.\nState Pension\n077030 Another branch.\n"])
        records, catalogue = b.segment_document("dmg", doc, extracted, "c" * 64)
        duplicate = [r for r in records if "guidance-077030" in r["id"]]
        self.assertEqual(len(duplicate), 2)
        self.assertNotEqual(duplicate[0]["id"], duplicate[1]["id"])
        self.assertIn("occurrence-0001", duplicate[0]["id"])
        self.assertIn("occurrence-0002", duplicate[1]["id"])
        self.assertEqual(catalogue["duplicate_paragraph_labels"], {"077030": 2})

    def test_reserved_ranges_remain_visible_without_expansion(self):
        doc, extracted = fixture(["077001 A condition.\n077002–077099 Reserved\n077100 Another condition.\n"])
        records, catalogue = b.segment_document("dmg", doc, extracted, "c" * 64)
        self.assertEqual(len(catalogue["structure_candidates"][0]["reserved_candidates"]), 1)
        self.assertTrue(any("077002–077099 Reserved" in r["text"] for r in records))
        self.assertFalse(any("guidance-077050" in r["id"] for r in records))

    def test_empty_and_damaged_extraction_have_explicit_accounting(self):
        doc, extracted = fixture(["", " \n\t", "Unassigned damaged \ufffd text\n"])
        doc["quality"]["flagged_pages"] = [{"page": 3, "flags": ["replacement-character"]}]
        records, catalogue = b.segment_document("dmg", doc, extracted, "c" * 64)
        self.assertEqual(catalogue["counts"]["empty_pages"], 2)
        self.assertEqual(catalogue["pages"][0]["accounting"], [])
        self.assertEqual(catalogue["pages"][2]["quality_flags"], ["replacement-character"])
        self.assertIn("\ufffd", records[0]["text"])
        self.assertEqual(records[0]["evidence_unit"]["kind"], "unresolved-fragment")

    def test_utf8_offsets_fragment_hashes_and_joiners_reconstruct(self):
        doc, extracted = fixture(["Intro £ 😀\n077001 Claimant’s condition\n", "and café.\n077002 Next.\n"])
        records, _ = b.segment_document("dmg", doc, extracted, "c" * 64)
        for record in records:
            payload = record["text"].encode()
            parts = []
            for span in record["evidence_unit"]["spans"]:
                page = next(p for p in extracted["pages"] if p["url"] == span["source_url"])
                original = page["text"].encode()[span["source_start"]:span["source_end"]]
                self.assertEqual(original, payload[span["unit_start"]:span["unit_end"]])
                self.assertEqual(b.sha(original), span["literal_sha256"])
                parts.append(original)
            self.assertEqual(b"\n".join(parts), payload)
            self.assertTrue(all(p["literal_sha256"] == b.sha(payload) for p in record["provenance"]))

    def test_reviewed_override_preserves_uncovered_material_and_source_binding(self):
        doc, extracted = fixture(["Navigation\n077001 Condition.\nExample 1\nFull example.\n077002 Another.\n"])
        text = extracted["pages"][0]["text"]
        start, end = len("Navigation\n".encode()), len(text[:text.index("077002")].encode())
        spec = override(doc, extracted, start, end)
        records, catalogue = b.segment_document("dmg", doc, extracted, "c" * 64, spec)
        selected = next(r for r in records if "/reviewed-rule-" in r["id"])
        self.assertEqual(selected["text"], text.encode()[start:end].decode())
        self.assertEqual(selected["evidence_unit"]["boundary_status"], "author-declared")
        self.assertEqual(catalogue["counts"]["source_bytes_accounted"], len(text.encode()))
        self.assertTrue(any("Navigation" in r["text"] for r in records))
        self.assertTrue(any("077002" in r["text"] for r in records))
        spec["source_sha256"] = "d" * 64
        with self.assertRaisesRegex(ValueError, "source binding"):
            b.segment_document("dmg", doc, extracted, "c" * 64, spec)

    def test_overlapping_discontinuous_bad_hash_or_specialist_overrides_reject(self):
        doc, extracted = fixture(["077001 This is a rule.\n077002 This is another.\n"])
        base = override(doc, extracted)
        variants = []
        x = copy.deepcopy(base); x["units"].append({**x["units"][0], "key": "overlapping"}); variants.append(x)
        x = copy.deepcopy(base); x["units"][0]["spans"][0]["literal_sha256"] = "e" * 64; variants.append(x)
        x = copy.deepcopy(base); x["units"][0]["specialist_review"] = "accepted"; variants.append(x)
        x = copy.deepcopy(base); x["units"][0]["support_unit_keys"] = ["missing"]; variants.append(x)
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                b.segment_document("dmg", doc, extracted, "c" * 64, variant)

    def test_oversized_automatic_candidate_remains_bounded_uncertain_fragments(self):
        doc, extracted = fixture(["077001 " + "😀" * 26000 + "\n"])
        records, catalogue = b.segment_document("dmg", doc, extracted, "c" * 64)
        self.assertGreater(len(records), 1)
        self.assertTrue(all(len(r["text"].encode()) <= b.MAX_UNIT_BYTES for r in records))
        self.assertTrue(all(r["evidence_unit"]["kind"] == "unresolved-fragment" for r in records))
        self.assertEqual(catalogue["counts"]["source_bytes_accounted"], len(extracted["pages"][0]["text"].encode()))
        with self.assertRaisesRegex(ValueError, "too large"):
            b.segment_document("dmg", doc, extracted, "c" * 64, override(doc, extracted))

    def test_source_version_changes_when_source_bytes_binding_changes(self):
        doc, extracted = fixture(["077001 A condition.\n"])
        first, _ = b.segment_document("dmg", doc, extracted, "c" * 64)
        other = copy.deepcopy(doc); other["sha256"] = "f" * 64
        second, _ = b.segment_document("dmg", other, extracted, "c" * 64)
        self.assertNotEqual(first[0]["id"], second[0]["id"])

    def test_source_input_bounds_symlink_and_fifo_admission(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            (root / "input.json").write_text("{}")
            reader = b.Inputs(root)
            self.assertEqual(reader.read("input.json"), b"{}")
            with self.assertRaises(ValueError): reader.read("input.json", limit=1)
            with self.assertRaises(ValueError): reader.read("../input.json")
            (root / "link").symlink_to(root / "input.json")
            with self.assertRaises(ValueError): reader.read("link")
            os.mkfifo(root / "fifo")
            with self.assertRaises(ValueError): reader.read("fifo")

    def test_json_duplicate_keys_and_nonfinite_reject(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}', b'{"a":-1e999}'):
            with self.assertRaises(ValueError): b.strict_json(raw)

    def test_changed_authored_boundary_gets_new_id_unchanged_boundary_repeats(self):
        doc, extracted = fixture(["077001 A condition.\n077002 Another condition.\n"])
        whole = override(doc, extracted)
        first, _ = b.segment_document("dmg", doc, extracted, "c" * 64, whole)
        repeated, _ = b.segment_document("dmg", doc, extracted, "c" * 64, whole)
        shortened = override(doc, extracted, last=len("077001 A condition.\n".encode()))
        changed, _ = b.segment_document("dmg", doc, extracted, "c" * 64, shortened)
        get = lambda rows: next(r for r in rows if "/reviewed-rule-" in r["id"])
        self.assertEqual(get(first), get(repeated))
        self.assertNotEqual(get(first)["id"], get(changed)["id"])

    def test_unrecognised_number_lines_are_accounted_and_reported(self):
        doc, extracted = fixture(["077001\nBody on a following line.\n077002 et seq applies.\n077003 A detected rule.\n"])
        records, catalogue = b.segment_document("dmg", doc, extracted, "c" * 64)
        self.assertEqual(catalogue["counts"]["unsegmented_number_candidates"], 2)
        self.assertEqual(catalogue["counts"]["numbered_boundary_candidates"], 1)
        self.assertIn("077001\nBody", records[0]["text"])

    def test_many_pages_respect_provenance_bound_without_dropping_a_byte(self):
        doc, extracted = fixture(["077001 Start.\n"] + ["continued £ text.\n"] * 35)
        records, catalogue = b.segment_document("dmg", doc, extracted, "c" * 64)
        self.assertEqual(len(records), 2)
        self.assertTrue(all(len(r["evidence_unit"]["spans"]) <= b.MAX_SPANS and len(r["provenance"]) <= 32 for r in records))
        self.assertEqual(catalogue["counts"]["unassigned_bytes"], 0)

    def test_source_file_replaced_by_fifo_after_admission_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            source = root / "source.json"; source.write_text("{}")
            original_open = b.os.open
            def replace(path, flags):
                source.unlink(); os.mkfifo(source)
                return original_open(path, flags)
            with patch.object(b.os, "open", side_effect=replace), self.assertRaisesRegex(ValueError, "changed during admission"):
                b.Inputs(root).read("source.json")

    def test_empty_page_visual_review_is_exactly_bound_and_not_a_rule(self):
        doc, extracted = fixture(["077001 A rule.\n", ""])
        expected = {"family": "dmg", "document_id": doc["id"], "page": 2, "expected_text_bytes": 0,
                    "expected_text_sha256": b.sha(b""), "review_status": "agent-visual-review-blank-render"}
        records, catalogue = b.segment_document("dmg", doc, extracted, "c" * 64, page_expectations=[expected])
        self.assertEqual(catalogue["pages"][1]["authored_page_expectation"], expected)
        self.assertEqual(catalogue["counts"]["authored_page_expectations"], 1)
        self.assertEqual(len(records), 1)
        wrong = {**expected, "expected_text_sha256": "d" * 64}
        with self.assertRaisesRegex(ValueError, "exact frozen source"):
            b.segment_document("dmg", doc, extracted, "c" * 64, page_expectations=[wrong])

    def test_authored_labels_and_capture_metadata_cannot_drift_from_sources(self):
        doc, extracted = fixture(["077001 A rule.\n"])
        for change in ("label", "date"):
            spec = override(doc, extracted)
            if change == "label": spec["units"][0]["paragraph_labels"] = ["077099"]
            else: spec["observed_at"] = "2020-01-01T00:00:00Z"
            with self.subTest(change=change), self.assertRaises(ValueError):
                b.segment_document("dmg", doc, extracted, "c" * 64, spec)

    def test_generated_output_parent_symlink_or_escape_rejects(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            (root / "logical").mkdir()
            (root / "elsewhere").mkdir()
            (root / "logical" / "records").symlink_to(root / "elsewhere", target_is_directory=True)
            with self.assertRaises(ValueError): b.admitted_output(root / "logical", "records/0000.json.gz")
            with self.assertRaises(ValueError): b.admitted_output(root / "logical", "../escape.json")
            self.assertEqual(list((root / "elsewhere").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
