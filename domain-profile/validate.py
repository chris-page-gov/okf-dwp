#!/usr/bin/env python3
"""Check the draft discovery contract without making network requests."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "domain-profile"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write a separate check receipt")
    args = parser.parse_args()
    source = PROFILE / "domain-profile.json"
    profile = json.loads(source.read_text())
    schema = json.loads((PROFILE / "domain-profile.schema.json").read_text())
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(profile)
    yaml = YAML(typ="safe")
    yaml.version = (1, 2)
    assert yaml.load((PROFILE / "domain-profile.yaml").read_text()) == profile, "YAML/JSON representations differ"
    inventory_path = ROOT / "source/inventory.json"
    inventory = json.loads(inventory_path.read_text())
    assert profile["input_snapshot"]["inventory_sha256"] == digest(inventory_path.read_bytes()), "Inventory digest changed"
    assert profile["input_snapshot"]["item_count"] == len(inventory["documents"]), "Document count mismatch"
    assert profile["input_snapshot"]["byte_count"] == sum(row["size_bytes"] for row in inventory["documents"]), "PDF byte count mismatch"
    evidence = {row["id"]: row for row in profile["evidence"]}
    assert len(evidence) == len(profile["evidence"]), "Duplicate evidence identifier"
    for row in profile["evidence"]:
        location = row["location"].split("#", 1)[0]
        if not location.startswith(("https://", "http://")):
            path = ROOT / location
            assert path.is_file(), f"Missing local evidence: {location}"
            if row["sha256"] != "unknown":
                assert row["sha256"] == digest(path.read_bytes()), f"Local evidence changed: {location}"
    for denominator in profile["semantic_linking"]["eligible_entity_denominators"]:
        candidates = denominator["candidate_ids"]
        assert len(candidates) == len(set(candidates)) == denominator["eligible_count"], "Candidate count mismatch"
        assert denominator["candidate_list_sha256"] == digest(canonical(sorted(candidates))), "Candidate list digest changed"
    for link_set in profile["semantic_linking"]["link_sets"]:
        result = link_set["coverage_result"]
        assert link_set["coverage_result_sha256"] == digest(canonical(result)), "Coverage digest changed"
        for assertion in result["link_assertions"]:
            assert all(ref in evidence for ref in assertion["evidence_refs"]), "Missing link assertion evidence"
    receipt = {
        "schema": "okf-dwp-domain-check.v1",
        "status": "passed",
        "checks": ["JSON Schema 2020-12 and formats", "YAML 1.2 / JSON equality", "Source inventory binding", "Local evidence integrity", "Collection-link ledger digests"],
        "profile_sha256": digest(source.read_bytes()),
        "scope": "Structural and evidence-integrity checks only; no legal, domain-review, actual-consumer or full Foundry assurance claim.",
    }
    if args.output:
        args.output.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
