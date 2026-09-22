#!/usr/bin/env python3
"""Additive, byte-accounted logical candidates from the frozen DMG/ADM census.

Number recognition is a navigation proposal, not a claim that a rule is complete.
Only separately authored, hash-bound overrides declare reviewed excerpt boundaries.
No source, previous corpus, semantic profile or acquisition artefact is rewritten.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = "logical-units"
CONFIG = "context/corpus-sources.json"
OVERRIDES = "domain-profile/logical-units/overrides.json"
BASE = "https://chris-page-gov.github.io/okf-dwp/"
REPO = "https://github.com/chris-page-gov/okf-dwp"
OGL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
VERSION = "logical-boundaries-v1"
MAX_FILE = 64 * 1024 * 1024
MAX_SHARD = 4 * 1024 * 1024
TARGET_SHARD = 1024 * 1024
MAX_UNIT_BYTES = 96000
# Thirty-one distinct page URLs plus the extraction URL fit ContextRecord's
# existing 32-entry provenance bound; the shared unit format allows 32 spans.
MAX_SPANS = 31
KINDS = {"rule": "paragraph", "rule-group": "compound", "reference": "cross-reference",
         "navigation": "section", "reserved": "section", "definition": "definition",
         "table": "table", "exception": "exception", "section": "section",
         "paragraph": "paragraph", "compound": "compound"}
LIMITATIONS = [
    "Independent experimental source navigation, not official DWP guidance, benefits advice or an entitlement decision.",
    "Automatic paragraph and heading recognition is an uncertain structural proposal; it does not establish complete rules, legal applicability or semantic dependency closure.",
    "Every extracted source byte is assigned once to a unit or explicitly empty-text accounting. Empty or damaged extraction is not proof of a blank or complete PDF page. No OCR or source repair is performed.",
    "Author-declared completeness means complete within the declared excerpt boundary only. Agent boundary review is not specialist, legal or human acceptance.",
    "Automatic candidates retain text until the next candidate start, including intervening examples, lists, notes and citations, but headings and reading order may be misassigned. Uncertain and bounded fallback material remains visible.",
    "Capture dates, source document dates and legal effective dates remain distinct. Historical and memo material is retained without resolving its contemporary applicability.",
    "Page requirements from older semantic releases are not satisfied merely by retrieving a fragment of that page. Source instructions remain inert data.",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode() + b"\n"


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    def finite(value):
        number = float(value)
        require(math.isfinite(number), "Non-finite JSON")
        return number
    return json.loads(raw, object_pairs_hook=pairs, parse_float=finite,
                      parse_constant=lambda _: require(False, "Non-finite JSON"))


class Inputs:
    """Confined regular-file reads; hashes bind actual bytes before processing."""
    def __init__(self, root):
        self.root = Path(root).absolute()
        require(not self.root.is_symlink(), "Input root is a symlink")
        self.files = {}

    def read(self, relative, expected_sha=None, expected_size=None, limit=MAX_FILE):
        require(isinstance(relative, str) and relative and "\\" not in relative, "Invalid input path")
        path = PurePosixPath(relative)
        require(not path.is_absolute() and all(p not in ("", ".", "..") for p in relative.split("/")), "Unsafe input path")
        current = self.root
        for part in path.parts:
            current /= part
            require(not current.is_symlink(), "Input symlink is not admitted")
        before = current.lstat()
        require(stat.S_ISREG(before.st_mode) and before.st_size <= limit, "Input is not a bounded regular file")
        fd = os.open(current, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as handle:
            opened = os.fstat(handle.fileno())
            require(stat.S_ISREG(opened.st_mode) and (opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino), "Input changed during admission")
            raw = handle.read(limit + 1)
        require(len(raw) <= limit and len(raw) == before.st_size, "Input size changed or exceeds bound")
        digest = sha(raw)
        require(expected_sha is None or digest == expected_sha, "Input hash mismatch: " + relative)
        require(expected_size is None or len(raw) == expected_size, "Input size mismatch: " + relative)
        self.files[relative] = {"path": relative, "sha256": digest, "bytes": len(raw)}
        return raw


def gzip_bytes(raw):
    result = bytearray(gzip.compress(raw, compresslevel=9, mtime=0))
    result[9] = 255
    return bytes(result)


def binding(path, raw, decoded=None):
    result = {"path": path, "sha256": sha(raw), "bytes": len(raw)}
    if decoded is not None:
        require(len(decoded) <= MAX_SHARD, "Decoded unit shard exceeds 4 MiB")
        result.update(encoding="gzip", decoded_sha256=sha(decoded), decoded_bytes=len(decoded))
    return result


def page_structure(text, family, chapter=None):
    """Return candidates with byte offsets; never silently repair source labels."""
    lines = text.splitlines(keepends=True)
    contents = bool(re.search(r"(?im)^\s*(?:contents|table of contents)\s*$", text)) or len(re.findall(r"\.{4,}", text)) >= 3
    starts, headings, reserved, rejected = [], [], [], []
    offset = 0
    pattern = r"^[ \t]*(?P<label>\d{5,6}|[A-Z]\d{4,5})(?P<tail>[^\r\n]*)"
    for line in lines:
        stripped = line.strip()
        hit = re.match(pattern, line)
        if hit:
            label, tail = hit.group("label"), hit.group("tail")
            correct_family = (label.isdigit() if family == "dmg" else not label.isdigit())
            if chapter is not None:
                prefix = str(chapter).upper()
                correct_family = correct_family and (label.startswith(f"{int(chapter):02d}") if family == "dmg" and str(chapter).isdigit() else label.startswith(prefix))
            is_range = bool(re.match(r"\s*[–—-]\s*(?:\d{5,6}|[A-Z]\d{4,5})", tail))
            body = bool(re.match(r"[ \t]+[A-Za-z\[“‘(]", tail))
            citation = bool(re.match(r"\s+(?:et seq|for guidance|and\s+(?:\d|[A-Z]\d))\b", tail, re.I))
            if correct_family and is_range:
                reserved.append({"start_utf8": offset, "label": label, "literal": stripped, "status": "range-or-reserved-candidate"})
            if correct_family and not contents and (body or is_range) and not citation:
                starts.append({"start_utf8": offset, "label": label, "kind": "reserved" if is_range else "rule"})
            elif correct_family:
                rejected.append({"start_utf8": offset, "label": label,
                                 "reason": "contents-candidate" if contents else ("reference-like-line" if citation else "number-line-without-recognised-body"),
                                 "literal": stripped})
        if (stripped and len(stripped) <= 140 and not hit and not re.search(r"[.;,:]$", stripped)
                and not re.search(r"\.{4,}|^\d+[.)]|^Example(?:\s+\d+)?$", stripped, re.I)
                and re.match(r"^[A-Z“‘]", stripped) and len(line) - len(line.lstrip()) <= 4):
            headings.append({"start_utf8": offset, "literal": stripped, "status": "machine-heading-candidate"})
        offset += len(line.encode())
    return {"contents_candidate": contents, "starts": starts, "headings": headings,
            "reserved_candidates": reserved, "unsegmented_number_candidates": rejected}


def source_spans(pages, start, end):
    """Map a document's concatenated source bytes to non-empty page spans."""
    result, offset = [], 0
    for page in pages:
        raw = page["text"].encode()
        low, high = max(0, start - offset), min(len(raw), end - offset)
        if low < high:
            fragment = raw[low:high]
            fragment.decode("utf-8", errors="strict")
            result.append({"page": page["page"], "start_utf8": low, "end_utf8": high, "literal_sha256": sha(fragment)})
        offset += len(raw)
        if offset >= end:
            break
    require(sum(row["end_utf8"] - row["start_utf8"] for row in result) == end - start, "Unmapped source interval")
    return result


def split_interval(pages, start, end):
    """Bound uncertain candidates without pretending the fragments are rules."""
    spans = source_spans(pages, start, end)
    chunks, chunk, size = [], [], 0
    for span in spans:
        raw = pages[span["page"] - 1]["text"].encode()
        cursor = span["start_utf8"]
        while cursor < span["end_utf8"]:
            if chunk and (len(chunk) >= MAX_SPANS or size >= MAX_UNIT_BYTES - 4):
                chunks.append(chunk)
                chunk, size = [], 0
            room = MAX_UNIT_BYTES - size - (1 if chunk else 0)
            stop = min(span["end_utf8"], cursor + room)
            while stop > cursor:
                try:
                    raw[cursor:stop].decode("utf-8", errors="strict")
                    break
                except UnicodeDecodeError:
                    stop -= 1
            require(stop > cursor, "Cannot split UTF-8 source safely")
            item = {"page": span["page"], "start_utf8": cursor, "end_utf8": stop, "literal_sha256": sha(raw[cursor:stop])}
            chunk.append(item)
            size += stop - cursor + (1 if len(chunk) > 1 else 0)
            cursor = stop
    if chunk:
        chunks.append(chunk)
    return chunks


def check_override(doc, pages, specification, inventory_sha):
    for key, expected in [("source_sha256", doc["sha256"]), ("pages_sha256", doc["pages_sha256"]), ("inventory_sha256", inventory_sha)]:
        require(specification.get(key) == expected, "Override source binding mismatch: " + key)
    for key, source_key in [("pages_path", "pages_path"), ("pdf_path", "pdf_path"), ("source_url", "url"), ("observed_at", "observed_at")]:
        if key in specification:
            require(specification[key] == doc.get(source_key), "Override source metadata mismatch: " + key)
    if "source_dates" in specification:
        require(specification["source_dates"].get("document") == doc.get("document_dates")
                and specification["source_dates"].get("publication_page_updated_at") == doc.get("publication_updated_at"),
                "Override source dates mismatch; capture must not become effective date")
    require(isinstance(specification.get("units"), list), "Override units must be a list")
    offsets, total = {}, 0
    for page in pages:
        offsets[page["page"]] = total
        total += len(page["text"].encode())
    units, keys, seen = [], set(), []
    for unit in specification["units"]:
        key = unit.get("key")
        require(isinstance(key, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", key) and key not in keys, "Invalid or duplicate authored unit key")
        keys.add(key)
        require(unit.get("kind") in KINDS and unit.get("review_status") == "agent-reviewed-boundary-only"
                and unit.get("specialist_review") == "not-reviewed", "Override cannot imply specialist acceptance")
        require(isinstance(unit.get("label"), str) and 0 < len(unit["label"]) <= 1000, "Missing or oversized unit label")
        require(isinstance(unit.get("review_note"), str) and unit["review_note"], "Override needs a boundary review note")
        require(unit.get("completeness", "unresolved") in ("unresolved", "complete-within-declared-boundary"), "Invalid authored completeness")
        require(isinstance(unit.get("paragraph_labels"), list) and len(unit["paragraph_labels"]) <= 100
                and all(isinstance(label, str) and re.fullmatch(r"(?:\d{5,6}|[A-Z]\d{4,5})", label)
                        for label in unit["paragraph_labels"]), "Invalid authored paragraph labels")
        spans = unit.get("spans")
        require(isinstance(spans, list) and 0 < len(spans) <= MAX_SPANS, "Authored unit span bound")
        previous, first = None, None
        for span in spans:
            number, low, high = (span.get(k) for k in ("page", "start_utf8", "end_utf8"))
            require(all(isinstance(x, int) and not isinstance(x, bool) for x in (number, low, high)) and 1 <= number <= len(pages), "Invalid override page/offset")
            raw = pages[number - 1]["text"].encode()
            require(0 <= low < high <= len(raw), "Override source range outside page")
            fragment = raw[low:high]
            fragment.decode("utf-8", errors="strict")
            require(sha(fragment) == span.get("literal_sha256"), "Override literal hash mismatch")
            absolute = offsets[number] + low
            require(previous is None or previous == absolute, "Override source spans must be contiguous and ordered")
            first = absolute if first is None else first
            previous = offsets[number] + high
        require(previous - first + len(spans) - 1 <= MAX_UNIT_BYTES, "Authored unit is too large; retain complete evidence and report the bound")
        literal = "\n".join(pages[s["page"] - 1]["text"].encode()[s["start_utf8"]:s["end_utf8"]].decode() for s in spans)
        require(all(re.search(r"\b" + re.escape(label) + r"\b", literal) for label in unit["paragraph_labels"]),
                "Authored paragraph label is absent from its bound source excerpt")
        for low, high in seen:
            require(previous <= low or first >= high, "Authored units overlap")
        seen.append((first, previous))
        units.append({**unit, "start": first, "end": previous, "authored": True})
    for unit in units:
        for field in ("support_unit_keys", "reference_unit_keys"):
            require(isinstance(unit.get(field, []), list) and all(key in keys and key != unit["key"] for key in unit.get(field, [])), "Missing or reflexive authored unit dependency")
    return sorted(units, key=lambda row: row["start"])


def make_record(family, doc, pages, unit, version):
    fragments, spans, provenance, unit_offset = [], [], [], 0
    extraction_url = REPO + "/blob/main/" + doc["pages_path"]
    observed = doc.get("observed_at") or doc.get("http", {}).get("observed_at")
    require(isinstance(observed, str) and observed, "Missing capture observation")
    for number, item in enumerate(unit["spans"]):
        page = pages[item["page"] - 1]
        raw = page["text"].encode()
        low, high = item["start_utf8"], item["end_utf8"]
        fragment = raw[low:high]
        require(sha(fragment) == item["literal_sha256"], "Unit literal source drift")
        fragments.append(fragment.decode("utf-8", errors="strict"))
        unit_offset += 1 if number else 0
        spans.append({"source_url": page["url"], "source_sha256": doc["sha256"],
                      "extraction_url": extraction_url, "extraction_sha256": doc["pages_sha256"],
                      "locator": f"pages[{page['page'] - 1}].text", "source_text_sha256": sha(raw), "source_text_bytes": len(raw),
                      "source_start": low, "source_end": high, "unit_start": unit_offset,
                      "unit_end": unit_offset + len(fragment), "literal_sha256": sha(fragment)})
        unit_offset += len(fragment)
        if not any(row["url"] == page["url"] for row in provenance):
            provenance.append({"url": page["url"], "source_sha256": doc["sha256"], "locator": f"PDF page {page['page']}", "captured_at": observed})
    text = "\n".join(fragments)
    digest = sha(text.encode())
    provenance.append({"url": extraction_url, "source_sha256": doc["pages_sha256"],
                       "locator": "Ordered page-text spans in evidence_unit", "captured_at": doc.get("extraction_observed_at") or observed})
    for item in provenance:
        item["literal_sha256"] = digest
    # Excerpt identity includes its exact ordered boundary. An override must not
    # reuse an old unit IRI for different text merely because its label is stable.
    boundary = sha(canonical(unit["spans"]))[:12]
    route = f"unit/{family}/{doc['id']}/{version}/{unit['key']}-{boundary}"
    label = doc["title"] + " — " + unit["label"]
    require(len(label) <= 500, "Unit label exceeds shared ContextRecord bound")
    kind = KINDS.get(unit["kind"], unit["kind"])
    completeness = unit.get("completeness", "unresolved")
    return {"id": BASE + "id/" + route, "route": route, "label": label,
            "kind": "evidence", "text": text, "assertion_status": "normalized",
            "authority": {"class": "derived", "label": "Exact frozen source spans; logical boundary proposal; applicability unreviewed", "source": doc["url"]},
            "scope": (f"Frozen {family.upper()} {doc['id']}; captured role: {doc.get('role') or doc.get('kind') or 'unclassified'}. "
                      f"Boundary: {'agent-reviewed excerpt only' if unit.get('authored') else 'machine candidate, unresolved'}. "
                      "A structural unit is not a complete legal rule or applicability decision. Capture dates are not effective dates. Check governing headings, definitions, exceptions and current source."),
            "provenance": provenance, "rights": OGL, "access": "public", "review_status": "unreviewed-specialist-review-required",
            "evidence_unit": {"schema": "okf-evidence-unit.v1", "kind": kind,
                              "boundary_status": "author-declared" if unit.get("authored") else "machine-detected",
                              "completeness": completeness, "offset_unit": "utf-8-bytes", "joiner": "\n", "spans": spans}}


def segment_document(family, doc, extracted, inventory_sha, override=None, page_expectations=None):
    pages = extracted["pages"]
    require([p["page"] for p in pages] == list(range(1, len(pages) + 1)) and len(pages) == doc["pages"], "Incomplete page sequence")
    expectations = {}
    for expectation in page_expectations or []:
        number = expectation.get("page")
        require(isinstance(number, int) and not isinstance(number, bool) and 1 <= number <= len(pages)
                and number not in expectations, "Invalid or duplicate page expectation")
        raw = pages[number - 1]["text"].encode()
        require(expectation.get("family") == family and expectation.get("document_id") == doc["id"]
                and expectation.get("expected_text_bytes") == len(raw) and expectation.get("expected_text_sha256") == sha(raw),
                "Page expectation is not bound to exact frozen source text")
        expectations[number] = expectation
    for page in pages:
        require(isinstance(page.get("text"), str) and page["url"] == doc["url"] + f"#page={page['page']}", "Source page text/URL mismatch")
        page["text"].encode("utf-8", errors="strict")
    structures, candidates, offset = [], [], 0
    heading_number = 0
    current_heading = None
    for page in pages:
        structure = page_structure(page["text"], family, doc.get("chapter"))
        structures.append({"page": page["page"], **structure})
        events = [(h["start_utf8"], "heading", h) for h in structure["headings"]] + [(c["start_utf8"], "start", c) for c in structure["starts"]]
        for pos, kind, item in sorted(events, key=lambda row: (row[0], row[1])):
            if kind == "heading":
                heading_number += 1
                current_heading = item["literal"]
            else:
                candidates.append({**item, "start": offset + pos, "section": heading_number, "heading_path": [current_heading] if current_heading else []})
        offset += len(page["text"].encode())
    total = offset
    authored = check_override(doc, pages, override, inventory_sha) if override else []
    # All authored endpoints participate in the same source partition. Any
    # uncovered bytes stay in automatic candidates or explicit fallback units.
    endpoints = {0, total, *(row["start"] for row in candidates)}
    for unit in authored:
        endpoints.update((unit["start"], unit["end"]))
    points = sorted(endpoints)
    autos, occurrence = [], Counter()
    for candidate in candidates:
        occurrence[candidate["label"]] += 1
        candidate["occurrence"] = occurrence[candidate["label"]]
    candidate_by_start = {item["start"]: item for item in candidates}
    for start, end in zip(points, points[1:]):
        if start == end or any(start >= unit["start"] and end <= unit["end"] for unit in authored):
            continue
        candidate = candidate_by_start.get(start)
        if candidate:
            label = candidate["label"]
            key = f"section-{candidate['section']:04d}-guidance-{label.lower()}-occurrence-{candidate['occurrence']:04d}"
            kind = candidate["kind"]
            heading_path = candidate["heading_path"]
        else:
            label, key, kind, heading_path = "Unassigned source material", f"unassigned-{start:010d}", "unresolved-fragment", []
        chunks = split_interval(pages, start, end)
        for n, spans in enumerate(chunks):
            if not candidate:
                # Deliberately do not call an arbitrary introductory/memo run a
                # section. It stays uncertain even if it contains many pages.
                chunk_kind = "unresolved-fragment"
            else:
                chunk_kind = "unresolved-fragment" if len(chunks) > 1 else kind
            autos.append({"key": key + (f"-fragment-{n + 1:03d}" if len(chunks) > 1 else ""), "label": label,
                          "kind": chunk_kind, "paragraph_labels": [candidate["label"]] if candidate else [],
                          "heading_path": heading_path, "spans": spans, "authored": False, "completeness": "unresolved",
                          "review_status": "machine-boundary-candidate", "specialist_review": "not-reviewed",
                          "uncertainties": ["Automatic boundary, governing heading and source reading order require review", "Legal dependencies and applicability are unresolved"]
                              + (["Candidate split at explicit transport bound; fragments are not complete rules"] if len(chunks) > 1 else [])})
    units = sorted(autos + authored, key=lambda row: (row["spans"][0]["page"], row["spans"][0]["start_utf8"]))
    version = "v1-" + sha(canonical({"pdf": doc["sha256"], "pages": doc["pages_sha256"]}))[:16]
    records, catalogue, accounting = [], [], {p["page"]: [] for p in pages}
    for unit in units:
        record = make_record(family, doc, pages, unit, version)
        empty = not record["text"].strip()
        if not empty:
            records.append(record)
        for span in unit["spans"]:
            accounting[span["page"]].append({"start_utf8": span["start_utf8"], "end_utf8": span["end_utf8"],
                                            "unit_id": None if empty else record["id"], "literal_sha256": span["literal_sha256"],
                                            "category": "empty-extracted-text" if empty else ("author-declared" if unit.get("authored") else "machine-uncertain")})
        if not empty:
            catalogue.append({"id": record["id"], "key": unit["key"], "label": unit["label"], "kind": record["evidence_unit"]["kind"],
                              "paragraph_labels": unit.get("paragraph_labels", []), "heading_path": unit.get("heading_path", []),
                              "boundary_status": record["evidence_unit"]["boundary_status"], "completeness": record["evidence_unit"]["completeness"],
                              "review_status": unit["review_status"], "specialist_review": "not-reviewed", "review_note": unit.get("review_note"),
                              "uncertainties": unit.get("uncertainties", []), "support_unit_keys": unit.get("support_unit_keys", []),
                              "reference_unit_keys": unit.get("reference_unit_keys", []), "concept_ids": unit.get("concept_ids", []),
                              "spans": unit["spans"], "record_sha256": sha(canonical(record)), "text_sha256": sha(record["text"].encode()),
                              "text_bytes": len(record["text"].encode()), "examples": len(re.findall(r"(?im)^\s*Example(?:\s+\d+)?\s*$", record["text"])),
                              "notes": len(re.findall(r"(?im)^\s*Note\b", record["text"]))})
    page_rows, counts = [], Counter(documents=1, pages=len(pages), source_text_bytes=total,
                                   records=len(records), authored_units=sum(u.get("authored", False) for u in units))
    counts["machine_uncertain_units"] = sum(row["boundary_status"] == "machine-detected" for row in catalogue)
    for page in pages:
        raw = page["text"].encode()
        spans = sorted(accounting[page["page"]], key=lambda row: row["start_utf8"])
        cursor, reconstructed = 0, []
        for span in spans:
            require(span["start_utf8"] == cursor, "Unassigned or overlapping source bytes")
            fragment = raw[cursor:span["end_utf8"]]
            require(sha(fragment) == span["literal_sha256"], "Accounting fragment hash mismatch")
            reconstructed.append(fragment)
            cursor = span["end_utf8"]
        require(cursor == len(raw) and b"".join(reconstructed) == raw, "Source reconstruction failed")
        empty = not page["text"].strip()
        counts["empty_pages" if empty else "nonempty_pages"] += 1
        flags = next((row["flags"] for row in doc.get("quality", {}).get("flagged_pages", []) if row["page"] == page["page"]), [])
        if flags:
            counts["quality_flagged_pages"] += 1
        if structures[page["page"] - 1]["contents_candidate"]:
            counts["contents_candidate_pages"] += 1
        page_rows.append({"page": page["page"], "url": page["url"], "source_text_sha256": sha(raw), "source_text_bytes": len(raw),
                          "empty_extraction": empty, "quality_flags": flags, "accounting": spans,
                          "authored_page_expectation": expectations.get(page["page"])})
    labels = Counter(label for unit in catalogue for label in unit["paragraph_labels"])
    duplicate_labels = {label: count for label, count in sorted(labels.items()) if count > 1}
    counts["duplicate_label_groups"] = len(duplicate_labels)
    counts["numbered_boundary_candidates"] = len(candidates)
    counts["unsegmented_number_candidates"] = sum(len(s["unsegmented_number_candidates"]) for s in structures)
    counts["heading_candidates"] = sum(len(s["headings"]) for s in structures)
    counts["reserved_range_candidates"] = sum(len(s["reserved_candidates"]) for s in structures)
    counts["cross_page_units"] = sum(len({s["page"] for s in u["spans"]}) > 1 for u in catalogue)
    counts["source_bytes_accounted"] = sum(p["source_text_bytes"] for p in page_rows)
    counts["unassigned_bytes"] = 0
    counts["authored_page_expectations"] = len(expectations)
    counts["unresolved_material_bytes"] = sum(s["end_utf8"] - s["start_utf8"] for u in catalogue if u["boundary_status"] == "machine-detected" for s in u["spans"])
    catalogue_doc = {"schema": "okf-dwp-logical-document.v1", "family": family, "document_id": doc["id"], "source_version": version,
                     "source": {"url": doc["url"], "sha256": doc["sha256"], "pages_path": doc["pages_path"], "pages_sha256": doc["pages_sha256"],
                                "inventory_sha256": inventory_sha, "observed_at": doc.get("observed_at"), "document_dates": doc.get("document_dates"),
                                "role": doc.get("role"), "extraction": extracted.get("extraction"), "legal_status": doc.get("legal_status")},
                     "counts": dict(sorted(counts.items())), "duplicate_paragraph_labels": duplicate_labels,
                     "pages": page_rows, "structure_candidates": structures, "units": catalogue,
                     "proposals": (override or {}).get("proposals", []), "limitations": LIMITATIONS}
    return records, catalogue_doc


def compile_units(root=ROOT):
    inputs = Inputs(root)
    config = strict_json(inputs.read(CONFIG, limit=1024 * 1024))
    require(config.get("schema") == "okf-dwp-context-corpus-sources.v1", "Unknown source configuration")
    require(isinstance(config.get("sources"), list) and {s["id"] for s in config["sources"]} == {"dmg", "adm"}
            and len(config["sources"]) == 2, "Full declared DMG and ADM source census is required")
    override_file = Path(root) / OVERRIDES
    overrides = strict_json(inputs.read(OVERRIDES, limit=4 * 1024 * 1024)) if override_file.exists() else {"schema": "okf-dwp-logical-unit-overrides.v1", "documents": []}
    require(overrides.get("schema") == "okf-dwp-logical-unit-overrides.v1", "Unknown logical-unit overrides")
    specifications = {}
    for item in overrides.get("documents", []):
        key = (item["family"], item["document_id"])
        require(key not in specifications, "Duplicate override document")
        specifications[key] = item
    page_expectations = defaultdict(list)
    require(isinstance(overrides.get("page_expectations", []), list), "Invalid page expectations")
    for item in overrides.get("page_expectations", []):
        page_expectations[(item["family"], item["document_id"])].append(item)
    outputs, records, documents, groups, visited = {}, [], [], [], set()
    for source in config["sources"]:
        family = source["id"]
        inventory_raw = inputs.read(source["inventory"], limit=16 * 1024 * 1024)
        inventory = strict_json(inventory_raw)
        require(inventory.get("documents") and not inventory.get("failures"), "Incomplete declared source inventory")
        if family == "adm":
            require(inventory.get("summary", {}).get("complete_for_frozen_adm_census") is True, "ADM frozen census incomplete")
        group_counts = Counter()
        for doc in sorted(inventory["documents"], key=lambda row: row["id"]):
            require(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", doc["id"]), "Unsafe document ID")
            key = (family, doc["id"])
            require(key not in visited, "Duplicate source document")
            visited.add(key)
            inputs.read(doc["pdf_path"], doc["sha256"], doc["size_bytes"])
            extracted = strict_json(inputs.read(doc["pages_path"], doc["pages_sha256"], limit=32 * 1024 * 1024))
            require(extracted["source_sha256"] == doc["sha256"] and extracted.get("document_id", doc["id"]) == doc["id"]
                    and extracted.get("source_url", doc["url"]) == doc["url"], "Extraction source mismatch")
            new_records, catalogue = segment_document(family, doc, extracted, sha(inventory_raw), specifications.get(key), page_expectations.get(key))
            records.extend(new_records)
            group_counts.update(catalogue["counts"])
            relative = f"documents/{family}/{doc['id']}.json.gz"
            decoded = canonical(catalogue)
            raw = gzip_bytes(decoded)
            outputs[relative] = raw
            documents.append({"family": family, "document_id": doc["id"], **binding(relative, raw, decoded), "counts": catalogue["counts"]})
        groups.append({"id": family, "inventory": {"repository_path": source["inventory"], "sha256": sha(inventory_raw)},
                       "source_collection_url": source["collection_url"], "counts": dict(sorted(group_counts.items()))})
    require(set(specifications) <= visited, "Override refers to a source outside the declared census")
    require(set(page_expectations) <= visited, "Page expectation refers to a source outside the declared census")
    records.sort(key=lambda row: row["id"])
    require(len({row["id"] for row in records}) == len(records), "Duplicate logical record identity")
    shards, chunk, size, first = [], [], 0, 0
    def emit():
        nonlocal chunk, size, first
        if not chunk:
            return
        decoded = canonical({"schema": "okf-context-records.v1", "first_ordinal": first, "records": chunk})
        raw = gzip_bytes(decoded)
        path = f"records/{len(shards):04d}.json.gz"
        outputs[path] = raw
        shards.append({"first_ordinal": first, "count": len(chunk), "first_id": chunk[0]["id"], "last_id": chunk[-1]["id"], **binding(path, raw, decoded)})
        first += len(chunk)
        chunk, size = [], 0
    for record in records:
        n = len(canonical(record))
        if chunk and (len(chunk) >= 128 or size + n > TARGET_SHARD):
            emit()
        chunk.append(record)
        size += n
    emit()
    producer = inputs.read("scripts/build_logical_units.py", limit=1024 * 1024)
    counts = Counter()
    for group in groups:
        counts.update(group["counts"])
    identity = {"version": VERSION, "sources": groups, "inputs": sorted(inputs.files.values(), key=lambda row: row["path"])}
    snapshot = "dwp-logical-units-" + sha(canonical(identity))[:20]
    manifest = {"schema": "okf-dwp-logical-units.v1", "snapshot": snapshot, "producer_version": VERSION,
                "producer_sha256": sha(producer), "source_groups": groups, "counts": dict(sorted(counts.items())),
                "records": {"count": len(records), "shards": shards}, "documents": documents,
                "inputs": identity["inputs"], "limitations": LIMITATIONS,
                "accounting": "Ordered non-overlapping source-byte partition; inserted unit joiners are separately declared and are not source bytes",
                "review": {"specialist_accepted": False, "semantic_completeness": "not-established"}}
    outputs["manifest.json"] = canonical(manifest)
    require(len(outputs["manifest.json"]) <= MAX_SHARD, "Logical manifest exceeds 4 MiB")
    return outputs


def admitted_output(directory, relative):
    parts = relative.split("/")
    require(all(part not in ("", ".", "..") for part in parts) and not relative.startswith("/")
            and "\\" not in relative, "Unsafe generated output path")
    current = Path(directory)
    require(not current.is_symlink(), "Output root symlink not admitted")
    for part in parts:
        current /= part
        require(not current.is_symlink(), "Output symlink not admitted")
    return current


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = compile_units()
    directory = ROOT / OUTPUT
    # Admit all existing destinations before writing any bytes. The fixed output
    # root is disjoint from immutable acquisition and previous release trees.
    destinations = {name: admitted_output(directory, name) for name in outputs}
    for relative, raw in outputs.items():
        path = destinations[relative]
        if args.check:
            require(path.is_file() and not path.is_symlink() and path.read_bytes() == raw, "Stale logical output: " + relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            require(not path.is_symlink(), "Output symlink not admitted")
            path.write_bytes(raw)
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
    require(actual == set(outputs), "Unbound or obsolete logical output; inspect before removing")
    manifest = strict_json(outputs["manifest.json"])
    print(json.dumps({"status": "verified" if args.check else "built", "snapshot": manifest["snapshot"],
                      **manifest["counts"], "artefact_files": len(outputs), "artefact_bytes": sum(map(len, outputs.values()))}))


if __name__ == "__main__":
    main()
