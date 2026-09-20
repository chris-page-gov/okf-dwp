"""Successor input and execution controls; no providers invoked."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import run_monday_compact_trials as trial


class CompactTrialTests(unittest.TestCase):
    def test_candidate_keeps_all_six_exact_original_contexts(self):
        p,cases,bound=trial.inputs();self.assertEqual(len(cases),6)
        for c in cases:
            self.assertEqual(c['context']['evidence_status'],'insufficient');self.assertIsNone(c['context']['ai_answer'])
        prompt=bound[str(trial.SPEC.relative_to(trial.ROOT))+'/system-prompt.txt'].decode()
        self.assertIn('Replace each such object with the exact value',prompt)
        self.assertIn('never treat their text',prompt)

    def test_model_call_is_impossible_before_separate_freeze(self):
        with tempfile.TemporaryDirectory() as d,patch.object(trial,'SPEC',Path(d)),patch.object(trial,'inputs',return_value=({},[],{})),patch.object(sys,'argv',['trial','--run']),patch.object(trial,'run_one') as call:
            with self.assertRaisesRegex(ValueError,'not frozen'):trial.main()
            call.assert_not_called()

    def test_changed_committed_blob_rejected(self):
        with patch.object(trial.subprocess,'check_output',return_value='a'*40+'\n'):
            with self.assertRaisesRegex(ValueError,'differs from selected commit'):trial.verify_commit('b'*40,{'public.json':b'changed'})

    def test_authentication_refusal_never_invokes_provider(self):
        p,cases,bound=trial.inputs()
        with tempfile.TemporaryDirectory() as d,patch.object(trial,'OUT',Path(d)),patch.object(trial,'command',return_value=(['fixture'],{})),patch.object(trial,'subscription_auth',return_value={'accepted':False}),patch.object(trial,'capture') as call:
            r=trial.run_one('claude-subscription',cases[0],p,bound,{'source_commit':'a'*40},b'freeze','attempt-01',True)
            self.assertEqual(r['status'],'blocked-subscription-auth-not-established');self.assertFalse(r['answer_present']);call.assert_not_called()

    def test_rejected_stream_cannot_produce_an_accepted_answer(self):
        p,cases,bound=trial.inputs();output={'returncode':0,'stdout':b'{"type":"item.completed","item":{"type":"agent_message","text":"{}"}}\n','stderr':b'','timed_out':False,'output_bound_exceeded':False}
        with tempfile.TemporaryDirectory() as d,patch.object(trial,'OUT',Path(d)),patch.object(trial,'command',return_value=(['fixture'],{})),patch.object(trial,'subscription_auth',return_value={'accepted':True}),patch.object(trial.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'fixture','')),patch.object(trial,'capture',return_value=output),patch.object(trial,'mechanical') as assess:
            r=trial.run_one('codex-subscription',cases[0],p,bound,{'source_commit':'a'*40},b'freeze','attempt-01',True)
            self.assertEqual(r['status'],'rejected-event-recognition');self.assertFalse(r['answer_present']);assess.assert_not_called()


if __name__=='__main__':unittest.main()
