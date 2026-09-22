#!/usr/bin/env python3
"""Observe declared PDF structure without changing frozen sources.

Default/--check replays hashes and the tree parser, without invoking Poppler.
--extract explicitly observes pending documents; existing attempts are immutable.
Use a fresh --output directory for a new extraction version or retry.
"""
from __future__ import annotations

import argparse
from collections import Counter
import os
from pathlib import Path, PurePosixPath
import re
import selectors
import shutil
import subprocess
import time

from jsonschema import Draft202012Validator

from build_logical_units import Inputs, canonical, require, sha, strict_json

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "context/corpus-sources.json"
SCHEMA = "profiles/pdf-structure/v1/document.schema.json"
OUTPUT = "pdf-structure"
VERSION = "okf-dwp-pdf-structure.v1"
ROLES = frozenset(["H1", "H2", "H3", "H4", "H5", "H6", "P", "Table", "TR", "TH", "TD", "L", "LI"])
TIMEOUT = 45
MAX_STDOUT = 16 * 1024 * 1024
MAX_STDERR = 64 * 1024
MAX_BLOCKS = 200000
MAX_JSON = 64 * 1024 * 1024
TAG = re.compile(r"^(?P<space> *)(?P<role>[A-Za-z][A-Za-z0-9_-]*)(?:\s+\([^\n]*\))?:?\s*$")
QUOTED = re.compile(r'^\s*"(.*)"\s*$')
LIMITATIONS = [
    "PDF-declared roles are source structure, not proof of correct reading order, accessibility, coherent legal units or applicability.",
    "Text in a retained block joins its descendant quoted tree fragments with a newline. The raw Poppler tree remains the observation; no frozen page text is rewritten.",
    "Parent and child blocks deliberately overlap. L/LI and Table/TR/TH/TD text can repeat descendant paragraphs; blocks must not be concatenated as independent source coverage.",
    "Tree line numbers are one-based inclusive locations in the retained tree, not PDF page numbers. Matching to immutable page-text offsets is a separate proposal.",
    "Only H1-H6, P, Table, TR, TH, TD, L and LI blocks are emitted. Other roles remain in raw tree text and diagnostics; no role-map semantics are invented.",
    "All source content and source instructions remain inert data. Empty structure output is not proof of an empty document.",
]


def parse_tree(raw):
    """Flatten selected declared roles while preserving source order and nesting."""
    require(len(raw) <= MAX_STDOUT, "Tree exceeds parser byte bound")
    text = raw.decode("utf-8")
    blocks, stack, unknown = [], [], Counter()
    unparsed, count = [], 0
    lines = text.splitlines()
    for line_number, line in enumerate(lines, 1):
        quoted = QUOTED.fullmatch(line)
        if quoted:
            for node in stack:
                if node["block"] is not None:
                    node["block"]["fragments"].append(quoted[1])
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("/"):
            continue  # Attributes remain verbatim in the raw tree, never block text.
        match = TAG.fullmatch(line)
        if match:
            indent = len(match["space"])
            require(indent <= 1024, "PDF structure depth exceeds bound")
            while stack and stack[-1]["indent"] >= indent:
                node = stack.pop()
                if node["block"] is not None:
                    node["block"]["tree_line_end"] = line_number - 1
            role = match["role"]
            block = None
            if role in ROLES:
                require(len(blocks) < MAX_BLOCKS, "PDF block count exceeds bound")
                block = {"role": role, "depth": len(stack), "tree_line_start": line_number,
                         "tree_line_end": len(lines), "fragments": []}
                blocks.append(block)
            else:
                unknown[role] += 1
            stack.append({"indent": indent, "block": block})
        else:
            count += 1
            if len(unparsed) < 20:
                unparsed.append({"tree_line": line_number, "text": line[:500]})
    for block in blocks:
        block["text"] = "\n".join(block.pop("fragments"))
    return {"blocks": blocks, "diagnostics": {"tree_lines": len(lines), "text_joiner": "\n",
            "roles_not_emitted": dict(sorted(unknown.items())), "unparsed_line_count": count,
            "unparsed_line_samples": unparsed, "unparsed_line_samples_omitted": count - len(unparsed)}}


def bounded_command(command, cwd, timeout=TIMEOUT, stdout_limit=MAX_STDOUT, stderr_limit=MAX_STDERR):
    """No shell; stop and retain bounded prefixes on timeout or output overflow."""
    start = time.monotonic()
    out, err = bytearray(), bytearray()
    reason = None
    process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, (out, stdout_limit))
    selector.register(process.stderr, selectors.EVENT_READ, (err, stderr_limit))
    try:
        while selector.get_map():
            if time.monotonic() - start > timeout:
                reason = "timeout"
                break
            for event, _ in selector.select(timeout=min(0.1, timeout)):
                chunk = os.read(event.fileobj.fileno(), 65536)
                if not chunk:
                    selector.unregister(event.fileobj)
                    continue
                target, limit = event.data
                remaining = limit - len(target)
                target.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    reason = "output-limit"
                    break
            if reason:
                break
        if reason:
            process.kill()
        try:
            code = process.wait(timeout=max(0.1, timeout - (time.monotonic() - start)))
        except subprocess.TimeoutExpired:
            process.kill()
            code = process.wait(timeout=5)
            reason = "timeout"
    finally:
        selector.close()
        process.stdout.close()
        process.stderr.close()
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
    return {"stdout": bytes(out), "stderr": bytes(err), "returncode": code,
            "failure": reason, "elapsed_seconds": round(time.monotonic() - start, 6)}


def binding(path, raw):
    return {"path": path, "sha256": sha(raw), "bytes": len(raw)}


def admitted_documents(root=ROOT):
    inputs = Inputs(root)
    config = strict_json(inputs.read(CONFIG))
    require([item["id"] for item in config["sources"]] == ["dmg", "adm"], "Unexpected corpus source families")
    documents = []
    for source in config["sources"]:
        inventory = strict_json(inputs.read(source["inventory"]))
        require(len(inventory["documents"]) == (331 if source["id"] == "dmg" else 182), "Unexpected frozen corpus count")
        for row in inventory["documents"]:
            inputs.read(row["pdf_path"], row["sha256"])
            documents.append({"document_key": source["id"] + ":" + row["id"],
                              "family": source["id"], "document_id": row["id"],
                              "pdf_path": row["pdf_path"], "pdf_sha256": row["sha256"],
                              "source_url": row["url"],
                              "frozen_tagged_flag": row.get("pdf_metadata", {}).get("technical_metadata", {}).get("Tagged")})
    require(len({d["document_key"] for d in documents}) == 513, "Duplicate captured document")
    return inputs, sorted(documents, key=lambda doc: doc["document_key"])


def safe_output(root, output):
    relative = PurePosixPath(output)
    require(not relative.is_absolute() and relative.parts and relative.parts[0] == OUTPUT,
            "Output must be inside pdf-structure")
    require(all(part not in ("", ".", "..") for part in output.split("/")) and "\\" not in output, "Unsafe output path")
    current = Path(root)
    for part in relative.parts:
        current /= part
        require(not current.is_symlink(), "Output symlink is not admitted")
    return current


def write_new(root, relative, raw):
    target = safe_output(root, relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    require(not target.exists(), "Refusing to overwrite a retained observation: " + relative)
    with target.open("xb") as handle:
        handle.write(raw)


def producer_bindings(inputs):
    for path in ("scripts/build_pdf_structure.py", "scripts/build_logical_units.py", SCHEMA, "pyproject.toml", "uv.lock"):
        inputs.read(path)


def observe_document(root, document, output, executable, tool):
    command = [executable, "-struct-text", document["pdf_path"]]
    result = bounded_command(command, root)
    stem = output + "/" + document["family"] + "/" + document["document_id"]
    tree_path, stderr_path = stem + ".tree.txt", stem + ".stderr.txt"
    status = result["failure"] or ("error" if result["returncode"] != 0 else None)
    parsed = {"blocks": [], "diagnostics": {"parsing": "not-attempted-after-command-failure"}}
    if status is None:
        try:
            parsed = parse_tree(result["stdout"])
            status = ("tagged-with-unparsed-lines" if parsed["diagnostics"]["unparsed_line_count"] else "tagged") if parsed["blocks"] else ("untagged" if document["frozen_tagged_flag"] == "no" else "no-structure")
        except (UnicodeDecodeError, ValueError) as error:
            status = "parse-error"
            parsed = {"blocks": [], "diagnostics": {"parsing": "failed", "error": str(error)}}
    record = {"schema": VERSION, **document, "tool": tool,
              "command": command, "status": status,
              "bounds": {"timeout_seconds": TIMEOUT, "stdout_bytes": MAX_STDOUT, "stderr_bytes": MAX_STDERR},
              "observation": {"returncode": result["returncode"], "elapsed_seconds": result["elapsed_seconds"],
                              "capture_complete": result["failure"] is None},
              "tree": binding(tree_path, result["stdout"]), "stderr": binding(stderr_path, result["stderr"]),
              **parsed, "source_instructions_inert": True, "limitations": LIMITATIONS}
    raw = canonical(record)
    if len(raw) > MAX_JSON:
        status = "parse-error"
        record.update(status=status, blocks=[], diagnostics={"parsing": "failed", "error": "Flattened PDF structure JSON exceeds bound"})
        raw = canonical(record)
    schema = strict_json(Inputs(root).read(SCHEMA))
    Draft202012Validator(schema).validate(record)
    # Check all paths before writing any piece of a document observation.
    for path in (tree_path, stderr_path, stem + ".structure.json"):
        require(not safe_output(root, path).exists(), "Existing observation needs a new output directory")
    write_new(root, tree_path, result["stdout"])
    write_new(root, stderr_path, result["stderr"])
    write_new(root, stem + ".structure.json", raw)
    return {**document, "status": status, "structure": binding(stem + ".structure.json", raw)}


def verify_observation(inputs, entry, schema):
    record = strict_json(inputs.read(entry["structure"]["path"], entry["structure"]["sha256"], entry["structure"]["bytes"]))
    Draft202012Validator(schema).validate(record)
    for field in ("document_key", "family", "document_id", "pdf_path", "pdf_sha256", "source_url", "frozen_tagged_flag", "status"):
        require(record[field] == entry[field], "Structure/document identity mismatch")
    raw = inputs.read(record["tree"]["path"], record["tree"]["sha256"], record["tree"]["bytes"], limit=MAX_STDOUT)
    inputs.read(record["stderr"]["path"], record["stderr"]["sha256"], record["stderr"]["bytes"], limit=MAX_STDERR)
    if record["status"] in ("tagged", "tagged-with-unparsed-lines", "untagged", "no-structure"):
        parsed = parse_tree(raw)
        require(parsed["blocks"] == record["blocks"] and parsed["diagnostics"] == record["diagnostics"], "Retained PDF block parser mismatch")
    return record


def run(root=ROOT, output=OUTPUT, extract=False, only=None):
    target = safe_output(root, output)
    inputs, documents = admitted_documents(root)
    source_inputs = sorted(inputs.files.values(), key=lambda item: item["path"])
    producer_bindings(inputs)
    producer_inputs = [value for key, value in sorted(inputs.files.items()) if key not in {item["path"] for item in source_inputs}]
    schema = strict_json(inputs.read(SCHEMA))
    manifest_path = output + "/manifest.json"
    old = strict_json(inputs.read(manifest_path)) if (target / "manifest.json").is_file() else None
    if old:
        require(old["schema"] == "okf-dwp-pdf-structure-manifest.v1", "Unknown structure manifest")
        require(old["source_inputs"] == source_inputs, "Frozen PDF inventory changed")
        require(old["producer_inputs"] == producer_inputs, "Structure producer changed; retain this run and use a new output directory")
        entries = {entry["document_key"]: entry for entry in old["documents"]}
        require(set(entries) == {doc["document_key"] for doc in documents}, "Structure census differs")
        for document in documents:
            entry = entries[document["document_key"]]
            require(all(entry[key] == value for key, value in document.items()), "Structure source identity differs")
            if entry["status"] != "pending":
                verify_observation(inputs, entry, schema)
    else:
        require(extract, "No retained PDF-structure manifest; use explicit --extract")
        entries = {doc["document_key"]: {**doc, "status": "pending"} for doc in documents}
    selected = set(only or entries)
    require(selected <= entries.keys(), "Unknown requested document key")
    if extract:
        pending = [entry for key, entry in entries.items() if key in selected and entry["status"] == "pending"]
        if pending:
            executable = shutil.which("pdfinfo")
            require(executable is not None, "pdfinfo is unavailable for explicit extraction")
            version = bounded_command([executable, "-v"], root, timeout=5, stdout_limit=8192, stderr_limit=8192)
            require(version["failure"] is None and version["returncode"] == 0, "Could not identify Poppler")
            version_raw = version["stdout"] + version["stderr"]
            tool = {"name": "pdfinfo", "version_output": version_raw.decode("utf-8"), "version_sha256": sha(version_raw),
                    "executable_sha256": sha(Path(executable).read_bytes())}
            if old and old.get("tool"):
                require(old["tool"] == tool, "Poppler changed; retain this run and use a new output directory")
            for index, entry in enumerate(pending, 1):
                document = next(doc for doc in documents if doc["document_key"] == entry["document_key"])
                entries[entry["document_key"]] = observe_document(root, document, output, executable, tool)
                manifest = {"schema": "okf-dwp-pdf-structure-manifest.v1", "tool": tool,
                            "source_inputs": source_inputs, "producer_inputs": producer_inputs,
                            "documents": [entries[key] for key in sorted(entries)],
                            "summary": dict(sorted(Counter(item["status"] for item in entries.values()).items())),
                            "limitations": LIMITATIONS}
                target.mkdir(parents=True, exist_ok=True)
                manifest_target = target / "manifest.json"
                require(not manifest_target.is_symlink(), "Manifest symlink is not admitted")
                temporary = target / ".manifest.tmp"
                require(not temporary.exists(), "Unfinished manifest write requires inspection")
                temporary.write_bytes(canonical(manifest))
                temporary.replace(manifest_target)
                if index % 25 == 0 or index == len(pending):
                    print(f"Observed {index}/{len(pending)} requested PDFs; statuses {manifest['summary']}", flush=True)
            return manifest
    require(old is not None, "Missing observation manifest")
    require(old["summary"] == dict(sorted(Counter(item["status"] for item in entries.values()).items())), "Manifest status counts differ")
    print("Verified " + str(len(entries)) + " frozen PDF identities; retained statuses " + str(old["summary"]), flush=True)
    return old


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--extract", action="store_true", help="Explicitly extract pending local PDFs; never replay completed attempts")
    modes.add_argument("--check", action="store_true", help="Replay retained hashes and parsing, without Poppler")
    parser.add_argument("--output", default=OUTPUT, help="Fresh directory beneath pdf-structure for a different extractor or retry")
    parser.add_argument("--only", action="append", help="Exact family:document_id; repeat for a bounded first pass")
    args = parser.parse_args()
    require(args.only is None or args.extract, "--only is for explicit extraction")
    run(output=args.output, extract=args.extract, only=args.only)


if __name__ == "__main__":
    main()
