#!/usr/bin/env python3
"""Check the retained first website publication without network or new claims."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "3f72ebc30128c2a3171951050a566d3ed8db7c16"
DIRECTORY = ROOT / "validation/learning-site" / ("public-" + COMMIT)
BASE = "https://chris-page-gov.github.io/okf-dwp/"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify(directory=DIRECTORY):
    inventory = json.loads((directory / "artifact-manifest.json").read_bytes())
    names = {"expected-site-manifest.json", "observation.json", "verify-public.mjs"}
    require(len(inventory["files"]) == len(names), "Wrong artefact census")
    require({row["path"] for row in inventory["files"]} == names, "Wrong artefact paths")
    materials = {}
    for row in inventory["files"]:
        path = directory / row["path"]
        require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 262144,
                "Artefact must be a bounded regular file")
        raw = path.read_bytes()
        require(len(raw) == row["bytes"] and sha(raw) == row["sha256"], "Artefact bytes differ")
        materials[row["path"]] = raw
    manifest_raw = materials["expected-site-manifest.json"]
    manifest = json.loads(manifest_raw)
    observed = json.loads(materials["observation.json"])
    require(manifest["schema"] == "okf-dwp-learning-site.v1" and
            observed["schema"] == "okf-dwp-learning-site-public-verification.v1", "Wrong observation schema")
    require(observed["source_commit"] == manifest["source_commit"] == COMMIT, "Wrong source commit")
    require(observed["base_url"] == BASE and observed["status"] == "passed" and
            observed["error"] is None, "Publication did not pass")
    require(observed["expected_manifest_sha256"] == sha(manifest_raw) and
            observed["verifier_sha256"] == sha(materials["verify-public.mjs"]), "Observation binding differs")
    require(observed["source_pages"] == manifest["page_count"] == len(manifest["source_pages"]) == 105,
            "Source-page census differs")
    require(observed["listed_outputs"] == len(manifest["files"]) == 108, "Output census differs")
    expected = {row["path"]: (row["bytes"], row["sha256"]) for row in manifest["files"]}
    require(len(expected) == 108, "Repeated output path")
    expected["site-manifest.json"] = (len(manifest_raw), sha(manifest_raw))
    rows = observed["requests"]
    require(len(rows) == observed["matched_requests"] == 109 and
            {row["path"] for row in rows} == set(expected), "Request census differs")
    for row in rows:
        require(row["status"] == "matched" and row["http_status"] == 200, "Unsuccessful request")
        require(row["url"] == row["response_url"] == BASE + row["path"], "Observed URL differs")
        require((row["bytes"], row["sha256"]) == expected[row["path"]], "Observed bytes differ")
    require(sum(row["bytes"] for row in rows) == observed["transferred_bytes"] == 1473921,
            "Transfer census differs")
    require(observed["limits"]["retries"] == 0, "Unexpected retry policy")
    return {"status": "passed", "source_commit": COMMIT, "matched_requests": 109,
            "network_used": False, "scope": "Retained point-in-time publication; not current availability."}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
