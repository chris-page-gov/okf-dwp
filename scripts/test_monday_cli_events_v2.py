"""Adversarial shape and formatter-correlation controls; no model calls."""
import json
import unittest
from copy import deepcopy
import monday_cli_events_v2 as parser


def inspect(provider,events):return parser.sanitise(provider,'\n'.join(map(json.dumps,events)).encode())
def formatter():return [{'type':'assistant','message':{'content':[{'type':'tool_use','id':'a','name':'StructuredOutput','input':{'outcome':'no_evidence'}}]}},{'type':'user','message':{'content':[{'type':'tool_result','tool_use_id':'a','content':'Done'}]}},{'type':'result','structured_output':{'outcome':'no_evidence'}}]


class EventTests(unittest.TestCase):
    def test_only_exact_observed_codex_warning_is_nonfatal(self):
        for text,accepted in [(parser.SKILL_WARNING,True),(parser.SKILL_WARNING+' extra',False),('unknown credential=private',False)]:
            result=inspect('codex-subscription',[{'type':'item.completed','item':{'id':'x','type':'error','message':text}},{'type':'turn.completed'}])
            self.assertEqual(not result['recognition_issues'],accepted);self.assertNotIn('private',json.dumps(result))

    def test_absent_or_false_formatter_error_flag_is_recorded_accurately(self):
        for flag in ['absent',False]:
            events=formatter()
            if flag!='absent':events[1]['message']['content'][0]['is_error']=flag
            result=inspect('claude-subscription',events);self.assertFalse(result['recognition_issues'])
            self.assertEqual(result['formatter_results'][0]['error_flag_presence'],'absent' if flag=='absent' else 'explicit-false')

    def test_reused_tool_id_duplicate_unmatched_or_failed_result_rejected(self):
        cases=[]
        events=formatter();events.insert(1,{'type':'assistant','message':{'content':[{'type':'tool_use','id':'a','name':'shell','input':{}}]}});cases.append(events)
        events=formatter();events.insert(2,deepcopy(events[1]));cases.append(events)
        events=formatter();events[1]['message']['content'][0]['tool_use_id']='unknown';cases.append(events)
        for flag in [True,'false',0,None]:
            events=formatter();events[1]['message']['content'][0]['is_error']=flag;cases.append(events)
        for events in cases:
            with self.subTest(events=events):self.assertTrue(inspect('claude-subscription',events)['recognition_issues'])

    def test_thinking_wrapper_requires_exact_observed_scalar_shape(self):
        event={'type':'system','subtype':'thinking_tokens','session_id':'private','uuid':'private','estimated_tokens':100,'estimated_tokens_delta':12}
        for changed in [event,{**event,'estimated_tokens':True},{**event,'reasoning':'private'}, {k:v for k,v in event.items() if k!='uuid'}]:
            result=inspect('claude-subscription',[changed,{'type':'result','result':'{}'}])
            self.assertEqual(not result['recognition_issues'],changed==event);self.assertNotIn('private',json.dumps(result))

    def test_final_output_must_match_successful_formatter_input(self):
        events=formatter();events[-1]['structured_output']={'outcome':'different'}
        self.assertIn('final-output-differs-from-successful-formatter',inspect('claude-subscription',events)['recognition_issues'])

    def test_rate_limit_shape_rejects_added_or_wrong_typed_fields(self):
        event={'type':'rate_limit_event','session_id':'private','uuid':'private','rate_limit_info':{'isUsingOverage':False,'overageResetsAt':1,'overageStatus':'allowed','rateLimitType':'five_hour','resetsAt':2,'status':'allowed','unifiedWindows':{'five_hour':{'resetsAt':2,'utilization':0.1},'seven_day':{'resetsAt':3,'utilization':0.2}}}}
        for value,accepted in [(event,True),({**event,'tool_use':{}},False)]:
            result=inspect('claude-subscription',[value,{'type':'result','result':'{}'}]);self.assertEqual(not result['recognition_issues'],accepted)
            self.assertNotIn('private',json.dumps(result))

    def test_unknown_or_incomplete_stream_never_passes(self):
        for events in [[{'type':'item.completed','item':{'type':'agent_message','text':'{}'}}],[{'type':'mcp_tool_call'},{'type':'turn.completed'}],[{'type':'turn.completed'},{'type':'turn.completed'}]]:
            self.assertTrue(inspect('codex-subscription',events)['recognition_issues'])


if __name__=='__main__':unittest.main()
