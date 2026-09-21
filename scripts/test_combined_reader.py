"""Real corpus controls for additive DMG/ADM Reader publication."""
from collections import Counter
from copy import deepcopy
import gzip
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from build_bundle import ROOT, BASE, digest, source_text_block
from build_combined_reader import LABELS, compile_combined, add_semantics
from build_full_dmg import bucket, tokens


@unittest.skipUnless(shutil.which("node"), "Node is required for browser-harness admission controls")
class CombinedBrowserOutputTests(unittest.TestCase):
    """Exercise admission before importing dependencies, without browser/network."""

    def run_harness(self, checkout, output, public=True):
        env = {key: value for key, value in os.environ.items() if not key.startswith("OKF_COMBINED_")}
        env.update(OKF_EXPLORER_CHECKOUT=str(checkout), OKF_COMBINED_OUTPUT=str(output))
        if public:
            env.update(
                OKF_COMBINED_BUNDLE_URL="https://raw.githubusercontent.com/chris-page-gov/okf-dwp/" + "a" * 40 + "/combined/okf-explorer.json",
                OKF_COMBINED_APP_URL="https://chris-page-gov.github.io/okf-explorer/explore/",
                OKF_COMBINED_APP_MANIFEST_SHA256="a" * 64,
            )
        return subprocess.run([shutil.which("node"), str(ROOT / "scripts/check_combined_reader_browser.mjs")],
                              env=env, text=True, capture_output=True, timeout=10, check=False)

    def test_public_rejects_existing_paths_before_import_and_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / "prior-pass"
            directory.mkdir()
            marker = directory / "observation.json"
            marker.write_bytes(b'{"original":"retained"}\n')
            existing_file = root / "existing-file"
            existing_file.write_bytes(b"retained file\n")
            link = root / "linked-pass"
            link.symlink_to(directory, target_is_directory=True)
            empty = root / "empty-directory"
            empty.mkdir()
            for output in (directory, existing_file, link, empty):
                with self.subTest(output=output.name):
                    result = self.run_harness(root / "missing-checkout", output)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Public observations require a fresh output directory", result.stderr)
                    self.assertNotIn("ERR_MODULE_NOT_FOUND", result.stderr)
                    self.assertEqual(marker.read_bytes(), b'{"original":"retained"}\n')
                    self.assertEqual(existing_file.read_bytes(), b"retained file\n")
                    self.assertEqual(list(directory.iterdir()), [marker])
                    self.assertEqual(list(empty.iterdir()), [])
                    self.assertTrue(link.is_symlink())

    def test_public_reserves_fresh_nested_directory_before_dependency_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "new-parent" / "new-run"
            result = self.run_harness(root / "missing-checkout", output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ERR_MODULE_NOT_FOUND", result.stderr)
            self.assertNotIn("Public observations require a fresh output directory", result.stderr)
            self.assertTrue(output.is_dir())
            self.assertEqual(list(output.iterdir()), [])

    def test_local_existing_directory_is_not_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            marker = root / "prior-local.json"
            marker.write_bytes(b"retained local data\n")
            result = self.run_harness(root / "missing-checkout", root, public=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ERR_MODULE_NOT_FOUND", result.stderr)
            self.assertNotIn("Public observations require a fresh output directory", result.stderr)
            self.assertEqual(marker.read_bytes(), b"retained local data\n")


class CombinedReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ROOT / "combined"
        cls.descriptor = cls.read("okf-explorer.json")
        cls.manifest = cls.read("data/manifest.json")
        cls.records = [row for path in cls.manifest["chunks"]["datasets"] for row in cls.read(path)]
        cls.by_route = {row["route"]: row for row in cls.records}
        cls.edges = [row for path in cls.manifest["chunks"]["relationships"] for row in cls.read(path)]
        cls.search = cls.read("data/search/manifest.json")

    @classmethod
    def read(cls, path):
        raw = (cls.root / path).read_bytes()
        return json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)

    def test_full_source_census_and_explicit_empty_pages(self):
        coverage = self.read("coverage.json")
        self.assertEqual(coverage["families"], {"dmg": 14743, "adm": 4347})
        self.assertEqual(coverage["source_documents"], 513)
        self.assertEqual(coverage["source_pages"], 19090)
        self.assertEqual(coverage["empty_extractions"], 893)
        self.assertEqual(sum(row["record_type"] == "Source PDF page" for row in self.records), 19090)

    def test_dmg_routes_and_existing_narratives_are_preserved(self):
        old = json.loads((ROOT / "full-dmg/context/navigation/runtime/manifest.json").read_bytes())
        for path in old["chunks"]["datasets"]:
            for row in json.loads(gzip.decompress((ROOT / "full-dmg" / path).read_bytes())):
                new = self.by_route[row["route"]]
                self.assertEqual(new["id"], row["id"])
                if new.get("context_semantics"):
                    self.assertTrue(new["narrative"]["body"].startswith(row["narrative"]["body"] + "\n\n## Current context definition — unreviewed"))
                else:
                    self.assertEqual(new["narrative"], row["narrative"])
                self.assertEqual(new["provenance"], row["provenance"])

    def test_every_adm_page_retains_source_and_exact_text(self):
        inventory = json.loads((ROOT / "source/adm-2026-09-19/inventory.json").read_bytes())
        for doc in inventory["documents"]:
            for page in json.loads((ROOT / doc["pages_path"]).read_bytes())["pages"]:
                route = f"page/adm/{doc['id']}/{page['page']:04d}"
                row = self.by_route[route]
                self.assertEqual(row["id"], BASE + "id/" + route)
                self.assertEqual(row["url"], page["url"])
                self.assertEqual(row["provenance"]["source_sha256"], doc["sha256"])
                self.assertEqual(row["provenance"]["page_text_sha256"], digest(page["text"].encode()))
                self.assertIn(source_text_block(page["text"]), row["narrative"]["body"])

    def test_facets_and_search_summaries_select_identical_records(self):
        for key in LABELS:
            postings = self.read(self.search["entrypoints"]["filter_postings"][key])["values"]
            expected = {}
            for ordinal, row in enumerate(self.records):
                values = row["topics"] if key == "topic" else row[key]
                for value in values if isinstance(values, list) else [values]:
                    expected.setdefault(value, []).append(ordinal)
            self.assertEqual(postings, expected)
        for path in self.search["entrypoints"]["result_docs"]:
            for row in self.read(path):
                record = self.records[row["ordinal"]]
                self.assertEqual(row["open"], record["route"])
                self.assertEqual(row["topics"], record["topics"])
                self.assertEqual(row["source_family"], record["source_family"])

    def test_every_relationship_keeps_both_navigation_directions(self):
        adjacency = self.read("data/adjacency/manifest.json")
        by_route = {}
        for path in adjacency["buckets"].values():
            by_route.update(self.read(path))
        for edge in self.edges:
            self.assertIn(edge, by_route[edge["source"]])
            self.assertIn(edge, by_route[edge["target"]])
            self.assertEqual(edge["source_iri"], self.by_route[edge["source"]]["id"])
            self.assertEqual(edge["target_iri"], self.by_route[edge["target"]]["id"])
        adm = [row for row in self.edges if row["source"].startswith("page/adm/")]
        self.assertEqual(len(adm), 4347)
        self.assertTrue(all(row["predicate"] == "http://purl.org/dc/terms/isPartOf" for row in adm))

    def test_qualification_support_edges_preserve_requirement_meaning_and_authority(self):
        catalogue = json.loads((ROOT / "evaluation/semantic-expansion/catalogue.json").read_bytes())
        required_ids = set(catalogue["qualification_assertion_ids"])
        edges = [row for row in self.edges if row["id"] in required_ids]
        self.assertEqual(len(edges), 29)
        self.assertEqual({row["id"] for row in edges}, required_ids)
        by_source = {}
        for row in edges:
            by_source.setdefault(row["source"], []).append(row)
        self.assertEqual({key: len(value) for key, value in by_source.items()}, {
            "staff-domain/household-separation": 7,
            "staff-domain/care-home": 1,
            "staff-domain/care-home-housing-costs": 5,
            "staff-domain/temporary-care-home": 2,
            "staff-domain/severe-disability-addition": 4,
            "staff-domain/no-partner-disability-addition": 10,
        })
        for row in edges:
            self.assertEqual(row["predicate"], "http://purl.org/dc/terms/requires")
            self.assertEqual(row["kind"], "authored context requirement")
            self.assertEqual(row["inverse_label"], "is required context for")
            self.assertTrue(row["label"].startswith("Required qualification context for "))
            self.assertEqual(row["assertion_status"], "model-derived")
            self.assertEqual(row["authority"]["class"], "model-assisted")
            self.assertEqual(row["review_status"], "unreviewed-specialist-review-required")
            self.assertTrue(row["evidence"])

    def test_all_routes_resolve_through_hash_bound_locator(self):
        locator = self.read("data/locator/manifest.json")
        cache = {key: self.read(value["path"]) for key, value in locator["buckets"].items()}
        for ordinal, row in enumerate(self.records):
            shard, offset = cache[bucket(row["route"])][row["route"]]
            self.assertEqual(shard * locator["chunk_size"] + offset, ordinal)

    def test_adm_capture_does_not_become_source_publication(self):
        for row in self.records:
            if row["source_family"] == "ADM" and row["publisher"] == "dwp":
                self.assertEqual(row["timestamp"], "")
                self.assertNotIn("published_at", row)
                self.assertEqual(row["provenance"]["date_roles"]["publication_date_status"], "not-established-from-document-evidence")
                self.assertIn("captured_at", row["provenance"]["date_roles"])

    def test_adm_full_text_search_reaches_beyond_snippets(self):
        inventory = json.loads((ROOT / "source/adm-2026-09-19/inventory.json").read_bytes())
        doc = next(row for row in inventory["documents"] if row["pages"] > 20)
        page = next(row for row in json.loads((ROOT / doc["pages_path"]).read_bytes())["pages"] if len(row["text"]) > 1200)
        route = f"page/adm/{doc['id']}/{page['page']:04d}"
        record = self.by_route[route]
        terms = set(tokens(page["text"][800:])) - set(tokens(record["notes"] + " " + record["title"]))
        self.assertTrue(terms)
        token = sorted(terms)[0]
        lexicon = self.read(self.search["entrypoints"]["lexicon"][token[:2]])
        posting = next(row for row in lexicon if row["token"] == token)
        ordinals = {row[0] for row in self.read(posting["postings"])["tokens"][token]}
        self.assertIn(next(i for i, row in enumerate(self.records) if row["route"] == route), ordinals)

    def test_statutory_bodies_keep_literal_text_source_links_and_date_roles(self):
        overlay = json.loads((ROOT / "domain-profile/legal-bodies/context-overlay.json").read_bytes())
        resources = {row["id"]: row for path in self.manifest["chunks"]["resources"] for row in self.read(path)}
        self.assertEqual(self.read("coverage.json")["selected_statutory_units"], 20)
        for original in overlay["records"]:
            row = self.by_route[original["route"]]
            source = original["provenance"][0]
            self.assertEqual(row["source_family"], "Legislation")
            self.assertEqual(row["timestamp"], "")
            self.assertNotIn("published_at", row)
            self.assertEqual(row["provenance"]["date_roles"]["requested_source_version"], "2026-09-20")
            self.assertEqual(row["provenance"]["authority"]["class"], "derived")
            self.assertEqual(row["provenance"]["review_status"], "unreviewed")
            self.assertEqual(row["provenance"]["literal_sha256"], digest(original["text"].encode()))
            self.assertIn(source_text_block(original["text"]), row["narrative"]["body"])
            self.assertIn(original["scope"], row["narrative"]["body"])
            self.assertEqual(row["url"], source["url"])
            self.assertEqual(resources[row["resource_ids"][0]]["source_access"]["url"], source["url"])

    def test_source_plane_binds_statutory_acquisitions_as_well_as_pdfs(self):
        from build_bundle import canonical
        identity = self.read("data/source-identity.json")
        self.assertEqual(len(identity["pdf_documents"]), 513)
        self.assertTrue(identity["statutory_retained_files"])
        self.assertEqual(digest(canonical(identity)), self.descriptor["plane_roots"]["source"])
        self.assertEqual(len(self.descriptor["source"]["statutory_inventories"]), 2)
        for binding in identity["statutory_retained_files"]:
            raw = (ROOT / binding["path"]).read_bytes()
            self.assertEqual(digest(raw), binding["sha256"])
            self.assertEqual(len(raw), binding["bytes"])
        changed = deepcopy(identity)
        changed["statutory_retained_files"][0]["sha256"] = "0" * 64
        self.assertNotEqual(digest(canonical(changed)), self.descriptor["plane_roots"]["source"])

    def test_context_exact_source_shards_preserved_and_snapshot_rebound(self):
        manifest = self.read("context/corpus/manifest.json")
        self.assertEqual(manifest["semantic_source_snapshot"], self.descriptor["snapshot"])
        base = self.read("context/corpus/base-index.json")
        self.assertEqual(base["bundle"]["snapshot"], self.descriptor["snapshot"])
        direct = self.read("context/assembly-index.json")
        self.assertEqual(direct, base)
        self.assertEqual(direct["schema"], "okf-context-index.v1")
        self.assertEqual((self.root / "context/assembly-index.json").read_bytes(), (self.root / "context/corpus/base-index.json").read_bytes())
        for part in [*manifest["records"]["shards"], *manifest["search"]["shards"].values()]:
            raw = (self.root / "context/corpus" / part["path"]).read_bytes()
            self.assertEqual(raw, (ROOT / "context/corpus" / part["path"]).read_bytes())
            self.assertEqual(digest(raw), part["sha256"])

    def test_new_semantic_assertions_retain_governed_fields_and_provenance_hashes(self):
        from jsonschema import Draft202012Validator, FormatChecker
        validator = Draft202012Validator(json.loads((ROOT / "profiles/bundle-wiki/v1/semantic-assertion.schema.json").read_bytes()), format_checker=FormatChecker())
        edges = [row for row in self.edges if row.get("projection_source")]
        self.assertTrue(edges)
        sources = {}
        for edge in edges:
            validator.validate({**edge, "source": edge["source_iri"], "target": edge["target_iri"]})
            self.assertEqual(edge["assertion_status"], "model-derived" if edge["authority"]["class"] == "model-assisted" else "normalized")
            for evidence in edge["evidence"]:
                from build_bundle import canonical
                self.assertEqual(evidence["source_value_sha256"], digest(canonical(evidence["source_value"])))
                self.assertEqual(evidence["source_value"]["url"], evidence["original_source_url"])
                self.assertEqual(evidence["source_sha256"], digest((ROOT / evidence["source_artifact"]).read_bytes()))
                self.assertEqual(evidence["source_value"]["source_sha256"], evidence["original_source_sha256"])
                if evidence["source_artifact"] not in sources:
                    sources[evidence["source_artifact"]] = json.loads((ROOT / evidence["source_artifact"]).read_bytes())
                match = re.fullmatch(r"assertions\[(\d+)\]\.provenance\[(\d+)\]", evidence["source_field"])
                self.assertIsNotNone(match)
                authored = sources[evidence["source_artifact"]]["assertions"][int(match[1])]
                self.assertEqual(authored["id"], edge["id"])
                self.assertEqual(authored["provenance"][int(match[2])], evidence["source_value"])

    def test_semantic_references_join_adm_pages_and_concept_facets(self):
        index = self.read("context/corpus/base-index.json")
        concepts = {row["id"]: row for row in index["records"] if row["kind"] == "concept"}
        relevant = [row for row in index["assertions"] if row["source"] in concepts and row["target"].startswith(BASE + "id/page/adm/")]
        self.assertTrue(relevant, "ADM pages must join to authored concepts, not only containment")
        for edge in relevant:
            target = self.by_route[edge["target"].removeprefix(BASE + "id/")]
            self.assertIn(concepts[edge["source"]]["label"], target["concept"])
            self.assertTrue(any(row["assertion_id"] == edge["id"] for row in target["classification"]["semantic_references"]))

    def test_all_build_and_entrypoint_hashes(self):
        receipt = json.loads((ROOT / "validation/combined-reader/build.json").read_bytes())
        for row in receipt["outputs"]:
            raw = (ROOT / row["path"]).read_bytes()
            self.assertEqual(len(raw), row["bytes"], row["path"])
            self.assertEqual(digest(raw), row["sha256"], row["path"])
        for row in self.descriptor["entrypoint_integrity"].values():
            raw = (self.root / row["path"]).read_bytes()
            self.assertEqual(digest(raw), row["sha256"])

    def test_semantic_direct_and_reified_projections_agree(self):
        from build_bundle import canonical, load_yaml
        semantic = self.read("data/semantic/manifest.json")
        control = load_yaml(self.root / "okf-bundle.yamlld")
        self.assertEqual(control, self.read("okf-bundle.jsonld"))
        self.assertEqual(control["snapshot_id"], self.descriptor["snapshot"])
        self.assertEqual(semantic["semantic_identity"]["sha256"], self.descriptor["plane_roots"]["semantic"])
        self.assertEqual(semantic["semantic_identity"]["sha256"], digest(canonical({key: semantic[key] for key in ("nodes", "assertions")})))
        nodes, assertions = {}, []
        for kind in ("nodes", "assertions"):
            for binding in semantic[kind]:
                raw = (self.root / binding["path"]).read_bytes()
                decoded = gzip.decompress(raw)
                self.assertEqual(digest(raw), binding["sha256"])
                self.assertEqual(digest(decoded), binding["decoded_sha256"])
                graph = json.loads(decoded)["@graph"]
                self.assertEqual(len(graph), binding["count"])
                rdf = (self.root / binding["rdf"]["path"]).read_bytes()
                self.assertEqual(digest(rdf), binding["rdf"]["sha256"])
                self.assertEqual(digest(gzip.decompress(rdf)), binding["rdf"]["canonical_sha256"])
                if kind == "nodes":
                    nodes.update({row["@id"]: row for row in graph})
                else:
                    assertions.extend(graph)
        self.assertEqual(len(nodes), len(self.records))
        self.assertEqual(len(assertions), len(self.edges))
        triples = sorted([row["source"], row["predicate"], row["target"]] for row in assertions)
        predicates = {row["predicate"] for row in assertions}
        direct = sorted((row["@id"], predicate, target["@id"]) for row in nodes.values()
                        for predicate in predicates for target in row.get(predicate, []))
        self.assertEqual(direct, sorted({tuple(row) for row in triples}))
        self.assertEqual(digest(canonical(triples)), semantic["direct_reified_triples_sha256"])
        self.assertEqual(nodes[BASE + "id/staff-domain/pip"]["@type"], ["skos:Concept", "dwp:Benefit"])

    def test_semantic_projection_fails_on_unresolved_relationship(self):
        with self.assertRaisesRegex(ValueError, "unresolved endpoint"):
            add_semantics([], [], [], {}, {"records": [], "assertions": [{"id": "unresolved", "source": "missing", "target": "missing"}]}, "2026-09-20T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
