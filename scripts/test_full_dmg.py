"""Controls for full-text fidelity, bounded partitioning and stable source IDs."""
from copy import deepcopy
import json
import gzip
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from build_full_dmg import (ROOT, build_search, canonical, check_full_relation, deterministic_gzip,
                            compile_full, digest, page_routes, referenced_publication_date, source_dates, tokens)
from validate_full_dmg import validate
from evaluate_full_dmg import IndexedEvidence


def record(route, title="Example"):
    return {"route": route, "name": route, "title": title, "publisher": "dwp", "publisher_title": "DWP",
            "resource_count": 1, "formats": ["PDF"], "tags": ["Memo — applicability unreviewed"], "topics": [],
            "notes": "A short display snippet", "record_type": "Source PDF page", "source_tier": "official-source-unreviewed-extraction",
            "source_adapter": "frozen-pdf", "timestamp": "", "license_id": "uk-ogl", "license_title": "OGL",
            "source_role": "Memo — applicability unreviewed", "volume": "Reference/memo", "document_id": "memo-a"}


class FullDmgTests(unittest.TestCase):
    def test_gzip_header_is_not_host_specific(self):
        raw = b"Portable indexed corpus control" * 100
        result = deterministic_gzip(raw)
        self.assertEqual(result[:10], b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff")
        self.assertEqual(gzip.decompress(result), raw)
        self.assertEqual(result, deterministic_gzip(raw))

    def test_isolated_pipeline_and_changed_source_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            pdf, text = b"synthetic PDF bytes for integrity control", "Fixture introduction. " + "padding " * 70 + "lateuniquetoken"
            url, when = "https://example.test/fixture.pdf", "2026-09-15T19:00:00Z"
            (source / "fixture.pdf").write_bytes(pdf)
            (source / "fixture.txt").write_text(text)
            pages = {"source_sha256": digest(pdf), "pages": [{"page": 1, "url": url + "#page=1", "text": text}]}
            (source / "fixture.json").write_bytes(canonical(pages))
            doc = {"id": "fixture-memo", "title": "Synthetic test memo", "url": url, "role": "memo", "volume": None,
                   "chapter": None, "pages": 1, "size_bytes": len(pdf), "observed_at": when, "extraction_observed_at": "2026-09-15T19:00:01Z",
                   "pdf_path": "source/fixture.pdf", "text_path": "source/fixture.txt", "pages_path": "source/fixture.json",
                   "sha256": digest(pdf), "text_sha256": digest(text.encode()), "pages_sha256": digest(canonical(pages))}
            (source / "inventory.json").write_bytes(canonical({"documents": [doc], "generated_at": "2026-09-15T19:00:02Z"}))
            profiles = root / "profiles/bundle-wiki/v1"
            profiles.mkdir(parents=True)
            for name in ("bundle.schema.json", "semantic-assertion.schema.json"):
                (profiles / name).write_bytes((ROOT / "profiles/bundle-wiki/v1" / name).read_bytes())
            outputs = compile_full(root, "source/inventory.json", include_pilot=False)
            self.assertEqual(json.loads(outputs['okf-explorer.json'])['source']['observed_at'], when)
            self.assertEqual(outputs, compile_full(root, "source/inventory.json", include_pilot=False))
            for path, data in outputs.items():
                target = root / "full-dmg" / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            result = validate(root, inventory_path="source/inventory.json")
            index = IndexedEvidence(root / "full-dmg")
            matches = index.search("lateuniquetoken", "fixture-memo")
            self.assertEqual(len(matches), 1)
            self.assertEqual(index.search("lateuniquetoken", "different-benefit"), [])
            self.assertEqual(index.search("unavailableclaimantdetails"), [])
            index.verify_passage(matches[0]["route"], text, digest(pdf))
            with self.assertRaisesRegex(ValueError, "passage"):
                index.verify_passage(matches[0]["route"], "Invented entitlement", digest(pdf))
            with self.assertRaisesRegex(ValueError, "passage"):
                index.verify_passage(matches[0]["route"], "[Verify the original PDF page 1](https://example.test/fixture.pdf#page=1)", digest(pdf))
            with self.assertRaisesRegex(ValueError, "identity"):
                index.verify_passage(matches[0]["route"], text, "0" * 64)
            self.assertEqual(result["checks"]["source_documents"], 1)
            self.assertEqual(result["checks"]["measured_pages"], 1)
            self.assertTrue(result["checks"]["all_rdf_shards_recomputed"])
            (source / "fixture.pdf").write_bytes(pdf + b"changed")
            with self.assertRaisesRegex(ValueError, "PDF byte count"):
                validate(root, inventory_path="source/inventory.json")

    def test_search_indexes_late_source_text_without_capping_postings(self):
        rows = [record(f"page/memo-{i}/0001") for i in range(2050)]
        texts = {row["route"]: "Introduction " + "x " * 300 + "lateuniquetoken café co-operate" for row in rows}
        files = {}
        result = build_search(rows, texts, "fixture", lambda path, value: files.__setitem__(path, deepcopy(value)))
        self.assertEqual(len(result["postings"]["lateuniquetoken"]), 2050)
        self.assertEqual(result["manifest"]["counts"]["postings"], result["manifest"]["counts"]["uncapped_postings"])
        self.assertNotIn("lateuniquetoken", result["results"][0]["notes"])
        self.assertEqual(tokens("Café co-operate THE"), ["cafe", "co", "operate"])

    def test_postings_partitions_keep_every_token(self):
        rows = [record("page/memo/0001")]
        files = {}
        text = " ".join("al" + str(i) for i in range(100))
        with patch("build_full_dmg.MAX_BYTES", 180):
            result = build_search(rows, {rows[0]["route"]: text}, "fixture", lambda path, value: files.__setitem__(path, deepcopy(value)))
        paths = result["manifest"]["entrypoints"]["postings"]
        self.assertGreater(len(paths), 1)
        emitted = [token for path in paths for token in files[path]["tokens"]]
        self.assertEqual(len(emitted), len(set(emitted)))
        self.assertTrue(set(tokens(text)).issubset(emitted))

    def test_reused_sources_preserve_routes_and_changed_bytes_fail(self):
        original = {"https://example.test/dmg.pdf": {"chapter": 84, "sha256": "a"}}
        doc = {"id": "dmg-vol14-ch84", "chapter": 84, "url": "https://example.test/dmg.pdf", "sha256": "a"}
        self.assertEqual(page_routes(doc, {"chapter/84": {}}, original), ("chapter/84", True))
        with self.assertRaisesRegex(ValueError, "Original source bytes changed"):
            page_routes({**doc, "sha256": "b"}, {"chapter/84": {}}, original)
        self.assertEqual(page_routes({**doc, "id": "dmg-vol2-ch7-part1", "url": "https://example.test/part1.pdf"}, {}, original), ("document/dmg-vol2-ch7-part1", False))

    def test_capture_and_listing_dates_do_not_become_publication(self):
        date = "2026-09-15T19:45:13Z"
        value = source_dates({"id": "memo", "observed_at": date, "publication_updated_at": "2026-07-01", "http": {"last_modified": "2026-06-01"}})
        self.assertEqual(value["captured_at"], date)
        self.assertEqual(value["publication_date_status"], "not-established-from-document-evidence")
        self.assertNotIn("published_at", value)
        self.assertEqual(referenced_publication_date({'schema:about': {'schema:datePublished': {'@value': '2026-04', '@type': 'xsd:gYearMonth'}}}), '2026-04')
        self.assertEqual(referenced_publication_date({'captured_at': date}), '')
        self.assertEqual(referenced_publication_date({'schema:about': {'schema:datePublished': {'@value': '2026-99', '@type': 'xsd:gYearMonth'}}}), '')

    def test_leading_zero_paragraph_evidence_is_checked_exactly(self):
        quote = "01001 This is an exact paragraph statement from the source."
        source, target = {"route": "term/a", "type": "Concept"}, {"route": "term/b", "type": "Concept"}
        nodes = {"term/b": target, "page/dmg-vol1-ch1/0001": {"type": "Source PDF page", "body": quote, "chapter": 1, "page_number": 1}}
        spec = {"target": "term/b", "predicate": "http://www.w3.org/2004/02/skos/core#related", "rationale": "Source-backed relationship proposal",
                "evidence": [{"page": "page/dmg-vol1-ch1/0001", "quote": quote, "locator": "DMG 01001"}]}
        self.assertEqual(check_full_relation(spec, source, nodes), target)

        spec["evidence"][0]["locator"] = "DMG 01002"
        with self.assertRaisesRegex(ValueError, "Paragraph locator"):
            check_full_relation(spec, source, nodes)

    def test_six_digit_international_locators_preserve_width(self):
        quote = "071700 This is an exact statement from the international source.\n071701 This is its next paragraph."
        source, target = {"route": "term/a", "type": "Concept"}, {"route": "term/b", "type": "Concept"}
        page = {"type": "Source PDF page", "body": quote, "chapter": 7, "page_number": 1}
        nodes = {"term/b": target, "page/international/0001": page}
        spec = {"target": "term/b", "predicate": "http://www.w3.org/2004/02/skos/core#related", "rationale": "Scoped association", "evidence": [{"page": "page/international/0001", "quote": quote, "locator": "DMG 071700–071701"}]}
        self.assertEqual(check_full_relation(spec, source, nodes), target)
        page['chapter'] = 1
        with self.assertRaisesRegex(ValueError, 'width'):
            check_full_relation(spec, source, nodes)

    def test_wrapped_range_is_not_semantic_paragraph_evidence(self):
        quote = '51006 - 51008 and DMG 51080 describe an exception elsewhere.'
        source, target = {'route':'term/a','type':'Concept'}, {'route':'term/b','type':'Concept'}
        nodes = {'term/b':target, 'page/ch51/0003':{'type':'Source PDF page','body':quote,'chapter':51,'page_number':3}}
        spec = {'target':'term/b','predicate':'http://www.w3.org/2004/02/skos/core#related','rationale':'Scoped association','evidence':[{'page':'page/ch51/0003','quote':quote,'locator':'DMG 51006'}]}
        with self.assertRaisesRegex(ValueError, 'Paragraph locator'):
            check_full_relation(spec, source, nodes)

    def test_quotation_led_paragraph_body_is_supported(self):
        quote = '42320 “Substantial” is not defined in the relevant regulations.'
        source, target = {'route':'term/a','type':'Concept'}, {'route':'term/b','type':'Concept'}
        nodes = {'term/b':target, 'page/ch42/0001':{'type':'Source PDF page','body':quote,'chapter':42,'page_number':1}}
        spec = {'target':'term/b','predicate':'http://www.w3.org/2004/02/skos/core#related','rationale':'Scoped association','evidence':[{'page':'page/ch42/0001','quote':quote,'locator':'DMG 42320'}]}
        self.assertEqual(check_full_relation(spec, source, nodes), target)

        quote = '42320 (See DMG memo 13-22) A decision cannot be revised in this example.'
        nodes['page/ch42/0001']['body'] = quote
        spec['evidence'][0]['quote'] = quote
        self.assertEqual(check_full_relation(spec, source, nodes), target)


if __name__ == "__main__":
    unittest.main()
