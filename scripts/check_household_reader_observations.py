#!/usr/bin/env python3
"""Verify retained local browser artefacts offline; never relabel them as public."""
import hashlib
import json
import os
import re
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "validation/household-reader"
MAX_MANIFEST_BYTES = 128 * 1024
MAX_MEMBER_BYTES = 10 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_directory(directory):
    directory = directory.absolute()
    for part in [*reversed(directory.parents), directory]:
        require(stat.S_ISDIR(part.lstat().st_mode), "Observation directory and parents must not be symlinks")
    return directory


def bounded_read(path, limit=MAX_MEMBER_BYTES):
    checked_directory(path.parent)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), "Observation must be a regular file, never a symlink")
    require(before.st_size <= limit, "Observation exceeds byte limit")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        require(stat.S_ISREG(opened.st_mode) and opened.st_size <= limit, "Opened observation exceeds bound")
        raw = stream.read(limit + 1)
    require(len(raw) <= limit and len(raw) == before.st_size == opened.st_size,
            "Observation changed or exceeded byte limit")
    return raw


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_files(directory, manifest):
    directory = checked_directory(directory)
    require(isinstance(manifest["files"], list) and 0 < len(manifest["files"]) <= 256,
            "Observation inventory exceeds file bound")
    require(all(type(row["bytes"]) is int and 0 <= row["bytes"] <= MAX_MEMBER_BYTES
                and re.fullmatch(r"[a-f0-9]{64}", row["sha256"]) for row in manifest["files"]),
            "Invalid bounded observation metadata")
    require(sum(row["bytes"] for row in manifest["files"]) <= 32 * 1024 * 1024,
            "Observation inventory exceeds total byte bound")
    expected = set()
    for row in manifest["files"]:
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != row["path"]:
            raise ValueError("Unsafe observation path")
        target = directory / relative
        if row["path"] in expected:
            raise ValueError("Repeated observation path")
        expected.add(row["path"])
        raw = bounded_read(target)
        if len(raw) != row["bytes"] or digest(raw) != row["sha256"]:
            raise ValueError("Observation artefact bytes differ: " + row["path"])
    paths = list(directory.rglob("*"))
    require(all(not p.is_symlink() for p in paths), "Symlinks are forbidden in observations")
    actual = {p.relative_to(directory).as_posix() for p in paths
              if p.is_file() and p.name not in {"artifact-manifest.json", "README.md", ".DS_Store"}}
    if actual != expected:
        raise ValueError("Observation inventory differs")


def validate(directory=DIRECTORY):
    directory = checked_directory(directory)
    manifest = json.loads(bounded_read(directory / "artifact-manifest.json", MAX_MANIFEST_BYTES))
    verify_files(directory, manifest)
    admitted = {row["path"] for row in manifest["files"]}
    observations = []
    for relative in manifest["passed_observations"]:
        assert relative in admitted
        path = directory / relative
        row = json.loads(bounded_read(path))
        assert row["status"] == "passed"
        assert row["environment"] == "local-browser-candidate"
        assert row["harness_sha256"] == digest(bounded_read(path.parent / "executed-harness.mjs"))
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
            context = json.loads(bounded_read(path.parent / filename))
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
        failed = json.loads(bounded_read(path))
        assert failed["status"] == "failed"
        assert failed["harness_sha256"] == digest(bounded_read(path.parent / "executed-harness.mjs"))
    return {"status": "passed", "files": len(manifest["files"]), "browser_observations": len(observations),
            "retained_failed_attempts": len(manifest["failed_attempts"]), "scope": "offline integrity of local observations; no new browser execution"}


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2))
