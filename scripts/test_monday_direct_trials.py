"""Synthetic offline controls only; these tests never call a provider or authentication."""
from copy import deepcopy
import json
import gzip
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_monday_direct_trials as trial
import monday_direct_events_v3 as event


def wire(rows): return '\n'.join(json.dumps(r, ensure_ascii=False) for r in rows).encode()
def answer(case='control-unknown', context=None):
    return {'case_id': case, 'context_id': context['context_id'] if context else 'urn:sha256:' + 'a' * 64,
        'package_evidence_status': 'insufficient', 'answer_disposition': 'cannot_establish',
        'summary': 'The supplied evidence cannot establish the answer.', 'claims': [],
        'gaps': ['No complete applicable evidence.'], 'abstentions': ['No individual decision.'],
        'limitations': ['No specialist acceptance.']}
def claude(value, assistant=True):
    text = json.dumps(value, ensure_ascii=False)
    rows = [{'type': 'assistant', 'message': {'role': 'assistant', 'model': 'claude-sonnet-4-6',
                'content': [{'type': 'text', 'text': text}]}}] if assistant else []
    return rows + [{'type': 'result', 'subtype': 'success', 'is_error': False, 'result': text}]
def codex(value):
    return [{'type': 'thread.started', 'thread_id': 'private-session'}, {'type': 'turn.started'},
        {'type': 'item.completed', 'item': {'id': 'private-item', 'type': 'agent_message', 'text': json.dumps(value)}},
        {'type': 'turn.completed', 'usage': {'input_tokens': 10, 'output_tokens': 5, 'cached_input_tokens': 0}}]
def repack(c):
    while True:
        raw = trial.canonical(c)
        if c['budget']['used_bytes'] == len(raw): return raw
        c['budget']['used_bytes'] = len(raw)


def context(case):
    record = {'id': 'urn:record', 'kind': 'evidence', 'text': 'A complete literal source quotation for a bounded claim.',
              'provenance': [{'url': 'https://example.test/source', 'locator': 'page 1'}]}
    c = {'schema': 'okf-governed-context.v1', 'question': trial.QUESTIONS[case],
         'context_id': 'urn:sha256:' + ('a' if case == 'control-unknown' else 'b') * 64,
         'evidence_status': 'insufficient', 'ai_answer': None, 'relationships': [],
         'selected': [] if case == 'control-unknown' else [{'record': record}],
         'budget': {'max_bytes': 524288, 'max_nodes': 64, 'max_relationships': 128, 'max_depth': 6,
             'used_nodes': 0 if case == 'control-unknown' else 1, 'used_relationships': 0, 'reached_depth': 0, 'used_bytes': 0, 'truncated': False},
         'bundle': {'snapshot': 'synthetic'}, 'binding': {'index_url': 'https://example.test/index', 'index_sha256': 'c' * 64}}
    while True:
        raw = json.dumps(c, sort_keys=True, separators=(',', ':')).encode()
        if c['budget']['used_bytes'] == len(raw): return raw, c
        c['budget']['used_bytes'] = len(raw)


class DirectTrials(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p, _ = trial.protocol(); cls.ready = {**cls.p, 'phase': 'ready-for-freeze'}
        cls.bound = {trial.PREFIX + name: (trial.SPEC / name).read_bytes() for name in ('answer.schema.json', 'prompt.md')}
        cls.schema = json.loads(cls.bound[trial.PREFIX + 'answer.schema.json'])
        cls.packages = {c: context(c) for c in trial.CASES}

    def test_protocol_stays_pending_and_source_question_is_exact(self):
        self.assertEqual(self.p['phase'], 'pending-final-source-package-runner-freeze')
        self.assertEqual(self.p['questions']['staff-012'], trial.QUESTIONS['staff-012'])
        self.assertEqual(self.p['allowed_tool_events'], [])
        self.assertEqual(self.schema['properties']['claims']['maxItems'], 3)
        self.assertEqual(self.schema['properties']['claims']['items']['properties']['evidence']['maxItems'], 2)
        with patch.object(sys, 'argv', ['trial', '--run']), patch.object(trial, 'command') as cmd, patch.object(trial, 'read') as read:
            with patch.object(trial, 'protocol', return_value=(self.p, b'pending')):
                with self.assertRaisesRegex(ValueError, 'protocol-still-pending'): trial.main()
            cmd.assert_not_called(); read.assert_not_called()

    def test_strict_json_refuses_duplicate_nonfinite_fenced_trailing_and_surrogate(self):
        for text in ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', '{"a":1e999}',
                     '```json\n{}\n```', '{} trailing', '{} {}', '{"a":"\\ud800"}']:
            with self.subTest(text=text), self.assertRaises((ValueError, UnicodeError)): event.strict_json(text)

    def test_successful_direct_streams_have_no_formatter_and_no_private_ids(self):
        for provider, rows in [('claude-subscription', claude(answer())), ('codex-subscription', codex(answer()))]:
            census, actual = event.recognise(provider, wire(rows))
            self.assertEqual(actual, answer()); self.assertEqual(census['issues'], [])
            self.assertEqual(census['tool_event_census'], 'complete-zero-observed-tools')
            self.assertNotIn('private', json.dumps(census))
        self.assertEqual(event.recognise('claude-subscription', wire(claude(answer(), False)))[0]['assistant_confirmation'], 'absent')

    def test_every_formatter_tool_and_tool_result_is_rejected(self):
        for name in ('StructuredOutput', 'Bash', 'web_search'):
            rows = claude(answer()); rows[0]['message']['content'] = [{'type': 'tool_use', 'id': 'secret', 'name': name, 'input': {'private': 'token'}}]
            census, value = event.recognise('claude-subscription', wire(rows))
            self.assertIsNone(value); self.assertEqual(census['tool_event_census'], 'unknown')
            self.assertEqual(census['observed_tool_events'], 1); self.assertNotIn('token', json.dumps(census))
        rows = [{'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': 'secret'}]}}] + claude(answer(), False)
        self.assertIsNone(event.recognise('claude-subscription', wire(rows))[1])
        rows = codex(answer()); rows[2]['item']['type'] = 'command_execution'
        self.assertIsNone(event.recognise('codex-subscription', wire(rows))[1])

    def test_unknown_fields_events_content_or_errors_are_not_safe_zero_tool_streams(self):
        base = codex(answer())
        for modified in [{**base[0], 'external_tool': {}}, {'type': 'new-event'},
                         {'type': 'item.completed', 'item': {'id': 'x', 'type': 'error', 'message': 'private token'}}]:
            census, value = event.recognise('codex-subscription', wire([modified] + base[1:]))
            self.assertIsNone(value); self.assertEqual(census['tool_event_census'], 'unknown')
            self.assertNotIn('private', json.dumps(census))
        rows = claude(answer()); rows[0]['message']['hidden_tool'] = {'name': 'secret'}
        self.assertIsNone(event.recognise('claude-subscription', wire(rows))[1])

    def test_only_exact_public_skill_warning_is_recognised(self):
        for message, accept in [(event.SKILL_WARNING, True), (event.SKILL_WARNING + ' extra', False)]:
            rows = codex(answer()); rows.insert(2, {'type': 'item.completed', 'item': {'id': 'secret', 'type': 'error', 'message': message}})
            census, value = event.recognise('codex-subscription', wire(rows)); self.assertEqual(value is not None, accept)
            self.assertNotIn('secret', json.dumps(census))

    def test_terminal_requires_success_once_and_last(self):
        base = claude(answer())
        for rows in [base[:-1], base + [base[-1]], list(reversed(base)), [{**base[-1], 'is_error': 'false'}],
                     [{**base[-1], 'is_error': True}], [{**base[-1], 'subtype': 'error_max_turns'}]]:
            self.assertIsNone(event.recognise('claude-subscription', wire(rows))[1])
        rows = codex(answer()); rows[-1]['type'] = 'turn.failed'
        self.assertIsNone(event.recognise('codex-subscription', wire(rows))[1])

    def test_competing_and_conflicting_answers_fail_without_selecting_convenient_one(self):
        rows = claude(answer()); rows[0]['message']['content'][0]['text'] = '{"different":true}'
        self.assertIsNone(event.recognise('claude-subscription', wire(rows))[1])
        rows = claude(answer()); rows.insert(0, deepcopy(rows[0]))
        self.assertIsNone(event.recognise('claude-subscription', wire(rows))[1])
        rows = codex(answer()); rows.insert(2, deepcopy(rows[2]))
        self.assertIsNone(event.recognise('codex-subscription', wire(rows))[1])

    def test_answer_and_stream_byte_caps(self):
        rows = claude({'huge': 'x' * 16384}, False)
        self.assertIsNone(event.recognise('claude-subscription', wire(rows))[1])
        self.assertIsNone(event.recognise('codex-subscription', b'x' * (2097152 + 1))[1])

    def test_wrapper_duplicate_keys_and_invalid_numeric_usage_fail_closed(self):
        raw = b'{"type":"turn.completed","type":"turn.completed","usage":{}}\n'
        self.assertIsNone(event.recognise('codex-subscription', raw)[1])
        for number in [True, -1, '1']:
            rows = codex(answer()); rows[-1]['usage']['input_tokens'] = number
            self.assertIsNone(event.recognise('codex-subscription', wire(rows))[1])

    def test_init_tool_and_customisation_configuration_cannot_be_hidden(self):
        init = {'type': 'system', 'subtype': 'init', 'tools': [], 'mcp_servers': [], 'permissionMode': 'dontAsk'}
        self.assertIsNotNone(event.recognise('claude-subscription', wire([init] + claude(answer())))[1])
        for field, value in [('tools', ['StructuredOutput']), ('mcp_servers', [{}]), ('permissionMode', 'bypassPermissions'), ('skills', ['private'])]:
            census, parsed = event.recognise('claude-subscription', wire([{**init, field: value}] + claude(answer())))
            self.assertIsNone(parsed); self.assertNotIn('private', json.dumps(census))

    def test_model_identity_is_unknown_or_mixed_without_inference(self):
        c, _ = event.recognise('codex-subscription', wire(codex(answer())))
        self.assertEqual(c['model_identity_status'], 'not-reported')
        rows = claude(answer()); rows[-1]['modelUsage'] = {'claude-opus-4-6': {'inputTokens': 10}}
        c, _ = event.recognise('claude-subscription', wire(rows))
        self.assertEqual(c['model_identity_status'], 'multiple-reported-identities')
        self.assertEqual(c['response_models'][0]['value'], 'claude-sonnet-4-6')
        self.assertEqual(c['accounting_models'][0]['model']['value'], 'claude-opus-4-6')

    def test_bad_answer_formats_remain_rejected_after_complete_stream(self):
        for text in ['```json\n{}\n```', '{} trailing', '{"a":1,"a":2}', '[]', '{"a":NaN}']:
            rows = claude(answer(), False); rows[-1]['result'] = text
            c, value = event.recognise('claude-subscription', wire(rows))
            self.assertIsNone(value); self.assertTrue(c['issues'])
            self.assertEqual(c['tool_event_census'], 'complete-zero-observed-tools')

    def test_telemetry_has_exact_shapes_and_dynamic_keys_are_not_published(self):
        thinking = {'type': 'system', 'subtype': 'thinking_tokens', 'session_id': 'private', 'uuid': 'private',
                    'estimated_tokens': 1, 'estimated_tokens_delta': 1}
        good = [thinking] + claude(answer(), False)
        self.assertIsNotNone(event.recognise('claude-subscription', wire(good))[1])
        bad = deepcopy(good); bad[0]['estimated_tokens'] = True
        self.assertIsNone(event.recognise('claude-subscription', wire(bad))[1])
        rows = claude(answer(), False); rows[-1]['modelUsage'] = {'private-account@example.test': {'inputTokens': 12}}
        census, value = event.recognise('claude-subscription', wire(rows)); self.assertIsNotNone(value)
        self.assertNotIn('private-account', json.dumps(census))
        self.assertIsNone(census['accounting_models'][0]['model']['value'])
        rows[-1]['usage'] = {'server_tool_use': {'web_search_requests': 1}}
        self.assertIsNone(event.recognise('claude-subscription', wire(rows))[1])

    def test_schema_identity_literal_locator_and_boundary_controls(self):
        c = self.packages['staff-012'][1]; a = answer('staff-012', c)
        a.update(answer_disposition='partial_evidence_only', claims=[{'id': 'c1', 'statement': 'A bounded source observation.',
            'scope_or_qualification': 'Only the selected source scope.', 'evidence': [{'record_id': 'urn:record',
            'quote': c['selected'][0]['record']['text'], 'source_url': 'https://example.test/source', 'locator': 'page 1'}]}])
        self.assertTrue(trial.mechanical(a, c, 'staff-012', self.schema)['passed'])
        for key, val in [('case_id', 'control-unknown'), ('context_id', 'wrong'), ('package_evidence_status', 'sufficient'),
                         ('answer_disposition', 'bounded_source_answer')]:
            b = deepcopy(a); b[key] = val; self.assertFalse(trial.mechanical(b, c, 'staff-012', self.schema)['passed'])
        for key, val in [('quote', 'A made-up but sufficiently long quotation'), ('locator', 'page 2'), ('record_id', 'missing')]:
            b = deepcopy(a); b['claims'][0]['evidence'][0][key] = val
            self.assertFalse(trial.mechanical(b, c, 'staff-012', self.schema)['passed'])
        b = deepcopy(a); b['claims'] *= 4
        self.assertFalse(trial.mechanical(b, c, 'staff-012', self.schema)['passed'])
        b = deepcopy(c); b['budget']['truncated'] = True
        self.assertFalse(trial.mechanical(a, b, 'staff-012', self.schema)['passed'])

    def test_package_does_not_change_question_status_control_or_literal(self):
        for case, (raw, value) in self.packages.items(): self.assertEqual(trial.package(case, raw, self.ready), value)
        for key, val in [('question', 'Assume no partner'), ('evidence_status', 'sufficient'), ('ai_answer', {})]:
            c = deepcopy(self.packages['staff-012'][1]); c[key] = val
            with self.assertRaises(ValueError): trial.package('staff-012', json.dumps(c).encode(), self.ready)

    def test_all_package_budget_fields_and_used_counts_are_checked(self):
        for key, value in [('max_nodes', 999), ('max_relationships', 999), ('max_depth', 99),
                           ('max_bytes', True), ('used_nodes', 999), ('used_relationships', 1),
                           ('reached_depth', 7), ('reached_depth', True), ('truncated', 'false')]:
            c = deepcopy(self.packages['staff-012'][1]); c['budget'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): trial.package('staff-012', repack(c), self.ready)
        for field, count in [('selected', 65), ('relationships', 129)]:
            c = deepcopy(self.packages['staff-012'][1])
            c[field] = c['selected'] * count if field == 'selected' else [{}] * count
            c['budget']['used_nodes' if field == 'selected' else 'used_relationships'] = count
            with self.assertRaises(ValueError): trial.package('staff-012', repack(c), self.ready)

    def test_huge_integer_usage_is_rejected_and_attempt_receipt_survives(self):
        rows = codex(answer()); rows[-1]['usage']['input_tokens'] = 10 ** 400
        census, value = event.recognise('codex-subscription', wire(rows))
        self.assertIsNone(value); self.assertEqual(census['tool_event_census'], 'unknown')
        self.assertNotIn(str(10 ** 400), json.dumps(census))
        result = {'returncode': 0, 'stdout': wire(rows), 'stderr': b'', 'timed_out': False, 'output_bound_exceeded': False}
        with tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve()) as temp, patch.object(trial, 'OUT', Path(temp)), patch.object(trial, 'command', return_value=(['fixture'], {})), patch.object(trial, 'subscription_auth', return_value={'accepted': True}), patch.object(trial, 'binary_identity', return_value={}), patch.object(trial, 'capture', return_value=result):
            r = trial.run_one('codex-subscription', 'control-unknown', self.ready, self.bound, self.packages, b'freeze', 'controls')
            self.assertEqual(r['status'], 'rejected-events-or-answer-json'); self.assertFalse(r['answer_present'])
            self.assertTrue((Path(temp) / 'codex-subscription/control-unknown/attempt-01/receipt.json').exists())

    def test_raced_fifo_is_opened_nonblocking_and_rejected_before_read(self):
        with tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve()) as temp:
            path = Path(temp) / 'member'; path.write_bytes(b'file'); original_open = os.open
            def replace_then_open(target, flags):
                self.assertTrue(flags & os.O_NONBLOCK)
                path.unlink(); os.mkfifo(path)
                return original_open(target, flags)
            with patch.object(trial.os, 'open', side_effect=replace_then_open):
                with self.assertRaisesRegex(ValueError, 'changed-file'): trial.bounded(path, 100)

    def test_commands_keep_subscription_defaults_without_claude_formatter(self):
        with tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve()) as temp, patch.object(trial.shutil, 'which', return_value='/fixture/cli'), patch.object(trial, 'skill_overrides', return_value=('[]', 0)):
            ca, _ = trial.command('claude-subscription', temp, b'{}'); co, _ = trial.command('codex-subscription', temp, b'{}')
            self.assertNotIn('--json-schema', ca); self.assertNotIn('--model', ca + co); self.assertNotIn('--fallback-model', ca + co)
            for flag in ['--safe-mode', '--no-chrome', '--tools', '--strict-mcp-config', '--verbose']: self.assertIn(flag, ca)
            for flag in ['--ignore-user-config', '--ignore-rules', '--output-schema', '--json', '--sandbox']: self.assertIn(flag, co)
            self.assertEqual(ca[ca.index('--output-format') + 1], 'stream-json')
        with patch.dict(os.environ, {'HOME': '/fixture', 'PATH': '/bin', 'OPENAI_API_KEY': 'private', 'ANTHROPIC_AUTH_TOKEN': 'private', 'CLAUDE_MODEL': 'override', 'HTTP_PROXY': 'private'}, clear=True):
            self.assertEqual(trial.environment(), {'HOME': '/fixture', 'PATH': '/bin'})

    def test_authentication_is_subscription_only_and_private_details_are_dropped(self):
        def result(text): return {'returncode': 0, 'stdout': text, 'stderr': b'', 'timed_out': False, 'output_bound_exceeded': False}
        with patch.object(trial, 'capture', return_value=result(b'{"loggedIn":true,"authMethod":"claude.ai","apiProvider":"firstParty","email":"private"}')):
            observed = trial.subscription_auth('claude-subscription', 'fixture', '/fixture', {})
            self.assertTrue(observed['accepted']); self.assertNotIn('private', str(observed))
        with patch.object(trial, 'capture', return_value=result(b'Logged in using an API key')):
            self.assertFalse(trial.subscription_auth('codex-subscription', 'fixture', '/fixture', {})['accepted'])
        for value in (b'true', b'[]', b'null'):
            with patch.object(trial, 'capture', return_value=result(value)):
                self.assertFalse(trial.subscription_auth('claude-subscription', 'fixture', '/fixture', {})['accepted'])

    def test_capture_timeout_and_both_caps_use_synthetic_python_process_only(self):
        with tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve()) as temp:
            for code in ['print("x"*3000)', 'import sys;sys.stderr.write("x"*3000)']:
                out = trial.capture([sys.executable, '-c', code], '', temp, trial.environment(), timeout=2, stdout_cap=1024, stderr_cap=1024)
                self.assertTrue(out['output_bound_exceeded']); self.assertLessEqual(len(out['stdout']), 1024); self.assertLessEqual(len(out['stderr']), 1024)
            out = trial.capture([sys.executable, '-c', 'import time;time.sleep(3)'], '', temp, trial.environment(), timeout=0.1)
            self.assertTrue(out['timed_out'])

    def test_symlink_parent_and_member_and_oversized_input_rejected(self):
        with tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve()) as temp:
            root = Path(temp); (root / 'real').mkdir(); (root / 'real/data').write_bytes(b'large')
            (root / 'link').symlink_to(root / 'real', target_is_directory=True); (root / 'member').symlink_to(root / 'real/data')
            for path, cap in [(root / 'link/data', 100), (root / 'member', 100), (root / 'real/data', 2)]:
                with self.assertRaises(ValueError): trial.bounded(path, cap)

    def test_mocked_controls_are_identical_and_gate_substantive_attempts(self):
        with tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve()) as temp, patch.object(trial, 'OUT', Path(temp)), patch.object(trial, 'command', return_value=(['fixture'], {})), patch.object(trial, 'subscription_auth', return_value={'accepted': True, 'category': 'synthetic'}), patch.object(trial, 'binary_identity', return_value={'version': 'synthetic'}):
            with patch.object(trial, 'capture') as invoke:
                with self.assertRaises((ValueError, FileNotFoundError)):
                    trial.run_one('codex-subscription', 'staff-012', self.ready, self.bound, self.packages, b'freeze', 'substantive')
                invoke.assert_not_called()
            controls = []
            for provider, rows in [('claude-subscription', claude(answer())), ('codex-subscription', codex(answer()))]:
                result = {'returncode': 0, 'stdout': wire(rows), 'stderr': b'private', 'timed_out': False, 'output_bound_exceeded': False}
                with patch.object(trial, 'capture', return_value=result):
                    receipt = trial.run_one(provider, 'control-unknown', self.ready, self.bound, self.packages, b'freeze', 'controls')
                self.assertEqual(receipt['status'], 'accepted-mechanical-only'); controls.append(receipt)
                self.assertNotIn('private', json.dumps(receipt))
            self.assertEqual(controls[0]['inputs'], controls[1]['inputs'])
            with patch.object(trial, 'capture') as invoke:
                with self.assertRaises(FileExistsError): trial.run_one('codex-subscription', 'control-unknown', self.ready, self.bound, self.packages, b'freeze', 'controls')
                invoke.assert_not_called()
            a = answer('staff-012', self.packages['staff-012'][1])
            result = {'returncode': 0, 'stdout': wire(codex(a)), 'stderr': b'', 'timed_out': False, 'output_bound_exceeded': False}
            with patch.object(trial, 'capture', return_value=result):
                r = trial.run_one('codex-subscription', 'staff-012', self.ready, self.bound, self.packages, b'freeze', 'substantive')
            self.assertEqual(r['status'], 'accepted-mechanical-only')
            expected = controls[0]['inputs']; context = self.packages['control-unknown'][1]
            bad = Path(temp) / 'claude-subscription/control-unknown/attempt-01/answer.json'; bad.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'artefact-changed'): trial.verify_control('claude-subscription', expected, context, self.schema)

    def test_failed_mocked_attempt_keeps_receipt_and_never_retains_answer(self):
        for status, overrides in [('timeout', {'timed_out': True}), ('output-bound-exceeded', {'output_bound_exceeded': True}),
                                  ('provider-call-failed', {'returncode': 1})]:
            result = {'returncode': 0, 'stdout': wire(codex(answer())), 'stderr': b'private error', 'timed_out': False, 'output_bound_exceeded': False, **overrides}
            with tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve()) as temp, patch.object(trial, 'OUT', Path(temp)), patch.object(trial, 'command', return_value=(['fixture'], {})), patch.object(trial, 'subscription_auth', return_value={'accepted': True}), patch.object(trial, 'binary_identity', return_value={}), patch.object(trial, 'capture', return_value=result):
                r = trial.run_one('codex-subscription', 'control-unknown', self.ready, self.bound, self.packages, b'freeze', 'controls')
                self.assertEqual(r['status'], status); self.assertFalse(r['answer_present'])
                self.assertTrue((Path(temp) / 'codex-subscription/control-unknown/attempt-01/receipt.json').exists())

    def freeze_fixture(self):
        sdk_path = 'validation/compact-delivery/v9.9.9/sdk/attempt-01/observation.json'
        dep_path = 'validation/compact-delivery/v9.9.9/deployment.json'
        source_commit = '1' * 40; trial_commit = '2' * 40; explorer_commit = '3' * 40; service_commit = '5' * 40; worker = '4' * 64
        blobs = {**self.bound, trial.PREFIX + 'protocol.json': trial.encoded(self.ready)}
        for name in trial.CODE + ['pyproject.toml', 'uv.lock']: blobs[name] = (trial.ROOT / name).read_bytes()
        blobs[trial.SOURCE_FILES[1]] = trial.encoded({'schema': 'okf-context-index.v1', 'bundle': {'snapshot': 'synthetic-semantic'}})
        source_manifest = {'schema': 'okf-context-corpus.v1', 'bundle': {'snapshot': 'synthetic-corpus'},
            'base_index': {'path': 'base-index.json', 'bytes': len(blobs[trial.SOURCE_FILES[1]]), 'sha256': event.sha(blobs[trial.SOURCE_FILES[1]])},
            'semantic_source_snapshot': 'synthetic-semantic'}
        blobs[trial.SOURCE_FILES[0]] = trial.encoded(source_manifest)
        blobs[trial.SOURCE_FILES[2]] = trial.encoded({'cases': [{'id': 'staff-012', 'question': trial.QUESTIONS['staff-012']}]})
        engine = {'schema': 'okf-context-engine-manifest.v1', 'source_commit': explorer_commit,
            'family': 'okf-context-assembly.v1', 'files': {n: {'sha256': event.sha(b'engine'), 'bytes': 6,
            'source_path': 'apps/okf-explorer/src/lib/context/' + n} for n in ('index.ts', 'corpus.ts', 'types.ts')}}
        engine['engine_id'] = 'urn:okf:context-engine:sha256:' + event.sha(trial.canonical(engine))
        catalogue = [{'engine_id': engine['engine_id'], 'source_commit': explorer_commit, 'source_versions': [source_commit]}]
        sdk = {'schema': 'okf-versioned-remote-verification.v1', 'classification': 'actual-public-http', 'passed': True,
            'current_source_version': source_commit, 'comparison_commit': service_commit, 'expected_worker_sha256': worker,
            'expected_service_version': '9.9.9', 'deployed_worker_bytes_independently_verified': False, 'full_ask_okf_calls': 0,
            'model_calls': 0, 'runner_sha256': event.sha(b'verifier'), 'engine_catalogue': catalogue,
            'observed_health': {'engine_id': engine['engine_id'], 'bundle_version': source_commit, 'approved_engines': catalogue},
            'origin': 'https://example.test', 'cases': [], 'artifacts': {}}
        cases = []
        for case, (_, original) in self.packages.items():
            ctx = deepcopy(original); ctx['bundle'] = source_manifest['bundle']
            ctx['binding'] = {'index_url': 'https://raw.githubusercontent.com/chris-page-gov/okf-dwp/' + source_commit + '/' + trial.SOURCE_FILES[0],
                'index_sha256': event.sha(blobs[trial.SOURCE_FILES[0]])}
            raw = repack(ctx); blobs[trial.PREFIX + 'frozen/contexts/' + case + '.json'] = raw
            compressed = gzip.compress(raw, mtime=0); received = sdk_path.rsplit('/', 1)[0] + '/' + case + '.json.gz'
            blobs[received] = compressed; sdk['artifacts'][received.rsplit('/', 1)[1]] = {'bytes': len(compressed), 'sha256': event.sha(compressed)}
            cases.append({'id': case, 'context_id': ctx['context_id'], 'sha256': event.sha(raw), 'bytes': len(raw),
                'sdk_case_id': case, 'received_package': received})
            sdk['cases'].append({'id': case, 'case_kind': 'current-empty-control' if case == 'control-unknown' else 'approved-source-engine-pair',
                'context_id': ctx['context_id'], 'question_sha256': event.sha(trial.QUESTIONS[case].encode()),
                'source_version': source_commit, 'engine_id': engine['engine_id'], 'context_budget': self.ready['context_budget'],
                'canonical_package_sha256': event.sha(raw), 'package_bytes': len(raw),
                'complete_package_matches_local_reference': True, 'compact_text_structured_values_equal': True,
                'ordered_catalogue': True, 'evidence_status': 'insufficient', 'relationships': 0,
                'provenance_sha256': event.sha(trial.canonical([{'id': i['record']['id'], 'provenance': i['record']['provenance']} for i in ctx['selected']])),
                'selected_records': len(ctx['selected']), 'reads': [{'section': 'package', 'content_sha256': event.sha(raw), 'slices': 1}]})
        blobs[sdk_path] = trial.encoded(sdk)
        blobs[dep_path] = trial.encoded({'schema': 'okf-compact-delivery-deployment.v1', 'source_commit': source_commit,
            'runtime_commit': service_commit, 'runtime_worker_sha256': worker, 'service_version': '9.9.9', 'archive_sha256': 'sha256:' + '6' * 64,
            'site_version_id': 'fixture', 'deployment': {'version_id': 'fixture', 'status': 'succeeded', 'url': 'https://example.test'}})
        manifest = {'schema': 'okf-direct-trial-freeze.v3', 'trial_commit': trial_commit, 'source_commit': source_commit,
            'explorer_commit': explorer_commit, 'service_commit': service_commit, 'worker_sha256': worker, 'service_version': '9.9.9',
            'sdk_receipt': sdk_path, 'deployment': dep_path, 'inputs': [], 'engine_id': engine['engine_id'],
            'engine_modules': {n: event.sha(b'engine') for n in ('index.ts', 'types.ts', 'corpus.ts')}, 'cases': cases}
        def rebind():
            manifest['inputs'] = [{'path': name, 'bytes': len(raw), 'sha256': event.sha(raw),
                'commit': source_commit if name in trial.SOURCE_FILES else trial_commit} for name, raw in blobs.items()]
        rebind()
        def git(root, commit, name, *args):
            if name.startswith('apps/'): return b'engine'
            if name.startswith('services/ask-okf-mcp/vendor/engines/'):
                return trial.encoded(engine) if name.endswith('/manifest.json') else b'engine'
            if name == 'services/ask-okf-mcp/scripts/verify-versioned-remote.ts': return b'verifier'
            return blobs[name]
        return blobs, manifest, git, rebind

    def test_frozen_manifest_changed_hash_commit_or_service_refuses(self):
        blobs, manifest, git, _ = self.freeze_fixture()
        with patch.object(trial, 'read', side_effect=lambda name, *args: blobs[name]), patch.object(trial, 'git_bytes', side_effect=git):
            trial.inputs(self.ready, manifest, Path('/fixture'))
            for mutate in [lambda m: m['inputs'][0].update(sha256='f' * 64), lambda m: m['inputs'][0].update(commit='f' * 40),
                           lambda m: m['cases'][0].update(context_id='wrong'), lambda m: m.update(worker_sha256='f' * 64),
                           lambda m: m['engine_modules'].update(**{'index.ts': 'f' * 64}),
                           lambda m: m.update(engine_id='wrong'), lambda m: m.update(extra='unknown'),
                           lambda m: m['inputs'].append(deepcopy(m['inputs'][0]))]:
                m = deepcopy(manifest); mutate(m)
                with self.assertRaises(ValueError): trial.inputs(self.ready, m, Path('/fixture'))
            with patch.object(trial, 'git_bytes', return_value=b'changed'):
                with self.assertRaisesRegex(ValueError, 'differs-from-commit'): trial.inputs(self.ready, manifest, Path('/fixture'))

    def test_historical_source_data_is_read_from_frozen_git_not_current_bundle(self):
        blobs, manifest, git, _ = self.freeze_fixture()
        def working(name, *args):
            self.assertNotIn(name, trial.SOURCE_FILES)
            return blobs[name]
        with patch.object(trial, 'read', side_effect=working), patch.object(trial, 'git_bytes', side_effect=git):
            trial.inputs(self.ready, manifest, Path('/fixture'))
        def altered_git(root, commit, name, *args):
            if name in trial.SOURCE_FILES:
                return b'changed frozen source'
            return git(root, commit, name, *args)
        with patch.object(trial, 'read', side_effect=working), patch.object(trial, 'git_bytes', side_effect=altered_git):
            with self.assertRaisesRegex(ValueError, 'input-hash-mismatch'):
                trial.inputs(self.ready, manifest, Path('/fixture'))

    def test_versioned_compact_observation_and_hosting_are_separate_boundaries(self):
        changes = [lambda s: s.update(schema='legacy'), lambda s: s.update(deployed_worker_bytes_independently_verified=True),
            lambda s: s.update(full_ask_okf_calls=1), lambda s: s.update(runner_sha256='f' * 64),
            lambda s: s['cases'][0].update(compact_text_structured_values_equal=False),
            lambda s: s['cases'][1].update(complete_package_matches_local_reference=False),
            lambda s: s['cases'][1].update(engine_id='wrong'), lambda s: s['cases'][1].update(source_version='f' * 40),
            lambda s: s['cases'][0].update(case_kind='historical-original-package'),
            lambda s: s['cases'][0].update(provenance_sha256='f' * 64), lambda s: s['cases'][0].update(reads=[]),
            lambda s: s['cases'][0].update(question_sha256='f' * 64), lambda s: s.update(cases=s['cases'][1:]),
            lambda s: s.update(artifacts={})]
        for mutate in changes:
            blobs, manifest, git, rebind = self.freeze_fixture(); sdk = json.loads(blobs[manifest['sdk_receipt']]); mutate(sdk)
            blobs[manifest['sdk_receipt']] = trial.encoded(sdk); rebind()
            with patch.object(trial, 'read', side_effect=lambda name, *args: blobs[name]), patch.object(trial, 'git_bytes', side_effect=git):
                with self.assertRaises(ValueError): trial.inputs(self.ready, manifest, Path('/fixture'))
        for change in [dict(source_commit='f' * 40), dict(runtime_worker_sha256='f' * 64), dict(deployment={'status': 'failed'})]:
            blobs, manifest, git, rebind = self.freeze_fixture(); dep = json.loads(blobs[manifest['deployment']]); dep.update(change)
            blobs[manifest['deployment']] = trial.encoded(dep); rebind()
            with patch.object(trial, 'read', side_effect=lambda name, *args: blobs[name]), patch.object(trial, 'git_bytes', side_effect=git):
                with self.assertRaises(ValueError): trial.inputs(self.ready, manifest, Path('/fixture'))

    def test_combined_source_and_received_gzip_must_match_actual_complete_package(self):
        for mode in ('legacy-semantic-bundle', 'base-index-digest', 'wrong-received-bytes', 'gzip-inflation'):
            blobs, manifest, git, rebind = self.freeze_fixture()
            if mode in ('legacy-semantic-bundle', 'base-index-digest'):
                source = json.loads(blobs[trial.SOURCE_FILES[0]])
                if mode == 'legacy-semantic-bundle': source['bundle'] = {'snapshot': 'synthetic-semantic'}
                else: source['base_index']['sha256'] = 'f' * 64
                blobs[trial.SOURCE_FILES[0]] = trial.encoded(source)
            else:
                name = manifest['cases'][0]['received_package']; blobs[name] = gzip.compress(b'x' * (524289 if mode == 'gzip-inflation' else 12), mtime=0)
                sdk = json.loads(blobs[manifest['sdk_receipt']]); sdk['artifacts'][name.rsplit('/', 1)[1]] = {'bytes': len(blobs[name]), 'sha256': event.sha(blobs[name])}
                blobs[manifest['sdk_receipt']] = trial.encoded(sdk)
            rebind()
            with patch.object(trial, 'read', side_effect=lambda name, *args: blobs[name]), patch.object(trial, 'git_bytes', side_effect=git):
                with self.assertRaises(ValueError): trial.inputs(self.ready, manifest, Path('/fixture'))

    def test_historical_public_result_is_only_a_synthetic_direct_fixture(self):
        path = trial.ROOT / 'validation/model-comparison/household-compact-v2/claude-subscription/control-unknown/attempt-01/model-output.json'
        retained = json.loads(path.read_bytes()); result = retained.get('provider_result')
        self.assertIsInstance(result, str)
        # This wraps a retained public terminal string synthetically; it does not
        # reclassify the old formatter invocation as a successful direct trial.
        census, value = event.recognise('claude-subscription', wire([{'type': 'result', 'subtype': 'success', 'is_error': False, 'result': result}]))
        self.assertIsInstance(value, dict); self.assertEqual(census['assistant_confirmation'], 'absent')
        self.assertEqual(retained['tool_event_names'], ['StructuredOutput'])


if __name__ == '__main__': unittest.main()
