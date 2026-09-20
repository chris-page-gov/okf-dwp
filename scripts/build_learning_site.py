#!/usr/bin/env python3
"""Publish only Git-tracked, allowlisted Markdown as a small static learning site."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
BASE = "/okf-dwp/"
REPOSITORY = "https://github.com/chris-page-gov/okf-dwp"
ROOT_DOCS = {"README.md", "CHANGELOG.md", "NOTICE.md", "AI_USAGE.md", "LICENSE_DECISIONS.md", "REPOSITORY_STATUS.md"}
CSS = """html{font:18px/1.6 system-ui,sans-serif;color:#172b3a;background:#fff}body{margin:0}a{color:#075a9c;text-underline-offset:.15em}a:focus-visible,summary:focus-visible{outline:3px solid #111;background:#ffdd00;color:#111}header,footer{background:#eff4f7;padding:1rem max(1rem,calc((100% - 72rem)/2))}header strong{font-size:1.5rem}nav{display:flex;gap:.7rem 1.3rem;flex-wrap:wrap}main{max-width:72rem;margin:2rem auto;padding:0 1rem;overflow-wrap:anywhere}article{max-width:52rem}h1{font-size:2.2rem;line-height:1.15}h2{margin-top:2rem}h3{margin-top:1.5rem}p,li{max-width:75ch}pre{overflow:auto;background:#f3f5f7;padding:1rem;max-width:100%}code{font-size:.9em}table{border-collapse:collapse;display:block;overflow:auto;max-width:100%}th,td{padding:.55rem;border:1px solid #b5c3ce;text-align:left;vertical-align:top}img{max-width:100%;height:auto}.notice{background:#fff5bf;border-left:.4rem solid #645700;padding:1rem}.skip{position:absolute;left:-10000px}.skip:focus{position:static}details{margin:1.5rem 0}summary{cursor:pointer;font-weight:bold}footer{margin-top:3rem;font-size:.85rem}.source{font-size:.85rem}h1,h2,h3,h4,[id]{scroll-margin-top:1rem}@media(max-width:40rem){html{font-size:16px}h1{font-size:1.8rem}main{margin:1rem auto}}"""


def tracked_files(root: Path) -> set[str]:
    return set(subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")) - {""}


def eligible(path: str) -> bool:
    p = PurePosixPath(path)
    return (p.suffix == ".md" and not any(part.startswith(".") for part in p.parts)
            and (path in ROOT_DOCS or p.parts[0] in {"docs", "evaluation"}))


def page_path(path: str) -> str:
    return str(PurePosixPath(path).with_suffix(".html"))


def source_url(path: str, commit: str) -> str:
    return f"{REPOSITORY}/blob/{commit}/{quote(path, safe='/')}"


def rewrite_link(href: str, source: str, pages: set[str], tracked: set[str], commit: str) -> str:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or href.startswith("#") or not parsed.path:
        return href
    target = posixpath.normpath(posixpath.join(posixpath.dirname(source), unquote(parsed.path)))
    if target.startswith("../") or target.startswith("/") or any(part.startswith('.') for part in PurePosixPath(target).parts):
        return source_url(source, commit)
    if target in pages:
        path = BASE + page_path(target)
    elif any(item.startswith(target.rstrip('/') + '/') for item in tracked):
        path = f"{REPOSITORY}/tree/{commit}/{quote(target, safe='/')}"
    else:
        # Missing authored references keep their intended repository destination;
        # never substitute a misleading link back to the referring page.
        path = source_url(target, commit)
    return urlunsplit(("", "", path, parsed.query, parsed.fragment))


def render(source: str, text: str, pages: set[str], tracked: set[str], commit: str) -> tuple[str, str]:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            text = text[end + 5:]
    # Preserve only simple explicit heading anchors from Markdown HTML. All other
    # HTML remains escaped; source content cannot install scripts or event handlers.
    anchors: dict[str, str] = {}
    def anchor(match):
        key = f"OKFEXPLICITANCHOR{len(anchors)}TOKEN"
        anchors[key] = match.group(1)
        return key
    text = re.sub(r'<a\s+id="([A-Za-z0-9_-]+)"\s*>\s*</a>', anchor, text)
    md = MarkdownIt("commonmark", {"html": False}).enable("table").enable("strikethrough")
    tokens = md.parse(text)
    used: dict[str, int] = {}
    headings = []
    title = source
    for i, token in enumerate(tokens):
        if token.type == "heading_open":
            label = tokens[i + 1].content
            slug = re.sub(r"[^\w\- ]", "", label.lower()).replace(" ", "-")
            n = used.get(slug, 0)
            used[slug] = n + 1
            identifier = slug + (f"-{n}" if n else "")
            token.attrSet("id", identifier)
            if token.tag == "h1" and title == source:
                title = label
            elif token.tag in {"h2", "h3"}:
                headings.append((identifier, label))
        for child in token.children or []:
            if child.type in {"link_open", "image"}:
                attribute = "href" if child.type == "link_open" else "src"
                rewritten = rewrite_link(child.attrGet(attribute) or "", source, pages, tracked, commit)
                if child.type == 'image' and rewritten.startswith(f'{REPOSITORY}/blob/{commit}/'):
                    rewritten = rewritten.replace(f'{REPOSITORY}/blob/', 'https://raw.githubusercontent.com/chris-page-gov/okf-dwp/', 1)
                child.attrSet(attribute, rewritten)
    body = md.renderer.render(tokens, md.options, {})
    for key, identifier in anchors.items():
        body = body.replace(key, f'<a id="{html.escape(identifier)}"></a>')
    toc = "".join(f'<li><a href="#{html.escape(i)}">{html.escape(t)}</a></li>' for i, t in headings)
    toc = f'<details><summary>On this page</summary><ul>{toc}</ul></details>' if toc else ""
    result = f'''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Independent OKF-DWP learning, evidence and research documentation.">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self'; img-src https:; base-uri 'none'; form-action 'none'">
<title>{html.escape(title)} — OKF-DWP</title><link rel="stylesheet" href="{BASE}assets/learning.css"></head>
<body><a class="skip" href="#main">Skip to content</a><header><strong>OKF-DWP</strong>
<nav aria-label="Main"><a href="{BASE}index.html">Start learning</a><a href="{BASE}docs/glossary.html">Glossary</a><a href="{BASE}docs/monday-demo-2026-09-21.html">Try the demonstration</a><a href="{BASE}docs/backlog.html">Remaining work</a><a href="https://ask-okf.crpage.chatgpt.site/">Ask OKF</a></nav></header>
<main id="main"><p class="notice">Independent experimental publication. Not an official DWP service, benefits advice or an entitlement calculator.</p>
<p class="source"><a href="{html.escape(source_url(source, commit))}">View this version’s Markdown source</a></p>{toc}<article>{body}</article></main>
<footer>Published from commit <a href="{REPOSITORY}/commit/{commit}">{commit[:12]}</a>.
<a href="{BASE}NOTICE.html">Rights and limitations</a> · <a href="{BASE}CHANGELOG.html">Changelog</a> · <a href="{BASE}site-manifest.json">Publication identity</a>.
Source dates and capture dates remain distinct. This page describes the project; it does not establish which benefit rules apply.</footer></body></html>'''
    return title, result


def build(root: Path, out: Path, commit: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("A full source commit is required")
    if out.exists():
        raise ValueError("Output must be a fresh directory; do not overwrite a publication candidate")
    tracked = tracked_files(root)
    pages = {p for p in tracked if eligible(p)}
    required = {"docs/learning-path.md", "docs/glossary.md", "NOTICE.md"}
    if not required <= pages:
        raise ValueError("Learning path, glossary and notice must be Git-tracked")
    source_records = []
    tree = subprocess.check_output(["git", "ls-tree", "-rz", commit], cwd=root)
    committed = {}
    for entry in tree.split(b"\0"):
        if entry:
            metadata, name = entry.split(b"\t", 1)
            mode, kind, digest = metadata.decode().split()
            committed[name.decode()] = (mode, kind, digest)
    outputs: dict[str, bytes] = {"assets/learning.css": CSS.encode(), ".nojekyll": b""}
    for path in sorted(pages):
        full = root / path
        if full.is_symlink() or not full.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Source must be a regular repository file: {path}")
        raw = full.read_bytes()
        blob_hash = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
        if committed.get(path) != ("100644", "blob", blob_hash):
            raise ValueError(f"Source differs from the declared commit: {path}")
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError(f"Markdown page exceeds 2 MiB: {path}")
        _, rendered = render(path, raw.decode(), pages, tracked, commit)
        outputs[page_path(path)] = rendered.encode()
        source_records.append({"path": path, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
    outputs["index.html"] = outputs["docs/learning-path.html"]
    if sum(map(len, outputs.values())) > 32 * 1024 * 1024:
        raise ValueError("Static documentation exceeds 32 MiB")
    manifest = {"schema": "okf-dwp-learning-site.v1", "source_commit": commit,
                "source_pages": source_records, "page_count": len(pages),
                "files": [{"path": p, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)} for p, raw in sorted(outputs.items())],
                "scope": "Tracked public project documentation; excludes private correspondence, untracked research and corpus bodies."}
    outputs["site-manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    for path, raw in outputs.items():
        destination = out / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "_site")
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    result = build(ROOT, args.output, args.commit)
    print(json.dumps({"source_commit": args.commit, "page_count": result["page_count"], "files": len(result["files"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()
