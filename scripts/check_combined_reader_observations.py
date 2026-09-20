#!/usr/bin/env python3
"""Verify retained combined Reader observations; no fresh browser claim."""
import json
from pathlib import Path

from build_bundle import ROOT, digest
from build_context_discovery import require


def check(root=ROOT):
    browser = root / "validation/combined-reader/browser"
    history = browser.parent / "history"
    archived = 0
    for manifest_path in history.glob("*/archive.json"):
        archive = json.loads(manifest_path.read_bytes())
        require(archive["status"] == "superseded-local-observation", "Historical observation scope changed")
        for item in archive["files"]:
            path = (manifest_path.parent / item["path"]).resolve()
            require(path.is_relative_to(manifest_path.parent.resolve()), "Historical artefact path escapes archive")
            raw = path.read_bytes()
            require(len(raw) == item["bytes"] and digest(raw) == item["sha256"], "Historical artefact changed: " + item["path"])
        require(digest((manifest_path.parent / "descriptor.json").read_bytes()) == archive["descriptor_sha256"], "Historical descriptor changed")
        archived += 1
    receipt = json.loads((browser / "artifacts.json").read_bytes())
    for item in receipt["files"]:
        path = (browser / item["path"]).resolve()
        require(path.is_relative_to(browser.resolve()), "Artefact path escapes observation directory")
        raw = path.read_bytes()
        require(len(raw) == item["bytes"] and digest(raw) == item["sha256"], "Browser artefact changed: " + item["path"])
    descriptor_raw = (root / "combined/okf-explorer.json").read_bytes()
    descriptor = json.loads(descriptor_raw)
    contexts = set()
    checked_files = set()
    for engine in ("chrome", "firefox", "webkit", "facets"):
        observation = json.loads((browser / engine / "observation.json").read_bytes())
        require(observation["status"] == "passed" and observation["environment"] == "local-browser-candidate", "Unexpected browser observation scope")
        require(observation["descriptor"]["sha256"] == digest(descriptor_raw) and observation["descriptor"]["snapshot"] == descriptor["snapshot"], "Stale browser descriptor")
        require(observation["console_errors"] == [], "Browser console errors recorded")
        files = observation.get("corpus_requests", observation.get("served_files"))
        require(isinstance(files, list) and files, "No observed corpus responses")
        for row in files:
            path = (root / "combined" / row["path"]).resolve()
            require(path.is_relative_to((root / "combined").resolve()), "Corpus path escapes candidate")
            raw = path.read_bytes()
            require(len(raw) == row["bytes"] and digest(raw) == row["sha256"], "Observed corpus response changed: " + row["path"])
            checked_files.add(row["path"])
        if engine != "facets":
            accessibility = observation["accessibility"]
            require(accessibility["desktop_ask_violations"] == [] and accessibility["mobile_ask_and_panel_violations"] == [], "Recorded accessibility violation")
            require(accessibility["mobile_viewport"] == {"width": 390, "height": 844}, "Unexpected narrow viewport")
            require(accessibility["keyboard"]["json_summary_focus_verified"] and accessibility["keyboard"]["same_context_as_desktop"], "Keyboard journey did not retain context and focus")
            require(accessibility["page_horizontal_overflow"] is False, "Narrow viewport overflows")
            context = json.loads((browser / engine / "context.json").read_bytes())
            require(context["context_id"] == observation["ask"]["context_id"], "Recorded context identity mismatch")
            require(context["ai_answer"] is None and context["evidence_status"] == "insufficient", "Staff question boundary changed")
            contexts.add(context["context_id"])
    require(len(contexts) == 1, "Engines produced different evidence contexts")
    return {"status": "verified-retained-observations", "engines": 3, "facet_groups": 5, "corpus_files": len(checked_files), "superseded_archives": archived, "snapshot": descriptor["snapshot"]}


if __name__ == "__main__":
    print(json.dumps(check()))
