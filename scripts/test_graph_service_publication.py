"""Offline failure controls for separate graph publication status."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('graph_service_publication', Path(__file__).with_name('build_graph_service_publication.py'))
M = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)


class GraphServicePublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.addCleanup(self.temp.cleanup)
        self.dep_path = 'validation/compact-delivery/v0.8.0/deployment.json'
        self.sdk_dir = 'validation/graph-evidence/v0.8.0/sdk/attempt-01'
        self.paths = {kind: f'{self.sdk_dir}/{kind}.json' for kind in ('summary', 'plan', 'wire')}
        self.worker = '5' * 64; self.build_sha = 'a' * 64; self.source = 'b' * 40
        self.producer = '8' * 40; self.graph = '7' * 64
        self.engine = 'urn:okf:graph-engine:sha256:' + '6' * 64
        self.dep = {'schema': 'okf-compact-delivery-deployment.v1', 'service_version': '0.8.0',
                    'source_commit': self.source, 'runtime_commit': 'c' * 40, 'runtime_worker_sha256': self.worker,
                    'build_receipt_sha256': self.build_sha, 'graph_evidence': {'producer_commit': self.producer,
                    'graph_sha256': self.graph, 'engine_id': self.engine}, 'site_version_id': 'site-08',
                    'deployment': {'status': 'succeeded', 'type': 'publish', 'version_id': 'site-08',
                    'url': M.S.ORIGIN, 'updated_at': '2026-11-14T10:00:00Z'}}
        self.prov = {'repository_git_head': 'd' * 40, 'repository_worktree_clean': True,
                     'verifier_module_sha256': 'e' * 64, 'verifier_git_head_sha256': 'e' * 64,
                     'verifier_matches_git_head': True, 'package_lock_sha256': 'f' * 64,
                     'package_lock_git_head_sha256': 'f' * 64, 'package_lock_matches_git_head': True,
                     'local_worker_sha256': self.worker, 'build_receipt_sha256': self.build_sha,
                     'build_receipt_worker_sha256': self.worker, 'worker_matches_build_receipt': True,
                     'build_receipt_package_lock_sha256': 'f' * 64, 'package_lock_matches_build_receipt': True,
                     'build_receipt_verifier_sha256': 'e' * 64, 'verifier_matches_build_receipt': True,
                     'build_receipt_status': 'valid', 'build_receipt_input_file_count': 1,
                     'build_receipt_inputs_match_worktree': True,
                     'worker_hash_scope': 'local dist/server/index.js only; not a remote deployment attestation',
                     'source_identity_status': 'tracked-source-and-local-worker-match'}
        qsha = '1' * 64; psha = 'urn:sha256:' + '2' * 64; package = '3' * 64; text_sha = '4' * 64
        self.plan = {'schema': 'okf-graph-remote-verification-plan.v1', 'producer_commit': self.producer,
                     'graph_sha256': self.graph, 'engine_id': self.engine, 'publication_status': 'pinned',
                     'verifier_provenance': copy.deepcopy(self.prov), 'question_count': 1, 'case_occurrences': 2,
                     'predicted_http_requests': 5, 'questions': [{'question_sha256': qsha, 'case_ids': ['uc-a', 'uc-b'],
                     'groups': ['fixed-uc'], 'plan_id': psha, 'package_sha256': package,
                     'expected_record_ids': ['record-1', 'record-2', 'record-3', 'record-4'],
                     'expected_source_text_hashes': {f'record-{n}': text_sha for n in range(1, 5)}}]}
        self.wire = self.make_wire()
        self.summary = {'schema': 'okf-graph-remote-sdk-verification.v1', 'status': 'passed',
                        'run': {'mode': 'public', 'started_at': '2026-11-14T10:02:00Z', 'duration_ms': 1000,
                        'http_requests': 5, 'public_network_calls': 5, 'model_calls': 0, 'paid_api_calls': 0,
                        'automatic_retries': 0},
                        'identities': {'service_version': '0.8.0', 'graph_sha256': self.graph,
                        'engine_id': self.engine, 'producer_commit': self.producer, 'admission_status': 'pinned',
                        'sdk_v1_tool_rows_sha256': '9' * 64, 'sdk_v2_tool_rows_sha256': '9' * 64,
                        'verifier_provenance': copy.deepcopy(self.prov)},
                        'counts': {'source_case_occurrences': 2, 'unique_questions': 1,
                        'completed_unique_questions': 1, 'expected_positive_targets': 4,
                        'max_evidence_http_response_bytes': 20, 'bytes_received': 100,
                        'original_graph_obligation_count': 203},
                        'gates': {key: 'passed' for key in ('producer_package_identity','expected_targets_and_paths',
                        'source_text_hashes','insufficient_boundary','no_truncation','original_obligations_open',
                        'full_http_envelope_limit','sdk_v1_v2_tool_parity')},
                        'wire_receipt': {'calls': 5, 'bytes_received': 100, 'max_response_bytes': 20,
                        'max_evidence_response_bytes': 20, 'min_request_interval_ms': 750, 'automatic_retries': 0,
                        'events': copy.deepcopy(self.wire['events'])}}
        self.summary['gates'].update(legal_or_entitlement_sufficiency='not-assessed', accessibility='not-assessed',
                                     withheld_cases='attempt-02 regression replay; not a new blind trial')
        self.put(self.dep_path, self.dep)
        for kind, value in [('summary', self.summary), ('plan', self.plan), ('wire', self.wire)]:
            self.put(self.paths[kind], value)
        self.git('init', '-q'); self.git('config', 'user.name', 'Graph receipt test'); self.git('config', 'user.email', 'fixture@example.invalid')
        self.commit(); self.select()

    def git(self, *args):
        return subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', *args],
                                       cwd=self.root, stderr=subprocess.PIPE, timeout=10).decode().strip()

    def commit(self):
        self.git('add', 'validation')
        self.git('-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'Fixture receipts')
        self.commit_id = self.git('rev-parse', 'HEAD')

    def put(self, rel, value):
        path = self.root / rel; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

    def pin(self, path):
        raw = (self.root / path).read_bytes()
        return {'path': path, 'commit': self.commit_id, 'bytes': len(raw), 'sha256': M.S.sha(raw)}

    def select(self, graph_sdk=True, native=None):
        value = {'schema': 'okf-graph-service-publication-selection.v1', 'deployment': self.pin(self.dep_path),
                 'graph_sdk': ({kind: self.pin(path) for kind, path in self.paths.items()} if graph_sdk else None),
                 'native': self.pin(native) if native else None}
        self.put(M.SELECTION, value)

    def make_wire(self):
        items = [('GET', '/health', None, None), ('POST', '/graph/mcp', 'initialize', None),
                 ('POST', '/graph/mcp', 'tools/list', None), ('POST', '/graph/mcp', 'tools/call', 'plan_okf_evidence'),
                 ('POST', '/graph/mcp', 'tools/call', 'read_okf_planned_evidence')]
        events = []
        for i, (method, path, rpc, tool) in enumerate(items, 1):
            events.append({'sequence': i, 'method': method, 'path': path, 'rpc_method': rpc, 'tool': tool,
                           'request_bytes': 10, 'status': 200, 'response_bytes': 20, 'response_sha256': format(i, '064x')})
        return {'calls': 5, 'bytes_received': 100, 'max_response_bytes': 20, 'min_request_interval_ms': 750,
                'automatic_retries': 0, 'evidence_calls': 2, 'evidence_response_bytes': 40, 'events': events}

    def mutate_receipt(self, kind, mutate):
        value = copy.deepcopy({'summary': self.summary, 'plan': self.plan, 'wire': self.wire}[kind])
        mutate(value)
        self.put(self.paths[kind], value); self.commit(); self.select()

    def test_complete_public_graph_pass_and_independent_pending_statuses(self):
        result = M.derive(self.root); page = M.render(result)
        self.assertEqual(result['graph_sdk']['wire']['evidence_max_bytes'], 20)
        self.assertIsNone(result['native'])
        self.assertIn('passed **1 unique questions**', page)
        self.assertIn('**Pending.** No separate native plugin host receipt', page)
        self.assertIn('not remote attestation', page)
        result = M.derive(self.root)
        self.assertEqual(page, M.render(result))

    def test_null_graph_sdk_keeps_public_status_pending(self):
        self.select(graph_sdk=False)
        result = M.derive(self.root)
        page = M.render(result)
        self.assertIsNone(result['graph_sdk'])
        self.assertIn('**Pending for this deployment.**', page)

    def test_receipt_commits_prints_only_safely_parsed_selected_pins(self):
        output = io.StringIO()
        with patch.object(M, 'ROOT', self.root), patch.object(sys, 'argv', ['builder', '--receipt-commits']), redirect_stdout(output):
            M.main()
        self.assertEqual(output.getvalue(), self.commit_id + '\n')

    def test_deployment_graph_identity_worker_and_service_version_must_match(self):
        self.mutate_receipt('summary', lambda x: x['identities'].update(graph_sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'differs from deployed graph identity'):
            M.derive(self.root)
        self.mutate_receipt('summary', lambda x: x['identities']['verifier_provenance'].update(local_worker_sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'Local verifier Worker differs'):
            M.derive(self.root)

    def test_graph_observation_must_follow_selected_deployment(self):
        self.mutate_receipt('summary', lambda x: x['run'].update(started_at='2026-11-14T09:59:59Z'))
        with self.assertRaisesRegex(ValueError, 'predates selected deployment'):
            M.derive(self.root)

    def test_wire_rejects_oversized_evidence_envelope(self):
        self.mutate_receipt('wire', lambda x: x['events'][3].update(response_bytes=8193))
        with self.assertRaisesRegex(ValueError, '8 KiB envelope'):
            M.derive(self.root)

    def test_wire_rejects_unapproved_route_and_counter_drift(self):
        self.mutate_receipt('wire', lambda x: x['events'][3].update(path='/okf/mcp'))
        with self.assertRaisesRegex(ValueError, 'route differs'):
            M.derive(self.root)
        self.mutate_receipt('wire', lambda x: x.update(bytes_received=101))
        with self.assertRaisesRegex(ValueError, 'byte count differs'):
            M.derive(self.root)

    def test_plan_must_preserve_case_and_source_target_census(self):
        self.mutate_receipt('plan', lambda x: x['questions'][0].update(expected_record_ids=[]))
        with self.assertRaisesRegex(ValueError, 'Empty graph target set'):
            M.derive(self.root)

    def test_boundary_cases_can_have_no_targets_without_becoming_positive_recall(self):
        self.plan['questions'].append({'question_sha256': '0' * 64, 'case_ids': ['hospital-boundary'],
            'groups': ['legacy-boundary'], 'plan_id': 'urn:sha256:' + '0' * 64, 'package_sha256': '0' * 64,
            'expected_record_ids': [], 'expected_source_text_hashes': {}})
        self.plan['question_count'] = 2; self.plan['case_occurrences'] = 3
        self.summary['counts'].update(unique_questions=2, completed_unique_questions=2, source_case_occurrences=3)
        self.put(self.paths['plan'], self.plan); self.put(self.paths['summary'], self.summary); self.commit(); self.select()
        result = M.derive(self.root)
        self.assertEqual(result['graph_sdk']['plan']['positive_targets'], 4)
        self.assertEqual(result['graph_sdk']['plan']['case_occurrences'], 3)

    def test_missing_gate_and_unassessed_claims_are_enforced(self):
        self.mutate_receipt('summary', lambda x: x['gates'].update(source_text_hashes='not-assessed'))
        with self.assertRaisesRegex(ValueError, 'required graph SDK gate'):
            M.derive(self.root)
        self.mutate_receipt('summary', lambda x: x['gates'].update(accessibility='passed'))
        with self.assertRaisesRegex(ValueError, 'overclaims legal or accessibility'):
            M.derive(self.root)

    def test_newer_deployment_cannot_silently_reuse_graph_observation(self):
        new = copy.deepcopy(self.dep); new['deployment']['updated_at'] = '2026-11-15T10:00:00Z'
        self.put('validation/compact-delivery/v0.8.1/deployment.json', new); self.commit()
        with self.assertRaisesRegex(ValueError, 'not the latest successful deployment'):
            M.derive(self.root)

    def test_changed_selected_bytes_and_unpinned_paths_rejected(self):
        path = self.root / self.paths['summary']; path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'bytes differ'):
            M.derive(self.root)
        path.write_bytes(json.dumps(self.summary, indent=2).encode() + b'\n')
        selection = M.read_selection(self.root); selection['graph_sdk']['summary']['path'] = 'validation/graph-evidence/v0.9.0/sdk/attempt-01/summary.json'
        self.put(M.SELECTION, selection)
        with self.assertRaisesRegex(ValueError, 'Unregistered graph SDK receipt path'):
            M.derive(self.root)

    def test_symlink_receipt_fails_closed(self):
        path = self.root / self.paths['wire']; original = path.read_bytes(); path.unlink()
        path.symlink_to(self.root / self.paths['summary'])
        with self.assertRaisesRegex(ValueError, 'linked'):
            M.derive(self.root)

    def native_receipt(self):
        return {'schema': 'okf-graph-native-host-observation.v1', 'status': 'passed',
                'classification': 'actual-native-plugin-host', 'scope': 'representative-uc-client-observation',
                'started_at': '2026-11-14T10:04:00Z', 'completed_at': '2026-11-14T10:05:00Z',
                'deployment_binding': {'service_version': '0.8.0', 'source_commit': self.source,
                'worker_sha256': self.worker, 'scope': 'declared-selection-only; not remotely attested'},
                'identities': {'producer_commit': self.producer, 'graph_sha256': self.graph, 'engine_id': self.engine,
                'question_sha256': 'c224ca359a090e29fbca4e58127f5e94968aab1808e2e1ae3801b395a39eb3e8',
                'plan_id': self.plan['questions'][0]['plan_id'], 'package_sha256': self.plan['questions'][0]['package_sha256']},
                'discovery': {'tool_names': ['plan_okf_evidence', 'read_okf_planned_evidence'], 'tool_rows_sha256': None},
                'counts': {'observed_tool_calls': 5, 'max_mcp_result_json_bytes': 1200, 'continuation_calls': 2},
                'source_text_checks': [{'record_id': f'record-{n}', 'source_text_sha256': '4' * 64,
                                        'expected_source_text_sha256': '4' * 64, 'matched': True} for n in range(1, 5)],
                'gates': {'manifest_continuation': 'passed', 'source_text_hashes': 'passed', 'no_truncated_tool_output': 'passed'},
                'transport_scope': 'MCP result JSON bytes observed by connector; not HTTP envelope bytes',
                'full_matrix_claimed': False}

    def test_native_pass_is_separate_representative_observation(self):
        path = self.sdk_dir + '/native-observation.json'
        self.put(path, self.native_receipt()); self.commit(); self.select(native=path)
        result = M.derive(self.root); page = M.render(result)
        self.assertEqual(result['native']['scope'], 'representative-uc-client-observation')
        self.assertIn('not an HTTP envelope measurement or a full-suite claim', page)

    def test_native_can_pass_while_public_sdk_status_remains_pending(self):
        path = self.sdk_dir + '/native-observation.json'
        self.put(path, self.native_receipt()); self.commit(); self.select(graph_sdk=False, native=path)
        result = M.derive(self.root); page = M.render(result)
        self.assertIsNone(result['graph_sdk'])
        self.assertIsNotNone(result['native'])
        self.assertIn('**Pending for this deployment.** No matching public graph SDK receipt', page)
        self.assertIn('A separate native observation passed', page)

    def test_native_observation_cannot_claim_worker_attestation_or_wrong_source_hash(self):
        path = self.sdk_dir + '/native-observation.json'
        observation = self.native_receipt(); observation['deployment_binding']['scope'] = 'remotely attested'
        self.put(path, observation); self.commit(); self.select(native=path)
        with self.assertRaisesRegex(ValueError, 'deployment binding differs'):
            M.derive(self.root)
        observation = self.native_receipt(); observation['source_text_checks'][0]['source_text_sha256'] = '0' * 64
        self.put(path, observation); self.commit(); self.select(native=path)
        with self.assertRaisesRegex(ValueError, 'source-text checks are incomplete'):
            M.derive(self.root)

    def test_native_observation_must_follow_deployment(self):
        path = self.sdk_dir + '/native-observation.json'
        observation = self.native_receipt(); observation['started_at'] = '2026-11-14T09:59:00Z'
        self.put(path, observation); self.commit(); self.select(native=path)
        with self.assertRaisesRegex(ValueError, 'Native observation chronology differs'):
            M.derive(self.root)


if __name__ == '__main__':
    unittest.main()
