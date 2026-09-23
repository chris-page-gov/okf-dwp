"""Pure source transforms for the bounded Pension Credit capital candidate.

The caller binds files and supplies the proposed boundaries. These functions do
not acquire sources, infer dependency closure or calculate an individual's award.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re

from manual_references import paragraph_references


MAX_UNITS = 2000
MAX_REPAIRS = 20
MAX_PARTS = 32
MAX_SPANS = 32
MAX_UNIT_BYTES = 65536
ROLES = {
    "paragraph", "rule", "section", "compound", "cross-reference", "table",
    "contents", "reserved", "unresolved-fragment",
}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _page_map(pages):
    _require(isinstance(pages, list) and 0 < len(pages) <= 2000, "Page count outside bound")
    result = {}
    for page in pages:
        number = page.get("page")
        _require(type(number) is int and number > 0 and number not in result,
                 "Invalid or duplicate page number")
        _require(isinstance(page.get("text"), str), "Missing page text")
        result[number] = page
    return result


def _read_spans(page_map, spans):
    _require(isinstance(spans, list) and 0 < len(spans) <= MAX_SPANS, "Span count outside bound")
    fragments, previous, size = [], None, 0
    for span in spans:
        number, low, high = (span.get(key) for key in ("page", "start_utf8", "end_utf8"))
        _require(all(type(value) is int for value in (number, low, high)) and number in page_map,
                 "Invalid span page or offset")
        raw = page_map[number]["text"].encode()
        _require(0 <= low < high <= len(raw), "Span outside source page")
        _require(previous is None or (number, low) >= previous, "Overlapping or unordered spans")
        fragment = raw[low:high]
        try:
            fragment.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise ValueError("Span cuts a UTF-8 character") from error
        _require(_sha(fragment) == span.get("literal_sha256"), "Span literal hash mismatch")
        size += len(fragment)
        _require(size <= MAX_UNIT_BYTES, "Source span bytes outside bound")
        fragments.append(fragment)
        previous = (number, high)
    return fragments


def _intervals(spans):
    """Coalesce only adjacent spans on the same page, preserving source order."""
    result = []
    for span in spans:
        number, low, high = (span[key] for key in ("page", "start_utf8", "end_utf8"))
        if result and result[-1][0] == number and result[-1][2] == low:
            result[-1] = (number, result[-1][1], high)
        else:
            result.append((number, low, high))
    return result


def split_units(units, pages, repairs):
    """Return copied catalogue units and a source-byte conservation receipt.

    A repair requires ``original_id``, ``original_text_sha256``, the complete
    ``original_spans`` list, and ``parts``. Each part requires a fresh ``key``,
    ``role``, ``label``, ``paragraph_labels`` and exact hash-bound ``spans``;
    ``heading_path`` is optional. Parts must partition the original in order.

    Changed units have no ``id`` or ``record_sha256``: the caller must generate
    records using a new version. Existing catalogue identity is retained solely
    in the receipt. No frozen input is mutated.
    """
    _require(isinstance(units, list) and 0 < len(units) <= MAX_UNITS, "Unit count outside bound")
    _require(isinstance(repairs, list) and len(repairs) <= MAX_REPAIRS, "Repair count outside bound")
    page_map = _page_map(pages)
    by_id, keys = {}, set()
    for unit in units:
        identity, key = unit.get("id"), unit.get("key")
        _require(isinstance(identity, str) and identity and identity not in by_id, "Missing or duplicate unit ID")
        _require(isinstance(key, str) and key and key not in keys, "Missing or duplicate unit key")
        fragments = _read_spans(page_map, unit["spans"])
        literal = b"\n".join(fragments)
        _require(unit.get("text_sha256") == _sha(literal), "Catalogue text hash mismatch")
        _require(unit.get("text") == literal.decode(), "Catalogue text differs from source spans")
        _require(unit.get("text_bytes") == len(literal), "Catalogue text byte count mismatch")
        by_id[identity] = unit
        keys.add(key)

    replacements, receipts = {}, []
    for repair in repairs:
        identity = repair.get("original_id")
        _require(identity in by_id and identity not in replacements, "Unknown or repeated repair ID")
        original = by_id[identity]
        _require(repair.get("original_text_sha256") == original["text_sha256"], "Original text binding mismatch")
        _require(repair.get("original_spans") == original["spans"], "Original span binding mismatch")
        parts = repair.get("parts")
        _require(isinstance(parts, list) and 2 <= len(parts) <= MAX_PARTS, "Repair part count outside bound")
        proposed, all_spans = [], []
        for part in parts:
            key, role = part.get("key"), part.get("role")
            _require(isinstance(key, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", key)
                     and key not in keys, "Part key is invalid or reuses an existing identity")
            keys.add(key)
            _require(role in ROLES, "Unsupported proposed role")
            label, labels = part.get("label"), part.get("paragraph_labels")
            _require(isinstance(label, str) and 0 < len(label) <= 400, "Missing or oversized part label")
            _require(isinstance(labels, list) and len(labels) <= 100
                     and len(set(labels)) == len(labels)
                     and all(isinstance(item, str) and re.fullmatch(r"(?:\d{5,6}|[A-Z]\d{4,5})", item)
                             for item in labels), "Invalid paragraph labels")
            fragments = _read_spans(page_map, part["spans"])
            literal = b"\n".join(fragments)
            text = literal.decode()
            _require(all(re.search(r"\b" + re.escape(item) + r"\b", text) for item in labels),
                     "Paragraph label absent from proposed span")
            _require(role != "contents" or not labels, "Contents must not declare substantive paragraph labels")
            _require(role != "reserved" or (len(labels) == 1 and text.strip() == labels[0]),
                     "Reserved standalone unit must contain only its paragraph label")
            headings = part.get("heading_path", [])
            _require(isinstance(headings, list) and all(isinstance(item, str) for item in headings),
                     "Invalid proposed heading path")
            proposed.append({
                "key": key, "role": role, "kind": "section" if role in {"contents", "reserved"} else role,
                "label": label, "paragraph_labels": deepcopy(labels), "heading_path": deepcopy(headings),
                "heading_context": [], "rejected_range_headings": [],
                "spans": deepcopy(part["spans"]), "text": text,
                "text_bytes": len(literal), "text_sha256": _sha(literal),
                "examples": len(re.findall(r"^Example(?: \d+)?\s*$", text, re.M)),
                "notes": len(re.findall(r"^Note\s*:", text, re.M)),
                "references": paragraph_references(text, "dmg"),
                "authored": True, "boundary_status": "author-declared",
                "review_status": "agent-reviewed-boundary-only", "specialist_review": "not-reviewed",
                "completeness": "complete-within-declared-boundary",
                "unknowns": ["Proposed source boundaries are not specialist acceptance or complete legal applicability"],
            })
            all_spans.extend(part["spans"])
        _require(_intervals(all_spans) == _intervals(original["spans"]),
                 "Parts must conserve every original source byte in order without gaps or overlaps")
        original_raw = b"".join(_read_spans(page_map, original["spans"]))
        # Each piece was hash checked above; compare actual bytes as well as ranges.
        replacement_raw = b"".join(page_map[s["page"]]["text"].encode()[s["start_utf8"]:s["end_utf8"]]
                                   for s in all_spans)
        _require(original_raw == replacement_raw, "Source-byte conservation mismatch")
        replacements[identity] = proposed
        receipts.append({
            "original_id": identity, "original_key": original["key"],
            "original_text_sha256": original["text_sha256"], "original_spans": deepcopy(original["spans"]),
            "replacement_keys": [part["key"] for part in proposed],
            "parts": [{"key": part["key"], "role": part["role"], "spans": part["spans"],
                       "text_sha256": part["text_sha256"],
                       "source_bytes": sum(s["end_utf8"] - s["start_utf8"] for s in part["spans"])}
                      for part in proposed],
            "source_bytes_before": len(original_raw), "source_bytes_after": len(replacement_raw),
            "source_bytes_sha256": _sha(original_raw), "unassigned_bytes": 0, "overlapping_bytes": 0,
        })
    result = [part for unit in units for part in replacements.get(unit["id"], [deepcopy(unit)])]
    total = sum(s["end_utf8"] - s["start_utf8"] for unit in units for s in unit["spans"])
    return result, {
        "schema": "okf-dwp-capital-boundary-receipt.v1", "repairs": receipts,
        "input_units": len(units), "output_units": len(result), "repaired_units": len(receipts),
        "source_bytes_before": total, "source_bytes_after": total,
        "source_instructions_inert": True, "specialist_review": "not-reviewed",
        "repair_specification_sha256": _sha(_canonical(repairs)),
    }


_HEADERS = (
    "Appendix 1 - How to work out deemed weekly income from capital",
    "(DMG 84911)",
    "How to work out deemed weekly income from capital (DMG 84911)",
    "Total capital Deemed weekly income from capital",
    "From To £",
    "£ £",
)
_MONEY = r"(?:NIL|\d{1,3}(?:,\d{3})*\.\d{2}|\d+\.\d{2})"
_ROW = re.compile(r"(?P<capital_from>" + _MONEY + r")\s+(?P<capital_to>" + _MONEY
                  + r")\s+(?P<deemed_weekly_income>NIL|\d+)")
_FIELDS = ("capital_from", "capital_to", "deemed_weekly_income")


def _source_ref(page_map, page, low, high):
    raw = page_map[page]["text"].encode()[low:high]
    return {"page": page, "start_utf8": low, "end_utf8": high, "literal_sha256": _sha(raw),
            "source_url": page_map[page].get("url"), "literal": raw.decode()}


def parse_capital_table(pages, spans):
    """Parse the frozen Appendix 1 layout; retain exact row and cell locations.

    Values are decimal strings. Commas are removed, NIL is explicitly normalised
    to zero, and integer pounds receive two decimal places. Column meanings are
    separately labelled model-derived proposals tied to literal source headings.
    No continuation rows or individual entitlement amounts are generated.
    """
    page_map = _page_map(pages)
    fragments = _read_spans(page_map, spans)
    headers, rows, continuation, blanks = [], [], None, []
    for span, fragment in zip(spans, fragments):
        page, cursor = span["page"], span["start_utf8"]
        page_raw = page_map[page]["text"].encode()
        _require(cursor == 0 or page_raw[cursor - 1:cursor] == b"\n", "Table span starts inside a line")
        _require(span["end_utf8"] == len(page_raw) or fragment.endswith(b"\n"), "Table span ends inside a line")
        for line in fragment.splitlines(keepends=True):
            low, high = cursor, cursor + len(line)
            cursor = high
            text = line.decode().rstrip("\r\n")
            ref = _source_ref(page_map, page, low, high)
            if not text.strip():
                blanks.append(ref)
                continue
            normal = " ".join(text.split())
            if len(headers) < len(_HEADERS):
                _require(normal == _HEADERS[len(headers)], "Unexpected or changed capital table heading")
                headers.append(ref)
                continue
            if re.fullmatch(r"and so on\s+and so on\s+and so on", text.strip()):
                _require(continuation is None and len(rows) == 21, "Unexpected table continuation or row count")
                continuation = {"kind": "continuation", "source": ref,
                                "literal_cells": ["and so on"] * 3, "generated_rows": 0,
                                "assertion_status": "normalised", "interpretation": "not-expanded"}
                continue
            match = _ROW.fullmatch(text.strip())
            _require(match is not None and continuation is None and len(rows) < 21,
                     "Unrecognised capital table row; refusing to invent or correct cells")
            leading = len(text) - len(text.lstrip())
            cells, values = {}, {}
            for field in _FIELDS:
                literal = match[field]
                start = low + len(text[:leading + match.start(field)].encode())
                stop = low + len(text[:leading + match.end(field)].encode())
                cells[field] = _source_ref(page_map, page, start, stop)
                values[field] = "0.00" if literal == "NIL" else literal.replace(",", "")
                if "." not in values[field]:
                    values[field] += ".00"
            rows.append({"ordinal": len(rows) + 1, "kind": "capital-income-table-row",
                         "currency": "GBP", **values, "source": ref, "source_cells": cells,
                         "assertion_status": "normalised", "specialist_review": "not-reviewed"})
    _require(len(headers) == len(_HEADERS) and len(rows) == 21 and continuation is not None,
             "Incomplete capital table: headings, 21 rows and continuation are required")
    header_indices = {"capital_from": [3, 4, 5], "capital_to": [3, 4, 5], "deemed_weekly_income": [3, 4]}
    labels = {"capital_from": "Total capital: from", "capital_to": "Total capital: to",
              "deemed_weekly_income": "Deemed weekly income from capital"}
    return {
        "schema": "okf-dwp-capital-table.v1", "currency": "GBP", "source_spans": deepcopy(spans),
        "source_text_sha256": _sha(b"\n".join(fragments)), "headers": headers,
        "column_semantics": [{"field": field, "label": labels[field], "datatype": "decimal-string",
                              "currency": "GBP", "assertion_status": "model-derived",
                              "specialist_review": "not-reviewed",
                              "header_sources": [headers[i] for i in header_indices[field]]}
                             for field in _FIELDS],
        "normalisation": {"assertion_status": "normalised", "thousands_separator": "removed",
                          "NIL": "0.00", "integer_pounds": "two decimal places",
                          "source_literals_retained": True},
        "rows": rows, "continuation": continuation, "blank_lines": blanks,
        "accounting": {"source_bytes": sum(len(item) for item in fragments),
                       "header_bytes": sum(item["end_utf8"] - item["start_utf8"] for item in headers),
                       "row_bytes": sum(row["source"]["end_utf8"] - row["source"]["start_utf8"] for row in rows),
                       "continuation_bytes": continuation["source"]["end_utf8"] - continuation["source"]["start_utf8"],
                       "blank_bytes": sum(item["end_utf8"] - item["start_utf8"] for item in blanks),
                       "unassigned_bytes": 0},
        "individual_award_calculated": False, "source_instructions_inert": True,
        "specialist_review": "not-reviewed", "legal_applicability": "not-established",
    }
