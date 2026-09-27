"""Offline controls for the reading-help technical release manifest gate."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_reading_help_release import (MANDATORY_BROWSER_CHECKS, ReleaseError,
                                        confined, validate)


def serial(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


class ReleaseManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest_path = Path("release/manifest.json")
        self.source = {"corpus": "frozen", "corpus_sha256": "c" * 64,
                       "registry": "questions", "registry_sha256": "d" * 64,
                       "engine_files": {"index.ts": "e" * 64}, "delivery_sha256": "f" * 64,
                       "model_calls": 0, "network_calls": 0}
        self.budget = {"max_bytes": 524288, "max_nodes": 64,
                       "max_relationships": 128, "max_depth": 6}
        self.manifest = self.make_manifest()
        self.save_manifest()

    def bind(self, path, value):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        body = serial(value) if not isinstance(value, bytes) else value
        file.write_bytes(body)
        return {"path": path, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}

    def fixture(self, prefix, count):
        return [{"id": f"{prefix}{n:02d}", "family": "dmg" if n <= count // 2 else "adm",
                 "document_id": f"doc-{prefix}-{n}", "page": 1, "start_utf8": n,
                 "end_utf8": n + 1, "literal_sha256": "1" * 64} for n in range(1, count + 1)]

    def make_manifest(self):
        counts = {"documents": 513, "leaves": 1455, "pages": 19090,
                  "passages": 53727, "extraction_blocked_pages": 893}
        catalogue = self.bind("reading-help-corpus/manifest.json", {
            "schema": "okf-reading-help-catalogue.v1", "rules_sha256": "a" * 64,
            "structured_snapshot": "frozen-structured", "status": "machine-proposed-unreviewed",
            "counts": counts})
        producer = self.bind("scripts/build_reading_help_corpus.py", b"producer\n")
        initial = self.fixture("I", 12)
        prior = self.fixture("H", 24)
        fresh = self.fixture("N", 24)
        initial_fixture = self.bind("controls/initial.json", {"initial": initial})
        prior_fixture = self.bind("controls/prior.json", {"cases": prior})
        fresh_fixture = self.bind("controls/fresh.json", {"cases": fresh})
        initial_receipt = self.bind("controls/initial-result.json", {
            "status": "passed", "passed_cases": [x["id"] for x in initial],
            "failed_cases": [], "model_calls": 0})
        original = self.bind("controls/prior-result.json", {
            "status": "failed", "passed_count": 23, "failed_count": 1,
            "failed_cases": [{"id": "H05"}]})
        latest = self.bind("controls/latest-result.json", {
            "initial_passed": 12, "revised_heldout_passed": 24, "failed": 0,
            "fixture_sha256": fresh_fixture["sha256"],
            "producer_sha256": producer["sha256"],
            "catalogue_sha256": catalogue["sha256"]})
        cases = [f"staff-{n:03d}" for n in range(1, 41)]
        case_files = []
        for case in cases:
            b = self.bind(f"replay/{case}.json", {
                "case_id": case, "passed": True, "failure": None,
                "evidence_status": "insufficient", "measurements": [
                    {"temperature": "cold", "bytes_read": 2, "package_sha256": "b" * 64, "package_bytes": 100},
                    {"temperature": "warm", "bytes_read": 0, "package_sha256": "b" * 64, "package_bytes": 100}]})
            case_files.append({**b, "path": f"{case}.json"})
        replay = self.bind("replay/report.json", {
            "schema": "okf-reading-help-question-replay.v1", "passed": True,
            "cases_passed": 40, "cases_failed": [], "cases": cases, "files": case_files,
            "source": self.source, "engine_files": self.source["engine_files"],
            "budget": self.budget, "model_calls": 0, "network_calls": 0,
            "total_cold_bytes": 80, "total_warm_bytes": 0})
        protocol = self.bind("replay/protocol.json", {
            "cases": cases, "source": self.source, "engine_files": self.source["engine_files"],
            "budget": self.budget, "model_calls": 0, "network_calls": 0})
        workbench_report = self.bind("workbench/report.json", {
            "questions": 40, "selected_evidence_records": 403,
            "exact_reading_help_targets": 401, "unmatched_records": ["u06", "u10"]})
        audit = self.bind("audit/consumer.json", {
            "failure_count": 0, "catalogue_sha256": catalogue["sha256"],
            "counts": {"documents": 513, "leaves": 1455}})
        return {
            "schema": "okf-reading-help-release.v1", "status": "candidate-awaiting-public-verification",
            "identity": {"catalogue": catalogue, "producer": producer, "rules_sha256": "a" * 64,
                         "structured_snapshot": "frozen-structured", "schema_ids": [
                             "okf-reading-help-catalogue.v1", "okf-reading-help-document.v1",
                             "okf-reading-help.v2"]},
            "coverage": {**counts, "status": "machine-proposed-unreviewed", "meaning": "bounded processing"},
            "source_controls": {"fixture": fresh_fixture, "initial_fixture": initial_fixture,
                                "original_heldout_fixture": prior_fixture, "initial_receipt": initial_receipt,
                                "original_heldout_failed": original, "latest_regression": latest,
                                "initial_passed": 12, "revised_fresh_heldout_passed": 24,
                                "latest_regression_failed": 0},
            "fixed_budget_replay": {"report": replay, "protocol": protocol,
                "source": self.source, "engine_files": self.source["engine_files"],
                "budget": self.budget, "cases": 40, "passed": 40, "failed": [],
                "all_insufficient": True, "packages_equal_to_retained": True,
                "model_calls": 0, "network_calls": 0,
                "cold_total_fetched_bytes": 80, "warm_total_fetched_bytes": 0},
            "workbench": {"report": workbench_report, "question_cases": 40,
                          "selected_distinct_records": 403, "exact_links": 401,
                          "unmatched_records": ["u06", "u10"],
                          "packages_changed": False, "evidence_requirements_changed": False},
            "corpus_consumer_compatibility": {"receipt": audit, "failure_count": 0,
                "counted_documents": 513, "counted_leaves": 1455},
            "revisions": {"consumer_merge_commit": "e" * 40,
                          "integrated_workbench_commit": "d" * 40,
                          "corpus_data_commit": "c" * 40,
                          "public_explorer_commit": None, "public_dwp_commit": None,
                          "public_browser_receipt": None}}

    def save_manifest(self):
        self.bind(self.manifest_path.as_posix(), self.manifest)

    def verify(self):
        return validate(self.root, self.manifest_path)

    def verified(self):
        self.manifest["status"] = "technically-verified-awaiting-specialist-review"
        self.manifest["revisions"].update(public_explorer_commit="e" * 40,
                                          public_dwp_commit="d" * 40)
        receipt = {"schema": "okf-reading-help-public-verification.v1", "status": "passed",
                   "errors": [], "inputs": {"explorer_commit": "e" * 40,
                   "workbench_commit": "d" * 40, "data_commit": "c" * 40},
                   "checks": [{"name": name, "passed": True}
                              for name in sorted(MANDATORY_BROWSER_CHECKS)]}
        self.manifest["revisions"]["public_browser_receipt"] = self.bind("public/receipt.json", receipt)
        self.save_manifest()
        return receipt

    def test_candidate_and_verified_states(self):
        self.assertFalse(self.verify()["public_browser_verified"])
        self.verified()
        self.assertTrue(self.verify()["public_browser_verified"])

    def test_missing_or_wrong_hash_fails(self):
        self.manifest["identity"]["producer"]["sha256"] = "0" * 64
        self.save_manifest()
        with self.assertRaisesRegex(ReleaseError, "SHA-256 differs"):
            self.verify()
        self.manifest["identity"]["producer"]["sha256"] = hashlib.sha256(b"producer\n").hexdigest()
        (self.root / "scripts/build_reading_help_corpus.py").unlink()
        self.save_manifest()
        with self.assertRaisesRegex(ReleaseError, "missing"):
            self.verify()

    def test_parent_and_symlink_escape_fail(self):
        with self.assertRaisesRegex(ReleaseError, "not a confined relative path"):
            confined(self.root, "../outside")
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "external.json"
            target.write_bytes(b"external")
            (self.root / "escape.json").symlink_to(target)
            with self.assertRaisesRegex(ReleaseError, "escapes"):
                confined(self.root, "escape.json")
            self.manifest["identity"]["producer"] = {
                "path": "escape.json", "bytes": 8,
                "sha256": hashlib.sha256(b"external").hexdigest()}
            self.save_manifest()
            with self.assertRaisesRegex(ReleaseError, "escapes"):
                self.verify()

    def test_failed_or_incomplete_public_receipt_cannot_verify(self):
        receipt = self.verified()
        receipt["checks"][0]["passed"] = False
        self.manifest["revisions"]["public_browser_receipt"] = self.bind("public/receipt.json", receipt)
        self.save_manifest()
        with self.assertRaisesRegex(ReleaseError, "check failed"):
            self.verify()
        receipt["checks"] = [x for x in receipt["checks"] if x["name"] != "staff-016 bound reading-help link"]
        receipt["status"] = "passed"
        for row in receipt["checks"]: row["passed"] = True
        self.manifest["revisions"]["public_browser_receipt"] = self.bind("public/receipt.json", receipt)
        self.save_manifest()
        with self.assertRaisesRegex(ReleaseError, "mandatory public browser check"):
            self.verify()

    def test_wrong_consumer_or_data_commit_fails(self):
        receipt = self.verified()
        receipt["inputs"]["explorer_commit"] = "f" * 40
        self.manifest["revisions"]["public_browser_receipt"] = self.bind("public/receipt.json", receipt)
        self.save_manifest()
        with self.assertRaisesRegex(ReleaseError, "another consumer or data"):
            self.verify()
        receipt["inputs"].update(explorer_commit="e" * 40, data_commit="f" * 40)
        self.manifest["revisions"]["public_browser_receipt"] = self.bind("public/receipt.json", receipt)
        self.save_manifest()
        with self.assertRaisesRegex(ReleaseError, "another consumer or data"):
            self.verify()

    def test_insufficient_and_retained_failure_are_not_upgraded(self):
        self.manifest["fixed_budget_replay"]["all_insufficient"] = False
        self.save_manifest()
        with self.assertRaisesRegex(ReleaseError, "Fixed-budget replay claim"):
            self.verify()
        self.manifest["fixed_budget_replay"]["all_insufficient"] = True
        failed = self.manifest["source_controls"]["original_heldout_failed"]
        replacement = self.bind(failed["path"], {"status": "passed", "passed_count": 24, "failed_count": 0, "failed_cases": []})
        self.manifest["source_controls"]["original_heldout_failed"] = replacement
        self.save_manifest()
        with self.assertRaisesRegex(ReleaseError, "Original held-out failure"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
