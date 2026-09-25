#!/usr/bin/env python3
"""Compare all 40 fixed workbench packages with retained candidate evidence."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evaluation/passage-boundary-candidate/question-replay.json"
RETAINED_ROOT = ROOT / "evaluation/passage-boundary-candidate/replay-projection"
EXPECTED_BUDGET = {"max_bytes": 524288, "max_nodes": 64, "max_relationships": 128, "max_depth": 6}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def read(root: Path, relative: str) -> tuple[bytes, dict]:
    path = root / relative
    raw = path.read_bytes() if path.is_file() else gzip.decompress((root / (relative + ".gz")).read_bytes())
    return raw, json.loads(raw)


def digest_list(rows: object) -> str:
    return sha(canonical(rows))


def verify_retained(candidate: Path, *, scratch: bool) -> str | None:
    receipt_path = candidate / "receipt.json"
    if not receipt_path.is_file():
        require(scratch and candidate.resolve() != RETAINED_ROOT.resolve(),
                "Retained replay receipt is missing; use --scratch only for an external scratch projection")
        return None
    receipt_raw = receipt_path.read_bytes()
    receipt = json.loads(receipt_raw)
    require(receipt["schema"] == "okf-dwp-passage-boundary-replay-retention.v1"
            and receipt["cases"] == 40 and len(receipt["files"]) == 48,
            "Retained replay receipt scope differs")
    expected = {"receipt.json"}
    for row in receipt["files"]:
        relative = row["retained_path"]
        require(relative not in expected and not Path(relative).is_absolute() and ".." not in Path(relative).parts,
                "Invalid retained replay path")
        expected.add(relative)
        stored = (candidate / relative).read_bytes()
        require(sha(stored) == row["retained_sha256"], "Retained replay file hash differs")
        raw = gzip.decompress(stored) if relative.endswith(".gz") else stored
        require(sha(raw) == row["sha256"] and len(raw) == row["bytes"],
                "Retained replay decoded bytes differ")
    actual = {p.relative_to(candidate).as_posix() for p in candidate.rglob("*") if p.is_file()}
    require(actual == expected, "Retained replay file set differs")
    return sha(receipt_raw)


def evidence(pack: dict) -> dict[str, dict]:
    found = {}
    for selected in pack["selected"]:
        record = selected["record"]
        if record["kind"] != "evidence":
            continue
        require(record["id"] not in found, "Duplicate selected evidence ID")
        spans = record.get("evidence_unit", {}).get("spans", [])
        found[record["id"]] = {"text_sha256": sha(record["text"].encode()),
            "spans": sorted([span["source_url"], span["source_start"], span["source_end"],
                             span["literal_sha256"]] for span in spans),
            "paths_sha256": digest_list(selected["paths"])}
    return found


def details(pack: dict) -> dict:
    selected = evidence(pack)
    requirements = {row["id"]: {"status": row["status"], "missing": row["missing"],
                    "required_paths_sha256": digest_list(row["required_paths"])} for row in pack["requirements"]}
    retrieval = pack.get("retrieval") or {}
    ordered = [item["record"]["id"] for item in pack["selected"] if item["record"]["kind"] == "evidence"]
    require(len(ordered) == len(selected), "Selected evidence sequence differs from unique set")
    return {"context_id": pack["context_id"], "evidence_status": pack["evidence_status"],
        "evidence": selected, "selected_evidence_ids_ordered": ordered, "requirements": requirements,
        "missing_evidence_sha256": digest_list(pack["missing_evidence"]),
        "missing_codes": sorted(row["code"] for row in pack["missing_evidence"]),
        "context_omissions_sha256": digest_list(pack["budget"]["omissions"]),
        "context_omission_codes": sorted(row["code"] for row in pack["budget"]["omissions"]),
        "retrieval_omissions_sha256": digest_list(retrieval.get("omissions", [])),
        "retrieval_omission_codes": sorted(row["code"] for row in retrieval.get("omissions", [])),
        "retrieval_candidates": retrieval.get("candidate_count"),
        "retrieval_fetched_bytes": retrieval.get("fetched_bytes"),
        "budget": {key: pack["budget"][key] for key in (*EXPECTED_BUDGET, "used_bytes", "used_nodes", "used_relationships", "truncated")}}


def compare(base: Path, candidate: Path, *, scratch: bool = False) -> dict:
    receipt_sha256 = verify_retained(candidate, scratch=scratch)
    base_registry_raw, base_registry = read(base, "evaluation/staff-questions/cases.json")
    candidate_registry_raw, candidate_registry = read(candidate, "evaluation/staff-questions/cases.json")
    require(base_registry_raw == candidate_registry_raw and len(base_registry["cases"]) == 40, 'Replay evidence invariant failed: base_registry_raw == candidate_registry_raw and len(base_registry["cases"]) == 40')
    require(base_registry == candidate_registry, 'Replay evidence invariant failed: base_registry == candidate_registry')
    base_workbench_raw, base_workbench = read(base, "evaluation/evidence-workbench/manifest.json")
    candidate_workbench_raw, candidate_workbench = read(candidate, "evaluation/evidence-workbench/manifest.json")
    require(base_workbench["source"]["engine_files"] == candidate_workbench["source"]["engine_files"], 'Replay evidence invariant failed: base_workbench["source"]["engine_files"] == candidate_workbench["source"]["engine_files"]')
    require(base_workbench["source"]["delivery_sha256"] == candidate_workbench["source"]["delivery_sha256"], 'Replay evidence invariant failed: base_workbench["source"]["delivery_sha256"] == candidate_workbench["source"]["delivery_sha')
    require(base_workbench["source"]["model_calls"] == candidate_workbench["source"]["model_calls"] == 0, 'Replay evidence invariant failed: base_workbench["source"]["model_calls"] == candidate_workbench["source"]["model_calls"] ==')
    require(base_workbench["source"]["network_calls"] == candidate_workbench["source"]["network_calls"] == 0, 'Replay evidence invariant failed: base_workbench["source"]["network_calls"] == candidate_workbench["source"]["network_calls"')
    base_units_raw, base_units = read(base, "structured-units/manifest.json")
    successor_units_raw, successor_units = read(base, "evaluation/passage-boundary-candidate/structured-units/manifest.json")
    scratch_units_raw, scratch_units = read(candidate, "structured-units/manifest.json")
    require(scratch_units["counts"] == successor_units["counts"], 'Replay evidence invariant failed: scratch_units["counts"] == successor_units["counts"]')
    require(scratch_units["records"] == successor_units["records"], 'Replay evidence invariant failed: scratch_units["records"] == successor_units["records"]')
    require([row["decoded_sha256"] for row in scratch_units["documents"]] == [row["decoded_sha256"] for row in successor_units["documents"]], 'Replay evidence invariant failed: [row["decoded_sha256"] for row in scratch_units["documents"]] == [row["decoded_sha256"] fo')
    require((candidate / "scripts/manual_structure.py").read_bytes() == (base / "scripts/passage_boundary_parser.py").read_bytes(), 'Replay evidence invariant failed: (candidate / "scripts/manual_structure.py").read_bytes() == (base / "scripts/passage_bound')
    require((candidate / "scripts/manual_navigation_regions.py").read_bytes() == (base / "scripts/manual_navigation_regions.py").read_bytes(), 'Replay evidence invariant failed: (candidate / "scripts/manual_navigation_regions.py").read_bytes() == (base / "scripts/manu')
    require(base_units["counts"]["units"] == 53727 and scratch_units["counts"]["units"] == 54577, 'Replay evidence invariant failed: base_units["counts"]["units"] == 53727 and scratch_units["counts"]["units"] == 54577')
    require(base_units["counts"]["source_text_bytes"] == scratch_units["counts"]["source_text_bytes"] == 35143443, 'Replay evidence invariant failed: base_units["counts"]["source_text_bytes"] == scratch_units["counts"]["source_text_bytes"] ')
    base_corpus_raw, base_corpus = read(base, "structured-context/evidence-connect-manifest.json")
    candidate_corpus_raw, candidate_corpus = read(candidate, "structured-context/evidence-connect-manifest.json")
    require(base_corpus["schema"] == candidate_corpus["schema"] == "okf-context-corpus.v3", 'Replay evidence invariant failed: base_corpus["schema"] == candidate_corpus["schema"] == "okf-context-corpus.v3"')
    require(base_corpus["extensions"]["unit_manifest"]["sha256"] == sha(base_units_raw), 'Replay evidence invariant failed: base_corpus["extensions"]["unit_manifest"]["sha256"] == sha(base_units_raw)')
    require(candidate_corpus["extensions"]["unit_manifest"]["sha256"] == sha(scratch_units_raw), 'Replay evidence invariant failed: candidate_corpus["extensions"]["unit_manifest"]["sha256"] == sha(scratch_units_raw)')
    base_assessment_raw, base_assessment = read(base, "evaluation/evidence-workbench/assessment.json")
    candidate_assessment_raw, candidate_assessment = read(candidate, "evaluation/evidence-workbench/assessment.json")
    require(base_assessment["source"]["registry_sha256"] == candidate_assessment["source"]["registry_sha256"] == sha(base_registry_raw), 'Replay evidence invariant failed: base_assessment["source"]["registry_sha256"] == candidate_assessment["source"]["registry_s')
    base_assessed = {row["id"]: row for row in base_assessment["cases"]}
    candidate_assessed = {row["id"]: row for row in candidate_assessment["cases"]}
    require(base_assessed.keys() == candidate_assessed.keys() == {row["id"] for row in base_registry["cases"]}, 'Replay evidence invariant failed: base_assessed.keys() == candidate_assessed.keys() == {row["id"] for row in base_registry["')
    rows = []
    for case in base_registry["cases"]:
        identifier = case["id"]
        relative = f"evaluation/evidence-workbench/packages/{identifier}.json"
        old_raw, old = read(base, relative)
        new_raw, new = read(candidate, relative)
        require(old["question"] == new["question"] == case["question"], 'Replay evidence invariant failed: old["question"] == new["question"] == case["question"]')
        require(old["ai_answer"] is new["ai_answer"] is None, 'Replay evidence invariant failed: old["ai_answer"] is new["ai_answer"] is None')
        require(all(old["budget"][key] == new["budget"][key] == value for key, value in EXPECTED_BUDGET.items()), 'Replay evidence invariant failed: all(old["budget"][key] == new["budget"][key] == value for key, value in EXPECTED_BUDGET.it')
        require(old["evidence_status"] == new["evidence_status"] == "insufficient", 'Replay evidence invariant failed: old["evidence_status"] == new["evidence_status"] == "insufficient"')
        before, after = details(old), details(new)
        old_assessed, new_assessed = base_assessed[identifier], candidate_assessed[identifier]
        require(old_assessed["package_sha256"] == sha(old_raw), 'Replay evidence invariant failed: old_assessed["package_sha256"] == sha(old_raw)')
        require(new_assessed["package_sha256"] == sha(new_raw), 'Replay evidence invariant failed: new_assessed["package_sha256"] == sha(new_raw)')
        page_retention = {}
        for field in ("selected_source_pages", "candidate_pages", "matched_candidate_pages"):
            old_pages, new_pages = set(old_assessed[field]), set(new_assessed[field])
            page_retention[field] = {"before": sorted(old_pages), "after": sorted(new_pages),
                                     "gained": sorted(new_pages - old_pages), "lost": sorted(old_pages - new_pages)}
        before_ids, after_ids = set(before["evidence"]), set(after["evidence"])
        before_paths, after_paths = before["requirements"], after["requirements"]
        require(before_paths.keys() == after_paths.keys(), 'Replay evidence invariant failed: before_paths.keys() == after_paths.keys()')
        delta = {"gained_ids": sorted(after_ids - before_ids), "lost_ids": sorted(before_ids - after_ids),
            "changed_text_ids": sorted(id for id in before_ids & after_ids
                                       if before["evidence"][id]["text_sha256"] != after["evidence"][id]["text_sha256"]),
            "changed_span_ids": sorted(id for id in before_ids & after_ids
                                       if before["evidence"][id]["spans"] != after["evidence"][id]["spans"]),
            "changed_selected_path_ids": sorted(id for id in before_ids & after_ids
                                       if before["evidence"][id]["paths_sha256"] != after["evidence"][id]["paths_sha256"]),
            "changed_requirement_ids": sorted(id for id in before_paths
                                       if before_paths[id] != after_paths[id]),
            "selected_evidence_order_changed": before["selected_evidence_ids_ordered"] != after["selected_evidence_ids_ordered"],
            "missing_evidence_changed": before["missing_evidence_sha256"] != after["missing_evidence_sha256"],
            "context_omissions_changed": before["context_omissions_sha256"] != after["context_omissions_sha256"],
            "retrieval_omissions_changed": before["retrieval_omissions_sha256"] != after["retrieval_omissions_sha256"],
            "package_bytes_delta": len(new_raw) - len(old_raw)}
        rows.append({"id": identifier, "question": case["question"],
                     "baseline_package_sha256": sha(old_raw), "candidate_package_sha256": sha(new_raw),
                     "before": before, "after": after, "page_retention": page_retention,
                     "source_delta": {"before": old_assessed["source_delta"], "after": new_assessed["source_delta"]},
                     "delta": delta})
    return {"schema": "okf-dwp-passage-boundary-question-replay.v1",
        "status": "offline-equal-budget-structural-candidate-comparison",
        "source": {"registry_sha256": sha(base_registry_raw),
                   "retained_receipt_sha256": receipt_sha256,
                   "comparison_script_sha256": sha(Path(__file__).read_bytes()),
                   "retention_script_sha256": sha((base / "scripts/retain_passage_boundary_replay.py").read_bytes()),
                   "baseline_workbench_manifest_sha256": sha(base_workbench_raw),
                   "candidate_workbench_manifest_sha256": sha(candidate_workbench_raw),
                   "baseline_assessment_sha256": sha(base_assessment_raw),
                   "candidate_assessment_sha256": sha(candidate_assessment_raw),
                   "baseline_unit_manifest_sha256": sha(base_units_raw),
                   "successor_unit_manifest_sha256": sha(successor_units_raw),
                   "scratch_unit_manifest_sha256": sha(scratch_units_raw),
                   "baseline_corpus_sha256": sha(base_corpus_raw),
                   "candidate_corpus_sha256": sha(candidate_corpus_raw),
                   "engine_files": base_workbench["source"]["engine_files"],
                   "delivery_sha256": base_workbench["source"]["delivery_sha256"],
                   "scratch_parser_sha256": sha((candidate / "scripts/manual_structure.py").read_bytes()),
                   "successor_parser_sha256": sha((base / "scripts/passage_boundary_parser.py").read_bytes()),
                   "scratch_navigation_sha256": sha((candidate / "scripts/manual_navigation_regions.py").read_bytes()),
                   "successor_navigation_sha256": sha((base / "scripts/manual_navigation_regions.py").read_bytes()),
                   "scratch_builder_sha256": sha((candidate / "scripts/build_structured_units.py").read_bytes()),
                   "budgets": EXPECTED_BUDGET, "model_calls": 0, "network_calls": 0},
        "summary": {"cases": len(rows), "all_insufficient": all(row["before"]["evidence_status"] == row["after"]["evidence_status"] == "insufficient" for row in rows),
                    "changed_selected_cases": sum(bool(row["delta"]["gained_ids"] or row["delta"]["lost_ids"]) for row in rows),
                    "changed_selected_order_cases": sum(row["delta"]["selected_evidence_order_changed"] for row in rows),
                    "changed_text_cases": sum(bool(row["delta"]["changed_text_ids"]) for row in rows),
                    "changed_requirement_cases": sum(bool(row["delta"]["changed_requirement_ids"]) for row in rows),
                    "changed_matched_candidate_page_cases": sum(bool(row["page_retention"]["matched_candidate_pages"]["gained"] or row["page_retention"]["matched_candidate_pages"]["lost"]) for row in rows),
                    "lost_matched_candidate_page_incidences": sum(len(row["page_retention"]["matched_candidate_pages"]["lost"]) for row in rows),
                    "gained_matched_candidate_page_incidences": sum(len(row["page_retention"]["matched_candidate_pages"]["gained"]) for row in rows),
                    "changed_context_omission_cases": sum(row["delta"]["context_omissions_changed"] for row in rows),
                    "changed_retrieval_omission_cases": sum(row["delta"]["retrieval_omissions_changed"] for row in rows),
                    "changed_package_bytes_cases": sum(bool(row["delta"]["package_bytes_delta"]) for row in rows)},
        "rows": rows,
        "limits": ["Source selection and exact passage retention are separate from legal applicability and answer quality.",
                   "The scratch projection changes producer bindings to run the candidate through the existing context chain; its unit records and document catalogues match the explicit versioned successor byte for byte.",
                   "No independent specialist review or current-law claim is made."]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--scratch", action="store_true", help="Compare an unretained disposable projection")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = compare(ROOT, args.candidate_root.resolve(), scratch=args.scratch)
    raw = canonical(report)
    if args.check:
        require(OUTPUT.read_bytes() == raw, "Question replay comparison drift")
    else:
        OUTPUT.write_bytes(raw)
    print(json.dumps({"status": "verified" if args.check else "built", **report["summary"],
                      "report_sha256": sha(raw)}))


if __name__ == "__main__":
    main()
