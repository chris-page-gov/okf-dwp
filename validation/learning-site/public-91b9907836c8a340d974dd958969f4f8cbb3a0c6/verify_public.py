#!/usr/bin/env python3
"""Bounded publication identity and internal-link audit; no browser or model calls."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import stat
import subprocess
import time
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

BASE = "https://chris-page-gov.github.io/okf-dwp/"
COMMIT = "91b9907836c8a340d974dd958969f4f8cbb3a0c6"
MAX_FILES = 200
MAX_MANIFEST = 128 * 1024
MAX_MEMBER = 2 * 1024 * 1024
MAX_TOTAL = 32 * 1024 * 1024
ROOT_DOCS = {"README.md", "CHANGELOG.md", "NOTICE.md", "AI_USAGE.md", "LICENSE_DECISIONS.md", "REPOSITORY_STATUS.md"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def directory(path):
    path = Path(path).absolute()
    for item in [*reversed(path.parents), path]:
        require(stat.S_ISDIR(item.lstat().st_mode), "Directory or parent is not a regular directory")
    return path


def bounded_read(path, limit):
    path = Path(path).absolute()
    directory(path.parent)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_size <= limit, "Invalid or oversized local file")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        opened = os.fstat(stream.fileno())
        require((opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino), "Local file changed before reading")
        raw = stream.read(limit + 1)
    require(len(raw) <= limit and len(raw) == before.st_size == opened.st_size, "Local file size changed")
    return raw


def safe_path(value):
    require(isinstance(value, str) and value and not value.startswith("/") and
            not any(c in value for c in "\\\0?#%") and
            all(part not in {"", ".", ".."} for part in value.split("/")), "Unsafe publication path")
    return value


def validate_manifest(value):
    require(set(value) == {"schema", "source_commit", "source_pages", "page_count", "files", "scope"}, "Unexpected manifest fields")
    require(value["schema"] == "okf-dwp-learning-site.v1" and value["source_commit"] == COMMIT, "Wrong source identity")
    require(isinstance(value["files"], list) and 1 <= len(value["files"]) <= MAX_FILES, "Output census outside bound")
    require(isinstance(value["source_pages"], list) and 1 <= len(value["source_pages"]) <= MAX_FILES, "Source census outside bound")
    require(value["page_count"] == len(value["source_pages"]), "Source page count differs")
    groups = []
    for key in ("source_pages", "files"):
        rows = {}
        for row in value[key]:
            require(isinstance(row, dict) and set(row) == {"path", "bytes", "sha256"}, "Invalid manifest entry")
            name = safe_path(row["path"])
            require(name not in rows, "Duplicate manifest path")
            require(type(row["bytes"]) is int and 0 <= row["bytes"] <= MAX_MEMBER, "Member outside byte bound")
            require(isinstance(row["sha256"], str) and len(row["sha256"]) == 64 and all(c in "0123456789abcdef" for c in row["sha256"]), "Invalid digest")
            if key == "source_pages":
                parts = PurePosixPath(name).parts
                require(name.endswith(".md") and not any(p.startswith(".") for p in parts) and
                        (name in ROOT_DOCS or parts[0] in {"docs", "evaluation"}), "Source is outside public documentation allowlist")
            rows[name] = row
        require(sum(row["bytes"] for row in rows.values()) <= MAX_TOTAL, "Manifest exceeds total byte bound")
        groups.append(rows)
    sources, files = groups
    expected = {str(PurePosixPath(name).with_suffix(".html")) for name in sources} | {"index.html", "assets/learning.css", ".nojekyll"}
    require(set(files) == expected, "Unexpected generated output paths")
    return sources, files


def verify_sources(repo, sources):
    """Only public allowlisted blobs at the exact commit; never the worktree."""
    directory(repo)
    checked = []
    for name, row in sorted(sources.items()):
        ref = COMMIT + ":" + name
        size = subprocess.check_output(["git", "cat-file", "-s", ref], cwd=repo, timeout=10)
        require(len(size) <= 32 and int(size) == row["bytes"], "Immutable source size differs")
        child = subprocess.Popen(["git", "cat-file", "blob", ref], cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            raw = child.stdout.read(row["bytes"] + 1)
            require(len(raw) == row["bytes"], "Immutable source exceeds declared size")
            require(child.wait(timeout=10) == 0 and sha(raw) == row["sha256"], "Immutable source digest differs")
        finally:
            child.stdout.close()
            if child.poll() is None:
                child.kill()
                child.wait()
        checked.append(row)
    return checked


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        raise ValueError("Publication redirect refused")


def fetch_one(name, expected, deadline):
    started = time.monotonic()
    row = {"path": name, "url": BASE + name, "started_at": datetime.now(timezone.utc).isoformat(), "status": "failed"}
    try:
        remaining = deadline - started
        require(remaining > 0, "Total request time bound exceeded")
        request = Request(row["url"], headers={"Accept-Encoding": "identity", "User-Agent": "OKF-DWP bounded publication verifier"})
        with build_opener(NoRedirect()).open(request, timeout=min(15, remaining)) as response:
            row.update(http_status=response.status, response_url=response.geturl())
            require(response.status == 200 and response.geturl() == row["url"], "Unexpected response status or URL")
            chunks, length = [], 0
            while length <= expected["bytes"]:
                require(time.monotonic() < deadline, "Total request time bound exceeded")
                chunk = response.read1(min(65536, expected["bytes"] + 1 - length))
                if not chunk:
                    break
                chunks.append(chunk)
                length += len(chunk)
            raw = b"".join(chunks)
        row.update(bytes=len(raw), sha256=sha(raw))
        require(len(raw) == expected["bytes"] and sha(raw) == expected["sha256"], "Published bytes differ from exact generated candidate")
        row["status"] = "matched"
        return row, raw
    except Exception as error:
        row["error_type"] = type(error).__name__
        # Avoid retaining arbitrary server response bodies or exception strings.
        return row, None
    finally:
        row["elapsed_ms"] = round((time.monotonic() - started) * 1000, 2)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])


def audit_links(materials):
    pages = {}
    for name, raw in materials.items():
        if name.endswith(".html"):
            page = Links()
            page.feed(raw.decode("utf-8"))
            pages[name] = page
    errors, per_page = [], []
    internal = external = 0
    for name, page in sorted(pages.items()):
        local = outside = 0
        for identifier in set(page.ids):
            if page.ids.count(identifier) > 1:
                errors.append({"page": name, "kind": "duplicate-id", "target": identifier})
        for href in page.links:
            parsed = urlsplit(urljoin(BASE + name, href))
            base = urlsplit(BASE)
            if parsed.scheme != base.scheme or parsed.netloc != base.netloc or not parsed.path.startswith(base.path):
                outside += 1
                continue
            local += 1
            target = unquote(parsed.path[len(base.path):])
            if not target or target.endswith("/"):
                target += "index.html"
            normalised = posixpath.normpath(target)
            if normalised != target or target not in materials:
                errors.append({"page": name, "kind": "missing-target", "target": href})
            elif parsed.fragment and target.endswith(".html") and unquote(parsed.fragment) not in pages[target].ids:
                errors.append({"page": name, "kind": "missing-fragment", "target": href})
        internal += local
        external += outside
        per_page.append({"path": name, "ids": len(page.ids), "internal_links": local, "external_links_not_fetched": outside})
    return {"html_pages": len(pages), "internal_links": internal, "external_links_not_fetched": external,
            "errors": errors, "pages": per_page,
            "scope": "Anchor hrefs and fragment IDs in received HTML; not external links, browser layout or assistive-technology acceptance."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dwp-root", type=Path, required=True)
    parser.add_argument("--expected-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    directory(args.output.parent)
    # Refuse an existing file or symlink before network or source reads.
    fd = os.open(args.output, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o644)
    result = {"schema": "okf-dwp-learning-site-public-verification.v2", "source_commit": COMMIT,
              "base_url": BASE, "started_at": datetime.now(timezone.utc).isoformat(), "status": "failed",
              "requests": [], "limits": {"files": MAX_FILES, "manifest_bytes": MAX_MANIFEST,
              "member_bytes": MAX_MEMBER, "total_bytes": MAX_TOTAL, "parallel_requests": 4,
              "socket_operation_timeout_seconds": 15, "request_start_and_read_deadline_seconds": 180, "retries": 0},
              "limitations": ["Point-in-time public HTTP identity and internal-link audit; no browser, model or external-link verification.",
                              "No corpus downloads or private correspondence reads; only allowlisted public documentation source blobs."]}
    try:
        result["phase"] = "expected-manifest"
        expected_raw = bounded_read(args.expected_manifest, MAX_MANIFEST)
        expected = json.loads(expected_raw)
        sources, files = validate_manifest(expected)
        require(sum(row["bytes"] + 1 for row in files.values()) + len(expected_raw) + 1 <= MAX_TOTAL,
                "Response body reservations exceed aggregate byte bound")
        result.update(expected_manifest_sha256=sha(expected_raw), verifier_sha256=sha(bounded_read(__file__, MAX_MEMBER)),
                      source_pages=len(sources), listed_outputs=len(files))
        result["phase"] = "immutable-source-blobs"
        result["immutable_sources"] = verify_sources(args.dwp_root, sources)
        deadline = time.monotonic() + 180
        result["phase"] = "public-manifest"
        row, public_raw = fetch_one("site-manifest.json", {"bytes": len(expected_raw), "sha256": sha(expected_raw)}, deadline)
        result["requests"].append(row)
        require(public_raw is not None, "Public manifest identity did not match")
        public = json.loads(public_raw)
        _, actual_files = validate_manifest(public)
        materials = {"site-manifest.json": public_raw}
        result["phase"] = "public-files"
        with ThreadPoolExecutor(max_workers=4) as executor:
            pending = [(name, executor.submit(fetch_one, name, item, deadline)) for name, item in sorted(actual_files.items())]
            for name, future in pending:
                request_row, raw = future.result()
                result["requests"].append(request_row)
                if raw is not None:
                    materials[name] = raw
        require(all(row["status"] == "matched" for row in result["requests"]), "One or more public files failed verification")
        result["phase"] = "internal-links"
        result["link_audit"] = audit_links(materials)
        require(not result["link_audit"]["errors"], "Internal link audit failed")
        result["status"] = "passed"
        result["phase"] = "complete"
    except Exception as error:
        result["error_type"] = type(error).__name__
    finally:
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        result["matched_requests"] = sum(row["status"] == "matched" for row in result["requests"])
        result["transferred_bytes"] = sum(row.get("bytes", 0) for row in result["requests"])
        with os.fdopen(fd, "w") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
    print(json.dumps({key: result[key] for key in ("status", "source_commit", "matched_requests", "transferred_bytes")}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
