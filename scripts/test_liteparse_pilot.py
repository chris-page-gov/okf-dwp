"""Focused synthetic checks for the frozen LiteParse pilot harness."""

from __future__ import annotations

import json
import tempfile
import unittest
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from liteparse_pilot import (PilotError, artefact_hashes, assess_case, canonical,
                             bounded_json_file, check, command_for, digest, expected_manifest, file_digest, gate, markdown,
                             read_bytes, source_anchor_preflight, validate_cases, verify_case_dir, verify_source)


def synthetic_case(root: Path) -> dict:
    (root / "source").mkdir(exist_ok=True)
    pdf = root / "source/example.pdf"
    pdf.write_bytes(b"synthetic PDF bytes only; never passed to a parser")
    page_text = "Heading\nFirst evidence line. Second evidence line."
    pages = root / "source/example.json"
    pages.write_bytes(canonical({"source_sha256": file_digest(pdf), "pages": [{"page": 1, "text": page_text}]}))
    return {"id": "s1-01", "stage": 1, "source": {"pdf_path": "source/example.pdf", "pdf_sha256": file_digest(pdf), "pages_path": "source/example.json", "pages_sha256": file_digest(pages), "pdf_pages": [1], "page_text_sha256": [digest(page_text.encode())]}, "critical_anchors": [{"text": "First evidence line.", "match": "whitespace-normalised-literal"}, {"text": "Second evidence line.", "match": "whitespace-normalised-literal"}], "anchor_order": "source-order", "expected_blocks": []}


def output(*, text: str = "Heading\nFirst evidence line. Second evidence line.", bbox: dict | None = None, page: int = 1) -> bytes:
    if bbox is None:
        bbox = {"x": 10, "y": 10, "width": 200, "height": 20}
    return canonical({"pages": [{"page": page, "width": 300, "height": 300, "text": text, "blocks": [{"kind": "paragraph", "text": text, "bbox": bbox}]}]})


def write_multipage_pdf(path: Path, count: int = 5) -> None:
    objects: list[bytes] = [b"<< /Type /Catalog /Pages 2 0 R >>", b"", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    page_ids = []
    for number in range(1, count + 1):
        page_id = len(objects) + 1
        content_id = page_id + 1
        page_ids.append(page_id)
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>".encode())
        stream = f"BT /F1 16 Tf 72 700 Td (Synthetic PDF page {number}) Tj ET".encode()
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
    objects[1] = ("<< /Type /Pages /Kids [" + " ".join(f"{n} 0 R" for n in page_ids) + f"] /Count {count} >>").encode()
    data = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, 1):
        offsets.append(len(data))
        data.extend(f"{number} 0 obj\n".encode() + body + b"\nendobj\n")
    xref = len(data)
    data.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets:
        data.extend(f"{offset:010d} 00000 n \n".encode())
    data.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    path.write_bytes(data)


class PilotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.case = synthetic_case(self.root)
        self.source_text = ["Heading\nFirst evidence line. Second evidence line."]

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_source_hash_mismatch(self) -> None:
        verify_source(self.root, self.case)
        (self.root / "source/example.pdf").write_bytes(b"altered")
        with self.assertRaisesRegex(PilotError, "PDF hash mismatch"):
            verify_source(self.root, self.case)

    def test_every_frozen_source_anchor_is_checked(self) -> None:
        source_anchor_preflight(self.case, self.source_text)
        self.case["critical_anchors"].append({"text": "Absent phrase", "match": "whitespace-normalised-literal"})
        with self.assertRaisesRegex(PilotError, "Frozen source lacks critical anchor"):
            source_anchor_preflight(self.case, self.source_text)

    def test_missing_output_page_is_rejected(self) -> None:
        with self.assertRaisesRegex(PilotError, "page omission"):
            assess_case(self.case, self.source_text, canonical({"pages": []}), b"First evidence line. Second evidence line.")

    def test_missing_anchor_and_geometry_fail_gate(self) -> None:
        row = assess_case(self.case, self.source_text, output(text="Heading\nFirst evidence line."), b"First evidence line. Second evidence line.")
        self.assertFalse(row["critical_anchors_pass"])
        self.assertFalse(gate([row])["passed"])
        row = assess_case(self.case, self.source_text, output(bbox={"x": 10, "y": 10, "width": float("nan"), "height": 20}), b"First evidence line. Second evidence line.")
        self.assertFalse(row["geometry_pass"])

    def test_output_page_identity_mismatch_is_rejected(self) -> None:
        with self.assertRaisesRegex(PilotError, "page omission"):
            assess_case(self.case, self.source_text, output(page=2), b"First evidence line. Second evidence line.")

    def test_stage_identity_mismatch_is_rejected(self) -> None:
        self.case["stage"] = 2
        cases_doc = {"schema": "okf-dwp-liteparse-source-cases.v1", "status": "frozen-before-parser-outcomes", "cases": [self.case] * 36}
        with self.assertRaisesRegex(PilotError, "Stage/ID mismatch"):
            validate_cases(self.root, cases_doc)

    def test_cache_tamper_is_rejected_offline(self) -> None:
        case_dir = self.root / "cache"
        case_dir.mkdir()
        (case_dir / "liteparse.json").write_bytes(output())
        (case_dir / "liteparse.stdout").write_bytes(b"")
        (case_dir / "liteparse.stderr").write_bytes(b"")
        (case_dir / "baseline.txt").write_bytes(b"First evidence line. Second evidence line.")
        (case_dir / "baseline.stderr").write_bytes(b"")
        expected = expected_manifest(self.case, "a" * 64, "b" * 64, {"lit_version": "2.14.6"}, "runner")
        empty = {"stdout": {"original_bytes": 0, "original_sha256": digest(b""), "truncated": False}, "stderr": {"original_bytes": 0, "original_sha256": digest(b""), "truncated": False}}
        (case_dir / "receipt.json").write_bytes(canonical({"inputs": expected, "sha256": artefact_hashes(case_dir), "timings": {}, "timing_provenance": "fresh", "liteparse_streams": empty, "baseline_streams": {**empty, "stdout": {"original_bytes": len(b"First evidence line. Second evidence line."), "original_sha256": digest(b"First evidence line. Second evidence line."), "truncated": False}}, "raw_json": {"original_bytes": len(output()), "original_sha256": digest(output()), "truncated": False, "missing": False}}))
        verify_case_dir(case_dir, expected)
        (case_dir / "liteparse.json").write_bytes(output(text="tampered"))
        with self.assertRaisesRegex(PilotError, "Raw artefact hash mismatch"):
            verify_case_dir(case_dir, expected)

    def test_exact_table_cells_are_required(self) -> None:
        self.case["expected_blocks"] = [{"kind": "table", "table_type": "two-column", "columns": ["Left", "Right"], "rows": [["A", "B"]], "contains": ["A", "B"]}]
        value = json.loads(output())
        value["pages"][0]["blocks"] = [{"kind": "table", "text": "Left Right A B", "bbox": {"x": 10, "y": 10, "width": 200, "height": 20}}]
        row = assess_case(self.case, self.source_text, canonical(value), b"First evidence line. Second evidence line.")
        self.assertFalse(row["expected_structure_pass"])
        value["pages"][0]["blocks"][0]["header"] = [{"text": "Left"}, {"text": "Right"}]
        value["pages"][0]["blocks"][0]["rows"] = [[{"text": "A"}, {"text": "B"}]]
        row = assess_case(self.case, self.source_text, canonical(value), b"First evidence line. Second evidence line.")
        self.assertTrue(row["expected_structure_pass"])

    def test_multilevel_table_header_and_grid_text(self) -> None:
        self.case["critical_anchors"] = [{"text": "From To", "match": "whitespace-normalised-literal"}, {"text": "10,000.01 10,500.00", "match": "whitespace-normalised-literal"}]
        self.case["expected_blocks"] = [{"kind": "table", "table_type": "capital-band", "columns": ["From", "To", "Income"], "rows": [["10,000.01", "10,500.00", "1"]], "contains": ["Total capital", "10,000.01"]}]
        block = {"kind": "table", "bbox": {"x": 10, "y": 10, "width": 200, "height": 100}, "header": [{"text": "Total capital"}, {"text": ""}, {"text": "Income"}], "rows": [[{"text": "From"}, {"text": "To"}, {"text": ""}], [{"text": "10,000.01"}, {"text": "10,500.00"}, {"text": "1"}]]}
        value = {"pages": [{"page": 1, "width": 300, "height": 300, "text": "From To 10,000.01 10,500.00", "blocks": [block, {"kind": "grid_fallback", "lines": ["Grid line"], "bbox": {"x": 10, "y": 120, "width": 100, "height": 10}}]}]}
        row = assess_case(self.case, self.source_text, canonical(value), b"From To 10,000.01 10,500.00")
        self.assertTrue(row["expected_structure_pass"])
        self.assertTrue(row["anchors"]["liteparse_block_text"]["present"][0])
        block["rows"][1][0]["text"], block["rows"][1][1]["text"] = block["rows"][1][1]["text"], block["rows"][1][0]["text"]
        row = assess_case(self.case, self.source_text, canonical(value), b"From To 10,000.01 10,500.00")
        self.assertFalse(row["expected_structure_pass"])

    def test_oversize_json_preserves_bounded_diagnostic(self) -> None:
        import unittest.mock as mock
        path = self.root / "oversize.json"
        original = b"x" * 100
        path.write_bytes(original)
        with mock.patch("liteparse_pilot.MAX_JSON", 64):
            metadata = bounded_json_file(path)
        self.assertEqual(metadata["original_bytes"], len(original))
        self.assertEqual(metadata["original_sha256"], digest(original))
        self.assertTrue(metadata["truncated"])
        self.assertLessEqual(path.stat().st_size, len(original))

    def test_high_target_pages_survive_max_pages_cap(self) -> None:
        lit = Path(__file__).resolve().parents[1] / "tools/liteparse-pilot/.venv/bin/lit"
        if not lit.is_file():
            self.skipTest("Pinned LiteParse runtime is unavailable")
        pdf = self.root / "five-pages.pdf"
        result = self.root / "result.json"
        write_multipage_pdf(pdf)
        run = subprocess.run(command_for(lit, pdf, [4, 5], result), capture_output=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr.decode(errors="replace"))
        pages = json.loads(result.read_bytes())["pages"]
        self.assertEqual([p["page"] for p in pages], [4, 5])
        self.assertEqual([p["text"] for p in pages], ["Synthetic PDF page 4", "Synthetic PDF page 5"])

    def test_cli_rejects_source_git_and_overlapping_paths(self) -> None:
        script = Path(__file__).resolve().parent / "run_liteparse_pilot.py"
        root = script.parents[1]
        scenarios = [
            ["--check", "--output", "source/stage-1-test"],
            ["--check", "--output", ".git/stage-1-test"],
            ["--stage", "1", "--output", "evaluation/liteparse-pilot/stage-1-test", "--cache-dir", "evaluation/liteparse-pilot/stage-1-test/cache"],
        ]
        for arguments in scenarios:
            result = subprocess.run([sys.executable, str(script), *arguments], cwd=root, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 2, arguments)
            self.assertIn(b"LiteParse pilot:", result.stderr)

    def test_offline_report_recalculation_rejects_tampering(self) -> None:
        runtime = {"lit_version": "2.14.6", "package_sha256": {"engine.so": "a" * 64}, "wrapper_sha256": "b" * 64, "interpreter_sha256": "e" * 64, "uv_lock_sha256": "c" * 64, "pdftotext_sha256": "d" * 64}
        case_dir = self.root / "result/cases/s1-01"
        case_dir.mkdir(parents=True)
        (case_dir / "liteparse.json").write_bytes(output())
        (case_dir / "liteparse.stdout").write_bytes(b"")
        (case_dir / "liteparse.stderr").write_bytes(b"")
        (case_dir / "baseline.txt").write_bytes(b"First evidence line. Second evidence line.")
        (case_dir / "baseline.stderr").write_bytes(b"")
        inputs = expected_manifest(self.case, "e" * 64, "f" * 64, runtime, "runner")
        empty = {"original_bytes": 0, "original_sha256": digest(b""), "truncated": False}
        base = b"First evidence line. Second evidence line."
        receipt = {"inputs": inputs, "sha256": artefact_hashes(case_dir), "timings": {}, "timing_provenance": "fresh", "failure": None, "liteparse_streams": {"stdout": empty, "stderr": empty}, "baseline_streams": {"stdout": {"original_bytes": len(base), "original_sha256": digest(base), "truncated": False}, "stderr": empty}, "raw_json": {"original_bytes": len(output()), "original_sha256": digest(output()), "truncated": False, "missing": False}}
        (case_dir / "receipt.json").write_bytes(canonical(receipt))
        row = assess_case(self.case, self.source_text, output(), b"First evidence line. Second evidence line.")
        row.update(receipt_sha256=file_digest(case_dir / "receipt.json"), timings={}, timing_provenance="fresh")
        report = {"schema": "okf-dwp-liteparse-pilot-report.v1", "stage": 1, "protocol_sha256": "e" * 64, "cases_sha256": "f" * 64, "runtime": runtime, "runner_sha256": "runner", "cases": [row], "gate": gate([row])}
        (self.root / "result/report.json").write_bytes(canonical(report))
        (self.root / "result/REPORT.md").write_text(markdown(report), encoding="utf-8")
        check(self.root / "result", self.root, "e" * 64, "f" * 64, [self.case], "runner")
        (case_dir / "liteparse.json").write_bytes(output(text="tampered"))
        with self.assertRaisesRegex(PilotError, "Raw artefact hash mismatch"):
            check(self.root / "result", self.root, "e" * 64, "f" * 64, [self.case], "runner")


if __name__ == "__main__":
    unittest.main()
