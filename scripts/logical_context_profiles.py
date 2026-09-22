"""Compile explicit logical-unit proposals into the existing context vocabulary."""
from copy import deepcopy
import gzip
import json

from build_bundle import BASE, REPO, canonical, digest, load_yaml
from build_context_discovery import require

AUTHORING = "domain-profile/logical-units/"
DCT = "http://purl.org/dc/terms/"
REVIEW = "unreviewed-specialist-review-required"


def project(inputs, manifest, units):
    previous = json.loads(inputs.read("combined/context/corpus/base-index.json"))
    concepts = {r["id"]: deepcopy(r) for r in previous["records"] if r["kind"] == "concept"}
    edges = {r["id"]: deepcopy(r) for r in previous["assertions"] if r["source"] in concepts and r["target"] in concepts}
    from logical_unit_authoring import load_semantics
    overrides, declarations, profiles, reference_review, dispositions = load_semantics(inputs)
    require(profiles["schema"] == "okf-dwp-logical-task-profiles.v1", "Unsupported unit profiles")
    index = {r["id"]: r for r in units}
    declarations_by_key, catalogue_by_key, owners_by_key = {}, {}, {}
    docrefs = {(d["family"], d["document_id"]): d for d in manifest["documents"]}
    for document in overrides["documents"]:
        ref = docrefs[(document["family"], document["document_id"])]
        raw = inputs.read("logical-units/" + ref["path"], ref["sha256"], ref["bytes"])
        from build_logical_context import decode_shard
        decoded = decode_shard(raw, ref)
        require(digest(decoded) == ref["decoded_sha256"], "Unit catalogue hash differs")
        catalogue = json.loads(decoded)
        require(catalogue["source"]["sha256"] == document["source_sha256"], "Override version differs")
        by_key = {r["key"]: r for r in catalogue["units"]}
        for row in document["units"]:
            key = row["key"]
            require(key not in declarations_by_key and key in by_key, "Duplicate or absent authored unit key")
            target = index.get(by_key[key]["id"])
            require(target and target["evidence_unit"]["boundary_status"] == "author-declared", "Authored unit was not admitted by producer")
            require(by_key[key]["spans"] == row["spans"], "Authored boundary differs from producer: " + key)
            require(by_key[key]["record_sha256"] == digest(canonical(target)) and by_key[key]["text_sha256"] == digest(target["text"].encode()), "Authored unit record identity differs")
            declarations_by_key[key], catalogue_by_key[key] = row, target
            owners_by_key[key] = (document["family"], document["document_id"])
    require(declarations["schema"] == "okf-dwp-logical-concept-authoring.v1", "Unsupported logical concepts")
    for row in declarations["@graph"]:
        require(row["@id"] not in concepts and row["assertion_status"] == "model-derived" and row["review_status"] == REVIEW,
                "New concepts cannot replace existing identity or upgrade review")
        require(all(k in catalogue_by_key for k in row["source_unit_keys"]), "Concept source not admitted")
        evidence = []
        for key in row["source_unit_keys"]:
            evidence.extend({k: v for k, v in p.items() if k != "literal_sha256"} for p in catalogue_by_key[key]["provenance"])
        evidence = list({canonical(p): p for p in evidence}.values())
        concepts[row["@id"]] = {"id": row["@id"], "route": row["@id"].removeprefix(BASE + "id/"),
            "label": row["label"], "kind": "concept", "text": row["definition"], "aliases": row["aliases"],
            "assertion_status": "model-derived", "authority": {"class": "model-assisted", "label": "Source-backed project concept; specialist review pending", "source": REPO + "/blob/main/" + row["authoring_path"]},
            "scope": profiles["scope"], "provenance": evidence, "rights": REPO + "/blob/main/NOTICE.md", "access": "public", "review_status": REVIEW}
    for row in declarations.get("alias_additions", []):
        require(row["id"] in concepts and row["review_status"] == REVIEW and row["scope"].strip(), "Unknown alias concept or review scope")
        require(isinstance(row["aliases"], list) and row["aliases"] and all(isinstance(s, str) and s.strip() and len(s) <= 300 for s in row["aliases"]), "Invalid alias additions")
        require(row["source_unit_keys"] and all(k in catalogue_by_key for k in row["source_unit_keys"]), "Alias source unit not admitted")
        target = concepts[row["id"]]
        target["aliases"] = [*target.get("aliases", [])]
        for alias in row["aliases"]:
            if alias not in target["aliases"]:
                target["aliases"].append(alias)
        target["scope"] += " " + row["scope"]
        for key in row["source_unit_keys"]:
            for item in catalogue_by_key[key]["provenance"]:
                evidence = {k: v for k, v in item.items() if k != "literal_sha256"}
                if evidence not in target["provenance"]:
                    target["provenance"].append(evidence)
    authored_pairs = {}
    proposals = {}
    for document in overrides["documents"]:
        for proposal in document["proposals"]:
            pair = (proposal["source_unit_key"], proposal["target_unit_key"], proposal["predicate"])
            require(pair not in proposals and proposal["assertion_status"] == "model-derived" and proposal["review_status"] == REVIEW, "Duplicate proposal or unreviewed authority upgrade")
            require(pair[0] in catalogue_by_key and pair[1] in catalogue_by_key and pair[2] in {DCT + "requires", DCT + "references"}, "Unsupported proposal endpoint or predicate")
            require(owners_by_key[pair[0]] == (document["family"], document["document_id"]), "Proposal source document owner differs")
            expected_target = proposal.get("target_document_id", document["document_id"])
            require(owners_by_key[pair[1]][1] == expected_target, "Proposal target document owner differs")
            require("target_document_id" in proposal or owners_by_key[pair[1]] == owners_by_key[pair[0]], "Cross-document proposal needs an explicit target document")
            require(proposal["evidence_spans"] == declarations_by_key[pair[0]]["spans"], "Proposal source spans differ")
            proposals[pair] = proposal

    def edge(source, target, predicate, label, proposal, evidence):
        pair = (source, target, predicate)
        if pair in authored_pairs:
            return authored_pairs[pair]
        iri = BASE + "id/assertion/logical-unit/" + digest(canonical(pair))
        value = {"id": iri, "source": source, "target": target, "predicate": predicate, "label": label,
            "assertion_status": "model-derived", "authority": {"class": "model-assisted", "label": "Agent source review; specialist interpretation unreviewed", "source": REPO + "/blob/main/" + proposal["authoring_path"]},
            "scope": " ".join(str(proposal[k]) for k in ("assertion_scope", "conditional_scope", "reason", "review_note") if proposal.get(k)) + " Specialist acceptance and current applicability are not established.",
            "provenance": evidence}
        require(iri not in edges, "Assertion identity collision")
        edges[iri] = value; authored_pairs[pair] = iri
        return iri

    for key, declaration in declarations_by_key.items():
        unit = catalogue_by_key[key]
        for identifier in declaration.get("concept_ids", []):
            require(identifier in concepts, "Authored unit concept is absent: " + identifier)
            edge(identifier, unit["id"], DCT + "references", "references source unit", declaration, unit["provenance"])
        for field, predicate, label in (("support_unit_keys", DCT + "requires", "requires supporting source unit"),
                                      ("reference_unit_keys", DCT + "references", "references related source unit")):
            for other in declaration.get(field, []):
                require(other in catalogue_by_key, "Unresolved authored support key: " + other)
                proposal = proposals.get((key, other, predicate), declaration)
                edge(unit["id"], catalogue_by_key[other]["id"], predicate, label, proposal, unit["provenance"])
    # Includes explicit cross-document references, never guessed from labels.
    for (source, target, predicate), proposal in proposals.items():
        unit = catalogue_by_key[source]
        edge(unit["id"], catalogue_by_key[target]["id"], predicate,
             "requires supporting source unit" if predicate == DCT + "requires" else "references related source unit", proposal, unit["provenance"])
    for row in reference_review["references"]:
        require(row["status"] == "unresolved" and row["source_unit_key"] in catalogue_by_key, "Unknown unresolved reference")
        require(owners_by_key[row["source_unit_key"]][1] == row["document_id"], "Reference-review document owner differs")
        require(row["evidence_spans"] == declarations_by_key[row["source_unit_key"]]["spans"], "Reference-review source spans differ")
    for row in dispositions:
        require(all(key in catalogue_by_key for key in row["target_unit_keys"]), "Reference disposition target was not admitted")
    requirements = []
    for row in profiles["profiles"]:
        require(row["assertion_status"] == "model-derived" and row["review_status"] == REVIEW and row["missing_obligations"], "Profile cannot silently upgrade answerability")
        require(set(row["when_all"]) <= set(concepts) and set(row["covers"]) <= set(row["when_all"]), "Unknown profile concept")
        require(len(set(r["id"] for r in row["missing_obligations"])) == len(row["missing_obligations"]), "Duplicate missing-obligation identity")
        require(len(set(row["required_unit_keys"])) == len(row["required_unit_keys"]), "Duplicate profile required unit")
        required = [catalogue_by_key[key]["id"] for key in row["required_unit_keys"]]
        paths = []
        for path in row["required_paths"]:
            require(path["seed"] in row["when_all"], "Required path must start at a resolved profile concept")
            records = [path["seed"], *[catalogue_by_key[key]["id"] for key in path["unit_keys"]]]
            assertions = []
            for source, target in zip(records, records[1:]):
                matches = [identifier for (a, b, _), identifier in authored_pairs.items() if a == source and b == target]
                require(len(matches) == 1, "Missing or ambiguous declared required path")
                assertions.extend(matches)
            paths.append({"seed": path["seed"], "records": records, "assertions": assertions})
        obligations = [BASE + "id/obligation/logical/" + row["id"] + "/" + r["id"] for r in row["missing_obligations"]]
        require(not set(obligations) & (set(concepts) | set(index)), "Open obligation must remain absent")
        requirements.append({"id": BASE + "id/requirement/" + row["id"], "label": row["id"].replace("-", " "),
            "when_all": row["when_all"], "covers": row["covers"], "required": required + obligations,
            "required_paths": paths, "scope": row["scope"],
            "limitations": [r["category"] + ": " + r["label"] for r in row["missing_obligations"]]
                + ["unresolved_reference: " + r["literal_reference"] + ": " + r["note"] for r in reference_review["references"] if r["source_unit_key"] in row["required_unit_keys"]]
                + ["reference_target_review: " + r["literal_reference"] + ": " + r["target_status"] + ": " + r["note"]
                   for r in dispositions if r["source_unit_key"] in row["required_unit_keys"]]})
    return {"schema": "okf-context-index.v1", "records": sorted(concepts.values(), key=lambda r: r["id"]),
        "assertions": sorted(edges.values(), key=lambda r: r["id"]), "requirements": requirements}, declarations
