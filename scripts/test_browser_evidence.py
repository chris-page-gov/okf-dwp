"""Synthetic controls for offline browser-observation validation, not browser tests."""
from copy import deepcopy
import hashlib
import json
from urllib.parse import urlencode
import unittest

from check_browser_evidence import DIRECTORY, IDENTITY_PATH, IDENTITY_URL, JOURNEYS, validate_observation


class BrowserEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.receipt = json.loads((DIRECTORY / "bounded-abroad/receipt.json").read_text())
        self.context_bytes = (DIRECTORY / "bounded-abroad/context.json").read_bytes()
        self.context = json.loads(self.context_bytes)
        self.identity_bytes = json.dumps({"schema": "okf-publication-deployment-identity.v1", "commit": "a" * 40,
                                          "materials": [{"path": "fixture-only.json", "sha256": "b" * 64}]}).encode()
        descriptor = f"https://raw.githubusercontent.com/chris-page-gov/okf-dwp/{self.receipt['bundle_version']}/full-dmg/okf-corpus-context.json"
        self.observation = {
            "schema": "okf-dwp-public-corpus-explorer-observation.v1", "observed_at": "2026-09-19T18:00:00Z",
            "method": "Synthetic test fixture only; no browser observation asserted.",
            "url": "https://chris-page-gov.github.io/okf-explorer/explore/?" + urlencode({"bundle": descriptor}),
            "explorer_commit": "a" * 40, "pages_run_url": "https://github.com/chris-page-gov/okf-explorer/actions/runs/1",
            "identity_file": {"path": IDENTITY_PATH, "url": IDENTITY_URL, "bytes": len(self.identity_bytes),
                              "sha256": hashlib.sha256(self.identity_bytes).hexdigest()},
            "source": {"version": self.receipt["bundle_version"], "descriptor_url": descriptor,
                       "manifest_url": self.context["binding"]["index_url"], "manifest_sha256": self.context["binding"]["index_sha256"],
                       "snapshot": self.context["bundle"]["snapshot"]},
            "search": {"query": "abroad", "matches": 10, "shown": 10},
            "ask": {"question": self.context["question"], "context_id": self.context["context_id"],
                    "selected_records": len(self.context["selected"]), "relationships": len(self.context["relationships"]),
                    "package_bytes": len(self.context_bytes), "evidence_status": self.context["evidence_status"],
                    "truncated": self.context["budget"]["truncated"], "max_bytes": self.context["budget"]["max_bytes"],
                    "source_urls": [self.context["selected"][0]["record"]["provenance"][0]["url"]]},
            "webmcp": {"build_context_id": self.context["context_id"], "build_matches_remote": True,
                       "explain_matches_build": True, "read_only": True},
            "journeys": dict.fromkeys(JOURNEYS, True), "console_errors": [],
            "limitations": ["Synthetic fixture, not a browser result."]}

    def check(self, observation=None, identity_bytes=None):
        validate_observation(observation or self.observation, identity_bytes or self.identity_bytes,
                             self.receipt, self.context, self.context_bytes)

    def test_consistent_synthetic_observation(self):
        self.check()

    def test_context_counts_scope_and_budget_cannot_drift(self):
        changes = {"context_id": "wrong", "selected_records": 5, "relationships": 1, "package_bytes": 30000,
                   "evidence_status": "sufficient", "truncated": False, "max_bytes": 65536}
        for key, value in changes.items():
            with self.subTest(field=key):
                changed = deepcopy(self.observation)
                changed["ask"][key] = value
                with self.assertRaisesRegex(ValueError, "Observed Ask"):
                    self.check(changed)

    def test_changed_identity_bytes_and_commit_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "identity bytes differ"):
            self.check(identity_bytes=self.identity_bytes + b"\n")
        self.observation["explorer_commit"] = "c" * 40
        with self.assertRaisesRegex(ValueError, "identity commit differs"):
            self.check()

    def test_mutable_bundle_url_is_rejected(self):
        self.observation["url"] = self.observation["url"].replace(self.receipt["bundle_version"], "main")
        with self.assertRaisesRegex(ValueError, "immutable corpus descriptor"):
            self.check()

    def test_missing_actual_journey_or_webmcp_proof_is_rejected(self):
        for section, field in [("journeys", "native_webmcp"), ("webmcp", "explain_matches_build")]:
            with self.subTest(field=field):
                changed = deepcopy(self.observation)
                changed[section][field] = False
                with self.assertRaises(ValueError):
                    self.check(changed)

    def test_arbitrary_file_and_source_links_are_rejected(self):
        changed = deepcopy(self.observation)
        changed["identity_file"]["path"] = "../../.email.md"
        with self.assertRaisesRegex(ValueError, "Unexpected identity source"):
            self.check(changed)
        self.observation["ask"]["source_urls"] = ["https://example.org/invented-evidence"]
        with self.assertRaisesRegex(ValueError, "selected official evidence"):
            self.check()

    def test_changed_binding_and_reference_package_are_rejected(self):
        self.observation["source"]["manifest_sha256"] = "d" * 64
        with self.assertRaisesRegex(ValueError, "source/version/binding differs"):
            self.check()
        self.context_bytes += b"\n"
        with self.assertRaisesRegex(ValueError, "reference package bytes differ"):
            self.check()

    def test_undocumented_console_error_is_rejected(self):
        self.observation["console_errors"] = [{"message": "Synthetic fixture error"}]
        with self.assertRaisesRegex(ValueError, "allowlist justification"):
            self.check()
        self.observation["console_errors"][0]["justification"] = "Synthetic control only, not an actual allowed application error."
        self.check()


if __name__ == "__main__":
    unittest.main()
