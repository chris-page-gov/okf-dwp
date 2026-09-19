#!/usr/bin/env python3
"""Add reviewable conceptual navigation without rewriting frozen source releases.

Literal mention tags and existing authored references are discovery metadata.
They never create appliesTo assertions, legal answers or completeness profiles.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import gzip
import json
import math
from pathlib import Path
import re
from urllib.parse import quote

from build_bundle import BASE, ROOT, canonical, digest, load_yaml, pretty
from build_context_corpus import deterministic_gzip
from build_context_discovery import Inputs, read_semantics, require

RULES = "domain-profile/navigation/catalogue.yamlld"
OUTPUT = "full-dmg/context/navigation"
RUNTIME = "context/navigation/runtime"
DIMENSIONS = {"benefit": "Benefit mentions", "circumstance": "Circumstance mentions",
              "topic": "Topic mentions", "concept": "Authored concept references"}
UNKNOWN = "Not classified"
LIMITATIONS = [
    "Independent experimental navigation metadata; not official guidance or a legal applicability classification.",
    "Explicit mentions use whole-word literal matching, flexible whitespace and case-sensitive declared abbreviations. A mention may occur in a footnote, example, exclusion or historical passage.",
    "Authored concept references retain existing unreviewed source-selection decisions. No page inherits concepts from neighbouring pages or a chapter title.",
    "Not classified means that this limited method found no assignment. It does not mean the subject is absent.",
    "The assignment audit covers DMG and ADM. The additive Reader projection retains the frozen DMG record universe; ADM remains available through Ask OKF and the assignment audit.",
    "Source capture, publication, revision and legal effective dates remain distinct. No date or current-law status is inferred by navigation classification.",
]


def load_rules(inputs):
    inputs.read(RULES)
    data = load_yaml(inputs.path(RULES))
    require(data.get("schema") == "okf-dwp-navigation-rules.v1", "Unknown navigation rule schema")
    rules = [row for row in data["@graph"] if row.get("@type") == "skos:Concept"]
    require(len({r["@id"] for r in rules}) == len(rules), "Duplicate navigation rule")
    for row in rules:
        require(row.get("dimension") in {"benefit", "circumstance", "topic"}, "Unknown rule dimension")
        require(row.get("review_status") == "unreviewed", "Classification cannot claim review")
        require(row["@id"].startswith(BASE + "id/navigation/"), "Noncanonical navigation rule")
        require(set(row["match"]).issubset({"phrases", "case_sensitive_abbreviations", "excluded_spans"}), "Unknown literal matching control")
        values = row["match"].get("phrases", []) + row["match"].get("case_sensitive_abbreviations", [])
        require(values and all(isinstance(v, str) and 2 <= len(v) <= 100 for v in values), "Invalid literal rule")
        require(all(isinstance(v, str) and 2 <= len(v) <= 100 for v in row["match"].get("excluded_spans", [])), "Invalid excluded literal")
    return data, rules


def phrase_pattern(phrase):
    return r"(?<!\w)" + r"\s+".join(re.escape(x) for x in phrase.split()) + r"(?!\w)"


def compile_matchers(rules):
    return [(row, [(re.compile(phrase_pattern(term), re.IGNORECASE), term)
                   for term in row["match"].get("phrases", [])]
             + [(re.compile(phrase_pattern(term)), term)
                for term in row["match"].get("case_sensitive_abbreviations", [])]) for row in rules]


def literal_assignments(text, matchers):
    result = []
    for rule, patterns in matchers:
        excluded = [match.span() for phrase in rule["match"].get("excluded_spans", [])
                    for match in re.finditer(phrase_pattern(phrase), text, re.IGNORECASE)]
        matches = []
        for pattern, term in patterns:
            for match in pattern.finditer(text):
                if not any(start <= match.start() and match.end() <= end for start, end in excluded):
                    matches.append((match.start(), match.end(), term))
                    break
        if matches:
            start, end, term = min(matches)
            result.append({"value_id": rule["@id"], "dimension": rule["dimension"],
                           "label": rule["skos:prefLabel"]["@value"], "method": "explicit-mention",
                           "rule_literal": term, "start": start, "end": end, "matched_text": text[start:end]})
    return result


def load_pages(inputs):
    config = json.loads(inputs.read("context/corpus-sources.json"))
    source_map = json.loads(inputs.read("full-dmg/data/source-documents.json"))
    routes = {r["id"]: r["page_routes"] for r in source_map["documents"]}
    pages, documents = [], {}
    for family in config["sources"]:
        inventory = json.loads(inputs.read(family["inventory"]))
        for doc in sorted(inventory["documents"], key=lambda row: row["id"]):
            inputs.read(doc["pdf_path"], doc["sha256"], doc["size_bytes"])
            raw = json.loads(inputs.read(doc["pages_path"], doc["pages_sha256"]))
            require(raw["source_sha256"] == doc["sha256"] and len(raw["pages"]) == doc["pages"], "Source page identity mismatch")
            require([x["page"] for x in raw["pages"]] == list(range(1, doc["pages"] + 1)), "Noncontiguous page sequence")
            documents[doc["id"]] = doc | {"family": family["id"]}
            for page in raw["pages"]:
                route = (routes[doc["id"]][page["page"] - 1] if family["id"] == "dmg"
                         else f"page/adm/{doc['id']}/{page['page']:04d}")
                require(page["url"] == doc["url"] + f"#page={page['page']}", "Page URL mismatch")
                pages.append(page | {"route": route, "id": BASE + "id/" + route, "document_id": doc["id"],
                                     "family": family["id"], "source_sha256": doc["sha256"],
                                     "literal_sha256": digest(page["text"].encode())})
    return sorted(pages, key=lambda row: row["id"]), documents


def classify_pages(pages, rules, nodes, assertions):
    matchers = compile_matchers(rules)
    concepts = {iri: row for iri, row in nodes.items() if row.get("type") == "Concept"}
    label_counts = Counter(row["title"] for row in concepts.values())
    concept_values = {iri: {"id": iri, "label": row["title"] + (f" [{row['route']}]" if label_counts[row["title"]] > 1 else ""),
                            "dimension": "concept", "method": "curated-reference", "review_status": "unreviewed"}
                      for iri, row in concepts.items()}
    references = defaultdict(list)
    for edge in assertions:
        if edge["source"] in concepts and edge["predicate"] == "http://purl.org/dc/terms/references":
            references[edge["target"]].append({"value_id": edge["source"], "dimension": "concept",
                                                "label": concept_values[edge["source"]]["label"],
                                                "method": "curated-reference", "assertion_id": edge["@id"],
                                                "source_assertion_status": edge["assertion_status"],
                                                "source_review_status": edge.get("review_status", "not-declared")})
    assignments = []
    for page in pages:
        evidence = literal_assignments(page["text"], matchers) + sorted(references[page["id"]], key=lambda row: row["value_id"])
        facets = {key: sorted({row["label"] for row in evidence if row["dimension"] == key}) or [UNKNOWN]
                  for key in DIMENSIONS}
        assignments.append({"record_id": page["id"], "route": page["route"], "source_group": page["family"],
                            "document_id": page["document_id"], "page": page["page"], "source_url": page["url"],
                            "source_sha256": page["source_sha256"], "literal_sha256": page["literal_sha256"],
                            "empty_extraction": not page["text"].strip(), "facets": facets, "evidence": evidence,
                            "assertion_status": "normalized", "review_status": "unreviewed"})
    return assignments, list(concept_values.values())


def ontology_inventory(inputs, semantic, nodes, assertions):
    """Count actual RDF positions, excluding URLs mentioned inside prose."""
    predicates, types = Counter(), Counter()
    pattern = re.compile(r"^(?:<[^>]*>|_:[^ ]+) <([^>]*)> (.*)")
    for kind in ("nodes", "assertions"):
        for shard in semantic[kind]:
            rdf = shard["rdf"]
            raw = gzip.decompress(inputs.bound("full-dmg", rdf))
            require(digest(raw) == rdf["canonical_sha256"], "Canonical RDF hash mismatch")
            for line in raw.decode().splitlines():
                match = pattern.match(line)
                require(match is not None, "Unrecognised canonical N-Quad")
                predicates[match[1]] += 1
                if match[1] == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" and match[2].startswith("<"):
                    types[match[2][1:match[2].index(">")]] += 1
    namespaces = {"RDF": "http://www.w3.org/1999/02/22-rdf-syntax-ns#", "RDFS": "http://www.w3.org/2000/01/rdf-schema#",
                  "SKOS": "http://www.w3.org/2004/02/skos/core#", "Dublin Core terms": "http://purl.org/dc/terms/",
                  "PROV-O": "http://www.w3.org/ns/prov#", "DCAT": "http://www.w3.org/ns/dcat#",
                  "Schema.org": "https://schema.org/", "OKF profile": "https://chris-page-gov.github.io/okf-explorer/ns#",
                  "DWP project": "https://chris-page-gov.github.io/okf-dwp/ns#", "OWL": "http://www.w3.org/2002/07/owl#",
                  "ELI": "http://data.europa.eu/eli/ontology#"}
    return {"schema": "okf-dwp-ontology-use-inventory.v1", "source_snapshot": semantic["snapshot"],
            "method": "predicate-and-rdf-type-positions-in-hash-verified-canonical-nquads-v1",
            "namespaces": [{"label": label, "namespace": namespace,
                "predicate_uses": sum(count for iri, count in predicates.items() if iri.startswith(namespace)),
                "type_uses": sum(count for iri, count in types.items() if iri.startswith(namespace))}
                for label, namespace in namespaces.items()],
            "rdf_types": dict(sorted(types.items())),
            "relationship_predicates": dict(sorted(Counter(edge["predicate"] for edge in assertions).items())),
            "runtime_concept_labels": sum(row.get("type") == "Concept" for row in nodes.values()),
            "limitations": ["Counts are occurrences in separately canonicalised shards, not a globally deduplicated RDF dataset.",
                "Declaring a namespace does not prove actual predicate/type use. ELI/OWL zero counts do not claim an imported legal ontology or reasoning.",
                "XSD supplies literal datatypes and is deliberately not counted as a predicate or class vocabulary.",
                "Older runtime Concept labels do not all have skos:Concept RDF types. This audit exposes that modelling debt without rewriting history."]}


def add_runtime(inputs, outputs, assignments, values, nav_binding):
    """Reuse stable DMG ordinals and text search, adding native filter postings."""
    original = json.loads(inputs.read("full-dmg/okf-corpus-context.json"))
    snapshot = original["snapshot"]
    manifest = json.loads(inputs.bound("full-dmg", original["entrypoint_integrity"]["data_manifest"]))
    by_route = {row["route"]: row for row in assignments}
    metadata = {}

    def put(path, value):
        raw = canonical(value)
        encoded = deterministic_gzip(raw) if path.endswith(".gz") else raw
        outputs["full-dmg/" + path] = encoded
        result = {"path": path, "bytes": len(encoded), "sha256": digest(encoded),
                  "decoded_bytes": len(raw), "decoded_sha256": digest(raw), "snapshot": snapshot}
        metadata[path] = result
        return result

    def bind(path):
        row = metadata[path]
        return {k: row[k] for k in ("path", "bytes", "sha256")}

    records, record_paths, record_shards, filters = [], [], [], {key: defaultdict(list) for key in DIMENSIONS}
    for index, shard in enumerate(manifest["shards"]["datasets"]):
        raw = inputs.bound("full-dmg", shard)
        decoded = gzip.decompress(raw)
        require(digest(decoded) == shard["decoded_sha256"], "Reader record hash mismatch")
        chunk = json.loads(decoded)
        for record in chunk:
            assignment = by_route.get(record["route"])
            record["classification"] = {"status": "unreviewed", "basis": "navigation-only",
                                        "audit": nav_binding["path"]}
            for key in DIMENSIONS:
                record[key] = assignment["facets"][key] if assignment else [UNKNOWN]
                for value in record[key]:
                    filters[key][value].append(len(records))
            # Explorer's established singular "topic" facet reads the plural
            # record field. Keep that canonical projection in parity with the
            # static postings; source_role retains the structural classification.
            record["topics"] = record["topic"]
            records.append(record)
        path = f"{RUNTIME}/records-{index:04d}.json.gz"
        record_paths.append(path)
        record_shards.append(put(path, chunk))
    require(len(records) == original["counts"]["records"], "Reader ordinal count changed")
    locator = json.loads(inputs.bound("full-dmg", original["entrypoints"]["record_locator"]))
    locator["record_chunks"] = record_paths
    put(f"{RUNTIME}/locator.json", locator)

    facets = json.loads(inputs.read("full-dmg/data/facets.json"))
    search = json.loads(inputs.bound("full-dmg", original["entrypoint_integrity"]["search_manifest"]))
    search_metadata = json.loads(inputs.read("full-dmg/" + search["shard_metadata"]))
    old_bindings = {row["path"]: row for row in search_metadata["shards"]["search"]}
    search_files = [row for path, row in old_bindings.items()
                    if path != search["entrypoints"]["facets"] and path not in search["entrypoints"]["result_docs"]]
    for key, rows in filters.items():
        facets[key] = [{"value": value, "count": len(ids)} for value, ids in sorted(rows.items(), key=lambda item: (-len(item[1]), item[0]))]
        path = f"{RUNTIME}/filters/{key}.json.gz"
        search_files.append(put(path, {"schema": "okf-filter-postings.v1", "key": key, "values": dict(sorted(rows.items()))}))
        search["entrypoints"]["filter_postings"][key] = path
    search_files.append(put(f"{RUNTIME}/facets.json", facets))
    search["entrypoints"]["facets"] = f"{RUNTIME}/facets.json"
    result_paths = []
    for index, old_path in enumerate(search["entrypoints"]["result_docs"]):
        rows = json.loads(gzip.decompress(inputs.bound("full-dmg", old_bindings[old_path])))
        for row in rows:
            require(records[row["ordinal"]]["route"] == row["open"], "Search record ordinal mismatch")
            row.update({key: records[row["ordinal"]][key] for key in DIMENSIONS})
            row["topics"] = records[row["ordinal"]]["topics"]
        path = f"{RUNTIME}/results-{index:04d}.json.gz"
        result_paths.append(path)
        search_files.append(put(path, rows))
    search["entrypoints"]["result_docs"] = result_paths
    search_shards = {"search": sorted(search_files, key=lambda row: row["path"])}
    put(f"{RUNTIME}/search-shards.json", {"snapshot": snapshot, "shards": search_shards})
    search["shard_metadata"] = f"{RUNTIME}/search-shards.json"
    search["shard_manifest_sha256"] = digest(canonical(search_shards))
    put(f"{RUNTIME}/search.json", search)
    overview = json.loads(inputs.bound("full-dmg", original["entrypoint_integrity"]["overview_index"]))
    overview["facet_previews"] = {key: rows[:15] for key, rows in facets.items()}
    overview["notices"] = LIMITATIONS + overview["notices"]
    put(f"{RUNTIME}/overview.json", overview)
    labels = json.loads(gzip.decompress(inputs.bound("full-dmg", original["entrypoint_integrity"]["endpoint_labels"])))
    for key in DIMENSIONS:
        for item in facets[key]:
            route = "facet/" + quote(key, safe="-._~") + "/" + quote(item["value"], safe="-._~")
            labels["entries"].append({"route": route, "iri": BASE + "id/" + route, "label": item["value"],
                                     "language": "en-GB", "type": DIMENSIONS[key],
                                     "label_authority": {"class": "editorial", "source": BASE + RULES}})
            if key == "topic":
                topic_route = "topic/" + quote(item["value"], safe="-._~")
                labels["entries"].append({"route": topic_route, "iri": BASE + "id/" + topic_route,
                    "label": item["value"], "language": "en-GB", "type": "Topic mention",
                    "label_authority": {"class": "editorial", "source": BASE + RULES}})
    labels["counts"]["entries"] = len(labels["entries"])
    put(f"{RUNTIME}/endpoint-labels.json.gz", labels)
    analysis = {"schema": "okf-analysis.v1", "snapshot": snapshot, "facet_analysis": []}
    for key, label in DIMENSIONS.items():
        count = len(records) - len(filters[key].get(UNKNOWN, []))
        sizes = [len(ids) for ids in filters[key].values()]
        total = sum(sizes)
        analysis["facet_analysis"].append({"key": key, "label": label, "coverage": count / len(records),
            "cardinality": len(sizes), "top_share": max(sizes) / len(records),
            "entropy": -sum((n / total) * math.log2(n / total) for n in sizes), "expected_reduction": 0,
            "recommended_control": "list", "recommendation": "suggested",
            "classification": {"basis": ["curated-reference" if key == "concept" else "explicit-mention"],
                               "review_status": "unreviewed", "classified_records": count, "total_records": len(records),
                               "limitations": [LIMITATIONS[2] if key == "concept" else LIMITATIONS[1], LIMITATIONS[3]]}})
    put(f"{RUNTIME}/analysis.json", analysis)
    manifest["chunks"]["datasets"], manifest["shards"]["datasets"] = record_paths, record_shards
    manifest["indexes"].update({"facets": f"{RUNTIME}/facets.json", "search": f"{RUNTIME}/search.json",
        "overview": f"{RUNTIME}/overview.json", "record_locator": bind(f"{RUNTIME}/locator.json"),
        "endpoint_labels": bind(f"{RUNTIME}/endpoint-labels.json.gz"), "analysis": f"{RUNTIME}/analysis.json"})
    put(f"{RUNTIME}/manifest.json", manifest)
    original["title"] = "DWP evidence review: conceptual navigation and full-source Ask OKF"
    original["description"] = "Independent experimental navigation. Benefit, circumstance and topic mentions are unreviewed discovery labels."
    for key, name in {"data_manifest": "manifest.json", "overview_index": "overview.json", "search_manifest": "search.json",
                      "record_locator": "locator.json", "endpoint_labels": "endpoint-labels.json.gz"}.items():
        binding = bind(f"{RUNTIME}/{name}")
        original["entrypoints"][key] = binding if key in {"record_locator", "endpoint_labels"} else binding["path"]
        original["entrypoint_integrity"][key] = binding
    original["entrypoints"]["concept_navigation"] = nav_binding
    original["entrypoint_integrity"]["concept_navigation"] = nav_binding
    original["extensions"] = {"okf-explorer-presentation.v1": {"schema": "okf-explorer-presentation.v1", "status": "experimental",
        "snapshot": snapshot, "defaults": {"facet_mode": "suggested"}, "facets": [
            {"key": key, "label": label, "description": ("Existing project-authored concept references; specialist review required."
              if key == "concept" else "Exact source-text mentions; navigation only, not legal applicability."),
             "order": index, "default_state": "pinned" if key != "concept" else "shown", "open_control": "list", "value_order": "count-desc"}
            for index, (key, label) in enumerate(DIMENSIONS.items())]}}
    original["plane_roots"]["data"] = digest(canonical(record_shards))
    original["plane_roots"]["search"] = digest(canonical(search_shards))
    original["plane_roots"]["presentation"] = digest(canonical(original["extensions"]))
    original["exploratory_publication"]["applicable_plane_roots"] = original["plane_roots"]
    original["exploratory_publication"]["limitations"] = LIMITATIONS + original["exploratory_publication"]["limitations"]
    outputs["full-dmg/okf-review-context.json"] = canonical(original)
    return {key: {"classified": len(records) - len(filters[key].get(UNKNOWN, [])), "total": len(records)} for key in DIMENSIONS}


def compile_navigation(root=ROOT):
    inputs, outputs = Inputs(root), {}
    rules_data, rules = load_rules(inputs)
    pages, documents = load_pages(inputs)
    semantic, nodes, assertions, _ = read_semantics(inputs)
    outputs["validation/navigation/ontology-use.json"] = pretty(ontology_inventory(inputs, semantic, nodes, assertions))
    assignments, concept_values = classify_pages(pages, rules, nodes, assertions)
    values = [{"id": row["@id"], "dimension": row["dimension"], "label": row["skos:prefLabel"]["@value"],
               "method": "explicit-mention", "review_status": "unreviewed"} for row in rules] + concept_values
    outputs[OUTPUT + "/catalogue.yamlld"] = inputs.read(RULES)
    shards = []
    for offset in range(0, len(assignments), 256):
        raw = canonical({"schema": "okf-concept-navigation-assignments.v1", "assignments": assignments[offset:offset + 256]})
        encoded = deterministic_gzip(raw)
        path = f"assignments/{offset // 256:04d}.json.gz"
        outputs[OUTPUT + "/" + path] = encoded
        shards.append({"path": path, "bytes": len(encoded), "sha256": digest(encoded), "decoded_bytes": len(raw),
                       "decoded_sha256": digest(raw), "records": min(256, len(assignments) - offset)})
    coverage = {}
    for family in ("dmg", "adm"):
        subset = [row for row in assignments if row["source_group"] == family]
        coverage[family] = {"pages": len(subset), "empty_extractions": sum(row["empty_extraction"] for row in subset),
                           "dimensions": {key: {"classified": sum(row["facets"][key] != [UNKNOWN] for row in subset),
                                                "unclassified": sum(row["facets"][key] == [UNKNOWN] for row in subset)} for key in DIMENSIONS}}
    manifest = {"schema": "okf-concept-navigation.v1", "source_snapshot": semantic["snapshot"],
                "classification_snapshot": "dwp-navigation-" + digest(canonical({"rules": rules_data, "shards": shards}))[:20],
                "dimensions": [{"key": key, "label": label} for key, label in DIMENSIONS.items()],
                "values": values, "assignments": shards, "coverage": coverage, "limitations": LIMITATIONS,
                "offset_encoding": "Unicode code point indices, zero-based start-inclusive/end-exclusive into exact frozen page text",
                "review_status": "unreviewed", "legal_applicability": "not-established"}
    raw = pretty(manifest)
    outputs[OUTPUT + "/manifest.json"] = raw
    reader = add_runtime(inputs, outputs, assignments, values, {"path": "context/navigation/manifest.json", "bytes": len(raw), "sha256": digest(raw)})
    inputs.read("scripts/build_review_navigation.py")
    receipt = {"schema": "okf-dwp-navigation-build.v1", "classification_snapshot": manifest["classification_snapshot"],
               "source_snapshot": semantic["snapshot"], "coverage": coverage, "reader_coverage": reader,
               "source_documents": len(documents), "rules": len(rules), "concept_values": len(concept_values),
               "inputs": list(sorted(inputs.files.values(), key=lambda row: row["path"])),
               "outputs": [{"path": path, "bytes": len(raw), "sha256": digest(raw)} for path, raw in sorted(outputs.items())]}
    outputs["validation/navigation/build.json"] = pretty(receipt)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = compile_navigation()
    for name, raw in outputs.items():
        path = ROOT / name
        if args.check:
            require(path.is_file() and path.read_bytes() == raw, "Stale conceptual navigation: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(json.dumps({"status": "verified" if args.check else "built", "files": len(outputs),
                      "coverage": json.loads(outputs["validation/navigation/build.json"])["coverage"]}))


if __name__ == "__main__":
    main()
