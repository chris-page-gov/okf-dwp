#!/usr/bin/env python3
"""Generate small, inspectable staff evidence review packs from frozen candidates.

Assessor-selected candidates are deliberately separate from observed retrieval.
No expected source is inserted into the retrieval engine or an answer profile.
"""
from __future__ import annotations

import argparse
import json
import re

from build_bundle import ROOT, canonical, digest, pretty
from build_context_discovery import Inputs, require

REGISTRY = "evaluation/staff-questions/cases.json"
RECEIPT = "validation/corpus-questions/receipt.json"
OUTPUT = "evaluation/staff-review"
MAX_EXCERPT = 1800
MAX_PACK_BYTES = 16 * 1024
MAX_EVIDENCE_BYTES = 8 * 1024
LIMITATIONS = [
    "Research review pack, not an answer, an entitlement decision or a complete legal evidence bundle.",
    "Candidate selection is project-authored and unreviewed. It is independent of the retained retrieval run and is not injected into search or Ask OKF.",
    "Each excerpt is an exact bounded substring of frozen machine text, with offsets, a literal hash and a whole-page link. Its surrounding qualifications may be outside the excerpt or on adjacent pages.",
    "Machine extraction can damage tables, footnotes, spacing and reading order. Compare each material proposition with the original PDF, adjacent text and cited legislation.",
    "Original source roles, capture dates and historical limitations remain unchanged. Current applicability and specialist acceptance are not established.",
]


def bounded_excerpt(text, anchor, limit=MAX_EXCERPT):
    require(isinstance(anchor, str) and anchor in text, "Candidate anchor is absent from exact page text")
    require(limit >= len(anchor) and limit > 0, "Excerpt limit cannot contain anchor")
    matches = [match.start() for match in re.finditer(re.escape(anchor), text)]
    # Prefer a source paragraph beginning, otherwise the first exact occurrence.
    starts = [position for position in matches if not text[text.rfind("\n", 0, position) + 1:position].strip()]
    position = (starts or matches)[0]
    start = text.rfind("\n", 0, position) + 1
    if position - start + len(anchor) > limit:
        start = position
    end = min(len(text), start + limit)
    if end < len(text):
        newline = text.rfind("\n", position + len(anchor), end)
        if newline > position + len(anchor):
            end = newline
    literal = text[start:end]
    require(anchor in literal and literal == text[start:end], "Excerpt lost anchor")
    return {"text": literal, "start": start, "end": end, "sha256": digest(literal.encode()),
            "offset_encoding": "Unicode code points; zero-based start-inclusive/end-exclusive",
            "whole_page_characters": len(text), "omitted_before": start, "omitted_after": len(text) - end,
            "anchor": anchor, "anchor_occurrences_on_page": len(matches),
            "method": "exact-anchor-line-start-bounded-substring-v1",
            "completeness": "partial-page-navigation-excerpt"}


def compile_review_packs(root=ROOT):
    inputs, outputs = Inputs(root), {}
    registry = json.loads(inputs.read(REGISTRY))
    run = json.loads(inputs.read(RECEIPT))
    require(run["inputs"]["registry_sha256"] == digest(inputs.read(REGISTRY)), "Retrieval run uses another registry")
    inventory = json.loads(inputs.read(registry["source_inventory"]["path"], registry["source_inventory"]["sha256"]))
    documents = {doc["id"]: doc for doc in inventory["documents"]}
    candidates = {}
    for candidate in registry["source_candidates"]:
        doc = documents[candidate["document_id"]]
        require(doc["sha256"] == candidate["source_sha256"] and doc["pages_sha256"] == candidate["pages_sha256"], "Candidate source binding differs")
        inputs.read(doc["pdf_path"], doc["sha256"], doc["size_bytes"])
        pages = json.loads(inputs.read(doc["pages_path"], doc["pages_sha256"]))["pages"]
        page = pages[candidate["page"] - 1]
        require(page["page"] == candidate["page"] and page["url"] == candidate["url"], "Candidate locator differs")
        require(digest(page["text"].encode()) == candidate["literal_sha256"], "Candidate literal differs")
        excerpt = bounded_excerpt(page["text"], candidate["anchor"])
        adjacent = [{"page": number, "url": doc["url"] + f"#page={number}", "status": "not-selected-for-this-excerpt"}
                    for number in (page["page"] - 1, page["page"] + 1) if 1 <= number <= len(pages)]
        row = {"schema": "okf-review-evidence.v1", "id": candidate["id"], "record_id": candidate["record_id"],
               "route": candidate["route"], "document_id": doc["id"], "title": doc["title"],
               "selection": {"method": "independent-assessor-candidate-from-existing-registry", "status": candidate["status"],
                             "review_note": candidate["review_note"]},
               "excerpt": excerpt, "provenance": {"source_url": page["url"], "source_sha256": doc["sha256"],
                   "pages_path": doc["pages_path"], "pages_sha256": doc["pages_sha256"],
                   "page": page["page"], "page_literal_sha256": candidate["literal_sha256"], "captured_at": candidate["captured_at"],
                   "locator": candidate["locator"], "source_publication_date": candidate["source_publication_date"],
                   "source_role": candidate["source_role"], "legal_status": candidate["legal_status"]},
               "adjacent_pages": adjacent, "assertion_status": "normalized", "authority": "derived-extraction",
               "review_status": "unreviewed", "limitations": LIMITATIONS[2:]}
        candidates[row["id"]] = row
        encoded = pretty(row)
        require(len(encoded) <= MAX_EVIDENCE_BYTES, "One evidence resource exceeds its byte budget")
        outputs[f"{OUTPUT}/evidence/{row['id']}.json"] = encoded
    observed = {row["id"]: row for row in run["cases"]}
    index = []
    for case in registry["cases"]:
        retrieval = observed[case["id"]]
        require(retrieval["question"] == case["question"], "Question wording changed")
        evidence = [candidates[identifier] for identifier in case["candidate_ids"]]
        review = {"schema": "okf-staff-evidence-review.v1", "id": case["id"], "question": case["question"],
                  "section": case["section"], "duplicate_of": case["duplicate_of"], "evidence_status": "insufficient",
                  "review_status": "awaiting-specialist-review", "ai_answer": None,
                  "required_evidence": [{"requirement": item, "status": "not-yet-established"} for item in case["required_evidence"]],
                  "ambiguities": case["ambiguities"], "scope_gaps": case["scope_gaps"],
                  "candidate_evidence": [{"id": item["id"], "record_id": item["record_id"],
                      "path": f"../evidence/{item['id']}.json",
                      "bytes": len(outputs[f"{OUTPUT}/evidence/{item['id']}.json"]),
                      "sha256": digest(outputs[f"{OUTPUT}/evidence/{item['id']}.json"]),
                      "source_url": item["provenance"]["source_url"], "page": item["provenance"]["page"],
                      "selection_status": item["selection"]["status"],
                      "review_note": item["selection"]["review_note"]} for item in evidence],
                  "observed_retrieval": {"receipt_path": RECEIPT, "receipt_sha256": digest(inputs.read(RECEIPT)),
                      "version": run["version"], "context_id": retrieval["context_id"],
                      "candidate_ids_retained": retrieval["independently_located_candidates_retained"],
                      "candidate_documents_retained": retrieval["candidate_documents_retained"],
                      "selected_records": retrieval["selected_records"], "package_bytes": retrieval["package_bytes"],
                      "truncated": retrieval["package_truncated"], "evidence_status": retrieval["evidence_status"],
                      "note": "Historical observed retrieval, not a new evaluation or an answer-quality grade."},
                  "review_checklist": [
                      "Resolve benefit, variant, time period and claimant circumstances without inventing missing facts.",
                      "Check each exact source passage and its adjacent pages against the official PDF.",
                      "Locate every condition, exception, qualification and cross-reference needed for the declared question.",
                      "Reconcile relevant legislation, amendments, ADM/DMG regime and effective dates.",
                      "Record each supported claim against exact evidence IDs, with contradicting or missing evidence separately.",
                      "Keep the answer insufficient until evidence requirements and claim-level assessment justify a bounded conclusion."],
                  "limitations": LIMITATIONS}
        raw = pretty(review)
        require(len(raw) <= MAX_PACK_BYTES, "Review pack exceeds its byte budget; partition explicitly")
        outputs[f"{OUTPUT}/cases/{case['id']}.json"] = raw
        lines = [f"# {case['id']}: {case['question']}", "", "**Awaiting specialist review · evidence insufficient · no AI answer.**", "",
                 "This is a review aid made from independently located source candidates. It does not alter Ask OKF retrieval.", "",
                 "## Review needs", ""]
        lines += ["- " + item for item in case["required_evidence"] + case["ambiguities"]]
        lines += ["", "## Candidate evidence", ""]
        for item in evidence:
            lines += [f"### {item['id']}: {item['title']} — PDF page {item['provenance']['page']}", "",
                      f"[Official source]({item['provenance']['source_url']}) · [Exact excerpt and hashes](../evidence/{item['id']}.json)", "",
                      item["selection"]["review_note"], "", "```text", item["excerpt"]["text"].replace("```", "``\u200b`"), "```", "",
                      f"Excerpt omits {item['excerpt']['omitted_before']:,} characters before and {item['excerpt']['omitted_after']:,} after on this page. Check surrounding text and adjacent pages.", ""]
        lines += ["## Observed retrieval", "", f"The retained run selected {retrieval['selected_records']} records, using {retrieval['package_bytes']:,} bytes. "
                  f"It retained {len(retrieval['independently_located_candidates_retained'])} of {len(evidence)} independently located candidate pages. "
                  "This measures candidate overlap, not substantive correctness.", "", "## Review checklist", ""]
        lines += ["- [ ] " + item for item in review["review_checklist"]]
        lines += ["", "## Boundaries", ""] + ["- " + value for value in LIMITATIONS]
        outputs[f"{OUTPUT}/cases/{case['id']}.md"] = ("\n".join(lines) + "\n").encode()
        index.append({"id": case["id"], "question": case["question"], "section": case["section"], "duplicate_of": case["duplicate_of"],
                      "path": f"cases/{case['id']}.json", "bytes": len(raw), "sha256": digest(raw),
                      "candidate_pages": len(evidence), "retained_candidate_pages": len(retrieval["independently_located_candidates_retained"]),
                      "review_status": "awaiting-specialist-review", "evidence_status": "insufficient"})
    manifest = {"schema": "okf-staff-review-manifest.v1", "question_occurrences": len(index),
                "unique_questions": len({row["question"] for row in index}), "unique_candidate_pages": len(candidates),
                "source_run": {"path": RECEIPT, "sha256": digest(inputs.read(RECEIPT)), "version": run["version"]},
                "cases": index, "maximum_pack_bytes": max(row["bytes"] for row in index),
                "minimum_pack_bytes": min(row["bytes"] for row in index), "limitations": LIMITATIONS}
    manifest["budgets"] = {"pack_bytes": MAX_PACK_BYTES, "evidence_resource_bytes": MAX_EVIDENCE_BYTES,
                           "excerpt_characters": MAX_EXCERPT, "overflow_policy": "fail-closed-no-silent-truncation"}
    outputs[f"{OUTPUT}/manifest.json"] = pretty(manifest)
    lines = ["# Staff evidence review packs", "", "40 question occurrences, 39 unique questions. All remain insufficient and awaiting specialist review.", "",
             "Each pack separates independently located candidate passages from what Ask OKF actually retrieved in the retained run. "
             "Exact bounded quotations, source hashes, neighbouring-page links and a checklist make review practical without returning every whole page.", "",
             "| Case | Question | Candidate pages | Retained candidate pages |", "|---|---|---:|---:|"]
    lines += [f"| [{row['id']}](cases/{row['id']}.md) | {row['question'].replace('|', '&#124;')} | {row['candidate_pages']} | {row['retained_candidate_pages']} |" for row in index]
    lines += ["", "[Machine-readable pack manifest](manifest.json)", ""] + ["- " + item for item in LIMITATIONS]
    outputs[f"{OUTPUT}/README.md"] = ("\n".join(lines) + "\n").encode()
    inputs.read("scripts/build_staff_review_packs.py")
    outputs["validation/staff-review/build.json"] = pretty({"schema": "okf-staff-review-build.v1",
        "inputs": sorted(inputs.files.values(), key=lambda row: row["path"]),
        "outputs": [{"path": path, "bytes": len(raw), "sha256": digest(raw)} for path, raw in sorted(outputs.items())]})
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = compile_review_packs()
    for name, raw in outputs.items():
        path = ROOT / name
        if args.check:
            require(path.is_file() and path.read_bytes() == raw, "Stale staff review pack: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(json.dumps({"status": "verified" if args.check else "built", "files": len(outputs),
                      **{key: value for key, value in json.loads(outputs[f"{OUTPUT}/manifest.json"]).items()
                         if key in {"question_occurrences", "unique_candidate_pages", "maximum_pack_bytes", "minimum_pack_bytes"}}}))


if __name__ == "__main__":
    main()
