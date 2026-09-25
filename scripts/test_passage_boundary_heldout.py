"""Source-bound controls outside the known outlier and development sets."""
import hashlib
import json
from pathlib import Path
import unittest

from passage_boundary_parser import segment_source

ROOT = Path(__file__).resolve().parents[1]
CONTROLS = ROOT / "domain-profile/passage-boundary-review/held-out-controls.json"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def document(family: str, identifier: str) -> dict:
    path = ROOT / ("source/full-dmg-2026-09-15/inventory.json" if family == "dmg"
                   else "source/adm-2026-09-19/inventory.json")
    return next(row for row in json.loads(path.read_bytes())["documents"] if row["id"] == identifier)


def source(control: dict) -> tuple[dict, list[dict]]:
    doc = document(control["family"], control["document_id"])
    assert doc["sha256"] == control["pdf_sha256"]
    assert sha((ROOT / doc["pdf_path"]).read_bytes()) == control["pdf_sha256"]
    raw = (ROOT / control["pages_path"]).read_bytes()
    assert sha(raw) == doc["pages_sha256"] == control["pages_sha256"]
    extraction = json.loads(raw)
    assert extraction["source_sha256"] == control["pdf_sha256"]
    return doc, extraction["pages"]


class HeldOutSourceControls(unittest.TestCase):
    def test_two_genuine_cross_page_passages_remain_whole(self):
        controls = json.loads(CONTROLS.read_bytes())
        self.assertEqual(len(controls["cross_page_controls"]), 2)
        for control in controls["cross_page_controls"]:
            with self.subTest(document=control["document_id"]):
                doc, pages = source(control)
                units, _ = segment_source(control["family"], doc, pages)
                matching = [unit for unit in units if unit["paragraph_labels"] == [control["paragraph_label"]]]
                self.assertEqual(len(matching), 1)
                unit = matching[0]
                self.assertEqual(unit["role"], "paragraph")
                self.assertEqual(sorted({span["page"] for span in unit["spans"]}), control["pages"])
                self.assertEqual(sha(unit["text"].encode()), control["text_sha256"])
                self.assertIn("\n", unit["text"])

    def test_unseen_amendment_replacement_sheet_is_reference_material(self):
        control = json.loads(CONTROLS.read_bytes())["amendment_control"]
        doc, pages = source(control)
        literal = pages[control["page"] - 1]["text"].encode()[control["start_utf8"]:control["end_utf8"]]
        self.assertEqual(sha(literal), control["literal_sha256"])
        units, _ = segment_source(control["family"], doc, pages)
        containing = [unit for unit in units if any(span["page"] == control["page"]
                      and span["start_utf8"] <= control["start_utf8"]
                      and span["end_utf8"] >= control["end_utf8"] for span in unit["spans"])]
        self.assertEqual(len(containing), 1)
        self.assertEqual(containing[0]["role"], control["expected_role"])
        self.assertEqual(containing[0]["paragraph_labels"], [])


if __name__ == "__main__":
    unittest.main()
