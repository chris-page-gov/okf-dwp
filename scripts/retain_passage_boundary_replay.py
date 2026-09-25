#!/usr/bin/env python3
"""Retain exact offline candidate workbench inputs for independent replay checks."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/passage-boundary-candidate/replay-projection"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    candidate = args.candidate_root.resolve()
    registry = json.loads((ROOT / "evaluation/staff-questions/cases.json").read_bytes())
    require(len(registry["cases"]) == 40, 'Replay evidence invariant failed: len(registry["cases"]) == 40')
    paths = ["evaluation/staff-questions/cases.json",
             "structured-units/manifest.json",
             "structured-context/evidence-connect-manifest.json",
             "evaluation/evidence-workbench/manifest.json",
             "evaluation/evidence-workbench/assessment.json",
             "scripts/manual_structure.py", "scripts/manual_navigation_regions.py",
             "scripts/build_structured_units.py"]
    paths.extend(f"evaluation/evidence-workbench/packages/{case['id']}.json" for case in registry["cases"])
    outputs = {}
    bindings = []
    for path in paths:
        raw = (candidate / path).read_bytes()
        retained = path + ".gz" if path.endswith("/assessment.json") or "/packages/" in path else path
        outputs[retained] = gzip.compress(raw, mtime=0) if retained.endswith(".gz") else raw
        bindings.append({"path": path, "sha256": sha(raw), "bytes": len(raw),
                         "retained_path": retained, "retained_sha256": sha(outputs[retained])})
    require((candidate / "scripts/manual_structure.py").read_bytes() == (ROOT / "scripts/passage_boundary_parser.py").read_bytes(), 'Replay evidence invariant failed: (candidate / "scripts/manual_structure.py").read_bytes() == (ROOT / "scripts/passage_bound')
    require((candidate / "scripts/manual_navigation_regions.py").read_bytes() == (ROOT / "scripts/manual_navigation_regions.py").read_bytes(), 'Replay evidence invariant failed: (candidate / "scripts/manual_navigation_regions.py").read_bytes() == (ROOT / "scripts/manu')
    receipt = {"schema": "okf-dwp-passage-boundary-replay-retention.v1",
               "status": "offline-candidate-projection-retained",
               "cases": len(registry["cases"]), "files": bindings,
               "scope": "Exact generated JSON bytes and producer substitutions; frozen PDFs and source remain in the repository."}
    outputs["receipt.json"] = (json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if args.check:
        existing = {p.relative_to(OUT).as_posix(): p.read_bytes() for p in OUT.rglob("*") if p.is_file()}
        require(outputs == existing, "Retained replay projection differs")
    else:
        for path, raw in outputs.items():
            target = OUT / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    print(json.dumps({"status": "verified" if args.check else "built", "cases": len(registry["cases"]),
                      "files": len(bindings), "receipt_sha256": sha(outputs["receipt.json"])}))


if __name__ == "__main__":
    main()
