"""Real corpus controls for additive DMG/ADM Reader publication."""
from collections import Counter
from copy import deepcopy
import gzip
import json
import re
import unittest

from build_bundle import ROOT, BASE, digest, source_text_block
from build_combined_reader import LABELS, compile_combined, add_semantics
from build_full_dmg import bucket, tokens


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
