"""Source-bound regressions registered before the auxiliary region repair.

The four boundaries below were checked against frozen page extraction; DMG67
pages152–153 and DMG42 pages112–113 were also visually inspected. The source
pages and complete PDF/extraction identities remain unchanged. These examples
establish bounded structural labels, not legal applicability.
"""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FIXTURES = [{'family': 'dmg',
  'document_id': 'dmg-vol8-ch42',
  'pages_path': 'source/full-dmg-2026-09-15/pages/dmg-vol8-ch42.json',
  'pages_sha256': '76f4177f72f76ab6250f9d08c9901dd5be53b71af1100ada6a7403f9c3f379f5',
  'pdf_sha256': '94a571d424358872f55f212b4c831a4cd4d33d478233d15f860a00d2eb1ab110',
  'page': 112,
  'start_utf8': 426,
  'end_utf8': 532,
  'role': 'document-notice',
  'literal': 'The content of the examples in this document (including use of imagery) is for '
             'illustrative purposes\n'
             'only\n',
  'literal_sha256': 'b481f5b45121fd540476bb3ce318e1f29fc5495258784ad2bbc2f2ffb4f43a4b',
  'following_page_prefix': 'Appendix 2 - DMG Memo 1-18: ESA: Work Related Activity and\n'
                           'Substantial Risk\n'
                           'Contents                '},
 {'family': 'dmg',
  'document_id': 'dmg-vol11-ch67',
  'pages_path': 'source/full-dmg-2026-09-15/pages/dmg-vol11-ch67.json',
  'pages_sha256': 'f6415f436f2f1eea4febaa9f82fbd0ad34a6fc754ce3c59c24fd10311ba0ad12',
  'pdf_sha256': '3c7414b2ec9ba0ec4073199a063a97072e1bf2c670f1620e241884a39b7e201a',
  'page': 152,
  'start_utf8': 243,
  'end_utf8': 257,
  'role': 'reserved',
  'literal': '67956 - 67999\n',
  'literal_sha256': 'fd1c3067b82c4eb49ed393908076a4da7816c2f4ae7980447204f747f4c471c0',
  'following_page_prefix': 'Appendix 1 - Prescribed diseases added and changes made to the\n'
                           'Schedule of Diseases since 5 July 194'},
 {'family': 'adm',
  'document_id': 'adm-chapter-f1',
  'pages_path': 'source/adm-2026-09-19/pages/adm-chapter-f1.json',
  'pages_sha256': 'c5b5c405f2c77cece7da418826dbcf298a89323a3788bda3cfebf1136dc6cf27',
  'pdf_sha256': '124b7e41af2b491209f694941482e6e4bb69e78692a84a343299dc53f25b8731',
  'page': 14,
  'start_utf8': 1840,
  'end_utf8': 1856,
  'role': 'reserved',
  'literal': 'F1085 – F1099\n',
  'literal_sha256': 'cd7ab219c5868afe1d2d1bacdb86222cc0294fbf366689bbc9ff3f69539b87fd',
  'following_page_prefix': 'Run on after death F1100 - F1109\n'
                           '\n'
                           '\n'
                           '\n'
                           'Run on after death F1100\n'
                           '\n'
                           '\n'
                           '\n'
                           '\n'
                           'Run on after death\n'
                           '\n'
                           'F1100 Where\n'
                           '\n'
                           '\n'
                           '1'},
 {'family': 'adm',
  'document_id': 'adm-chapter-p2',
  'pages_path': 'source/adm-2026-09-19/pages/adm-chapter-p2.json',
  'pages_sha256': 'd00ddea746a34b7d2ba4f3c3195bd532cec097da5f390077da941b24533a92ea',
  'pdf_sha256': '81698afa30d449695b0ebd72bb4bd7bd3d105a1976644b2943073ba364ca5e5a',
  'page': 36,
  'start_utf8': 744,
  'end_utf8': 850,
  'role': 'document-notice',
  'literal': 'The content of the examples in this document (including use of imagery) is for '
             'illustrative purposes\n'
             'only\n',
  'literal_sha256': 'b481f5b45121fd540476bb3ce318e1f29fc5495258784ad2bbc2f2ffb4f43a4b',
  'following_page_prefix': 'PIP Mobility Activity 1 – effect of UT decision MH v SSWP (PIP) [2016]\n'
                           'UKUT 531 (AAC)\n'
                           '\n'
                           'INTRODUCTION\n'}]


class FrozenAuxiliaryFixtures(unittest.TestCase):
    def test_frozen_sources_and_exact_expectations(self):
        for fixture in SOURCE_FIXTURES:
            with self.subTest(document=fixture["document_id"]):
                raw = (ROOT / fixture["pages_path"]).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), fixture["pages_sha256"])
                extraction = json.loads(raw)
                self.assertEqual(extraction["source_sha256"], fixture["pdf_sha256"])
                self.assertEqual(extraction["document_id"], fixture["document_id"])
                pages = extraction["pages"]
                literal = pages[fixture["page"]-1]["text"].encode()[fixture["start_utf8"]:fixture["end_utf8"]]
                self.assertEqual(literal.decode(), fixture["literal"])
                self.assertEqual(hashlib.sha256(literal).hexdigest(), fixture["literal_sha256"])
                self.assertTrue(pages[fixture["page"]]["text"].startswith(fixture["following_page_prefix"]))


class AuxiliaryRegionControls(unittest.TestCase):
    def regions(self, text, family='dmg', chapter=None):
        from manual_auxiliary_structure import literal_auxiliary_regions
        pages = [{'page': 1, 'text': text}]
        regions = literal_auxiliary_regions(pages, family, chapter)
        for region in regions:
            self.assertEqual(hashlib.sha256(text.encode()[region['start']:region['end']]).hexdigest(), region['literal_sha256'])
            self.assertEqual(region['legal_dependency'], 'not-established')
        return regions

    def test_source_regressions_do_not_absorb_the_following_appendix_or_prose(self):
        from manual_auxiliary_structure import literal_auxiliary_regions
        for fixture in SOURCE_FIXTURES:
            with self.subTest(document=fixture['document_id']):
                pages = json.loads((ROOT / fixture['pages_path']).read_bytes())['pages']
                before = sum(len(page['text'].encode()) for page in pages[:fixture['page']-1])
                regions = literal_auxiliary_regions(pages, fixture['family'])
                selected = [r for r in regions if r['start'] == before + fixture['start_utf8']]
                self.assertEqual(len(selected), 1)
                region = selected[0]
                self.assertEqual(region['end'], before + fixture['end_utf8'])
                self.assertEqual(region['role'], fixture['role'])
                self.assertEqual(region['literal_sha256'], fixture['literal_sha256'])
                self.assertLess(region['end'] - region['start'], 200)

    def test_reserved_line_stops_before_blank_or_nonblank_following_text(self):
        for gap in ('', '\n'):
            text = '67956 - 67999\n' + gap + 'Appendix 1 - table\nFurther guidance\n'
            region = self.regions(text)[0]
            self.assertEqual(text[region['start']:region['end']], '67956 - 67999\n')
            self.assertEqual(region['boundary_status'], 'explicit-line-end')

    def test_reserved_scope_requires_whole_line_order_and_manual_family(self):
        for text, family in [('67999 - 67956\n','dmg'), ('F1085 – F1099\n','dmg'),
                             ('67956 - 67999\n','adm'), ('F1085 – G1099\n','adm'),
                             ('See 67956 - 67999\n','dmg'), ('67956 - 67999 applies elsewhere\n','dmg'),
                             ('67956 - 99\n','dmg')]:
            with self.subTest(text=text, family=family):
                self.assertEqual(self.regions(text, family), [])
        self.assertEqual(self.regions('F1085 – F1099\n','adm','P1'), [])
        self.assertEqual(self.regions('67956 - 67999\n','dmg','68'), [])
        self.assertEqual(len(self.regions('F1085 – F1099\n','adm','F1')), 1)

    def test_notice_stops_at_complete_sentence_even_without_blank_line(self):
        text = ('The content of the examples in this document (including use of imagery) is for\n'
                'illustrative purposes only\nAppendix 2 - actual guidance\n')
        region = self.regions(text)[0]
        self.assertEqual(text[region['start']:region['end']], text.split('Appendix')[0])
        self.assertTrue(region['notice_sentence_complete'])

    def test_notice_stops_at_blank_line_or_next_structure_and_exposes_uncertainty(self):
        for suffix in ('\nFurther text\n', 'Appendix 2 - following material\n'):
            text = 'The content of the examples in this document is described below\n' + suffix
            region = self.regions(text)[0]
            self.assertEqual(region['end'], text.index('\n')+1)
            self.assertFalse(region['notice_sentence_complete'])

    def test_notice_does_not_cross_a_page_boundary(self):
        from manual_auxiliary_structure import literal_auxiliary_regions
        first = 'The content of the examples in this document is incomplete\n'
        pages = [{'page':1,'text':first},{'page':2,'text':'Appendix with unrelated material\n'}]
        region = literal_auxiliary_regions(pages,'dmg')[0]
        self.assertEqual(region['end'],len(first.encode()))
        self.assertFalse(region['notice_sentence_complete'])

    def test_notice_limits_preserve_uncertainty(self):
        from unittest.mock import patch
        text = 'The content of the examples in this document starts here\n' + 'continuation\n'*12
        with patch('manual_auxiliary_structure.MAX_NOTICE_LINES',2):
            region = self.regions(text)[0]
            self.assertEqual(region['end'],len(''.join(text.splitlines(keepends=True)[:2]).encode()))
            self.assertFalse(region['notice_sentence_complete'])
        with patch('manual_auxiliary_structure.MAX_NOTICE_BYTES',70):
            region = self.regions(text)[0]
            self.assertLessEqual(region['end'],70)
            self.assertFalse(region['notice_sentence_complete'])

    def test_utf8_and_crlf_are_source_bytes_not_normalised_text(self):
        text = 'Évidence\r\n\tF1085 – F1099\r\nFurther text\r\n'
        region = self.regions(text,'adm')[0]
        self.assertEqual(text.encode()[region['start']:region['end']], '\tF1085 – F1099\r\n'.encode())

    def test_bad_source_order_and_unknown_family_fail_closed(self):
        from manual_auxiliary_structure import literal_auxiliary_regions
        with self.assertRaises(ValueError):literal_auxiliary_regions([{'page':2,'text':'67956 - 67999\n'}],'dmg')
        with self.assertRaises(ValueError):self.regions('67956 - 67999\n','other')
        with self.assertRaises(ValueError):self.regions('67956 - 67999\n','dmg','A')


class MemoObservationControls(unittest.TestCase):
    @staticmethod
    def block(text, fragment, line, role='P'):
        start = text.encode().index(fragment.encode())
        return {'role':role,'start':start,'end':start+len(fragment.encode()),'tree_line_start':line,'tree_line_end':line+1}

    def test_p_tags_do_not_promote_indented_nested_points_to_accepted_events(self):
        from manual_auxiliary_structure import memo_paragraph_candidates
        text = '1. Main paragraph\n\n    1. Nested point\n\n2. Second paragraph\n'
        blocks = [self.block(text,fragment,number) for fragment,number in [('1. Main paragraph',1),('1. Nested point',3),('2. Second paragraph',5)]]
        rows = memo_paragraph_candidates({'kind':'memo'},[{'page':1,'text':text}],blocks)
        self.assertEqual([r['at_document_number_margin'] for r in rows],[True,False,True])
        self.assertTrue(all(r['admission_status']=='candidate-only' and not r['boundary_complete'] for r in rows))
        self.assertTrue(all(r['legal_dependency']=='not-established' for r in rows))

    def test_container_ancestry_remains_explicit(self):
        from manual_auxiliary_structure import memo_paragraph_candidates
        text = '1. Main paragraph\n2. List paragraph\n'
        blocks = [self.block(text,'1. Main paragraph',1),self.block(text,'2. List paragraph',8),
                  {'role':'LI','tree_line_start':7,'tree_line_end':12}]
        rows = memo_paragraph_candidates({'kind':'memo'},[{'page':1,'text':text}],blocks)
        self.assertEqual(rows[1]['container_ancestry'],['LI'])
        self.assertEqual(rows[1]['admission_status'],'candidate-only')

    def test_decimal_numbers_citations_and_unaligned_short_p_do_not_create_candidates(self):
        from manual_auxiliary_structure import memo_paragraph_candidates
        text = '1.1 Nested decimal\n1. Main body with a superscript\n'
        blocks = [self.block(text,'1.1 Nested decimal',1),self.block(text,'1.',3)]
        self.assertEqual(memo_paragraph_candidates({'kind':'memo'},[{'page':1,'text':text}],blocks),[])
        self.assertEqual(memo_paragraph_candidates({'kind':'chapter'},[{'page':1,'text':text}],blocks),[])


if __name__ == '__main__':
    unittest.main()
