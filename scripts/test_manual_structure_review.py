"""Independent generalisation controls beyond the eight registered source cases.

These synthetic controls do not change the 4/8 experiment denominator or tune
staff questions. Failures are retained as review findings until fixed.
"""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import manual_structure as manual
import pdf_structure_alignment as alignment


def pages(*texts):
    return [{"page": n + 1, "text": text, "url": f"https://example.invalid/source.pdf#page={n + 1}"}
            for n, text in enumerate(texts)]


def untagged():
    return {"status": "not-available", "blocks": [], "unmatched": []}


class ManualStructureIndependentReviewTests(unittest.TestCase):
    def test_repeated_heading_without_disambiguating_context_remains_unknown(self):
        source = pages("Contents\nRepeated heading\n\nIntroduction\nA first paragraph.\n\nRepeated heading\nA second paragraph.\n")
        result = alignment.align_blocks(source, [{"role": "H2", "text": "Repeated heading",
                                                  "tree_line_start": 2, "tree_line_end": 3}])
        self.assertEqual(result["blocks"], [])
        self.assertEqual(len(result["unmatched"]), 1)

    def test_unique_heading_keeps_exact_original_utf8_offsets(self):
        source = pages("Préface\nA heading\n77001 Body text.\n")
        result = alignment.align_blocks(source, [{"role": "H2", "text": "A heading"}])
        matched = result["blocks"][0]
        self.assertEqual(source[0]["text"].encode()[matched["start"]:matched["end"]], b"A heading")
        self.assertEqual(matched["page"], 1)

    def test_reclassified_sidecar_cannot_override_unchanged_raw_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "pdf-structure/dmg"
            target.mkdir(parents=True)
            raw = b'Document\n  P\n    "A heading"\n'
            (target / "sample.tree.txt").write_bytes(raw)
            record = {"pdf_sha256": "a" * 64, "status": "tagged",
                      "tree": {"sha256": hashlib.sha256(raw).hexdigest()},
                      "blocks": [{"role": "H1", "text": "A heading", "tree_line_start": 2, "tree_line_end": 3}]}
            (target / "sample.structure.json").write_text(json.dumps(record))
            with self.assertRaises(ValueError):
                alignment.load_alignment("dmg", {"id": "sample", "sha256": "a" * 64}, pages("A heading\n"), root=root)

    def test_document_notice_cannot_absorb_later_numbered_guidance(self):
        source = pages("Section 77001 - 77099\n77001 First source passage.\nThe content of the examples in this document is illustrative.\n",
                       "77002 Second source passage and its condition.\n")
        with patch.object(manual, "load_alignment", return_value=untagged()):
            units, _ = manual.segment_source("dmg", {"id": "synthetic", "chapter": 77, "kind": "chapter", "role": "substantive"}, source)
        matching = [unit for unit in units if "77002" in unit["paragraph_labels"]]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["role"], "paragraph")

    def test_memo_nested_list_numbers_are_not_body_paragraph_labels(self):
        source = pages("Memo\nIntroduction\n1. This memo has conditions.\n   1. First condition\n   2. Second condition\n2. A later paragraph.\n")
        with patch.object(manual, "load_alignment", return_value=untagged()):
            units, _ = manual.segment_source("adm", {"id": "synthetic", "kind": "memo", "role": "supplementary-guidance-applicability-unreviewed"}, source)
        self.assertTrue(units)
        self.assertTrue(all(not unit["paragraph_labels"] for unit in units))
        self.assertTrue(all(unit["completeness"] == "unresolved" for unit in units))

    def test_untagged_source_remains_complete_partition_and_unreviewed(self):
        source = pages("Some heading\n77001 A source passage begins.\nExample\nA story continues", " on this page.\n77002 Another passage.\n")
        with patch.object(manual, "load_alignment", return_value=untagged()):
            units, structure = manual.segment_source("dmg", {"id": "synthetic", "chapter": 77, "kind": "chapter", "role": "substantive"}, source)
        raw = b''.join(page["text"].encode() for page in source)
        rebuilt = b''.join(source[span["page"] - 1]["text"].encode()[span["start_utf8"]:span["end_utf8"]]
                           for unit in units for span in unit["spans"])
        self.assertEqual(rebuilt, raw)
        self.assertEqual(structure["pdf_structure"]["status"], "not-available")
        self.assertTrue(all(unit["specialist_review"] == "not-reviewed" for unit in units))

    def test_fragmented_annotation_references_belong_to_each_exact_fragment(self):
        import build_logical_units
        source = pages("Memo\nIntroduction\n1. Introductory text.\nAnnotations\nC1001\n" + "padding " * 60 + "\nC1002\nContacts\nContact text.\n")
        with patch.object(manual, "load_alignment", return_value=untagged()), patch.object(build_logical_units, "MAX_UNIT_BYTES", 120):
            units, _ = manual.segment_source("adm", {"id": "synthetic", "kind": "memo", "role": "supplementary-guidance-applicability-unreviewed"}, source)
        self.assertGreater(len([u for u in units if u["role"] == "annotation"]), 1)
        for unit in units:
            raw = unit["text"].encode()
            for reference in unit["references"]:
                actual = raw[reference["start_utf8"]:reference["end_utf8"]].decode()
                self.assertEqual(actual, reference["literal"], unit["key"])

    def test_out_of_range_navigation_heading_does_not_govern(self):
        source = pages("Main group P4001 - P4099\nLater conditions P4090 - P4099\nP4001 First rule.\n")
        with patch.object(manual, "load_alignment", return_value=untagged()):
            units, _ = manual.segment_source("adm", {"id": "synthetic", "chapter": "P4", "kind": "chapter", "role": "substantive"}, source)
        body = next(unit for unit in units if unit["paragraph_labels"] == ["P4001"])
        self.assertNotIn("Later conditions", body["heading_path"])


if __name__ == "__main__":
    unittest.main()
