#!/usr/bin/env python3
"""Run or verify the frozen, local LiteParse source pilot."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from liteparse_pilot import PilotError, check, file_digest, read_json, repo_path, run, validate_cases


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "domain-profile/liteparse-pilot/protocol.json"
CASES = ROOT / "domain-profile/liteparse-pilot/cases.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stage", type=int, choices=(1, 2), help="Run a frozen stage")
    mode.add_argument("--check", action="store_true", help="Verify retained artefacts without running extractors")
    parser.add_argument("--output", metavar="RELATIVE_DIRECTORY", help="New versioned output directory inside this repository")
    parser.add_argument("--stage1-dir", metavar="RELATIVE_DIRECTORY", help="Verified stage-one output, required for stage two")
    parser.add_argument("--cache-dir", metavar="RELATIVE_DIRECTORY", help="Optional bounded cache inside this repository")
    args = parser.parse_args()
    try:
        protocol, _ = read_json(PROTOCOL)
        cases_doc, _ = read_json(CASES)
        if protocol.get("schema") != "okf-dwp-liteparse-source-protocol.v1" or protocol.get("status") != "fixed-before-liteparse-outcomes":
            raise PilotError("Protocol is not fixed before outcomes")
        cases = validate_cases(ROOT, cases_doc)
        protocol_sha = file_digest(PROTOCOL)
        cases_sha = file_digest(CASES)
        runner_sha = file_digest(Path(__file__)) + ":" + file_digest(ROOT / "scripts/liteparse_pilot.py")
        if not args.output:
            parser.error("--output is required")
        pilot_root = repo_path(ROOT, "evaluation/liteparse-pilot")
        output = repo_path(ROOT, args.output)
        if not output.is_relative_to(pilot_root):
            raise PilotError("Output must be inside evaluation/liteparse-pilot")
        if args.check:
            result = check(output, ROOT, protocol_sha, cases_sha, cases, runner_sha)
            print(f"Verified stage {result['stage']} ({len(result['cases'])} cases); gate {'pass' if result['gate']['passed'] else 'fail'}")
            return 0
        if args.stage == 2 and not args.stage1_dir:
            parser.error("--stage1-dir is required for stage two")
        if args.stage == 1 and args.stage1_dir:
            parser.error("--stage1-dir applies only to stage two")
        lit = ROOT / "tools/liteparse-pilot/.venv/bin/lit"
        if not lit.is_file():
            raise PilotError("Pinned LiteParse executable is missing")
        pdftotext_name = shutil.which("pdftotext")
        if not pdftotext_name:
            raise PilotError("pdftotext is missing")
        if not re.fullmatch(rf"stage-{args.stage}-[a-z0-9][a-z0-9-]*", output.name):
            raise PilotError("Output directory must have a versioned stage-N-name basename")
        cache_dir = repo_path(ROOT, args.cache_dir) if args.cache_dir else None
        stage1_dir = repo_path(ROOT, args.stage1_dir) if args.stage1_dir else None
        for label, directory in (("Cache", cache_dir), ("Stage-one", stage1_dir)):
            if directory is not None and not directory.is_relative_to(pilot_root):
                raise PilotError(f"{label} directory must be inside evaluation/liteparse-pilot")
            if directory is not None and (directory == output or directory.is_relative_to(output) or output.is_relative_to(directory)):
                raise PilotError(f"{label} directory overlaps output")
        if cache_dir is not None and stage1_dir is not None and (cache_dir == stage1_dir or cache_dir.is_relative_to(stage1_dir) or stage1_dir.is_relative_to(cache_dir)):
            raise PilotError("Cache and stage-one directories overlap")
        result = run(ROOT, output, args.stage, protocol_sha, cases_sha, cases, lit, Path(pdftotext_name), runner_sha, cache_dir, stage1_dir)
        print(f"Stage {args.stage}: gate {'pass' if result['gate']['passed'] else 'fail'}; report: {output.relative_to(ROOT)}/REPORT.md")
        return 0
    except PilotError as exc:
        print(f"LiteParse pilot: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
