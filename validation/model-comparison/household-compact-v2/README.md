# Successor trial: nine retained attempts

This separate experiment binds [reviewed commit and frozen inputs](../../../evaluation/model-comparison/household-compact-v2-candidate/frozen-manifest.json). Its complete lossless decoding is described in the [candidate guide](../../../evaluation/model-comparison/household-compact-v2-candidate/README.md). The [original five failures/rejections](../household-2026-09-21/results.json) remain unchanged.

The [verified results ledger](results.json) contains **nine attempts: seven parser-accepted responses, one rejected formatter sequence and one timeout**. Six responses pass mechanical checks; Staff 008 fails a source-locator check. Five substantive answers remain partial and their packages remain insufficient. No substantive pair is complete. Earlier [two-control](history/control-only/results.json) and [four-attempt](history/first-substantive-pair/results.json) ledgers are preserved unchanged.

The [claim-level model critique](claim-level-model-critique.json) reviews all 14 substantive claims and 21 citations, plus both abstention controls. It binds exact answer and context hashes. It is fallible model review with human and specialist acceptance pending; it does not repair any original answer.

## Unknown-term controls

| Provider | Elapsed time | Event recognition | Mechanical checks | Answer behaviour |
| --- | ---: | --- | --- | --- |
| Codex subscription | 10.602 seconds | Passed | Passed | Cannot establish; zero claims or citations |
| Claude subscription | 37.208 seconds | Passed | Passed | Cannot establish; zero claims or citations |

Both preserve `insufficient` and avoid inventing a meaning for the unknown token. Codex does not expose a response-model identity in its retained events; it remains unknown. Claude reports `claude-opus-5`. These are default-subscription observations, not a controlled model comparison or an accuracy ranking. The control packet has no evidence and does not establish performance on the substantial staff questions.

Each provider received identical authored public inputs. The Codex skill-catalogue warning remains explicitly recorded, so identical whole provider system contexts are not claimed. Claude telemetry and formatter-result matching passed the separately reviewed strict checks. No raw reasoning, credentials or account/session identifiers are retained.

## Staff 012: permanent care-home residence and self-funding

The two authorised attempts used the same frozen evidence, decoding instructions and four-minute bound:

| Provider | Elapsed time | Event recognition | Mechanical checks |
| --- | ---: | --- | --- |
| Codex subscription | 30.887 seconds | Passed | 3 claims and 3 citations passed |
| Claude subscription | 221.524 seconds | **Rejected** | Not assessed as an accepted answer |

The [Codex answer](codex-subscription/staff-012/attempt-01/answer.json) expressly retains the no-partner heading and all-conditions qualification. It distinguishes the severe-disability and housing-cost additional amounts from the whole Pension Credit award. It preserves insufficient status, truncation, unresolved partner branches and temporal/territorial applicability, and abstains from an automatic stop/continue or individual entitlement decision. Mechanical quotation checks do not establish legal completeness; independent claim review remains separate.

The [Claude receipt](claude-subscription/staff-012/attempt-01/receipt.json) records two `StructuredOutput` inputs but only one valid single matched non-error result. It reports `formatter-result-missing` and `unmatched-duplicate-or-error-tool-result`. The sanitised record cannot distinguish which alternative caused the rejected result, and no cause is inferred. The final structured output retained in `model-output.json` is **unaccepted**, not a completed answer or pair. No retry or parser change has been made.

The model critique flags a separate concern in Codex claim 2: its household statement does not clearly distinguish one partner entering a care home from both partners entering. The project-authored concept in the package warns about that distinction, but the authoritative DMG 77128–77130 continuation is omitted. Later gaps acknowledge the missing branches. This is a source-reconciliation concern, not an established legal falsehood; exact quotation success does not resolve it. A second task agent independently identified the concern.

Claude completed within the bound on this observation, but this does not establish that the modest byte reduction caused it: prompt and event recognition also changed, provider context is uncontrolled, and the result was rejected.

## Remaining authorised batch and stopping decision

| Provider and case | Elapsed time | Event recognition | Mechanical checks |
| --- | ---: | --- | --- |
| Codex Staff 020 | 36.038 seconds | Passed | 3 claims, 3 citations passed |
| Claude Staff 020 | 240.419 seconds | **Timeout** | Not assessed as an accepted answer |
| Codex Staff 005 | 40.495 seconds | Passed | 3 claims, 5 citations passed |
| Codex Staff 026 | 43.874 seconds | Passed | 4 claims, 6 citations passed |
| Codex Staff 008 | 32.330 seconds | Passed | **1 claim, 4 citations; source-locator failure** |

The conditional execution gate authorised Claude Staff 020 first and required holding its remaining cases after another timeout or formatter rejection. Its timeout therefore leaves **Claude Staff 005, 026 and 008 uncalled**. Codex completed its four separately authorised attempts. No attempt was retried and no frozen parser, prompt or evidence was changed. No further provider calls are authorised by this note.

### What source review adds

- **Staff 020:** the mixed-age claim quotes the ordinary dated continuity rule but does not reconcile a selected memo's conditional migration/restoration provision. Present-but-unreconciled evidence differs from genuinely omitted evidence.
- **Staff 005:** the statement that National Insurance provisions can be satisfied “through their partner” is not established by its quotation. The source's claimant/partner subjects need to be preserved.
- **Staff 026:** the detailed claim preserves the 8 April 2013 DLA cohort, but the summary broadens this to existing DLA claimants generally. The summary is not a safe substitute for its qualified claim.
- **Staff 008:** ambiguity between Severe Disablement Allowance and the Pension Credit additional amount remains explicit. The 2024 citation has an invalid locator, and the 2025 figures lack a claim-level citation despite being present on selected page 67. Neither defect has been silently repaired.

These are review observations about a bounded experiment, not a provider ranking, accuracy score, legal decision or complete answer to the staff questions. Requested statutory versions, source capture dates and current applicability remain distinct.

## Offline verification

```sh
uv run --locked python scripts/project_monday_model_contexts.py
uv run --locked python scripts/run_monday_compact_trials.py
uv run --locked python scripts/run_monday_compact_trials.py --check-report
```

These commands make no model call. The retained failed and rejected attempts are part of the result, not removed outliers.
