# Monday handover: inspect the evidence and name the gaps

**For the meeting on Monday 21 September 2026. Independent experimental publication; not official DWP guidance or individual benefits advice.** Use the public sample questions without claimant details.

The useful demonstration is now a reviewable path from a staff question to source text, its qualifications and the remaining gaps. Capturing documents and finding related passages are substantial progress. Neither establishes a complete benefits answer.

## Start with the learning website

Open the [learning website](https://chris-page-gov.github.io/okf-dwp/) and follow [Learn OKF-DWP by using it](https://chris-page-gov.github.io/okf-dwp/docs/learning-path.html). Keep the [glossary](https://chris-page-gov.github.io/okf-dwp/docs/glossary.html) available for unfamiliar terms.

**DWP** is the Department for Work and Pensions. Its **Decision makers’ guide (DMG)** and **Advice for decision making (ADM)** are separate staff guidance collections. The captured collections contain 513 PDFs and 19,090 pages. A **bundle** brings source records, named concepts and relationships together so people and software can inspect them.

The website was checked against exact source commit `91b9907836c8a340d974dd958969f4f8cbb3a0c6` on 21 September at 01:53 BST. Its manifest and all 122 listed output files matched: 123 successful HTTPS responses. All 2,382 internal links resolved, including section anchors. This is a dated publication check. The [latest receipt](../validation/learning-site/public-91b9907836c8a340d974dd958969f4f8cbb3a0c6/README.md) records the check's limits; the [earlier observation](../validation/learning-site/public-7815b17bb3db3903738c745d3fb9508919ebab15/README.md) remains unchanged.

### Later candidate checks

A separate public Chrome check at **01:55 BST** passed six journeys against disability source `df352daa…`. Its care-home context retained 61 records and 124 relationships in 520,494 bytes; the package remained insufficient and truncated. The [source-bound receipt and screenshots](../validation/household-reader-public/df352daa-c4f2de0a/README.md) distinguish this public candidate from the earlier qualification demonstration below.

The subsequent partner increment has 903 authored records, 1,482 assertions and 39 declared support dependencies. Its [frozen comparison](../validation/partner-context/2026-09-21/README.md) retains 585/585 declared path occurrences at 512 KiB and 449/585 at 256 KiB. These are offline source/assembler checks, not fresh public-service or AI-answer observations. Publication and remote replay are tracked separately; the live MCP service remains version 0.5.0 until its successor is deployed and checked.

## Which version are we demonstrating?

An **immutable commit** identifies an exact saved repository version. A **receipt** records what a check actually observed, including versions, outcomes and failures.

| Surface | Verified position at this handover | Where to inspect it |
| --- | --- | --- |
| Required qualification evidence | [DWP PR 17](https://github.com/chris-page-gov/okf-dwp/pull/17) merged as `91b9907836c8a340d974dd958969f4f8cbb3a0c6`. Its immutable source is `7f9feb9634e3d94004853b838462aca132c505a5`. Earlier trials retain source `3ef0e786…`; the larger disability increment is a separate candidate. | [Qualification comparison](../validation/qualification-context/2026-09-21/README.md), [disability candidate](disability-addition-qualification-review.md) |
| Household Reader and Ask OKF | A fresh public Chrome journey passed on 21 September at 01:23 BST against source `7f9feb96…` and application manifest `9fc8cb1b…`, checking 270 immutable corpus files without console or network errors. | [Current public receipt and screenshots](../validation/household-reader-public/7f9feb96-c4f2de0a/README.md), [earlier local cross-browser checks](household-reader-verification.md) |
| Public compact evidence service | **0.5.0 is deployed and verified**, using source `3ef0e786e9a18e76fa17c7d925ff509d6d6c9f84`. Seven full-package and four compact SDK cases passed. The care-home evidence journey passed in all three browsers; strict console checks passed in Chrome and WebKit, with two Firefox hosting-cookie warnings retained. | [Service home](https://ask-okf.crpage.chatgpt.site/), [0.5.0 deployment, SDK and browser evidence](../validation/compact-delivery/v0.5.0/README.md) |
| Household model trials | The first experiment retains five unsuccessful attempts. A separate successor retains nine attempts: seven parser-accepted responses, including both empty-evidence controls; six pass mechanical citation checks. All five substantive responses are Codex outputs; one has a defective locator, and model review identifies scope concerns. No successful substantive provider pair or specialist acceptance is established. | [Trial guide](monday-model-trials.md), [successor outcomes and critique](../validation/model-comparison/household-compact-v2/README.md) |

The public 0.5.0 observation finished on 20 September at 23:42 BST. It made 90 browser tool requests without retries and retained exact catalogue, provenance and full-package comparisons. A clean three-browser console gate has **not** passed because of Firefox's warnings. The separate historical four-journey browser suite was **not run** for 0.5.0. These results remain distinct from the broader local household Reader checks and the earlier [0.4.0 observations](../validation/compact-delivery/v0.4.0/README.md).

The [SDK receipt](../validation/compact-delivery/v0.5.0/sdk-receipt.json), [hosting receipt](../validation/compact-delivery/v0.5.0/deployment.json) and [browser summary](../validation/compact-delivery/v0.5.0/browser/staff/run-summary.json) identify the checked runtime and source. Before the meeting, compare the live release with these records. Successful evidence delivery does not establish legal completeness or AI answer quality.

## What the household increment adds

The next authored source candidate has **51 concepts**, **98 selected source pages** and **20 selected statutory units**. The published qualification source has 96 selected source pages; all source versions retain their own counts. A **concept** names a meaning, such as a couple or a benefit component. A **statutory unit** is a selected section, regulation or schedule paragraph; the count does not mean 20 complete Acts. The source manuals remain much larger than these deliberately modelled selections.

The [current development check](../evaluation/semantic-expansion/evaluation.json) retrieves **177 of 177 expected candidate occurrences** across **40 supplied question occurrences, representing 39 unique questions**, using the separate qualification source and revised engine. These are candidate passages chosen for investigation, not 177 correct answers. All 40 question packages still report **insufficient**; there are no AI answers or independent specialist approvals in this retrieval evaluation. The earlier public source and engine retrieved 176 occurrences; their [retained result](https://github.com/chris-page-gov/okf-dwp/blob/3ef0e786e9a18e76fa17c7d925ff509d6d6c9f84/evaluation/semantic-expansion/evaluation.json) remains unchanged.

### Qualification release: measured separately from the service

The new source declares 15 support dependencies, including whole passages that
qualify household, housing-cost and temporary-residence summaries. A dependency
says which material must accompany an interpretation; it does not make that
interpretation official. The [joint comparison](../validation/qualification-context/2026-09-21/README.md)
freezes source `7f9feb9634e3d94004853b838462aca132c505a5` and Explorer
`c4f2de0a99b7bc2f8b8c8a06a3c715fb56b66d8e` independently of the public 0.5.0
demonstration above. Explorer PR 131 has merged and passed its canonical and Pages checks. A fresh public Chrome observation verifies the qualification source on that application; the MCP service upgrade remains separate.

At both 256 KiB and 512 KiB, the pair retains all 433 declared path occurrences.
Both care-home questions retain all seven household-support pages through their
declared paths. At 256 KiB each package has 27 records and 63 relationships.
The 512 KiB result also includes an optional temporary-care summary whose page
78/24 support is missing, and reports that gap. The earlier 64 KiB envelope
cannot hold the expanded care-home requirement metadata: it returns an explicit
`metadata_budget` refusal. That is a useful limit to demonstrate, not an answer.

All 203 obligations remain open. None of these new observations repairs an
earlier model response or establishes specialist acceptance. Use the
[component review](carehome-component-dependency-review.md) to inspect the exact
wording corrections. The separate [disability increment](disability-addition-qualification-review.md) now declares 29 dependencies in a 903-record index. Its 40-case replay retains all 177 candidate occurrences at 512 KiB; at 256 KiB the richer care-home support does not all fit, and the package explicitly names missing evidence. Source review, 46 semantic controls and 20 combined Reader controls pass. Publication and new compact delivery of that larger source remain pending.

There are **203 open obligations**: 43 evidence-closure requirements and 40 each for applicability, legal version, independent review and question scope. An **open obligation** names something that has not been established. It prevents the system from turning a promising source trail into a false claim of completeness. The [profiles](../evaluation/semantic-expansion/profiles.json) retain these requirements; the [legal-body guide](legal-body-evidence.md) records the statutory extraction and its remaining limits, including 12 units with unknown extent.

## Ten-minute demonstration

### 0–2 minutes: explain the three jobs

Open the learning website, then [the fixed qualification source in Explorer](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F7f9feb9634e3d94004853b838462aca132c505a5%2Fcombined%2Fokf-explorer.json#overview). This link fixes the bundle version; it does not freeze the deployed Explorer application. The [public journey and screenshots](../validation/household-reader-public/7f9feb96-c4f2de0a/README.md) bind the application actually checked. If a later preflight differs, use the labelled retained observation and state that limitation.

- **Search** finds possible records, using repeatable matching.
- **Ask OKF** assembles a limited evidence package and explains why records were included.
- An **AI answer** is a separate interpretation of that package. Explorer does not generate an answer merely by building the package.

### 2–4 minutes: read the care-home qualification

Paste the original staff wording into Ask OKF, including its recorded typo:

> Does Pension Credit stop is a citizen moves into a care home permanently if they are self-funding?

Select **Build evidence package**, inspect its insufficient status and open the source passage containing DMG 78088. Read the preceding heading: **“Claimants who have no partner (including self- funders)”** in the retained extraction. This limits the branch being discussed. Self-funding alone does not justify applying that paragraph to every household or every component of Pension Credit.

The checked public package contains 62 records and 124 relationships, with truncation. **Truncation** means the limits caused some material to be omitted. Some housing-cost statutory units are omitted here, so this is a demonstration of a preserved qualification and a visible gap, not a complete answer. The [retained package](../validation/household-reader-public/7f9feb96-c4f2de0a/attempt-01-chrome/care-home-context.json) lets a reviewer inspect the same result afterwards.

### 4–6 minutes: keep an ambiguous abbreviation unresolved

Ask:

> What was the SDA amount over the last five years?

Show the two labelled alternatives: **Severe Disablement Allowance** and a **severe-disability additional amount**. The latter is a component of an award, not the same benefit. Ask OKF displays both possible evidence branches without choosing the intended meaning. The [retained package](../validation/household-reader-public/7f9feb96-c4f2de0a/attempt-01-chrome/sda-context.json) remains insufficient and truncated; it does not claim a complete five-year rate history.

### 6–8 minutes: follow the source and its relationships

Use the **Legislation** filter. It keeps the same 20-record scope in Reader, Graph and Timeline. Open regulation 5 of the State Pension Credit Regulations 2002 and inspect its official dated HTML link. **Provenance** records where the text came from and which version was acquired; it is separate from the reason Ask OKF selected it.

In Graph, inspect the incoming guidance references and outgoing reference to the Universal Credit Regulations 2013 couple definition. A relationship is a route for investigation, not proof of legal applicability. In Timeline, compare source and audit dates: the requested statutory version, 20 September 2026, is not a publication or commencement event. See the [statutory graph screenshot](../validation/household-reader-public/7f9feb96-c4f2de0a/attempt-01-chrome/statutory-graph.png).

<a id="compact-evidence-demo"></a>

### 8–10 minutes: inspect a small evidence delivery

Open the [verified 0.5.0 care-home replay](https://ask-okf.crpage.chatgpt.site/review/#eyJidW5kbGUiOiJva2YtZHdwIiwidmVyc2lvbiI6IjNlZjBlNzg2ZTlhMThlNzZmYTE3YzdkOTI1ZmY1MDlkNmQ2YzlmODQiLCJxdWVzdGlvbiI6IkRvZXMgUGVuc2lvbiBDcmVkaXQgc3RvcCBpcyBhIGNpdGl6ZW4gbW92ZXMgaW50byBhIGNhcmUgaG9tZSBwZXJtYW5lbnRseSBpZiB0aGV5IGFyZSBzZWxmLWZ1bmRpbmc_IiwiYnVkZ2V0Ijp7Im1heF9ub2RlcyI6NjQsIm1heF9yZWxhdGlvbnNoaXBzIjoxMjgsIm1heF9kZXB0aCI6NiwibWF4X2J5dGVzIjoyNjIxNDR9LCJjb250ZXh0X2lkIjoidXJuOnNoYTI1Njo2Y2RjM2RkMTU0ZDRmMTFlMWZiOGI5ZGQxYjk5YzQyZGE1OTg1NmJhNzg1N2RlNWEzZmUwNGQ2ZjNhYjg2MDc4In0), then select **Recreate evidence**. The link is inert until invoked. It fixes the question, source version, budget and expected context identifier recorded in the SDK receipt.

Show the 35 selected records, 50 relationships and **insufficient** status. Open **Read exact text** for Chapter 78, PDF page 25: the no-partner heading, paragraph 78088 and its legal footnote are visible. Then inspect provenance, gaps and the full machine package. All three browsers reconstructed the same package in the [actual public check](../validation/compact-delivery/v0.5.0/README.md); two passed strict console checks. This is a smaller package than the earlier local Reader demonstration, so its record count is different.

A **manifest** is a small catalogue of the package. It lets a person or AI request selected text and metadata in bounded parts instead of receiving the whole package at once. The service exposes the read-only tools `ask_okf`, `ask_okf_manifest` and `read_okf_evidence`. **MCP**, the Model Context Protocol, is the interface an already connected AI client can use to call them; a website alone does not establish that a particular client is connected.

Show the question, source version, budget and **context ID**, the fingerprint identifying the assembled package. The same replay inputs allow the reader to recreate it. Browser Ask OKF uses a 524,288-byte default; the compact trial packages use 262,144 bytes. Different budgets can produce different packages, so compare their identities before saying they contain exactly the same evidence. The review link recreates evidence; it does not preserve an AI conversation.

## Staff review: the next useful contribution

| Review action | What to record | Backlog work package |
| --- | --- | --- |
| Clarify the intended question, especially SDA and “all scenarios”. | Intended benefit, component, date, jurisdiction and relevant hypothetical circumstances, without claimant details. | [DWP-BL-001](backlog-work-packages.md#dwp-bl-001-extensive-persona-journey-and-question-review) and [DWP-BL-007.acceptance](backlog-work-packages.md#dwp-bl-007-broader-semantic-modelling-task-specific-evidence-profiles) |
| Review the care-home and mixed-age concepts. | Missing qualifications, misleading aliases or source-backed relationships that need correction. | [DWP-BL-005.acceptance](backlog-work-packages.md#dwp-bl-005-broader-semantic-modelling-neutral-domain-concepts-and-relationships) |
| Check the statutory trail and source completeness. | Exact missing provision or case, applicable version, commencement, extent and unresolved contradiction. | [DWP-BL-006.acceptance](backlog-work-packages.md#dwp-bl-006-legislation-regulations-and-case-law-reconciliation) and [DWP-BL-007.evidence-closure](backlog-work-packages.md#dwp-bl-007-broader-semantic-modelling-task-specific-evidence-profiles) |
| Review any later accepted model claim against the whole condition. | Claim, exact source, heading, exception and whether the conclusion is supported. | [DWP-BL-010.acceptance](backlog-work-packages.md#dwp-bl-010-fixed-evidence-claim-level-model-trials) |
| Try the actual reading task using assistive technology. | Browser, task, barrier and expected behaviour. Local keyboard and automated checks are not human accessibility acceptance. | [DWP-BL-019](backlog-work-packages.md#dwp-bl-019-broader-accessibility-and-cross-browser-review) |

Use the [staff review packs](../evaluation/staff-review/README.md) and [question-to-journey matrix](../evaluation/staff-needs/README.md) to attach feedback to a named question. The [work-package backlog](backlog-work-packages.md) separates delivered implementation from outstanding evidence and human acceptance; broader semantic modelling remains open there.

The first five household model attempts establish execution and event-format problems, not a ranking of models or proof that their benefits answers were wrong. Two attempts timed out and three were rejected by the frozen event checks. Their original evidence, controls and failures remain intact. Each successor needs its own reviewed, frozen protocol and claim-level review; diagnostics, correct quotations and a smaller representation are not by themselves evidence of correct legal answers.

For a future departmental bundle, retain the same sequence: [discover terminology, sources, legislation and ontologies before modelling](methodology.md), then author evidence-backed relationships, define review questions and publish measured limitations. The [HMRC discovery brief template](templates/hmrc-discovery-brief.md) preserves that method; it does not claim HMRC discovery has already been completed.

## Voice and room-audio fallback

Use the [five-minute Voice rehearsal sheet](voice-rehearsal.md) to check actual
tool access separately from speech and the room equipment. If any part fails,
use the verified public evidence reader, or its labelled retained screenshots.
No unattended run has enabled microphone access, changed audio routes or proved
Voice invocation. This is a prepared fallback, not completed room acceptance.
