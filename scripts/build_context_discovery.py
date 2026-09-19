#!/usr/bin/env python3
"""Project broader research context without changing the frozen full-DMG release.

This is a deterministic view of existing semantic assertions, not new modelling,
question-specific retrieval or a completeness profile. No network access occurs.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import gzip
import json
from pathlib import Path

from build_bundle import BASE, OGL, REPO, ROOT, canonical, digest, load_yaml, pretty

OUTPUT = "context/discovery"
INVENTORY = "source/full-dmg-2026-09-15/inventory.json"
MAX_INDEX_BYTES = 4 * 1024 * 1024
MAX_SHARD_BYTES = 5 * 1024 * 1024
PART_OF = "http://purl.org/dc/terms/isPartOf"
SUPPORTED = {
    "http://purl.org/dc/terms/references", "http://purl.org/dc/terms/requires",
    "http://www.w3.org/2004/02/skos/core#related",
    "http://www.w3.org/2004/02/skos/core#broader",
    "http://www.w3.org/2004/02/skos/core#narrower",
}
SCOPE = (
    "Frozen full-DMG research discovery: existing authored concepts, their cited "
    "whole extracted pages and existing directed relationships. No complete legal "
    "coverage, contemporary applicability or individual entitlement decision is established."
)
LIMITATIONS = [
    "Independent experimental publication, not official DWP guidance, benefits advice or an entitlement decision.",
    "This projection has no completeness requirements. Retrieved material is a research lead; evidence_status must remain insufficient.",
    "The complete source collection contains 331 PDFs and 14,743 measured pages. This context projection contains only pages cited by existing semantic concepts plus the separately authored custody context; full source capture is not complete context coverage.",
    "Concept definitions, query aliases and semantic relationships are existing project-authored interpretations requiring specialist review. No new synonyms, questions, answers or legal outcomes are inferred by this build.",
    "Whole machine-extracted pages retain neighbouring and partial paragraphs. Tables, footnotes, reading order, dates and current applicability require checking against the official PDF.",
    "A source capture date is not a publication, revision or commencement date. Historical, amendment, transitional and memo material retains its captured document classification.",
    "ADM bodies, statutory provision text, tribunal judgments and subscriber handbook contents are not acquired by this projection.",
    "Traversal retains original direction and predicates. Unsupported predicates are exposed by the context engine; no replacement predicate or inverse edge is invented.",
    "Source containment edges are excluded from this context view. Source URLs, document identities, page locators and hashes remain in provenance; containment remains available in the full semantic graph.",
    "Discovery uses the consumer's declared-phrase resolver. Missing aliases and non-matching natural-language phrases can prevent retrieval even where captured sources contain relevant text.",
]


def require(condition: bool, message: str):
    if not condition:
        raise ValueError(message)


class Inputs:
    """Read only repository-local bytes and retain a deterministic input receipt."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.files: dict[str, dict] = {}

    def path(self, relative: str) -> Path:
        require(isinstance(relative, str) and not Path(relative).is_absolute(), "Input path must be relative")
        path = (self.root / relative).resolve()
        require(path.is_relative_to(self.root), "Input path escapes the repository")
        return path

    def read(self, relative: str, expected: str | None = None, size: int | None = None) -> bytes:
        raw = self.path(relative).read_bytes()
        sha = digest(raw)
        require(expected is None or sha == expected, f"Input digest mismatch: {relative}")
        require(size is None or len(raw) == size, f"Input size mismatch: {relative}")
        self.files[relative] = {"path": relative, "sha256": sha, "bytes": len(raw)}
        return raw

    def bound(self, base: str, binding: dict) -> bytes:
        return self.read(str(Path(base) / binding["path"]), binding["sha256"], binding["bytes"])


def read_semantics(inputs: Inputs) -> tuple[dict, dict, list, dict]:
    control_path = "full-dmg/okf-bundle.yamlld"
    inputs.read(control_path)
    control = load_yaml(inputs.path(control_path))
    manifest = json.loads(inputs.bound("full-dmg", control["semantic_manifest"]))
    snapshot = control["snapshot_id"]
    require(manifest["snapshot"] == snapshot, "Semantic snapshot mismatch")
    require(digest(canonical({key: manifest[key] for key in ("nodes", "assertions")}))
            == manifest["semantic_identity"]["sha256"], "Semantic manifest identity mismatch")
    groups, node_origins = {}, {}
    for kind in ("nodes", "assertions"):
        rows = []
        for shard in manifest[kind]:
            require(shard["snapshot"] == snapshot and shard["encoding"] == "gzip", "Invalid semantic shard identity")
            require(0 < shard["decoded_bytes"] <= MAX_SHARD_BYTES, "Decoded semantic shard exceeds bound")
            raw = inputs.bound("full-dmg", shard)
            # A malicious compressed input cannot expand past the declared cap.
            import io
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
                decoded = stream.read(shard["decoded_bytes"] + 1)
            require(len(decoded) == shard["decoded_bytes"] and digest(decoded) == shard["decoded_sha256"],
                    "Decoded semantic shard integrity mismatch")
            graph = json.loads(decoded)["@graph"]
            require(len(graph) == shard["count"], "Semantic shard count mismatch")
            for row in graph:
                if kind == "nodes":
                    require(row["@id"] not in node_origins, "Duplicate semantic node")
                    node_origins[row["@id"]] = {
                        "path": "full-dmg/" + shard["path"], "sha256": shard["sha256"],
                    }
            rows.extend(graph)
        groups[kind] = rows
        require(len(rows) == manifest["counts"][kind], "Semantic manifest count mismatch")
    assertions = groups["assertions"]
    ids = [edge["@id"] for edge in assertions]
    require(len(set(ids)) == len(ids), "Duplicate semantic assertion")
    require(digest(canonical(sorted(ids))) == manifest["assertion_ids_sha256"], "Assertion identity mismatch")
    triples = sorted([[edge["source"], edge["predicate"], edge["target"]] for edge in assertions])
    require(digest(canonical(triples)) == manifest["direct_reified_triples_sha256"], "Semantic triple mismatch")
    return manifest, {row["@id"]: row for row in groups["nodes"]}, assertions, node_origins


def literal(row: dict) -> tuple[str, str]:
    """Select an existing literal; never summarise or manufacture a definition."""
    if isinstance(row.get("skos:definition"), dict) and isinstance(row["skos:definition"].get("@value"), str):
        return "skos:definition/@value", row["skos:definition"]["@value"]
    if isinstance(row.get("description"), str) and row["description"].strip():
        return "description", row["description"]
    return "title", row["title"]


def read_authored(inputs: Inputs, ids: set[str]) -> dict:
    result = {}
    for path in sorted(inputs.root.joinpath("knowledge").rglob("*.yamlld")):
        document = load_yaml(path)
        for row in document.get("@graph", []):
            if row.get("@id") not in ids:
                continue
            relative = path.relative_to(inputs.root).as_posix()
            raw = inputs.read(relative)
            require(row["@id"] not in result, "Duplicate authored concept identity")
            result[row["@id"]] = (row, relative, digest(raw))
    require(set(result) == ids, "A projected concept lacks its authored source")
    return result


def project(root: Path = ROOT) -> dict[str, bytes]:
    inputs = Inputs(root)
    manifest, nodes, assertions, node_origins = read_semantics(inputs)
    descriptor = json.loads(inputs.read("full-dmg/okf-explorer.json"))
    require(descriptor["snapshot_id"] == manifest["snapshot"], "Descriptor snapshot mismatch")
    binding = descriptor["entrypoints"]["context_assembly"]
    require(binding == descriptor["entrypoint_integrity"]["context_assembly"], "Custody binding mismatch")
    old = json.loads(inputs.bound("full-dmg", binding))
    require(old["bundle"]["snapshot"] == manifest["snapshot"], "Custody context snapshot mismatch")
    inventory_raw = inputs.read(INVENTORY)
    inventory = json.loads(inventory_raw)
    require(digest(inventory_raw) == descriptor["plane_roots"]["source"], "Source inventory identity mismatch")
    documents = {doc["sha256"]: doc for doc in inventory["documents"]}

    concepts = {iri for iri, row in nodes.items() if row.get("type") == "Concept"}
    authored = read_authored(inputs, concepts)
    # Existing custody page continuations and metadata evidence are retained, but
    # their six task-completeness requirements are deliberately not imported.
    records = {row["id"]: deepcopy(row) for row in old["records"]}
    selected = set(records) | concepts
    concept_edges = [edge for edge in assertions if edge["source"] in concepts]
    selected.update(edge["target"] for edge in concept_edges)
    require(selected <= set(nodes), "Projected semantic destination is absent")
    page_cache = {}

    def source_page(node: dict) -> tuple[str, list, dict]:
        doc = documents.get(node.get("source_sha256"))
        require(doc is not None, "Source page lacks frozen document identity")
        if doc["sha256"] not in page_cache:
            inputs.read(doc["pdf_path"], doc["sha256"], doc["size_bytes"])
            pages = json.loads(inputs.read(doc["pages_path"], doc["pages_sha256"]))
            require(pages["source_sha256"] == doc["sha256"] and len(pages["pages"]) == doc["pages"],
                    "Frozen extraction document mismatch")
            page_cache[doc["sha256"]] = pages
        number = node["page_number"]
        page = page_cache[doc["sha256"]]["pages"][number - 1]
        require(page["page"] == number and page["url"] == doc["url"] + f"#page={number}" == node["source"],
                "Source page URL/number mismatch")
        text = page["text"]
        require(text.strip() and digest(text.encode()) == node["text_sha256"], "Exact source text mismatch")
        provenance = [
            {"url": node["source"], "source_sha256": doc["sha256"], "locator": f"PDF page {number}",
             "captured_at": doc["observed_at"], "literal_sha256": digest(text.encode())},
            {"url": REPO + "/blob/main/" + doc["pages_path"], "source_sha256": doc["pages_sha256"],
             "locator": f"pages[{number - 1}].text", "captured_at": doc.get("extraction_observed_at") or doc["observed_at"],
             "literal_sha256": digest(text.encode())},
        ]
        return text, provenance, doc

    for iri in sorted(selected):
        node = nodes[iri]
        if node.get("type") == "Source PDF page":
            text, provenance, doc = source_page(node)
            if iri in records:
                require(records[iri]["kind"] == "evidence" and records[iri]["text"] == text,
                        "Preserved custody page differs from frozen source")
                continue
            kind, status, authority = "evidence", "normalized", {
                "class": "derived", "label": "Exact frozen machine extraction; applicability unreviewed", "source": node["source"]}
            scope = (SCOPE + " Captured document role: " + str(doc.get("role", doc.get("kind", "unclassified")))
                     + "; document: " + doc["id"] + ".")
            rights = OGL
        elif iri in concepts:
            original, path, sha = authored[iri]
            field, text = literal(node)
            require(literal(original) == (field, text), "Concept literal differs from authored source")
            if iri in records:
                continue
            kind, status, authority = "concept", "model-derived", {
                "class": "model-assisted", "label": "Existing authored research concept; specialist review required", "source": REPO}
            provenance = [{"url": REPO + "/blob/main/" + path, "source_sha256": sha,
                           "locator": f"@graph/@id={iri}/{field}",
                           "captured_at": node.get("observedAt") or node["generated"]["at"],
                           "literal_sha256": digest(text.encode())}]
            scope = node.get("skos:scopeNote", {}).get("@value", SCOPE)
            rights = REPO + "/blob/main/NOTICE.md"
        elif iri in records:
            continue
        elif node.get("type") in {"Guidance chapter", "Source document"}:
            doc = documents.get(node.get("source_sha256"))
            require(doc is not None and node["source"] == doc["url"], "Chapter scope lacks source document identity")
            inputs.read(doc["pdf_path"], doc["sha256"], doc["size_bytes"])
            text = doc["title"]
            kind, status, authority = "scope", "normalized", {
                "class": "derived", "label": "Frozen document identity; not selected legal evidence", "source": doc["url"]}
            provenance = [{"url": doc["url"], "source_sha256": doc["sha256"], "locator": "Complete document identity",
                           "captured_at": doc["observed_at"]},
                          {"url": REPO + "/blob/main/" + INVENTORY, "source_sha256": digest(inventory_raw),
                           "locator": f"documents[id={doc['id']}].title", "captured_at": doc["observed_at"],
                           "literal_sha256": digest(text.encode())}]
            scope, rights = SCOPE + " Document role: " + str(doc.get("role", "unclassified")) + ".", OGL
        else:
            raise ValueError(f"Unsupported projected record type: {node.get('type')}")
        records[iri] = {"id": iri, "route": node["route"], "label": node["title"], "kind": kind, "text": text,
                        "assertion_status": status, "authority": authority, "scope": scope, "provenance": provenance,
                        "rights": rights, "access": "public", "review_status": "unreviewed-specialist-review-required"}

    edges, excluded, unsupported = [], Counter(), Counter()
    for edge in assertions:
        if edge["source"] not in records or edge["target"] not in records:
            excluded["endpoint_outside_projection"] += 1
            continue
        if edge["predicate"] == PART_OF:
            excluded["source_containment_retained_in_full_graph"] += 1
            continue
        # Preserve every remaining directed semantic predicate, including those
        # the current consumer cannot traverse. It reports these as unsupported.
        if edge["predicate"] not in SUPPORTED:
            unsupported[edge["predicate"]] += 1
        provenance = []
        for evidence in edge["evidence"]:
            inputs.read(evidence["source_artifact"], evidence["source_sha256"])
            require(digest(str(evidence["source_value"]).encode()) == evidence["source_value_sha256"],
                    "Assertion evidence literal digest mismatch")
            if evidence.get("source_pdf_artifact"):
                inputs.read(evidence["source_pdf_artifact"], evidence["source_pdf_sha256"])
            if evidence.get("source_page_route"):
                page = records.get(BASE + "id/" + evidence["source_page_route"])
                require(page is not None and page["kind"] == "evidence" and evidence["source_value"] in page["text"],
                        "Assertion passage absent from projected frozen page")
            provenance.append({"url": evidence["url"], "source_sha256": evidence["source_sha256"],
                               "locator": evidence["locator"], "captured_at": evidence["retrieved_at"],
                               "literal_sha256": evidence["source_value_sha256"]})
        edges.append({"id": edge["@id"], "source": edge["source"], "target": edge["target"],
                      "predicate": edge["predicate"], "label": edge["label"], "assertion_status": edge["assertion_status"],
                      "authority": deepcopy(edge["authority"]), "scope": edge.get("context_scope", SCOPE),
                      "provenance": provenance, "original_assertion_id": edge["@id"]})
    index = {"schema": "okf-context-index.v1", "bundle": deepcopy(old["bundle"]), "scope": SCOPE,
             "limitations": LIMITATIONS, "records": sorted(records.values(), key=lambda row: row["id"]),
             "assertions": sorted(edges, key=lambda row: row["id"]), "requirements": []}
    encoded = canonical(index)
    require(len(encoded) <= MAX_INDEX_BYTES and len(records) <= 10000 and len(edges) <= 30000,
            "Discovery projection exceeds consumer bounds")
    require(all(len(row["text"]) <= 100000 and len(row["provenance"]) <= 32 for row in records.values()),
            "Discovery record exceeds consumer bounds")
    producer_path = "scripts/build_context_discovery.py"
    inputs.read(producer_path)
    inputs.read("scripts/build_bundle.py")
    inputs.read("uv.lock")
    receipt = {
        "schema": "okf-dwp-context-discovery-projection.v1", "source_snapshot": manifest["snapshot"],
        "source_semantic_identity": manifest["semantic_identity"]["sha256"],
        "projection_policy": "existing-concepts-cited-whole-pages-existing-directed-assertions-v1",
        "completeness": "No completeness requirements; discovery-only, always insufficient for a complete answer.",
        "counts": {"source_concepts": len(concepts), "source_pages": sum(n.get("type") == "Source PDF page" for n in nodes.values()),
                   "records": len(records), "record_kinds": dict(sorted(Counter(r["kind"] for r in records.values()).items())),
                   "assertions": len(edges), "requirements": 0},
        "unsupported_predicates_retained": dict(sorted(unsupported.items())),
        "assertions_not_projected": dict(sorted(excluded.items())),
        "index": {"path": "assembly-index.json", "bytes": len(encoded), "sha256": digest(encoded)},
        "preserved_custody_index": {"path": "full-dmg/" + binding["path"], "bytes": binding["bytes"], "sha256": binding["sha256"]},
        "inputs": sorted(inputs.files.values(), key=lambda item: item["path"]),
    }
    return {"assembly-index.json": encoded, "manifest.json": pretty(receipt)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Rebuild in memory and compare committed projection bytes")
    args = parser.parse_args()
    outputs = project()
    directory = ROOT / OUTPUT
    for name, raw in outputs.items():
        path = directory / name
        if args.check:
            require(path.is_file() and path.read_bytes() == raw, f"Stale discovery output: {path.relative_to(ROOT)}")
        else:
            directory.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    receipt = json.loads(outputs["manifest.json"])
    print(json.dumps({"status": "verified" if args.check else "built", **receipt["counts"], "index_bytes": receipt["index"]["bytes"]}))


if __name__ == "__main__":
    main()
