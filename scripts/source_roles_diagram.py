#!/usr/bin/env python3
"""Render and verify the one source-roles Mermaid diagram as a static SVG."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN = Path("docs/learning-path.md")
SVG = Path("docs/source-roles-diagram.svg")
PUBLISHED_SVG = "assets/source-roles-diagram.svg"
HEADING = "### How law, guidance and people fit together"
EXPECTED_NODES = {"LAW", "CASES", "DMG", "CPAG", "CITIZEN", "DM", "ADVISER"}
NODE = re.compile(r'^\s*([A-Z]+)\["([^"\n]+)"\]\s*$')
EDGE = re.compile(r'^\s*([A-Z]+) -->\|([^|\n]+)\| ([A-Z]+)\s*$')
CLASS_DEF = re.compile(r'^\s*classDef (\w+) fill:(#[0-9a-fA-F]{6}),stroke:(#[0-9a-fA-F]{6}),color:(#[0-9a-fA-F]{6})\s*$')
CLASS = re.compile(r'^\s*class ([A-Z,]+) (\w+)\s*$')
STAMP = re.compile(r'mermaid-sha256: ([a-f0-9]{64})')


def mermaid(markdown: str) -> str:
    start = markdown.index(HEADING)
    start = markdown.index("```mermaid\n", start) + len("```mermaid\n")
    end = markdown.index("\n```", start)
    return markdown[start:end] + "\n"


def parse(source: str) -> tuple[dict, list, dict, dict]:
    nodes, edges, colours, classes = {}, [], {}, {}
    lines = source.splitlines()
    if not lines or lines[0] != "flowchart TD":
        raise ValueError("Expected one top-down source-roles diagram")
    for line in lines[1:]:
        if not line.strip():
            continue
        if match := NODE.fullmatch(line):
            key, label = match.groups()
            if key in nodes:
                raise ValueError("Duplicate diagram node")
            nodes[key] = label.replace("<br/>", "\n")
        elif match := EDGE.fullmatch(line):
            edges.append(match.groups())
        elif match := CLASS_DEF.fullmatch(line):
            name, fill, stroke, colour = match.groups()
            colours[name] = (fill, stroke, colour)
        elif match := CLASS.fullmatch(line):
            ids, name = match.groups()
            for key in ids.split(","):
                if key in classes:
                    raise ValueError("Duplicate diagram class")
                classes[key] = name
        else:
            raise ValueError(f"Unsupported source-roles Mermaid line: {line}")
    if set(nodes) != EXPECTED_NODES or set(classes) != EXPECTED_NODES or len(edges) != 12:
        raise ValueError("Source-roles node or edge census changed")
    if any(a not in nodes or b not in nodes or not label.strip() for a, label, b in edges):
        raise ValueError("Invalid source-roles edge")
    if any(name not in colours for name in classes.values()):
        raise ValueError("Missing source-roles colour")
    return nodes, edges, colours, classes


def dot_source(source: str) -> str:
    nodes, edges, colours, classes = parse(source)
    lines = ['digraph sources {', 'graph [rankdir=TB, bgcolor="white", pad="0.3", nodesep="0.7", ranksep="1.0", splines=polyline];',
             'node [shape=box, style="rounded,filled", penwidth=2, fontname="Arial", fontsize=16, margin="0.25,0.16"];',
             'edge [fontname="Arial", fontsize=10, color="#59636e", fontcolor="#17212b", arrowsize=0.8];',
             '{ rank=same; LAW; CASES; }', '{ rank=same; DMG; CPAG; }', '{ rank=same; DM; ADVISER; }']
    def quote(value: str) -> str:
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    for key, label in nodes.items():
        fill, stroke, colour = colours[classes[key]]
        lines.append(f'{key} [label={quote(label)}, fillcolor="{fill}", color="{stroke}", fontcolor="{colour}"];')
    for start, label, end in edges:
        lines.append(f'{start} -> {end} [label={quote(label)}];')
    lines.append('}')
    return "\n".join(lines) + "\n"


def stamp(source: str) -> str:
    return hashlib.sha256(source.encode()).hexdigest()


def render(markdown: str) -> bytes:
    source = mermaid(markdown)
    graph = subprocess.run(["dot", "-Tsvg"], input=dot_source(source).encode(), capture_output=True, check=True).stdout
    marker = f"<!-- mermaid-sha256: {stamp(source)} -->\n".encode()
    return graph.replace(b"<svg ", marker + b"<svg ", 1)


def check(markdown: str, raw: bytes) -> None:
    source = mermaid(markdown)
    nodes, edges, _, _ = parse(source)
    decoded = raw.decode()
    match = STAMP.search(decoded)
    if not match or match.group(1) != stamp(source):
        raise ValueError("Static source-roles SVG differs from the Mermaid source")
    if any(token in decoded.lower() for token in ("<script", "foreignobject", "javascript:", "data:", "<image")):
        raise ValueError("Static source-roles SVG contains an active or external element")
    tree = ET.fromstring(raw)
    if tree.tag != "{http://www.w3.org/2000/svg}svg":
        raise ValueError("Static source-roles asset is not SVG")
    allowed_tags = {f"{{http://www.w3.org/2000/svg}}{name}" for name in ("svg", "g", "title", "polygon", "path", "text")}
    allowed_attributes = {"class", "d", "fill", "font-family", "font-size", "height", "id", "points", "stroke", "stroke-width", "text-anchor", "transform", "version", "viewBox", "width", "x", "{http://www.w3.org/XML/1998/namespace}space", "y"}
    if any(node.tag not in allowed_tags or set(node.attrib) - allowed_attributes for node in tree.iter()):
        raise ValueError("Static source-roles SVG contains an unexpected element or attribute")
    titles = {"".join(node.itertext()) for node in tree.iter() if node.tag == "{http://www.w3.org/2000/svg}title"}
    if not set(nodes) <= titles or not {f"{a}->{b}" for a, _, b in edges} <= titles:
        raise ValueError("Static source-roles SVG omits a Mermaid node or edge")
    if len(raw) > 65536:
        raise ValueError("Static source-roles SVG exceeds 64 KiB")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    markdown = (ROOT / MARKDOWN).read_text()
    if args.check:
        check(markdown, (ROOT / SVG).read_bytes())
        print("Source-roles Mermaid and static SVG match")
    else:
        raw = render(markdown)
        check(markdown, raw)
        (ROOT / SVG).write_bytes(raw)
        print(f"Built {SVG} ({len(raw)} bytes)")


if __name__ == "__main__":
    main()
