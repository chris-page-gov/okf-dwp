#!/usr/bin/env python3
"""Build an additive, offline legal-reference review projection.

Detected citation lines are research candidates, not a complete legal parser.
No provision metadata, title match or tribunal search hit establishes applicability.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from build_bundle import yaml_bytes

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "source/legal-discovery-2026-09-20"
SEEDS = "domain-profile/legal-reconciliation/seeds.json"
BASE = "https://chris-page-gov.github.io/okf-dwp/id/"
REPO = "https://github.com/chris-page-gov/okf-dwp/blob/main/"
PREDICATE = "http://purl.org/dc/terms/references"
SIGNAL = re.compile(r"\b(?:Regs|reg\b|Act\b|Sch\b|Art\b|UKUT\b)|\bR\(")
PROVISION = re.compile(r"\b(reg|s|Sch)\s+([0-9]+[A-Za-z]?|IIIA|IIA|III|IV|II|I)\b")
LIMITS = [
    "Independent project-authored reference reconciliation; no specialist legal acceptance.",
    "Literal citation candidates preserve frozen page offsets. Indented-line detection may miss split, unindented or damaged citations; no-candidate-found is not no-legal-dependency.",
    "Official metadata verifies selected identities and observed versions, not statutory propositions, complete amendments, commencement or territorial applicability.",
    "Tribunal query results are bounded official discovery metadata, not a relevance or applicability decision. Judgment bodies have not been acquired.",
    "No individual entitlement decisions or award calculations. Source instructions remain inert data.",
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pretty(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def load(root: Path, path: str) -> dict:
    return json.loads((root / path).read_text())


def citation_lines(text: str) -> list[dict]:
    """Retain exact candidate line groups; offsets use Python Unicode code points."""
    lines = []
    offset = 0
    for raw in text.splitlines(keepends=True):
        literal = raw.rstrip("\r\n")
        lines.append((offset, literal, len(literal) - len(literal.lstrip())))
        offset += len(raw)
    selected = set()
    for index, (_, literal, indent) in enumerate(lines):
        if indent >= 8 and SIGNAL.search(literal) and not re.match(r"\s*\d{5,6}\b", literal):
            selected.add(index)
            for next_index in range(index + 1, len(lines)):
                _, continuation, spaces = lines[next_index]
                if not continuation.strip() or spaces < 8 or re.match(r"\s*\d{5,6}\b", continuation):
                    break
                selected.add(next_index)
    groups = []
    for index in sorted(selected):
        start, literal, _ = lines[index]
        if groups and index == groups[-1]["last_line"] + 1:
            groups[-1]["end"] = start + len(literal)
            groups[-1]["last_line"] = index
        else:
            groups.append({"start": start, "end": start + len(literal), "last_line": index})
    return [{"start": g["start"], "end": g["end"], "literal": text[g["start"]:g["end"]],
             "literal_sha256": sha(text[g["start"]:g["end"]].encode())} for g in groups]


def references(literal: str, works: list[dict], observations: dict) -> list[dict]:
    occurrences = []
    # Longest alias first avoids treating the 1987-suffixed alias twice.
    occupied = set()
    for work, alias in sorted(((w, a) for w in works for a in w["aliases"]), key=lambda x: -len(x[1])):
        for match in re.finditer(re.escape(alias) + r"(?!\w)", literal):
            span = set(range(match.start(), match.end()))
            if occupied & span:
                continue
            occupied |= span
            occurrences.append({"start": match.start(), "end": match.end(), "alias": alias, "work": work})
    occurrences.sort(key=lambda x: x["start"])
    results = []
    for index, occurrence in enumerate(occurrences):
        work = occurrence["work"]
        end = occurrences[index + 1]["start"] if index + 1 < len(occurrences) else len(literal)
        tail = literal[occurrence["end"]:end]
        # An unknown work is a hard boundary. A bare ``reg 3`` may inherit a
        # preceding explicit work, but ``Unknown Regulations, reg 3`` must not.
        # Keep the original full citation in the census for unresolved review.
        safe_segments = []
        for segment_index, segment in enumerate(tail.split(";")):
            opening = re.sub(r"^\s*\d+\s+", "", segment).lstrip()
            if segment_index and not re.match(r"(?:reg|s|Sch|Art)\s", opening) and re.search(
                    r"\b(?:Regs?|Regulations?|Act|Order|Scheme|UKUT)\b|\bR\(", opening):
                break
            safe_segments.append(segment)
        tail = ";".join(safe_segments)
        refs = []
        for match in PROVISION.finditer(tail):
            kind = {"s": "section", "reg": "regulation", "Sch": "schedule"}[match.group(1)]
            target = work["work_path"] + "/" + kind + "/" + match.group(2)
            observed = observations.get(target)
            refs.append({"literal_locator": match.group(), "target": target,
                         "provision_id": "http://www.legislation.gov.uk/id/" + target,
                         "verification_status": observed["status"] if observed else "not-acquired",
                         "observation_path": SOURCE + "/legislation/" + target.replace("/", "--") + ".json" if observed else None,
                         "finer_locator_status": "literal-retained; subsections-and-inherited-locators-not-resolved"})
        results.append({"work_id": work["id"], "work_identifier": "http://www.legislation.gov.uk/id/" + work["work_path"],
                        "literal_alias": occurrence["alias"], "alias_start": occurrence["start"], "alias_end": occurrence["end"],
                        "predicate": PREDICATE, "mapping_status": "normalised-reference-proposal",
                        "applicability_review": "unreviewed", "provisions": refs})
    return results


def check_snapshot(root: Path) -> tuple[dict, dict]:
    manifest = load(root, SOURCE + "/manifest.json")
    if manifest["seed_sha256"] != sha((root / SEEDS).read_bytes()):
        raise ValueError("Legal acquisition seed drift")
    observations = {}
    seen_paths = set()
    for binding in manifest["files"]:
        relative = Path(binding["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe metadata path")
        if str(relative) in seen_paths:
            raise ValueError("Duplicate metadata path")
        seen_paths.add(str(relative))
        data = (root / SOURCE / relative).read_bytes()
        if len(data) != binding["bytes"] or sha(data) != binding["sha256"]:
            raise ValueError("Legal observation hash mismatch: " + str(relative))
        value = json.loads(data)
        if value.get("kind") == "legislation-provision-metadata":
            if value["status"] == "identifier-verified":
                expected = "http://www.legislation.gov.uk/id/" + value["target"]
                if value["metadata"]["target_attributes"].get("IdURI") != expected:
                    raise ValueError("Official target identity does not match requested provision")
            observations[value["target"]] = value
    expected = {row["target"] for row in load(root, SEEDS)["provisions"]}
    if set(observations) != expected:
        raise ValueError("Official request census does not match declared targets")
    projected_ids={effect["effect_identifier_sha256"] for row in observations.values()
                   for effect in row.get("metadata",{}).get("effect_metadata",[])
                   if "effect_identifier_sha256" in effect}
    if projected_ids:
        if not {"publication-projection.json","effect-identifier-verification.json"} <= seen_paths:
            raise ValueError("Public effect projection evidence is not manifest-bound")
        if manifest.get("publication_projection") != "publication-projection.json":
            raise ValueError("Public effect projection declaration missing")
        proof=load(root,SOURCE+"/effect-identifier-verification.json")
        observed={e["effect_identity_sha256"] for row in proof["observations"] for e in row.get("observations",[])}
        if not projected_ids <= observed or not proof["all_expected_identifiers_observed"]:
            raise ValueError("Projected effect identifiers lack official-origin observations")
    return manifest, observations


def record(route: str, title: str, description: str, resource: str, body: str) -> dict:
    return {"@id": BASE + route, "@type": "schema:CreativeWork", "route": route,
            "title": title, "type": "Legal reference", "description": description,
            "status": "draft", "authority": "Project-authored normalisation of official metadata; not a legal proposition",
            "observedAt": "2026-09-20", "resource": resource, "license": REPO + "LICENSE",
            "review_status": "unreviewed", "body": body,
            "context_assembly": {"kind": "reference", "text": description, "scope": LIMITS[2]}}


def build(root: Path = ROOT) -> dict[str, bytes]:
    seeds = load(root, SEEDS)
    registry = load(root, "evaluation/staff-questions/cases.json")
    manifest, observations = check_snapshot(root)
    cases_by_candidate = {c["id"]: [case["id"] for case in registry["cases"] if c["id"] in case["candidate_ids"]]
                          for c in registry["source_candidates"]}
    census, assertions, graph = [], [], []
    for candidate in registry["source_candidates"]:
        raw = (root / candidate["pages_path"]).read_bytes()
        if sha(raw) != candidate["pages_sha256"]:
            raise ValueError("Frozen candidate page file changed: " + candidate["id"])
        page = json.loads(raw)["pages"][candidate["page"] - 1]
        text = page["text"]
        if sha(text.encode()) != candidate["literal_sha256"]:
            raise ValueError("Frozen page literal changed: " + candidate["id"])
        citations = citation_lines(text)
        for number, citation in enumerate(citations, 1):
            citation["id"] = candidate["id"] + "-citation-" + str(number).zfill(2)
            citation["references"] = references(citation["literal"], seeds["works"], observations)
            citation["resolution_status"] = "partial-reference-proposal" if citation["references"] else "unresolved"
            citation["unresolved"] = ["Entire literal requires review; exact subordinate and inherited locators, unknown abbreviations and case citations may remain."]
            for ref in citation["references"]:
                for provision in ref["provisions"]:
                    if provision["verification_status"] == "identifier-verified":
                        assertions.append({"source_candidate_id": candidate["id"], "source": candidate["route"],
                            "target": "legal/" + provision["target"], "predicate": PREDICATE,
                            "assertion_status": "normalized", "review_status": "unreviewed",
                            "authority": "project-reference-normalisation", "scope": "citation-navigation-only",
                            "case_ids": cases_by_candidate[candidate["id"]], "citation_id": citation["id"],
                            "evidence": {"literal": citation["literal"], "literal_sha256": citation["literal_sha256"],
                                         "start": citation["start"], "end": citation["end"],
                                         "source_url": candidate["url"], "source_sha256": candidate["source_sha256"],
                                         "page_literal_sha256": candidate["literal_sha256"],
                                         "observation_path": provision["observation_path"]}})
        census.append({"source_candidate_id": candidate["id"], "route": candidate["route"],
                       "case_ids": cases_by_candidate[candidate["id"]], "page": candidate["page"],
                       "source_url": candidate["url"], "page_literal_sha256": candidate["literal_sha256"],
                       "source_publication_date": candidate["source_publication_date"],
                       "citation_candidate_status": "candidates-detected" if citations else "no-candidate-detected; review-surrounding-pages",
                       "citations": citations})
    for work in seeds["works"]:
        route = "legal/" + work["work_path"]
        rows = [v for k, v in observations.items() if k.startswith(work["work_path"] + "/")]
        verified = [r for r in rows if r["status"] == "identifier-verified"]
        description = f"Official work identity reference; {len(verified)} selected provision identifiers verified in the dated metadata acquisition. Applicability and full effects are unreviewed."
        node = record(route, work["title"], description,
                      "https://www.legislation.gov.uk/" + work["work_path"] + "/contents",
                      "# " + work["title"] + "\n\n" + description + "\n\nLiteral DWP abbreviations: " + ", ".join(work["aliases"]) + ".\n\nNo statutory body text is included.\n")
        node["schema:about"] = {"@id": "http://www.legislation.gov.uk/id/" + work["work_path"]}
        node["context_assembly"]["aliases"] = work["aliases"]
        node["references"] = ["legal/" + r["target"] for r in verified]
        graph.append(node)
    for target, row in sorted(observations.items()):
        if row["status"] != "identifier-verified":
            continue
        meta = row["metadata"]
        description = f"Official identifier observed for {target}; metadata requested for {row['requested_version_date']}. This reference contains no statutory text or accepted applicability conclusion."
        url = row["receipt"]["requested_url"].removesuffix("/data.xml")
        node = record("legal/" + target, meta["title"] + " — " + "/".join(target.split("/")[3:]),
                      description, url, "# Legal provision reference\n\n" + description + "\n\n[Official dated provision](" + url + ").\n")
        node["schema:about"] = {"@id": meta["target_attributes"]["IdURI"]}
        node["source"] = REPO + SOURCE + "/legislation/" + target.replace("/", "--") + ".json"
        node["legal_metadata"] = {"document_uri": meta["target_attributes"].get("DocumentURI"),
                                  "requested_version_date": row["requested_version_date"],
                                  "target_and_ancestor_restrictions": meta["target_and_ancestor_restrictions"],
                                  "effects": meta["effects_assessment"], "commencement": meta["commencement_assessment"],
                                  "applicability_review": "unreviewed"}
        node["references"] = ["legal/" + "/".join(target.split("/")[:3])]
        graph.append(node)
    queries = load(root, SOURCE + "/queries.json")
    decisions = []
    for item in manifest["files"]:
        if not item["path"].startswith("tribunal/"):
            continue
        row = load(root, SOURCE + "/" + item["path"])
        if row["status"] != "observed":
            continue
        meta = row["metadata"]
        key = meta["base_path"].rsplit("/", 1)[-1]
        decisions.append({"id": key, **meta})
        description = "Official tribunal catalogue metadata from bounded discovery. Its presence is not a conclusion that this decision applies to any supplied question."
        node = record("legal/tribunal/" + key, meta["title"], description,
                      "https://www.gov.uk" + meta["base_path"], "# Tribunal discovery reference\n\n" + description + "\n")
        node["source"] = REPO + SOURCE + "/" + item["path"]
        node["decision_date"] = meta["decision_date"]
        node["publication_date"] = meta["first_published_at"]
        node["context_assembly"]["scope"] = "Discovery-only; legal applicability and judgment-body rights unassessed."
        graph.append(node)
    effect_observations = {}
    for target, observation in observations.items():
        for effect in observation.get("metadata", {}).get("effect_metadata", []):
            identity = effect.get("effect_identifier_sha256")
            if not identity:
                continue
            entry = effect_observations.setdefault(identity, {"id": "urn:sha256:" + identity,
                "identity_kind": "digest-of-source-EffectId; opaque identifier omitted from public projection", "observations": []})
            entry["observations"].append({"source_target": target,
                "observation_path": SOURCE + "/legislation/" + target.replace("/", "--") + ".json",
                "source_metadata_projection": effect})
    all_citations = [c for p in census for c in p["citations"]]
    statuses = dict(sorted(Counter(r["status"] for r in observations.values()).items()))
    coverage = {"schema": "okf-legal-reconciliation-coverage.v1", "observed_on": "2026-09-20",
                "staff_case_occurrences": len(registry["cases"]), "candidate_pages": len(census),
                "pages_with_detected_citation_candidates": sum(bool(p["citations"]) for p in census),
                "citation_candidates": len(all_citations), "work_aliases_selected": len(seeds["works"]),
                "official_provision_requests": len(observations), "official_provision_statuses": statuses,
                "reference_assertions": len(assertions), "tribunal_queries": len(queries["queries"]),
                "distinct_source_effect_identifiers": len(effect_observations),
                "provision_responses_with_effect_metadata": sum(bool(r.get("metadata", {}).get("effect_metadata")) for r in observations.values()),
                "provisions_with_observed_extent_attributes": sum(any("RestrictExtent" in a["attributes"] for a in r.get("metadata", {}).get("target_and_ancestor_restrictions", [])) for r in observations.values()),
                "extent_unknown_count": sum(not any("RestrictExtent" in a["attributes"] for a in r.get("metadata", {}).get("target_and_ancestor_restrictions", [])) for r in observations.values()),
                "tribunal_decisions_observed": len(decisions),
                "tribunal_queries_truncated": sum(q["truncated"] is True for q in queries["queries"]),
                "statutory_or_judgment_bodies_acquired": 0, "accepted_legal_propositions": 0,
                "engineering_status": "bounded-source-reference-reconciliation-built",
                "specialist_acceptance": "pending", "legal_completeness": "not-established",
                "limitations": LIMITS,
                "source_manifest_sha256": sha((root / SOURCE / "manifest.json").read_bytes())}
    return {"evaluation/legal-reconciliation/citations.json": pretty({"schema": "okf-legal-citation-census.v1", "offset_encoding": "Unicode code points; zero-based start-inclusive/end-exclusive", "scope": "all 42 declared candidate pages; detected indented citation candidates only", "limitations": LIMITS, "pages": census}),
            "evaluation/legal-reconciliation/assertions.json": pretty({"schema": "okf-legal-reference-assertions.v1", "assertions": assertions}),
            "evaluation/legal-reconciliation/tribunal-discovery.json": pretty({"schema": "okf-tribunal-discovery.v1", "queries": queries["queries"], "decisions": decisions, "limitations": LIMITS}),
            "evaluation/legal-reconciliation/effects.json": pretty({"schema": "okf-observed-legal-effects.v1", "scope": "Effect metadata carried in the selected XML responses; records can concern other parts of the same work. No target-specific application, complete amendment chain or commencement conclusion is asserted.", "effects": [effect_observations[k] for k in sorted(effect_observations)]}),
            "evaluation/legal-reconciliation/coverage.json": pretty(coverage),
            "domain-profile/legal-reconciliation/references.yamlld": yaml_bytes({"@context": "https://chris-page-gov.github.io/okf-explorer/profile/bundle-wiki/v1/context.jsonld", "@graph": graph})}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    differences = []
    outputs = build()
    for name, data in outputs.items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                differences.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if differences:
        raise SystemExit("Legal reconciliation projection drift: " + ", ".join(differences))
    print(json.dumps({"ok": True, "outputs": len(outputs), "network_access": False,
                      "legal_completeness": "not-established"}))


if __name__ == "__main__":
    main()
