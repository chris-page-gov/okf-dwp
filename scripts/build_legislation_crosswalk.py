#!/usr/bin/env python3
"""Build a hash-bound DWP statutory-reference to legislation-work crosswalk."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path('evaluation/retrieval-gate/legislation-crosswalk.json')
EXPECTED_LEGISLATION_COMMIT = '9830fde2d32052f10713298f16b8ab1e321b1928'
EXPECTED_DWP_INPUT_COMMIT = '77ef16047415ee48dcb93b80adf1ba057ea00d9b'
CATALOGUE_MANIFEST = 'data/records/manifest.json'
CHECKSUMS = 'bundle/checksums.json'

INPUT_PATHS = [
    'domain-profile/legal-reconciliation/seeds.json',
    'evaluation/legal-reconciliation/citations.json',
    'evaluation/legal-reconciliation/coverage.json',
    'evaluation/legal-reconciliation/tribunal-discovery.json',
    'domain-profile/legal-bodies/seeds.json',
    'domain-profile/legal-bodies/coverage.json',
    'domain-profile/legal-bodies/context-overlay.json',
    'domain-profile/legal-bodies/navigation.json',
    'domain-profile/legal-reconciliation/references.yamlld',
    'domain-profile/reading-help-law/seeds.json',
    'evaluation/staff-questions/cases.json',
    'scripts/build_legal_body_evidence.py',
    'source/legal-discovery-2026-09-20/manifest.json',
    'source/legal-bodies-2026-09-21/manifest.json',
    'source/legal-bodies-2026-09-21-v2/manifest.json',
]


class CrosswalkError(ValueError):
    """Raised when an identity or provenance binding does not verify."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise CrosswalkError(f'Cannot read JSON input {path}: {exc}') from exc


def git(root: Path, *args: str) -> str:
    result = subprocess.run(['git', '-C', str(root), *args], check=False,
                            capture_output=True, text=True)
    if result.returncode:
        command = ' '.join(args)
        raise CrosswalkError(f'Git verification failed ({command}): {result.stderr.strip()}')
    return result.stdout.strip()


def verify_git_object(root: Path, commit: str, relative: str, raw: bytes | None = None) -> dict:
    """Bind a working-tree file to an immutable blob in the specified commit."""
    path = root / relative
    try:
        data = path.read_bytes() if raw is None else raw
    except OSError as exc:
        raise CrosswalkError(f'Missing hash-bound file {relative}: {exc}') from exc
    blob = git(root, 'rev-parse', f'{commit}:{relative}')
    working_blob = git(root, 'hash-object', str(path))
    if blob != working_blob:
        raise CrosswalkError(f'Working-tree file differs from Git object {commit}:{relative}')
    object_bytes = subprocess.run(['git', '-C', str(root), 'cat-file', 'blob', blob],
                                  check=False, capture_output=True)
    if object_bytes.returncode or object_bytes.stdout != data:
        raise CrosswalkError(f'Git blob bytes do not match {relative}')
    return {'path': relative, 'bytes': len(data), 'sha256': sha256(data),
            'git_blob': blob, 'git_commit': commit, 'matches_immutable_git_object': True}


def legislation_work_path(target: str) -> str:
    """Return the work path for a work or provision reference."""
    if not isinstance(target, str):
        raise CrosswalkError('Statutory target must be a string')
    parts = target.strip('/').split('/')
    if len(parts) < 3 or parts[0] not in {'ukpga', 'uksi'}:
        raise CrosswalkError(f'Invalid legislation work or provision identifier: {target}')
    if not parts[1].isdigit() or not parts[2].isdigit():
        raise CrosswalkError(f'Invalid legislation work identity in target: {target}')
    return '/'.join(parts[:3])


def _fnv_bucket(route: str) -> str:
    value = 0x811C9DC5
    for byte in route.encode('utf-8'):
        value ^= byte
        value = (value * 0x01000193) & 0xFFFFFFFF
    return f'{(value >> 24) & 0xFF:02x}'


def _version_date(document_uri: str | None) -> str | None:
    if not isinstance(document_uri, str):
        return None
    match = re.search(r'/(20\d{2}-\d{2}-\d{2})$', document_uri)
    return match.group(1) if match else None


class CatalogueReader:
    """Read only the hash-bound work locator buckets and chunks we need."""

    def __init__(self, legislation_root: Path, expected_commit: str | None = EXPECTED_LEGISLATION_COMMIT,
                 verify_git_objects: bool = True):
        self.root = legislation_root.resolve()
        self.bundle = self.root / 'bundle'
        self.verify_git_objects = verify_git_objects
        self.commit = git(self.root, 'rev-parse', 'HEAD')
        if expected_commit and self.commit != expected_commit:
            raise CrosswalkError(f'Legislation repository HEAD {self.commit} differs from pinned {expected_commit}')
        self.bindings: dict[str, dict] = {}
        self.bucket_cache: dict[str, dict] = {}
        self.chunk_cache: dict[int, list] = {}
        self.manifest_path = CATALOGUE_MANIFEST
        manifest_raw = self._read_bound(self.manifest_path)
        self.manifest_sha256 = sha256(manifest_raw)
        self.manifest = json.loads(manifest_raw)
        checksums_raw = self._read_bound(CHECKSUMS)
        self.checksums = json.loads(checksums_raw)
        expected = self.checksums.get('files', {}).get('data/records/manifest.json', {})
        if expected.get('sha256') != self.manifest_sha256 or expected.get('bytes') != len(manifest_raw):
            raise CrosswalkError('Catalogue work locator manifest differs from bundle/checksums.json')
        if self.manifest.get('schema') != 'okf-record-locator-sharded.v1':
            raise CrosswalkError('Unexpected work locator manifest schema')
        if self.manifest.get('algorithm') != 'fnv1a32-prefix-2':
            raise CrosswalkError('Unexpected work locator hashing algorithm')
        if not isinstance(self.manifest.get('records'), int) or not self.manifest.get('buckets'):
            raise CrosswalkError('Work locator manifest is incomplete')
        self.snapshot = self.manifest.get('snapshot')

    def _read_bound(self, relative: str, expected: dict | None = None) -> bytes:
        path = self.bundle / relative if relative.startswith('data/') else self.root / relative
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise CrosswalkError(f'Missing legislation catalogue file {relative}: {exc}') from exc
        if expected:
            if len(raw) != expected.get('compressed_bytes', expected.get('bytes')):
                raise CrosswalkError(f'Byte count mismatch for legislation catalogue file {relative}')
            if sha256(raw) != expected.get('sha256'):
                raise CrosswalkError(f'SHA-256 mismatch for legislation catalogue file {relative}')
        if self.verify_git_objects:
            binding = verify_git_object(self.root, self.commit, f'bundle/{relative}' if relative.startswith('data/') else relative, raw)
        else:
            binding = {'path': f'bundle/{relative}' if relative.startswith('data/') else relative,
                       'bytes': len(raw), 'sha256': sha256(raw), 'matches_immutable_git_object': False}
        self.bindings[binding['path']] = binding
        return raw

    def work(self, work_path: str) -> tuple[dict, dict]:
        if not re.fullmatch(r'(?:ukpga|uksi)/\d{4}/\d+', work_path):
            raise CrosswalkError(f'Invalid work id: {work_path}')
        route = 'dataset/' + work_path.replace('/', '-')
        bucket_id = _fnv_bucket(route)
        bucket_meta = self.manifest['buckets'].get(bucket_id)
        if not bucket_meta:
            raise CrosswalkError(f'No catalogue bucket for work route {route}')
        if bucket_id not in self.bucket_cache:
            raw = self._read_bound(bucket_meta['path'], bucket_meta)
            try:
                bucket = json.loads(gzip.decompress(raw))
            except (OSError, json.JSONDecodeError) as exc:
                raise CrosswalkError(f'Cannot decode catalogue bucket {bucket_id}: {exc}') from exc
            self.bucket_cache[bucket_id] = bucket
        location = self.bucket_cache[bucket_id].get(route)
        if not isinstance(location, list) or len(location) != 2:
            raise CrosswalkError(f'Catalogue work route not found: {route}')
        chunk_index, record_index = location
        if not isinstance(chunk_index, int) or not isinstance(record_index, int):
            raise CrosswalkError(f'Invalid catalogue locator for {route}')
        chunks = self.manifest.get('record_chunks', [])
        if chunk_index < 0 or chunk_index >= len(chunks):
            raise CrosswalkError(f'Invalid catalogue chunk index for {route}')
        if chunk_index not in self.chunk_cache:
            chunk_meta = chunks[chunk_index]
            raw = self._read_bound(chunk_meta['path'], chunk_meta)
            try:
                rows = json.loads(gzip.decompress(raw))
            except (OSError, json.JSONDecodeError) as exc:
                raise CrosswalkError(f'Cannot decode catalogue work shard {chunk_meta["path"]}: {exc}') from exc
            if len(rows) != chunk_meta.get('records'):
                raise CrosswalkError(f'Record count mismatch in catalogue work shard {chunk_meta["path"]}')
            self.chunk_cache[chunk_index] = rows
        rows = self.chunk_cache[chunk_index]
        if record_index < 0 or record_index >= len(rows):
            raise CrosswalkError(f'Invalid catalogue record index for {route}')
        record = rows[record_index]
        expected_id = f'https://www.legislation.gov.uk/id/{work_path}'
        if record.get('route') != route or record.get('id') != expected_id:
            raise CrosswalkError(f'Work identity mismatch for {work_path}')
        chunk_meta = chunks[chunk_index]
        locator_binding = self.bindings.get(f'bundle/{bucket_meta["path"]}')
        chunk_binding = self.bindings.get(f'bundle/{chunk_meta["path"]}')
        integrity = {'manifest_path': self.manifest_path, 'manifest_sha256': self.manifest_sha256,
                     'bucket_path': bucket_meta['path'], 'bucket_sha256': bucket_meta['sha256'],
                     'bucket_git_blob': locator_binding.get('git_blob') if locator_binding else None,
                     'work_shard_path': chunk_meta['path'], 'work_shard_sha256': chunk_meta['sha256'],
                     'work_shard_git_blob': chunk_binding.get('git_blob') if chunk_binding else None,
                     'work_chunk_index': chunk_index, 'record_index': record_index}
        return record, integrity


def _input_inventory(root: Path, commit: str, paths: list[str]) -> tuple[dict[str, dict], list[dict]]:
    values: dict[str, dict] = {}
    inventory: list[dict] = []
    for relative in dict.fromkeys(paths):
        info = verify_git_object(root, commit, relative)
        inventory.append(info)
        if relative.endswith('.json'):
            values[relative] = json.loads((root / relative).read_text(encoding='utf-8'))
    return values, inventory


def _target_stem(target: str) -> str:
    return target.replace('/', '--') + '.json'


def _source_manifest_index(manifest: dict) -> dict[str, dict]:
    return {row['path']: row for row in manifest.get('files', [])}


def _validate_manifest_file(root: Path, commit: str, path: str, expected: dict) -> dict:
    info = verify_git_object(root, commit, path)
    if info['bytes'] != expected.get('bytes') or info['sha256'] != expected.get('sha256'):
        raise CrosswalkError(f'DWP evidence manifest mismatch for {path}')
    return info


def _citation_records(citations: dict, candidates: dict[str, dict], dwp_root: Path, dwp_commit: str,
                      file_bindings: dict[str, dict], citations_input: dict) -> tuple[dict[str, list], list]:
    result: dict[str, list] = {}
    case_mentions: list[dict] = []
    case_pattern = re.compile(r'\bR\(\s*[A-Z]+\s*\)\s*\d+/\d+\b', re.I)
    for page_index, page in enumerate(citations.get('pages', [])):
        candidate = candidates.get(page.get('source_candidate_id'))
        if not candidate:
            raise CrosswalkError(f'Unknown source candidate on cited page {page.get("route")}')
        page_path = candidate['pages_path']
        pdf_path = candidate['source_pdf']
        for source_path, expected_hash in ((page_path, candidate['pages_sha256']),
                                           (pdf_path, candidate['source_sha256'])):
            binding = file_bindings.get(source_path)
            if binding is None:
                binding = verify_git_object(dwp_root, dwp_commit, source_path)
                file_bindings[source_path] = binding
            if binding['sha256'] != expected_hash:
                raise CrosswalkError(f'Candidate source hash mismatch: {source_path}')
        pages_doc = read_json(dwp_root / page_path)
        source_page = next((row for row in pages_doc.get('pages', [])
                            if row.get('page') == candidate.get('page')), None)
        if not source_page or sha256(source_page.get('text', '').encode('utf-8')) != page.get('page_literal_sha256'):
            raise CrosswalkError(f'Citation page literal differs from frozen page source: {page.get("route")}')
        if candidate.get('route') != page.get('route') or candidate.get('literal_sha256') != page.get('page_literal_sha256'):
            raise CrosswalkError(f'Citation page identity differs from source candidate: {page.get("route")}')
        for citation_index, citation in enumerate(page.get('citations', [])):
            literal = citation.get('literal', '')
            if not literal or literal not in source_page['text']:
                raise CrosswalkError(f'Citation literal not present at frozen source page: {citation.get("id")}')
            if sha256(literal.encode('utf-8')) != citation.get('literal_sha256'):
                raise CrosswalkError(f'Citation literal hash mismatch: {citation.get("id")}')
            citation_base = {'citation_id': citation.get('id'), 'original_citation': literal,
                'citation_sha256': citation.get('literal_sha256'), 'page_source_candidate_id': page.get('source_candidate_id'),
                'page_route': page.get('route'), 'page_url': page.get('source_url'),
                'page_pdf_sha256': candidate.get('source_sha256'), 'page_file': page_path,
                'page_file_sha256': candidate.get('pages_sha256'), 'page_literal_sha256': page.get('page_literal_sha256'),
                'page_locator': candidate.get('locator'), 'page_publication_date': page.get('source_publication_date'),
                'citation_offsets': {'start': citation.get('start'), 'end': citation.get('end'),
                                     'encoding': citations.get('offset_encoding')},
                'source': {'file': 'evaluation/legal-reconciliation/citations.json',
                           'file_sha256': citations_input['sha256'], 'git_commit': dwp_commit,
                           'git_blob': citations_input['git_blob'],
                           'json_locator': f'$.pages[{page_index}].citations[{citation_index}]'}}
            for mention in case_pattern.finditer(literal):
                case_mentions.append({**citation_base, 'case_law_reference': mention.group(0),
                    'status': 'case-law-string-excluded-from-statutory-work-crosswalk'})
            for reference in citation.get('references', []):
                for provision in reference.get('provisions', []):
                    target = provision.get('target')
                    if not target:
                        continue
                    result.setdefault(target, []).append({**citation_base,
                        'literal_alias': reference.get('literal_alias'),
                        'literal_locator': provision.get('literal_locator'),
                        'work_seed_id': reference.get('work_id'),
                        'provision_identifier': provision.get('provision_id'),
                        'provision_verification_status': provision.get('verification_status'),
                        'finer_locator_status': provision.get('finer_locator_status')})
    return result, case_mentions


def _body_index(dwp_root: Path, dwp_commit: str, body_manifest: dict,
                body_manifest_inventory: dict[str, dict]) -> tuple[dict[str, list], list[dict]]:
    manifest_index = _source_manifest_index(body_manifest)
    body_targets: dict[str, list] = {}
    evidence_files = []
    for rel, metadata in manifest_index.items():
        if not rel.startswith('provisions/'):
            continue
        full = f'source/legal-bodies-2026-09-21-v2/{rel}'
        binding = _validate_manifest_file(dwp_root, dwp_commit, full, metadata)
        evidence_files.append(binding)
        document = json.loads((dwp_root / full).read_text(encoding='utf-8'))
        if document.get('schema') != 'okf-legal-body-projection.v1':
            raise CrosswalkError(f'Unexpected DWP legal-body projection schema in {full}')
        for unit_index, unit in enumerate(document.get('units', [])):
            target = unit.get('target')
            body_text = unit.get('body_text')
            if not target or not isinstance(body_text, str) or not body_text:
                continue
            if sha256(body_text.encode('utf-8')) != unit.get('body_text_sha256'):
                raise CrosswalkError(f'DWP projected provision text hash mismatch: {target}')
            body_targets.setdefault(target, []).append({
                'source_file': full, 'source_file_sha256': binding['sha256'],
                'source_git_blob': binding['git_blob'], 'json_locator': f'$.units[{unit_index}]',
                'body_text_sha256': unit['body_text_sha256'], 'body_text_characters': len(body_text),
                'body_text_method': unit.get('text_method'),
                'body_tree_present': bool(unit.get('body_tree')),
                'requested_version_date': document.get('requested_version_date'),
                'response_sha256': document.get('receipt', {}).get('response_sha256'),
                'response_body_retained_in_public_snapshot': document.get('receipt', {}).get('response_body_retained_in_public_snapshot'),
                'projection_policy': document.get('projection_policy'),
                'applicability_review': document.get('applicability_review'),
                'extent_status': unit.get('extent_status'),
                'specialist_review_status': 'pending-specialist-review',
            })
    return body_targets, evidence_files


def _legal_metadata_index(dwp_root: Path, dwp_commit: str, manifest: dict,
                          manifest_binding: dict) -> tuple[dict[str, dict], list[dict]]:
    index = _source_manifest_index(manifest)
    observations: dict[str, dict] = {}
    evidence_files = []
    for path, metadata in index.items():
        if not path.startswith('legislation/') or not path.endswith('.json'):
            continue
        full = 'source/legal-discovery-2026-09-20/' + path
        binding = _validate_manifest_file(dwp_root, dwp_commit, full, metadata)
        evidence_files.append(binding)
        row = read_json(dwp_root / full)
        target = row.get('target')
        if not target:
            continue
        receipt = row.get('receipt', {})
        observations[target] = {
            'status': row.get('status'), 'schema': row.get('schema'),
            'requested_version_date': row.get('requested_version_date'),
            'observed_title': row.get('metadata', {}).get('title'),
            'observed_identifier': row.get('metadata', {}).get('target_identifier_observed'),
            'document_identifier': row.get('metadata', {}).get('document_identifier'),
            'requested_url': receipt.get('requested_url'), 'resolved_url': receipt.get('resolved_url'),
            'http_status': receipt.get('http_status'), 'response_sha256': receipt.get('response_sha256'),
            'response_bytes': receipt.get('response_bytes'),
            'response_body_retained': receipt.get('response_body_retained'),
            'source_file': full, 'source_file_sha256': binding['sha256'], 'source_git_blob': binding['git_blob'],
            'manifest_path': manifest_binding['path'], 'manifest_sha256': manifest_binding['sha256'],
            'json_locator': '$.metadata',
        }
    return observations, evidence_files


def _add_source(rows: dict[str, list], target: str, source: dict) -> None:
    rows.setdefault(target, []).append(source)


def _clean_duplicates(rows: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for row in rows:
        marker = json.dumps(row, ensure_ascii=False, sort_keys=True)
        if marker not in seen:
            seen.add(marker)
            result.append(row)
    return result


def _unresolved_rows(*seed_docs: dict) -> list[dict]:
    out = []
    for name, doc in zip(('legal-reconciliation', 'legal-bodies', 'reading-help-law'), seed_docs):
        for index, text in enumerate(doc.get('unresolved_literal_policy', [])):
            kind = 'case-law-unresolved' if re.search(r'R\s*\(', text, re.I) else 'statutory-reference-unresolved'
            out.append({'source_seed': name, 'json_locator': f'$.unresolved_literal_policy[{index}]',
                        'original_unresolved_text': text, 'status': kind + '-not-mapped-to-a-work-or-provision'})
    return out


def build_crosswalk(dwp_root: Path, legislation_root: Path,
                    expected_legislation_commit: str | None = EXPECTED_LEGISLATION_COMMIT,
                    verify_git_objects: bool = True) -> dict:
    dwp_root = dwp_root.resolve()
    dwp_commit = EXPECTED_DWP_INPUT_COMMIT
    dwp_docs, dwp_file_inventory = _input_inventory(dwp_root, dwp_commit, INPUT_PATHS)
    recon_seeds = dwp_docs['domain-profile/legal-reconciliation/seeds.json']
    citations = dwp_docs['evaluation/legal-reconciliation/citations.json']
    legal_recon_coverage = dwp_docs['evaluation/legal-reconciliation/coverage.json']
    tribunal = dwp_docs['evaluation/legal-reconciliation/tribunal-discovery.json']
    legal_body_seeds = dwp_docs['domain-profile/legal-bodies/seeds.json']
    legal_body_coverage = dwp_docs['domain-profile/legal-bodies/coverage.json']
    context_overlay = dwp_docs['domain-profile/legal-bodies/context-overlay.json']
    reading_help = dwp_docs['domain-profile/reading-help-law/seeds.json']
    question_registry = dwp_docs['evaluation/staff-questions/cases.json']
    discovery_manifest = dwp_docs['source/legal-discovery-2026-09-20/manifest.json']
    body_manifest = dwp_docs['source/legal-bodies-2026-09-21-v2/manifest.json']
    dwp_info = {row['path']: row for row in dwp_file_inventory}

    if body_manifest.get('seed_sha256') != dwp_info['domain-profile/legal-bodies/seeds.json']['sha256']:
        raise CrosswalkError('Legal-body acquisition manifest does not bind to its DWP seed file')
    coverage_bindings = {row['path']: row['sha256'] for row in legal_body_coverage.get('bindings', [])}
    for path in ('source/legal-bodies-2026-09-21-v2/manifest.json',
                 'source/legal-bodies-2026-09-21/manifest.json',
                 'domain-profile/legal-bodies/seeds.json',
                 'evaluation/staff-questions/cases.json'):
        if path in coverage_bindings:
            actual_path = path
            if dwp_info.get(actual_path) is None:
                dwp_info[actual_path] = verify_git_object(dwp_root, dwp_commit, actual_path)
                dwp_file_inventory.append(dwp_info[actual_path])
            if dwp_info[actual_path]['sha256'] != coverage_bindings[path]:
                raise CrosswalkError(f'Legal-body coverage binding differs for {path}')

    file_bindings = {row['path']: row for row in dwp_file_inventory}
    candidates = {row['id']: row for row in question_registry.get('source_candidates', [])}
    citation_map, case_mentions = _citation_records(citations, candidates, dwp_root, dwp_commit,
                                                    file_bindings, dwp_info['evaluation/legal-reconciliation/citations.json'])
    dwp_file_inventory = list(file_bindings.values())

    body_manifest_binding = dwp_info['source/legal-bodies-2026-09-21-v2/manifest.json']
    body_targets, body_files = _body_index(dwp_root, dwp_commit, body_manifest, body_manifest_binding)
    metadata_manifest_binding = dwp_info['source/legal-discovery-2026-09-20/manifest.json']
    metadata_targets, metadata_files = _legal_metadata_index(dwp_root, dwp_commit, discovery_manifest,
                                                               metadata_manifest_binding)
    for row in body_files + metadata_files:
        file_bindings[row['path']] = row

    seed_works = recon_seeds.get('works', [])
    work_aliases: dict[str, list[dict]] = {}
    for index, row in enumerate(seed_works):
        path = row['work_path']
        work_aliases.setdefault(path, []).append({'source_kind': 'legal-reconciliation-work-seed',
            'seed_id': row['id'], 'expected_title': row['title'], 'aliases': row.get('aliases', []),
            'interpretation': row.get('interpretation'),
            'source': {'file': 'domain-profile/legal-reconciliation/seeds.json',
                       'file_sha256': dwp_info['domain-profile/legal-reconciliation/seeds.json']['sha256'],
                       'git_commit': dwp_commit, 'git_blob': dwp_info['domain-profile/legal-reconciliation/seeds.json']['git_blob'],
                       'json_locator': f'$.works[{index}]'}})
    for index, row in enumerate(reading_help.get('works', [])):
        path = legislation_work_path(row['target'])
        support = row.get('support', {})
        pages_path = support.get('pages_path')
        support_binding = None
        if pages_path:
            support_binding = file_bindings.get(pages_path)
            if support_binding is None:
                support_binding = verify_git_object(dwp_root, dwp_commit, pages_path)
                file_bindings[pages_path] = support_binding
            if support_binding['sha256'] != support.get('pages_sha256'):
                raise CrosswalkError(f'Reading-help source-page hash mismatch: {pages_path}')
            start, end = support.get('start_utf8'), support.get('end_utf8')
            if not isinstance(start, int) or not isinstance(end, int) or end < start:
                raise CrosswalkError(f'Invalid reading-help byte locator for {row["target"]}')
            page_doc = read_json(dwp_root / pages_path)
            support_page = next((item for item in page_doc.get('pages', [])
                                 if item.get('page') == support.get('page')), None)
            if not support_page or not isinstance(support_page.get('text'), str):
                raise CrosswalkError(f'Reading-help source page is missing: {pages_path} page {support.get("page")}')
            page_bytes = support_page['text'].encode('utf-8')
            span = page_bytes[start:end]
            if sha256(span) != support.get('literal_sha256'):
                raise CrosswalkError(f'Reading-help literal hash mismatch for {row["target"]}')
            if span.decode('utf-8') != support.get('quote'):
                raise CrosswalkError(f'Reading-help quote differs from its exact source-page locator for {row["target"]}')
        work_aliases.setdefault(path, []).append({'source_kind': 'reading-help-law-work-seed',
            'work_id': row.get('work_id'), 'expected_title': row.get('title'),
            'abbreviation': row.get('abbreviation'), 'mapping_status': row.get('mapping_status'),
            'support': {'pages_path': pages_path, 'pages_sha256': support.get('pages_sha256'),
                        'page': support.get('page'), 'start_utf8': support.get('start_utf8'),
                        'end_utf8': support.get('end_utf8'), 'literal_sha256': support.get('literal_sha256'),
                        'source_git_blob': support_binding.get('git_blob') if support_binding else None},
            'source': {'file': 'domain-profile/reading-help-law/seeds.json',
                       'file_sha256': dwp_info['domain-profile/reading-help-law/seeds.json']['sha256'],
                       'git_commit': dwp_commit, 'git_blob': dwp_info['domain-profile/reading-help-law/seeds.json']['git_blob'],
                       'json_locator': f'$.works[{index}]'}})

    sources_by_target: dict[str, list] = {}
    for index, row in enumerate(recon_seeds.get('provisions', [])):
        target = row['target']
        work_path = legislation_work_path(target)
        if work_path not in {item['work_path'] for item in seed_works}:
            raise CrosswalkError(f'Provision seed references an unregistered work: {target}')
        _add_source(sources_by_target, target, {'source_kind': 'legal-reconciliation-provision-seed',
            'work_seed_id': row.get('work_id'), 'target': target,
            'source': {'file': 'domain-profile/legal-reconciliation/seeds.json',
                       'file_sha256': dwp_info['domain-profile/legal-reconciliation/seeds.json']['sha256'],
                       'git_commit': dwp_commit, 'git_blob': dwp_info['domain-profile/legal-reconciliation/seeds.json']['git_blob'],
                       'json_locator': f'$.provisions[{index}]'}})
    for index, row in enumerate(legal_body_seeds.get('requests', [])):
        target = row['target']
        work_path = legislation_work_path(target)
        for link_index, link in enumerate(row.get('citation_links', [])):
            source = {'source_kind': 'legal-body-literal-citation-request', 'target': target,
                'selection_status': row.get('selection_status'), 'citation_id': link.get('citation_id'),
                'original_citation': link.get('literal'), 'citation_sha256': link.get('literal_sha256'),
                'page_literal_sha256': link.get('page_literal_sha256'),
                'source_candidate_id': link.get('source_candidate_id'), 'source_route': link.get('source_route'),
                'source_url': link.get('source_url'), 'case_ids': link.get('case_ids', []),
                'source': {'file': 'domain-profile/legal-bodies/seeds.json',
                           'file_sha256': dwp_info['domain-profile/legal-bodies/seeds.json']['sha256'],
                           'git_commit': dwp_commit, 'git_blob': dwp_info['domain-profile/legal-bodies/seeds.json']['git_blob'],
                           'json_locator': f'$.requests[{index}].citation_links[{link_index}]'}}
            _add_source(sources_by_target, target, source)
        if not row.get('citation_links'):
            _add_source(sources_by_target, target, {'source_kind': 'additional-bounded-context-proposal',
                'target': target, 'selection_status': row.get('selection_status'),
                'proposal_rationale': legal_body_seeds.get('additional_context_rationale', {}).get(target),
                'source': {'file': 'domain-profile/legal-bodies/seeds.json',
                           'file_sha256': dwp_info['domain-profile/legal-bodies/seeds.json']['sha256'],
                           'git_commit': dwp_commit, 'git_blob': dwp_info['domain-profile/legal-bodies/seeds.json']['git_blob'],
                           'json_locator': f'$.requests[{index}]'}})
        if work_path not in work_aliases:
            work_aliases[work_path] = [{'source_kind': 'provision-work-path-derived-from-bounded-request',
                'source': {'file': 'domain-profile/legal-bodies/seeds.json',
                           'file_sha256': dwp_info['domain-profile/legal-bodies/seeds.json']['sha256'],
                           'git_commit': dwp_commit, 'git_blob': dwp_info['domain-profile/legal-bodies/seeds.json']['git_blob'],
                           'json_locator': f'$.requests[{index}].target'}}]
    for index, target in enumerate(reading_help.get('targets', [])):
        _add_source(sources_by_target, target, {'source_kind': 'reading-help-law-provision-target',
            'target': target, 'mapping_status': 'project-authored-navigation-target; not an entitlement assertion',
            'source': {'file': 'domain-profile/reading-help-law/seeds.json',
                       'file_sha256': dwp_info['domain-profile/reading-help-law/seeds.json']['sha256'],
                       'git_commit': dwp_commit, 'git_blob': dwp_info['domain-profile/reading-help-law/seeds.json']['git_blob'],
                       'json_locator': f'$.targets[{index}]'}})

    target_paths = set(sources_by_target)
    work_paths = set(work_aliases) | {legislation_work_path(target) for target in target_paths}
    catalogue = CatalogueReader(legislation_root, expected_legislation_commit, verify_git_objects)
    work_records = {}
    for path in sorted(work_paths):
        record, integrity = catalogue.work(path)
        work_records[path] = (record, integrity)

    work_rows = []
    title_exact_matches = 0
    for path in sorted(work_paths):
        record, integrity = work_records[path]
        aliases = work_aliases.get(path, [])
        expected_titles = sorted({row['expected_title'] for row in aliases if row.get('expected_title')})
        title_matches = [title for title in expected_titles if title == record.get('title')]
        title_exact_matches += int(bool(title_matches))
        work_rows.append({'work_path': path, 'work_uri': record['id'], 'route': record['route'],
            'catalogue_title': record.get('title'), 'seed_titles': expected_titles,
            'seed_title_exact_match': bool(title_matches) if expected_titles else None,
            'aliases_and_source_contexts': aliases,
            'catalogued_version_uri': record.get('document_uri'),
            'catalogued_version_date': _version_date(record.get('document_uri')),
            'catalogued_version_date_meaning': 'Date from the catalogue record document_uri only; not a finding about current law, in-force effect or commencement.',
            'catalogue_snapshot': catalogue.snapshot,
            'metadata_modified': record.get('metadata_modified'),
            'metadata_modified_meaning': 'Catalogue metadata modification timestamp; not a legislative effective date.',
            'resource_count_metadata': record.get('resource_count'),
            'resources_embedded_in_work_record': bool(record.get('resources')),
            'record_type': record.get('record_type'),
            'provision_body_present_in_work_record': False,
            'interpretation': 'Exact work identity and catalogue metadata match only. The catalogue work record is not provision text.',
            'catalogue_integrity': integrity})

    provision_rows = []
    for target in sorted(target_paths):
        work_path = legislation_work_path(target)
        record, integrity = work_records[work_path]
        body = body_targets.get(target, [])
        metadata_observation = metadata_targets.get(target)
        if body:
            body_capture = {'status': 'dwp-provision-body-text-projection-captured',
                'captured': True, 'projection_only': True,
                'raw_official_response_publicly_retained': False,
                'projections': body,
                'meaning': 'Selected machine-extracted provision text is retained in the DWP v2 acquisition projection; it is not a retained full response, accepted legal interpretation or complete effects chain.'}
        elif metadata_observation:
            body_capture = {'status': 'dwp-provision-metadata-observation-only', 'captured': False,
                'projection_only': False, 'metadata_observation': metadata_observation,
                'meaning': 'A point-in-time official response hash and metadata are recorded, but the response body is not retained in the DWP public snapshot.'}
        else:
            body_capture = {'status': 'work-metadata-only-no-dwp-provision-body-observation', 'captured': False,
                'projection_only': False, 'metadata_observation': None,
                'meaning': 'The pinned catalogue supplies work-level metadata only for this target; no matching DWP provision-body projection or retained provision response was found in the selected local manifests.'}
        source_rows = _clean_duplicates(sources_by_target[target])
        linked_citations = _clean_duplicates(citation_map.get(target, []))
        provision_rows.append({'target': target,
            'provision_uri': f'https://www.legislation.gov.uk/id/{target}',
            'work_path': work_path, 'work_uri': record['id'], 'work_title': record.get('title'),
            'catalogued_version_uri': record.get('document_uri'),
            'catalogued_version_date': _version_date(record.get('document_uri')),
            'catalogued_version_date_is_current_law_claim': False,
            'catalogue_has_provision_record_for_target': False,
            'catalogue_work_integrity': integrity,
            'source_seeds_and_locators': source_rows,
            'original_source_citations': linked_citations,
            'citation_status': 'exact-citations-retained' if linked_citations else 'no-exact-literal-linked-in-local-citation-census',
            'dwp_provision_capture': body_capture,
            'case_law_status': 'case-law-not-mapped-as-statutory-provision',
            'extent_status': 'unresolved-or-not-inferred-by-this-crosswalk',
            'commencement_status': 'unresolved-or-not-inferred-by-this-crosswalk',
            'temporal_applicability_status': 'unresolved; catalogue and DWP requested version dates are not proof of applicable law',
            'specialist_review_status': 'not-approved-by-this-crosswalk'})

    explicit_case_law = []
    for source_path, doc in (('domain-profile/legal-reconciliation/seeds.json', recon_seeds),
                             ('domain-profile/legal-bodies/seeds.json', legal_body_seeds)):
        for i, text in enumerate(doc.get('unresolved_literal_policy', [])):
            if re.search(r'R\s*\(', text, re.I):
                explicit_case_law.append({'citation_or_note': text,
                    'status': 'case-law-unresolved-excluded-from-statutory-work-match',
                    'source': {'file': source_path, 'file_sha256': dwp_info[source_path]['sha256'],
                               'git_commit': dwp_commit, 'git_blob': dwp_info[source_path]['git_blob'],
                               'json_locator': f'$.unresolved_literal_policy[{i}]'}})
    tribunal_ids = {row.get('id') for row in tribunal.get('decisions', [])}
    tribunal_inventory = [{'id': row.get('id'), 'title': row.get('title'),
        'decision_date': row.get('decision_date'), 'base_path': row.get('base_path'),
        'classification': 'case-law-decision-metadata; excluded from statutory work matching',
        'judgment_body_acquired': False,
        'source': {'file': 'evaluation/legal-reconciliation/tribunal-discovery.json',
                   'file_sha256': dwp_info['evaluation/legal-reconciliation/tribunal-discovery.json']['sha256'],
                   'git_commit': dwp_commit, 'git_blob': dwp_info['evaluation/legal-reconciliation/tribunal-discovery.json']['git_blob'],
                   'json_locator': f'$.decisions[{i}]'}}
        for i, row in enumerate(tribunal.get('decisions', []))]
    case_law_mentions = _clean_duplicates(case_mentions)

    unresolved_rows = _unresolved_rows(recon_seeds, legal_body_seeds, reading_help)
    unresolved_rows.extend(explicit_case_law)
    citation_file = dwp_info['evaluation/legal-reconciliation/citations.json']
    source_file_inventory = sorted(file_bindings.values(), key=lambda row: row['path'])
    body_count = sum(row['dwp_provision_capture']['captured'] for row in provision_rows)
    metadata_only_count = sum(row['dwp_provision_capture']['status'] == 'dwp-provision-metadata-observation-only'
                              for row in provision_rows)
    catalogue_only_count = sum(row['dwp_provision_capture']['status'] == 'work-metadata-only-no-dwp-provision-body-observation'
                               for row in provision_rows)
    obligations_closed = 0
    report = {
        'schema': 'okf-dwp-statutory-reference-crosswalk.v1',
        'status': 'deterministic-crosswalk-not-legal-approval',
        'scope': 'Statutory work identity and existing local provision-capture inventory for DWP reference seeds; this does not reconcile law, applicability, commencement, extent or entitlement.',
        'run': {'network_calls': 0, 'source_acquisition': 'none', 'paid_api_calls': 0,
                'catalogue_read': 'selected manifest-bound work locator buckets and work shards only'},
        'identities': {'dwp_commit': dwp_commit, 'legislation_commit': catalogue.commit,
            'expected_legislation_commit': expected_legislation_commit,
            'legislation_catalogue_snapshot': catalogue.snapshot,
            'catalogue_manifest': {'path': f'bundle/{CATALOGUE_MANIFEST}', 'sha256': catalogue.manifest_sha256,
                'git_blob': catalogue.bindings[f'bundle/{CATALOGUE_MANIFEST}']['git_blob'],
                'verified_by_bundle_checksum': True,
                'checksum_file': CHECKSUMS,
                'checksum_file_sha256': catalogue.bindings[CHECKSUMS]['sha256']},
            'dwp_input_files': dwp_file_inventory,
            'dwp_source_files': source_file_inventory,
            'catalogue_selected_files': sorted(catalogue.bindings.values(), key=lambda row: row['path']),
            'source_candidate_registry_sha256': dwp_info['evaluation/staff-questions/cases.json']['sha256']},
        'counts': {'dwp_legal_reconciliation_work_seeds': len(seed_works),
            'reconciliation_provision_seed_occurrences': len(recon_seeds.get('provisions', [])),
            'legal_body_request_targets': len(legal_body_seeds.get('requests', [])),
            'reading_help_provision_targets': len(reading_help.get('targets', [])),
            'unique_statutory_provision_targets': len(provision_rows),
            'unique_exact_catalogue_work_records': len(work_rows),
            'catalogue_work_title_exact_matches': title_exact_matches,
            'dwp_targets_with_provision_body_projection': body_count,
            'dwp_targets_with_metadata_only_response': metadata_only_count,
            'catalogue_work_metadata_only_targets': catalogue_only_count,
            'case_law_decision_metadata_excluded': len(tribunal_ids),
            'case_law_citation_mentions_unresolved': len(case_law_mentions) + len(explicit_case_law),
            'original_obligations_closed': obligations_closed},
        'works': work_rows,
        'provisions': provision_rows,
        'unresolved_references': unresolved_rows,
        'case_law_excluded': {'statutory_work_mapping': 'excluded; no case law is converted to a legislation work or provision',
            'literal_mentions_in_source_citations': case_law_mentions,
            'explicit_unresolved_notes': explicit_case_law,
            'existing_tribunal_decision_metadata': tribunal_inventory,
            'tribunal_queries': [{'id': row.get('id'), 'query': row.get('query'), 'scope': row.get('scope'),
                'status': 'case-law-discovery-query; not a statutory work identity'}
                for row in recon_seeds.get('tribunal_queries', [])],
            'limitations': ['The six tribunal search queries are bounded and all six were truncated in the existing legal-reconciliation report.',
                'Observed decision metadata is not judgment text; no judgment bodies were acquired in this crosswalk.',
                'An unresolved case citation such as R(IS)1/99 remains unresolved and is not substituted with a similarly named statutory work.']},
        'obligation_policy': {'closed_count': 0, 'closed_by_metadata_match': False,
            'note': 'Work identity or catalogue metadata matches do not close any of the DWP evidence obligations.'},
        'legal_status_limits': [
            'The catalogue snapshot is dated 11 July 2026 at 18:00 UTC; a date in a work document_uri is the catalogue record’s point-in-time version locator, not a claim of current law.',
            'The work catalogue contains work-level records, not statutory provision bodies. A resource_count or URL does not mean the provision text was acquired or inspected.',
            'DWP provision text, where present, is a selected machine-extracted XML-tree projection. The original full official response is not retained in the public projection and the extracted body is not specialist-approved.',
            'Effect metadata, dates, titles and observed extent attributes do not establish commencement, amendments, territory or individual applicability.',
            'Legal acceptance remains pending specialist review; no obligation, legal proposition or entitlement is accepted by this crosswalk.',
        ],
        'dwp_legal_reconciliation_baseline': {'observed_on': legal_recon_coverage.get('observed_on'),
            'official_provision_requests': legal_recon_coverage.get('official_provision_requests'),
            'statutory_or_judgment_bodies_acquired_at_that_baseline': legal_recon_coverage.get('statutory_or_judgment_bodies_acquired'),
            'specialist_acceptance': legal_recon_coverage.get('specialist_acceptance'),
            'later_legal_body_projection_status': legal_body_coverage.get('legal_acceptance'),
            'later_projection_selected_units': legal_body_coverage.get('selected_units'),
            'later_projection_requested_provisions': legal_body_coverage.get('requested_provisions')},
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--legislation-root', required=True, type=Path,
                        help='Read-only local checkout of okf-uk-legislation at the pinned commit')
    parser.add_argument('--check', action='store_true', help='Compare generated output without writing')
    args = parser.parse_args()
    report = build_crosswalk(ROOT, args.legislation_root)
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    output = ROOT / OUT
    if args.check:
        try:
            retained = output.read_text(encoding='utf-8')
        except OSError as exc:
            raise SystemExit(f'Crosswalk output is missing: {exc}') from exc
        if retained != encoded:
            raise SystemExit('Legislation crosswalk differs from deterministic output')
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding='utf-8')
    print(json.dumps({'status': 'checked' if args.check else 'generated',
        'works': report['counts']['unique_exact_catalogue_work_records'],
        'provisions': report['counts']['unique_statutory_provision_targets'],
        'body_projections': report['counts']['dwp_targets_with_provision_body_projection'],
        'metadata_only': report['counts']['dwp_targets_with_metadata_only_response'],
        'catalogue_only': report['counts']['catalogue_work_metadata_only_targets'],
        'case_law_excluded': report['counts']['case_law_decision_metadata_excluded']}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except CrosswalkError as exc:
        print(f'error: {exc}', file=sys.stderr)
        raise SystemExit(2)
