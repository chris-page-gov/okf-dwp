"""Compile authored learning resources into the combined Reader only.

Teaching references are navigation, not assertions of legal applicability.
"""
import json
import re
from build_bundle import BASE, REPO, digest, load_yaml
from build_context_discovery import require

SOURCE = "domain-profile/learning/programme.yamlld"
ROUTE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._~-]*/[A-Za-z0-9][A-Za-z0-9._~/-]*$")


def add_learning(inputs, records, full_text, when):
    raw = inputs.read(SOURCE)
    inputs.read("scripts/build_learning_paths.py")
    doc = load_yaml(inputs.path(SOURCE))
    cases_raw = inputs.read("evaluation/staff-questions/cases.json")
    require(digest(cases_raw) == doc["question_registry_sha256"], "Learning question registry changed: review coverage")
    cases = json.loads(cases_raw)
    cases = cases["cases"] if isinstance(cases, dict) else cases
    known_questions = {row["id"] for row in cases}
    paths = doc["paths"]
    require(0 < len(paths) <= 12, "Learning path limit")
    ids = {p["id"] for p in paths}
    require(len(ids) == len(paths), "Duplicate learning path")
    available = {r["route"] for r in records}
    lesson_routes = set()
    questions = set()
    projected = []
    def bounded(value, maximum):
        require(isinstance(value, str) and 0 < len(value.strip()) <= maximum, "Learning text exceeds Reader contract")
        return value
    def visit(key, seen):
        require(key in ids and key not in seen, "Unknown or cyclic learning prerequisite")
        for dependency in next(p for p in paths if p["id"] == key)["prerequisites"]:
            visit(dependency, seen | {key})
    for path in paths:
        visit(path["id"], set())
        require(0 < len(path["steps"]) <= 24, "Learning step limit")
        require(set(path["persona_routes"]) <= available, "Missing learning persona")
        steps = []
        for step in path["steps"]:
            route = step["route"]
            require(ROUTE.fullmatch(route) and ".." not in route and route not in available | lesson_routes, "Invalid or duplicate lesson route")
            require(step["@id"] == BASE + "id/" + route, "Lesson identity mismatch")
            lesson_routes.add(route)
            require(set(step["evidence_routes"]) <= available, "Missing lesson evidence route")
            require(set(step["question_ids"]) <= known_questions, "Unknown lesson question")
            questions.update(step["question_ids"])
            title = bounded(step["title"], 240)
            outcome = bounded(step["outcome"], 800)
            practice = bounded(step["practice"], 1200)
            body = (f"# {title}\n\n{doc['authority']}\n\n## Learning outcome\n\n{outcome}\n\n## Practice artefact\n\n{practice}"
                + "\n\n## Evidence record locators\n\n" + "\n".join(f"- `{r}`" for r in step["evidence_routes"])
                + "\n\nThese locators are teaching references, not proof of complete evidence or legal applicability. Inspect governing headings, exact source spans, qualifications and unresolved dependencies."
                + "\n\n## Path assessment\n\n" + path["assessment"]
                + "\n\nUse fictional examples. A justified cannot-determine result can meet the objective. Step ticks do not award competence.")
            record = {"id":step["@id"],"name":route,"route":route,"title":title,"type":"Learning activity","record_type":"Learning activity",
                "notes":outcome,"narrative":{"title":title,"body":body},"publisher":"independent-project","publisher_title":"Independent OKF-DWP research project",
                "resource_ids":[],"resource_count":0,"formats":[],"tags":["Learning activity"],"topics":["Evidence literacy"],"source_family":"Project-authored",
                "source_role":"Project-authored learning activity","source_adapter":"authored-learning-yaml-ld","source_tier":"editorial-unreviewed","timestamp":"","metadata_created":doc["created_at"],
                "url":REPO+"/blob/main/"+SOURCE,"license_id":"mit","license_title":"MIT Licence","license_source_id":REPO+"/blob/main/LICENSE",
                "provenance":{"semantic_iri":step["@id"],"authority":doc["authority"],"source_sha256":digest(raw),"review_status":"unreviewed-specialist-review-required"},
                "extras":{"learning_path":path["id"],"question_ids":step["question_ids"],"teaching_references":step["evidence_routes"]}}
            records.append(record)
            full_text[route] = body
            steps.append({k:step[k] for k in ("route","title","outcome","practice","minutes","evidence_routes")})
        projected.append({"id":path["id"],"title":bounded(path["title"],240),"description":bounded(path["objective"],800),"assessment":bounded(path["assessment"],1200),"prerequisites":path["prerequisites"],"personas":path["persona_routes"],"steps":steps})
    require(questions == known_questions, "Learning programme does not cover all staff questions")
    return {"schema":"okf-large-learning-presentation.v2","title":doc["title"],"introduction":doc["introduction"],"programme":doc["programme"],"paths":projected}
