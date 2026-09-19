#!/usr/bin/env python3
"""Check retained public-browser observations offline; this never runs a browser."""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "validation/corpus-questions"
OBSERVATION = DIRECTORY / "public-explorer-observation.json"
IDENTITY_PATH = "validation/corpus-questions/public-explorer-identity.json"
IDENTITY_URL = "https://chris-page-gov.github.io/okf-explorer/okf-publication-identity.json"
JOURNEYS = {"search", "ask", "provenance", "graph", "machine_readable_context", "native_webmcp"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_observation(observation: dict, identity_bytes: bytes, receipt: dict,
                         context: dict, context_bytes: bytes) -> None:
    require(observation.get("schema") == "okf-dwp-public-corpus-explorer-observation.v1", "Wrong observation schema")
    observed_at = datetime.fromisoformat(observation["observed_at"].replace("Z", "+00:00"))
    require(observed_at.tzinfo is not None, "Observation time needs an explicit time zone")
    require(isinstance(observation.get("method"), str) and bool(observation["method"].strip()), "Observation method is absent")
    require(isinstance(observation.get("limitations"), list) and all(isinstance(x, str) and x.strip() for x in observation["limitations"])
            and bool(observation["limitations"]), "Observation limitations are absent")
    console_errors = observation.get("console_errors")
    require(isinstance(console_errors, list), "Observed console error list is absent")
    for error in console_errors:
        require(isinstance(error, dict) and all(isinstance(error.get(key), str) and bool(error[key].strip())
                                                for key in ["message", "justification"]), "Console error lacks an explicit allowlist justification")
    require(bool(re.fullmatch(r"[0-9a-f]{40}", observation["explorer_commit"])), "Explorer commit must be exact")
    require(bool(re.fullmatch(r"https://github\.com/chris-page-gov/okf-explorer/actions/runs/[0-9]+", observation["pages_run_url"])),
            "Pages run must identify this repository")
    identity_file = observation["identity_file"]
    require(identity_file.get("path") == IDENTITY_PATH and identity_file.get("url") == IDENTITY_URL, "Unexpected identity source")
    require(identity_file.get("bytes") == len(identity_bytes)
            and identity_file.get("sha256") == hashlib.sha256(identity_bytes).hexdigest(), "Retained identity bytes differ")
    identity = json.loads(identity_bytes)
    require(identity.get("schema") == "okf-publication-deployment-identity.v1"
            and identity.get("commit") == observation["explorer_commit"], "Deployed identity commit differs")
    require(isinstance(identity.get("materials"), list) and bool(identity["materials"]), "Deployed identity has no materials")
    require(receipt["context"]["bytes"] == len(context_bytes)
            and receipt["context"]["sha256"] == hashlib.sha256(context_bytes).hexdigest(), "Bounded reference package bytes differ")
    require(context["binding"] == receipt["binding"], "Bounded reference binding differs")
    version = receipt["bundle_version"]
    descriptor = f"https://raw.githubusercontent.com/chris-page-gov/okf-dwp/{version}/full-dmg/okf-corpus-context.json"
    expected_source = {"version": version, "descriptor_url": descriptor,
                       "manifest_url": context["binding"]["index_url"],
                       "manifest_sha256": context["binding"]["index_sha256"], "snapshot": context["bundle"]["snapshot"]}
    require(observation["source"] == expected_source, "Observed source/version/binding differs")
    url = urlparse(observation["url"])
    require(url.scheme == "https" and url.netloc == "chris-page-gov.github.io" and url.path == "/okf-explorer/explore/"
            and parse_qs(url.query).get("bundle") == [descriptor], "Observed Explorer URL must load the immutable corpus descriptor")
    search = observation["search"]
    require(isinstance(search.get("query"), str) and bool(search["query"].strip()), "Observed search is absent")
    require(type(search.get("matches")) is int and type(search.get("shown")) is int
            and 0 < search["shown"] <= search["matches"], "Observed search counts are invalid")
    ask = observation["ask"]
    expected_ask = {"question": context["question"], "context_id": context["context_id"],
                    "selected_records": len(context["selected"]), "relationships": len(context["relationships"]),
                    "package_bytes": len(context_bytes), "evidence_status": context["evidence_status"],
                    "truncated": context["budget"]["truncated"], "max_bytes": context["budget"]["max_bytes"]}
    for key, value in expected_ask.items():
        require(ask.get(key) == value and type(ask.get(key)) is type(value), f"Observed Ask {key} differs")
    source_urls = {p["url"] for item in context["selected"] for p in item["record"].get("provenance", [])
                   if urlparse(p["url"]).netloc == "assets.publishing.service.gov.uk"}
    require(isinstance(ask.get("source_urls"), list) and bool(ask["source_urls"])
            and all(isinstance(x, str) for x in ask["source_urls"]) and set(ask["source_urls"]).issubset(source_urls),
            "Observed source links must come from the selected official evidence")
    webmcp = observation["webmcp"]
    require(webmcp.get("build_context_id") == context["context_id"], "WebMCP context differs")
    for key in ["build_matches_remote", "explain_matches_build", "read_only"]:
        require(webmcp.get(key) is True, f"WebMCP observation lacks {key}")
    require(JOURNEYS.issubset(observation["journeys"])
            and all(observation["journeys"][key] is True for key in JOURNEYS), "Required actual-browser journey is absent")


def main() -> None:
    # Fixed public paths only: no arbitrary file reads, URLs, browser or network.
    observation = json.loads(OBSERVATION.read_text())
    receipt = json.loads((DIRECTORY / "bounded-abroad/receipt.json").read_text())
    context_bytes = (DIRECTORY / "bounded-abroad/context.json").read_bytes()
    validate_observation(observation, (ROOT / IDENTITY_PATH).read_bytes(), receipt, json.loads(context_bytes), context_bytes)
    print(json.dumps({"status": "passed-retained-browser-evidence", "browser_launched": False, "network_used": False,
                      "explorer_commit": observation["explorer_commit"], "context_id": observation["ask"]["context_id"],
                      "scope": "Offline consistency of the recorded manual public-browser journeys and deployed identity with retained MCP evidence; not a fresh browser run, accessibility audit or legal assurance."}))


if __name__ == "__main__":
    main()
