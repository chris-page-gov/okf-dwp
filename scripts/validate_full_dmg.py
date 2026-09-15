#!/usr/bin/env python3
"""Validate every full-DMG source, page, search token and semantic assertion."""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
import gzip
import json
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker
from pyld import jsonld
from build_full_dmg import (BASE, CONSUMER_COMMIT, INPUT, OUTPUT, ROOT, PROFILE,
                            bucket, canonical, digest, load_yaml, pinned_loader,
                            safe_path, tokens)


def require(test: bool, message: str) -> None:
    if not test:
        raise ValueError(message)


def read_json(path: Path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def validate(root: Path = ROOT, output: str = OUTPUT, inventory_path: str = INPUT, *, verify_rdf: bool = True) -> dict:
    out = safe_path(root, output)
    inventory = read_json(safe_path(root, inventory_path))
    documents = inventory["documents"]
    descriptor = read_json(out / "okf-explorer.json")
    snapshot = descriptor["snapshot"]
    require(descriptor.get("plane_roots") == descriptor["exploratory_publication"]["applicable_plane_roots"], "Exploratory publication roots differ from the descriptor envelope")
    @lru_cache(maxsize=None)
    def source_hash(relative: str) -> str:
        return digest(safe_path(root, relative).read_bytes())
    checksums = read_json(out / "checksums.json")
    checked_files = 0
    for row in checksums["files"]:
        raw = safe_path(out, row["path"]).read_bytes()
        require(len(raw) == row["bytes"] and digest(raw) == row["sha256"], "Generated file hash mismatch: " + row["path"])
        if row["path"].endswith(".gz"):
            require(len(gzip.decompress(raw)) <= 64 * 1024 * 1024, "Decoded shard too large: " + row["path"])
        checked_files += 1
    inputs = read_json(out / "build-inputs.json")
    for row in inputs["files"] + inputs["additional_knowledge"]:
        require(source_hash(row["path"]) == row["sha256"], "Build input changed: " + row["path"])
    require(inputs["consumer"]["commit"] == CONSUMER_COMMIT, "Unexpected consumer contract revision")
    publication_time = datetime.fromisoformat(descriptor["generated_at"].replace("Z", "+00:00"))
    for value in [inventory.get("generated_at")] + [doc.get("extraction_observed_at") for doc in documents]:
        if value:
            require(publication_time >= datetime.fromisoformat(value.replace("Z", "+00:00")), "Bundle aggregation timestamp predates extraction")
    yaml_descriptor = load_yaml(out / "okf-explorer.yamlld")
    yaml_descriptor.pop("@context")
    require(yaml_descriptor == descriptor, "Indexed YAML-LD and JSON descriptors disagree")
    semantic_control = load_yaml(out / "okf-bundle.yamlld")
    require(semantic_control == read_json(out / "okf-bundle.jsonld"), "Semantic YAML-LD and JSON-LD controls disagree")
    bundle_schema = read_json(root / "profiles/bundle-wiki/v1/bundle.schema.json")
    Draft202012Validator(bundle_schema, format_checker=FormatChecker()).validate(semantic_control)
    manifest = read_json(out / "data/manifest.json")
    require(manifest["snapshot"] == snapshot, "Manifest snapshot mismatch")
    records = []
    for path in manifest["chunks"]["datasets"]:
        records.extend(read_json(out / path))
    routes = {row["route"]: row for row in records}
    require(len(routes) == len(records) == descriptor["counts"]["records"], "Record identities/counts mismatch")
    label_ref = descriptor["entrypoints"]["endpoint_labels"]
    require(label_ref == manifest["indexes"]["endpoint_labels"] == descriptor["entrypoint_integrity"]["endpoint_labels"], "Endpoint label bindings differ")
    labels = read_json(out / label_ref["path"])
    label_map = {row['route']:row for row in labels['entries']}
    resources = [row for part in manifest['chunks']['resources'] for row in read_json(out / part)]
    publishers = read_json(out / 'data/publishers.json')
    require(labels["snapshot"] == snapshot and labels["counts"]["entries"] == len(label_map) == len(records) + len(resources) + len(publishers), "Endpoint label snapshot or denominator differs")
    require({route: (label_map[route]["iri"], label_map[route]["label"], label_map[route]["type"]) for route in routes} ==
            {row["route"]: (row["id"], re.sub(r"\s+", " ", row["title"]).strip(), row["record_type"]) for row in records}, "Endpoint labels lose a semantic route or source title")
    for publisher in publishers:
        require(label_map[publisher['id']]['label'] == publisher['title'], 'Publisher label missing')
        require(publisher['resource_count'] == sum(row['resource_count'] for row in records if row['publisher'] == publisher['name']), 'Publisher source count mismatch')
    for resource in resources:
        require(label_map['resource/' + resource['id']]['iri'] == BASE + 'id/' + resource['id'], 'Resource label route mismatch')
        require(resource['host'] == urlsplit(resource['url']).hostname, 'Resource host missing or changed')
    locator = read_json(out / "data/locator/manifest.json")
    locator_buckets = {key: read_json(out / ref["path"]) for key, ref in locator["buckets"].items()}
    for ordinal, record in enumerate(records):
        require(locator_buckets[bucket(record["route"])][record["route"]] == [ordinal // locator["chunk_size"], ordinal % locator["chunk_size"]], "Record locator mismatch")
    source_records = read_json(out / "data/source-documents.json")
    by_document = {doc["id"]: doc for doc in source_records["documents"]}
    require(source_records["inventory_sha256"] == digest(safe_path(root, inventory_path).read_bytes()), "Source inventory binding mismatch")
    require(len(by_document) == len(documents) == descriptor["counts"]["source_documents"], "Source document denominator mismatch")
    if "summary" in inventory and "expected_pdf_documents" in inventory["summary"]:
        require(len(documents) == inventory["summary"]["expected_pdf_documents"], "Not all censused PDFs are acquired")
        require(inventory["summary"]["complete_documents"] == len(documents), "Acquisition is incomplete")
    page_count, nonempty, expected_page_text = 0, 0, {}
    for doc in documents:
        require(len(safe_path(root, doc["pdf_path"]).read_bytes()) == doc["size_bytes"], "PDF byte count differs: " + doc["id"])
        for path_key, hash_key in [("pdf_path", "sha256"), ("text_path", "text_sha256"), ("pages_path", "pages_sha256")]:
            if doc.get(hash_key):
                require(source_hash(doc[path_key]) == doc[hash_key], "Source hash differs: " + doc[path_key])
        page_document = read_json(safe_path(root, doc["pages_path"]))
        require(page_document["source_sha256"] == doc["sha256"], "Page extraction source differs")
        pages = page_document["pages"]
        require(len(pages) == doc["pages"], "Measured page count differs")
        declared = by_document[doc["id"]]
        require(len(declared["page_routes"]) == len(pages), "Page route count differs")
        for index, (page, route) in enumerate(zip(pages, declared["page_routes"]), 1):
            require(page["page"] == index, "Page sequence differs")
            row = routes[route]
            text = page["text"]
            require(text in row["narrative"]["body"], "Complete page text absent: " + route)
            require(row["url"] == page["url"] == doc["url"] + f"#page={index}", "Page locator differs: " + route)
            require(row["provenance"]["source_sha256"] == doc["sha256"] and row["provenance"]["page_text_sha256"] == digest(text.encode()), "Page identity differs: " + route)
            require(row["provenance"]["date_roles"]["captured_at"] == doc["observed_at"], "Capture date was replaced: " + route)
            require(row["timestamp"] == "", "Unreviewed publication date inferred from another date role")
            expected_page_text[route] = text
            page_count += 1
            nonempty += bool(text.strip())
    coverage = read_json(out / "coverage.json")
    require(coverage["source_pages"] == page_count and coverage["nonempty_text_pages"] == nonempty, "Measured page coverage differs")
    require(coverage["source_roles"] == dict(sorted(Counter(doc["role"] for doc in documents).items())), "Source role denominator differs")
    # Validate semantic bytes, every assertion, direct/reified agreement and
    # round-trip through the pinned local JSON-LD contexts.
    semantic = read_json(out / "data/semantic/manifest.json")
    groups, nodes, assertions = {}, {}, []
    for kind in ("nodes", "assertions"):
        groups[kind] = semantic[kind]
        for shard in semantic[kind]:
            raw = (out / shard["path"]).read_bytes()
            decoded = gzip.decompress(raw)
            require(digest(raw) == shard["sha256"] and digest(decoded) == shard["decoded_sha256"], "Semantic shard hash differs")
            graph = json.loads(decoded)
            require(len(graph["@graph"]) == shard["count"], "Semantic shard count differs")
            if verify_rdf:
                rdf = jsonld.normalize(graph, options={"algorithm": "URDNA2015", "format": "application/n-quads", "documentLoader": pinned_loader})
                require(digest(rdf.encode()) == shard["rdf"]["canonical_sha256"], "RDF identity differs")
                require(gzip.decompress((out / shard["rdf"]["path"]).read_bytes()) == rdf.encode(), "RDF serialisation differs")
            if kind == "nodes":
                for node in graph["@graph"]:
                    require(node["@id"] not in nodes, "Duplicate semantic entity identity")
                    nodes[node["@id"]] = node
            else:
                assertions.extend(graph["@graph"])
    require(semantic["semantic_identity"]["sha256"] == digest(canonical(groups)), "Semantic manifest identity differs")
    require(len(nodes) == len(records) == semantic["counts"]["nodes"], "Semantic/runtime entity count differs")
    require(len({row["@id"] for row in assertions}) == len(assertions) == semantic["counts"]["assertions"], "Assertion identities/counts differ")
    validator = Draft202012Validator(read_json(root / "profiles/bundle-wiki/v1/semantic-assertion.schema.json"), format_checker=FormatChecker())
    triples = []
    for row in assertions:
        validator.validate(row)
        require(row["source"] in nodes and row["target"] in nodes, "Unresolved semantic endpoint")
        source, target = nodes[row["source"]], nodes[row["target"]]
        require(row["source_route"] == source["route"] and row["target_route"] == target["route"], "Semantic route/IRI mismatch")
        predicate = row["predicate"]
        compact = predicate.replace("http://purl.org/dc/terms/", "dcterms:")
        values = source.get(predicate, source.get(compact, []))
        values = values if isinstance(values, list) else [values]
        require({"@id": row["target"]} in values, "Direct triple absent for assertion " + row["@id"])
        for item in row["evidence"]:
            if item.get("source_artifact"):
                require(source_hash(item["source_artifact"]) == item["source_sha256"], "Assertion evidence hash differs")
            if "source_value" in item:
                require(digest(str(item["source_value"]).encode()) == item["source_value_sha256"], "Assertion source-value hash differs")
            if item.get("source_page_route"):
                require(item["source_value"] in expected_page_text[item["source_page_route"]], "Semantic quotation differs from source text")
        if row["assertion_status"] == "model-derived":
            require(row["review_status"] == "unreviewed-specialist-review-required", "Model-derived review status was upgraded")
        triples.append([row["source"], predicate, row["target"]])
    require(digest(canonical(sorted(triples))) == semantic["direct_reified_triples_sha256"], "Direct/reified statement identity differs")
    reified = {tuple(row) for row in triples}
    direct = set()
    for predicate in {row[1] for row in triples}:
        compact = predicate.replace("http://purl.org/dc/terms/", "dcterms:")
        for iri, node in nodes.items():
            values = node.get(predicate, node.get(compact, []))
            for value in values if isinstance(values, list) else [values]:
                if isinstance(value, dict) and "@id" in value:
                    direct.add((iri, predicate, value["@id"]))
    require(direct == reified, "Unreified or missing direct semantic relationships")
    runtime = []
    for path in manifest["chunks"]["relationships"]:
        runtime.extend(read_json(out / path))
    require(len(runtime) == len(assertions), "Runtime assertion count differs")
    runtime_by_id = {row["id"]: row for row in runtime}
    for row in assertions:
        expected = {**row, "id": row["@id"], "source": row["source_route"], "target": row["target_route"], "source_iri": row["source"], "target_iri": row["target"]}
        require(runtime_by_id[row["@id"]] == expected, "Runtime assertion projection differs")
    adjacency_manifest = read_json(out / "data/adjacency/manifest.json")
    adjacency = {}
    for path in adjacency_manifest["buckets"].values():
        adjacency.update(read_json(out / path))
    expected_incident = {}
    for row in runtime:
        for route in {row["source"], row["target"]}:
            expected_incident.setdefault(route, set()).add(row["id"])
    require(set(adjacency) == set(expected_incident), "Adjacency route set differs")
    for route, rows in adjacency.items():
        require({row["id"] for row in rows} == expected_incident[route] and len(rows) == len(expected_incident[route]), "Adjacency incident assertions differ")
    # Prove full-text indexing, not just title/snippet retrieval. Every token of
    # every page must have its exact ordinal and description-field mask.
    search = read_json(out / "data/search/manifest.json")
    require(search["counts"]["postings"] == search["counts"]["uncapped_postings"], "Search silently caps token coverage")
    postings = {}
    for path in search["entrypoints"]["postings"]:
        for token, rows in read_json(out / path)["tokens"].items():
            require(token not in postings, "Duplicate search token partition")
            postings[token] = {row[0]: row[2] for row in rows}
            require(len(postings[token]) == len(rows), "Duplicate posting ordinal")
    checked_tokens = 0
    for ordinal, record in enumerate(records):
        node = nodes[record["id"]]
        text = expected_page_text.get(record["route"], node.get("body", ""))
        for token in tokens(text):
            require(postings.get(token, {}).get(ordinal, 0) & 8 != 0, f"Full-text token missing: {record['route']} / {token}")
            checked_tokens += 1
    require(sum(map(len, postings.values())) == search["counts"]["postings"], "Posting count differs")
    return {"schema": "okf-full-dmg-validation.v1", "status": "passed", "snapshot": snapshot,
            "validator_sha256": digest(Path(__file__).read_bytes()),
            "consumer_commit": CONSUMER_COMMIT, "checks": {"generated_file_hashes": checked_files, "source_documents": len(documents), "measured_pages": page_count,
            "empty_text_pages": page_count - nonempty, "semantic_entities": len(nodes), "semantic_assertions": len(assertions),
            "all_page_and_record_text_tokens_checked": checked_tokens, "all_rdf_shards_recomputed": verify_rdf,
            "direct_reified_agreement": "passed", "lazy_record_routes": "passed", "adjacency_incident_assertions": "passed"},
            "scope": "Deterministic source, extraction, search and semantic integrity only; no legal or specialist review."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=OUTPUT, help="Generated corpus directory")
    parser.add_argument("--inventory", default=INPUT)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    result = validate(ROOT, args.output, args.inventory)
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_bytes(canonical(result))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
