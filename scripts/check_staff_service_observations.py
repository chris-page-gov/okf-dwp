#!/usr/bin/env python3
"""Check retained public browser observations offline; never run a browser/network."""
import argparse
import hashlib
import json
import os
import stat
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "validation/compact-delivery/v0.4.0"
MANIFEST = "artifacts.json"
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_MANIFEST_BYTES = 128 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def bounded_read(file, limit):
    metadata = file.lstat()
    assert stat.S_ISREG(metadata.st_mode), "Artefact must be a regular file, never a symlink"
    assert metadata.st_size <= limit, "Artefact exceeds byte limit"
    descriptor = os.open(file, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        assert stat.S_ISREG(opened.st_mode) and opened.st_size <= limit
        data = stream.read(limit + 1)
    assert len(data) <= limit and len(data) == metadata.st_size == opened.st_size, "Artefact changed or exceeded byte limit"
    return data


def inventory(directory):
    assert not directory.is_symlink(), "Observation directory must not be a symlink"
    rows = []
    for file in sorted(directory.rglob("*")):
        assert not file.is_symlink(), "Symlinks are forbidden in public observations"
        if not file.is_file() or file.name == MANIFEST and file.parent == directory:
            continue
        assert file.suffix in {".json", ".md", ".mjs", ".ts", ".py", ".png"}, "Unexpected public artefact type"
        data = bounded_read(file, MAX_FILE_BYTES)
        rows.append({"path": file.relative_to(directory).as_posix(), "bytes": len(data), "sha256": digest(data)})
    assert 0 < len(rows) <= 256 and sum(row["bytes"] for row in rows) <= 32 * 1024 * 1024
    return rows


def verify_manifest(directory):
    assert not directory.is_symlink(), "Observation directory must not be a symlink"
    manifest = json.loads(bounded_read(directory / MANIFEST, MAX_MANIFEST_BYTES))
    assert manifest["schema"] == "okf-compact-delivery-artifact-manifest.v1"
    rows = manifest["files"]
    assert isinstance(rows, list) and 0 < len(rows) <= 256
    seen = set()
    for row in rows:
        relative = PurePosixPath(row["path"])
        assert not relative.is_absolute() and ".." not in relative.parts and relative.as_posix() == row["path"]
        assert row["path"] not in seen and row["path"] != MANIFEST
        assert re.fullmatch(r"[a-f0-9]{64}", row["sha256"])
        assert type(row["bytes"]) is int and 0 <= row["bytes"] <= 10 * 1024 * 1024
        seen.add(row["path"])
    assert inventory(directory) == rows, "Artefact bytes or path census differ"
    return manifest


def check_outcomes(summary, receipts):
    assert len(summary["results"]) == len(receipts)
    seen = set()
    for row in summary["results"]:
        browser = row["browser"]
        assert browser in {"chrome", "firefox", "webkit"} and browser not in seen
        seen.add(browser)
        receipt = receipts[browser]
        assert row["receipt"] == browser + "-receipt.json"
        for field in ["functional_status", "strict_console_status", "overall_clean_browser_acceptance"]:
            assert row[field] == receipt[field], "Summary changed a retained outcome"
        clean = receipt["functional_status"] == "passed" and receipt["strict_console_status"] == "passed"
        assert receipt["overall_clean_browser_acceptance"] is clean
        if receipt["console_errors"]:
            assert receipt["strict_console_status"] == "failed", "Console failures must remain visible"
    assert summary["all_requested_engines_passed"] is all(r["overall_clean_browser_acceptance"] for r in receipts.values())


def verify_observations(directory):
    sdk_bytes = (directory / "sdk-receipt.json").read_bytes()
    deployment_bytes = (directory / "deployment.json").read_bytes()
    sdk, deployment = json.loads(sdk_bytes), json.loads(deployment_bytes)
    expected = sdk["compact_delivery"]
    assert sdk["passed"] is True and deployment["deployment"]["status"] == "succeeded"
    assert sdk["comparison_source_commit"] == deployment["runtime_commit"]
    assert sdk["comparison_worker_sha256"] == deployment["runtime_worker_sha256"]
    outcomes = []
    for name in ["staff", "staff-native"]:
        folder = directory / "browser" / name
        summary = json.loads((folder / "run-summary.json").read_bytes())
        receipts = {engine: json.loads((folder / (engine + "-receipt.json")).read_bytes()) for engine in ["chrome", "firefox", "webkit"]}
        check_outcomes(summary, receipts)
        for receipt in receipts.values():
            binding = receipt["binding"]
            assert binding == summary["binding"]
            assert binding["sdk"]["sha256"] == digest(sdk_bytes)
            assert binding["deployment"]["sha256"] == digest(deployment_bytes)
            assert binding["runtime_commit"] == deployment["runtime_commit"]
            assert binding["runtime_worker_sha256"] == deployment["runtime_worker_sha256"]
            harness = folder / ("verifier-" + binding["script"]["sha256"] + ".mjs")
            assert digest(harness.read_bytes()) == binding["script"]["sha256"]
            assert receipt["context_id"] == expected["context_id"] and receipt["source_version"] == expected["bundle_version"]
            assert binding["request_pacing"]["automatic_retries"] is False
            if receipt["functional_status"] == "passed":
                assert receipt["catalogue"]["metadata_matches_verified_package"] is True
                assert receipt["catalogue"]["records"] == expected["selected_records"]
                assert receipt["catalogue"]["summary"]["relationships"] == expected["selected_relationships"]
                assert len(receipt["reads"]) == len(expected["reads"])
                for observed, reference in zip(receipt["reads"], expected["reads"]):
                    assert observed["section"] == reference["section"] and observed["record_id"] == reference["record_id"]
                    assert observed["rendered_sha256"] == reference["content_sha256"] and observed["characters"] == reference["characters"]
                    assert observed["matches_sdk"] is True
                for suffix in ["catalogue", "source-evidence"]:
                    assert (folder / (receipt["browser"] + "-" + suffix + ".png")).is_file()
        outcomes.append({"attempt": name, "functional_passes": sum(r["functional_status"] == "passed" for r in receipts.values()),
                         "strict_console_passes": sum(r["strict_console_status"] == "passed" for r in receipts.values()),
                         "overall_clean_pass": summary["all_requested_engines_passed"]})
    folder = directory / "browser/historical"
    historical = json.loads((folder / "run-summary.json").read_bytes())
    assert historical["deployment"]["receipt_sha256"] == digest(deployment_bytes)
    assert historical["raw_results_and_traces_published"] is False
    assert digest((folder / ("projector-" + historical["projector_sha256"] + ".py")).read_bytes()) == historical["projector_sha256"]
    for item in historical["harness"]:
        assert Path(item["copy"]).name == item["copy"]
        assert digest((folder / item["copy"]).read_bytes()) == item["sha256"]
    for item in historical["receipts"]:
        assert Path(item["path"]).name == item["path"]
        assert digest((folder / item["path"]).read_bytes()) == item["sha256"]
    tests = historical["tests"]
    assert len(tests) == 12 and len({(r["browser"], r["title"]) for r in tests}) == 12
    assert historical["functional_tests_passed"] == sum(r["functional_status"] == "passed" for r in tests)
    assert historical["strict_tests_passed"] == sum(r["strict_status"] == "passed" for r in tests)
    assert historical["strict_tests_failed"] == sum(r["strict_status"] != "passed" for r in tests)
    assert historical["strict_status"] == ("passed" if historical["strict_tests_failed"] == 0 else "failed")
    return {"staff_attempts": outcomes, "historical_functional_passes": historical["functional_tests_passed"],
            "historical_strict_passes": historical["strict_tests_passed"], "historical_strict_status": historical["strict_status"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DEFAULT)
    parser.add_argument("--write-manifest", action="store_true", help="Create a new manifest; refuse replacement")
    args = parser.parse_args()
    if args.write_manifest:
        assert not (args.directory / MANIFEST).exists(), "Never replace an observation manifest"
        (args.directory / MANIFEST).write_text(json.dumps({"schema": "okf-compact-delivery-artifact-manifest.v1",
            "scope": "Exact retained public deployment, SDK and browser artefacts, including failed attempts. This manifest excludes itself; verification makes no network request and does not turn a retained failure into acceptance.",
            "files": inventory(args.directory)}, indent=2) + "\n")
    manifest = verify_manifest(args.directory)
    outcomes = verify_observations(args.directory)
    print(json.dumps({"status": "passed-retained-observation-integrity", "network_used": False,
                      "browser_launched": False, "files": len(manifest["files"]), **outcomes}))


if __name__ == "__main__":
    main()
