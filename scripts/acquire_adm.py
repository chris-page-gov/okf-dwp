#!/usr/bin/env python3
"""Freeze and acquire the public ADM publication separately from the DMG snapshot.

Run --discover once to retain current publication metadata and its attachment
census. A normal run acquires every PDF in that frozen census; --check is offline.
The existing bounded DMG download/extraction helpers are reused unchanged.
"""

from __future__ import annotations

import argparse
from collections import Counter
import concurrent.futures
import fcntl
import json
from pathlib import Path
import re
import shutil
import time
import urllib.request

import acquire_full_dmg as common


ROOT = common.ROOT
OUTPUT = ROOT / 'source/adm-2026-09-19'
PUBLICATION_URL = 'https://www.gov.uk/government/publications/advice-for-decision-making-staff-guide'
API_URL = PUBLICATION_URL.replace('www.gov.uk/', 'www.gov.uk/api/content/', 1)
PRIOR = ROOT / 'source/discovery-2026-09-15/census.json'
PRIOR_SHA = '445308cd5cba91d997f21b8408cb8cfeb52e2a888f291492bcdcc41c16c2be88'
SNAPSHOT = 'adm-2026-09-19'
MAX_METADATA_BYTES = 8 * 1024 * 1024
CLASSIFICATIONS = {**common.CLASSIFICATIONS, 'annex-spare': ('annex', 'spare')}
CLASSIFICATION_BASIS = 'publication family and attachment title only; content and temporal applicability not reviewed'


def fetch_metadata(url: str) -> tuple[bytes, dict]:
    common.check_url(url)
    redirect = common.CheckedRedirect()
    started = time.monotonic()
    request = urllib.request.Request(url, headers={
        'User-Agent': 'okf-dwp/0.3 (independent public guidance research; bounded acquisition)',
        'Accept': 'application/json' if url == API_URL else 'text/html', 'Accept-Encoding': 'identity',
    })
    with urllib.request.build_opener(redirect).open(request, timeout=30) as response:
        common.check_url(response.url)
        if response.status != 200 or response.headers.get('Content-Encoding', 'identity').lower() != 'identity':
            raise ValueError('Expected unchanged HTTP 200 metadata response')
        chunks, size = [], 0
        while True:
            if time.monotonic() - started > 120:
                raise TimeoutError('Publication metadata deadline exceeded')
            chunk = response.read(65536)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_METADATA_BYTES:
                raise ValueError('Publication metadata exceeds bounded size')
            chunks.append(chunk)
        raw = b''.join(chunks)
        return raw, {
            'requested_url': url, 'resolved_url': response.url, 'http_status': response.status,
            'observed_at': common.utc_now(), 'redirects': redirect.observations,
            'content_type': response.headers.get('Content-Type'),
            'content_length': response.headers.get('Content-Length'),
            'last_modified': response.headers.get('Last-Modified'), 'etag': response.headers.get('ETag'),
            'sha256': common.digest(raw), 'bytes': len(raw),
        }


def classify(title: str) -> str:
    lower = title.lower()
    if re.search(r'\bmemo\b', lower) or re.match(r'adm\s+\d+\s*/\s*\d+', lower):
        return 'memo'
    if 'summary of changes' in lower:
        return 'change-summary'
    if 'abbreviations' in lower:
        return 'abbreviations'
    if 'statutes and statutory instruments' in lower:
        return 'legislation-reference-list'
    if lower.startswith('annex '):
        return 'annex-spare' if 'spare' in lower else 'annex-listed'
    if re.match(r'chapter [a-z]\d+\b', lower):
        if 'spare' in lower:
            return 'chapter-spare'
        return 'chapter-transitional' if 'transitional' in lower else 'chapter-current-listed'
    raise ValueError(f'Unrecognised ADM attachment title; classification review required: {title}')


def describe(attachment: dict, publication: dict, observed_at: str) -> dict:
    title = attachment['title']
    classification = classify(title)
    kind, role = CLASSIFICATIONS[classification]
    chapter = re.match(r'Chapter ([A-Z]\d+)\b', title, re.I)
    annex = re.match(r'Annex ([A-Z])\b', title, re.I)
    memo = re.search(r'\b(?:ADM\s+(?:Memo\s+)?|Memo\s+)(\d+)\s*/\s*(\d+)\b', title, re.I)
    if chapter:
        identifier = f'adm-chapter-{chapter[1].lower()}'
    elif annex:
        identifier = f'adm-annex-{annex[1].lower()}'
    elif memo:
        identifier = f'adm-memo-{int(memo[1]):02d}-{memo[2]}'
    else:
        identifier = f'adm-{common.slug(title)}'
    common.check_url(attachment['url'])
    return {
        'id': identifier, 'family': 'adm', 'title': title, 'url': attachment['url'],
        'kind': kind, 'role': role, 'volume': None,
        'chapter': chapter[1].upper() if chapter else None, 'part': None,
        'attachment_id': attachment.get('id'), 'original_filename': attachment.get('filename'),
        'declared_size_bytes': attachment.get('file_size'), 'declared_pages': attachment.get('number_of_pages'),
        'accessible_format_available': attachment.get('accessible'),
        'discovery_classification': classification, 'classification_basis': CLASSIFICATION_BASIS,
        'publication': {
            'url': PUBLICATION_URL, 'title': publication['title'], 'family': 'adm',
            'first_published_at': publication.get('first_published_at'),
            'public_updated_at': publication.get('public_updated_at'),
            'withdrawn_notice': publication.get('withdrawn_notice', {}),
            'metadata_path': common.relative(OUTPUT / 'publication.json'),
        },
        'publication_updated_at': publication.get('public_updated_at'),
        'document_dates': {
            'published_at': None, 'status': 'not-declared-in-frozen-attachment-metadata',
            'limitation': 'Publication-page dates, title dates, HTTP headers and PDF technical metadata are not inferred document publication or legal effective dates.',
        },
        'current_attachment': True, 'listed_at': observed_at,
        'legal_status': 'Departmental guidance, not legislation. Listed in the frozen ADM publication; current legal applicability and supersession have not been reviewed.',
    }


def build_census(publication: dict, receipt: dict) -> dict:
    if common.digest(PRIOR.read_bytes()) != PRIOR_SHA:
        raise ValueError('Prior discovery census hash changed')
    prior = next(row for row in common.read_json(PRIOR)['publications'] if row['family'] == 'adm')
    attachments = publication['details']['attachments']
    pdfs = [row for row in attachments if row.get('content_type') == 'application/pdf']
    descriptions = [describe(row, publication, receipt['observed_at']) for row in pdfs]
    if not descriptions or len({row['id'] for row in descriptions}) != len(descriptions):
        raise ValueError('Empty census or colliding ADM document identifiers')
    if len({row['url'] for row in descriptions}) != len(descriptions):
        raise ValueError('Repeated ADM PDF URL requires explicit reconciliation')
    old = {row['url']: row['title'] for row in prior['attachments'] if row.get('is_pdf')}
    new = {row['url']: row['title'] for row in descriptions}
    return {
        'schema': 'okf-dwp-adm-census.v1', 'snapshot_id': SNAPSHOT,
        'publication_url': PUBLICATION_URL, 'metadata_observed_at': receipt['observed_at'],
        'publication_sha256': receipt['sha256'], 'prior_census_sha256': PRIOR_SHA,
        'attachment_count': len(attachments), 'pdf_count': len(pdfs),
        'non_pdf_attachments': [{'title': row.get('title'), 'url': row.get('url'), 'content_type': row.get('content_type')}
                                for row in attachments if row.get('content_type') != 'application/pdf'],
        'comparison_to_2026_09_15': {
            'prior_pdf_count': len(old), 'added_urls': sorted(new.keys() - old.keys()),
            'removed_urls': sorted(old.keys() - new.keys()),
            'changed_titles': [{'url': url, 'before': old[url], 'after': new[url]}
                               for url in sorted(old.keys() & new.keys()) if old[url] != new[url]],
            'limitation': 'Attachment URL/title comparison only; identical URLs do not prove unchanged PDF bytes.',
        },
        'documents': descriptions,
    }


def load_inputs() -> tuple[dict, dict]:
    receipts = {}
    for name, url in [('publication', API_URL), ('publication-html', PUBLICATION_URL)]:
        extension = 'json' if name == 'publication' else 'html'
        raw = (OUTPUT / f'{name}.{extension}').read_bytes()
        receipt = common.read_json(OUTPUT / f'{name}-receipt.json')
        if receipt['requested_url'] != url or common.digest(raw) != receipt['sha256'] or len(raw) != receipt['bytes']:
            raise ValueError(f'Frozen publication/receipt mismatch: {name}')
        common.check_url(receipt['resolved_url'])
        receipts[name] = receipt
    publication = common.read_json(OUTPUT / 'publication.json')
    census = common.read_json(OUTPUT / 'census.json')
    if census != build_census(publication, receipts['publication']):
        raise ValueError('Frozen census differs from retained official metadata')
    return census, receipts


def discover() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if (OUTPUT / 'census.json').exists():
        census, _ = load_inputs()
        print(json.dumps({'frozen_census_reused': True, 'pdf_count': census['pdf_count']}))
        return
    for name, url, extension in [('publication', API_URL, 'json'), ('publication-html', PUBLICATION_URL, 'html')]:
        target = OUTPUT / f'{name}.{extension}'
        if target.exists():
            receipt = common.read_json(OUTPUT / f'{name}-receipt.json')
            if common.digest(target.read_bytes()) != receipt['sha256']:
                raise ValueError('Interrupted metadata observation has mismatched bytes')
            continue
        raw, receipt = fetch_metadata(url)
        if extension == 'json':
            publication = json.loads(raw)
            if publication.get('base_path') != '/government/publications/advice-for-decision-making-staff-guide':
                raise ValueError('Official content API returned a different publication')
        common.atomic_bytes(target, raw)
        common.atomic_json(OUTPUT / f'{name}-receipt.json', receipt)
    publication = common.read_json(OUTPUT / 'publication.json')
    receipt = common.read_json(OUTPUT / 'publication-receipt.json')
    census = build_census(publication, receipt)
    common.atomic_json(OUTPUT / 'census.json', census)
    load_inputs()
    print(json.dumps({key: census[key] for key in ('pdf_count', 'metadata_observed_at', 'comparison_to_2026_09_15')}, indent=2))


def validate_record(record: dict, description: dict) -> None:
    if record.get('status') != 'complete' or any(record.get(key) != value for key, value in description.items()):
        raise ValueError(f'ADM record differs from frozen census: {description["id"]}')
    for key in ('pdf_path', 'text_path', 'pages_path'):
        common.checked_path(record[key], within=OUTPUT)
    pages = common.validate_materials(record)
    extracted = common.read_json(common.checked_path(record['pages_path'], within=OUTPUT))
    if extracted['extraction'] != record['extraction']:
        raise ValueError('ADM page and record extraction provenance differ')
    for key, expected in {
        'method': 'pdftotext -layout -enc UTF-8',
        'review_status': 'unreviewed-machine-extraction',
        'limitations': common.EXTRACTION_LIMITATIONS, 'ocr_performed': False,
    }.items():
        if record['extraction'].get(key) != expected:
            raise ValueError('ADM extraction status cannot be upgraded or its limitations removed')
    if record['quality'] != common.assess_quality(pages):
        raise ValueError('ADM extraction-quality metrics changed')
    if record['text_characters'] != len(common.checked_path(record['text_path']).read_text(encoding='utf-8')):
        raise ValueError('ADM text character count changed')
    if record['nonempty_text_pages'] != sum(bool(page.strip()) for page in pages):
        raise ValueError('ADM nonempty page count changed')
    receipt = common.read_json(common.checked_path(record['acquisition']['receipt_path'], within=OUTPUT))
    if (receipt != record['http'] or receipt['sha256'] != record['sha256'] or receipt['bytes'] != record['size_bytes']
            or record['acquisition']['mode'] != 'additional-frozen-census-download'):
        raise ValueError('ADM acquisition receipt differs from source bytes')
    if record['declared_page_count_matches_measured'] != (record['declared_pages'] == record['pages']):
        raise ValueError('ADM declared/measured page comparison changed')
    if record['declared_size_matches_measured'] != (record['declared_size_bytes'] == record['size_bytes']):
        raise ValueError('ADM declared/measured size comparison changed')


def acquire_one(description: dict, retries: int) -> tuple[dict, str]:
    record_path = OUTPUT / 'records' / f'{description["id"]}.json'
    if record_path.exists():
        record = common.read_json(record_path)
        validate_record(record, description)
        return record, 'verified-existing'
    record, action = common.acquire_one(description, {}, OUTPUT, retries)
    validate_record(record, description)
    return record, action


def inventory(census: dict, receipts: dict, records: list[dict], failures: list[dict], started: str) -> dict:
    order = {row['id']: index for index, row in enumerate(census['documents'])}
    records = sorted(records, key=lambda row: order[row['id']])
    return {
        'schema': 'okf-dwp-adm-acquisition.v1', 'snapshot_id': SNAPSHOT, 'family': 'adm',
        'generated_at': common.utc_now(), 'run_started_at': started,
        'census': {'path': common.relative(OUTPUT / 'census.json'), 'sha256': common.digest((OUTPUT / 'census.json').read_bytes())},
        'publication': {'url': PUBLICATION_URL, 'api_url': API_URL, 'receipts': receipts},
        'authority': 'official-source-bytes; unreviewed-machine-extraction; project-authored-classification',
        'licence_url': 'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/',
        'attribution': 'Contains public sector information licensed under the Open Government Licence v3.0. Source: Department for Work and Pensions, Advice for decision making. Rights exceptions remain applicable.',
        'rights_evidence': common.relative(OUTPUT / 'publication-html.html'),
        'limitations': [common.EXTRACTION_LIMITATIONS,
            'Frozen direct ADM PDF attachments only; separate from DMG, CPAG and claimant-facing web guidance.',
            'Full acquisition does not establish complete policy modelling, current-law consolidation or specialist acceptance.',
            'Source text remains inert evidence and does not authorise actions or override client instructions.',
            'Publication-page dates, source capture dates, PDF technical dates and legal effective dates remain distinct.'],
        'summary': {
            'expected_pdf_documents': census['pdf_count'], 'complete_documents': len(records),
            'measured_pages': sum(row['pages'] for row in records),
            'declared_pages': sum(row['declared_pages'] or 0 for row in census['documents']),
            'pdf_bytes': sum(row['size_bytes'] for row in records),
            'text_characters': sum(row['text_characters'] for row in records),
            'documents_by_kind': dict(Counter(row['kind'] for row in records)),
            'quality_flags': dict(Counter(flag for row in records for page in row['quality']['flagged_pages'] for flag in page['flags'])),
            'declared_page_mismatches': [row['id'] for row in records if not row['declared_page_count_matches_measured']],
            'declared_byte_mismatches': [row['id'] for row in records if not row['declared_size_matches_measured']],
            'failure_count': len(failures),
            'complete_for_frozen_adm_census': len(records) == census['pdf_count'] and not failures,
        },
        'documents': records, 'failures': failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--discover', action='store_true', help='Freeze current official publication metadata only')
    mode.add_argument('--plan', action='store_true', help='Inspect frozen census without networking or writing')
    mode.add_argument('--check', action='store_true', help='Verify all acquired PDF/text/page evidence offline')
    parser.add_argument('--workers', type=int, default=4, choices=range(1, 5))
    parser.add_argument('--retries', type=int, default=3, choices=range(1, 4))
    args = parser.parse_args()
    if args.discover:
        discover()
        return 0
    census, receipts = load_inputs()
    if args.plan:
        print(json.dumps({'pdf_count': census['pdf_count'], 'declared_pages': sum(row['declared_pages'] or 0 for row in census['documents']),
                          'documents_by_kind': dict(Counter(row['kind'] for row in census['documents']))}, indent=2))
        return 0
    for executable in ('pdfinfo', 'pdftotext'):
        if not shutil.which(executable):
            parser.error(f'Required installed executable missing: {executable}')
    if args.check:
        current = common.read_json(OUTPUT / 'inventory.json')
        if not current['summary']['complete_for_frozen_adm_census'] or len(current['documents']) != census['pdf_count']:
            raise ValueError('ADM inventory is incomplete')
        records = {row['id']: row for row in current['documents']}
        if len(records) != census['pdf_count']:
            raise ValueError('ADM inventory contains duplicate identifiers')
        for description in census['documents']:
            record = common.read_json(OUTPUT / 'records' / f'{description["id"]}.json')
            if record != records.get(description['id']):
                raise ValueError('ADM inventory differs from acquisition record')
            validate_record(record, description)
            measured, _ = common.pdf_information(common.checked_path(record['pdf_path'], within=OUTPUT))
            if measured != record['pages']:
                raise ValueError('ADM PDF page count differs on remeasurement')
        expected = inventory(census, receipts, list(records.values()), [], current['run_started_at'])
        expected['generated_at'] = current['generated_at']
        if current != expected:
            raise ValueError('ADM inventory metadata or aggregate metrics changed')
        print(json.dumps({'passed': True, 'network_used': False, **current['summary']}))
        return 0
    lock_path = OUTPUT / '.acquisition.lock'
    with lock_path.open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        started = common.utc_now()
        records, failures = [], []
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
                futures = {pool.submit(acquire_one, row, args.retries): row for row in census['documents']}
                for future in concurrent.futures.as_completed(futures):
                    description = futures[future]
                    try:
                        record, action = future.result()
                        records.append(record)
                        print(f'{len(records):03d}/{census["pdf_count"]} {action} {record["id"]}: {record["pages"]} pages', flush=True)
                    except Exception as error:
                        failures.append({'id': description['id'], 'url': description['url'], 'observed_at': common.utc_now(),
                                         'error_type': type(error).__name__, 'error': str(error)})
                        print(f'FAILED {description["id"]}: {error}', flush=True)
                    if (len(records) + len(failures)) % 20 == 0:
                        common.atomic_json(OUTPUT / 'inventory.json', inventory(census, receipts, records, failures, started))
            final = inventory(census, receipts, records, failures, started)
            common.atomic_json(OUTPUT / 'inventory.json', final)
            common.atomic_json(OUTPUT / 'runs' / f'{started.replace(":", "").replace(".", "-")}.json', {
                'started_at': started, 'completed_at': common.utc_now(), 'workers': args.workers,
                'inventory_sha256': common.digest((OUTPUT / 'inventory.json').read_bytes()),
                'acquisition_script_sha256': common.digest(Path(__file__).read_bytes()),
                'shared_helpers_sha256': common.digest(Path(common.__file__).read_bytes()),
                'summary': final['summary'],
            })
            print(json.dumps(final['summary'], indent=2), flush=True)
            return int(bool(failures))
        finally:
            lock_path.unlink(missing_ok=True)


if __name__ == '__main__':
    raise SystemExit(main())
