"""Generic boundary controls; source case IDs never enter parser decisions."""
import unittest
from unittest.mock import patch
import passage_boundary_parser as manual


def pages(*texts):
    return [{"page": i + 1, "text": text} for i, text in enumerate(texts)]


class NavigationRegionControls(unittest.TestCase):
    def parse(self, source, kind="historical-amendment", blocks=()):
        with patch.object(manual, "load_alignment", return_value={"status": "test", "blocks": list(blocks)}):
            return manual.segment_source("dmg", {"kind": kind}, source)

    def test_contents_continuation_does_not_complete_an_unfinished_rule(self):
        source = pages("12345 A condition and\n", "Another subject\nOne ........... 12400\nTwo ........... 12410\nThree ........... 12420\n", "12400 The actual rule.\n")
        units, _ = self.parse(source)
        rule = next(u for u in units if u["paragraph_labels"] == ["12345"])
        self.assertEqual(rule["text"], source[0]["text"])
        self.assertEqual(rule["completeness"], "unresolved")
        self.assertTrue(any(u["role"] == "contents" for u in units))
        self.assertTrue(any(u["paragraph_labels"] == ["12400"] for u in units))

    def test_cover_change_summary_is_not_a_rule(self):
        source = pages("Volume 9\nAmendment 22\nThis letter provides details on Amendment 22.\n12345 added a provision and renumbered.\n", "12340 Actual rule text.\n")
        units, _ = self.parse(source)
        self.assertEqual([u["paragraph_labels"] for u in units if u["paragraph_labels"]], [["12340"]])
        self.assertEqual(units[0]["role"], "document-notice")

    def test_replacement_table_is_not_a_paragraph_or_heading(self):
        source = pages("Remove                 Insert\n12345 – 12349 (2 pages)  12345 – 12349 (3 pages)\n", "12345 Actual rule.\n")
        units, _ = self.parse(source)
        self.assertEqual(units[0]["role"], "reference-table")
        self.assertEqual(units[-1]["paragraph_labels"], ["12345"])

    def test_reference_table_does_not_absorb_following_rule(self):
        source = pages("Abbreviations\nABC      A source abbreviation\n", "12345 A rule.\n")
        units, _ = self.parse(source)
        self.assertEqual(units[0]["role"], "reference-table")
        self.assertEqual(units[-1]["paragraph_labels"], ["12345"])

    def test_reciprocal_overlap_matrix_is_reference_material(self):
        source = pages("12345 The listed countries are\n1. Switzerland\n2. Turkey\n",
                       "The table below summarises the effects of overlap under Reciprocal Agreements\n"
                       "for RP, WB, IBST, IBLT and MB.\nRP WB IBST IBLT MB ESA (C)\n"
                       "Barbados PR PR DMG 074221\n",
                       "12346 A following rule.\n")
        units, _ = self.parse(source)
        self.assertEqual(next(u for u in units if u["paragraph_labels"] == ["12345"])["text"], source[0]["text"])
        self.assertTrue(any(u["role"] == "reference-table" and "Barbados" in u["text"] for u in units))
        self.assertTrue(any(u["paragraph_labels"] == ["12346"] for u in units))

    def test_overlap_phrase_alone_does_not_classify_body_as_table(self):
        source = pages("12345 A rule begins.\n",
                       "The table below summarises the effects of overlap under Reciprocal Agreements\n"
                       "This prose does not have the matrix columns.\n")
        units, _ = self.parse(source)
        self.assertFalse(any(u["role"] == "reference-table" for u in units))

    def test_tagged_document_heading_cannot_pull_across_prose(self):
        text = "Volume 9\nAn administrative paragraph.\n12345 A rule.\n"
        block = {"role": "H2", "text": "Volume 9", "start": 0, "end": 8, "page": 1, "alignment": "test"}
        units, _ = self.parse(pages(text), blocks=[block])
        rule = next(u for u in units if u["paragraph_labels"] == ["12345"])
        self.assertEqual(rule["text"], "12345 A rule.\n")

    def test_real_local_heading_remains_attached(self):
        text = "Real heading\n\n1\n12345 A rule.\n"
        block = {"role": "H2", "text": "Real heading", "start": 0, "end": 12, "page": 1, "alignment": "test"}
        units, _ = self.parse(pages(text), blocks=[block])
        self.assertEqual(units[0]["text"], text)

    def test_bare_appendix_ends_rule_without_promoting_local_numbers(self):
        units, _ = self.parse(pages("12345 A rule and qualification.\nAPPENDIX\n1. Local appendix text.\n"))
        self.assertNotIn("APPENDIX", units[0]["text"])
        self.assertEqual(units[1]["role"], "section")
        self.assertEqual(units[1]["paragraph_labels"], [])

    def test_substantive_running_appendix_header_does_not_split_continuation(self):
        source = pages("12345 A condition applies where\n1. the first test is met and\n",
                       "Appendix\n2. the second test is met.\n")
        units, _ = self.parse(source, kind="chapter")
        rule = next(u for u in units if u["paragraph_labels"] == ["12345"])
        self.assertIn("2. the second test is met.", rule["text"])
        self.assertFalse(any(u["role"] == "section" for u in units))

    def test_cross_page_example_and_single_dotted_field_are_not_contents(self):
        units, _ = self.parse(pages("12345 A rule.\nExample\nA person fills in a field ........... 12345\n", "and the example continues.\n12346 A different rule.\n"))
        first = next(u for u in units if u["paragraph_labels"] == ["12345"])
        self.assertIn("and the example continues.", first["text"])
        self.assertFalse(any(u["role"] == "contents" for u in units))

    def test_remove_words_and_amendment_footer_do_not_classify_body(self):
        source = pages("12345 Remove an amount where these conditions apply.\nVol 9 Amendment 22 June 2017\n")
        units, _ = self.parse(source)
        self.assertEqual(units[0]["role"], "paragraph")
        self.assertEqual(units[0]["text"], source[0]["text"])

    def test_same_page_contents_preserves_real_body(self):
        source = pages("Contents\nOne ........... 12345\nTwo ........... 12346\nThree ........... 12347\n12345 The actual body.\n")
        units, _ = self.parse(source)
        self.assertTrue(any(u["role"] == "contents" for u in units))
        self.assertTrue(any(u["paragraph_labels"] == ["12345"] for u in units))

    def test_amendment_role_rule_does_not_apply_to_a_current_chapter_quotation(self):
        source = pages("12344 A rule.\nExample\nVolume 9 Amendment 22\n"
                       "This letter provides details on Amendment 22.\n12345 An actual following paragraph.\n")
        units, _ = self.parse(source, kind="chapter")
        self.assertFalse(any(u["role"] == "document-notice" for u in units))
        self.assertTrue(any(u["paragraph_labels"] == ["12345"] for u in units))


if __name__ == "__main__":
    unittest.main()
