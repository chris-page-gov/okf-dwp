#!/usr/bin/env python3
"""Build additive DMG/ADM Reader navigation; never alter frozen source releases.

This projection reuses the published indexed Reader contracts. Whole-page text,
source identity and authored assertions remain separate from mention facets.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import gzip
import json
import re
from urllib.parse import quote, urlsplit
from jsonschema import Draft202012Validator, FormatChecker
from pyld import jsonld

from build_bundle import BASE, OGL, REPO, ROOT, PROFILE, canonical, context, digest, load_yaml, pinned_loader, pretty, source_text_block, yaml_bytes
from build_context_discovery import Inputs, require
from build_full_dmg import (CHUNK, bucket, build_search, deterministic_gzip,
                            new_node, observed, role, role_label, source_assertion, source_dates, utc_key)
from build_review_navigation import DIMENSIONS, UNKNOWN, load_pages

OUTPUT = "combined"
SEMANTIC = "evaluation/semantic-expansion/assembly-index.json"
CONSUMER_COMMIT = "0e6a639f87c4060123b72d82c1ebe30405d475f1"
LABELS = {"source_family": "Source family", **DIMENSIONS}
TITLE = "DWP guidance: combined DMG and ADM evidence review"
LIMITATIONS = [
    "Independent experimental publication, not official DWP guidance, benefits advice or an entitlement decision.",
    "DMG (Decision makers’ guide) and ADM (Advice for decision making) are distinct source families. A match does not select the applicable benefit regime or current law.",
    "Benefit, circumstance and topic facets record literal mentions; they are discovery aids, not legal applicability assertions. Authored concepts and relationships remain unreviewed.",
    "All captured pages are accounted for, including empty machine extractions. Tables, footnotes and reading order require comparison with the official PDF.",
    "Publication, revision, capture and generation dates remain separate. Capture is not publication or legal commencement; unknown source dates remain unknown.",
    "Historical, amendment, transitional and memo documents retain their captured classifications. Recently captured does not mean currently applicable.",
    "The graph retains relationship direction and evidence. Facet co-occurrence does not generate a legal relationship.",
    "Ask OKF uses the same frozen source pages. Completeness requires the declared task evidence and unresolved obligations; no general legal completeness is claimed.",
    "Selected dated statutory units are supplied as unreviewed machine extractions. Their legal applicability and complete amendment dependencies remain unestablished. Tribunal judgments and subscriber-only handbook contents are not supplied.",
]


def decoded(inputs, base, binding):
    raw = inputs.bound(base, binding)
    data = gzip.decompress(raw) if binding["path"].endswith(".gz") else raw
    if "decoded_sha256" in binding:
        require(digest(data) == binding["decoded_sha256"] and len(data) == binding["decoded_bytes"], "Decoded integrity mismatch")
    return json.loads(data)


def source_record(route, title, body, doc, page=None, family="ADM"):
    """Use the established Reader projection without changing a source date."""
    source = doc["url"] + (f"#page={page['page']}" if page else "")
    label = role_label(role(doc))
    dates = source_dates(doc)
    provenance = {"semantic_iri": BASE + "id/" + route, "source_role": label,
        "authority": "official-source-text; independent unreviewed extraction", "source_sha256": doc["sha256"],
        "page_text_sha256": digest(page["text"].encode()) if page else None,
        "source_artifact": doc["pdf_path"], "date_roles": dates, "extraction": doc.get("extraction"),
        "review_status": "unreviewed-specialist-review-required"}
    resource_id = "resource/source-" + digest(route.encode())[:24]
    kind = "Source PDF page" if page else "Source document"
    resource = {"id": resource_id, "route": resource_id, "dataset": route, "name": "Official source PDF page" if page else "Official source PDF",
        "url": source, "host": urlsplit(source).hostname, "format": "PDF",
        "source_access": {"url": source, "label": "Verify the official PDF", "media_type": "application/pdf", "display_mode": "link"}, "provenance": provenance}
    record = {"id": BASE + "id/" + route, "name": route, "route": route, "title": title, "type": kind, "record_type": kind,
        "notes": label + ". " + re.sub(r"\s+", " ", page["text"] if page else body).strip()[:360],
        "narrative": {"title": title, "body": f"**{label}.**\n\n[Verify the original PDF]({source})\n\n" + body},
        "publisher": "dwp", "publisher_title": "Department for Work and Pensions — source; independent extraction",
        "resource_ids": [resource_id], "resource_count": 1, "formats": ["PDF"], "tags": [label, kind, family], "topics": [label],
        "source_role": label, "source_family": family, "document_id": doc["id"], "volume": "Reference/memo",
        "source_tier": "official-source-unreviewed-extraction", "source_adapter": "frozen-dwp-pdf-page-text", "timestamp": "",
        "metadata_created": doc.get("extraction_observed_at") or observed(doc), "url": source,
        "license_id": "uk-ogl", "license_title": "Open Government Licence v3.0", "license_source_id": OGL,
        "provenance": provenance, "extras": {"source_dates": dates, "source_page_number": page["page"] if page else None}}
    return record, resource


def runtime_edge(edge):
    return {**edge, "id": edge["@id"], "source": edge["source_route"], "target": edge["target_route"],
            "source_iri": edge["source"], "target_iri": edge["target"]}


def compile_combined(root=ROOT, semantic_path=SEMANTIC):
    inputs, outputs, metadata = Inputs(root), {}, {}
    old = json.loads(inputs.read("full-dmg/okf-review-context.json"))
    manifest = decoded(inputs, "full-dmg", old["entrypoint_integrity"]["data_manifest"])
    records = [row for shard in manifest["shards"]["datasets"] for row in decoded(inputs, "full-dmg", shard)]
    resources = [row for shard in manifest["shards"]["resources"] for row in decoded(inputs, "full-dmg", shard)]
    edges = [row for shard in manifest["shards"]["relationships"] for row in decoded(inputs, "full-dmg", shard)]
    semantic_raw = inputs.read(semantic_path)
    semantic = json.loads(semantic_raw)
    require(semantic.get("schema") == "okf-context-index.v1", "Unsupported semantic overlay")
    statutory = json.loads(inputs.read("domain-profile/legal-bodies/context-overlay.json"))
    statutory_source_files = {}
    statutory_inventories = []
    for binding in statutory["bindings"]:
        if not binding["path"].startswith("source/"):
            continue
        raw = inputs.read(binding["path"])
        require(digest(raw) == binding["sha256"], "Statutory acquisition manifest changed")
        statutory_source_files[binding["path"]] = {"path": binding["path"], "bytes": len(raw), "sha256": digest(raw)}
        statutory_inventories.append(statutory_source_files[binding["path"]])
        directory = binding["path"].rsplit("/", 1)[0]
        for item in json.loads(raw)["files"]:
            path = directory + "/" + item["path"]
            value = inputs.read(path)
            require(len(value) == item["bytes"] and digest(value) == item["sha256"], "Retained statutory source changed")
            statutory_source_files[path] = {"path": path, "bytes": len(value), "sha256": digest(value)}
    declarations_path = "domain-profile/staff-semantic/concepts.yamlld"
    inputs.read(declarations_path)
    declarations = load_yaml(inputs.path(declarations_path))
    pages, documents = load_pages(inputs)
    page_by_route = {row["route"]: row for row in pages}
    nav = json.loads(inputs.read("full-dmg/context/navigation/manifest.json"))
    assignments = {row["route"]: row for part in nav["assignments"]
                   for row in decoded(inputs, "full-dmg/context/navigation", part)["assignments"]}
    require(set(assignments) == set(page_by_route), "Classification and source page universes differ")
    old_records = {row["route"]: deepcopy(row) for row in records}
    full_text = {}
    for record in records:
        page = page_by_route.get(record["route"])
        record["source_family"] = "DMG" if record["publisher"] == "dwp" else "Project-authored"
        full_text[record["route"]] = page["text"] if page else record.get("narrative", {}).get("body", "")
    config = json.loads(inputs.read("context/corpus-sources.json"))
    adm_config = next(row for row in config["sources"] if row["id"] == "adm")
    adm_inventory_raw = inputs.read(adm_config["inventory"])
    adm_inventory = json.loads(adm_inventory_raw)
    require(adm_inventory["summary"]["complete_for_frozen_adm_census"], "ADM frozen census incomplete")
    times = [observed(doc) for doc in documents.values()]
    if semantic:
        times.extend(p["captured_at"] for row in semantic["records"] for p in row.get("provenance", []) if p.get("captured_at"))
    when = max(times, key=utc_key)
    guide = new_node("guide/adm", "Advice for decision making: captured source collection", "Collection overview",
                     "# Advice for decision making\n\n" + "\n\n".join(LIMITATIONS), when)
    # A project-authored guide has no fabricated PDF or official authority.
    guide_record = deepcopy(next(row for row in records if row["route"] == "guide/full-dmg"))
    guide_record.update(id=guide["@id"], name=guide["route"], route=guide["route"], title=guide["title"],
        narrative={"title": guide["title"], "body": guide["body"]}, resource_ids=[], resource_count=0,
        source_family="ADM", url=adm_config["collection_url"], metadata_created=when)
    guide_record["extras"] = {"source_dates": {"generated_at": when, "publication_date_status": "not-established-from-document-evidence"}}
    guide_record["provenance"] = {"semantic_iri": guide["@id"], "authority": "independent project-authored navigation",
        "review_status": "unreviewed", "date_roles": {"generated_at": when}}
    records.append(guide_record)
    full_text[guide["route"]] = guide["body"]
    source_documents = json.loads(inputs.read("full-dmg/data/source-documents.json"))["documents"]
    for row in source_documents:
        row["source_family"] = "dmg"
    for doc in sorted(adm_inventory["documents"], key=lambda row: row["id"]):
        route = "document/adm/" + doc["id"]
        doc_node = new_node(route, doc["title"], "Source document", "", observed(doc))
        body = f"# {doc['title']}\n\nAdvice for decision making (ADM). {doc['pages']} measured PDF pages.\n\nCapture: {observed(doc)}. Source publication and current applicability are not established."
        record, resource = source_record(route, doc["title"], body, doc)
        records.append(record); resources.append(resource); full_text[route] = body
        edge = source_assertion(doc_node, guide, doc, None)
        edge["evidence"][0].update(url=adm_config["collection_url"], source_artifact=adm_config["inventory"],
            source_sha256=digest(adm_inventory_raw), source_field=f"documents[{doc['id']}].url",
            source_value=doc["url"], source_value_sha256=digest(doc["url"].encode()))
        edge["derivation"] = BASE + "rules/frozen-source-containment-v1"
        edges.append(runtime_edge(edge))
        routes = []
        for page in [row for row in pages if row["document_id"] == doc["id"] and row["family"] == "adm"]:
            route = page["route"]; routes.append(route)
            title = f"{doc['title']} — PDF page {page['page']}"
            body = f"# {title}\n\n> Machine-extracted source text. Tables, footnotes and reading order require checking.\n\n" + source_text_block(page["text"])
            record, resource = source_record(route, title, body, doc, page)
            records.append(record); resources.append(resource); full_text[route] = page["text"]
            edge = source_assertion(new_node(route, title, "Source PDF page", body, observed(doc)), doc_node, doc, page["page"])
            edge["derivation"] = BASE + "rules/frozen-source-containment-v1"
            edges.append(runtime_edge(edge))
        source_documents.append({"id": doc["id"], "route": doc_node["route"], "page_routes": routes,
            "pages": doc["pages"], "role": role(doc), "url": doc["url"], "sha256": doc["sha256"],
            "pages_path": doc["pages_path"], "source_family": "adm"})
    inputs.read("context/corpus/manifest.json")
    inputs.read("context/corpus/base-index.json")
    if semantic:
        add_semantics(records, resources, edges, full_text, semantic, when, semantic_path, digest(semantic_raw))
    semantic_concepts = {row["id"]: row for row in semantic["records"] if row["kind"] == "concept"} if semantic else {}
    semantic_references = defaultdict(list)
    for edge in semantic["assertions"] if semantic else []:
        if edge["source"] in semantic_concepts and edge["predicate"] == "http://purl.org/dc/terms/references":
            concept = semantic_concepts[edge["source"]]
            semantic_references[edge["target"]].append({"value_id": concept["id"], "label": concept["label"], "assertion_id": edge["id"],
                "method": "curated-reference", "review_status": concept.get("review_status", "unreviewed")})
    for record in records:
        assignment = assignments.get(record["route"])
        for key in DIMENSIONS:
            record[key] = assignment["facets"][key] if assignment else record.get(key, [UNKNOWN])
        if semantic_references[record["id"]]:
            record["concept"] = sorted(set(record["concept"]) - {UNKNOWN} | {row["label"] for row in semantic_references[record["id"]]})
        record["topics"] = record["topic"]
        record["classification"] = {"status": "unreviewed", "basis": "navigation-only", "audit": "context/navigation/manifest.json",
            "semantic_references": semantic_references[record["id"]], "semantic_source": "context/corpus/base-index.json"}
    records.sort(key=lambda row: row["route"])
    require(len({row["id"] for row in records}) == len(records), "Duplicate record identity")
    by_route = {row["route"]: row for row in records}
    edges.sort(key=lambda row: row["id"])
    require(len({row["id"] for row in edges}) == len(edges), "Duplicate relationship identity")
    require(all(edge["source"] in by_route and edge["target"] in by_route for edge in edges), "Unresolved graph endpoint")
    inputs.read("scripts/build_combined_reader.py")
    for path in ("scripts/build_full_dmg.py", "scripts/build_bundle.py", "scripts/build_review_navigation.py", "scripts/build_context_discovery.py", "uv.lock",
                 "profiles/bundle-wiki/v1/context.jsonld", "profiles/bundle-wiki/v1/semantic-context.jsonld",
                 "profiles/bundle-wiki/v1/bundle.schema.json", "profiles/bundle-wiki/v1.vendor-lock.json"):
        inputs.read(path)
    assertion_schema = json.loads(inputs.read("profiles/bundle-wiki/v1/semantic-assertion.schema.json"))
    validator = Draft202012Validator(assertion_schema, format_checker=FormatChecker())
    for edge in edges:
        validator.validate({**edge, "source": edge["source_iri"], "target": edge["target_iri"]})
    snapshot = "dwp-combined-" + digest(canonical(sorted(inputs.files.values(), key=lambda row: row["path"])))[:20]

    def put(path, value):
        raw = canonical(value)
        require(len(raw) <= 64 * 1024 * 1024, "Reader decoded-byte limit")
        outputs[path] = deterministic_gzip(raw) if path.endswith(".gz") else raw
        metadata[path] = {"path": path, "bytes": len(outputs[path]), "sha256": digest(outputs[path]),
            "decoded_bytes": len(raw), "decoded_sha256": digest(raw), "snapshot": snapshot}
        return metadata[path]

    def bind(path):
        raw = outputs[path]
        return {"path": path, "bytes": len(raw), "sha256": digest(raw)}

    dataset_shards = [put(f"data/records-{offset // CHUNK:04d}.json.gz", records[offset:offset + CHUNK]) for offset in range(0, len(records), CHUNK)]
    resource_shards = [put(f"data/resources-{offset // CHUNK:04d}.json.gz", resources[offset:offset + CHUNK]) for offset in range(0, len(resources), CHUNK)]
    relationship_shards = [put(f"data/relationships-{offset // CHUNK:04d}.json.gz", edges[offset:offset + CHUNK]) for offset in range(0, len(edges), CHUNK)]
    locations, adjacency = defaultdict(dict), defaultdict(dict)
    for ordinal, record in enumerate(records):
        locations[bucket(record["route"])][record["route"]] = [ordinal // CHUNK, ordinal % CHUNK]
    for edge in edges:
        for route in {edge["source"], edge["target"]}:
            adjacency[bucket(route)].setdefault(route, []).append(edge)
    locator = {}
    for key, rows in sorted(locations.items()):
        path = f"data/locator/{key}.json"; put(path, rows); locator[key] = bind(path)
    put("data/locator/manifest.json", {"schema": "okf-record-locator-sharded.v1", "algorithm": "fnv1a32-prefix-2", "snapshot": snapshot,
        "records": len(records), "chunk_size": CHUNK, "record_chunks": [row["path"] for row in dataset_shards], "buckets": locator, "bucket_count": len(locator)})
    adjacent_shards = [put(f"data/adjacency/{key}.json.gz", rows) for key, rows in sorted(adjacency.items())]
    put("data/adjacency/manifest.json", {"schema": "okf-relationship-adjacency.v1", "algorithm": "fnv1a32-prefix-2", "snapshot": snapshot,
        "routes": sum(map(len, adjacency.values())), "relationships": len(edges), "buckets": {key: f"data/adjacency/{key}.json.gz" for key in sorted(adjacency)}, "shards": adjacent_shards})
    search = build_search(records, full_text, snapshot, put)
    facets = search["facets"]
    for key in LABELS:
        values = defaultdict(list)
        for ordinal, row in enumerate(records):
            for value in row[key] if isinstance(row[key], list) else [row[key]]:
                values[value].append(ordinal)
        path = f"data/search/filters/{key}.json.gz"
        put(path, {"schema": "okf-filter-postings.v1", "key": key, "values": dict(sorted(values.items()))})
        search["manifest"]["entrypoints"]["filter_postings"][key] = path
        facets[key] = [{"value": value, "count": len(ids)} for value, ids in sorted(values.items(), key=lambda item: (-len(item[1]), item[0]))]
    for path in search["manifest"]["entrypoints"]["result_docs"]:
        rows = json.loads(gzip.decompress(outputs[path]))
        for row in rows:
            row.update({key: records[row["ordinal"]][key] for key in LABELS})
        put(path, rows)
    put("data/facets.json", facets)
    search_shards = {"search": [{**bind(path), "snapshot": snapshot} for path in sorted(outputs) if path.startswith("data/search/") or path == "data/facets.json"]}
    put("data/search/shards.json", {"snapshot": snapshot, "shards": search_shards})
    search["manifest"].update(shard_metadata="data/search/shards.json", shard_manifest_sha256=digest(canonical(search_shards)))
    put("data/search/manifest.json", search["manifest"])
    counts = {"records": len(records), "datasets": len(records), "resources": len(resources), "relationships": len(edges),
        "publishers": 3, "source_documents": len(documents), "source_pages": len(pages),
        "selected_statutory_units": sum(row["source_family"] == "Legislation" for row in records)}
    publishers = [{"id": "publisher/" + name, "name": name, "title": title,
        "dataset_count": sum(row["publisher"] == name for row in records), "resource_count": sum(row["resource_count"] for row in records if row["publisher"] == name)}
        for name, title in (("dwp", "DWP source; independent extraction"), ("independent-project", "Independent project-authored research"),
                            ("legislation-gov-uk", "Legislation.gov.uk source; independent extraction"))]
    put("data/publishers.json", publishers)
    put("data/overview.json", {"schema": "okf-large-overview.v1", "title": TITLE, "generated_at": when, "counts": counts,
        "recent_datasets": search["results"][:12], "notices": LIMITATIONS, "facet_previews": {key: rows[:15] for key, rows in facets.items()}})
    put("data/source-documents.json", {"snapshot": snapshot, "documents": source_documents})
    labels = endpoint_labels(records, resources, publishers, facets)
    put("data/endpoint-labels.json.gz", {"schema": "okf-explorer-endpoint-label-index.v1", "snapshot": snapshot, "generated_at": when,
        "default_language": "en-GB", "opaque_identifier_patterns": [], "entries": labels, "counts": {"entries": len(labels)}})
    analysis = []
    for key, label in LABELS.items():
        classified = len(records) - next((row["count"] for row in facets[key] if row["value"] == UNKNOWN), 0)
        analysis.append({"key": key, "label": label, "coverage": classified / len(records), "cardinality": len(facets[key]),
            "top_share": max(row["count"] for row in facets[key]) / len(records), "recommended_control": "list", "recommendation": "suggested",
            "classification": {"basis": ["source-inventory" if key == "source_family" else "curated-reference" if key == "concept" else "explicit-mention"],
                "review_status": "unreviewed", "classified_records": classified, "total_records": len(records), "limitations": LIMITATIONS[1:3]}})
    put("data/analysis.json", {"schema": "okf-analysis.v1", "snapshot": snapshot, "facet_analysis": analysis})
    new_manifest = {"title": TITLE, "snapshot": snapshot, "generated_at": when, "counts": counts,
        "chunks": {"datasets": [row["path"] for row in dataset_shards], "resources": [row["path"] for row in resource_shards],
            "relationships": [row["path"] for row in relationship_shards], "publishers": [bind("data/publishers.json")]},
        "shards": {"datasets": dataset_shards, "resources": resource_shards, "relationships": relationship_shards},
        "indexes": {"overview": "data/overview.json", "facets": "data/facets.json", "search": "data/search/manifest.json", "analysis": "data/analysis.json",
            "record_locator": bind("data/locator/manifest.json"), "relationship_adjacency": "data/adjacency/manifest.json", "endpoint_labels": bind("data/endpoint-labels.json.gz")}}
    put("data/manifest.json", new_manifest)
    semantic_manifest = emit_semantics(records, edges, semantic, declarations, snapshot, when, put, outputs, bind)
    descriptor = deepcopy(old)
    descriptor.update(title=TITLE, description=LIMITATIONS[0], snapshot=snapshot, snapshot_id=snapshot, counts=counts, generated_at=when)
    descriptor["consumer"] = {"repository": "https://github.com/chris-page-gov/okf-explorer", "commit": CONSUMER_COMMIT}
    descriptor["semantic_descriptor"] = "okf-bundle.yamlld"
    descriptor["entrypoints"] = {"markdown_index": "index.md"}; descriptor["entrypoint_integrity"] = {}
    for key, path in {"data_manifest": "data/manifest.json", "overview_index": "data/overview.json", "search_manifest": "data/search/manifest.json",
        "record_locator": "data/locator/manifest.json", "relationship_adjacency": "data/adjacency/manifest.json", "endpoint_labels": "data/endpoint-labels.json.gz"}.items():
        descriptor["entrypoints"][key] = bind(path) if key in {"record_locator", "endpoint_labels"} else path
        descriptor["entrypoint_integrity"][key] = bind(path)
    relocate_context(inputs, outputs, descriptor, snapshot, semantic)
    # Copy the small audit manifests and exact assignment shards, not old runtime outputs.
    for path in ["manifest.json", "catalogue.yamlld", *[row["path"] for row in nav["assignments"]]]:
        outputs["context/navigation/" + path] = inputs.read("full-dmg/context/navigation/" + path)
    outputs["context/navigation/frozen-manifest.json"] = outputs["context/navigation/manifest.json"]
    nav = deepcopy(nav)
    nav["source_snapshot"] = snapshot
    nav["limitations"] = LIMITATIONS
    nav["assignment_scope"] = "Frozen whole-page literal assignments. Additive authored semantic references are retained per Reader record with assertion IDs and the bound context base."
    nav["frozen_assignment_manifest"] = bind("context/navigation/frozen-manifest.json")
    nav["semantic_reference_index"] = bind("context/corpus/base-index.json")
    outputs["context/navigation/manifest.json"] = pretty(nav)
    descriptor["entrypoints"]["concept_navigation"] = bind("context/navigation/manifest.json")
    descriptor["entrypoint_integrity"]["concept_navigation"] = bind("context/navigation/manifest.json")
    descriptor["extensions"]["okf-explorer-presentation.v1"]["snapshot"] = snapshot
    descriptor["extensions"]["okf-explorer-presentation.v1"]["facets"].insert(0,
        {"key": "source_family", "label": "Source family", "description": "DMG, ADM, selected statutory units or project-authored material; legal regime and applicability still require checking.",
         "order": -1, "default_state": "pinned", "open_control": "list", "value_order": "count-desc"})
    descriptor["vocabulary"]["search_placeholder"] = "Search captured guidance and selected legislation"
    source_identity = {"pdf_documents": [{"id": doc["id"], "sha256": doc["sha256"]} for doc in sorted(documents.values(), key=lambda row: row["id"])],
        "statutory_retained_files": sorted(statutory_source_files.values(), key=lambda row: row["path"])}
    put("data/source-identity.json", source_identity)
    descriptor["plane_roots"] = {"source": digest(canonical(source_identity)),
        "semantic": semantic_manifest["semantic_identity"]["sha256"], "data": digest(canonical(dataset_shards)), "search": digest(canonical(search_shards)), "presentation": digest(canonical(descriptor["extensions"]))}
    descriptor["exploratory_publication"].update(snapshot_id=snapshot, generated_at=when, applicable_plane_roots=descriptor["plane_roots"], limitations=LIMITATIONS)
    descriptor["source"] = {"url": REPO, "inventory": "context/corpus-sources.json", "sha256": digest(inputs.read("context/corpus-sources.json")), "observed_at": when}
    descriptor["source"].update(identity=bind("data/source-identity.json"), statutory_inventories=statutory_inventories,
        scope="513 captured DWP PDFs plus separately retained statutory acquisition projections and failures. Original statutory HTTP hashes are observed; original responses are not retained publicly.")
    put("okf-explorer.json", descriptor)
    control = {"@context": context(), "@id": BASE + "id/bundle/combined", "@type": "okf:Bundle", "title": TITLE,
        "description": LIMITATIONS[0], "version": "0.1.0", "status": "experimental",
        "descriptor": {"@id": BASE + "combined/okf-explorer.json"}, "semanticDescriptor": {"@id": BASE + "combined/okf-bundle.yamlld"},
        "home": {"@id": REPO}, "profile": {"@id": PROFILE}, "publisher": {"@id": "https://github.com/chris-page-gov"},
        "license": {"@id": REPO + "/blob/main/NOTICE.md"}, "snapshot_id": snapshot,
        "semantic_manifest": bind("data/semantic/manifest.json"), "counts": semantic_manifest["counts"],
        "assertion_scope": "real-world", "exploratory_publication": descriptor["exploratory_publication"]}
    Draft202012Validator(json.loads(inputs.read("profiles/bundle-wiki/v1/bundle.schema.json")), format_checker=FormatChecker()).validate(control)
    outputs["okf-bundle.yamlld"] = yaml_bytes(control)
    put("okf-bundle.jsonld", control)
    put("coverage.json", {"schema": "okf-combined-reader-coverage.v1", "snapshot": snapshot, **counts,
        "families": dict(sorted(Counter(row["family"] for row in pages).items())), "empty_extractions": sum(not row["text"].strip() for row in pages),
        "reader_records_by_family": dict(sorted(Counter(row["source_family"] for row in records).items())),
        "preserved_dmg_records": len(old_records), "semantic_overlay": semantic_path if semantic else None, "limitations": LIMITATIONS})
    outputs["index.md"] = ("# " + TITLE + "\n\n" + "\n\n".join(LIMITATIONS) + "\n\n[Indexed Reader descriptor](okf-explorer.json) · [Source coverage](coverage.json) · [Source documents](data/source-documents.json).\n").encode()
    receipt = {"schema": "okf-combined-reader-build.v1", "snapshot": snapshot,
        "inputs": sorted(inputs.files.values(), key=lambda row: row["path"]),
        "outputs": [{"path": OUTPUT + "/" + path, "bytes": len(raw), "sha256": digest(raw)} for path, raw in sorted(outputs.items())]}
    return {OUTPUT + "/" + path: raw for path, raw in outputs.items()} | {"validation/combined-reader/build.json": pretty(receipt)}


def endpoint_labels(records, resources, publishers, facets):
    result = {}
    def add(route, title, kind="Facet value", iri=None):
        label = re.sub(r"\s+", " ", title).strip()
        require(label and len(label) <= 512, "Invalid endpoint label")
        row = {"route": route, "iri": iri or BASE + "id/" + route, "label": label, "language": "en-GB", "type": kind,
            "label_authority": {"class": "editorial", "source": REPO + "/blob/main/scripts/build_combined_reader.py"}}
        require(route not in result or result[route] == row, "Conflicting endpoint label")
        result[route] = row
    titles = {row["route"]: row["title"] for row in records}
    for row in records:
        add(row["route"], row["title"], row["record_type"], row["id"])
        for kind, values in (("format", row["formats"]), ("topic", row["topics"]), ("tag", row["tags"]), ("license", [row["license_id"]])):
            for value in values:
                add(kind + "/" + quote(value, safe="-._~"), row["license_title"] if kind == "license" else value, kind)
    for row in resources:
        add("resource/" + row["id"], row["name"] + " — " + titles[row["dataset"]], "Source resource", BASE + "id/" + row["id"])
    for row in publishers:
        add(row["id"], row["title"], "Source organisation")
    for key, rows in facets.items():
        for row in rows:
            add("facet/" + quote(key, safe="-._~") + "/" + quote(row["value"], safe="-._~"), row["value"])
    return list(result.values())


def emit_semantics(records, edges, semantic, declarations, snapshot, when, put, outputs, bind):
    """Emit direct and reified assertions from one governed assertion set.

    Semantic nodes are identity/definition projections. Source page bodies stay
    in their hash-bound Reader and acquisition records; snippets are not new
    authoritative policy literals. Each RDF shard has its own blank-node scope.
    """
    declaration_map = {row["@id"]: row for row in declarations["@graph"]}
    context_map = {row["id"]: row for row in semantic["records"]}
    semantic_context = context() + [declarations["@context"]]
    status_types = {"official": "okf:OfficialAssertion", "normalized": "okf:NormalizedAssertion",
                    "inferred": "okf:InferredAssertion", "model-derived": "okf:ModelDerivedAssertion"}
    nodes = {}
    for record in records:
        authored = declaration_map.get(record["id"])
        item = context_map.get(record["id"])
        node = {"@id": record["id"], "@type": authored["@type"] if authored else "schema:DigitalDocument",
            "route": record["route"], "title": item["label"] if authored else record["title"], "type": record["record_type"],
            "generated": {"by": "process:okf-combined-reader-build/1", "at": when},
            "okf:reviewStatus": record["provenance"].get("review_status", "unreviewed"),
            "dcterms:source": {"@id": record["url"]}, "dcterms:license": {"@id": record["license_source_id"]},
            "projection_note": "Generated identity and relationship projection; complete source text and extraction hashes remain in the bound Reader records."}
        if item:
            node["okf:assertionStatus"] = {"@id": status_types[item["assertion_status"]]}
            node["prov:wasDerivedFrom"] = [{"@id": p["url"]} for p in item["provenance"]]
            if item["kind"] == "concept":
                if not authored:
                    node["@type"] = "skos:Concept"
                node["skos:prefLabel"] = {"@value": item["label"], "@language": "en-GB"}
                node["skos:definition"] = {"@value": item["text"], "@language": "en-GB"}
        if record["provenance"].get("source_sha256"):
            node["okf:sourceSha256"] = record["provenance"]["source_sha256"]
        if record["provenance"].get("page_text_sha256"):
            node["okf:pageTextSha256"] = record["provenance"]["page_text_sha256"]
        nodes[record["id"]] = node
    assertions = [{**edge, "source": edge["source_iri"], "target": edge["target_iri"]} for edge in edges]
    for edge in assertions:
        value = {"@id": edge["target"]}
        direct = nodes[edge["source"]].setdefault(edge["predicate"], [])
        if value not in direct:
            direct.append(value)
    groups = {}
    for kind, rows in (("nodes", sorted(nodes.values(), key=lambda row: row["@id"])), ("assertions", assertions)):
        shards = []
        for offset in range(0, len(rows), CHUNK):
            graph = {"@context": semantic_context, "@graph": rows[offset:offset + CHUNK]}
            path = f"data/semantic/{kind}-{offset // CHUNK:04d}.jsonld.gz"
            metadata = put(path, graph)
            metadata.update(count=len(graph["@graph"]), media_type="application/ld+json", encoding="gzip")
            rdf = jsonld.normalize(graph, options={"algorithm": "URDNA2015", "format": "application/n-quads", "documentLoader": pinned_loader})
            rdf_path = path.replace(".jsonld.gz", ".nq.gz")
            outputs[rdf_path] = deterministic_gzip(rdf.encode())
            metadata["rdf"] = {**bind(rdf_path), "canonical_sha256": digest(rdf.encode()), "statements": len(rdf.splitlines()),
                "canonicalisation": "URDNA2015; blank-node scope is this shard"}
            shards.append(metadata)
        groups[kind] = shards
    triples = sorted([edge["source"], edge["predicate"], edge["target"]] for edge in assertions)
    direct = sorted({tuple(triple) for triple in triples})
    manifest = {"schema": "okf-semantic-shard-manifest.v1", "snapshot": snapshot,
        "canonical_authoring": "Frozen source identities and existing governed assertions, plus domain-profile/staff-semantic YAML-LD and verified legal citation references; all authored meanings remain unreviewed.",
        "projection_scope": "Identity and definition nodes with direct triples and the same reified assertions. Complete source page bodies remain in bound Reader and acquisition records.",
        "partition": {"algorithm": "lexical-absolute-IRI-contiguous", "max_rows": CHUNK}, **groups,
        "counts": {"nodes": len(nodes), "assertions": len(assertions), "distinct_direct_triples": len(direct)},
        "assertion_ids_sha256": digest(canonical([row["@id"] for row in assertions])),
        "direct_reified_triples_sha256": digest(canonical(triples)), "distinct_direct_triples_sha256": digest(canonical(direct)),
        "direct_triple_policy": "Set of assertion subject-predicate-object triples; evidence-bearing duplicate assertions retain separate identities.",
        "semantic_identity": {"algorithm": "sha256-over-canonical-shard-manifest; RDF canonicalised independently per shard", "sha256": digest(canonical(groups))}}
    put("data/semantic/manifest.json", manifest)
    return manifest


def add_semantics(records, resources, edges, full_text, semantic, when, semantic_path=SEMANTIC, semantic_sha=None):
    """Project authored ContextRecords without inventing policy assertions."""
    by_id = {row["id"]: row for row in records}
    for row in semantic["records"]:
        if row["id"] in by_id:
            # The original Reader narrative is retained verbatim. The current
            # context definition is separately labelled, source linked and
            # available to the same search and graph consumer.
            if row["kind"] == "concept":
                target = by_id[row["id"]]
                target["context_semantics"] = {key: row[key] for key in ("text", "assertion_status", "authority", "provenance", "scope")}
                target["narrative"]["body"] += "\n\n## Current context definition — unreviewed\n\n" + row["text"] + "\n\n" + "\n".join(f"- [{p.get('locator', 'Source')}]({p['url']})" for p in row.get("provenance", []))
                full_text[target["route"]] += "\n" + row["text"]
            continue
        route = row["route"]
        kind = {"concept": "Concept", "scope": "Scope note", "evidence": "Evidence record"}[row["kind"]]
        record = {"id": row["id"], "name": route, "route": route, "title": row["label"], "type": kind,
            "record_type": kind, "notes": row["text"][:360],
            "narrative": {"title": row["label"], "body": "# " + row["label"] + "\n\n**" + row["assertion_status"] + "; " + row.get("review_status", "unreviewed") + ".**\n\n" + row["text"] + "\n\n" + row["scope"] + "\n\n" + "\n".join(f"- [{p.get('locator', 'Source')}]({p['url']})" for p in row.get("provenance", []))},
            "publisher": "independent-project", "publisher_title": "Independent project-authored research", "resource_ids": [], "resource_count": 0,
            "formats": ["Markdown"], "tags": ["Authored semantic overlay — unreviewed"], "topics": [UNKNOWN], "source_family": "Project-authored",
            "source_role": "Project-authored research aid — unreviewed", "document_id": "Project-authored", "volume": "Project-authored",
            "source_tier": "unreviewed-project-authored", "source_adapter": "authored-context-overlay", "timestamp": "", "metadata_created": when, "url": REPO,
            "license_id": "mixed-see-notice", "license_title": "Original metadata MIT; source-specific rights apply", "license_source_id": REPO + "/blob/main/NOTICE.md",
            "provenance": {"semantic_iri": row["id"], "authority": row.get("authority"), "assertion_status": row.get("assertion_status"),
                "review_status": row.get("review_status", "unreviewed"), "source_references": row.get("provenance", []), "date_roles": {"generated_at": when}}}
        if route.startswith("legal-body/"):
            require(row["kind"] == "evidence" and row["authority"]["class"] == "derived"
                    and row["assertion_status"] == "normalized" and row.get("review_status") == "unreviewed",
                    "Statutory body must remain a derived, unreviewed evidence record")
            source = row["provenance"][0]
            require(urlsplit(source["url"]).hostname == "www.legislation.gov.uk"
                    and source["literal_sha256"] == digest(row["text"].encode()), "Invalid statutory source identity")
            resource_id = "resource/source-" + digest(route.encode())[:24]
            dates = {"captured_at": source["captured_at"], "generated_at": when,
                     "requested_source_version": source["source_date"],
                     "publication_date_status": "not-established-from-document-evidence",
                     "commencement_status": "not-established-for-task"}
            record.update(type="Statutory unit", record_type="Statutory unit", source_family="Legislation",
                publisher="legislation-gov-uk", publisher_title="Legislation.gov.uk source; independent extraction",
                source_role="Selected dated statutory unit — unreviewed extraction", source_tier="official-source-unreviewed-extraction",
                source_adapter="retained-statutory-xml-projection", document_id=route.removeprefix("legal-body/"),
                volume="Statutory provision", metadata_created=source["captured_at"], url=source["url"],
                resource_ids=[resource_id], resource_count=1, formats=["HTML"], tags=["Legislation", "Unreviewed extraction"],
                license_id="uk-ogl", license_title="Open Government Licence v3.0", license_source_id=row["rights"])
            record["provenance"].update(source_sha256=source["source_sha256"], literal_sha256=source["literal_sha256"], date_roles=dates)
            record["narrative"]["body"] = ("# " + row["label"] + "\n\n**Normalised machine extraction from legislation.gov.uk; unreviewed.**\n\n"
                + row["scope"] + "\n\n## Captured source text\n\n" + source_text_block(row["text"])
                + "\n\n## Provenance\n\n" + "\n".join(f"- [{p['locator']}]({p['url']})" for p in row["provenance"]))
            resources.append({"id": resource_id, "route": resource_id, "dataset": route, "name": "Official dated statutory source",
                "url": source["url"], "host": urlsplit(source["url"]).hostname, "format": "HTML",
                "source_access": {"url": source["url"], "label": "Verify the official statutory source", "media_type": "text/html", "display_mode": "link"},
                "provenance": record["provenance"]})
        records.append(record); by_id[row["id"]] = record; full_text[route] = row["text"]
    existing = {row["id"] for row in edges}
    predicate_labels = {row["predicate"]: (row["kind"], row.get("inverse_label", "is referenced by")) for row in edges}
    for assertion_ordinal, row in enumerate(semantic["assertions"]):
        if row["id"] in existing:
            continue
        require(row["source"] in by_id and row["target"] in by_id, "Semantic overlay has unresolved endpoint")
        kind, inverse = predicate_labels.get(row["predicate"], ("semantic-reference", "is referenced by"))
        evidence = [{"@id": BASE + "id/evidence/context-projection/" + digest(canonical([row["id"], index, item])),
            "type": "captured-context-provenance", "url": REPO + "/blob/main/" + semantic_path,
            "source_artifact": semantic_path, "source_sha256": semantic_sha or digest(canonical(semantic)),
            "source_field": f"assertions[{assertion_ordinal}].provenance[{index}]", "source_value": item,
            "source_value_sha256": digest(canonical(item)), "source_value_hash_canonicalization": "canonical-json-sorted-keys-utf8",
            "locator": item["locator"], "retrieved_at": item["captured_at"],
            "original_source_url": item["url"], "original_source_sha256": item["source_sha256"],
            **({"literal_sha256": item["literal_sha256"]} if item.get("literal_sha256") else {}),
            "rationale": "Preserved captured provenance from the authored context assertion; this projection does not invent a source quotation."}
            for index, item in enumerate(row["provenance"])]
        projected = {**row, "@id": row["id"], "@type": ["rdf:Statement", "RelationshipAssertion"],
            "source": by_id[row["source"]]["route"], "target": by_id[row["target"]]["route"],
            "source_route": by_id[row["source"]]["route"], "target_route": by_id[row["target"]]["route"],
            "source_iri": row["source"], "target_iri": row["target"], "label": row.get("label") or row["predicate"].rsplit("/", 1)[-1],
            "kind": row.get("kind", kind), "inverse_label": inverse, "assertion_scope": "real-world", "evidence": evidence,
            "derivation": BASE + "rules/authored-context-assertion-projection-v1",
            "observed_at": max((item["captured_at"] for item in row["provenance"]), key=utc_key),
            "review_status": "unreviewed-specialist-review-required",
            "rights": {"source": REPO + "/blob/main/NOTICE.md", "assertion": "Original project-authored context assertion projection; source-specific rights remain applicable."},
            "projection_source": semantic_path}
        if row["assertion_status"] == "model-derived":
            projected.update(confidence_score=0.5, derivation_activity=BASE + "id/activity/staff-semantic-authoring",
                confidence_method="Fixed schema compatibility indicator used by the existing full-DMG authoring profile; uncalibrated, not a probability or specialist grade.")
        edges.append(projected)


def relocate_context(inputs, outputs, descriptor, snapshot, semantic):
    """Rebind only the additive manifest/base; retain exact frozen source shards."""
    manifest = json.loads(inputs.read("context/corpus/manifest.json"))
    # Preserve the explicit version link to the source semantics in the new base.
    base = deepcopy(semantic) if semantic else json.loads(inputs.bound("context/corpus", manifest["base_index"]))
    base["bundle"]["snapshot"] = snapshot
    base_raw = canonical(base)
    require(len(base_raw) <= 8 * 1024 * 1024, "Combined context base exceeds the consumer 8 MiB semantic-index bound")
    outputs["context/corpus/base-index.json"] = base_raw
    manifest["base_index"] = {"path": "base-index.json", "bytes": len(base_raw), "sha256": digest(base_raw)}
    manifest["semantic_source_snapshot"] = snapshot
    manifest["bundle"]["snapshot"] = "dwp-combined-context-" + digest(base_raw)[:20]
    for binding in [*manifest["records"]["shards"], *manifest["search"]["shards"].values()]:
        raw = inputs.bound("context/corpus", binding)
        decoded_raw = gzip.decompress(raw)
        require(len(decoded_raw) == binding["decoded_bytes"] and digest(decoded_raw) == binding["decoded_sha256"], "Context source shard integrity mismatch")
        outputs["context/corpus/" + binding["path"]] = raw
    outputs["context/corpus/manifest.json"] = pretty(manifest)
    outputs["context/assembly-index.json"] = base_raw
    for key, path in (("context_assembly", "context/assembly-index.json"), ("context_corpus", "context/corpus/manifest.json")):
        binding = {"path": path, "bytes": len(outputs[path]), "sha256": digest(outputs[path])}
        descriptor["entrypoints"][key] = binding; descriptor["entrypoint_integrity"][key] = binding


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = compile_combined()
    for name, raw in outputs.items():
        path = ROOT / name
        if args.check:
            require(path.is_file() and path.read_bytes() == raw, "Stale combined Reader: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    print(json.dumps({"status": "verified" if args.check else "built", "files": len(outputs), "coverage": json.loads(outputs["combined/coverage.json"])}))


if __name__ == "__main__":
    main()
