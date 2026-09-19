#!/usr/bin/env python3
"""Offline integrity and quotation diagnosis for the retained model baseline."""
import hashlib
import json
from pathlib import Path
import re

from evaluate_fixed_answers import DEFAULT_OUTPUT, SPEC, assess, load_case


def diagnose():
    results = []
    for case in json.loads((SPEC / "cases.json").read_text())["cases"]:
        root = DEFAULT_OUTPUT / case["id"]
        receipt = json.loads((root / "receipt.json").read_text())
        for path, digest in [("answer.json", receipt["answer_sha256"]), ("model-output.json", receipt["model_output_sha256"]),
                             ("prompt.txt", receipt["inputs"]["prompt_sha256"]),
                             ("system-prompt.txt", receipt["inputs"]["system_prompt_sha256"]),
                             ("input.context.json", receipt["inputs"]["context_sha256"])]:
            if hashlib.sha256((root / path).read_bytes()).hexdigest() != digest:
                raise ValueError(f"Retained {case['id']} {path} digest differs")
        _, context = load_case(case)
        answer = json.loads((root / "answer.json").read_text())
        if assess(answer, context) != receipt["mechanical_assessment"]:
            raise ValueError("Recorded mechanical outcome differs")
        records = {item["record"]["id"]: item["record"] for item in context["selected"]}
        normalise = lambda value: re.sub(r"\s+", " ", value).strip()
        citations = []
        for claim in answer["claims"]:
            for position, evidence in enumerate(claim["evidence"]):
                text = records.get(evidence["record_id"], {}).get("text", "")
                exact = evidence["quote"] in text
                whitespace = normalise(evidence["quote"]) in normalise(text)
                citations.append({"claim_id": claim["id"], "citation_index": position, "record_id": evidence["record_id"],
                                  "exact": exact, "matches_after_whitespace_only_normalisation": whitespace,
                                  "entailment": "not-assessed"})
        results.append({"id": case["id"], "strict_result": receipt["mechanical_assessment"]["status"], "citations": citations})
    diagnosis = {"schema": "okf-model-quotation-diagnosis.v1", "method": "Exact substring, then Unicode whitespace runs replaced by one ASCII space and ends stripped; no other text normalisation.",
                 "scope": "Diagnostic only; does not replace strict trial outcomes, establish entailment or constitute human review.", "cases": results}
    return diagnosis


def main():
    diagnosis = diagnose()
    expected = DEFAULT_OUTPUT / "quotation-diagnosis.json"
    if json.loads(expected.read_text()) != diagnosis:
        raise ValueError("Retained quotation diagnosis differs")
    print(json.dumps({"status": "retained-model-artefacts-and-diagnosis-verified", "cases": len(diagnosis["cases"]),
                      "model_calls": 0, "human_review": "pending", "strict_failures_preserved": True}))


if __name__ == "__main__":
    main()
