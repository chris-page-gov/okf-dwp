"""Protect private inputs, safe rendering, stable routes and repeatable publication."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from build_learning_site import build, eligible, render, rewrite_link

COMMIT = "a" * 40


class LearningSiteTests(unittest.TestCase):
    def test_allowlist_excludes_private_and_corpus_content(self):
        for path in [".email.md", "docs/.email.md", "research/private.md", "source/pages/a.md", "full-dmg/index.md", "AGENTS.md"]:
            self.assertFalse(eligible(path), path)
        self.assertTrue(eligible("docs/learning-path.md"))

    def test_local_guide_and_fragment_rewritten(self):
        self.assertEqual(rewrite_link("glossary.md#scope", "docs/learning-path.md", {"docs/glossary.md"}, {"docs/glossary.md"}, COMMIT), "/okf-dwp/docs/glossary.html#scope")

    def test_evidence_links_remain_commit_bound(self):
        self.assertIn(f"/blob/{COMMIT}/evaluation/test.json", rewrite_link("../evaluation/test.json", "docs/learning-path.md", set(), {"evaluation/test.json"}, COMMIT))

    def test_raw_html_inert_and_anchors_retained(self):
        _, output = render("docs/a.md", '# Heading\n\n<a id="scope"></a>\n<script>alert(1)</script>\n\n[x](javascript:alert(1))', set(), set(), COMMIT)
        self.assertNotIn("<script>", output)
        self.assertNotIn('href="javascript:', output)
        self.assertIn('<a id="scope"></a>', output)

    def test_duplicate_heading_ids_are_distinct(self):
        _, output = render("docs/a.md", "# A\n\n## Scope\n\n## Scope\n", set(), set(), COMMIT)
        self.assertIn('id="scope"', output)
        self.assertIn('id="scope-1"', output)

    def test_build_only_reads_tracked_allowlist_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "docs").mkdir()
            for path in ["docs/learning-path.md", "docs/glossary.md", "NOTICE.md"]:
                (root / path).write_text("# Public\n")
                subprocess.run(["git", "add", path], cwd=root, check=True)
            (root / "docs/private.md").write_text("PRIVATE SECRET")
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "Fixture"], cwd=root, check=True)
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip()
            first = build(root, root / "site1", commit)
            second = build(root, root / "site2", commit)
            self.assertEqual(first, second)
            self.assertEqual(first["page_count"], 3)
            self.assertFalse((root / "site1/docs/private.html").exists())
            with self.assertRaisesRegex(ValueError, "fresh directory"):
                build(root, root / "site1", commit)
            (root / "NOTICE.md").write_text("Changed without a commit")
            with self.assertRaisesRegex(ValueError, "differs from the declared commit"):
                build(root, root / "site3", commit)


if __name__ == "__main__":
    unittest.main()
