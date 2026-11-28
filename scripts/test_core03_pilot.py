"""Check the additive pilot's complete evidence and relationship identity."""
import json
from pathlib import Path
import tempfile
import unittest

from build_bundle import ROOT, digest
from build_core03_pilot import project


class Core03PilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.candidate = project()
        cls.reader = json.loads(cls.candidate["okf-explorer.json"])
        cls.frozen = json.loads((ROOT / "bundle/okf-bundle.json").read_bytes())
        cls.manifest = json.loads(cls.candidate["manifest.json"])

    def test_all_records_preserve_evidence_metadata(self) -> None:
        expected_routes = {f"records/{route}.md" for route in self.frozen["nodes"]}
        self.assertEqual(set(self.reader["nodes"]), expected_routes)
        self.assertEqual(self.reader["okf_version"], "0.3")
        self.assertEqual(self.frozen["okf_version"], "0.2")
        for source_route, frozen in self.frozen["nodes"].items():
            expected = {name: value for name, value in frozen.items() if name != "body"}
            if expected["status"] == "experimental":
                expected.update(status="draft", **{"x-okf-dwp-status": "experimental"})
            actual = self.reader["nodes"][f"records/{source_route}.md"]["frontmatter"]
            self.assertEqual(actual, expected, source_route)
        self.assertEqual(self.manifest["legacy_status_mappings"],
                         ["records/journey/chapter-navigation.md"])

    def test_typed_assertions_and_markdown_navigation_are_complete(self) -> None:
        expected = [
            {**row, "source": f"records/{row['source']}.md", "target": f"records/{row['target']}.md"}
            for row in self.frozen["relationships"]
        ]
        self.assertEqual(self.reader["relationships"][:len(expected)], expected)
        pairs = {(row["source"], row["target"]) for row in self.reader["edges"]}
        mapped = {(path, target) for path, row in self.reader["nodes"].items()
                  for target in row["markdown_links"].values()}
        self.assertEqual(pairs, mapped)
        self.assertEqual(len(pairs), 971)
        relationships = {(row["source"], row["target"]) for row in self.reader["relationships"]}
        self.assertTrue(pairs <= relationships)

    def test_walkthrough_evidence_and_output_manifest(self) -> None:
        packet = json.loads(self.candidate["evidence.json"])
        page = self.reader["nodes"][packet["source_record"]]
        self.assertEqual(packet["source_excerpt"], page["body"])
        self.assertEqual(packet["source_pdf_sha256"], page["source_sha256"])
        self.assertTrue(packet["source_url"].endswith("#page=35"))
        self.assertIn(packet["assertion"], self.reader["relationships"])
        names = set(self.candidate) - {"manifest.json"}
        self.assertEqual({entry["path"] for entry in self.manifest["files"]}, names)
        for entry in self.manifest["files"]:
            data = self.candidate[entry["path"]]
            self.assertEqual((len(data), digest(data)), (entry["bytes"], entry["sha256"]))

    def test_unrecognised_frozen_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bundle").mkdir()
            (root / "bundle/checksums.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Frozen pilot checksum catalogue changed"):
                project(root)


if __name__ == "__main__":
    unittest.main()
