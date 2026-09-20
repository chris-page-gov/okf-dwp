"""Synthetic diagnostic controls; no subscription calls."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import diagnose_monday_cli_events as diagnostic


class DiagnosticTests(unittest.TestCase):
    def test_error_redacts_paths_accounts_tokens_and_identifiers(self):
        raw='Warning /Users/private/.codex/config.toml user@example.invalid token=abc sk-secret123 https://example.invalid/private 12345678-abcd-1234-abcd-123456789abc'
        result=diagnostic.redacted_message(raw)
        for secret in ['Users','private','example.invalid','abc','secret123','12345678']:
            self.assertNotIn(secret,result)
        self.assertIn('Warning',result)

    def test_shapes_never_retain_private_field_values(self):
        event={'type':'system','subtype':'thinking_tokens','session_id':'private','mystery_account':'private','thinking_tokens':1000}
        result=diagnostic.census(json.dumps(event).encode())
        self.assertNotIn('private',json.dumps(result));self.assertNotIn('mystery_account',json.dumps(result))
        self.assertEqual(result['events'][0]['subtype'],'thinking_tokens')

    def test_formatter_result_requires_a_preceding_matching_identifier(self):
        events=[{'type':'assistant','message':{'content':[{'type':'tool_use','name':'StructuredOutput','id':'private-a','input':{'outcome':'no_evidence'}}]}},
                {'type':'user','message':{'content':[{'type':'tool_result','tool_use_id':'private-a','content':'private body'},{'type':'tool_result','tool_use_id':'private-b','content':'private body'}]}}]
        result=diagnostic.census('\n'.join(map(json.dumps,events)).encode())
        self.assertEqual([r['matches_preceding_structured_output'] for r in result['formatter_results']],[True,False])
        self.assertNotIn('private',json.dumps(result))

    def test_existing_output_refused_before_authentication_or_call(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(diagnostic,'OUT',Path(directory)),patch.object(diagnostic,'command') as command,patch.object(sys,'argv',['diagnostic','--run','--provider','codex-subscription']):
            (Path(directory)/'codex-subscription').mkdir()
            with self.assertRaises(FileExistsError):diagnostic.main()
            command.assert_not_called()


if __name__=='__main__':unittest.main()
