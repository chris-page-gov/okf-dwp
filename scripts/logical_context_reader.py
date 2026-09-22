"""Indexed Reader projection of the same logical units used by Ask OKF."""
from collections import Counter, defaultdict
from copy import deepcopy
import gzip
import json
from urllib.parse import urlsplit

from build_bundle import BASE, PROFILE, REPO, canonical, context, digest, source_text_block, yaml_bytes
from build_context_corpus import deterministic_gzip
from build_context_discovery import require
from build_full_dmg import CHUNK, bucket, build_search, utc_key, role, role_label, source_dates
from build_combined_reader import add_semantics, endpoint_labels, emit_semantics, source_record

TITLE = "DWP guidance: logical evidence units"
FACETS = {"source_family": "Source family", "boundary_status": "Boundary status", "unit_kind": "Unit kind", "concept": "Authored concept references"}


def emit_reader(inputs, corpus, units, semantic, declarations, corpus_outputs):
    outputs, metadata = {}, {}
    snapshot = corpus["bundle"]["snapshot"]
    when = max(p["captured_at"] for r in semantic["records"] for p in r["provenance"])
    records, resources, edges, full_text = [], [], [], {}
    all_context = {**semantic, "records": [*semantic["records"], *units]}
    add_semantics(records, resources, edges, full_text, all_context, when,
                  "logical-context/base-index.json", digest(corpus_outputs["base-index.json"]))
    concepts = {r["id"]: r for r in semantic["records"] if r["kind"] == "concept"}
    references = defaultdict(set)
    for edge in semantic["assertions"]:
        if edge["source"] in concepts:
            references[edge["target"]].add(concepts[edge["source"]]["label"])
    unit_map = {r["id"]: r for r in units}
    source_documents = {}
    for group in corpus["source_groups"]:
        inventory = json.loads(inputs.read(group["inventory"]["repository_path"], group["inventory"]["sha256"]))
        source_documents.update({(group["id"], d["id"]): d for d in inventory["documents"]})
    # One PDF resource per source document; each unit already exposes its exact
    # page spans. Repeating the same PDF resource for every paragraph inflates
    # the endpoint catalogue and obscures the document/unit distinction.
    document_resources, document_records = {}, []
    for document_key, doc in sorted(source_documents.items()):
        family, document_id = document_key
        route = "document/logical/" + family + "/" + document_id + "/pdf-" + doc["sha256"][:16]
        document, resource = source_record(route, doc["title"],
            "# " + doc["title"] + "\n\nSource document for the logical units. Exact page locations are retained in each unit’s source spans. Documents with no extracted text remain listed. No complete policy or current applicability is asserted.", doc, family=family.upper())
        document.update(boundary_status="Not applicable", unit_kind="Source document", concept=["No authored reference"])
        document_records.append(document); resources.append(resource)
        full_text[route] = document["narrative"]["body"]
        document_resources[document_key] = resource["id"]
    for row in records:
        row.update(boundary_status="Not applicable", unit_kind="Not applicable",
                   concept=sorted(references[row["id"]]) or ["No authored reference"])
        item = unit_map.get(row["id"])
        if not item:
            continue
        unit = item["evidence_unit"]
        source = item["provenance"][0]
        family = row["route"].split("/")[1].upper()
        document_id = row["route"].split("/")[2]
        document_key = (family.lower(), document_id)
        doc = source_documents[document_key]
        captured_role = role_label(role(doc))
        resource_id = document_resources[document_key]
        row.update(type="Logical evidence unit", record_type="Logical evidence unit",
            publisher="dwp", publisher_title="DWP source; independent extraction",
            source_family=family, source_role=captured_role,
            source_adapter="logical-source-spans-v1", source_tier="official-source-unreviewed-extraction",
            boundary_status=unit["boundary_status"], unit_kind=unit["kind"],
            document_id=document_id, volume="See source document",
            formats=["PDF"], tags=[family, unit["kind"], unit["boundary_status"], captured_role],
            resource_ids=[resource_id], resource_count=1, url=source["url"],
            license_id="uk-ogl", license_title="Open Government Licence v3.0", license_source_id=item["rights"])
        # This is source text with an authored/machine boundary, not authored prose.
        row["provenance"].update(authority=item["authority"], source_sha256=source["source_sha256"],
            literal_sha256=digest(item["text"].encode()), evidence_unit=unit,
            date_roles=source_dates(doc))
        row["extras"] = {"evidence_unit": unit, "source_dates": row["provenance"]["date_roles"]}
        row["narrative"]["body"] = ("# " + item["label"] + "\n\n**Source extraction; " + unit["boundary_status"]
            + "; " + unit["completeness"] + ". Specialist review required.**\n\n" + item["scope"]
            + "\n\n## Captured source text\n\n" + source_text_block(item["text"])
            + "\n\n## Source spans\n\nOffsets are half-open UTF-8 byte offsets in extracted text.\n\n"
            + "\n".join(f"- [{s['locator']}]({s['source_url']}): source bytes {s['source_start']}–{s['source_end']}; fragment SHA-256 `{s['literal_sha256']}`."
                for s in unit["spans"]))
    records.extend(document_records)
    records.sort(key=lambda r: r["route"])
    edges.sort(key=lambda r: r["id"])
    require(len({r["id"] for r in records}) == len(records), "Duplicate logical Reader identity")
    known = {r["route"] for r in records}
    require(all(e["source"] in known and e["target"] in known for e in edges), "Unresolved Reader edge")

    def put(path, value):
        raw = canonical(value)
        require(len(raw) <= 64 * 1024 * 1024, "Reader decoded byte limit")
        outputs[path] = deterministic_gzip(raw) if path.endswith(".gz") else raw
        metadata[path] = {"path": path, "bytes": len(outputs[path]), "sha256": digest(outputs[path]),
            "decoded_bytes": len(raw), "decoded_sha256": digest(raw), "snapshot": snapshot}
        return metadata[path]

    def bind(path):
        return {"path": path, "bytes": len(outputs[path]), "sha256": digest(outputs[path])}

    shard_groups = {}
    for kind, rows in (("datasets", records), ("resources", resources), ("relationships", edges)):
        shard_groups[kind] = [put(f"data/{kind}-{i // CHUNK:04d}.json.gz", rows[i:i + CHUNK]) for i in range(0, len(rows), CHUNK)]
    locations, adjacent = defaultdict(dict), defaultdict(dict)
    for n, row in enumerate(records):
        locations[bucket(row["route"])][row["route"]] = [n // CHUNK, n % CHUNK]
    for edge in edges:
        for route in {edge["source"], edge["target"]}:
            adjacent[bucket(route)].setdefault(route, []).append(edge)
    locator = {}
    for key, rows in sorted(locations.items()):
        path = f"data/locator/{key}.json"
        put(path, rows); locator[key] = bind(path)
    put("data/locator/manifest.json", {"schema": "okf-record-locator-sharded.v1", "algorithm": "fnv1a32-prefix-2", "snapshot": snapshot,
        "records": len(records), "chunk_size": CHUNK, "record_chunks": [r["path"] for r in shard_groups["datasets"]], "buckets": locator, "bucket_count": len(locator)})
    adjacency_shards = [put(f"data/adjacency/{key}.json.gz", rows) for key, rows in sorted(adjacent.items())]
    put("data/adjacency/manifest.json", {"schema": "okf-relationship-adjacency.v1", "algorithm": "fnv1a32-prefix-2", "snapshot": snapshot,
        "routes": sum(map(len, adjacent.values())), "relationships": len(edges), "buckets": {k: f"data/adjacency/{k}.json.gz" for k in sorted(adjacent)}, "shards": adjacency_shards})
    search = build_search(records, full_text, snapshot, put)
    # The consumer bounds postings per token, not the total document census.
    # Declare the actual maximum; no token or posting is discarded.
    largest_posting = max((len(rows) for rows in search["postings"].values()), default=1)
    if largest_posting > 50_000:
        raise ValueError("Logical Reader token exceeds the supported postings bound")
    search["manifest"]["counts"]["max_postings_per_token"] = largest_posting
    facets = search["facets"]
    for key in FACETS:
        values = defaultdict(list)
        for n, row in enumerate(records):
            for value in row[key] if isinstance(row[key], list) else [row[key]]:
                values[value].append(n)
        path = f"data/search/filters/{key}.json.gz"
        put(path, {"schema": "okf-filter-postings.v1", "key": key, "values": dict(sorted(values.items()))})
        search["manifest"]["entrypoints"]["filter_postings"][key] = path
        facets[key] = [{"value": v, "count": len(ids)} for v, ids in sorted(values.items(), key=lambda p: (-len(p[1]), p[0]))]
    for path in search["manifest"]["entrypoints"]["result_docs"]:
        rows = json.loads(gzip.decompress(outputs[path]))
        for row in rows:
            row.update({key: records[row["ordinal"]][key] for key in FACETS})
        put(path, rows)
    put("data/facets.json", facets)
    search_shards = {"search": [{**bind(p), "snapshot": snapshot} for p in sorted(outputs) if p.startswith("data/search/") or p == "data/facets.json"]}
    put("data/search/shards.json", {"snapshot": snapshot, "shards": search_shards})
    search["manifest"].update(shard_metadata="data/search/shards.json", shard_manifest_sha256=digest(canonical(search_shards)))
    put("data/search/manifest.json", search["manifest"])
    counts = {"records": len(records), "datasets": len(records), "resources": len(resources), "relationships": len(edges),
        "publishers": 2, "source_documents": corpus["counts"]["documents"], "source_pages": corpus["counts"]["pages"]}
    publishers = [{"id": "publisher/" + key, "name": key, "title": title,
        "dataset_count": sum(r["publisher"] == key for r in records), "resource_count": len({resource for r in records if r["publisher"] == key for resource in r["resource_ids"]})}
        for key, title in (("dwp", "DWP source; independent extraction"), ("independent-project", "Independent project-authored research"))]
    put("data/publishers.json", publishers)
    put("data/overview.json", {"schema": "okf-large-overview.v1", "title": TITLE, "generated_at": when, "counts": counts,
        "recent_datasets": search["results"][:12], "notices": corpus["limitations"], "facet_previews": {k: v[:15] for k, v in facets.items()}})
    labels = endpoint_labels(records, resources, publishers, facets)
    put("data/endpoint-labels.json.gz", {"schema": "okf-explorer-endpoint-label-index.v1", "snapshot": snapshot, "generated_at": when,
        "default_language": "en-GB", "opaque_identifier_patterns": [], "entries": labels, "counts": {"entries": len(labels)}})
    put("data/analysis.json", {"schema": "okf-analysis.v1", "snapshot": snapshot, "facet_analysis": []})
    put("data/manifest.json", {"title": TITLE, "snapshot": snapshot, "generated_at": when, "counts": counts,
        "chunks": {**{k: [r["path"] for r in v] for k, v in shard_groups.items()}, "publishers": [bind("data/publishers.json")]}, "shards": shard_groups,
        "indexes": {"overview": "data/overview.json", "facets": "data/facets.json", "search": "data/search/manifest.json", "analysis": "data/analysis.json",
            "record_locator": bind("data/locator/manifest.json"), "relationship_adjacency": "data/adjacency/manifest.json", "endpoint_labels": bind("data/endpoint-labels.json.gz")}})
    semantic_manifest = emit_semantics(records, edges, all_context, declarations, snapshot, when, put, outputs, bind)
    semantic_manifest["canonical_authoring"] = "Frozen source-unit identities, retained neutral concepts, and explicit domain-profile/logical-units proposals. Boundaries and relationships remain distinct and require specialist review."
    semantic_manifest["projection_scope"] = "Identity and definition nodes, direct triples and the same reified assertions. Exact unit text and byte-span provenance remain in the bound Reader and context records."
    put("data/semantic/manifest.json", semantic_manifest)
    # Keep the existing large-corpus wire format, replacing every data binding.
    descriptor = deepcopy(json.loads(inputs.read("combined/okf-explorer.json")))
    descriptor.update(title=TITLE, description=corpus["limitations"][0], snapshot=snapshot, snapshot_id=snapshot, counts=counts, generated_at=when)
    descriptor.pop("consumer", None)  # Exact tested engine identity is bound by the evaluation receipt.
    descriptor["entrypoints"] = {"markdown_index": "index.md"}
    descriptor["entrypoint_integrity"] = {}
    for key, path in {"data_manifest": "data/manifest.json", "overview_index": "data/overview.json", "search_manifest": "data/search/manifest.json",
        "record_locator": "data/locator/manifest.json", "relationship_adjacency": "data/adjacency/manifest.json", "endpoint_labels": "data/endpoint-labels.json.gz"}.items():
        descriptor["entrypoints"][key] = bind(path) if key in {"record_locator", "endpoint_labels"} else path
        descriptor["entrypoint_integrity"][key] = bind(path)
    for key, path in (("context_assembly", "base-index.json"), ("context_corpus", "manifest.json")):
        ref = {"path": path, "bytes": len(corpus_outputs[path]), "sha256": digest(corpus_outputs[path])}
        descriptor["entrypoints"][key] = ref; descriptor["entrypoint_integrity"][key] = ref
    descriptor["extensions"] = {"okf-explorer-presentation.v1": {"schema": "okf-explorer-presentation.v1", "snapshot": snapshot,
        "status": "experimental", "defaults": {"facet_mode": "suggested"}, "facets": [{"key": k, "label": label,
        "description": "Discovery and review status only; not an applicability claim.", "order": n, "default_state": "pinned", "open_control": "list", "value_order": "count-desc"}
        for n, (k, label) in enumerate(FACETS.items())]}}
    source_identity = {"unit_manifest": corpus["unit_producer"], "source_groups": corpus["source_groups"]}
    put("data/source-identity.json", source_identity)
    descriptor["plane_roots"] = {"source": digest(canonical(source_identity)), "semantic": semantic_manifest["semantic_identity"]["sha256"],
        "data": digest(canonical(shard_groups["datasets"])), "search": digest(canonical(search_shards)), "presentation": digest(canonical(descriptor["extensions"]))}
    descriptor["exploratory_publication"].update(snapshot_id=snapshot, generated_at=when, applicable_plane_roots=descriptor["plane_roots"],
        limitations=corpus["limitations"], permitted_claims=["Exact source-byte accounting, candidate logical units and explicitly authored routes; no complete legal answerability."])
    descriptor["source"] = {"url": REPO, "identity": bind("data/source-identity.json"), "scope": corpus["scope"]}
    descriptor["vocabulary"]["search_placeholder"] = "Search logical evidence units"
    put("okf-explorer.json", descriptor)
    control = {"@context": context(), "@id": BASE + "id/bundle/logical-context", "@type": "okf:Bundle", "title": TITLE,
        "description": corpus["limitations"][0], "version": "0.1.0", "status": "experimental", "descriptor": {"@id": BASE + "logical-context/okf-explorer.json"},
        "semanticDescriptor": {"@id": BASE + "logical-context/okf-bundle.yamlld"}, "home": {"@id": REPO}, "profile": {"@id": PROFILE},
        "publisher": {"@id": "https://github.com/chris-page-gov"}, "license": {"@id": REPO + "/blob/main/NOTICE.md"},
        "snapshot_id": snapshot, "semantic_manifest": bind("data/semantic/manifest.json"), "counts": semantic_manifest["counts"],
        "assertion_scope": "real-world", "exploratory_publication": descriptor["exploratory_publication"]}
    outputs["okf-bundle.yamlld"] = yaml_bytes(control)
    put("okf-bundle.jsonld", control)
    outputs["index.md"] = ("# " + TITLE + "\n\n" + "\n\n".join(corpus["limitations"])
        + "\n\n[Reader descriptor](okf-explorer.json) · [Ask corpus](manifest.json) · [Method and acceptance](../docs/logical-evidence-units.md).\n").encode()
    return outputs
