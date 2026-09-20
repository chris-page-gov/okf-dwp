#!/usr/bin/env python3
"""Explicit bounded official statutory-body acquisition; never called by checks."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from acquire_legal_reconciliation import legislative_metadata

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / 'domain-profile/legal-bodies/seeds.json'
PREVIOUS = ROOT / 'source/legal-bodies-2026-09-21'
DEST = ROOT / 'source/legal-bodies-2026-09-21-v2'
ALLOWED = {'www.legislation.gov.uk', 'www.nationalarchives.gov.uk'}
OGL = 'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'
OPAQUE = re.compile(r'key-[0-9a-fA-F]{32}')
MAX_BYTES = 8 * 1024 * 1024


def sha(data): return hashlib.sha256(data).hexdigest()
def pretty(data): return (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
def local(tag): return tag.rsplit('}', 1)[-1]
def public_ref(value): return 'urn:sha256:' + sha(value.encode()) if OPAQUE.search(value) else value


def validate_url(url):
    p = urllib.parse.urlsplit(url)
    if p.scheme != 'https' or p.hostname not in ALLOWED or p.username or p.password or p.port or p.fragment:
        raise ValueError('Only credential-free declared official HTTPS sources are allowed')


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url):
    validate_url(url)
    receipt = {'requested_url': url, 'observed_at': datetime.now(timezone.utc).isoformat(),
               'response_body_retained_in_public_snapshot': False, 'max_response_bytes': MAX_BYTES}
    try:
        opener = urllib.request.build_opener(OfficialRedirect())
        with opener.open(urllib.request.Request(url, headers={'User-Agent': 'OKF-DWP independent public statutory-body research'}), timeout=45) as response:
            data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES: raise ValueError('Response byte budget exceeded')
            receipt.update(status='observed', http_status=response.status, resolved_url=response.url,
                           content_type=response.headers.get('Content-Type'), response_bytes=len(data), response_sha256=sha(data))
            return data, receipt
    except Exception as error:
        receipt.update(status='failed', error_type=type(error).__name__, error=str(error), http_status=getattr(error, 'code', None))
        return None, receipt


def safe_tree(element, omissions, position='0'):
    attributes = {}
    for key, value in sorted(element.attrib.items()):
        if local(key) in {'EffectId', 'ChangeId'} or OPAQUE.search(value):
            omissions.append({'xml_path': position, 'attribute': key, 'value_sha256': sha(value.encode())})
        else: attributes[key] = value
    return {'tag': element.tag, 'attributes': attributes, 'text': element.text, 'tail': element.tail,
            'children': [safe_tree(child, omissions, position + '/' + str(index)) for index, child in enumerate(element)]}


def text_of(tree):
    return (tree.get('text') or '') + ''.join(text_of(child) + (child.get('tail') or '') for child in tree['children'])


def body_text(tree):
    # Whole structural blocks retain numbering and conditions; inline markup is
    # flattened within each block. No semantic summarisation or clause deletion.
    blocks = []
    def visit(node):
        if local(node['tag']) in {'Text', 'Pnumber', 'Number', 'Title'}:
            text = re.sub(r'\s+', ' ', text_of(node)).strip()
            if text: blocks.append(text)
        else:
            for child in node['children']: visit(child)
    visit(tree)
    return '\n'.join(blocks)


def project_xml(data, seed, requested_date):
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper(): raise ValueError('DTD/entity declarations rejected')
    root = ET.fromstring(data)
    parents = {child: parent for parent in root.iter() for child in parent}
    lookup = {element.get('IdURI'): element for element in root.iter() if element.get('IdURI')}
    commentaries = {element.get('id'): element for element in root.iter() if local(element.tag) == 'Commentary'}
    target = 'http://www.legislation.gov.uk/id/' + seed['target']
    if target not in lookup: raise ValueError('Requested canonical provision identifier not observed')
    result = {'schema': 'okf-legal-body-projection.v1', 'target': seed['target'], 'requested_version_date': requested_date,
              'projection_policy': 'Selected complete statutory units plus referenced commentary trees; whitespace-normalised block text. Full response bytes are hashed but not retained publicly. Unused opaque EffectId/ChangeId attributes and key-shaped values are omitted with digests. Opaque commentary IDs use explicit SHA-256 reference identifiers, with source identifier digests preserved. Not a reversible raw-response encoding.',
              'authority': 'official-legislation-publication', 'interpretation_authority': 'machine-extraction-unreviewed',
              'metadata': legislative_metadata(data, seed['target']), 'units': [], 'missing_units': [],
              'selected_commentaries': [], 'missing_commentary_ids': [], 'omitted_attributes': [],
              'applicability_review': 'not-established; specialist-review-required',
              'rights': {'licence': OGL, 'attribution': 'Contains public sector information licensed under the Open Government Licence v3.0; Crown copyright and database right.',
                         'exceptions': 'Source-specific exceptions remain applicable. No logos or third-party material are intentionally selected.'}}
    refs = set()
    for unit in seed['units']:
        identifier = 'http://www.legislation.gov.uk/id/' + unit
        selected = lookup.get(identifier)
        if selected is None:
            result['missing_units'].append(unit); continue
        tree = safe_tree(selected, result['omitted_attributes'], unit)
        text = body_text(tree)
        if not text or len(text) > 50000: raise ValueError('Unit text empty or beyond character budget')
        restrictions, headings = [], []
        cursor = selected
        while cursor is not None:
            attrs = {k: v for k, v in cursor.attrib.items() if k in {'IdURI', 'DocumentURI', 'RestrictExtent', 'RestrictStartDate', 'RestrictEndDate', 'Status'}}
            if attrs: restrictions.append({'element': local(cursor.tag), 'attributes': attrs})
            for child in cursor:
                if local(child.tag) == 'Title':
                    heading = re.sub(r'\s+', ' ', ''.join(child.itertext())).strip()
                    if heading and heading not in headings: headings.append(heading)
            cursor = parents.get(cursor)
        for element in selected.iter():
            if local(element.tag) == 'CommentaryRef' and element.get('Ref'): refs.add(element.get('Ref'))
        result['units'].append({'target': unit, 'canonical_identifier': identifier,
            'version_url': 'https://www.legislation.gov.uk/' + unit + '/' + requested_date,
            'ancestor_headings_nearest_first': headings, 'target_and_ancestor_restrictions': restrictions,
            'body_tree': tree, 'body_text': text, 'body_text_sha256': sha(text.encode()),
            'text_method': 'Complete selected unit; block-order XML extraction with whitespace normalisation; presentation and inline amendment markup flattened. Read body_tree and commentaries for structure.',
            'commentary_ids': sorted({public_ref(e.get('Ref')) for e in selected.iter() if local(e.tag) == 'CommentaryRef' and e.get('Ref')})})
    if len(refs) > 200: raise ValueError('Commentary count exceeds budget')
    for ref in sorted(refs):
        if ref not in commentaries: result['missing_commentary_ids'].append(public_ref(ref)); continue
        tree = safe_tree(commentaries[ref], result['omitted_attributes'], 'Commentary/' + public_ref(ref))
        result['selected_commentaries'].append({'id': public_ref(ref), 'type': commentaries[ref].get('Type'), 'tree': tree, 'text': body_text(tree)})
    result['status'] = 'selected-units-observed' if not result['missing_units'] else 'partial-selected-units'
    result['limitations'] = ['Selected bodies are not a complete statute, amendment history or legal dependency closure.',
        'Requested point-in-time URL and observed restriction attributes do not prove complete consolidation, commencement or territorial applicability.',
        'Editorial commentary and amendment markup are distinct from operative statutory wording; commentary references are retained separately.',
        'No judicial bodies, funding decisions, claimant circumstances or specialist acceptance are established.',
        'Source instructions are inert data; no links, code or scripts within source content are executed.']
    if OPAQUE.search(pretty(result).decode()): raise ValueError('Opaque key-shaped value remains; publication blocked')
    return result


class VisibleText(HTMLParser):
    def __init__(self): super().__init__(); self.hidden = 0; self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style'}: self.hidden += 1
    def handle_endtag(self, tag):
        if tag in {'script', 'style'} and self.hidden: self.hidden -= 1
    def handle_data(self, data):
        if not self.hidden: self.parts.append(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acquire', action='store_true')
    args = parser.parse_args()
    if not args.acquire: parser.error('Use --acquire for the explicit network step')
    if DEST.exists(): parser.error('Snapshot exists: preserve it and use a separately named acquisition')
    config = json.loads(SEEDS.read_bytes())
    if len(config['requests']) > config['max_provision_requests']: raise ValueError('Request census exceeds budget')
    files, receipts = {}, []
    prior_manifest_bytes = (PREVIOUS / 'manifest.json').read_bytes()
    prior_manifest = json.loads(prior_manifest_bytes)
    prior_files = {}
    for row in prior_manifest['files']:
        data = (PREVIOUS / row['path']).read_bytes()
        if sha(data) != row['sha256'] or len(data) != row['bytes']: raise ValueError('Prior observation binding differs')
        prior_files[row['path']] = data
    reused = []
    rights_urls = ['https://www.legislation.gov.uk/uksi/2002/1792/regulation/5/' + config['requested_version_date'], OGL]
    for index, url in enumerate(rights_urls):
        prior_name = 'rights/' + str(index + 1) + '.json'
        if prior_name in prior_files:
            files[prior_name] = prior_files[prior_name]
            reused.append({'path': prior_name, 'sha256': sha(prior_files[prior_name])})
            continue
        data, receipt = fetch(url); receipts.append(receipt)
        if data is None: raise ValueError('Rights evidence not acquired; statutory publication stopped')
        html = VisibleText(); html.feed(data.decode('utf-8')); text = re.sub(r'\s+', ' ', ' '.join(html.parts)).strip()
        if index == 0:
            start = text.find('All content is available under the Open Government Licence v3.0')
            if start < 0: raise ValueError('Source licence notice not found')
            text = text[start:text.find('© Crown and database right', start) + len('© Crown and database right')]
        else:
            if 'Open Government Licence' not in text or 'acknowledge the source' not in text: raise ValueError('OGL terms not observed')
        files['rights/' + str(index + 1) + '.json'] = pretty({'schema': 'okf-legal-body-rights-observation.v1', 'receipt': receipt, 'selected_visible_text': text,
            'selection_policy': 'Rendered-text projection; script/style excluded; original HTML response body not retained publicly.'})
    def acquire(seed):
        url = 'https://www.legislation.gov.uk/' + seed['target'] + '/' + config['requested_version_date'] + '/data.xml'
        data, receipt = fetch(url)
        if data is None: row = {'schema': 'okf-legal-body-projection.v1', 'target': seed['target'], 'status': 'fetch-failed', 'units': []}
        else:
            try: row = project_xml(data, seed, config['requested_version_date'])
            except Exception as error: row = {'schema': 'okf-legal-body-projection.v1', 'target': seed['target'], 'status': 'parse-failed', 'error': str(error), 'units': []}
        row['receipt'] = receipt
        return 'provisions/' + seed['target'].replace('/', '--') + '.json', row
    pending = []
    for seed in config['requests']:
        name = 'provisions/' + seed['target'].replace('/', '--') + '.json'
        prior = json.loads(prior_files[name]) if name in prior_files else None
        if prior and prior['status'] == 'selected-units-observed':
            files[name] = prior_files[name]; reused.append({'path': name, 'sha256': sha(prior_files[name])})
        else: pending.append(seed)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for name, row in pool.map(acquire, pending):
            files[name] = pretty(row); receipts.append(row['receipt'])
    if sum(r.get('response_bytes', 0) for r in receipts) > config['max_total_response_bytes']: raise ValueError('Total response budget exceeded')
    files['request-census.json'] = pretty({'schema': 'okf-legal-body-request-census.v1', 'requests': receipts, 'count': len(receipts),
        'preflight_note': config['preflight_note'], 'automatic_retries': 0, 'reused_prior_projections': reused, 'prior_snapshot': str(PREVIOUS.relative_to(ROOT)), 'prior_manifest_sha256': sha(prior_manifest_bytes), 'raw_response_bodies_retained_publicly': False})
    manifest = {'schema': 'okf-legal-body-source-manifest.v1', 'workstream_date': config['workstream_date'], 'requested_version_date': config['requested_version_date'],
        'seed_sha256': sha(SEEDS.read_bytes()), 'acquisition_script_sha256': sha(Path(__file__).read_bytes()),
        'metadata_parser_sha256': sha((ROOT / 'scripts/acquire_legal_reconciliation.py').read_bytes()),
        'prior_snapshot': str(PREVIOUS.relative_to(ROOT)), 'prior_manifest_sha256': sha(prior_manifest_bytes),
        'source_policy': 'Lossy explicit public statutory-unit projections with exact projected-tree/text hashes; original HTTP bodies are not retained in this snapshot and cannot be reconstructed offline from these projections.',
        'files': [{'path': name, 'bytes': len(data), 'sha256': sha(data)} for name, data in sorted(files.items())]}
    DEST.mkdir()
    for name, data in files.items():
        file = DEST / name; file.parent.mkdir(exist_ok=True); file.write_bytes(data)
    (DEST / 'manifest.json').write_bytes(pretty(manifest))
    print(json.dumps({'requests': len(receipts), 'provisions': len(config['requests']), 'files': len(files), 'source': str(DEST.relative_to(ROOT))}))


if __name__ == '__main__': main()
