"""Broader discovery controls: source fidelity, preservation and fail-closed inputs."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from build_context_discovery import Inputs, MAX_INDEX_BYTES, OUTPUT, PART_OF, ROOT, project, read_semantics
from build_bundle import digest


class ContextDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_bytes = (ROOT / "full-dmg/context/assembly-index.json").read_bytes()
        cls.outputs = project()
        cls.index = json.loads(cls.outputs["assembly-index.json"])
        cls.receipt = json.loads(cls.outputs["manifest.json"])

    def test_deterministic_build_and_old_index_preserved(self):
        self.assertEqual(project(), self.outputs)
        self.assertEqual((ROOT / "full-dmg/context/assembly-index.json").read_bytes(), self.old_bytes)
        self.assertEqual(self.receipt["preserved_custody_index"]["sha256"], digest(self.old_bytes))
        for name, raw in self.outputs.items():
            self.assertEqual((ROOT / OUTPUT / name).read_bytes(), raw)

    def test_all_concepts_and_cited_pages_projected_without_requirements(self):
        _, nodes, assertions, _ = read_semantics(Inputs(ROOT))
        projected = {row["id"]: row for row in self.index["records"]}
        concepts = {iri for iri, row in nodes.items() if row.get("type") == "Concept"}
        self.assertEqual(concepts, {row["id"] for row in self.index["records"] if row["kind"] == "concept"})
        for edge in assertions:
            if edge["source"] in concepts:
                self.assertIn(edge["target"], projected)
        self.assertEqual(self.index["requirements"], [])
        self.assertLessEqual(len(self.outputs["assembly-index.json"]), MAX_INDEX_BYTES)

    def test_original_assertions_remain_exact_and_unsupported_are_not_relabelled(self):
        _, _, assertions, _ = read_semantics(Inputs(ROOT))
        originals = {row["@id"]: row for row in assertions}
        for row in self.index["assertions"]:
            source = originals[row["id"]]
            self.assertEqual(row["id"], row["original_assertion_id"])
            for field in ("source", "target", "predicate", "label", "assertion_status", "authority"):
                self.assertEqual(row[field], source[field])
            self.assertNotEqual(row["predicate"], PART_OF)
        self.assertEqual(sum(self.receipt["unsupported_predicates_retained"].values()), 4)

    def test_exact_whole_pages_and_existing_aliases_only(self):
        old = {row["id"]: row for row in json.loads(self.old_bytes)["records"]}
        for row in self.index["records"]:
            if row["id"] in old:
                self.assertEqual(row, old[row["id"]])
            else:
                self.assertNotIn("aliases", row)
            if row["kind"] == "evidence":
                self.assertEqual(row["assertion_status"], "normalized")
                self.assertEqual(row["authority"]["class"], "derived")
                for item in row["provenance"]:
                    self.assertIsInstance(item["captured_at"], str)
                    if "literal_sha256" in item:
                        self.assertEqual(item["literal_sha256"], digest(row["text"].encode()))

    def test_every_input_and_output_digest_matches(self):
        self.assertEqual(self.receipt["index"]["sha256"], digest(self.outputs["assembly-index.json"]))
        for item in self.receipt["inputs"]:
            raw = (ROOT / item["path"]).read_bytes()
            self.assertEqual(digest(raw), item["sha256"])
            self.assertEqual(len(raw), item["bytes"])

    def assert_tamper_rejected(self, target):
        original = Path.read_bytes
        target = (ROOT / target).resolve()

        def changed(path):
            raw = original(path)
            return raw + b"tampered" if path.resolve() == target else raw

        with patch.object(Path, "read_bytes", changed):
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                project()

    def test_changed_semantic_shard_rejected(self):
        target = next(row["path"] for row in self.receipt["inputs"] if "/semantic/nodes-" in row["path"])
        self.assert_tamper_rejected(target)

    def test_changed_source_extraction_rejected(self):
        target = next(row["path"] for row in self.receipt["inputs"] if "/pages/" in row["path"])
        self.assert_tamper_rejected(target)

    def test_changed_source_pdf_rejected(self):
        target = next(row["path"] for row in self.receipt["inputs"] if row["path"].endswith(".pdf"))
        self.assert_tamper_rejected(target)

    def test_paths_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as directory:
            reader = Inputs(Path(directory))
            for value in ("../outside", "/absolute"):
                with self.assertRaises(ValueError):
                    reader.path(value)


if __name__ == "__main__":
    unittest.main()
