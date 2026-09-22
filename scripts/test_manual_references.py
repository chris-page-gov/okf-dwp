"""Generic controls for source-observed references; no legal dependency claims."""
import unittest

from manual_references import paragraph_references


class ManualReferenceControls(unittest.TestCase):
    def refs(self, text, family="dmg"):
        refs = paragraph_references(text, family)
        for ref in refs:
            self.assertEqual(text.encode()[ref["start_utf8"]:ref["end_utf8"]].decode(), ref["literal"])
            self.assertEqual(ref["legal_dependency"], "not-established")
            self.assertEqual(ref["relationship_role"], "source-reference")
        return refs

    def test_both_memo_word_orders_and_date_separators(self):
        refs = self.refs("[See DMG memo 12/23] [See DMG memorandum 12-25] (Memo ADM 09-25).")
        self.assertEqual([(r["manual"], r["target_kind"], r["target_label"]) for r in refs],
                         [("dmg", "memo", "12/23"), ("dmg", "memo", "12-25"), ("adm", "memo", "09-25")])

    def test_reverse_form_mixed_manual_memos_keeps_each_scope(self):
        refs = self.refs("77140 (See ADM memo 05-24) (see DMG memo 04-24)")
        self.assertEqual([(r["manual"], r["target_label"]) for r in refs], [("adm", "05-24"), ("dmg", "04-24")])

    def test_range_is_one_unexpanded_observation_not_its_first_member(self):
        refs = self.refs("see DMG 60035 - 60042")
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]["target_kind"], "paragraph-range")
        self.assertEqual((refs[0]["lower_label"], refs[0]["upper_label"]), ("60035", "60042"))
        self.assertEqual(refs[0]["range_status"], "literal-unexpanded")

    def test_range_dashes_to_and_leading_zeroes(self):
        for separator in ("–", "—", "to"):
            with self.subTest(separator=separator):
                ref = self.refs("see DMG 077001 " + separator + " 077014")[0]
                self.assertEqual(ref["target_label"], "077001–077014")

    def test_descending_or_mixed_prefix_ranges_do_not_become_members(self):
        for text in ("ADM P4099–P4001", "ADM P4001–Q4002"):
            ref = self.refs(text, "adm")[0]
            self.assertEqual(ref["target_kind"], "paragraph-range")
            self.assertEqual(ref["range_status"], "unresolved-range-scope")

    def test_chapter_part_is_not_downgraded_to_whole_chapter(self):
        ref = self.refs("see DMG Chapter 07 Part 2")[0]
        self.assertEqual(ref["target_kind"], "chapter-part")
        self.assertEqual((ref["chapter_label"], ref["part_label"]), ("07", "2"))
        self.assertEqual(ref["literal"], "DMG Chapter 07 Part 2")

    def test_abbreviated_ranges_remain_unresolved_with_complete_literal(self):
        for text in ("ADM P4001–04", "DMG 60035-42"):
            ref = self.refs(text)[0]
            self.assertEqual(ref["target_kind"], "unresolved-reference")
            self.assertEqual(ref["literal"], text)
            self.assertEqual(ref["reference_scope_status"], "abbreviated-range-not-expanded")

    def test_unsupported_and_multiple_parts_are_not_whole_chapter_targets(self):
        for text in ("DMG Chapter 7 Part VI", "DMG Chapter 7 Part unknown", "DMG Chapter 7 Part 2 and Part 3", "DMG Chapter 7 Part 2–3", "DMG Chapter 7 Parts 2 and 3", "DMG Chapter 7 Part 2/3", "DMG Chapter 7 Part II/III"):
            with self.subTest(text=text):
                ref = self.refs(text)[0]
                self.assertEqual(ref["target_kind"], "unresolved-reference")
                self.assertEqual(ref["literal"], text)
                self.assertEqual(ref["reference_scope_status"], "multiple-or-unsupported-part-qualifier")

    def test_slash_composite_does_not_silently_target_its_first_paragraph(self):
        text = "ADM P4001/P4002"
        ref = self.refs(text)[0]
        self.assertEqual(ref["literal"], text)
        self.assertEqual(ref["target_kind"], "unresolved-reference")
        self.assertEqual(ref["reference_scope_status"], "unsupported-slash-reference")

    def test_bare_financial_at_is_not_a_graph_target(self):
        ref = self.refs("The calculation starts at 10000.")[0]
        self.assertEqual(ref["target_kind"], "unresolved-reference")
        self.assertEqual(ref["reference_scope_status"], "at-without-guidance-cue")
        for text in ("guidance at 60025", "defined at 60025", "described at 60025", "set out at 60025", "at DMG 60025"):
            self.assertEqual(self.refs(text)[0]["target_kind"], "paragraph")

    def test_comma_and_list_retains_only_unambiguous_scope(self):
        refs = self.refs("DMG 77035, 77140 and 77016; unrelated 60025.")
        self.assertEqual([r["target_label"] for r in refs], ["77035", "77140", "77016"])
        self.assertTrue(all(r["manual"] == "dmg" for r in refs))
        self.assertEqual(refs[1]["scope_basis"], "preceding-explicit-reference-list")

    def test_list_manual_change_starts_a_new_reference_scope(self):
        refs = self.refs("See ADM A1002 and DMG 60025, 60033.", "adm")
        self.assertEqual([(r["manual"], r["target_label"]) for r in refs],
                         [("adm", "A1002"), ("dmg", "60025"), ("dmg", "60033")])

    def test_wrapped_explicit_list_keeps_scope_but_blank_line_stops_it(self):
        refs = self.refs("DMG 60025,\n60033 and\n60044")
        self.assertEqual([r["target_label"] for r in refs], ["60025", "60033", "60044"])
        self.assertEqual([r["target_label"] for r in self.refs("DMG 60025,\n\n60033")], ["60025"])

    def test_range_inside_list_preserves_range_not_expansion(self):
        refs = self.refs("ADM P4001, P4002–P4004 and P4005", "adm")
        self.assertEqual([r["target_kind"] for r in refs], ["paragraph", "paragraph-range", "paragraph"])
        self.assertEqual([r["target_label"] for r in refs], ["P4001", "P4002–P4004", "P4005"])

    def test_new_sentence_and_incompatible_label_do_not_inherit_manual(self):
        refs = self.refs("DMG 60025 and P4001. 60033 is another number.")
        self.assertEqual([r["target_label"] for r in refs], ["60025"])

    def test_explicit_manual_label_conflict_remains_unresolved(self):
        ref = self.refs("DMG P4001")[0]
        self.assertEqual(ref["target_kind"], "unresolved-reference")
        self.assertEqual(ref["reference_scope_status"], "manual-label-conflict")

    def test_unicode_prefix_keeps_exact_utf8_offsets(self):
        refs = self.refs("Évidence — see ADM C1988 and C1989; DMG Chapter 07 Part 2", "adm")
        self.assertEqual(len(refs), 3)
        self.assertEqual(refs[0]["start_utf8"], len("Évidence — see ".encode()))

    def test_bare_paragraph_and_amount_numbers_are_not_references(self):
        self.assertEqual(self.refs("60025 A rule; £60033 is an amount; paragraph 12 is not a full DMG number."), [])

    def test_existing_citations_and_single_chapter_are_preserved(self):
        refs = self.refs("SPC Act 02, s 1(2); see DMG Chapter 02; see P1013.", "adm")
        self.assertEqual([r["target_kind"] for r in refs], ["legislation", "chapter", "paragraph"])
        self.assertEqual(refs[0]["target_label"], "SPC Act 02, s 1(2)")


if __name__ == "__main__":
    unittest.main()
