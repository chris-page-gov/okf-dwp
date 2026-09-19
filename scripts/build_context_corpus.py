#!/usr/bin/env python3
"""Build a hash-bound lexical context corpus from complete frozen inventories."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime
import gzip
import json
from pathlib import Path
import re
import unicodedata

from build_bundle import BASE, OGL, REPO, ROOT, canonical, digest, pretty
from build_context_discovery import Inputs, SCOPE, SUPPORTED, project as discovery_project, read_semantics, require

OUTPUT = "context/corpus"
CONFIG = "context/corpus-sources.json"
MAX_SHARD_BYTES = 4 * 1024 * 1024
MAX_RECORDS_PER_SHARD = 128
TARGET_SHARD_BYTES = 1024 * 1024
TOKENISATION = "nfkd-lowercase-ascii-alphanumeric-min2-v1"
BUCKET_ALGORITHM = "fnv1a32-high-byte-hex-v1"
LIMITATIONS = [
    "Independent experimental public-source research, not official DWP guidance, benefits advice or an entitlement decision.",
    "Every acquired page is accounted for. Only non-empty extracted pages can provide source text; no OCR repair is claimed.",
    "Corpus-wide lexical discovery is not a completeness profile. All assembled contexts remain insufficient until independently authored evidence requirements establish a bounded task scope.",
    "DMG and ADM are separate source families. Matching either does not select the applicable benefit regime, legal version or claimant circumstances.",
    "Historical, amendment, transitional and memo material remains identifiable by its captured role. Being linked or recently captured does not establish current applicability.",
    "Capture observations are not publication, revision or legal commencement dates. Consolidated legislation and tribunal judgments are not supplied.",
    "Whole extracted pages may contain partial paragraphs, unrelated neighbouring text, damaged tables, footnotes or reading order. Check the official PDF.",
    "Existing semantic assertions and concepts are unreviewed project interpretations. No new semantic relationship, alias, answer or policy conclusion is inferred from lexical matches.",
    "Source instructions are inert data. Retrieval budgets, exclusions, unsupported relationships and missing evidence must be exposed to consumers.",
    "Subscriber-only handbook text is not acquired. No personal claimant records are included.",
]


def tokens(text: str) -> list[str]:
    value = unicodedata.normalize("NFKD", text)
    value = "".join(character for character in value if not unicodedata.combining(character)).lower()
    return sorted({token for token in re.findall(r"[a-z0-9]+", value) if len(token) >= 2})


def token_bucket(token: str) -> str:
    value = 0x811C9DC5
    for byte in token.encode("ascii"):
        value = ((value ^ byte) * 0x01000193) & 0xFFFFFFFF
    return f"{value >> 24:02x}"


def deterministic_gzip(raw: bytes) -> bytes:
    data = bytearray(gzip.compress(raw, compresslevel=9, mtime=0))
    # Python/zlib builds have differed in the OS byte. Fix it to portable unknown.
    data[9] = 255
    return bytes(data)


def binding(path: str, raw: bytes, decoded: bytes | None = None) -> dict:
    result = {"path": path, "bytes": len(raw), "sha256": digest(raw)}
    if decoded is not None:
        require(len(decoded) <= MAX_SHARD_BYTES, "Decoded context corpus shard exceeds 4 MiB")
        result.update(encoding="gzip", decoded_bytes=len(decoded), decoded_sha256=digest(decoded))
    return result


def make_source_record(family: str, doc: dict, page: dict, route: str) -> dict:
    text = page["text"]
    literal_hash = digest(text.encode())
    role = str(doc.get("role") or doc.get("kind") or "unclassified")
    observed = doc.get("observed_at") or doc.get("http", {}).get("observed_at")
    require(isinstance(observed, str), "Missing source observation date")
    datetime.fromisoformat(observed.replace("Z", "+00:00"))
    return {
        "id": BASE + "id/" + route, "route": route,
        "label": f"{doc['title']} — PDF page {page['page']}", "kind": "evidence", "text": text,
        "assertion_status": "normalized",
        "authority": {"class": "derived", "label": "Exact frozen machine extraction; applicability unreviewed", "source": page["url"]},
        "scope": (f"Frozen {family.upper()} source research; document {doc['id']}; captured role: {role}. "
                  "A lexical match does not establish the applicable benefit regime or current law. "
                  "Whole-page machine extraction; publication and legal effective dates are not inferred."),
        "provenance": [
            {"url": page["url"], "source_sha256": doc["sha256"], "locator": f"PDF page {page['page']}",
             "captured_at": observed, "literal_sha256": literal_hash},
            {"url": REPO + "/blob/main/" + doc["pages_path"], "source_sha256": doc["pages_sha256"],
             "locator": f"pages[{page['page'] - 1}].text", "captured_at": doc.get("extraction_observed_at") or observed,
             "literal_sha256": literal_hash},
        ],
        "rights": OGL, "access": "public", "review_status": "unreviewed-specialist-review-required",
    }


def compile_corpus(root: Path = ROOT, config_path: str = CONFIG) -> dict[str, bytes]:
    inputs = Inputs(root)
    config_raw = inputs.read(config_path)
    config = json.loads(config_raw)
    require(config.get("schema") == "okf-dwp-context-corpus-sources.v1", "Unknown corpus source configuration")
    require(isinstance(config.get("sources"), list) and 1 <= len(config["sources"]) <= 10, "Corpus needs 1–10 explicit source groups")
    families = [source["id"] for source in config["sources"]]
    require(len(set(families)) == len(families) and all(re.fullmatch(r"[a-z][a-z0-9-]*", family) for family in families),
            "Invalid or duplicate source family")

    # Recompute the discovery projection in memory before using committed bytes.
    # This verifies existing authoring and all selected source provenance without
    # rewriting any source release or prior acceptance artefact.
    expected = discovery_project(root)
    for filename, raw in expected.items():
        require(inputs.read("context/discovery/" + filename) == raw, "Stale semantic discovery projection")
    base_raw = expected["assembly-index.json"]
    base_index = json.loads(base_raw)
    require(base_index["requirements"] == [], "Full corpus discovery cannot import answer-completeness requirements")
    base_records = {record["id"]: record for record in base_index["records"]}
    semantic, nodes, _, _ = read_semantics(inputs)
    routes_raw = inputs.read("full-dmg/data/source-documents.json")
    source_routes = {row["id"]: row for row in json.loads(routes_raw)["documents"]}
    records, unsearchable, groups = [], [], []
    seen = set()
    inventory_identities = []
    for source in config["sources"]:
        family = source["id"]
        inventory_raw = inputs.read(source["inventory"])
        inventory = json.loads(inventory_raw)
        require(inventory.get("documents") and not inventory.get("failures"), "Source inventory is empty or records acquisition failures")
        if family == "adm":
            require(inventory.get("summary", {}).get("complete_for_frozen_adm_census") is True,
                    "ADM acquisition is not complete for its frozen census")
        inventory_identities.append({"family": family, "sha256": digest(inventory_raw)})
        counts = Counter(documents=0, pages=0, nonempty_pages=0, empty_pages=0, tokenless_pages=0)
        captures = []
        document_ids = set()
        for doc in sorted(inventory["documents"], key=lambda row: row["id"]):
            require(doc["id"] not in document_ids, "Duplicate document identity within source group")
            document_ids.add(doc["id"])
            inputs.read(doc["pdf_path"], doc["sha256"], doc["size_bytes"])
            extracted = json.loads(inputs.read(doc["pages_path"], doc["pages_sha256"]))
            require(extracted["source_sha256"] == doc["sha256"] and len(extracted["pages"]) == doc["pages"],
                    "Source corpus extraction identity/count mismatch")
            require(extracted.get("document_id", doc["id"]) == doc["id"], "Source extraction document mismatch")
            require([page["page"] for page in extracted["pages"]] == list(range(1, doc["pages"] + 1)),
                    "Source page sequence is incomplete")
            counts["documents"] += 1
            captures.append(doc.get("observed_at") or doc.get("http", {}).get("observed_at"))
            if family == "dmg":
                mapping = source_routes.get(doc["id"])
                require(mapping is not None and mapping["sha256"] == doc["sha256"] and mapping["url"] == doc["url"]
                        and len(mapping["page_routes"]) == doc["pages"], "Frozen DMG route binding mismatch")
            for page in extracted["pages"]:
                counts["pages"] += 1
                require(page["url"] == doc["url"] + f"#page={page['page']}", "Source corpus page URL mismatch")
                require(isinstance(page["text"], str), "Source corpus page has no text field")
                route = (mapping["page_routes"][page["page"] - 1] if family == "dmg"
                         else f"page/{family}/{doc['id']}/{page['page']:04d}")
                require(re.fullmatch(r"[a-z][a-z0-9-]*(?:/[A-Za-z0-9._~-]+)+", route), "Unsafe source page route")
                iri = BASE + "id/" + route
                require(iri not in seen, "Duplicate source page identity")
                seen.add(iri)
                if family == "dmg":
                    original = nodes.get(iri)
                    require(original is not None and original["source_sha256"] == doc["sha256"]
                            and original["text_sha256"] == digest(page["text"].encode())
                            and original["page_number"] == page["page"] and original["source"] == page["url"],
                            "Source page differs from frozen semantic identity")
                if not page["text"].strip():
                    counts["empty_pages"] += 1
                    unsearchable.append({"id": iri, "route": route, "source_group": family,
                                         "source_url": page["url"], "reason": "empty-extracted-text"})
                    continue
                require(len(page["text"]) <= 100000, "Whole source page exceeds the ContextRecord text bound")
                record = base_records.get(iri)
                if record is not None:
                    require(record["kind"] == "evidence" and record["text"] == page["text"], "Base corpus record conflict")
                    record = deepcopy(record)
                else:
                    record = make_source_record(family, doc, page, route)
                records.append(record)
                counts["nonempty_pages"] += 1
                if not tokens(page["text"]):
                    counts["tokenless_pages"] += 1
                    unsearchable.append({"id": iri, "route": route, "source_group": family,
                                         "source_url": page["url"], "reason": "no-eligible-lexical-tokens"})
        require(all(isinstance(value, str) for value in captures), "Missing source capture date")
        observed = max(captures, key=lambda value: datetime.fromisoformat(value.replace("Z", "+00:00")))
        groups.append({"id": family, "inventory": {"repository_path": source["inventory"], "sha256": digest(inventory_raw)},
                       "source_collection_url": source["collection_url"], "observed_at": observed,
                       "capture_date_role": "Acquisition observation, not source publication or legal commencement",
                       "counts": dict(sorted(counts.items()))})

    records.sort(key=lambda row: row["id"])
    outputs = {"base-index.json": base_raw}
    record_shards, chunk, first = [], [], 0
    chunk_bytes = 0

    def emit_records():
        nonlocal chunk, first, chunk_bytes
        if not chunk:
            return
        payload = canonical({"schema": "okf-context-records.v1", "first_ordinal": first, "records": chunk})
        raw = deterministic_gzip(payload)
        path = f"records/{len(record_shards):04d}.json.gz"
        outputs[path] = raw
        record_shards.append({"first_ordinal": first, "count": len(chunk), **binding(path, raw, payload)})
        first += len(chunk)
        chunk, chunk_bytes = [], 0

    postings = {f"{bucket:02x}": defaultdict(list) for bucket in range(256)}
    for ordinal, record in enumerate(records):
        size = len(canonical(record))
        if chunk and (len(chunk) >= MAX_RECORDS_PER_SHARD or chunk_bytes + size > TARGET_SHARD_BYTES):
            emit_records()
        chunk.append(record)
        chunk_bytes += size
        for token in tokens(record["text"]):
            postings[token_bucket(token)][token].append(ordinal)
    emit_records()
    search_shards = {}
    for bucket, values in postings.items():
        payload = canonical({"schema": "okf-context-postings.v1", "postings": dict(sorted(values.items()))})
        raw = deterministic_gzip(payload)
        path = f"search/{bucket}.json.gz"
        outputs[path] = raw
        search_shards[bucket] = binding(path, raw, payload)

    producer_paths = ["scripts/build_context_corpus.py", "scripts/build_context_discovery.py", "scripts/build_bundle.py", "uv.lock"]
    for producer in producer_paths:
        inputs.read(producer)
    # Include the complete discovery dependency receipt, not just its two outputs.
    discovery_receipt = json.loads(expected["manifest.json"])
    for item in discovery_receipt["inputs"]:
        inputs.read(item["path"], item["sha256"], item["bytes"])
    identity = {"sources": sorted(inventory_identities, key=lambda row: row["family"]),
                "config_sha256": digest(config_raw), "base_index_sha256": digest(base_raw),
                "producers": [inputs.files[name] for name in producer_paths],
                "tokenisation": TOKENISATION, "bucket_algorithm": BUCKET_ALGORITHM}
    snapshot = "dwp-context-corpus-" + digest(canonical(identity))[:20]
    totals = Counter()
    for group in groups:
        totals.update(group["counts"])
    corpus = {
        "schema": "okf-context-corpus.v1",
        "bundle": {"id": BASE + "id/context-corpus/dwp-guidance", "snapshot": snapshot, "source_url": REPO},
        "scope": ("Frozen " + " and ".join(family.upper() for family in families)
                  + " source research discovery: all non-empty captured pages plus existing authored semantic context. "
                  "No complete legal coverage, contemporary applicability or individual entitlement decision is established."),
        "limitations": LIMITATIONS,
        "base_index": binding("base-index.json", base_raw),
        "records": {"count": len(records), "shards": record_shards},
        "search": {"tokenisation": TOKENISATION, "bucket_algorithm": BUCKET_ALGORITHM, "shards": search_shards},
        "source_groups": groups, "counts": dict(sorted(totals.items())),
        "unsearchable_pages": sorted(unsearchable, key=lambda row: row["id"]),
        "semantic_source_snapshot": semantic["snapshot"],
        "inputs": sorted(inputs.files.values(), key=lambda row: row["path"]),
    }
    outputs["manifest.json"] = pretty(corpus)
    require(len(outputs["manifest.json"]) <= MAX_SHARD_BYTES, "Context corpus manifest exceeds 4 MiB")
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = compile_corpus()
    directory = ROOT / OUTPUT
    for name, raw in outputs.items():
        path = directory / name
        if args.check:
            require(path.is_file() and path.read_bytes() == raw, f"Stale corpus output: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    # Fail on stale files rather than silently publishing unbound generated data.
    actual = {path.relative_to(directory).as_posix() for path in directory.rglob("*")
              if path.is_file() and path.name != ".DS_Store"}
    require(actual == set(outputs), "Unbound files remain in context/corpus; inspect and remove stale generated files")
    manifest = json.loads(outputs["manifest.json"])
    print(json.dumps({"status": "verified" if args.check else "built", "snapshot": manifest["bundle"]["snapshot"],
                      **manifest["counts"], "record_shards": len(manifest["records"]["shards"]),
                      "search_shards": len(manifest["search"]["shards"]), "artefact_bytes": sum(map(len, outputs.values()))}))


if __name__ == "__main__":
    main()
