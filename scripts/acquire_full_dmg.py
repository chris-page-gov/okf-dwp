#!/usr/bin/env python3
"""Acquire the frozen full-DMG census without replacing the Pension Credit snapshot.

Only the standard library and installed Poppler are used. Completed document
records are committed atomically after their files and checked on every resume.
The frozen census, its API receipts and the original inventory are pinned below.
No collection discovery, ADM acquisition, OCR or legal interpretation occurs.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DISCOVERY = ROOT / "source/discovery-2026-09-15"
OUTPUT = ROOT / "source/full-dmg-2026-09-15"
PINNED_INPUTS = {
    "source/discovery-2026-09-15/census.json": "445308cd5cba91d997f21b8408cb8cfeb52e2a888f291492bcdcc41c16c2be88",
    "source/discovery-2026-09-15/receipts.json": "15878dd2ed56ed1fff73053860a15c0c60592420cc1dfae7e5f191646760fc2c",
    "source/inventory.json": "bf225f86a43959d45e59204d3de34dccba6590970626eb659038febca47889df",
}
ALLOWED_HOSTS = {"www.gov.uk", "assets.publishing.service.gov.uk"}
MAX_PDF_BYTES = 32 * 1024 * 1024
MAX_TEXT_BYTES = 64 * 1024 * 1024
SOCKET_TIMEOUT_SECONDS = 30
DOWNLOAD_TIMEOUT_SECONDS = 120
EXTRACTION_TIMEOUT_SECONDS = 120
EXTRACTION_LIMITATIONS = (
    "Unreviewed machine text extraction. Reading order, footnotes, tables and "
    "characters require comparison with the PDF. Page indices are one-based "
    "PDF pages, not printed page labels. Empty or sparse text is not proof of a "
    "blank page. No OCR or automatic word repair was performed."
)
CLASSIFICATIONS = {
    "chapter-current-listed": ("chapter", "substantive"),
    "chapter-spare": ("chapter", "spare"),
    "chapter-transitional": ("chapter", "transitional"),
    "amendment-record": ("historical-amendment", "historical-amendment-not-current-rules"),
    "change-summary": ("change-summary", "change-history"),
    "memo": ("memo", "supplementary-guidance-applicability-unreviewed"),
    "annex-listed": ("annex", "annex-applicability-unreviewed"),
    "abbreviations": ("abbreviations", "reference"),
    "legislation-reference-list": ("legislation-reference-list", "reference-not-legislation-text"),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as file:
        temporary = Path(file.name)
        try:
            file.write(raw)
            file.flush()
            os.fsync(file.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_json(path: Path, value: object) -> None:
    atomic_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def checked_path(value: str, *, within: Path = ROOT / "source") -> Path:
    path = ROOT / value
    if path.is_symlink() or not path.resolve().is_relative_to(within.resolve()):
        raise ValueError(f"Evidence path escapes its allowed source tree: {value}")
    return path


def check_url(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS
        or parsed.username or parsed.password or parsed.port not in (None, 443)
        or parsed.fragment or "\\" in url or any(ord(c) <= 32 or ord(c) == 127 for c in url)
    ):
        raise ValueError(f"URL is outside the credential-free GOV.UK HTTPS allowlist: {url!r}")


class CheckedRedirect(urllib.request.HTTPRedirectHandler):
    max_redirections = 5
    max_repeats = 2

    def __init__(self):
        super().__init__()
        self.observations: list[dict] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        destination = urllib.parse.urljoin(req.full_url, newurl)
        check_url(destination)
        self.observations.append({
            "status": code, "from_url": req.full_url, "to_url": destination,
            "observed_at": utc_now(),
        })
        return super().redirect_request(req, fp, code, msg, headers, destination)


class AcquisitionFailure(RuntimeError):
    def __init__(self, message: str, observation: dict):
        super().__init__(message)
        self.observation = observation


def fetch_pdf(url: str) -> tuple[bytes, dict]:
    check_url(url)
    started = time.monotonic()
    redirect = CheckedRedirect()
    observation = {"requested_url": url, "started_at": utc_now(), "redirects": redirect.observations}
    request = urllib.request.Request(url, headers={
        "User-Agent": "okf-dwp/0.2 (independent public guidance research; bounded snapshot acquisition)",
        "Accept": "application/pdf", "Accept-Encoding": "identity",
    })
    try:
        opener = urllib.request.build_opener(redirect)
        with opener.open(request, timeout=SOCKET_TIMEOUT_SECONDS) as response:
            check_url(response.url)
            observation.update({
                "resolved_url": response.url, "http_status": response.status,
                "content_type": response.headers.get("Content-Type"),
                "content_length": response.headers.get("Content-Length"),
                "content_encoding": response.headers.get("Content-Encoding"),
                "last_modified": response.headers.get("Last-Modified"),
                "etag": response.headers.get("ETag"), "date": response.headers.get("Date"),
            })
            length = response.headers.get("Content-Length")
            if length is not None and (not length.isdecimal() or int(length) > MAX_PDF_BYTES):
                raise ValueError("Invalid or oversized declared HTTP content length")
            if response.status != 200:
                raise ValueError(f"Expected HTTP 200, received {response.status}")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise ValueError("Unexpected HTTP content encoding; only unchanged PDF bytes are accepted")
            chunks = []
            size = 0
            while True:
                if time.monotonic() - started > DOWNLOAD_TIMEOUT_SECONDS:
                    raise TimeoutError("Overall PDF download deadline exceeded")
                chunk = response.read(65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_PDF_BYTES:
                    raise ValueError("PDF exceeds the measured byte limit")
                chunks.append(chunk)
            raw = b"".join(chunks)
            if length is not None and len(raw) != int(length):
                raise ValueError("Measured PDF bytes differ from HTTP Content-Length")
            if not raw.startswith(b"%PDF-"):
                raise ValueError("Response lacks a PDF file signature")
        observation.update({"observed_at": utc_now(), "bytes": len(raw), "sha256": digest(raw)})
        return raw, observation
    except Exception as exc:
        if isinstance(exc, urllib.error.HTTPError):
            observation.update({"http_status": exc.code, "resolved_url": exc.url})
        observation.update({"observed_at": utc_now(), "error_type": type(exc).__name__, "error": str(exc)})
        raise AcquisitionFailure(str(exc), observation) from exc
    finally:
        observation["elapsed_seconds"] = round(time.monotonic() - started, 6)


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def document_description(attachment: dict, publication: dict, originals: dict) -> dict:
    title = attachment["title"]
    category = attachment["discovery_classification"]
    kind, role = CLASSIFICATIONS[category]
    volume_match = re.search(r"\bVol\s+(\d+)", title, re.I)
    chapter_match = re.search(r"\bCh\s+(\d+)", title, re.I)
    part_match = re.search(r"\bPart\s+(\d+)", title, re.I)
    amendment_match = re.search(r"\bAmendment\s+(\d+)", title, re.I)
    volume = int(volume_match[1]) if volume_match else None
    chapter = int(chapter_match[1]) if chapter_match else None
    part = int(part_match[1]) if part_match else None
    original = originals.get(attachment["url"])
    if original:
        doc_id = original["id"]
    elif chapter is not None:
        doc_id = f"dmg-vol{volume}-ch{chapter}" + (f"-part{part}" if part else "")
    elif amendment_match:
        doc_id = f"dmg-vol{volume}-amendment{amendment_match[1]}"
    elif kind == "change-summary" and volume is not None:
        doc_id = f"dmg-vol{volume}-changes"
    else:
        stem = slug(Path(attachment["filename"]).stem).removeprefix("dmg-")
        doc_id = f"dmg-{stem[:75]}-{digest(attachment['url'].encode())[:10]}"
    return {
        "id": doc_id, "title": title, "url": attachment["url"], "kind": kind, "role": role,
        "volume": volume, "chapter": chapter, "part": part,
        "attachment_id": attachment.get("id"), "original_filename": attachment.get("filename"),
        "declared_size_bytes": attachment.get("file_size"), "declared_pages": attachment.get("number_of_pages"),
        "accessible_format_available": attachment.get("accessible"),
        "discovery_classification": category, "classification_basis": attachment["classification_basis"],
        "publication": {
            "url": publication["page_url"], "title": publication["title"], "family": publication["family"],
            "first_published_at": publication["first_published_at"],
            "public_updated_at": publication["public_updated_at"], "withdrawn_notice": publication["withdrawn_notice"],
            "metadata_path": relative(DISCOVERY / publication["api_path"]),
        },
        "publication_updated_at": publication["public_updated_at"],
        "document_dates": {
            "published_at": None, "status": "not-declared-in-frozen-attachment-metadata",
            "limitation": "Dates in titles, collection metadata, HTTP headers and PDF technical metadata are not inferred document publication or legal effective dates.",
        },
        "current_attachment": True,
        "listed_at": "2026-09-15T16:55:18.464057Z",
        "legal_status": "Departmental guidance, not legislation. Listed in the frozen collection; current legal applicability and supersession have not been reviewed.",
    }


def load_inputs() -> tuple[dict, list[dict], dict, dict]:
    for name, expected in PINNED_INPUTS.items():
        if digest((ROOT / name).read_bytes()) != expected:
            raise ValueError(f"Frozen input hash mismatch: {name}")
    census = read_json(DISCOVERY / "census.json")
    receipts = read_json(DISCOVERY / "receipts.json")
    for receipt in receipts:
        path = checked_path(relative(DISCOVERY / receipt["path"]), within=DISCOVERY)
        raw = path.read_bytes()
        if len(raw) != receipt["bytes"] or digest(raw) != receipt["sha256"]:
            raise ValueError(f"Frozen API response does not match receipt: {path}")
    original_inventory = read_json(ROOT / "source/inventory.json")
    originals = {doc["url"]: doc for doc in original_inventory["documents"]}
    if len(originals) != 36:
        raise ValueError("Expected 36 unique original PDF URLs")
    documents = []
    for publication in census["publications"]:
        if publication["family"] not in {"dmg-volume", "dmg-memos", "dmg-abbreviations"}:
            continue
        for attachment in publication["attachments"]:
            if not attachment.get("is_pdf"):
                continue
            check_url(attachment["url"])
            documents.append(document_description(attachment, publication, originals))
    if len(documents) != 331 or len({doc["url"] for doc in documents}) != 331:
        raise ValueError("Frozen DMG census must contain exactly 331 unique PDFs")
    if len({doc["id"] for doc in documents}) != 331:
        raise ValueError("Document identifiers collide; explicit disambiguation is required")
    if set(originals) - {doc["url"] for doc in documents}:
        raise ValueError("An original PDF URL is absent from the frozen full-DMG census")
    collection = read_json(DISCOVERY / census["collection_api_path"])
    return census, documents, originals, collection


def pdf_information(pdf_path: Path) -> tuple[int, dict]:
    result = subprocess.run(["pdfinfo", str(pdf_path)], capture_output=True, text=True, timeout=EXTRACTION_TIMEOUT_SECONDS, check=True)
    match = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, re.M)
    if not match or not 0 < int(match[1]) <= 5000:
        raise ValueError(f"No bounded measured PDF page count: {pdf_path.name}")
    metadata = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            if key in {"Title", "Author", "Creator", "Producer", "CreationDate", "ModDate", "Tagged", "Encrypted", "PDF version", "JavaScript"}:
                metadata[key] = value.strip()
    return int(match[1]), {
        "technical_metadata": metadata,
        "date_semantics": "PDF CreationDate and ModDate are technical metadata only; neither is asserted to be publication or legal commencement.",
        "pdfinfo_warnings": result.stderr.strip(),
    }


def split_pages(text: str, page_count: int) -> list[str]:
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    if len(pages) != page_count:
        raise ValueError(f"Measured PDF/text page boundary mismatch: {page_count} PDF pages, {len(pages)} text pages")
    return pages


def assess_quality(pages: list[str]) -> dict:
    rows = []
    for index, text in enumerate(pages, 1):
        words = re.findall(r"[A-Za-z]+", text)
        single_ratio = sum(len(word) == 1 for word in words) / len(words) if words else 0
        nonspace = len(re.sub(r"\s", "", text))
        flags = []
        if not nonspace:
            flags.append("no-machine-extracted-text")
        elif nonspace < 100:
            flags.append("sparse-machine-extracted-text")
        if "\ufffd" in text:
            flags.append("unicode-replacement-characters")
        if len(words) >= 100 and single_ratio >= 0.25:
            flags.append("possible-letter-spacing-defect")
        if flags:
            rows.append({"page": index, "flags": flags, "nonspace_characters": nonspace,
                         "replacement_characters": text.count("\ufffd"), "single_letter_word_ratio": round(single_ratio, 4)})
    return {
        "assessment": "automated-heuristics-only; not a legibility, completeness or legal review",
        "pages_measured": len(pages), "pages_with_flags": len(rows),
        "flag_counts": dict(Counter(flag for row in rows for flag in row["flags"])),
        "flagged_pages": rows, "ocr_performed": False, "human_review_status": "not-reviewed",
        "limitation": EXTRACTION_LIMITATIONS,
    }


def validate_materials(record: dict, *, original: bool = False) -> list[str]:
    pdf = checked_path(record["pdf_path"])
    text_path = checked_path(record["text_path"])
    pages_path = checked_path(record["pages_path"])
    pdf_raw, text_raw, pages_raw = pdf.read_bytes(), text_path.read_bytes(), pages_path.read_bytes()
    if digest(pdf_raw) != record["sha256"] or len(pdf_raw) != record["size_bytes"]:
        raise ValueError(f"Cached PDF integrity mismatch: {record['id']}")
    if not pdf_raw.startswith(b"%PDF-") or digest(text_raw) != record["text_sha256"]:
        raise ValueError(f"Cached text/signature integrity mismatch: {record['id']}")
    if not original and digest(pages_raw) != record["pages_sha256"]:
        raise ValueError(f"Cached page JSON hash mismatch: {record['id']}")
    page_data = json.loads(pages_raw)
    pages = split_pages(text_raw.decode("utf-8"), record["pages"])
    if (page_data["document_id"] != record["id"] or page_data["source_url"] != record["url"]
            or page_data["source_sha256"] != record["sha256"] or len(page_data["pages"]) != len(pages)):
        raise ValueError(f"Cached page identity mismatch: {record['id']}")
    for index, (page, text) in enumerate(zip(page_data["pages"], pages, strict=True), 1):
        if page["page"] != index or page["text"] != text or page["url"] != f"{record['url']}#page={index}":
            raise ValueError(f"Cached page locator/text mismatch: {record['id']} page {index}")
    if record["http"]["requested_url"] != record["url"] or record["observed_at"] != record["http"]["observed_at"]:
        raise ValueError(f"Cached HTTP provenance mismatch: {record['id']}")
    check_url(record["http"]["resolved_url"])
    return pages


def validate_completed_record(record: dict, originals: dict) -> None:
    pages = validate_materials(record)
    if record["quality"] != assess_quality(pages):
        raise ValueError(f"Quality metrics differ from extracted page text: {record['id']}")
    if record["text_characters"] != len(checked_path(record["text_path"]).read_text(encoding="utf-8")):
        raise ValueError(f"Text character count differs: {record['id']}")
    if record["nonempty_text_pages"] != sum(bool(page.strip()) for page in pages):
        raise ValueError(f"Nonempty page count differs: {record['id']}")
    if record["declared_page_count_matches_measured"] != (record["declared_pages"] == record["pages"]):
        raise ValueError(f"Declared page comparison differs: {record['id']}")
    if record["declared_size_matches_measured"] != (record["declared_size_bytes"] == record["size_bytes"]):
        raise ValueError(f"Declared byte comparison differs: {record['id']}")
    original = originals.get(record["url"])
    if original:
        protected = ("id", "sha256", "size_bytes", "text_sha256", "pages", "observed_at", "http", "pdf_path", "text_path", "pages_path")
        if record["acquisition"]["mode"] != "reused-original-snapshot" or any(record[key] != original[key] for key in protected):
            raise ValueError(f"Original source provenance was not preserved: {record['id']}")
    else:
        receipt = read_json(checked_path(record["acquisition"]["receipt_path"], within=OUTPUT))
        if (receipt != record["http"] or receipt["sha256"] != record["sha256"] or receipt["bytes"] != record["size_bytes"]
                or record["acquisition"]["mode"] != "additional-frozen-census-download"):
            raise ValueError(f"Recorded HTTP acquisition differs from extracted source: {record['id']}")


def reuse_original(description: dict, original: dict) -> dict:
    if original["url"] != description["url"] or original["id"] != description["id"]:
        raise ValueError("Original source identity does not match the census")
    pages = validate_materials(original, original=True)
    measured_pages, metadata = pdf_information(checked_path(original["pdf_path"]))
    if measured_pages != original["pages"]:
        raise ValueError(f"Original measured page count mismatch: {original['id']}")
    record = {**copy.deepcopy(original), **description}
    record.update({
        "status": "complete", "pages_sha256": digest(checked_path(original["pages_path"]).read_bytes()),
        "pdf_metadata": metadata, "quality": assess_quality(pages),
        "acquisition": {"mode": "reused-original-snapshot", "original_inventory": "source/inventory.json",
                        "original_inventory_sha256": PINNED_INPUTS["source/inventory.json"],
                        "verified_at": utc_now(), "original_observed_at_preserved": True},
        "extraction_observed_at": None,
        "extraction_observation_limitation": "Original extraction did not record a separate extraction timestamp; the HTTP observation is preserved unchanged.",
    })
    return record


def download_or_resume(description: dict, output: Path, retries: int) -> tuple[Path, dict]:
    doc_id = description["id"]
    pdf_path = output / "pdf" / f"{doc_id}.pdf"
    receipt_path = output / "acquisition" / f"{doc_id}.json"
    if receipt_path.exists():
        receipt = read_json(receipt_path)
        if receipt["requested_url"] != description["url"]:
            raise ValueError(f"Resumable download URL mismatch: {doc_id}")
        raw = pdf_path.read_bytes()
        if len(raw) != receipt["bytes"] or digest(raw) != receipt["sha256"]:
            raise ValueError(f"Resumable download byte hash mismatch: {doc_id}")
        check_url(receipt["resolved_url"])
        return pdf_path, receipt
    attempts_dir = output / "attempts" / doc_id
    attempts_dir.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists():
        # A process can stop after atomically writing the PDF but before writing
        # its convenience receipt. Recover only from a matching, already saved
        # successful HTTP observation; do not invent a new capture timestamp.
        raw = pdf_path.read_bytes()
        for path in sorted(attempts_dir.glob("*.json"), reverse=True):
            attempt = read_json(path)
            if (attempt.get("status") == "downloaded" and attempt.get("requested_url") == description["url"]
                    and attempt.get("sha256") == digest(raw) and attempt.get("bytes") == len(raw)):
                receipt = {key: value for key, value in attempt.items() if key != "status"}
                check_url(receipt["resolved_url"])
                atomic_json(receipt_path, receipt)
                return pdf_path, receipt
        raise ValueError(f"PDF exists without matching recorded HTTP evidence; investigate: {doc_id}")
    existing = len(list(attempts_dir.glob("*.json")))
    for attempt in range(1, retries + 1):
        try:
            raw, receipt = fetch_pdf(description["url"])
            atomic_json(attempts_dir / f"{existing + attempt:03d}.json", {"status": "downloaded", **receipt})
            atomic_bytes(pdf_path, raw)
            atomic_json(receipt_path, receipt)
            return pdf_path, receipt
        except AcquisitionFailure as exc:
            atomic_json(attempts_dir / f"{existing + attempt:03d}.json", {"status": "failed", **exc.observation})
            if attempt == retries or exc.observation.get("http_status") in {400, 401, 403, 404, 410}:
                raise
            time.sleep(min(attempt, 3))
    raise RuntimeError("Exhausted download attempts")


def acquire_one(description: dict, originals: dict, output: Path, retries: int) -> tuple[dict, str]:
    record_path = output / "records" / f"{description['id']}.json"
    if record_path.exists():
        cached = read_json(record_path)
        if cached.get("status") == "complete":
            if any(cached.get(key) != value for key, value in description.items()):
                raise ValueError(f"Completed record no longer matches the frozen census: {description['id']}")
            validate_completed_record(cached, originals)
            return cached, "verified-existing"
    if description["url"] in originals:
        record = reuse_original(description, originals[description["url"]])
        action = "reused-original"
    else:
        pdf_path, http = download_or_resume(description, output, retries)
        page_count, metadata = pdf_information(pdf_path)
        text_path = output / "text" / f"{description['id']}.txt"
        pages_path = output / "pages" / f"{description['id']}.json"
        text_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output, prefix=".extract-") as temporary:
            temporary_text = Path(temporary) / "text.txt"
            result = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(pdf_path), str(temporary_text)],
                                    capture_output=True, timeout=EXTRACTION_TIMEOUT_SECONDS, check=True)
            if temporary_text.stat().st_size > MAX_TEXT_BYTES:
                raise ValueError("Extracted text exceeds the bounded text byte limit")
            text_raw = temporary_text.read_bytes()
        text = text_raw.decode("utf-8")
        pages = split_pages(text, page_count)
        extraction = {
            "method": "pdftotext -layout -enc UTF-8", "review_status": "unreviewed-machine-extraction",
            "limitations": EXTRACTION_LIMITATIONS, "ocr_performed": False,
            "warnings": result.stderr.decode("utf-8", errors="replace").strip(),
        }
        page_data = {
            "document_id": description["id"], "source_url": description["url"], "source_sha256": http["sha256"],
            "extraction": extraction,
            "pages": [{"page": index, "url": f"{description['url']}#page={index}", "text": page}
                      for index, page in enumerate(pages, 1)],
        }
        atomic_bytes(text_path, text_raw)
        atomic_json(pages_path, page_data)
        record = {
            **description, "status": "complete", "sha256": http["sha256"], "size_bytes": http["bytes"],
            "pages": page_count, "text_sha256": digest(text_raw), "pages_sha256": digest(pages_path.read_bytes()),
            "text_characters": len(text), "nonempty_text_pages": sum(bool(page.strip()) for page in pages),
            "observed_at": http["observed_at"], "extraction_observed_at": utc_now(),
            "pdf_path": relative(pdf_path), "text_path": relative(text_path), "pages_path": relative(pages_path),
            "http": http, "extraction": extraction, "pdf_metadata": metadata, "quality": assess_quality(pages),
            "acquisition": {"mode": "additional-frozen-census-download", "receipt_path": relative(output / "acquisition" / f"{description['id']}.json")},
        }
        action = "acquired-additional"
    record["declared_page_count_matches_measured"] = record["declared_pages"] == record["pages"]
    record["declared_size_matches_measured"] = record["declared_size_bytes"] == record["size_bytes"]
    atomic_json(record_path, record)
    return record, action


def inventory(census: dict, collection: dict, expected: list[dict], records: list[dict], failures: list[dict], started: str) -> dict:
    order = {doc["id"]: index for index, doc in enumerate(expected)}
    records = sorted(records, key=lambda doc: order[doc["id"]])
    by_kind = Counter(doc["kind"] for doc in records)
    return {
        "schema": "okf-dwp-full-dmg-acquisition.v1", "snapshot_id": "dmg-full-2026-09-15",
        "generated_at": utc_now(), "run_started_at": started,
        "census": {"path": relative(DISCOVERY / "census.json"), "sha256": PINNED_INPUTS[relative(DISCOVERY / "census.json")],
                   "metadata_observed_from": census["retrieved_from"], "metadata_observed_to": census["retrieved_to"]},
        "frozen_inputs": PINNED_INPUTS,
        "collection": {"url": census["collection_url"], "title": collection["title"],
                       "first_published_at": collection["first_published_at"], "public_updated_at": collection["public_updated_at"],
                       "api_updated_at": collection["updated_at"], "date_scope": "collection metadata only"},
        "authority": "official-source-bytes; unreviewed-machine-extraction; project-authored-classification",
        "licence_url": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        "attribution": "Contains public sector information licensed under the Open Government Licence v3.0. Source: Department for Work and Pensions, Decision makers' guide.",
        "limitations": [EXTRACTION_LIMITATIONS,
                        "Frozen direct DMG attachment census only; ADM and claimant-facing UC pages are separate source families.",
                        "No current-law consolidation, entitlement determination, executable policy rules or specialist review.",
                        "Attachment listing dates and PDF technical dates are not document publication or legal effective dates.",
                        "Original Pension Credit evidence is reused by path, URL and hashes; its observation dates are unchanged."],
        "summary": {
            "expected_pdf_documents": len(expected), "complete_documents": len(records),
            "reused_original_documents": sum(doc["acquisition"]["mode"] == "reused-original-snapshot" for doc in records),
            "additional_documents": sum(doc["acquisition"]["mode"] == "additional-frozen-census-download" for doc in records),
            "declared_pages": sum(doc["declared_pages"] or 0 for doc in expected),
            "measured_pages": sum(doc["pages"] for doc in records),
            "pdf_bytes": sum(doc["size_bytes"] for doc in records),
            "text_characters": sum(doc["text_characters"] for doc in records),
            "documents_by_kind": dict(by_kind),
            "pages_by_kind": {kind: sum(doc["pages"] for doc in records if doc["kind"] == kind) for kind in by_kind},
            "quality_flags": dict(Counter(flag for doc in records for page in doc["quality"]["flagged_pages"] for flag in page["flags"])),
            "declared_page_mismatches": [doc["id"] for doc in records if not doc["declared_page_count_matches_measured"]],
            "declared_byte_mismatches": [doc["id"] for doc in records if not doc["declared_size_matches_measured"]],
            "failure_count": len(failures), "complete_for_frozen_dmg_census": len(records) == len(expected) and not failures,
        },
        "documents": records, "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4, choices=range(1, 5))
    parser.add_argument("--retries", type=int, default=3, choices=range(1, 4))
    parser.add_argument("--plan", action="store_true", help="Validate frozen inputs and print the acquisition plan without writing or networking")
    parser.add_argument("--check", action="store_true", help="Verify every completed record and material without writing or networking")
    args = parser.parse_args()
    census, expected, originals, collection = load_inputs()
    if args.plan:
        print(json.dumps({"documents": len(expected), "reusable_originals": len(originals), "new_downloads": len(expected) - len(originals),
                          "declared_pdf_bytes": sum(doc["declared_size_bytes"] for doc in expected),
                          "declared_pages": sum(doc["declared_pages"] for doc in expected),
                          "ids": [doc["id"] for doc in expected]}, indent=2))
        return 0
    for executable in ("pdfinfo", "pdftotext"):
        if not shutil.which(executable):
            parser.error(f"Required installed executable missing: {executable}")
    if args.check:
        current = read_json(OUTPUT / "inventory.json")
        if not current["summary"]["complete_for_frozen_dmg_census"] or len(current["documents"]) != len(expected):
            raise ValueError("Full-DMG inventory is incomplete")
        records = {record["id"]: record for record in current["documents"]}
        for description in expected:
            record = read_json(OUTPUT / "records" / f"{description['id']}.json")
            if records.get(description["id"]) != record or any(record.get(key) != value for key, value in description.items()):
                raise ValueError(f"Inventory/record/census mismatch: {description['id']}")
            validate_completed_record(record, originals)
            measured, _ = pdf_information(checked_path(record["pdf_path"]))
            if measured != record["pages"]:
                raise ValueError(f"Re-measured PDF page count differs: {record['id']}")
        expected_inventory = inventory(census, collection, expected, list(records.values()), [], current["run_started_at"])
        if current["summary"] != expected_inventory["summary"] or current["frozen_inputs"] != PINNED_INPUTS:
            raise ValueError("Aggregate inventory summary or frozen input identity differs")
        quality = read_json(OUTPUT / "extraction-quality.json")
        expected_quality = [{"id": doc["id"], "sha256": doc["sha256"], **doc["quality"]} for doc in current["documents"]]
        if quality["documents"] != expected_quality or quality["summary"] != current["summary"]["quality_flags"]:
            raise ValueError("Aggregate extraction-quality report differs from verified records")
        print(f"Verified {len(expected)} complete DMG documents and all PDF/text/page hashes; frozen original inputs unchanged.")
        return 0
    OUTPUT.mkdir(parents=True, exist_ok=True)
    lock_path = OUTPUT / ".acquisition.lock"
    with lock_path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        started = utc_now()
        monotonic_started = time.monotonic()
        records, failures = [], []
        actions: Counter = Counter()
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
                futures = {pool.submit(acquire_one, doc, originals, OUTPUT, args.retries): doc for doc in expected}
                for future in concurrent.futures.as_completed(futures):
                    description = futures[future]
                    try:
                        record, action = future.result()
                        records.append(record)
                        actions[action] += 1
                        print(f"{len(records):03d}/{len(expected)} {action} {record['id']}: {record['pages']} pages", flush=True)
                    except Exception as exc:
                        failure = {"id": description["id"], "url": description["url"], "observed_at": utc_now(),
                                   "error_type": type(exc).__name__, "error": str(exc)}
                        failures.append(failure)
                        atomic_json(OUTPUT / "failures" / f"{description['id']}-{started.replace(':', '').replace('.', '-')}.json", failure)
                        print(f"FAILED {description['id']}: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
                    if (len(records) + len(failures)) % 20 == 0:
                        atomic_json(OUTPUT / "inventory.json", inventory(census, collection, expected, records, failures, started))
            final = inventory(census, collection, expected, records, failures, started)
            atomic_json(OUTPUT / "inventory.json", final)
            atomic_json(OUTPUT / "extraction-quality.json", {
                "schema": "okf-dwp-full-dmg-extraction-quality.v1", "assessed_at": utc_now(),
                "assessment_scope": "Automated metrics across all completed documents; no whole-corpus visual or specialist review.",
                "summary": final["summary"]["quality_flags"],
                "documents": [{"id": doc["id"], "sha256": doc["sha256"], **doc["quality"]} for doc in final["documents"]],
                "prior_visual_sample_evidence": "source/extraction-quality.json",
            })
            receipt = {"started_at": started, "completed_at": utc_now(), "elapsed_seconds": round(time.monotonic() - monotonic_started, 3),
                       "workers": args.workers, "retries_per_download": args.retries, "actions": dict(actions),
                       "inventory_sha256": digest((OUTPUT / "inventory.json").read_bytes()), "summary": final["summary"],
                       "limits": {"pdf_bytes": MAX_PDF_BYTES, "text_bytes": MAX_TEXT_BYTES, "socket_timeout_seconds": SOCKET_TIMEOUT_SECONDS,
                                  "download_deadline_seconds": DOWNLOAD_TIMEOUT_SECONDS, "subprocess_timeout_seconds": EXTRACTION_TIMEOUT_SECONDS}}
            atomic_json(OUTPUT / "runs" / f"{started.replace(':', '').replace('.', '-')}.json", receipt)
            print(json.dumps(receipt, indent=2), flush=True)
            return 1 if failures else 0
        finally:
            lock_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
