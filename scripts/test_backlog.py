#!/usr/bin/env python3
"""Negative controls for a portable public backlog gate."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from check_backlog import STATUSES, validate


class BacklogTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "public.md").write_text("Public fixture")
        self.register = {"schema": "okf-dwp-backlog.v1", "updated_on": "2026-09-19",
                         "status_meanings": {s: s for s in STATUSES}, "items": [
            {"id": "DWP-BL-001", "title": "Review sources", "status": "in_progress", "priority": "P0",
             "depends_on": [], "owner_role": "Reviewer", "evidence": ["public.md"],
             "acceptance_checks": ["Inspect source dates"], "scope_note": "No approval claimed"}]}
        self.markdown = "| DWP-BL-001 | P0 | Review sources | `in_progress` | — |"

    def test_valid_public_fixture(self):
        self.assertEqual(validate(self.register, self.markdown, self.root)["items"], 1)

    def test_rejects_duplicate_id(self):
        self.register["items"].append(deepcopy(self.register["items"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate(self.register, self.markdown, self.root)

    def test_rejects_dependency_cycle(self):
        self.register["items"][0]["depends_on"] = ["DWP-BL-001"]
        with self.assertRaisesRegex(ValueError, "cycle"):
            validate(self.register, self.markdown, self.root)

    def test_rejects_unknown_dependency(self):
        self.register["items"][0]["depends_on"] = ["DWP-BL-999"]
        with self.assertRaisesRegex(ValueError, "dependency"):
            validate(self.register, self.markdown, self.root)

    def test_rejects_private_or_escaping_paths_before_reading(self):
        for path in [".email.md", "nested/.email.md", "research/private.md", "../public.md", "/tmp/public.md", "https://example.com/data"]:
            with self.subTest(path=path):
                self.register["items"][0]["evidence"] = [path]
                with self.assertRaisesRegex(ValueError, "Unsafe or private"):
                    validate(self.register, self.markdown, self.root)

    def test_rejects_missing_evidence(self):
        self.register["items"][0]["evidence"] = ["missing.md"]
        with self.assertRaisesRegex(ValueError, "Missing or external"):
            validate(self.register, self.markdown, self.root)

    def test_rejects_unknown_status(self):
        self.register["items"][0]["status"] = "approved"
        with self.assertRaisesRegex(ValueError, "status"):
            validate(self.register, self.markdown, self.root)

    def test_rejects_misleading_documentation(self):
        with self.assertRaisesRegex(ValueError, "rows differ"):
            validate(self.register, self.markdown.replace("in_progress", "recorded_complete"), self.root)

    def tracked(self):
        self.register["delivery_tracking"] = "okf-backlog-work-packages.v1"
        self.register["items"][0]["work_packages"] = [
            {"id": "DWP-BL-001.delivery", "kind": "implementation", "status": "recorded_complete",
             "executor": "agent", "next_action": "Retain the inspected fixture", "evidence": ["public.md"]},
            {"id": "DWP-BL-001.acceptance", "kind": "independent_review", "status": "waiting",
             "executor": "human", "next_action": "Review the intended meaning", "evidence": []}]
        return self.register["items"][0]

    def test_delivery_can_complete_while_review_stays_open(self):
        self.tracked()
        self.assertEqual(validate(self.register, self.markdown, self.root)["items"], 1)

    def test_rejects_completion_that_hides_pending_review(self):
        item = self.tracked()
        item["status"] = "recorded_complete"
        with self.assertRaisesRegex(ValueError, "hides open"):
            validate(self.register, self.markdown.replace("in_progress", "recorded_complete"), self.root)

    def test_rejects_completed_work_without_evidence(self):
        self.tracked()["work_packages"][0]["evidence"] = []
        with self.assertRaisesRegex(ValueError, "lacks evidence"):
            validate(self.register, self.markdown, self.root)

    def test_rejects_model_review_as_independent_acceptance(self):
        self.tracked()["work_packages"][1]["executor"] = "agent"
        with self.assertRaisesRegex(ValueError, "cannot be assigned"):
            validate(self.register, self.markdown, self.root)

    def test_rejects_missing_delivery_breakdown(self):
        self.register["delivery_tracking"] = "okf-backlog-work-packages.v1"
        with self.assertRaisesRegex(ValueError, "Missing work packages"):
            validate(self.register, self.markdown, self.root)

    def test_rejects_unregistered_package_evidence(self):
        self.tracked()["work_packages"][0]["evidence"] = [".email.md"]
        with self.assertRaisesRegex(ValueError, "Unregistered"):
            validate(self.register, self.markdown, self.root)

    def test_work_package_projection_preserves_open_acceptance(self):
        from build_backlog_work_packages import render
        self.tracked()
        result = render(self.register)
        self.assertIn("`DWP-BL-001.acceptance` | independent_review | `waiting` | human", result)


if __name__ == "__main__":
    unittest.main()
