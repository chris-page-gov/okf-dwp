#!/usr/bin/env python3
"""Execute indexed evidence retrieval controls; never grade legal answers."""
from __future__ import annotations

import argparse
from functools import lru_cache
import gzip
import json
from pathlib import Path
import re

from build_bundle import ROOT, canonical, digest, load_yaml
from build_full_dmg import tokens

OUTPUT = "evaluation/full-dmg-retrieval.json"


def read(path: Path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


class IndexedEvidence:
    """Read the published postings and records, not reconstructed source search."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.descriptor = read(directory / "okf-explorer.json")
        self.manifest = read(directory / "data/search/manifest.json")
        self.records = [row for part in read(directory / "data/manifest.json")["chunks"]["datasets"]
                        for row in read(directory / part)]
        self.routes = {row["route"]: row for row in self.records}
        self.postings = {token: rows for part in self.manifest["entrypoints"]["postings"]
                         for token, rows in read(directory / part)["tokens"].items()}

    def search(self, query: str, document_id: str | None = None) -> list[dict]:
        terms = tokens(query)
        if not terms:
            return []
        matches = [dict((row[0], row[1]) for row in self.postings.get(term, [])) for term in terms]
        ordinals = set(matches[0]).intersection(*(set(rows) for rows in matches[1:]))
        ranked = sorted(ordinals, key=lambda i: (-sum(rows[i] for rows in matches), self.records[i]["title"], i))
        return [self.records[i] for i in ranked if document_id is None or self.records[i].get("document_id") == document_id]

    def verify_passage(self, route: str, quote: str, source_sha256: str) -> dict:
        row = self.routes[route]
        if not quote or quote not in row["narrative"]["body"]:
            raise ValueError("The expected passage is absent from the indexed record")
        if row["provenance"]["source_sha256"] != source_sha256:
            raise ValueError("The source PDF identity differs")
        return {"route": route, "title": row["title"], "source_url": row["url"],
                "source_role": row["source_role"], "quote": quote, "quote_sha256": digest(quote.encode()),
                "source_sha256": source_sha256, "page_text_sha256": row["provenance"]["page_text_sha256"],
                "publication_date": None, "publication_date_status": "not-established",
                "applicability": "not-established", "specialist_acceptance": "not-recorded"}


def evaluate(root: Path = ROOT) -> dict:
    corpus = IndexedEvidence(root / "full-dmg")
    plan = read(root / "evaluation/full-dmg-coverage-plan.json")
    inventory = read(root / "source/full-dmg-2026-09-15/inventory.json")
    documents = {doc["id"]: doc for doc in inventory["documents"]}
    by_url = {doc["url"]: doc for doc in inventory["documents"]}
    source_units = {unit["id"]: unit for unit in plan["source_units"]}
    source_routes = {doc["id"]: doc["page_routes"] for doc in read(root / "full-dmg/data/source-documents.json")["documents"]}
    semantic_passages = {}
    inputs = []
    for path in sorted((root / "knowledge").rglob("*.yamlld")):
        inputs.append({"path": path.relative_to(root).as_posix(), "sha256": digest(path.read_bytes())})
        for node in load_yaml(path).get("@graph", []):
            for relation in node.get("semantic_relations", []):
                for evidence in relation.get("evidence", []):
                    row = corpus.routes.get(evidence.get("page"))
                    if row:
                        semantic_passages.setdefault(row.get("document_id"), evidence)
    @lru_cache(maxsize=None)
    def pages(document_id):
        return read(root / documents[document_id]["pages_path"])["pages"]
    cases = []
    for task in plan["chapter_tasks"]:
        doc = by_url[source_units[task["source_unit"]]["official_url"]]
        evidence = semantic_passages.get(doc["id"])
        if not evidence:
            cases.append({"task_id": task["id"], "status": "not-run-no-authored-passage-yet", "document_id": doc["id"]})
            continue
        match = re.match(r"DMG (\d{5,6})", evidence["locator"])
        query = match[1] if match else " ".join(tokens(evidence["quote"])[:3])
        found = corpus.search(query, doc["id"])
        expected_found = evidence["page"] in {row["route"] for row in found}
        actual = corpus.verify_passage(evidence["page"], evidence["quote"], doc["sha256"])
        absent_query = "okfintentionallymissingclaimantevidence" + doc["id"].replace("-", "")
        no_match = corpus.search(absent_query, doc["id"])
        if not expected_found or no_match:
            raise ValueError("Indexed locator or no-result control failed: " + task["id"])
        cases.append({"task_id": task["id"], "source_unit_id": task["source_unit"], "document_id": doc["id"],
                      "status": "passed-deterministic-locator-and-no-result-controls",
                      "execution_method": "Indexed exact-token AND retrieval, document filter and complete-record hydration",
                      "positive": {"query": query, "query_basis": "Explicit authored paragraph locator; this is not natural-language question answering",
                                   "matched_routes": [row["route"] for row in found], "returned_evidence": actual},
                      "negative": {"query": absent_query, "matched_routes": [], "actual_output": "No matching evidence in this frozen corpus."},
                      "journey_questions": task["journey_questions"],
                      "behavioural_case_status": "not-executed-by-this-deterministic-harness",
                      "specialist_accepted": False})
    baseline = []
    for case in plan["baseline_case_tasks"]:
        routes = [case["question_route"], *case["persona_routes"], *case["story_routes"], *case["source_navigation"]]
        missing = sorted(set(routes) - corpus.routes.keys())
        if missing:
            raise ValueError("Baseline navigation missing: " + str(missing))
        baseline.append({"id": case["id"], "status": "passed-route-preservation",
                         "routes": sorted(set(routes)), "question_body_sha256": digest(corpus.routes[case["question_route"]]["narrative"]["body"].encode()),
                         "persona_routes": case["persona_routes"], "story_routes": case["story_routes"],
                         "answer_evaluation": "not-executed; navigation integrity only"})
    families = []
    for task in plan["family_case_tasks"]:
        doc = by_url[source_units[task["source_units"][0]]["official_url"]]
        if task["kind"] == "boundary":
            query = "okfintentionallymissingfamilysource"
            result = corpus.search(query, doc["id"])
            if result:
                raise ValueError("Family no-result control failed")
            actual = {"query": query, "matched_routes": [], "output": "No matching evidence in this frozen corpus."}
        else:
            page = next((p for p in pages(doc["id"]) if p["text"].strip()), None)
            if page is None:
                actual = {"output": "No machine-extracted text; source PDF retained.", "source_url": doc["url"]}
            else:
                route = source_routes[doc["id"]][page["page"] - 1]
                actual = corpus.verify_passage(route, page["text"], doc["sha256"])
        families.append({"id": task["id"], "family_id": task["family_id"], "document_id": doc["id"],
                         "status": "passed-source-navigation" if task["kind"] != "boundary" else "passed-no-result-control",
                         "actual_output": actual, "legal_boundary_evaluation": "not-executed"})
    probes = [case for case in cases if case["status"].startswith("passed")]
    controls = []
    if probes:
        evidence = probes[0]["positive"]["returned_evidence"]
        for label, quote, sha in [("fabricated-passage", "This fabricated sentence awards all claims.", evidence["source_sha256"]),
                                  ("changed-source-identity", evidence["quote"], "0" * 64)]:
            try:
                corpus.verify_passage(evidence["route"], quote, sha)
            except ValueError:
                controls.append(label)
            else:
                raise ValueError("Negative integrity control was accepted")
    binding_paths = ["scripts/evaluate_full_dmg.py", "full-dmg/checksums.json", "evaluation/full-dmg-coverage-plan.json", "source/full-dmg-2026-09-15/inventory.json"]
    return {"schema": "okf-dwp-indexed-retrieval-evaluation.v1", "snapshot": corpus.descriptor["snapshot"],
            "execution_kind": "deterministic evidence retrieval; no language model response generation",
            "status": "passed-for-executed-controls", "inputs": [{"path": path, "sha256": digest((root / path).read_bytes())} for path in binding_paths] + inputs,
            "counts": {"substantive_units": len(cases), "locator_and_no_result_pairs_passed": len(probes),
                       "not_run_without_authored_passage": len(cases) - len(probes), "baseline_routes_checked": len(baseline),
                       "family_controls_passed": len(families), "behavioural_or_specialist_cases_executed": 0},
            "chapter_controls": cases, "baseline_controls": baseline, "family_controls": families, "negative_integrity_controls": controls,
            "limitations": ["Locator replay demonstrates evidence availability, not natural-language question answering.",
                            "Designed positive and boundary questions still require separate observed responses and grading.",
                            "No current-law applicability, specialist acceptance, model-comparison result or entitlement decision is inferred."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    data = canonical(result)
    path = ROOT / OUTPUT
    if args.check:
        if not path.exists() or path.read_bytes() != data:
            raise SystemExit("Indexed retrieval receipt is stale")
    else:
        path.write_bytes(data)
    print(json.dumps({"status": result["status"], "snapshot": result["snapshot"], **result["counts"]}))


if __name__ == "__main__":
    main()
