"""Literal navigation/front-matter regions without changing source bytes.

These are source-structure observations, not benefit rules. They deliberately
do not infer missing excerpt text or renumber local appendix paragraphs.
"""
import re


LEADER = re.compile(r"\.{4,}\s*(?:[A-Z]?\d{4,6}|Appendix\s+[A-Z0-9]+)\s*$", re.I)
REPLACEMENT = re.compile(r"(?:\d{5,6}\s*[-–—]\s*\d{5,6}|Conts?\b|Contents\b).*\(\d+\s+pages?\)", re.I)
FOOTER = re.compile(r"Vol(?:ume)?\s+\d+\s+Amendment\s+\d+\b", re.I)
OVERLAP_TABLE = re.compile(
    r"^The table below summarises the effects of overlap under Reciprocal Agreements\s*$", re.I
)


def navigation_regions(doc, lines, total, paragraphs):
    """Observe complete local rows, never promote their references to rules."""
    by_page = {}
    for line in lines:
        by_page.setdefault(line.page, []).append(line)
    regions = []
    historical = doc.get("kind") == "historical-amendment"
    if not historical:
        return regions
    for page, page_lines in by_page.items():
        visible = [line for line in page_lines if line.stripped]
        if not visible:
            continue
        begin, end = page_lines[0].start, page_lines[-1].end
        text = "\n".join(line.stripped for line in visible)
        opening = "\n".join(line.stripped for line in visible[:8])
        body = [p for p in paragraphs if p["page"] == page]
        # This historical amendment has a full-page overlap matrix after
        # paragraph 070594. Its many DMG numbers are column references.
        if (historical and OVERLAP_TABLE.fullmatch(visible[0].stripped)
                and any("RP" in line.stripped and "WB" in line.stripped and "IBLT" in line.stripped
                        for line in visible[1:8])):
            later = [p["start"] for p in body if p["start"] > visible[0].end]
            regions.append({"start": begin, "end": min(later, default=end), "role": "reference-table",
                            "basis": "literal-reciprocal-agreement-overlap-matrix",
                            "heading_path": ["Overlap under reciprocal agreements"]})
            continue
        # Explicit amendment letters carry administrative references to many
        # paragraph numbers. Their list items are not paragraph-body events.
        if (historical and re.search(r"This letter provides details on Amendment\b", text, re.I)
                and re.search(r"Amendment\s+\d+", opening, re.I)):
            regions.append({"start": begin, "end": end, "role": "document-notice",
                            "basis": "literal-amendment-cover-letter", "heading_path": ["Amendment notice"]})
            continue
        replacement_rows = [line for line in visible if REPLACEMENT.search(line.stripped)]
        if historical and (re.search(r"^Remove\s{2,}Insert\s*$", opening, re.M)
                           or len(replacement_rows) >= 2):
            # A replacement sheet can continue without repeating its columns.
            # Do not swallow any later real rule on a mixed page.
            last = max((line.end for line in replacement_rows), default=begin)
            later = [p["start"] for p in body if p["start"] >= last]
            stop = min(later, default=end)
            regions.append({"start": begin, "end": stop, "role": "reference-table",
                            "basis": "literal-amendment-replacement-table", "heading_path": ["Remove and insert"]})
            continue
        headers = [line for line in visible[:3] if line.stripped.casefold() in {"abbreviations", "statutory instruments"}]
        if historical and headers:
            head = headers[0]
            later = [p["start"] for p in body if p["start"] >= head.end]
            regions.append({"start": head.start, "end": min(later, default=end), "role": "reference-table",
                            "basis": "literal-amendment-reference-table", "heading_path": [head.stripped]})
            continue
        leaders = [line for line in visible if LEADER.search(line.stripped)]
        if len(leaders) >= 3 and len(leaders) * 3 >= len(visible):
            # A contents continuation need not repeat a Contents heading.
            # A real paragraph on the same page still bounds the region.
            first, last = leaders[0], leaders[-1]
            earlier = [p for p in body if p["start"] < first.start]
            start = first.start if earlier else begin
            titles = [line.start for line in visible if (not earlier or line.start > earlier[-1]["start"])
                      and line.start < first.start and line.stripped.casefold() in {"contents", "subpages"}]
            if titles:
                start = max(titles)
            later = [p["boundary_start"] for p in body if p["start"] >= last.end]
            regions.append({"start": start, "end": min(later, default=end), "role": "contents",
                            "basis": "repeated-dotted-leader-navigation", "heading_path": ["Contents"]})
    return [row for row in regions if row["end"] > row["start"]]


def local_heading_attachment(lines, heading_end, paragraph_start):
    """Only white space/isolated footnote markers may connect a heading/body.

    Explicit running amendment footers are inert. Ordinary prose, tables and
    other section text prevent a source heading pulling a paragraph backwards.
    """
    between = [line.stripped for line in lines if line.start >= heading_end and line.end <= paragraph_start]
    return all(not text or re.fullmatch(r"\d{1,2}", text) or FOOTER.match(text) for text in between)
