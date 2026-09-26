#!/usr/bin/env python3
"""Build a bounded, source-checked Chapter 60 reading aid without source acquisition."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORING = "domain-profile/reading-help/ch60.json"
OUTPUT = "reading-help-ch60.json"
SCHEMA = "okf-reading-help.v1"
ROLES = {"abbreviation", "source_marker", "condition_number", "note_number",
         "numbered_alternative", "manual_pointer", "word", "unresolved_reference_marker"}
KINDS = {"expansion", "source_definition_pointer", "model_explanation",
         "citation_navigation", "unresolved_reference"}
AUTHORITIES = {"source-backed-expansion-with-project-authored-context",
               "source-pointer-with-project-authored-explanation",
               "project-authored-reading-explanation", "source-defect-observation"}
REVIEW_STATUSES = {"unreviewed", "unresolved"}
# Independent controls for the three context corrections and printed defects.
CRITICAL_BINDINGS = {
    "prescribed-60025": "60025-prescribed",
    "prescribed-60033": "60033-prescribed",
    "60033-definition": "60025-60033-pointer",
    "60033-marker-12": "60033-rate-marker-12",
    "60033-extra-2": "60033-extra-2",
}


def require(test: bool, message: str) -> None:
    if not test:
        raise ValueError(message)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def read_confined(path: str, expected_sha: str | None = None) -> bytes:
    source = (ROOT / path).resolve()
    require(source.is_relative_to(ROOT.resolve()) and source.is_file(), f"Missing or unsafe input: {path}")
    raw = source.read_bytes()
    if expected_sha is not None:
        require(digest(raw) == expected_sha, f"Changed input: {path}")
    return raw


def span(page: bytes, start: int, end: int) -> dict:
    require(0 <= start < end <= len(page), "Invalid page byte span")
    literal = page[start:end].decode("utf-8")
    return {"page_start_utf8": start, "page_end_utf8": end,
            "literal": literal, "literal_sha256": digest(page[start:end])}


def unique_offset(haystack: bytes, needle: str, context: str) -> int:
    raw = needle.encode("utf-8")
    require(raw, f"Empty source anchor: {context}")
    start = haystack.find(raw)
    require(start >= 0 and haystack.find(raw, start + 1) < 0,
            f"Missing or ambiguous source anchor: {context}")
    return start


def build() -> dict:
    authored = json.loads(read_confined(AUTHORING))
    require(authored["schema"] == "okf-dwp-reading-help-authoring.v1", "Wrong authoring schema")
    proposals = {}
    for kind, identity in authored["proposal_inputs"].items():
        raw = read_confined(identity["path"], identity["sha256"])
        records = [json.loads(line) for line in raw.splitlines()]
        key = "candidate_id" if kind == "vocabulary" else "proposal_id"
        ids = [record[key] for record in records]
        require(len(ids) == len(set(ids)), f"Duplicate {kind} proposal ID")
        proposals.update({identifier: record for identifier, record in zip(ids, records)})
    pages = {}
    sources = []
    for source in authored["sources"]:
        sid = source["id"]
        require(sid not in pages, f"Duplicate source: {sid}")
        package = json.loads(read_confined(source["pages_url"], source["pages_sha256"]))
        pdf_path = source["pages_url"].replace("/pages/", "/pdf/").replace(".json", ".pdf")
        read_confined(pdf_path, source["pdf_sha256"])
        require(package["document_id"] == sid and package["source_url"] == source["pdf_url"]
                and package["source_sha256"] == source["pdf_sha256"], f"Source identity mismatch: {sid}")
        page_rows = package["pages"]
        require([row["page"] for row in page_rows] == list(range(1, len(page_rows) + 1)),
                f"Non-contiguous pages: {sid}")
        pages[sid] = {row["page"]: row["text"].encode("utf-8") for row in page_rows}
        sources.append(source)
    passages = []
    passage_spans = {}
    for item in authored["passages"]:
        sid = item["source_id"]
        require(sid in pages, f"Unknown passage source: {sid}")
        require(item["id"] not in passage_spans, f"Duplicate passage: {item['id']}")
        rows = []
        for source_span in item["spans"]:
            number = source_span["page"]
            raw = pages[sid][number]
            start = unique_offset(raw, source_span["start_anchor"], item["id"])
            end = (unique_offset(raw, source_span["end_anchor"], item["id"])
                   if source_span["end_anchor"] is not None else len(raw))
            record = {"page": number, **span(raw, start, end)}
            rows.append(record)
        require(rows and [row["page"] for row in rows] == sorted({row["page"] for row in rows}),
                "Invalid or unordered passage pages")
        passage_spans[item["id"]] = {(sid, row["page"]): row for row in rows}
        passages.append({"id": item["id"], "label": item["label"], "source_id": sid, "spans": rows})
    occurrences = []
    occurrence_ids = set()
    occupied = {}
    for item in authored["occurrences"]:
        identifier = item["id"]
        require(identifier not in occurrence_ids, f"Duplicate occurrence: {identifier}")
        occurrence_ids.add(identifier)
        require(item["role"] in ROLES, f"Invalid role: {identifier}")
        passage = next((p for p in passages if p["id"] == item["passage_id"]), None)
        require(passage is not None, f"Unknown passage for {identifier}")
        sid, number = passage["source_id"], item["page"]
        page = pages[sid][number]
        require((sid, number) in passage_spans[item["passage_id"]],
                f"Occurrence outside selected passage pages: {identifier}")
        parent = passage_spans[item["passage_id"]][(sid, number)]
        context_start = unique_offset(page, item["context"], identifier)
        context = item["context"].encode("utf-8")
        token_start = unique_offset(context, item["literal"], identifier)
        start, end = context_start + token_start, context_start + token_start + len(item["literal"].encode("utf-8"))
        require(parent["page_start_utf8"] <= start < end <= parent["page_end_utf8"],
                f"Occurrence outside passage: {identifier}")
        for first, last, other in occupied.get((sid, number), []):
            require(end <= first or start >= last, f"Overlapping occurrences: {identifier}, {other}")
        occupied.setdefault((sid, number), []).append((start, end, identifier))
        occurrences.append({"id": identifier, "passage_id": item["passage_id"], "source_id": sid,
                            "page": number, "role": item["role"], **span(page, start, end)})
    cards = []
    card_ids = set()
    used_occurrences = set()
    by_occurrence = {o["id"]: o for o in occurrences}
    for item in authored["cards"]:
        identifier = item["id"]
        require(identifier not in card_ids and item["kind"] in KINDS, f"Invalid card: {identifier}")
        card_ids.add(identifier)
        require(item["authority"] in AUTHORITIES and item["review_status"] in REVIEW_STATUSES,
                f"Unrecognised authority or review status: {identifier}")
        if identifier in CRITICAL_BINDINGS:
            require(item["occurrence_ids"] == [CRITICAL_BINDINGS[identifier]],
                    f"Wrong reviewed occurrence binding: {identifier}")
        require(item["occurrence_ids"] and set(item["occurrence_ids"]) <= occurrence_ids,
                f"Unknown occurrence in card: {identifier}")
        require(not (set(item["occurrence_ids"]) & used_occurrences), f"Competing cards: {identifier}")
        used_occurrences.update(item["occurrence_ids"])
        require(item["proposal_ids"] and all(p in proposals for p in item["proposal_ids"]),
                f"Unknown original proposal: {identifier}")
        require(item["target"]["status"] in {"resolved", "unresolved"}, f"Invalid target: {identifier}")
        if item["target"]["status"] == "resolved":
            require(item["target"].get("id") in passage_spans, f"Unresolved local target: {identifier}")
        else:
            require("id" not in item["target"] and "url" not in item["target"],
                    f"Unresolved target presented as link: {identifier}")
        support = []
        require(item["source_support"], f"Missing source support: {identifier}")
        for entry in item["source_support"]:
            sid, number = entry["source_id"], entry["page"]
            require(sid in pages and number in pages[sid], f"Unknown support source: {identifier}")
            page = pages[sid][number]
            start = unique_offset(page, entry["quote"], identifier)
            record = {"source_id": sid, "page": number, **span(page, start, start + len(entry["quote"].encode("utf-8")))}
            record["quote"] = record.pop("literal")
            support.append(record)
        for occurrence_id in item["occurrence_ids"]:
            occurrence = by_occurrence[occurrence_id]
            require(any(entry["source_id"] == occurrence["source_id"]
                        and entry["page"] == occurrence["page"]
                        and entry["page_start_utf8"] <= occurrence["page_start_utf8"]
                        and occurrence["page_end_utf8"] <= entry["page_end_utf8"] for entry in support),
                    f"Card lacks support for its exact occurrence: {identifier}")
        cards.append({key: value for key, value in item.items() if key != "source_support"} | {"source_support": support})
    reviewed_corrections = []
    for correction in authored["review_overlay"]:
        require(correction["proposal_id"] in proposals, "Unknown review overlay proposal")
        require(correction["disposition"] in {"excluded-from-live-pilot", "split-by-occurrence"},
                "Unknown review disposition")
        require(correction["source_support"], "Review correction lacks exact source support")
        support = []
        for entry in correction["source_support"]:
            sid, number = entry["source_id"], entry["page"]
            require(sid in pages and number in pages[sid], "Unknown review source")
            page = pages[sid][number]
            start = unique_offset(page, entry["quote"], correction["issue"])
            record = {"source_id": sid, "page": number,
                      **span(page, start, start + len(entry["quote"].encode("utf-8")))}
            record["quote"] = record.pop("literal")
            support.append(record)
        reviewed_corrections.append({**correction, "source_support": support})
    require({p["id"] for p in passages} == {"dmg-60025", "dmg-60033"}, "Pilot scope changed")
    require(all(o["passage_id"] in {"dmg-60025", "dmg-60033"} for o in occurrences), "Pilot scope escaped")
    return {"schema": SCHEMA, "status": "bounded-unreviewed-reading-aid",
            "scope": authored["scope"], "sources": sources,
            "proposal_inputs": authored["proposal_inputs"], "passages": passages,
            "occurrences": occurrences, "cards": cards,
            "review_overlay": reviewed_corrections, "limitations": authored["limitations"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare generated bytes without writing")
    args = parser.parse_args()
    result = canonical(build())
    target = ROOT / OUTPUT
    if args.check:
        require(target.is_file() and target.read_bytes() == result, "Reading-help projection differs")
        print("Reading-help projection matches frozen inputs and authoring.")
    else:
        target.write_bytes(result)
        print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
