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


if __name__ == "__main__":
    unittest.main()
