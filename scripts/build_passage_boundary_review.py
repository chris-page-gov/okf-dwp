#!/usr/bin/env python3
"""Build a source-bound inspection queue for the parked amendment candidate.

This is an additive review projection. It never installs candidate units.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()

OUT = ROOT / "evaluation/passage-boundary-review"
FINDINGS = "evaluation/manual-structure/large-paragraph-review-2026-09-23/findings.json"
OBSERVATIONS = "evaluation/manual-structure/large-paragraph-review-2026-09-23/source-observations.json"
CENSUS = "domain-profile/passage-boundary-review/amendment-candidate-census.json"
SUCCESSOR_CENSUS = "evaluation/passage-boundary-candidate/versioned-census-02/report.json"
PROTOCOL = "domain-profile/passage-boundary-review/protocol.json"
BASELINE = "structured-units/manifest.json"
JOINER = b"\n"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: str) -> tuple[bytes, dict]:
    raw = (ROOT / path).read_bytes()
    return raw, json.loads(raw)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def source_ranges(spans: list[dict], page_ranges: dict[int, tuple[int, int]], page_bytes: dict[int, bytes]) -> list[dict]:
    result = []
    previous = -1
    for span in spans:
        page = span["page"]
        start, end = span["start_utf8"], span["end_utf8"]
        raw = page_bytes[page]
        require(0 <= start < end <= len(raw), "Span outside exact extraction")
        part = raw[start:end]
        require(digest(part) == span["literal_sha256"], "Source span hash differs")
        absolute_start = page_ranges[page][0] + start
        absolute_end = page_ranges[page][0] + end
        require(absolute_start >= previous, "Spans overlap or are out of order")
        previous = absolute_end
        result.append({"page": page, "start_utf8": absolute_start, "end_utf8": absolute_end,
                       "literal_sha256": span["literal_sha256"]})
    return result


def materialise(unit: dict, page_ranges: dict[int, tuple[int, int]], page_bytes: dict[int, bytes], *, baseline: bool) -> dict:
    spans = source_ranges(unit["spans"], page_ranges, page_bytes)
    raw = JOINER.join(page_bytes[s["page"]][s["start_utf8"] - page_ranges[s["page"]][0]:
                                        s["end_utf8"] - page_ranges[s["page"]][0]] for s in spans)
    require(len(raw) == unit["text_bytes"], "Passage byte count differs")
    require(not baseline or digest(raw) == unit["text_sha256"], "Baseline passage hash differs")
    if baseline:
        require(raw.decode("utf-8") == unit["text"], "Baseline passage text differs")
    return {"id": unit["id"], "role": unit["role"], "paragraph_labels": unit["paragraph_labels"],
            "spans": spans, "joiner": "\n", "text": raw.decode("utf-8"), "text_sha256": digest(raw),
            "text_bytes": len(raw), "boundary_status": unit["boundary_status"],
            "completeness": unit["completeness"]}


def overlap_bytes(before: list[dict], after: list[dict]) -> tuple[int, int]:
    """Check exact coverage of the old passage, allowing candidate units outside it."""
    covered = 0
    candidate_total = sum(s["end_utf8"] - s["start_utf8"] for s in after)
    for old in before:
        intervals = sorted((max(old["start_utf8"], new["start_utf8"]), min(old["end_utf8"], new["end_utf8"]))
                           for new in after if new["page"] == old["page"]
                           and max(old["start_utf8"], new["start_utf8"]) < min(old["end_utf8"], new["end_utf8"]))
        cursor = old["start_utf8"]
        for start, end in intervals:
            require(start == cursor, "Candidate loses or duplicates old passage bytes")
            covered += end - start
            cursor = end
        require(cursor == old["end_utf8"], "Candidate leaves old passage bytes uncovered")
    return covered, candidate_total - covered


def build() -> dict[str, bytes]:
    finding_raw, findings = read_json(FINDINGS)
    observation_raw, observations = read_json(OBSERVATIONS)
    census_raw, census = read_json(CENSUS)
    successor_raw, successor = read_json(SUCCESSOR_CENSUS)
    protocol_raw, protocol = read_json(PROTOCOL)
    baseline_raw, baseline = read_json(BASELINE)
    require(protocol["baseline_commit"] == "68c34d6ff9c82b9c7795c44bad39b57424fc4c95"
            and protocol["case_denominator"] == 28 and protocol["candidate_source"] == CENSUS,
            "Review protocol scope differs")
    require(len(findings["items"]) == len(observations["items"]) == len(census["source_cases"]) == 28,
            "Expected 28 frozen source cases")
    require(digest(baseline_raw) == findings["source_baseline"]["sha256"] == census["protocol"]["source_manifest"]["sha256"],
            "Frozen baseline identity differs")
    require(digest(finding_raw) == census["protocol"]["reviewed_expectations"]["sha256"],
            "Frozen findings identity differs")
    require(census["documents"] == 513 and census["authored_units_exact"] == 75 and census["changed_document_count"] == 134,
            "Parked census denominator differs")
    require(census["context_assemblies"] == census["model_calls"] == census["network_calls"] == 0,
            "Parked census performed external or question work")
    parked_cases = {row["number"]: row for row in census["source_cases"]}
    successor_cases = {row["number"]: row for row in successor["source_cases"]}
    require(parked_cases.keys() == successor_cases.keys() == set(range(1, 29)), "Successor case census differs")
    require([number for number in parked_cases if parked_cases[number] != successor_cases[number]] == [19],
            "Successor case difference is not the bounded overlap-table correction")
    require(successor["documents"] == 513 and successor["authored_units_exact"] == 75,
            "Successor corpus or authored denominator differs")
    require(successor["candidate_counts"]["source_text_bytes"] == census["original_source_bytes"],
            "Successor source byte census differs")
    require(successor["changed_document_count"] == 125
            and all(row["source_role"] != "substantive" for row in successor["changed_documents"]),
            "Successor amendment scope differs")
    inv_raw, inventory = read_json("source/full-dmg-2026-09-15/inventory.json")
    documents = {d["id"]: d for d in inventory["documents"]}
    baseline_docs = {(d["family"], d["document_id"]): d for d in baseline["documents"]}
    successor_manifest_raw, successor_manifest = read_json("evaluation/passage-boundary-candidate/structured-units/manifest.json")
    require(digest(successor_manifest_raw) == successor["candidate_manifest_sha256"],
            "Installed successor units differ from review census")
    successor_docs = {(d["family"], d["document_id"]): d for d in successor_manifest["documents"]}
    observations_by_number = {x["number"]: x for x in observations["items"]}
    candidate_by_number = {x["number"]: x for x in census["source_cases"]}
    outputs: dict[str, bytes] = {}
    cases = []
    for finding in findings["items"]:
        number = finding["number"]
        observation = observations_by_number[number]
        candidate = candidate_by_number[number]
        require(finding["unit_id"] == observation["id"] == candidate["old_unit_id"], "Case identity differs")
        require(finding["document_id"] == observation["document_id"] == candidate["document_id"], "Case document differs")
        doc = documents[finding["document_id"]]
        require(doc["sha256"] == observation["source"]["sha256"], "PDF identity differs")
        require(digest((ROOT / doc["pdf_path"]).read_bytes()) == doc["sha256"], "Frozen PDF hash differs")
        pages_path = observation["pages_path"]
        pages_raw, source = read_json(pages_path)
        require(digest(pages_raw) == doc["pages_sha256"] == observation["source"]["pages_sha256"],
                "Frozen extraction hash differs")
        require(source["source_sha256"] == doc["sha256"], "Extraction belongs to another PDF")
        page_bytes = {p["page"]: p["text"].encode("utf-8") for p in source["pages"]}
        extraction = bytearray()
        page_ranges: dict[int, tuple[int, int]] = {}
        page_rows = []
        for index, page in enumerate(source["pages"]):
            if index:
                extraction.extend(JOINER)
            start = len(extraction)
            extraction.extend(page_bytes[page["page"]])
            end = len(extraction)
            page_ranges[page["page"]] = (start, end)
            page_rows.append({"number": page["page"], "start_utf8": start, "end_utf8": end})
        case_id = f"case-{number:03d}"
        extraction_path = f"extractions/{doc['id']}.txt"
        outputs[extraction_path] = bytes(extraction)
        ref = baseline_docs[(observation["family"], doc["id"])]
        raw = (ROOT / "structured-units" / ref["path"]).read_bytes()
        require(digest(raw) == ref["sha256"], "Baseline document hash differs")
        base_doc = json.loads(gzip.decompress(raw))
        old = next(u for u in base_doc["units"] if u["id"] == finding["unit_id"])
        require(old["record_sha256"] == finding["record_sha256"], "Baseline record hash differs")
        before = [materialise(old, page_ranges, page_bytes, baseline=True)]
        after = [materialise(u, page_ranges, page_bytes, baseline=False) for u in candidate["intersecting_units"]]
        successor_case = successor_cases[number]
        if successor_case != candidate:
            successor_ref = successor_docs[(observation["family"], doc["id"])]
            successor_doc_raw = (ROOT / "evaluation/passage-boundary-candidate/structured-units" / successor_ref["path"]).read_bytes()
            require(digest(successor_doc_raw) == successor_ref["sha256"], "Successor document hash differs")
            successor_doc = json.loads(gzip.decompress(successor_doc_raw))
            successor_ids = {u["id"] for u in successor_case["intersecting_units"]}
            successor_units = [u for u in successor_doc["units"] if u["id"] in successor_ids]
            require(len(successor_units) == len(successor_ids), "Successor case units missing")
            successor_after = [materialise(u, page_ranges, page_bytes, baseline=False) for u in successor_units]
            overlap_bytes(before[0]["spans"], [s for u in successor_after for s in u["spans"]])
        old_spans = before[0]["spans"]
        after_spans = [s for u in after for s in u["spans"]]
        covered, outside = overlap_bytes(old_spans, after_spans)
        evidence = []
        for probe in finding["evidence"]:
            page = probe["page"]
            local = page_bytes[page][probe["start_utf8"]:probe["end_utf8"]]
            require(digest(local) == probe["literal_sha256"] and local.decode("utf-8") == probe["literal"],
                    "Frozen source observation differs")
            evidence.append({"page": page, "start_utf8": page_ranges[page][0] + probe["start_utf8"],
                             "end_utf8": page_ranges[page][0] + probe["end_utf8"],
                             "literal": probe["literal"], "literal_sha256": probe["literal_sha256"],
                             "pdf_url": probe.get("official_source", doc["url"] + f"#page={page}")})
        payload = {"schema": "okf-passage-boundary-review.v1", "id": case_id,
            "label": f"{doc['title']}: {', '.join(finding['paragraph_labels']) or 'unlabelled passage'}",
            "document": {"id": doc["id"], "family": observation["family"],
                "version": doc["sha256"], "source_role": doc["role"],
                "pdf": {"url": doc["url"], "sha256": doc["sha256"], "repository_path": doc["pdf_path"],
                        "delivery_url": "https://raw.githubusercontent.com/chris-page-gov/okf-dwp/"
                                        + protocol["baseline_commit"] + "/" + doc["pdf_path"]},
                "extraction": {"url": extraction_path, "sha256": digest(bytes(extraction)),
                               "source_path": pages_path, "source_sha256": digest(pages_raw)},
                "baseline_sha256": digest(baseline_raw),
                "parser": {"version": "parked-candidate-6ae66224", "ruleset_version": "amendment-repair-v1",
                           "settings_sha256": digest(canonical(census["protocol"])),
                           "settings_text": canonical(census["protocol"]).decode("utf-8"),
                           "applied_rules": ["parked-historical-navigation-and-bare-appendix"],
                           "implementation_bindings": census["implementation_bindings"]}},
            "pages": page_rows, "before": before, "after": after,
            "coverage": {"old_passage_bytes": sum(s["end_utf8"] - s["start_utf8"] for s in old_spans),
                         "covered_once_bytes": covered, "candidate_bytes_outside_old_passage": outside,
                         "scope": "The old passage only; not a complete document census"},
            "observation": {"method": "frozen-source-review-and-parked-parser-census",
                            "classification": finding["classification"], "finding_status": finding["finding_status"],
                            "rationale": finding["finding"], "uncertainty": finding["follow_up"],
                            "source_links": evidence},
            "review": {"status": "pending-independent-review", "specialist_review": "not-reviewed",
                       "legal_answerability": "not-established"}}
        residual = sum(unit["text_bytes"] for unit in (successor_after if successor_case != candidate else after)
                       if unit["role"] == "unresolved-fragment")
        # These decisions judge the named source boundary, not complete rule
        # interpretation. Large untyped amendment blocks and ambiguous local
        # numbering remain partial even when the old giant unit is split.
        partial = {3, 9, 11, 12, 15, 16, 17, 20, 23, 25, 26, 27}
        status = "unresolved" if number == 14 else "partial" if number in partial else "corrected"
        findings = []
        if residual:
            findings.append(f"{residual} source bytes remain in unresolved-fragment units; their local roles are not established.")
        if number == 14:
            findings.append("The frozen extraction is scrambled across pages and the 071920 passage is unchanged.")
        if number == 11:
            findings.append("The separated appendix section still contains local table material without its own reviewed boundary.")
        if number in (16, 17):
            findings.append("Trailing 83040 or 75165 markers may still sit with the preceding paragraph.")
        if number == 19:
            rationale = "The successor separates the page-36 overlap matrix from 070594 as reference-table material and retains the contents boundary."
        elif number == 14:
            rationale = "No source-safe structural correction is supported by the scrambled frozen extraction."
        elif number == 11:
            rationale = "The appendix is separated from 070333, but the appendix's internal table boundary remains unreviewed."
        elif status == "partial":
            rationale = "The original giant passage is split at the observed boundary, but substantial adjacent amendment material remains structurally untyped."
        else:
            rationale = "The observed front-matter or contents boundary is separated from the paragraph in the successor projection."
        outcome = {"status": status, "target_boundary": status, "rationale": rationale,
                   "residual_structural_findings": findings, "legal_answerability": "not-established"}
        payload["technical_outcome"] = outcome
        if successor_case != candidate:
            payload["successor_after"] = successor_after
        path = f"cases/{case_id}.json"
        outputs[path] = canonical(payload)
        cases.append({"id": case_id, "label": payload["label"], "url": path,
                      "sha256": digest(outputs[path]), "bytes": len(outputs[path]),
                      "document_id": doc["id"], "classification": finding["classification"],
                      "review_status": "pending-independent-review",
                      "technical_outcome": outcome["status"]})
    changed = census["changed_documents"]
    substantive = [row for row in changed if row["source_role"] == "substantive"]
    require(len(substantive) == 9, "Nine-chapter impact set differs")
    migration = {"schema": "okf-dwp-passage-boundary-identity-migration.v1",
        "status": "unreviewed-overlap-proposals-no-redirects",
        "baseline_manifest_sha256": digest(baseline_raw),
        "candidate_manifest_sha256": census["candidate_manifest_sha256"],
        "case_mappings": [{"case_id": f"case-{row['number']:03d}", "old_id": row["old_unit_id"],
                           "candidate_ids": [u["id"] for u in row["intersecting_units"]],
                           "mapping_status": "overlap-only-pending-independent-review"}
                          for row in census["source_cases"]],
        "changed_documents": changed,
        "removed_ids": sum(row["removed_ids"] for row in changed),
        "added_ids": sum(row["added_ids"] for row in changed),
        "limits": "Identifier overlap does not establish semantic equivalence or legal-reference redirection."}
    outputs["identity-migration.json"] = canonical(migration)
    successor_settings = {"profile": "passage-boundary-v1",
        "profile_argument": "--profile passage-boundary-v1",
        "source_scope": "frozen-513-document-corpus",
        "bare_appendix_scope": "historical-amendments-only",
        "overlap_matrix_rule": "literal-reciprocal-agreement-heading-plus-column-controls",
        "bytes": "exact-original-utf8"}
    manifest = {"schema": "okf-passage-boundary-review-manifest.v1", "title": "Historical amendment passage boundary review",
        "status": "candidate-for-independent-source-review", "baseline_commit": "68c34d6ff9c82b9c7795c44bad39b57424fc4c95",
        "source": {"baseline_manifest_sha256": digest(baseline_raw), "findings_sha256": digest(finding_raw),
                   "observations_sha256": digest(observation_raw), "inventory_sha256": digest(inv_raw),
                   "parked_census_sha256": digest(census_raw), "successor_census_sha256": digest(successor_raw),
                   "review_protocol_sha256": digest(protocol_raw),
                   "parked_candidate_manifest_sha256": census["candidate_manifest_sha256"]},
        "cases": cases,
        "candidate_comparison": {"status": "narrowed-historical-amendment-candidate-technical-review",
            "parser_version": "passage-boundary-v1",
            "identity_version": "manual-structure-v1",
            "ruleset_version": "historical-navigation-and-amendment-only-bare-appendix-v2",
            "settings_text": canonical(successor_settings).decode("utf-8"),
            "settings_sha256": digest(canonical(successor_settings)),
            "implementation_bindings_sha256": digest(canonical(successor["implementation_bindings"])),
            "changed_documents": successor["changed_document_count"],
            "candidate_units": successor["candidate_counts"]["units"],
            "historical_amendments_changed": len(successor["changed_documents"]),
            "substantive_chapters_changed": 0,
            "case_outputs_sha256": digest(canonical(successor["source_cases"]))},
        "successor_case_differences": ["case-019"],
        "impact": {"documents": census["documents"], "original_source_bytes": census["original_source_bytes"],
                   "authored_units_exact": census["authored_units_exact"],
                   "changed_documents": census["changed_document_count"],
                   "historical_amendments_changed": len(changed) - len(substantive),
                   "substantive_chapters_changed": substantive,
                   "baseline_units": census["baseline_counts"]["units"],
                   "candidate_units": census["candidate_counts"]["units"],
                   "removed_ids": sum(row["removed_ids"] for row in changed),
                   "added_ids": sum(row["added_ids"] for row in changed),
                   "identity_migration_status": "unreviewed-overlap-required",
                   "identity_migration": {"url": "identity-migration.json", "sha256": digest(outputs["identity-migration.json"]),
                                          "bytes": len(outputs["identity-migration.json"])}},
        "limits": ["Selected known outliers, not a corpus error-rate estimate.",
                   "Candidate source partitions and roles require independent source review.",
                   "Structural checks do not establish legal applicability, specialist acceptance or answer quality."]}
    outputs["manifest.json"] = canonical(manifest)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build()
    if args.check:
        existing = {p.relative_to(OUT).as_posix(): p.read_bytes() for p in OUT.rglob("*") if p.is_file()}
        require(existing == outputs, "Generated passage review has drifted")
    else:
        for relative, raw in outputs.items():
            target = OUT / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    print(json.dumps({"status": "verified" if args.check else "built", "cases": 28,
                      "files": len(outputs), "manifest_sha256": digest(outputs["manifest.json"])}))


if __name__ == "__main__":
    main()
