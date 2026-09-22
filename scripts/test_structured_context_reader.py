"""Small offline contract controls for the additive source-led Reader.

Synthetic source text exercises projection behaviour, not DWP legal meaning.
The complete source corpus and earlier generated releases are never written.
"""
from copy import deepcopy
import gzip
import json
import unittest

from build_bundle import BASE, ROOT, canonical, digest, source_text_block
from build_full_dmg import bucket
from build_logical_units import make_record
from structured_context_reader import bound_cards, emit_reader


def fixture():
    when = "2026-09-01T12:00:00Z"
    doc = {"id": "synthetic-manual", "title": "Synthetic manual", "role": "substantive", "kind": "chapter",
           "url": "https://example.org/manual.pdf", "sha256": "a" * 64, "pages_sha256": "b" * 64,
           "pages_path": "source/synthetic-pages.json", "pdf_path": "source/synthetic.pdf", "observed_at": when}
    pages = [{"page": n + 1, "text": text, "url": doc["url"] + f"#page={n + 1}"}
             for n, text in enumerate(["A source sentence ends across", "two pages; its qualification remains."])]
    source_unit = {"key": "retained-rule", "label": "Retained rule", "kind": "compound", "authored": False,
                   "spans": [{"page": p["page"], "start_utf8": 0, "end_utf8": len(p["text"].encode()),
                              "literal_sha256": digest(p["text"].encode())} for p in pages]}
    unit = make_record("dmg", doc, pages, source_unit, "test-v1")
    concept = {"id": BASE + "id/concept/synthetic", "route": "concept/synthetic", "label": "Declared concept",
               "kind": "concept", "text": "A separately authored neutral concept.", "assertion_status": "model-derived",
               "authority": {"class": "model-assisted", "label": "Test author", "source": "https://example.org/profile"},
               "scope": "Unreviewed test metadata.", "provenance": deepcopy(unit["provenance"][:1]),
               "rights": "https://example.org/licence", "access": "public"}
    edge = {"id": BASE + "id/assertion/synthetic", "source": concept["id"], "target": unit["id"],
            "predicate": "http://purl.org/dc/terms/references", "assertion_status": "model-derived",
            "authority": deepcopy(concept["authority"]), "scope": "Navigation only, not applicability.",
            "reason": "Retained declared concept reference.", "provenance": deepcopy(unit["provenance"][:1])}
    semantic = {"schema": "okf-context-index.v1", "bundle": {"id": BASE + "id/bundle/test", "snapshot": "test-structured"},
                "records": [concept], "assertions": [edge], "requirements": [], "scope": "Synthetic controls.", "limitations": []}
    card = {"id": BASE + "id/discovery/test", "evidence_id": unit["id"], "evidence_sha256": digest(canonical(unit)[:-1]),
            "label": unit["label"], "heading_path": ["Applications", "Travel conditions"], "summary": "zzpreviewonly",
            "search_aliases": ["zztagalias"], "assertion_status": "normalized", "authority": {"class": "derived", "label": "Test extraction"},
            "scope": "Source discovery only.", "provenance": deepcopy(unit["provenance"]), "rights": unit["rights"], "access": unit["access"]}
    empty_doc = {**doc, "id": "empty-document", "title": "Empty document", "url": "https://example.org/empty.pdf", "sha256": "c" * 64}
    inventory = canonical({"documents": [doc, empty_doc]})
    corpus = {"schema": "okf-context-corpus.v3", "bundle": semantic["bundle"], "scope": "Synthetic complete captured text.",
              "counts": {"documents": 2, "pages": 3}, "limitations": ["Independent experimental source navigation."],
              "extensions": {"source_groups": [{"id": "dmg", "inventory": {"repository_path": "test-inventory.json", "sha256": digest(inventory)}}],
                             "unit_manifest": {"repository_path": "structured-units/manifest.json", "sha256": "d" * 64}}}
    base = canonical({**semantic, "assertions": []})
    corpus_outputs = {"base-index.json": base, "manifest.json": canonical(corpus)}
    declarations = {"@context": {}, "@graph": []}

    class Inputs:
        def read(self, path, expected=None):
            raw = inventory if path == "test-inventory.json" else (ROOT / path).read_bytes()
            if expected is not None and digest(raw) != expected:
                raise ValueError("Fixture binding differs")
            return raw

    return Inputs(), corpus, [unit], semantic, declarations, corpus_outputs, [card]


def decoded(outputs, path):
    raw = outputs[path]
    return json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)


class StructuredReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args = fixture()
        cls.outputs = emit_reader(*cls.args)
        cls.manifest = decoded(cls.outputs, "data/manifest.json")
        cls.records = [r for shard in cls.manifest["shards"]["datasets"] for r in decoded(cls.outputs, shard["path"])]
        cls.record = next(r for r in cls.records if r["id"] == cls.args[2][0]["id"])

    def test_complete_source_text_and_page_spans_remain_exact(self):
        unit = self.args[2][0]
        self.assertIn(source_text_block(unit["text"]), self.record["narrative"]["body"])
        self.assertEqual(unit["evidence_unit"], self.record["extras"]["evidence_unit"])
        for span in unit["evidence_unit"]["spans"]:
            self.assertIn(span["source_url"], self.record["narrative"]["body"])
            self.assertIn(span["literal_sha256"], self.record["narrative"]["body"])

    def test_cards_remain_separate_metadata_not_nodes_or_concepts(self):
        card = self.args[6][0]
        self.assertEqual(card, self.record["extras"]["discovery_card"])
        self.assertIn("Discovery metadata — not evidence", self.record["narrative"]["body"])
        self.assertNotIn(card["id"], {r["id"] for r in self.records})
        self.assertEqual(["Declared concept"], self.record["concept"])
        self.assertEqual(4, len(self.records))  # One concept, one unit, two source documents.

    def test_heading_role_and_kind_facets_bind_result_rows(self):
        facets = decoded(self.outputs, "data/facets.json")
        self.assertEqual({"Applications", "Travel conditions", "No source heading recorded"},
                         {r["value"] for r in facets["source_heading"]})
        self.assertEqual("chapter", self.record["source_kind"])
        self.assertEqual(["Applications", "Travel conditions"], self.record["source_heading"])
        filters = decoded(self.outputs, "data/search/filters/source_heading.json.gz")
        ordinal = self.records.index(self.record)
        self.assertEqual([ordinal], filters["values"]["Applications"])
        search = decoded(self.outputs, "data/search/manifest.json")
        result = next(r for path in search["entrypoints"]["result_docs"] for r in decoded(self.outputs, path) if r["ordinal"] == ordinal)
        for key in ("source_heading", "source_role", "source_kind", "concept"):
            self.assertEqual(self.record[key], result[key])

    def test_source_search_and_discovery_tags_keep_distinct_fields(self):
        search = decoded(self.outputs, "data/search/manifest.json")
        postings = {k: v for p in search["entrypoints"]["postings"] for k, v in decoded(self.outputs, p)["tokens"].items()}
        self.assertNotIn("zzpreviewonly", postings)  # A preview is not indexed as source evidence.
        self.assertEqual(32, postings["zztagalias"][0][2])
        self.assertEqual(32, postings["travel"][0][2])
        self.assertTrue(any(mask & 8 for _, _, mask in postings["qualification"]))

    def test_actual_assertion_shard_is_the_projection_provenance(self):
        edges = [r for s in self.manifest["shards"]["relationships"] for r in decoded(self.outputs, s["path"])]
        self.assertEqual(1, len(edges))
        edge = edges[0]
        original = self.args[3]["assertions"][0]
        self.assertEqual(original["scope"], edge["scope"])
        self.assertEqual(original["reason"], edge["reason"])
        provenance = edge["evidence"][0]
        self.assertEqual("structured-context/data/context-assertions/0000.json", provenance["source_artifact"])
        path = provenance["source_artifact"].removeprefix("structured-context/")
        self.assertEqual(digest(self.outputs[path]), provenance["source_sha256"])
        self.assertEqual("assertions[0].provenance[0]", provenance["source_field"])
        self.assertEqual(provenance["source_value"], decoded(self.outputs, path)["assertions"][0]["provenance"][0])
        self.assertEqual([], json.loads(self.args[5]["base-index.json"])["assertions"])
        adjacent = decoded(self.outputs, f"data/adjacency/{bucket(self.record['route'])}.json.gz")
        self.assertEqual([edge], adjacent[self.record["route"]])

    def test_descriptor_uses_separate_output_without_combined_teaching_routes(self):
        descriptor = decoded(self.outputs, "okf-explorer.json")
        self.assertNotIn("learning_presentation", descriptor)
        control = decoded(self.outputs, "okf-bundle.jsonld")
        self.assertTrue(control["descriptor"]["@id"].endswith("structured-context/okf-explorer.json"))
        self.assertEqual(digest(self.args[5]["manifest.json"]), descriptor["entrypoints"]["context_corpus"]["sha256"])
        self.assertTrue(any(r["title"] == "Empty document" for r in self.records))
        self.assertTrue(all(r["timestamp"] == "" for r in self.records))

    def test_normalised_reference_is_not_described_as_authored(self):
        args = fixture()
        args[3]["assertions"][0].update(assertion_status="normalized", authority=deepcopy(args[2][0]["authority"]))
        outputs = emit_reader(*args)
        manifest = decoded(outputs, "data/manifest.json")
        edge = decoded(outputs, manifest["shards"]["relationships"][0]["path"])[0]
        self.assertEqual("normalized", edge["assertion_status"])
        self.assertNotIn("authored", edge["derivation"])
        self.assertTrue(all("authored" not in p["rationale"] for p in edge["evidence"]))

    def test_deterministic_projection_does_not_mutate_inputs(self):
        before = deepcopy(self.args[1:])
        self.assertEqual(self.outputs, emit_reader(*self.args))
        self.assertEqual(before, self.args[1:])

    def test_stale_record_or_span_metadata_is_rejected(self):
        args = fixture()
        args[2][0]["evidence_unit"]["spans"][0]["locator"] = "Changed locator"
        with self.assertRaisesRegex(ValueError, "stale complete-record"):
            bound_cards(args[2], args[6])

    def test_missing_duplicate_cards_are_rejected(self):
        for cards in ([], self.args[6] * 2):
            with self.subTest(cards=len(cards)), self.assertRaises(ValueError):
                bound_cards(self.args[2], cards)

    def test_authority_or_access_upgrade_is_rejected(self):
        for field, value in (("assertion_status", "official"), ("access", "restricted")):
            cards = deepcopy(self.args[6]); cards[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                bound_cards(self.args[2], cards)
        cards = deepcopy(self.args[6]); cards[0]["authority"]["class"] = "official"
        with self.assertRaisesRegex(ValueError, "official authority"):
            bound_cards(self.args[2], cards)


if __name__ == "__main__":
    unittest.main()
