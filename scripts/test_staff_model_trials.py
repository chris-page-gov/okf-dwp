#!/usr/bin/env python3
"""Offline model-trial privacy, boundary and citation controls."""
import copy
import ast
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from run_staff_model_trials import command, forbidden_tool_events, mechanical, numerical, parse_answer, safe_environment, sanitise_claude, sanitise_codex


class StaffModelTrialTests(unittest.TestCase):
    def setUp(self):
        self.text = "This exact source sentence is retained with a condition."
        self.context = {"context_id": "urn:sha256:fixture", "evidence_status": "insufficient",
                        "budget": {"truncated": True}, "selected": [{"record": {"id": "urn:evidence:1", "text": self.text,
                        "provenance": [{"url": "https://example.invalid/source", "locator": "paragraph 1"}]}}]}
        self.answer = {"context_id": "urn:sha256:fixture", "package_evidence_status": "insufficient",
                       "answer_disposition": "partial_evidence_only", "summary": "The package is truncated and insufficient.",
                       "claims": [{"id": "c1", "statement": "The source includes a condition.",
                                   "evidence": [{"record_id": "urn:evidence:1", "quote": self.text,
                                                 "source_url": "https://example.invalid/source", "locator": "paragraph 1"}],
                                   "scope_or_qualification": "Only the supplied fixture."}],
                       "gaps": ["No full answer."], "abstentions": ["No individual decision."], "limitations": ["Unreviewed."]}

    def test_exact_claim_pass_is_not_specialist_acceptance(self):
        result = mechanical(self.answer, self.context)
        self.assertEqual(result["status"], "passed-mechanical-controls")
        self.assertFalse(result["specialist_accepted"])

    def test_nonverbatim_quote_fails(self):
        self.answer["claims"][0]["evidence"][0]["quote"] = "This approximate sentence is not in the supplied source."
        self.assertIn("c1:quote_not_verbatim", mechanical(self.answer, self.context)["failures"])

    def test_invented_record_fails(self):
        self.answer["claims"][0]["evidence"][0]["record_id"] = "urn:invented:2"
        self.assertIn("c1:unknown_record", mechanical(self.answer, self.context)["failures"])

    def test_invented_source_locator_fails(self):
        self.answer["claims"][0]["evidence"][0]["locator"] = "paragraph 999"
        self.assertIn("c1:source_locator_not_in_package", mechanical(self.answer, self.context)["failures"])

    def test_insufficiency_cannot_be_upgraded(self):
        self.answer["answer_disposition"] = "bounded_source_answer"
        self.assertIn("unsupported_complete_disposition", mechanical(self.answer, self.context)["failures"])

    def test_truncation_must_be_declared(self):
        self.answer["summary"] = "This is the answer."
        self.assertIn("package_truncation_not_explicit_in_summary", mechanical(self.answer, self.context)["failures"])

    def test_no_evidence_control_requires_abstention(self):
        self.context["selected"] = []
        self.assertIn("no_evidence_abstention_failed", mechanical(self.answer, self.context)["failures"])

    def test_invalid_schema_retained_as_failure(self):
        self.answer["invented"] = "field"
        self.assertEqual(mechanical(self.answer, self.context)["failures"], ["answer_schema_invalid"])

    def test_codex_retains_no_session_account_or_reasoning(self):
        events = [{"type": "thread.started", "thread_id": "secret-session"},
                  {"type": "item.completed", "item": {"type": "reasoning", "text": "private reasoning"}},
                  {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(self.answer)}},
                  {"type": "turn.completed", "usage": {"input_tokens": 12, "output_tokens": 13, "account_id": "private-account", "session_number": 987654}}]
        result = sanitise_codex("\n".join(map(json.dumps, events)))
        for secret in ["secret-session", "private reasoning", "private-account"]:
            self.assertNotIn(secret, json.dumps(result))
        self.assertEqual(result["reported_models"], [])
        self.assertNotIn("session_number", result["usage"])
        self.assertEqual(parse_answer(result["provider_result"]), self.answer)

    def test_codex_tool_event_is_detected_without_publishing_arguments(self):
        events = [{"type": "item.completed", "item": {"type": "command_execution", "command": "private command", "output": "private output"}}]
        result = sanitise_codex("\n".join(map(json.dumps, events)))
        self.assertEqual(result["tool_event_names"], ["command_execution"])
        self.assertNotIn("private command", json.dumps(result))

    def test_claude_excludes_initialisation_and_retains_tool_census(self):
        events = [{"type": "system", "session_id": "private-session", "apiKeySource": "private-key"},
                  {"type": "assistant", "message": {"model": "observed-model", "content": [{"type": "thinking", "thinking": "private reasoning"},
                    {"type": "tool_use", "name": "Browse", "input": {"token": "private-token"}}]}},
                  {"type": "result", "structured_output": self.answer, "usage": {"input_tokens": 8}, "session_id": "private-session"}]
        result = sanitise_claude("\n".join(map(json.dumps, events)))
        self.assertEqual(result["tool_event_names"], ["Browse"])
        self.assertEqual(result["reported_models"], ["observed-model"])
        for secret in ["private-session", "private-key", "private reasoning", "private-token"]:
            self.assertNotIn(secret, json.dumps(result))

    def test_ambient_api_credentials_not_forwarded(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "fixture", "ANTHROPIC_API_KEY": "fixture", "CLAUDECODE": "fixture"}):
            env = safe_environment()
            self.assertNotIn("OPENAI_API_KEY", env)
            self.assertNotIn("ANTHROPIC_API_KEY", env)
            self.assertNotIn("CLAUDECODE", env)

    def test_only_preregistered_claude_formatter_is_permitted(self):
        output = {"tool_event_names": ["StructuredOutput", "Browse"]}
        self.assertEqual(forbidden_tool_events("claude-subscription", output, {}), ["StructuredOutput", "Browse"])
        protocol = {"allowed_formatting_events": {"claude-subscription": ["StructuredOutput"]}}
        self.assertEqual(forbidden_tool_events("claude-subscription", output, protocol), ["Browse"])
        with self.assertRaises(ValueError):
            forbidden_tool_events("codex-subscription", output, {"allowed_formatting_events": {"codex-subscription": ["StructuredOutput"]}})

    def test_formatter_arguments_are_hashed_not_retained(self):
        events = [{"type":"assistant", "message":{"content":[{"type":"tool_use", "name":"StructuredOutput", "input":{"secret":"fixture-private"}}]}},
                  {"type":"result", "result":"{}"}]
        result = sanitise_claude("\n".join(map(json.dumps, events)))
        self.assertNotIn("fixture-private", json.dumps(result))
        self.assertEqual(len(result["tool_events"][0]["input_sha256"]),64)

    def test_codex_isolation_is_process_local_and_uses_no_model_override(self):
        with tempfile.TemporaryDirectory() as directory, patch("run_staff_model_trials.skill_overrides", return_value=("[]", 0)), patch("run_staff_model_trials.shutil.which", return_value="codex"):
            args, controls = command("codex-subscription", directory, "fixture system", "{}")
            self.assertIn("--ignore-user-config", args)
            self.assertIn("--ephemeral", args)
            self.assertIn("skills.config=[]", args)
            self.assertNotIn("--model", args)
            self.assertIn("read-only", args)
            self.assertEqual((Path(directory) / "system-prompt.txt").read_text(), "fixture system")

    def test_retained_execution_note_checks_identical_call_functions(self):
        root = Path(__file__).resolve().parents[1]
        note = json.loads((root/"validation/model-comparison/staff-2026-09-20/execution-provenance.json").read_text())
        snapshots = root/"evaluation/model-comparison/staff-2026-09-20/input-snapshots"
        for digest in [note["batch_invocation_startup_harness_sha256"],note["report_only_revision_harness_sha256"]]:
            raw = (snapshots/(digest+".py")).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
            tree=ast.parse(raw)
            for name,expected in note["identical_function_source_sha256"].items():
                function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
                self.assertEqual(hashlib.sha256(ast.get_source_segment(raw.decode(),function).encode()).hexdigest(),expected)

    def test_retained_model_critique_binds_every_claim_without_accepting_it(self):
        root=Path(__file__).resolve().parents[1]
        critique=json.loads((root/"validation/model-comparison/staff-2026-09-20/claim-level-model-critique.json").read_text())
        self.assertFalse(critique["specialist_accepted"])
        self.assertEqual(critique["human_review"],"pending")
        self.assertIsNone(critique["unsupported_claim_rate"])
        retained={str(p.relative_to(root)) for p in (root/"validation/model-comparison/staff-2026-09-20").glob("*/*/attempt-*/answer.json")}
        self.assertEqual(retained,{review["answer_path"] for review in critique["reviews"]})
        for review in critique["reviews"]:
            raw=(root/review["answer_path"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),review["answer_sha256"])
            answer=json.loads(raw)
            context_raw=(root/"evaluation/model-comparison/staff-2026-09-20/contexts"/(review["case_id"]+".json")).read_bytes()
            self.assertEqual(hashlib.sha256(context_raw).hexdigest(),review["context_sha256"])
            self.assertEqual({c["id"] for c in answer["claims"]},{c["claim_id"] for c in review["claim_reviews"]})
            self.assertTrue(all(c["human_acceptance"]=="pending" and c["explanation"] for c in review["claim_reviews"]))


if __name__ == "__main__":
    unittest.main()
