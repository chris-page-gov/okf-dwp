#!/usr/bin/env python3
"""Derive the latest recorded service position offline; never probe live health."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SELECTION = 'evaluation/service-publication.json'
OUTPUT = 'docs/service-publication.md'
ORIGIN = 'https://ask-okf.crpage.chatgpt.site'
PREFIX = 'validation/compact-delivery/'
MAX_FILE = 256 * 1024
MAX_ENTRIES = 4096
MAX_RECEIPTS = 64
MAX_CENSUS_BYTES = 8 * 1024 * 1024
RELEASE = r'v\d+\.\d+\.\d+(?:-followup-\d{4}-?\d{2}-?\d{2})?/'
DEPLOYMENT_PATH = re.compile(re.escape(PREFIX) + '(?:' + RELEASE + ')?deployment.json')
SDK_PATH = re.compile(re.escape(PREFIX) + '(?:(?:' + RELEASE + ')?sdk-receipt.json|' + RELEASE + r'sdk/attempt-\d{2}/observation.json)')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def no_links(path):
    for member in [*reversed(path.absolute().parents), path.absolute()]:
        require(stat.S_ISDIR(member.lstat().st_mode), 'Directory or ancestor is not a real directory')


def bounded(path, limit=MAX_FILE):
    no_links(path.parent)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_size <= limit, 'Receipt is linked, non-regular or oversized')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        require(stat.S_ISREG(opened.st_mode) and (opened.st_dev, opened.st_ino, opened.st_size) ==
                (before.st_dev, before.st_ino, before.st_size), 'Receipt changed before reading')
        raw = stream.read(limit + 1)
    require(len(raw) == before.st_size and len(raw) <= limit, 'Receipt changed or exceeded bound')
    return raw


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result

    def finite(value):
        result = float(value)
        require(math.isfinite(result), 'Non-finite JSON number')
        return result

    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_float=finite,
                      parse_constant=lambda _: require(False, 'Non-finite JSON number'))


def timestamp(value):
    require(isinstance(value, str) and len(value) <= 40, 'Missing bounded observation time')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.tzinfo is not None, 'Observation time needs a timezone')
    return result.astimezone(timezone.utc)


def hexadecimal(value, length):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{' + str(length) + '}', value), 'Invalid immutable identifier')
    return value


def deployment(value, path):
    require(value.get('schema') == 'okf-compact-delivery-deployment.v1', 'Unknown compact deployment schema')
    record = value.get('deployment', {})
    require(record.get('status') in {'succeeded', 'failed', 'pending', 'running'}, 'Unknown deployment outcome')
    if record['status'] != 'succeeded':
        return None
    require(record.get('url') == ORIGIN and record.get('type') == 'publish', 'Deployment origin or type differs')
    require(record.get('version_id') == value.get('site_version_id') and isinstance(value.get('site_version_id'), str)
            and bool(value['site_version_id']), 'Deployment site version differs')
    require(re.fullmatch(r'\d+\.\d+\.\d+', value.get('service_version', '')), 'Invalid service version')
    hexadecimal(value.get('runtime_commit'), 40)
    hexadecimal(value.get('runtime_worker_sha256'), 64)
    if value.get('source_commit') is not None:
        hexadecimal(value['source_commit'], 40)
    return {'path': path, 'raw': value, 'at': timestamp(record.get('updated_at')),
            'version': value['service_version'], 'worker': value['runtime_worker_sha256'],
            'source': value.get('source_commit')}


def sdk(value, path):
    schema = value.get('schema')
    require(schema in {'okf-remote-mcp-sdk-verification.v1', 'okf-versioned-remote-verification.v1'}, 'Unknown SDK schema')
    require(type(value.get('passed')) is bool, 'Unknown SDK outcome')
    if not value['passed']:
        return None
    modern = schema == 'okf-versioned-remote-verification.v1'
    if modern:
        require(value.get('classification') == 'actual-public-http', 'SDK observation is not actual public HTTP')
    origin = value.get('origin') if modern else value.get('endpoint', '').removesuffix('/okf/mcp')
    require(origin == ORIGIN, 'SDK origin differs')
    health = value.get('observed_health', {}) if modern else value.get('health', {})
    version = value.get('expected_service_version') if modern else health.get('version')
    source = value.get('current_source_version') if modern else value.get('bundle_version')
    worker = value.get('expected_worker_sha256') if modern else value.get('comparison_worker_sha256')
    hexadecimal(source, 40); hexadecimal(worker, 64)
    require(re.fullmatch(r'\d+\.\d+\.\d+', version or ''), 'SDK service version missing')
    started, completed = timestamp(value.get('started_at')), timestamp(value.get('completed_at'))
    require(started <= completed, 'SDK time order differs')
    return {'path': path, 'raw': value, 'at': completed, 'started': started, 'version': version,
            'worker': worker, 'source': source, 'modern': modern}


def census(root):
    """Reserve the compact-delivery namespace; unrelated Pages/Explorer receipts stay outside it."""
    base = root / PREFIX
    no_links(base)
    stack = [base]; entries = 0; total = 0; records = {}; deployments = []; observations = []
    while stack:
        directory = stack.pop(); no_links(directory)
        members = []
        with os.scandir(directory) as listing:
            for item in listing:
                entries += 1
                require(entries <= MAX_ENTRIES, 'Census entry cap exceeded')
                members.append(Path(item.path))
        for path in sorted(members):
            mode = path.lstat().st_mode
            require(not stat.S_ISLNK(mode), 'Linked census member')
            if stat.S_ISDIR(mode):
                stack.append(path)
                continue
            require(stat.S_ISREG(mode), 'Non-regular census member')
            rel = path.relative_to(root).as_posix()
            is_deployment = path.name == 'deployment.json'
            is_sdk = path.name == 'sdk-receipt.json' or (path.name == 'observation.json' and 'sdk' in path.parts)
            if not (is_deployment or is_sdk):
                continue
            pattern = DEPLOYMENT_PATH if is_deployment else SDK_PATH
            require(pattern.fullmatch(rel), 'Unregistered compact receipt location')
            require(len(records) < MAX_RECEIPTS, 'Receipt census cap exceeded')
            raw = bounded(path); total += len(raw)
            require(total <= MAX_CENSUS_BYTES, 'Receipt census byte cap exceeded')
            value = strict_json(raw)
            require(isinstance(value, dict), 'Receipt must be an object')
            records[rel] = raw
            normalised = deployment(value, rel) if is_deployment else sdk(value, rel)
            if normalised:
                (deployments if is_deployment else observations).append(normalised)
    require(deployments, 'No successful deployment was recorded')
    return records, deployments, observations


def matches(observation, deployed):
    return (observation['version'] == deployed['version'] and observation['worker'] == deployed['worker']
            and observation['started'] >= deployed['at']
            and (deployed['source'] is None or observation['source'] == deployed['source']))


def latest(rows, label):
    if not rows:
        return None
    result = max(rows, key=lambda row: row['at'])
    require(sum(row['at'] == result['at'] for row in rows) == 1, 'Ambiguous latest ' + label)
    return result


def bind(root, ref, records):
    require(isinstance(ref, dict) and set(ref) == {'path', 'commit', 'bytes', 'sha256'}, 'Invalid selected receipt binding')
    path = ref['path']; require(path in records, 'Selected receipt is outside the declared census')
    hexadecimal(ref['commit'], 40); hexadecimal(ref['sha256'], 64)
    raw = records[path]
    require(type(ref['bytes']) is int and ref['bytes'] == len(raw) and ref['sha256'] == sha(raw), 'Selected receipt bytes differ')
    # Never execute repository content. A shallow CI checkout explicitly fetches this public commit.
    key = ref['commit'] + ':' + path
    size = int(subprocess.check_output(['git', 'cat-file', '-s', key], cwd=root, timeout=10))
    require(size == len(raw) <= MAX_FILE, 'Immutable receipt size differs')
    blob = subprocess.check_output(['git', 'show', key], cwd=root, timeout=10)
    require(blob == raw, 'Selected receipt differs from its immutable Git blob')


def verify_modern(observation, root):
    value = observation['raw']
    require(observation['modern'], 'Selected SDK requires the explicit versioned observation contract')
    require(value.get('model_calls') == 0 and value.get('full_ask_okf_calls') == 0
            and value.get('deployed_worker_bytes_independently_verified') is False, 'SDK boundary differs')
    require(value.get('complete_tool_rows_equal') is True, 'Tool discovery differs')
    hexadecimal(value.get('comparison_commit'), 40)
    health = value.get('observed_health', {})
    catalogue = value.get('engine_catalogue')
    require(isinstance(catalogue, list) and 1 <= len(catalogue) <= 4 and
            health.get('approved_engines') == catalogue and health.get('version') == observation['version']
            and health.get('bundle_version') == observation['source'], 'SDK health/catalogue identity differs')
    engines = {entry['engine_id']: entry for entry in catalogue}
    require(len(engines) == len(catalogue) and health.get('engine_id') in engines, 'Engine identities differ')
    for entry in catalogue:
        require(re.fullmatch(r'urn:okf:context-engine:sha256:[0-9a-f]{64}', entry.get('engine_id', '')), 'Invalid engine identifier')
        hexadecimal(entry.get('source_commit'), 40)
    current = engines[health['engine_id']]
    require(observation['source'] in current.get('source_versions', []), 'Current source is incompatible')
    cases = value.get('cases', [])
    require(isinstance(cases, list) and 1 <= len(cases) <= 32 and len({row['id'] for row in cases}) == len(cases), 'Case census differs')
    kinds = Counter(row.get('case_kind') for row in cases)
    require(kinds['current-empty-control'] == 1 and kinds['historical-original-package'] == 1, 'A required control or historical case is omitted')
    pairs = set()
    for row in cases:
        require(row.get('complete_package_matches_local_reference') is True and
                row.get('compact_text_structured_values_equal') is True, 'Package reconstruction did not pass')
        require(row.get('engine_id') in engines and row.get('source_version') in engines[row['engine_id']]['source_versions'], 'Case source/engine is incompatible')
        if row.get('case_kind') == 'approved-source-engine-pair':
            pair = (row['source_version'], row['engine_id'])
            require(pair not in pairs, 'Repeated source/engine case'); pairs.add(pair)
        require(row.get('case_kind') in {'approved-source-engine-pair', 'current-empty-control', 'historical-original-package'}, 'Unknown evidence case')
    expected = {(version, engine) for engine, row in engines.items() for version in row['source_versions']}
    require(pairs == expected, 'An approved source/engine pair is omitted')
    transport = value.get('transport', {}); events = transport.get('events', [])
    require(1 <= len(events) <= 256 and transport.get('request_count') == len(events)
            and [row.get('sequence') for row in events] == list(range(1, len(events) + 1)), 'Request census differs')
    require(all(type(row.get('status')) is int and 200 <= row['status'] < 300 for row in events)
            and transport.get('automatic_retries') == 0, 'Transport failure or retry')
    require(all(type(row.get('response_bytes')) is int and 0 <= row['response_bytes'] <= MAX_FILE for row in events)
            and transport.get('received_bytes') == sum(row['response_bytes'] for row in events), 'Received-byte census differs')
    artifacts = value.get('artifacts', {})
    require(isinstance(artifacts, dict) and 1 <= len(artifacts) <= 64, 'SDK artefact cap exceeded')
    for name, ref in artifacts.items():
        require(re.fullmatch(r'[a-zA-Z0-9_.-]+', name) and name not in {'.', '..'}, 'Unsafe SDK artefact path')
        raw = bounded(root / Path(observation['path']).parent / name)
        require(type(ref.get('bytes')) is int and ref['bytes'] == len(raw) and ref.get('sha256') == sha(raw), 'SDK artefact bytes differ')
    require(artifacts.get('executed-verifier.ts', {}).get('sha256') == value.get('runner_sha256') and
            artifacts.get('build-receipt.json', {}).get('sha256') == value.get('build_receipt_sha256'), 'SDK implementation binding differs')
    return {'cases': len(cases), 'pairs': len(pairs), 'requests': len(events), 'bytes': transport['received_bytes'],
            'http_statuses': dict(sorted(Counter(str(row['status']) for row in events).items())),
            'engine_id': health['engine_id'], 'engine_commit': current['source_commit'],
            'verifier_commit': value['comparison_commit'], 'at': value['completed_at']}


def read_selection(root):
    selection = strict_json(bounded(root / SELECTION, 16 * 1024))
    require(isinstance(selection, dict) and set(selection) == {'schema', 'deployment', 'sdk'} and
            selection['schema'] == 'okf-service-publication-selection.v1', 'Unknown receipt selection')
    for kind, pattern in [('deployment', DEPLOYMENT_PATH), ('sdk', SDK_PATH)]:
        ref = selection[kind]
        if kind == 'sdk' and ref is None:
            continue
        require(isinstance(ref, dict) and set(ref) == {'path', 'commit', 'bytes', 'sha256'}, 'Invalid selected receipt binding')
        require(isinstance(ref['path'], str) and pattern.fullmatch(ref['path']), 'Unregistered selected receipt location')
        hexadecimal(ref['commit'], 40); hexadecimal(ref['sha256'], 64)
        require(type(ref['bytes']) is int and 0 <= ref['bytes'] <= MAX_FILE, 'Selected receipt size exceeds bound')
    return selection


def derive(root=ROOT):
    root = root.absolute(); no_links(root)
    selection = read_selection(root)
    records, deployments, observations = census(root)
    deployed = latest(deployments, 'deployment')
    require(selection['deployment']['path'] == deployed['path'], 'A newer successful deployment is not represented')
    bind(root, selection['deployment'], records)
    # A later successful SDK for an unknown deployment cannot disappear from the page silently.
    for observation in observations:
        require(any(matches(observation, item) for item in deployments), 'Successful SDK has no matching recorded deployment')
    accepted = latest([row for row in observations if matches(row, deployed)], 'matching SDK observation')
    if accepted is None:
        require(selection['sdk'] is None, 'A newer deployment must not inherit an earlier SDK pass')
        detail = None
    else:
        require(selection['sdk'] is not None and selection['sdk']['path'] == accepted['path'], 'A newer successful SDK observation is not represented')
        bind(root, selection['sdk'], records)
        detail = verify_modern(accepted, root)
    return {'selection': selection, 'deployment': deployed, 'sdk': accepted, 'detail': detail,
            'census': {'deployment_receipts': len(deployments), 'successful_sdk_receipts': len(observations),
                       'receipt_files': len(records)}}


def evidence_link(ref):
    return f"[exact recorded receipt](https://github.com/chris-page-gov/okf-dwp/blob/{ref['commit']}/{ref['path']})"


def render(result):
    selected = result['selection']; deployed = result['deployment']; detail = result['detail']; raw = deployed['raw']
    source = deployed['source'] or (result['sdk']['source'] if result['sdk'] else 'Not recorded')
    lines = ['# Latest recorded Ask OKF service publication', '',
             '<!-- Generated by scripts/build_service_publication.py. Edit evaluation/service-publication.json, not this page. -->', '',
             '**This page reports retained observations, not real-time health.** It makes no live request. '
             'Ask OKF is an independent experiment, not an official DWP service or benefits advice.', '',
             f"The latest recorded successful publication is **service {deployed['version']}**, on "
             f"**{deployed['at'].astimezone(ZoneInfo('Europe/London')).strftime('%d %B %Y at %H:%M:%S %Z')}**. "
             f"See the {evidence_link(selected['deployment'])}.", '',
             f"[Open the service]({ORIGIN}/) · [Monday walkthrough](monday-handover-2026-09-21.md) · "
             '[What Search, Ask OKF and an AI answer mean](learning-path.md)', '',
             '| Recorded identity | Value |', '| --- | --- |',
             f"| Service version | `{deployed['version']}` |", f'| DWP source commit | `{source}` |',
             f"| Deployed runtime commit | `{raw['runtime_commit']}` |",
             f"| Local Worker SHA-256 | `{deployed['worker']}` |", '', '## Recorded tool verification', '']
    if detail is None:
        lines += ['**Pending for this publication.** No successful SDK observation matching this deployment '
                  'has been recorded. An older verification does not establish the newer deployment\'s behaviour.', '']
    else:
        lines += [f"The {evidence_link(selected['sdk'])} completed at **{timestamp(detail['at']).astimezone(ZoneInfo('Europe/London')).strftime('%d %B %Y at %H:%M:%S %Z')}**. "
                  f"It passed **{detail['cases']} evidence cases**, including **{detail['pairs']} approved source/engine combinations**, "
                  f"with **{detail['requests']} HTTP requests** and **{detail['bytes']:,} received bytes**.", '',
                  'SDK means software development kit: here it is the test client used to call the tools. '
                  'Complete packages were reconstructed from bounded reads and compared with the local reference. '
                  'There were no automatic retries, model calls or full `ask_okf` calls.', '',
                  'HTTP response census: ' + ', '.join(f'{count} × HTTP {status}' for status, count in detail['http_statuses'].items()) + '.', '',
                  f"- Context engine source: `{detail['engine_commit']}`.",
                  f"- Context engine identifier: `{detail['engine_id']}`.",
                  f"- SDK verifier commit: `{detail['verifier_commit']}`.", '',
                  'The verifier and deployed runtime can have different commits: a verifier correction does not redeploy the service.', '']
    lines += ['## What these records do not establish', '',
              'The hosting record and SDK observation are separate evidence. The SDK explicitly does not independently '
              'attest the hosted Worker bytes. Delivery integrity does not establish complete evidence, legal correctness, '
              'specialist acceptance, a public browser journey or ChatGPT/Voice access. Those require their own observations. '
              'Earlier failures and successful historical checks remain unchanged.', '',
              '## Keep this page in step with new observations', '',
              'One authored [receipt selection](../evaluation/service-publication.json) pins exact public Git commits, '
              'paths, byte lengths and hashes. A hash identifies exact file contents. The generator checks those immutable '
              'bytes and scans the bounded `validation/compact-delivery/` receipt namespace. A newer successful publication '
              'or matching successful SDK receipt must be represented before CI passes. CI means automated repository checks.', '',
              'The census includes the unversioned compact receipt and versioned releases, including explicitly named follow-ups. '
              'Candidate builds, `failure.json` attempts, earlier non-compact deployment schemas and unrelated Explorer/Pages '
              'observations are outside this service-status census. An unknown schema or location within the reserved census '
              'fails closed. The check never queries a host or executes an acquired receipt.', '',
              'After recording a new publication, commit its receipt first, update the selection to its immutable identity, '
              'then regenerate this page. Set `sdk` to `null` while that publication has no matching successful observation. '
              'Do not copy an older SDK pass onto it.', '', '```sh', 'uv sync --locked',
              'uv run --locked python scripts/build_service_publication.py',
              'uv run --locked python scripts/build_service_publication.py --check',
              'uv run --locked python -m unittest discover -s scripts -p test_service_publication.py', '```', '',
              'A shallow checkout must contain the commits named in the receipt selection. CI fetches those exact public '
              'objects separately; the generator itself never uses the network.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--receipt-commits', action='store_true', help='Print validated immutable receipt pins for a separate CI fetch')
    args = parser.parse_args()
    if args.receipt_commits:
        selection = read_selection(ROOT)
        print('\n'.join(sorted({ref['commit'] for key in ['deployment', 'sdk'] if (ref := selection[key]) is not None})))
        return
    result = derive(ROOT); expected = render(result).encode()
    target = ROOT / OUTPUT
    if args.check:
        require(bounded(target) == expected, 'Generated service-status page is stale')
    else:
        no_links(target.parent)
        require(not target.is_symlink(), 'Generated status target must not be linked')
        target.write_bytes(expected)
    print(json.dumps({'status': 'verified' if args.check else 'generated', 'network_calls': 0,
                      'service_version': result['deployment']['version'],
                      'sdk_verification': 'recorded_pass' if result['sdk'] else 'pending', **result['census']}))


if __name__ == '__main__':
    main()
