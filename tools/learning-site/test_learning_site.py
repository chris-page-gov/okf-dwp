"""Protect private inputs, safe rendering, stable routes and repeatable publication."""
from pathlib import Path
import subprocess
import tempfile
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from build_learning_site import build, eligible, render, rewrite_link, normalise_table_alignment
import source_roles_diagram
from markdown_it.token import Token

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

    def test_directory_evidence_links_open_the_exact_tree(self):
        self.assertEqual(rewrite_link('../evaluation/cases/', 'docs/a.md', set(), {'evaluation/cases/a.json'}, COMMIT), f'https://github.com/chris-page-gov/okf-dwp/tree/{COMMIT}/evaluation/cases')

    def test_local_images_use_raw_commit_bound_assets(self):
        _, output = render('docs/a.md', '# A\n\n![Result](../validation/screenshot.png)', set(), {'validation/screenshot.png'}, COMMIT)
        self.assertIn(f'src="https://raw.githubusercontent.com/chris-page-gov/okf-dwp/{COMMIT}/validation/screenshot.png"', output)

    def test_named_mermaid_uses_local_static_image_on_pages(self):
        markdown = (Path(__file__).resolve().parents[2] / source_roles_diagram.MARKDOWN).read_text()
        _, output = render("docs/learning-path.md", markdown, set(), set(), COMMIT,
                           {source_roles_diagram.PUBLISHED_SVG})
        self.assertIn('src="/okf-dwp/assets/source-roles-diagram.svg"', output)
        self.assertIn("img-src 'self' https:", output)
        self.assertIn("How legislation, tribunal decisions", output)
        self.assertIn("<table>", output)
        self.assertNotIn("LAW[&quot;Legislation.gov.uk", output)
        _, other = render("docs/other.md", "# Other\n\n```mermaid\nflowchart TD\nA --> B\n```", set(), set(), COMMIT,
                          {source_roles_diagram.PUBLISHED_SVG})
        self.assertIn("flowchart TD", other)

    def test_static_diagram_bound_to_source_and_inert(self):
        root = Path(__file__).resolve().parents[2]
        markdown = (root / source_roles_diagram.MARKDOWN).read_text()
        svg = (root / source_roles_diagram.SVG).read_bytes()
        source_roles_diagram.check(markdown, svg)
        with self.assertRaisesRegex(ValueError, "differs from the Mermaid source"):
            source_roles_diagram.check(markdown.replace("may seek advice", "asks for advice"), svg)
        with self.assertRaisesRegex(ValueError, "active or external"):
            source_roles_diagram.check(markdown, svg.replace(b"</svg>", b"<script>alert(1)</script></svg>"))

    def test_raw_html_inert_and_anchors_retained(self):
        _, output = render("docs/a.md", '# Heading\n\n<a id="scope"></a>\n<script>alert(1)</script>\n\n[x](javascript:alert(1))', set(), set(), COMMIT)
        self.assertNotIn("<script>", output)
        self.assertNotIn('href="javascript:', output)
        self.assertIn('<a id="scope"></a>', output)

    def test_table_alignment_preserves_meaning_without_inline_styles(self):
        text = "# Figures\n\n| Left | Centre | Right | Default |\n| :--- | :---: | ---: | --- |\n| 1 | 2 | 3 | 4 |\n"
        _, output = render("docs/a.md", text, set(), set(), COMMIT)
        self.assertNotIn(' style=', output)
        for alignment in ("left", "center", "right"):
            self.assertIn(f'<th class="table-align-{alignment}">', output)
            self.assertIn(f'<td class="table-align-{alignment}">', output)
        self.assertIn('<th>Default</th>', output)
        self.assertIn("style-src 'self'", output)
        self.assertNotIn("unsafe-inline", output)

    def test_unexpected_table_styles_fail_closed(self):
        for style in ("text-align:justify", "text-align:right;color:red", "background:url(https://example.invalid)", ""):
            with self.subTest(style=style):
                token = Token("td_open", "td", 1, attrs={"style": style})
                with self.assertRaisesRegex(ValueError, "Unsupported table alignment"):
                    normalise_table_alignment(token)

    def test_table_alignment_retains_existing_classes(self):
        token = Token("th_open", "th", 1, attrs={"style": "text-align:right", "class": "existing"})
        normalise_table_alignment(token)
        self.assertEqual(token.attrs, {"class": "existing table-align-right"})

    def test_duplicate_heading_ids_are_distinct(self):
        _, output = render("docs/a.md", "# A\n\n## Scope\n\n## Scope\n", set(), set(), COMMIT)
        self.assertIn('id="scope"', output)
        self.assertIn('id="scope-1"', output)

    def test_build_only_reads_tracked_allowlist_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "config", "gc.auto", "0"], cwd=root, check=True)
            subprocess.run(["git", "config", "maintenance.auto", "false"], cwd=root, check=True)
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

# Synthetic archives exercise publication admission, not DWP legal conclusions.
import copy
import hashlib
import json
import os
from build_learning_site import bounded_regular, retained_examples, strict_json, utf16_length, verify_context_budget


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def ref(path, raw):
    return {'path': path, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def archive_fixture(root, *, wrong_catalogue=False, missing_reference=False, extra_file=False, budget_change=None):
    """One selected Unicode record with an exact original package and all read sections."""
    record = {'id': 'urn:example:record', 'label': 'Synthetic evidence', 'kind': 'Guidance',
              'assertion_status': 'normalised', 'text': 'Synthetic 😀 source text; not advice.',
              'authority': {'class': 'derived'}, 'provenance': [{'url': 'https://example.invalid/source', 'locator': 'Page 1'}]}
    item = {'record': record, 'reasons': ['Synthetic control'], 'paths': []}
    context = {'schema': 'okf-governed-context.v1', 'question': 'A synthetic question?',
               'context_id': 'urn:sha256:' + '1' * 64, 'bundle': {'id': 'fixture', 'version': 'test'},
               'binding': {'index_sha256': '2' * 64}, 'budget': {'max_bytes': 524288, 'used_bytes': 0, 'truncated': True, 'max_nodes': 10, 'max_relationships': 10, 'max_depth': 2, 'used_nodes': 1, 'used_relationships': 0, 'reached_depth': 0},
               'selected': [item], 'relationships': [], 'evidence_status': 'insufficient', 'ai_answer': None,
               'missing_evidence': [{'code': 'synthetic_gap', 'message': 'Not established'}]}
    context['budget'].update(budget_change or {})
    for _ in range(5):
        context['budget']['used_bytes'] = len(encoded(context))
    package = encoded(context)
    folder = hashlib.sha256(package).hexdigest()
    files = {}

    def data(value):
        raw = encoded(value)
        digest = hashlib.sha256(raw).hexdigest()
        files[f'{folder}/data/{digest}.json'] = raw
        return {'sha256': digest, 'bytes': len(raw)}

    def stream(value, section, record_id=None):
        text = value if isinstance(value, str) else encoded(value).decode()
        return [data({'schema': 'okf-context-read.v1', 'context_id': context['context_id'],
                     'evidence_status': 'insufficient', 'ai_answer': None, 'section': section,
                     'record_id': record_id, 'character_unit': 'utf-16-code-units', 'data': text,
                     'offset': 0, 'end_offset': utf16_length(text), 'next_offset': None,
                     'total_characters': utf16_length(text), 'content_sha256': hashlib.sha256(text.encode()).hexdigest()})]

    metadata = copy.deepcopy(item)
    del metadata['record']['text']
    metadata['record']['text_reference'] = {'section': 'record_text', 'characters': utf16_length(record['text']), 'sha256': hashlib.sha256(record['text'].encode()).hexdigest()}
    record_index = data([{'id': record['id'], 'text': stream(record['text'], 'record_text', record['id']),
                         'metadata': stream(metadata, 'record_metadata', record['id'])}])
    catalogue_row = {'id': record['id'], 'label': record['label'], 'kind': record['kind'],
                     'assertion_status': 'normalised', 'text_characters': utf16_length(record['text']),
                     'text_sha256': hashlib.sha256(record['text'].encode()).hexdigest(),
                     'source_url': 'https://wrong.invalid/' if wrong_catalogue else record['provenance'][0]['url'],
                     'source_locator': 'Page 1', 'authority_class': 'derived', 'review_status': 'not-declared', 'reasons': 1, 'paths': 0}
    catalogue = data({'schema': 'okf-context-manifest.v1', 'context_id': context['context_id'], 'question': context['question'],
                      'bundle': context['bundle'], 'binding': context['binding'], 'evidence_status': 'insufficient',
                      'records': [catalogue_row], 'delivery': {'offset': 0, 'returned': 1, 'total': 1, 'next_offset': None}})
    diagnostics = {k: v for k, v in context.items() if k not in {'selected', 'relationships'}}
    diagnostics.update(selected_records=1, relationship_count=0)
    sections = {'package': stream(package.decode(), 'package'), 'relationships': stream([], 'relationships'),
                'diagnostics': stream(diagnostics, 'diagnostics')}
    if missing_reference:
        sections['package'][0]['sha256'] = '0' * 64
    original_path = 'evaluation/examples/input.json'
    receipt_path = 'validation/examples/receipt.json'
    receipt = b'{"synthetic":true}\n'
    package_ref = {**ref(original_path, package), 'encoding': 'json', 'canonical_bytes': len(package), 'canonical_sha256': folder}
    entry = {'id': 'synthetic-control', 'title': 'Synthetic control', 'package': package_ref,
             'receipt': ref(receipt_path, receipt), 'question_sha256': hashlib.sha256(context['question'].encode()).hexdigest(),
             'source_version': 'synthetic-v1', 'engine_id': None, 'original_engine_id': None,
             'observation_kind': 'synthetic', 'approved_publication': True, 'publication_note': 'Test fixture only.'}
    descriptor = {k: v for k, v in entry.items() if k not in {'package', 'receipt', 'approved_publication'}}
    descriptor.update(schema='okf-context-archive.v1', question=context['question'], context_id=context['context_id'],
                      package_sha256=folder, package_bytes=len(package), bundle=context['bundle'], binding=context['binding'],
                      input_receipt=entry['receipt'], evidence_status='insufficient', ai_answer=None, budget=context['budget'],
                      counts={'records': 1, 'relationships': 0}, catalogues=[catalogue], record_indexes=[record_index], sections=sections,
                      limits={}, notice='Synthetic retained example.')
    files[f'{folder}/descriptor.json'] = encoded(descriptor)
    files[f'{folder}/package.json'] = package
    if extra_file:
        files[f'{folder}/data/' + '3' * 64 + '.json'] = b'{}'
    row = {'id': entry['id'], 'title': entry['title'], 'path': f'{folder}/descriptor.json',
           'descriptor': {k: v for k, v in ref('', encoded(descriptor)).items() if k != 'path'},
           'package_sha256': folder, 'evidence_status': 'insufficient', 'observation_kind': 'synthetic',
           'files': len(files), 'bytes': sum(map(len, files.values()))}
    registry = encoded({'schema': 'okf-context-archive-registry.v1', 'cases': [entry]})
    registry_path = 'evaluation/examples/registry.json'
    index = encoded({'schema': 'okf-context-archive-index.v1', 'registry_sha256': hashlib.sha256(registry).hexdigest(), 'cases': [row]})
    files['index.json'] = index
    files['index.html'] = f'<meta name="okf-archive-index" content="{hashlib.sha256(index).hexdigest()}:{len(index)}">'.encode()
    exporter = []
    for name in ('reader.mjs', 'shared.mjs', 'reader.css'):
        files[name] = b'/* Synthetic test asset. */'
        exporter.append(ref('tools/context-archive/' + name, files[name]))
    manifest = encoded({'schema': 'okf-context-archive-artifacts.v1', 'registry_sha256': hashlib.sha256(registry).hexdigest(),
                        'exporter_files': exporter, 'files': [ref(path, raw) for path, raw in sorted(files.items())]})
    prefix = 'evidence-examples/synthetic-test'
    approval = {'schema': 'okf-dwp-retained-evidence-publication.v1', 'releases': [
        {'id': 'synthetic-test', 'archive_root': prefix, 'registry': ref(registry_path, registry),
         'artifact_manifest': ref(prefix + '/artifact-manifest.json', manifest),
         'exporter': {'repository': 'https://github.com/chris-page-gov/okf-explorer', 'commit': 'a' * 40, 'files': exporter},
         'approved_publication': True, 'publication_note': 'Synthetic control, not public evidence.'}]}
    source = {original_path: package, receipt_path: receipt, registry_path: registry,
              'evidence-examples/registry.json': encoded(approval), prefix + '/artifact-manifest.json': manifest,
              **{prefix + '/' + p: raw for p, raw in files.items()}}
    for path, raw in source.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    return source, approval


class RetainedEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        # No background Git process may race deletion of an ephemeral fixture.
        subprocess.run(['git', 'config', 'gc.auto', '0'], cwd=self.root, check=True)
        subprocess.run(['git', 'config', 'maintenance.auto', 'false'], cwd=self.root, check=True)
        for path in ('docs/learning-path.md', 'docs/glossary.md', 'NOTICE.md'):
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('# Public\n\n[Example](../evidence-examples/synthetic-test/index.html#synthetic-control)\n')

    def commit(self):
        subprocess.run(['git', 'add', '.'], cwd=self.root, check=True)
        subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'Synthetic publication fixture'], cwd=self.root, check=True)
        return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=self.root).decode().strip()

    def test_archive_is_copied_byte_exact_and_manifest_bound(self):
        source, _ = archive_fixture(self.root)
        commit = self.commit()
        manifest = build(self.root, self.root / 'site', commit)
        self.assertEqual(manifest['schema'], 'okf-dwp-learning-site.v2')
        self.assertEqual(manifest['retained_evidence']['releases'][0]['cases'], 1)
        for path, raw in source.items():
            if path.startswith('evidence-examples/synthetic-test/'):
                self.assertEqual((self.root / 'site' / path).read_bytes(), raw)
        html = (self.root / 'site/docs/learning-path.html').read_text()
        self.assertIn('/okf-dwp/evidence-examples/synthetic-test/index.html#synthetic-control', html)
        self.assertFalse((self.root / 'site/evaluation').exists())
        self.assertFalse((self.root / 'site/validation').exists())
        self.assertEqual(manifest, build(self.root, self.root / 'second', commit))

    def test_tampered_catalogue_source_rejected_even_with_new_hashes(self):
        archive_fixture(self.root, wrong_catalogue=True)
        commit = self.commit()
        with self.assertRaisesRegex(ValueError, 'catalogue record metadata'):
            build(self.root, self.root / 'site', commit)
        self.assertFalse((self.root / 'site').exists())

    def test_missing_resource_rejected(self):
        archive_fixture(self.root, missing_reference=True)
        with self.assertRaisesRegex(ValueError, 'missing referenced resource'):
            build(self.root, self.root / 'site', self.commit())

    def test_unreferenced_archive_file_rejected(self):
        archive_fixture(self.root, extra_file=True)
        with self.assertRaisesRegex(ValueError, 'unreferenced files'):
            build(self.root, self.root / 'site', self.commit())

    def test_unknown_approval_fields_rejected(self):
        _, approval = archive_fixture(self.root)
        approval['allow_any_json'] = True
        (self.root / 'evidence-examples/registry.json').write_bytes(encoded(approval))
        with self.assertRaisesRegex(ValueError, 'unknown or missing'):
            build(self.root, self.root / 'site', self.commit())

    def test_unapproved_release_rejected(self):
        _, approval = archive_fixture(self.root)
        approval['releases'][0]['approved_publication'] = False
        (self.root / 'evidence-examples/registry.json').write_bytes(encoded(approval))
        with self.assertRaisesRegex(ValueError, 'explicit approval'):
            build(self.root, self.root / 'site', self.commit())

    def test_external_or_traversing_root_rejected(self):
        _, approval = archive_fixture(self.root)
        approval['releases'][0]['archive_root'] = '../source'
        (self.root / 'evidence-examples/registry.json').write_bytes(encoded(approval))
        with self.assertRaisesRegex(ValueError, 'archive root'):
            build(self.root, self.root / 'site', self.commit())

    def test_changed_tracked_archive_bytes_rejected(self):
        archive_fixture(self.root)
        commit = self.commit()
        (self.root / 'evidence-examples/synthetic-test/reader.mjs').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'differs from the declared commit'):
            build(self.root, self.root / 'site', commit)

    def test_symlinked_member_and_parent_rejected_before_read(self):
        target = self.root / 'regular.json'
        target.write_text('{}')
        (self.root / 'linked.json').symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'must be regular'):
            bounded_regular(self.root, 'linked.json', 100)
        (self.root / 'linked-directory').symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'regular directory'):
            bounded_regular(self.root, 'linked-directory/regular.json', 100)
        with self.assertRaisesRegex(ValueError, 'regular directory'):
            bounded_regular(self.root / 'linked-directory', 'regular.json', 100)

    def test_oversized_member_and_fifo_rejected_before_open(self):
        (self.root / 'large.json').write_bytes(b' ' * 101)
        with self.assertRaisesRegex(ValueError, 'at most 100'):
            bounded_regular(self.root, 'large.json', 100)
        os.mkfifo(self.root / 'pipe.json')
        with self.assertRaisesRegex(ValueError, 'must be regular'):
            bounded_regular(self.root, 'pipe.json', 100)

    def test_package_budget_cross_fields_reject_rehashed_invalid_values(self):
        for change in ({'used_nodes': 0}, {'used_relationships': 1}, {'max_nodes': 999}, {'max_relationships': 9999}, {'max_depth': 9}, {'reached_depth': 3}, {'max_bytes': 100}):
            with self.subTest(change=change):
                archive_fixture(self.root, budget_change=change)
                with self.assertRaisesRegex(ValueError, 'package budget'):
                    build(self.root, self.root / 'site', self.commit())

    def test_selected_path_must_respect_declared_depth(self):
        source, _ = archive_fixture(self.root)
        context = strict_json(source['evaluation/examples/input.json'])
        context['selected'][0]['paths'] = [{'records': ['a', 'b', 'c', 'd'], 'assertions': ['ab', 'bc', 'cd']}]
        for _ in range(5):
            context['budget']['used_bytes'] = len(encoded(context))
        with self.assertRaisesRegex(ValueError, 'traversal exceeds'):
            verify_context_budget(context, encoded(context))

    def test_oversized_approval_manifest_rejected_before_parsing(self):
        archive_fixture(self.root)
        (self.root / 'evidence-examples/registry.json').write_bytes(b' ' * 65537)
        with self.assertRaisesRegex(ValueError, 'at most 65536'):
            build(self.root, self.root / 'site', self.commit())

    def test_duplicate_and_nonfinite_json_rejected(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}', b'{"a":1e999}', b'{"a":-1e999}'):
            with self.assertRaises(ValueError):
                strict_json(raw)

    def test_untracked_registry_is_not_published(self):
        commit = self.commit()
        archive_fixture(self.root)
        result = build(self.root, self.root / 'site', commit)
        self.assertEqual(result['schema'], 'okf-dwp-learning-site.v1')
        self.assertFalse((self.root / 'site/evidence-examples').exists())


if __name__ == "__main__":
    unittest.main()
