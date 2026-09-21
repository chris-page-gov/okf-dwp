# Monday handover: inspect the evidence and name the gaps

**For the meeting on Monday 21 September 2026. Independent experimental publication; not official DWP guidance or individual benefits advice.** Use the public sample questions without claimant details.

The useful demonstration is now a reviewable path from a staff question to source text, its qualifications and the remaining gaps. Capturing documents and finding related passages are substantial progress. Neither establishes a complete benefits answer.

## Start with the learning website

Open the [learning website](https://chris-page-gov.github.io/okf-dwp/) and follow [Learn OKF-DWP by using it](https://chris-page-gov.github.io/okf-dwp/docs/learning-path.html). Keep the [glossary](https://chris-page-gov.github.io/okf-dwp/docs/glossary.html) available for unfamiliar terms.

**DWP** is the Department for Work and Pensions. Its **Decision makers’ guide (DMG)** and **Advice for decision making (ADM)** are separate staff guidance collections. The captured collections contain 513 PDFs and 19,090 pages. A **bundle** brings source records, named concepts and relationships together so people and software can inspect them.

The website was checked against exact source commit `91b9907836c8a340d974dd958969f4f8cbb3a0c6` on 21 September at 01:53 BST. Its manifest and all 122 listed output files matched: 123 successful HTTPS responses. All 2,382 internal links resolved, including section anchors. This is a dated publication check. The [receipt for that version](../validation/learning-site/public-91b9907836c8a340d974dd958969f4f8cbb3a0c6/README.md) records the check's limits; the [earlier observation](../validation/learning-site/public-7815b17bb3db3903738c745d3fb9508919ebab15/README.md) remains unchanged.

## Current delivery position: 21 September 2026

The [public service](https://ask-okf.crpage.chatgpt.site/) runs **0.6.0**, with the partner-qualified source `723bcc5b015ab38a026625c2148edbd784edf7c7` and explicitly versioned assemblers. Its [actual public SDK observation](../validation/compact-delivery/v0.6.0/README.md) passed 11 cases and 121 requests. The current care-home package contains 55 records and 115 relationships in 523,326 bytes. It remains **insufficient**. The unknown-term control is empty; the original historical package retains its exact earlier bytes.

Here, **SDK** means software development kit: the test client used to call the service and reconstruct its responses.

The first public verification failure is retained. It exposed a difference between SDK response envelopes; complete tool definitions were identical. A separately reviewed verifier correction passed the fresh observation. The deployed runtime and verifier have distinct recorded identities; the service was not redeployed to fix its verifier.

| Surface | Recorded position | Where to inspect it |
| --- | --- | --- |
| Public context service | 0.6.0 deployment succeeded; actual bounded SDK reconstruction passed. No fresh public browser or Voice acceptance is claimed. | [Service and exact receipts](../validation/compact-delivery/v0.6.0/README.md) |
| Retained evidence reader | Three approved examples contain current care-home, empty-control and original historical care-home packages. PR 21 is awaiting CI and public verification; do not yet describe the new website reader as publicly verified. Every complete package and small resource is hash-bound. | [Examples and boundaries](retained-evidence-examples.md), [beginner walkthrough](evidence-delivery-learning.md) |
| Public Explorer browser | Six Chrome journeys passed against disability source `df352daa…` at 01:55 BST. Its exact source and application identity are separate from the later MCP release. | [Browser receipt and screenshots](../validation/household-reader-public/df352daa-c4f2de0a/README.md) |
| Direct paired model trial | Both v4 empty controls and both Staff 012 answers were accepted by the mechanical checks, with zero observed tool calls. Agent claim review identifies omitted exceptions and an overstated gap in one answer; human acceptance remains pending. | [Paired v4 attempts and limits](../validation/model-comparison/household-direct-v4/README.md) |

A **receipt** records what a check actually observed. An **immutable commit** identifies an exact repository version. Opening a retained package does not rerun the question, update the law or generate an AI answer. The later website publication must be checked separately from the SDK observation and local exporter tests.

The [earlier 0.5.0 service observations](../validation/compact-delivery/v0.5.0/README.md) remain unchanged, including three functional browser journeys, Firefox cookie warnings and the historical browser suite that was not run. Earlier [model attempts](monday-model-trials.md) and their substantive critique also remain available. Both [v3 empty controls](../validation/model-comparison/household-direct-v3/README.md) were rejected for unrecognised client metadata, so no substantive v3 calls followed. The separately frozen v4 trial does not replace those observations.

## Source modelling and the service are different versions

The latest published ignored-person source, `c44bc3a111d18b6d4098a148a9a1b67c1411882b`, has **53 concepts**, **106 selected source pages**, **61 support dependencies** and **20 selected statutory units**. Its semantic index contains 913 records and 1,526 assertions. A **concept** names a meaning, such as a couple or a benefit component. A **support dependency** identifies material that must accompany an interpretation. A **statutory unit** is a selected section, regulation or schedule paragraph, not a complete Act. The captured manuals remain much larger than these deliberately modelled selections.

This newer source is **not the source used by public service 0.6.0 or the paired v4 trial**. Those use the partner-qualified source `723bcc5b015ab38a026625c2148edbd784edf7c7`. Keep the source, assembler and package identities visible when comparing results.

The [ignored-person comparison](../validation/ignored-person-context/2026-09-21/README.md) shows a capacity regression. At **512 KiB** (524,288 bytes), the required-evidence allocator retains **177 of 177 expected candidate occurrences**, but only **647 of 765 declared path occurrences**, across 40 supplied question occurrences representing 39 unique questions. A **path** is a directed chain of relationships needed to reach supporting evidence. Finding a candidate page does not mean every qualification travelled with it. The two care-home cases retain six of their seven household-support pages at this budget; Chapter 77 page 19 is missing. At 256 KiB the newer source retains 171 of 177 candidate occurrences and 393 of 765 paths.

All packages remain **insufficient**. The comparison measures evidence retention; it generates no AI answers and establishes no specialist acceptance. No obligations or byte limits were reduced to hide the regression. The earlier public source's [176-occurrence result](https://github.com/chris-page-gov/okf-dwp/blob/3ef0e786e9a18e76fa17c7d925ff509d6d6c9f84/evaluation/semantic-expansion/evaluation.json) remains unchanged.

### Earlier qualification and disability checkpoints (historical)

The earlier qualification source declared 15 support dependencies, including whole passages that
qualify household, housing-cost and temporary-residence summaries. A dependency
says which material must accompany an interpretation; it does not make that
interpretation official. The [joint comparison](../validation/qualification-context/2026-09-21/README.md)
freezes source `7f9feb9634e3d94004853b838462aca132c505a5` and Explorer
`c4f2de0a99b7bc2f8b8c8a06a3c715fb56b66d8e` independently of the then-current public 0.5.0 service. Explorer PR 131 merged and passed its canonical and Pages checks. The retained public Chrome observation verifies that qualification source on the recorded application; it does not verify the later service release.

In that historical comparison, at both 256 KiB and 512 KiB, the pair retains all 433 declared path occurrences.
Both care-home questions retain all seven household-support pages through their
declared paths. At 256 KiB each package has 27 records and 63 relationships.
The 512 KiB result also includes an optional temporary-care summary whose page
78/24 support is missing, and reports that gap. The earlier 64 KiB envelope
cannot hold the expanded care-home requirement metadata: it returns an explicit
`metadata_budget` refusal. That is a useful limit to demonstrate, not an answer.

All 203 obligations remain open. None of these historical observations repairs an
earlier model response or establishes specialist acceptance. Use the
[component review](carehome-component-dependency-review.md) to inspect the exact
wording corrections. The subsequent [disability increment](disability-addition-qualification-review.md) declared 29 dependencies in a 903-record index. Its 40-case replay retains all 177 candidate occurrences at 512 KiB; at 256 KiB the richer care-home support does not all fit, and the package explicitly names missing evidence. Source review, 46 semantic controls and 20 combined Reader controls pass. These are results for that disability checkpoint, not the later ignored-person source or current service.

There are **203 open obligations**: 43 evidence-closure requirements and 40 each for applicability, legal version, independent review and question scope. An **open obligation** names something that has not been established. It prevents the system from turning a promising source trail into a false claim of completeness. The [profiles](../evaluation/semantic-expansion/profiles.json) retain these requirements; the [legal-body guide](legal-body-evidence.md) records the statutory extraction and its remaining limits, including 12 units with unknown extent.

## Ten-minute demonstration

### 0–2 minutes: explain the three jobs and check the route

Open the [learning website](https://chris-page-gov.github.io/okf-dwp/). The new [retained care-home example](https://chris-page-gov.github.io/okf-dwp/evidence-examples/monday-2026-09-21/index.html#current-care-home) is the intended starting point after PR 21 passes CI and its public check. **CI** means automated repository checks. Until that publication is verified, use the [repository walkthrough and exact retained files](retained-evidence-examples.md), and state the delivery limitation.

- **Search** finds possible records using repeatable matching.
- **Ask OKF** assembles a limited evidence package and explains the selections and omissions.
- An **AI answer** interprets that package. Its claims need a separate review.

Explain that this retained example comes from service 0.6.0 and source `723bcc5b…`; the newer `c44bc3a1…` source has a separate capacity evaluation. Opening a saved package does not fetch new law or ask an AI another question.

### 2–4 minutes: read the care-home qualification

Show the original staff wording, including its recorded typo:

> Does Pension Credit stop is a citizen moves into a care home permanently if they are self-funding?

The retained current package has **55 records, 115 relationships and 523,326 bytes**, and reports **insufficient**. Open the passage containing DMG 78088 and read the preceding heading: **“Claimants who have no partner (including self- funders)”** in the retained extraction. This limits the branch being discussed; it does not establish that the person in the question has no partner. Show the whole passage, its footnote and its gaps, rather than quoting the conclusion alone.

**Provenance** records where the text came from and which version was captured. The separate inclusion reasons and directed relationships explain why it was selected. **Truncation** means package limits omitted some material. Neither a selected relationship nor a valid source link proves that a rule applies to a particular person.

<a id="compact-evidence-demo"></a>

### 4–6 minutes: inspect small parts and the complete package

Use the retained reader's evidence, provenance and relationship views, then its complete-package button. A **manifest** is a small catalogue that helps the reader request selected parts. A **hash** is a fingerprint of exact bytes; the complete package's SHA-256 is `cb7e8e6f62a49a15907b09d2a32d525539c6853d5344ebcd5566bf616315e8f7`. The static reader opens saved evidence without recreating it through the service.

Compare the [empty control](https://chris-page-gov.github.io/okf-dwp/evidence-examples/monday-2026-09-21/index.html#unknown-control), which has no selected records or relationships, with the [historical care-home example](https://chris-page-gov.github.io/okf-dwp/evidence-examples/monday-2026-09-21/index.html#historical-care-home), which has 35 records and 50 relationships. The historical package preserves its original bytes and does not invent a previously unrecorded engine identity. All three remain insufficient. Follow the same publication preflight above for these links.

For external clients, **MCP** (Model Context Protocol) is the interface for calling the service's read-only tools. Opening the website or retained reader does not prove that ChatGPT Voice or another client has connected to those tools. The [actual SDK check](../validation/compact-delivery/v0.6.0/README.md) verifies the recorded tool delivery separately.

### 6–8 minutes: compare the paired v4 answers

Open the [v4 trial record](../validation/model-comparison/household-direct-v4/README.md). Both Claude and Codex first passed the empty control, then produced mechanically accepted answers to Staff 012 from the same frozen evidence package, with **zero observed tool calls**. Show the original answers and their cited source text side by side.

**Mechanical acceptance** means the recorded output passed format, execution-boundary and citation checks. It does not mean the claims are complete, applicable or legally correct. The [separate agent claim review](../validation/model-comparison/household-direct-v4/independent-claim-review.md) identifies specific omitted exceptions and an overstated evidence gap in one response; specialist review remains pending. Ask the reviewer to compare each claim with its whole source heading, conditions and exceptions; do not present either model as the adjudicator of entitlement. Earlier rejected attempts remain recorded under their own protocols.

### 8–10 minutes: name the next work precisely

Show the [newer-source capacity result](../validation/ignored-person-context/2026-09-21/README.md): finding all 177 candidate occurrences at 512 KiB still leaves 118 of 765 required path occurrences absent. This explains why adding more modelling can improve the declared knowledge while exceeding a fixed delivery budget. It is a measured limitation, not a successful complete answer.

Finish with the **203 open obligations** and choose one staff review action below. Keep the source/version, missing qualification and proposed correction together. If there is time, the [earlier SDA ambiguity example](../validation/household-reader-public/7f9feb96-c4f2de0a/README.md) shows why “SDA” must remain unresolved between Severe Disablement Allowance and a severe-disability additional amount without clarification. Its dated package is a separate historical observation.

## Staff review: the next useful contribution

| Review action | What to record | Backlog work package |
| --- | --- | --- |
| Clarify the intended question, especially SDA and “all scenarios”. | Intended benefit, component, date, jurisdiction and relevant hypothetical circumstances, without claimant details. | [DWP-BL-001](backlog-work-packages.md#dwp-bl-001-extensive-persona-journey-and-question-review) and [DWP-BL-007.acceptance](backlog-work-packages.md#dwp-bl-007-broader-semantic-modelling-task-specific-evidence-profiles) |
| Review the care-home and mixed-age concepts. | Missing qualifications, misleading aliases or source-backed relationships that need correction. | [DWP-BL-005.acceptance](backlog-work-packages.md#dwp-bl-005-broader-semantic-modelling-neutral-domain-concepts-and-relationships) |
| Check the statutory trail and source completeness. | Exact missing provision or case, applicable version, commencement, extent and unresolved contradiction. | [DWP-BL-006.acceptance](backlog-work-packages.md#dwp-bl-006-legislation-regulations-and-case-law-reconciliation) and [DWP-BL-007.evidence-closure](backlog-work-packages.md#dwp-bl-007-broader-semantic-modelling-task-specific-evidence-profiles) |
| Review the mechanically accepted v4 claims against the whole condition. | Claim, exact source, heading, exception and whether the conclusion is supported. | [DWP-BL-010.acceptance](backlog-work-packages.md#dwp-bl-010-fixed-evidence-claim-level-model-trials) |
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
