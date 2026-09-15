"""Compile a deliberately small, evidence-bound semantic proposal vocabulary."""
from hashlib import sha256
import json
import re

NS = "https://chris-page-gov.github.io/okf-dwp/ns#"
SKOS = "http://www.w3.org/2004/02/skos/core#"
PREDICATES = {
    SKOS + "related": ("related concept", "has related concept", "has related concept"),
    NS + "hasEvidenceRequirement": ("evidence requirement", "has evidence requirement", "is evidence requirement for"),
    NS + "hasDisregardPeriod": ("disregard period", "has disregard period", "is disregard period for"),
    NS + "precedesAssessmentOf": ("guidance sequence", "precedes assessment of", "is assessed after"),
}


def digest(data):
    return sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def check_relation(spec, source, nodes):
    """Fail closed on unknown predicates, endpoints and unsupported evidence."""
    if spec.get("predicate") not in PREDICATES:
        raise ValueError("Unregistered semantic predicate")
    target = nodes.get(spec.get("target"))
    if target is None or source.get("type") != "Concept" or target.get("type") != "Concept":
        raise ValueError("Semantic pilot endpoints must be existing concepts")
    if source["route"] == target["route"]:
        raise ValueError("Self relationships are not allowed in this pilot")
    if not spec.get("rationale", "").strip() or not spec.get("evidence"):
        raise ValueError("Semantic proposal needs a rationale and source evidence")
    for item in spec["evidence"]:
        page = nodes.get(item.get("page"))
        quote = item.get("quote", "")
        if not page or page.get("type") != "Source PDF page" or len(quote.strip()) < 20:
            raise ValueError("Semantic evidence needs a source page and a substantive exact passage")
        if quote not in page["body"] or not item.get("locator", "").strip():
            raise ValueError("Semantic evidence passage or locator does not match the source page")
        locator = item["locator"]
        paragraphs = re.fullmatch(r"DMG (\d{5})(?:–(\d{5}))?", locator)
        navigation = re.fullmatch(r"DMG chapter (\d+) section navigation, PDF page (\d+)", locator)
        if paragraphs:
            start, end = int(paragraphs[1]), int(paragraphs[2] or paragraphs[1])
            if end < start or end - start > 20 or any(not re.search(rf"^\s*{number}\b", quote, re.MULTILINE) for number in range(start, end + 1)):
                raise ValueError("Paragraph locator is not supported by the quoted passage")
        elif navigation:
            if int(navigation[1]) != page["chapter"] or int(navigation[2]) != page["page_number"]:
                raise ValueError("Navigation locator disagrees with source page")
        else:
            raise ValueError("Unrecognised semantic evidence locator")
    return target


def compile_relations(nodes, authored_rows, root, base, repo, read):
    inventory = json.loads((root / "source/inventory.json").read_text())
    documents = {doc["sha256"]: doc for doc in inventory["documents"]}
    result, seen = [], set()
    for source, path, file_hash in authored_rows:
        for position, spec in enumerate(source.pop("semantic_relations", [])):
            target = check_relation(spec, source, nodes)
            predicate = spec["predicate"]
            triple = (source["@id"], predicate, target["@id"])
            if triple in seen:
                raise ValueError("Duplicate semantic proposal")
            seen.add(triple)
            identity = digest(canonical(list(triple)))
            observed = str(source.get("observedAt") or source["generated"]["at"])
            evidence = []
            value = canonical(spec).decode().rstrip("\n")
            evidence.append({"@id": base + "id/evidence/semantic-authoring/" + identity,
                "type": "authored-semantic-proposal", "url": read + path.relative_to(root).as_posix(),
                "source_artifact": path.relative_to(root).as_posix(), "source_sha256": file_hash,
                "source_field": f"{source['route']}.semantic_relations[{position}]", "source_value": value,
                "source_value_sha256": digest(value.encode()), "source_value_hash_canonicalization": "utf8-verbatim",
                "locator": source["route"], "rationale": spec["rationale"], "retrieved_at": observed})
            for index, item in enumerate(spec["evidence"]):
                page = nodes[item["page"]]
                doc = documents[page["source_sha256"]]
                pages_path = root / doc["pages_path"]
                page_data = json.loads(pages_path.read_text())["pages"][page["page_number"] - 1]
                if item["quote"] not in page_data["text"]:
                    raise ValueError("Semantic quote must occur in frozen extracted source text")
                evidence.append({"@id": base + "id/evidence/semantic-passage/" + identity + f"/{index}",
                    "type": "source-passage-for-model-proposal", "url": page["source"],
                    "source_artifact": doc["pages_path"], "source_sha256": digest(pages_path.read_bytes()),
                    "source_pdf_artifact": doc["pdf_path"], "source_pdf_sha256": doc["sha256"],
                    "source_page_route": item["page"], "source_field": f"pages[{page['page_number'] - 1}].text",
                    "source_value": item["quote"], "source_value_sha256": digest(item["quote"].encode()),
                    "source_value_hash_canonicalization": "utf8-verbatim", "locator": item["locator"],
                    "retrieved_at": doc["observed_at"]})
            kind, label, inverse = PREDICATES[predicate]
            result.append({"@id": base + "id/assertion/" + identity,
                "@type": ["rdf:Statement", "RelationshipAssertion"],
                "source": source["@id"], "target": target["@id"], "predicate": predicate,
                "source_route": source["route"], "target_route": target["route"],
                "kind": kind, "label": label, "inverse_label": inverse,
                "assertion_status": "model-derived", "assertion_scope": "real-world",
                "authority": {"class": "model-assisted", "label": "Source-backed semantic proposal; unreviewed", "source": repo},
                "derivation": base + "rules/source-backed-semantic-proposal-v1",
                "derivation_activity": base + "id/activity/semantic-stage-two-2026-09-15",
                "confidence_score": 0.5, "review_status": "unreviewed-specialist-review-required",
                "observed_at": observed, "evidence": evidence,
                "rights": {"source": read + "NOTICE.md", "assertion": "Original model-assisted interpretation; source passages retain OGL attribution"}})
            # Absolute predicates prevent a compact label from changing the meaning.
            source.setdefault(predicate, []).append({"@id": target["@id"]})
            source["body"] += f"\n\n**Proposed relationship:** {label} [{target['title']}]({read}bundle/records/{target['route']}.md). {spec['rationale']} Specialist review required."
    return result
