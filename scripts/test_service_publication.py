"""Synthetic, offline controls for recorded deployment status, never live service tests."""
import copy
import importlib.util
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('service_publication', Path(__file__).with_name('build_service_publication.py'))
M = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)


class ServicePublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve(strict=True)
        self.addCleanup(self.temp.cleanup)
        self.dep_path = 'validation/compact-delivery/v1.0.0/deployment.json'
        self.sdk_path = 'validation/compact-delivery/v1.0.0/sdk/attempt-01/observation.json'
        self.engine = 'urn:okf:context-engine:sha256:' + '3' * 64
        self.dep = {'schema': 'okf-compact-delivery-deployment.v1', 'service_version': '1.0.0',
                    'source_commit': '1' * 40, 'runtime_commit': '2' * 40, 'runtime_worker_sha256': '4' * 64,
                    'site_version_id': 'fixture-v1', 'deployment': {'status': 'succeeded', 'type': 'publish',
                    'version_id': 'fixture-v1', 'url': M.ORIGIN, 'updated_at': '2026-09-21T01:00:00Z'}}
        catalog = [{'engine_id': self.engine, 'source_commit': '5' * 40, 'source_versions': ['1' * 40]}]
        self.sdk = {'schema': 'okf-versioned-remote-verification.v1', 'classification': 'actual-public-http',
                    'passed': True, 'origin': M.ORIGIN, 'expected_service_version': '1.0.0',
                    'expected_worker_sha256': '4' * 64, 'current_source_version': '1' * 40,
                    'started_at': '2026-09-21T01:01:00Z', 'completed_at': '2026-09-21T01:02:00Z',
                    'comparison_commit': '6' * 40, 'deployed_worker_bytes_independently_verified': False,
                    'complete_tool_rows_equal': True, 'model_calls': 0, 'full_ask_okf_calls': 0,
                    'engine_catalogue': catalog, 'observed_health': {'version': '1.0.0', 'bundle_version': '1' * 40,
                    'engine_id': self.engine, 'approved_engines': catalog},
                    'transport': {'request_count': 2, 'automatic_retries': 0, 'received_bytes': 100,
                    'events': [{'sequence': 1, 'status': 200, 'response_bytes': 100},
                               {'sequence': 2, 'status': 202, 'response_bytes': 0}]},
                    'cases': [{'id': 'pair-00', 'case_kind': 'approved-source-engine-pair',
                    'source_version': '1' * 40, 'engine_id': self.engine,
                    'complete_package_matches_local_reference': True, 'compact_text_structured_values_equal': True}]}
        for identifier, kind in [('control', 'current-empty-control'), ('history', 'historical-original-package')]:
            self.sdk['cases'].append({**self.sdk['cases'][0], 'id': identifier, 'case_kind': kind})
        artifacts = {}
        for name, raw in [('executed-verifier.ts', b'// inert fixture\n'), ('build-receipt.json', b'{}\n')]:
            p = self.root / Path(self.sdk_path).parent / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(raw)
            artifacts[name] = {'bytes': len(raw), 'sha256': M.sha(raw)}
        self.sdk.update(artifacts=artifacts, runner_sha256=artifacts['executed-verifier.ts']['sha256'],
                        build_receipt_sha256=artifacts['build-receipt.json']['sha256'])
        self.put(self.dep_path, self.dep); self.put(self.sdk_path, self.sdk)
        self.git('init', '-q'); self.git('config', 'user.name', 'Synthetic test'); self.git('config', 'user.email', 'fixture@example.invalid')
        self.commit(); self.select()

    def git(self, *args):
        return subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', *args],
                                       cwd=self.root, stderr=subprocess.PIPE, timeout=10).decode().strip()

    def commit(self):
        self.git('add', 'validation'); self.git('-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'Synthetic receipts')
        self.commit_id = self.git('rev-parse', 'HEAD')

    def put(self, rel, value):
        p = self.root / rel; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value, indent=2) + '\n')

    def binding(self, rel):
        raw = (self.root / rel).read_bytes()
        return {'path': rel, 'commit': self.commit_id, 'bytes': len(raw), 'sha256': M.sha(raw)}

    def select(self, sdk=True):
        self.put(M.SELECTION, {'schema': 'okf-service-publication-selection.v1', 'deployment': self.binding(self.dep_path),
                              'sdk': self.binding(self.sdk_path) if sdk else None})

    def changed_sdk(self, mutate):
        mutate(self.sdk); self.put(self.sdk_path, self.sdk); self.commit(); self.select()

    def test_actual_receipt_shapes_and_deterministic_generated_page(self):
        result = M.derive(self.root); text = M.render(result)
        self.assertEqual(result['detail']['requests'], 2)
        self.assertIn('1 × HTTP 200, 1 × HTTP 202', text)
        self.assertIn('not real-time health', text)
        self.assertIn('21 September 2026 at 02:00:00 BST', text)
        self.assertIn('21 September 2026 at 02:02:00 BST', text)
        self.assertIn('SDK verifier commit: `' + '6' * 40, text)
        self.assertEqual(text, M.render(M.derive(self.root)))

    def test_newer_unrepresented_deployment_rejected(self):
        future = copy.deepcopy(self.dep); future['deployment']['updated_at'] = '2026-09-22T01:00:00Z'
        self.put('validation/compact-delivery/v1.0.1/deployment.json', future)
        with self.assertRaisesRegex(ValueError, 'newer successful deployment'): M.derive(self.root)

    def test_same_version_redeployment_requires_pending_not_old_pass(self):
        self.dep_path = 'validation/compact-delivery/v1.0.0-followup-20260922/deployment.json'
        self.dep['deployment']['updated_at'] = '2026-09-22T01:00:00Z'
        self.put(self.dep_path, self.dep); self.commit(); self.select()
        with self.assertRaisesRegex(ValueError, 'inherit an earlier SDK pass'): M.derive(self.root)
        self.select(sdk=False); result = M.derive(self.root)
        self.assertIsNone(result['sdk']); self.assertIn('**Pending for this publication.**', M.render(result))

    def test_newer_matching_sdk_must_be_selected(self):
        later = copy.deepcopy(self.sdk); later['started_at'] = '2026-09-21T02:00:00Z'; later['completed_at'] = '2026-09-21T02:01:00Z'
        self.put('validation/compact-delivery/v1.0.0/sdk/attempt-02/observation.json', later)
        with self.assertRaisesRegex(ValueError, 'newer successful SDK'): M.derive(self.root)

    def test_missing_success_cannot_be_hidden_as_pending(self):
        self.select(sdk=False)
        with self.assertRaisesRegex(ValueError, 'successful SDK'): M.derive(self.root)

    def test_changed_receipt_hash_rejected(self):
        (self.root / self.sdk_path).write_bytes((self.root / self.sdk_path).read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'receipt bytes differ'): M.derive(self.root)

    def test_updated_hash_cannot_replace_immutable_receipt(self):
        self.sdk['completed_at'] = '2026-09-21T01:03:00Z'; self.put(self.sdk_path, self.sdk); self.select()
        with self.assertRaisesRegex(ValueError, 'Immutable receipt size|immutable Git blob'): M.derive(self.root)

    def test_mismatched_source_worker_and_origin_are_not_accepted(self):
        for field, value in [('current_source_version', '9' * 40), ('expected_worker_sha256', '9' * 64), ('origin', 'https://example.test')]:
            with self.subTest(field=field):
                mutated = copy.deepcopy(self.sdk); mutated[field] = value; self.put(self.sdk_path, mutated)
                with self.assertRaises(ValueError): M.derive(self.root)
        self.put(self.sdk_path, self.sdk)

    def test_incomplete_pair_census_rejected(self):
        self.changed_sdk(lambda v: v['engine_catalogue'][0]['source_versions'].append('9' * 40))
        with self.assertRaisesRegex(ValueError, 'pair is omitted'): M.derive(self.root)

    def test_transport_count_and_reconstruction_failure_rejected(self):
        self.changed_sdk(lambda v: v['transport'].update(request_count=3))
        with self.assertRaisesRegex(ValueError, 'Request census'): M.derive(self.root)
        self.changed_sdk(lambda v: (v['transport'].update(request_count=2), v['cases'][0].update(complete_package_matches_local_reference=False)))
        with self.assertRaisesRegex(ValueError, 'reconstruction'): M.derive(self.root)

    def test_failed_attempt_preserved_but_does_not_replace_pass(self):
        self.put('validation/compact-delivery/v1.0.0/sdk/attempt-02/failure.json', {'schema': 'recorded-failure', 'passed': False})
        self.assertEqual(M.derive(self.root)['sdk']['path'], self.sdk_path)

    def test_unknown_schema_location_and_duplicate_json_rejected(self):
        path = 'validation/compact-delivery/unregistered/deployment.json'; self.put(path, self.dep)
        with self.assertRaisesRegex(ValueError, 'Unregistered'): M.derive(self.root)
        (self.root / path).unlink()
        bad = copy.deepcopy(self.dep); bad['schema'] = 'unknown'; self.put(self.dep_path, bad)
        with self.assertRaisesRegex(ValueError, 'Unknown compact'): M.derive(self.root)
        for raw in [b'{"passed":true,"passed":false}', b'{"x":1e999}', b'{"x":NaN}']:
            with self.assertRaises(ValueError): M.strict_json(raw)

    def test_symlink_root_parent_member_and_artifact_refused(self):
        link = self.root / 'alias'; link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError): M.derive(link)
        target = self.root / self.sdk_path; original = target.read_bytes(); target.unlink(); target.symlink_to(self.root / self.dep_path)
        with self.assertRaisesRegex(ValueError, 'Linked census'): M.derive(self.root)
        target.unlink(); target.write_bytes(original); link.unlink()
        artifact = self.root / Path(self.sdk_path).parent / 'build-receipt.json'; artifact.unlink(); artifact.symlink_to(target)
        with self.assertRaises(ValueError): M.derive(self.root)

    def test_oversized_receipt_and_census_caps_rejected(self):
        with patch.object(M, 'MAX_RECEIPTS', 1):
            with self.assertRaisesRegex(ValueError, 'Receipt census cap'): M.derive(self.root)
        with patch.object(M, 'MAX_ENTRIES', 1):
            with self.assertRaisesRegex(ValueError, 'entry cap'): M.derive(self.root)
        with patch.object(M, 'MAX_CENSUS_BYTES', 1):
            with self.assertRaisesRegex(ValueError, 'byte cap'): M.derive(self.root)
        (self.root / self.sdk_path).write_bytes(b' ' * (M.MAX_FILE + 1))
        with self.assertRaisesRegex(ValueError, 'oversized'): M.derive(self.root)

    def test_ambiguous_latest_deployments_fail_closed(self):
        self.put('validation/compact-delivery/v1.0.1/deployment.json', self.dep)
        with self.assertRaisesRegex(ValueError, 'Ambiguous latest'): M.derive(self.root)

    def test_missing_empty_control_rejected(self):
        self.changed_sdk(lambda v: v['cases'].pop(1))
        with self.assertRaisesRegex(ValueError, 'required control'): M.derive(self.root)

    def test_generated_status_drift_rejected_by_check_mode(self):
        (self.root / 'docs').mkdir()
        with patch.object(M, 'ROOT', self.root), patch('sys.argv', ['builder']), redirect_stdout(io.StringIO()):
            M.main()
        with patch.object(M, 'ROOT', self.root), patch('sys.argv', ['builder', '--check']), redirect_stdout(io.StringIO()):
            M.main()
            (self.root / M.OUTPUT).write_text('Service is undeployed.\n')
            with self.assertRaisesRegex(ValueError, 'page is stale'): M.main()

    def test_commit_export_is_bounded_and_validated(self):
        output = io.StringIO()
        with patch.object(M, 'ROOT', self.root), patch('sys.argv', ['builder', '--receipt-commits']), redirect_stdout(output):
            M.main()
        self.assertEqual(output.getvalue(), self.commit_id + '\n')
        selection = json.loads((self.root / M.SELECTION).read_text())
        selection['deployment']['commit'] = '--upload-pack=unsafe'
        self.put(M.SELECTION, selection)
        with self.assertRaisesRegex(ValueError, 'immutable identifier'): M.read_selection(self.root)

    def test_artifact_mutation_refused(self):
        (self.root / Path(self.sdk_path).parent / 'executed-verifier.ts').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'artefact bytes'): M.derive(self.root)


if __name__ == '__main__':
    unittest.main()
