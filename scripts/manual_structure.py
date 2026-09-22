"""Source-led structural proposals; original source text is never rewritten.

The parser distinguishes contents declarations from paragraph bodies, checks
heading-range containment, and carries examples/notes/citations over page breaks.
Its outputs are machine proposals, not legal rules or specialist acceptance.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import re

from pdf_structure_alignment import load_alignment

from build_logical_units import require, sha, source_spans, split_interval

VERSION = "manual-structure-v1"
LABEL = r"(?:[A-Z]\d{4,5}|\d{5,6})"
PARAGRAPH = re.compile(r"^(?P<indent>[ \t]*)(?P<label>" + LABEL + r")(?P<tail>[^\r\n]*)$")
RANGE_HEADING = re.compile(
    r"^(?P<title>.+?)[ \t]+(?P<low>" + LABEL + r")"
    r"(?:\s*[-–—]\s*(?P<high>" + LABEL + r"))?\s*$"
)
RANGE_TAIL = re.compile(r"^\s*[-–—]\s*(?P<high>" + LABEL + r")\s*$")
BODY = re.compile(r"^[ \t]+[A-Za-z\[‘“(]")
CITATION_TAIL = re.compile(r"^\s+(?:et seq|for guidance|and\s+(?:\d|[A-Z]\d))\b", re.I)
EXAMPLE = re.compile(r"^\s*Example(?:\s+\d+)?\s*$", re.I)
NOTE = re.compile(r"^\s*Note(?:\s+\d+)?(?:\s*:|\s|$)", re.I)


@dataclass(frozen=True)
class Line:
    start: int
    end: int
    page: int
    text: str

    @property
    def stripped(self):
        return self.text.strip()


def label_parts(value):
    match = re.fullmatch(r"([A-Z]?)(\d{4,6})", value)
    return (match[1], int(match[2])) if match else None


def contains(low, high, value):
    a, b, c = (label_parts(item) for item in (low, high, value))
    return bool(a and b and c and a[0] == b[0] == c[0] and a[1] <= c[1] <= b[1])


def accepts_label(value, family, chapter):
    if family == "dmg":
        return value.isdigit() and (chapter is None or value.startswith(f"{int(chapter):02d}"))
    return bool(re.fullmatch(r"[A-Z]\d{4,5}", value)) and (chapter is None or value.startswith(str(chapter).upper()))


def source_lines(pages):
    lines, cursor = [], 0
    for expected, page in enumerate(pages, 1):
        require(page["page"] == expected and isinstance(page["text"], str), "Invalid ordered source pages")
        for text in page["text"].splitlines(keepends=True):
            end = cursor + len(text.encode("utf-8"))
            lines.append(Line(cursor, end, expected, text))
            cursor = end
    return lines, cursor


def normal_title(value):
    return re.sub(r"\s+", " ", value.strip().lstrip("•").strip()).casefold()


def discover_structure(family, doc, pages):
    """Recover navigation declarations and paragraph events independently.

    A Subpages list on a page does not invalidate a real paragraph elsewhere on
    that page. Range declarations cannot govern identifiers outside their range.
    Unnumbered headings are admitted only when they repeat a declared title.
    """
    lines, total = source_lines(pages)
    chapter = doc.get("chapter")
    headings, starts, rejected = [], [], []
    page_first = {}
    for line in lines:
        if line.stripped:
            page_first.setdefault(line.page, line.start)
    for index, line in enumerate(lines):
        literal = line.stripped
        if not literal:
            continue
        match = PARAGRAPH.fullmatch(line.text.rstrip("\r\n"))
        if match and accepts_label(match["label"], family, chapter):
            tail = match["tail"]
            reserved = RANGE_TAIL.fullmatch(tail)
            if reserved and contains(match["label"], reserved["high"], match["label"]):
                starts.append({"start": line.start, "label": match["label"], "range_end": reserved["high"],
                               "role": "reserved", "page": line.page})
            elif BODY.match(tail) and not CITATION_TAIL.match(tail) and not re.search(r"\.{4,}", tail):
                starts.append({"start": line.start, "label": match["label"], "role": "paragraph", "page": line.page})
            else:
                rejected.append({"start": line.start, "page": line.page, "label": match["label"],
                                 "reason": "numbered-line-without-admitted-paragraph-body"})
            continue
        heading = RANGE_HEADING.fullmatch(literal)
        if not heading or not accepts_label(heading["low"], family, chapter):
            continue
        high = heading["high"] or heading["low"]
        if not contains(heading["low"], high, heading["low"]):
            continue
        title, begin = heading["title"].strip(), line.start
        bullet = title.startswith("•")
        # A wrapped heading's final line often starts with a dash. Join only
        # an immediately preceding same-page non-sentence title line.
        if title.startswith(("-", "–", "—")) and index:
            previous = lines[index - 1]
            if (previous.page == line.page and previous.stripped
                    and len(previous.stripped) <= 140
                    and not re.search(r"[.;:]$", previous.stripped)
                    and not PARAGRAPH.match(previous.stripped)):
                title = previous.stripped + " " + title
                begin = previous.start
                bullet = previous.stripped.startswith("•")
        if len(title) > 260 or re.search(r"\.{4,}|[.;:]$", title):
            continue
        headings.append({"start": begin, "end": line.end, "page": line.page,
                         "title": title.lstrip("•").strip(), "low": heading["low"], "high": high,
                         "role": "contents-entry" if bullet else "range-heading-declaration",
                         "page_opening": begin == page_first.get(line.page),
                         "basis": "literal-number-range"})
    declared = {}
    for heading in headings:
        declared.setdefault(normal_title(heading["title"]), []).append(heading)
    literal_headings = []
    for line in lines:
        if not line.stripped or line.stripped.startswith("•"):
            continue
        matches = declared.get(normal_title(line.stripped), [])
        if matches:
            literal_headings.append({"start": line.start, "end": line.end, "page": line.page,
                                     "title": line.stripped, "declared_ranges": matches,
                                     "basis": "literal-declared-title-repeat"})
    occurrences = Counter()
    for position, item in enumerate(starts):
        occurrences[item["label"]] += 1
        item["occurrence"] = occurrences[item["label"]]
        admitted = [h for h in headings if h["start"] < item["start"]
                    and contains(h["low"], h["high"], item["label"])]
        # Nearest source declaration wins among the same range, then retain
        # nested containing ranges in broad-to-narrow order. No out-of-range
        # declaration can be silently carried forward from a contents list.
        latest = {}
        for heading in admitted:
            key = (heading["low"], heading["high"])
            if key not in latest or heading["start"] > latest[key]["start"]:
                latest[key] = heading
        context = sorted(latest.values(), key=lambda h: (-(label_parts(h["high"])[1] - label_parts(h["low"])[1]), h["start"]))
        item["heading_context"] = context
        item["heading_path"] = list(dict.fromkeys(h["title"] for h in context))
        item["rejected_range_headings"] = [h for h in headings
            if h["page"] == item["page"] and h["start"] < item["start"]
            and not contains(h["low"], h["high"], item["label"])]
        # A repeated, declared local heading is part of the following passage,
        # rather than the final lines of the preceding passage.
        candidates = [h for h in literal_headings if h["page"] == item["page"] and h["start"] < item["start"]
                      and any(contains(r["low"], r["high"], item["label"]) for r in h["declared_ranges"])]
        previous_start = starts[position - 1]["start"] if position else -1
        candidates = [h for h in candidates if h["start"] > previous_start]
        item["boundary_start"] = max(candidates, key=lambda h: h["start"])["start"] if candidates else item["start"]
    return {"lines": lines, "source_bytes": total, "paragraphs": starts,
            "range_headings": headings, "literal_headings": literal_headings, "rejected_number_lines": rejected}


def paragraph_references(text, family):
    """Literal navigation references only; no automatic legal requires edges."""
    found = []
    expression = re.compile(r"\b(?:(?P<manual>DMG|ADM)\s+)?(?P<cue>Chapter\s+|(?:see|at|paragraphs?|paras?)\s+)?"
                            r"(?P<label>" + LABEL + r"|[A-Z]\d{1,2}|\d{1,2})\b", re.I)
    for hit in expression.finditer(text):
        manual, cue, label = hit["manual"], hit["cue"] or "", hit["label"].upper()
        if not manual and not cue:
            continue
        is_chapter = cue.lower().startswith("chapter")
        if not is_chapter and not re.fullmatch(LABEL, label):
            continue
        if is_chapter and not re.fullmatch(r"[A-Z]?\d{1,2}", label):
            continue
        found.append({"manual": manual.lower() if manual else family, "target_kind": "chapter" if is_chapter else "paragraph",
                      "target_label": label, "literal": hit[0],
                      "start_utf8": len(text[:hit.start()].encode()), "end_utf8": len(text[:hit.end()].encode()),
                      "relationship_role": "source-reference", "legal_dependency": "not-established"})
    # Updates and legal citations are literal source references, never an
    # inferred amendment effect or an acquired legislative body.
    memo = re.compile(r"\b(?:Memo(?:randum)?\s+)(DMG|ADM)\s+(\d{1,2}[-/]\d{2,4})", re.I)
    legislation = re.compile(r"\b([A-Z][A-Za-z]*(?:[ \t]+(?:[A-Za-z]+|\([A-Z]+\))){0,5}[ \t]+(?:Regs|Act)(?:[ \t]+\d{2,4})?)[ \t]*,[ \t]*((?:reg|s|art)\s+\d+[A-Za-z]?(?:\([0-9A-Za-z]+\))*)")
    for pattern, kind in ((memo, "memo"), (legislation, "legislation")):
        for hit in pattern.finditer(text):
            target = hit[2] if kind == "memo" else re.sub(r"\s+", " ", hit[0])
            found.append({"manual": hit[1].lower() if kind == "memo" else family,
                          "target_kind": kind, "target_label": target, "literal": hit[0],
                          "start_utf8": len(text[:hit.start()].encode()), "end_utf8": len(text[:hit.end()].encode()),
                          "relationship_role": "source-reference", "legal_dependency": "not-established"})
    return found



def apply_pdf_structure(family, doc, pages, structure):
    """Use aligned source-declared headings, preserving fallback uncertainty."""
    alignment = load_alignment(family, doc, pages)
    structure["pdf_structure"] = {k: v for k, v in alignment.items() if k != "blocks"}
    headings = []
    for block in alignment["blocks"]:
        if not re.fullmatch(r"H[1-6]", block["role"]):
            continue
        text = re.sub(r"\s+", " ", block["text"]).strip()
        if re.fullmatch(r"Subpages|Contents|Examples?(?:\s+\d+)?|Notes?(?:\s+\d+)?", text, re.I):
            continue
        headings.append({**block, "title": text, "level": int(block["role"][1:])})
    headings.sort(key=lambda h: (h["start"], h["end"]))
    stack, cursor = [], 0
    for pos, item in enumerate(structure["paragraphs"]):
        while cursor < len(headings) and headings[cursor]["end"] <= item["start"]:
            heading = headings[cursor]; cursor += 1
            while stack and stack[-1]["level"] >= heading["level"]:
                stack.pop()
            stack.append(heading)
        compatible = []
        for heading in stack:
            number = RANGE_HEADING.fullmatch(heading["title"])
            if number and not contains(number["low"], number["high"] or number["low"], item["label"]):
                continue
            compatible.append(heading)
        if compatible:
            item["heading_path"] = list(dict.fromkeys([h["title"] for h in compatible] + item["heading_path"]))
            item["heading_basis"] = "source-declared-pdf-tags-and-literal-ranges"
            previous = structure["paragraphs"][pos - 1]["start"] if pos else -1
            local = [h for h in compatible if previous < h["start"] < item["start"]]
            # A range heading with intervening mini-contents remains a separate
            # navigation region; it is not folded into the rule's source text.
            if local:
                nearest = local[-1]
                between = [h for h in structure["range_headings"] if nearest["end"] <= h["start"] < item["start"]]
                if not between:
                    item["boundary_start"] = min(item["boundary_start"], nearest["start"])
    structure["tagged_headings"] = [{k: h[k] for k in ("start", "end", "page", "title", "level", "alignment")} for h in headings]
    return alignment

def structure_regions(structure):
    """Classify literal local contents intervals without treating them as rules."""
    regions = []
    for item in structure["paragraphs"]:
        preceding = [h for h in structure["range_headings"]
                     if h["page"] == item["page"] and h["end"] <= item["start"]]
        local_paragraphs = [p for p in structure["paragraphs"]
                            if p["page"] == item["page"] and p["start"] < item["start"]]
        if len(preceding) >= 2 and not local_paragraphs:
            first = min(preceding, key=lambda h: h["start"])
            regions.append({"start": first["end"], "end": item["boundary_start"],
                            "role": "contents", "basis": "local-range-declarations-before-body"})
    return [r for r in regions if r["end"] > r["start"]]




def scoped_references(text, family, role):
    refs = paragraph_references(text, family)
    if role == "annotation":
        for match in re.finditer(r"\b" + LABEL + r"\b", text):
            refs.append({"manual": family, "target_kind": "paragraph", "target_label": match[0],
                "kind": "update-annotation", "literal": match[0], "legal_dependency": "not-established",
                "start_utf8": len(text[:match.start()].encode()), "end_utf8": len(text[:match.end()].encode())})
    return refs

def special_regions(family, doc, structure, pages):
    """Explicit document conventions; no document IDs or benefit rules."""
    lines, total = structure["lines"], structure["source_bytes"]
    regions = []
    raw = b"".join(p["text"].encode() for p in pages)
    for index, line in enumerate(lines):
        if re.match(r"The content of the examples in this document\b", line.stripped):
            following = [p["boundary_start"] for p in structure["paragraphs"] if p["boundary_start"] > line.start]
            regions.append({"start": line.start, "end": min(following, default=total), "role": "document-notice", "heading_path": []})
        if re.match(r"Appendix\s+[A-Z0-9]+\s*[-–—:]", line.stripped):
            # A declared appendix plus explicit table columns supports a table
            # candidate; the heading alone does not establish tabular structure.
            following = raw[line.start:min(total, line.start + 1800)].decode(errors="replace")
            if re.search(r"\bFrom\s+To\b", following) and re.search(r"\d[,.]\d{2}\b", following):
                later = [r.start for r in lines[index + 1:]
                         if re.match(r"Appendix\s+[A-Z0-9]+\s*[-–—:]|The content of the examples in this document\b", r.stripped)]
                heading = line.stripped
                if index + 1 < len(lines) and lines[index + 1].stripped.startswith("("):
                    heading += " " + lines[index + 1].stripped
                regions.append({"start": line.start, "end": min(later, default=total), "role": "table", "heading_path": [heading]})
    if doc.get("kind") == "abbreviations" and doc.get("role", "").startswith("reference"):
        regions.append({"start": 0, "end": total, "role": "reference-table", "heading_path": [doc.get("title", "Abbreviations")]})
    if doc.get("kind") == "memo":
        body = next((line.start for line in lines if re.match(r"1\.\s+[A-Z]", line.stripped)), None)
        if body is not None:
            contents = next((line.start for line in lines if line.start < body and re.match(r"Contents\b", line.stripped)), None)
            intro = [line.start for line in lines if line.start < body and line.stripped.casefold() == "introduction"]
            if contents is not None and intro:
                regions.append({"start": contents, "end": max(intro), "role": "contents", "heading_path": ["Contents"]})
            section_roles = {"examples": "example-group", "annotations": "annotation", "contacts": "contact"}
            headings = [line for line in lines if line.start > body and line.stripped.casefold() in section_roles]
            for pos, line in enumerate(headings):
                end = headings[pos + 1].start if pos + 1 < len(headings) else total
                region = {"start": line.start, "end": end, "role": section_roles[line.stripped.casefold()], "heading_path": [line.stripped]}
                text = raw[line.start:end].decode()
                region["references"] = paragraph_references(text, family)
                if region["role"] == "annotation":
                    for match in re.finditer(r"\b" + LABEL + r"\b", text):
                        region["references"].append({"manual": family, "target_kind": "paragraph", "target_label": match[0],
                            "kind": "update-annotation", "literal": match[0], "legal_dependency": "not-established",
                            "start_utf8": len(text[:match.start()].encode()), "end_utf8": len(text[:match.end()].encode())})
                regions.append(region)
    return regions

def segment_source(family, doc, pages, authored=()):
    """Return a complete byte partition with explicit unsupported material.

    Authored source-bound excerpts take precedence without being relabelled as
    specialist-reviewed. Plain-number memo and table structure is initially
    retained as reference/fallback material until its separate conventions apply.
    """
    structure = discover_structure(family, doc, pages)
    apply_pdf_structure(family, doc, pages, structure)
    structure["source_instructions_inert"] = True
    structure["regions"] = structure_regions(structure)
    special = special_regions(family, doc, structure, pages)
    structure["regions"].extend(special)
    events = {p["boundary_start"]: p for p in structure["paragraphs"]
              if not any(r["start"] <= p["boundary_start"] < r["end"] for r in special)}
    total = structure["source_bytes"]
    endpoints = {0, total, *events}
    for region in special:
        endpoints.update((region["start"], region["end"]))
    for unit in authored:
        endpoints.update((unit["start"], unit["end"]))
    raw = b"".join(p["text"].encode() for p in pages)
    units = []
    points = sorted(endpoints)
    for start, end in zip(points, points[1:]):
        if start == end or any(start >= u["start"] and end <= u["end"] for u in authored):
            continue
        event = events.get(start)
        region = next((r for r in special if r["start"] <= start < r["end"]), None)
        default_role = "reference-material" if doc.get("role", "").startswith("reference") else "unresolved-fragment"
        role = region["role"] if region else event["role"] if event else default_role
        for chunk_index, spans in enumerate(split_interval(pages, start, end)):
            literal = "\n".join(pages[s["page"] - 1]["text"].encode()[s["start_utf8"]:s["end_utf8"]].decode() for s in spans)
            source_size = sum(s["end_utf8"] - s["start_utf8"] for s in spans)
            fragmented = source_size != end - start
            unit = {"key": f"source-{start:010d}-{chunk_index:03d}", "role": role,
                    "paragraph_labels": [event["label"]] if event and event["role"] != "reserved" else [], "heading_path": region.get("heading_path", []) if region else event["heading_path"] if event else [],
                    "heading_context": event["heading_context"] if event else [],
                    "rejected_range_headings": event["rejected_range_headings"] if event else [],
                    "spans": spans, "text_sha256": sha(literal.encode()), "text_bytes": len(literal.encode()),
                    "text": literal, "review_status": "machine-structure-proposal", "specialist_review": "not-reviewed",
                    "boundary_status": "bounded-fragment" if fragmented else "source-structure-candidate",
                    "completeness": "unresolved", "authored": False,
                    "examples": sum(bool(EXAMPLE.fullmatch(line)) for line in literal.splitlines()),
                    "notes": sum(bool(NOTE.match(line)) for line in literal.splitlines()),
                    "references": scoped_references(literal, family, role),
                    "unknowns": ["Legal applicability and required dependency closure are not established",
                                 "Machine structure has not received specialist review"]}
            if not event:
                unit["unknowns"].append("No admitted numbered paragraph boundary; retain original source locations")
            if fragmented:
                unit["unknowns"].append("Source interval exceeds the bounded transport unit; fragment is not a whole rule")
            units.append(unit)
    for old in authored:
        spans = old["spans"]
        literal = "\n".join(pages[s["page"] - 1]["text"].encode()[s["start_utf8"]:s["end_utf8"]].decode() for s in spans)
        unit = {**old, "role": old.get("kind", "paragraph"), "text": literal, "text_sha256": sha(literal.encode()),
                "text_bytes": len(literal.encode()), "boundary_status": "author-declared", "authored": True,
                "references": paragraph_references(literal, family), "unknowns": ["Agent boundary review is not specialist acceptance"]}
        units.append(unit)
    units.sort(key=lambda u: (u["spans"][0]["page"], u["spans"][0]["start_utf8"]))
    by_page = {p["page"]: [] for p in pages}
    for unit in units:
        for span in unit["spans"]:
            by_page[span["page"]].append(span)
    for page in pages:
        cursor, reconstructed = 0, bytearray()
        source = page["text"].encode()
        for span in sorted(by_page[page["page"]], key=lambda s: s["start_utf8"]):
            require(span["start_utf8"] == cursor, "Structural source partition overlaps or has a gap")
            literal = source[cursor:span["end_utf8"]]
            require(sha(literal) == span["literal_sha256"], "Structural span does not match source")
            reconstructed.extend(literal)
            cursor = span["end_utf8"]
        require(bytes(reconstructed) == source, "Structural source byte reconstruction failed")
    require(sum(sum(s["end_utf8"] - s["start_utf8"] for s in u["spans"]) for u in units) == len(raw), "Structural source accounting differs")
    return units, {k: v for k, v in structure.items() if k != "lines"}
