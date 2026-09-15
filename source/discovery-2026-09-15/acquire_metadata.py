#!/usr/bin/env python3
"""Refresh a bounded GOV.UK metadata census, or reproduce it offline.

No linked attachment, PDF, legislation or claimant information is downloaded.
"""

import argparse
import concurrent.futures
import hashlib
import json
import re
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COLLECTION = "/government/collections/decision-makers-guide-staff-guide"
ADM = "/government/publications/advice-for-decision-making-staff-guide"
UC = "/universal-credit/eligibility"


def filename(path):
    return path.strip("/").replace("/", "__") + ".json"


def load(path):
    return json.loads((ROOT / "api" / filename(path)).read_bytes())


def fetch(path):
    url = "https://www.gov.uk/api/content" + path
    request = urllib.request.Request(url, headers={"User-Agent": "okf-dwp-public-metadata-census/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
        receipt = {
            "page_url": "https://www.gov.uk" + path,
            "request_url": url,
            "final_url": response.url,
            "retrieved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": response.status,
            "content_type": response.headers.get("Content-Type"),
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "path": "api/" + filename(path),
        }
    json.loads(data)
    (ROOT / receipt["path"]).write_bytes(data)
    return receipt


def classify(title, family):
    text = title.lower()
    if "summary" in text and ("change" in text or "amend" in text):
        return "change-summary"
    if "amendment" in text and family == "dmg-volume":
        return "amendment-record"
    if "memo" in text or family == "dmg-memos" or (family == "adm" and re.match(r"adm \d{1,2}/\d{2}:", text)):
        return "memo"
    if "statutes" in text or "statutory instruments" in text:
        return "legislation-reference-list"
    if "abbreviation" in text:
        return "abbreviations"
    if "annex" in text:
        return "annex-spare" if "spare" in text else "annex-listed"
    if re.search(r"\b(ch|chapter)\s+", text):
        if "spare" in text:
            return "chapter-spare"
        if "transitional" in text:
            return "chapter-transitional"
        return "chapter-current-listed"
    return "other-listed-attachment"


def build():
    collection = load(COLLECTION)
    groups = {
        content_id: group["title"]
        for group in collection["details"]["collection_groups"]
        for content_id in group["documents"]
    }
    pages = []
    documents = collection["links"]["documents"]
    for stub in documents + [{"base_path": ADM}, {"base_path": UC}]:
        data = load(stub["base_path"])
        group = groups.get(data["content_id"])
        family = (
            "dmg-volume" if group == "Volumes" else
            "dmg-memos" if "memos" in data["base_path"] else
            "dmg-abbreviations" if "abbreviations" in data["base_path"] else
            "adm" if data["base_path"] == ADM else "claimant-information"
        )
        attachments = []
        for attachment in data.get("details", {}).get("attachments", []):
            title = attachment.get("title", "")
            item = dict(attachment)
            item["discovery_classification"] = classify(title, family)
            item["classification_basis"] = "publication family and attachment title only; content and temporal applicability not reviewed"
            item["downloaded"] = False
            item["content_sha256"] = None
            item["is_pdf"] = attachment.get("content_type") == "application/pdf" or str(attachment.get("url", "")).lower().split("?")[0].endswith(".pdf")
            attachments.append(item)
        counts = Counter(a["discovery_classification"] for a in attachments)
        pages.append({
            "title": data["title"],
            "page_url": "https://www.gov.uk" + stub["base_path"],
            "canonical_page_url": "https://www.gov.uk" + data["base_path"],
            "base_path": data["base_path"],
            "content_id": data["content_id"],
            "family": family,
            "collection_group": group,
            "document_type": data.get("document_type"),
            "first_published_at": data.get("first_published_at"),
            "public_updated_at": data.get("public_updated_at"),
            "withdrawn_notice": data.get("withdrawn_notice"),
            "description": data.get("description"),
            "attachment_count": len(attachments),
            "pdf_count": sum(a["is_pdf"] for a in attachments),
            "declared_pdf_pages": sum(a.get("number_of_pages", 0) or 0 for a in attachments if a["is_pdf"]),
            "pdf_page_count_missing": sum(a.get("number_of_pages") is None for a in attachments if a["is_pdf"]),
            "classification_counts": dict(sorted(counts.items())),
            "attachments": attachments,
            "api_path": "api/" + filename(stub["base_path"]),
        })
    receipts = json.loads((ROOT / "receipts.json").read_text())
    for receipt in receipts:
        data = (ROOT / receipt["path"]).read_bytes()
        assert len(data) == receipt["bytes"]
        assert hashlib.sha256(data).hexdigest() == receipt["sha256"]
    summaries = {}
    for family in ("dmg-volume", "dmg-memos", "dmg-abbreviations", "adm", "claimant-information"):
        matching = [p for p in pages if p["family"] == family]
        attachments = [a for p in matching for a in p["attachments"]]
        summaries[family] = {
            "publication_count": len(matching),
            "attachment_count": len(attachments),
            "pdf_count": sum(a["is_pdf"] for a in attachments),
            "unique_pdf_urls": len({a.get("url") for a in attachments if a["is_pdf"]}),
            "declared_pdf_pages": sum(p["declared_pdf_pages"] for p in matching),
            "pdf_page_count_missing": sum(p["pdf_page_count_missing"] for p in matching),
            "classification_counts": dict(sorted(Counter(a["discovery_classification"] for a in attachments).items())),
        }
    dmg = [p for p in pages if p["family"].startswith("dmg-")]
    census = {
        "schema": "okf-dwp-source-metadata-census.v1",
        "snapshot_date": "2026-09-15",
        "authority": "project-authored metadata census of official GOV.UK API responses; not a legal completeness assessment",
        "scope": "DMG collection direct publication members plus ADM publication and UC eligibility context; no linked attachment downloads",
        "collection_url": "https://www.gov.uk" + COLLECTION,
        "collection_api_path": "api/" + filename(COLLECTION),
        "retrieved_from": min(r["retrieved_at"] for r in receipts),
        "retrieved_to": max(r["retrieved_at"] for r in receipts),
        "response_count": len(receipts),
        "dmg_volumes_represented": 14,
        "dmg_direct_publication_count": len(dmg),
        "dmg_pdf_count": sum(p["pdf_count"] for p in dmg),
        "dmg_unique_pdf_urls": len({a.get("url") for p in dmg for a in p["attachments"] if a["is_pdf"]}),
        "dmg_declared_pdf_pages": sum(p["declared_pdf_pages"] for p in dmg),
        "summaries": summaries,
        "limitations": [
            "PDF page counts are publisher metadata and have not been measured from newly downloaded files.",
            "PDF content hashes are deliberately null: no attachment bytes were retrieved by this census.",
            "Current-listed chapter classification means present in the live publication, not legally current or consolidated.",
            "Memo dates do not establish that a memo is historical or superseded; status needs content review.",
            "Amendment records are listed separately and must not be flattened into current guidance.",
            "This does not follow every link within documents, include withdrawn assets no longer linked, or enumerate legislation and case law.",
            "All classifications are title-based planning aids; ambiguous records remain other-listed-attachment.",
        ],
        "publications": pages,
    }
    return (json.dumps(census, ensure_ascii=False, indent=2) + "\n").encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Download the 14 public metadata API responses; never downloads PDFs")
    parser.add_argument("--check", action="store_true", help="Verify frozen response hashes and reproduce census bytes without network")
    args = parser.parse_args()
    if args.refresh and args.check:
        parser.error("--refresh and --check cannot be combined")
    if args.refresh:
        if (ROOT / "receipts.json").exists():
            parser.error("Frozen receipts already exist. Copy this script to a new dated directory for a fresh snapshot.")
        (ROOT / "api").mkdir(parents=True, exist_ok=True)
        receipts = [fetch(COLLECTION)]
        paths = [d["base_path"] for d in load(COLLECTION)["links"]["documents"]] + [ADM, UC]
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            receipts.extend(pool.map(fetch, paths))
        (ROOT / "receipts.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + "\n")
    result = build()
    output = ROOT / "census.json"
    if args.check:
        assert output.read_bytes() == result, "Census differs from frozen metadata"
        print("PASS: all frozen response hashes and reproducible census bytes")
    else:
        output.write_bytes(result)
        print("Wrote " + str(output))


if __name__ == "__main__":
    main()
