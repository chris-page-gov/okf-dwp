#!/usr/bin/env python3
"""Acquire only approved Chapter 60 targets; offline checks never call this."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import urllib.error
import urllib.request
from acquire_legal_bodies import OGL, project_xml, pretty, sha, validate_url, VisibleText

ROOT = Path(__file__).resolve().parents[1]
SEEDS = 'domain-profile/reading-help-law/seeds.json'
MAX_RESPONSE = 8 * 1024 * 1024
MAX_TOTAL = 32 * 1024 * 1024

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class Acquisition:
    """Serial, no retry/redirect; account for failed projections and error bodies."""
    def __init__(self, opener=None):
        self.opener = opener or urllib.request.build_opener(NoRedirect())
        self.total = 0
        self.requests = 0

    def fetch(self, url):
        validate_url(url)
        if self.requests >= 5:
            raise ValueError('Five-request ceiling reached')
        receipt = {'requested_url': url, 'observed_at': datetime.now(timezone.utc).isoformat(),
                   'automatic_retries': 0, 'redirects_followed': 0}
        remaining = min(MAX_RESPONSE, MAX_TOTAL - self.total)
        if remaining <= 0:
            return None, {**receipt, 'status': 'not-requested', 'error': 'Aggregate byte budget exhausted'}
        self.requests += 1
        chunks, response = [], None
        try:
            try:
                response = self.opener.open(urllib.request.Request(url, headers={
                    'User-Agent': 'OKF-DWP bounded independent reading-help research',
                    'Accept-Encoding': 'identity'}), timeout=45)
            except urllib.error.HTTPError as error:
                response = error
            receipt.update(http_status=response.code, resolved_url=response.url,
                           content_type=response.headers.get('Content-Type'))
            length = response.headers.get('Content-Length')
            if length and int(length) > remaining:
                raise ValueError('Advertised response exceeds remaining byte budget')
            count = 0
            while count < remaining:
                block = response.read(min(65536, remaining - count))
                if not block:
                    break
                chunks.append(block)
                count += len(block)
                self.total += len(block)
            data = b''.join(chunks)
            # No probe byte beyond the hard budget. An unknown-length response
            # filling the boundary is conservatively incomplete.
            if count == remaining and (length is None or int(length) != count):
                raise ValueError('Byte boundary reached; response completeness unestablished')
            if length is not None and int(length) != len(data):
                raise ValueError('Content-Length and complete body length differ')
            if response.headers.get('Content-Encoding', 'identity') not in ('identity', ''):
                raise ValueError('Encoded responses are not admitted')
            if response.code != 200:
                raise ValueError('HTTP status is not 200; no redirect or retry')
            receipt['status'] = 'observed'
            return data, {**receipt, 'response_bytes': len(data), 'response_sha256': sha(data)}
        except Exception as error:
            partial = b''.join(chunks)
            return None, {**receipt, 'status': 'failed', 'error_type': type(error).__name__,
                          'error': str(error), 'received_bytes': len(partial),
                          'received_sha256': sha(partial), 'response_complete': False}
        finally:
            if response is not None:
                response.close()

def acquire(root: Path, destination: Path, raw_cache: Path):
    if destination.exists():
        raise ValueError('Snapshot exists; never overwrite retained attempts')
    seeds_raw = (root / SEEDS).read_bytes()
    seeds = json.loads(seeds_raw)
    if seeds['targets'] != ['ukpga/1992/4/section/70', 'uksi/1976/409/regulation/3', 'uksi/1976/409/regulation/6']:
        raise ValueError('Request targets differ from approved bounded increment')
    if seeds['comparison_date'] != '2026-09-20':
        raise ValueError('Comparison date differs')
    session = Acquisition()
    destination.mkdir(parents=True)
    raw_cache.mkdir(parents=True, exist_ok=True)
    files, receipts = [], []
    def retain(path, obj):
        data = pretty(obj)
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        files.append({'path': path, 'bytes': len(data), 'sha256': sha(data)})
    def request(url):
        data, receipt = session.fetch(url)
        receipts.append(receipt)
        if data is not None:
            cached = raw_cache / receipt['response_sha256']
            if cached.exists() and cached.read_bytes() != data:
                raise ValueError('Raw cache hash collision or corruption')
            cached.write_bytes(data)
        return data, receipt
    for target in seeds['targets']:
        url = 'https://www.legislation.gov.uk/' + target + '/' + seeds['comparison_date'] + '/data.xml'
        data, receipt = request(url)
        result = {'schema': 'okf-legal-body-projection.v1', 'target': target, 'status': 'fetch-failed', 'units': []}
        if data is not None:
            try:
                result = project_xml(data, {'target': target, 'units': [target]}, seeds['comparison_date'])
                from build_legal_body_evidence import verify_version
                verify_version(result, seeds['comparison_date'])
            except Exception as error:
                result = {**result, 'status': 'projection-failed', 'error': str(error)}
        result['receipt'] = receipt
        retain('provisions/' + target.replace('/', '--') + '.json', result)
    rights = ['https://www.legislation.gov.uk/ukpga/1992/4/section/70/2026-09-20', OGL]
    for i, url in enumerate(rights):
        data, receipt = request(url)
        visible = ''
        if data is not None:
            parser = VisibleText()
            parser.feed(data.decode('utf-8'))
            visible = ' '.join(' '.join(parser.parts).split())
        expected = ['Open Government Licence', 'Crown'] if i == 0 else ['Open Government Licence', 'acknowledge the source']
        matched = bool(visible) and all(term in visible for term in expected)
        retain('rights/' + str(i + 1) + '.json', {'schema': 'okf-reading-help-law-rights.v1',
            'receipt': receipt, 'notice_observed': matched, 'required_literal_terms': expected,
            'selected_visible_text': visible if i else visible[max(0, visible.find('All content is available under')):][:2000],
            'status': 'observed-notice' if matched else 'unresolved'})
    retain('request-census.json', {'requests': receipts, 'request_count': session.requests,
        'received_bytes': session.total, 'max_requests': 5, 'max_response_bytes': MAX_RESPONSE,
        'max_aggregate_bytes': MAX_TOTAL, 'automatic_retries': 0, 'redirects_followed': 0})
    manifest = {'schema': 'okf-reading-help-law-acquisition.v1', 'comparison_date': seeds['comparison_date'],
        'source_commit': seeds['baseline_dwp_commit'], 'seed_sha256': sha(seeds_raw),
        'acquisition_script_sha256': sha(Path(__file__).read_bytes()),
        'projection_script_sha256': sha((root/'scripts/acquire_legal_bodies.py').read_bytes()),
        'metadata_parser_sha256': sha((root/'scripts/acquire_legal_reconciliation.py').read_bytes()),
        'files': sorted(files, key=lambda f: f['path']),
        'raw_response_policy': 'Exact successful responses retained by SHA-256 in the local audit cache; public XML-tree projections are lossy and not reconstructible raw responses.',
        'applicability': 'unresolved', 'legal_review': 'not-specialist-reviewed'}
    (destination / 'manifest.json').write_bytes(pretty(manifest))
    return manifest

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--acquire', action='store_true')
    p.add_argument('--snapshot', required=True)
    p.add_argument('--raw-cache', type=Path, required=True)
    args = p.parse_args()
    if not args.acquire:
        p.error('Network acquisition requires --acquire')
    if not args.snapshot.startswith('reading-help-law-') or not all(c.isalnum() or c in '-_' for c in args.snapshot):
        p.error('Use a simple, new reading-help-law-* snapshot name')
    result = acquire(ROOT, ROOT/'source'/args.snapshot, args.raw_cache)
    print(json.dumps({'files': len(result['files']), 'snapshot': args.snapshot, 'legal_review': result['legal_review']}))

if __name__ == '__main__':
    main()
