#!/usr/bin/env python3
"""Check a reading-help release manifest without network or source rebuilding.

This validates recorded bytes and technical release evidence. It cannot establish
legal applicability, answer quality, continuous service health or specialist review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "okf-reading-help-release.v1"
CANDIDATE = "candidate-awaiting-public-verification"
VERIFIED = "technically-verified-awaiting-specialist-review"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
MAX_BOUND_BYTES = 64 * 1024 * 1024
MANDATORY_BROWSER_CHECKS = frozenset({
    "public Explorer identity", "immutable corpus catalogue",
    "40 bound workbench sidecars", "local Chapter 60 source controls",
    "local ADM source controls", "printed 166-literal table control",
    "explicit ADM extraction gap control", "DMG 60025 source and cache",
    "ADM source passage", "printed table and extraction gap",
    "ADM extraction gap", "immutable Chapter 60 v1 manifests",
    "original Chapter 60 v1 fallback", "paired Chapter 60 footer",
    "dated Chapter 60 provision link", "staff-016 bound reading-help link",
})


class ReleaseError(ValueError):
    """A release claim or its local binding is unsupported."""


def require(value: Any, message: str) -> None:
    if not value:
        raise ReleaseError(message)


def confined(root: Path, relative: str) -> Path:
    """Resolve a declared path, including symlinks, inside the release checkout."""
    require(isinstance(relative, str) and relative and "\\" not in relative, "Invalid bound path")
    path = Path(relative)
    require(not path.is_absolute() and all(part not in (".", "..") for part in relative.split("/")),
            f"Bound path is not a confined relative path: {relative}")
    base = root.resolve(strict=True)
    try:
        target = (base / path).resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ReleaseError(f"Bound path is missing or invalid: {relative}") from error
    require(target.is_relative_to(base) and target.is_file(), f"Bound path escapes or is not a file: {relative}")
    return target


def bound_bytes(root: Path, binding: dict[str, Any], label: str) -> bytes:
    require(isinstance(binding, dict) and {"path", "bytes", "sha256"} <= binding.keys(),
            f"Incomplete binding: {label}")
    count, digest = binding["bytes"], binding["sha256"]
    require(type(count) is int and 0 < count <= MAX_BOUND_BYTES and
            isinstance(digest, str) and SHA256.fullmatch(digest), f"Invalid byte/hash binding: {label}")
    path = confined(root, binding["path"])
    require(path.stat().st_size == count, f"Byte count differs: {label}")
    body = path.read_bytes()
    require(hashlib.sha256(body).hexdigest() == digest, f"SHA-256 differs: {label}")
    return body


def json_body(body: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(body)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ReleaseError(f"Invalid JSON: {label}") from error
    require(isinstance(value, dict), f"Expected JSON object: {label}")
    return value


def all_bindings(root: Path, value: Any, location: str = "manifest") -> int:
    """Verify each recursively declared path/bytes/SHA triple, including duplicates."""
    if isinstance(value, list):
        return sum(all_bindings(root, item, f"{location}[{i}]") for i, item in enumerate(value))
    if not isinstance(value, dict):
        return 0
    fields = {"path", "bytes", "sha256"} & value.keys()
    own = 0
    if fields:
        bound_bytes(root, value, location)
        own = 1
    return own + sum(all_bindings(root, item, f"{location}.{key}")
                     for key, item in value.items() if key not in {"path", "bytes", "sha256"})


def matching(left: dict[str, Any], right: dict[str, Any], keys: tuple[str, ...], label: str) -> None:
    for key in keys:
        require(key in left and left[key] == right.get(key), f"{label} differs: {key}")


def validate_replay(root: Path, manifest: dict[str, Any]) -> None:
    claim = manifest["fixed_budget_replay"]
    report_binding = claim["report"]
    report = json_body(bound_bytes(root, report_binding, "fixed_budget_replay.report"), "replay report")
    protocol = json_body(bound_bytes(root, claim["protocol"], "fixed_budget_replay.protocol"), "replay protocol")
    require(report.get("schema") == "okf-reading-help-question-replay.v1" and report.get("passed") is True,
            "Replay report is not a passed retained comparison")
    require(report.get("cases_passed") == 40 and report.get("cases_failed") == [] and
            report.get("cases") == protocol.get("cases") and len(report["cases"]) == 40 and
            len(set(report["cases"])) == 40, "Replay does not cover 40 distinct cases")
    matching(claim, report, ("model_calls", "network_calls", "budget", "engine_files", "source"), "Replay claim")
    require(claim.get("cases") == 40 and claim.get("passed") == 40 and claim.get("failed") == [] and
            claim.get("all_insufficient") is True and claim.get("packages_equal_to_retained") is True and
            claim.get("cold_total_fetched_bytes") == report.get("total_cold_bytes") and
            claim.get("warm_total_fetched_bytes") == report.get("total_warm_bytes") == 0 and
            claim.get("model_calls") == report.get("model_calls") == 0 and
            claim.get("network_calls") == report.get("network_calls") == 0,
            "Fixed-budget replay claim differs from the receipt")
    matching(protocol, report, ("source", "engine_files", "budget", "model_calls", "network_calls"), "Replay protocol")
    files = report.get("files")
    require(isinstance(files, list) and len(files) == 40, "Replay case file census differs")
    case_ids: set[str] = set()
    base = Path(report_binding["path"]).parent
    cold_sum = warm_sum = 0
    for item in files:
        require(isinstance(item, dict), "Invalid replay case binding")
        case = json_body(bound_bytes(root, {**item, "path": (base / item["path"]).as_posix()}, "replay case"), "replay case")
        case_id = case.get("case_id")
        require(case_id in report["cases"] and case_id not in case_ids, "Duplicate or unknown replay case")
        case_ids.add(case_id)
        readings = case.get("measurements")
        require(case.get("passed") is True and case.get("failure") is None and
                case.get("evidence_status") == "insufficient" and isinstance(readings, list) and
                len(readings) == 2 and [x.get("temperature") for x in readings] == ["cold", "warm"],
                f"Replay case is not a matched insufficient pair: {case_id}")
        cold, warm = readings
        require(cold.get("package_sha256") == warm.get("package_sha256") and
                cold.get("package_bytes") == warm.get("package_bytes") and
                warm.get("bytes_read") == 0, f"Cold/warm package differs: {case_id}")
        cold_sum += cold["bytes_read"]
        warm_sum += warm["bytes_read"]
    require(case_ids == set(report["cases"]) and cold_sum == report["total_cold_bytes"] and
            warm_sum == report["total_warm_bytes"], "Replay file totals differ")


def validate_controls(root: Path, manifest: dict[str, Any]) -> None:
    claim = manifest["source_controls"]
    latest = json_body(bound_bytes(root, claim["latest_regression"], "latest source control"), "latest control")
    original = json_body(bound_bytes(root, claim["original_heldout_failed"], "original held-out control"), "original held-out")
    require(claim.get("initial_passed") == latest.get("initial_passed") == 12 and
            claim.get("revised_fresh_heldout_passed") == latest.get("revised_heldout_passed") == 24 and
            claim.get("latest_regression_failed") == latest.get("failed") == 0 and
            latest.get("fixture_sha256") == claim["fixture"]["sha256"] and
            latest.get("producer_sha256") == manifest["identity"]["producer"]["sha256"] and
            latest.get("catalogue_sha256") == manifest["identity"]["catalogue"]["sha256"],
            "Current 12/24 structural control binding differs")
    require(original.get("status") == "failed" and original.get("passed_count") == 23 and
            original.get("failed_count") == 1 and
            any(row.get("id") == "H05" for row in original.get("failed_cases", [])),
            "Original held-out failure was lost or relabelled")
    initial_receipt = json_body(bound_bytes(root, claim["initial_receipt"], "initial control receipt"), "initial receipt")
    require(initial_receipt.get("status") == "passed" and len(initial_receipt.get("passed_cases", [])) == 12 and
            initial_receipt.get("failed_cases") == [] and initial_receipt.get("model_calls") == 0,
            "Initial 12-case gate is not a recorded pass")
    initial = json_body(bound_bytes(root, claim["initial_fixture"], "initial fixture"), "initial fixture").get("initial")
    prior = json_body(bound_bytes(root, claim["original_heldout_fixture"], "original held-out fixture"), "original fixture").get("cases")
    fresh = json_body(bound_bytes(root, claim["fixture"], "fresh held-out fixture"), "fresh fixture").get("cases")
    def locations(rows: Any, count: int, each_family: int) -> set[tuple[Any, ...]]:
        require(isinstance(rows, list) and len(rows) == count, "Source control case count differs")
        require(sum(row.get("family") == "dmg" for row in rows) == each_family and
                sum(row.get("family") == "adm" for row in rows) == each_family,
                "Source control family balance differs")
        keys = {(row.get("family"), row.get("document_id"), row.get("page"),
                 row.get("start_utf8"), row.get("end_utf8")) for row in rows}
        require(len(keys) == count and all(isinstance(row.get("literal_sha256"), str) and
                SHA256.fullmatch(row["literal_sha256"]) for row in rows),
                "Source control locations or literals are duplicated/invalid")
        return keys
    initial_locations = locations(initial, 12, 6)
    prior_locations = locations(prior, 24, 12)
    fresh_locations = locations(fresh, 24, 12)
    require(not initial_locations & prior_locations and not initial_locations & fresh_locations and
            not prior_locations & fresh_locations, "Fresh held-out locations overlap an earlier control")
    require(set(initial_receipt["passed_cases"]) == {row["id"] for row in initial},
            "Initial receipt names different cases")
    require(len(original.get("failed_cases", [])) == 1 and original["failed_cases"][0]["id"] in
            {row["id"] for row in prior}, "Original failed case is not in its frozen fixture")
    require(manifest["coverage"] == {**json_body(bound_bytes(root, manifest["identity"]["catalogue"],
            "catalogue"), "catalogue")["counts"], "status": "machine-proposed-unreviewed",
            "meaning": manifest["coverage"].get("meaning")}, "Coverage differs from the catalogue")


def validate_public(root: Path, manifest: dict[str, Any]) -> None:
    revisions = manifest["revisions"]
    for key in ("public_explorer_commit", "public_dwp_commit", "consumer_merge_commit", "integrated_workbench_commit", "corpus_data_commit"):
        require(isinstance(revisions.get(key), str) and COMMIT.fullmatch(revisions[key]),
                f"Missing exact public or paired commit: {key}")
    receipt = json_body(bound_bytes(root, revisions.get("public_browser_receipt"), "public browser receipt"), "browser receipt")
    require(receipt.get("schema") == "okf-reading-help-public-verification.v1" and
            receipt.get("status") == "passed" and receipt.get("errors") == [],
            "Public browser receipt is failed or incomplete")
    inputs = receipt.get("inputs")
    require(isinstance(inputs, dict) and inputs.get("explorer_commit") == revisions["public_explorer_commit"] == revisions["consumer_merge_commit"] and
            inputs.get("workbench_commit") == revisions["integrated_workbench_commit"] and
            inputs.get("data_commit") == revisions["corpus_data_commit"],
            "Public browser receipt is for another consumer or data revision")
    checks = receipt.get("checks")
    require(isinstance(checks, list) and checks and all(isinstance(row, dict) and
            isinstance(row.get("name"), str) and row.get("passed") is True for row in checks),
            "A public browser check failed or is malformed")
    names = [row["name"] for row in checks]
    require(len(names) == len(set(names)) and MANDATORY_BROWSER_CHECKS <= set(names),
            "A mandatory public browser check is missing or duplicated")


def validate(root: Path, manifest_path: Path) -> dict[str, Any]:
    base = root.resolve(strict=True)
    path = manifest_path if manifest_path.is_absolute() else base / manifest_path
    try:
        path = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ReleaseError("Release manifest is missing or invalid") from error
    require(path.is_relative_to(base) and path.is_file(), "Release manifest escapes the checkout")
    manifest = json_body(path.read_bytes(), "release manifest")
    require(manifest.get("schema") == SCHEMA, "Unsupported release manifest schema")
    status = manifest.get("status")
    require(status in {CANDIDATE, VERIFIED}, "Unsupported or overstated release status")
    count = all_bindings(base, manifest)
    require(count >= 10, "Release manifest lacks source and check bindings")
    identity = manifest.get("identity")
    require(isinstance(identity, dict) and isinstance(identity.get("rules_sha256"), str) and
            SHA256.fullmatch(identity["rules_sha256"]) and identity.get("schema_ids") ==
            ["okf-reading-help-catalogue.v1", "okf-reading-help-document.v1", "okf-reading-help.v2"],
            "Corpus rules or schema identity differs")
    catalogue = json_body(bound_bytes(base, identity["catalogue"], "catalogue"), "catalogue")
    require(catalogue.get("rules_sha256") == identity["rules_sha256"] and
            catalogue.get("structured_snapshot") == identity.get("structured_snapshot") and
            catalogue.get("status") == "machine-proposed-unreviewed", "Corpus identity differs")
    validate_controls(base, manifest)
    validate_replay(base, manifest)
    workbench = manifest.get("workbench")
    report = json_body(bound_bytes(base, workbench["report"], "workbench report"), "workbench report")
    require(workbench.get("question_cases") == report.get("questions") == 40 and
            workbench.get("selected_distinct_records") == report.get("selected_evidence_records") == 403 and
            workbench.get("exact_links") == report.get("exact_reading_help_targets") == 401 and
            workbench.get("unmatched_records") == report.get("unmatched_records") and
            workbench.get("packages_changed") is False and
            workbench.get("evidence_requirements_changed") is False,
            "Workbench link claim differs")
    compatibility = manifest.get("corpus_consumer_compatibility")
    audit = json_body(bound_bytes(base, compatibility["receipt"], "consumer compatibility"), "consumer audit")
    require(compatibility.get("failure_count") == audit.get("failure_count") == 0 and
            compatibility.get("counted_documents") == audit.get("counts", {}).get("documents") == 513 and
            compatibility.get("counted_leaves") == audit.get("counts", {}).get("leaves") == 1455 and
            audit.get("catalogue_sha256") == identity["catalogue"]["sha256"],
            "Corpus consumer compatibility differs")
    if status == VERIFIED:
        validate_public(base, manifest)
    return {"schema": "okf-reading-help-release-check.v1", "status": status,
            "bound_files_checked": count, "public_browser_verified": status == VERIFIED,
            "boundary": "Technical evidence only; specialist legal review and service health are separate."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.root, args.manifest), sort_keys=True))
    except (ReleaseError, OSError, KeyError, TypeError, ValueError) as error:
        parser.exit(1, f"Reading-help release check failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
