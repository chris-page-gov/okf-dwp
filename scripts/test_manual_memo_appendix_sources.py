"""Independent frozen-source controls for memo citations and appendix boundaries.

These controls were prepared concurrently with a repair prompted by the complete
corpus outlier census. They are regression evidence, not a blinded experiment or
specialist acceptance. Source instructions remain inert.
"""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / 'evaluation/manual-structure/auxiliary-review/memo-appendix-follow-on/source-fixtures.json'
FIXTURES = json.loads(FIXTURE_PATH.read_text())['fixtures']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class MemoAppendixSourceControls(unittest.TestCase):
    def source(self, fixture):
        raw = (ROOT / fixture['record_path']).read_bytes()
        self.assertEqual(sha(raw), fixture['record_sha256'])
        document = json.loads(raw)
        raw = (ROOT / fixture['pages_path']).read_bytes()
        self.assertEqual(sha(raw), fixture['pages_sha256'])
        extraction = json.loads(raw)
        self.assertEqual(extraction['source_sha256'], fixture['pdf_sha256'])
        self.assertEqual(sha((ROOT / fixture['pdf_path']).read_bytes()), fixture['pdf_sha256'])
        self.assertEqual(document['kind'], fixture['source_kind'])
        self.assertEqual(document['role'], fixture['source_role'])
        return document, extraction['pages']

    def partition(self, units, pages):
        for page in pages:
            spans = sorted((span for unit in units for span in unit['spans']
                            if span['page'] == page['page']), key=lambda s: s['start_utf8'])
            cursor, raw = 0, page['text'].encode()
            for span in spans:
                self.assertEqual(span['start_utf8'], cursor)
                self.assertEqual(sha(raw[cursor:span['end_utf8']]), span['literal_sha256'])
                cursor = span['end_utf8']
            self.assertEqual(cursor, len(raw))

    def test_memo_reference_is_not_main_numbering(self):
        from manual_structure import segment_source
        f = FIXTURES[0]
        document, pages = self.source(f)
        context = f['expected_reference_context']
        literal = pages[f['source_page'] - 1]['text'].encode()[context['start_utf8']:context['end_utf8']]
        self.assertEqual(literal.decode(), context['literal'])
        self.assertEqual(sha(literal), context['literal_sha256'])
        units, structure = segment_source('adm', document, pages)
        self.assertEqual([label for unit in units for label in unit['paragraph_labels']], [])
        self.assertTrue(any(context['literal'] in unit['text'] for unit in units))
        self.assertTrue(any(ref.get('target_label') == f['expected_reference_label']
                            for unit in units for ref in unit['references']))
        self.assertTrue(any(r['label'] == f['forbidden_main_label'] and
                            r['reason'] == 'chapter-number-in-memo-is-reference-or-quotation-not-main-numbering'
                            for r in structure['rejected_number_lines']))
        self.partition(units, pages)

    def test_memo_annotations_and_source_headings_remain_separate(self):
        from manual_structure import segment_source
        f = FIXTURES[0]
        document, pages = self.source(f)
        units, structure = segment_source('adm', document, pages)
        annotations = [unit for unit in units if unit['role'] == 'annotation']
        self.assertTrue(annotations)
        self.assertTrue(all(span['page'] == f['annotation_page'] for u in annotations for span in u['spans']))
        refs = [ref for unit in annotations for ref in unit['references'] if ref['kind'] == 'update-annotation']
        self.assertTrue(set(f['annotation_labels']) <= {ref['target_label'] for ref in refs})
        self.assertTrue(all(ref['legal_dependency'] == 'not-established' for ref in refs))
        for heading in ('Introduction', 'Background – EU Social Security Coordination'):
            self.assertTrue(any(unit['role'] == 'section' and heading in unit['heading_path']
                                and unit['spans'][0]['page'] == 2 for unit in units))
        self.assertTrue(all(item['admission_status'] == 'candidate-only'
                            for item in structure['memo_numbering_candidates']))

    def test_spaced_appendix_stops_prior_paragraph_after_full_example(self):
        from manual_structure import segment_source
        f = FIXTURES[1]
        document, source_pages = self.source(f)
        first = f['expected_paragraph_spans'][0]['page']
        last = f['appendix_page']
        # Three unchanged source pages, locally numbered 1..3 for this bounded
        # fallback control. The frozen fixture retains real PDF page identities.
        pages = [{'page': i + 1, 'text': page['text']}
                 for i, page in enumerate(source_pages[first - 1:last])]
        document = {key: document[key] for key in ('kind', 'role', 'chapter')}
        units, _ = segment_source('dmg', document, pages)
        paragraph = next(unit for unit in units if unit['paragraph_labels'] == [f['main_label']])
        expected = [{**span, 'page': span['page'] - first + 1} for span in f['expected_paragraph_spans']]
        self.assertEqual(paragraph['spans'], expected)
        self.assertIn(f['required_continuation_marker'], paragraph['text'])
        self.assertNotIn(f['appendix_literal'], paragraph['text'])
        appendix = next(unit for unit in units if f['appendix_literal'] in unit['heading_path'])
        self.assertEqual(appendix['role'], 'section')
        self.assertEqual(appendix['spans'][0]['page'], last - first + 1)
        self.assertEqual(appendix['spans'][0]['start_utf8'], f['appendix_line_start_utf8'])
        self.assertEqual(appendix['completeness'], 'unresolved')
        self.partition(units, pages)


if __name__ == '__main__':
    unittest.main()
