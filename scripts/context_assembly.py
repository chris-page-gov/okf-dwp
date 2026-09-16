"""Project an explicitly authored context profile from the governed bundle graph.

This producer does not inspect questions, rank evidence or create answer keys.
Source-page overlays reuse their existing identities and exact frozen text.
Context dependencies are compiled into the ordinary assertion graph first.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re

from build_bundle import BASE, REPO, OGL, canonical, digest, load_yaml, make_assertion

DCT = "http://purl.org/dc/terms/"
SKOS = "http://www.w3.org/2004/02/skos/core#"
ALLOWED = {DCT + "requires", DCT + "references", SKOS + "related"}
REVIEW = "unreviewed-specialist-review-required"


def require(test, message):
    if not test:
        raise ValueError(message)


def local(root: Path, path: str) -> Path:
    result = (root / path).resolve()
    require(result.is_relative_to(root.resolve()), "Context input escapes repository")
    return result


def pointer(document, value: str):
    require(value.startswith("/"), "Context metadata needs an absolute JSON pointer")
    for item in value[1:].split("/"):
        item = item.replace("~1", "/").replace("~0", "~")
        document = document[int(item)] if isinstance(document, list) else document[item]
    return document


def augment_context_graph(root: Path, nodes: dict, assertions: list, documents: list,
                          inventory_path: str = "source/full-dmg-2026-09-15/inventory.json") -> dict | None:
    """Validate explicit overlays and add source-backed context dependencies."""
    declarations, requirements, profiles, inputs = {}, [], [], set()
    for path in sorted((root / "knowledge/full-dmg").rglob("*.yamlld")):
        document = load_yaml(path)
        if "context_profile" in document:
            profiles.append(document["context_profile"])
        requirements.extend(deepcopy(document.get("context_requirements", [])))
        for row in document.get("@graph", []) + document.get("context_overlays", []):
            if "context_assembly" not in row:
                continue
            route = row["route"]
            require(route in nodes and route not in declarations, "Duplicate or unknown context route: " + route)
            declarations[route] = (deepcopy(row["context_assembly"]), path, digest(path.read_bytes()))
            nodes[route].pop("context_assembly", None)
    if not declarations:
        require(not profiles and not requirements, "Context profile has no records")
        return None
    require(len(profiles) == 1, "Exactly one versioned producer context profile is required")
    profile = profiles[0]
    require(profile.get("schema") == "okf-dwp-context-authoring.v1", "Unknown context authoring schema")
    require(profile.get("scope") and profile.get("limitations"), "Context scope and limitations are mandatory")
    require(isinstance(profile.get("authored_at"), str) and profile["authored_at"].endswith("Z"),
            "Context profile needs an explicit UTC authoring timestamp")
    by_hash = {d["sha256"]: d for d in documents}
    page_cache, records, evidence_by_route = {}, {}, {}

    def author_evidence(route, path, file_hash, field, value):
        literal = value if isinstance(value, str) else canonical(value).decode()
        identity = digest(canonical([path.relative_to(root).as_posix(), route, field, literal]))
        return {"@id": BASE + "id/evidence/context-authoring/" + identity,
                "type": "authored-context-profile", "url": REPO + "/blob/main/" + path.relative_to(root).as_posix(),
                "source_artifact": path.relative_to(root).as_posix(), "source_sha256": file_hash,
                "source_field": route + ".context_assembly." + field, "source_value": literal,
                "source_value_sha256": digest(literal.encode()), "locator": route,
                "retrieved_at": profile["authored_at"]}

    for route, (spec, path, file_hash) in sorted(declarations.items()):
        node = nodes[route]
        kind = spec.get("kind")
        require(kind in {"concept", "evidence", "scope"}, "Invalid context record kind")
        require(bool(spec.get("scope")), "Context record scope required")
        aliases = spec.get("aliases", [])
        require(kind == "concept" or not aliases, "Only concepts may resolve query aliases")
        for alias in aliases:
            require(isinstance(alias, str) and bool(alias.strip()) or isinstance(alias, dict)
                    and set(alias) == {"label", "case_sensitive"} and isinstance(alias["label"], str)
                    and bool(alias["label"].strip()) and isinstance(alias["case_sensitive"], bool), "Malformed context alias")
        provenance, evidence = [], []
        status = "model-derived"
        authority = {"class": "model-assisted", "label": "Authored research context; specialist review required", "source": REPO}
        if spec.get("source_page"):
            require(kind == "evidence" and node.get("type") == "Source PDF page", "Page evidence must reuse a source-page identity")
            require(spec["source_page"] == route, "Page overlay cannot change its evidence identity")
            doc = by_hash[node["source_sha256"]]
            if doc["id"] not in page_cache:
                raw = local(root, doc["pages_path"]).read_bytes()
                require(digest(raw) == doc["pages_sha256"], "Context extraction hash differs")
                require(digest(local(root, doc["pdf_path"]).read_bytes()) == doc["sha256"], "Context PDF hash differs")
                page_cache[doc["id"]] = json.loads(raw)
            page = page_cache[doc["id"]]["pages"][node["page_number"] - 1]
            text = page["text"]
            require(bool(text.strip()), "Empty extraction cannot serve as mandatory context evidence")
            require(page["url"] == node["source"], "Context page URL differs")
            locator = spec.get("locator", "")
            require(f"PDF page {page['page']}" in locator, "Context locator must retain its PDF page")
            for label in spec.get("paragraphs", []):
                require(re.fullmatch(r"\d{5,6}", label) and re.search(rf"(?m)^\s*{label}\b", text), "Context paragraph absent from its exact page")
            literal_hash = digest(text.encode())
            provenance = [{"url": page["url"], "source_sha256": doc["sha256"], "locator": locator,
                           "captured_at": doc["observed_at"], "literal_sha256": literal_hash},
                          {"url": REPO + "/blob/main/" + doc["pages_path"], "source_sha256": doc["pages_sha256"],
                           "locator": f"pages[{page['page'] - 1}].text", "captured_at": doc["observed_at"], "literal_sha256": literal_hash}]
            evidence = [{"@id": BASE + "id/evidence/context-page/" + digest(canonical([route, doc["pages_sha256"], literal_hash])),
                         "type": "source-page-for-context", "url": page["url"], "source_artifact": doc["pages_path"],
                         "source_sha256": doc["pages_sha256"], "source_pdf_artifact": doc["pdf_path"],
                         "source_pdf_sha256": doc["sha256"], "source_page_route": route,
                         "source_field": f"pages[{page['page'] - 1}].text", "source_value": text,
                         "source_value_sha256": literal_hash, "locator": locator, "retrieved_at": doc["observed_at"]}]
            status = "normalized"
            authority = {"class": "derived", "label": "Exact frozen machine extraction of official DWP guidance; applicability unreviewed", "source": doc["url"]}
        elif spec.get("source_document"):
            require(kind == "scope" and node.get("source_sha256") in by_hash,
                    "Document context must reuse a frozen source identity")
            doc = by_hash[node["source_sha256"]]
            require(doc["id"] == spec["source_document"] and node["source"] == doc["url"],
                    "Document context identity differs")
            require(digest(local(root, doc["pdf_path"]).read_bytes()) == doc["sha256"], "Context PDF hash differs")
            text = doc["title"]
            inventory_raw = local(root, inventory_path).read_bytes()
            inventoried = json.loads(inventory_raw)["documents"]
            position = next((i for i, row in enumerate(inventoried) if row["id"] == doc["id"]), None)
            require(position is not None and inventoried[position] == doc, "Chapter metadata differs from the frozen inventory")
            provenance = [{"url": doc["url"], "source_sha256": doc["sha256"],
                           "locator": "Frozen document identity; chapter metadata, not passage evidence",
                           "captured_at": doc["observed_at"]},
                          {"url": REPO + "/blob/main/" + inventory_path, "source_sha256": digest(inventory_raw),
                           "locator": f"/documents/{position}/title", "captured_at": doc["observed_at"],
                           "literal_sha256": digest(text.encode())}]
            status = "normalized"
            authority = {"class": "derived", "label": "Frozen DWP document identity; not a selected legal conclusion", "source": doc["url"]}
        elif spec.get("metadata_source"):
            require(kind == "evidence", "Metadata evidence must be labelled evidence")
            source = spec["metadata_source"]
            raw = local(root, source["path"]).read_bytes()
            require(digest(raw) == source["sha256"], "Context metadata source hash differs")
            text = pointer(json.loads(raw), source["pointer"])
            require(isinstance(text, str) and text == spec["text"], "Context metadata quotation differs")
            capture = json.loads(local(root, source["capture_path"]).read_bytes())
            captured_at = capture[source["capture_field"]]
            inputs.update([source["path"], source["capture_path"]])
            provenance = [{"url": source["url"], "source_sha256": source["sha256"], "locator": source["pointer"],
                           "captured_at": captured_at, "literal_sha256": digest(text.encode())}]
            if source.get("source_date_pointer"):
                provenance[0].update(source_date=pointer(json.loads(raw), source["source_date_pointer"]),
                                     source_date_kind="catalogue change-history event; not inferred legal commencement")
            evidence = [{"@id": BASE + "id/evidence/context-metadata/" + digest(canonical([source["path"], source["sha256"], source["pointer"]])),
                         "type": "frozen-publication-metadata", "url": source["url"], "source_artifact": source["path"],
                         "source_sha256": source["sha256"], "source_field": source["pointer"], "source_value": text,
                         "source_value_sha256": digest(text.encode()), "locator": source["pointer"], "retrieved_at": captured_at}]
            status = "normalized"
            authority = {"class": "derived", "label": "Exact field from frozen official GOV.UK catalogue metadata", "source": source["url"]}
        else:
            text = spec.get("text", "")
            require(kind != "evidence" and bool(text.strip()), "Authored context text required; evidence must bind a source")
            evidence = [author_evidence(route, path, file_hash, "text", text)]
            provenance = [{"url": evidence[0]["url"], "source_sha256": file_hash, "locator": evidence[0]["source_field"],
                           "captured_at": evidence[0]["retrieved_at"], "literal_sha256": digest(text.encode())}]
        evidence_by_route[route] = evidence
        records[route] = {"id": node["@id"], "route": route, "label": node["title"], "kind": kind,
                          "text": text, "assertion_status": status, "authority": authority, "scope": spec["scope"],
                          "provenance": provenance, "rights": OGL if kind == "evidence" else REPO + "/blob/main/NOTICE.md",
                          "access": "public", "review_status": REVIEW}
        if aliases:
            records[route]["aliases"] = aliases

    for route, (spec, path, file_hash) in sorted(declarations.items()):
        node = nodes[route]
        for relation in spec.get("relations", []):
            target_route, predicate = relation.get("target"), relation.get("predicate")
            require(target_route in declarations and target_route != route and predicate in ALLOWED, "Invalid context dependency endpoint/predicate")
            require(bool(relation.get("rationale")), "Context dependency needs an authored rationale")
            support = relation.get("evidence", [])
            require(bool(support) and all(r in evidence_by_route and records[r]["kind"] == "evidence" for r in support), "Dependency needs source-evidence routes")
            support_evidence = [deepcopy(e) for r in support for e in evidence_by_route[r]]
            authored = author_evidence(route, path, file_hash, "relations", relation)
            labels = {DCT + "requires": ("requires context", "is required context for"),
                      DCT + "references": ("references source context", "is referenced as source context by"),
                      SKOS + "related": ("has related concept", "has related concept")}
            require(predicate != SKOS + "related" or records[route]["kind"] == records[target_route]["kind"] == "concept", "SKOS related requires concept endpoints")
            edge = make_assertion(node, nodes[target_route], predicate, *labels[predicate], authored["retrieved_at"], authored, True)
            existing = next((a for a in assertions if a["@id"] == edge["@id"]), None)
            require(existing is None, "Context edge duplicates an existing assertion; declare the existing edge only once")
            edge.update(kind="authored context requirement" if predicate == DCT + "requires" else "source-backed context association",
                        assertion_status="model-derived", review_status=REVIEW, confidence_score=0.5,
                        authority={"class": "model-assisted", "label": "Authored context dependency, not a legal implication", "source": REPO},
                        derivation=BASE + "rules/explicit-context-dependency-v1",
                        derivation_activity=BASE + "id/activity/imprisonment-context-authoring", context_scope=spec["scope"],
                        context_rationale=relation["rationale"], evidence=[authored] + support_evidence,
                        rights={"source": OGL, "assertion": "Original context selection; source text remains OGL"})
            if relation.get("literal_chapter_route"):
                routing = relation["literal_chapter_route"]
                chapter = by_hash.get(nodes[target_route].get("source_sha256"), {}).get("chapter")
                quote = routing.get("quote", "")
                require(predicate == DCT + "references" and spec.get("source_page") == route
                        and declarations[target_route][0].get("source_document")
                        and quote in records[route]["text"] and len(quote) >= 40
                        and re.search(rf"\bDMG\s+Chapter\s+{chapter}\b", quote),
                        "Literal chapter routing needs an exact source passage naming the target chapter")
                edge.update(kind="normalised literal chapter routing", assertion_status="normalized",
                            authority={"class": "derived", "label": "Literal source chapter reference resolved to its frozen document identity", "source": nodes[route]["source"]},
                            derivation=BASE + "rules/literal-chapter-routing-v1")
                edge.pop("confidence_score")
                edge.pop("derivation_activity")
            assertions.append(edge)
            node.setdefault(predicate, []).append({"@id": nodes[target_route]["@id"]})

    ids = {r["id"] for r in records.values()}
    edges_by_id = {edge["@id"]: edge for edge in assertions}
    seen = set()
    for requirement in requirements:
        require(requirement["id"].startswith(BASE + "id/") and requirement["id"] not in seen, "Invalid context requirement identity")
        seen.add(requirement["id"])
        require(requirement.get("scope") and requirement.get("label"), "Context requirement needs a scope and label")
        require(requirement.get("when_all") and requirement.get("required"), "Context requirement must declare concepts and evidence")
        require(set(requirement["when_all"]) <= ids and set(requirement["required"]) <= ids, "Context requirement references unknown records")
        covered = requirement.get("covers", requirement["when_all"])
        require(isinstance(covered, list) and set(requirement["when_all"]) <= set(covered) <= ids,
                "Context coverage must retain its triggers and reference known concepts")
        require(all(records[next(r for r in records if records[r]["id"] == i)]["kind"] == "concept" for i in covered), "Requirement conditions and coverage must be concepts")
        for path in requirement.get("required_paths", []):
            path_records, path_edges = path.get("records", []), path.get("assertions", [])
            require(path_edges and len(path_records) == len(path_edges) + 1
                    and path.get("seed") == path_records[0] and set(path_records) <= ids,
                    "Required context path has invalid shape or records")
            for i, edge_id in enumerate(path_edges):
                edge = edges_by_id.get(edge_id, {})
                require(edge.get("source") == path_records[i] and edge.get("target") == path_records[i + 1]
                        and edge.get("predicate") in ALLOWED, "Required path does not follow an actual directed context assertion")
    return {"profile": profile, "records": records, "requirements": requirements, "inputs": sorted(inputs)}


def project_context_index(plan: dict, assertions: list, snapshot: str) -> dict:
    """Project existing directed assertions only; requirements never seed retrieval."""
    records = plan["records"]
    ids = {r["id"] for r in records.values()}
    edges = []
    for edge in assertions:
        if edge["source"] not in ids or edge["target"] not in ids or edge["predicate"] not in ALLOWED:
            continue
        provenance = [{"url": e["url"], "source_sha256": e["source_sha256"], "locator": e["locator"],
                       "captured_at": e["retrieved_at"], "literal_sha256": e["source_value_sha256"]} for e in edge["evidence"]]
        edges.append({"id": edge["@id"], "source": edge["source"], "target": edge["target"], "predicate": edge["predicate"],
                      "label": edge["label"], "assertion_status": edge["assertion_status"], "authority": edge["authority"],
                      "scope": edge.get("context_scope", "Source routing only; no legal implication or identity inference"),
                      "provenance": provenance, "original_assertion_id": edge["@id"]})
    return {"schema": "okf-context-index.v1", "bundle": {"id": BASE + "id/bundle/full-dmg", "snapshot": snapshot,
             "source_url": REPO}, "scope": plan["profile"]["scope"], "limitations": plan["profile"]["limitations"],
            "records": sorted(records.values(), key=lambda r: r["id"]), "assertions": sorted(edges, key=lambda a: a["id"]),
            "requirements": sorted(plan["requirements"], key=lambda r: r["id"])}
