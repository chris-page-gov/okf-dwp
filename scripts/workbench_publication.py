"""Admit only the declared public staff-question workbench and its bound files."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import PurePosixPath

MANIFEST = "evaluation/evidence-workbench/manifest.json"
QUESTIONS = "evaluation/staff-questions/cases.json"
CORPUS = "structured-context/evidence-connect-manifest.json"
PREFIX = "evaluation/evidence-workbench/"
MAX_TOTAL = 56 * 1024 * 1024


def publish_workbench(read, committed, strict_json, verify_budget):
    if MANIFEST not in committed:
        return {}, None
    outputs = {}

    def require(ok, message):
        if not ok:
            raise ValueError(f"Workbench publication rejected: {message}")

    def take(path, cap):
        raw = read(path, cap)
        outputs[path] = raw
        require(sum(map(len, outputs.values())) <= MAX_TOTAL, "publication exceeds 56 MiB")
        return raw

    def bound(ref, cap):
        require(isinstance(ref, dict) and isinstance(ref.get("url"), str), "missing file reference")
        name = ref["url"]
        require(name and not name.startswith("/") and "\\" not in name and ":" not in name
                and "%" not in name and "?" not in name and "#" not in name
                and all(part not in {"", ".", ".."} and not part.startswith(".") for part in name.split("/")), "unsafe relative file reference")
        require(str(PurePosixPath(name)) == name, "non-canonical file reference")
        require(re.fullmatch(r"(?:packages|parts)/[a-zA-Z0-9_-]+\.json", name), "unexpected evidence file reference")
        raw = take(PREFIX + name, cap)
        require(hashlib.sha256(raw).hexdigest() == ref.get("sha256"), "file hash differs")
        if "bytes" in ref:
            require(type(ref["bytes"]) is int and ref["bytes"] == len(raw), "file size differs")
        return raw

    raw_manifest = take(MANIFEST, 262144)
    manifest = strict_json(raw_manifest)
    require(manifest.get("schema") == "okf-evidence-workbench.v1", "unknown manifest schema")
    approved_raw = read(QUESTIONS, 2 * 1024 * 1024)
    approved = strict_json(approved_raw)
    source = manifest.get("source", {})
    require(source.get("registry") == QUESTIONS and source.get("corpus") == CORPUS,
            "unexpected producer source")
    require(source.get("registry_sha256") == hashlib.sha256(approved_raw).hexdigest()
            and source.get("corpus_sha256") == hashlib.sha256(read(CORPUS, 2 * 1024 * 1024)).hexdigest(),
            "producer source hash differs")
    questions = {row["id"]: row["question"] for row in approved["cases"]}
    rows = manifest.get("questions")
    require(isinstance(rows, list) and 0 < len(rows) <= 40 and len(rows) == len(questions), "question census differs")
    require(len({row["id"] for row in rows}) == len(rows) and {row["id"] for row in rows} == set(questions), "question identities differ")
    for row in rows:
        require(row["question"] == questions[row["id"]], "question is not the approved public wording")
        raw = bound(row["package"], 524288)
        context = strict_json(raw)
        require(context.get("schema") == "okf-governed-context.v1" and context.get("question") == row["question"]
                and context.get("ai_answer") is None, "unexpected context or generated answer")
        verify_budget(context, raw)
        selected = context.get("selected")
        require(isinstance(selected, list) and all(isinstance(item, dict)
                and isinstance(item.get("record"), dict) and item["record"].get("access") == "public"
                for item in selected), "only explicitly public selected records may be published")
        parts = row["package"].get("parts", [])
        require(isinstance(parts, list) and 0 < len(parts) <= 128, "bounded package parts required")
        text, offset = [], 0
        for i, ref in enumerate(parts):
            piece_raw = bound(ref, 32768)
            piece = strict_json(piece_raw)
            require(piece.get("schema") == "okf-context-read.v1" and piece.get("section") == "package"
                    and piece.get("record_id") is None and piece.get("context_id") == context["context_id"]
                    and piece.get("content_sha256") == row["package"]["sha256"]
                    and piece.get("evidence_status") == context["evidence_status"]
                    and piece.get("ai_answer") is None and piece.get("character_unit") == "utf-16-code-units"
                    and piece.get("media_type") == "application/json"
                    and piece.get("total_characters") == len(raw.decode().encode("utf-16-le")) // 2
                    and piece.get("context_truncated") == context["budget"]["truncated"]
                    and piece.get("retrieval_truncated") == context.get("retrieval", {}).get("truncated", False),
                    "part identity differs")
            delivery = piece.get("delivery", {})
            require(delivery.get("used_bytes") == len(piece_raw) and delivery.get("max_bytes") == 32768,
                    "part delivery byte count differs")
            data = piece.get("data")
            require(isinstance(data, str) and piece.get("offset") == offset, "part offsets differ")
            offset += len(data.encode("utf-16-le")) // 2
            require(piece.get("end_offset") == offset
                    and piece.get("next_offset") == (None if i == len(parts) - 1 else offset), "part continuation differs")
            text.append(data)
        require("".join(text).encode() == raw, "parts do not reconstruct the exact package")
    return outputs, {"schema": "okf-dwp-workbench-publication.v1", "questions": len(rows),
                     "manifest_sha256": hashlib.sha256(raw_manifest).hexdigest(),
                     "files": len(outputs), "bytes": sum(map(len, outputs.values())),
                     "verified": ["public question register", "corpus manifest", "package hashes", "exact parts", "public access markers"],
                     "producer_claims": "Engine and delivery file identities and call counts require the separate pinned producer replay; this publisher does not independently observe execution.",
                     "scope": "Fixed public staff questions and hash-bound evidence; no source rewrite or answer acceptance."}
