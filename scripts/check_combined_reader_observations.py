#!/usr/bin/env python3
"""Verify retained combined Reader observations; no fresh browser claim."""
import json
import re
from pathlib import Path
from urllib.parse import urljoin

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
    public = browser.parent / "public"
    public_contexts, public_files, public_engines = set(), set(), []
    post_deployment_files = 0
    if (public / "artifacts.json").exists():
        manifest = json.loads((public / "artifacts.json").read_bytes())
        for item in manifest["files"]:
            path = (public / item["path"]).resolve()
            require(path.is_relative_to(public.resolve()), "Public artefact path escapes observation directory")
            raw = path.read_bytes()
            require(len(raw) == item["bytes"] and digest(raw) == item["sha256"], "Public artefact changed: " + item["path"])
        local_app = json.loads((browser / "chrome/observation.json").read_bytes())["app"]
        for engine in manifest["engines"]:
            require(engine in {"chrome", "firefox", "webkit"}, "Unknown public browser engine")
            observation = json.loads((public / engine / "observation.json").read_bytes())
            require(observation["status"] == "passed" and observation["environment"] == "published-browser-observation", "Unexpected public observation scope")
            require(observation["network_mode"] == "real-https-no-interception" and observation["public_response_integrity_errors"] == [], "Public response check failed")
            require(observation["descriptor"]["sha256"] == digest(descriptor_raw) and observation["descriptor"]["snapshot"] == descriptor["snapshot"], "Stale public descriptor")
            match = re.fullmatch(r"https://raw\.githubusercontent\.com/chris-page-gov/okf-dwp/([a-f0-9]{40})/combined/okf-explorer\.json", observation["bundle_url"])
            require(match is not None and match[1] == observation["content_commit"], "Public bundle is not an immutable commit")
            require(observation["app"] == local_app and observation["console_errors"] == [], "Public app identity or console differs")
            prefix = observation["bundle_url"].removesuffix("okf-explorer.json")
            for row in observation["corpus_requests"]:
                path = (root / "combined" / row["path"]).resolve()
                require(path.is_relative_to((root / "combined").resolve()), "Public corpus path escapes candidate")
                raw = path.read_bytes()
                require(len(raw) == row["bytes"] and digest(raw) == row["sha256"], "Published corpus bytes changed: " + row["path"])
                require(row["url"] == prefix + row["path"], "Published response URL differs")
                public_files.add(row["path"])
            context = json.loads((public / engine / "context.json").read_bytes())
            require(context["context_id"] == observation["ask"]["context_id"] and context["budget"] == observation["ask"]["budget"], "Public context or budget mismatch")
            require(context["ai_answer"] is None and context["evidence_status"] == "insufficient", "Public staff boundary changed")
            require(context["binding"]["index_url"] == prefix + "context/corpus/manifest.json", "Public context was assembled from another binding")
            require(context["binding"]["index_sha256"] == digest((root / "combined/context/corpus/manifest.json").read_bytes()), "Public context manifest hash differs")
            require(observation["accessibility"]["desktop_ask_violations"] == [] and observation["accessibility"]["mobile_ask_and_panel_violations"] == [], "Public targeted accessibility violation")
            require(observation["accessibility"]["keyboard"]["same_context_as_desktop"] and observation["accessibility"]["keyboard"]["json_summary_focus_verified"] and not observation["accessibility"]["page_horizontal_overflow"], "Public keyboard or narrow layout control failed")
            require(observation["phase_timings"][-1]["phase"] == "narrow_keyboard_ask_ready", "Public timings lack completed journey")
            public_contexts.add(context["context_id"])
            public_engines.append(engine)
        require(len(public_contexts) == 1, "Public engines produced different contexts")
        if manifest.get("post_service_merge_observation"):
            fingerprint = json.loads((public / "post-service-merge.json").read_bytes())
            require(fingerprint["schema"] == "okf-combined-reader-post-deployment-fingerprint.v1" and fingerprint["status"] == "identical-application-bytes", "Unexpected post-deployment scope")
            require(fingerprint["network_mode"] == "real-https-no-interception" and fingerprint["journeys_rerun"] is False and fingerprint["corpus_refetched"] is False, "Post-deployment fingerprint overclaims a new journey")
            app = fingerprint["app"]
            require(all(app[key] == local_app[key] for key in ("manifest_sha256", "tree_sha256", "verified_materials")), "Post-deployment app differs from retained journeys")
            raw = fingerprint["manifest_text"].encode("utf-8")
            require(len(raw) == app["manifest_bytes"] and digest(raw) == app["manifest_sha256"], "Post-deployment manifest bytes differ")
            published_manifest = json.loads(raw)
            require(published_manifest["schema"] == "okf-explorer-app-build-manifest.v1", "Unexpected application manifest")
            materials = [{key: row[key] for key in ("path", "bytes", "sha256")} for row in published_manifest["materials"]]
            paths = [row["path"] for row in materials]
            require(paths == sorted(set(paths)), "Post-deployment materials are not uniquely ordered")
            # The application producer preserves path/bytes/sha256 key order.
            tree_raw = (json.dumps(materials, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
            require(digest(tree_raw) == app["tree_sha256"] == published_manifest["tree_sha256"], "Post-deployment material tree differs")
            require(len(materials) == app["verified_materials"] == published_manifest["file_count"] == len(fingerprint["files"]), "Post-deployment file count differs")
            require(app["manifest_url"] == "https://chris-page-gov.github.io/okf-explorer/okf-explorer-build-manifest.json", "Post-deployment manifest URL differs")
            for expected, observed in zip(materials, fingerprint["files"], strict=True):
                require(all(observed[key] == expected[key] for key in expected), "Post-deployment response fingerprint differs")
                require(observed["url"] == urljoin(app["manifest_url"], expected["path"]) and observed["status"] == 200 and observed["matches_manifest"] is True, "Post-deployment response identity differs")
            require({row["path"] for row in fingerprint["prior_journeys"]} == {engine + "/observation.json" for engine in manifest["engines"]}, "Post-deployment receipt does not bind all prior engines")
            for previous in fingerprint["prior_journeys"]:
                raw = (public / previous["path"]).read_bytes()
                require(digest(raw) == previous["sha256"] and json.loads(raw)["observed_at"] == previous["observed_at"], "Prior journey was changed after fingerprint check")
            require(fingerprint["deployment"]["conclusion"] == "success" and fingerprint["deployment"]["status"] == "completed", "Post-deployment workflow was not complete")
            post_deployment_files = len(materials)
        if manifest.get("facet_observation"):
            facets = json.loads((public / "facets/observation.json").read_bytes())
            require(facets["status"] == "passed" and facets["environment"] == "public-browser-deployment", "Unexpected public facet observation scope")
            require(facets["app_build"] == local_app and facets["console_errors"] == [], "Public facet app or console differs")
            require(facets["descriptor"]["sha256"] == digest(descriptor_raw), "Public facet descriptor differs")
            require({row["key"] for row in facets["observations"]} == {"source_family", "benefit", "circumstance", "topic", "concept"}, "Missing public conceptual facet")
            require(all(row["targeted_accessibility_violations"] == [] for row in facets["observations"]), "Public facet accessibility violation")
            for row in facets["served_files"]:
                path = (root / "combined" / row["path"]).resolve()
                require(path.is_relative_to((root / "combined").resolve()), "Public facet corpus path escapes candidate")
                raw = path.read_bytes()
                require(len(raw) == row["bytes"] and digest(raw) == row["sha256"], "Public facet response changed")
                public_files.add(row["path"])
    return {"status": "verified-retained-observations", "engines": 3, "facet_groups": 5, "corpus_files": len(checked_files), "superseded_archives": archived,
            "public_engines": public_engines, "public_corpus_files": len(public_files), "post_deployment_application_files": post_deployment_files, "snapshot": descriptor["snapshot"]}


if __name__ == "__main__":
    print(json.dumps(check()))
