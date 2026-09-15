#!/usr/bin/env python3
"""Replay recorded trial integrity and aggregate existing grades; never grade answers."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = "evaluation/full-dmg-behavioural/"
OUTPUT = BASE + "summary.json"
INVENTORY = "source/full-dmg-2026-09-15/inventory.json"
PLAN = "evaluation/full-dmg-coverage-plan.json"
REGISTRY = BASE + "case-registry.json"
EXPORT = BASE + "answerer-tasks.json"
PACKETS = ("comms", "personas", "esa")
SCHEMAS = {
    "comms": ("okf-dwp-observed-source-grounded-trials.v1", "okf-dwp-independent-model-trial-assessment.v1"),
    "personas": ("okf-dwp-source-grounded-answer-trials.v1", "okf-dwp-source-grounded-independent-assessment.v1"),
    "esa": ("okf-dwp-observed-source-trials.v1", "okf-dwp-independent-source-trial-assessment.v1"),
}
GRADE_CATEGORIES = {
    "supported-within-selected-source-scope": "supported",
    "prompt-supported-rubric-underspecified": "rubric-underspecified",
    "partial-authored-rubric-coverage": "partial",
    "meets-bounded-authored-case": "supported",
    "meets-authored-case": "supported",
    "partially-meets-authored-case": "partial",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical(value: object) -> bytes:
    # This is the canonicalisation used for original_case_sha256 in the registry.
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def pointer(value: object, path: str) -> object:
    """Resolve an RFC 6901 JSON pointer; never evaluate source text as code."""
    if path == "":
        return value
    require(path.startswith("/"), f"Invalid JSON pointer: {path}")
    for part in path[1:].split("/"):
        require(re.search(r"~[^01]|~$", part) is None, f"Invalid pointer escape: {path}")
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            require(re.fullmatch(r"0|[1-9][0-9]*", part) is not None,
                    f"Invalid array pointer: {path}")
            require(int(part) < len(value), f"Array pointer out of range: {path}")
            value = value[int(part)]
        else:
            require(isinstance(value, dict) and part in value, f"Missing JSON pointer: {path}")
            value = value[part]
    return value


def unique(rows: list[dict], key: str, context: str) -> dict[str, dict]:
    result = {}
    for row in rows:
        require(isinstance(row.get(key), str) and row[key], f"Missing {key}: {context}")
        require(row[key] not in result, f"Duplicate {key}: {context}: {row[key]}")
        result[row[key]] = row
    return result


class TrialReplay:
    def __init__(self, root: Path = ROOT):
        self.root = root.resolve()
        self.inputs: dict[str, str] = {}
        self.json_cache: dict[str, dict] = {}
        self.counts: Counter = Counter()
        self.observations: set[str] = set()
        self.inventory = self.read(INVENTORY)
        self.documents = unique(self.inventory["documents"], "id", INVENTORY)
        self.plan = self.read(PLAN)
        self.units = unique(self.plan["source_units"], "official_url", PLAN)
        pilot = self.read("source/inventory.json")
        self.pilot_ids = {d["id"] for d in pilot["documents"] if d.get("role") == "substantive"}
        self.pages: dict[str, dict] = {}

    def path(self, name: str) -> Path:
        require(isinstance(name, str) and not Path(name).is_absolute(), f"Non-portable path: {name}")
        path = (self.root / name).resolve()
        require(path.is_relative_to(self.root), f"Path leaves repository: {name}")
        return path

    def file_hash(self, name: str) -> str:
        if name not in self.inputs:
            self.inputs[name] = digest(self.path(name).read_bytes())
        return self.inputs[name]

    def read(self, name: str) -> dict:
        if name not in self.json_cache:
            raw = self.path(name).read_bytes()
            self.inputs[name] = digest(raw)
            self.json_cache[name] = json.loads(raw)
        return self.json_cache[name]

    def binding(self, name: str, expected: str) -> None:
        require(self.file_hash(name) == expected, f"File hash mismatch: {name}")
        self.counts["declared_file_hash_bindings"] += 1

    def input_bindings(self, packet: dict) -> None:
        for row in packet.get("inputs", []):
            self.binding(row["path"], row["sha256"])

    def source_unit(self, unit: dict) -> None:
        doc = self.documents[unit["document_id"]]
        require(unit["pdf_sha256"] == doc["sha256"] and unit["source_url"] == doc["url"],
                f"Source unit identity mismatch: {doc['id']}")
        require(unit["id"] == self.units[doc["url"]]["id"], f"Source unit plan mismatch: {doc['id']}")
        require(unit["chapter"] == doc["chapter"] and unit["part"] == doc.get("part"),
                f"Source unit chapter mismatch: {doc['id']}")

    def source_page(self, document_id: str, number: int) -> tuple[dict, dict]:
        doc = self.documents[document_id]
        if document_id not in self.pages:
            self.binding(doc["pdf_path"], doc["sha256"])
            self.binding(doc["pages_path"], doc["pages_sha256"])
            data = self.read(doc["pages_path"])
            require(data["document_id"] == document_id and data["source_sha256"] == doc["sha256"]
                    and data["source_url"] == doc["url"], f"Page artefact identity: {document_id}")
            require(len(data["pages"]) == doc["pages"], f"Page denominator: {document_id}")
            self.pages[document_id] = data
        require(type(number) is int and 1 <= number <= doc["pages"], f"Invalid PDF page: {document_id}/{number}")
        page = self.pages[document_id]["pages"][number - 1]
        require(page["page"] == number and page["url"] == doc["url"] + f"#page={number}",
                f"Page position or URL mismatch: {document_id}/{number}")
        return doc, page

    def route(self, document_id: str, number: int) -> str:
        doc = self.documents[document_id]
        part = str(doc["chapter"]) if document_id in self.pilot_ids else document_id
        return f"page/{part}/{number:04d}"

    def evidence(self, document_id: str, number: int, *, route: str, url: str,
                 pdf_hash: str, page_hash: str, text: str | None = None,
                 text_hash: str | None = None, whole_page: bool = False) -> str:
        doc, page = self.source_page(document_id, number)
        require(route == self.route(document_id, number), f"Evidence route mismatch: {route}")
        require(url == page["url"] and pdf_hash == doc["sha256"], f"Evidence source identity: {route}")
        require(page_hash == digest(page["text"].encode()), f"Evidence page text hash: {route}")
        if text is not None:
            require(isinstance(text, str) and bool(text), f"Empty recorded evidence: {route}")
            require(text == page["text"] if whole_page else text in page["text"],
                    f"Evidence text is not at the cited page: {route}")
            require(text_hash == digest(text.encode()), f"Evidence quotation hash: {route}")
            self.counts["exact_evidence_text_checks"] += 1
        self.counts["evidence_identity_checks"] += 1
        return page["text"]

    def locator(self, text: str, locator: str | None) -> None:
        if locator is None:
            self.counts["page_evidence_without_numbered_locator"] += 1
            return
        require(isinstance(locator, str), "Invalid locator type")
        labels = re.findall(r"(?<!\d)\d{5,6}(?!\d)", locator)
        for label in labels:
            require(re.search(r"(?<!\d)" + re.escape(label) + r"(?!\d)", text) is not None,
                    f"Locator token missing from cited evidence: {locator}")
            self.counts["locator_token_presence_checks"] += 1
        # A literal occurrence is a navigation check, not proof of paragraph scope/meaning.

    def registry_case(self, case: dict) -> None:
        source = case["source_packet"]
        self.binding(source["path"], source["sha256"])
        packet = self.read(source["path"])
        require(packet.get("schema") == source["schema"], f"Original packet schema: {case['registry_id']}")
        original = pointer(packet, source["json_pointer"])
        require(original == case["original_case"], f"Original case pointer mismatch: {case['registry_id']}")
        require(digest(canonical(original)) == case["original_case_sha256"],
                f"Original case canonical hash: {case['registry_id']}")
        prompt = case["prompt"]
        require(pointer(self.read(prompt["path"]), prompt["json_pointer"]) == prompt["text"],
                f"Prompt pointer mismatch: {case['registry_id']}")
        require(digest(prompt["text"].encode()) == case["prompt_sha256"], f"Prompt hash: {case['registry_id']}")
        self.source_unit(case["source_unit"])
        require(case["candidate_binding"] is None and case["specialist_accepted"] is False,
                f"Unsupported registry promotion: {case['registry_id']}")
        require(case["observed_response"] is None and case["grade"] is None,
                f"Registry design substituted for observation: {case['registry_id']}")
        for ev in case["expected_evidence"]:
            require(pointer(packet, ev["declaration_pointer"]) == ev["declared"],
                    f"Expected-evidence pointer: {case['registry_id']}")
            identity = ev["source_identity"]
            document_id = identity["document_id"]
            number = int(ev["page"].rsplit("/", 1)[1])
            doc = self.documents[document_id]
            require(identity["source_pages_sha256"] == doc["pages_sha256"]
                    and identity["source_unit_id"] == self.units[doc["url"]]["id"],
                    f"Expected source identity: {case['registry_id']}")
            text = self.evidence(document_id, number, route=ev["page"], url=identity["source_url"],
                                 pdf_hash=identity["source_pdf_sha256"], page_hash=identity["page_text_sha256"],
                                 text=ev.get("quote"), text_hash=ev.get("quote_sha256"))
            if ev.get("locator"):
                self.locator(text, ev["locator"])
            for variant in ev.get("packet_quote_variants", []):
                original_ev = pointer(packet, variant["source_pointer"])
                require(original_ev["quote"] == variant["quote"], f"Quote pointer: {case['registry_id']}")
                require(variant["page"] == ev["page"] and variant["locator"] == ev["locator"],
                        f"Quote variant address: {case['registry_id']}")
                self.evidence(document_id, number, route=variant["page"], url=identity["source_url"],
                              pdf_hash=identity["source_pdf_sha256"], page_hash=identity["page_text_sha256"],
                              text=variant["quote"], text_hash=variant["quote_sha256"])
            self.counts["expected_evidence_pointer_checks"] += 1
        self.counts["registry_case_pointer_checks"] += 1

    def observed_case(self, case: dict, registry: dict, answer_field: str, hash_field: str) -> str:
        require(case["prompt"] == registry["prompt"]["text"]
                and case["prompt_sha256"] == registry["prompt_sha256"],
                f"Observed prompt differs: {case['case_id']}")
        response = case[answer_field]
        require(isinstance(response, str) and bool(response), f"Missing observed response: {case['case_id']}")
        require(digest(response.encode()) == case[hash_field], f"Observed response hash: {case['case_id']}")
        require(case.get("candidate_binding") is None, f"Unexpected runtime binding: {case['case_id']}")
        require(case.get("specialist_accepted", False) is False
                and case.get("individual_entitlement_decision", False) is False,
                f"Unsupported observed status: {case['case_id']}")
        if "source_unit" in case:
            require(case["source_unit"] == registry["source_unit"], f"Observed source unit: {case['case_id']}")
        self.counts["observed_prompt_response_checks"] += 1
        return case[hash_field]

    def comms_evidence(self, packet: dict, cases: dict) -> dict:
        records = unique(packet["evidence_records"], "id", "comms evidence")
        for ev in records.values():
            self.binding(ev["page_artifact_path"], ev["page_artifact_sha256"])
            source = self.read(ev["page_artifact_path"])
            require(source["document_id"] == ev["document_id"] and source["source_sha256"] == ev["pdf_sha256"],
                    f"Comms retained page identity: {ev['id']}")
            require(ev["source_role"] == self.documents[ev["document_id"]]["role"], f"Comms source role: {ev['id']}")
            text = self.evidence(ev["document_id"], ev["pdf_page"], route=ev["page_route"],
                                 url=ev["source_url"], pdf_hash=ev["pdf_sha256"], page_hash=ev["page_text_sha256"],
                                 text=ev["source_text"], text_hash=ev["page_text_sha256"], whole_page=True)
            require(source["pages"][ev["pdf_page"] - 1]["text"] == text, f"Comms retained page bytes: {ev['id']}")
            require(ev["document_publication_date"] is None, f"Unestablished publication date: {ev['id']}")
        for case in cases.values():
            cited_routes = {ref["page_route"] for ref in case["returned_evidence"]}
            for ref in case["returned_evidence"]:
                require(ref["evidence_id"] in records, f"Unknown evidence: {case['case_id']}")
                ev = records[ref["evidence_id"]]
                require(ref["page_route"] == ev["page_route"] and ref["source_url"] == ev["source_url"],
                        f"Returned evidence address: {case['case_id']}")
                for label in ref["paragraph_locators"]:
                    if "continuation" in label:
                        # The source does not repeat this paragraph label on its next page.
                        # Verify the adjacent cited context; do not invent a body anchor.
                        number = ev["pdf_page"]
                        require(number > 1 and self.route(ev["document_id"], number - 1) in cited_routes,
                                f"Continuation lacks adjacent cited context: {ref['page_route']}")
                        _, previous = self.source_page(ev["document_id"], number - 1)
                        self.locator(previous["text"], label)
                        self.counts["declared_continuation_context_checks"] += 1
                        self.observations.add(f"{ref['page_route']}: {label}; adjacent cited page has the label. The continuation's semantic extent is not established by replay.")
                    else:
                        self.locator(ev["source_text"], label)
        return records

    def personas_evidence(self, packet: dict, cases: dict) -> dict:
        for reader in packet["source_reader_versions"]:
            self.binding(reader["path"], reader["sha256"])
        records = unique(packet["evidence_records"], "id", "personas evidence")
        for ev in records.values():
            out = ev["output"]
            require(ev["arguments"]["path"] == self.documents[out["document_id"]]["pages_path"],
                    f"Source-read path: {ev['id']}")
            require(out["source_pages_sha256"] == self.documents[out["document_id"]]["pages_sha256"],
                    f"Source-read page artefact hash: {ev['id']}")
            require(out["source_role"] == self.documents[out["document_id"]]["role"], f"Source-read role: {ev['id']}")
            self.evidence(out["document_id"], ev["arguments"]["pdf_page"], route=out["route"],
                          url=out["source_url"], pdf_hash=out["source_pdf_sha256"], page_hash=out["page_text_sha256"],
                          text=out["excerpt"], text_hash=out["excerpt_sha256"])
        for case in cases.values():
            for ref in case["returned_evidence"]:
                require(ref["read_id"] in records, f"Unknown source read: {case['case_id']}")
                ev = records[ref["read_id"]]
                out = ev["output"]
                for key, other in (("excerpt_sha256", "excerpt_sha256"), ("page_route", "route"),
                                   ("page_text_sha256", "page_text_sha256"), ("pdf_sha256", "source_pdf_sha256"),
                                   ("source_url", "source_url"), ("source_role", "source_role")):
                    require(ref[key] == out[other], f"Returned read identity: {case['case_id']}: {key}")
                self.locator(out["excerpt"], ref["locator"])
                trace = ref["trace"]
                self.binding(trace["trace"], trace["trace_sha256"])
                reads = unique(self.read(trace["trace"])["reads"], "id", trace["trace"])
                require(trace["read_id"] == ref["read_id"] and reads[ref["read_id"]] == ev,
                        f"Retained trace differs: {case['case_id']}")
        return records

    def esa_evidence(self, packet: dict, cases: dict) -> dict:
        self.binding(INVENTORY, packet["inventory_sha256"])
        self.binding(EXPORT, packet["answerer_tasks_sha256"])
        require(packet["runtime_bundle_binding"] is None, "Unexpected ESA runtime binding")
        require(packet["case_count"] == len(cases), "ESA trial denominator")
        records = {}
        for case in cases.values():
            for ev in case["evidence"]:
                document_id = ev["route"].split("/")[1]
                number = int(ev["route"].rsplit("/", 1)[1])
                self.binding(ev["pages_path"], ev["pages_sha256"])
                require(ev["pages_path"] == self.documents[document_id]["pages_path"], "ESA evidence page path")
                self.evidence(document_id, number, route=ev["route"], url=ev["url"],
                              pdf_hash=ev["source_pdf_sha256"], page_hash=ev["page_text_sha256"],
                              text=ev["quote"], text_hash=ev["quote_sha256"])
                self.locator(ev["quote"], ev["locator"])
                records[ev["route"] + "#" + ev["quote_sha256"]] = ev
        return records

    def assessment_cases(self, name: str, packet: dict, observed: dict, evidence: dict) -> list[dict]:
        self.input_bindings(packet)
        cases = unique(packet["cases"], "case_id", name + " assessment")
        require(set(cases) == set(observed), f"Assessment denominator differs: {name}")
        results = []
        for case_id, case in sorted(cases.items()):
            trial = observed[case_id]
            response_hash = trial.get("response_sha256", trial.get("answer_sha256"))
            require(case.get("response_sha256", case.get("answer_sha256")) == response_hash,
                    f"Assessment response binding: {case_id}")
            if "prompt_sha256" in case:
                require(case["prompt_sha256"] == trial["prompt_sha256"], f"Assessment prompt binding: {case_id}")
            require(case.get("specialist_accepted", case.get("specialist_acceptance")) is False,
                    f"Unsupported specialist promotion: {case_id}")
            grade = case.get("outcome", case.get("assessment"))
            require(grade in GRADE_CATEGORIES, f"Unrecognised recorded grade: {case_id}: {grade}")
            for criterion in case.get("criteria", []):
                require(set(criterion.get("evidence_ids", [])) <= set(evidence), f"Assessment evidence IDs: {case_id}")
            require(set(case.get("source_evidence_ids", [])) <= set(evidence), f"Assessment source IDs: {case_id}")
            for ev in case.get("supplemental_grading_evidence", []):
                self.evidence(ev["document_id"], ev["pdf_page"], route=self.route(ev["document_id"], ev["pdf_page"]),
                              url=ev["url"], pdf_hash=ev["source_pdf_sha256"], page_hash=ev["page_text_sha256"],
                              text=ev["quote"], text_hash=ev["quote_sha256"])
                self.locator(ev["quote"], ev["locator"])
            results.append({"case_id": case_id, "prompt_sha256": trial["prompt_sha256"],
                            "response_sha256": response_hash, "recorded_grade": grade,
                            "summary_category": GRADE_CATEGORIES[grade],
                            "trial_packet": BASE + name + "-trials.json",
                            "assessment_packet": BASE + name + "-assessment.json",
                            "specialist_accepted": False})
            self.counts["assessment_response_bindings"] += 1
        declared = packet.get("counts", packet.get("summary", {}))
        require(declared.get("cases", declared.get("assessed", len(cases))) == len(cases), f"Declared assessment count: {name}")
        if "outcomes" in declared:
            require(declared["outcomes"] == dict(Counter(r["recorded_grade"] for r in results)), f"Declared outcome counts: {name}")
        if name == "esa":
            require(declared["meets_bounded_authored_case"] == sum(r["summary_category"] == "supported" for r in results)
                    and declared["partially_meets_authored_case"] == sum(r["summary_category"] == "partial" for r in results),
                    "Declared ESA outcome counts")
        return results

    def run(self) -> dict:
        self.file_hash("scripts/verify_full_dmg_trials.py")
        registry = self.read(REGISTRY)
        self.input_bindings(registry)
        cases = unique(registry["cases"], "registry_id", REGISTRY)
        require(len(cases) == registry["scope"]["cases"] == 160, "Expected 160 uniquely authored cases")
        require(Counter(c["batch"] for c in cases.values()) == registry["scope"]["by_batch"], "Registry batch denominators")
        require(Counter(c["kind"] for c in cases.values()) == registry["scope"]["by_kind"], "Registry kind denominators")
        source_units = {c["source_unit"]["id"] for c in cases.values()}
        require(source_units == {u["id"] for u in self.plan["source_units"] if u["classification"] == "chapter-current-listed"},
                "Registry does not cover the 78 substantive source units")
        for case in cases.values():
            self.registry_case(case)
        export = self.read(EXPORT)
        self.binding(REGISTRY, export["assessor_registry_sha256"])
        exported = unique(export["cases"], "case_id", EXPORT)
        require(set(exported) == set(cases) and export["case_count"] == 160, "Prompt-only export denominator")
        for case_id, exported_case in exported.items():
            require(exported_case["prompt"] == cases[case_id]["prompt"]["text"]
                    and exported_case["prompt_sha256"] == cases[case_id]["prompt_sha256"]
                    and exported_case["source_unit"] == cases[case_id]["source_unit"], f"Prompt export mismatch: {case_id}")
        all_observed = set()
        assessed = []
        packets = []
        for name in PACKETS:
            trial_path = BASE + name + "-trials.json"
            trial = self.read(trial_path)
            require(trial["schema"] == SCHEMAS[name][0], f"Unsupported trial schema: {name}")
            self.input_bindings(trial)
            observed = unique(trial["cases"], "case_id", trial_path)
            require(set(observed) <= set(cases), f"Unregistered observed case: {name}")
            require(not all_observed.intersection(observed), f"Duplicate observed case across packets: {name}")
            all_observed.update(observed)
            for case_id, case in observed.items():
                self.observed_case(case, cases[case_id], "answer" if name == "esa" else "observed_response",
                                   "answer_sha256" if name == "esa" else "response_sha256")
            evidence = getattr(self, name + "_evidence")(trial, observed)
            if name == "comms":
                self.binding(REGISTRY, trial["assessor_registry_sha256_from_export"])
                require(trial["candidate_binding"] is None, "Unexpected comms runtime binding")
            assessment_path = BASE + name + "-assessment.json"
            assessment = self.read(assessment_path)
            require(assessment["schema"] == SCHEMAS[name][1], f"Unsupported assessment schema: {name}")
            require(any(row["path"] == trial_path and row["sha256"] == self.file_hash(trial_path)
                        for row in assessment["inputs"]), f"Assessment must bind exact trial packet: {name}")
            rows = self.assessment_cases(name, assessment, observed, evidence)
            assessed.extend(rows)
            packets.append({"name": name, "trial_schema": trial["schema"], "assessment_schema": assessment["schema"],
                            "observed_cases": len(observed), "assessed_cases": len(rows),
                            "retained_evidence_records": len(evidence),
                            "recorded_grades": dict(sorted(Counter(r["recorded_grade"] for r in rows).items())),
                            "summary_categories": dict(sorted(Counter(r["summary_category"] for r in rows).items()))})
        require(all_observed == set(cases), "Observed trials do not cover all 160 registry cases")
        unique(assessed, "case_id", "combined assessments")
        self.counts["distinct_source_documents_checked"] = len(self.pages)
        # Fail if any shared input changed during this bounded replay.
        for path, value in self.inputs.items():
            require(digest(self.path(path).read_bytes()) == value, f"Input changed during replay: {path}")
        summary = {
            "schema": "okf-dwp-source-trial-replay-summary.v1",
            "status": "passed-mechanical-replay; recorded-partials-and-rubric-gaps-retained",
            "method": "Recompute retained file/text hashes, resolve original JSON pointers, reconcile unique case denominators, check exact frozen evidence and aggregate the supplied assessment labels. No model call, answer regeneration or semantic grading is performed.",
            "inputs": [{"path": path, "sha256": value} for path, value in sorted(self.inputs.items())],
            "scope": {"registry_cases": len(cases), "substantive_source_units": len(source_units),
                      "observed_responses": len(all_observed), "recorded_assessments": len(assessed),
                      "source_grounding_cases": sum(c["kind"] == "source-grounding" for c in cases.values()),
                      "boundary_control_cases": sum(c["kind"] == "boundary-control" for c in cases.values()),
                      "specialist_accepted": 0, "live_runtime_verified": 0},
            "recorded_outcomes": dict(sorted(Counter(r["summary_category"] for r in assessed).items())),
            "recorded_grade_labels": dict(sorted(Counter(r["recorded_grade"] for r in assessed).items())),
            "grade_category_mapping": GRADE_CATEGORIES,
            "mechanical_checks": dict(sorted(self.counts.items())),
            "citation_observations": sorted(self.observations),
            "packets": packets,
            "cases": sorted(assessed, key=lambda c: c["case_id"]),
            "unmeasured": {"runtime_bundle_binding": None, "provider_model_version": None,
                           "comparative_model_accuracy": None, "token_usage": None, "cost": None,
                           "end_to_end_latency": None, "specialist_acceptance": None},
            "limitations": [
                "The grades are preserved independent-model judgements from the cited assessment packets, not grades calculated by this verifier or a specialist gold standard.",
                "Supported, partial and underspecified labels have different original schemas. The mapping retains each original label; underspecified is not counted as fully supported.",
                "Authoring and response contexts were exposed to source/review material. These are context-aware raw-source trials, not blind hold-outs, independent samples or a comparative model benchmark.",
                "Exact text and locator-token checks do not establish the meaning, completeness, applicability or currency of a paragraph. Full-page and excerpt evidence retain different precision.",
                "The prompt-only export, original authored exemplars, read traces, observed responses and assessments remain distinct. A read trace or authored exemplar is not an observed answer.",
                "Runtime candidate binding is null: no Explorer, browser, WebMCP or live-voice execution is proven by this replay.",
                "No new timestamps are generated. Earlier observation/recording times remain in their original hash-bound packets; no absent model identity, cost or timing is inferred.",
                "The denominator is the 160 authored behavioural cases across 78 substantive units. Baseline route and family navigation checks are separate evidence and are not added to this count.",
            ],
        }
        return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify the retained summary is exactly reproducible; do not write it")
    args = parser.parse_args()
    try:
        summary = TrialReplay().run()
        expected = canonical(summary)
        target = ROOT / OUTPUT
        if args.check:
            require(target.exists() and target.read_bytes() == expected,
                    f"Replay summary is absent or stale: run python scripts/verify_full_dmg_trials.py")
        else:
            target.write_bytes(expected)
        counts = summary["recorded_outcomes"]
        print(f"Verified 160 observed responses and assessments: {counts}. Mechanical replay only.")
        return 0
    except (ValueError, KeyError, IndexError, OSError, TypeError) as exc:
        print(f"Trial replay failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
