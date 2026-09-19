"""Mechanical boundary controls; these do not grade legal reasoning."""
from copy import deepcopy
import json
import unittest

from evaluate_fixed_answers import SPEC, assess, load_case


class FixedAnswerTests(unittest.TestCase):
    def setUp(self):
        self.cases = json.loads((SPEC / "cases.json").read_text())["cases"]
        _, self.context = load_case(self.cases[0])
        record = self.context["selected"][0]["record"]
        provenance = record["provenance"][0]
        self.answer = {"context_id": self.context["context_id"], "package_evidence_status": "insufficient",
                       "answer_disposition": "partial_evidence_only", "summary": "Synthetic test, no substantive conclusion.",
                       "claims": [{"id": "c1", "statement": "Synthetic exact-quote control only.", "evidence": [{
                           "record_id": record["id"], "quote": record["text"][:100], "source_url": provenance["url"],
                           "locator": provenance["locator"]}], "scope_or_qualification": "Test fixture only."}],
                       "gaps": [], "abstentions": [], "limitations": ["Synthetic fixture, not a reviewed answer."]}

    def test_all_fixed_inputs_have_the_declared_identity(self):
        for case in self.cases:
            raw, context = load_case(case)
            self.assertGreater(len(raw), 0)
            self.assertEqual(context["evidence_status"], case["expected_package_status"])

    def test_literal_citation_controls_can_pass_without_claiming_truth(self):
        result = assess(self.answer, self.context)
        self.assertEqual(result["status"], "passed-mechanical-controls")
        self.assertEqual(result["entailment_review"], "pending-independent-human-review")
        self.assertFalse(result["specialist_accepted"])

    def test_altered_quote_and_invented_locator_are_rejected(self):
        for key, value in [("quote", "This exact quotation was invented for the negative control."),
                           ("record_id", "urn:invented"), ("locator", "invented page"),
                           ("source_url", "https://example.org/invented")]:
            answer = deepcopy(self.answer)
            answer["claims"][0]["evidence"][0][key] = value
            self.assertEqual(assess(answer, self.context)["status"], "failed-mechanical-controls")

    def test_no_evidence_requires_abstention(self):
        _, context = load_case(self.cases[2])
        result = assess(self.answer, context)
        self.assertIn("no_evidence_abstention_failed", result["failures"])

    def test_false_sufficiency_and_context_identity_are_rejected(self):
        answer = deepcopy(self.answer)
        answer.update(context_id="urn:wrong", package_evidence_status="sufficient", answer_disposition="bounded_source_answer")
        result = assess(answer, self.context)
        self.assertEqual(set(result["failures"]), {"wrong_context_id", "altered_evidence_status", "unsupported_complete_disposition"})

    def test_source_tampering_is_rejected_before_a_call(self):
        changed = dict(self.cases[0], source_sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "input digest"):
            load_case(changed)


if __name__ == "__main__":
    unittest.main()
