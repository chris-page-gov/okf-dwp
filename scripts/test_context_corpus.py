"""Full-source corpus controls: all-page accounting and verified lexical shards."""
from collections import Counter
import gzip
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from build_bundle import ROOT, digest
from build_context_corpus import (CONFIG, MAX_SHARD_BYTES, OUTPUT, compile_corpus,
                                  deterministic_gzip, token_bucket, tokens)


class ContextCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = ROOT / OUTPUT
        cls.manifest = json.loads((cls.directory / "manifest.json").read_bytes())
        cls.records = []
        for shard in cls.manifest["records"]["shards"]:
            payload = cls.read_shard(shard)
            if payload["first_ordinal"] != len(cls.records):
                raise AssertionError("Non-contiguous record ordinals")
            cls.records.extend(payload["records"])

    @classmethod
    def read_shard(cls, shard):
        raw = (cls.directory / shard["path"]).read_bytes()
        if len(raw) != shard["bytes"] or digest(raw) != shard["sha256"]:
            raise AssertionError("Transfer digest/size mismatch")
        decoded = gzip.decompress(raw)
        if len(decoded) != shard["decoded_bytes"] or digest(decoded) != shard["decoded_sha256"]:
            raise AssertionError("Decoded digest/size mismatch")
        if len(decoded) > MAX_SHARD_BYTES:
            raise AssertionError("Decoded shard exceeds bound")
        return json.loads(decoded)

    def test_rebuild_matches_every_committed_artefact(self):
        for name, expected in compile_corpus().items():
            self.assertEqual((self.directory / name).read_bytes(), expected, name)

    def test_every_acquired_page_accounted_for_and_every_nonempty_text_exact(self):
        by_source = {record["provenance"][0]["url"]: record for record in self.records}
        excluded = {row["source_url"]: row for row in self.manifest["unsearchable_pages"]}
        seen = Counter()
        config = json.loads((ROOT / CONFIG).read_bytes())
        for source in config["sources"]:
            inventory = json.loads((ROOT / source["inventory"]).read_bytes())
            for doc in inventory["documents"]:
                pages = json.loads((ROOT / doc["pages_path"]).read_bytes())["pages"]
                for page in pages:
                    seen["pages"] += 1
                    if not page["text"].strip():
                        self.assertEqual(excluded[page["url"]]["reason"], "empty-extracted-text")
                        self.assertNotIn(page["url"], by_source)
                        seen["empty_pages"] += 1
                    else:
                        record = by_source[page["url"]]
                        self.assertEqual(record["text"], page["text"])
                        self.assertEqual(record["assertion_status"], "normalized")
                        self.assertEqual(record["authority"]["class"], "derived")
                        self.assertEqual(record["provenance"][0]["source_sha256"], doc["sha256"])
                        seen["nonempty_pages"] += 1
        for key, count in seen.items():
            self.assertEqual(self.manifest["counts"][key], count)
        self.assertEqual(len(self.records), seen["nonempty_pages"])

    def test_all_page_text_tokens_have_postings_and_no_out_of_range_ids(self):
        postings = {}
        for bucket, shard in self.manifest["search"]["shards"].items():
            payload = self.read_shard(shard)
            self.assertEqual(payload["schema"], "okf-context-postings.v1")
            for token, ordinals in payload["postings"].items():
                self.assertEqual(token_bucket(token), bucket)
                self.assertEqual(ordinals, sorted(set(ordinals)))
                self.assertTrue(all(0 <= ordinal < len(self.records) for ordinal in ordinals))
                postings[token] = set(ordinals)
        expected = {}
        for ordinal, record in enumerate(self.records):
            for token in tokens(record["text"]):
                expected.setdefault(token, set()).add(ordinal)
        self.assertEqual(postings, expected)

    def test_existing_semantic_records_reused_exactly_and_no_answer_requirements(self):
        base = json.loads((self.directory / self.manifest["base_index"]["path"]).read_bytes())
        self.assertEqual(base["requirements"], [])
        original = {record["id"]: record for record in base["records"]}
        for record in self.records:
            if record["id"] in original:
                self.assertEqual(record, original[record["id"]])
        self.assertEqual([row["id"] for row in self.records], sorted({row["id"] for row in self.records}))

    def test_source_families_and_empty_extractions_are_explicit(self):
        config = json.loads((ROOT / CONFIG).read_bytes())
        self.assertEqual({source["id"] for source in config["sources"]},
                         {source["id"] for source in self.manifest["source_groups"]})
        for group in self.manifest["source_groups"]:
            self.assertEqual(group["counts"]["pages"], group["counts"]["nonempty_pages"] + group["counts"]["empty_pages"])
            self.assertIn("not source publication", group["capture_date_role"])
        self.assertEqual(self.manifest["records"]["count"], len(self.records))

    def test_additive_explorer_descriptor_binds_exact_copies_and_preserves_reader(self):
        original = json.loads((ROOT / 'full-dmg/okf-explorer.json').read_bytes())
        added = json.loads((ROOT / 'full-dmg/okf-corpus-context.json').read_bytes())
        for field in ('snapshot', 'snapshot_id', 'counts', 'plane_roots', 'source'):
            self.assertEqual(added[field], original[field])
        for key, value in original['entrypoints'].items():
            self.assertEqual(added['entrypoints'][key], value)
        ref = added['entrypoints']['context_corpus']
        raw = (ROOT / 'full-dmg' / ref['path']).read_bytes()
        self.assertEqual(raw, (self.directory / 'manifest.json').read_bytes())
        self.assertEqual(digest(raw), ref['sha256'])
        receipt = json.loads((ROOT / 'context/corpus-explorer-projection.json').read_bytes())
        self.assertEqual(receipt['source_descriptor']['sha256'], digest((ROOT / 'full-dmg/okf-explorer.json').read_bytes()))
        for item in receipt['files']:
            self.assertEqual(digest((ROOT / item['path']).read_bytes()), item['sha256'])

    def test_changed_pdf_outside_old_semantic_selection_is_rejected(self):
        base = json.loads((self.directory / "base-index.json").read_bytes())
        selected_hashes = {p["source_sha256"] for row in base["records"] for p in row["provenance"]}
        config = json.loads((ROOT / CONFIG).read_bytes())
        documents = [doc for source in config["sources"]
                     for doc in json.loads((ROOT / source["inventory"]).read_bytes())["documents"]]
        target = ROOT / next(doc["pdf_path"] for doc in documents if doc["sha256"] not in selected_hashes)
        original = Path.read_bytes

        def changed(path):
            raw = original(path)
            return raw + b"tampered" if path.resolve() == target.resolve() else raw

        with patch.object(Path, "read_bytes", changed):
            with self.assertRaisesRegex(ValueError, "Input digest mismatch"):
                compile_corpus()

    def test_portable_tokenisation_and_compression(self):
        self.assertEqual(tokens("HÔSPITAL hospital 24 1 a ESA(IR)"), ["24", "esa", "hospital", "ir"])
        # Independently checked with unsigned JavaScript Math.imul: 0x4f9cd7b3.
        self.assertEqual(token_bucket("hospital"), "4f")
        raw = b"Deterministic corpus evidence" * 20
        compressed = deterministic_gzip(raw)
        self.assertEqual(gzip.decompress(compressed), raw)
        self.assertEqual(compressed[:10], b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff")
        self.assertEqual(compressed, deterministic_gzip(raw))


if __name__ == "__main__":
    unittest.main()
