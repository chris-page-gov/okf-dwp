#!/usr/bin/env python3
"""Render a separately pinned graph-service observation without probing the host."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SELECTION = 'evaluation/graph-service-publication.json'
OUTPUT = 'docs/graph-service-publication.md'
PREFIX = 'validation/graph-evidence/v0.8.0/sdk/'
ATTEMPT = re.compile(re.escape(PREFIX) + r'attempt-(\d{2})/(summary|plan|wire)\.json')
NATIVE = re.compile(re.escape(PREFIX) + r'attempt-(\d{2})/native-observation\.json')
MAX_SELECTION = 16 * 1024
MAX_SUMMARY_OR_WIRE = 16 * 1024 * 1024
MAX_PLAN = 2 * 1024 * 1024
MAX_GRAPH_TOTAL = 32 * 1024 * 1024

_SPEC = importlib.util.spec_from_file_location('service_publication_helpers', Path(__file__).with_name('build_service_publication.py'))
S = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(S)


def same(a, b):
    return json.dumps(a, sort_keys=True, separators=(',', ':'), ensure_ascii=False) == json.dumps(b, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def read_selection(root):
    value = S.strict_json(S.bounded(root / SELECTION, MAX_SELECTION))
    S.require(isinstance(value, dict) and set(value) == {'schema', 'deployment', 'graph_sdk', 'native'}
              and value['schema'] == 'okf-graph-service-publication-selection.v1', 'Unknown graph publication selection')
    dep = value['deployment']
    S.require(isinstance(dep, dict) and set(dep) == {'path', 'commit', 'bytes', 'sha256'}
              and isinstance(dep.get('path'), str) and S.DEPLOYMENT_PATH.fullmatch(dep['path']),
              'Graph publication must pin a registered deployment')
    S.hexadecimal(dep['commit'], 40); S.hexadecimal(dep['sha256'], 64)
    S.require(type(dep['bytes']) is int and 0 <= dep['bytes'] <= S.MAX_FILE, 'Deployment pin exceeds byte bound')
    for field in ('graph_sdk', 'native'):
        S.require(value[field] is None or isinstance(value[field], dict), f'{field} pin must be an object or null')
    if value['graph_sdk'] is not None:
        refs = value['graph_sdk']
        S.require(set(refs) == {'summary', 'plan', 'wire'}, 'Graph SDK must pin summary, plan and wire receipts separately')
        attempts = set(); commits = set()
        for kind, ref in refs.items():
            pattern = re.compile(re.escape(PREFIX) + rf'attempt-(\d{{2}})/{kind}\.json')
            S.require(isinstance(ref, dict) and set(ref) == {'path', 'commit', 'bytes', 'sha256'}
                      and isinstance(ref.get('path'), str) and pattern.fullmatch(ref['path']), 'Unregistered graph SDK receipt path')
            S.hexadecimal(ref['commit'], 40); S.hexadecimal(ref['sha256'], 64)
            cap = MAX_PLAN if kind == 'plan' else MAX_SUMMARY_OR_WIRE
            S.require(type(ref['bytes']) is int and 0 <= ref['bytes'] <= cap, 'Graph SDK receipt exceeds byte bound')
            attempts.add(Path(ref['path']).parent.name); commits.add(ref['commit'])
        S.require(sum(ref['bytes'] for ref in refs.values()) <= MAX_GRAPH_TOTAL, 'Combined graph SDK receipts exceed byte bound')
        S.require(len(attempts) == len(commits) == 1, 'Graph SDK receipt pins must share one attempt and Git commit')
    if value['native'] is not None:
        ref = value['native']; pattern = re.compile(re.escape(PREFIX) + r'attempt-\d{2}/native-observation\.json')
        S.require(set(ref) == {'path', 'commit', 'bytes', 'sha256'} and isinstance(ref.get('path'), str)
                  and pattern.fullmatch(ref['path']), 'Unregistered native observation path')
        S.hexadecimal(ref['commit'], 40); S.hexadecimal(ref['sha256'], 64)
        S.require(type(ref['bytes']) is int and 0 <= ref['bytes'] <= S.MAX_FILE, 'Native receipt exceeds byte bound')
    return value


def read_pin(root, ref, pattern, limit=MAX_SUMMARY_OR_WIRE):
    S.require(isinstance(ref, dict) and set(ref) == {'path', 'commit', 'bytes', 'sha256'}, 'Invalid graph receipt pin')
    path = ref['path']
    S.require(isinstance(path, str) and pattern.fullmatch(path), 'Unregistered graph receipt path')
    S.hexadecimal(ref['commit'], 40); S.hexadecimal(ref['sha256'], 64)
    S.require(type(ref['bytes']) is int and 0 <= ref['bytes'] <= limit, 'Graph receipt exceeds byte bound')
    raw = S.bounded(root / path, limit)
    S.require(len(raw) == ref['bytes'] and S.sha(raw) == ref['sha256'], 'Graph receipt bytes differ from selection')
    key = ref['commit'] + ':' + path
    size = int(subprocess.check_output(['git', 'cat-file', '-s', key], cwd=root, timeout=10))
    S.require(size == len(raw) <= limit, 'Immutable graph receipt size differs')
    blob = subprocess.check_output(['git', 'show', key], cwd=root, timeout=10)
    S.require(blob == raw, 'Graph receipt differs from immutable Git blob')
    return S.strict_json(raw), raw


def _sha(value, name):
    return S.hexadecimal(value, 64)


def _same_identity(obj, identities, fields):
    for field in fields:
        S.require(obj.get(field) == identities.get(field), f'Graph receipt identity differs: {field}')


def _validate_deployment(root, ref):
    S.require(isinstance(ref, dict) and set(ref) == {'path', 'commit', 'bytes', 'sha256'}, 'Invalid deployment pin')
    S.require(isinstance(ref['path'], str) and S.DEPLOYMENT_PATH.fullmatch(ref['path']), 'Unregistered deployment path')
    S.hexadecimal(ref['commit'], 40); S.hexadecimal(ref['sha256'], 64)
    records, deployments, _ = S.census(root)
    deployed = S.latest(deployments, 'deployment')
    S.require(deployed['path'] == ref['path'], 'Selected graph deployment is not the latest successful deployment')
    S.bind(root, ref, records)
    raw = deployed['raw']
    S.require(isinstance(raw.get('graph_evidence'), dict), 'Deployment lacks graph_evidence identity')
    evidence = raw['graph_evidence']
    S.require(set(evidence) == {'producer_commit', 'graph_sha256', 'engine_id'}, 'Malformed deployment graph_evidence identity')
    S.hexadecimal(evidence['producer_commit'], 40); _sha(evidence['graph_sha256'], 'graph SHA')
    S.require(re.fullmatch(r'urn:okf:graph-engine:sha256:[0-9a-f]{64}', evidence['engine_id']) is not None,
              'Malformed deployment graph engine identity')
    _sha(raw.get('build_receipt_sha256'), 'build receipt SHA')
    return deployed, evidence


def validate_wire(wire, summary):
    S.require(isinstance(wire, dict) and set(wire) == {'calls', 'bytes_received', 'max_response_bytes',
              'min_request_interval_ms', 'automatic_retries', 'evidence_calls', 'evidence_response_bytes', 'events'},
              'Malformed graph wire receipt')
    events = wire['events']
    S.require(isinstance(events, list) and 1 <= len(events) <= 12000 and wire['calls'] == len(events), 'Graph wire call census differs')
    S.require(type(wire['automatic_retries']) is int and wire['automatic_retries'] == 0, 'Graph wire retries are not zero')
    S.require(type(wire['min_request_interval_ms']) in (int, float) and wire['min_request_interval_ms'] >= 750,
              'Graph wire request pacing is below the public run interval')
    total = 0; max_bytes = 0; evidence_total = 0; evidence_calls = 0; evidence_max = 0
    for index, row in enumerate(events, 1):
        S.require(isinstance(row, dict) and row.get('sequence') == index, 'Graph wire sequence differs')
        S.require((row.get('method'), row.get('path')) in {('GET', '/health'), ('POST', '/graph/mcp')}, 'Graph wire route differs')
        S.require(type(row.get('status')) is int and 200 <= row['status'] < 300, 'Graph wire contains an unsuccessful HTTP response')
        S.require(type(row.get('request_bytes')) is int and 0 <= row['request_bytes'] <= 32768, 'Graph wire request exceeds byte bound')
        if row['method'] == 'GET':
            S.require(row['path'] == '/health' and row.get('rpc_method') is None and row.get('tool') is None,
                      'Graph health request metadata differs')
        else:
            S.require(row['path'] == '/graph/mcp' and row.get('rpc_method') in {
                'initialize', 'notifications/initialized', 'notifications/cancelled', 'ping', 'server/discover', 'tools/list', 'tools/call'},
                'Graph JSON-RPC method differs')
            if row['rpc_method'] == 'tools/call':
                S.require(row.get('tool') in {'plan_okf_evidence', 'read_okf_planned_evidence'}, 'Unapproved graph tool call')
            else:
                S.require(row.get('tool') is None, 'Tool name is present on a non-tool-call request')
        S.require(type(row.get('response_bytes')) is int and 0 <= row['response_bytes'] <= 65536, 'Graph wire response exceeds route limit')
        _sha(row.get('response_sha256'), 'response SHA')
        total += row['response_bytes']; max_bytes = max(max_bytes, row['response_bytes'])
        if row.get('tool') in {'plan_okf_evidence', 'read_okf_planned_evidence'}:
            S.require(row['path'] == '/graph/mcp' and row.get('rpc_method') == 'tools/call'
                      and row['response_bytes'] <= 8192, 'Evidence HTTP response exceeds 8 KiB envelope bound')
            evidence_calls += 1; evidence_total += row['response_bytes']; evidence_max = max(evidence_max, row['response_bytes'])
        else:
            S.require(row.get('tool') is None, 'Unexpected graph SDK tool call')
    S.require(type(wire['bytes_received']) is int and wire['bytes_received'] == total, 'Graph wire byte count differs')
    S.require(wire['max_response_bytes'] == max_bytes and wire['evidence_calls'] == evidence_calls
              and wire['evidence_response_bytes'] == evidence_total
              and total <= 256 * 1024 * 1024, 'Graph wire summary counters differ')
    receipt = summary.get('wire_receipt', {})
    S.require(receipt.get('calls') == len(events) and receipt.get('bytes_received') == total
              and receipt.get('max_response_bytes') == max_bytes and receipt.get('max_evidence_response_bytes') == evidence_max
              and receipt.get('min_request_interval_ms') == wire['min_request_interval_ms']
              and receipt.get('automatic_retries') == 0 and same(receipt.get('events'), events),
              'Graph summary and wire receipt differ')
    return {'calls': len(events), 'bytes': total, 'max_bytes': max_bytes, 'evidence_calls': evidence_calls,
            'evidence_bytes': evidence_total, 'evidence_max_bytes': evidence_max}


def validate_plan(plan, summary, identities):
    S.require(plan.get('schema') == 'okf-graph-remote-verification-plan.v1', 'Unknown graph plan schema')
    for field, expected in [('producer_commit', identities['producer_commit']), ('graph_sha256', identities['graph_sha256']),
                            ('engine_id', identities['engine_id'])]:
        S.require(plan.get(field) == expected, f'Graph plan identity differs: {field}')
    S.require(plan.get('publication_status') == 'pinned', 'Graph producer source is not pinned')
    prov = plan.get('verifier_provenance')
    S.require(isinstance(prov, dict) and same(prov, identities['verifier_provenance']), 'Graph plan verifier provenance differs')
    questions = plan.get('questions')
    S.require(isinstance(questions, list) and len(questions) == plan.get('question_count')
              == summary['counts'].get('unique_questions'), 'Graph plan question count differs')
    S.require(len({row.get('question_sha256') for row in questions}) == len(questions), 'Duplicate graph plan question')
    occurrences = 0; positive_targets = 0
    for row in questions:
        S.hexadecimal(row.get('question_sha256'), 64); S.hexadecimal(row.get('package_sha256'), 64)
        S.require(isinstance(row.get('case_ids'), list) and row['case_ids'], 'Graph plan case IDs are missing')
        S.require(re.fullmatch(r'urn:sha256:[0-9a-f]{64}', row.get('plan_id', '')) is not None,
                  'Graph plan ID is malformed')
        S.require(isinstance(row.get('expected_record_ids'), list), 'Graph plan target list is missing')
        groups = row.get('groups')
        S.require(isinstance(groups, list) and groups, 'Graph plan groups are missing')
        if not row['expected_record_ids']:
            S.require(any(group in {'persona-boundary', 'legacy-boundary', 'recovery', 'withheld-regression'} for group in groups),
                      'Empty graph target set is not scoped to a boundary/control group')
        hashes = row.get('expected_source_text_hashes')
        S.require(isinstance(hashes, dict) and set(hashes) == set(row['expected_record_ids']),
                  'Graph plan target hash mapping is missing or overbroad')
        for digest in hashes.values(): _sha(digest, 'expected source text SHA')
        occurrences += len(row['case_ids']); positive_targets += len(row['expected_record_ids'])
    S.require(occurrences == plan.get('case_occurrences'), 'Graph plan case occurrence count differs')
    counts = summary['counts']
    S.require(counts.get('source_case_occurrences') == occurrences and counts.get('expected_positive_targets', 0) >= positive_targets,
              'Graph summary case or target count differs from plan')
    S.require(counts.get('original_graph_obligation_count') == 203, 'Original graph obligation census differs')
    return {'questions': len(questions), 'case_occurrences': occurrences, 'positive_targets': counts['expected_positive_targets']}


def validate_summary(summary, deployed, evidence):
    S.require(summary.get('schema') == 'okf-graph-remote-sdk-verification.v1' and summary.get('status') == 'passed',
              'Graph SDK observation is not a passed v1 public receipt')
    run = summary.get('run', {})
    S.require(run.get('mode') == 'public', 'Graph SDK observation is not public HTTP')
    start = S.timestamp(run.get('started_at'))
    S.require(start >= deployed['at'], 'Graph observation predates selected deployment')
    S.require(type(run.get('duration_ms')) is int and 0 <= run['duration_ms'] <= 4 * 60 * 60 * 1000,
              'Graph observation duration exceeds the run bound')
    S.require(start + timedelta(milliseconds=run['duration_ms']) <= datetime.now(timezone.utc),
              'Graph observation completion is in the future')
    S.require(type(run.get('http_requests')) is int and run['http_requests'] > 0
              and run.get('public_network_calls') == run['http_requests'] and run.get('model_calls') == 0
              and run.get('paid_api_calls') == 0 and run.get('automatic_retries') == 0,
              'Graph public run counters differ')
    identities = summary.get('identities', {})
    S.require(identities.get('service_version') == deployed['version'], 'Graph observation service version differs')
    for key in ('producer_commit', 'graph_sha256', 'engine_id'):
        S.require(identities.get(key) == evidence[key], f'Graph observation differs from deployed graph identity: {key}')
    S.require(identities.get('admission_status') == 'pinned', 'Graph source admission is not pinned')
    S.hexadecimal(identities.get('sdk_v1_tool_rows_sha256'), 64); S.require(
        identities.get('sdk_v1_tool_rows_sha256') == identities.get('sdk_v2_tool_rows_sha256'), 'Graph SDK tool rows differ')
    prov = identities.get('verifier_provenance', {})
    S.require(prov.get('local_worker_sha256') == deployed['worker'], 'Local verifier Worker differs from selected deployment Worker')
    S.require(prov.get('build_receipt_sha256') == deployed['raw']['build_receipt_sha256'], 'Graph verifier build receipt differs from deployment')
    for key in ('repository_worktree_clean', 'verifier_matches_git_head', 'package_lock_matches_git_head',
                'worker_matches_build_receipt', 'package_lock_matches_build_receipt', 'verifier_matches_build_receipt',
                'build_receipt_inputs_match_worktree'):
        S.require(prov.get(key) is True, f'Graph verifier provenance is not pinned: {key}')
    S.require(prov.get('build_receipt_status') == 'valid'
              and prov.get('source_identity_status') == 'tracked-source-and-local-worker-match'
              and prov.get('worker_hash_scope') == 'local dist/server/index.js only; not a remote deployment attestation',
              'Graph verifier provenance status differs')
    S.hexadecimal(prov.get('repository_git_head'), 40)
    for key in ('verifier_module_sha256', 'package_lock_sha256', 'build_receipt_sha256', 'build_receipt_worker_sha256',
                'verifier_git_head_sha256', 'package_lock_git_head_sha256', 'build_receipt_package_lock_sha256',
                'build_receipt_verifier_sha256'):
        _sha(prov.get(key), key)
    S.require(prov['verifier_module_sha256'] == prov['verifier_git_head_sha256'] == prov['build_receipt_verifier_sha256']
              and prov['package_lock_sha256'] == prov['package_lock_git_head_sha256'] == prov['build_receipt_package_lock_sha256']
              and prov['local_worker_sha256'] == prov['build_receipt_worker_sha256'], 'Graph verifier hash chain differs')
    counts = summary.get('counts', {})
    S.require(counts.get('completed_unique_questions') == counts.get('unique_questions')
              and counts.get('unique_questions', 0) > 0 and counts.get('max_evidence_http_response_bytes', 0) <= 8192,
              'Graph SDK question completion or response bound differs')
    S.require(type(counts.get('bytes_received')) is int and 0 <= counts['bytes_received'] <= 256 * 1024 * 1024
              and run['http_requests'] <= 12000, 'Graph SDK request/byte ceiling differs')
    gates = summary.get('gates', {})
    passed = {'producer_package_identity', 'expected_targets_and_paths', 'source_text_hashes', 'insufficient_boundary',
              'no_truncation', 'original_obligations_open', 'full_http_envelope_limit', 'sdk_v1_v2_tool_parity'}
    S.require(all(gates.get(key) == 'passed' for key in passed), 'A required graph SDK gate did not pass')
    S.require(gates.get('legal_or_entitlement_sufficiency') == 'not-assessed'
              and gates.get('accessibility') == 'not-assessed', 'Graph receipt overclaims legal or accessibility review')
    return identities, counts


def validate_native(value, deployed, evidence, graph_plan=None):
    S.require(value.get('schema') == 'okf-graph-native-host-observation.v1'
              and value.get('status') == 'passed' and value.get('classification') == 'actual-native-plugin-host'
              and value.get('scope') == 'representative-uc-client-observation', 'Unknown or incomplete native host receipt')
    start = S.timestamp(value.get('started_at')); end = S.timestamp(value.get('completed_at'))
    S.require(start >= deployed['at'] and start <= end and end <= datetime.now(timezone.utc),
              'Native observation chronology differs')
    ids = value.get('identities', {})
    for key, expected in [('graph_sha256', evidence['graph_sha256']), ('engine_id', evidence['engine_id']),
                          ('producer_commit', evidence['producer_commit'])]:
        S.require(ids.get(key) == expected, f'Native receipt graph identity differs: {key}')
    S.require(ids.get('question_sha256') == 'c224ca359a090e29fbca4e58127f5e94968aab1808e2e1ae3801b395a39eb3e8',
              'Native observation is not the fixed UC question')
    S.require(re.fullmatch(r'urn:sha256:[0-9a-f]{64}', ids.get('plan_id', '')) is not None,
              'Native plan ID is malformed')
    S.hexadecimal(ids.get('package_sha256'), 64)
    uc_questions = []
    if graph_plan is not None:
        uc_questions = [row for row in graph_plan['questions'] if 'fixed-uc' in row.get('groups', [])]
        S.require(any(row.get('plan_id') == ids['plan_id'] and row.get('package_sha256') == ids['package_sha256']
                      for row in uc_questions), 'Native observation package is not the pinned fixed-UC package')
    bind = value.get('deployment_binding', {})
    S.require(bind.get('service_version') == deployed['version'] and bind.get('worker_sha256') == deployed['worker']
              and bind.get('source_commit') == deployed['source']
              and bind.get('scope') == 'declared-selection-only; not remotely attested', 'Native deployment binding differs')
    counts = value.get('counts', {})
    S.require(type(counts.get('observed_tool_calls')) is int and 1 <= counts['observed_tool_calls'] <= 512
              and type(counts.get('max_mcp_result_json_bytes')) is int and 0 <= counts['max_mcp_result_json_bytes'] <= 8192
              and type(counts.get('continuation_calls')) is int and counts['continuation_calls'] >= 0,
              'Native observed tool call census differs')
    discovery = value.get('discovery', {})
    names = discovery.get('tool_names')
    S.require(names is None or (isinstance(names, list) and len(names) == 2
                                and set(names) == {'plan_okf_evidence', 'read_okf_planned_evidence'}),
              'Native tool discovery differs')
    S.require(discovery.get('tool_rows_sha256') is None or re.fullmatch(r'[0-9a-f]{64}', discovery['tool_rows_sha256']),
              'Native tool rows digest differs')
    checks = value.get('source_text_checks')
    S.require(isinstance(checks, list) and len(checks) == 4
              and all(isinstance(row, dict) and row.get('matched') is True
                      and isinstance(row.get('record_id'), str) and row['record_id']
                      and re.fullmatch(r'[0-9a-f]{64}', row.get('source_text_sha256', ''))
                      and row.get('source_text_sha256') == row.get('expected_source_text_sha256')
                      and re.fullmatch(r'[0-9a-f]{64}', row.get('expected_source_text_sha256', '')) for row in checks)
              and len({row['record_id'] for row in checks}) == 4,
              'Native source-text checks are incomplete')
    if graph_plan is not None:
        uc_targets = set().union(*(set(row['expected_record_ids']) for row in uc_questions))
        uc_hashes = {key: digest for row in uc_questions for key, digest in row['expected_source_text_hashes'].items()}
        S.require({row['record_id'] for row in checks} == uc_targets
                  and all(uc_hashes.get(row['record_id']) == row['source_text_sha256'] for row in checks),
                  'Native source-text checks differ from pinned fixed-UC target hashes')
    gates = value.get('gates', {})
    S.require(all(gates.get(key) == 'passed' for key in ('manifest_continuation', 'source_text_hashes', 'no_truncated_tool_output')),
              'Native evidence gate did not pass')
    S.require(value.get('transport_scope') == 'MCP result JSON bytes observed by connector; not HTTP envelope bytes'
              and value.get('full_matrix_claimed') is False, 'Native receipt scope overclaims transport or suite coverage')
    return {'scope': value['scope'], 'calls': counts['observed_tool_calls'], 'max_result_bytes': counts['max_mcp_result_json_bytes']}


def derive(root=ROOT):
    root = Path(root).absolute()
    S.no_links(root)
    selection = read_selection(root)
    deployed, evidence = _validate_deployment(root, selection['deployment'])
    sdk_detail = None; native_detail = None
    if selection['graph_sdk'] is not None:
        refs = selection['graph_sdk']
        S.require(set(refs) == {'summary', 'plan', 'wire'}, 'Graph SDK must pin summary, plan and wire receipts separately')
        loaded = {}
        attempt_dirs = set()
        for kind in ('summary', 'plan', 'wire'):
            pattern = re.compile(re.escape(PREFIX) + rf'attempt-(\d{{2}})/{kind}\.json')
            cap = MAX_PLAN if kind == 'plan' else MAX_SUMMARY_OR_WIRE
            loaded[kind], _ = read_pin(root, refs[kind], pattern, cap)
            attempt_dirs.add(str(Path(refs[kind]['path']).parent))
        S.require(len(attempt_dirs) == 1, 'Graph SDK receipts must be from one attempt directory')
        identities, counts = validate_summary(loaded['summary'], deployed, evidence)
        plan_detail = validate_plan(loaded['plan'], loaded['summary'], identities)
        wire_detail = validate_wire(loaded['wire'], loaded['summary'])
        S.require(loaded['summary']['run']['http_requests'] == wire_detail['calls']
                  and loaded['summary']['counts']['bytes_received'] == wire_detail['bytes'],
                  'Graph summary run or byte counters differ from wire receipt')
        S.require(loaded['summary']['counts']['max_evidence_http_response_bytes'] == wire_detail['evidence_max_bytes'],
                  'Graph evidence response maximum differs from wire event census')
        sdk_detail = {'identities': identities, 'counts': counts, 'plan': plan_detail, 'wire': wire_detail,
                      'summary_ref': refs['summary'], 'started_at': loaded['summary']['run']['started_at'],
                      'duration_ms': loaded['summary']['run']['duration_ms']}
    if selection['native'] is not None:
        native_path_pattern = re.compile(re.escape(PREFIX) + r'attempt-\d{2}/native-observation\.json')
        native, _ = read_pin(root, selection['native'], native_path_pattern, S.MAX_FILE)
        native_detail = validate_native(native, deployed, evidence,
                                        loaded['plan'] if sdk_detail is not None else None)
    return {'selection': selection, 'deployment': deployed, 'graph_identity': evidence,
            'graph_sdk': sdk_detail, 'native': native_detail}


def render(result):
    d = result['deployment']; selection = result['selection']; sdk = result['graph_sdk']; native = result['native']
    lines = ['# Recorded graph service verification', '',
             '<!-- Generated by scripts/build_graph_service_publication.py. Edit evaluation/graph-service-publication.json. -->', '',
             '**This page reports retained observations, not real-time health.** The builder makes no live request. '
             'The graph suite is separate from the legacy SDK receipt and does not replace it.', '',
             f"Selected deployment: service **{d['version']}**, recorded **{d['at'].astimezone(timezone.utc).isoformat()}**; "
             f"Worker SHA-256 `{d['worker']}`. The deployment receipt also declares graph producer `{result['graph_identity']['producer_commit']}`, "
             f"graph SHA-256 `{result['graph_identity']['graph_sha256']}` and engine `{result['graph_identity']['engine_id']}`. "
             f"See the {S.evidence_link(result['selection']['deployment'])}.", '',
             '## Public graph SDK verification', '']
    if sdk is None:
        lines += ['**Pending for this deployment.** No matching public graph SDK receipt is selected.', '']
    else:
        wire = sdk['wire']; counts = sdk['counts']; ids = sdk['identities']
        started_at = S.timestamp(sdk['started_at'])
        completed_at = started_at + timedelta(milliseconds=sdk['duration_ms'])
        lines += [f"The pinned SDK observation completed at **{completed_at.astimezone(timezone.utc).isoformat()}** "
                  f"and passed **{counts['completed_unique_questions']} unique questions**, covering **{counts['source_case_occurrences']} case occurrences** "
                  f"and **{counts['expected_positive_targets']} expected positive source targets**.", '',
                  f"It recorded **{wire['calls']} HTTP requests** and **{wire['bytes']:,} response bytes**. "
                  f"The largest evidence response was **{wire['evidence_max_bytes']:,} bytes** (8,192-byte ceiling).", '',
                  f"- Graph producer commit: `{ids['producer_commit']}`.", f"- Graph SHA-256: `{ids['graph_sha256']}`.",
                  f"- Engine identifier: `{ids['engine_id']}`.",
                  f"- Local verifier Worker SHA-256: `{ids['verifier_provenance']['local_worker_sha256']}` (local build identity; not remote attestation).", '',
                  f"Pinned inputs: {S.evidence_link(selection['graph_sdk']['summary'])} · "
                  f"{S.evidence_link(selection['graph_sdk']['plan'])} · {S.evidence_link(selection['graph_sdk']['wire'])}.", '',
                  'The pinned verifier labels this as a public-mode SDK run and records the `/graph/mcp` route under its fixed-origin contract. '
                  'It is a software test client, not the native plugin host.', '',
                  'Passed checks included package identity, expected targets and paths, source-text hashes, open obligations, no truncation and the full HTTP envelope limit.', '',
                  'The recorded retrieval gates do not establish legal sufficiency, entitlement correctness, human accessibility review, specialist approval or a correct answer.', '']
    lines += ['## Native plugin host observation', '']
    if native is None:
        lines += ['**Pending.** No separate native plugin host receipt is selected. Public SDK evidence does not establish native host behaviour.', '']
    else:
        lines += [f"A separate native observation passed for **{native['scope']}** with {native['calls']} observed tool calls "
                  f"and a maximum MCP result JSON size of {native['max_result_bytes']:,} bytes. "
                  f"See the {S.evidence_link(selection['native'])}. This is not an HTTP envelope measurement or a full-suite claim.", '']
    lines += ['## Scope', '',
              'The deployment, legacy SDK observation, graph SDK observation and native host observation are distinct evidence. '
              'The graph SDK validates retrieval and bounded delivery against its pinned test protocol; it does not independently attest hosted Worker bytes. '
              'The native observation, if present, uses connector-visible evidence and declares the deployment binding rather than attesting it.', '',
              'A null receipt remains pending. No earlier SDK result is inherited across deployments. The source evidence and graph are experimental and do not constitute official DWP guidance or legal advice.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--receipt-commits', action='store_true', help='Print exact pinned receipt commits for an external CI fetch')
    args = parser.parse_args()
    if args.receipt_commits:
        selection = read_selection(ROOT)
        refs = [selection['deployment']]
        if selection['graph_sdk']:
            refs.extend(selection['graph_sdk'].values())
        if selection['native']:
            refs.append(selection['native'])
        print('\n'.join(sorted({ref['commit'] for ref in refs})))
        return
    result = derive(ROOT); content = render(result).encode()
    target = ROOT / OUTPUT
    if args.check:
        S.require(S.bounded(target) == content, 'Generated graph-service publication page is stale')
    else:
        S.no_links(target.parent)
        S.require(not target.is_symlink(), 'Generated graph-service publication target must not be linked')
        target.write_bytes(content)
    print(json.dumps({'status': 'verified' if args.check else 'generated', 'network_calls': 0,
                      'graph_sdk': 'passed' if result['graph_sdk'] else 'pending',
                      'native': 'passed' if result['native'] else 'pending'}))


if __name__ == '__main__':
    main()
