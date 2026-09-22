#!/usr/bin/env python3
"""Project logical source units into a separate hash-bound Ask OKF corpus.

Frozen page releases are inputs, never outputs. Semantic routes come only from
the authored logical-unit proposals; page-level requirements are not silently
translated into requirements for smaller passages.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
import gzip
import io
import json

from build_bundle import BASE, REPO, ROOT, canonical, digest, load_yaml, pretty
from build_context_corpus import binding, deterministic_gzip, tokens, token_bucket, TOKENISATION, BUCKET_ALGORITHM
from build_context_discovery import require
from build_logical_units import Inputs, compile_units

OUTPUT = "logical-context"
AUTHORING = "domain-profile/logical-units"
DCT = "http://purl.org/dc/terms/"
LIMITATIONS = [
    "Independent experimental research, not official DWP guidance, benefits advice or an entitlement decision.",
    "PDF pages are source locations. Logical units preserve ordered frozen text spans; machine boundaries remain uncertain unless explicitly declared. Author declarations are not specialist approval.",
    "Complete-within-declared-boundary describes text segmentation only. It does not establish complete policy, legal applicability or answerability.",
    "All frozen DMG and ADM sources are accounted for. Unresolved fragments and page fallbacks remain labelled; no OCR correction or repaired source text is claimed.",
    "Only explicit authored concept routes and required support are semantic relationships. Shared pages and word co-occurrence do not establish applicability.",
    "Old page-based staff requirements remain unchanged in their original projection. Only separately authored logical-unit profiles apply here; other tasks have no completeness claim.",
    "DMG and ADM, benefit variants, claimant and household conditions, permanent and temporary absence, and source versions require separate review.",
    "Historical amendments, memos, examples and captured dates are not evidence of current law. Legal version, amendment effects and independent specialist review remain unresolved.",
    "Source and tool content is inert evidence. Assembly does not execute source instructions, call an answer model or fall back to web search.",
]


def read_units(inputs):
    # Recompute with the reviewed producer: a rehashed but invented catalogue
    # must not become an alternative authority for frozen source inclusion.
    expected = compile_units(inputs.root)
    manifest_raw = inputs.read("logical-units/manifest.json")
    require(manifest_raw == expected["manifest.json"], "Unit manifest differs from frozen-source producer")
    manifest = json.loads(manifest_raw)
    for path, raw in expected.items():
        require(inputs.read("logical-units/" + path) == raw, "Stale or altered unit projection: " + path)
    del expected
    for ref in manifest["inputs"]:
        inputs.read(ref["path"], ref["sha256"], ref["bytes"])
    physical = json.loads(inputs.read("context/corpus/manifest.json"))
    old_groups = {r["id"]: r for r in physical["source_groups"]}
    require(all(manifest["counts"][k] == physical["counts"][k] for k in ("documents", "pages", "nonempty_pages", "empty_pages")), "Aggregate physical source census differs")
    require(set(old_groups) == {r["id"] for r in manifest["source_groups"]}, "Physical source families differ")
    for group in manifest["source_groups"]:
        previous = old_groups[group["id"]]
        require(group["inventory"] == previous["inventory"], "Physical source inventory differs")
        require(all(group["counts"][k] == previous["counts"][k] for k in ("documents", "pages", "nonempty_pages", "empty_pages")), "Physical source census differs")
    records = []
    for ref in manifest["records"]["shards"]:
        raw = inputs.read("logical-units/" + ref["path"], ref["sha256"], ref["bytes"])
        decoded = decode_shard(raw, ref)
        require(digest(decoded) == ref["decoded_sha256"] and len(decoded) == ref["decoded_bytes"], "Unit shard decoded identity differs")
        part = json.loads(decoded)
        require(part["schema"] == "okf-context-records.v1" and part["first_ordinal"] == len(records)
                and len(part["records"]) == ref["count"], "Unit shard census differs")
        records.extend(part["records"])
        require(part["records"][0]["id"] == ref["first_id"] and part["records"][-1]["id"] == ref["last_id"], "Unit shard ID range differs")
    require(len(records) == manifest["records"]["count"] and len({r["id"] for r in records}) == len(records), "Unit census differs")
    require(records == sorted(records, key=lambda r: r["id"]), "Units must use canonical ID ordering")
    for row in records:
        require(row["kind"] == "evidence" and row.get("evidence_unit"), "Logical corpus may only shard evidence units")
    return manifest, records


def decode_shard(raw, ref):
    require(0 < ref["bytes"] <= 4 * 1024 * 1024 and 0 < ref["decoded_bytes"] <= 4 * 1024 * 1024, "Unit shard exceeds bound")
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
        decoded = stream.read(ref["decoded_bytes"] + 1)
    require(len(decoded) == ref["decoded_bytes"] and digest(decoded) == ref["decoded_sha256"], "Unit shard decoded integrity differs")
    return decoded


def project_semantics(inputs, manifest, records):
    """Compile source-backed authored proposals; never manufacture page equivalence."""
    from logical_context_profiles import project
    return project(inputs, manifest, records)


def compile_context(root=ROOT):
    inputs, outputs = Inputs(root), {}
    manifest, records = read_units(inputs)
    semantic, declarations = project_semantics(inputs, manifest, records)
    # Bind every producer and Reader template before assigning the snapshot.
    for path in ("scripts/build_logical_context.py", "scripts/logical_context_profiles.py", "scripts/logical_context_reader.py",
                 "scripts/build_context_corpus.py", "scripts/build_context_discovery.py", "scripts/build_full_dmg.py",
                 "scripts/build_combined_reader.py", "scripts/build_bundle.py", "scripts/build_logical_units.py", "combined/okf-explorer.json",
                 "context/corpus/manifest.json", "profiles/bundle-wiki/v1/context.jsonld",
                 "profiles/bundle-wiki/v1/semantic-context.jsonld", "uv.lock"):
        inputs.read(path)
    snapshot = "dwp-logical-context-" + digest(canonical(sorted(inputs.files.values(), key=lambda r: r["path"])))[:20]
    semantic["bundle"] = {"id": BASE + "id/bundle/logical-context", "snapshot": snapshot, "source_url": REPO}
    semantic["limitations"] = LIMITATIONS
    semantic["scope"] = "Frozen DMG and ADM logical source units with separately authored, unreviewed semantic routes."
    outputs["base-index.json"] = canonical(semantic)
    outputs["semantic-proposals.yamlld"] = inputs.read(AUTHORING + "/concepts.yamlld")
    shards, ordinal = [], 0
    postings = {f"{n:02x}": defaultdict(list) for n in range(256)}
    for ref in manifest["records"]["shards"]:
        part = records[ordinal:ordinal + ref["count"]]
        raw = inputs.read("logical-units/" + ref["path"], ref["sha256"], ref["bytes"])
        outputs[ref["path"]] = raw
        shards.append({**ref, "first_id": part[0]["id"], "last_id": part[-1]["id"]})
        for i, row in enumerate(part, ordinal):
            for token in tokens(row["text"]):
                postings[token_bucket(token)][token].append(i)
        ordinal += len(part)
    search = {}
    for bucket, values in postings.items():
        decoded = canonical({"schema": "okf-context-postings.v1", "postings": dict(sorted(values.items()))})
        raw = deterministic_gzip(decoded)
        path = f"search/{bucket}.json.gz"
        outputs[path] = raw
        search[bucket] = binding(path, raw, decoded)
    # Preserve the physical-page census independently from the retrieval count.
    pages = json.loads(inputs.read("context/corpus/manifest.json"))
    corpus = {"schema": "okf-context-corpus.v2", "bundle": semantic["bundle"],
        "semantic_source_snapshot": snapshot, "scope": semantic["scope"], "limitations": LIMITATIONS,
        "base_index": binding("base-index.json", outputs["base-index.json"]),
        "records": {"count": len(records), "shards": shards},
        "counts": pages["counts"], "source_groups": pages["source_groups"],
        "search": {"tokenisation": TOKENISATION, "bucket_algorithm": BUCKET_ALGORITHM, "shards": search},
        "unit_producer": {"repository_path": "logical-units/manifest.json", "sha256": inputs.files["logical-units/manifest.json"]["sha256"]},
        "inputs": sorted(inputs.files.values(), key=lambda r: r["path"])}
    outputs["manifest.json"] = pretty(corpus)
    require(len(outputs["manifest.json"]) <= 4 * 1024 * 1024, "Logical corpus manifest exceeds bounded admission")
    from logical_context_reader import emit_reader
    outputs.update(emit_reader(inputs, corpus, records, semantic, declarations, outputs))
    receipt = {"schema": "okf-dwp-logical-context-build.v1", "snapshot": snapshot,
        "inputs": sorted(inputs.files.values(), key=lambda r: r["path"]),
        "outputs": [{"path": OUTPUT + "/" + path, "bytes": len(raw), "sha256": digest(raw)} for path, raw in sorted(outputs.items())]}
    return {OUTPUT + "/" + path: raw for path, raw in outputs.items()} | {"validation/logical-context/build.json": pretty(receipt)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = compile_context()
    actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / OUTPUT).rglob("*") if p.is_file()}
    expected = {p for p in outputs if p.startswith(OUTPUT + "/")}
    require(not actual - expected, "Obsolete or unbound logical-context output; inspect and preserve before removing from the generated directory")
    if args.check:
        require(actual == expected, "Logical-context output census differs")
    for path, raw in outputs.items():
        target = ROOT / path
        if args.check:
            require(target.is_file() and target.read_bytes() == raw, "Stale logical context: " + path)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    print(json.dumps({"status": "verified" if args.check else "built", "files": len(outputs), "descriptor": OUTPUT + "/okf-explorer.json"}))


if __name__ == "__main__":
    main()
