#!/usr/bin/env python3
"""Observe bounded official listing metadata and compare source snapshots offline.

--acquire is the only network path. It never downloads a PDF or changes an old
source inventory. Default and --check regenerate deterministic comparison reports.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import urllib.parse

from acquire_legal_reconciliation import fetch, pretty, sha

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "source/discovery-2026-09-20"
POLICY = "domain-profile/source-refresh-policy.json"
FIELDS = ["title", "url", "declared_size_bytes", "declared_pages", "publication_updated_at", "source_publication_date", "classification"]


def identity(document: dict) -> str:
    publication = document["publication_url"]
    return publication + ("#attachment=" + str(document["attachment_id"]) if document.get("attachment_id") else "#url=" + document["url"])


def normalise_inventory(inventory: dict, family: str) -> list[dict]:
    return [{"id": d["id"], "family": family, "attachment_id": str(d["attachment_id"]) if d.get("attachment_id") is not None else None,
             "title": d["title"], "url": d["url"], "publication_url": d["publication"]["url"],
             "declared_size_bytes": d.get("declared_size_bytes"), "declared_pages": d.get("declared_pages"),
             "publication_updated_at": d.get("publication_updated_at"),
             "source_publication_date": d.get("document_dates", {}).get("published_at"),
             "classification": d.get("discovery_classification"),
             "content_sha256": d.get("sha256"), "extraction_sha256": d.get("pages_sha256"),
             "observed_at": d.get("observed_at")} for d in inventory["documents"]]


def keyed(documents: list[dict]) -> dict:
    result = {}
    for document in documents:
        key = identity(document)
        if key in result:
            raise ValueError("Duplicate source identity; explicit reconciliation required: " + key)
        result[key] = document
    return result


def compare(old: list[dict], new: list[dict], observed_publications: set[str]) -> dict:
    before, after = keyed(old), keyed(new)
    rows = []
    for key in sorted(before.keys() | after.keys()):
        a, b = before.get(key), after.get(key)
        if a is None:
            rows.append({"key": key, "presence": "added", "after": b, "content": "unknown", "extraction": "unknown"})
            continue
        if b is None:
            rows.append({"key": key, "presence": "removed" if a["publication_url"] in observed_publications else "unknown",
                         "before": a, "content": "unknown", "extraction": "unknown",
                         "reason": "publication-observed-completely" if a["publication_url"] in observed_publications else "publication-not-observed"})
            continue
        changes, unknown = {}, []
        for field in FIELDS:
            if a.get(field) is None or b.get(field) is None:
                unknown.append(field)
            elif a[field] != b[field]:
                changes[field] = {"before": a[field], "after": b[field]}
        def state(field):
            if not a.get(field) or not b.get(field):
                return "unknown"
            return "unchanged" if a[field] == b[field] else "changed"
        rows.append({"key": key, "id": a["id"], "family": a["family"], "presence": "present",
                     "metadata": "changed" if changes else "no-change-in-comparable-fields",
                     "changes": changes, "unknown_metadata_fields": unknown,
                     "content": state("content_sha256"), "extraction": state("extraction_sha256"),
                     "before_observed_at": a.get("observed_at"), "after_observed_at": b.get("observed_at")})
    return {"schema": "okf-source-census-comparison.v1", "before_documents": len(old), "after_documents": len(new),
            "presence_counts": dict(sorted(Counter(r["presence"] for r in rows).items())),
            "content_counts": dict(sorted(Counter(r["content"] for r in rows).items())),
            "extraction_counts": dict(sorted(Counter(r["extraction"] for r in rows).items())),
            "metadata_changed_documents": sum(bool(r.get("changes")) for r in rows), "documents": rows,
            "limitations": ["Matching listing metadata never proves unchanged PDF bytes.",
                            "Removed means absent from a successfully observed complete publication attachment list, not repealed or deleted from all official services.",
                            "Unknown dates/classifications remain unknown; a source refresh does not establish legal applicability.",
                            "No source version or live context binding is changed by this report."]}


def baseline(root: Path, policy: dict) -> tuple[list[dict], list[dict]]:
    rows, bindings = [], []
    for family, path in zip(policy["source_families"], policy["inventories"], strict=True):
        raw = (root / path).read_bytes()
        bindings.append({"path": path, "sha256": sha(raw), "bytes": len(raw)})
        rows.extend(normalise_inventory(json.loads(raw), family))
    keyed(rows)
    return rows, bindings


def api_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "www.gov.uk" or not parsed.path.startswith("/government/") or parsed.query or parsed.fragment:
        raise ValueError("Only declared GOV.UK collection/publication metadata routes allowed")
    return "https://www.gov.uk/api/content" + parsed.path


def acquire(root: Path = ROOT) -> None:
    policy = json.loads((root / POLICY).read_text())
    dest = root / SOURCE
    if (dest / "manifest.json").exists():
        raise ValueError("Dated source discovery exists; preserve it and use a separately named refresh")
    old, bindings = baseline(root, policy)
    pending = set(d["publication_url"] for d in old)
    raw, receipt = fetch(api_url(policy["collection_url"]))
    receipts, files = [], {}
    total_bytes = 0
    collection_links = []
    if raw is not None:
        data = json.loads(raw)
        collection_links = sorted({"https://www.gov.uk" + d["base_path"] for d in data.get("links", {}).get("documents", [])
                                   if d.get("base_path", "").startswith("/government/publications/")})
        pending.update(collection_links)
        files["api/collection.json"] = raw
        total_bytes += len(raw)
        receipt["path"] = "api/collection.json"
        receipt["response_body_retained"] = True
    receipt["publication_url"] = policy["collection_url"]
    receipts.append(receipt)
    selected = sorted(pending)[:policy["max_api_requests"] - 1]
    not_requested = sorted(pending - set(selected))
    def retrieve(url):
        body, result = fetch(api_url(url))
        result["publication_url"] = url
        return url, body, result
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(retrieve, selected))
    for url, body, result in results:
        if body is not None:
            total_bytes += len(body)
            if total_bytes > policy["max_total_response_bytes"]:
                raise ValueError("Combined metadata response budget exceeded; no snapshot published")
            name = "api/" + urllib.parse.urlparse(url).path.rsplit("/", 1)[-1] + ".json"
            files[name] = body
            result["path"] = name
            result["response_body_retained"] = True
        receipts.append(result)
    files["receipts.json"] = pretty({"schema": "okf-metadata-refresh-receipts.v1", "receipts": receipts,
                                    "not_requested_due_to_budget": not_requested, "observed_collection_publications": collection_links,
                                    "requests": len(receipts), "total_response_bytes": total_bytes, "pdf_downloads": 0})
    manifest = {"schema": "okf-source-discovery-refresh.v1", "observed_on": policy["observation_date"],
                "policy_sha256": sha((root / POLICY).read_bytes()), "baseline_inventories": bindings,
                "files": [{"path": p, "bytes": len(b), "sha256": sha(b)} for p, b in sorted(files.items())]}
    for path, data in files.items():
        target = dest / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (dest / "manifest.json").write_bytes(pretty(manifest))
    print(json.dumps({"requests": len(receipts), "metadata_bytes": total_bytes, "unvisited": len(not_requested), "pdf_downloads": 0}))


def refreshed(root: Path, old: list[dict], manifest: dict) -> tuple[list[dict], set[str], dict]:
    bound_paths = set()
    for item in manifest["files"]:
        path = Path(item["path"])
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Unsafe refresh metadata path")
        if str(path) in bound_paths:
            raise ValueError("Duplicate metadata binding")
        bound_paths.add(str(path))
        raw = (root / SOURCE / path).read_bytes()
        if sha(raw) != item["sha256"] or len(raw) != item["bytes"]:
            raise ValueError("Refresh metadata hash mismatch: " + str(path))
    if "receipts.json" not in bound_paths:
        raise ValueError("Acquisition receipts must have a verified manifest binding")
    receipts = json.loads((root / SOURCE / "receipts.json").read_text())
    before = keyed(old)
    rows, complete = [], set()
    for receipt in receipts["receipts"]:
        if not receipt.get("path") or receipt["path"] == "api/collection.json":
            continue
        if receipt["path"] not in bound_paths:
            raise ValueError("Unbound API receipt path")
        raw = (root / SOURCE / receipt["path"]).read_bytes()
        if sha(raw) != receipt["response_sha256"] or len(raw) != receipt["response_bytes"]:
            raise ValueError("Raw API response does not match acquisition receipt")
        publication = json.loads(raw)
        if "https://www.gov.uk" + publication.get("base_path", "") != receipt["publication_url"]:
            raise ValueError("API response belongs to a different publication")
        attachments = publication.get("details", {}).get("attachments")
        if not isinstance(attachments, list):
            continue  # Missing list must never imply removal.
        url = receipt["publication_url"]
        complete.add(url)
        family = "adm" if url.endswith("/advice-for-decision-making-staff-guide") else "dmg"
        for attachment in attachments:
            if attachment.get("content_type") != "application/pdf":
                continue
            row = {"id": "unmatched", "family": family, "attachment_id": str(attachment["id"]) if attachment.get("id") is not None else None,
                   "publication_url": url, "title": attachment["title"], "url": attachment["url"],
                   "declared_size_bytes": attachment.get("file_size"), "declared_pages": attachment.get("number_of_pages"),
                   "publication_updated_at": publication.get("public_updated_at"), "source_publication_date": None,
                   "classification": None, "content_sha256": None, "extraction_sha256": None,
                   "observed_at": receipt["observed_at"]}
            prior = before.get(identity(row))
            if prior:
                row["id"] = prior["id"]
                # No new classification inferred merely because titles are unchanged.
            rows.append(row)
    return rows, complete, receipts


def synthetic_controls() -> dict:
    a = {"id": "fixture-a", "family": "synthetic", "publication_url": "https://example.invalid/publication", "attachment_id": "1",
         "url": "https://example.invalid/a.pdf", "title": "Synthetic source", "content_sha256": "a", "extraction_sha256": "x",
         "classification": "chapter", "publication_updated_at": "2026-01-01"}
    changed = {**a, "content_sha256": "b", "extraction_sha256": "y", "title": "Changed synthetic source", "classification": "memo", "publication_updated_at": "2026-02-01"}
    added = {**a, "id": "fixture-b", "attachment_id": "2"}
    return {"schema": "okf-source-drift-controls.v1", "synthetic": True,
            "content_extraction_date_classification_changes": compare([a], [changed], {a["publication_url"]}),
            "added_and_removed": compare([a], [added], {a["publication_url"]}),
            "failed_publication_is_unknown": compare([a], [], set()),
            "metadata_only_content_is_unknown": compare([a], [{**a, "content_sha256": None, "extraction_sha256": None}], {a["publication_url"]})}


def build(root: Path = ROOT) -> dict[str, bytes]:
    policy = json.loads((root / POLICY).read_text())
    old, bindings = baseline(root, policy)
    manifest = json.loads((root / SOURCE / "manifest.json").read_text())
    if manifest["policy_sha256"] != sha((root / POLICY).read_bytes()) or manifest["baseline_inventories"] != bindings:
        raise ValueError("Refresh baseline or policy drift")
    new, complete, receipts = refreshed(root, old, manifest)
    observed = compare(old, new, complete)
    observed["binding"] = {"source_manifest_sha256": sha((root / SOURCE / "manifest.json").read_bytes()),
                           "baseline_inventories": bindings, "observed_on": policy["observation_date"]}
    observed["publications"] = {"successfully_observed": len(complete), "not_requested": receipts["not_requested_due_to_budget"],
                                "request_failures": [r for r in receipts["receipts"] if not r.get("path")],
                                "collection_observation_status": "observed" if any(r.get("path") == "api/collection.json" for r in receipts["receipts"]) else "unknown"}
    previous_collection = {r["publication_url"] for r in old if r["family"] == "dmg"}
    current_collection = set(receipts["observed_collection_publications"])
    observed["collection_links"] = {
        "added": sorted(current_collection - previous_collection) if observed["publications"]["collection_observation_status"] == "observed" else None,
        "removed": sorted(previous_collection - current_collection) if observed["publications"]["collection_observation_status"] == "observed" else None,
        "scope": "DMG collection membership only; removal is not repeal or absence from a directly observed publication"}
    return {"evaluation/source-refresh/observed-comparison.json": pretty(observed),
            "evaluation/source-refresh/baseline-self-check.json": pretty(compare(old, old, {r["publication_url"] for r in old})),
            "evaluation/source-refresh/synthetic-controls.json": pretty(synthetic_controls())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acquire", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.acquire and args.check:
        parser.error("Choose network acquisition or offline check, not both")
    if args.acquire:
        acquire()
        return
    differences = []
    outputs = build()
    for name, data in outputs.items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                differences.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if differences:
        raise SystemExit("Source comparison drift: " + ", ".join(differences))
    print(json.dumps({"ok": True, "outputs": len(outputs), "network_access": False, "source_bindings_changed": False}))


if __name__ == "__main__":
    main()
