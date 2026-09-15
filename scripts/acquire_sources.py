#!/usr/bin/env python3
"""Acquire the public DWP Pension Credit guide with auditable extraction metadata.

Standard library only. Requires Poppler's pdfinfo and pdftotext executables.
Run without --refresh to reuse the downloaded publication snapshot and PDFs;
--refresh deliberately takes a new observation of the publication and assets.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source"
PUBLICATION_URL = "https://www.gov.uk/government/publications/decision-makers-guide-vols-13-and-14-state-pension-credit-staff-guide"
CONTENT_API_URL = PUBLICATION_URL.replace("www.gov.uk/", "www.gov.uk/api/content/", 1)
ALLOWED_HOSTS = {"www.gov.uk", "assets.publishing.service.gov.uk"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def check_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"Source URL is outside the GOV.UK HTTPS allowlist: {url}")


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url: str) -> tuple[bytes, dict]:
    check_url(url)
    request = urllib.request.Request(url, headers={"User-Agent": "okf-dwp/0.1 (public research demonstrator)"})
    opener = urllib.request.build_opener(SafeRedirect())
    with opener.open(request, timeout=90) as response:
        return response.read(), {
            "requested_url": url,
            "resolved_url": response.url,
            "observed_at": utc_now(),
            "http_status": response.status,
            "content_type": response.headers.get("Content-Type"),
            "last_modified": response.headers.get("Last-Modified"),
            "etag": response.headers.get("ETag"),
        }


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def describe(attachment: dict) -> dict:
    title = attachment["title"]
    volume_match = re.search(r"Vol\s+(\d+)", title, re.I)
    chapter_match = re.search(r"\bCh\s+(\d+)", title, re.I)
    amendment_match = re.search(r"\bAmendment\s+(\d+)", title, re.I)
    volume = int(volume_match[1]) if volume_match else None
    chapter = int(chapter_match[1]) if chapter_match else None
    if chapter:
        kind = "chapter"
        doc_id = f"dmg-vol{volume}-ch{chapter}"
        role = "spare" if chapter in (81, 82) else "transitional" if chapter == 80 else "substantive"
    elif "summary of changes" in title.lower():
        kind = "change-summary"
        doc_id = f"dmg-vol{volume}-changes"
        role = "change-history"
    elif amendment_match:
        kind = "historical-amendment"
        doc_id = f"dmg-vol{volume}-amendment{amendment_match[1]}"
        role = "historical-amendment-not-current-rules"
    else:
        raise ValueError(f"Unrecognised PDF attachment classification: {title}")
    return {
        "id": doc_id,
        "title": title,
        "url": attachment["url"],
        "kind": kind,
        "role": role,
        "volume": volume,
        "chapter": chapter,
        "attachment_id": attachment.get("id"),
        "declared_size_bytes": attachment.get("file_size"),
        "declared_pages": attachment.get("number_of_pages"),
        "accessible_format_available": attachment.get("accessible"),
        "original_filename": attachment.get("filename"),
    }


def acquire_one(attachment: dict, publication: dict, previous: dict, refresh: bool) -> dict:
    record = describe(attachment)
    doc_id = record["id"]
    pdf_path = SOURCE / "pdf" / f"{doc_id}.pdf"
    text_path = SOURCE / "text" / f"{doc_id}.txt"
    pages_path = SOURCE / "pages" / f"{doc_id}.json"
    cached = previous.get(doc_id, {})
    if pdf_path.exists() and cached.get("url") == record["url"] and not refresh:
        raw = pdf_path.read_bytes()
        if digest(raw) != cached.get("sha256"):
            raise ValueError(f"Cached PDF hash mismatch: {doc_id}; investigate or use --refresh")
        http = cached["http"]
    else:
        raw, http = fetch(record["url"])
        if not raw.startswith(b"%PDF-"):
            raise ValueError(f"Downloaded content is not a PDF: {record['url']}")
        pdf_path.write_bytes(raw)
    pdf_information = subprocess.run(["pdfinfo", str(pdf_path)], check=True, capture_output=True, text=True).stdout
    page_match = re.search(r"^Pages:\s+(\d+)", pdf_information, re.M)
    if not page_match:
        raise ValueError(f"Unable to determine PDF page count: {doc_id}")
    page_count = int(page_match[1])
    subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(pdf_path), str(text_path)], check=True, capture_output=True)
    text = text_path.read_text(encoding="utf-8")
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    if len(pages) != page_count:
        raise ValueError(f"Page boundary mismatch in {doc_id}: {len(pages)} text pages, {page_count} PDF pages")
    pdf_sha = digest(raw)
    extraction = {
        "method": "pdftotext -layout -enc UTF-8",
        "review_status": "unreviewed-machine-extraction",
        "limitations": "PDF reading order, footnotes, tables and characters require checking against the cited PDF. Page numbers are one-based PDF page indices, not printed page labels.",
        "ocr_performed": False,
    }
    write_json(pages_path, {
        "document_id": doc_id,
        "source_url": record["url"],
        "source_sha256": pdf_sha,
        "extraction": extraction,
        "pages": [{"page": index, "url": f"{record['url']}#page={index}", "text": page} for index, page in enumerate(pages, 1)],
    })
    record.update({
        "sha256": pdf_sha,
        "size_bytes": len(raw),
        "pages": page_count,
        "text_sha256": digest(text_path.read_bytes()),
        "text_characters": len(text),
        "nonempty_text_pages": sum(bool(page.strip()) for page in pages),
        "observed_at": http["observed_at"],
        "publication_updated_at": publication["public_updated_at"],
        "pdf_path": str(pdf_path.relative_to(ROOT)),
        "text_path": str(text_path.relative_to(ROOT)),
        "pages_path": str(pages_path.relative_to(ROOT)),
        "http": http,
        "extraction": extraction,
        "current_attachment": True,
        "legal_status": "Departmental guidance; not legislation. A currently linked attachment does not establish that every statement remains applicable.",
    })
    print(f"Acquired {doc_id}: {page_count} pages", flush=True)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Take a new publication and PDF observation instead of reusing hash-checked downloads")
    parser.add_argument("--workers", type=int, default=6, choices=range(1, 9), metavar="1..8")
    args = parser.parse_args()
    for executable in ("pdfinfo", "pdftotext"):
        if not shutil.which(executable):
            parser.error(f"Required executable not found: {executable} (install Poppler)")
    for directory in (SOURCE, SOURCE / "pdf", SOURCE / "text", SOURCE / "pages"):
        directory.mkdir(parents=True, exist_ok=True)
    publication_path = SOURCE / "publication.json"
    receipt_path = SOURCE / "publication-receipt.json"
    inventory_path = SOURCE / "inventory.json"
    if args.refresh or not publication_path.exists():
        publication_raw, publication_http = fetch(CONTENT_API_URL)
        publication = json.loads(publication_raw)
        publication_path.write_bytes(publication_raw)
        write_json(receipt_path, {**publication_http, "sha256": digest(publication_raw), "size_bytes": len(publication_raw)})
        html, html_http = fetch(PUBLICATION_URL)
        (SOURCE / "publication.html").write_bytes(html)
        write_json(SOURCE / "publication-html-receipt.json", {**html_http, "sha256": digest(html), "size_bytes": len(html)})
    else:
        publication = json.loads(publication_path.read_text(encoding="utf-8"))
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if digest(publication_path.read_bytes()) != receipt["sha256"]:
            raise ValueError("Publication metadata hash does not match its acquisition receipt")
    previous_inventory = json.loads(inventory_path.read_text(encoding="utf-8")) if inventory_path.exists() else {}
    previous = {entry["id"]: entry for entry in previous_inventory.get("documents", [])}
    attachments = publication["details"]["attachments"]
    pdf_attachments = [entry for entry in attachments if entry.get("content_type") == "application/pdf"]
    documents = []
    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(acquire_one, attachment, publication, previous, args.refresh): attachment for attachment in pdf_attachments}
        for future in concurrent.futures.as_completed(futures):
            try:
                documents.append(future.result())
            except Exception as exc:
                errors.append({"url": futures[future]["url"], "error": str(exc)})
                print(f"ERROR {errors[-1]}", file=sys.stderr)
    order = {entry["url"]: index for index, entry in enumerate(pdf_attachments)}
    documents.sort(key=lambda record: order[record["url"]])
    counts = dict(Counter(document["kind"] for document in documents))
    page_counts = dict(Counter({kind: sum(document["pages"] for document in documents if document["kind"] == kind) for kind in counts}))
    summary = {
        "linked_attachments": len(attachments),
        "linked_pdf_attachments": len(pdf_attachments),
        "acquired_documents": len(documents),
        "documents_by_kind": counts,
        "pages_by_kind": page_counts,
        "total_pages": sum(document["pages"] for document in documents),
        "total_pdf_bytes": sum(document["size_bytes"] for document in documents),
        "total_text_characters": sum(document["text_characters"] for document in documents),
        "errors": errors,
        "complete_for_linked_pdfs": len(documents) == len(pdf_attachments) and not errors,
    }
    write_json(inventory_path, {
        "schema_version": "1.0",
        "publication_url": PUBLICATION_URL,
        "content_api_url": CONTENT_API_URL,
        "title": publication["title"],
        "publisher": "Department for Work and Pensions",
        "publication_updated_at": publication["public_updated_at"],
        "publication_first_published_at": publication["first_published_at"],
        "observation": json.loads(receipt_path.read_text(encoding="utf-8")),
        "generated_at": utc_now(),
        "licence_url": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        "attribution": "Contains public sector information licensed under the Open Government Licence v3.0. Source: Department for Work and Pensions, Decision makers' guide, volumes 13 and 14.",
        "status": "Unofficial research demonstrator; not endorsed by DWP. Extracted text has not undergone expert or accessibility review. Historical amendments are evidence of changes, not a current consolidated rule set.",
        "summary": summary,
        "documents": documents,
    })
    print(json.dumps(summary, indent=2), flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
