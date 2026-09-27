#!/usr/bin/env python3
"""Source-led initial reading-help expectations, frozen before evaluation."""
from __future__ import annotations

import gzip
import json
from pathlib import Path
import unittest

from build_logical_units import sha

ROOT = Path(__file__).resolve().parents[1]
CONTROLS = ROOT / "evaluation/reading-help-rollout/meaningful-controls.json"


class MeaningfulControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controls = json.loads(CONTROLS.read_text())
        cls.catalogue = json.loads((ROOT / "reading-help-corpus/manifest.json").read_text())
        cls.documents = {(d["family"], d["document_id"]): d for d in cls.catalogue["documents"]}

    def test_initial_twelve(self):
        cases = self.controls["initial"]
        self.assertEqual(len(cases), 12)
        self.assertEqual(sum(c["family"] == "dmg" for c in cases), 6)
        self.assertEqual(sum(c["family"] == "adm" for c in cases), 6)
        for case in cases:
            with self.subTest(case=case["id"]):
                self.check_case(case)

    def test_fresh_heldout_twenty_four(self):
        heldout = json.loads((ROOT / "evaluation/reading-help-rollout/heldout-controls.json").read_text())
        self.assertEqual(heldout["status"], "frozen-before-heldout-evaluation")
        cases = heldout["cases"]
        self.assertEqual(len(cases), 24)
        self.assertEqual(sum(c["family"] == "dmg" for c in cases), 12)
        self.assertEqual(sum(c["family"] == "adm" for c in cases), 12)
        self.assertTrue({(c["document_id"], c["page"], c["start_utf8"], c["end_utf8"])
                         for c in cases}.isdisjoint(
            {(c["document_id"], c["page"], c["start_utf8"], c["end_utf8"])
             for c in self.controls["initial"]}))
        for case in cases:
            with self.subTest(case=case["id"]):
                self.check_case(case)

    def test_revised_fresh_heldout_twenty_four(self):
        heldout = json.loads((ROOT / "evaluation/reading-help-rollout/heldout-03-controls.json").read_text())
        self.assertEqual(heldout["status"], "frozen-before-third-heldout-evaluation")
        cases = heldout["cases"]
        self.assertEqual(len(cases), 24)
        self.assertEqual(sum(c["family"] == "dmg" for c in cases), 12)
        self.assertEqual(sum(c["family"] == "adm" for c in cases), 12)
        self.assertEqual(len({(c["family"], c["document_id"]) for c in cases}), 24)
        previous = json.loads((ROOT / "evaluation/reading-help-rollout/heldout-controls.json").read_text())["cases"]
        self.assertTrue({(c["document_id"], c["page"], c["start_utf8"], c["end_utf8"])
                         for c in cases}.isdisjoint(
            {(c["document_id"], c["page"], c["start_utf8"], c["end_utf8"])
             for c in self.controls["initial"] + previous}))
        for case in cases:
            with self.subTest(case=case["id"]):
                self.check_case(case)

    def check_case(self, case):
        source_raw = (ROOT / case["extraction_path"]).read_bytes()
        self.assertEqual(sha(source_raw), case["extraction_sha256"])
        extracted = json.loads(source_raw)
        self.assertEqual(extracted["source_sha256"], case["source_pdf_sha256"])
        page = extracted["pages"][case["page"] - 1]["text"].encode()
        literal = page[case["start_utf8"]:case["end_utf8"]]
        self.assertEqual(literal.decode(), case["literal"])
        self.assertEqual(sha(literal), case["literal_sha256"])
        dref = self.documents[(case["family"], case["document_id"])]
        index_raw = (ROOT / dref["path"]).read_bytes()
        self.assertEqual(sha(index_raw), dref["sha256"])
        index = json.loads(index_raw)
        expected = case["expected"]
        if expected["kind"] == "extraction_blocked":
            self.assertIn(case["page"], index["extraction_blocked_pages"])
            return
        passages = {}
        for leaf in index["leaves"]:
            packed = (ROOT / leaf["path"]).read_bytes()
            self.assertEqual(sha(packed), leaf["sha256"])
            decoded = gzip.decompress(packed)
            self.assertEqual(sha(decoded), leaf["decoded_sha256"])
            for row in json.loads(decoded)["passages"]:
                item = passages.setdefault(row["id"], {"parts": {}, "spans": row["source_spans"],
                    "role": row["role"], "occurrences": [], "cards": [], "footers": []})
                item["parts"][row["segment"]["ordinal"]] = row["segment"]["text"]
                item["occurrences"].extend(row["occurrences"])
                item["cards"].extend(row["cards"])
                item["footers"].extend(row["reference_list_segments"])
        covering = [p for p in passages.values() if any(s["page"] == case["page"] and
                    s["start_utf8"] <= case["start_utf8"] and case["end_utf8"] <= s["end_utf8"]
                    for s in p["spans"])]
        self.assertTrue(covering, "No complete source passage covers the chosen span")
        for passage in covering:
            passage["text"] = "".join(passage["parts"][n] for n in sorted(passage["parts"]))
        kind = expected["kind"]
        if kind == "source_retained":
            self.assertTrue(any(case["literal"] in p["text"] for p in covering))
        elif kind == "cross_page":
            self.assertTrue(any(expected["other_literal"] in p["text"] and
                                any(s["page"] == expected["other_page"] for s in p["spans"])
                                for p in covering), "Continuation or qualification lost")
        elif kind == "table_continuation":
            self.assertTrue(any(p["role"] == expected["role"] and
                                case["literal"] in p["text"] and
                                expected["other_literal"] in p["text"] and
                                any(s["page"] == expected["other_page"] for s in p["spans"])
                                for p in covering), "Complete continuing source table was not retained")
        elif kind == "exception_retained":
            self.assertTrue(any(case["literal"] in p["text"] and
                                expected["condition"] in p["text"] and
                                expected["exception"] in p["text"]
                                for p in covering), "Source condition or exception was lost")
        elif kind == "footer_unlinked":
            self.assertTrue(any(f["marker"] == expected["marker"] and
                                f["start_utf8"] <= case["start_utf8"] and
                                case["end_utf8"] <= f["end_utf8"] and
                                f["status"] == "unresolved" and not f["body_occurrence_ids"]
                                for p in covering for f in p["footers"]),
                            "Restarted footer marker was joined or omitted")
        else:
            token = expected.get("token", case["literal"])
            matches = [(o, c, p) for p in covering for o in p["occurrences"] for c in p["cards"]
                       if c["occurrence_id"] == o["id"] and o["page"] == case["page"] and
                       (o["start_utf8"] == case["start_utf8"] if kind == "abbreviation" else
                        case["start_utf8"] <= o["start_utf8"] < o["end_utf8"] <= case["end_utf8"]) and
                       (o["literal"] == token if kind == "abbreviation" else
                        o["literal"] in case["literal"])]
            self.assertTrue(matches, "No exact occurrence/card at frozen source span")
            for occurrence, card, passage in matches:
                self.assertEqual(page[occurrence["start_utf8"]:occurrence["end_utf8"]].decode(),
                                 occurrence["literal"])
            if kind == "abbreviation":
                self.assertTrue(any(c["kind"] == "expansion" and c["status"] == expected["status"] and
                                    expected["source_table_document_id"] in c["scope"]["source_table_document_ids"] and
                                    ("expansion" not in expected or any(r["expansion"] == expected["expansion"]
                                        for r in c["source_table_rows"])) for o, c, p in matches))
            else:
                self.assertTrue(any(c["kind"] == "citation_navigation" and
                                    c["status"] == expected["status"] and
                                    c["target"]["target_kind"] == expected["target_kind"] and
                                    c["target"]["target_label"] == expected["target_label"]
                                    for o, c, p in matches), "Wrong or missing source navigation")
                if expected.get("retain_literal"):
                    self.assertTrue(any(expected["retain_literal"] in p["text"] for o, c, p in matches),
                                    "Qualification lost from reference passage")


if __name__ == "__main__":
    unittest.main()
