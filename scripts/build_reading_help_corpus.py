#!/usr/bin/env python3
"""Build source-bound reading-help candidates from the adopted DMG/ADM units."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path
import re

from build_logical_units import Inputs, canonical, require, sha
from manual_references import paragraph_references

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ("okf-reading-help-catalogue.v1", "okf-reading-help-document.v1", "okf-reading-help.v2")
RULE = "deterministic-reading-help-2026-09-26.v1"
MAX_LEAF = 256 * 1024
TARGET_LEAF = MAX_LEAF - 8192
ABBREV = re.compile(r"\b[A-Z][A-Z0-9]{1,7}\b")
DEFINITION = re.compile(r"(?m)^\s*([A-Z][A-Z0-9]{1,7})\s+(?:means|stands for)\s+([^\n.]{3,100})")
TABLE_ROW = re.compile(r'(?m)^([ \t]*)([“"]?)([A-Z][A-Z0-9]{1,7})([”"]?)[ \t]{2,}([^\n]{3,120})$')
PHRASE = re.compile(r"\b(?:[A-Za-z][a-z]+\s+){2,3}[A-Za-z][a-z]+\b")
FOOTER_ROW = re.compile(r"(?m)^([1-9][0-9]?)\s{2,}([^\n]{10,180})$")


def binding(path, data):
    return {"url": path, "path": path, "sha256": sha(data), "bytes": len(data)}


def location(unit, start, end):
    cursor = 0
    for number, span in enumerate(unit["spans"]):
        cursor += bool(number)  # The adopted producer joins source spans with one newline.
        length = span["end_utf8"] - span["start_utf8"]
        if cursor <= start < end <= cursor + length:
            return {"page": span["page"], "start_utf8": span["start_utf8"] + start - cursor,
                    "end_utf8": span["start_utf8"] + end - cursor}
        cursor += length
    return None


def unit_offset(unit, source):
    cursor = 0
    for number, span in enumerate(unit["spans"]):
        cursor += bool(number)
        if (span["page"] == source["page"] and span["start_utf8"] <=
                source["start_utf8"] < span["end_utf8"]):
            return cursor + source["start_utf8"] - span["start_utf8"]
        cursor += span["end_utf8"] - span["start_utf8"]
    raise ValueError("Occurrence outside structured passage")


def segments(unit):
    data = unit["text"].encode("utf-8")
    out = []
    if not data:
        return [{"ordinal": 0, "start_utf8": 0, "end_utf8": 0,
                 "text": "", "sha256": sha(b"")}]
    start = 0
    while start < len(data):
        end = min(start + 8192, len(data))
        while end < len(data) and data[end] & 0xc0 == 0x80:
            end -= 1
        require(end > start, "Invalid UTF-8 split")
        part = data[start:end]
        out.append({"ordinal": len(out), "start_utf8": start, "end_utf8": end,
                    "text": part.decode("utf-8"), "sha256": sha(part)})
        start = end
    return out


def extract(unit, family, pages, definitions, docid):
    text = unit["text"]
    raw = text.encode("utf-8")
    matches = [(r["start_utf8"], r["end_utf8"], "manual_reference", r)
               for r in paragraph_references(text, family)]
    for match in ABBREV.finditer(text):
        if match.group() in definitions:
            matches.append((len(text[:match.start()].encode()), len(text[:match.end()].encode()),
                            "abbreviation", {"definitions": definitions[match.group()]}))
    matches.sort(key=lambda r: (r[0], -(r[1] - r[0]), r[2]))
    occurrences, cards, occupied = [], [], []
    for start, end, kind, detail in matches:
        if any(start < high and end > low for low, high in occupied):
            continue
        span = location(unit, start, end)
        if not span:
            continue
        literal = raw[start:end]
        require(pages[span["page"]][span["start_utf8"]:span["end_utf8"]] == literal,
                "Source span differs")
        ident = sha(canonical([unit["id"], span, kind]))[:24]
        occurrences.append({"id": ident, "passage_id": unit["id"], "role": kind, **span,
                            "literal": literal.decode("utf-8"), "literal_sha256": sha(literal),
                            "status": "source_verified"})
        if kind == "abbreviation":
            candidates = detail["definitions"]
            cards.append({"id": "card-" + ident, "occurrence_id": ident, "kind": "expansion",
                          "status": "proposed" if len({d["expansion"] for d in candidates}) == 1 else "ambiguous",
                          "scope": {"target_document_id": docid, "source_table_document_ids": sorted({d["document_id"] for d in candidates})},
                          "source_table_rows": candidates})
        else:
            cards.append({"id": "card-" + ident, "occurrence_id": ident,
                          "kind": "citation_navigation", "target": {k: detail[k] for k in
                          ("manual", "target_kind", "target_label")},
                          "status": "unresolved" if detail["target_kind"] in
                          ("unresolved-reference", "paragraph-range") else "proposed"})
        occupied.append((start, end))
    return occurrences, cards


def definitions_and_phrases(units):
    definitions, proposals, phrases = defaultdict(set), [], defaultdict(set)
    for unit in units:
        for match in DEFINITION.finditer(unit["text"]):
            term, expansion = match.group(1), match.group(2).strip()
            if len(expansion.split()) <= 15:
                definitions[term].add(expansion)
                proposals.append({"term": term, "expansion": expansion,
                                  "passage_id": unit["id"], "scope": "document", "status": "proposed"})
        for phrase in set(m.group().lower() for m in PHRASE.finditer(unit["text"])):
            if len(phrase) >= 18:
                phrases[phrase].add(unit["id"])
    repeat = [{"literal": text, "passage_count": len(ids), "meaning": None,
               "scope": "document", "status": "proposed"}
              for text, ids in sorted(phrases.items()) if len(ids) >= 3][:100]
    return definitions, proposals, repeat


def reference_list_rows(unit, pages):
    rows = []
    text = unit["text"]
    for match in FOOTER_ROW.finditer(text):
        start = len(text[:match.start()].encode())
        end = len(text[:match.end()].encode())
        span = location(unit, start, end)
        if span is None:
            continue
        literal = text[match.start():match.end()].encode()
        require(pages[span["page"]][span["start_utf8"]:span["end_utf8"]] == literal,
                "Reference list row/source mismatch")
        rows.append({"occurrence_id": sha(canonical([unit["id"], span, "reference_list_row"]))[:24],
                     "passage_id": unit["id"], "marker": match.group(1), **span,
                     "literal": literal.decode(), "literal_sha256": sha(literal),
                     "status": "unresolved", "body_occurrence_ids": []})
    return rows


def abbreviation_tables(inputs, inventories):
    """Read only explicitly named printed abbreviation documents."""
    tables = defaultdict(lambda: defaultdict(list))
    for family, inventory in inventories.items():
        for row in inventory["documents"]:
            if "abbreviations" not in row["id"] or "summary-of-changes" in row["id"]:
                continue
            extraction_raw = inputs.read(row["pages_path"], row["pages_sha256"], limit=32*1024*1024)
            data = json.loads(extraction_raw)
            for page in data["pages"]:
                text = page["text"]
                for match in TABLE_ROW.finditer(text):
                    term, expansion = match.group(3), match.group(5).strip()
                    if not expansion[0].isalpha() and expansion[0] not in '“"':
                        continue
                    raw = text.encode("utf-8")
                    start = len(text[:match.start(2)].encode())
                    end = len(text[:match.end(5)].encode())
                    literal = raw[start:end]
                    tables[family][term].append({"document_id": row["id"], "page": page["page"],
                                                  "start_utf8": start, "end_utf8": end,
                                                  "literal": literal.decode("utf-8"),
                                                  "literal_sha256": sha(literal), "expansion": expansion,
                                                  "source_pdf_sha256": row["sha256"],
                                                  "extraction_sha256": sha(extraction_raw),
                                                  "printed_quoted_term": bool(match.group(2)),
                                                  "status": "source_verified"})
    return tables


def compile_corpus(root=ROOT, use_cache=True):
    inputs = Inputs(root)
    manifest_raw = inputs.read("structured-units/manifest.json")
    manifest = json.loads(manifest_raw)
    require(manifest["schema"] == "okf-dwp-structured-units.v1" and
            manifest["counts"]["units"] == 53727, "Adopted unit baseline differs")
    rules_hash = sha(canonical({"rule": RULE, "schemas": SCHEMAS,
                                "producer": inputs.read("scripts/build_reading_help_corpus.py").hex()[:0] or
                                inputs.files["scripts/build_reading_help_corpus.py"]["sha256"]}))
    source_paths, inventories = {}, {}
    for family, inventory_path in (("dmg", "source/full-dmg-2026-09-15/inventory.json"),
                                   ("adm", "source/adm-2026-09-19/inventory.json")):
        inventory = json.loads(inputs.read(inventory_path))
        inventories[family] = inventory
        source_paths.update({(family, row["id"]): row["pages_path"] for row in inventory["documents"]})
    tables = abbreviation_tables(inputs, inventories)
    outputs, doc_refs, totals = {}, [], Counter()
    for source_doc in manifest["documents"]:
        family, docid = source_doc["family"], source_doc["document_id"]
        structured_path = "structured-units/" + source_doc["path"]
        packed = inputs.read(structured_path, source_doc["sha256"], source_doc["bytes"], limit=64*1024*1024)
        unpacked = gzip.decompress(packed)
        require(sha(unpacked) == source_doc["decoded_sha256"], "Structured hash differs")
        doc = json.loads(unpacked)
        units = doc["units"]
        require(len(units) == source_doc["counts"]["units"], "Unit count differs")
        extraction_path = source_paths[(family, docid)]
        extraction = inputs.read(extraction_path, doc["source"]["pages_sha256"], limit=32*1024*1024)
        source = json.loads(extraction)
        require(source["source_sha256"] == doc["source"]["sha256"], "PDF identity differs")
        pages = {p["page"]: p["text"].encode("utf-8") for p in source["pages"]}
        base = f"reading-help-corpus/documents/{family}/{docid}"
        index_path = f"{base}/index.json"
        cached_path = root / index_path
        if use_cache and cached_path.is_file():
            cached_raw = cached_path.read_bytes()
            cached = json.loads(cached_raw)
            if (cached.get("schema") == SCHEMAS[1] and cached.get("rules_sha256") == rules_hash
                    and cached.get("extraction", {}).get("sha256") == sha(extraction)
                    and cached.get("structured_document", {}).get("sha256") == sha(packed)
                    and "occurrences" in cached.get("counts", {})):
                try:
                    cached_outputs = {index_path: cached_raw}
                    for leaf in cached["leaves"]:
                        leaf_data = (root / leaf["path"]).read_bytes()
                        require(len(leaf_data) == leaf["bytes"] and sha(leaf_data) == leaf["sha256"],
                                "Cached leaf hash differs")
                        cached_outputs[leaf["path"]] = leaf_data
                except (OSError, ValueError):
                    pass
                else:
                    outputs.update(cached_outputs)
                    doc_refs.append({"family": family, "document_id": docid,
                                     **binding(index_path, cached_raw), "counts": cached["counts"],
                                     "status": "extraction_blocked" if cached["extraction_blocked_pages"] else "processed"})
                    totals.update({"documents": 1, **cached["counts"]})
                    continue
        _local_defs, proposals, phrases = definitions_and_phrases(units)
        defs = tables[family]
        leaves, passage_refs, waiting = [], [], []
        detected_count = 0

        def flush():
            nonlocal waiting
            if not waiting:
                return
            path = f"{base}/leaves/{len(leaves):04d}.json.gz"
            data = canonical({"schema": SCHEMAS[2], "family": family, "document_id": docid,
                              "source_sha256": doc["source"]["sha256"],
                              "extraction_sha256": sha(extraction), "rules_sha256": rules_hash,
                              "source_instructions_inert": True, "passages": waiting})
            require(len(data) <= MAX_LEAF, "Leaf exceeds 256 KiB")
            packed = gzip.compress(data, mtime=0)
            outputs[path] = packed
            leaves.append({**binding(path, packed), "decoded_bytes": len(data),
                           "decoded_sha256": sha(data), "encoding": "gzip",
                           "passage_count": len(waiting)})
            waiting = []

        for unit in units:
            require(sha(unit["text"].encode()) == unit["text_sha256"], "Unit text differs")
            reconstructed = []
            for span in unit["spans"]:
                fragment = pages[span["page"]][span["start_utf8"]:span["end_utf8"]]
                require(sha(fragment) == span["literal_sha256"], "Structured source span differs")
                reconstructed.append(fragment)
            require(b"\n".join(reconstructed) == unit["text"].encode("utf-8"),
                    "Full structured unit/source reconstruction differs")
            occurrences, cards = extract(unit, family, pages, defs, docid)
            detected_count += len(occurrences)
            footer_rows = reference_list_rows(unit, pages)
            parts = segments(unit)
            for part in parts:
                # The exact source page span is the authority; use the corresponding
                # unit offset rather than a literal search when repetitions occur.
                part_occurrences = []
                for occurrence in occurrences:
                    unit_cursor = unit_offset(unit, occurrence)
                    if part["start_utf8"] <= unit_cursor < part["end_utf8"]:
                        part_occurrences.append(occurrence)
                part_ids = {o["id"] for o in part_occurrences}
                part_cards = [c for c in cards if c["occurrence_id"] in part_ids]
                row = {"id": unit["id"], "unit_sha256": unit["record_sha256"],
                       "role": unit["role"], "paragraph_labels": unit["paragraph_labels"],
                       "source_spans": unit["spans"], "text_sha256": unit["text_sha256"],
                       "segment": part, "segment_count": len(parts),
                       "passage_complete": len(parts) == 1,
                       "status": ("extraction_blocked" if not unit["text"] else
                                  "proposed" if part_occurrences else "processed"),
                       "occurrences": part_occurrences,
                       "cards": part_cards,
                       "reference_list_segments": [r for r in footer_rows if part["start_utf8"] <=
                                                   unit_offset(unit, r) < part["end_utf8"]]}
                if len(canonical(row)) > TARGET_LEAF:
                    row["status"] = "unsupported"
                    row["undelivered_candidate_count"] = len(row["occurrences"])
                    row["undelivered_reference_row_count"] = len(row["reference_list_segments"])
                    row["occurrences"], row["cards"] = [], []
                    row["reference_list_segments"] = []
                candidate = canonical({"passages": waiting + [row]})
                if waiting and len(candidate) > TARGET_LEAF:
                    flush()
                leaf_path = f"{base}/leaves/{len(leaves):04d}.json.gz"
                waiting.append(row)
                passage_refs.append({"unit_id": unit["id"], "unit_sha256": unit["record_sha256"],
                                     "role": unit["role"], "pages": [s["page"] for s in unit["spans"]],
                                     "segment_ordinal": part["ordinal"], "segment_count": len(parts),
                                     "leaf_url": leaf_path, "status": row["status"]})
            totals["passages"] += 1
        flush()
        leaf_by_path = {r["path"]: r for r in leaves}
        for row in passage_refs:
            row["leaf_sha256"] = leaf_by_path[row["leaf_url"]]["sha256"]
            row["leaf_bytes"] = leaf_by_path[row["leaf_url"]]["bytes"]
        empty = [p["page"] for p in source["pages"] if not p["text"].strip()]
        counts = {"pages": len(pages), "passages": len(units), "segments": len(passage_refs),
                  "leaves": len(leaves), "extraction_blocked_pages": len(empty),
                  "definition_proposals": len(proposals),
                  "unsupported_segments": sum(r["status"] == "unsupported" for r in passage_refs),
                  "detected_occurrences": detected_count,
                  "occurrences": sum(len(p["occurrences"]) for leaf in leaves for p in
                                     json.loads(gzip.decompress(outputs[leaf["path"]]))["passages"]),
                  "cards": sum(len(p["cards"]) for leaf in leaves for p in
                               json.loads(gzip.decompress(outputs[leaf["path"]]))["passages"])}
        totals.update({"occurrences": counts["occurrences"], "cards": counts["cards"],
                       "detected_occurrences": detected_count,
                       "unsupported_segments": counts["unsupported_segments"]})
        totals.update({"documents": 1, "pages": len(pages), "segments": len(passage_refs),
                       "leaves": len(leaves), "extraction_blocked_pages": len(empty),
                       "definition_proposals": len(proposals)})
        index = {"schema": SCHEMAS[1], "family": family, "document_id": docid,
                 "source": doc["source"], "extraction": binding(extraction_path, extraction),
                 "structured_document": binding(structured_path, packed), "rules_sha256": rules_hash,
                 "counts": counts, "extraction_blocked_pages": empty,
                 "passages": passage_refs, "leaves": leaves,
                 "abbreviation_definitions": proposals, "repeated_phrase_proposals": phrases,
                 "review": {"specialist_accepted": False, "legal_answerability": "not-established"}}
        path = index_path
        data = canonical(index)
        outputs[path] = data
        doc_refs.append({"family": family, "document_id": docid, **binding(path, data),
                         "counts": counts, "status": "extraction_blocked" if empty else "processed"})
    require((totals["documents"], totals["pages"], totals["passages"], totals["extraction_blocked_pages"])
            == (513, 19090, 53727, 893), "Corpus census differs")
    catalogue = {"schema": SCHEMAS[0], "status": "machine-proposed-unreviewed",
                 "structured_snapshot": manifest["snapshot"],
                 "structured_manifest": binding("structured-units/manifest.json", manifest_raw),
                 "rules_sha256": rules_hash, "counts": dict(totals), "documents": doc_refs,
                 "limitations": ["Every adopted structured passage is counted; extraction gaps are not blank PDFs.",
                                 "Proposals have no specialist legal review or established answerability."]}
    outputs["reading-help-corpus/manifest.json"] = canonical(catalogue)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = compile_corpus(use_cache=not args.check)
    if args.check:
        require({str(p.relative_to(ROOT)) for p in (ROOT / "reading-help-corpus").rglob("*") if p.is_file()}
                == set(outputs), "Output set differs")
        for path, data in outputs.items():
            require((ROOT / path).read_bytes() == data, f"Output differs: {path}")
    else:
        current = {str(p.relative_to(ROOT)) for p in (ROOT / "reading-help-corpus").rglob("*") if p.is_file()}
        for stale in current - set(outputs):
            (ROOT / stale).unlink()
        for path, data in outputs.items():
            target = ROOT / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    print(json.dumps({"status": "verified" if args.check else "built",
                      **json.loads(outputs["reading-help-corpus/manifest.json"])["counts"]}))


if __name__ == "__main__":
    main()
