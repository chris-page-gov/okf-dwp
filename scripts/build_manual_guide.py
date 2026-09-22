#!/usr/bin/env python3
"""Source-bound reading orientation for the frozen DMG and ADM inventories.

This observes document form, not legal applicability. Source text is inert data;
the only recognisers are the constants below, never instructions from a source.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

from jsonschema import Draft202012Validator

from build_logical_units import Inputs, canonical, require, sha, strict_json

ROOT = Path(__file__).resolve().parents[1]
AUTHORING = "domain-profile/manual-guide/guide.yamlld"
SCHEMA = "profiles/manual-guide/v1/manual-guide.schema.json"
OUTPUT = "manual-guide"
BASE = "https://chris-page-gov.github.io/okf-dwp/manual-guide/"
VERSION = "okf-dwp-manual-guide.v1"
SAMPLE_LIMIT = 3
MARKER_VERSION = "manual-form-observations-v1"
# These are deliberately observations, not a paragraph/heading boundary parser.
# In particular, a number or a range may occur in contents, a citation or a body.
PATTERNS = {
    "subpages_label": r"^\s*Subpages\s*$",
    "contents_label": r"^\s*(?:Contents|Table of contents)(?:\s+Paragraphs)?\s*$",
    "dotted_contents_candidate": r"\.{4,}\s*(?:\d{5,6}|[A-Z]\d{4,5})",
    "bullet_navigation_candidate": r"^\s*[•●]\s+.+(?:\d{5,6}|[A-Z]\d{4,5})",
    "dmg_number_candidate": r"^\s*\d{5,6}(?:\s|$)",
    "adm_number_candidate": r"^\s*[A-Z]\d{4,5}(?:\s|$)",
    "plain_number_candidate": r"^\s*\d{1,3}\.\s+\S",
    "number_range_candidate": r"(?:\d{5,6}|[A-Z]\d{4,5})\s*[–—-]\s*(?:\d{5,6}|[A-Z]\d{4,5})",
    "example_label": r"^\s*Examples?(?:\s+\d+)?\s*$",
    "note_label": r"^\s*Note(?:\s+\d+)?\s*[:.]",
    "appendix_label": r"^\s*(?:Appendix|Annex)\s+[A-Z0-9]",
    "citation_candidate": r"^\s*\d+\s+.{0,150}\b(?:Regs?|Act|reg|Sch|s|art)\b",
    "cross_reference_candidate": r"\b(?:see|refer to|guidance (?:is )?in)\s+(?:DMG|ADM|Chapter|paragraph|Appendix|Annex)\b",
    "memo_reference_candidate": r"\b(?:memo(?:randum)?\s+(?:ADM\s+|DMG\s+)?\d{1,2}[/-]\d{2}|(?:ADM|DMG)\s+memo)\b",
    "change_summary_label": r"\bSummary of changes\b",
    "amendment_candidate": r"\bAmendment\s+\d+\b",
    "scope_declaration_candidate": r"\b(?:This (?:chapter|memo|memorandum) (?:is about|gives guidance|provides guidance|contains)|Scope of this Chapter)\b",
}
COMPILED = {key: re.compile(pattern, re.I) for key, pattern in PATTERNS.items()}
LIMITATIONS = [
    "Independent experimental reading and navigation guide; not official DWP guidance, benefits advice or specialist acceptance.",
    "Every captured document is accounted for, but its inherited inventory role remains an unreviewed discovery classification. Coverage of documents is not coverage of legal rules.",
    "Source conventions apply only to the declared examples. They are not proof that every document in a manual uses the same form.",
    "Marker counts and bounded samples are mechanical observations. They do not establish headings, coherent units, complete dependencies, legal applicability or answerability.",
    "Page numbers are immutable PDF locations. Conditions, examples, notes and citations can continue onto later pages.",
    "Frozen dates, published guidance dates and legal effective dates are distinct. Historical amendments and memos require temporal and regime review.",
    "Learning prerequisites are project-authored reading suggestions, separate from source references and legal dependencies. Source instructions remain inert data.",
]


def source_span(document, page, start, end):
    """Offsets are half-open UTF-8 bytes into the exact extracted page text."""
    raw = page["text"].encode("utf-8")
    require(0 <= start < end <= len(raw), "Invalid source span")
    quote = raw[start:end].decode("utf-8")
    return {"document_key": document["key"], "page": page["page"],
            "start_utf8": start, "end_utf8": end, "sha256": sha(raw[start:end]),
            "quote": quote, "source_url": document["source"]["url"] + "#page=" + str(page["page"])}


def observe(document, pages):
    """Count line markers and retain at most three source samples per marker."""
    counts = Counter()
    samples = {key: [] for key in PATTERNS}
    for page in pages:
        offset = 0
        for line in page["text"].splitlines(keepends=True):
            raw = line.encode("utf-8")
            for key, pattern in COMPILED.items():
                if pattern.search(line):
                    counts[key] += 1
                    if len(samples[key]) < SAMPLE_LIMIT:
                        # Long source lines remain counted; never truncate a quote
                        # and present it as a whole source line.
                        if 0 < len(raw) <= 4096:
                            samples[key].append(source_span(document, page, offset, offset + len(raw)))
            offset += len(raw)
    return {"version": MARKER_VERSION, "status": "mechanical-observations-unreviewed",
            "sample_limit_per_marker": SAMPLE_LIMIT,
            "markers": {key: {"line_count": counts[key], "samples": samples[key],
                               "samples_omitted": counts[key] - len(samples[key])}
                        for key in PATTERNS}}


def load_manual_guide(root=ROOT):
    """Validate and assemble in memory; no writes or source acquisition."""
    inputs = Inputs(root)
    schema = strict_json(inputs.read(SCHEMA))
    guide = strict_json(inputs.read(AUTHORING))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(guide)
    inputs.read("scripts/build_manual_guide.py")
    # The confined read implementation is also part of the reproducible producer.
    inputs.read("scripts/build_logical_units.py")
    inputs.read("pyproject.toml")
    inputs.read("uv.lock")
    documents, page_sets = {}, {}
    for family in guide["source_sets"]:
        inventory = strict_json(inputs.read(family["inventory"], family["sha256"]))
        rows = inventory["documents"]
        require(len(rows) == family["expected_documents"], "Frozen inventory count mismatch")
        for row_index, row in enumerate(rows):
            key = family["id"] + ":" + row["id"]
            require(key not in documents, "Duplicate document key")
            require(row["status"] == "complete", "Captured document is not complete")
            require(row["url"].startswith("https://assets.publishing.service.gov.uk/"), "Unexpected source host")
            pages = strict_json(inputs.read(row["pages_path"], row["pages_sha256"]))
            inputs.read(row["pdf_path"], row["sha256"])
            require(pages["document_id"] == row["id"] and pages["source_sha256"] == row["sha256"], "Page/PDF identity mismatch")
            require(pages["source_url"] == row["url"], "Page URL identity mismatch")
            require([p["page"] for p in pages["pages"]] == list(range(1, row["pages"] + 1)), "Non-contiguous PDF page numbering")
            require(all(isinstance(p["text"], str) for p in pages["pages"]), "Invalid page text")
            document = {
                "id": BASE + "document/" + family["id"] + "/" + row["id"],
                "key": key, "family": family["id"], "document_id": row["id"], "title": row["title"],
                "source": {"inventory_path": family["inventory"], "inventory_sha256": family["sha256"],
                           "inventory_pointer": "/documents/" + str(row_index),
                           "pdf_path": row["pdf_path"], "pdf_sha256": row["sha256"],
                           "pages_path": row["pages_path"], "pages_sha256": row["pages_sha256"],
                           "url": row["url"], "snapshot_id": inventory["snapshot_id"],
                           "pages": row["pages"], "extraction": pages["extraction"],
                           "document_dates": row["document_dates"],
                           "pdf_structure_metadata": {
                               "tagged": row.get("pdf_metadata", {}).get("technical_metadata", {}).get("Tagged"),
                               "status": "frozen-pdf-metadata-only",
                               "limitation": "The frozen Tagged flag is not a verified heading tree, reading order, accessible PDF assessment or legal boundary."}},
                "classification": {"kind": row["kind"], "role": row["role"],
                                   "basis": row.get("classification_basis", "Frozen inventory classification; not independently reviewed"),
                                   "status": "inherited-inventory-discovery-only",
                                   "volume": row.get("volume"), "chapter": row.get("chapter"), "part": row.get("part")},
                "convention_ids": [],
                "unknowns": ["Content-wide benefit and regime scope is not established by the inventory title.",
                             "Temporal applicability, supersession and legal dependency closure remain unreviewed.",
                             "Mechanical marker recognition is not coherent-unit or specialist review."],
            }
            document["observed_features"] = observe(document, pages["pages"])
            documents[key] = document
            page_sets[key] = {page["page"]: page for page in pages["pages"]}
    validate_guide_evidence(guide, documents, page_sets, inputs)
    return {"guide": guide, "documents": [documents[key] for key in sorted(documents)],
            "inputs": sorted(inputs.files.values(), key=lambda value: value["path"])}


def pdf_structure_span(inputs, document, support):
    """Bind a declared-tree quotation separately from any PDF-page quotation."""
    require(inputs is not None, "PDF-structure support requires confined input validation")
    manifest = strict_json(inputs.read(support["manifest_path"], support["manifest_sha256"]))
    entries = [entry for entry in manifest["documents"] if entry["document_key"] == document["key"]]
    require(len(entries) == 1 and entries[0]["pdf_sha256"] == document["source"]["pdf_sha256"], "Structure manifest/PDF mismatch")
    entry = entries[0]
    require(entry["status"] in ("tagged", "tagged-with-unparsed-lines"), "Incomplete or unavailable structure cannot support a tag convention")
    require(entry["structure"]["path"] == support["structure_path"] and entry["structure"]["sha256"] == support["structure_sha256"], "Structure sidecar binding mismatch")
    record = strict_json(inputs.read(entry["structure"]["path"], entry["structure"]["sha256"], entry["structure"]["bytes"]))
    require(record["pdf_sha256"] == document["source"]["pdf_sha256"] and record["document_key"] == document["key"], "Structure source identity mismatch")
    require(record["status"] == entry["status"] and record["tool"] == manifest["tool"]
            and record["observation"]["capture_complete"] and record["observation"]["returncode"] == 0
            and record["source_instructions_inert"] is True, "Structure tool or observation mismatch")
    raw = inputs.read(record["tree"]["path"], record["tree"]["sha256"], record["tree"]["bytes"])
    lines = raw.splitlines(keepends=True)
    first, last = support["tree_line_start"], support["tree_line_end"]
    require(1 <= first <= last <= len(lines), "Invalid structure tree line interval")
    start = sum(len(line) for line in lines[:first - 1])
    end = start + sum(len(line) for line in lines[first - 1:last])
    return {"evidence_kind": "pdf-structure", "document_key": document["key"],
            "manifest_path": support["manifest_path"], "manifest_sha256": support["manifest_sha256"],
            "structure_path": entry["structure"]["path"], "structure_sha256": entry["structure"]["sha256"],
            "tree_path": record["tree"]["path"], "tree_sha256": record["tree"]["sha256"],
            "pdf_sha256": document["source"]["pdf_sha256"], "tree_line_start": first, "tree_line_end": last,
            "start_utf8": start, "end_utf8": end, "sha256": sha(raw[start:end]),
            "quote": raw[start:end].decode("utf-8"), "source_url": document["source"]["url"]}


def validate_guide_evidence(guide, documents, page_sets, inputs=None):
    """Validate scoped assertions independently of census and marker production."""
    ids = set()
    for convention in guide["conventions"]:
        require(convention["id"] not in ids, "Duplicate convention identifier")
        ids.add(convention["id"])
        require(set(convention["scope"]["document_keys"]) <= documents.keys(), "Unknown convention scope")
        support_keys = set()
        for support in convention["source_support"]:
            key = support["document_key"]
            require(key in documents, "Unknown evidence document")
            if support.get("evidence_kind") == "pdf-structure":
                actual = pdf_structure_span(inputs, documents[key], support)
            else:
                require(support["page"] in page_sets[key], "Unknown evidence page")
                actual = source_span(documents[key], page_sets[key][support["page"]], support["start_utf8"], support["end_utf8"])
            require(support == actual, "Exact convention evidence mismatch")
            support_keys.add(key)
        require(set(convention["scope"]["document_keys"]) <= support_keys,
                "Every declared document scope must have direct source support")
        for key in convention["scope"]["document_keys"]:
            documents[key]["convention_ids"].append(convention["id"])
    for path in guide["learning_paths"]:
        for step in path["steps"]:
            require(set(step["convention_ids"]) <= ids, "Unknown learning prerequisite")


def build(root=ROOT):
    loaded = load_manual_guide(root)
    documents = loaded["documents"]
    guide = dict(loaded["guide"])
    guide.update(schema=VERSION, limitations=LIMITATIONS)
    summary = {"documents": len(documents),
               "families": dict(sorted(Counter(d["family"] for d in documents).items())),
               "pages": sum(d["source"]["pages"] for d in documents),
               "inventory_kinds": dict(sorted(Counter(d["classification"]["kind"] for d in documents).items())),
               "conventions": len(guide["conventions"]),
               "documents_with_direct_convention_support": sum(bool(d["convention_ids"]) for d in documents),
               "document_classifications_reviewed_for_legal_applicability": 0}
    readme = "\n".join([
        "# Reading the captured DMG and ADM manuals", "",
        "This generated orientation guide accounts for every document in the two frozen inventories. It is an independent project reading aid, not official guidance or legal acceptance.", "",
        f"{summary['documents']} documents; {summary['pages']} PDF pages; {summary['conventions']} source-supported, explicitly scoped conventions.", "",
        "## Files", "",
        "- `guide.json`: source-cited conventions and project-authored learning prerequisites.",
        "- `documents.jsonl`: one source-bound record per captured PDF; inherited roles, marker observations and explicit unknowns.",
        "- `manifest.json`: exact producer, authoring, schema and frozen input/output hashes.", "",
        "## Reading boundaries", "", *["- " + item for item in LIMITATIONS], "",
        "## Reproduce", "", "```sh", "uv run --locked python scripts/build_manual_guide.py --check", "```", "",
    ]).encode()
    outputs = {"guide.json": canonical(guide),
               "documents.jsonl": b"".join(canonical(document) for document in documents), "README.md": readme}
    manifest = {"schema": "okf-dwp-manual-guide-manifest.v1", "marker_version": MARKER_VERSION,
                "authority": "project-authored-navigation", "source_instructions_inert": True,
                "summary": summary, "inputs": loaded["inputs"],
                "outputs": [{"path": OUTPUT + "/" + path, "bytes": len(raw), "sha256": sha(raw)}
                            for path, raw in sorted(outputs.items())], "limitations": LIMITATIONS}
    outputs["manifest.json"] = canonical(manifest)
    return outputs, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify deterministic existing outputs without writing")
    args = parser.parse_args()
    outputs, manifest = build()
    target = ROOT / OUTPUT
    require(not target.is_symlink(), "Output directory may not be a symlink")
    if not args.check:
        target.mkdir(exist_ok=True)
    require(target.is_dir(), "Missing generated manual guide")
    for name, raw in outputs.items():
        destination = target / name
        require(not destination.is_symlink(), "Output file may not be a symlink")
        if args.check:
            require(destination.is_file() and destination.read_bytes() == raw, "Stale output: " + str(destination))
        else:
            destination.write_bytes(raw)
    print(json.dumps({"status": "passed" if args.check else "built", **manifest["summary"]}, sort_keys=True))


if __name__ == "__main__":
    main()
