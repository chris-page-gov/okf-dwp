"""Prevent unsupported contract extensions and weakened canonical validation."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from jsonschema import ValidationError

from check_semantic_contract import (ROOT, SCHEMA, PUBLICATION_SCHEMA, SOURCE_FAMILY_SCHEMA,
    check_delivery_description, check_paths, check_publication_references, publication_validator, validator)


class SemanticContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((ROOT / "okf.semantic.json").read_text())
        self.validator = validator()

    def test_current_contract_and_delivery_references(self):
        self.validator.validate(self.contract)
        check_paths(self.contract)
        check_delivery_description(self.contract, json.loads((ROOT / "okf.delivery.json").read_text()))

    def test_custom_output_role_is_rejected(self):
        self.contract["semantic_layer"]["outputs"][0]["role"] = "hash-bound-full-dmg-and-adm-context-corpus"
        with self.assertRaises(ValidationError):
            self.validator.validate(self.contract)

    def test_unsupported_fields_are_rejected_at_their_original_locations(self):
        for section, field in [("semantic_layer", "deliveries"), ("reader", "additional_deliveries"),
                               ("relationship_contract", "pilot_vocabulary"), ("relationship_contract", "proposal_input")]:
            with self.subTest(field=field):
                value = deepcopy(self.contract)
                value[section][field] = []
                with self.assertRaises(ValidationError):
                    self.validator.validate(value)

    def test_unsafe_output_path_is_rejected(self):
        self.contract["semantic_layer"]["outputs"][0]["path"] = "../outside.json"
        with self.assertRaises(ValidationError):
            self.validator.validate(self.contract)

    def test_missing_required_output_is_rejected(self):
        self.contract["semantic_layer"]["outputs"][0]["path"] = "missing-contract-fixture.json"
        self.validator.validate(self.contract)
        with self.assertRaisesRegex(ValueError, "required output is absent"):
            check_paths(self.contract)

    def test_changed_canonical_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "schema.json"
            schema = json.loads(SCHEMA.read_text())
            schema["additionalProperties"] = True
            path.write_text(json.dumps(schema))
            with self.assertRaisesRegex(ValueError, "schema bytes differ"):
                validator(path)

    def test_delivery_description_cannot_reference_an_absent_output(self):
        description = json.loads((ROOT / "okf.delivery.json").read_text())
        description["output_groups"][0]["canonical_output_paths"] = ["undeclared.json"]
        with self.assertRaisesRegex(ValueError, "undeclared canonical output"):
            check_delivery_description(self.contract, description)


class PublicationContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((ROOT / "okf.publication.json").read_text())
        self.validator = publication_validator()

    def test_current_contract_and_references(self):
        self.validator.validate(self.contract)
        check_publication_references(self.contract)

    def test_custom_plane_and_source_classifications_are_rejected(self):
        for field in ["plane", "source"]:
            with self.subTest(field=field):
                value = deepcopy(self.contract)
                if field == "plane":
                    value["planes"][0]["id"] = "context-discovery"
                else:
                    value["source_families"][0]["kind"] = "public-document-snapshot"
                with self.assertRaises(ValidationError):
                    self.validator.validate(value)

    def test_required_browser_verification_needs_a_command(self):
        self.contract["verification"]["command_ids"] = []
        with self.assertRaises(ValidationError):
            self.validator.validate(self.contract)

    def test_unknown_command_is_rejected(self):
        self.contract["verification"]["command_ids"] = ["undeclared-command"]
        self.validator.validate(self.contract)
        with self.assertRaisesRegex(ValueError, "Unknown publication command_ids"):
            check_publication_references(self.contract)

    def test_plane_cycle_is_rejected(self):
        self.contract["planes"][0]["depends_on"] = [self.contract["planes"][0]["id"]]
        with self.assertRaisesRegex(ValueError, "dependency cycle"):
            check_publication_references(self.contract)

    def test_both_publication_schemas_are_hash_pinned(self):
        with tempfile.TemporaryDirectory() as directory:
            for field, schema_path in [("publication", PUBLICATION_SCHEMA), ("source-family", SOURCE_FAMILY_SCHEMA)]:
                with self.subTest(schema=field):
                    changed = Path(directory) / schema_path.name
                    changed.write_bytes(schema_path.read_bytes() + b"\n")
                    with self.assertRaisesRegex(ValueError, "schema bytes differ"):
                        publication_validator(changed, SOURCE_FAMILY_SCHEMA) if field == "publication" else publication_validator(PUBLICATION_SCHEMA, changed)


if __name__ == "__main__":
    unittest.main()
