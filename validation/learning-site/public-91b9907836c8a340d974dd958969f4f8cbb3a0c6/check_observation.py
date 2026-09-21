#!/usr/bin/env python3
"""Verify retained receipt integrity offline, without claiming a fresh publication check."""
import json
from pathlib import Path
from verify_public import BASE, COMMIT, MAX_MANIFEST, MAX_MEMBER, bounded_read, require, sha, validate_manifest

HERE = Path(__file__).absolute().parent
NAMES = {"expected-site-manifest.json", "observation.json", "verify_public.py", "test_verify_public.py",
         "canonical-status.json", "pages-status.json", "README.md", "check_observation.py"}


def verify():
    inventory = json.loads(bounded_read(HERE / "artifact-manifest.json", MAX_MANIFEST))
    require(inventory["schema"] == "okf-publication-observation-artifacts.v1" and inventory["source_commit"] == COMMIT,
            "Wrong artefact identity")
    require(len(inventory["files"]) == len(NAMES) and {row["path"] for row in inventory["files"]} == NAMES,
            "Unexpected artefact paths")
    materials = {}
    for row in inventory["files"]:
        raw = bounded_read(HERE / row["path"], MAX_MEMBER)
        require(len(raw) == row["bytes"] and sha(raw) == row["sha256"], "Artefact identity differs")
        materials[row["path"]] = raw
    manifest = json.loads(materials["expected-site-manifest.json"])
    sources, files = validate_manifest(manifest)
    observed = json.loads(materials["observation.json"])
    require(observed["schema"] == "okf-dwp-learning-site-public-verification.v2" and
            observed["source_commit"] == COMMIT and observed["base_url"] == BASE and
            observed["status"] == "passed" and observed["phase"] == "complete", "Publication observation did not pass")
    require(observed["expected_manifest_sha256"] == sha(materials["expected-site-manifest.json"]) and
            observed["verifier_sha256"] == sha(materials["verify_public.py"]), "Execution binding differs")
    require(observed["immutable_sources"] == [sources[name] for name in sorted(sources)], "Recorded immutable sources differ")
    expected = {**files, "site-manifest.json": {"bytes": len(materials["expected-site-manifest.json"]), "sha256": sha(materials["expected-site-manifest.json"])}}
    rows = observed["requests"]
    require(len(rows) == len(expected) == observed["matched_requests"] and {r["path"] for r in rows} == set(expected), "Request census differs")
    for row in rows:
        require(row["status"] == "matched" and row["http_status"] == 200 and
                row["url"] == row["response_url"] == BASE + row["path"] and
                (row["bytes"], row["sha256"]) == (expected[row["path"]]["bytes"], expected[row["path"]]["sha256"]), "Response identity differs")
    require(sum(row["bytes"] for row in rows) == observed["transferred_bytes"], "Byte census differs")
    audit = observed["link_audit"]
    html = {name for name in files if name.endswith(".html")}
    require(len(audit["pages"]) == audit["html_pages"] == len(html) and
            {row["path"] for row in audit["pages"]} == html and not audit["errors"], "Link-audit census differs")
    for key in ("internal_links", "external_links_not_fetched"):
        require(sum(row[key] for row in audit["pages"]) == audit[key], "Link count differs")
    for name, run_id in (("canonical-status.json", 35547851197), ("pages-status.json", 35548811691)):
        run = json.loads(materials[name])
        require(run["headSha"] == COMMIT and run["databaseId"] == run_id and
                run["status"] == "completed" and run["conclusion"] == "success", "Required publication gate did not pass")
    return {"status": "verified-offline-receipt-integrity", "source_commit": COMMIT,
            "matched_requests": len(rows), "internal_links": audit["internal_links"], "network_calls": 0,
            "scope": "Retained point-in-time observations; neither fresh availability nor a rerun of the HTML audit."}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
