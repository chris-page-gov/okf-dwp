# Fixed-evidence answer review

[Changes](../../CHANGELOG.md) · [Backlog DWP-BL-010](../../docs/backlog.md) · [Work log](../../docs/work-log-2026-09-19.md)

**Three actual Claude Code trials are retained. Independent human review is
pending.** These are model outputs over fixed public packages, separate from
source capture, retrieval parity and the 43 engineering evaluations. They are
not gold answers, specialist approval or a fair comparison with Astra.

## Fixed conditions

The [case register](cases.json) pins three existing packages by source digest.
The [system prompt](system-prompt.txt), [user prompt](user-prompt.txt) and
[answer schema](answer.schema.json) are shared. Every call receives the complete
package, including scope, provenance, gaps and truncation, with no outside
retrieval. The input contexts are 31,312 bytes (abroad), 487,506 bytes (preserved
custody) and 4,383 bytes (no-result control). The case budget is a maximum of
524,288 context bytes; prompt bytes are recorded separately by their digest.

The harness uses the existing default Claude Code subscription, without a model
override. Safe mode disables customisations; built-in tools, MCP and browser
access are disabled, and sessions are not persisted. A one-line public capability
probe succeeded at the normal host boundary after a sandbox-only authentication
failure. No new login, installation or credential export was performed. Each
receipt records the CLI's observed model-usage entries, not an inferred model
configuration. Provider cost fields are not proof of a subscription charge.

## Observed first trial

| Case | Model disposition | Mechanical result | Remaining review |
| --- | --- | --- | --- |
| Abroad, full-corpus bounded package | Partial evidence only; 10 claims and 14 citations | Source IDs/locators/status retained; 10 citations fail strict verbatim checking, while 4 are exact. The 10 failures match after whitespace-only normalisation. Original failure retained. | Claim entailment, qualifications, source currency and missing-context handling |
| Custody, preserved narrow profile | Bounded source answer; 12 claims and 31 citations | All 31 quoted citations are exact; identity, locator and boundary controls pass | Whether each inference and benefit qualification is fully supported within the frozen scope |
| No-result control | Cannot establish; no claims | Correct no-evidence abstention; controls pass | Human confirmation that no unsupported explanation was introduced |

Read the actual answers and receipts under
[the baseline directory](../../validation/answer-review/claude-baseline-2026-09-19/).
The [quotation diagnosis](../../validation/answer-review/claude-baseline-2026-09-19/quotation-diagnosis.json)
distinguishes exact text from whitespace changes. It does not overwrite the
strict failure or establish that a passage entails a claim. We do not report
an unsupported-claim rate or an answer-quality score until claims are reviewed.

## Claim-level review rubric

For each answer, a reviewer records an outcome for every claim:

| Dimension | Review question | Hard failure |
| --- | --- | --- |
| Identity | Is this the requested context/version, and is each citation a selected record? | Invented or substituted evidence |
| Literal support | Does the quoted passage match the captured text, with any display normalisation explicitly identified? | Changed wording, missing negation or fabricated quote |
| Entailment | Does that passage actually support the claim, without external assumptions? | Decision-critical conclusion unsupported by its cited evidence |
| Conditions and exceptions | Are benefit variants, dates, jurisdiction and qualifying facts retained? | Simplified rule changes the supported meaning |
| Authority | Are official source wording, normalisation, authored relationships and model conclusions distinguished? | Model interpretation presented as official or specialist accepted |
| Completeness | Does the answer preserve package gaps, conflicts and truncation? | Insufficient package presented as a complete answer |
| Abstention | Does the model decline what the supplied evidence cannot establish? | No-evidence control produces a substantive answer |
| Usefulness | Can a reader inspect the exact source and understand the next evidence needed? | Citation is present but cannot be located or explained |

Allowed claim outcomes are `supported-within-stated-scope`, `partly-supported`,
`unsupported`, `contradicted`, `unclear-needs-review` and `not-a-substantive-claim`.
Record reasons and precise evidence. Unreviewed is not a passing grade. A single
decision-critical failure cannot be hidden by a high average.

## Replay without model calls

From the locked repository environment:

```sh
uv run --locked python scripts/evaluate_fixed_answers.py
uv run --locked python scripts/check_answer_review.py
uv run --locked python -m unittest discover -s scripts -p test_fixed_answers.py
```

The default evaluation mode checks retained answers; it does not call Claude.
Only explicit `--run` opts into subscription calls. Existing matching attempts
are replayed without calls; changed inputs require a new output directory and
must not overwrite the old run. An authentication/model error is not an answer.
The six checker tests use synthetic mutations; they do not grade these answers.

## Next comparison

The planned progressive interface supplies a compact manifest and exact evidence
reads with hashes and continuations. A later trial can reconstruct those spans
and use this rubric. To compare delivery or models fairly, freeze the same
question, source version, accessible evidence, prompt, output rules and reviewer
process. If the model receives different passages, describe it as a different
input condition, not a direct model-quality benchmark. Token/cost and expert
review measures need their own recorded denominators.
