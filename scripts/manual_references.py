"""Literal DMG/ADM reference observations, separate from legal dependencies.

A range is retained as a range, never expanded into required paragraphs. A
chapter with a part is not reduced to the chapter. List scope is inherited only
across an explicit separator and a compatible full paragraph identifier.
"""
from __future__ import annotations

import re

LABEL = r"(?:[A-Z]\d{4,5}|\d{5,6})"
SINGLE = re.compile(r"\b(?:(?P<manual>DMG|ADM)\s+)?(?P<cue>Chapter\s+|(?:see|at|paragraphs?|paras?)\s+)?"
                    r"(?P<label>" + LABEL + r"|[A-Z]\d{1,2}|\d{1,2})\b", re.I)
RANGE = re.compile(r"\s*(?:[-–—]|to\b)\s*(?P<upper>" + LABEL + r")\b", re.I)
UNSUPPORTED_RANGE = re.compile(r"\s*(?:[-–—/]|to\b)\s*(?P<upper>[A-Z]?\d{1,6})\b", re.I)
PART = re.compile(r"\s+(?P<marker>Parts?)\s+(?P<part>[A-Za-z0-9]+)\b", re.I)
MORE_PARTS = re.compile(r"\s*(?:,|and/or\b|and\b|&|[-–—/]|to\b)\s*(?:Parts?\s+[A-Za-z0-9]+|(?:\d{1,2}|[IVXLCDM]+)\b)", re.I)
SUPPORTED_AT = re.compile(r"(?:guidance|defined|described|set out)\s+$", re.I)
LIST_SPACE = r"[ \t]*(?:\r?\n[ \t]*)?"
LIST_GAP = r"(?:[ \t]+|[ \t]*\r?\n[ \t]*)"
CONTINUATION = re.compile(LIST_SPACE + r"(?:," + LIST_SPACE + r"(?:and" + LIST_GAP + r")?|and" + LIST_GAP + r"|&" + LIST_GAP + r")(?P<label>" + LABEL + r")\b", re.I)
MEMO = re.compile(r"\b(?:(?P<before>DMG|ADM)\s+Memo(?:randum)?|Memo(?:randum)?\s+(?P<after>DMG|ADM))\s+(?P<number>\d{1,2}[-/]\d{2,4})\b", re.I)
LEGISLATION = re.compile(r"\b([A-Z][A-Za-z]*(?:[ \t]+(?:[A-Za-z]+|\([A-Z]+\))){0,5}[ \t]+(?:Regs|Act)(?:[ \t]+\d{2,4})?)[ \t]*,[ \t]*((?:reg|s|art)\s+\d+[A-Za-z]?(?:\([0-9A-Za-z]+\))*)")


def compatible(manual, label):
    return bool(re.fullmatch(LABEL, label)) and ((manual == "adm") == label[0].isalpha())


def paragraph_references(text, family):
    """Observe explicitly cued references and their exact original UTF-8 spans."""
    if family not in {"dmg", "adm"}:
        raise ValueError("Unknown source manual family")
    found = []
    consumed = set()

    def row(start, end, manual, kind, target, **extra):
        return {"manual": manual, "target_kind": kind, "target_label": target,
                "literal": text[start:end], "start_utf8": len(text[:start].encode()),
                "end_utf8": len(text[:end].encode()), "relationship_role": "source-reference",
                "legal_dependency": "not-established", **extra}

    def paragraph(start, end, manual, label, **extra):
        match = RANGE.match(text, end)
        if match:
            upper = match["upper"].upper()
            prefix = re.match(r"[A-Z]*", label)[0]
            upper_prefix = re.match(r"[A-Z]*", upper)[0]
            ordered = prefix == upper_prefix and int(label[len(prefix):]) <= int(upper[len(upper_prefix):])
            return row(start, match.end(), manual, "paragraph-range", label + "–" + upper,
                       lower_label=label, upper_label=upper,
                       range_status="literal-unexpanded" if ordered and compatible(manual, upper) else "unresolved-range-scope",
                       **extra), match.end()
        unsupported = UNSUPPORTED_RANGE.match(text, end)
        if unsupported:
            return row(start, unsupported.end(), manual, "unresolved-reference", label + "–" + unsupported["upper"].upper(),
                       lower_label=label, upper_literal=unsupported["upper"],
                       reference_scope_status="unsupported-slash-reference" if unsupported[0].lstrip().startswith("/") else "abbreviated-range-not-expanded", **extra), unsupported.end()
        return row(start, end, manual, "paragraph", label, **extra), end

    for hit in SINGLE.finditer(text):
        if hit.start() in consumed:
            continue
        manual, cue, label = hit["manual"], hit["cue"] or "", hit["label"].upper()
        if not manual and not cue:
            continue
        explicit_manual = bool(manual)
        manual = manual.lower() if manual else family
        if cue.lower().strip() == "at" and not explicit_manual and not SUPPORTED_AT.search(text[max(0, hit.start()-40):hit.start()]):
            if re.fullmatch(LABEL, label):
                found.append(row(hit.start(), hit.end(), manual, "unresolved-reference", label,
                                 reference_scope_status="at-without-guidance-cue"))
            continue
        if cue.lower().startswith("chapter"):
            if not re.fullmatch(r"[A-Z]?\d{1,2}", label):
                continue
            part = PART.match(text, hit.end())
            if part:
                end = part.end()
                extra_part = MORE_PARTS.match(text, end)
                multiple = bool(extra_part) or part["marker"].lower() == "parts"
                while extra_part:
                    end = extra_part.end()
                    extra_part = MORE_PARTS.match(text, end)
                if re.fullmatch(r"\d{1,2}", part["part"]) and not multiple:
                    found.append(row(hit.start(), end, manual, "chapter-part", label + " Part " + part["part"],
                                     chapter_label=label, part_label=part["part"]))
                else:
                    found.append(row(hit.start(), end, manual, "unresolved-reference",
                                     label + text[hit.end():end], chapter_label=label,
                                     part_literal=text[hit.end():end].strip(),
                                     reference_scope_status="multiple-or-unsupported-part-qualifier"))
            else:
                found.append(row(hit.start(), hit.end(), manual, "chapter", label))
            continue
        if not re.fullmatch(LABEL, label):
            continue
        # An explicitly conflicting manual/label remains visible but cannot be
        # promoted to an ordinary uniquely resolvable paragraph target.
        if not compatible(manual, label):
            found.append(row(hit.start(), hit.end(), manual, "unresolved-reference", label,
                             reference_scope_status="manual-label-conflict"))
            continue
        reference, cursor = paragraph(hit.start(), hit.end(), manual, label)
        found.append(reference)
        while True:
            following = CONTINUATION.match(text, cursor)
            if not following or not compatible(manual, following["label"].upper()):
                break
            start = following.start("label")
            consumed.add(start)
            reference, cursor = paragraph(start, following.end(), manual, following["label"].upper(),
                                          scope_basis="preceding-explicit-reference-list",
                                          scope_anchor_start_utf8=len(text[:hit.start()].encode()))
            found.append(reference)
    for hit in MEMO.finditer(text):
        found.append(row(hit.start(), hit.end(), (hit["before"] or hit["after"]).lower(), "memo", hit["number"]))
    for hit in LEGISLATION.finditer(text):
        found.append(row(hit.start(), hit.end(), family, "legislation", re.sub(r"\s+", " ", hit[0])))
    unique = {(r["start_utf8"], r["end_utf8"], r["manual"], r["target_kind"], r["target_label"]): r for r in found}
    return sorted(unique.values(), key=lambda r: (r["start_utf8"], r["end_utf8"], r["target_kind"]))
