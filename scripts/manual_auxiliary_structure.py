"""Bound literal auxiliary regions without extending their label into guidance.

These are machine structural observations, never legal dependencies. A reserved
range labels its own source line only. A familiar document notice labels only
its bounded paragraph. Following appendices, tables and prose remain available
to the caller's independently supported classification or unresolved fallback.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
import hashlib
import re

LABEL = r"(?:[A-Z]\d{4,5}|\d{5,6})"
RESERVED = re.compile(r"[ \t]*(?P<low>" + LABEL + r")[ \t]*[-–—][ \t]*(?P<high>" + LABEL + r")[ \t]*")
NOTICE_START = re.compile(r"The content of the examples in this document\b")
NOTICE_END = re.compile(r"\billustrative purposes only[.!]?\s*$")
NEXT_STRUCTURE = re.compile(r"(?:Appendix\b|Chapter\b|Contents\b|Introduction\b|" + LABEL + r"\b)", re.I)
MEMO_NUMBER = re.compile(r"(?P<indent>[ \t]*)(?P<label>[1-9]\d{0,2})[.]?[ \t]+(?P<body>[A-Z][^\r\n]*)")
CONTAINER_ROLES = {"L", "LI", "Table", "TR", "TH", "TD"}
MAX_NOTICE_BYTES = 2048
MAX_NOTICE_LINES = 8


@dataclass(frozen=True)
class SourceLine:
    start: int
    end: int
    page: int
    text: str


def source_lines(pages):
    """Use original UTF-8 offsets; page boundaries introduce no synthetic bytes."""
    result, cursor = [], 0
    for number, page in enumerate(pages, 1):
        if page.get("page") != number or not isinstance(page.get("text"), str):
            raise ValueError("Expected consecutive frozen source pages")
        for text in page["text"].splitlines(keepends=True):
            end = cursor + len(text.encode())
            result.append(SourceLine(cursor, end, number, text))
            cursor = end
    return result, b"".join(page["text"].encode() for page in pages)


def compatible_range(low, high, family, chapter):
    left = re.fullmatch(r"([A-Z]?)(\d{4,6})", low)
    right = re.fullmatch(r"([A-Z]?)(\d{4,6})", high)
    if not left or not right or left[1] != right[1] or int(left[2]) > int(right[2]):
        return False
    if family == "dmg":
        return not left[1] and (chapter is None or low.startswith(f"{int(chapter):02d}") and high.startswith(f"{int(chapter):02d}"))
    return bool(left[1]) and (chapter is None or low.startswith(str(chapter).upper()) and high.startswith(str(chapter).upper()))


def literal_auxiliary_regions(pages, family, chapter=None):
    """Return exact, explicitly ended regions, not continuing paragraph events.

The caller must remove its continuing reserved-range events, otherwise a second
unbounded event can still relabel the text after this region. No bytes are
discarded or rewritten, including whitespace outside the returned intervals.
"""
    if family not in {"dmg", "adm"}:
        raise ValueError("Unknown manual family")
    if family == "dmg" and chapter is not None and not str(chapter).isdigit():
        raise ValueError("DMG chapter must be numeric")
    lines, raw = source_lines(pages)
    regions = []
    for index, line in enumerate(lines):
        reserved = RESERVED.fullmatch(line.text.rstrip("\r\n"))
        if reserved and compatible_range(reserved["low"], reserved["high"], family, chapter):
            regions.append({"start": line.start, "end": line.end, "page": line.page,
                "role": "reserved", "heading_path": [], "range_start": reserved["low"],
                "range_end": reserved["high"], "basis": "literal-standalone-number-range",
                "boundary_status": "explicit-line-end"})
        if not NOTICE_START.match(line.text.strip()):
            continue
        end, complete, boundary = line.start, False, "bounded-notice-prefix"
        for offset, part in enumerate(lines[index:index + MAX_NOTICE_LINES]):
            if part.page != line.page or not part.text.strip():
                boundary = "page-or-blank-paragraph-end"
                break
            if offset and NEXT_STRUCTURE.match(part.text.strip()):
                boundary = "following-structure-start"
                break
            if part.end - line.start > MAX_NOTICE_BYTES:
                boundary = "notice-byte-limit"
                break
            end = part.end
            if NOTICE_END.search(re.sub(r"\s+", " ", raw[line.start:end].decode())):
                complete, boundary = True, "literal-notice-sentence-end"
                break
        else:
            boundary = "notice-line-limit" if len(lines) - index >= MAX_NOTICE_LINES else "document-end"
        if end > line.start:
            regions.append({"start": line.start, "end": end, "page": line.page,
                "role": "document-notice", "heading_path": [],
                "basis": "literal-notice-prefix-and-bounded-paragraph",
                "boundary_status": boundary, "notice_sentence_complete": complete})
    for region in regions:
        region.update(literal_sha256=hashlib.sha256(raw[region["start"]:region["end"]]).hexdigest(),
                      review_status="machine-structure-proposal", legal_dependency="not-established")
    return sorted(regions, key=lambda region: (region["start"], region["end"]))


def memo_paragraph_candidates(doc, pages, blocks):
    """Observe source-tagged, margin-aligned numbering; do not accept boundaries.

    PDFs can tag nested points as P and body paragraphs as LI. Original indentation
    and container ancestry are therefore recorded independently; numbering scope
    remains unresolved.
Even a matching candidate needs a caller's explicit boundary policy. This
observer never returns a complete-rule, legal-dependency or official assertion.
"""
    if doc.get("kind") != "memo":
        return []
    lines, raw = source_lines(pages)
    starts = [line.start for line in lines]
    containers = [block for block in blocks if block.get("role") in CONTAINER_ROLES]
    observations = []
    for block in blocks:
        if block.get("role") != "P" or not isinstance(block.get("start"), int) or not isinstance(block.get("end"), int):
            continue
        begin, end = block["start"], block["end"]
        if not 0 <= begin < end <= len(raw):
            raise ValueError("Aligned paragraph span is outside the source")
        raw[begin:end].decode("utf-8", errors="strict")
        at = bisect_right(starts, begin) - 1
        if at < 0:
            continue
        line = lines[at]
        match = MEMO_NUMBER.fullmatch(line.text.rstrip("\r\n"))
        if not match or begin != line.start + len(match["indent"].encode()):
            continue
        # A leaf label/body must be in the exact source-declared P span. Merely
        # intersecting a large container or an unrelated short P is insufficient.
        if end < line.start + len(line.text.rstrip().encode()):
            continue
        ancestry = [other["role"] for other in containers
            if isinstance(other.get("tree_line_start"), int) and isinstance(other.get("tree_line_end"), int)
            and isinstance(block.get("tree_line_start"), int) and isinstance(block.get("tree_line_end"), int)
            and other["tree_line_start"] < block["tree_line_start"] <= block["tree_line_end"] <= other["tree_line_end"]]
        observations.append({"start": begin, "end": end, "page": line.page,
            "label": match["label"], "indent_columns": len(match["indent"].expandtabs(8)),
            "tag_role": "P", "container_ancestry": ancestry,
            "tree_line_start": block.get("tree_line_start"), "tree_line_end": block.get("tree_line_end"),
            "basis": "aligned-source-p-tag-and-original-line-number",
            "literal_sha256": hashlib.sha256(raw[begin:end]).hexdigest(),
            "review_status": "machine-structure-proposal", "legal_dependency": "not-established",
            "admission_status": "candidate-only", "boundary_complete": False})
    margin = min((row["indent_columns"] for row in observations if not row["container_ancestry"]), default=None)
    for row in observations:
        row["at_document_number_margin"] = margin is not None and row["indent_columns"] == margin
        row["unknowns"] = ["P tags and indentation do not prove main paragraph or complete rule scope",
                           "Sequential numbering and source-layout review remain necessary before use as an event"]
        if row["container_ancestry"]:
            row["unknowns"].append("Numbered P is nested in a source-declared list or table")
        if not row["at_document_number_margin"]:
            row["unknowns"].append("Numbered P is indented relative to other source candidates")
    return sorted(observations, key=lambda row: (row["start"], row["end"]))
