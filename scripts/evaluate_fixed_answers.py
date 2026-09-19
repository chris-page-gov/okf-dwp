#!/usr/bin/env python3
"""Bounded, tools-disabled Claude trials over an allow-listed public package set."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "evaluation/answer-review"
DEFAULT_OUTPUT = ROOT / "validation/answer-review/claude-baseline-2026-09-19"
CLAUDE = Path(shutil.which("claude") or Path.home() / ".local/bin/claude")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def load_case(case):
    path = (ROOT / case["path"]).resolve()
    if not path.is_relative_to(ROOT / "validation"):
        raise ValueError("Only declared public validation packages are permitted")
    raw = path.read_bytes()
    if sha(raw) != case["source_sha256"]:
        raise ValueError("Fixed input digest differs")
    if case["format"] == "context-json":
        context_raw = raw
    else:
        # Declared, digest-checked local archives only; never arbitrary URLs.
        decoded = gzip.decompress(raw)
        if len(decoded) > 2_000_000:
            raise ValueError("Retained transport exceeds trial limit")
        if case["format"] == "tool-result-gzip":
            tool = json.loads(decoded)
        elif case["format"] == "sse-gzip":
            events = [json.loads(line[5:].strip()) for line in decoded.decode().splitlines() if line.startswith("data:")]
            results = [event["result"] for event in events if "result" in event]
            if len(results) != 1:
                raise ValueError("Expected one retained tool result")
            tool = results[0]
        else:
            raise ValueError("Unknown fixed input representation")
        texts = [item["text"] for item in tool["content"] if item.get("type") == "text"]
        if len(texts) != 1 or json.loads(texts[0]) != tool["structuredContent"]:
            raise ValueError("Retained text and structured package differ")
        context_raw = texts[0].encode()
    context = json.loads(context_raw)
    if (context.get("schema") != "okf-governed-context.v1" or context.get("ai_answer") is not None
            or context["evidence_status"] != case["expected_package_status"]):
        raise ValueError("Unexpected fixed context contract")
    return context_raw, context


def assess(answer, context):
    """Structural and literal checks only: quoted text can still mis-support a claim."""
    Draft202012Validator(json.loads((SPEC / "answer.schema.json").read_text())).validate(answer)
    failures = []
    if answer["context_id"] != context["context_id"]:
        failures.append("wrong_context_id")
    if answer["package_evidence_status"] != context["evidence_status"]:
        failures.append("altered_evidence_status")
    if context["evidence_status"] != "sufficient" and answer["answer_disposition"] == "bounded_source_answer":
        failures.append("unsupported_complete_disposition")
    selected = {item["record"]["id"]: item["record"] for item in context["selected"]}
    if not selected and (answer["claims"] or answer["answer_disposition"] != "cannot_establish"):
        failures.append("no_evidence_abstention_failed")
    if len({claim["id"] for claim in answer["claims"]}) != len(answer["claims"]):
        failures.append("duplicate_claim_id")
    checked = 0
    for claim in answer["claims"]:
        for evidence in claim["evidence"]:
            record = selected.get(evidence["record_id"])
            if record is None:
                failures.append(f"{claim['id']}:unknown_record")
                continue
            if evidence["quote"] not in record.get("text", ""):
                failures.append(f"{claim['id']}:quote_not_verbatim")
            if not any(evidence["source_url"] == provenance.get("url") and evidence["locator"] == provenance.get("locator")
                       for provenance in record.get("provenance", [])):
                failures.append(f"{claim['id']}:source_locator_not_in_package")
            checked += 1
    return {"status": "passed-mechanical-controls" if not failures else "failed-mechanical-controls",
            "failures": failures, "claims": len(answer["claims"]), "citations_checked": checked,
            "entailment_review": "pending-independent-human-review", "unsupported_claim_rate": None,
            "answer_quality_score": None, "specialist_accepted": False,
            "limitation": "Exact quotation, identifier and boundary checks do not establish that the cited passage entails the claim or that conditions and exceptions are complete."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Make subscription calls; default checks retained results only")
    parser.add_argument("--case", choices=["abroad", "custody", "unsupported"])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    cases = json.loads((SPEC / "cases.json").read_text())
    system = (SPEC / "system-prompt.txt").read_text()
    template = (SPEC / "user-prompt.txt").read_text()
    schema_raw = (SPEC / "answer.schema.json").read_text()
    results = []
    for case in cases["cases"]:
        if args.case and case["id"] != args.case:
            continue
        context_raw, context = load_case(case)
        if len(context_raw) > cases["max_context_bytes"]:
            raise ValueError("Fixed context exceeds the declared whole-package budget")
        prompt = template.replace("{{CONTEXT_JSON}}", context_raw.decode())
        binding = {"source_path": case["path"], "source_sha256": case["source_sha256"],
                   "context_sha256": sha(context_raw), "context_bytes": len(context_raw), "context_id": context["context_id"],
                   "system_prompt_sha256": sha(system.encode()), "prompt_sha256": sha(prompt.encode()),
                   "schema_sha256": sha(schema_raw.encode()), "harness_sha256": sha(Path(__file__).read_bytes())}
        out = args.output / case["id"]
        receipt_path = out / "receipt.json"
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text())
            if receipt["inputs"] != binding:
                raise ValueError("Existing attempt has different inputs; choose a new output directory")
            if sha((out / "answer.json").read_bytes()) != receipt["answer_sha256"]:
                raise ValueError("Retained answer digest differs")
            assessment = assess(json.loads((out / "answer.json").read_text()), context)
            if assessment != receipt["mechanical_assessment"]:
                raise ValueError("Retained assessment differs")
            results.append({"id": case["id"], "mode": "offline-replay", "assessment": assessment})
            continue
        if not args.run:
            raise ValueError(f"No retained trial for {case['id']}; --run explicitly opts into subscription calls")
        if out.exists():
            raise ValueError("Unfinished attempt directory exists; preserve it and choose a new output directory")
        out.mkdir(parents=True)
        (out / "prompt.txt").write_text(prompt)
        (out / "system-prompt.txt").write_text(system)
        (out / "input.context.json").write_bytes(context_raw)
        command = [str(CLAUDE), "--safe-mode", "--print", "--tools", "", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                   "--no-chrome", "--disable-slash-commands", "--no-session-persistence", "--permission-mode", "dontAsk",
                   "--output-format", "json", "--system-prompt", system, "--json-schema", schema_raw]
        started = datetime.now(timezone.utc).isoformat()
        start = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="okf-public-answer-trial-") as directory:
            completed = subprocess.run(command, input=prompt, text=True, capture_output=True, cwd=directory, timeout=180)
        response = json.loads(completed.stdout)
        # Only model outputs and numeric usage metadata; omit session/account IDs,
        # private configuration, stderr and local authentication information.
        allowed = {key: response[key] for key in ["result", "structured_output", "is_error", "subtype", "usage", "modelUsage",
                   "duration_ms", "duration_api_ms", "num_turns", "stop_reason", "total_cost_usd"] if key in response}
        (out / "model-output.json").write_bytes(encoded(allowed))
        if completed.returncode or response.get("is_error"):
            (out / "failure.json").write_bytes(encoded({"status": "model-call-failed", "exit_code": completed.returncode,
                                                       "inputs": binding, "started_at": started}))
            raise ValueError(f"Claude trial failed for {case['id']}; no automatic retry")
        answer = response.get("structured_output")
        if answer is None:
            answer = json.loads(response["result"])
        (out / "answer.json").write_bytes(encoded(answer))
        assessment = assess(answer, context)
        receipt = {"schema": "okf-fixed-model-answer-trial.v1", "id": case["id"], "started_at": started,
                   "finished_at": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": round(time.monotonic()-start, 3),
                   "provider_surface": "existing Claude Code subscription", "cli_version": subprocess.check_output([str(CLAUDE),"--version"],text=True).strip(),
                   "model_override": None, "reported_model_usage_entries": list(response.get("modelUsage", {})),
                   "tools_enabled": [], "mcp_servers": [], "customisations": "disabled-safe-mode", "session_persistence": False,
                   "inputs": binding, "answer_sha256": sha((out / "answer.json").read_bytes()),
                   "model_output_sha256": sha((out / "model-output.json").read_bytes()), "mechanical_assessment": assessment,
                   "human_review": "pending", "comparative_benchmark": False,
                   "cost_boundary": "Any CLI cost field is provider-reported accounting, not a verified subscription charge or saving. No price or model configuration was changed."}
        receipt_path.write_bytes(encoded(receipt))
        results.append({"id": case["id"], "mode": "actual-model-call", "assessment": assessment})
        print(json.dumps(results[-1]), flush=True)
    if not args.run:
        print(json.dumps({"status": "offline-replay-complete", "cases": results}))


if __name__ == "__main__":
    main()
