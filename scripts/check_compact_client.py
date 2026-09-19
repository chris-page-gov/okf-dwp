#!/usr/bin/env python3
"""Offline verification of retained local client bytes; no model or network calls."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation/compact-client"
CONTEXT = ROOT / "validation/corpus-questions/bounded-abroad/context.json"
EXPECTED_CONTEXT_SHA = "f997c8147987c69960030e2cba717b7d9106b301c749fdb22b07ee1d75f8a932"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def units(text):
    return len(text.encode("utf-16-le")) // 2


def checked_file(root, item):
    path = (root / item["path"]).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("Capture path is absent or outside its observation")
    raw = path.read_bytes()
    if len(raw) != item["bytes"] or digest(raw) != item["sha256"]:
        raise ValueError("Captured bytes differ from the observation")
    return raw


def message(raw):
    if raw.lstrip().startswith(b"{"):
        return json.loads(raw)
    events = [json.loads(line[5:].strip()) for line in raw.decode().splitlines() if line.startswith("data:")]
    if len(events) != 1:
        raise ValueError("Expected one recorded JSON-RPC response")
    return events[0]


def verify():
    raw = CONTEXT.read_bytes()
    if digest(raw) != EXPECTED_CONTEXT_SHA:
        raise ValueError("Frozen comparison context bytes differ")
    context = json.loads(raw)
    by_id = {item["record"]["id"]: item for item in context["selected"]}
    results = []
    for name in ["claude-local-2026-09-19", "claude-local-explicit-mcp-2026-09-19"]:
        root = BASE / name
        observation_raw = (root / "observation.json").read_bytes()
        observation = json.loads(observation_raw)
        for path, item in observation["files"].items():
            checked_file(root, {"path": path, **item})
        if observation["builtin_tools"] or observation["model_override"] is not None or observation["session_persistence"]:
            raise ValueError("Client safety configuration differs")
        tool_calls = []
        read_groups = {}
        manifest = None
        rejected_subscriptions = 0
        for row in observation["calls"]:
            request = message(checked_file(root, row["request"]))
            response = message(checked_file(root, row["response"]))
            if request["method"] != row["method"]:
                raise ValueError("Recorded method differs")
            if request["method"] == "subscriptions/listen":
                if row["response"]["http_status"] != 400 or "error" not in response:
                    raise ValueError("Unsupported subscription boundary differs")
                rejected_subscriptions += 1
            if request["method"] != "tools/call":
                continue
            name_ = request["params"]["name"]
            args = request["params"]["arguments"]
            tool = response["result"]
            if name_ not in observation["allowed_mcp_tools"] or tool.get("isError") or row["response"]["http_status"] != 200:
                raise ValueError("Unexpected or failed evidence call")
            if args["bundle"] != "okf-dwp" or args["version"] != "bf50ef8d91b9f1ccc2cbdb354198eae74c9ed752" or args["question"] != context["question"]:
                raise ValueError("Client requested different context inputs")
            value = tool["structuredContent"]
            text = tool["content"][0]["text"]
            if json.loads(text) != value or value["context_id"] != context["context_id"] or value["evidence_status"] != context["evidence_status"]:
                raise ValueError("Tool text, context identity or evidence status differs")
            response_bytes = len(text.encode())
            if name_ == "ask_okf_manifest":
                if manifest is not None:
                    raise ValueError("Unexpected additional catalogue page in this fixed trial")
                manifest = value
                if args["budget"] != {"max_bytes": 32768} or value["binding"] != context["binding"] or value["bundle"] != context["bundle"]:
                    raise ValueError("Manifest binding or original budget differs")
                if value["response_bytes"] != response_bytes or response_bytes > args["delivery_bytes"]:
                    raise ValueError("Manifest delivery size differs")
                ids = [r["id"] for r in value["records"]]
                if ids != list(by_id) or value["delivery"]["next_offset"] is not None:
                    raise ValueError("Catalogue omits or reorders selected records")
                for record in value["records"]:
                    source = by_id[record["id"]]["record"]
                    if (record["text_sha256"] != digest(source["text"].encode()) or record["text_characters"] != units(source["text"])
                            or record["source_url"] != source["provenance"][0]["url"] or record["source_locator"] != source["provenance"][0]["locator"]):
                        raise ValueError("Catalogue source identity differs")
                summary = value["summary"]
                if (summary["selected_records"] != len(context["selected"]) or summary["context_truncated"] != context["budget"]["truncated"]
                        or summary["retrieval_truncated"] != context["retrieval"]["truncated"] or summary["ai_answer"] is not None):
                    raise ValueError("Catalogue evidence boundary differs")
            else:
                if manifest is None or args["context_id"] != context["context_id"] or args["budget"] != manifest["replay"]["budget"]:
                    raise ValueError("Read omitted original context replay identity")
                section, identity = args["section"], args.get("record_id")
                if section == "diagnostics":
                    data = {k: v for k, v in context.items() if k not in ["selected", "relationships"]}
                    data.update(selected_records=len(context["selected"]), relationship_count=len(context["relationships"]))
                    whole = canonical(data)
                elif section in ["record_text", "record_metadata"]:
                    item = by_id[identity]
                    if section == "record_text":
                        whole = item["record"]["text"]
                    else:
                        record = {k: v for k, v in item["record"].items() if k != "text"}
                        source_text = item["record"]["text"]
                        record["text_reference"] = {"section": "record_text", "characters": units(source_text), "sha256": digest(source_text.encode())}
                        whole = canonical({**item, "record": record})
                else:
                    raise ValueError("Unexpected section in the two-record client trial")
                if (value["content_sha256"] != digest(whole.encode()) or value["total_characters"] != units(whole)
                        or value["character_unit"] != "utf-16-code-units" or value["section"] != section or value["record_id"] != identity
                        or value["offset"] != args.get("offset", 0) or value["end_offset"] != value["offset"] + units(value["data"])):
                    raise ValueError("Read source identity, offsets or hash differ")
                expected = whole.encode("utf-16-le")[value["offset"]*2:value["end_offset"]*2].decode("utf-16-le")
                if value["data"] != expected or value["next_offset"] != (value["end_offset"] if value["end_offset"] < units(whole) else None):
                    raise ValueError("Read passage or continuation differs")
                if (value["delivery"]["used_bytes"] != response_bytes or response_bytes > args["delivery_bytes"]
                        or value["delivery"]["max_bytes"] != args["delivery_bytes"]
                        or value["context_truncated"] != context["budget"]["truncated"]
                        or value["retrieval_truncated"] != context["retrieval"]["truncated"] or value["ai_answer"] is not None):
                    raise ValueError("Read size or evidence boundary differs")
                read_groups.setdefault((section, identity), []).append(value)
            tool_calls.append({"sequence": row["sequence"], "tool": name_, "section": args.get("section"),
                               "record_id": args.get("record_id"), "json_bytes": response_bytes,
                               "structured_sha256": digest(canonical(value).encode())})
        completed = []
        for (section, identity), values in read_groups.items():
            offset = 0
            for value in values:
                if value["offset"] != offset:
                    raise ValueError("Client skipped or repeated an evidence slice")
                offset = value["end_offset"]
            if values[-1]["next_offset"] is not None or digest(''.join(v["data"] for v in values).encode()) != values[0]["content_sha256"]:
                raise ValueError("Client did not receive a complete requested value")
            completed.append({"section": section, "record_id": identity, "slices": len(values), "content_sha256": values[0]["content_sha256"]})
        if name == "claude-local-2026-09-19":
            if tool_calls or observation["status"] != "failed-no-real-tool-call":
                raise ValueError("No-call failure was erased")
        elif len(tool_calls) != 7 or len(completed) != 5 or len({r["record_id"] for r in completed if r["record_id"]}) != 2:
            raise ValueError("Expected manifest plus diagnostics and two complete text/metadata records")
        results.append({"observation": name, "observation_sha256": digest(observation_raw), "actual_tool_calls": len(tool_calls),
                        "unsupported_subscription_probes": rejected_subscriptions, "context_id": context["context_id"] if tool_calls else None,
                        "evidence_status": context["evidence_status"] if tool_calls else None, "complete_values": completed, "tools": tool_calls,
                        "status": "captured-evidence-verified" if tool_calls else "retained-no-call-failure-verified"})
    return {"schema": "okf-compact-client-verification.v1", "comparison_context": {"path": str(CONTEXT.relative_to(ROOT)),
            "sha256": digest(raw), "context_id": context["context_id"]}, "observations": results,
            "model_calls": 0, "network_calls": 0, "human_answer_review": "pending",
            "limitation": "Exact tool delivery and failure preservation only. No legal-entailment or answer-quality score; local client observation is not a public deployment test."}


def main():
    result = verify()
    expected = BASE / "verification.json"
    if json.loads(expected.read_text()) != result:
        raise ValueError("Retained compact-client verification differs")
    print(json.dumps({"status": "compact-client-observations-verified", "actual_tool_calls": 7, "complete_values": 5,
                      "preserved_no_call_failures": 1, "model_calls": 0, "human_answer_review": "pending"}))


if __name__ == "__main__":
    main()
