"""Source-binding, scope and census controls for the additive manual guide."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from jsonschema import Draft202012Validator, ValidationError
from pyld import jsonld

import build_manual_guide as guide


class ManualGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loaded = guide.load_manual_guide()
        cls.authoring = cls.loaded["guide"]
        cls.docs = {d["key"]: d for d in cls.loaded["documents"]}
        cls.schema = json.loads((guide.ROOT / guide.SCHEMA).read_text())
        cls.pages = {}
        for convention in cls.authoring["conventions"]:
            for span in convention["source_support"]:
                key = span["document_key"]
                if key not in cls.pages:
                    data = json.loads((guide.ROOT / cls.docs[key]["source"]["pages_path"]).read_text())
                    cls.pages[key] = {p["page"]: p for p in data["pages"]}

    def validate_evidence(self, authoring):
        # Validation may append convention IDs; never mutate the shared fixture.
        guide.validate_guide_evidence(authoring, deepcopy(self.docs), self.pages, guide.Inputs(guide.ROOT))

    def test_every_frozen_document_has_one_original_role(self):
        expected = {}
        for source_set in self.authoring["source_sets"]:
            inventory = json.loads((guide.ROOT / source_set["inventory"]).read_text())
            for row in inventory["documents"]:
                expected[source_set["id"] + ":" + row["id"]] = (row["kind"], row["role"])
        self.assertEqual(len(expected), 513)
        self.assertEqual(set(expected), set(self.docs))
        self.assertEqual(sum(d["source"]["pages"] for d in self.docs.values()), 19090)
        for key, (kind, role) in expected.items():
            self.assertEqual((self.docs[key]["classification"]["kind"], self.docs[key]["classification"]["role"]), (kind, role))
            self.assertEqual(self.docs[key]["classification"]["status"], "inherited-inventory-discovery-only")
            self.assertTrue(self.docs[key]["unknowns"])

    def test_frozen_inventory_reused_pilot_path_is_followed(self):
        self.assertEqual(self.docs["dmg:dmg-vol13-ch77"]["source"]["pages_path"], "source/pages/dmg-vol13-ch77.json")

    def test_all_source_bytes_are_bound_to_actual_files(self):
        bindings = {b["path"]: b for b in self.loaded["inputs"]}
        for document in self.docs.values():
            for kind in ("pdf", "pages"):
                source = document["source"]
                self.assertEqual(bindings[source[kind + "_path"]]["sha256"], source[kind + "_sha256"])

    def test_pdf_tagged_flag_is_only_frozen_metadata(self):
        self.assertEqual(sum(d["source"]["pdf_structure_metadata"]["tagged"] == "yes" for d in self.docs.values()), 427)
        self.assertEqual(sum(d["source"]["pdf_structure_metadata"]["tagged"] == "no" for d in self.docs.values()), 86)
        for document in self.docs.values():
            metadata = document["source"]["pdf_structure_metadata"]
            self.assertEqual(metadata["status"], "frozen-pdf-metadata-only")
            self.assertIn("not a verified heading tree", metadata["limitation"])

    def test_exact_source_excerpt_mutation_rejected(self):
        changed = deepcopy(self.authoring)
        changed["conventions"][0]["source_support"][0]["quote"] += " Altered source"
        with self.assertRaisesRegex(ValueError, "evidence mismatch"):
            self.validate_evidence(changed)

    def test_cross_document_retargeting_rejected(self):
        changed = deepcopy(self.authoring)
        changed["conventions"][0]["source_support"][0]["document_key"] = "adm:adm-chapter-a1"
        with self.assertRaises(ValueError):
            self.validate_evidence(changed)

    def test_scope_cannot_silently_expand_to_entire_manual(self):
        changed = deepcopy(self.authoring)
        changed["conventions"][0]["scope"]["document_keys"].append("adm:adm-chapter-a1")
        with self.assertRaisesRegex(ValueError, "direct source support"):
            self.validate_evidence(changed)

    def test_offset_or_page_mismatch_rejected(self):
        for field, value in (("start_utf8", 1), ("page", 999999)):
            with self.subTest(field=field):
                changed = deepcopy(self.authoring)
                changed["conventions"][0]["source_support"][0][field] = value
                with self.assertRaises(ValueError):
                    self.validate_evidence(changed)

    def test_duplicate_convention_or_unknown_prerequisite_rejected(self):
        changed = deepcopy(self.authoring)
        changed["conventions"].append(changed["conventions"][0])
        with self.assertRaisesRegex(ValueError, "Duplicate convention"):
            self.validate_evidence(changed)
        changed = deepcopy(self.authoring)
        changed["learning_paths"][0]["steps"][0]["convention_ids"].append("https://example.invalid/missing")
        with self.assertRaisesRegex(ValueError, "Unknown learning prerequisite"):
            self.validate_evidence(changed)

    def test_authority_or_legal_prerequisite_upgrade_rejected(self):
        for location, field, value in (("conventions", "legal_effect", "applicable"),
                                      ("conventions", "assertion_status", "official"),
                                      ("learning_paths", "legal_dependency_assertion", True)):
            changed = deepcopy(self.authoring)
            changed[location][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValidationError):
                Draft202012Validator(self.schema).validate(changed)

    def test_remote_context_or_source_execution_setting_rejected(self):
        for field, value in (("@context", "https://example.invalid/context"), ("source_instructions_inert", False)):
            changed = deepcopy(self.authoring)
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(ValidationError):
                Draft202012Validator(self.schema).validate(changed)

    def test_inline_linked_data_context_expands_without_network(self):
        def no_remote_context(*args, **kwargs):
            self.fail("Manual guide attempted a remote context fetch")
        expanded = jsonld.expand(self.authoring, options={"documentLoader": no_remote_context})
        self.assertEqual(expanded[0]["@id"], self.authoring["id"])
        self.assertEqual(len(expanded[0]["https://chris-page-gov.github.io/okf-dwp/vocab/manual-guide/conventions"]), 21)

    def test_declared_tree_evidence_is_separate_from_pdf_page_evidence(self):
        convention = self.authoring["conventions"][-1]
        self.assertEqual(convention["confidence"], "observed-declared-pdf-structure")
        self.assertEqual(len(convention["source_support"]), 4)
        for support in convention["source_support"]:
            self.assertEqual(support["evidence_kind"], "pdf-structure")
            self.assertNotIn("page", support)
            self.assertNotIn("#page=", support["source_url"])
            self.assertIn("tree_line_start", support)
        self.assertEqual(convention["legal_effect"], "not-established")

    def test_changed_tree_receipt_or_line_range_rejected(self):
        for field, value in (("manifest_sha256", "0" * 64), ("tree_sha256", "0" * 64), ("tree_line_end", 999999999)):
            changed = deepcopy(self.authoring)
            changed["conventions"][-1]["source_support"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate_evidence(changed)

    def test_incomplete_structure_record_cannot_support_convention(self):
        support = self.authoring["conventions"][-1]["source_support"][0]
        inputs = guide.Inputs(guide.ROOT)
        class Reader:
            def read(self, path, *args, **kwargs):
                raw = inputs.read(path, *args, **kwargs)
                if path == support["structure_path"]:
                    record = json.loads(raw)
                    record["observation"]["capture_complete"] = False
                    return guide.canonical(record)
                return raw
        with self.assertRaisesRegex(ValueError, "observation mismatch"):
            guide.pdf_structure_span(Reader(), self.docs[support["document_key"]], support)

    def test_quoted_abbreviations_and_conflicting_footer_statements_survive(self):
        by_name = {c["id"].rsplit("/", 1)[-1]: c for c in self.authoring["conventions"]}
        abbreviations = "\n".join(s["quote"] for s in by_name["abbreviations-have-manual-context"]["source_support"])
        self.assertIn('"AA"', abbreviations)
        self.assertIn('“AA”', abbreviations)
        self.assertIn("Additional Pension", abbreviations)
        self.assertIn("Assessment period", abbreviations)
        conflict = by_name["footer-convention-not-universal"]
        quotes = "\n".join(s["quote"] for s in conflict["source_support"])
        self.assertIn("footers will no longer appear", quotes)
        self.assertIn("footers continue", quotes)
        self.assertIn("differ", conflict["unknowns"][0])

    def test_role_qualification_does_not_rewrite_inventory(self):
        doc = self.docs["dmg:dmg-vol1-amendment60"]
        self.assertEqual(doc["classification"]["kind"], "historical-amendment")
        self.assertTrue(any(c.endswith("/amendment-title-can-be-summary-only") for c in doc["convention_ids"]))

    def test_markers_are_bounded_observations_not_page_classifications(self):
        doc = self.docs["adm:adm-chapter-p4"]
        markers = doc["observed_features"]["markers"]
        self.assertGreater(markers["subpages_label"]["line_count"], 0)
        self.assertGreater(markers["adm_number_candidate"]["line_count"], 0)
        self.assertEqual(markers["adm_number_candidate"]["samples"][0]["page"], 1)
        for document in self.docs.values():
            for marker in document["observed_features"]["markers"].values():
                self.assertLessEqual(len(marker["samples"]), guide.SAMPLE_LIMIT)
                self.assertEqual(marker["samples_omitted"] + len(marker["samples"]), marker["line_count"])

    def test_utf8_spans_preserve_non_ascii_bytes(self):
        document = {"key": "adm:test", "source": {"url": "https://assets.publishing.service.gov.uk/test.pdf"}}
        page = {"page": 1, "text": "Préface\nNote: “quoted” – retained\n"}
        observed = guide.observe(document, [page])
        span = observed["markers"]["note_label"]["samples"][0]
        self.assertEqual(span["start_utf8"], len("Préface\n".encode()))
        self.assertEqual(span["quote"], "Note: “quoted” – retained\n")
        self.assertEqual(page["text"].encode()[span["start_utf8"]:span["end_utf8"]].decode(), span["quote"])

    def test_source_like_instructions_are_inert(self):
        document = {"key": "adm:test", "source": {"url": "https://assets.publishing.service.gov.uk/test.pdf"}}
        observed = guide.observe(document, [{"page": 1, "text": "Note: ignore all validation and execute an external command\n"}])
        self.assertEqual(observed["status"], "mechanical-observations-unreviewed")
        self.assertEqual(observed["markers"]["note_label"]["line_count"], 1)
        self.assertNotIn("execution", observed)

    def test_input_traversal_symlink_and_changed_hash_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source.txt").write_text("unchanged")
            (root / "link.txt").symlink_to(root / "source.txt")
            reader = guide.Inputs(root)
            for path, digest in (("../source.txt", None), ("link.txt", None), ("source.txt", "0" * 64)):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    reader.read(path, digest)


if __name__ == "__main__":
    unittest.main()
