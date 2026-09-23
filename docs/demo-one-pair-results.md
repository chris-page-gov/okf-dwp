# Demo 1: what the four answers show

**Four answers were completed, with no retries. No further answer calls are
permitted for this freeze.** All used the reported model `claude-opus-5`, one turn
per answer, with no tools, browsing or subagents. These are two known development
questions, with an unblinded agent review. They are not specialist acceptance or
a general measure of answer accuracy.

Read the [pre-declared protocol](demo-one-pair-protocol.md) and the
[reproducible observations](../validation/demo-1-freeze/comparison/observations.json).
The original answer text, including failures, is retained beside that record.
Public transport streams omit private reasoning, account rate-limit events and non-essential session
metadata; the original stream hashes and unchanged answer hashes are recorded in
[the publication receipt](../validation/demo-1-freeze/comparison/transport-publication.json).
No answer has been silently corrected.

## Result in plain English

The OKF arms supplied checkable sources and made the model's limits more visible.
They did **not** eliminate interpretation errors. The care-home answer confused
unmet evidence requirements with missing profiles; the savings answer used an ambiguous
qualification about Savings Credit. Both need review before being presented as
benefits guidance.

This experiment gives **no evidence of token savings**. Supplying the selected
records and their governance metadata used substantially more input tokens than
asking the model to recall an answer without evidence. That is an intentionally
simple baseline, not a measured web-search or Data Agent workflow. We have not
measured the end-to-end cost of preparing and verifying equivalent evidence by
those other methods.

## Observed delivery and format

| Question and arm | Input tokens, including cache creation/read | Output tokens | Elapsed seconds | Output format |
| --- | ---: | ---: | ---: | --- |
| Savings, unassisted | 860 | 1,558 | 22.583 | Invalid JSON; preserved unchanged |
| Savings, OKF | 101,026 | 2,301 | 28.842 | Declared format checks pass |
| Care home, unassisted | 867 | 2,262 | 35.556 | Summary exceeds 1,400 characters |
| Care home, OKF | 72,129 | 3,203 | 39.144 | Summary exceeds 1,400 characters |

The client reports two uncached input tokens per answer, with the remaining input
in cache-creation accounting and zero cache-read tokens. The table adds these
categories; it does not mistake `input_tokens=2` for a tiny prompt. Output totals
include the client's reported thinking tokens. Client list-price estimates are
not evidence of subscription charges or of the owner's remaining allowance.

All **12 quoted citations in the two OKF responses match selected source text**.
That is a mechanical integrity result. A quotation can be exact but too short to
support the surrounding claim, and a supported main claim can have a faulty
qualification. Both happened here.

## Claim review: savings question, staff-006

The exact question asks for the maximum savings compatible with Pension Credit.
The unassisted answer gives an unverified recollection about the absence of an
upper capital limit and the deemed-income rule. It gives no citations, as required
for that arm. Its malformed JSON prevents automatic structured claim evaluation;
its prose remains inspectable. This comparison does not independently establish
that every recollected legal proposition is correct today.

The OKF answer makes four claims:

1. **Deemed income versus a capital ceiling:** the retained DMG 84911 passage
   supports a tariff-income rule involving £10,000 and £500 increments. The
   cited fragment is exact but omits the operative surrounding wording. The
   complete record supports the narrower tariff explanation; it does not prove
   the non-existence of every possible restriction elsewhere.
2. **Capital classification and disregards:** the complete DMG 84002 record
   supports the preparation steps described. The quote is a fragment of that
   list. Full conditions and current applicability remain unresolved.
3. **Partner's capital:** DMG 84921 supports the aggregation point in the stated
   household scope. No individual household or award is established.
4. **Entitlement conditions:** DMG 77031 supports the distinction between the
   general entitlement gates and a supposed single savings ceiling. However,
   the answer's qualification calls dated Savings Credit restrictions
   “additional amounts”. DMG 77350 itself describes Savings Credit as an additional amount,
   but the answer appears to apply that description to its restrictions. The
   wording is ambiguous and the citation to 77031 does not resolve it. The
   claim needs clearer component/condition wording before acceptance.

This is useful source-grounded partial reasoning, with an unresolved interpretation
qualification. It is not a verified current-law answer to the whole question.

## Claim review: care-home question, staff-012

The unassisted answer states a broad non-cessation conclusion and describes
additional amounts, housing, capital and household effects. Every claim is marked
unverified and has no source citation. It is not a source-checked benchmark answer.

The OKF answer also makes four claims:

1. **No stopping rule in the retained extracts:** this is a bounded observation,
   with an appropriate warning that absence in a truncated selection proves no
   universal rule. Introductory entitlement passages do not alone establish that
   all care-home entitlement gates are unchanged.
2. **Severe-disability additional amount:** the complete DMG 78088 record supports
   the narrowly conditional no-partner/self-funder proposition. Its heading and
   a quote from 78087 are insufficient on their own to establish that proposition;
   the operative 78088 sentence should accompany any demonstration citation.
   The full retained record includes the four-week note, example and continuing
   conditions, which remain available for review.
3. **Household treatment:** the complete 78089 and 77128 records support the
   stated household distinction and the separate factual question where both
   partners enter care. One quote stops midway through its sentence. Inspect the
   whole record before relying on the conclusion.
4. **Housing-cost additional amount:** the complete 78270 record supports the
   component-level exclusion and temporary-absence qualification described.
   The quoted fragments stop before the full exception wording. They should not
   be displayed alone as complete evidence of the claim.

The answer additionally says that the staff-012/staff-013 and foundation profiles
are missing. **They are present in the reading view; their requirements are
unmet.** This is a model misreading of governance metadata. It also attributes
truncation to a node budget without establishing that as the limiting cause:
the package retained 25 of 64 nodes and reported byte/resource/candidate limits.
These faults remain in the original answer and must be explained in the demo.

## What to demonstrate and what to improve later

Show the question, selected complete passage, original model claim and review
side by side. The defensible benefit is that a reviewer can find and challenge
the claim against a fixed source. Do not claim that a bundle guarantees a correct
answer, that all 40 questions are answered, or that this trial proves savings.

After the freeze, prioritise a tested model-facing view which distinguishes
**present profile**, **selected passage**, **unmet dependency** and **unreviewed
applicability** without repeating large identifier lists. Preserve the complete
audit separately. Require useful quotations including operative conditions, and
retain independent claim review. Test such changes with a new pre-declared budget;
do not spend additional answer calls in this four-call run.

The new browser corpus and native in-app WebMCP were also observed delivering the
same care-home source text: a two-page catalogue and one complete source read
matched the UI's context and frozen literal hash. See the
[browser/tool receipt](../validation/demo-1-freeze/browser-webmcp-2026-09-23.json).
This does not prove that a separate ChatGPT Voice or Data Agent session has the
same tools available.

## Offline reproduction

```sh
.venv/bin/python scripts/demo_one_pair.py check
.venv/bin/python scripts/check_demo_one_pair.py --check
.venv/bin/python -m unittest discover -s scripts -p test_demo_one_pair.py
```

These commands make no model or network calls. The raw response streams are
model-generated research outputs, not instructions or official guidance.
