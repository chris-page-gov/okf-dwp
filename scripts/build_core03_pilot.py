#!/usr/bin/env python3
"""Build a separate Core 0.3 candidate from the immutable Pension Credit pilot."""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import posixpath
import re
from urllib.parse import quote, unquote

from build_bundle import ROOT, ROUTE, canonical, digest


BASE_COMMIT = "3fee61fb4980f0684443c78cd3806b886eb6b772"
BASE_MANIFEST = "147c8baffa839bdee9105ecaf4e66bbb7f78e81545932e63352198fa7293c85a"
SPECIFICATION = (
    "https://github.com/open-knowledge-format/open-knowledge-format/blob/"
    "527e81aff55992be21507e97004286789126f88c/SPEC.md"
)
LEGACY_LINK = re.compile(
    r"(?<=\()https://github\.com/chris-page-gov/okf-dwp/blob/main/bundle/"
    r"(records/[^?#)\s]+\.md)(?=\))"
)
TITLE = "Pension Credit guidance · Core 0.3 evidence review"
LIMIT = (
    "Independent evidence navigation from a frozen source. "
    "The preview gives no individual entitlement assessment or judgement on current law."
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_frozen_pilot(root: Path) -> dict[str, bytes]:
    """Admit only the exact previously published pilot, including all graph planes."""
    bundle_path = root / "bundle"
    manifest_bytes = (bundle_path / "checksums.json").read_bytes()
    require(digest(manifest_bytes) == BASE_MANIFEST, "Frozen pilot checksum catalogue changed")
    manifest = json.loads(manifest_bytes)
    files = {}
    for entry in manifest["files"]:
        name = entry["path"].removeprefix("bundle/")
        path = bundle_path / name
        require(path.resolve().is_relative_to(bundle_path.resolve()) and not path.is_symlink(),
                f"Unsafe frozen pilot member {name}")
        data = path.read_bytes()
        require(len(data) == entry["bytes"] and digest(data) == entry["sha256"],
                f"Frozen pilot member changed: {name}")
        files[name] = data
    return files


def render_walkthrough(question: str, entry: str, page: str, source_url: str) -> bytes:
    reader = "../reader/explore/?bundle=/candidate/okf-explorer.json&amp;view=reader#"
    return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trace Pension Credit capital guidance</title>
<style>
  body {{ font: 1rem/1.55 system-ui, sans-serif; color: #17283b; margin: 0; background: #f4f7fa; }}
  main {{ max-width: 44rem; padding: clamp(1rem, 5vw, 3rem); margin: auto; }}
  li {{ background: white; padding: 0.8rem 1rem; margin-block: 0.6rem; border-inline-start: 0.25rem solid #345e83; overflow-wrap: anywhere; }}
  a {{ color: #174d7c; }}
</style>
</head>
<body><main>
  <p>Core OKF 0.3 development review candidate</p>
  <h1>{escape(question)}</h1>
  <ol aria-label="Evidence journey">
    <li>Open the <a href="{reader}{quote(entry)}">Pension Credit research question</a> in Explorer.</li>
    <li>Follow its research reference to <a href="{reader}{quote(page)}">chapter 84, PDF page 35</a>.
        The retained passage covers DMG 84351–84353.</li>
    <li>Compare the passage with the <a href="{escape(source_url, quote=True)}">official source at page 35</a>.
        Check nearby passages, source currency and cross-references before relying on the result.</li>
  </ol>
  <p>{escape(LIMIT)}</p>
  <p><a href="evidence.json">Read the bounded evidence packet</a></p>
</main></body>
</html>
""".encode()


def project(root: Path = ROOT) -> dict[str, bytes]:
    frozen = read_frozen_pilot(root)
    original = json.loads(frozen["okf-bundle.json"])
    require(original["okf_version"] == "0.2", "Expected the frozen Core 0.2 pilot")
    records = original["nodes"]
    record_paths = {route: f"records/{route}.md" for route in records}
    require(len(records) == 821 and all(ROUTE.fullmatch(route) for route in records),
            "Unexpected frozen pilot routes")
    require({name for name in frozen if name.startswith("records/")} == set(record_paths.values()),
            "Frozen record files differ from the Reader nodes")

    nodes = {}
    pairs = set()
    rewritten = 0
    mapped_status = []
    outputs = {}
    for original_route, source_path in record_paths.items():
        metadata = {key: value for key, value in records[original_route].items() if key != "body"}
        frontmatter, body = frozen[source_path].decode("utf-8").split("\n---\n", 1)
        local_links = {}

        def rebase(match: re.Match[str]) -> str:
            nonlocal rewritten
            target = unquote(match[1], errors="strict")
            require(target in frozen and target.startswith("records/"), f"Missing local target {target}")
            destination = posixpath.relpath(target, posixpath.dirname(source_path))
            local_links[destination] = target
            pairs.add((source_path, target))
            rewritten += 1
            return destination

        body = LEGACY_LINK.sub(rebase, body)
        if metadata["status"] == "experimental":
            old_line = "\nstatus: experimental\n"
            require(old_line in frontmatter and "x-okf-dwp-status" not in metadata,
                    f"Unexpected legacy status in {source_path}")
            frontmatter = frontmatter.replace(
                old_line, "\nstatus: draft\nx-okf-dwp-status: experimental\n", 1
            )
            metadata.update(status="draft", **{"x-okf-dwp-status": "experimental"})
            mapped_status.append(source_path)
        require(metadata["status"] in {"draft", "stable", "deprecated"},
                f"Unsupported Core 0.3 lifecycle in {source_path}")
        outputs[f"source/{source_path}"] = (frontmatter + "\n---\n" + body).encode()
        nodes[source_path] = {
            **metadata,
            "id": source_path,
            "body": body.strip(),
            "frontmatter": metadata,
            "source_path": source_path,
            "section": "records",
            "markdown_links": local_links,
        }

    typed = [
        {**row, "source": record_paths[row["source"]], "target": record_paths[row["target"]]}
        for row in original["relationships"]
    ]
    typed_pairs = {(row["source"], row["target"]) for row in typed}
    require(len(typed) == 964 and len(pairs) == 971 and rewritten == 977,
            "Frozen assertion or Markdown navigation denominator changed")
    edges = [
        {"source": source, "target": target, "kind": "references", "source_fields": ["markdown"]}
        for source, target in sorted(pairs)
    ]
    core_only = [edge for edge in edges if (edge["source"], edge["target"]) not in typed_pairs]
    frozen_index = frozen["index.md"]
    header = b'---\nokf_version: "0.2"\n---\n'
    require(frozen_index.startswith(header), "Unexpected frozen index declaration")
    index = frozen_index.replace(header, b'---\nokf_version: "0.3"\n---\n', 1)
    for name, data in frozen.items():
        if "/" not in name and name.endswith(".md"):
            outputs[f"source/{name}"] = index if name == "index.md" else data

    outputs["okf-explorer.json"] = canonical({
        "schema": original["schema"],
        "kind": original["kind"],
        "id": "okf-dwp-pension-credit-core03-preview",
        "snapshot": original["snapshot_id"],
        "version": "0.3-preview",
        "okf_version": "0.3",
        "title": TITLE,
        "status": "draft",
        "description": LIMIT,
        "meta": {
            **original["meta"],
            "title": TITLE,
            "description": LIMIT,
            "core_conformance": "OKF 0.3",
            "source_okf_version": "0.2",
            "source_commit": BASE_COMMIT,
            "okf_specification": SPECIFICATION,
            "frontmatter": {"okf_version": "0.3"},
        },
        "nodes": nodes,
        "edges": edges,
        "relationships": typed + core_only,
    })
    question = "records/question/pc001.md"
    page = "records/page/84/0035.md"
    assertion, = [row for row in typed if row["source"] == question and row["target"] == page]
    source_url = nodes[question]["sources"][0]["resource"]
    question_text = "Where does the retained staff guide discuss capital disregards?"
    require(source_url.endswith("#page=35") and (question, page) in pairs,
            "The walkthrough's exact source route changed")
    outputs["evidence.json"] = canonical({
        "schema": "okf-dwp-core03-pilot-evidence.v1",
        "question": question_text,
        "question_record": question,
        "source_record": page,
        "source_url": source_url,
        "source_pdf_sha256": nodes[page]["source_sha256"],
        "source_commit": BASE_COMMIT,
        "source_record_url": f"https://raw.githubusercontent.com/chris-page-gov/okf-dwp/{BASE_COMMIT}/bundle/{quote(page)}",
        "source_excerpt": nodes[page]["body"],
        "assertion": assertion,
        "boundary": LIMIT,
    })
    outputs["walkthrough.html"] = render_walkthrough(question_text, question, page, source_url)
    outputs["manifest.json"] = canonical({
        "schema": "okf-dwp-core03-pilot-preview.v1",
        "status": "development-review-candidate",
        "source_commit": BASE_COMMIT,
        "source_checksum_catalogue_sha256": BASE_MANIFEST,
        "core_version": "0.3",
        "specification": SPECIFICATION,
        "counts": {
            "retained_files_checked": len(frozen),
            "records": len(nodes),
            "typed_assertions": len(typed),
            "markdown_reference_pairs": len(pairs),
            "rewritten_links": rewritten,
            "additional_markdown_pairs_in_reader": len(core_only),
        },
        "legacy_status_mappings": mapped_status,
        "files": [
            {"path": name, "bytes": len(data), "sha256": digest(data)}
            for name, data in sorted(outputs.items())
        ],
    })
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = args.output.absolute()
    require(not output.resolve().is_relative_to(ROOT),
            "Candidate output must be outside the source checkout")
    outputs = project()
    if args.check:
        actual = {path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file()}
        require(actual == set(outputs), "Candidate file census changed")
        for name, data in outputs.items():
            require((output / name).read_bytes() == data, f"Candidate member changed: {name}")
    else:
        output.mkdir(parents=True, exist_ok=False)
        for name, data in outputs.items():
            path = output / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(json.dumps(json.loads(outputs["manifest.json"])["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
