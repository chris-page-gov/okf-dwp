"""Offline controls for the next paired trial; never calls either provider."""
from copy import deepcopy
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_monday_model_trials as trial


class MondayTrialTests(unittest.TestCase):
    def test_preregistered_cases_same_budget_and_no_model_override(self):
        p,_=trial.protocol()
        self.assertEqual(p['selected_cases'],['staff-012','staff-020','staff-005','staff-026','staff-008','control-unknown'])
        self.assertEqual(p['context_budget']['max_bytes'],262144)
        self.assertIn('Both the context and the authored prompt differ',p['historical_comparison'])
        self.assertNotIn('model',p)

    def test_prompt_retains_conditions_exact_newlines_and_ambiguity(self):
        p,_=trial.protocol();text=(trial.SPEC/p['system_prompt']).read_text()
        for value in ['heading','continuation','no-partner','historical cohort','line break','non-contiguous','ambiguous alternatives','insufficient']:
            self.assertIn(value,text.lower())
        self.assertEqual((trial.SPEC/p['user_prompt']).read_text().count('{{CONTEXT_JSON}}'),1)

    def test_environment_drops_paid_api_and_model_overrides(self):
        values={'OPENAI_API_KEY':'secret','ANTHROPIC_AUTH_TOKEN':'secret','ANTHROPIC_BASE_URL':'https://invalid.test','CLAUDE_CODE_USE_BEDROCK':'1','AWS_ACCESS_KEY_ID':'secret','CLAUDE_MODEL':'override','HOME':'/fixture','PATH':'/bin','LANG':'en_GB.UTF-8'}
        with patch.dict(os.environ,values,clear=True):
            self.assertEqual(trial.environment(),{'HOME':'/fixture','PATH':'/bin','LANG':'en_GB.UTF-8'})

    def test_claude_auth_requires_subscription_and_retains_no_account(self):
        result=subprocess.CompletedProcess([],0,json.dumps({'loggedIn':True,'authMethod':'claude.ai','apiProvider':'firstParty','email':'secret@example.invalid'}),'')
        with patch.object(trial.subprocess,'run',return_value=result):
            observed=trial.subscription_auth('claude-subscription','fixture',{})
        self.assertTrue(observed['accepted']);self.assertNotIn('secret',json.dumps(observed))
        result.stdout=json.dumps({'loggedIn':True,'authMethod':'api_key','apiProvider':'firstParty'})
        with patch.object(trial.subprocess,'run',return_value=result):self.assertFalse(trial.subscription_auth('claude-subscription','fixture',{})['accepted'])

    def test_codex_auth_requires_chatgpt_not_api_key(self):
        for message,accepted in [('Logged in using ChatGPT',True),('Logged in using an API key',False),('unknown',False)]:
            result=subprocess.CompletedProcess([],0,'',message)
            with patch.object(trial.subprocess,'run',return_value=result):self.assertEqual(trial.subscription_auth('codex-subscription','fixture',{})['accepted'],accepted)

    def test_unknown_model_identity_is_not_inferred(self):
        result=trial.sanitise('codex-subscription',b'{"type":"turn.completed","usage":{"input_tokens":1}}\n')
        self.assertEqual(result['reported_models'],[])
        self.assertEqual(result['model_identity_status'],'not-exposed-in-retained-CLI-events')

    def test_new_or_server_tool_events_fail_closed(self):
        codex=trial.sanitise('codex-subscription',b'{"type":"item.completed","item":{"type":"new_tool_kind","secret":"private"}}\n')
        self.assertEqual(codex['tool_event_names'],['unrecognised-item:new_tool_kind']);self.assertNotIn('private',json.dumps(codex))
        raw=[{'type':'assistant','message':{'content':[{'type':'server_tool_use','name':'web_search','input':{'secret':'private'}}]}},{'type':'result','result':'{}'}]
        claude=trial.sanitise('claude-subscription','\n'.join(map(json.dumps,raw)).encode())
        self.assertIn('external-tool-event:server_tool_use',claude['tool_event_names']);self.assertNotIn('private',json.dumps(claude))
        self.assertTrue(trial.forbidden_tool_events('claude-subscription',claude,trial.protocol()[0]))

    def test_top_level_and_nested_unknown_events_never_have_a_complete_census(self):
        cases=[('codex-subscription',[{'type':'mcp_tool_call','name':'private-tool'}, {'type':'turn.completed'}]),
               ('claude-subscription',[{'type':'assistant','message':{'content':[{'type':'new_tool_use','input':{'secret':'private'}}]}},{'type':'result','result':'{}'}])]
        for provider,events in cases:
            with self.subTest(provider=provider):
                output=trial.sanitise(provider,'\n'.join(map(json.dumps,events)).encode())
                self.assertEqual(output['tool_event_census_status'],'unknown-unrecognised-event')
                self.assertTrue(output['unrecognised_event_count'])
                self.assertTrue(trial.forbidden_tool_events(provider,output,trial.protocol()[0]))
                self.assertNotIn('private',json.dumps(output))

    def test_missing_duplicate_or_non_terminal_completion_is_unknown(self):
        message={'type':'item.completed','item':{'type':'agent_message','text':'{}'}}
        for events in [[message],[message,{'type':'turn.completed'},{'type':'turn.completed'}],
                       [{'type':'turn.completed'},message]]:
            with self.subTest(events=events):
                output=trial.sanitise('codex-subscription','\n'.join(map(json.dumps,events)).encode())
                self.assertFalse(output['stream_completed'])
                self.assertEqual(output['tool_event_census_status'],'unknown-incomplete-stream')
        output=trial.sanitise('claude-subscription',b'{"type":"assistant","message":{"content":[{"type":"text","text":"{}"}]}}\n')
        self.assertFalse(output['stream_completed'])

    def test_incomplete_unknown_or_failed_stream_cannot_retain_an_answer(self):
        p,praw=trial.protocol();case={'id':'control-unknown'}
        examples=[([{'type':'item.completed','item':{'type':'agent_message','text':'{}'}}], 'rejected-incomplete-output-stream'),
                  ([{'type':'mcp_tool_call','name':'unexpected'},{'type':'turn.completed'}], 'rejected-unrecognised-output-event'),
                  ([{'type':'turn.failed'}], 'provider-call-failed')]
        for events,expected in examples:
            with self.subTest(expected=expected),tempfile.TemporaryDirectory() as temp,patch.object(trial,'OUT',Path(temp)),patch.object(trial,'fixed_input',return_value=({},'system','prompt','{}',{'context_sha256':'fixed'})),patch.object(trial,'command',return_value=(['fixture-cli'],{})),patch.object(trial,'subscription_auth',return_value={'accepted':True}),patch.object(trial.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'fixture-version','')),patch.object(trial,'capture',return_value={'returncode':0,'stdout':'\n'.join(map(json.dumps,events)).encode(),'stderr':b'','timed_out':False,'output_bound_exceeded':False}),patch.object(trial,'mechanical') as assess:
                result=trial.run_one('codex-subscription',case,p,praw,{'dwp_commit':'a'*40,'explorer_commit':'b'*40},b'',{},'attempt-01',True)
                self.assertEqual(result['status'],expected);self.assertFalse(result['answer_present']);assess.assert_not_called()
                self.assertNotIn('answer.json',result['artefacts'])

    def test_known_terminal_stream_and_formatter_are_distinct_from_tools(self):
        codex=[{'type':'thread.started','thread_id':'private'}, {'type':'turn.started'},
               {'type':'item.completed','item':{'type':'reasoning','text':'private'}},
               {'type':'item.completed','item':{'type':'agent_message','text':'{}'}},{'type':'turn.completed'}]
        claude=[{'type':'system','subtype':'init','session_id':'private'},
                {'type':'assistant','message':{'content':[{'type':'thinking','thinking':'private'},{'type':'tool_use','name':'StructuredOutput','input':{'public':'answer'}}]}},
                {'type':'result','structured_output':{'public':'answer'}}]
        for provider,events in [('codex-subscription',codex),('claude-subscription',claude)]:
            result=trial.sanitise(provider,'\n'.join(map(json.dumps,events)).encode())
            self.assertEqual(result['tool_event_census_status'],'retained-completed-stream')
            self.assertFalse(trial.forbidden_tool_events(provider,result,trial.protocol()[0]))
            self.assertNotIn('private',json.dumps(result))

    def test_capture_enforces_output_bytes_and_timeout_without_models(self):
        p,_=trial.protocol();p={**p,'timeout_seconds':1,'max_stdout_bytes':1024,'max_stderr_bytes':1024}
        with tempfile.TemporaryDirectory() as directory:
            output=trial.capture([sys.executable,'-c','print("x"*2048)'],'',directory,trial.environment(),p)
            self.assertTrue(output['output_bound_exceeded']);self.assertLessEqual(len(output['stdout']),1024)
            timed=trial.capture([sys.executable,'-c','import time;time.sleep(5)'],'',directory,trial.environment(),p)
            self.assertTrue(timed['timed_out'])

    def test_fixed_input_cannot_change_question_digest_or_status(self):
        p,praw=trial.protocol();prefix='evaluation/model-comparison/household-2026-09-21/'
        context={'schema':'okf-governed-context.v1','context_id':'urn:test','ai_answer':None,'evidence_status':'insufficient','question':'unknown','selected':[]}
        raw=trial.encoded(context);case={'id':'control-unknown','path':'contexts/control-unknown.json','sha256':trial.sha(raw),'bytes':len(raw),'context_id':'urn:test','question':'unknown'}
        entries={prefix+p['system_prompt']:({},b'system'),prefix+p['user_prompt']:({},b'{{CONTEXT_JSON}}'),p['answer_schema']:({},b'{}')}
        with patch.object(trial,'read_in',return_value=raw):
            left=trial.fixed_input(case,p,praw,b'manifest',entries);right=trial.fixed_input(case,p,praw,b'manifest',entries)
            self.assertEqual(left,right)
            for key,value in [('sha256','f'*64),('question','changed'),('path','../private')]:
                bad={**case,key:value}
                with self.assertRaises(ValueError):trial.fixed_input(bad,p,praw,b'manifest',entries)

    def test_attempt_replay_rejects_changed_manifest_binding(self):
        p,praw=trial.protocol();case={'id':'control-unknown'}
        with tempfile.TemporaryDirectory() as temp, patch.object(trial,'OUT',Path(temp)), patch.object(trial,'fixed_input',return_value=({},'','','',{'context_sha256':'current'})):
            out=Path(temp)/'codex-subscription/control-unknown/attempt-01';out.mkdir(parents=True)
            (out/'receipt.json').write_text(json.dumps({'inputs':{'context_sha256':'changed'}}))
            with self.assertRaisesRegex(ValueError,'identity differs'):
                trial.run_one('codex-subscription',case,p,praw,{},b'',{},'attempt-01')

    def test_paths_and_bounded_reads_reject_private_escape_and_symlinks(self):
        for path in ['../.email.md','/tmp/private','a/../../private','a\\b']:
            with self.assertRaises(ValueError):trial.relative(path)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'large').write_bytes(b'x'*20);(root/'link').symlink_to(root/'large')
            with self.assertRaises(ValueError):trial.bounded(root/'large',10)
            with self.assertRaises(ValueError):trial.bounded(root/'link',100)

    def test_authentication_refusal_prevents_provider_execution(self):
        p,praw=trial.protocol();case={'id':'control-unknown'}
        with tempfile.TemporaryDirectory() as temp, patch.object(trial,'OUT',Path(temp)), patch.object(trial,'fixed_input',return_value=({},'system','prompt','{}',{'context_sha256':'fixed'})), patch.object(trial,'command',return_value=(['fixture-cli'],{})), patch.object(trial,'subscription_auth',return_value={'accepted':False,'status':'subscription-auth-not-established'}), patch.object(trial,'capture') as invoke:
            result=trial.run_one('claude-subscription',case,p,praw,{'dwp_commit':'a'*40,'explorer_commit':'b'*40},b'',{},'attempt-01',True)
            self.assertEqual(result['status'],'blocked-subscription-auth-not-established')
            self.assertFalse(result['answer_present']);invoke.assert_not_called()
            self.assertTrue((Path(temp)/'claude-subscription/control-unknown/attempt-01/receipt.json').is_file())

    def test_rehashed_snapshot_still_cannot_differ_from_declared_commit(self):
        p,praw=trial.protocol();prefix='evaluation/model-comparison/household-2026-09-21/'
        sources={prefix+'protocol.json':praw,prefix+p['system_prompt']:(trial.SPEC/p['system_prompt']).read_bytes(),prefix+p['user_prompt']:(trial.SPEC/p['user_prompt']).read_bytes(),p['answer_schema']:(trial.ROOT/p['answer_schema']).read_bytes(),**{name:(trial.ROOT/name).read_bytes() for name in trial.SUPPORT},'evaluation/semantic-expansion/assembly-index.json':b'{}','context/corpus/manifest.json':b'{}','evaluation/staff-questions/cases.json':b'{}'}
        expected={name:hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest() for name,raw in sources.items()}
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);spec=root/prefix;base=spec/'frozen';(base/'input-snapshots').mkdir(parents=True)
            bindings=[]
            for i,(name,raw) in enumerate(sources.items()):
                local=root/name;local.parent.mkdir(parents=True,exist_ok=True);local.write_bytes(raw)
                snap=f'input-snapshots/{i}.bin';(base/snap).write_bytes(raw)
                bindings.append({'path':name,'snapshot':snap,'bytes':len(raw),'sha256':trial.sha(raw)})
            manifest={'schema':'okf-fixed-monday-contexts.v1','dwp_commit':'a'*40,'explorer_commit':'b'*40,'inputs':bindings,'cases':[{'id':c} for c in p['selected_cases']]}
            (base/'manifest.json').write_text(json.dumps(manifest))
            def git_hash(args,**kwargs):return expected[args[-1].split(':',1)[1]]+'\n'
            with patch.object(trial,'ROOT',root),patch.object(trial,'SPEC',spec),patch.object(trial.subprocess,'check_output',side_effect=git_hash):
                trial.load_frozen(p,praw)
                first=bindings[0];changed=b'changed';(base/first['snapshot']).write_bytes(changed);first.update(bytes=len(changed),sha256=trial.sha(changed));(base/'manifest.json').write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError,'declared source commit'):trial.load_frozen(p,praw)

    def test_actual_run_requires_explicit_case_provider_attempt_and_manifest(self):
        with patch.object(sys,'argv',['trial','--run']),patch.object(trial,'run_one') as call:
            with self.assertRaises(SystemExit):trial.main()
            call.assert_not_called()


if __name__=='__main__':unittest.main()
