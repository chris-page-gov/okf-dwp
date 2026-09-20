#!/usr/bin/env python3
"""Verify retained local browser artefacts offline; never relabel them as public."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "validation/household-reader"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_files(directory, manifest):
    expected = set()
    for row in manifest["files"]:
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != row["path"]:
            raise ValueError("Unsafe observation path")
        target = directory / relative
        if target.is_symlink() or not target.is_file():
            raise ValueError("Observation must be an independent regular file")
        if row["path"] in expected:
            raise ValueError("Repeated observation path")
        expected.add(row["path"])
        raw = target.read_bytes()
        if len(raw) != row["bytes"] or digest(raw) != row["sha256"]:
            raise ValueError("Observation artefact bytes differ: " + row["path"])
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*")
              if p.is_file() and p.name not in {"artifact-manifest.json", "README.md", ".DS_Store"}}
    if actual != expected:
        raise ValueError("Observation inventory differs")


def validate(directory=DIRECTORY):
    manifest = json.loads((directory / "artifact-manifest.json").read_bytes())
    verify_files(directory, manifest)
    admitted = {row["path"] for row in manifest["files"]}
    observations = []
    for relative in manifest["passed_observations"]:
        assert relative in admitted
        path = directory / relative
        row = json.loads(path.read_bytes())
        assert row["status"] == "passed"
        assert row["environment"] == "local-browser-candidate"
        assert row["harness_sha256"] == digest((path.parent / "executed-harness.mjs").read_bytes())
        assert not row["console_errors"]
        checks = row["checks"]
        assert checks["facets_and_timeline"]["statutory_units"] == 20
        assert checks["facets_and_timeline"]["reader_graph_timeline_parity"]
        assert checks["facets_and_timeline"]["source_series"] == 0
        assert checks["facets_and_timeline"]["audit_series"] > 0
        assert len(checks["literal_bodies"]) == 20
        assert len({body["route"] for body in checks["literal_bodies"]}) == 20
        assert all(body["exact_visible_literal"] for body in checks["literal_bodies"])
        assert checks["statutory_graph"]["incoming_and_outgoing_visible"]
        assert not checks["accessibility"]["desktop_ask_violations"]
        assert not checks["accessibility"]["narrow_ask_and_panel_violations"]
        assert checks["accessibility"]["json_focus"] and checks["accessibility"]["same_context_id"]
        for filename, key in [("care-home-context.json", "care_home"), ("sda-context.json", "sda")]:
            context = json.loads((path.parent / filename).read_bytes())
            observed = checks[key]
            assert context["context_id"] == observed["context_id"]
            assert context["bundle"]["snapshot"] == observed["context_snapshot"]
            assert observed["reader_snapshot"] == row["descriptor"]["snapshot"]
            assert context["evidence_status"] == observed["evidence_status"] == "insufficient"
            assert context["ai_answer"] is None
            assert len(context["selected"]) == observed["selected_records"]
            assert len(context["relationships"]) == observed["relationships"]
            assert context["budget"] == observed["budget"]
            compact = json.dumps(context, ensure_ascii=False, separators=(",", ":")).encode()
            assert len(compact) == observed["compact_json_bytes"] <= context["budget"]["max_bytes"] <= 524288
            if key == "care_home":
                heading = observed["controlling_heading"]
                assert heading["selected"] and heading["visible"]
                record = next(item["record"] for item in context["selected"] if item["record"]["id"] == heading["record_id"])
                assert "Claimants who have no partner" in record["text"] and "78088" in record["text"]
            else:
                ambiguity = next(item for item in context["ambiguities"] if item["phrase"] == "SDA")
                assert len(ambiguity["candidates"]) == 2
                assert set(ambiguity["candidates"]).isdisjoint(item["id"] for item in context["resolved_concepts"])
                assert all(any(any(route["seed"] == candidate for route in item["paths"]) for item in context["selected"])
                           for candidate in ambiguity["candidates"])
                assert len(observed["alternative_labels"]) >= 2
        observations.append(row)
    assert {row["browser"] for row in observations} == {"chrome", "firefox", "webkit"}
    for key in ["care_home", "sda"]:
        assert len({row["checks"][key]["context_id"] for row in observations}) == 1
    assert len({row["app"]["manifest_sha256"] for row in observations}) == 1
    assert len({row["descriptor"]["sha256"] for row in observations}) == 1
    for relative in manifest["failed_attempts"]:
        assert relative in admitted
        path = directory / relative
        failed = json.loads(path.read_bytes())
        assert failed["status"] == "failed"
        assert failed["harness_sha256"] == digest((path.parent / "executed-harness.mjs").read_bytes())
    return {"status": "passed", "files": len(manifest["files"]), "browser_observations": len(observations),
            "retained_failed_attempts": len(manifest["failed_attempts"]), "scope": "offline integrity of local observations; no new browser execution"}


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2))
