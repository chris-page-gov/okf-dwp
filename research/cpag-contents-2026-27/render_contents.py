#!/usr/bin/env python3
"""Render offline metadata projections from the observed public contents JSON."""
from collections import Counter
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "contents.json").read_text())
entries = data["entries"]
by_id = {row["id"]: row for row in entries}
book_url = "https://askcpag.org.uk/?id=" + data["source_id"]

lines = [
    "# Welfare Benefits Handbook 2026/27: contents with links", "",
    "Publisher: Child Poverty Action Group (CPAG). "
    "[Original handbook](" + data["source_url"] + ").", "",
    "Observed on 15 September 2026. **90 linked entries: 10 parts, 68 chapters, "
    "5 appendices and 7 front/back-matter or container entries.**", "",
    "This is the complete observed contents listing at part, chapter and appendix "
    "level. It preserves the public navigation order. Chapter subsections, index "
    "entries and handbook prose are outside this harvest.", "",
    "The links were visible without logging in. The source displays subscription "
    "notices for the underlying content. Each URL was observed as a public link; "
    "individual chapter/appendix destinations were not tested. CPAG's rights "
    "and terms remain applicable.", "",
    "## Front matter and reference links", "",
]
for row in entries:
    if row["parent_id"] is not None:
        continue
    children = sorted((child for child in entries if child["parent_id"] == row["id"]),
                      key=lambda child: child["order"])
    if row["kind"] == "part" or row["title"] == "Appendices":
        lines += ["", f"## [{row['title']}]({row['url']})", ""]
    else:
        lines.append(f"- [{row['title']}]({row['url']})")
    lines += [f"- [{child['title']}]({child['url']})" for child in children]
lines += ["", "## Files and verification", "",
          "- [Structured contents](contents.json)",
          "- [YAML-LD projection](contents.yamlld)",
          "- [Validation report](validation.json)",
          "- [File SHA-256 values](checksums.json)", "",
          "This is a local research export. It has not been added to the published "
          "OKF bundle or presented as CPAG-approved material.", ""]
(ROOT / "contents.md").write_text("\n".join(lines))

graph = [
    {"@id": "urn:okf-dwp:cpag-public-contents:2026-27:2026-09-15",
     "@type": "schema:Dataset", "dcterms:title": data["title"],
     "dcterms:description": data["scope"],
     "dcterms:source": {"@id": data["source_url"]},
     "dcterms:rights": data["rights"]["notice"],
     "prov:generatedAtTime": {"@value": data["observed_at"], "@type": "xsd:dateTime"},
     "dcterms:references": [{"@id": row["url"]} for row in entries]},
    {"@id": book_url, "@type": "schema:Book",
     "dcterms:title": "Welfare Benefits Handbook 2026/27",
     "dcterms:publisher": {"@id": "https://cpag.org.uk/"}},
]
for row in entries:
    graph.append({
        "@id": row["url"], "@type": "schema:CreativeWork",
        "dcterms:identifier": row["id"], "dcterms:title": row["title"],
        "dcterms:type": row["kind"], "schema:position": row["order"],
        "dcterms:isPartOf": {"@id": by_id[row["parent_id"]]["url"] if row["parent_id"] else book_url},
        "prov:wasDerivedFrom": {"@id": row["observed_on"]},
        "dcterms:accessRights": "Public navigation label and link observed; underlying item access not independently tested.",
    })
linked = {"@context": {
    "schema": "https://schema.org/", "dcterms": "http://purl.org/dc/terms/",
    "prov": "http://www.w3.org/ns/prov#", "xsd": "http://www.w3.org/2001/XMLSchema#",
}, "@graph": graph}
yaml = YAML()
yaml.allow_unicode = True
yaml.width = 120
yaml.representer.ignore_aliases = lambda _: True
buffer = StringIO()
yaml.dump(linked, buffer)
rendered = "\n".join(line.rstrip() for line in buffer.getvalue().split("\n"))
assert YAML(typ="safe").load(rendered) == linked
(ROOT / "contents.yamlld").write_text(rendered)

files = []
for path in sorted(ROOT.iterdir()):
    if path.is_file() and path.name != "checksums.json":
        content = path.read_bytes()
        files.append({"path": path.name, "bytes": len(content), "sha256": sha256(content).hexdigest()})
(ROOT / "checksums.json").write_text(json.dumps({"algorithm": "sha256", "files": files}, indent=2) + "\n")
print(json.dumps({"status": "rendered", "entries": len(entries),
                  "counts": dict(Counter(row["kind"] for row in entries))}))
