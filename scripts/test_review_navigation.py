"""Navigation classifications must remain inspectable, reversible and non-legal."""
from collections import Counter
from copy import deepcopy
import gzip
import json
import unittest

from build_bundle import ROOT, digest
from build_context_discovery import Inputs
from build_review_navigation import (DIMENSIONS, OUTPUT, RUNTIME, UNKNOWN, compile_matchers,
                                     literal_assignments, load_rules)


class NavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / OUTPUT / "manifest.json").read_bytes())
        cls.rules = load_rules(Inputs(ROOT))[1]
        cls.assignments = []
        for shard in cls.manifest["assignments"]:
            raw = (ROOT / OUTPUT / shard["path"]).read_bytes()
            assert len(raw) == shard["bytes"] and digest(raw) == shard["sha256"]
            decoded = gzip.decompress(raw)
            assert len(decoded) == shard["decoded_bytes"] and digest(decoded) == shard["decoded_sha256"]
            rows = json.loads(decoded)["assignments"]
            assert len(rows) == shard["records"]
            cls.assignments.extend(rows)
        cls.runtime = json.loads((ROOT / "full-dmg" / RUNTIME / "manifest.json").read_bytes())
        cls.records = []
        for shard in cls.runtime["shards"]["datasets"]:
            raw = (ROOT / "full-dmg" / shard["path"]).read_bytes()
            assert digest(raw) == shard["sha256"]
            cls.records.extend(json.loads(gzip.decompress(raw)))

    def test_whole_word_and_case_sensitive_abbreviations(self):
        matcher = compile_matchers([row for row in self.rules if row["@id"].endswith("/pip")])
        self.assertEqual(literal_assignments("pip pipe PIPP", matcher), [])
        self.assertEqual(literal_assignments("PIP", matcher)[0]["matched_text"], "PIP")

    def test_flexible_whitespace_preserves_exact_span(self):
        text = "Prefix: PENSION\n   CREDIT applies here"
        matcher = compile_matchers([row for row in self.rules if row["@id"].endswith("/pension-credit")])
        row = literal_assignments(text, matcher)[0]
        self.assertEqual(row["matched_text"], "PENSION\n   CREDIT")
        self.assertEqual(text[row["start"]:row["end"]], row["matched_text"])

    def test_ambiguous_short_aliases_deliberately_absent(self):
        aliases = {alias for row in self.rules for alias in row["match"].get("case_sensitive_abbreviations", [])}
        self.assertFalse(aliases.intersection({"IS", "PC", "SP", "CA", "AA", "SDA"}))

    def test_state_pension_credit_is_not_silently_state_pension(self):
        matcher = compile_matchers([row for row in self.rules if row["@id"].endswith("/state-pension")])
        self.assertEqual(literal_assignments("State Pension Credit", matcher), [])
        rows = literal_assignments("State Pension Credit and State Pension", matcher)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["start"], 25)

    def test_full_corpus_accounting_and_empty_extractions(self):
        self.assertEqual(len(self.assignments), 19090)
        self.assertEqual(len({row["record_id"] for row in self.assignments}), 19090)
        self.assertEqual(Counter(row["source_group"] for row in self.assignments), {"dmg": 14743, "adm": 4347})
        self.assertEqual(sum(row["empty_extraction"] for row in self.assignments), 893)
        for family, coverage in self.manifest["coverage"].items():
            subset = [row for row in self.assignments if row["source_group"] == family]
            for key in DIMENSIONS:
                self.assertEqual(coverage["dimensions"][key]["classified"], sum(row["facets"][key] != [UNKNOWN] for row in subset))

    def test_assignment_literals_exactly_match_frozen_pages(self):
        by_doc = {}
        for family in json.loads((ROOT / "context/corpus-sources.json").read_bytes())["sources"]:
            for doc in json.loads((ROOT / family["inventory"]).read_bytes())["documents"]:
                by_doc[doc["id"]] = json.loads((ROOT / doc["pages_path"]).read_bytes())["pages"]
        for row in self.assignments:
            page = by_doc[row["document_id"]][row["page"] - 1]
            self.assertEqual(digest(page["text"].encode()), row["literal_sha256"])
            for item in row["evidence"]:
                if item["method"] == "explicit-mention":
                    self.assertEqual(page["text"][item["start"]:item["end"]], item["matched_text"])
                else:
                    self.assertEqual(item["method"], "curated-reference")
                    self.assertIn("assertion_id", item)

    def test_no_applicability_or_review_promotion(self):
        self.assertEqual(self.manifest["legal_applicability"], "not-established")
        self.assertEqual(self.manifest["review_status"], "unreviewed")
        self.assertTrue(all(row["review_status"] == "unreviewed" for row in self.assignments))
        self.assertEqual(sum(row["facets"]["concept"] != [UNKNOWN] for row in self.assignments if row["source_group"] == "adm"), 0)

    def test_reader_original_records_preserved_except_explicit_overlay_fields(self):
        original = json.loads((ROOT / "full-dmg/data/manifest.json").read_bytes())
        before = []
        for shard in original["shards"]["datasets"]:
            before.extend(json.loads(gzip.decompress((ROOT / "full-dmg" / shard["path"]).read_bytes())))
        self.assertEqual(len(before), len(self.records))
        for old, new in zip(before, self.records):
            projection = deepcopy(new)
            for key in [*DIMENSIONS, "classification"]:
                projection.pop(key)
            # New conceptual topic projection deliberately replaces the old
            # structural topics array; source_role still carries that value.
            projection["topics"] = old["topics"]
            self.assertEqual(projection, old)
        self.assertEqual(original["chunks"]["relationships"], self.runtime["chunks"]["relationships"])
        self.assertEqual(original["chunks"]["resources"], self.runtime["chunks"]["resources"])

    def test_native_filter_postings_match_record_fields(self):
        for key in DIMENSIONS:
            postings = json.loads(gzip.decompress((ROOT / "full-dmg" / RUNTIME / "filters" / f"{key}.json.gz").read_bytes()))
            expected = {}
            for ordinal, row in enumerate(self.records):
                # Match the consumer's native plural alias for the topic facet,
                # not merely a redundant producer field which could mask drift.
                values = row["topics"] if key == "topic" else row[key]
                for value in values:
                    expected.setdefault(value, []).append(ordinal)
            self.assertEqual(postings["values"], expected)
            self.assertEqual(set().union(*(set(ids) for ids in expected.values())), set(range(len(self.records))))

    def test_search_topic_summaries_match_lazy_records(self):
        search = json.loads((ROOT / "full-dmg" / RUNTIME / "search.json").read_bytes())
        for shard in search["entrypoints"]["result_docs"]:
            for row in json.loads(gzip.decompress((ROOT / "full-dmg" / shard).read_bytes())):
                self.assertEqual(row["topics"], self.records[row["ordinal"]]["topics"])

    def test_native_search_manifest_hashes_and_no_lexical_postings_change(self):
        original = json.loads((ROOT / "full-dmg/data/search/manifest.json").read_bytes())
        search = json.loads((ROOT / "full-dmg" / RUNTIME / "search.json").read_bytes())
        for key in ("lexicon", "prefixes", "postings", "doc_map", "sort_values"):
            self.assertEqual(search["entrypoints"][key], original["entrypoints"][key])
        binding = json.loads((ROOT / "full-dmg" / search["shard_metadata"]).read_bytes())
        from build_bundle import canonical
        self.assertEqual(digest(canonical(binding["shards"])), search["shard_manifest_sha256"])
        for item in binding["shards"]["search"]:
            raw = (ROOT / "full-dmg" / item["path"]).read_bytes()
            self.assertEqual(len(raw), item["bytes"])
            self.assertEqual(digest(raw), item["sha256"])

    def test_descriptor_bindings_and_original_ask_preserved(self):
        new = json.loads((ROOT / "full-dmg/okf-review-context.json").read_bytes())
        old = json.loads((ROOT / "full-dmg/okf-corpus-context.json").read_bytes())
        for key in ("context_assembly", "context_corpus", "relationship_adjacency"):
            self.assertEqual(new["entrypoints"][key], old["entrypoints"][key])
        for row in new["entrypoint_integrity"].values():
            raw = (ROOT / "full-dmg" / row["path"]).read_bytes()
            self.assertEqual(len(raw), row["bytes"])
            self.assertEqual(digest(raw), row["sha256"])


if __name__ == "__main__":
    unittest.main()
