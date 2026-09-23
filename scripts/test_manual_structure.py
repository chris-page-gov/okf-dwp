"""Source-agnostic controls for structural proposals and byte accounting."""
import unittest

from manual_structure import discover_structure, paragraph_references, segment_source


def pages(*texts):
    return [{"page": i + 1, "text": text} for i, text in enumerate(texts)]


class ManualStructureControls(unittest.TestCase):
    def test_mini_contents_does_not_overwrite_parent_heading(self):
        source = pages("Scope A1001 - A1099\n\nOther subject A1050 - A1099\n\nA1001 First condition.\n")
        result = discover_structure("adm", {"chapter": "A1"}, source)
        self.assertEqual(result["paragraphs"][0]["heading_path"], ["Scope"])
        self.assertEqual(result["paragraphs"][0]["rejected_range_headings"][0]["title"], "Other subject")

    def test_real_paragraph_survives_same_page_contents(self):
        source = pages("Introduction\nA1001 A source introduction.\n\nSubpages\n • Scope A1002 - A1099\n")
        result = discover_structure("adm", {"chapter": "A1"}, source)
        self.assertEqual([p["label"] for p in result["paragraphs"]], ["A1001"])
        self.assertEqual(result["range_headings"][0]["role"], "contents-entry")

    def test_example_and_footnote_continue_across_pages(self):
        source = pages("A1001 A conditional rule.\nExample\nA person begins", " and finishes.\n1 Act, s 2\nA1002 A different rule.\n")
        units, _ = segment_source("adm", {"chapter": "A1"}, source)
        first = next(u for u in units if u["paragraph_labels"] == ["A1001"])
        self.assertIn("and finishes.", first["text"])
        self.assertIn("1 Act, s 2", first["text"])
        self.assertNotIn("A1002", first["text"])
        self.assertEqual(len(first["spans"]), 2)

    def test_repeated_declared_heading_belongs_to_following_rule(self):
        source = pages("Subpages\n • Second A1002\n\nA1001 First rule.\n\nSecond\n\nA1002 Second rule.\n")
        units, _ = segment_source("adm", {"chapter": "A1"}, source)
        first = next(u for u in units if u["paragraph_labels"] == ["A1001"])
        second = next(u for u in units if u["paragraph_labels"] == ["A1002"])
        self.assertNotIn("Second", first["text"])
        self.assertTrue(second["text"].startswith("Second"))

    def test_reserved_range_is_not_a_rule(self):
        source = pages("A1001 A rule.\nA1002 - A1099\n")
        units, _ = segment_source("adm", {"chapter": "A1"}, source)
        self.assertEqual(units[1]["role"], "reserved")
        self.assertEqual(units[1]["completeness"], "unresolved")

    def test_auxiliary_role_ends_before_appendix_or_next_rule(self):
        source = pages("A1001 A rule.\nA1002 - A1099\nAppendix 1\nOther source material.\n"
                       "The content of the examples in this document is for illustrative purposes only.\n"
                       "Appendix 2\nAdditional material.\nA1100 Another rule.\n")
        units, _ = segment_source("adm", {"chapter": "A1"}, source)
        reserved = next(u for u in units if u["role"] == "reserved")
        notice = next(u for u in units if u["role"] == "document-notice")
        self.assertEqual(reserved["text"], "A1002 - A1099\n")
        self.assertNotIn("Appendix", notice["text"])
        self.assertTrue(any(u["paragraph_labels"] == ["A1100"] for u in units))
        self.assertEqual("".join(u["text"] for u in units), source[0]["text"])

    def test_multiline_heading_and_range(self):
        source = pages("An applicable section\n- a qualification A1001-A1099\n\nDifferent subject A1050-A1099\nA1001 A rule.\n")
        result = discover_structure("adm", {"chapter": "A1"}, source)
        self.assertEqual(result["paragraphs"][0]["heading_path"], ["An applicable section - a qualification"])

    def test_literal_references_do_not_become_legal_dependencies(self):
        result = paragraph_references("See ADM A1002 and DMG Chapter 02; see P1013.", "adm")
        self.assertEqual([(r["manual"], r["target_kind"], r["target_label"]) for r in result],
                         [("adm", "paragraph", "A1002"), ("dmg", "chapter", "02"), ("adm", "paragraph", "P1013")])
        self.assertTrue(all(r["legal_dependency"] == "not-established" for r in result))

    def test_empty_and_unicode_source_conserved(self):
        source = pages("", "\n", "A1001 A claimant’s source — with α.\n")
        units, structure = segment_source("adm", {"chapter": "A1"}, source)
        self.assertEqual(sum(s["end_utf8"] - s["start_utf8"] for u in units for s in u["spans"]),
                         sum(len(p["text"].encode()) for p in source))
        self.assertEqual(structure["source_bytes"], sum(len(p["text"].encode()) for p in source))

    def test_wrong_manual_or_chapter_is_not_a_boundary(self):
        source = pages("77031 Quoted from another manual.\nB1001 Quoted from another chapter.\nA1001 The local rule.\n")
        result = discover_structure("adm", {"chapter": "A1"}, source)
        self.assertEqual([p["label"] for p in result["paragraphs"]], ["A1001"])

    def test_wrapped_reference_range_end_does_not_cut_off_notes(self):
        source = pages("A1001 The rule. See ADM A1002 -\nA1004 for further details.\n"
                       "Note: The original qualification.\n1 Act, s 2\nA1002 - A1009\nA1010 Next rule.\n")
        units, structure = segment_source("adm", {"chapter": "A1"}, source)
        first = next(u for u in units if u["paragraph_labels"] == ["A1001"])
        self.assertIn("Note: The original qualification.", first["text"])
        self.assertIn("1 Act, s 2", first["text"])
        self.assertNotIn("A1004", [label for u in units for label in u["paragraph_labels"]])
        self.assertTrue(any(p["reason"] == "wrapped-reference-range-end-not-paragraph" for p in structure["rejected_number_lines"]))
        self.assertTrue(any(u["paragraph_labels"] == ["A1010"] for u in units))

    def test_hyphen_without_reference_cue_does_not_suppress_paragraph(self):
        source = pages("A1001 A heading-like sentence -\nA1002 A real source paragraph.\n")
        result = discover_structure("adm", {"chapter": "A1"}, source)
        self.assertEqual([p["label"] for p in result["paragraphs"]], ["A1001", "A1002"])

    def test_appendix_heading_ends_chapter_paragraph_but_keeps_its_example(self):
        source = pages("44001 A source rule.\nExample\nAn example continues", " here.\nA p p e n di x 3\n1 A separate appendix.\n")
        units, _ = segment_source("dmg", {"chapter": "44"}, source)
        rule = next(u for u in units if u["paragraph_labels"] == ["44001"])
        self.assertIn("here.", rule["text"])
        self.assertNotIn("Appendix", rule["text"].replace(" ", ""))
        appendix = next(u for u in units if u["role"] == "section")
        self.assertIn("separate appendix", appendix["text"])
        self.assertEqual(appendix["paragraph_labels"], [])

    def test_memo_chapter_reference_is_not_its_main_numbering(self):
        source = pages("Introduction\n1 A memo passage.\nC2130 and C2150 need consideration.\n2 The next memo passage.\n")
        units, structure = segment_source("adm", {"kind": "memo"}, source)
        self.assertEqual(structure["paragraphs"], [])
        self.assertTrue(all(not u["paragraph_labels"] for u in units))
        self.assertTrue(any("C2130" in u["text"] for u in units))


if __name__ == "__main__":
    unittest.main()
