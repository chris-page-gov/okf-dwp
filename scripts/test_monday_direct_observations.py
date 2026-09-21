"""Offline tamper controls; no provider, network or Git calls."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import check_monday_direct_observations as check


class DirectObservationChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trial, cls.freeze_raw, cls.freeze = check.load_frozen(check.ROOT)
        cls.protocol, _ = cls.trial.protocol()
        names = [check.SPEC + 'prompt.md', check.SPEC + 'answer.schema.json']
        cls.bound = {n: check.bounded(check.ROOT / n) for n in names}
        raw = check.bounded(check.ROOT / (check.SPEC + 'frozen/contexts/control-unknown.json'))
        cls.packages = {'control-unknown': (raw, cls.trial.package('control-unknown', raw, cls.protocol))}
        prompt = cls.trial.fixed_prompt('control-unknown', raw, cls.bound)
        cls.expected = cls.trial.binding('control-unknown', raw, prompt,
                                        cls.bound[check.SPEC + 'answer.schema.json'], cls.freeze_raw)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir='/private/tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        out = self.root / check.OUTPUT
        out.mkdir(parents=True)
        (out / 'README.md').write_text('Synthetic temporary test copy of recorded public observations.\n')
        for provider in check.PROVIDERS:
            p = Path(check.OUTPUT) / provider / 'control-unknown/attempt-01'
            (self.root / p).mkdir(parents=True)
            for name in ('receipt.json', 'model-output.json'):
                (self.root / p / name).write_bytes(check.bounded(check.ROOT / p / name))

    def run_outcomes(self):
        with patch.object(self.trial, 'OUT', self.root / check.OUTPUT):
            return check.outcomes(self.root, self.trial, self.protocol, self.bound, self.packages, self.freeze_raw)

    def target(self, name='receipt.json'):
        return self.root / check.OUTPUT / 'codex-subscription/control-unknown/attempt-01' / name

    def test_retained_census_and_frozen_gate_remain_closed(self):
        result = self.run_outcomes()
        self.assertEqual((result['recorded_attempts'], result['rejected_attempts'],
                          result['accepted_answers'], result['substantive_attempts']), (2, 2, 0, 0))
        self.assertEqual(result['unknown_tool_census_attempts'], 2)
        self.assertTrue(result['control_gate_closed'])

    def test_receipt_and_projection_byte_tampering_rejects(self):
        for name in ('receipt.json', 'model-output.json'):
            with self.subTest(name=name):
                p = self.target(name); original = p.read_bytes(); p.write_bytes(original + b' ')
                with self.assertRaisesRegex(ValueError, 'fingerprint differs'):
                    self.run_outcomes()
                p.write_bytes(original)

    def test_unregistered_provider_substantive_retry_and_private_file_reject(self):
        for name, kind in [('other-provider', 'dir'), ('codex-subscription/staff-012', 'dir'),
                           ('codex-subscription/control-unknown/attempt-02', 'dir'),
                           ('codex-subscription/control-unknown/attempt-01/raw-private.txt', 'file')]:
            with self.subTest(name=name):
                p = self.root / check.OUTPUT / name
                p.mkdir() if kind == 'dir' else p.write_text('Must never be read.')
                with self.assertRaisesRegex(ValueError, 'Unexpected experiment entry'):
                    self.run_outcomes()
                p.rmdir() if kind == 'dir' else p.unlink()

    def test_missing_answer_or_receipt_census_cannot_be_hidden(self):
        p = self.target(); original = p.read_bytes(); p.unlink()
        with self.assertRaisesRegex(ValueError, 'Missing experiment entry'):
            self.run_outcomes()
        p.write_bytes(original)
        answer = self.target('answer.json'); answer.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Unexpected experiment entry'):
            self.run_outcomes()

    def test_semantic_input_code_and_acceptance_tampering_rejects(self):
        r = json.loads(self.target().read_bytes()); p = json.loads(self.target('model-output.json').read_bytes())
        for mutation in ('input', 'loaded', 'answer', 'status'):
            bad = deepcopy(r)
            if mutation == 'input': bad['inputs']['context_sha256'] = '0' * 64
            elif mutation == 'loaded': bad['loaded_code_sha256'][check.CODE[0]] = '0' * 64
            elif mutation == 'answer': bad['answer_present'] = True
            else: bad['status'] = 'accepted-mechanical-only'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                check.check_attempt(bad, p, 'codex-subscription', self.expected, self.trial.LOADED, self.protocol)

    def test_unknown_census_must_not_be_upgraded_to_zero(self):
        r = json.loads(self.target().read_bytes()); p = json.loads(self.target('model-output.json').read_bytes())
        for key, value in [('tool_event_census', 'complete-zero-observed-tools'), ('stream_completed', True), ('issues', [])]:
            bad = deepcopy(p); bad[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'Recorded parser projection differs'):
                check.check_attempt(r, bad, 'codex-subscription', self.expected, self.trial.LOADED, self.protocol)

    def test_oversized_special_and_symlinked_paths_reject_before_read(self):
        p = self.root / 'bounded'; p.write_bytes(b'x' * 17)
        with self.assertRaises(ValueError): check.bounded(p, 16)
        p.unlink(); os.mkfifo(p)
        with self.assertRaises(ValueError): check.bounded(p)
        p.unlink(); p.symlink_to(self.target())
        with self.assertRaises(ValueError): check.bounded(p)
        p.unlink(); p.symlink_to(self.target().parent, target_is_directory=True)
        with self.assertRaises(ValueError): check.bounded(p / 'receipt.json')
        with self.assertRaises(ValueError): check.directory(p)

    def test_frozen_code_tampering_rejects_before_module_execution(self):
        names = [check.FREEZE, *check.CODE]
        for name in names:
            target = self.root / name; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(check.bounded(check.ROOT / name))
        code = self.root / check.CODE[1]; code.write_text('raise RuntimeError("must not execute")\n')
        with self.assertRaisesRegex(ValueError, 'Frozen code differs'):
            check.load_frozen(self.root)
        (self.root / check.FREEZE).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Approved freeze fingerprint differs'):
            check.load_frozen(self.root)


if __name__ == '__main__':
    unittest.main()
