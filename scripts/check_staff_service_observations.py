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
LAYOUT_SCHEMA = "okf-compact-delivery-observation-layout.v1"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_directory(directory):
    directory = directory.absolute()
    for part in [*reversed(directory.parents), directory]:
        assert stat.S_ISDIR(part.lstat().st_mode), "Observation directory and parents must not be symlinks"
    return directory


def bounded_read(file, limit):
    checked_directory(file.parent)
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
    directory = checked_directory(directory)
    rows = []
    total_bytes = 0
    for file in sorted(directory.rglob("*")):
        assert not file.is_symlink(), "Symlinks are forbidden in public observations"
        if not file.is_file() or file.name == MANIFEST and file.parent == directory:
            continue
        assert len(rows) < 256, "Observation file count exceeds bound"
        total_bytes += file.lstat().st_size
        assert total_bytes <= 32 * 1024 * 1024, "Observation total exceeds byte bound"
        assert file.suffix in {".json", ".md", ".mjs", ".ts", ".py", ".png"}, "Unexpected public artefact type"
        data = bounded_read(file, MAX_FILE_BYTES)
        rows.append({"path": file.relative_to(directory).as_posix(), "bytes": len(data), "sha256": digest(data)})
    assert 0 < len(rows) <= 256 and sum(row["bytes"] for row in rows) <= 32 * 1024 * 1024
    return rows


def observation_layout(manifest):
    if "observation_layout" not in manifest:
        return {"staff_attempts": ["staff", "staff-native"], "historical_suite": "present"}
    layout = manifest["observation_layout"]
    assert isinstance(layout, dict) and set(layout) == {"schema", "staff_attempts", "historical_suite"}, "Unknown observation layout fields"
    assert layout["schema"] == LAYOUT_SCHEMA, "Unknown observation layout schema"
    names = layout["staff_attempts"]
    assert isinstance(names, list) and 0 < len(names) <= 8, "Declare one to eight staff attempts"
    assert all(isinstance(name, str) and re.fullmatch(r"[a-z][a-z0-9-]{0,63}", name)
               and name != "historical" for name in names), "Unsafe staff attempt name"
    assert len(set(names)) == len(names), "Repeated staff attempt"
    assert layout["historical_suite"] in {"present", "not_run"}, "Historical suite must be present or not_run"
    return layout


def verify_manifest(directory):
    directory = checked_directory(directory)
    manifest = json.loads(bounded_read(directory / MANIFEST, MAX_MANIFEST_BYTES))
    assert isinstance(manifest, dict) and set(manifest) <= {"schema", "scope", "files", "observation_layout"}, "Unknown artefact manifest fields"
    assert manifest["schema"] == "okf-compact-delivery-artifact-manifest.v1"
    observation_layout(manifest)
    rows = manifest["files"]
    assert isinstance(rows, list) and 0 < len(rows) <= 256
    seen = set()
    for row in rows:
        assert isinstance(row, dict) and set(row) == {"path", "bytes", "sha256"}, "Unknown artefact binding fields"
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


def verify_observations(directory, manifest):
    directory = checked_directory(directory)
    layout = observation_layout(manifest)
    admitted = {row["path"]: row for row in manifest["files"]}
    def read(file):
        name = file.relative_to(directory).as_posix()
        assert name in admitted, "Observation dependency is not manifest-bound"
        raw = bounded_read(file, MAX_FILE_BYTES)
        assert len(raw) == admitted[name]["bytes"] and digest(raw) == admitted[name]["sha256"], "Observation changed after inventory verification"
        return raw
    expected_folders = set(layout["staff_attempts"]) | ({"historical"} if layout["historical_suite"] == "present" else set())
    browser_paths = [PurePosixPath(name) for name in admitted if name.startswith("browser/")]
    assert all(len(name.parts) >= 3 and name.parts[1] in expected_folders for name in browser_paths), "Undeclared browser attempt must not be hidden"
    summaries = {name.parts[1] for name in browser_paths if name.name == "run-summary.json"}
    assert summaries == expected_folders, "Declared observation summaries differ"
    sdk_bytes = read(directory / "sdk-receipt.json")
    deployment_bytes = read(directory / "deployment.json")
    sdk, deployment = json.loads(sdk_bytes), json.loads(deployment_bytes)
    expected = sdk["compact_delivery"]
    assert sdk["passed"] is True and deployment["deployment"]["status"] == "succeeded"
    assert sdk["comparison_source_commit"] == deployment["runtime_commit"]
    assert sdk["comparison_worker_sha256"] == deployment["runtime_worker_sha256"]
    outcomes = []
    for name in layout["staff_attempts"]:
        folder = directory / "browser" / name
        summary = json.loads(read(folder / "run-summary.json"))
        receipts = {engine: json.loads(read(folder / (engine + "-receipt.json"))) for engine in ["chrome", "firefox", "webkit"]}
        check_outcomes(summary, receipts)
        for receipt in receipts.values():
            binding = receipt["binding"]
            assert binding == summary["binding"]
            assert binding["sdk"]["sha256"] == digest(sdk_bytes)
            assert binding["deployment"]["sha256"] == digest(deployment_bytes)
            assert binding["runtime_commit"] == deployment["runtime_commit"]
            assert binding["runtime_worker_sha256"] == deployment["runtime_worker_sha256"]
            harness = folder / ("verifier-" + binding["script"]["sha256"] + ".mjs")
            assert digest(read(harness)) == binding["script"]["sha256"]
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
                    read(folder / (receipt["browser"] + "-" + suffix + ".png"))
        outcomes.append({"attempt": name, "functional_passes": sum(r["functional_status"] == "passed" for r in receipts.values()),
                         "strict_console_passes": sum(r["strict_console_status"] == "passed" for r in receipts.values()),
                         "overall_clean_pass": summary["all_requested_engines_passed"]})
    if layout["historical_suite"] == "not_run":
        return {"staff_attempts": outcomes, "historical_functional_passes": None,
                "historical_strict_passes": None, "historical_strict_status": "not_run"}
    folder = directory / "browser/historical"
    historical = json.loads(read(folder / "run-summary.json"))
    assert historical["deployment"]["receipt_sha256"] == digest(deployment_bytes)
    assert historical["raw_results_and_traces_published"] is False
    assert digest(read(folder / ("projector-" + historical["projector_sha256"] + ".py"))) == historical["projector_sha256"]
    for item in historical["harness"]:
        assert Path(item["copy"]).name == item["copy"]
        assert digest(read(folder / item["copy"])) == item["sha256"]
    for item in historical["receipts"]:
        assert Path(item["path"]).name == item["path"]
        assert digest(read(folder / item["path"])) == item["sha256"]
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
    parser.add_argument("--directory", type=Path, help="Explicit retained release directory; default is historical v0.4.0")
    parser.add_argument("--write-manifest", action="store_true", help="Create a new manifest; refuse replacement")
    parser.add_argument("--staff-attempt", action="append", help="Declare each retained browser attempt when creating a new release manifest")
    parser.add_argument("--historical-suite", choices=["present", "not_run"], help="Declare whether the historical suite was run for this release")
    args = parser.parse_args()
    explicit_directory = args.directory is not None
    args.directory = checked_directory(args.directory or DEFAULT)
    assert args.write_manifest or not (args.staff_attempt or args.historical_suite), "Verification reads the frozen manifest layout; flags cannot override it"
    if args.write_manifest:
        extra = {}
        if args.directory != DEFAULT or args.staff_attempt or args.historical_suite:
            assert explicit_directory and args.staff_attempt and args.historical_suite, "New layouts require an explicit directory, staff attempts and historical-suite declaration"
            extra = {"observation_layout": {"schema": LAYOUT_SCHEMA, "staff_attempts": args.staff_attempt,
                                           "historical_suite": args.historical_suite}}
            observation_layout(extra)
        assert not os.path.lexists(args.directory / MANIFEST), "Never replace an observation manifest"
        manifest = {"schema": "okf-compact-delivery-artifact-manifest.v1",
            "scope": "Exact retained public deployment, SDK and browser artefacts, including failed attempts. This manifest excludes itself; verification makes no network request and does not turn a retained failure into acceptance.",
            **extra, "files": inventory(args.directory)}
        verify_observations(args.directory, manifest)
        with (args.directory / MANIFEST).open("x") as stream:
            stream.write(json.dumps(manifest, indent=2) + "\n")
    manifest = verify_manifest(args.directory)
    outcomes = verify_observations(args.directory, manifest)
    print(json.dumps({"status": "passed-retained-observation-integrity", "network_used": False,
                      "browser_launched": False, "files": len(manifest["files"]), **outcomes}))


if __name__ == "__main__":
    main()
