#!/usr/bin/env python3
"""Publish Git-bound Markdown and explicitly approved retained evidence archives."""
from __future__ import annotations

import argparse
import hashlib
import html
import gzip
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
import stat
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from markdown_it import MarkdownIt
import source_roles_diagram

ROOT = Path(__file__).resolve().parents[1]
BASE = "/okf-dwp/"
REPOSITORY = "https://github.com/chris-page-gov/okf-dwp"
ROOT_DOCS = {"README.md", "CHANGELOG.md", "NOTICE.md", "AI_USAGE.md", "LICENSE_DECISIONS.md", "REPOSITORY_STATUS.md"}
EXAMPLE_REGISTRY = "evidence-examples/registry.json"
EXAMPLE_LIMIT = 32 * 1024 * 1024
HEX64 = re.compile(r"[0-9a-f]{64}")


def strict_json(raw: bytes):
    """Reject ambiguous JSON rather than choosing one duplicate or non-finite value."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError(f"Non-finite JSON value: {value}")
    def finite_float(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            invalid(value)
        return parsed
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=invalid, parse_float=finite_float)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError("Invalid retained-example JSON") from error


def relative_path(value: str) -> str:
    if (not isinstance(value, str) or not value or len(value) > 512
            or not re.fullmatch(r"[A-Za-z0-9_./-]+", value)
            or value.startswith("/") or any(part in {"", ".", ".."} or part.startswith(".")
                                               for part in value.split("/"))):
        raise ValueError("Unsafe retained-example path")
    return value


def bounded_regular(root: Path, relative: str, cap: int) -> bytes:
    """Read a regular member only after checking its root, parents and size."""
    relative_path(relative)
    root = root.absolute()
    path = root / relative
    for parent in [*reversed(root.parents), root]:
        if not stat.S_ISDIR(parent.lstat().st_mode):
            raise ValueError(f"Source parent must be a regular directory: {parent}")
    # Walk the repository-relative parents explicitly (including archive roots).
    current = root
    for part in PurePosixPath(relative).parts[:-1]:
        current /= part
        if not stat.S_ISDIR(current.lstat().st_mode):
            raise ValueError(f"Source parent must be a regular directory: {relative}")
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > cap:
        raise ValueError(f"Retained-example member must be regular and at most {cap} bytes: {relative}")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        opened = os.fstat(fd)
        if (not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino, opened.st_size)
                != (before.st_dev, before.st_ino, before.st_size)):
            raise ValueError(f"Retained-example member changed during admission: {relative}")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            raw = stream.read(cap + 1)
        if len(raw) != before.st_size or len(raw) > cap:
            raise ValueError(f"Retained-example member changed or exceeded its bound: {relative}")
        return raw
    finally:
        os.close(fd)


def file_identity(path: str, raw: bytes) -> dict:
    return {"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def committed_member(root: Path, path: str, cap: int, committed: dict) -> bytes:
    raw = bounded_regular(root, path, cap)
    blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
    if committed.get(path) != ("100644", "blob", blob):
        raise ValueError(f"Retained-example input differs from the declared commit: {path}")
    return raw


def require(ok: bool, message: str):
    if not ok:
        raise ValueError(f"Retained examples rejected: {message}")


def keys(value, expected: set[str]):
    require(isinstance(value, dict) and set(value) == expected, "unknown or missing manifest fields")


def binding(value, cap: int, *, path: bool = True):
    keys(value, {"bytes", "sha256", "path"} if path else {"bytes", "sha256"})
    require(type(value["bytes"]) is int and 0 < value["bytes"] <= cap
            and isinstance(value["sha256"], str) and HEX64.fullmatch(value["sha256"]), "invalid hash or size binding")
    if path:
        relative_path(value["path"])
    return value


def matches(raw: bytes, ref: dict):
    require(len(raw) == ref["bytes"] and hashlib.sha256(raw).hexdigest() == ref["sha256"], "file binding differs")


def utf16_length(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def verify_context_budget(context: dict, raw: bytes):
    budget = context["budget"]
    for field, minimum, maximum in (("max_nodes", 1, 200), ("max_relationships", 1, 1000),
                                     ("max_depth", 0, 8), ("max_bytes", 8192, 524288)):
        require(type(budget[field]) is int and minimum <= budget[field] <= maximum, "invalid package budget bound")
    require(isinstance(context["selected"], list) and isinstance(context["relationships"], list), "invalid package census")
    for field, count, limit in (("used_nodes", len(context["selected"]), budget["max_nodes"]),
                                ("used_relationships", len(context["relationships"]), budget["max_relationships"]),
                                ("used_bytes", len(raw), budget["max_bytes"])):
        require(type(budget[field]) is int and budget[field] == count and count <= limit,
                "package budget census differs or exceeds its declared bound")
    require(type(budget["reached_depth"]) is int and 0 <= budget["reached_depth"] <= budget["max_depth"],
            "package budget reached depth exceeds its declared bound")
    for selected in context["selected"]:
        require(isinstance(selected["paths"], list), "invalid selected traversal paths")
        for path in selected["paths"]:
            require(isinstance(path["assertions"], list) and len(path["assertions"]) <= budget["max_depth"],
                    "selected traversal exceeds package budget depth")


def verify_archive_case(files: dict[str, bytes], row: dict, approved: dict, context: dict, raw: bytes) -> set[str]:
    """Check the archive's fixed references and every reconstructed evidence value."""
    folder = approved["package"]["canonical_sha256"]
    require(row["path"] == f"{folder}/descriptor.json" and row["package_sha256"] == folder, "case path differs")
    descriptor_raw = files[row["path"]]
    matches(descriptor_raw, binding(row["descriptor"], 65536, path=False))
    d = strict_json(descriptor_raw)
    require(d["schema"] == "okf-context-archive.v1" and d["ai_answer"] is None, "unexpected descriptor or AI answer")
    for field in ("id", "title", "question_sha256", "source_version", "engine_id", "original_engine_id", "observation_kind", "publication_note"):
        require(d[field] == approved[field], f"descriptor {field} differs from approval")
    for field in ("id", "title", "evidence_status", "observation_kind"):
        require(row[field] == d[field], f"index {field} differs from descriptor")
    require(d["input_receipt"] == approved["receipt"], "descriptor receipt differs")
    for field in ("question", "context_id", "bundle", "binding", "budget", "evidence_status"):
        require(d[field] == context[field], f"descriptor {field} differs from original package")
    require(d["package_sha256"] == folder and d["package_bytes"] == len(raw)
            and hashlib.sha256(context["question"].encode()).hexdigest() == d["question_sha256"], "package/question identity differs")
    require(files[f"{folder}/package.json"] == raw, "canonical package bytes changed")
    selected, relationships = context["selected"], context["relationships"]
    require(len(selected) <= 200 and len(relationships) <= 1000
            and d["counts"] == {"records": len(selected), "relationships": len(relationships)}, "context census exceeds limits or differs")
    used = {row["path"], f"{folder}/package.json"}

    def resource(ref, cap=65536):
        binding(ref, cap, path=False)
        name = f"{folder}/data/{ref['sha256']}.json"
        require(name in files, "missing referenced resource")
        matches(files[name], ref)
        used.add(name)
        return strict_json(files[name])

    def stream(refs, section, record_id=None):
        require(isinstance(refs, list) and 0 < len(refs) <= 1024, "invalid resource stream")
        text, offset, first = "", 0, None
        for i, ref in enumerate(refs):
            part = resource(ref)
            require(part["schema"] == "okf-context-read.v1" and part["context_id"] == context["context_id"]
                    and part["evidence_status"] == context["evidence_status"] and part["ai_answer"] is None
                    and part["section"] == section and part["record_id"] == record_id
                    and part["character_unit"] == "utf-16-code-units" and isinstance(part["data"], str)
                    and part["offset"] == offset, "resource stream identity or offset differs")
            end = offset + utf16_length(part["data"])
            require(part["end_offset"] == end and part["next_offset"] == (None if i == len(refs) - 1 else end), "resource stream gap")
            if first is None:
                first = part
            require((part["content_sha256"], part["total_characters"]) == (first["content_sha256"], first["total_characters"]), "resource stream content identity differs")
            text += part["data"]
            require(len(text.encode()) <= 524288, "decoded stream exceeds 512 KiB")
            offset = end
        require(offset == first["total_characters"] and hashlib.sha256(text.encode()).hexdigest() == first["content_sha256"], "complete stream hash differs")
        return text

    keys(d["sections"], {"package", "relationships", "diagnostics"})
    require(stream(d["sections"]["package"], "package").encode() == raw, "package stream differs from original bytes")
    require(strict_json(stream(d["sections"]["relationships"], "relationships").encode()) == relationships, "relationships changed")
    diagnostics = {k: v for k, v in context.items() if k not in {"selected", "relationships"}}
    diagnostics.update(selected_records=len(selected), relationship_count=len(relationships))
    require(strict_json(stream(d["sections"]["diagnostics"], "diagnostics").encode()) == diagnostics, "diagnostics changed")
    record_rows = []
    require(isinstance(d["record_indexes"], list) and len(d["record_indexes"]) <= 200, "invalid record index list")
    for ref in d["record_indexes"]:
        rows = resource(ref, 16384)
        require(isinstance(rows, list), "record index must be an array")
        record_rows.extend(rows)
    require([x["id"] for x in record_rows] == [x["record"]["id"] for x in selected], "record indexes differ from selected records")
    for entry, item in zip(record_rows, selected):
        keys(entry, {"id", "text", "metadata"})
        record = item["record"]
        require(stream(entry["text"], "record_text", entry["id"]) == record["text"], "record text changed")
        metadata = {**item, "record": {k: v for k, v in record.items() if k != "text"}}
        metadata["record"]["text_reference"] = {"section": "record_text", "characters": utf16_length(record["text"]), "sha256": hashlib.sha256(record["text"].encode()).hexdigest()}
        require(strict_json(stream(entry["metadata"], "record_metadata", entry["id"]).encode()) == metadata, "record provenance or metadata changed")
    require(isinstance(d["catalogues"], list) and 0 < len(d["catalogues"]) <= 1024, "invalid catalogue list")
    catalogue = []
    for i, ref in enumerate(d["catalogues"]):
        page = resource(ref, 16384)
        require(page["schema"] == "okf-context-manifest.v1" and page["context_id"] == context["context_id"]
                and page["evidence_status"] == context["evidence_status"] and page["question"] == context["question"]
                and page["bundle"] == context["bundle"] and page["binding"] == context["binding"], "catalogue identity differs")
        delivery = page["delivery"]
        require(delivery["offset"] == len(catalogue) and delivery["total"] == len(selected)
                and delivery["returned"] == len(page["records"]), "catalogue census differs")
        catalogue.extend(page["records"])
        require(delivery["next_offset"] == (None if i == len(d["catalogues"]) - 1 else len(catalogue)), "catalogue pagination gap")
    expected = []
    for item in selected:
        record = item["record"]
        source = (record["provenance"] or [{}])[0]
        expected.append({"id": record["id"], "label": record["label"], "kind": record["kind"],
                         "assertion_status": record["assertion_status"], "text_characters": utf16_length(record["text"]),
                         "text_sha256": hashlib.sha256(record["text"].encode()).hexdigest(), "source_url": source.get("url", ""),
                         "source_locator": source.get("locator", ""), "authority_class": record["authority"]["class"],
                         "review_status": record.get("review_status", "not-declared"), "reasons": len(item["reasons"]), "paths": len(item["paths"])})
    require(catalogue == expected, "catalogue record metadata differs from original package")
    case_files = {path for path in files if path.startswith(folder + "/")}
    require(used == case_files and len(case_files) <= 1024 and sum(len(files[p]) for p in case_files) <= 8 * 1024 * 1024, "unreferenced files or excessive case archive")
    require(row["files"] == len(case_files) and row["bytes"] == sum(len(files[p]) for p in case_files), "index archive census differs")
    return used


def retained_examples(root: Path, tracked: set[str], committed: dict) -> tuple[dict[str, bytes], dict | None]:
    """Admit only a reviewed, commit-bound declaration; never scan general JSON."""
    if EXAMPLE_REGISTRY not in committed:
        require(EXAMPLE_REGISTRY not in tracked, "approval registry is not in the declared commit")
        return {}, None
    inputs = {}
    def read(path, cap):
        raw = committed_member(root, path, cap, committed)
        inputs[path] = file_identity(path, raw)
        return raw
    def bound(ref, cap):
        binding(ref, cap)
        raw = read(ref["path"], cap)
        matches(raw, ref)
        return raw
    approval_raw = read(EXAMPLE_REGISTRY, 65536)
    approval = strict_json(approval_raw)
    keys(approval, {"schema", "releases"})
    require(approval["schema"] == "okf-dwp-retained-evidence-publication.v1"
            and isinstance(approval["releases"], list) and 0 < len(approval["releases"]) <= 3, "invalid approval registry")
    outputs, releases, ids, total_cases = {}, [], set(), 0
    for release in approval["releases"]:
        keys(release, {"id", "archive_root", "registry", "artifact_manifest", "exporter", "approved_publication", "publication_note"})
        slug = release["id"]
        require(isinstance(slug, str) and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", slug)
                and slug not in ids and release["approved_publication"] is True
                and isinstance(release["publication_note"], str) and 0 < len(release["publication_note"]) <= 2048, "release lacks unique identity or explicit approval")
        ids.add(slug)
        prefix = f"evidence-examples/{slug}"
        require(release["archive_root"] == prefix and release["artifact_manifest"]["path"] == f"{prefix}/artifact-manifest.json", "archive root differs from approved release")
        require(release["registry"]["path"].startswith("evaluation/"), "export registry must be under evaluation")
        registry_raw = bound(release["registry"], 65536)
        registry = strict_json(registry_raw)
        keys(registry, {"schema", "cases"})
        require(registry["schema"] == "okf-context-archive-registry.v1" and isinstance(registry["cases"], list)
                and 0 < len(registry["cases"]) <= 3, "invalid export registry")
        total_cases += len(registry["cases"])
        require(total_cases <= 3, "publication exceeds three approved examples")
        manifest_raw = bound(release["artifact_manifest"], 1024 * 1024)
        manifest = strict_json(manifest_raw)
        keys(manifest, {"schema", "registry_sha256", "exporter_files", "files"})
        require(manifest["schema"] == "okf-context-archive-artifacts.v1"
                and manifest["registry_sha256"] == hashlib.sha256(registry_raw).hexdigest(), "archive registry binding differs")
        exporter = release["exporter"]
        keys(exporter, {"repository", "commit", "files"})
        require(exporter["repository"] == "https://github.com/chris-page-gov/okf-explorer"
                and isinstance(exporter["commit"], str) and re.fullmatch(r"[a-f0-9]{40}", exporter["commit"])
                and isinstance(exporter["files"], list) and 1 <= len(exporter["files"]) <= 32
                and exporter["files"] == manifest["exporter_files"], "exporter provenance differs from approval")
        exporter_files = {}
        for ref in exporter["files"]:
            binding(ref, 1024 * 1024)
            require(ref["path"] not in exporter_files and ref["path"].startswith(("tools/context-archive/", "profiles/context-archive/", "profiles/context-assembly/", "apps/okf-explorer/src/lib/context/")), "unexpected exporter dependency")
            exporter_files[ref["path"]] = ref
        require(isinstance(manifest["files"], list) and 0 < len(manifest["files"]) <= 3077, "excessive archive inventory")
        files = {}
        for ref in manifest["files"]:
            binding(ref, 524288)
            path = ref["path"]
            require(path not in files and re.fullmatch(r"(?:index\.(?:html|json)|reader\.(?:mjs|css)|shared\.mjs|[a-f0-9]{64}/(?:descriptor\.json|package\.json|data/[a-f0-9]{64}\.json))", path), "duplicate or unapproved archive path")
            cap = 524288 if path.endswith("/package.json") else 16384 if path == "index.json" else 65536
            raw = read(f"{prefix}/{path}", cap)
            matches(raw, ref)
            files[path] = raw
            require(sum(map(len, files.values())) <= EXAMPLE_LIMIT, "archive exceeds 32 MiB")
        fixed = {"index.html", "index.json", "reader.mjs", "shared.mjs", "reader.css"}
        require(fixed <= files.keys(), "missing fixed reader assets")
        for name in ("reader.mjs", "shared.mjs", "reader.css"):
            require(f"tools/context-archive/{name}" in exporter_files, "missing reader dependency binding")
            matches(files[name], exporter_files[f"tools/context-archive/{name}"])
        index = strict_json(files["index.json"])
        keys(index, {"schema", "registry_sha256", "cases"})
        require(index["schema"] == "okf-context-archive-index.v1" and index["registry_sha256"] == manifest["registry_sha256"]
                and len(index["cases"]) == len(registry["cases"]), "root index differs from approved registry")
        index_tag = f'name="okf-archive-index" content="{hashlib.sha256(files["index.json"]).hexdigest()}:{len(files["index.json"])}"'.encode()
        require(files["index.html"].count(index_tag) == 1, "HTML does not bind the exact archive index")
        seen_cases, seen_packages, used = set(), set(), set(fixed)
        for entry, row in zip(registry["cases"], index["cases"]):
            keys(entry, {"id", "title", "package", "receipt", "question_sha256", "source_version", "engine_id", "original_engine_id", "observation_kind", "approved_publication", "publication_note"})
            require(entry["approved_publication"] is True and entry["observation_kind"] in {"local", "public", "synthetic"}
                    and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", entry["id"]) and entry["id"] not in seen_cases, "invalid or duplicate case approval")
            seen_cases.add(entry["id"])
            package = entry["package"]
            keys(package, {"path", "bytes", "sha256", "encoding", "canonical_bytes", "canonical_sha256"})
            require(package["path"].startswith(("evaluation/", "validation/")) and entry["receipt"]["path"].startswith(("evaluation/", "validation/")), "package and receipt must be retained evaluation inputs")
            encoded = bound({k: package[k] for k in ("path", "bytes", "sha256")}, 1048576)
            require(package["encoding"] in {"json", "gzip"}, "unsupported package encoding")
            if package["encoding"] == "gzip":
                with gzip.GzipFile(fileobj=io.BytesIO(encoded)) as stream:
                    raw = stream.read(524289)
            else:
                raw = encoded
            canonical_ref = binding({"bytes": package["canonical_bytes"], "sha256": package["canonical_sha256"]}, 524288, path=False)
            matches(raw, canonical_ref)
            require(package["canonical_sha256"] not in seen_packages, "duplicate canonical package")
            seen_packages.add(package["canonical_sha256"])
            bound(entry["receipt"], 2097152)
            context = strict_json(raw)
            require(context["schema"] == "okf-governed-context.v1" and context["ai_answer"] is None
                    and re.fullmatch(r"urn:sha256:[a-f0-9]{64}", context["context_id"]), "invalid package or identity")
            verify_context_budget(context, raw)
            used.update(verify_archive_case(files, row, entry, context, raw))
        require(used == set(files), "archive contains unreferenced files")
        declared = {f"{prefix}/{p}" for p in files} | {f"{prefix}/artifact-manifest.json"}
        require({p for p in committed if p.startswith(prefix + "/")} == declared, "committed archive census differs from manifest")
        # Untracked files never enter the copy plan; every admitted byte is listed.
        outputs.update({f"{prefix}/{p}": raw for p, raw in files.items()})
        outputs[f"{prefix}/artifact-manifest.json"] = manifest_raw
        releases.append({"id": slug, "archive_root": prefix, "registry": release["registry"],
                         "artifact_manifest": release["artifact_manifest"], "exporter": exporter,
                         "cases": len(registry["cases"]), "publication_note": release["publication_note"]})
    return outputs, {"approval": file_identity(EXAMPLE_REGISTRY, approval_raw), "releases": releases,
                     "inputs": [inputs[p] for p in sorted(inputs)],
                     "exporter_identity_check": "Module hashes match the Git-approved declaration; the remote Explorer commit is declared provenance, not independently fetched or attested by this build."}
CSS = """html{font:18px/1.6 system-ui,sans-serif;color:#172b3a;background:#fff}body{margin:0}a{color:#075a9c;text-underline-offset:.15em}a:focus-visible,summary:focus-visible{outline:3px solid #111;background:#ffdd00;color:#111}header,footer{background:#eff4f7;padding:1rem max(1rem,calc((100% - 72rem)/2))}header strong{font-size:1.5rem}nav{display:flex;gap:.7rem 1.3rem;flex-wrap:wrap}main{max-width:72rem;margin:2rem auto;padding:0 1rem;overflow-wrap:anywhere}article{max-width:52rem}h1{font-size:2.2rem;line-height:1.15}h2{margin-top:2rem}h3{margin-top:1.5rem}p,li{max-width:75ch}pre{overflow:auto;background:#f3f5f7;padding:1rem;max-width:100%}code{font-size:.9em}table{border-collapse:collapse;display:block;overflow:auto;max-width:100%}th,td{padding:.55rem;border:1px solid #b5c3ce;text-align:left;vertical-align:top}img{max-width:100%;height:auto}.table-align-left{text-align:left}.table-align-center{text-align:center}.table-align-right{text-align:right}.notice{background:#fff5bf;border-left:.4rem solid #645700;padding:1rem}.skip{position:absolute;left:-10000px}.skip:focus{left:1rem;top:.5rem;z-index:1;padding:.25rem .5rem;background:#ffdd00;color:#111}details{margin:1.5rem 0}summary{cursor:pointer;font-weight:bold}footer{margin-top:3rem;font-size:.85rem}.source{font-size:.85rem}h1,h2,h3,h4,[id]{scroll-margin-top:1rem}@media(max-width:40rem){html{font-size:16px}h1{font-size:1.8rem}main{margin:1rem auto}}"""


def tracked_files(root: Path) -> set[str]:
    return set(subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")) - {""}


def committed_tree(root: Path, commit: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("A full source commit is required")
    tree = subprocess.check_output(["git", "ls-tree", "-rz", commit], cwd=root)
    committed = {}
    for entry in tree.split(b"\0"):
        if entry:
            metadata, name = entry.split(b"\t", 1)
            committed[name.decode()] = tuple(metadata.decode().split())
    return committed


def eligible(path: str) -> bool:
    p = PurePosixPath(path)
    return (p.suffix == ".md" and not any(part.startswith(".") for part in p.parts)
            and (path in ROOT_DOCS or p.parts[0] in {"docs", "evaluation"}))


def page_path(path: str) -> str:
    return str(PurePosixPath(path).with_suffix(".html"))


def source_url(path: str, commit: str) -> str:
    return f"{REPOSITORY}/blob/{commit}/{quote(path, safe='/')}"


def rewrite_link(href: str, source: str, pages: set[str], tracked: set[str], commit: str, published: set[str] | None = None) -> str:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or href.startswith("#") or not parsed.path:
        return href
    target = posixpath.normpath(posixpath.join(posixpath.dirname(source), unquote(parsed.path)))
    if target.startswith("../") or target.startswith("/") or any(part.startswith('.') for part in PurePosixPath(target).parts):
        return source_url(source, commit)
    if target in (published or set()):
        path = BASE + target
    elif target in pages:
        path = BASE + page_path(target)
    elif any(item.startswith(target.rstrip('/') + '/') for item in tracked):
        path = f"{REPOSITORY}/tree/{commit}/{quote(target, safe='/')}"
    else:
        # Missing authored references keep their intended repository destination;
        # never substitute a misleading link back to the referring page.
        path = source_url(target, commit)
    return urlunsplit(("", "", path, parsed.query, parsed.fragment))


def normalise_table_alignment(token) -> None:
    """Move only parser-generated table alignment into our external stylesheet."""
    if token.type not in {"th_open", "td_open"}:
        return
    style = token.attrs.pop("style", None)
    if style is None:
        return
    classes = {f"text-align:{value}": f"table-align-{value}" for value in ("left", "center", "right")}
    if style not in classes:
        raise ValueError("Unsupported table alignment style")
    token.attrJoin("class", classes[style])


def render(source: str, text: str, pages: set[str], tracked: set[str], commit: str, published: set[str] | None = None) -> tuple[str, str]:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            text = text[end + 5:]
    # Pages has no Mermaid runtime. Replace only this reviewed diagram with its
    # static, hash-checked asset; retain all other Mermaid source blocks.
    if source == "docs/learning-path.md" and source_roles_diagram.PUBLISHED_SVG in (published or set()):
        diagram = source_roles_diagram.mermaid(text)
        fence = f"```mermaid\n{diagram}```"
        text = text.replace(fence, "![How legislation, tribunal decisions, staff guidance, independent advice and people connect](../assets/source-roles-diagram.svg)", 1)
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
        normalise_table_alignment(token)
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
                rewritten = rewrite_link(child.attrGet(attribute) or "", source, pages, tracked, commit, published)
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
    if out.exists() or out.is_symlink():
        raise ValueError("Output must be a fresh directory; do not overwrite a publication candidate")
    tracked = tracked_files(root)
    pages = {p for p in tracked if eligible(p)}
    required = {"docs/learning-path.md", "docs/glossary.md", "NOTICE.md"}
    if not required <= pages:
        raise ValueError("Learning path, glossary and notice must be Git-tracked")
    source_records = []
    committed = committed_tree(root, commit)
    examples, retained = retained_examples(root, tracked, committed)
    from workbench_publication import publish_workbench
    workbench, workbench_receipt = publish_workbench(
        lambda path, cap: committed_member(root, path, cap, committed), committed, strict_json, verify_context_budget)
    outputs: dict[str, bytes] = {"assets/learning.css": CSS.encode(), ".nojekyll": b"", **examples, **workbench}
    learning_path = committed_member(root, "docs/learning-path.md", 2 * 1024 * 1024, committed).decode()
    if source_roles_diagram.HEADING in learning_path:
        diagram_svg = committed_member(root, str(source_roles_diagram.SVG), 65536, committed)
        source_roles_diagram.check(learning_path, diagram_svg)
        outputs[source_roles_diagram.PUBLISHED_SVG] = diagram_svg
    published_assets = set(examples) | set(workbench) | ({source_roles_diagram.PUBLISHED_SVG} if source_roles_diagram.PUBLISHED_SVG in outputs else set())
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
        _, rendered = render(path, raw.decode(), pages, tracked, commit, published_assets)
        destination = page_path(path)
        if destination in outputs:
            raise ValueError(f"Publication output collision: {destination}")
        outputs[destination] = rendered.encode()
        source_records.append({"path": path, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
    outputs["index.html"] = outputs["docs/learning-path.html"]
    publication_limit = (64 if workbench_receipt else 32) * 1024 * 1024
    if sum(map(len, outputs.values())) > publication_limit:
        raise ValueError("Static documentation and declared evidence exceed the publication limit")
    manifest = {"schema": "okf-dwp-learning-site.v1", "source_commit": commit,
                "source_pages": source_records, "page_count": len(pages),
                "files": [{"path": p, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)} for p, raw in sorted(outputs.items())],
                "scope": "Tracked public project documentation; excludes private correspondence, untracked research and corpus bodies."}
    if retained is not None:
        manifest.update(schema="okf-dwp-learning-site.v2", retained_evidence=retained,
                        scope="Tracked public project documentation and explicitly approved, bounded retained evidence examples. Excludes private correspondence, untracked research and unlisted corpus files. Retained examples do not establish legal applicability or AI answer correctness.")
    if workbench_receipt is not None:
        manifest.update(schema="okf-dwp-learning-site.v3", evidence_workbench=workbench_receipt,
                        scope="Tracked public documentation, approved retained examples and declared public staff-question workbench evidence. Excludes private correspondence and unlisted corpus files. No legal applicability or AI answer acceptance is implied.")
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
    parser.add_argument("--check-examples", action="store_true", help="Verify approved archives without writing a site")
    args = parser.parse_args()
    if args.check_examples:
        outputs, retained = retained_examples(ROOT, tracked_files(ROOT), committed_tree(ROOT, args.commit))
        print(json.dumps({"source_commit": args.commit, "retained_examples": retained is not None,
                          "files": len(outputs), "bytes": sum(map(len, outputs.values()))}))
        return
    result = build(ROOT, args.output, args.commit)
    print(json.dumps({"source_commit": args.commit, "page_count": result["page_count"], "files": len(result["files"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()
