#!/usr/bin/env python3
"""Bounded offline integrity audit for an archived remote graph verification packet."""

import argparse
import collections
import gzip
import hashlib
import json
import os
import re
import stat
import sys
import zlib
from pathlib import Path, PurePosixPath

HASH = re.compile(r"^[a-f0-9]{64}$")
MAX_PACKET = 256 * 1024 * 1024
MAX_FILE = 16 * 1024 * 1024
MAX_PACKAGE = 32 * 1024 * 1024
MAX_MCP_BODY = 8192
MAX_QUESTIONS = 106
MAX_CASES = 108
MAX_UNIQUE_TARGET_PAIRS = 352
MAX_CASE_TARGET_CHECKS = 355
EXPECTED_CASES_SHA256 = "920f6ae84dd5207a8366b695814534875c9f03648d12ed315d84ba3a7d7e0e7d"
EXPECTED_PRODUCER_COMMIT = "2e12f20cfd20e62a67197e7aade4ea612b873684"
EXPECTED_GRAPH_SHA256 = "ff51d877ed13f7089e7512224a4a8dcd356d0ae8e5964fe33349edf0a263b426"
EXPECTED_ENGINE_ID = "urn:okf:graph-engine:sha256:c75b01d322236e4c13fc1ad72a7e3424203dbae2413c4e6be64b960d8566cb42"
ALLOWED_RPC_METHODS = {"initialize", "notifications/initialized", "notifications/cancelled",
                       "ping", "server/discover", "tools/list", "tools/call"}
ALLOWED_TOOLS = {"plan_okf_evidence", "read_okf_planned_evidence"}


class AuditError(Exception):
    pass


def need(ok, message):
    if not ok:
        raise AuditError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    # Matches graphCanonical: sorted object keys, UTF-8 JSON, compact separators.
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def read_regular(path, limit):
    info = path.lstat()
    need(stat.S_ISREG(info.st_mode), f"not a regular file: {path}")
    need(info.st_size <= limit, f"file exceeds {limit} byte bound: {path}")
    data = path.read_bytes()
    need(len(data) == info.st_size, f"file changed while reading: {path}")
    return data


def read_json(path, limit=MAX_FILE):
    try:
        value = json.loads(read_regular(path, limit))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"invalid JSON in {path}: {exc}") from exc
    need(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def safe_packet_path(root, relative, expected):
    need(isinstance(relative, str), "package_file is not a string")
    posix = PurePosixPath(relative)
    need(not posix.is_absolute() and ".." not in posix.parts and str(posix) == expected,
         f"unsafe or unexpected package path: {relative!r}")
    current = root
    for part in posix.parts:
        current = current / part
        need(not current.is_symlink(), f"symlink in package path: {relative}")
    return current


def gunzip_bounded(data, label):
    inflater = zlib.decompressobj(16 + zlib.MAX_WBITS)
    out = bytearray()
    try:
        for offset in range(0, len(data), 65536):
            chunk = data[offset:offset + 65536]
            while chunk:
                piece = inflater.decompress(chunk, MAX_PACKAGE + 1 - len(out))
                out.extend(piece)
                need(len(out) <= MAX_PACKAGE, f"decompressed package exceeds 32 MiB: {label}")
                chunk = inflater.unconsumed_tail
                if not chunk:
                    break
        out.extend(inflater.flush(MAX_PACKAGE + 1 - len(out)))
    except zlib.error as exc:
        raise AuditError(f"invalid gzip package {label}: {exc}") from exc
    need(len(out) <= MAX_PACKAGE, f"decompressed package exceeds 32 MiB: {label}")
    need(inflater.eof and not inflater.unused_data and not inflater.unconsumed_tail,
         f"incomplete gzip stream or trailing data: {label}")
    return bytes(out)


def load_expected_cases(packet_root):
    fixture_path = Path(__file__).with_name("expected-cases.json")
    raw = read_regular(fixture_path, MAX_FILE)
    need(sha(raw) == EXPECTED_CASES_SHA256, "frozen expected-case fixture hash differs")
    archived_fixture = packet_root / "expected-cases.json"
    if archived_fixture.exists():
        need(read_regular(archived_fixture, MAX_FILE) == raw, "archived expected-case fixture differs")
    fixture = read_json(fixture_path, MAX_FILE)
    need(fixture.get("schema") == "okf-graph-archive-case-bindings.v1", "unexpected expected-case fixture schema")
    need(fixture.get("producer_commit") == EXPECTED_PRODUCER_COMMIT
         and fixture.get("graph_sha256") == EXPECTED_GRAPH_SHA256
         and fixture.get("engine_id") == EXPECTED_ENGINE_ID,
         "expected-case fixture producer/graph/engine identity differs")
    provenance = fixture.get("verifier_provenance")
    need(isinstance(provenance, dict) and provenance.get("verifier_matches_git_head") is True
         and provenance.get("package_lock_matches_git_head") is True
         and provenance.get("worker_matches_build_receipt") is True
         and provenance.get("package_lock_matches_build_receipt") is True
         and provenance.get("verifier_matches_build_receipt") is True,
         "expected-case fixture verifier provenance is incomplete")
    cases = fixture.get("cases")
    need(isinstance(cases, list) and len(cases) == MAX_CASES, "expected-case fixture census differs")
    by_question = collections.defaultdict(list)
    case_ids = set()
    target_occurrences = 0
    target_pairs = set()
    for case in cases:
        need(isinstance(case, dict), "expected-case row is malformed")
        case_id = case.get("case_id")
        qhash = case.get("question_sha256")
        ids = case.get("expected_record_ids")
        hashes = case.get("expected_source_text_hashes")
        path_count = case.get("expected_path_count")
        negative = case.get("negative_boundary")
        need(isinstance(case_id, str) and case_id and case_id not in case_ids,
             "expected-case ID is invalid or duplicated")
        need(isinstance(qhash, str) and HASH.fullmatch(qhash), "expected-case question digest is invalid")
        need(isinstance(ids, list) and all(isinstance(record_id, str) and record_id for record_id in ids)
             and len(ids) == len(set(ids)), f"expected-case targets are invalid: {case_id}")
        need(isinstance(hashes, dict) and set(hashes) == set(ids)
             and all(isinstance(value, str) and HASH.fullmatch(value) for value in hashes.values()),
             f"expected-case source hashes differ: {case_id}")
        need(type(path_count) is int and path_count >= 0 and type(negative) is bool,
             f"expected-case path/boundary fields are invalid: {case_id}")
        need((not negative or (not ids and path_count == 0)) and (bool(ids) or negative),
             f"expected-case boundary classification differs: {case_id}")
        case_ids.add(case_id)
        by_question[qhash].append(case)
        target_occurrences += len(ids)
        target_pairs.update((qhash, record_id) for record_id in ids)
    need(target_occurrences == MAX_CASE_TARGET_CHECKS and len(target_pairs) == MAX_UNIQUE_TARGET_PAIRS
         and len(by_question) == MAX_QUESTIONS,
         "expected-case target or question census differs")
    return fixture, by_question


def bind_plan_to_fixture(plan, by_question, verifier_provenance):
    need(plan.get("producer_commit") == EXPECTED_PRODUCER_COMMIT
         and plan.get("graph_sha256") == EXPECTED_GRAPH_SHA256
         and plan.get("engine_id") == EXPECTED_ENGINE_ID,
         "plan producer/graph/engine identity differs from frozen fixture")
    need(plan.get("publication_status") == "pinned", "plan is not pinned for public verification")
    need(plan.get("verifier_provenance") == verifier_provenance,
         "plan verifier provenance differs from frozen fixture")
    plan_questions = plan.get("questions")
    need(isinstance(plan_questions, list), "plan questions are missing")
    plan_by_question = {row.get("question_sha256"): row for row in plan_questions if isinstance(row, dict)}
    need(set(plan_by_question) == set(by_question) and len(plan_by_question) == len(plan_questions),
         "plan question set differs from frozen case fixture")
    for qhash, cases in by_question.items():
        row = plan_by_question[qhash]
        expected_ids = {record_id for case in cases for record_id in case["expected_record_ids"]}
        expected_hashes = {}
        for case in cases:
            for record_id, digest in case["expected_source_text_hashes"].items():
                need(record_id not in expected_hashes or expected_hashes[record_id] == digest,
                     f"frozen fixture has conflicting source hashes for {qhash} {record_id}")
                expected_hashes[record_id] = digest
        need(isinstance(row.get("case_ids"), list)
             and collections.Counter(row["case_ids"]) == collections.Counter(case["case_id"] for case in cases),
             f"plan case IDs differ from frozen fixture for {qhash}")
        need(isinstance(row.get("expected_record_ids"), list)
             and set(row["expected_record_ids"]) == expected_ids
             and len(row["expected_record_ids"]) == len(expected_ids),
             f"plan targets differ from frozen fixture for {qhash}")
        need(row.get("expected_source_text_hashes") == expected_hashes,
             f"plan source hashes differ from frozen fixture for {qhash}")
    return plan_by_question


def validate_wire_event(event, sequence, question_hashes):
    need(isinstance(event, dict), "wire event is not an object")
    need(set(event) == {"sequence", "method", "path", "rpc_method", "tool", "question_sha256",
                        "request_bytes", "request_sha256", "status", "response_bytes", "response_sha256"},
         "wire event fields differ from the pinned verifier schema")
    need(type(event.get("sequence")) is int and event["sequence"] == sequence,
         "wire event sequence is not contiguous")
    method, path = event.get("method"), event.get("path")
    rpc, tool, qhash = event.get("rpc_method"), event.get("tool"), event.get("question_sha256")
    status = event.get("status")
    request_bytes, response_bytes = event.get("request_bytes"), event.get("response_bytes")
    need((method, path) in {("GET", "/health"), ("POST", "/graph/mcp")},
         "wire event route or method is outside the pinned verifier contract")
    need(type(request_bytes) is int and 0 <= request_bytes <= 32768,
         "wire request body exceeds 32 KiB or has invalid size")
    need(type(response_bytes) is int and response_bytes >= 0,
         "wire response body size is invalid")
    need(type(status) is int and 200 <= status < 300, "wire event status is not successful")
    response_digest = event.get("response_sha256")
    need(isinstance(response_digest, str) and HASH.fullmatch(response_digest), "wire response hash is invalid")
    need((request_bytes == 0 and event.get("request_sha256") is None)
         or (request_bytes > 0 and isinstance(event.get("request_sha256"), str)
             and HASH.fullmatch(event["request_sha256"])), "wire request hash/size binding differs")
    if method == "GET":
        need(request_bytes == 0 and rpc is None and tool is None and qhash is None,
             "health request contains JSON-RPC metadata")
        need(event.get("request_sha256") is None, "health request unexpectedly has a body hash")
        need(response_bytes <= 65536, "health response exceeds 65,536 bytes")
    else:
        need(request_bytes > 0, "JSON-RPC request body is empty")
        need(isinstance(event.get("request_sha256"), str) and HASH.fullmatch(event["request_sha256"]),
             "JSON-RPC request hash is invalid")
        need(rpc in ALLOWED_RPC_METHODS, "unknown JSON-RPC method in wire event")
        if rpc == "tools/call":
            need(tool in ALLOWED_TOOLS and isinstance(qhash, str) and qhash in question_hashes,
                 "unknown evidence tool or question in wire event")
            need(response_bytes <= MAX_MCP_BODY, "evidence HTTP response body exceeds 8,192 bytes")
        else:
            need(tool is None and qhash is None, "non-tool RPC event has tool/question metadata")
            need(response_bytes <= 65536, "non-evidence HTTP response exceeds 65,536 bytes")


def audit(root, allow_partial):
    need(not root.is_symlink() and root.is_dir(), "packet root must be a real directory")
    allowed_root = {"plan.json", "summary.json", "wire.json", "case-index", "checkpoints", "packages",
                    "native-observation.json", "native-results.json", "expected-cases.json", "verify_native_observation.py",
                    "verify_graph_packet.py"}
    for child in root.iterdir():
        need(not child.is_symlink(), f"symlink is not allowed: {child.name}")
        need(child.name in allowed_root, f"unexpected packet artefact: {child.name}")
    for name in ("case-index", "checkpoints", "packages"):
        need((root / name).is_dir(), f"missing packet directory: {name}")

    total_files = 0
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in dirs:
            need(not (Path(base) / name).is_symlink(), f"symlink directory: {Path(base) / name}")
        for name in files:
            path = Path(base) / name
            info = path.lstat()
            need(stat.S_ISREG(info.st_mode), f"non-regular packet entry: {path}")
            total_files += info.st_size
            need(total_files <= MAX_PACKET, "packet exceeds 256 MiB total file-size bound")

    fixture, expected_by_question = load_expected_cases(root)
    plan = read_json(root / "plan.json", MAX_FILE)
    need(plan.get("schema") == "okf-graph-remote-verification-plan.v1", "unexpected plan schema")
    bind_plan_to_fixture(plan, expected_by_question, fixture["verifier_provenance"])
    questions = plan.get("questions")
    need(isinstance(questions, list) and plan.get("question_count") == MAX_QUESTIONS,
         "plan does not declare the 106-question suite")
    need(plan.get("case_occurrences") == MAX_CASES, "plan does not declare 108 case occurrences")
    by_hash = {}
    all_case_ids = []
    expected_targets = 0
    for row in questions:
        qhash = row.get("question_sha256")
        need(isinstance(qhash, str) and HASH.fullmatch(qhash) and qhash not in by_hash,
             "invalid or duplicate plan question digest")
        ids, hashes = row.get("expected_record_ids"), row.get("expected_source_text_hashes")
        need(isinstance(ids, list) and len(ids) == len(set(ids)), f"invalid target list for {qhash}")
        need(isinstance(hashes, dict) and set(hashes) == set(ids), f"source-hash target set differs for {qhash}")
        need(all(isinstance(v, str) and HASH.fullmatch(v) for v in hashes.values()), f"invalid source digest for {qhash}")
        cases = row.get("case_ids")
        need(isinstance(cases, list) and cases and all(isinstance(x, str) and x for x in cases), f"invalid case IDs for {qhash}")
        all_case_ids.extend(cases)
        expected_targets += len(ids)
        by_hash[qhash] = row
    need(len(by_hash) == MAX_QUESTIONS and len(all_case_ids) == MAX_CASES,
         "plan question/case census differs")
    need(expected_targets == MAX_UNIQUE_TARGET_PAIRS,
         f"plan unique question-target pair census is {expected_targets}, expected 352")

    # The original verifier gate owns directed-path and legal/sufficiency reasoning.
    # This archive audit only retains its published result; it does not recalculate it.
    complete = 0
    verified_cases = []
    verified_pairs = 0
    verified_targets = 0
    package_expanded_total = 0
    for qhash, row in by_hash.items():
        expected_name = f"{qhash}.json"
        cp_path = root / "checkpoints" / expected_name
        ix_path = root / "case-index" / expected_name
        if not cp_path.exists() or not ix_path.exists():
            continue
        cp_bytes = read_regular(cp_path, MAX_FILE)
        cp = read_json(cp_path, MAX_FILE)
        index = read_json(ix_path, MAX_FILE)
        need(index == {"question_sha256": qhash, "case_ids": row["case_ids"], "checkpoint_sha256": sha(cp_bytes)},
             f"case-index checkpoint binding differs for {qhash}")
        need(cp.get("schema") == "okf-graph-remote-question-checkpoint.v1", f"checkpoint schema differs for {qhash}")
        need(cp.get("question_sha256") == qhash and cp.get("case_ids") == row["case_ids"], f"checkpoint identity/cases differ for {qhash}")
        need(cp.get("plan_id") == row.get("plan_id") and cp.get("package_sha256") == row.get("package_sha256"),
             f"checkpoint plan/package identity differs for {qhash}")
        need(cp.get("evidence_status") == "insufficient" and cp.get("ai_answer") is None
             and cp.get("assembly_truncated") is False, f"checkpoint boundary flags differ for {qhash}")
        package_rel = f"packages/{qhash}.json.gz"
        package_path = safe_packet_path(root, cp.get("package_file"), package_rel)
        package_bytes = read_regular(package_path, MAX_FILE)
        need(cp.get("package_file_bytes") == len(package_bytes) and cp.get("package_file_sha256") == sha(package_bytes),
             f"checkpoint gzip byte binding differs for {qhash}")
        expanded = gunzip_bounded(package_bytes, qhash)
        package_expanded_total += len(expanded)
        need(package_expanded_total <= MAX_PACKET, "decompressed packages exceed 256 MiB aggregate bound")
        try:
            package = json.loads(expanded)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise AuditError(f"invalid decompressed package {qhash}: {exc}") from exc
        need(isinstance(package, dict), f"package is not an object: {qhash}")
        need(sha(canonical(package).encode("utf-8")) == row["package_sha256"] == cp["package_sha256"],
             f"canonical package SHA-256 differs for {qhash}")
        plan_identity = dict(package)
        plan_id = plan_identity.pop("plan_id", None)
        need(plan_id == row["plan_id"] and "urn:sha256:" + sha(canonical(plan_identity).encode("utf-8")) == plan_id,
             f"canonical plan identity differs for {qhash}")
        question = package.get("question")
        need(isinstance(question, str) and sha(question.encode("utf-8")) == qhash, f"question digest differs for {qhash}")
        need(package.get("schema") == "okf-graph-evidence-package.v1", f"package schema differs for {qhash}")
        for field in ("evidence_status", "ai_answer", "retrieval_complete", "retrieval_status", "assembly_truncated"):
            need(package.get(field) == cp.get(field), f"package/checkpoint {field} differs for {qhash}")
        need(package.get("evidence_status") == "insufficient" and package.get("ai_answer") is None
             and package.get("assembly_truncated") is False, f"package boundary flags differ for {qhash}")
        selected = package.get("selected")
        need(isinstance(selected, list), f"package selected records missing for {qhash}")
        selected_text = {}
        for item in selected:
            need(isinstance(item, dict) and isinstance(item.get("record"), dict),
                 f"package selected record is malformed for {qhash}")
            record = item["record"]
            record_id = record.get("id")
            need(isinstance(record_id, str) and record_id and record_id not in selected_text,
                 f"package selected record ID is invalid or duplicated for {qhash}")
            selected_text[record_id] = record.get("text")
        verified = cp.get("verified_source_text_sha256")
        need(isinstance(verified, dict) and set(row["expected_record_ids"]) == set(verified)
             and set(row["expected_record_ids"]).issubset(selected_text),
             f"expected source target absent from package {qhash}")
        for record_id in row["expected_record_ids"]:
            text = selected_text[record_id]
            digest = sha(text.encode("utf-8")) if isinstance(text, str) else None
            need(digest == row["expected_source_text_hashes"][record_id] == verified.get(record_id),
                 f"source text digest differs for {qhash} {record_id}")
        checks = cp.get("source_target_checks")
        expected_cases = {case["case_id"]: case for case in expected_by_question[qhash]}
        need(isinstance(checks, list) and collections.Counter(x.get("case_id") for x in checks if isinstance(x, dict))
             == collections.Counter(expected_cases.keys()), f"checkpoint case-level target checks differ for {qhash}")
        for check in checks:
            need(isinstance(check, dict), f"checkpoint case target row is malformed for {qhash}")
            expected_case = expected_cases[check["case_id"]]
            expected_count = len(expected_case["expected_record_ids"])
            need(type(check.get("target_count")) is int and check["target_count"] == expected_count
                 and type(check.get("source_hashes_verified")) is int
                 and check["source_hashes_verified"] == expected_count
                 and type(check.get("path_count")) is int
                 and check["path_count"] == expected_case["expected_path_count"]
                 and check.get("negative_boundary") is expected_case["negative_boundary"],
                 f"checkpoint case-level targets/path/boundary differ for {qhash} {check['case_id']}")
        verified_cases.extend(x["case_id"] for x in checks)
        verified_targets += sum(x["target_count"] for x in checks)
        complete += 1
        verified_pairs += len(row["expected_record_ids"])

    for directory, suffix in (("checkpoints", ".json"), ("case-index", ".json"), ("packages", ".json.gz")):
        found = {p.name for p in (root / directory).iterdir() if p.is_file()}
        unexpected = found - {qhash + suffix for qhash in by_hash}
        need(not unexpected, f"unexpected files in {directory}: {sorted(unexpected)[:3]}")
    need(not (collections.Counter(verified_cases) - collections.Counter(all_case_ids)),
         "checkpoint case IDs include unexpected or duplicated plan occurrences")
    need(verified_pairs <= MAX_UNIQUE_TARGET_PAIRS, "checkpoint unique target-pair total exceeds plan census")
    need(verified_targets <= MAX_CASE_TARGET_CHECKS, "checkpoint case-target total exceeds case census")
    if complete == MAX_QUESTIONS:
        need(collections.Counter(verified_cases) == collections.Counter(all_case_ids), "final 108-case occurrence census differs")
        need(verified_pairs == MAX_UNIQUE_TARGET_PAIRS,
             f"checkpoint unique question-target pairs are {verified_pairs}, expected 352")
        need(verified_targets == MAX_CASE_TARGET_CHECKS,
             f"checkpoint per-case target/hash totals are {verified_targets}, expected 355")

    summary_path = root / "summary.json"
    if summary_path.exists():
        summary = read_json(summary_path, MAX_FILE)
        need(summary.get("schema") == "okf-graph-remote-sdk-verification.v1" and summary.get("status") == "passed",
             "final summary schema/status is not passed")
        run = summary.get("run", {})
        need(run.get("mode") == "public" and isinstance(run.get("http_requests"), int)
             and run.get("http_requests", 0) > 0 and run.get("public_network_calls") == run.get("http_requests"),
             "final summary is not a completed public run")
        identities = summary.get("identities", {})
        need(identities.get("producer_commit") == fixture["producer_commit"]
             and identities.get("graph_sha256") == fixture["graph_sha256"]
             and identities.get("engine_id") == fixture["engine_id"]
             and identities.get("admission_status") == "pinned"
             and identities.get("verifier_provenance") == fixture["verifier_provenance"],
             "final summary identities/provenance differ from frozen fixture")
        need(run.get("model_calls") == 0 and run.get("paid_api_calls") == 0 and run.get("automatic_retries") == 0,
             "final summary records model/paid calls or automatic retries")
        counts = summary.get("counts", {})
        need(counts.get("unique_questions") == MAX_QUESTIONS and counts.get("completed_unique_questions") == MAX_QUESTIONS
             and counts.get("source_case_occurrences") == MAX_CASES and counts.get("expected_positive_targets") == MAX_CASE_TARGET_CHECKS,
             "final summary census differs")
        gates = summary.get("gates", {})
        need(gates.get("expected_targets_and_paths") == "passed", "original directed-path verifier gate was not passed")
        need(gates.get("source_text_hashes") == "passed" and gates.get("insufficient_boundary") == "passed"
             and gates.get("no_truncation") == "passed", "final summary integrity gates differ")
        need(complete == MAX_QUESTIONS and verified_pairs == MAX_UNIQUE_TARGET_PAIRS
             and verified_targets == MAX_CASE_TARGET_CHECKS, "summary is present before archive census is complete")
        wire = read_json(root / "wire.json", MAX_FILE)
        events = wire.get("events")
        need(isinstance(events, list) and summary.get("wire_receipt", {}).get("events") == events,
             "wire.json events differ from final summary")
        calls = wire.get("calls")
        bytes_received = wire.get("bytes_received")
        need(type(calls) is int and calls == len(events) and calls <= 12000, "wire call count differs or exceeds limit")
        need(type(bytes_received) is int and 0 <= bytes_received <= MAX_PACKET, "wire byte total exceeds limit")
        for index, event in enumerate(events, start=1):
            validate_wire_event(event, index, set(by_hash))
        need(sum(e.get("response_bytes", 0) for e in events) == bytes_received, "wire event byte sum differs")
        max_response = max((e.get("response_bytes", 0) for e in events), default=0)
        need(wire.get("max_response_bytes") == max_response, "wire maximum response byte count differs")
        evidence_events = [e for e in events if e.get("rpc_method") == "tools/call"]
        need(evidence_events, "wire receipt has no evidence-tool calls")
        max_evidence = max((e["response_bytes"] for e in evidence_events), default=0)
        need(wire.get("evidence_calls") == len(evidence_events)
             and wire.get("evidence_response_bytes") == sum(e["response_bytes"] for e in evidence_events),
             "wire evidence call/byte totals differ from events")
        need(counts.get("evidence_http_calls") == len(evidence_events)
             and counts.get("max_evidence_http_response_bytes") == max_evidence,
             "summary evidence HTTP counts differ from wire events")
        wire_summary = summary["wire_receipt"]
        need(wire_summary.get("calls") == calls and wire_summary.get("bytes_received") == bytes_received
             and wire_summary.get("max_response_bytes") == max_response
             and wire_summary.get("max_evidence_response_bytes") == max_evidence
             and wire_summary.get("automatic_retries") == 0, "wire totals differ from summary")
        need(plan.get("question_count") == len(by_hash), "plan count differs at finalisation")
        print(f"PASS: archived packet integrity verified: {complete}/106 questions, 108 case occurrences, "
              f"352 unique question-target pairs, 355 fixture-bound per-case target checks; max evidence HTTP body {max_evidence} bytes.")
        print("The original directed-path gate is retained; this audit does not recalculate path resolution or assess legal sufficiency.")
        print("Wire response bodies are not retained here; response digests and byte counts are checked as recorded metadata.")
        return

    need(allow_partial, "summary.json is absent; use --allow-partial for a non-final checkpoint audit")
    need(complete < MAX_QUESTIONS, "all checkpoints exist but final summary.json is absent")
    print(f"PARTIAL AUDIT: verified {complete}/106 complete question checkpoints, "
          f"{len(verified_cases)}/108 case occurrences, {verified_pairs}/352 unique question-target pairs, "
          f"{verified_targets}/355 per-case target checks; final summary is absent.")
    print("No final pass or semantic/path-resolution claim is made.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-root", required=True, type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    try:
        audit(args.packet_root.absolute(), args.allow_partial)
    except (AuditError, OSError, ValueError, zlib.error) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
