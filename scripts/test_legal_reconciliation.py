#!/usr/bin/env python3
"""Offline provenance, parsing and fail-closed legal-reference controls."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from acquire_legal_reconciliation import legislative_metadata, decision_metadata, pretty, public_effect_projection
from build_legal_reconciliation import ROOT, SOURCE, SEEDS, build, check_snapshot, citation_lines, references, sha

XML = b'''<Legislation xmlns="http://www.legislation.gov.uk/namespaces/legislation"
 xmlns:m="http://www.legislation.gov.uk/namespaces/metadata" xmlns:dc="http://purl.org/dc/elements/1.1/"
 IdURI="http://www.legislation.gov.uk/id/uksi/2002/1792" RestrictStartDate="2026-07-16" RestrictExtent="E+W+S">
 <m:Metadata><dc:title>Fixture Regulations</dc:title><m:SecondaryMetadata><m:Made Date="2002-07-11"/></m:SecondaryMetadata></m:Metadata>
 <Body><P1 IdURI="http://www.legislation.gov.uk/id/uksi/2002/1792/regulation/3" DocumentURI="http://www.legislation.gov.uk/uksi/2002/1792/regulation/3/2026-09-20"><Text>Not persisted statutory body</Text></P1></Body></Legislation>'''


class LegalReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = build()
        cls.seeds = json.loads((ROOT / SEEDS).read_text())
        _, cls.observations = check_snapshot(ROOT)

    def test_literal_offsets_preserve_unicode_and_adjacent_lines(self):
        text = "Narrative £é\n              1 SPC Regs, reg 3;\n                2 reg 5(2)\n\nEnd\n"
        rows = citation_lines(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(text[rows[0]["start"]:rows[0]["end"]], rows[0]["literal"])
        self.assertEqual(sha(rows[0]["literal"].encode()), rows[0]["literal_sha256"])

    def test_narrative_and_paragraph_numbers_do_not_become_citation_lines(self):
        self.assertEqual(citation_lines("The Act governs this example\n           77001 The Act provides\n"), [])

    def test_verified_provision_and_finer_locator_remain_distinct(self):
        row = references("1 SPC Regs, reg 3(1)(a)", self.seeds["works"], self.observations)[0]
        self.assertEqual(row["provisions"][0]["verification_status"], "identifier-verified")
        self.assertIn("not-resolved", row["provisions"][0]["finer_locator_status"])
        self.assertEqual(row["applicability_review"], "unreviewed")

    def test_nonexistent_or_unacquired_provision_fails_closed(self):
        row = references("1 SPC Regs, reg 999", self.seeds["works"], self.observations)[0]
        self.assertEqual(row["provisions"][0]["verification_status"], "not-acquired")
        self.assertIsNone(row["provisions"][0]["observation_path"])

    def test_unknown_abbreviations_not_guessed(self):
        self.assertEqual(references("1 Unknown Regs, reg 3", self.seeds["works"], self.observations), [])

    def test_unknown_instrument_ends_inherited_work_scope(self):
        rows = references("SPC Regs, reg 3; Unknown Regulations, reg 15", self.seeds["works"], self.observations)
        self.assertEqual([p["target"] for p in rows[0]["provisions"]], ["uksi/2002/1792/regulation/3"])

    def test_actual_child_benefit_footnote_does_not_become_dla_citation(self):
        rows = references("SS (DLA) Regs, reg 2(2)(e); 3 CHB (R & PA) Regs, reg 2(2)(c)(iii)", self.seeds["works"], self.observations)
        self.assertEqual(len(rows[0]["provisions"]), 1)

    def test_bare_following_locator_can_retain_known_work(self):
        rows = references("SPC Regs, reg 3; 2 reg 5(2)", self.seeds["works"], self.observations)
        self.assertEqual([p["target"] for p in rows[0]["provisions"]], ["uksi/2002/1792/regulation/3", "uksi/2002/1792/regulation/5"])

    def test_long_alias_does_not_produce_duplicate_work(self):
        rows = references("SS (II) (REA & Trans) Regs 87, reg 5", self.seeds["works"], self.observations)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["literal_alias"], "SS (II) (REA & Trans) Regs 87")

    def test_version_restriction_is_not_invented_provision_commencement(self):
        meta = legislative_metadata(XML, "uksi/2002/1792/regulation/3")
        self.assertTrue(meta["target_identifier_observed"])
        self.assertNotIn("RestrictStartDate", meta["target_attributes"])
        self.assertEqual(meta["work_attributes"]["RestrictStartDate"], "2026-07-16")
        self.assertIn("not-reconciled", meta["commencement_assessment"])
        self.assertNotIn("Not persisted statutory body", json.dumps(meta))

    def test_absent_target_identifier_is_not_filled_from_request(self):
        meta = legislative_metadata(XML, "uksi/2002/1792/regulation/999")
        self.assertFalse(meta["target_identifier_observed"])
        self.assertIsNone(meta["target_attributes"])

    def test_xml_entities_rejected(self):
        with self.assertRaisesRegex(ValueError, "entities"):
            legislative_metadata(b'<!DOCTYPE test [<!ENTITY x "bad">]>' + XML, "uksi/2002/1792/regulation/3")

    def test_decision_parser_discards_judgment_and_hidden_indexed_body(self):
        raw = {"title": "Case [2026] UKUT 1 (AAC)", "details": {"body": "private fixture",
               "metadata": {"hidden_indexable_content": "private fixture", "tribunal_decision_decision_date": "2026-01-03"}}}
        meta = decision_metadata(json.dumps(raw).encode())
        self.assertNotIn("private fixture", json.dumps(meta))
        self.assertEqual(meta["decision_date"], "2026-01-03")
        self.assertIn("not-applicability", meta["applicability_review"])

    def test_all_source_pages_and_duplicate_occurrences_retained(self):
        census = json.loads(self.outputs["evaluation/legal-reconciliation/citations.json"])
        self.assertEqual(len(census["pages"]), 42)
        ids = {i for page in census["pages"] for i in page["case_ids"]}
        self.assertEqual(len(ids), 40)
        for case in ("staff-026", "staff-033"):
            self.assertIn(case, ids)
        self.assertTrue(any(not p["citations"] for p in census["pages"]))

    def test_actual_queries_declare_bound_and_truncation(self):
        discovery = json.loads(self.outputs["evaluation/legal-reconciliation/tribunal-discovery.json"])
        self.assertEqual(len(discovery["queries"]), 6)
        self.assertEqual(len(discovery["decisions"]), 18)
        for query in discovery["queries"]:
            self.assertEqual(query["requested_count"], 3)
            self.assertEqual(query["truncated"], query["total_matching_results"] > query["returned_count"])
        self.assertTrue(all(d["decision_date"] for d in discovery["decisions"]))

    def test_assertions_are_only_evidenced_navigation(self):
        data = json.loads(self.outputs["evaluation/legal-reconciliation/assertions.json"])
        self.assertGreater(len(data["assertions"]), 0)
        for row in data["assertions"]:
            self.assertEqual(row["predicate"], "http://purl.org/dc/terms/references")
            self.assertEqual(row["review_status"], "unreviewed")
            self.assertEqual(row["scope"], "citation-navigation-only")
            self.assertEqual(sha(row["evidence"]["literal"].encode()), row["evidence"]["literal_sha256"])

    def test_metadata_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / SOURCE, root / SOURCE)
            (root / SEEDS).parent.mkdir(parents=True)
            shutil.copyfile(ROOT / SEEDS, root / SEEDS)
            target = next((root / SOURCE / "legislation").glob("*.json"))
            target.write_text(target.read_text() + " ")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                check_snapshot(root)

    def test_wrong_official_identifier_rejected_even_when_file_hash_is_rebound(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / SOURCE, root / SOURCE)
            (root / SEEDS).parent.mkdir(parents=True)
            shutil.copyfile(ROOT / SEEDS, root / SEEDS)
            manifest_path = root / SOURCE / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            binding = next(x for x in manifest["files"] if x["path"].startswith("legislation/"))
            path = root / SOURCE / binding["path"]
            observation = json.loads(path.read_text())
            observation["metadata"]["target_attributes"]["IdURI"] = "http://www.legislation.gov.uk/id/uksi/2002/1792/regulation/999"
            raw = pretty(observation)
            path.write_bytes(raw)
            binding.update({"sha256": sha(raw), "bytes": len(raw)})
            manifest_path.write_bytes(pretty(manifest))
            with self.assertRaisesRegex(ValueError, "identity does not match"):
                check_snapshot(root)

    def test_missing_request_is_not_silently_excluded_from_census(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / SOURCE, root / SOURCE)
            (root / SEEDS).parent.mkdir(parents=True)
            shutil.copyfile(ROOT / SEEDS, root / SEEDS)
            path = root / SOURCE / "manifest.json"
            manifest = json.loads(path.read_text())
            index = next(i for i, x in enumerate(manifest["files"]) if x["path"].startswith("legislation/"))
            manifest["files"].pop(index)
            path.write_bytes(pretty(manifest))
            with self.assertRaisesRegex(ValueError, "request census"):
                check_snapshot(root)

    def test_legal_acceptance_never_fabricated(self):
        coverage = json.loads(self.outputs["evaluation/legal-reconciliation/coverage.json"])
        self.assertEqual(coverage["accepted_legal_propositions"], 0)
        self.assertEqual(coverage["specialist_acceptance"], "pending")
        self.assertEqual(coverage["statutory_or_judgment_bodies_acquired"], 0)

    def test_public_effect_projection_omits_literal_opaque_identifiers(self):
        source={"EffectId":"fixture-opaque-identifier","URI":"https://example.invalid/effect/fixture", "Type":"repealed", "Row":"3"}
        projected=public_effect_projection(source,2)
        self.assertNotIn("EffectId",projected)
        self.assertNotIn("URI",projected)
        self.assertEqual(projected["effect_identifier_sha256"],sha(source["EffectId"].encode()))
        self.assertEqual(projected["source_xml_effect_ordinal"],2)
        self.assertEqual(projected["Type"],source["Type"])
        self.assertEqual(projected["Row"],source["Row"])

    def test_all_projected_effect_ids_have_official_xml_origin_observations(self):
        proof=json.loads((ROOT/SOURCE/"effect-identifier-verification.json").read_text())
        expected={e["effect_identifier_sha256"] for row in self.observations.values() for e in row.get("metadata",{}).get("effect_metadata",[])}
        observed={e["effect_identity_sha256"] for row in proof["observations"] for e in row.get("observations",[])}
        self.assertEqual(len(expected),179)
        self.assertLessEqual(expected,observed)
        self.assertTrue(proof["all_expected_identifiers_observed"])
        self.assertLessEqual(proof["actual_requests"],proof["maximum_requests"])
        for row in proof["observations"]:
            self.assertTrue(row["receipt"]["requested_url"].startswith("https://www.legislation.gov.uk/"))
            self.assertEqual(row["receipt"]["http_status"],200)
            self.assertTrue(all(e["element"].startswith("{http://www.legislation.gov.uk/namespaces/metadata}") for e in row.get("observations",[])))

    def test_projection_ledger_binds_new_public_bytes_and_preserves_original_hashes(self):
        ledger=json.loads((ROOT/SOURCE/"publication-projection.json").read_text())
        self.assertEqual(len(ledger["changed_files"]),21)
        for item in ledger["changed_files"]:
            raw=(ROOT/SOURCE/item["path"]).read_bytes()
            self.assertEqual(sha(raw),item["projected_sha256"])
            self.assertNotEqual(item["previous_sha256"],item["projected_sha256"])
            value=json.loads(raw)
            self.assertEqual(value["receipt"]["response_sha256"],item["original_xml_response_sha256"])
            self.assertTrue(all("EffectId" not in e and "URI" not in e for e in value["metadata"]["effect_metadata"]))

    def test_projection_proof_cannot_be_removed_from_manifest_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            shutil.copytree(ROOT/SOURCE,root/SOURCE)
            (root/SEEDS).parent.mkdir(parents=True)
            shutil.copyfile(ROOT/SEEDS,root/SEEDS)
            path=root/SOURCE/"manifest.json"
            manifest=json.loads(path.read_text())
            manifest["files"]=[r for r in manifest["files"] if r["path"]!="effect-identifier-verification.json"]
            path.write_bytes(pretty(manifest))
            with self.assertRaisesRegex(ValueError,"not manifest-bound"):
                check_snapshot(root)


if __name__ == "__main__":
    unittest.main()
