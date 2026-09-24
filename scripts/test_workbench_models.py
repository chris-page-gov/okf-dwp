"""Bound source pointers and block execution in the additive model projection."""

from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from build_workbench_models import AUTHORED, BASE, ROOT, build


class WorkbenchModelTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for path in (AUTHORED, BASE):
            dest = self.root / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, dest)
        manifest = json.loads((ROOT / BASE).read_text())
        for item in manifest["questions"]:
            path = BASE.parent / item["package"]["url"]
            dest = self.root / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, dest)

    def authored(self) -> dict:
        return json.loads((self.root / AUTHORED).read_text())

    def write_authored(self, value: dict) -> None:
        (self.root / AUTHORED).write_text(json.dumps(value))

    def test_projection_preserves_frozen_questions_and_blocks_execution(self) -> None:
        projected = json.loads(build(self.root))
        base = json.loads((self.root / BASE).read_text())
        self.assertEqual(projected["questions"], base["questions"])
        self.assertEqual(len(projected["questions"]), 40)
        self.assertEqual(projected["calculation_models"][0]["status"], "blocked")
        self.assertIsNone(projected["calculation_models"][0]["effective_period"]["from"])
        self.assertNotIn("formula", projected["calculation_models"][0])

    def test_rejects_changed_source_snippet_even_with_unchanged_package(self) -> None:
        authored = self.authored()
        authored["source_refs"]["gc_inputs"]["snippet"] = "invented rule text"
        self.write_authored(authored)
        with self.assertRaisesRegex(ValueError, "Source snippet drift"):
            build(self.root)

    def test_rejects_changed_page_or_source_hash(self) -> None:
        authored = self.authored()
        authored["source_refs"]["gc_inputs"]["locator"] = "PDF page 99"
        self.write_authored(authored)
        with self.assertRaisesRegex(ValueError, "Provenance drift"):
            build(self.root)
        authored = self.authored()
        authored["source_refs"]["gc_inputs"]["locator"] = "PDF page 32"
        authored["source_refs"]["gc_inputs"]["source_sha256"] = "0" * 64
        self.write_authored(authored)
        with self.assertRaisesRegex(ValueError, "Provenance drift"):
            build(self.root)

    def test_rejects_changed_package_and_stale_manifest_binding(self) -> None:
        path = self.root / BASE.parent / "packages/staff-010.json"
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "Package drift"):
            build(self.root)
        shutil.copyfile(ROOT / BASE.parent / "packages/staff-010.json", path)
        authored = self.authored()
        authored["source_manifest"]["sha256"] = "0" * 64
        self.write_authored(authored)
        with self.assertRaisesRegex(ValueError, "Base manifest digest drift"):
            build(self.root)

    def test_rejects_unselected_evidence_and_executable_model(self) -> None:
        authored = self.authored()
        authored["source_refs"]["gc_inputs"]["record_id"] = "https://example.invalid/unselected"
        self.write_authored(authored)
        with self.assertRaisesRegex(ValueError, "Reference absent from selected evidence"):
            build(self.root)
        authored = copy.deepcopy(json.loads((ROOT / AUTHORED).read_text()))
        authored["calculation_models"][0]["status"] = "ready"
        self.write_authored(authored)
        with self.assertRaisesRegex(ValueError, "Execution is prohibited"):
            build(self.root)


if __name__ == "__main__":
    unittest.main()
