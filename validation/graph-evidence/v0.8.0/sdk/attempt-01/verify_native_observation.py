#!/usr/bin/env python3
"""Offline replay checks for the bounded native OKF graph observation."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PRODUCER = "2e12f20cfd20e62a67197e7aade4ea612b873684"
GRAPH = "ff51d877ed13f7089e7512224a4a8dcd356d0ae8e5964fe33349edf0a263b426"
ENGINE = "urn:okf:graph-engine:sha256:c75b01d322236e4c13fc1ad72a7e3424203dbae2413c4e6be64b960d8566cb42"
PLAN = "urn:sha256:dc6f63b47864c1fd81781d3f4459ae08e4a611150470a509a494198582547a39"
PACKAGE = "ce30679c784930b4db9a0ec9cdc6b88a3dfdf99ffab86c51ca94f07f4ffd2406"
QUESTION = (
    "Where a child is awarded the highest-rate care component of DLA from 26 January 2025, "
    "but the change is reported to Universal Credit on 28 March 2026, what is the effective "
    "date of the higher disabled-child addition, and from which assessment period should it be paid?"
)
QUESTION_SHA256 = "c224ca359a090e29fbca4e58127f5e94968aab1808e2e1ae3801b395a39eb3e8"
TARGETS = (
    "https://chris-page-gov.github.io/okf-dwp/id/unit/adm/adm-chapter-a4/manual-structure-v1/source-0000055420-000-9e9c31f56b39",
    "https://chris-page-gov.github.io/okf-dwp/id/unit/adm/adm-chapter-a4/manual-structure-v1/source-0000059337-000-65ba8377e1e6",
    "https://chris-page-gov.github.io/okf-dwp/id/unit/adm/adm-chapter-f1/manual-structure-v1/source-0000023318-000-bec866c4cfa0",
    "https://chris-page-gov.github.io/okf-dwp/id/unit/adm/adm-chapter-f1/manual-structure-v1/source-0000024273-000-64312571d5f1",
)
MAX_BLOB = 16 * 1024 * 1024
MAX_MCP_RESULT = 8192


class CheckError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckError(message)


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CheckError(f"cannot read JSON {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object in {path}")
    return value


def utf16_units(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def run_git(root: Path, *args: str, binary: bool = False):
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.decode("utf-8", "replace").strip()
        raise CheckError(f"git {' '.join(args)} failed: {message}") from exc
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


def frozen_blob(root: Path, path: str) -> bytes:
    size = int(run_git(root, "cat-file", "-s", f"{PRODUCER}:{path}"))
    require(size <= MAX_BLOB, f"producer blob exceeds 16 MiB: {path}")
    data = run_git(root, "show", f"{PRODUCER}:{path}", binary=True)
    require(len(data) == size, f"producer blob size mismatch: {path}")
    return data


def verify(root: Path) -> None:
    attempt = root / "validation/graph-evidence/v0.8.0/sdk/attempt-01"
    raw_path = attempt / "native-results.json"
    receipt_path = attempt / "native-observation.json"
    raw_bytes = raw_path.read_bytes()
    raw = read_json(raw_path)
    receipt = read_json(receipt_path)
    require(all(raw.get(key) == receipt.get(key) for key in ('started_at', 'completed_at')),
            'raw capture times differ from the selected receipt')
    start = datetime.fromisoformat(raw['started_at'].replace('Z', '+00:00'))
    end = datetime.fromisoformat(raw['completed_at'].replace('Z', '+00:00'))
    require(start.tzinfo is not None and end.tzinfo is not None and start <= end,
            'native capture time range is invalid')
    previous = start
    for call in raw.get('calls', []):
        at = datetime.fromisoformat(call['observed_at'].replace('Z', '+00:00'))
        require(at.tzinfo is not None and previous <= at <= end, 'native call times are outside capture order')
        previous = at

    require(receipt.get("schema") == "okf-graph-native-host-observation.v1", "unexpected receipt schema")
    require(receipt.get("status") == "passed", "receipt status is not passed")
    require(receipt.get("classification") == "actual-native-plugin-host" and receipt.get("scope") == "representative-uc-client-observation", "receipt classification or scope differs")
    require(receipt.get("raw_credentials") is False and receipt.get("full_matrix_claimed") is False, "receipt credential or full-matrix boundary differs")
    require(receipt.get("transport_scope") == "MCP result JSON bytes observed by connector; not HTTP envelope bytes", "receipt transport measurement scope differs")
    deployment = receipt.get("deployment_binding", {})
    require(deployment.get("service_version") == "0.8.0" and deployment.get("scope") == "declared-selection-only; not remotely attested", "deployment binding boundary differs")
    binding = receipt.get("raw_observation", {})
    require(binding == {
        "path": "native-results.json",
        "bytes": len(raw_bytes),
        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
    }, "receipt does not bind the adjacent raw results bytes")
    require(raw.get("schema") == "okf-graph-native-host-raw-observation.v1", "unexpected raw results schema")
    require(set(raw) == {"schema", "classification", "host_scope", "started_at", "completed_at", "question", "calls", "source_texts", "transport_scope", "full_matrix_claimed"}, "raw results contain unknown fields")
    require(raw.get("full_matrix_claimed") is False, "raw results claim a full matrix")
    require(raw.get("question") == QUESTION, "native question differs from the expected question")
    require(hashlib.sha256(QUESTION.encode()).hexdigest() == QUESTION_SHA256, "expected question digest constant is inconsistent")

    calls = raw.get("calls")
    require(isinstance(calls, list) and len(calls) == 5, "expected exactly five native calls")
    expected_ids = list(TARGETS)
    max_result_bytes = 0
    parsed_results = []
    for index, call in enumerate(calls):
        require(set(call) == {"tool", "arguments", "response", "observed_at", "mcp_result_json_bytes"}, f"call {index} contains unknown fields")
        response = call.get("response")
        require(isinstance(response, dict) and set(response) == {"content", "structuredContent", "isError"}, f"call {index} response contains fields beyond raw MCP result values")
        require(response.get("isError") is False, f"native call {index} reported an error")
        normalised_size = len(json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        require(call.get("mcp_result_json_bytes") == normalised_size, f"call {index} normalised MCP result byte count differs")
        require(normalised_size <= MAX_MCP_RESULT, f"call {index} exceeds the 8192-byte MCP result limit")
        max_result_bytes = max(max_result_bytes, normalised_size)
        content = response.get("content")
        require(isinstance(content, list), f"call {index} content is not a list")
        require(all(isinstance(item, dict) and set(item) == {"type", "text"} for item in content), f"call {index} content contains unexpected fields")
        text_values = [item.get("text") for item in content if isinstance(item, dict) and item.get("type") == "text"]
        require(len(text_values) == 1 and isinstance(text_values[0], str), f"call {index} lacks one text result")
        try:
            decoded = json.loads(text_values[0])
        except json.JSONDecodeError as exc:
            raise CheckError(f"call {index} text result is not JSON: {exc}") from exc
        require(decoded == response.get("structuredContent"), f"call {index} text and structured result differ")
        parsed_results.append(decoded)

    require(calls[0]["tool"] == "plan_okf_evidence", "first call is not the plan call")
    require(calls[0]["arguments"] == {"bundle": "okf-dwp", "question": QUESTION, "delivery_bytes": 8192}, "plan call arguments differ")
    manifest = parsed_results[0]
    require(manifest.get("plan_id") == PLAN and manifest.get("graph_sha256") == GRAPH and manifest.get("engine_id") == ENGINE and manifest.get("package_sha256") == PACKAGE, "native manifest identities differ")
    require(manifest.get("evidence_status") == "insufficient" and manifest.get("ai_answer") is None, "native manifest does not preserve insufficient/null-answer status")
    require(manifest.get("retrieval_complete") is True and manifest.get("assembly_truncated") is False, "manifest retrieval/truncation flags differ")

    offsets: dict[str, int] = {record_id: 0 for record_id in TARGETS}
    reconstructed: dict[str, str] = {record_id: "" for record_id in TARGETS}
    for n, (call, result) in enumerate(zip(calls[1:], parsed_results[1:])):
        record_id = TARGETS[n]
        require(call["tool"] == "read_okf_planned_evidence", f"call {n + 1} is not a read call")
        args = call["arguments"]
        require(args == {"bundle": "okf-dwp", "question": QUESTION, "graph_sha256": GRAPH, "engine_id": ENGINE, "plan_id": PLAN, "section": "record_text", "record_id": record_id, "offset": 0, "delivery_bytes": 8192}, f"read call {n + 1} arguments differ")
        require(result.get("record_id") == record_id and result.get("section") == "record_text", f"read call {n + 1} target differs")
        require(result.get("plan_id") == PLAN and result.get("graph_sha256") == GRAPH and result.get("engine_id") == ENGINE, f"read call {n + 1} identities differ")
        require(result.get("evidence_status") == "insufficient" and result.get("ai_answer") is None, f"read call {n + 1} status/answer differs")
        require(result.get("character_unit") == "utf-16-code-units", f"read call {n + 1} does not declare UTF-16 offsets")
        start, end, data = result.get("offset"), result.get("end_offset"), result.get("data")
        require(isinstance(start, int) and isinstance(end, int) and isinstance(data, str), f"read call {n + 1} slice fields invalid")
        require(start == offsets[record_id] and end - start == utf16_units(data), f"read call {n + 1} offsets are not contiguous UTF-16 units")
        require(result.get("total_characters") == end and result.get("next_offset") is None, f"read call {n + 1} is incomplete or has an unexpected continuation")
        require(result.get("content_sha256") == hashlib.sha256(data.encode("utf-8")).hexdigest(), f"read call {n + 1} text hash differs")
        offsets[record_id] = end
        reconstructed[record_id] += data

    require(set(raw["source_texts"]) == set(TARGETS), "raw source-text map does not contain exactly the four target IDs")
    expected_hashes: dict[str, str] = {}
    for record_id in TARGETS:
        source = raw["source_texts"][record_id]
        require(set(source) == {"text", "declared_text_sha256", "characters"}, f"source text for {record_id} has unknown fields")
        text = source.get("text")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest() if isinstance(text, str) else ""
        require(text == reconstructed[record_id], f"source text for {record_id} differs from native slices")
        require(source.get("characters") == utf16_units(text), f"source character count for {record_id} differs")
        require(source.get("declared_text_sha256") == digest, f"source text digest for {record_id} differs")
        expected_hashes[record_id] = digest

    graph_path = "retrieval-graph/graph.json"
    report_path = "evaluation/retrieval-gate/graph-evaluation.json"
    graph_bytes = frozen_blob(root, graph_path)
    report_bytes = frozen_blob(root, report_path)
    require(hashlib.sha256(graph_bytes).hexdigest() == GRAPH, "frozen producer graph blob SHA-256 differs")
    try:
        graph = json.loads(graph_bytes)
        report = json.loads(report_bytes)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CheckError(f"frozen producer graph/report JSON is invalid: {exc}") from exc
    records = graph.get("index", {}).get("records")
    require(isinstance(records, list), "frozen producer graph has no index.records list")
    graph_texts = {row.get("id"): row.get("text") for row in records if isinstance(row, dict)}
    for record_id, digest in expected_hashes.items():
        graph_text = graph_texts.get(record_id)
        require(isinstance(graph_text, str), f"frozen graph has no full text for {record_id}")
        require(hashlib.sha256(graph_text.encode("utf-8")).hexdigest() == digest, f"frozen graph source text hash differs for {record_id}")
        require(graph_text == reconstructed[record_id], f"native source text differs from frozen graph for {record_id}")
    case = report.get("fixed_uc_out_of_sample_case", {})
    require(case.get("question_sha256") == QUESTION_SHA256, "frozen report question digest differs")
    report_targets = case.get("expected_record_ids")
    require(isinstance(report_targets, list) and len(report_targets) == 4 and set(report_targets) == set(TARGETS), "frozen report expected target IDs differ")
    require(case.get("package_sha256") == PACKAGE and case.get("plan_id") == PLAN, "frozen report package or plan identity differs")
    require(case.get("evidence_status") == "insufficient" and case.get("ai_answer") is None, "frozen report does not preserve insufficient/null-answer status")
    require(report.get("identities", {}).get("graph_sha256") == GRAPH, "frozen report graph identity differs")
    require(report.get("identities", {}).get("engine_id") == ENGINE, "frozen report engine identity differs")
    require(receipt.get("identities", {}).get("producer_commit") == PRODUCER, "receipt producer commit differs")
    observed = receipt.get("identities", {})
    require(observed.get("question_sha256") == QUESTION_SHA256, "receipt question digest differs")
    require(observed.get("graph_sha256") == GRAPH and observed.get("engine_id") == ENGINE and observed.get("plan_id") == PLAN and observed.get("package_sha256") == PACKAGE, "receipt observed identity fields differ")
    require(receipt.get("counts", {}).get("observed_tool_calls") == 5, "receipt call count differs")
    require(receipt.get("counts", {}).get("max_mcp_result_json_bytes") == max_result_bytes, "receipt maximum MCP result byte count differs")
    require(receipt.get("counts", {}).get("continuation_calls") == 0, "receipt records unexpected continuation calls")
    require(receipt.get("discovery", {}).get("tool_names") == ["plan_okf_evidence", "read_okf_planned_evidence"], "receipt tool discovery names differ")
    require(receipt.get("gates") == {"manifest_continuation": "passed", "source_text_hashes": "passed", "no_truncated_tool_output": "passed"}, "receipt gate results differ")
    checks = receipt.get("source_text_checks")
    require(isinstance(checks, list) and len(checks) == 4, "receipt source-text check list differs")
    checks_by_id = {item.get("record_id"): item for item in checks if isinstance(item, dict)}
    require(set(checks_by_id) == set(TARGETS), "receipt source-text check IDs differ")
    for record_id, digest in expected_hashes.items():
        item = checks_by_id[record_id]
        require(item.get("source_text_sha256") == digest and item.get("expected_source_text_sha256") == digest and item.get("matched") is True, f"receipt source-text check differs for {record_id}")

    print("PASS: raw native results are receipt-bound; five MCP calls, four targets, UTF-16 slices, source hashes, identities and insufficient/null status verified.")
    print(f"Producer graph blob: {graph_path} ({hashlib.sha256(graph_bytes).hexdigest()})")
    print(f"Producer report blob: {report_path}")
    print(f"Maximum normalised MCP result JSON: {max_result_bytes} bytes (not HTTP envelope bytes).")
    print("Boundary: service version, source commit and Worker digest remain declared bindings; package was not reconstructed; no Worker attestation is claimed.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dwp-root", type=Path, default=Path(__file__).resolve().parents[5], help="OKF-DWP checkout (default: repository containing this verifier)")
    args = parser.parse_args()
    try:
        verify(args.dwp_root.resolve())
    except CheckError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
