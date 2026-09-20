#!/usr/bin/env python3
"""Bounded, explicit public metadata acquisition; never called by offline checks.

Only metadata selected by the parsers is retained. Full legislative and judicial
bodies are not published here. Each receipt binds the response bytes received.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "source/legal-discovery-2026-09-20"
DATE = "2026-09-20"
MAX_BYTES = 8 * 1024 * 1024
MAX_CASES_PER_QUERY = 3
OGL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
NS = {"l": "http://www.legislation.gov.uk/namespaces/legislation",
      "m": "http://www.legislation.gov.uk/namespaces/metadata",
      "dc": "http://purl.org/dc/elements/1.1/"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pretty(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def public_effect_projection(attributes: dict, ordinal: int) -> dict:
    """Omit unused opaque source IDs; preserve identity digests and XML position.

    These are public legislation identifiers, not credentials. Their literal
    shape triggers credential scanners, and the consumers need no opaque ID.
    This is an explicit lossy metadata projection, never a reversible encoding.
    """
    projected = {k:v for k,v in attributes.items() if k not in {"EffectId", "URI"}}
    for field, key in [("EffectId", "effect_identifier_sha256"),("URI", "effect_uri_sha256")]:
        if field in attributes:
            projected[key] = sha(attributes[field].encode())
    projected["source_xml_effect_ordinal"] = ordinal
    return projected


def fetch(url: str) -> tuple[bytes | None, dict]:
    allowed = {"www.legislation.gov.uk", "www.gov.uk"}
    if urllib.parse.urlparse(url).hostname not in allowed:
        raise ValueError("Only declared official metadata hosts are allowed")
    receipt = {"requested_url": url, "observed_at": datetime.now(timezone.utc).isoformat(),
               "response_body_retained": False, "max_response_bytes": MAX_BYTES}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={
                "User-Agent": "OKF-DWP independent legal metadata research"}), timeout=45) as response:
            if urllib.parse.urlparse(response.url).hostname not in allowed:
                raise ValueError("Unexpected redirect host")
            data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise ValueError("Response exceeded declared byte budget")
            receipt.update({"resolved_url": response.url, "http_status": response.status,
                            "content_type": response.headers.get("Content-Type"),
                            "response_bytes": len(data), "response_sha256": sha(data)})
            return data, receipt
    except Exception as error:
        receipt.update({"status": "failed", "error": type(error).__name__ + ": " + str(error)})
        return None, receipt


def legislative_metadata(data: bytes, target: str) -> dict:
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValueError("XML entities and DTDs are not accepted")
    root = ET.fromstring(data)
    target_id = "http://www.legislation.gov.uk/id/" + target
    selected = next((e for e in root.iter() if e.get("IdURI") == target_id), None)
    parents = {child: parent for parent in root.iter() for child in parent}
    ancestors = []
    cursor = selected
    while cursor is not None:
        attrs = {k: v for k, v in cursor.attrib.items() if k in {
            "IdURI", "DocumentURI", "RestrictExtent", "RestrictStartDate", "RestrictEndDate", "Status"}}
        if attrs:
            ancestors.append({"element": cursor.tag.rsplit("}", 1)[-1], "attributes": attrs})
        cursor = parents.get(cursor)
    metadata = root.find("m:Metadata", NS)
    dates = []
    if metadata is not None:
        for item in metadata.iter():
            name = item.tag.rsplit("}", 1)[-1]
            if name in {"Made", "Laid", "DateTime", "EnactmentDate", "DocumentStatus", "Year", "Number", "Extent"}:
                dates.append({"element": name, "attributes": dict(item.attrib),
                              "text": (item.text or "").strip() or None})
    changes = [dict(e.attrib) for e in root.iter() if e.tag.rsplit("}", 1)[-1] in {"UnappliedEffect", "Effect"}]
    citation_uris = sorted({e.get("URI") for e in root.iter() if e.tag.rsplit("}", 1)[-1] == "Citation" and e.get("URI")})
    return {"title": root.findtext("m:Metadata/dc:title", namespaces=NS),
            "document_identifier": root.findtext("m:Metadata/dc:identifier", namespaces=NS),
            "work_attributes": {k: v for k, v in root.attrib.items() if k in {
                "IdURI", "DocumentURI", "RestrictStartDate", "RestrictEndDate", "RestrictExtent"}},
            "target_identifier_observed": selected is not None,
            "target_attributes": dict(selected.attrib) if selected is not None else None,
            "target_and_ancestor_restrictions": ancestors,
            "instrument_metadata": dates,
            "effect_elements_observed": len(changes),
            "effect_metadata": [public_effect_projection(e,n) for n,e in enumerate(changes[:100],1)],
            "effect_identifier_policy": "lossy-public-projection; opaque EffectId and associated effect URI omitted; SHA-256 digests and one-based Effect/UnappliedEffect XML-order positions retained",
            "effect_metadata_truncated": len(changes) > 100,
            "source_citation_uris": citation_uris[:200],
            "source_citation_uris_truncated": len(citation_uris) > 200,
            "extent_assessment": "observed-attributes-only; absence-is-unknown",
            "commencement_assessment": "instrument-dates-only; provision-commencement-not-reconciled",
            "effects_assessment": "XML-observation-only; absence-is-not-a-complete-effects-census"}


def acquire_provision(item: dict) -> tuple[str, dict]:
    target = item["target"]
    url = f"https://www.legislation.gov.uk/{target}/{DATE}/data.xml"
    data, receipt = fetch(url)
    result = {"schema": "okf-legal-source-observation.v1", "kind": "legislation-provision-metadata",
              "target": target, "requested_version_date": DATE, "receipt": receipt,
              "authority": "official-legislation-publication", "applicability_review": "unreviewed",
              "rights": {"reference": "https://www.legislation.gov.uk/information/copyright",
                         "licence": OGL, "scope": "selected-public-metadata-only; source-exceptions-preserved"}}
    if data is not None:
        try:
            result["metadata"] = legislative_metadata(data, target)
            result["status"] = "identifier-verified" if result["metadata"]["target_identifier_observed"] else "identifier-not-observed"
        except (ET.ParseError, ValueError) as error:
            result.update({"status": "parse-failed", "error": str(error)})
    else:
        result["status"] = "fetch-failed"
    return target.replace("/", "--") + ".json", result


def decision_metadata(data: bytes) -> dict:
    source = json.loads(data)
    details = source.get("details", {})
    meta = details.get("metadata", {})
    return {"content_id": source.get("content_id"), "title": source.get("title"),
            "description": source.get("description"), "base_path": source.get("base_path"),
            "document_type": source.get("document_type"),
            "first_published_at": source.get("first_published_at"),
            "public_updated_at": source.get("public_updated_at"),
            "withdrawn_notice": source.get("withdrawn_notice"),
            "decision_date": meta.get("tribunal_decision_decision_date"),
            "judges": meta.get("tribunal_decision_judges", []),
            "categories": meta.get("tribunal_decision_categories", []),
            "sub_categories": meta.get("tribunal_decision_sub_categories", []),
            "attachments": [{k: a.get(k) for k in ("title", "url", "content_type", "content_id")}
                            for a in details.get("attachments", [])],
            "authority": "HM Courts & Tribunals Service publication of Upper Tribunal Administrative Appeals Chamber decision metadata",
            "jurisdiction": "Upper Tribunal (Administrative Appeals Chamber); case-specific territorial scope unreviewed",
            "applicability_review": "not-assessed; query-match-is-not-applicability",
            "rights": {"licence": OGL, "scope": "GOV.UK catalogue metadata with exceptions; judgment-body rights not assessed; bodies not acquired"}}


def acquire_queries(queries: list[dict]) -> tuple[list[dict], dict[str, dict]]:
    outputs, decisions = [], {}
    for query in queries:
        params = {"filter_content_store_document_type": "utaac_decision", "q": query["query"],
                  "count": MAX_CASES_PER_QUERY, "start": 0}
        url = "https://www.gov.uk/api/search.json?" + urllib.parse.urlencode(params)
        data, receipt = fetch(url)
        row = {**query, "receipt": receipt, "requested_count": MAX_CASES_PER_QUERY,
               "start": 0, "ranking": "official-API-default-relevance", "decision_ids": []}
        if data is None:
            row.update({"status": "fetch-failed", "total_matching_results": None, "truncated": None})
            outputs.append(row)
            continue
        raw = json.loads(data)
        row.update({"status": "observed", "total_matching_results": raw.get("total"),
                    "returned_count": len(raw.get("results", [])),
                    "truncated": raw.get("total", 0) > len(raw.get("results", []))})
        for match in raw.get("results", []):
            route = match["link"]
            if not route.startswith("/administrative-appeals-tribunal-decisions/"):
                raise ValueError("Unexpected decision route")
            key = route.rsplit("/", 1)[-1]
            row["decision_ids"].append(key)
            if key not in decisions:
                body, observation = fetch("https://www.gov.uk/api/content" + route)
                decisions[key] = {"schema": "okf-legal-source-observation.v1", "kind": "tribunal-decision-metadata",
                                  "receipt": observation, "status": "observed" if body else "fetch-failed"}
                if body:
                    decisions[key]["metadata"] = decision_metadata(body)
        outputs.append(row)
    return outputs, decisions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acquire", action="store_true", help="Explicitly acquire this dated metadata snapshot once")
    args = parser.parse_args()
    if not args.acquire:
        parser.error("Network acquisition requires --acquire; offline checks never call this command")
    if (DEST / "manifest.json").exists():
        parser.error("Dated metadata already exists; retain it and create a separately named refresh")
    config = json.loads((ROOT / "domain-profile/legal-reconciliation/seeds.json").read_text())
    files = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for name, row in pool.map(acquire_provision, config["provisions"]):
            files["legislation/" + name] = pretty(row)
    queries, decisions = acquire_queries(config["tribunal_queries"])
    files["queries.json"] = pretty({"schema": "okf-tribunal-query-census.v1", "queries": queries,
                                    "scope": "bounded-discovery; not-complete-tribunal-corpus",
                                    "judgment_bodies_acquired": 0})
    for name, row in decisions.items():
        files["tribunal/" + name + ".json"] = pretty(row)
    manifest = {"schema": "okf-legal-discovery-manifest.v1", "observed_on": DATE,
                "seed_sha256": sha((ROOT / "domain-profile/legal-reconciliation/seeds.json").read_bytes()),
                "source_body_policy": "metadata-only; response hashes retained; no full legislative or judicial text persisted",
                "acquisition_method": "scripts/acquire_legal_reconciliation.py --acquire",
                "files": [{"path": path, "bytes": len(body), "sha256": sha(body)} for path, body in sorted(files.items())]}
    for name, body in files.items():
        path = DEST / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    (DEST / "manifest.json").write_bytes(pretty(manifest))
    print(json.dumps({"metadata_files": len(files), "provisions": len(config["provisions"]),
                      "queries": len(queries), "decisions": len(decisions)}))


if __name__ == "__main__":
    main()
