#!/usr/bin/env python3
"""Validate both repository contracts offline against unchanged canonical schemas."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "profiles/bundle-wiki/v1/repository-contract.schema.json"
SCHEMA_SHA256 = "783f81c5c785b3a13cfdedce3a89dd1e5c3f64a007cfe370bc82e37e2caa5ba8"
SCHEMA_ID = "https://chris-page-gov.github.io/okf-explorer/profile/bundle-wiki/v1/repository-contract.schema.json"
PUBLICATION_SCHEMA = ROOT / "profiles/publication-method/v1/repository-publication.schema.json"
PUBLICATION_SHA256 = "04c5d229a2900616d7a194d256ae1edb162d2c18beec7e2354723ce711b4eec3"
SOURCE_FAMILY_SCHEMA = ROOT / "profiles/publication-method/v1/source-family.schema.json"
SOURCE_FAMILY_SHA256 = "8c4734f554920fd34157ce90172a53ced492198d3761e7a62ebebf51036b3f6b"
PROFILE_URL = "https://chris-page-gov.github.io/okf-explorer/profile/publication-method/v1/"


def validator(schema_path: Path = SCHEMA) -> Draft202012Validator:
    raw = schema_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SCHEMA_SHA256:
        raise ValueError("Canonical semantic contract schema bytes differ from the pinned profile")
    schema = json.loads(raw)
    if schema.get("$id") != SCHEMA_ID:
        raise ValueError("Canonical semantic contract schema identity differs")
    Draft202012Validator.check_schema(schema)
    # The pinned schema uses local fragment references only; no network retrieval.
    return Draft202012Validator(schema, format_checker=FormatChecker())


def publication_validator(publication_path: Path = PUBLICATION_SCHEMA,
                          family_path: Path = SOURCE_FAMILY_SCHEMA) -> Draft202012Validator:
    resources = []
    for path, digest, name in [(publication_path, PUBLICATION_SHA256, "repository-publication.schema.json"),
                               (family_path, SOURCE_FAMILY_SHA256, "source-family.schema.json")]:
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(f"Canonical publication schema bytes differ: {name}")
        schema = json.loads(raw)
        if schema.get("$id") != PROFILE_URL + name:
            raise ValueError(f"Canonical publication schema identity differs: {name}")
        Draft202012Validator.check_schema(schema)
        resources.append((schema["$id"], Resource.from_contents(schema)))
    # Registry has no retrieval callback: the canonical absolute reference resolves
    # only to the hash-checked local source-family schema, never to the network.
    registry = Registry().with_resources(resources)
    return Draft202012Validator(resources[0][1].contents, registry=registry, format_checker=FormatChecker())


def check_publication_references(contract: dict) -> None:
    planes = {item["id"]: item for item in contract["planes"]}
    commands = {item["id"]: item for item in contract["tooling"]["commands"]}
    families = {item["id"]: item for item in contract["source_families"]}
    if (len(planes) != len(contract["planes"]) or len(commands) != len(contract["tooling"]["commands"])
            or len(families) != len(contract["source_families"])):
        raise ValueError("Publication identifiers must be unique within their collections")

    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                table = commands if key in {"command_ids", "build_command_ids", "check_command_ids"} else (
                    planes if key in {"depends_on", "invalidates", "planes"} else None)
                if table is not None and isinstance(item, list) and all(isinstance(x, str) for x in item):
                    unknown = set(item) - set(table)
                    if unknown:
                        raise ValueError(f"Unknown publication {key}: {sorted(unknown)}")
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(contract)
    visiting, visited = set(), set()

    def visit(identifier):
        if identifier in visiting:
            raise ValueError("Publication plane dependency cycle")
        if identifier not in visited:
            visiting.add(identifier)
            for dependency in planes[identifier]["depends_on"]:
                visit(dependency)
            visiting.remove(identifier)
            visited.add(identifier)

    for identifier in planes:
        visit(identifier)


def check_paths(contract: dict, root: Path = ROOT) -> None:
    root = root.resolve()
    root_index = (root / contract["repository"]["root_index"]).resolve()
    if not root_index.is_relative_to(root):
        raise ValueError("Root index leaves the repository")
    if not re.search(r"(?m)^okf_version:\s*[\"']?0\.2[\"']?\s*$", root_index.read_text()[:4096]):
        raise ValueError("Root index must declare okf_version: 0.2")
    for output in contract["semantic_layer"]["outputs"]:
        paths = list(root.glob(output["path"]))
        if any(not path.resolve().is_relative_to(root) for path in paths):
            raise ValueError(f"Declared output leaves the repository: {output['path']}")
        if output.get("required", True) and not any(path.is_file() for path in paths):
            raise ValueError(f"Declared required output is absent: {output['path']}")


def check_delivery_description(contract: dict, description: dict) -> None:
    if description.get("schema") != "okf-dwp-delivery-description.v1" or description.get("semantic_contract") != "okf.semantic.json":
        raise ValueError("Delivery description must identify its separate local format and semantic contract")
    outputs = {item["path"] for item in contract["semantic_layer"]["outputs"]}
    for group in description["output_groups"]:
        if not group["canonical_output_paths"] or not set(group["canonical_output_paths"]).issubset(outputs):
            raise ValueError("Delivery description refers to an undeclared canonical output")


def main() -> None:
    contract = json.loads((ROOT / "okf.semantic.json").read_text())
    validator().validate(contract)
    check_paths(contract)
    check_delivery_description(contract, json.loads((ROOT / "okf.delivery.json").read_text()))
    publication = json.loads((ROOT / "okf.publication.json").read_text())
    publication_validator().validate(publication)
    check_publication_references(publication)
    print(json.dumps({"status": "passed", "schema": SCHEMA_ID, "schema_sha256": SCHEMA_SHA256,
                      "publication_schema_sha256": PUBLICATION_SHA256, "source_family_schema_sha256": SOURCE_FAMILY_SHA256,
                      "outputs": len(contract["semantic_layer"]["outputs"]), "network_used": False,
                      "scope": "Contract shape, declared output presence and descriptive metadata references; no legal or specialist assurance."}))


if __name__ == "__main__":
    main()
