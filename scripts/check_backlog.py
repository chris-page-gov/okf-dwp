#!/usr/bin/env python3
"""Check the public backlog's identities, dependencies, evidence paths and prose projection."""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"recorded_complete", "in_progress", "needs_domain_review", "needs_external_permission", "not_started"}


def validate(register, markdown, root=ROOT):
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    require(register.get("schema") == "okf-dwp-backlog.v1", "Unknown backlog schema")
    date.fromisoformat(register["updated_on"])
    require(set(register["status_meanings"]) == STATUSES, "Backlog status meanings differ")
    items = register["items"]
    require(isinstance(items, list) and items, "Backlog must contain items")
    ids = [item["id"] for item in items]
    require(len(ids) == len(set(ids)) and all(re.fullmatch(r"DWP-BL-\d{3}", value) for value in ids), "Duplicate or invalid backlog ID")
    for item in items:
        require(item["status"] in STATUSES, "Unknown backlog status")
        require(item["priority"] in {"P0", "P1", "P2"}, "Unknown backlog priority")
        for key in ["title", "owner_role", "scope_note"]:
            require(isinstance(item[key], str) and item[key].strip(), f"Missing {key}")
        for key in ["evidence", "acceptance_checks"]:
            require(isinstance(item[key], list) and item[key] and all(isinstance(v, str) and v.strip() for v in item[key]), f"Missing {key}")
        deps = item["depends_on"]
        require(isinstance(deps, list) and len(deps) == len(set(deps)) and all(d in ids for d in deps), "Unknown or duplicate dependency")
        for value in item["evidence"]:
            path = PurePosixPath(value)
            require(not path.is_absolute() and ".." not in path.parts and "\\" not in value
                    and ":" not in value and not any(p.startswith('.') or p == 'research' for p in path.parts), "Unsafe or private evidence path")
            absolute = (root / value).resolve()
            require(absolute.is_relative_to(root.resolve()) and absolute.is_file(), "Missing or external evidence file")
    by_id = {item["id"]: item for item in items}
    active, done = set(), set()

    def visit(identifier):
        require(identifier not in active, "Backlog dependency cycle")
        if identifier in done:
            return
        active.add(identifier)
        for dependency in by_id[identifier]["depends_on"]:
            visit(dependency)
        active.remove(identifier)
        done.add(identifier)

    for identifier in ids:
        visit(identifier)
    rows = [line for line in markdown.splitlines() if line.startswith("| DWP-BL-")]
    expected = ["| " + " | ".join([item["id"], item["priority"], item["title"], f'`{item["status"]}`',
                                   ", ".join(item["depends_on"]) or "—"]) + " |" for item in items]
    require(rows == expected, "Human-readable backlog rows differ from the machine register")
    return {"status": "backlog-verified", "items": len(items), "dependency_cycles": 0,
            "evidence_paths_exist": True, "markdown_matches": True,
            "limitation": "Structural checks do not establish that an acceptance check has been satisfied."}


def main():
    result = validate(json.loads((ROOT / "evaluation/backlog.json").read_text()), (ROOT / "docs/backlog.md").read_text())
    print(json.dumps(result))


if __name__ == "__main__":
    main()
