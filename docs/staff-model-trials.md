# Fixed-evidence staff question trials

These are observations of how two subscription clients use the **same public evidence**, not a benefits advice service or an accuracy league table. Independent human and domain review remain pending.

## Start with the question

The trial covers four supplied questions: Pension Credit savings, a permanent move into a care home, Child Disability Living Allowance (DLA) and Personal Independence Payment (PIP), and Carer’s Allowance. A fifth, deliberately unrecognised term checks whether each client abstains when the package contains no evidence. The exact original wording is retained in the [preregistered protocol](../evaluation/model-comparison/staff-2026-09-20/protocol.json) and [input catalogue](../evaluation/model-comparison/staff-2026-09-20/contexts.json).

*Preregistered* means the questions, evidence budget, instructions and checks were recorded before observing substantive answers. The protocol also records every amendment, including a change made after the first empty-evidence controls.

## Understand what the model receives

Ask OKF assembles records, relationships and provenance into a bounded JSON document. JSON is a machine-readable text format. The package includes its own missing-evidence and truncation warnings. *Truncation* means the budget stopped the system including every candidate; it does not mean the missing material is irrelevant.

The four substantive packages contain 47 to 52 selected records and 36 to 55 relationships. They remain **insufficient** because unresolved review obligations and evidence gaps are explicit. Each model receives the same exact package, authored instructions and answer schema. The whole-package limit is 262,144 bytes; there is no silent retrieval or model-knowledge fallback.

The shared Explorer consumer is pinned to commit `602622771e222db880a9d53b299db1d79d612409`. Its input is the exact [archived staff semantic index](../evaluation/model-comparison/staff-2026-09-20/input-snapshots/assembly-index.json) plus the unchanged frozen corpus. These are offline experimental packages, not a claim about what the public deployment currently serves.

## Why the budget controls matter

The initial 65,536-byte run lost all selected records because missing-evidence diagnostics were added after byte trimming. The generic consumer now budgets those diagnostics while trimming. Corrected 65,536-byte controls preserve 4, 6, 11 and 9 evidence records, but no relationship paths. The paired trial therefore retains the larger fixed budget so the models can inspect useful paths. The original failures, initial larger-budget observations and corrected smaller-budget controls all remain under [budget-controls](../evaluation/model-comparison/staff-2026-09-20/budget-controls/).

## Tools and model identity

Both clients use existing subscription defaults without model overrides or API keys. Retrieval, shell execution, browser, MCP and project customisation capabilities are disabled for the calls. MCP means Model Context Protocol, an interface through which an AI client can call tools; it is deliberately unavailable during these fixed-evidence trials.

Claude’s schema output mode emits an internal `StructuredOutput` formatting event. The original strict-policy control rejected that event and is retained. A documented amendment permits only this formatter, whose event name and argument hash are recorded. Every other observed tool event is rejected. A hash is a digest that detects changed bytes; it does not prove a claim is correct.

Codex’s retained events do not expose the actual model identity, so the reports say unknown. They do not infer Astra from the surrounding task. User skill paths are disabled with process-local configuration; no skill-shortening warning was observed in the first control. Provider wrappers and host instructions may still differ, so identical authored prompts do not prove identical full system context.

## Read the checks in the right order

1. The answer must preserve the package identifier and its evidence status.
2. Every cited record must exist in the selected package.
3. Every quotation must match source text exactly; its URL and locator must occur together in that record’s provenance.
4. An insufficient package cannot become a complete answer. Empty evidence requires abstention. Substantive truncated packages must mention truncation in the summary.
5. A separate model critique examines the meaning and qualifications of each claim. This is another fallible review, not a gold answer or specialist approval.
6. A benefits or legal specialist must still assess applicable dates, conditions, exceptions and legal interpretation.

The [results ledger](../validation/model-comparison/staff-2026-09-20/results.json) links every attempt, including failures and retries. Provider accounting is retained where available. It is not verified subscription cost, future pricing or evidence of affordability.

## What happened in this run

Twelve attempts are retained: ten structured responses, the original strict formatter rejection, and one 240-second timeout followed by a separately identified retry. The ten responses contain 49 claims and 79 citations. All preserve the insufficient status; both unknown-term responses contain no claims.

| Case | Claude literal and boundary checks | Codex literal and boundary checks |
| --- | --- | --- |
| Pension Credit savings | Pass: 8 claims, 14 citations | Pass: 3 claims, 4 citations |
| Permanent care home | Pass: 8 claims, 8 citations | Pass: 3 claims, 3 citations |
| Child DLA and PIP | Pass after retained timeout: 10 claims, 26 citations | Fail: two non-verbatim quotations; 5 claims, 7 citations |
| Carer’s Allowance | Pass: 9 claims, 13 citations | Fail: one non-verbatim quotation; 3 claims, 4 citations |
| Unknown term | Pass after retained formatter rejection: no claims | Pass: no claims |

These are **mechanical results**, not accuracy results. The [claim-level model critique](../validation/model-comparison/staff-2026-09-20/claim-level-model-critique.json) covers every retained claim and records substantive concerns:

- Both care-home answers omit the source heading restricting the severe-disability additional-amount passage to claimants who have no partner.
- The Codex DLA-continuation claim omits the source’s 8 April 2013 cohort restriction. Claude preserves it in the claim but broadens it in the summary.
- Many mechanically passing Claude citations are sentence fragments that omit operative conditions. The full cited page contains more support than the chosen quotation.
- Claude’s disability-transition answer says no Welsh territorial guidance is included, despite citing an England-and-Wales memo. A missing complete territorial answer is different from no territorial evidence.
- Three Codex quotations collapse line wrapping. That breaks the exact-quotation contract even where the wording remains recognisable; the original outputs remain unchanged.

A second model reviewer independently confirmed the early household, date-cohort and quotation-fragment findings. Later claims were reviewed by the task’s review agent. All of this remains fallible model review; **no specialist has accepted the answers**. There is no unsupported-claim rate, quality score, preferred-model recommendation or affordability finding.

Claude receipts expose `claude-opus-5` and `claude-haiku-4-5-20251001` in response/accounting events; this is not a controlled single-model comparison. Codex’s actual model identity is not exposed. No external tool event appears in the retained completed event projections. The timed-out attempt has no retained event census, so its events are unknown, not zero.

[Execution provenance](../validation/model-comparison/staff-2026-09-20/execution-provenance.json) explains a harness bookkeeping correction: adding offline reporting during a batch changed the on-disk file hash, while the running process retained its loaded functions. Both historical source snapshots remain and the invocation, isolation and assessment functions are byte-identical. Future attempts cache the loaded source digest once. No original receipt was rewritten.

## A short demonstration

1. Open the input catalogue and select the care-home package. Show its missing requirements and `insufficient` status.
2. Open each original answer and its receipt. Both pass the literal checks.
3. Open the source page through a claim’s provenance and read the heading above paragraph 78088.
4. Open the claim-level critique: the missing “no partner” qualification illustrates why a quote checker is necessary but insufficient.
5. Show the unknown-term pair, which supplies no claims, and the retained timeout and formatter rejection.
6. End at the review boundary: these are inspectable evidence-and-answer artefacts for specialists to check, not completed individual advice.

## Reproduce

Use the documented locked environment. Offline replay does not call a model:

```sh
uv run --locked python scripts/run_staff_model_trials.py --report --check-report
uv run --locked python -m unittest discover -s scripts -p test_staff_model_trials.py
node --experimental-strip-types scripts/export_staff_trial_contexts.mjs --check --explorer-root /path/to/okf-explorer-at-6026227
```

To run one intentional new subscription attempt, specify `--run`, the provider, the case and an unused attempt identifier. Omitting provider or case selects the registered batch; this makes real subscription calls. Existing receipts are verified and never overwritten. Do not rerun or refreeze evidence as if it were the same trial after changing a source, engine, prompt or schema.

## Historical replay and later source projections

A later publication projection omitted unused opaque effect identifiers from legal metadata after verifying their public official origin. This changes the current metadata hashes and semantic build, but does not alter the historical trial inputs. The replay command uses the archived trial index and verifies the original exporter digest. [The projection ledger](../source/legal-discovery-2026-09-20/publication-projection.json) relates previous and projected source hashes. A historical source hash must not be checked against today's mutable URL and reported as unchanged.
