#!/usr/bin/env python3
"""Paired, fixed-public-evidence subscription trials; default is offline replay.

No API keys are read or configured. CLI authentication remains with each provider.
Only allow-listed model output, numeric usage and sanitised event categories are
retained. Shell, web, MCP and other model tools are disabled for actual calls.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

from jsonschema import ValidationError
from evaluate_fixed_answers import assess

RUNNING_HARNESS_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "evaluation/model-comparison/staff-2026-09-20"
OUT = ROOT / "validation/model-comparison/staff-2026-09-20"
SCHEMA = ROOT / "evaluation/answer-review/answer.schema.json"
TIMEOUT = 240
FEATURES = ["shell_tool", "unified_exec", "apps", "multi_agent", "memories", "hooks", "remote_plugin"]
TOOL_ITEMS = {"command_execution", "file_change", "mcp_tool_call", "web_search", "collab_tool_call", "tool_call", "function_call"}
USAGE_FIELDS = {"input_tokens", "output_tokens", "cached_input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens",
                "cache_creation", "ephemeral_5m_input_tokens", "ephemeral_1h_input_tokens", "server_tool_use", "web_search_requests",
                "web_fetch_requests", "inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens", "costUSD",
                "contextWindow", "maxOutputTokens", "input_tokens_details", "cached_tokens", "output_tokens_details", "reasoning_tokens"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def numerical(value):
    """Retain only numeric accounting, never arbitrary strings or session IDs."""
    if isinstance(value, dict):
        return {k: numerical(v) for k, v in value.items() if k in USAGE_FIELDS and isinstance(v, (dict, int, float)) and not isinstance(v, bool)}
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return None


def parse_answer(text):
    value = text.strip()
    if value.startswith("```json") and value.endswith("```"):
        value = value[7:-3].strip()
    elif value.startswith("```") and value.endswith("```"):
        value = value[3:-3].strip()
    return json.loads(value)


def sanitise_claude(stdout):
    # Stream JSON permits an actual tool-event census without publishing COT,
    # environment initialisation, account details, stderr or session identifiers.
    events = [json.loads(line) for line in stdout.splitlines() if line.strip()]
    final = next((e for e in reversed(events) if e.get("type") == "result"), None)
    if final is None and len(events) == 1:
        final = events[0]
    if not final:
        raise ValueError("No final provider result")
    tool_names, tool_events, models = [], [], set()
    for event in events:
        message = event.get("message", {})
        if isinstance(message, dict):
            if isinstance(message.get("model"), str):
                models.add(message["model"])
            for part in message.get("content", []):
                if isinstance(part, dict) and part.get("type") == "tool_use":
                    tool_names.append(part.get("name", "unknown"))
                    tool_events.append({"name": part.get("name", "unknown"), "input_sha256": sha(encoded(part.get("input", {})))})
    usage = {name: numerical(data) for name, data in final.get("modelUsage", {}).items()}
    models.update(usage)
    allowed = {"provider_result": final.get("result"), "structured_output": final.get("structured_output"),
               "is_error": bool(final.get("is_error")), "usage": numerical(final.get("usage", {})),
               "model_usage": usage, "reported_models": sorted(models), "tool_event_names": tool_names,
               "tool_events": tool_events,
               "event_count": len(events)}
    for key in ["duration_ms", "duration_api_ms", "num_turns", "total_cost_usd"]:
        if isinstance(final.get(key), (int, float)):
            allowed[key] = final[key]
    return allowed


def sanitise_codex(stdout):
    events = [json.loads(line) for line in stdout.splitlines() if line.strip()]
    messages, tool_events, models = [], [], set()
    usage, errors, shortened = {}, 0, False
    for event in events:
        if isinstance(event.get("model"), str):
            models.add(event["model"])
        if event.get("type") == "turn.completed":
            usage = numerical(event.get("usage", {}))
        if event.get("type") == "error":
            errors += 1
            if "skill" in str(event).lower() and "shorten" in str(event).lower():
                shortened = True
        item = event.get("item", {})
        if item.get("type") in TOOL_ITEMS:
            tool_events.append(item["type"])
        if event.get("type") == "item.completed" and item.get("type") == "agent_message":
            messages.append(item.get("text", ""))
    return {"provider_result": messages[-1] if messages else None, "usage": usage,
            "reported_models": sorted(models), "tool_event_names": tool_events,
            "event_count": len(events), "error_event_count": errors,
            "skill_description_shortening_observed": shortened,
            "model_identity_status": "reported" if models else "not-exposed-in-retained-CLI-events"}


def mechanical(answer, context):
    try:
        result = assess(answer, context)
    except (ValidationError, KeyError, TypeError) as error:
        return {"status": "failed-mechanical-controls", "failures": ["answer_schema_invalid"],
                "claims": 0, "citations_checked": 0, "schema_error_type": type(error).__name__,
                "specialist_accepted": False, "entailment_review": "pending-independent-human-review"}
    if context["budget"]["truncated"] and not re.search(r"\btruncat(?:ed|ion)\b", answer["summary"], re.I):
        result["failures"].append("package_truncation_not_explicit_in_summary")
        result["status"] = "failed-mechanical-controls"
    return result


def forbidden_tool_events(provider, output, protocol):
    allowed = protocol.get("allowed_formatting_events", {}).get(provider, [])
    # The only supported exception is an output-formatting facility, never an
    # arbitrary name supplied by an evidence package or provider response.
    if any(name != "StructuredOutput" or provider != "claude-subscription" for name in allowed):
        raise ValueError("Unsupported tool-policy exception")
    return [name for name in output.get("tool_event_names", []) if name not in allowed]


def safe_environment():
    # Existing subscription authentication is managed by the CLI. Do not pass
    # ambient API credentials or nested-agent/session overrides into these calls.
    return {key: value for key, value in os.environ.items()
            if key not in {"OPENAI_API_KEY", "ANTHROPIC_API_KEY", "CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT"}}


def skill_overrides():
    paths = set()
    for root in [Path.home() / ".codex/skills", Path.home() / ".agents/skills"]:
        if root.is_dir():
            paths.update(str(p.resolve()) for p in root.rglob("SKILL.md"))
    # Process-local documented overrides. No user file is changed. The entries
    # themselves contain machine paths and are never included in public receipts.
    value = "[" + ",".join("{path=" + json.dumps(p) + ",enabled=false}" for p in sorted(paths)) + "]"
    return value, len(paths)


def command(provider, directory, system, schema):
    if provider == "claude-subscription":
        binary = shutil.which("claude")
        if not binary:
            raise FileNotFoundError("Claude CLI unavailable")
        args = [binary, "--safe-mode", "--print", "--tools", "", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                "--no-chrome", "--disable-slash-commands", "--no-session-persistence", "--permission-mode", "dontAsk",
                "--output-format", "stream-json", "--verbose", "--system-prompt", system, "--json-schema", schema]
        return args, {"skills_policy": "disabled-safe-mode-and-slash-commands", "customisations": "disabled-safe-mode"}
    binary = shutil.which("codex")
    if not binary:
        raise FileNotFoundError("Codex CLI unavailable")
    system_path = Path(directory) / "system-prompt.txt"
    system_path.write_text(system)
    schema_path = Path(directory) / "answer.schema.json"
    schema_path.write_text(schema)
    overrides, count = skill_overrides()
    args = [binary, "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral", "--skip-git-repo-check",
            "--sandbox", "read-only", "-C", directory]
    for feature in FEATURES:
        args += ["--disable", feature]
    for setting in ['agents.enabled=false', 'web_search="disabled"', 'project_doc_max_bytes=0',
                    'approval_policy="never"', "skills.config=" + overrides,
                    "model_instructions_file=" + json.dumps(str(system_path))]:
        args += ["-c", setting]
    args += ["--json", "--output-schema", str(schema_path), "-"]
    return args, {"skills_policy": "process-local-disabled-for-discovered-user-skill-paths",
                  "disabled_skill_path_count": count, "customisations": "user-config-rules-project-docs-and-listed-features-disabled",
                  "limitation": "Host/system additions may still differ; absence of a warning is not proof of identical provider system context."}


def fixed_input(case, manifest, protocol):
    path = (ROOT / case["path"]).resolve()
    if not path.is_relative_to(SPEC / "contexts"):
        raise ValueError("Fixed input outside declared public trial contexts")
    raw = path.read_bytes()
    if sha(raw) != case["sha256"] or len(raw) != case["bytes"]:
        raise ValueError("Fixed context digest or size differs")
    context = json.loads(raw)
    if len(raw) > protocol["context_budget"]["max_bytes"] or context["context_id"] != case["context_id"] or context["ai_answer"] is not None:
        raise ValueError("Unexpected governed trial context")
    system = (SPEC / protocol["system_prompt"]).read_text()
    prompt = (SPEC / protocol["user_prompt"]).read_text().replace("{{CONTEXT_JSON}}", raw.decode())
    schema = SCHEMA.read_text()
    binding = {"context_path": case["path"], "context_sha256": sha(raw), "context_id": context["context_id"], "context_bytes": len(raw),
               "system_prompt_sha256": sha(system.encode()), "prompt_sha256": sha(prompt.encode()), "schema_sha256": sha(schema.encode()),
               "protocol_sha256": sha((SPEC / "protocol.json").read_bytes()), "context_manifest_sha256": sha((SPEC / "contexts.json").read_bytes())}
    return context, system, prompt, schema, binding


def run_one(provider, case, manifest, protocol, attempt, run):
    context, system, prompt, schema, binding = fixed_input(case, manifest, protocol)
    out = OUT / provider / case["id"] / attempt
    receipt_path = out / "receipt.json"
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt["inputs"] != binding:
            # A preregistered policy amendment may leave exact evidence and
            # authored prompts unchanged. Verify historical public protocol and
            # context-manifest bytes, rather than reinterpreting the old attempt.
            old = receipt["inputs"]
            mutable = {"protocol_sha256", "context_manifest_sha256"}
            if {k:v for k,v in old.items() if k not in mutable} != {k:v for k,v in binding.items() if k not in mutable}:
                raise ValueError("Existing attempt has different fixed evidence or prompt; use a new attempt")
            for key in mutable:
                snapshot = SPEC / "input-snapshots" / (old[key] + ".json")
                if not snapshot.exists() or sha(snapshot.read_bytes()) != old[key]:
                    raise ValueError("Historical input snapshot absent or changed")
        for name, expected in receipt["artefacts"].items():
            if sha((out / name).read_bytes()) != expected:
                raise ValueError("Trial artefact hash differs: " + name)
        if receipt.get("answer_present"):
            assessment = mechanical(json.loads((out / "answer.json").read_text()), context)
            if assessment != receipt["mechanical_assessment"]:
                raise ValueError("Retained mechanical result differs")
        return receipt
    if not run:
        raise ValueError("No retained attempt for " + provider + "/" + case["id"])
    if out.exists():
        raise ValueError("Unfinished attempt already exists; preserve it and choose a new attempt ID")
    out.mkdir(parents=True)
    started = datetime.now(timezone.utc).isoformat()
    tick = time.monotonic()
    receipt = {"schema": "okf-paired-staff-model-attempt.v1", "provider": provider, "case_id": case["id"], "attempt": attempt,
               "started_at": started, "inputs": binding, "harness_sha256": RUNNING_HARNESS_SHA,
               "model_override": None, "tools_requested": [], "mcp_servers": [], "human_review": "pending",
               "comparative_accuracy_or_affordability_established": False, "answer_present": False,
               "cost_boundary": "Provider usage and cost accounting are not verified subscription charges, future pricing, savings or human review costs.",
               "artefacts": {}}
    def retain(name, value):
        data = encoded(value)
        (out / name).write_bytes(data)
        receipt["artefacts"][name] = sha(data)
    try:
        with tempfile.TemporaryDirectory(prefix="okf-fixed-staff-trial-") as directory:
            args, controls = command(provider, directory, system, schema)
            receipt["isolation"] = controls
            version = subprocess.run([args[0], "--version"], text=True, capture_output=True, timeout=10)
            receipt["cli_version"] = version.stdout.strip().splitlines()[0][:100] if version.stdout.strip() else "not-observed"
            completed = subprocess.run(args, input=prompt, text=True, capture_output=True, cwd=directory,
                                       env=safe_environment(), timeout=TIMEOUT)
        receipt["exit_code"] = completed.returncode
        receipt["stdout_sha256"] = sha(completed.stdout.encode())
        receipt["stderr_sha256"] = sha(completed.stderr.encode())
        model_output = sanitise_claude(completed.stdout) if provider == "claude-subscription" else sanitise_codex(completed.stdout)
        retain("model-output.json", model_output)
        receipt["observed_tool_events"] = model_output.get("tool_event_names", [])
        receipt["formatting_events"] = [e for e in model_output.get("tool_events", []) if e["name"] == "StructuredOutput"]
        receipt["reported_models"] = model_output.get("reported_models", [])
        receipt["usage"] = model_output.get("usage", {})
        if completed.returncode or model_output.get("is_error"):
            receipt["status"] = "provider-call-failed"
        elif forbidden_tool_events(provider, model_output, protocol):
            receipt["status"] = "rejected-observed-tool-event"
        else:
            answer = model_output.get("structured_output")
            if answer is None:
                answer = parse_answer(model_output.get("provider_result") or "")
            retain("answer.json", answer)
            receipt["answer_present"] = True
            receipt["mechanical_assessment"] = mechanical(answer, context)
            receipt["status"] = "actual-model-response-retained"
    except subprocess.TimeoutExpired:
        receipt["status"] = "provider-timeout"
        receipt["timeout_seconds"] = TIMEOUT
    except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError) as error:
        receipt["status"] = "provider-or-output-error"
        receipt["error_category"] = type(error).__name__
        # Error text may contain local paths or authentication details. Retain
        # only its category; never copy raw stderr into this public repository.
    receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
    receipt["elapsed_seconds"] = round(time.monotonic() - tick, 3)
    receipt_path.write_bytes(encoded(receipt))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--provider", choices=["claude-subscription", "codex-subscription"])
    parser.add_argument("--case")
    parser.add_argument("--attempt", default="attempt-01")
    parser.add_argument("--report", action="store_true", help="Verify every retained attempt and write the deterministic paired-results ledger")
    parser.add_argument("--check-report", action="store_true", help="With --report, verify the ledger without rewriting it")
    args = parser.parse_args()
    if not re.fullmatch(r"attempt-[0-9]{2}", args.attempt):
        parser.error("Use an explicit attempt-NN identity")
    protocol = json.loads((SPEC / "protocol.json").read_text())
    manifest = json.loads((SPEC / "contexts.json").read_text())
    if args.case and args.case not in protocol["selected_cases"]:
        parser.error("Case is not preregistered")
    if manifest["inputs"]["protocol_sha256"] != sha((SPEC / "protocol.json").read_bytes()):
        raise ValueError("Protocol changed after context export")
    if args.report:
        results = []
        cases = {case["id"]:case for case in manifest["cases"]}
        for file in sorted(OUT.glob("*/*/attempt-*/receipt.json")):
            provider, case_id, attempt = file.parts[-4:-1]
            if provider not in protocol["providers"] or case_id not in cases:
                raise ValueError("Unregistered trial output")
            receipt = run_one(provider, cases[case_id], manifest, protocol, attempt, False)
            results.append({"provider":provider,"case_id":case_id,"attempt":attempt,
                            "receipt":str(file.relative_to(ROOT)),"receipt_sha256":sha(file.read_bytes()),
                            "status":receipt["status"],"reported_models":receipt.get("reported_models", []),
                            "elapsed_seconds":receipt["elapsed_seconds"],"usage":receipt.get("usage", {}),
                            "mechanical_assessment":receipt.get("mechanical_assessment"),
                            "observed_tool_events":receipt.get("observed_tool_events"),
                            "tool_event_census_status":"retained" if "observed_tool_events" in receipt else "not-retained-for-failed-attempt",
                            "context_sha256":receipt["inputs"]["context_sha256"],
                            "authored_prompt_sha256":receipt["inputs"]["prompt_sha256"]})
        paired = []
        for case in manifest["cases"]:
            entries = [r for r in results if r["case_id"] == case["id"] and r["status"] == "actual-model-response-retained"]
            chosen = {p:next((r for r in reversed(entries) if r["provider"] == p),None) for p in protocol["providers"]}
            comparable = all(chosen.values())
            if comparable and (len({r["context_sha256"] for r in chosen.values()}) != 1 or len({r["authored_prompt_sha256"] for r in chosen.values()}) != 1):
                raise ValueError("Paired inputs differ")
            paired.append({"case_id":case["id"],"both_responses_retained":comparable,
                           "attempts":{p:r["attempt"] if r else None for p,r in chosen.items()},
                           "same_public_context_and_authored_prompt":comparable})
        report = {"schema":"okf-paired-staff-results.v1","protocol_sha256":sha((SPEC/"protocol.json").read_bytes()),
                  "context_manifest_sha256":sha((SPEC/"contexts.json").read_bytes()),"attempts":results,"pairs":paired,
                  "human_review":"pending","specialist_accepted":False,"comparative_accuracy_or_affordability_established":False,
                  "limitations":["Matching quotations and source locators do not establish entailment or complete legal qualifications.",
                                 "The authored public inputs are identical; provider wrappers, host instructions and model defaults can differ.",
                                 "Retain every failure and retry; usage accounting is not verified subscription pricing."]}
        OUT.mkdir(parents=True,exist_ok=True)
        if args.check_report:
            if (OUT/"results.json").read_bytes() != encoded(report):
                raise ValueError("Paired-results ledger differs")
        else:
            (OUT/"results.json").write_bytes(encoded(report))
        print(json.dumps({"attempts":len(results),"paired_cases":sum(p["both_responses_retained"] for p in paired)}))
        return
    for case in manifest["cases"]:
        if args.case and case["id"] != args.case:
            continue
        for provider in protocol["providers"]:
            if args.provider and provider != args.provider:
                continue
            result = run_one(provider, case, manifest, protocol, args.attempt, args.run)
            print(json.dumps({"case": case["id"], "provider": provider, "status": result["status"],
                              "mechanical": result.get("mechanical_assessment", {}).get("status"),
                              "elapsed_seconds": result["elapsed_seconds"]}), flush=True)


if __name__ == "__main__":
    main()
