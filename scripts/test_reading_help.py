"""Regression tests for the bounded, occurrence-specific Chapter 60 aid."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import build_reading_help as aid


class ReadingHelpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.authored = json.loads((aid.ROOT / aid.AUTHORING).read_text())

    def build_with(self, change):
        authored = copy.deepcopy(self.authored)
        change(authored)
        original = aid.read_confined

        def supplied(path, expected_sha=None):
            if path == aid.AUTHORING:
                return aid.canonical(authored)
            return original(path, expected_sha)

        with patch.object(aid, "read_confined", side_effect=supplied):
            return aid.build()

    def test_pilot_has_four_exact_slices_and_keeps_cross_context_terms_out(self):
        manifest = aid.build()
        self.assertEqual([p["id"] for p in manifest["passages"]], ["dmg-60025", "dmg-60033"])
        self.assertEqual([s["page"] for p in manifest["passages"] for s in p["spans"]], [3, 4, 4, 5])
        self.assertEqual({x["proposal_id"] for x in manifest["review_overlay"]},
                         {"pilot-ch60-v083-01", "pilot-ch60-v143-01", "pilot-ch60-v108-01"})
        self.assertFalse(any("living with" in x["literal"] or "qualifying young person" in x["literal"]
                             for x in manifest["occurrences"]))
        self.assertEqual({card["id"] for card in manifest["cards"] if card["kind"] == "expansion"},
                         {"fte-expansion", "gb-expansion", "wdisp-expansion"})
        self.assertEqual({card["target"]["status"] for card in manifest["cards"]
                          if card["kind"] == "unresolved_reference"}, {"unresolved"})

    def test_condition_and_citation_marker_do_not_share_a_span(self):
        manifest = aid.build()
        by_id = {o["id"]: o for o in manifest["occurrences"]}
        for number in (5, 6):
            condition = by_id[f"60025-condition-{number}-number"]
            marker = by_id[f"60025-{'fte' if number == 5 else 'gb'}-marker-{number}"]
            self.assertLess(condition["page_end_utf8"], marker["page_start_utf8"])
            self.assertEqual(condition["role"], "condition_number")
            self.assertEqual(marker["role"], "source_marker")
        self.assertEqual(by_id["60025-note-2-number"]["role"], "note_number")

    def test_wrong_context_fails_closed(self):
        cases = [
            ("CA in citation rather than benefit prose", "60025-gb", "CA"),
            ("AP from another manual", "60025-fte", "AP"),
            ("living with in the wrong passage", "60025-prescribed", "living with"),
            ("prescribed from WDisP attached to residence", "60033-prescribed", "prescribed in GB"),
        ]
        for label, identifier, wrong_context in cases:
            with self.subTest(label=label), self.assertRaises(ValueError):
                self.build_with(lambda a: next(o for o in a["occurrences"] if o["id"] == identifier)
                                .update(context=wrong_context))

    def test_excluded_corrections_keep_exact_source_support(self):
        manifest = aid.build()
        by_proposal = {r["proposal_id"]: r for r in manifest["review_overlay"]}
        note = by_proposal["pilot-ch60-v108-01"]["source_support"][0]
        self.assertEqual(note["page"], 23)
        self.assertIn("See DMG Chapter 16", note["quote"])
        self.assertEqual(by_proposal["pilot-ch60-v083-01"]["disposition"], "excluded-from-live-pilot")
        self.assertEqual({r["page"] for r in by_proposal["pilot-ch60-v083-01"]["source_support"]}, {19, 23})
        with self.assertRaisesRegex(ValueError, "source anchor"):
            self.build_with(lambda a: next(r for r in a["review_overlay"]
                                           if r["proposal_id"] == "pilot-ch60-v108-01")
                            ["source_support"][0].update(quote="Note 2: unsupported Chapter 16 wording"))

    def test_all_body_markers_have_separate_local_reference_cards(self):
        manifest = aid.build()
        occurrences = {o["id"]: o for o in manifest["occurrences"]}
        linked = {oid for card in manifest["cards"] for oid in card["occurrence_ids"]}
        for paragraph, count in (("60025", 7), ("60033", 13)):
            for number in range(1, count + 1):
                matches = [o for o in occurrences.values() if o["passage_id"] == f"dmg-{paragraph}"
                           and o["role"] == "source_marker" and o["literal"] == str(number)]
                self.assertEqual(len(matches), 1, (paragraph, number))
                self.assertIn(matches[0]["id"], linked)
        self.assertEqual(occurrences["60033-extra-2"]["role"], "unresolved_reference_marker")

    def test_valid_prescribed_occurrences_cannot_be_swapped(self):
        def swapped(a):
            cards = {c["id"]: c for c in a["cards"]}
            first, second = cards["prescribed-60025"], cards["prescribed-60033"]
            first["occurrence_ids"], second["occurrence_ids"] = second["occurrence_ids"], first["occurrence_ids"]
            first["source_support"], second["source_support"] = second["source_support"], first["source_support"]
        with self.assertRaisesRegex(ValueError, "Wrong reviewed occurrence binding"):
            self.build_with(swapped)

    def test_local_support_must_cover_the_selected_occurrence(self):
        with self.assertRaisesRegex(ValueError, "Card lacks support"):
            self.build_with(lambda a: next(c for c in a["cards"] if c["id"] == "prescribed-60025")
                            .update(source_support=[{"source_id": "dmg-vol10-ch60", "page": 5,
                                                     "quote": "Note: The meaning of WDisP is prescribed13."}]))

    def test_overlaps_order_and_review_status_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "Overlapping occurrences"):
            self.build_with(lambda a: a["occurrences"].append(
                {"id": "duplicate-gb", "passage_id": "dmg-60025", "page": 3,
                 "context": "presence in GB6 (see DMG", "literal": "GB", "role": "abbreviation"}))
        with self.assertRaisesRegex(ValueError, "unordered passage"):
            self.build_with(lambda a: a["passages"][0]["spans"].reverse())
        with self.assertRaisesRegex(ValueError, "authority or review status"):
            self.build_with(lambda a: a["cards"][0].update(review_status="human-reviewed"))

    def test_real_out_of_scope_contexts_are_not_imported(self):
        chapter = json.loads(aid.read_confined("source/full-dmg-2026-09-15/pages/dmg-vol10-ch60.json"))
        pages = {p["page"]: p["text"] for p in chapter["pages"]}
        self.assertIn("CA SSWP", pages[13])  # Case citation, not benefit prose.
        self.assertIn("living with", pages[19])
        self.assertIn("living with", pages[23])
        self.assertIn("60083", pages[17])
        self.assertIn("60083", pages[19])  # Duplicate body label in different sections.
        dmg = json.loads(aid.read_confined("source/full-dmg-2026-09-15/pages/dmg-abbreviations-0db6c476b0.json"))
        adm = json.loads(aid.read_confined("source/adm-2026-09-19/pages/adm-list-of-abbreviations.json"))
        self.assertIn("AP            Additional Pension", dmg["pages"][0]["text"])
        self.assertIn("AP                 Assessment period", adm["pages"][0]["text"])
        with self.assertRaisesRegex(ValueError, "outside selected passage pages"):
            self.build_with(lambda a: a["occurrences"].append(
                {"id": "case-ca-from-page-13", "passage_id": "dmg-60025", "page": 13,
                 "context": "CA SSWP", "literal": "CA", "role": "abbreviation"}))
        with self.assertRaisesRegex(ValueError, "outside selected passage pages"):
            self.build_with(lambda a: a["occurrences"].append(
                {"id": "living-with-page-19", "passage_id": "dmg-60033", "page": 19,
                 "context": "living with", "literal": "living with", "role": "word"}))
        with self.assertRaisesRegex(ValueError, "Unknown passage source"):
            self.build_with(lambda a: a["passages"].append(
                {"id": "adm-ap", "label": "ADM AP", "source_id": "adm-list-of-abbreviations",
                 "spans": [{"page": 1, "start_anchor": "AP", "end_anchor": None}]}))

    def test_duplicate_passage_identity_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Duplicate passage"):
            self.build_with(lambda a: a["passages"].append(copy.deepcopy(a["passages"][0])))

    def test_changed_source_hash_and_unresolved_target_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "Changed input"):
            self.build_with(lambda a: a["sources"][0].update(pages_sha256="0" * 64))
        with self.assertRaisesRegex(ValueError, "Unresolved target presented as link"):
            self.build_with(lambda a: next(c for c in a["cards"] if c["id"] == "60033-extra-2")
                            ["target"].update(id="dmg-60033"))


if __name__ == "__main__":
    unittest.main()
