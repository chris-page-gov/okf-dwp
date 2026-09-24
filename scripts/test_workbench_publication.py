"""Public workbench publishing must not admit private or unbound resources."""
import hashlib
import json
import unittest
from workbench_publication import MANIFEST, QUESTIONS, CORPUS, PREFIX, publish_workbench


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


class WorkbenchPublicationTests(unittest.TestCase):
    def setUp(self):
        self.context = {"schema": "okf-governed-context.v1", "question": "Public synthetic question?",
                        "context_id": "urn:sha256:" + "a" * 64, "evidence_status": "insufficient", "ai_answer": None,
                        "budget": {"truncated": False},
                        "selected": [{"record": {"access": "public", "text": "Public source"}}]}
        raw = encoded(self.context)
        digest = hashlib.sha256(raw).hexdigest()
        part = {"schema": "okf-context-read.v1", "section": "package", "record_id": None,
                "context_id": self.context["context_id"], "content_sha256": digest,
                "evidence_status": "insufficient", "ai_answer": None, "character_unit": "utf-16-code-units",
                "media_type": "application/json", "total_characters": len(raw),
                "context_truncated": False, "retrieval_truncated": False,
                "delivery": {"used_bytes": 0, "max_bytes": 32768},
                "offset": 0, "end_offset": len(raw), "next_offset": None, "data": raw.decode()}
        while part["delivery"]["used_bytes"] != len(encoded(part)):
            part["delivery"]["used_bytes"] = len(encoded(part))
        part_raw = encoded(part)
        self.manifest = {"schema": "okf-evidence-workbench.v1", "questions": [{"id": "staff-001",
            "question": self.context["question"], "package": {"url": "packages/staff-001.json", "sha256": digest,
                "parts": [{"url": "parts/staff-001-0.json", "bytes": len(part_raw), "sha256": hashlib.sha256(part_raw).hexdigest()}]}}]}
        self.files = {QUESTIONS: encoded({"cases": [{"id": "staff-001", "question": self.context["question"]}]}),
                      PREFIX + "packages/staff-001.json": raw, PREFIX + "parts/staff-001-0.json": part_raw,
                      CORPUS: b"{}", ".email.md": b"Private correspondence", PREFIX + "unlisted.json": b"Private working notes"}
        self.manifest["source"] = {"registry": QUESTIONS, "registry_sha256": hashlib.sha256(self.files[QUESTIONS]).hexdigest(),
                                   "corpus": CORPUS, "corpus_sha256": hashlib.sha256(self.files[CORPUS]).hexdigest()}

    def run_publish(self):
        self.files[MANIFEST] = encoded(self.manifest)
        def read(path, cap):
            raw = self.files[path]
            if len(raw) > cap:
                raise ValueError("size limit")
            return raw
        # The site's duplicate-key JSON parser has its own isolated renderer tests.
        return publish_workbench(read, self.files, json.loads, lambda context, raw: None)

    def test_only_declared_fixed_question_and_bound_files_are_published(self):
        files, receipt = self.run_publish()
        self.assertEqual(receipt["questions"], 1)
        self.assertEqual(set(files), {MANIFEST, PREFIX + "packages/staff-001.json", PREFIX + "parts/staff-001-0.json"})
        self.assertNotIn(".email.md", files)
        self.assertNotIn(PREFIX + "unlisted.json", files)

    def test_private_escaping_and_remote_references_are_rejected(self):
        for path in ["../.email.md", ".email.md", "https://example.com/package.json", "/etc/passwd", "parts/%2e%2e/x", "parts//x", "parts/foo.html"]:
            with self.subTest(path=path):
                self.manifest["questions"][0]["package"]["url"] = path
                with self.assertRaisesRegex(ValueError, "reference"):
                    self.run_publish()

    def test_question_changes_and_missing_occurrences_are_rejected(self):
        self.manifest["questions"][0]["question"] = "New unapproved question"
        with self.assertRaisesRegex(ValueError, "wording"):
            self.run_publish()
        self.manifest["questions"] = []
        with self.assertRaisesRegex(ValueError, "census"):
            self.run_publish()

    def test_tampered_package_rejected(self):
        self.files[PREFIX + "packages/staff-001.json"] += b" "
        with self.assertRaisesRegex(ValueError, "hash"):
            self.run_publish()

    def test_false_source_identity_rejected(self):
        self.manifest["source"]["registry_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash"):
            self.run_publish()

    def test_restricted_or_unspecified_record_access_rejected(self):
        for access in ["restricted", None]:
            with self.subTest(access=access):
                self.context["selected"][0]["record"]["access"] = access
                raw = encoded(self.context)
                self.files[PREFIX + "packages/staff-001.json"] = raw
                self.manifest["questions"][0]["package"]["sha256"] = hashlib.sha256(raw).hexdigest()
                with self.assertRaisesRegex(ValueError, "explicitly public"):
                    self.run_publish()

    def test_incomplete_browser_delivery_metadata_rejected(self):
        part_path = PREFIX + "parts/staff-001-0.json"
        part = json.loads(self.files[part_path])
        part.pop("delivery")
        self.files[part_path] = encoded(part)
        ref = self.manifest["questions"][0]["package"]["parts"][0]
        ref.update(bytes=len(self.files[part_path]), sha256=hashlib.sha256(self.files[part_path]).hexdigest())
        with self.assertRaisesRegex(ValueError, "delivery byte count"):
            self.run_publish()

    def test_missing_and_repeated_parts_rejected(self):
        parts = self.manifest["questions"][0]["package"]["parts"]
        self.manifest["questions"][0]["package"]["parts"] = []
        with self.assertRaisesRegex(ValueError, "parts"):
            self.run_publish()
        self.manifest["questions"][0]["package"]["parts"] = parts * 2
        with self.assertRaisesRegex(ValueError, "continuation"):
            self.run_publish()


if __name__ == "__main__":
    unittest.main()
