# Proposed evaluation protocol

Status: model-derived, unreviewed proposal. One diagnostic context has been observed; the comparative experiments below have not run.

## Questions the study should answer
Does OKF improve discovery of the controlling evidence? Does retaining dependencies improve a model's interpretation? Can different interfaces deliver and expose the same bounded evidence reliably? Does the resulting workflow improve a human decision-maker's correctness and effort? These are separate outcomes.

Build on Explorer's existing A-H evaluation: source, semantic representation, retrieval, traversal, assembly, provenance, boundaries and answerability. Add a separate answer-quality assessment and a separate human/client usability assessment. Do not replace all stages with one average. [REPO-EVAL]

## Three experiments

### 1. Fixed-evidence interpretation
Give each selected model the same independently reviewed source package, the same question and the same instructions. Disable outside retrieval for this condition where the host supports that control. Record any inability to disable it. Compare legal reasoning, supported claims, relevant qualifications, handling of missing facts and citations. A package delivered through several renderings must preserve the same evidence, roles, version and gaps; record each rendering's digest. This isolates interpretation, not search quality.

### 2. End-to-end evidence discovery
Compare these source-access conditions:

| Condition | Permitted material | What is measured |
|---|---|---|
| Human/manual | Official ADM/DMG and legislation | Source-finding, interpretation, time and confidence |
| AI/official web | Official sources only; OKF sites excluded | Search and interpretation without OKF |
| AI/raw corpus | Same frozen source documents as OKF | Corpus access without authored graph context |
| Flat retrieval baseline | Same corpus and comparable evidence budget | Retrieval without required dependency traversal |
| OKF assembly | Same source snapshot, declared graph/profile/engine | Selection, dependencies, omissions and subsequent answer |
| Guided rescue | Additional declared search or legal hints | Assistance required to recover a failed natural question |

Do not label the guided rescue as the same experiment as the original unaltered question. Do not put the answer key, mandatory passage list or new benchmark-specific semantic routes into a supposedly blinded retrieval condition. Measure any proposed bundle improvement against the retained baseline and an independently authored holdout, not only the case it was designed to fix.

Use the identical model/product/version across access conditions wherever possible. Compare models separately using fixed evidence. A subscription product may select a model dynamically; record the visible selection and any unobservable backend rather than inventing a precise model identity.

### 3. Transport and interface equivalence
Replay one canonical assembly using fixed source, engine, exact question and budget through the direct engine and remote MCP. Compare reconstructed package bytes and digests where that contract promises exact equality. Test WebMCP Reader assembly only if that exact operation exists and can actually be invoked. Treat the saved Workbench as a separate inspection task: it searches admitted questions or selected case evidence, not arbitrary whole-corpus discovery. [REPO-PAGE; REPO-MCP]

File/HTML/Markdown/Word renderings need semantic and provenance equivalence, not identical rendering bytes. A SharePoint index is another retrieval system: indexing delay, selected scope, chunking and permissions are independent conditions. Page session references and cursors must not be treated as permanent remote record identifiers.

## Reference-case gates
A correct answer under the stated GB/continuing-UC assumptions distinguishes the qualifying DLA date from the UC supersession date; uses the special relevant-benefit rule; selects the assessment period containing the qualifying event rather than notification; and refuses to invent the missing assessment-period boundaries. See the assessor file for the proposed key and authorities. [LAW-24; LAW-31; ADM-A4; ADM-F1]

A response that gives a correct date using unstated outside knowledge can pass an open-answer test but fail an evidence-only faithfulness test. Conversely, a bounded response that accurately says the controlling evidence is missing can pass a safety/faithfulness check while remaining unable to answer the substantive question.

## Execution controls
Freeze inputs, budgets, source versions, engine identities, prompts, evaluation criteria and client permissions before a comparative run. Run in fresh conversations with memory and retrieval settings recorded. Pre-register allowed reformulations, retries and stops; preserve every failed attempt. Use at least three repeats per selected cell for an exploratory study, with a larger design justified separately for inferential claims. Three repeats do not establish a stable population accuracy estimate.

Use the supplied 12 cases only for development and rehearsal. Obtain separately authored withheld cases. Include boundary dates, irrelevant rate/components, delayed notification that is and is not within the relevant-benefit exception, later UC commencement, absent award dates and deliberately incomplete evidence. Human trials should counterbalance order and use equivalent but different cases to reduce learning carry-over.

## Measurements
Record per-stage pass/fail/unknown, not merely answer plausibility. Report required-evidence recall against an independently defined set, preservation of qualifications, irrelevant-benefit retrieval, actual cited passages, and unresolved dependencies. Source relationships that are only navigation links must not silently acquire legal authority.

Measure time to first useful evidence and complete supported answer, tool calls, actual transferred bytes, model-input tokens if exposed, total assembled-package bytes, retries, user interventions and host clipping. Keep these quantities separate: a 522,218-byte package does not mean that many bytes reached a model. Source capture date, legal effective date, award-decision date, report date and run date are separate fields.

Critical legal errors remain individually visible: wrong assessment period, generic late-reporting cap applied to the special route, care/mobility confusion, invented AP boundaries, payment before UC entitlement, and unsupported citations. A correct answer must not hide a broken provenance or dependency gate.

## Minimal sequence
Preserve today's baseline; obtain an independently reviewed point-in-time reference pack; run fixed-evidence interpretation in each available product; then compare discovery routes with one fixed model; then test transport/UI parity. Improve only the failure stage supported by the results. Do not run a large all-models/all-routes matrix before basic comparability is established.

All bracketed references resolve in `sources.json`. No performance advantage, legal completeness or universal compatibility is established by this proposed protocol.
