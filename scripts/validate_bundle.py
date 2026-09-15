#!/usr/bin/env python3
"""Validate every source, page and semantic assertion in the local snapshot."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker
from pyld import jsonld

from build_bundle import ROOT, PROFILE, REPO, CURRENT_CHAPTERS, ROUTE, canonical, digest, load_yaml, pinned_loader


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="Write a validation receipt outside the generated bundle")
    args = parser.parse_args()
    errors: list[str] = []
    checks: dict[str, object] = {}
    inventory = json.loads((ROOT / "source/inventory.json").read_text())
    bundle = json.loads((ROOT / "bundle/okf-bundle.json").read_text())
    graph = load_yaml(ROOT / "bundle/okf-bundle.yamlld")
    json_graph = json.loads((ROOT / "bundle/okf-bundle.jsonld").read_text())
    require(graph == json_graph, "YAML-LD and JSON-LD data models differ")
    checks["yaml_json_data_equivalence"] = "passed"
    lock = json.loads((ROOT / "profiles/bundle-wiki/v1.vendor-lock.json").read_text())
    for row in lock["files"]:
        data = (ROOT / "profiles/bundle-wiki/v1" / row["path"]).read_bytes()
        require(len(data) == row["bytes"] and digest(data) == row["sha256"], f"Profile bytes differ: {row['path']}")
    require(len(lock["files"]) == 16, "Expected all 16 pinned canonical profile files")
    checks["canonical_profile_vendor_lock"] = "passed"
    bundle_schema = json.loads((ROOT / "profiles/bundle-wiki/v1/bundle.schema.json").read_text())
    assertion_schema = json.loads((ROOT / "profiles/bundle-wiki/v1/semantic-assertion.schema.json").read_text())
    bundle_validator = Draft202012Validator(bundle_schema, format_checker=FormatChecker())
    assertion_validator = Draft202012Validator(assertion_schema, format_checker=FormatChecker())
    errors.extend(f"bundle descriptor: {err.message}" for err in bundle_validator.iter_errors(graph))
    assertions = [row for row in graph["@graph"] if "predicate" in row and "target" in row]
    entities = [row for row in graph["@graph"] if row not in assertions]
    iris = {row["@id"]: row for row in entities}
    require(len(iris) == len(entities), "Duplicate semantic entity IRI")
    require(len({row["@id"] for row in assertions}) == len(assertions), "Duplicate assertion IRI")
    require(len({row["route"] for row in entities}) == len(entities), "Duplicate entity route")
    publication_time = datetime.fromisoformat(bundle["generated_at"].replace("Z", "+00:00"))
    for row in entities:
        for value in (row.get("observedAt"), row.get("generated", {}).get("at")):
            if value:
                require(publication_time >= datetime.fromisoformat(str(value).replace("Z", "+00:00")),
                        f"Publication predates an input observation: {row['route']}")
    require(bundle["exploratory_publication"]["generated_at"] == bundle["generated_at"], "Publication timestamps disagree")
    checks["publication_timestamp_covers_inputs"] = {"status": "passed", "generated_at": bundle["generated_at"]}
    cpag = bundle["nodes"].get("resource/cpag-welfare-benefits-handbook")
    date_receipt_path = ROOT / "docs/evidence/cpag-publication-date-review.json"
    if cpag and date_receipt_path.is_file():
        dates = json.loads(date_receipt_path.read_text())
        require(digest(date_receipt_path.read_bytes()) == cpag["okf:publicationMetadataReceiptSha256"],
                "CPAG publication metadata receipt hash mismatch")
        require(cpag["schema:about"]["schema:datePublished"] == {"@value": dates["release_month"], "@type": "xsd:gYearMonth"},
                "CPAG publication precision or source date differs from publisher evidence")
        require(cpag["generated"]["at"].startswith("2026-09-15"), "Original CPAG reference authoring date was replaced")
        capture_receipt = json.loads((ROOT / "docs/evidence/cpag-access-review.json").read_text())
        require(cpag["captured_at"] == capture_receipt["observed_at"], "Original CPAG metadata capture date was replaced")
        require(cpag["observedAt"] == dates["observed_at"], "CPAG publication metadata review date differs from its receipt")
        checks["cpag_source_publication_separate_from_capture"] = "passed"
    for row in entities:
        require(bool(ROUTE.fullmatch(row["route"])), f"Unsafe route {row['route']}")
        require(bool(row.get("title", "").strip()), f"Missing human-readable label: {row['route']}")
        require(bool(row.get("type", "").strip()), f"Missing OKF core type: {row['route']}")
        require(row["route"] in bundle["nodes"], f"Entity missing from runtime: {row['route']}")
    for row in assertions:
        errors.extend(f"{row['@id']}: {err.message}" for err in assertion_validator.iter_errors(row))
        require(row["source"] in iris and row["target"] in iris, f"Unresolved assertion endpoint {row['@id']}")
        require(row["source_route"] == iris[row["source"]]["route"], "Source route disagrees with IRI")
        require(row["target_route"] == iris[row["target"]]["route"], "Target route disagrees with IRI")
        source = iris[row["source"]]
        rights_source = row["rights"]["source"]
        local_rights_prefix = REPO + "/blob/main/"
        if rights_source.startswith(local_rights_prefix):
            require((ROOT / rights_source.removeprefix(local_rights_prefix)).is_file(), f"Missing project rights document: {rights_source}")
        term = row["predicate"].replace("http://purl.org/dc/terms/", "dcterms:")
        values = source.get(term, [])
        values = values if isinstance(values, list) else [values]
        require({"@id": row["target"]} in values, f"Missing synchronised direct triple: {row['@id']}")
        for evidence in row["evidence"]:
            if evidence.get("source_artifact"):
                evidence_path = ROOT / evidence["source_artifact"]
                require(evidence_path.is_relative_to(ROOT), "Unsafe evidence source path")
                require(evidence_path.is_file(), f"Missing evidence artefact {evidence_path}")
                require(digest(evidence_path.read_bytes()) == evidence["source_sha256"], f"Evidence hash mismatch: {evidence_path}")
            require(digest(str(evidence["source_value"]).encode()) == evidence["source_value_sha256"], "Evidence source-value hash mismatch")
            if evidence.get("type") == "source-passage-for-model-proposal":
                page = bundle["nodes"][evidence["source_page_route"]]
                require(evidence["source_value"] in page["body"], "Semantic quotation is absent from the cited page")
                page_doc = json.loads((ROOT / evidence["source_artifact"]).read_text())
                require(evidence["source_value"] in page_doc["pages"][page["page_number"] - 1]["text"],
                        "Semantic quotation is absent from the frozen extraction")
                require(digest((ROOT / evidence["source_pdf_artifact"]).read_bytes()) == evidence["source_pdf_sha256"],
                        "Semantic passage PDF hash mismatch")
                require(page["source_sha256"] == evidence["source_pdf_sha256"], "Semantic page and PDF identities disagree")
        if row["assertion_status"] == "model-derived":
            from semantic_authoring import PREDICATES
            require(row["predicate"] in PREDICATES, "Unregistered model-derived predicate")
            require(row["review_status"] == "unreviewed-specialist-review-required", "Pilot review state changed without review")
            require(any(e.get("type") == "source-passage-for-model-proposal" for e in row["evidence"]), "Missing semantic source passage")
    checks["all_semantic_assertions"] = {"status": "passed" if not errors else "failed", "count": len(assertions), "schema": assertion_schema["$id"]}
    require(len(bundle["relationships"]) == len(assertions), "Semantic/runtime relationship count mismatch")
    runtime_assertions = {row["id"]: row for row in bundle["relationships"]}
    for row in assertions:
        runtime = runtime_assertions[row["@id"]]
        require(runtime["source_iri"] == row["source"] and runtime["target_iri"] == row["target"], "Runtime assertion IRI mismatch")
    pages_checked = 0
    for doc in inventory["documents"]:
        require(digest((ROOT / doc["pdf_path"]).read_bytes()) == doc["sha256"], f"PDF hash mismatch: {doc['id']}")
        require(digest((ROOT / doc["text_path"]).read_bytes()) == doc["text_sha256"], f"Extracted-text hash mismatch: {doc['id']}")
        page_doc = json.loads((ROOT / doc["pages_path"]).read_text())
        require(page_doc["source_sha256"] == doc["sha256"], f"Page source hash mismatch: {doc['id']}")
        pages = page_doc["pages"]
        require(len(pages) == doc["pages"], f"Page count mismatch: {doc['id']}")
        require([row["page"] for row in pages] == list(range(1, len(pages) + 1)), f"Page sequence broken: {doc['id']}")
        if doc.get("role") != "substantive" or int(doc.get("chapter") or 0) not in CURRENT_CHAPTERS:
            continue
        for page in pages:
            route = f"page/{int(doc['chapter'])}/{page['page']:04d}"
            runtime = bundle["nodes"][route]
            require(page["text"] in runtime["body"], f"Incomplete source page body: {route}")
            require(runtime["text_sha256"] == digest(page["text"].encode()), f"Source page text hash mismatch: {route}")
            require(runtime["source"] == page["url"], f"Source PDF page link mismatch: {route}")
            pages_checked += 1
    require(pages_checked == bundle["coverage"]["searchable_pdf_pages"], "Page coverage denominator mismatch")
    checks["source_pdf_hashes_and_page_coverage"] = {"status": "passed", "source_documents": len(inventory["documents"]), "searchable_pdf_pages": pages_checked}
    rdf = jsonld.normalize(graph, options={"algorithm": "URDNA2015", "format": "application/n-quads", "documentLoader": pinned_loader})
    require(rdf.encode() == (ROOT / "bundle/okf-bundle.nq").read_bytes(), "Canonical RDF dataset differs")
    require(digest(rdf.encode()) == bundle["plane_roots"]["semantic"], "Semantic digest differs")
    checks["canonical_rdf_identity"] = {"status": "passed", "algorithm": "URDNA2015", "sha256": digest(rdf.encode()), "statements": len(rdf.splitlines())}
    for row in assertions:
        triple = f'<{row["source"]}> <{row["predicate"]}> <{row["target"]}>'
        require(any(line.startswith(triple + " ") for line in rdf.splitlines()),
                f"Relationship lost or changed in RDF expansion: {row['@id']}")
    checks["assertion_direct_triples_survive_rdf_expansion"] = "passed"
    manifest = json.loads((ROOT / "bundle/checksums.json").read_text())
    for entry in manifest["files"]:
        data = (ROOT / entry["path"]).read_bytes()
        require(len(data) == entry["bytes"] and digest(data) == entry["sha256"], f"Generated checksum mismatch: {entry['path']}")
    checks["generated_checksums"] = {"status": "passed", "files": len(manifest["files"])}
    # Negative controls test the same canonical schema used on every assertion.
    bad = deepcopy(assertions[0])
    bad.pop("evidence")
    require(not assertion_validator.is_valid(bad), "Missing-evidence negative control incorrectly accepted")
    bad = deepcopy(assertions[0])
    bad["authority"]["class"] = "official"
    require(not assertion_validator.is_valid(bad), "Contradictory-authority negative control incorrectly accepted")
    try:
        pinned_loader("https://untrusted.invalid/context.jsonld")
    except ValueError:
        pass
    else:
        raise ValueError("Unpinned remote context negative control incorrectly accepted")
    checks["negative_controls"] = {"status": "passed", "cases": ["missing assertion evidence", "contradictory assertion authority", "unpinned remote context"]}
    receipt = {"schema": "okf-dwp-validation.v1", "status": "passed" if not errors else "failed", "snapshot_id": bundle["snapshot_id"],
        "checks": checks, "errors": errors, "not_claimed": ["Specialist legal or pensions review", "Full Foundry production gate completion", "SHACL conformance", "RDF Dataset Canonicalization 1.0 (RDFC-1.0); the applied algorithm is URDNA2015", "Browser acceptance; recorded separately"]}
    if args.output:
        destination = args.output.resolve()
        require(not destination.is_relative_to(ROOT / "bundle"), "Validation receipt must be outside generated bundle")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(canonical(receipt))
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
