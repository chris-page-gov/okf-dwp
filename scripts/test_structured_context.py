"""Independent controls over retained source-led production artefacts.

These checks do not rebuild the corpus, acquire sources or establish legal
answerability. The source-case experiment retains its separate 4/8 denominator.
"""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import unittest

from build_structured_context import occurrences, runtime_canonical

ROOT = Path(__file__).resolve().parents[1]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def load_bound(root, binding):
    raw = (root / binding["path"]).read_bytes()
    if digest(raw) != binding["sha256"] or len(raw) != binding["bytes"]:
        raise AssertionError("Bound source changed: " + binding["path"])
    decoded = gzip.decompress(raw) if binding.get("encoding") == "gzip" or binding["path"].endswith(".gz") else raw
    if "decoded_sha256" in binding and (digest(decoded) != binding["decoded_sha256"] or len(decoded) != binding["decoded_bytes"]):
        raise AssertionError("Decoded binding changed: " + binding["path"])
    return json.loads(decoded)


class StructuredContextHelperControls(unittest.TestCase):
    def test_runtime_commitment_is_canonical_json_without_file_newline(self):
        sample = {"z": ["é", "plain"], "a": {"nested": 1}}
        self.assertEqual(runtime_canonical(sample), canonical(sample))
        self.assertFalse(runtime_canonical(sample).endswith(b"\n"))

    def test_all_unicode_mark_categories_match_consumer_tokens(self):
        # Combining class zero is still a Unicode Mark and must be removed.
        self.assertEqual(occurrences("a\u20ddb café A12 x"), ["ab", "cafe", "a12"])


class StructuredContextArtefactControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ROOT / "structured-context"
        cls.manifest = json.loads((cls.root / "manifest.json").read_bytes())
        cls.records = []
        for shard in cls.manifest["records"]["shards"]:
            part = load_bound(cls.root, shard)
            if part["first_ordinal"] != len(cls.records):
                raise AssertionError("Record ordinal sequence differs")
            cls.records.extend(part["records"])
        cls.by_id = {row["id"]: row for row in cls.records}
        cls.cards = []
        for shard in cls.manifest["discovery"]["shards"]:
            part = load_bound(cls.root, shard)
            if part["first_ordinal"] != len(cls.cards):
                raise AssertionError("Card ordinal sequence differs")
            cls.cards.extend(part["cards"])
        cls.base = load_bound(cls.root, cls.manifest["base_index"])

    def test_exact_card_census_and_complete_evidence_commitments(self):
        self.assertEqual(len(self.records), self.manifest["records"]["count"])
        self.assertEqual(len(self.by_id), len(self.records))
        self.assertEqual(len(self.cards), len(self.records))
        self.assertEqual(len({c["id"] for c in self.cards}), len(self.cards))
        for row, card in zip(self.records, self.cards):
            self.assertEqual(card["evidence_id"], row["id"])
            self.assertEqual(card["evidence_sha256"], digest(canonical(row)))
            self.assertNotIn(card["id"], self.by_id)
            self.assertEqual(card["authority"]["class"], "derived")
            self.assertEqual(card["access"], row["access"])
            self.assertTrue(row["text"].strip())

    def test_global_ranking_totals_and_posting_frequencies_are_bound(self):
        lengths = []
        totals = Counter(source=0, discovery=0)
        term_totals = {"source": Counter(), "discovery": Counter()}
        for row, card in zip(self.records, self.cards):
            source = occurrences(row["text"])
            discovery = occurrences("\n".join([card["label"], *card["heading_path"], card["summary"], *card["search_aliases"]]))
            lengths.append((len(source), len(discovery)))
            totals.update(source=len(source), discovery=len(discovery))
            term_totals["source"].update(source)
            term_totals["discovery"].update(discovery)
        self.assertEqual(dict(totals), self.manifest["search"]["total_tokens"])
        seen = set()
        for shard in self.manifest["search"]["shards"].values():
            part = load_bound(self.root, shard)
            for token, postings in part["postings"].items():
                self.assertNotIn(token, seen)
                seen.add(token)
                self.assertEqual(sum(p[1] for p in postings), term_totals["source"][token])
                self.assertEqual(sum(p[3] for p in postings), term_totals["discovery"][token])
                self.assertEqual([p[0] for p in postings], sorted({p[0] for p in postings}))
                for ordinal, source_tf, source_length, discovery_tf, discovery_length in postings:
                    self.assertEqual((source_length, discovery_length), lengths[ordinal])
                    self.assertGreater(source_tf + discovery_tf, 0)
                    self.assertLessEqual(source_tf, source_length)
                    self.assertLessEqual(discovery_tf, discovery_length)
        self.assertEqual(seen, term_totals["source"].keys() | term_totals["discovery"].keys())

    def test_every_incident_commitment_has_exact_matching_opposite_endpoint(self):
        edges, appearances = {}, Counter()
        known = set(self.by_id) | {r["id"] for r in self.base["records"]}
        endpoints = set()
        for shard in self.manifest["relationships"]["shards"].values():
            for entry in load_bound(self.root, shard)["entries"]:
                self.assertNotIn(entry["id"], endpoints)
                endpoints.add(entry["id"])
                for direction, endpoint_field in (("outgoing", "source"), ("incoming", "target")):
                    values = entry[direction]
                    identifiers = [e["id"] for e in values]
                    self.assertEqual(identifiers, sorted(set(identifiers)))
                    self.assertEqual(entry[direction + "_count"], len(values))
                    self.assertEqual(entry[direction + "_ids_sha256"], digest(canonical(identifiers)))
                    for edge in values:
                        self.assertEqual(edge[endpoint_field], entry["id"])
                        self.assertIn(edge["source"], known)
                        self.assertIn(edge["target"], known)
                        self.assertEqual(edges.setdefault(edge["id"], edge), edge)
                        appearances[edge["id"]] += 1
                        if "/source-reference/" in edge["id"]:
                            self.assertEqual(edge["predicate"], "http://purl.org/dc/terms/references")
                            self.assertEqual(edge["assertion_status"], "normalized")
                            self.assertEqual(edge["authority"]["class"], "derived")
                            self.assertIn("Navigation observation only", edge["scope"])
        self.assertEqual(endpoints, known)
        self.assertTrue(all(count == 2 for count in appearances.values()))
        self.assertEqual(self.base["assertions"], [])

    def test_every_catalogue_reference_is_present_at_its_exact_unit_byte_offsets(self):
        manifest = json.loads((ROOT / "structured-units/manifest.json").read_bytes())
        for binding in manifest["documents"]:
            document = load_bound(ROOT / "structured-units", binding)
            for unit in document["units"]:
                text = self.by_id[unit["id"]]["text"].encode()
                self.assertEqual(unit["record_sha256"], digest(canonical(self.by_id[unit["id"]]) + b"\n"))
                for reference in unit.get("references", []):
                    start, end = reference["start_utf8"], reference["end_utf8"]
                    self.assertGreaterEqual(start, 0)
                    self.assertGreater(end, start)
                    self.assertLessEqual(end, len(text))
                    self.assertEqual(text[start:end].decode(), reference["literal"], unit["id"])
                    self.assertEqual(reference["legal_dependency"], "not-established")

    def test_existing_authored_id_and_record_bytes_are_retained(self):
        old = json.loads((ROOT / "logical-units/manifest.json").read_bytes())
        authored = 0
        for binding in old["documents"]:
            for unit in load_bound(ROOT / "logical-units", binding)["units"]:
                if unit.get("boundary_status") == "author-declared":
                    authored += 1
                    self.assertIn(unit["id"], self.by_id)
                    self.assertEqual(unit["record_sha256"], digest(canonical(self.by_id[unit["id"]]) + b"\n"))
        self.assertEqual(authored, old["counts"]["authored_units"])


if __name__ == "__main__":
    unittest.main()
