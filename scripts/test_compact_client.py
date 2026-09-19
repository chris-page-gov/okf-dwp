#!/usr/bin/env python3
"""Independent corruption controls for the retained compact-client observation."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import check_compact_client as checker


class CompactClientTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name) / "captures"
        shutil.copytree(checker.BASE, self.base)
        self.patch = patch.object(checker, "BASE", self.base)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.active = self.base / "claude-local-explicit-mcp-2026-09-19"

    def test_retained_calls_and_failed_attempt_replay(self):
        result = checker.verify()
        self.assertEqual([v["actual_tool_calls"] for v in result["observations"]], [0, 7])

    def mutate_tool_value(self, change):
        receipt_path = self.active / "observation.json"
        receipt = json.loads(receipt_path.read_text())
        row = next(r for r in receipt["calls"] if r["tool"] == "read_okf_evidence")
        path = self.active / row["response"]["path"]
        response = checker.message(path.read_bytes())
        value = response["result"]["structuredContent"]
        change(value)
        response["result"]["content"][0]["text"] = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        raw = json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode()
        path.write_bytes(raw)
        row["response"]["sha256"] = hashlib.sha256(raw).hexdigest()
        row["response"]["bytes"] = len(raw)
        receipt_path.write_text(json.dumps(receipt))

    def test_rejects_changed_source_slice_even_with_updated_capture_hash(self):
        self.mutate_tool_value(lambda value: value.update(data=value["data"] + "fabricated"))
        with self.assertRaises(ValueError):
            checker.verify()

    def test_rejects_upgraded_evidence_status(self):
        self.mutate_tool_value(lambda value: value.update(evidence_status="sufficient"))
        with self.assertRaisesRegex(ValueError, "evidence status"):
            checker.verify()

    def test_rejects_forged_byte_limit(self):
        self.mutate_tool_value(lambda value: value["delivery"].update(used_bytes=1))
        with self.assertRaisesRegex(ValueError, "size"):
            checker.verify()

    def test_rejects_erased_no_call_failure(self):
        p = self.base / "claude-local-2026-09-19/observation.json"
        receipt = json.loads(p.read_text()); receipt["status"] = "passed"
        p.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, "failure was erased"):
            checker.verify()


if __name__ == "__main__":
    unittest.main()
