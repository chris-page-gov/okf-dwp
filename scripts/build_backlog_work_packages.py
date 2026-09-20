#!/usr/bin/env python3
"""Project the delivery and acceptance ledger without deciding review outcomes."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render(register):
    lines = ["# Delivery and acceptance work packages", "",
             "Generated from [the public backlog register](../evaluation/backlog.json).",
             "Delivery, independent human review and external permission are separate.",
             "A completed proposal or model trial does not establish specialist acceptance.", "",
             "[Backlog overview](backlog.md) · [Team handover](team-handover-2026-09-20.md)", ""]
    for item in register["items"]:
        lines += [f"## {item['id']}: {item['title']}", "",
                  f"Priority **{item['priority']}**; aggregate status `{item['status']}`.", "",
                  "| Work package | Kind | Status | Executor | Next action or retained result |",
                  "| --- | --- | --- | --- | --- |"]
        for p in item["work_packages"]:
            action = p["next_action"].replace("|", "\\|")
            lines.append(f"| `{p['id']}` | {p['kind']} | `{p['status']}` | {p['executor']} | {action} |")
        lines += ["", "Evidence: " + " · ".join(f"[{path}](../{path})" for path in item["evidence"]), ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = render(json.loads((ROOT / "evaluation/backlog.json").read_text()))
    output = ROOT / "docs/backlog-work-packages.md"
    if args.check:
        if not output.is_file() or output.read_text() != result:
            raise SystemExit("Work-package documentation differs from the register")
        print("Work-package documentation matches the register.")
    else:
        output.write_text(result)


if __name__ == "__main__":
    main()
