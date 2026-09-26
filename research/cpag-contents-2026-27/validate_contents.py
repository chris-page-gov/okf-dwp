#!/usr/bin/env python3
"""Validate a metadata-only CPAG contents export using the Python standard library.

Usage:
  python3 validate_cpag_contents.py contents.json --output validation.json
  python3 validate_cpag_contents.py contents.json --expect-chapters 68 --expect-parts 10

Expected top-level fields: source_url, observed_at (ISO 8601), scope, entries.
Every entry has: id, title, url, kind, parent_id, order, observed_on.
``parent_id`` is null for root entries; ``observed_on`` is a source URL or a
non-empty list of source URLs. The numeric id is the observed CPAG node id.
Allowed kinds: front-matter, part, chapter, back-matter, appendix.

Checks establish structural integrity only. They do not prove that a source
page is complete or that any content may be republished. Expected final counts
must be supplied from acquisition evidence, never inferred as completeness.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from urllib.parse import parse_qs, unquote, urlsplit


KINDS = {"front-matter", "part", "chapter", "back-matter", "appendix"}
REQUIRED = {"id", "title", "url", "kind", "parent_id", "order", "observed_on"}


def cpag_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        url = urlsplit(value)
        return (
            url.scheme == "https"
            and url.hostname == "askcpag.org.uk"
            and url.username is None
            and url.password is None
            and url.port in (None, 443)
        )
    except ValueError:
        return False


def url_has_id(value: str, node_id: str) -> bool:
    """Accept query ids and exact numeric path segments; reject substring matches."""
    url = urlsplit(value)
    query_values = [v for values in parse_qs(url.query).values() for v in values]
    path_segments = [unquote(segment) for segment in url.path.split("/")]
    return node_id in query_values or node_id in path_segments


def roman_number(value: str) -> int:
    digits = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total, previous = 0, 0
    for char in reversed(value.upper()):
        current = digits[char]
        total += -current if current < previous else current
        previous = max(previous, current)
    return total


def title_number(title: str, kind: str) -> int | None:
    match = re.match(rf"^\s*{kind}\s+(\d+|[IVXLCDM]+)\b", title, re.IGNORECASE)
    if match is None:
        return None
    value = match.group(1)
    return int(value) if value.isdigit() else roman_number(value)


def validate(data: object, expected: dict[str, int | None]) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    report = {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "validation_scope": "Structural validation of an observed public contents metadata export; not independent proof of source completeness or permission.",
        "errors": errors,
        "warnings": warnings,
    }
    if not isinstance(data, dict):
        report.update(valid=False)
        errors.append("The export must be a JSON object.")
        return report
    for field in ("source_url", "observed_at", "scope", "entries"):
        if field not in data:
            errors.append(f"Missing top-level field: {field}.")
    if not cpag_url(data.get("source_url")):
        errors.append("source_url must be an HTTPS askcpag.org.uk URL.")
    observed = data.get("observed_at")
    try:
        parsed = datetime.fromisoformat(observed.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            errors.append("observed_at must include a time-zone offset.")
    except (AttributeError, TypeError, ValueError):
        errors.append("observed_at must be an ISO 8601 date and time.")
    if not isinstance(data.get("scope"), str) or not data["scope"].strip():
        errors.append("scope must be a non-empty description of the acquisition boundary.")
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("entries must be a non-empty list.")
        report.update(valid=False)
        return report

    ids: dict[str, dict] = {}
    seen_urls: dict[str, str] = {}
    kind_counts: Counter = Counter()
    numbered: dict[str, list[int]] = {"part": [], "chapter": []}
    sibling_order: dict[tuple, list[str]] = defaultdict(list)
    observed_pages: set[str] = set()
    for index, entry in enumerate(entries):
        label = f"Entry {index + 1}"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object.")
            continue
        missing = REQUIRED - entry.keys()
        if missing:
            errors.append(f"{label} is missing: {', '.join(sorted(missing))}.")
        node_id = entry.get("id")
        if not isinstance(node_id, str) or re.fullmatch(r"-?\d+", node_id) is None:
            errors.append(f"{label} id must be a numeric CPAG node id encoded as a string.")
        elif node_id in ids:
            errors.append(f"Duplicate node id: {node_id}.")
        else:
            ids[node_id] = entry
        title = entry.get("title")
        if not isinstance(title, str) or not title.strip():
            errors.append(f"{label} title must be a non-empty string.")
        url = entry.get("url")
        if not cpag_url(url):
            errors.append(f"{label} url must be an HTTPS askcpag.org.uk URL.")
        else:
            if isinstance(node_id, str) and not url_has_id(url, node_id):
                errors.append(f"{label} url does not contain its exact observed node id {node_id!r}.")
            if url in seen_urls:
                errors.append(f"Duplicate URL for {node_id!r} and {seen_urls[url]!r}: {url}")
            else:
                seen_urls[url] = str(node_id)
        kind = entry.get("kind")
        if not isinstance(kind, str) or kind not in KINDS:
            errors.append(f"{label} has unsupported kind {kind!r}.")
        else:
            kind_counts[kind] += 1
            if kind in numbered and isinstance(title, str):
                number = title_number(title, kind)
                if number is None or number < 1:
                    errors.append(f"{label} has no parseable {kind} number in title {title!r}.")
                else:
                    numbered[kind].append(number)
        parent_id = entry.get("parent_id")
        if parent_id is not None and not isinstance(parent_id, str):
            errors.append(f"{label} parent_id must be null or a string.")
        order = entry.get("order")
        if isinstance(order, bool) or not isinstance(order, int) or order < 0:
            errors.append(f"{label} order must be a non-negative integer.")
        elif isinstance(parent_id, str) or parent_id is None:
            sibling_order[(parent_id, order)].append(str(node_id))
        pages = entry.get("observed_on")
        if isinstance(pages, str):
            pages = [pages]
        if not isinstance(pages, list) or not pages:
            errors.append(f"{label} observed_on must be a URL or a non-empty list of URLs.")
        else:
            for page in pages:
                if not cpag_url(page):
                    errors.append(f"{label} observed_on contains an invalid HTTPS askcpag.org.uk URL.")
                else:
                    observed_pages.add(page)

    for node_id, entry in ids.items():
        parent_id = entry.get("parent_id")
        if isinstance(parent_id, str) and parent_id not in ids:
            errors.append(f"Unresolved parent {parent_id!r} for {node_id!r}.")
        visited = {node_id}
        while isinstance(parent_id, str) and parent_id in ids:
            if parent_id in visited:
                errors.append(f"Parent cycle detected from {node_id!r}.")
                break
            visited.add(parent_id)
            parent_id = ids[parent_id].get("parent_id")
    for (parent_id, order), siblings in sibling_order.items():
        if len(siblings) > 1:
            errors.append(f"Duplicate order {order} under parent {parent_id!r}: {', '.join(siblings)}.")

    sequences = {}
    for kind, values in numbered.items():
        sorted_values = sorted(values)
        last = max(values, default=0)
        missing = sorted(set(range(1, last + 1)) - set(values))
        duplicates = sorted(number for number, count in Counter(values).items() if count > 1)
        if not values:
            errors.append(f"No numbered {kind} entries found.")
        if missing:
            errors.append(f"{kind.capitalize()} sequence gaps: {missing}.")
        if duplicates:
            errors.append(f"Repeated {kind} numbers: {duplicates}.")
        if values != sorted_values:
            errors.append(f"{kind.capitalize()} entries are not in numeric source sequence.")
        expected_count = expected.get(kind)
        if expected_count is not None and len(values) != expected_count:
            errors.append(f"Expected {expected_count} {kind} entries; observed {len(values)}.")
        if expected_count is not None and last != expected_count:
            errors.append(f"Expected final {kind} number {expected_count}; observed {last}.")
        if expected_count is None:
            warnings.append(f"No independently evidenced final {kind} count supplied; a contiguous sequence does not establish full source coverage.")
        sequences[kind] = {"observed_count": len(values), "first": min(values, default=None), "last": last or None, "missing": missing, "duplicates": duplicates, "expected_count": expected_count}
    report.update(
        valid=not errors,
        source_url=data.get("source_url"),
        observed_at=observed,
        entry_count=len(entries),
        unique_id_count=len(ids),
        unique_url_count=len(seen_urls),
        kind_counts=dict(sorted(kind_counts.items())),
        observed_page_count=len(observed_pages),
        sequences=sequences,
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="JSON metadata export, or - for standard input")
    parser.add_argument("--output", type=Path, help="Also write the validation report to this path")
    parser.add_argument("--expect-chapters", type=int)
    parser.add_argument("--expect-parts", type=int)
    args = parser.parse_args()
    try:
        raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, ValueError) as exc:
        print(f"Cannot read metadata export: {exc}", file=sys.stderr)
        return 2
    report = validate(data, {"chapter": args.expect_chapters, "part": args.expect_parts})
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
