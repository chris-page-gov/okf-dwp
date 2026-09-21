"""Offline integrity controls using copies of public observations; no provider calls."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import check_monday_direct_v4_observations as check


class V4ObservationChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trial,cls.freeze_raw,cls.freeze=check.load_frozen(check.ROOT)
        cls.protocol,_=cls.trial.protocol()
        cls.bound={check.SPEC+n:check.bounded(check.ROOT/check.SPEC/n) for n in ('prompt.md','answer.schema.json')}
        cls.schema=cls.trial.events.strict_json(cls.bound[check.SPEC+'answer.schema.json'])
        cls.packages={}
        for case in check.CASES:
            raw=check.bounded(check.ROOT/check.SPEC/'frozen/contexts'/f'{case}.json',524288)
            cls.packages[case]=(raw,cls.trial.package(case,raw,cls.protocol))

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve())
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        for provider in check.PROVIDERS:
            for case in check.CASES:
                p=Path(check.OUTPUT)/provider/case/'attempt-01';(self.root/p).mkdir(parents=True)
                for n in ('receipt.json','model-output.json','answer.json'):
                    (self.root/p/n).write_bytes(check.bounded(check.ROOT/p/n))

    def target(self,name='receipt.json',case='staff-012',provider='codex-subscription'):
        return self.root/check.OUTPUT/provider/case/'attempt-01'/name

    def run_outcomes(self):
        with patch.object(self.trial,'OUT',self.root/check.OUTPUT):
            return check.outcomes(self.root,self.trial,self.protocol,self.bound,self.packages,self.freeze_raw)

    def direct(self,r=None,p=None,a=None):
        case='staff-012';provider='codex-subscription'
        r=r if r is not None else json.loads(self.target().read_bytes())
        p=p if p is not None else json.loads(self.target('model-output.json').read_bytes())
        a=a if a is not None else json.loads(self.target('answer.json').read_bytes())
        raw,c=self.packages[case];prompt=self.trial.fixed_prompt(case,raw,self.bound)
        expected=self.trial.binding(case,raw,prompt,self.bound[check.SPEC+'answer.schema.json'],self.freeze_raw)
        assessment=self.trial.mechanical(a,c,case,self.schema)
        return check.check_attempt(r,p,a,provider,case,expected,self.trial.LOADED,self.protocol,assessment)

    def test_actual_four_observations_replay_mechanical_checks_only(self):
        x=self.run_outcomes()
        self.assertEqual((x['recorded_attempts'],x['accepted_answers'],x['rejected_attempts']),(4,4,0))
        self.assertEqual((x['mechanically_checked_claims'],x['literal_citations_checked']),(6,7))
        self.assertTrue(x['both_control_gates_verified']);self.assertTrue(x['both_controls_preceded_substantive_attempts'])
        self.assertFalse(x['specialist_accepted']);self.assertEqual(x['provider_calls'],0)

    def test_each_attempt_artifact_has_immutable_byte_binding(self):
        for provider in check.PROVIDERS:
            for case in check.CASES:
                for name in ('receipt.json','model-output.json','answer.json'):
                    p=self.target(name,case,provider);raw=p.read_bytes();p.write_bytes(raw+b' ')
                    with self.subTest(provider=provider,case=case,name=name),self.assertRaisesRegex(ValueError,'fingerprint differs'):
                        self.run_outcomes()
                    p.write_bytes(raw)

    def test_extra_provider_case_retry_or_private_file_is_not_ignored(self):
        for n,kind in [('third-provider','dir'),('codex-subscription/other-case','dir'),
            ('codex-subscription/staff-012/attempt-02','dir'),('codex-subscription/staff-012/attempt-01/raw-private.txt','file')]:
            p=self.root/check.OUTPUT/n;p.mkdir() if kind=='dir' else p.write_text('not inspected')
            with self.assertRaisesRegex(ValueError,'Unexpected experiment entry'):self.run_outcomes()
            p.rmdir() if kind=='dir' else p.unlink()

    def test_missing_control_or_answer_cannot_be_presented_as_complete(self):
        for name,case in [('receipt.json','control-unknown'),('answer.json','staff-012')]:
            p=self.target(name,case);raw=p.read_bytes();p.unlink()
            with self.assertRaises((ValueError,FileNotFoundError)):self.run_outcomes()
            p.write_bytes(raw)

    def test_replayed_quotation_mechanical_assessment_is_not_trusted_blindly(self):
        a=json.loads(self.target('answer.json').read_bytes());a['claims'][0]['evidence'][0]['quote']='Fabricated source statement of sufficient length.'
        with self.assertRaisesRegex(ValueError,'assessment differs'):self.direct(a=a)
        r=json.loads(self.target().read_bytes());r['mechanical_assessment']['specialist_accepted']=True
        with self.assertRaisesRegex(ValueError,'assessment differs'):self.direct(r=r)

    def test_input_and_recorded_zero_tool_status_tampering_rejects(self):
        for field,value in [('status','rejected-events-or-answer-json'),('tool_event_census','unknown'),
            ('model_override','another-model'),('specialist_accepted',True)]:
            r=json.loads(self.target().read_bytes());r[field]=value
            with self.assertRaises(ValueError):self.direct(r=r)
        r=json.loads(self.target().read_bytes());r['inputs']['context_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'binding differs'):self.direct(r=r)
        p=json.loads(self.target('model-output.json').read_bytes());p['observed_tool_events']=1
        with self.assertRaisesRegex(ValueError,'zero-tool census differs'):self.direct(p=p)

    def test_synthetic_rejected_stream_remains_failure_and_unknown(self):
        r=json.loads(self.target().read_bytes());p=json.loads(self.target('model-output.json').read_bytes())
        r.update(status='rejected-events-or-answer-json',answer_present=False,tool_event_census='unknown')
        r.pop('mechanical_assessment');r['artefacts'].pop('answer.json')
        p.update(issues=['unknown-event'],stream_completed=False,tool_event_census='unknown')
        raw,c=self.packages['staff-012'];expected=self.trial.binding('staff-012',raw,
            self.trial.fixed_prompt('staff-012',raw,self.bound),self.bound[check.SPEC+'answer.schema.json'],self.freeze_raw)
        result=check.check_attempt(r,p,None,'codex-subscription','staff-012',expected,self.trial.LOADED,self.protocol,None)
        self.assertFalse(result['accepted']);self.assertTrue(result['unknown'])
        p['stream_completed']=True
        with self.assertRaisesRegex(ValueError,'Unknown census upgraded'):
            check.check_attempt(r,p,None,'codex-subscription','staff-012',expected,self.trial.LOADED,self.protocol,None)

    def test_optional_review_is_separate_and_cannot_introduce_special_files(self):
        p=self.root/check.OUTPUT/'independent-claim-review.md';p.write_text('Separate model review; not specialist acceptance.')
        self.assertEqual(self.run_outcomes()['accepted_answers'],4)
        p.unlink();p.symlink_to(self.target('answer.json'))
        with self.assertRaisesRegex(ValueError,'symlinked or special'):self.run_outcomes()

    def test_bound_files_links_fifo_and_race_are_rejected(self):
        p=self.root/'read';p.write_bytes(b'x'*17)
        with self.assertRaises(ValueError):check.bounded(p,16)
        p.unlink();os.mkfifo(p)
        with self.assertRaises(ValueError):check.bounded(p)
        p.unlink();p.symlink_to(self.target())
        with self.assertRaises(ValueError):check.bounded(p)
        p.unlink();p.symlink_to(self.target().parent,target_is_directory=True)
        with self.assertRaises(ValueError):check.bounded(p/'receipt.json')
        p.unlink();p.write_bytes(b'original');real_open=os.open
        def race(path,flags):
            self.assertTrue(flags&os.O_NONBLOCK);p.unlink();os.mkfifo(p);return real_open(path,flags)
        with patch.object(check.os,'open',side_effect=race):
            with self.assertRaisesRegex(ValueError,'Opened file changed'):check.bounded(p)

    def test_rehashed_synthetic_chronology_cannot_bypass_both_control_order(self):
        p=self.target();r=json.loads(p.read_bytes())
        r['started_at']='2026-09-21T07:00:00+00:00';r['finished_at']='2026-09-21T07:00:01+00:00';r['elapsed_seconds']=1
        raw=self.trial.encoded(r);p.write_bytes(raw)
        # A synthetic rehashed receipt still has to obey the semantic chronology.
        approved={**check.RECEIPTS,('codex-subscription','staff-012'):check.sha(raw)}
        with patch.object(check,'RECEIPTS',approved):
            with self.assertRaisesRegex(ValueError,'preceded both completed controls'):self.run_outcomes()


    def test_modified_module_is_rejected_before_execution(self):
        for n in [check.FREEZE,*check.CODE]:
            p=self.root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(check.bounded(check.ROOT/n))
        p=self.root/check.CODE[1];p.write_text('raise RuntimeError("must not execute")\n')
        with self.assertRaisesRegex(ValueError,'Frozen code differs'):check.load_frozen(self.root)
        (self.root/check.FREEZE).write_text('{}')
        with self.assertRaisesRegex(ValueError,'Approved freeze fingerprint differs'):check.load_frozen(self.root)


if __name__=='__main__':unittest.main()
