"""Bounded source controls, including the two frozen Chapter 84 defects."""
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import unittest

from capital_pilot_source import parse_capital_table, split_units


ROOT = Path(__file__).resolve().parents[1]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def span(pages, number, low=0, high=None):
    raw = next(page for page in pages if page["page"] == number)["text"].encode()
    high = len(raw) if high is None else high
    return {"page": number, "start_utf8": low, "end_utf8": high,
            "literal_sha256": sha(raw[low:high])}


def part(key, role, spans, labels=()):
    return {"key": key, "role": role, "label": key.replace("-", " "),
            "paragraph_labels": list(labels), "spans": spans}


def repair(original, parts):
    return {"original_id": original["id"], "original_text_sha256": original["text_sha256"],
            "original_spans": deepcopy(original["spans"]), "parts": parts}


class CapitalPilotSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = json.loads((ROOT / "source/pages/dmg-vol14-ch84.json").read_text())["pages"]
        cls.catalogue = json.loads(gzip.decompress(
            (ROOT / "structured-units/documents/dmg/dmg-vol14-ch84.json.gz").read_bytes()))
        cls.originals = [next(unit for unit in cls.catalogue["units"] if unit["paragraph_labels"] == [label])
                         for label in ("84356", "84699")]
        cls.table = next(unit for unit in cls.catalogue["units"] if unit["kind"] == "table")

    def proposals(self):
        first, second = deepcopy(self.originals)
        first_body = span(self.pages, 36, first["spans"][0]["start_utf8"], 1429)
        reserved_start = self.pages[93]["text"].encode().index(b"84700")
        return [repair(first, [
            part("repaired-period", "paragraph", [first_body], ["84356"]),
            part("indefinite-contents-first", "contents", [span(self.pages, 36, 1429), first["spans"][1]]),
            part("indefinite-contents-last", "contents", [first["spans"][2]]),
        ]), repair(second, [
            part("repaired-common-owner", "paragraph", [second["spans"][0], span(self.pages, 94, 0, reserved_start)], ["84699"]),
            part("standalone-reserved", "reserved", [span(self.pages, 94, reserved_start)], ["84700"]),
            part("valuation-contents", "contents", [second["spans"][2]]),
        ])]

    def test_frozen_repairs_conserve_bytes_and_separate_roles(self):
        originals, proposals = deepcopy(self.originals), self.proposals()
        before = deepcopy((originals, self.pages, proposals))
        result, receipt = split_units(originals, self.pages, proposals)
        self.assertEqual((originals, self.pages, proposals), before)
        self.assertEqual(len(result), 6)
        self.assertEqual(result[0]["spans"][-1]["end_utf8"], 1429)
        self.assertNotIn("Capital disregarded indefinitely", result[0]["text"])
        self.assertIn("1 SPC Regs, Sch V", result[0]["text"])
        self.assertIn("Example 1", result[3]["text"])
        self.assertIn("Example 2", result[3]["text"])
        self.assertIn("share of the property into account.", result[3]["text"])
        self.assertNotIn("84700", result[3]["text"])
        self.assertEqual(result[4]["text"].strip(), "84700")
        self.assertEqual(result[4]["role"], "reserved")
        self.assertEqual(result[5]["role"], "contents")
        self.assertNotIn("id", result[0])
        self.assertNotIn("record_sha256", result[0])
        self.assertEqual(receipt["source_bytes_before"], receipt["source_bytes_after"])
        self.assertEqual([row["original_id"] for row in receipt["repairs"]], [unit["id"] for unit in originals])
        for row in receipt["repairs"]:
            self.assertEqual(row["unassigned_bytes"], 0)
            self.assertEqual(row["overlapping_bytes"], 0)
            self.assertEqual(row["source_bytes_before"], sum(p["source_bytes"] for p in row["parts"]))
        for unit in result:
            raw = b"\n".join(self.pages[s["page"] - 1]["text"].encode()[s["start_utf8"]:s["end_utf8"]]
                              for s in unit["spans"])
            self.assertEqual(unit["text_sha256"], sha(raw))

    def test_full_chapter_leaves_other_units_unchanged_and_repeats_deterministically(self):
        first = split_units(self.catalogue["units"], self.pages, self.proposals())
        second = split_units(self.catalogue["units"], self.pages, self.proposals())
        self.assertEqual(first, second)
        repaired_ids = {unit["id"] for unit in self.originals}
        self.assertEqual([unit for unit in first[0] if "id" in unit],
                         [unit for unit in self.catalogue["units"] if unit["id"] not in repaired_ids])

    def test_substantive_source_tampering_is_rejected(self):
        pages = deepcopy(self.pages)
        pages[35]["text"] = pages[35]["text"].replace("indefinite period", "definitive period")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            split_units(self.originals, pages, self.proposals())

    def test_original_binding_and_cached_text_tampering_are_rejected(self):
        proposals = self.proposals()
        proposals[0]["original_text_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "binding mismatch"):
            split_units(self.originals, self.pages, proposals)
        originals = deepcopy(self.originals)
        originals[0]["text"] = "Altered cached material"
        with self.assertRaisesRegex(ValueError, "text differs"):
            split_units(originals, self.pages, self.proposals())

    def test_gap_overlap_and_reordered_parts_are_rejected_even_with_valid_hashes(self):
        for alteration in ("gap", "overlap", "reorder"):
            proposals = self.proposals()
            parts = proposals[0]["parts"]
            if alteration == "reorder":
                parts[0], parts[1] = parts[1], parts[0]
            else:
                parts[0]["spans"][0] = span(self.pages, 36, 998, 1428 if alteration == "gap" else 1430)
            with self.subTest(alteration=alteration), self.assertRaisesRegex(ValueError, "conserve"):
                split_units(self.originals, self.pages, proposals)

    def test_out_of_range_boolean_and_utf8_cut_are_rejected(self):
        for alteration in ("range", "boolean", "utf8"):
            proposals = self.proposals()
            target = proposals[1]["parts"][0]["spans"][0]
            if alteration == "range":
                target["end_utf8"] = 999999
            elif alteration == "boolean":
                target["start_utf8"] = True
            else:
                raw = self.pages[92]["text"].encode()
                target["end_utf8"] = raw.index("’".encode(), target["start_utf8"]) + 1
                target["literal_sha256"] = sha(raw[target["start_utf8"]:target["end_utf8"]])
            with self.subTest(alteration=alteration), self.assertRaises(ValueError):
                split_units(self.originals, self.pages, proposals)

    def test_stale_key_and_substantive_reserved_claim_are_rejected(self):
        proposals = self.proposals()
        proposals[0]["parts"][0]["key"] = self.originals[0]["key"]
        with self.assertRaisesRegex(ValueError, "reuses"):
            split_units(self.originals, self.pages, proposals)
        proposals = self.proposals()
        proposals[1]["parts"][0]["role"] = "reserved"
        with self.assertRaisesRegex(ValueError, "Reserved standalone"):
            split_units(self.originals, self.pages, proposals)

    def test_synthetic_labels_and_offsets_do_not_depend_on_frozen_paragraphs(self):
        pages = [{"page": 1, "text": "Heading\n12345 Café.\n12346\nContents\n"}]
        raw = pages[0]["text"].encode()
        original = {"id": "synthetic:old", "key": "old", "spans": [span(pages, 1)],
                    "text": raw.decode(), "text_sha256": sha(raw), "text_bytes": len(raw)}
        reserved = raw.index(b"12346")
        contents = raw.index(b"Contents")
        specification = repair(original, [
            part("synthetic-body", "paragraph", [span(pages, 1, 0, reserved)], ["12345"]),
            part("synthetic-reserved", "reserved", [span(pages, 1, reserved, contents)], ["12346"]),
            part("synthetic-contents", "contents", [span(pages, 1, contents)]),
        ])
        result, receipt = split_units([original], pages, [specification])
        self.assertIn("Café", result[0]["text"])
        self.assertEqual(result[1]["text"], "12346\n")
        self.assertEqual(receipt["source_bytes_after"], len(raw))

    def test_table_numeric_cells_and_separate_continuation_have_exact_locators(self):
        table = parse_capital_table(self.pages, self.table["spans"])
        self.assertEqual(len(table["rows"]), 21)
        self.assertEqual(table["rows"][0]["capital_from"], "0.00")
        self.assertEqual(table["rows"][0]["capital_to"], "10000.00")
        self.assertEqual(table["rows"][0]["deemed_weekly_income"], "0.00")
        self.assertEqual(table["rows"][0]["source_cells"]["capital_from"]["literal"], "NIL")
        self.assertEqual(table["rows"][-1]["capital_from"], "19500.01")
        self.assertEqual(table["rows"][-1]["capital_to"], "20000.00")
        self.assertEqual(table["rows"][-1]["deemed_weekly_income"], "20.00")
        self.assertEqual(table["continuation"]["generated_rows"], 0)
        self.assertEqual(table["continuation"]["literal_cells"], ["and so on"] * 3)
        self.assertEqual(table["column_semantics"][0]["assertion_status"], "model-derived")
        self.assertFalse(table["individual_award_calculated"])
        accounting = table["accounting"]
        self.assertEqual(accounting["source_bytes"], sum(accounting[field] for field in (
            "header_bytes", "row_bytes", "continuation_bytes", "blank_bytes")))
        refs = table["headers"] + table["blank_lines"] + [table["continuation"]["source"]]
        for row in table["rows"]:
            self.assertEqual(row["currency"], "GBP")
            refs.extend([row["source"], *row["source_cells"].values()])
        for ref in refs:
            literal = self.pages[ref["page"] - 1]["text"].encode()[ref["start_utf8"]:ref["end_utf8"]]
            self.assertEqual(ref["literal"], literal.decode())
            self.assertEqual(ref["literal_sha256"], sha(literal))

    def test_table_source_hash_tampering_is_rejected(self):
        pages = deepcopy(self.pages)
        pages[130]["text"] = pages[130]["text"].replace("20,000.00", "29,000.00")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            parse_capital_table(pages, self.table["spans"])

    def test_unrecognised_header_or_row_is_rejected_with_updated_span_hash(self):
        for old, new in (("Total capital", "Total income"), ("NIL         10,000.00 NIL", "NIL         unknown NIL")):
            pages, spans = deepcopy(self.pages), deepcopy(self.table["spans"])
            pages[129]["text"] = pages[129]["text"].replace(old, new)
            spans[0] = span(pages, 130)
            with self.subTest(change=new), self.assertRaises(ValueError):
                parse_capital_table(pages, spans)

    def test_partial_row_and_incomplete_table_are_rejected(self):
        spans = deepcopy(self.table["spans"])
        spans[1] = span(self.pages, 131, 1, spans[1]["end_utf8"])
        with self.assertRaisesRegex(ValueError, "inside a line"):
            parse_capital_table(self.pages, spans)
        with self.assertRaisesRegex(ValueError, "Incomplete capital table"):
            parse_capital_table(self.pages, [self.table["spans"][0]])


if __name__ == "__main__":
    unittest.main()
