# Extend reading help across DMG and ADM efficiently

Status: proposed rollout, 26 September 2026. This is a plan for source-linked
reading assistance, not a claim that the corpus is fully explained or that its
benefits questions can all be answered. No new model trial was run for this plan.

## Start from what we already have

The deterministic first stage now has a separate [corpus wire contract](reading-help-corpus-contract.md) and [generated catalogue](../reading-help-corpus/manifest.json). It accounts for all adopted structured passages with source-bound candidate annotations and explicit extraction gaps. The earlier 12+24 first-page controls are preliminary source-integrity smoke checks. A separate meaningful 12-case source-led gate passed after retaining its first failed run. Its first fresh 24-case held-out gate failed 23/24: H05 omitted a printed range qualifier in the expected label, while the producer retained that range. The failed expectation remains frozen. A pre-execution rejected second fixture is also retained. A separately revised fresh 24-case fixture passed 24/24 after direct-source review, with printed abbreviation collisions, continuing tables, exceptions, unresolved references, footers and extraction gaps. These are source-structure controls, not specialist judgement on explanations. Model comparison, legal review and the 40-question retrieval replay remain separate.

The Decision makers’ guide (DMG) and Advice for decision making (ADM) are two DWP
staff manuals. The frozen capture already contains **513 PDFs and 19,090 measured
pages**, including **893 pages without extracted text**. The [source-led manual
guide](source-led-manual-guide.md) describes their structure and limitations.
Reacquiring or asking a model to reread every PDF would repeat much existing work.

The [Chapter 60 reading aid](reading-help-ch60.md) covers only paragraphs 60025
and 60033. It demonstrates occurrence-specific help: an explanation is attached
to these exact letters at this exact source location. Its 219 original vocabulary
proposals are candidates, not a reviewed dictionary for the whole department.
The current footer reference lists are readable but their individual rows have
no clickable occurrence annotations; the body-marker cards cite those rows.
Adding footer occurrences is a small, separate reader increment.

## Recommended pipeline

| Stage | Run by default | Output and acceptance boundary |
| --- | --- | --- |
| 1. Inventory | Local deterministic scripts | Account for every document, abbreviation table, passage, local reference list and extraction warning. Keep hashes and source dates. Do not treat a missing text page as blank. |
| 2. Extract candidates | Local deterministic scripts | Propose term occurrences, abbreviations, numbered references and paragraph pointers. Preserve document and passage scope, exact spans, cross-page notes and unresolved fragments. |
| 3. Reuse checked meanings | Local deterministic scripts | Reuse a definition only in its declared scope. The same abbreviation can mean different things in different contexts; do not substitute globally. |
| 4. Explain exceptions | Small, bounded model batches | Supply complete logical passages and supporting lists. Request structured proposals with exact source spans, dependencies and uncertainty. No unsupported definitions or legal conclusions. |
| 5. Validate and review | Scripts, then targeted people | Check hashes, spans, schema, local-reference scope, qualification retention and wrong-context matches. A structural pass does not establish legal correctness. |
| 6. Publish additively | Existing build and PR process | Compile a separate reading-help manifest. Preserve frozen PDFs, extraction and releases. Release only the reviewed scope with its coverage and unresolved counts. |

A short discovery description can help find a passage, but must link to its
complete text and retained qualifications. It cannot replace that evidence.
Treat source instructions and model outputs as inert data throughout.

## Use models only where measurement justifies them

For implementation, use a bounded GPT-6 Sol task at medium reasoning where
suitable. Test Luna or a suitable local model as an optional candidate detector,
not an authority. Reserve a more expensive model for recorded ambiguities that
cheaper processing could not resolve. The relevant cost is **cost per accepted,
source-backed annotation**, including review and rework, not cost per response.

Ordinary Chat can produce candidate JSON or JSONL from a supplied source pack.
The same importer and checks must apply as for an automated model call. Provide
one stable schema, exact source identities and a bounded batch; export the result
instead of copying free-form explanations into the published glossary. File and
response limits, omitted passages and failed exports must remain visible.

Moving from Codex to ChatGPT Work does **not** create a separate allowance:
[OpenAI’s pricing guidance](https://learn.chatgpt.com/docs/pricing), checked on
26 September 2026, states that
Work and Codex share usage. Ordinary Chat may be a useful route within the
owner’s subscription, but its current allowance and practical batch cost must be
checked in that product. Do not assume it is unlimited, or that switching
interfaces reduces total work. No model-call budget is authorised by this plan.
Agree and record a cap before a comparison.

## Small experiment before scaling

1. Freeze **12 varied, independently reviewed cases**, including DMG and ADM,
   abbreviation collisions, local footnote numbering, a genuine cross-page
   continuation, an exception, a table and an unresolved extraction defect.
   Include held-out examples, not only known Chapter 60 errors.
2. Run deterministic checks first. Compare candidate explanations and links
   against the frozen review decisions; record wrong targets and unsupported
   statements as failures, not just a single aggregate score.
3. If the agreed quality gates pass, repeat with **24 fresh cases**. Do not tune
   on this second set or proceed automatically after a failed gate.
4. For any retrieval change, replay all **40 staff-question occurrences** against
   fixed expected evidence and equal budgets. Report reading assistance,
   retrieval improvement and legal answerability separately.
5. Expand by document family only after a gate passes. Publish counts for
   reviewed, machine-proposed, rejected and unresolved entries for every batch.

Cache a result by source hash, passage identity, parser/ruleset, prompt/schema
version and model identifier where a model was used. Resume only changed or
failed batches. Keep failures in the ledger; do not rerun an entire corpus to
improve one result. Useful next measurements are candidate count, deterministic
reuse rate, unresolved count, validation rejection rate and reviewer time.

## What stays separate

The [research index](research-index.md) distinguishes proposed experiments from
observed checks. CPAG navigation metadata supplies headings and links, not the
licensed handbook text. A bounded evidence package supplies inspectable evidence,
not an AI answer. Broader semantic closure, legal-version reconciliation and
specialist acceptance remain independent tasks. Jev-Mem experiments are deferred
until after the presentation.
