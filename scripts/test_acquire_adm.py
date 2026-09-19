"""Independent controls for ADM source boundaries, frozen identity and authority."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import acquire_adm as adm
from test_acquire_full_dmg import FakeResponse


class AdmAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / 'source/adm-test'
        self.output.mkdir(parents=True)
        self.prior = self.root / 'source/prior.json'
        self.url = 'https://assets.publishing.service.gov.uk/example.pdf'
        self.attachment = {'title': 'Chapter A1: Principles', 'url': self.url,
                           'content_type': 'application/pdf', 'file_size': 9, 'number_of_pages': 1}
        self.publication = {'title': 'Advice for decision making: staff guide', 'details': {'attachments': [self.attachment]},
                            'first_published_at': '2013-03-22T00:00:00Z', 'public_updated_at': '2026-08-27T00:00:00Z'}
        self.receipt = {'observed_at': '2026-09-19T00:00:00Z', 'sha256': 'a' * 64}
        self.prior.write_text(json.dumps({'publications': [{'family': 'adm', 'attachments': [
            {**self.attachment, 'is_pdf': True}]}]}))
        original_checked_path = adm.common.checked_path
        for target, name, value in [
            (adm, 'ROOT', self.root), (adm.common, 'ROOT', self.root),
            (adm, 'OUTPUT', self.output), (adm, 'PRIOR', self.prior),
            (adm, 'PRIOR_SHA', adm.common.digest(self.prior.read_bytes())),
        ]:
            patcher = patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(adm.common, 'checked_path', side_effect=lambda value, within=None:
                               original_checked_path(value, within=within or self.root / 'source'))
        patcher.start()
        self.addCleanup(patcher.stop)

    def record(self):
        description = adm.describe(self.attachment, self.publication, self.receipt['observed_at'])
        pdf, text = b'%PDF-test', b'one page\f'
        extraction = {'method': 'pdftotext -layout -enc UTF-8', 'review_status': 'unreviewed-machine-extraction',
                      'limitations': adm.common.EXTRACTION_LIMITATIONS, 'ocr_performed': False, 'warnings': ''}
        http = {'requested_url': self.url, 'resolved_url': self.url, 'observed_at': self.receipt['observed_at'],
                'bytes': len(pdf), 'sha256': adm.common.digest(pdf)}
        record = {**description, 'status': 'complete', 'sha256': http['sha256'], 'size_bytes': len(pdf), 'pages': 1,
                  'text_sha256': adm.common.digest(text), 'observed_at': http['observed_at'], 'http': http,
                  'text_characters': len(text), 'nonempty_text_pages': 1, 'quality': adm.common.assess_quality(['one page']),
                  'extraction': extraction, 'declared_page_count_matches_measured': True, 'declared_size_matches_measured': True,
                  'acquisition': {'mode': 'additional-frozen-census-download', 'receipt_path': 'source/adm-test/acquisition.json'}}
        for key, filename, raw in [('pdf_path', 'document.pdf', pdf), ('text_path', 'document.txt', text)]:
            record[key] = f'source/adm-test/{filename}'
            (self.output / filename).write_bytes(raw)
        record['pages_path'] = 'source/adm-test/pages.json'
        adm.common.atomic_json(self.output / 'pages.json', {
            'document_id': record['id'], 'source_url': self.url, 'source_sha256': record['sha256'],
            'extraction': extraction, 'pages': [{'page': 1, 'url': self.url + '#page=1', 'text': 'one page'}],
        })
        record['pages_sha256'] = adm.common.digest((self.output / 'pages.json').read_bytes())
        adm.common.atomic_json(self.output / 'acquisition.json', http)
        return description, record

    def test_frozen_comparison_does_not_infer_document_publication_date(self):
        census = adm.build_census(self.publication, self.receipt)
        self.assertEqual(1, census['pdf_count'])
        self.assertEqual([], census['comparison_to_2026_09_15']['added_urls'])
        doc = census['documents'][0]
        self.assertEqual('A1', doc['chapter'])
        self.assertEqual('adm-chapter-a1', doc['id'])
        self.assertIsNone(doc['document_dates']['published_at'])
        self.assertNotEqual(doc['listed_at'], doc['publication_updated_at'])

    def test_memos_with_and_without_word_memo_keep_separate_numbered_identities(self):
        for title in ('ADM Memo 05/25: Rates', 'ADM 05/25: Rates'):
            row = adm.describe({**self.attachment, 'title': title}, self.publication, self.receipt['observed_at'])
            self.assertEqual('adm-memo-05-25', row['id'])
            self.assertEqual('supplementary-guidance-applicability-unreviewed', row['role'])

    def test_unrecognised_and_colliding_attachments_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'classification review required'):
            adm.classify('Unrecognised handbook')
        self.publication['details']['attachments'].append(copy.deepcopy(self.attachment))
        with self.assertRaisesRegex(ValueError, 'colliding'):
            adm.build_census(self.publication, self.receipt)

    def test_prior_census_tampering_is_rejected(self):
        self.prior.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Prior discovery census hash changed'):
            adm.build_census(self.publication, self.receipt)

    def test_metadata_size_and_external_url_rejected(self):
        with self.assertRaises(ValueError), patch.object(adm.urllib.request, 'build_opener') as opener:
            adm.fetch_metadata('https://example.invalid/publication')
        opener.assert_not_called()
        with patch.object(adm, 'MAX_METADATA_BYTES', 5), patch.object(adm.urllib.request, 'build_opener') as opener:
            opener.return_value.open.return_value = FakeResponse(b'123456')
            with self.assertRaisesRegex(ValueError, 'bounded size'):
                adm.fetch_metadata(adm.API_URL)

    def test_valid_record_passes_and_pdf_tampering_fails(self):
        description, record = self.record()
        adm.validate_record(record, description)
        (self.output / 'document.pdf').write_bytes(b'%PDF-changed')
        with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
            adm.validate_record(record, description)

    def test_an_adm_record_cannot_reuse_an_outside_dmg_path(self):
        description, record = self.record()
        record['pdf_path'] = 'source/full-dmg-2026-09-15/example.pdf'
        with self.assertRaisesRegex(ValueError, 'escapes'):
            adm.validate_record(record, description)

    def test_matching_hashes_do_not_permit_false_page_locators_or_authority(self):
        for mutation in ('locator', 'authority'):
            with self.subTest(mutation=mutation):
                description, record = self.record()
                page_path = self.output / 'pages.json'
                pages = json.loads(page_path.read_text())
                if mutation == 'locator':
                    pages['pages'][0]['url'] = self.url + '#page=999'
                else:
                    record['extraction']['review_status'] = 'official-reviewed'
                    pages['extraction'] = copy.deepcopy(record['extraction'])
                adm.common.atomic_json(page_path, pages)
                record['pages_sha256'] = adm.common.digest(page_path.read_bytes())
                with self.assertRaises(ValueError):
                    adm.validate_record(record, description)


if __name__ == '__main__':
    unittest.main()
