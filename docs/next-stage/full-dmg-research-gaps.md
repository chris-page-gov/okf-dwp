# Full DMG research status and remaining gaps

Assessment: 15 September 2026. Content freeze: 24 September 2026. Seminar: 30 September 2026.

The frozen collection contains **331 source units**. The chapter batches account for 78 substantive units. The [source-family register](../../evaluation/full-dmg-source-family-review.json) gives terminal outcomes for the other **253 units**, covering 6,646 PDF pages, plus all 11 publication families and six cross-cutting tasks.

**Terminal means this bounded research attempt has finished and recorded its limitations.** It does not mean every paragraph has been interpreted, every workplan deliverable is complete, all law is current, or a specialist has accepted the domain. The register explicitly leaves those gates unsatisfied. It adds no semantic concepts or relations and makes no individual entitlement decision.

## What the remaining source types contain

| Frozen classification | Units | Research outcome |
| --- | ---: | --- |
| Memos | 66 | Acquired evidence and literal dependencies checked; applicability and incorporation unresolved. |
| Historical amendment records | 151 | Historical bytes retained; affected locations and dates remain source statements until reconciled. Some attachments contain inserted chapter pages; others are summaries. |
| Change summaries | 15 | Change statements retained; a summary date is not a provision's commencement date. |
| Abbreviations and legislation reference lists | 3 | Reference material, with selected ambiguity checks; no acquired statutory provisions or complete identity mapping. |
| Annexes | 4 | Selected role and scope review; complete structural and relationship modelling remains outstanding. |
| Transitional chapters | 3 | Selected historic scope reviewed; savings, exceptions and relevant legal versions remain to be reconciled. |
| Spare chapters | 11 | Each single page explicitly says the chapter is spare and intentionally blank; no invented definition or rule. |

“Non-substantive” is the workplan's accounting category. It does **not** imply that memos, annexes, transitional chapters or inserted amendment pages contain no substantive guidance.

## What was actually checked

The register recomputes 1,265 artefact hashes and verifies every existing candidate span for these 253 sources: **26,494 date/reference candidates**, **20,760 dependency spans** and **7,181 candidate target pointers**. It includes 253 opening-page provenance checks and 1,012 rejected record mutations covering fabricated text, changed source identity, unsupported specialist status and unsupported effective-date promotion.

Those tests check records and provenance. They do not test a model's reasoning or refusal behaviour. Twenty-two previously executed family navigation/no-result outputs were checked against frozen source evidence; this is not a new browser run. The input hashes identify the exact receipts assessed.

The register's start/end timestamps measure its mechanical accounting pass, not the earlier model reading and interpretation, whose duration was not recorded. Four changing progress/review/retrieval/coverage inputs are preserved as exact copies under [`evaluation/full-dmg-source-family-inputs`](../../evaluation/full-dmg-source-family-inputs), with their original paths and hashes retained. Later results do not replace those assessed bytes.

The assistant inspected bounded role/scope excerpts from 27 units, with 52 page references, and visually checked one problematic diagram. Other source bodies were not read in full for this accounting pass. All source interpretations remain unreviewed by specialists. The per-source rows enumerate quality flags, recognised citations, unresolved dependencies and requirement outcomes. A zero citation count is not evidence of no citations.

## Concrete source and interpretation gaps

| Priority | Evidence | Required next action |
| --- | --- | --- |
| High | Vol 1 Annex M, PDF page 43 | A rendered check confirms a multi-step appeal timeline. Extracted text retains only headings and the final sentence; the quality heuristic did not flag it. Produce a checked transcription with diagram relationships before relying on the example. |
| High | Memo 14/25, PDF pages 1–3 | The recogniser produced zero dependencies despite citations to **SSWP v VB [2024] UKUT 212 (AAC)**, **SSWP v HH [2015] UKUT 0583 (AAC)** and annotation targets 073492, 072842 and 072845. Append reviewed citation matches; test recall. The memo's SPC title and UC litigation context require scoped applicability review. |
| High | Vol 1 Annex F, PDF pages 25–26; Memo 13/25 reference | Reconcile the any-grounds/any-time MR distinction, the memo and procedural case law before operational use. A selected example is not a universal appeal deadline. |
| High | Memo 15/25 and Chapter 7 paragraphs 073496–073499 | Reconcile the source-stated section 45 change, decision-date boundary and Memo 26/20 paragraphs 39–40. Preserve the continuing HRT/right-to-reside conditions. Annotation is not proof of incorporation into every frozen chapter. |
| High | Chapter 80, PDF page 3 | Keep the 6 October 2003 IS-to-SPC transfer context and historical age 60 wording. Do not expose that age as today's Pension Credit qualifying age. Resolve the consequential regulations and AIP transition versions. |
| High | Chapters 39/40 and 64/72 | Resolve the WFP boundary discrepancy (15 September versus 16 September 2025) and Unemployability Supplement closure discrepancy (6 versus 8 April 1987) recorded in the [non-income/industrial review](../../evaluation/full-dmg-non-income-and-industrial-review.json). Do not silently select one date. |
| High | Chapter 6 source marking | Preserve the publicly acquired PDF and its “Official-DWP Use Only” footer. Ask the source owner about the marking and intended reuse. Do not infer an undisclosed status or silently redact the original. |
| Medium | Chapter 36, PDF page 5; Chapter 55, PDF page 3 | Keep the 1988/1996 Supp B–IS–JSA(IB) and 1995 sickness/invalidity–IB transitions distinct from UC or New Style ESA. Complete the savings, repeat-claim and dependency exceptions before modelling any executable rule. |
| Medium | Vol 2 Annexes 1–3 | Preserve pre-1989 frozen-rate scope and the Australia agreement's 28 February 2001 claim/entitlement conditions. Reconcile historical Orders, treaty articles, uprating and residence exceptions. Empty extracted pages are not proven blank. |
| Medium | Abbreviation lists | Preserve multiple expansions and contexts, including AA/quoted AA and BP. Wrapped title/abbreviation pairs need checking. The “Statutes” list also includes Orders, a Regulation and a treaty label; its title is not an instrument-type classifier. |
| Medium | Amendment 61 (Vol 1), Amendment 39 (Vol 14), Vol 14 changes | Compare source-stated incorporation and affected paragraphs against the correct chapter versions. The summary's 84365/16 July 2026 change and Memo 01/26 link need provision-level review; a contemporary listing does not establish legal currency. |

These examples are recorded as observations and unresolved dependencies, not new legal propositions. Original PDFs, hashes, extraction and classifications remain unchanged.

## Cross-cutting completion and acceptance

| Workstream | Available foundation | Still needed |
| --- | --- | --- |
| Benefit, territory and time | Scoped concepts, chapter packets and a bounded transition matrix in the register | Complete applicability matrix; paragraph-specific DMG/ADM routing; dated exceptions and contradictions resolved by specialists. |
| Legislation and case law | Exact-span candidate navigation and [pinned legislation assessment](legislation-integration.md) | Acquire relevant provisions/judgments and their versions; reconcile effects, commencement and territorial scope. A catalogue entry, footnote or single location match is insufficient. |
| Staff evidence and operations | [De-identified staff needs and projected journeys](stakeholder-needs-and-evaluation.md) | Named policy, operational and fraud/error owners; agreed evidence collection and assisted-journey requirements. The earlier referenced staff plan was not supplied. |
| Adviser and calculator comparison | CPAG contents/navigation metadata; source and tool links | Appropriate publisher permission/access for substantive processing, plus recorded synthetic calculator runs. No handbook-body interpretation or calculator accuracy comparison has been established. |
| Graph and consumer quality | Source hashes, exact evidence, independent research review, indexed retrieval and [recorded public browser journeys](../../validation/full-dmg-browser.json) | Comprehensive accessibility, responsive/cross-browser DWP journeys and comparative load/search/graph measurements remain separate. Preserve the targeted-resource-hydration limitation. Explorer term expansion differs from the Python exact-match evaluator: inspect the displayed matched term. |
| Model evaluation and affordability | [160 observed source trials and recorded assessments](../../evaluation/full-dmg-behavioural/summary.json), plus the [comparison design](../../evaluation/model-comparison/README.md) | Address the recorded partial and underspecified cases; freeze comparative runs with model/effort, retries, usage, elapsed time and reviewer cost. These context-aware trials are not a calibrated model comparison. |

Initial ADM context remains bounded to A1, A2, E1, E4, H1, H2 and M6. B1, M5 and other specifically recorded dependencies require separate scope decisions or follow-up; the full ADM is not silently included. Universal Credit guidance provides context, not equivalence with legacy DMG regimes.

## Before the freeze and seminar

The trial summary is later evidence than the source-family accounting pass: it records 90 supported, 56 partial and 14 rubric-underspecified assessor outcomes. Its replay verifies retained hashes and citations, without regenerating answers or grading them in code. These counts are not an accuracy score or specialist acceptance.

For **24 September**, bind the public research candidate to tested immutable bytes, retain the gap register, resolve the agreed partial-answer and rubric gaps, and obtain named specialist review for any interpretation presented as accepted. The source-complete research bundle can be useful while those acceptance gates remain visibly open. A benefits engine and operational application/change service need their own validated requirements and rules.

For **30 September**, rehearse the actual [evidence website, ChatGPT live voice and room audio path](seminar-webmcp-and-audio.md): callable page tools, microphone/input, Mac output to the PA and projected evidence. A subscription or voice output does not prove WebMCP access. Retain deterministic source navigation as the demonstrated fallback. This register adds no website, deployment, voice compatibility or room acceptance claim.

Later remediation should append a new linked attempt with source and assertion hashes, observed results and reviewer decisions. Do not overwrite the frozen evidence or change these outcomes to specialist accepted without an explicit acceptance receipt.
