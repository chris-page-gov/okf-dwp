"""Negative controls for full-DMG acquisition identity and resume boundaries."""

import json
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch

import acquire_full_dmg as acquisition


class FakeResponse:
    def __init__(self, raw, headers=None):
        self.raw = raw
        self.headers = headers or {}
        self.url = "https://assets.publishing.service.gov.uk/example.pdf"
        self.status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size):
        result, self.raw = self.raw[:size], self.raw[size:]
        return result


class AcquisitionTests(unittest.TestCase):
    def test_external_redirect_and_credentialled_urls_are_rejected_before_fetch(self):
        for url in ["http://www.gov.uk/a.pdf", "https://www.gov.uk.evil.test/a.pdf",
                    "https://user:password@www.gov.uk/a.pdf", "https://www.gov.uk:444/a.pdf",
                    "https://www.gov.uk/a.pdf#fragment", "https://www.gov.uk/a\n.pdf"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                acquisition.check_url(url)
        request = urllib.request.Request("https://www.gov.uk/a.pdf")
        with self.assertRaises(ValueError):
            acquisition.CheckedRedirect().redirect_request(request, None, 302, "Found", {}, "https://example.com/private.pdf")

    def test_actual_stream_size_is_bounded_without_content_length(self):
        response = FakeResponse(b"%PDF-" + b"x" * 50)
        with patch.object(acquisition, "MAX_PDF_BYTES", 10), patch.object(acquisition.urllib.request, "build_opener") as opener:
            opener.return_value.open.return_value = response
            with self.assertRaises(acquisition.AcquisitionFailure) as caught:
                acquisition.fetch_pdf(response.url)
        self.assertIn("measured byte limit", str(caught.exception))
        self.assertEqual(200, caught.exception.observation["http_status"])
        self.assertIn("observed_at", caught.exception.observation)

    def test_oversized_declared_length_and_non_pdf_body_fail(self):
        for response in [FakeResponse(b"%PDF-small", {"Content-Length": str(acquisition.MAX_PDF_BYTES + 1)}),
                         FakeResponse(b"<html>Not a PDF</html>")]:
            with self.subTest(response=response), patch.object(acquisition.urllib.request, "build_opener") as opener:
                opener.return_value.open.return_value = response
                with self.assertRaises(acquisition.AcquisitionFailure):
                    acquisition.fetch_pdf(response.url)

    def test_page_boundaries_preserve_empty_pages_and_reject_mismatch(self):
        self.assertEqual(["first", "", "third"], acquisition.split_pages("first\f\fthird\f", 3))
        with self.assertRaises(ValueError):
            acquisition.split_pages("first\fthird\f", 3)

    def test_quality_flags_are_evidence_signals_and_do_not_rewrite_text(self):
        text = " ".join(["a", "b", "c", "word"] * 30)
        quality = acquisition.assess_quality(["", text, "\ufffd imperfect"])
        self.assertEqual(1, quality["flag_counts"]["no-machine-extracted-text"])
        self.assertEqual(1, quality["flag_counts"]["possible-letter-spacing-defect"])
        self.assertEqual(1, quality["flag_counts"]["unicode-replacement-characters"])
        self.assertEqual("not-reviewed", quality["human_review_status"])

    def original_fixture(self, root):
        url = "https://assets.publishing.service.gov.uk/example.pdf"
        pdf, text = b"%PDF-test", b"page text\f"
        record = {"id": "original", "url": url, "sha256": acquisition.digest(pdf), "size_bytes": len(pdf),
                  "text_sha256": acquisition.digest(text), "pages": 1, "observed_at": "2026-01-01T01:00:00Z",
                  "pdf_path": "source/original.pdf", "text_path": "source/original.txt", "pages_path": "source/original.json",
                  "http": {"requested_url": url, "resolved_url": url, "observed_at": "2026-01-01T01:00:00Z"}}
        (root / "source").mkdir()
        (root / record["pdf_path"]).write_bytes(pdf)
        (root / record["text_path"]).write_bytes(text)
        (root / record["pages_path"]).write_text(json.dumps({
            "document_id": "original", "source_url": url, "source_sha256": record["sha256"],
            "pages": [{"page": 1, "url": url + "#page=1", "text": "page text"}],
        }))
        return record

    def test_original_observation_and_paths_survive_reuse_but_tampering_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = self.original_fixture(root)
            with patch.object(acquisition, "ROOT", root), patch.object(acquisition, "checked_path", side_effect=lambda value: root / value), \
                    patch.object(acquisition, "pdf_information", return_value=(1, {})):
                record = acquisition.reuse_original({"id": original["id"], "url": original["url"]}, original)
                for field in ["observed_at", "pdf_path", "text_path", "pages_path", "http"]:
                    self.assertEqual(original[field], record[field])
                record["quality"]["flag_counts"] = {"fabricated-flag": 1}
                with self.assertRaisesRegex(ValueError, "Quality metrics differ"):
                    acquisition.validate_completed_record(record, {original["url"]: original})
                page_path = root / original["pages_path"]
                page_data = json.loads(page_path.read_text())
                page_data["pages"][0]["url"] = original["url"] + "#page=999"
                page_path.write_text(json.dumps(page_data))
                with self.assertRaisesRegex(ValueError, "locator/text mismatch"):
                    acquisition.reuse_original({"id": original["id"], "url": original["url"]}, original)

    def test_interrupted_download_recovers_only_matching_prior_http_observation(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / "pdf").mkdir()
            (output / "attempts/doc").mkdir(parents=True)
            raw = b"%PDF-real-observed-bytes"
            (output / "pdf/doc.pdf").write_bytes(raw)
            url = "https://assets.publishing.service.gov.uk/example.pdf"
            receipt = {"status": "downloaded", "requested_url": url, "resolved_url": url, "bytes": len(raw),
                       "sha256": acquisition.digest(raw), "observed_at": "2026-01-01T01:00:00Z"}
            acquisition.atomic_json(output / "attempts/doc/001.json", receipt)
            with patch.object(acquisition, "fetch_pdf", side_effect=AssertionError("No network on recovery")):
                _, recovered = acquisition.download_or_resume({"id": "doc", "url": url}, output, 1)
            self.assertEqual(receipt["observed_at"], recovered["observed_at"])
            (output / "pdf/doc.pdf").write_bytes(b"%PDF-altered")
            with self.assertRaisesRegex(ValueError, "byte hash mismatch"):
                acquisition.download_or_resume({"id": "doc", "url": url}, output, 1)

    def test_frozen_input_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "input.json").write_text("{}")
            with patch.object(acquisition, "ROOT", root), patch.object(acquisition, "PINNED_INPUTS", {"input.json": "0" * 64}):
                with self.assertRaisesRegex(ValueError, "Frozen input hash mismatch"):
                    acquisition.load_inputs()


if __name__ == "__main__":
    unittest.main()
