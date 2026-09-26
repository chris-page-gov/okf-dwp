"""Bounded, offline-verifiable LiteParse source pilot.

The frozen cases are proposals about source presentation, not legal findings.
All page numbers here are one-based PDF indices.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
from datetime import datetime, timezone
import json
import math
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


SCHEMA = "okf-dwp-liteparse-pilot-report.v1"
MAX_JSON = 32 * 1024 * 1024
MAX_STDOUT = 2 * 1024 * 1024
MAX_STDERR = 2 * 1024 * 1024
TIMEOUT = 240
SHA = re.compile(r"^[a-f0-9]{64}$")
CASE_ID = re.compile(r"^s[12]-[0-9]{2}$")


class PilotError(ValueError):
    """Invalid frozen input or unverifiable retained artefact."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PilotError(message)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_bytes(path: Path, limit: int = MAX_JSON) -> bytes:
    require(path.is_file() and not path.is_symlink(), f"Missing or linked file: {path}")
    require(path.stat().st_size <= limit, f"Oversize file: {path}")
    return path.read_bytes()


def read_json(path: Path) -> tuple[dict, bytes]:
    raw = read_bytes(path)
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PilotError(f"Invalid JSON: {path}") from exc
    require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value, raw


def repo_path(root: Path, relative: str) -> Path:
    require(isinstance(relative, str) and relative and not Path(relative).is_absolute(), "Path must be repository relative")
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), f"Path escapes repository: {relative}")
    return path


def normalise(value: str) -> str:
    return " ".join(value.split())


def bounded_run(args: list[str], timeout: int = TIMEOUT, check: bool = True) -> tuple[subprocess.CompletedProcess[bytes], float, float]:
    start_wall = time.monotonic()
    start_cpu = os.times().children_user + os.times().children_system
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        timed_out = False
        try:
            process = subprocess.run(args, stdout=out, stderr=err, timeout=timeout, check=False)
            returncode = process.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            returncode = 124
        out_size, err_size = out.tell(), err.tell()
        out.seek(0)
        err.seek(0)
        out_hash, err_hash = hashlib.sha256(), hashlib.sha256()
        while chunk := out.read(1024 * 1024):
            out_hash.update(chunk)
        while chunk := err.read(1024 * 1024):
            err_hash.update(chunk)
        out.seek(0)
        err.seek(0)
        result = subprocess.CompletedProcess(args, returncode, out.read(MAX_STDOUT), err.read(MAX_STDERR))
        result.streams = {"stdout": {"original_bytes": out_size, "original_sha256": out_hash.hexdigest(), "truncated": out_size > MAX_STDOUT},
                          "stderr": {"original_bytes": err_size, "original_sha256": err_hash.hexdigest(), "truncated": err_size > MAX_STDERR}}
        result.timed_out = timed_out
    elapsed = time.monotonic() - start_wall
    cpu = os.times().children_user + os.times().children_system - start_cpu
    if check:
        require(not timed_out, f"Command timed out after {timeout}s: {Path(args[0]).name}")
        require(not any(s["truncated"] for s in result.streams.values()), "Command output exceeds bound")
        require(result.returncode == 0, f"Command failed ({result.returncode}): {Path(args[0]).name}; see local stderr")
    return result, elapsed, cpu


def validate_cases(root: Path, cases: dict) -> list[dict]:
    require(cases.get("schema") == "okf-dwp-liteparse-source-cases.v1", "Unexpected cases schema")
    require(cases.get("status") == "frozen-before-parser-outcomes", "Cases must be frozen before outcomes")
    entries = cases.get("cases")
    require(isinstance(entries, list) and len(entries) == 36, "Expected exactly 36 preselected cases")
    ids: set[str] = set()
    counts = {1: 0, 2: 0}
    for case in entries:
        require(isinstance(case, dict), "Case must be an object")
        case_id = case.get("id")
        stage = case.get("stage")
        require(isinstance(case_id, str) and CASE_ID.fullmatch(case_id) and case_id not in ids, "Invalid or duplicate case ID")
        require(stage in (1, 2) and case_id.startswith(f"s{stage}-"), f"Stage/ID mismatch: {case_id}")
        ids.add(case_id)
        counts[stage] += 1
        source = case.get("source")
        require(isinstance(source, dict), f"Missing source: {case_id}")
        pages = source.get("pdf_pages")
        require(isinstance(pages, list) and pages and all(type(n) is int and n > 0 for n in pages), f"Invalid pages: {case_id}")
        require(pages == list(range(pages[0], pages[-1] + 1)), f"Pages must be contiguous: {case_id}")
        require(isinstance(source.get("page_text_sha256"), list) and len(source["page_text_sha256"]) == len(pages), f"Page hash count mismatch: {case_id}")
        for key in ("pdf_sha256", "pages_sha256"):
            require(isinstance(source.get(key), str) and SHA.fullmatch(source[key]), f"Invalid {key}: {case_id}")
        require(all(isinstance(s, str) and SHA.fullmatch(s) for s in source["page_text_sha256"]), f"Invalid page text hash: {case_id}")
        for key in ("pdf_path", "pages_path"):
            path = repo_path(root, source.get(key))
            require(path.is_file() and not path.is_symlink(), f"Missing frozen source: {path}")
            require(Path(source[key]).parts[0] == "source", f"Source path outside frozen source tree: {case_id}")
        require(source["pdf_path"].endswith(".pdf") and source["pages_path"].endswith(".json"), f"Invalid source extension: {case_id}")
        anchors = case.get("critical_anchors")
        require(isinstance(anchors, list) and anchors, f"Missing anchors: {case_id}")
        require(all(isinstance(a, dict) and isinstance(a.get("text"), str) and a["text"].strip() and a.get("match") in ("whitespace-normalised-literal", "whitespace-insensitive-literal") for a in anchors), f"Invalid anchors: {case_id}")
        require(case.get("anchor_order") in ("source-order", "not-applicable"), f"Invalid anchor order: {case_id}")
        require(isinstance(case.get("expected_blocks"), list), f"Invalid expected blocks: {case_id}")
        for block in case["expected_blocks"]:
            require(isinstance(block, dict) and block.get("kind") == "table", f"Unsupported expected block: {case_id}")
            require(isinstance(block.get("contains"), list) and block["contains"] and all(isinstance(s, str) and s.strip() for s in block["contains"]), f"Invalid expected table cells: {case_id}")
            require(isinstance(block.get("columns"), list) and block["columns"] and all(isinstance(s, str) and s.strip() for s in block["columns"]), f"Invalid table columns: {case_id}")
            require(isinstance(block.get("rows"), list) and block["rows"] and all(isinstance(row, list) and len(row) == len(block["columns"]) and all(isinstance(s, str) and s.strip() for s in row) for row in block["rows"]), f"Invalid table rows: {case_id}")
    require(counts == {1: 12, 2: 24}, "Expected 12 stage-one and 24 stage-two cases")
    require(ids == {f"s1-{n:02d}" for n in range(1, 13)} | {f"s2-{n:02d}" for n in range(1, 25)}, "Case IDs must be exact")
    return entries


def verify_source(root: Path, case: dict) -> tuple[Path, list[str]]:
    source = case["source"]
    pdf = repo_path(root, source["pdf_path"])
    pages_file = repo_path(root, source["pages_path"])
    require(file_digest(pdf) == source["pdf_sha256"], f"PDF hash mismatch: {case['id']}")
    require(file_digest(pages_file) == source["pages_sha256"], f"Pages JSON hash mismatch: {case['id']}")
    page_doc, _ = read_json(pages_file)
    require(page_doc.get("source_sha256") == source["pdf_sha256"], f"Pages PDF identity mismatch: {case['id']}")
    rows = page_doc.get("pages")
    require(isinstance(rows, list), f"Missing page rows: {case['id']}")
    result = []
    for page_num, expected in zip(source["pdf_pages"], source["page_text_sha256"], strict=True):
        require(page_num <= len(rows), f"Page out of range: {case['id']}")
        row = rows[page_num - 1]
        require(row.get("page") == page_num and isinstance(row.get("text"), str), f"Page locator mismatch: {case['id']}")
        value = row["text"]
        require(digest(value.encode("utf-8")) == expected, f"Page text hash mismatch: {case['id']} page {page_num}")
        result.append(value)
    return pdf, result


def command_for(lit: Path, pdf: Path, pages: list[int], output: Path) -> list[str]:
    return [str(lit), "parse", str(pdf), "--format", "json", "--no-ocr", "--target-pages", f"{pages[0]}-{pages[-1]}", "--max-pages", str(len(pages)), "--preserve-small-text", "--keep-headers-footers", "--extract-blocks", "--extract-structure-tree", "--extract-text-metadata", "--complexity", "-o", str(output)]


def baseline_command(pdftotext: Path, pdf: Path, pages: list[int]) -> list[str]:
    return [str(pdftotext), "-f", str(pages[0]), "-l", str(pages[-1]), "-layout", "-enc", "UTF-8", str(pdf), "-"]


def find_anchors(text: str, anchors: list[dict]) -> dict:
    positions = []
    counts = []
    for anchor in anchors:
        transform = (lambda s: "".join(s.split())) if anchor["match"] == "whitespace-insensitive-literal" else normalise
        hay, needle = transform(text), transform(anchor["text"])
        positions.append(hay.find(needle))
        counts.append(hay.count(needle))
    return {"present": [p >= 0 for p in positions], "duplicate": [n > 1 for n in counts], "positions": positions}


def source_anchor_preflight(case: dict, source_text: list[str]) -> None:
    result = find_anchors("\n".join(source_text), case["critical_anchors"])
    require(all(result["present"]), f"Frozen source lacks critical anchor: {case['id']}")
    if case["anchor_order"] == "source-order":
        require(result["positions"] == sorted(result["positions"]), f"Frozen source anchor order differs: {case['id']}")


def cell_text(cell: Any) -> str | None:
    if isinstance(cell, dict):
        cell = cell.get("text")
    return normalise(cell) if isinstance(cell, str) else None


def table_cells(block: dict) -> tuple[list[str], list[list[str]]] | None:
    """Read LiteParse's separate header and rows without flattening their roles."""
    rows = block.get("rows")
    header = block.get("header")
    if not isinstance(rows, list) or not rows or not isinstance(header, (list, type(None))):
        return None
    header_values = [cell_text(cell) for cell in header] if header is not None else []
    if any(value is None for value in header_values):
        return None
    grid = []
    for row in rows:
        if not isinstance(row, list):
            return None
        values = [cell_text(cell) for cell in row]
        if any(value is None for value in values):
            return None
        grid.append(values)
    widths = {len(row) for row in grid}
    if len(widths) != 1 or 0 in widths or (header_values and len(header_values) != len(grid[0])):
        return None
    return header_values, grid


def table_match(block: dict, expected: dict) -> tuple[bool, str]:
    if block.get("kind") != "table":
        return False, "not a typed table"
    parsed = table_cells(block)
    if parsed is None:
        return False, "typed table has no explicit rectangular cell grid"
    header, rows = parsed
    width = len(expected["columns"])
    if any(len(row) != width for row in rows):
        return False, "table column count differs"
    wanted_rows = [[normalise(s) for s in row] for row in expected["rows"]]
    matches = []
    next_expected = 0
    for index, row in enumerate(rows):
        if next_expected < len(wanted_rows) and row == wanted_rows[next_expected]:
            matches.append(index)
            next_expected += 1
    if next_expected != len(wanted_rows):
        return False, "declared data rows do not match ordered cell positions"
    first_data = matches[0]
    header_area = ([header] if header else []) + rows[:first_data]
    if not header_area:
        return False, "no header cells before declared data rows"
    for col, label in enumerate(expected["columns"]):
        if not any(normalise(label) == row[col] for row in header_area if len(row) == width):
            return False, f"column {col + 1} header is not associated with {label!r}"
    all_cells = [cell for row in ([header] if header else []) + rows for cell in row]
    for phrase in expected["contains"]:
        if not any(normalise(phrase) == cell for cell in all_cells):
            return False, f"declared table text missing: {phrase!r}"
    return True, "exact ordered data rows and associated header columns"


def block_text_parts(block: dict) -> list[str]:
    result = []
    value = block.get("text")
    if isinstance(value, str):
        result.append(value)
    lines = block.get("lines")
    if isinstance(lines, list):
        result.extend(line for line in lines if isinstance(line, str))
    if block.get("kind") == "table":
        header = block.get("header")
        if isinstance(header, list):
            result.extend(value for cell in header if (value := cell_text(cell)) is not None)
        rows = block.get("rows")
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, list):
                    result.extend(value for cell in row if (value := cell_text(cell)) is not None)
    return result


def token_retention(source: str, extracted: str) -> dict:
    # Diagnostic only: extraction can join, split or reorder legitimate text.
    source_tokens = re.findall(r"\w+", normalise(source).casefold())
    extracted_tokens = re.findall(r"\w+", normalise(extracted).casefold())
    from collections import Counter
    a, b = Counter(source_tokens), Counter(extracted_tokens)
    overlap = sum((a & b).values())
    source_chars = [c for c in normalise(source).casefold() if not c.isspace()]
    extracted_chars = [c for c in normalise(extracted).casefold() if not c.isspace()]
    char_overlap = sum((Counter(source_chars) & Counter(extracted_chars)).values())
    return {"source_tokens": len(source_tokens), "extracted_tokens": len(extracted_tokens), "multiset_overlap": overlap, "source_token_retention": round(overlap / len(source_tokens), 4) if source_tokens else None,
            "source_nonspace_characters": len(source_chars), "extracted_nonspace_characters": len(extracted_chars), "character_multiset_overlap": char_overlap,
            "source_character_retention": round(char_overlap / len(source_chars), 4) if source_chars else None}


def assess_case(case: dict, source_text: list[str], raw: bytes, baseline: bytes) -> dict:
    try:
        parsed = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PilotError(f"Invalid LiteParse JSON: {case['id']}") from exc
    require(isinstance(parsed, dict), f"Invalid LiteParse root: {case['id']}")
    pages = parsed.get("pages")
    expected_pages = case["source"]["pdf_pages"]
    require(isinstance(pages, list), f"Missing LiteParse pages: {case['id']}")
    observed_pages = [p.get("page") if isinstance(p, dict) else None for p in pages]
    require(observed_pages == expected_pages, f"LiteParse page omission or order mismatch: {case['id']}: {observed_pages}")
    full_text = "\n".join(p.get("text", "") if isinstance(p.get("text"), str) else "" for p in pages)
    block_parts: list[str] = []
    all_blocks: list[dict] = []
    geometry_errors: list[str] = []
    for page in pages:
        width, height = page.get("width"), page.get("height")
        require(all(isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n) and n > 0 for n in (width, height)), f"Invalid page dimensions: {case['id']}")
        blocks = page.get("blocks")
        require(isinstance(blocks, list), f"Missing block list: {case['id']}")
        for idx, block in enumerate(blocks):
            require(isinstance(block, dict), f"Malformed block: {case['id']}")
            block_parts.extend(block_text_parts(block))
            all_blocks.append(block)
            box = block.get("bbox")
            if not isinstance(box, dict):
                geometry_errors.append(f"PDF page {page['page']} block {idx}: missing bbox")
                continue
            coords = [box.get(k) for k in ("x", "y", "width", "height")]
            if not all(isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n) for n in coords):
                geometry_errors.append(f"PDF page {page['page']} block {idx}: non-finite bbox")
                continue
            x, y, w, h = coords
            if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > width + 0.5 or y + h > height + 0.5:
                geometry_errors.append(f"PDF page {page['page']} block {idx}: bbox outside page")
            if block.get("kind") == "table":
                cell_groups = [block.get("header"), *(block.get("rows") or [])]
                for group in cell_groups:
                    if not isinstance(group, list):
                        continue
                    for cell in group:
                        if not isinstance(cell, dict) or cell.get("bbox") is None:
                            continue
                        cell_box = cell["bbox"]
                        if not isinstance(cell_box, dict):
                            geometry_errors.append(f"PDF page {page['page']} block {idx}: malformed cell bbox")
                            continue
                        cell_coords = [cell_box.get(k) for k in ("x", "y", "width", "height")]
                        if not all(isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n) for n in cell_coords):
                            geometry_errors.append(f"PDF page {page['page']} block {idx}: non-finite cell bbox")
                            continue
                        cx, cy, cw, ch = cell_coords
                        if cx < 0 or cy < 0 or cw <= 0 or ch <= 0 or cx + cw > width + 0.5 or cy + ch > height + 0.5:
                            geometry_errors.append(f"PDF page {page['page']} block {idx}: cell bbox outside page")
    block_text = "\n".join(block_parts)
    source_joined = "\n".join(source_text)
    baseline_text = baseline.decode("utf-8", errors="replace")
    anchors = case["critical_anchors"]
    source_anchor = find_anchors(source_joined, anchors)
    baseline_anchor = find_anchors(baseline_text, anchors)
    full_anchor = find_anchors(full_text, anchors)
    block_anchor = find_anchors(block_text, anchors)
    order_required = case["anchor_order"] == "source-order"
    def ordered(result: dict) -> bool:
        positions = result["positions"]
        return not order_required or (all(p >= 0 for p in positions) and positions == sorted(positions))
    table_checks = []
    for expected in case["expected_blocks"]:
        checks = [table_match(block, expected) for block in all_blocks if block.get("kind") == "table"]
        table_checks.append({"table_type": expected.get("table_type"), "columns": expected["columns"], "rows": expected["rows"], "matched_typed_table": any(ok for ok, _ in checks), "diagnostics": sorted(set(reason for _, reason in checks)) if checks else ["no typed table block"]})
    is_control = case["id"] in ("s1-01", "s1-02")
    source_control = all(source_anchor["present"]) and ordered(source_anchor)
    baseline_control = (not is_control) or (all(baseline_anchor["present"]) and ordered(baseline_anchor))
    critical = all(full_anchor["present"]) and all(block_anchor["present"]) and ordered(full_anchor) and ordered(block_anchor)
    structure = all(item["matched_typed_table"] for item in table_checks)
    return {
        "id": case["id"], "stage": case["stage"], "pdf_pages": expected_pages,
        "source_control_pass": source_control, "baseline_control_pass": baseline_control,
        "source_anchor_diagnostic": source_anchor, "baseline_anchor_diagnostic": baseline_anchor,
        "critical_anchors_pass": critical, "expected_structure_pass": structure,
        "geometry_pass": not geometry_errors, "geometry_errors": geometry_errors,
        "anchors": {"source": source_anchor, "fresh_baseline": baseline_anchor, "liteparse_full_text": full_anchor, "liteparse_block_text": block_anchor},
        "expected_tables": table_checks,
        "structural_improvement_over_baseline": bool(table_checks) and structure,
        "token_retention_diagnostic": {"full_text": token_retention(source_joined, full_text), "block_text": token_retention(source_joined, block_text)},
        "limits": ["Source roles, legal applicability and cross-page semantic correctness are unassessed.", "Token retention is a diagnostic and is not an answer-quality score."],
    }


def gate(results: list[dict], inherited_improvement: bool = False) -> dict:
    controls = all(r["source_control_pass"] and r["baseline_control_pass"] and r["critical_anchors_pass"] and r["expected_structure_pass"] and r["geometry_pass"] for r in results)
    improvement = inherited_improvement or any(r["structural_improvement_over_baseline"] for r in results)
    return {"passed": bool(controls and improvement), "all_mechanical_and_control_checks": bool(controls), "predeclared_structural_improvement": improvement, "expansion_allowed": bool(controls and improvement)}


def failed_case(case: dict, failure: str) -> dict:
    require(failure in ("liteparse-command", "liteparse-output", "baseline-command", "assessment"), "Unknown failure kind")
    return {"id": case["id"], "stage": case["stage"], "pdf_pages": case["source"]["pdf_pages"], "failure": failure,
            "source_control_pass": False, "baseline_control_pass": False, "critical_anchors_pass": False,
            "expected_structure_pass": False, "geometry_pass": False, "geometry_errors": [],
            "anchors": {}, "expected_tables": [], "structural_improvement_over_baseline": False,
            "token_retention_diagnostic": {}, "limits": ["Extraction or assessment failed; no source-quality conclusion is possible."]}


def sanitise_stderr(raw: bytes, root: Path, output: Path) -> bytes:
    value = raw.decode("utf-8", errors="replace")
    value = value.replace(str(output), "[output]").replace(str(root), "[repository]")
    value = re.sub(r"/Users/[^/\s]+/[^\s'\"]+", "[local-path]", value)
    return value.encode("utf-8")


def markdown(report: dict) -> str:
    gate_result = report["gate"]
    lines = ["# LiteParse source pilot", "", "This is an independent experimental publication, not an official DWP document.", "", f"Stage {report['stage']}: **{'pass' if gate_result['passed'] else 'fail'}** ({len(report['cases'])} frozen cases).", "", "The gate requires all source, baseline, anchor, structure and geometry checks, plus at least one predeclared typed-table improvement.", "", "| Case | PDF pages | Controls | Anchors | Structure | Geometry |", "| --- | --- | --- | --- | --- | --- |"]
    for row in report["cases"]:
        yes = lambda v: "pass" if v else "fail"
        lines.append(f"| {row['id']} | {', '.join(map(str,row['pdf_pages']))} | {yes(row['source_control_pass'] and row['baseline_control_pass'])} | {yes(row['critical_anchors_pass'])} | {yes(row['expected_structure_pass'])} | {yes(row['geometry_pass'])} |")
    lines.extend(["", "All page numbers are PDF indices. Full text and block text are checked separately. Missing or repeated anchors, reading order, typed tables and bounding boxes are detailed in report.json.", "", "Timings are one paired observation per case. Cached timings are labelled reused; they are not speedup evidence. No OCR, remote API or model call was made by this runner.", "", "Source role, legal applicability, logical cross-page joins and answer quality remain unassessed.", ""])
    return "\n".join(lines)


def platform_identity() -> dict:
    return {"system": platform.system(), "release": platform.release(), "machine": platform.machine(), "python": platform.python_version()}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def runtime_identity(root: Path, lit: Path, pdftotext: Path) -> dict:
    """Bind the Python wrapper, native engine, Poppler and dependency lock."""
    runtime_root = repo_path(root, "tools/liteparse-pilot")
    python = runtime_root / ".venv/bin/python"
    code = "import importlib.metadata as m, json; d=m.distribution('liteparse'); print(json.dumps({'version':d.version,'files':[str(f) for f in d.files if str(f).startswith('liteparse/') and str(f).endswith(('.py','.so','.dylib','.dll','.pyd'))]}))"
    result, _, _ = bounded_run([str(python), "-c", code], 20)
    info = json.loads(result.stdout)
    require(info.get("version") == "2.14.6" and isinstance(info.get("files"), list) and info["files"], "Native LiteParse runtime unavailable")
    site = next(runtime_root.glob(".venv/lib/python*/site-packages"), None)
    require(site is not None, "LiteParse site-packages unavailable")
    package_files = {}
    for relative in info["files"]:
        path = (site / relative).resolve()
        require(path.is_relative_to(site.resolve()) and path.is_file(), "Native runtime path invalid")
        package_files[relative] = file_digest(path)
    return {"lit_version": "2.14.6", "wrapper_sha256": file_digest(lit), "interpreter_sha256": file_digest(python.resolve()), "package_sha256": package_files, "uv_lock_sha256": file_digest(runtime_root / "uv.lock"), "pdftotext_sha256": file_digest(pdftotext)}


def expected_manifest(case: dict, protocol_sha: str, cases_sha: str, runtime: dict, runner_sha: str) -> dict:
    return {"case_id": case["id"], "source": case["source"], "protocol_sha256": protocol_sha, "cases_sha256": cases_sha, "runtime": runtime, "runner_sha256": runner_sha, "settings": {"format": "json", "ocr": False, "preserve_small_text": True, "keep_headers_footers": True, "extract_blocks": True, "extract_structure_tree": True, "extract_text_metadata": True, "complexity": True, "pages": case["source"]["pdf_pages"]}}


def artefact_hashes(case_dir: Path) -> dict:
    return {name: digest(read_bytes(case_dir / name)) for name in ("liteparse.json", "liteparse.stdout", "liteparse.stderr", "baseline.txt", "baseline.stderr")}


def bounded_json_file(path: Path) -> dict:
    if not path.is_file():
        path.write_bytes(b"{}\n")
        return {"original_bytes": 0, "original_sha256": digest(b""), "truncated": False, "missing": True}
    size = path.stat().st_size
    original_hash = file_digest(path)
    if size > MAX_JSON:
        with path.open("rb") as source:
            preview = source.read(min(4096, MAX_JSON))
        path.write_bytes(preview)
    return {"original_bytes": size, "original_sha256": original_hash, "truncated": size > MAX_JSON, "missing": False}


def verify_case_dir(case_dir: Path, expected: dict) -> dict:
    receipt, _ = read_json(case_dir / "receipt.json")
    require(receipt.get("inputs") == expected, f"Receipt inputs mismatch: {case_dir}")
    require(receipt.get("sha256") == artefact_hashes(case_dir), f"Raw artefact hash mismatch: {case_dir}")
    require(receipt.get("timing_provenance") in ("fresh", "reused"), f"Invalid timing provenance: {case_dir}")
    timings = receipt.get("timings")
    require(isinstance(timings, dict) and all(v is None or (isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v >= 0) for v in timings.values()), f"Invalid timings: {case_dir}")
    for key in ("liteparse_streams", "baseline_streams"):
        streams = receipt.get(key)
        require(isinstance(streams, dict) and set(streams) == {"stdout", "stderr"}, f"Missing command streams: {case_dir}")
        for stream in streams.values():
            require(isinstance(stream, dict) and type(stream.get("original_bytes")) is int and stream["original_bytes"] >= 0 and isinstance(stream.get("original_sha256"), str) and SHA.fullmatch(stream["original_sha256"]) and type(stream.get("truncated")) is bool, f"Invalid command stream record: {case_dir}")
    raw_json = receipt.get("raw_json")
    require(isinstance(raw_json, dict) and type(raw_json.get("original_bytes")) is int and raw_json["original_bytes"] >= 0 and isinstance(raw_json.get("original_sha256"), str) and SHA.fullmatch(raw_json["original_sha256"]) and type(raw_json.get("truncated")) is bool and type(raw_json.get("missing")) is bool, f"Invalid raw JSON record: {case_dir}")
    if not raw_json["truncated"] and not raw_json["missing"]:
        require(raw_json["original_bytes"] == (case_dir / "liteparse.json").stat().st_size and raw_json["original_sha256"] == digest(read_bytes(case_dir / "liteparse.json")), f"Raw JSON size/hash mismatch: {case_dir}")
    for key, name in (("liteparse_streams", "liteparse.stdout"), ("baseline_streams", "baseline.txt")):
        stream = receipt[key]["stdout"]
        if not stream["truncated"]:
            require(stream["original_bytes"] == (case_dir / name).stat().st_size and stream["original_sha256"] == digest(read_bytes(case_dir / name)), f"Command stdout size/hash mismatch: {case_dir}")
    return receipt


def verify_stage1(stage1_dir: Path, root: Path, protocol_sha: str, cases_sha: str, cases: list[dict], runtime: dict, runner_sha: str) -> None:
    report = check(stage1_dir, root, protocol_sha, cases_sha, cases, runner_sha)
    require(report["runtime"] == runtime, "Stage-one runtime differs from current stage-two runtime")
    require(report["stage"] == 1 and report["gate"]["expansion_allowed"], "Stage-one gate has not passed")


def check(output: Path, root: Path, protocol_sha: str, cases_sha: str, cases: list[dict], runner_sha: str) -> dict:
    report, raw_report = read_json(output / "report.json")
    require(report.get("schema") == SCHEMA and report.get("stage") in (1, 2), "Invalid report schema/stage")
    require(report.get("protocol_sha256") == protocol_sha and report.get("cases_sha256") == cases_sha, "Frozen protocol/cases mismatch")
    require(report.get("runner_sha256") == runner_sha, "Runner identity mismatch")
    runtime = report.get("runtime")
    require(isinstance(runtime, dict) and runtime.get("lit_version") == "2.14.6" and isinstance(runtime.get("package_sha256"), dict) and runtime["package_sha256"], "Invalid retained runtime identity")
    require(all(isinstance(v, str) and SHA.fullmatch(v) for v in list(runtime["package_sha256"].values()) + [runtime.get("wrapper_sha256"), runtime.get("interpreter_sha256"), runtime.get("uv_lock_sha256"), runtime.get("pdftotext_sha256")]), "Invalid retained runtime hashes")
    selected = [c for c in cases if c["stage"] == report["stage"]]
    inherited = False
    if report["stage"] == 2:
        prior_path = report.get("stage1_output")
        require(isinstance(prior_path, str), "Missing retained stage-one reference")
        prior_dir = repo_path(root, prior_path)
        require(prior_dir.is_relative_to(repo_path(root, "evaluation/liteparse-pilot")), "Stage-one reference outside pilot outputs")
        require(prior_dir != output, "Stage-one output cannot refer to stage two")
        prior = check(prior_dir, root, protocol_sha, cases_sha, cases, runner_sha)
        require(prior["stage"] == 1 and prior["gate"]["passed"], "Stage-one gate no longer verifies")
        require(report.get("stage1_report_sha256") == file_digest(prior_dir / "report.json"), "Stage-one report hash mismatch")
        require(prior["runtime"] == runtime, "Stage-one runtime mismatch")
        inherited = prior["gate"]["predeclared_structural_improvement"]
    require(len(report.get("cases", [])) == len(selected), "Report case count mismatch")
    recalculated = []
    for case in selected:
        _, source_text = verify_source(root, case)
        source_anchor_preflight(case, source_text)
        case_dir = output / "cases" / case["id"]
        expected = expected_manifest(case, protocol_sha, cases_sha, runtime, runner_sha)
        receipt = verify_case_dir(case_dir, expected)
        if receipt.get("failure"):
            result = failed_case(case, receipt["failure"])
        else:
            result = assess_case(case, source_text, read_bytes(case_dir / "liteparse.json"), read_bytes(case_dir / "baseline.txt"))
        result["receipt_sha256"] = file_digest(case_dir / "receipt.json")
        result["timings"] = receipt["timings"]
        result["timing_provenance"] = receipt["timing_provenance"]
        recalculated.append(result)
    rebuilt = dict(report)
    rebuilt["cases"] = recalculated
    rebuilt["gate"] = gate(recalculated, inherited)
    require(canonical(rebuilt) == raw_report, "Report is not byte-identical to recalculated metrics")
    require((output / "REPORT.md").read_bytes() == markdown(report).encode("utf-8"), "Markdown report mismatch")
    return report


def run(root: Path, output: Path, stage: int, protocol_sha: str, cases_sha: str, cases: list[dict], lit: Path, pdftotext: Path, runner_sha: str, cache_dir: Path | None, stage1_dir: Path | None) -> dict:
    runtime = runtime_identity(root, lit, pdftotext)
    version, _, _ = bounded_run([str(lit), "--version"], 20)
    require(version.stdout.decode("utf-8", errors="replace").strip() == "lit 2.14.6", "LiteParse version differs from 2.14.6")
    selected = [c for c in cases if c["stage"] == stage]
    source_texts = {c["id"]: verify_source(root, c)[1] for c in selected}
    for case in selected:
        source_anchor_preflight(case, source_texts[case["id"]])
    prior_report = None
    if stage == 2:
        require(stage1_dir is not None, "Stage two requires --stage1-dir")
        verify_stage1(stage1_dir, root, protocol_sha, cases_sha, cases, runtime, runner_sha)
        prior_report, _ = read_json(stage1_dir / "report.json")
    require(not output.exists(), "Output directory already exists; choose a new versioned directory")
    output.mkdir(parents=True, exist_ok=False)
    (output / "cases").mkdir()
    results = []
    for case in selected:
        source = case["source"]
        pdf = repo_path(root, source["pdf_path"])
        case_dir = output / "cases" / case["id"]
        case_dir.mkdir()
        expected = expected_manifest(case, protocol_sha, cases_sha, runtime, runner_sha)
        cache_key = digest(canonical(expected))
        cached = cache_dir / cache_key if cache_dir else None
        failure = None
        if cached and cached.exists():
            receipt = verify_case_dir(cached, expected)
            for name in ("liteparse.json", "liteparse.stdout", "liteparse.stderr", "baseline.txt", "baseline.stderr"):
                (case_dir / name).write_bytes(read_bytes(cached / name))
            timings = receipt["timings"]
            provenance = "reused"
            failure = receipt.get("failure")
            liteparse_streams = receipt["liteparse_streams"]
            baseline_streams = receipt["baseline_streams"]
            raw_json = receipt["raw_json"]
        else:
            command = command_for(lit, pdf, source["pdf_pages"], case_dir / "liteparse.json")
            parse_elapsed = parse_cpu = base_elapsed = base_cpu = None
            empty_streams = {"stdout": {"original_bytes": 0, "original_sha256": digest(b""), "truncated": False}, "stderr": {"original_bytes": 0, "original_sha256": digest(b""), "truncated": False}}
            liteparse_streams = empty_streams
            baseline_streams = empty_streams
            try:
                parsed, parse_elapsed, parse_cpu = bounded_run(command, check=False)
                liteparse_streams = parsed.streams
                (case_dir / "liteparse.stdout").write_bytes(parsed.stdout)
                (case_dir / "liteparse.stderr").write_bytes(sanitise_stderr(parsed.stderr, root, output))
                require(not parsed.timed_out, "LiteParse timed out")
                require(not any(s["truncated"] for s in parsed.streams.values()), "LiteParse stream exceeded bound")
                require(parsed.returncode == 0, f"LiteParse exited {parsed.returncode}")
                require(not parsed.stdout, "Unexpected LiteParse stdout")
            except PilotError as exc:
                failure = "liteparse-command"
                if not (case_dir / "liteparse.stdout").is_file():
                    (case_dir / "liteparse.stdout").write_bytes(b"")
                if not (case_dir / "liteparse.stderr").is_file():
                    (case_dir / "liteparse.stderr").write_bytes(sanitise_stderr(str(exc).encode(), root, output))
            raw_json = bounded_json_file(case_dir / "liteparse.json")
            if raw_json["truncated"] or raw_json["missing"]:
                failure = failure or "liteparse-output"
            try:
                baseline, base_elapsed, base_cpu = bounded_run(baseline_command(pdftotext, pdf, source["pdf_pages"]), check=False)
                baseline_streams = baseline.streams
                (case_dir / "baseline.stderr").write_bytes(sanitise_stderr(baseline.stderr, root, output))
                (case_dir / "baseline.txt").write_bytes(baseline.stdout)
                require(not baseline.timed_out, "pdftotext timed out")
                require(not any(s["truncated"] for s in baseline.streams.values()), "pdftotext stream exceeded bound")
                require(baseline.returncode == 0, f"pdftotext exited {baseline.returncode}")
            except PilotError as exc:
                failure = failure or "baseline-command"
                if not (case_dir / "baseline.txt").is_file():
                    (case_dir / "baseline.txt").write_bytes(b"")
                if not (case_dir / "baseline.stderr").is_file():
                    (case_dir / "baseline.stderr").write_bytes(sanitise_stderr(str(exc).encode(), root, output))
            timings = {"liteparse_elapsed_seconds": round(parse_elapsed, 6) if parse_elapsed is not None else None, "liteparse_child_cpu_seconds": round(parse_cpu, 6) if parse_cpu is not None else None, "pdftotext_elapsed_seconds": round(base_elapsed, 6) if base_elapsed is not None else None, "pdftotext_child_cpu_seconds": round(base_cpu, 6) if base_cpu is not None else None}
            provenance = "fresh"
        if not failure:
            try:
                result = assess_case(case, source_texts[case["id"]], read_bytes(case_dir / "liteparse.json"), read_bytes(case_dir / "baseline.txt"))
            except PilotError:
                failure = "assessment"
        if failure:
            result = failed_case(case, failure)
        receipt = {"inputs": expected, "sha256": artefact_hashes(case_dir), "timings": timings, "timing_provenance": provenance, "failure": failure, "raw_json": raw_json, "liteparse_streams": liteparse_streams, "baseline_streams": baseline_streams, "captured_at_utc": utc_now(), "platform": platform_identity(), "lit_version": "lit 2.14.6", "command_count": {"liteparse": 0 if provenance == "reused" else 1, "pdftotext": 0 if provenance == "reused" else 1, "ocr": 0, "remote_api": 0, "llm": 0}}
        (case_dir / "receipt.json").write_bytes(canonical(receipt))
        if cached and not cached.exists() and not failure:
            cached.mkdir(parents=True, exist_ok=False)
            for name in ("liteparse.json", "liteparse.stdout", "liteparse.stderr", "baseline.txt", "baseline.stderr", "receipt.json"):
                (cached / name).write_bytes(read_bytes(case_dir / name))
        result["receipt_sha256"] = file_digest(case_dir / "receipt.json")
        result["timings"] = timings
        result["timing_provenance"] = provenance
        results.append(result)
    report = {"schema": SCHEMA, "stage": stage, "protocol_sha256": protocol_sha, "cases_sha256": cases_sha, "runtime": runtime, "runner_sha256": runner_sha, "platform": platform_identity(), "captured_at_utc": utc_now(), "cases": results, "gate": gate(results, bool(prior_report and prior_report["gate"]["predeclared_structural_improvement"])), "limits": ["One paired observation per case; timings are not a benchmark or speedup claim.", "No legal applicability, source-role or semantic cross-page conclusion is established."]}
    if stage == 2:
        report["stage1_output"] = stage1_dir.relative_to(root).as_posix()
        report["stage1_report_sha256"] = file_digest(stage1_dir / "report.json")
    (output / "report.json").write_bytes(canonical(report))
    (output / "REPORT.md").write_text(markdown(report), encoding="utf-8")
    return report
