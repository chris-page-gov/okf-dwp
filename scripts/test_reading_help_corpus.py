#!/usr/bin/env python3
"""Frozen direct-source controls for the additive reading-help projection."""
from __future__ import annotations

from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import reading_help_chat
from reading_help_chat import export, import_replies
from build_logical_units import Inputs
from build_reading_help_corpus import abbreviation_tables, cache_matches, cached_leaf_path, portable_gzip, rules_identity

ROOT = Path(__file__).resolve().parents[1]
CONTROLS = ROOT / "evaluation/reading-help-rollout/source-controls.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


class CorpusChecks(unittest.TestCase):
    def test_portable_gzip_header_and_bytes(self):
        data = b"Cross-platform reading help: source bytes remain exact.\n" * 7
        first = portable_gzip(data)
        self.assertEqual(first, portable_gzip(data))
        self.assertEqual(first[:10], bytes.fromhex("1f8b08000000000002ff"))
        self.assertEqual(gzip.decompress(first), data)

    def test_cached_leaf_cannot_escape_its_document(self):
        base = 'reading-help-corpus/documents/dmg/example'
        row = {'path': base + '/leaves/0000.json.gz', 'url': base + '/leaves/0000.json.gz',
               'sha256': 'a' * 64, 'bytes': 100}
        self.assertEqual(cached_leaf_path(row, base), row['path'])
        for forged in (base + '/leaves/../../source/secret.json.gz',
                       'reading-help-corpus/documents/adm/other/leaves/0000.json.gz',
                       '/private/tmp/secret.json.gz'):
            with self.subTest(path=forged), self.assertRaises(ValueError):
                cached_leaf_path({**row, 'path': forged, 'url': forged}, base)

    @classmethod
    def setUpClass(cls):
        cls.controls = json.loads(CONTROLS.read_text())
        cls.catalogue = json.loads((ROOT / "reading-help-corpus/manifest.json").read_text())
        cls.docs = {(row["family"], row["document_id"]): row for row in cls.catalogue["documents"]}

    def check_group(self, name, expected):
        rows = self.controls[name]
        self.assertEqual(len(rows), expected)
        self.assertEqual(Counter(row["family"] for row in rows), {"dmg": expected // 2,
                                                                  "adm": expected // 2})
        for row in rows:
            with self.subTest(name=name, document=row["document_id"]):
                ref = self.docs[(row["family"], row["document_id"])]
                index_raw = (ROOT / ref["path"]).read_bytes()
                self.assertEqual(digest(index_raw), ref["sha256"])
                index = json.loads(index_raw)
                self.assertEqual(index["source"]["sha256"], row["source_pdf_sha256"])
                self.assertEqual(index["extraction"]["sha256"], row["extraction_sha256"])
                extraction = json.loads((ROOT / index["extraction"]["path"]).read_text())
                source = extraction["pages"][row["page"] - 1]["text"].encode()
                literal = source[row["start_utf8"]:row["end_utf8"]]
                self.assertEqual(literal.decode(), row["literal"])
                self.assertEqual(digest(literal), row["literal_sha256"])
                # Inspect the bounded leaves independently of the candidate
                # detector. The fixed literal must survive the projection.
                found = False
                parts = defaultdict(dict)
                for leaf in index["leaves"]:
                    packed = (ROOT / leaf["path"]).read_bytes()
                    self.assertEqual(len(packed), leaf["bytes"])
                    self.assertEqual(digest(packed), leaf["sha256"])
                    decoded = gzip.decompress(packed)
                    self.assertLessEqual(len(decoded), 256 * 1024)
                    self.assertEqual(digest(decoded), leaf["decoded_sha256"])
                    for passage in json.loads(decoded)["passages"]:
                        parts[passage["id"]][passage["segment"]["ordinal"]] = passage["segment"]["text"]
                        for span in passage["source_spans"]:
                            if (span["page"] == row["page"] and span["start_utf8"] <= row["start_utf8"]
                                    and row["end_utf8"] <= span["end_utf8"]):
                                found = True
                self.assertTrue(found, "Source control is not covered by a passage")

    def test_initial_twelve_frozen_source_controls(self):
        self.check_group("initial", 12)

    def test_fresh_twenty_four_heldout_source_controls(self):
        self.check_group("heldout", 24)

    def test_full_census_and_scoped_ambiguity(self):
        counts = self.catalogue["counts"]
        self.assertEqual((counts["documents"], counts["pages"], counts["passages"],
                          counts["extraction_blocked_pages"]), (513, 19090, 53727, 893))
        self.assertEqual(counts["detected_occurrences"], counts["occurrences"])
        self.assertEqual(counts["unsupported_segments"], 0)
        for family, docid in (("dmg", "dmg-vol10-ch60"), ("adm", "adm-chapter-a1")):
            ref = self.docs[(family, docid)]
            index = json.loads((ROOT / ref["path"]).read_text())
            index_abbreviations = {(r["unit_id"], r["segment_ordinal"]): r["abbreviations"]
                                   for r in index["passages"]}
            for leaf in index["leaves"]:
                for passage in json.loads(gzip.decompress((ROOT / leaf["path"]).read_bytes()))["passages"]:
                    expected_abbreviations = sorted({o["literal"] for o in passage["occurrences"]
                                                     if o["role"] == "abbreviation"})
                    self.assertEqual(index_abbreviations[(passage["id"], passage["segment"]["ordinal"])],
                                     expected_abbreviations)
                    for card in passage["cards"]:
                        if card["kind"] == "expansion":
                            self.assertEqual(card["scope"]["target_document_id"], docid)
                    for footer in passage["reference_list_segments"]:
                        self.assertEqual(footer["body_occurrence_ids"], [])
                        self.assertEqual(footer["status"], "unresolved")

    def test_chat_pack_rejects_forged_current_card(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
                reading_help_chat, "CHAT_TMP_ROOT", Path(directory)):
            directory = Path(directory)
            pack_path, forged_path = directory / "pack.json", directory / "forged.json"
            export("dmg-vol10-ch60", 1, pack_path)
            pack = json.loads(pack_path.read_text())
            self.assertEqual(len(pack["requests"]), 1)
            passage = pack["passages"][pack["requests"][0]["passage_id"]]
            self.assertEqual(digest(passage["text"].encode()), passage["text_sha256"])
            pack["requests"][0]["card"]["status"] = "source_verified"
            forged_path.write_bytes(json.dumps(pack).encode())
            request = pack["requests"][0]
            reply = {"schema": pack["schema"], "request_id": request["request_id"],
                     "occurrence_id": request["occurrence"]["id"],
                     "literal_sha256": request["occurrence"]["literal_sha256"],
                     "status": "unresolved", "proposal": "Review required."}
            reply_path = directory / "reply.jsonl"
            reply_path.write_text(json.dumps(reply) + "\n")
            with self.assertRaisesRegex(ValueError, "Request/card/source passage differs"):
                import_replies(forged_path, digest(forged_path.read_bytes()), reply_path,
                               directory / "quarantine.jsonl")
            with self.assertRaisesRegex(ValueError, "Output must stay"):
                export("dmg-vol10-ch60", 1, ROOT / "source/forbidden.json")

    def test_cache_key_changes_with_reference_parser_and_support_table(self):
        ref = self.docs[("dmg", "dmg-vol10-ch60")]
        index = json.loads((ROOT / ref["path"]).read_text())
        producer = digest((ROOT / "scripts/build_reading_help_corpus.py").read_bytes())
        parser = digest((ROOT / "scripts/manual_references.py").read_bytes())
        helper = digest((ROOT / "scripts/build_logical_units.py").read_bytes())
        inputs = Inputs(ROOT)
        inventories = {family: json.loads(inputs.read(path)) for family, path in (
            ("dmg", "source/full-dmg-2026-09-15/inventory.json"),
            ("adm", "source/adm-2026-09-19/inventory.json"))}
        _, tables = abbreviation_tables(inputs, inventories)
        self.assertTrue(tables)
        original = rules_identity(producer, parser, helper, tables)
        self.assertEqual(original, index["rules_sha256"])
        self.assertNotEqual(original, rules_identity(producer, "c" * 64, helper, tables))
        self.assertNotEqual(original, rules_identity(producer, parser, "e" * 64, tables))
        changed = [{**tables[0], "extraction_sha256": "d" * 64}, *tables[1:]]
        self.assertNotEqual(original, rules_identity(producer, parser, helper, changed))
        self.assertFalse(cache_matches(index, rules_identity(producer, parser, helper, changed), index["extraction"]["sha256"],
                                       index["structured_document"]["sha256"]))


if __name__ == "__main__":
    unittest.main()
