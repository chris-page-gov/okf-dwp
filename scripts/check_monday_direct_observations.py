#!/usr/bin/env python3
"""Check the two retained direct-v3 rejections; never run a provider.

Full admission reuses the hash-bound frozen input verifier and read-only Git
objects. Output checks inspect only the named public experiment tree. Raw event
streams were not retained: this checks recorded projections, not parser replay.
"""
from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
SPEC = 'evaluation/model-comparison/household-direct-v3/'
OUTPUT = 'validation/model-comparison/household-direct-v3'
FREEZE = SPEC + 'frozen/manifest.json'
FREEZE_SHA = 'a6b85c1db3d4ae6c9d6d182c3138e03de660d19a6fb32881f4f7e5e2390a6ea3'
PROVIDERS = ('claude-subscription', 'codex-subscription')
CODE = ('scripts/run_monday_direct_trials.py', 'scripts/monday_direct_events_v3.py')
RECEIPTS = {
    'claude-subscription': '970815320e3cfa15003d2a10eca55daffbe95a059cc76a026f8f55fcd488a795',
    'codex-subscription': '70a0d9a49ddd75df4f4ead152f48c794af0b04b15682b1b7b5ff622a8c043716'}
ISSUES = {'claude-subscription': 'unknown-or-missing-wrapper-field',
          'codex-subscription': 'unrecognised-usage-shape'}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def directory(path):
    path = Path(os.path.abspath(path))
    for part in [*reversed(path.parents), path]:
        require(stat.S_ISDIR(part.lstat().st_mode), 'Directory or parent must be real; symlinks forbidden')
    return path


def bounded(path, cap=65536):
    path = Path(path); directory(path.parent)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_size <= cap, 'File must be bounded and regular')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        require(stat.S_ISREG(opened.st_mode) and (before.st_dev, before.st_ino, before.st_size)
                == (opened.st_dev, opened.st_ino, opened.st_size), 'Opened file changed')
        raw = stream.read(cap + 1)
    require(len(raw) == opened.st_size and len(raw) <= cap, 'File changed or exceeded bound')
    return raw


def load_frozen(root):
    """Execute only the two exact reviewed modules after bounded hash admission."""
    root = directory(root)
    freeze_raw = bounded(root / FREEZE)
    require(sha(freeze_raw) == FREEZE_SHA, 'Approved freeze fingerprint differs')
    freeze = json.loads(freeze_raw)
    refs = {r['path']: r for r in freeze['inputs']}
    code = {}
    for name in CODE:
        raw = bounded(root / name)
        require(len(raw) == refs[name]['bytes'] and sha(raw) == refs[name]['sha256'], 'Frozen code differs')
        code[name] = raw
    helper = types.ModuleType('monday_direct_events_v3')
    helper.__file__ = str(root / CODE[1])
    exec(compile(code[CODE[1]], helper.__file__, 'exec'), helper.__dict__)
    old = sys.modules.get(helper.__name__)
    sys.modules[helper.__name__] = helper
    try:
        trial = types.ModuleType('_verified_monday_direct_v3')
        trial.__file__ = str(root / CODE[0])
        exec(compile(code[CODE[0]], trial.__file__, 'exec'), trial.__dict__)
    finally:
        if old is None:
            del sys.modules[helper.__name__]
        else:
            sys.modules[helper.__name__] = old
    require(trial.LOADED == {name: sha(raw) for name, raw in code.items()}, 'Loaded code differs')
    return trial, freeze_raw, freeze


def exact_directory(path, expected):
    directory(path)
    names = set()
    with os.scandir(path) as entries:
        for entry in entries:
            require(len(names) < len(expected), 'Unexpected experiment entry')
            require(entry.name in expected and entry.name not in names, 'Unexpected experiment entry')
            mode = entry.stat(follow_symlinks=False).st_mode
            require(stat.S_ISDIR(mode) if expected[entry.name] == 'directory' else stat.S_ISREG(mode),
                    'Experiment entry is symlinked or special')
            names.add(entry.name)
    require(names == set(expected), 'Missing experiment entry')


def census(root):
    """Bounded names-only admission rejects extra providers, cases or raw files."""
    out = root / OUTPUT
    exact_directory(out, {'README.md': 'file', **{p: 'directory' for p in PROVIDERS}})
    for provider in PROVIDERS:
        p = out / provider
        exact_directory(p, {'control-unknown': 'directory'})
        exact_directory(p / 'control-unknown', {'attempt-01': 'directory'})
        exact_directory(p / 'control-unknown/attempt-01', {'receipt.json': 'file', 'model-output.json': 'file'})


def check_attempt(receipt, projection, provider, expected, loaded, protocol):
    fields = {'answer_present', 'artefacts', 'attempt', 'auth', 'capture_complete', 'captured_stderr_bytes',
              'captured_stdout_bytes', 'case_id', 'cli', 'elapsed_seconds', 'exit_code', 'fallback_override',
              'finished_at', 'inputs', 'isolation', 'loaded_code_sha256', 'model_override',
              'process_group_kill_unavailable', 'provider', 'schema', 'specialist_accepted',
              'started_at', 'status', 'stderr_sha256', 'stdout_sha256', 'tool_event_census'}
    require(set(receipt) == fields, 'Receipt fields differ')
    require(provider in PROVIDERS and receipt['provider'] == provider
            and receipt['case_id'] == 'control-unknown' and receipt['attempt'] == 'attempt-01'
            and receipt['schema'] == 'okf-direct-attempt.v3', 'Unregistered attempt')
    require(receipt['inputs'] == expected and receipt['loaded_code_sha256'] == loaded, 'Attempt input/code binding differs')
    require(receipt['status'] == 'rejected-events-or-answer-json' and receipt['answer_present'] is False
            and receipt['specialist_accepted'] is False and receipt['model_override'] is None
            and receipt['fallback_override'] is None, 'Rejection or authority boundary differs')
    require(set(receipt['artefacts']) == {'model-output.json'}, 'Rejected attempt must not retain an answer')
    require(receipt['tool_event_census'] == 'unknown' and receipt['capture_complete'] is True
            and receipt['process_group_kill_unavailable'] is False and type(receipt['exit_code']) is int
            and receipt['exit_code'] == 0, 'Capture/census boundary differs')
    require(receipt['auth'] == {'accepted': True, 'category': 'subscription-observed'}, 'Subscription observation differs')
    for name, cap in [('captured_stdout_bytes', protocol['max_stdout_bytes']),
                      ('captured_stderr_bytes', protocol['max_stderr_bytes'])]:
        require(type(receipt[name]) is int and 0 <= receipt[name] <= cap, 'Capture count exceeds frozen bound')
    start = datetime.fromisoformat(receipt['started_at']); end = datetime.fromisoformat(receipt['finished_at'])
    require(start.tzinfo is not None and end.tzinfo is not None and start <= end, 'Invalid attempt timestamps')
    require(type(receipt['elapsed_seconds']) in (int, float) and 0 <= receipt['elapsed_seconds'] <= protocol['timeout_seconds'],
            'Elapsed capture bound differs')
    wanted = {'schema': 'okf-direct-cli-events.v3', 'accounting_models': [], 'assistant_confirmation': 'absent',
              'event_count': 7 if provider == 'claude-subscription' else 5,
              'issues': [ISSUES[provider]],
              'model_identity_boundary': 'Reported identities only; no inferred or controlled single-model identity.',
              'model_identity_status': 'not-reported', 'observed_tool_events': 0, 'response_models': [],
              'stream_completed': False, 'telemetry': [], 'tool_event_census': 'unknown', 'usage': {},
              'warnings': [] if provider == 'claude-subscription' else ['skill-catalogue-shortening-host-context-still-visible']}
    require(projection == wanted, 'Recorded parser projection differs; unknown census must remain unknown')


def outcomes(root, trial, protocol, bound, packages, freeze_raw):
    root = directory(root); census(root)
    raw, context = packages['control-unknown']
    prompt = trial.fixed_prompt('control-unknown', raw, bound)
    schema_raw = bound[SPEC + 'answer.schema.json']
    expected = trial.binding('control-unknown', raw, prompt, schema_raw, freeze_raw)
    for provider in PROVIDERS:
        prefix = root / OUTPUT / provider / 'control-unknown/attempt-01'
        receipt_raw = bounded(prefix / 'receipt.json')
        require(sha(receipt_raw) == RECEIPTS[provider], 'Recorded receipt fingerprint differs')
        receipt = trial.events.strict_json(receipt_raw)
        model_raw = bounded(prefix / 'model-output.json')
        require(receipt['artefacts'].get('model-output.json') == sha(model_raw), 'Retained artefact fingerprint differs')
        projection = trial.events.strict_json(model_raw)
        check_attempt(receipt, projection, provider, expected, trial.LOADED, protocol)
        # Replay the frozen substantive gate only; this function performs local reads.
        try:
            trial.verify_control(provider, expected, context, trial.events.strict_json(schema_raw))
        except ValueError as error:
            require(str(error) == 'control-gate-failed', 'Unexpected control gate failure')
        else:
            raise ValueError('Failed control unexpectedly permits a substantive attempt')
    return {'schema': 'okf-direct-observation-check.v1', 'passed': True, 'freeze_sha256': FREEZE_SHA,
            'recorded_attempts': 2, 'rejected_attempts': 2, 'accepted_answers': 0, 'substantive_attempts': 0,
            'unknown_tool_census_attempts': 2, 'control_gate_closed': True,
            'basis': 'recorded-parser-projections-only; raw streams were not retained',
            'provider_calls': 0, 'network_calls': 0, 'specialist_accepted': False}


def validate(root=ROOT, explorer_root=None):
    require(explorer_root is not None, 'Full frozen input admission requires --explorer-root')
    trial, freeze_raw, freeze = load_frozen(root)
    protocol, _ = trial.protocol()
    bound, packages = trial.inputs(protocol, freeze, directory(explorer_root))
    result = outcomes(root, trial, protocol, bound, packages, freeze_raw)
    result['full_frozen_input_admission'] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--explorer-root', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(explorer_root=args.explorer_root), sort_keys=True))


if __name__ == '__main__':
    main()
