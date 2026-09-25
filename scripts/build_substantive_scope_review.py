#!/usr/bin/env python3
"""Record exact source observations behind the rejected broad appendix scope."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BROAD = ROOT / "evaluation/passage-boundary-candidate/census-01/report.json"
NARROW = ROOT / "evaluation/passage-boundary-candidate/versioned-census-02/report.json"
OUTPUT = ROOT / "evaluation/passage-boundary-candidate/substantive-scope-review.json"
BARE = re.compile(r"^\s*appendix\s*$", re.I)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def main() -> None:
    broad_raw = BROAD.read_bytes()
    narrow_raw = NARROW.read_bytes()
    broad = json.loads(broad_raw)
    narrow = json.loads(narrow_raw)
    changed = [row for row in broad["changed_documents"] if row["source_role"] == "substantive"]
    assert len(changed) == 9 and narrow["changed_document_count"] == 125
    assert not any(row["source_role"] == "substantive" for row in narrow["changed_documents"])
    inventories = {}
    for family, path in (("dmg", "source/full-dmg-2026-09-15/inventory.json"),
                         ("adm", "source/adm-2026-09-19/inventory.json")):
        inventories[family] = {doc["id"]: doc for doc in json.loads((ROOT / path).read_bytes())["documents"]}
    rows = []
    for item in changed:
        family, identifier = item["family"], item["document_id"]
        doc = inventories[family][identifier]
        pdf = (ROOT / doc["pdf_path"]).read_bytes()
        extracted = (ROOT / doc["pages_path"]).read_bytes()
        assert sha(pdf) == doc["sha256"] and sha(extracted) == doc["pages_sha256"]
        pages = json.loads(extracted)
        assert pages["source_sha256"] == doc["sha256"]
        headings = []
        for page in pages["pages"]:
            lines = page["text"].splitlines(keepends=True)
            offset = 0
            for index, line in enumerate(lines):
                if BARE.fullmatch(line.strip()):
                    literal = line.encode("utf-8")
                    headings.append({"page": page["page"], "start_utf8": offset,
                        "end_utf8": offset + len(literal), "literal_sha256": sha(literal),
                        "preceding_lines": [x.strip() for x in lines[max(0, index - 3):index]],
                        "following_lines": [x.strip() for x in lines[index + 1:index + 4]],
                        "pdf_url": doc["url"] + f"#page={page['page']}"})
                offset += len(line.encode("utf-8"))
        assert headings, f"No bare heading observed in {identifier}"
        rows.append({"family": family, "document_id": identifier,
                     "pdf_path": doc["pdf_path"], "pdf_sha256": doc["sha256"],
                     "extraction_path": doc["pages_path"], "extraction_sha256": doc["pages_sha256"],
                     "broad_change": {key: item[key] for key in ("before_units", "after_units", "removed_ids", "added_ids", "before_roles", "after_roles")},
                     "bare_line_observations": headings,
                     "successor_change": "none; bare-heading split confined to historical amendments"})
    visual = ROOT / "evaluation/passage-boundary-candidate/visual/dmg-vol1-ch5-page-152.png"
    if not visual.is_file():
        raise ValueError("PDF visual observation missing")
    report = {"schema": "okf-dwp-substantive-appendix-scope-review.v1",
        "status": "broad-generic-rule-rejected; narrowed-successor-technically-reviewed-with-residuals",
        "broad_census_sha256": sha(broad_raw), "narrowed_census_sha256": sha(narrow_raw),
        "documents_reviewed": len(rows), "items": rows,
        "confirmed_false_split": {"document_id": "dmg-vol1-ch5", "page": 152,
            "finding": "The extracted standalone word Appendix is the wrapped final word of 'Annex to this Appendix' in the continuing item 3. A bare-heading split breaks the sentence.",
            "visual_path": str(visual.relative_to(ROOT)), "visual_sha256": sha(visual.read_bytes()),
            "pdf_sha256": inventories["dmg"]["dmg-vol1-ch5"]["sha256"]},
        "decision": "Keep numbered appendix handling for substantive chapters; confine bare-heading proposals to historical amendments. Other substantive appendix observations remain unadopted without their own source review.",
        "limits": "This is technical source-bound review. It does not establish legal applicability, specialist acceptance or answer quality."}
    OUTPUT.write_bytes(canonical(report))
    print(json.dumps({"documents_reviewed": len(rows), "bare_lines": sum(len(x["bare_line_observations"]) for x in rows),
                      "report_sha256": sha(OUTPUT.read_bytes())}))


if __name__ == "__main__":
    main()
