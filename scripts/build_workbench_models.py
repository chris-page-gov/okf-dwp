#!/usr/bin/env python3
"""Build a bounded, source-bound workbench inspection manifest without rules."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUTHORED = Path("domain-profile/workbench-models/inspection.json")
BASE = Path("evaluation/evidence-workbench/manifest.json")
OUTPUT = Path("evaluation/evidence-workbench/tools-manifest.json")
SHA = re.compile(r"^[0-9a-f]{64}$")
CASE = re.compile(r"^staff-[0-9]{3}$")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> dict:
    value = json.loads(path.read_bytes())
    require(isinstance(value, dict), f"Expected object: {path}")
    return value


def build(root: Path = ROOT) -> bytes:
    authored = load_json(root / AUTHORED)
    require(authored.get("schema") == "okf-dwp-workbench-models-authored.v1", "Unsupported authored model schema")
    source = authored.get("source_manifest")
    require(isinstance(source, dict) and source.get("path") == BASE.as_posix(), "Unexpected source manifest")
    base_raw = (root / BASE).read_bytes()
    require(source.get("sha256") == sha(base_raw), "Base manifest digest drift")
    base = json.loads(base_raw)
    require(base.get("schema") == "okf-evidence-workbench.v1", "Unsupported workbench schema")
    questions = base.get("questions")
    require(isinstance(questions, list) and len(questions) == 40, "Expected 40 frozen cases")
    ids = [q.get("id") for q in questions]
    require(len(set(ids)) == 40 and all(isinstance(i, str) and CASE.fullmatch(i) for i in ids), "Invalid case IDs")
    cases = {q["id"]: q for q in questions}

    refs = authored.get("source_refs")
    require(isinstance(refs, dict) and 1 <= len(refs) <= 100, "Invalid source references")
    seen = set()
    for key, ref in refs.items():
        require(isinstance(key, str) and isinstance(ref, dict), "Invalid source reference")
        case_id, record_id = ref.get("case_id"), ref.get("record_id")
        require(case_id in cases and isinstance(record_id, str), f"Unbound reference: {key}")
        package = cases[case_id]["package"]
        package_path = package.get("url")
        require(package_path == f"packages/{case_id}.json", f"Unexpected package path: {key}")
        raw = (root / BASE.parent / package_path).read_bytes()
        require(SHA.fullmatch(package.get("sha256", "")) is not None and sha(raw) == package["sha256"], f"Package drift: {case_id}")
        context = json.loads(raw)
        require(context.get("question") == cases[case_id]["question"] and context.get("evidence_status") == "insufficient", f"Case state drift: {case_id}")
        matched = [s["record"] for s in context.get("selected", []) if s.get("record", {}).get("id") == record_id]
        require(len(matched) == 1, f"Reference absent from selected evidence: {key}")
        record = matched[0]
        require(record.get("kind") == "evidence" and record.get("assertion_status") == "normalized", f"Unsupported authority: {key}")
        unit = record.get("evidence_unit") or {}
        require(unit.get("boundary_status") == ref.get("boundary_status") and unit.get("completeness") == ref.get("completeness"), f"Boundary drift: {key}")
        provenance = record.get("provenance") or []
        require(len(provenance) >= 1 and isinstance(provenance[0], dict), f"Missing provenance: {key}")
        p = provenance[0]
        for field in ("source_url", "locator", "source_sha256", "literal_sha256", "captured_at"):
            field_in_package = "url" if field == "source_url" else field
            require(ref.get(field) == p.get(field_in_package), f"Provenance drift: {key}:{field}")
        spans = unit.get("spans") or []
        require(bool(spans) and any(
            span.get("source_url") == ref["source_url"]
            and span.get("source_sha256") == ref["source_sha256"]
            and SHA.fullmatch(str(span.get("literal_sha256", ""))) is not None
            for span in spans
        ), f"Exact source span drift: {key}")
        require(SHA.fullmatch(ref["source_sha256"]) is not None and SHA.fullmatch(ref["literal_sha256"]) is not None, f"Invalid source digest: {key}")
        snippet = ref.get("snippet")
        require(isinstance(snippet, str) and 8 <= len(snippet) <= 120 and snippet in record.get("text", ""), f"Source snippet drift: {key}")
        require(ref.get("paragraph") is None or ref["paragraph"] in record["text"], f"Paragraph drift: {key}")
        seen.add((case_id, record_id))

    models = authored.get("calculation_models")
    interactions = authored.get("interaction_proposals")
    require(isinstance(models, list) and len(models) == 1, "Expected one blocked inspection model")
    require(isinstance(interactions, list) and len(interactions) <= 12, "Invalid interaction proposals")
    all_refs = {(r["case_id"], r["record_id"]) for r in refs.values()}

    def check_evidence(items: object, owner: str) -> None:
        require(isinstance(items, list) and items, f"Missing evidence: {owner}")
        for item in items:
            require(isinstance(item, dict) and set(item) == {"case_id", "record_id"} and
                    (item["case_id"], item["record_id"]) in all_refs, f"Unbound model evidence: {owner}")

    model = models[0]
    require(set(model) == {"id", "title", "status", "authority", "case_ids", "components", "jurisdiction", "effective_period", "inputs", "stages", "gaps"}, "Unexpected model contract")
    require(model["status"] == "blocked" and model["authority"] == "authored-unreviewed-proposal", "Execution is prohibited")
    require(model["jurisdiction"] is None and model["effective_period"] == {"from": None, "to": None}, "Unreviewed applicability cannot be dated")
    require(model["case_ids"] == ["staff-010", "staff-015", "staff-016"], "Unexpected model cases")
    require(isinstance(model["components"], list) and model["components"] == ["Guarantee Credit", "Savings Credit"], "Component drift")
    require(isinstance(model["inputs"], list) and 3 <= len(model["inputs"]) <= 30, "Invalid input count")
    input_ids = set()
    for field in model["inputs"]:
        require(set(field) == {"id", "label", "type", "unit", "reason", "required", "group"}, "Unexpected input field")
        require(field["id"] not in input_ids and field["type"] in {"money", "date", "boolean", "enum", "integer"}, "Invalid input type or ID")
        require(field["required"] is None, "Unreviewed inputs cannot be mandatory")
        require(field["unit"] is None or field["unit"] in {"GBP", "GBP/week"}, "Unexpected input unit")
        input_ids.add(field["id"])
    require(isinstance(model["stages"], list) and 3 <= len(model["stages"]) <= 12, "Invalid stage count")
    for stage in model["stages"]:
        require(set(stage) == {"id", "label", "description", "evidence", "gaps"}, "Unexpected stage field")
        check_evidence(stage["evidence"], stage["id"])
        require(isinstance(stage["gaps"], list) and stage["gaps"], "Stages need gaps")
    require(isinstance(model["gaps"], list) and model["gaps"], "Model needs gaps")
    for interaction in interactions:
        require(set(interaction) == {"id", "case_id", "from", "to", "distinction", "effect", "qualification", "evidence", "authority"}, "Unexpected interaction field")
        require(interaction["case_id"] == "staff-039" and interaction["authority"] == "authored-unreviewed-proposal", "Interaction scope drift")
        check_evidence(interaction["evidence"], interaction["id"])
    require(len({i["id"] for i in interactions}) == len(interactions), "Duplicate interaction IDs")
    output = {**base, "calculation_models": models, "interaction_proposals": interactions}
    raw = (json.dumps(output, ensure_ascii=False, indent=2) + "\n").encode()
    require(len(raw) <= 256 * 1024, "Workbench manifest exceeds Explorer limit")
    return raw


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify the generated manifest without writing")
    args = parser.parse_args()
    raw = build()
    path = ROOT / OUTPUT
    if args.check:
        require(path.read_bytes() == raw, "Generated workbench model manifest has drifted")
    else:
        path.write_bytes(raw)
    print(f"{'Verified' if args.check else 'Built'} {OUTPUT} ({len(raw)} bytes; sha256 {sha(raw)})")


if __name__ == "__main__":
    main()
