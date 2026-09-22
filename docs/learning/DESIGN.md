# DWP demonstration learning-path design

**Review draft — 22 September 2026.** Independent learning design, not official DWP training, benefits advice, a deployed curriculum or a validated competency award.

Use **12 paths and 112 steps**, with a maximum of **20 steps in one path**. Cover every supplied question, but organise learning around the decisions a person must be able to make. The programme is a role-based catalogue: nobody is expected to complete all 112 steps before attending a demonstration.

The design has three programme outcomes:

1. **Demo 1:** find, inspect and communicate bounded evidence; measure whether OKF improves cost and answer quality rather than assume that it does.
2. **Demo 2:** trace application fields to the appropriate public form, support an accessible human journey, and prove that an agent can use the same validation with explicit user control.
3. **Demo 3:** distinguish evidence, interpretation, rule specification and executable behaviour; demonstrate a bounded prototype only when its dependencies and review gates are satisfied.

[Read all 112 step specifications](LESSONS.md). Each includes an outcome, a practice artefact, existing evidence routes, question references and an estimated duration. [Inspect the machine-readable design](learning-design.json), [question coverage](question-coverage.json), [source identities](source-manifest.json) and [design validation](design-validation.json).

## What the source material actually establishes

The inspected [ai-demo revision](https://github.com/bitsls2/ai-demo/tree/977193212c23923824b54d4e0766ffcad9d17bf0) contains three files:

- [README](https://github.com/bitsls2/ai-demo/blob/977193212c23923824b54d4e0766ffcad9d17bf0/README.md): public-domain demonstration boundary and three aims.
- [Demo 1 notes](https://github.com/bitsls2/ai-demo/blob/977193212c23923824b54d4e0766ffcad9d17bf0/demo-1-overview.md): 40 question occurrences, comprising 39 unique questions, and a proposed with/without-OKF comparison.
- [Demo 2 notes](https://github.com/bitsls2/ai-demo/blob/977193212c23923824b54d4e0766ffcad9d17bf0/demo-2-overview.md): a Pension Credit application using CASA and agent-accessible browser tools. Demo 3 has an aim in the README but no equivalent detailed script.

The demo repository does **not** define named personas. This design maps its aims onto the eight projected personas actually present in the inspected okf-dwp combined corpus. The six-persona staff-needs register is a narrower source; the combined corpus also contains applicant/change-reporter and rules-architect personas. None should be represented as validated user research.

All 40 demo question occurrences match the existing staff-question registry, in order and exact wording. The registry retains the wording; this design uses question IDs and paraphrased teaching objectives. All 42 source-candidate routes referenced by that registry exist in the inspected combined corpus of 20,046 records. Existence establishes a usable anchor, not complete evidence or correct legal applicability.

Pinned inputs: ai-demo `977193212c23923824b54d4e0766ffcad9d17bf0`; okf-dwp `d45774648f00008ffff744a9c8d37bd154070d1c`; Explorer `fff8781907aa46aed40c70a984b502c12dd5e201`. File hashes are retained in the source manifest. The seven topical paths adapt the existing projected [staff journeys](https://github.com/chris-page-gov/okf-dwp/blob/d45774648f00008ffff744a9c8d37bd154070d1c/domain-profile/staff-needs/journeys.json), adding learning tasks and assessment gates. Carer interactions move to P08 so the carer pathway owns all three related questions.

## Path allocation

Step counts include preparation, worked practice, counterexamples and assessment. Times in LESSONS.md are planning estimates, including short artefact preparation; specialist marking and source acquisition are additional.

| Path | Learning objective and assessed output | Main participants | Demo | Steps | Primary question ownership |
| --- | --- | --- | --- | ---: | --- |
| P01 — Read evidence before trusting an answer | Produce a claim-to-evidence ledger, preserve qualifications and recognise insufficiency. | All staff roles; assisted participants | All | 8 | Foundation across all cases |
| P02 — Absence abroad and residence | Scope benefit, territory, duration and purpose; re-evaluate a changed scenario. | Adviser, policy reviewer | 1 | 7 | 001, 023 |
| P03 — Pension regimes, age and transitions | Separate age, regime, qualification, claim and payment in a transition brief. | Pensions specialist, policy reviewer | 1 | 8 | 002, 004, 025, 032 |
| P04 — Pension Credit inputs and calculation structure | Produce an input dictionary and dependency graph with unknowns and dated parameters. | Pensions specialist, rules architect, assurance reviewer | 1, 2, 3 | 10 | 006, 010, 015, 016, 019, 020, 021 |
| P05 — Historical rates, additions and ambiguous terms | Produce a date-bound comparison with separate SDA meanings and explicit missing cells. | Pensions specialist, policy and assurance reviewers | 1, 3 | 8 | 007, 008, 009 |
| P06 — Partners, household and care-home changes | Compare funding and household variants; identify an omitted qualification in a plausible answer. | Adviser, pensions specialist, assurance reviewer | 1, 2, 3 | 10 | 012, 013, 014, 017, 018 |
| P07 — Directed benefit interactions and disability transitions | Build variant-specific directed maps and reproduce the duplicate question package. | Adviser, policy and assurance reviewers | 1 | 20 | 003, 005, 011, 022, 024, 026–031, 033–037 |
| P08 — Caring conditions and effects on others | Distinguish conditions, evidence and effects on each person; reject unsupported multiple-payment arithmetic. | Adviser, assurance reviewer | 1 | 7 | 038–040 |
| P09 — Test whether OKF improves the AI demonstration | Run a fair paired experiment and publish complete cost, quality and failure accounting. | Knowledge engineer, policy and assurance reviewers | 1 | 8 | Revisits 002, 006, 008, 012, 026, 033; unknown-term control |
| P10 — Design an accessible Pension Credit application journey | Produce a field-to-form map and a keyboard-complete synthetic journey. | Knowledge engineer, pensions specialist, assisted participant, applicant | 2 | 8 | Application use of P04 and P06 |
| P11 — Demonstrate a trustworthy agent-assisted application | Prove callable tools, validation parity, exact-state confirmation and safe recovery. | Knowledge engineer, assisted participant, assurance reviewer | 2 | 8 | Human/agent parity, cancellation and retry cases |
| P12 — From evidence to a reviewable rules prototype | Produce a traceable, bounded non-operational rule pack with counterexamples and promotion blockers. | Rules architect, policy and assurance reviewers | 3 | 10 | Transfer from P04–P07 and P09 |

This allocation uses every path slot for a distinct decision or demonstration capability. It avoids one superficial path per benefit or persona. It uses **112 of 288 possible step positions**, leaving 176 positions for justified remediation or later evidence. Unused positions are capacity, not missing learning. P07 has only four spare positions, so run it as two sessions with a break after step 10; do not force more content into it without reviewing its scope.

Each question has exactly one primary owner. Cross-path reuse is intentional transfer practice. Keep staff-026 and staff-033 separately identifiable: their duplicate wording tests whether identical governed inputs reproduce the same evidence identity. Different model prose is not, by itself, evidence of a retrieval inconsistency.

## Persona-specific routes

- **Welfare rights adviser:** P01 → the relevant P02, P06, P07 or P08 casework path. Assessment is a qualified source explanation and a useful next step, not an entitlement answer.
- **Pensions specialist:** P01 → P03–P06 as required. Assessment focuses on regime, dates, household qualifications and calculation dependencies.
- **Policy and legislation reviewer:** P01 → relevant subject paths → P12. Review whether sources support the proposed interpretation and what legal reconciliation remains.
- **Evidence assurance reviewer:** P01 → P06 → P09; add P11 for service assurance. Review claims, omitted conditions, failed runs and promotion blockers.
- **Knowledge engineer:** P01 → P09; for the application demonstration, complete the P10 prerequisites and continue to P11. Retain source, runtime, model and tool identities separately.
- **Rules architect:** P01 → P04, P05, P06, P07 and P09 → P12. An output that cannot be promoted may be a successful learning result if the learner correctly identifies why.
- **Applicant/change reporter:** participate in P10 steps 1, 4, 5, 7 and 8 with fictional information. They are not required to learn CASA, rule engineering or benefit-law interpretation. The builder/facilitator owns P10's technical prerequisites.
- **Assisted support practitioner:** support P01 and the human-facing portions of P10/P11. Test explanation, keyboard access, correction, confirmation and recovery. Support must not become an assumption of consent.

The prerequisite graph is acyclic and is declared in the design JSON. A path prerequisite is an **assessed outcome**; equivalent prior evidence may satisfy it after review. Merely ticking every earlier step does not.

## How to enforce the objectives

The current Reader displays title, description, ordered steps, outcomes, practice prompts, time estimates and in-memory completion ticks. It does **not** store assessed competence, enforce prerequisites, validate answers, preserve progress across reloads, or issue credentials. Metadata alone cannot change that.

For the present demonstrations, use a facilitator-controlled assessment ledger alongside the Reader. For software enforcement, implement the state machine and gate contract below in a separate change. Until then, describe the paths as **guided and assessed by a facilitator**, never automatically enforced.

### Per-step and per-path evidence

Each learner produces the artefact named in the step: for example a clarification tree, dated rate table, directed relationship map, claim ledger, field map or synthetic test report. The final step uses a different example or changed material fact, so copying the worked example is insufficient.

Score the final artefact on five dimensions, each from 0 to 2:

| Dimension | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Source traceability | No verifiable source | Source named, context or locator incomplete | Exact source, context, locator and version retained |
| Scope and qualifications | Unsupported generalisation | Some limits identified | Relevant regime, date, variant, exceptions and uncertainty explicit |
| Task-specific reasoning | Wrong or unsupported inference | Partially justified output | Declared path objective demonstrated with justified relationships |
| Counterexample and gaps | Ignores a changed fact or missing requirement | Detects but cannot resolve or explain | Re-evaluates correctly, or gives a justified cannot-determine result |
| Clear and reproducible communication | Unusable or unreproducible | Understandable with support | Clear artefact, explicit assumptions and reproducible inputs |

Proposed pass rule: **at least 8/10**, with **2/2 for traceability, scope and counterexamples**, the path-specific artefact accepted, and no critical failure. This is a proposed instructional standard to calibrate with reviewers, not an established DWP competency threshold.

Critical failures override the numeric score: invented citation or tool call; concealed missing evidence; unsupported individual entitlement or award; assumed current legal applicability; unauthorised or real submission during a synthetic exercise; silently selecting an ambiguous meaning; comparison results presented as improved without supporting measurements. Reading more material cannot compensate for one of these failures.

After a failed criterion, assign a specific remedial step and a different transfer case. A repeat assessment records the earlier failure; it does not overwrite it. Use an optional later recall/transfer check to test retention. No scheduled reminder or automatic monitoring is created by this design.

### Proposed enforcement state machine

`not_started → practising → submitted → changes_required | passed`

Only an authorised assessor can move `submitted` to `passed`. A learner completion tick may mark practice activity but cannot mark an assessment passed. A dependent path unlocks only when all applicable prerequisite outcomes have accepted evidence or a recorded equivalent-prior-learning decision. Correct remediation returns the learner to `submitted` with a new attempt. Learners can still inspect the catalogue and prerequisites; an assessment lock must not conceal source information.

Use the [assessment ledger template](assessment-ledger-template.csv) for facilitator assessment. Store a minimal attempt record: pseudonymous learner key; path and objective versions; bundle snapshot; question/case IDs; source and artefact hashes; per-dimension scores; critical-failure flags; assessor identity and role; decision time; remediation references. Keep claimant details out of this ledger. Changed source or objective versions mark the prior pass as needing review for the new version, while preserving its historical validity. A specialist reviews legal interpretation; a technical reviewer alone cannot certify it.

## Demonstration scripts and honest claims

### Demo 1: ten-minute excerpt

- Minute 0–1: P01 step 2 — distinguish original text, extraction and interpretation.
- Minutes 1–4: P06 step 4 — inspect staff-012, including the qualifying heading and household context.
- Minutes 4–6: P06 step 9 — critique a plausible answer that quotes accurately but omits a qualification.
- Minutes 6–8: P09 step 5 — show paired cost and quality results if available, with complete token accounting.
- Minutes 8–10: P09 step 8 — state supported conclusions, failed cases and what reviewers must check next.

This is a demonstration excerpt, not completion of P01, P06 or P09. Do not mark omitted steps as passed. If paired results do not exist, show the experiment design and label it unrun.

For the fair comparison, use the same frozen source material in raw-document and OKF-assisted conditions, the same model/settings and comparable output budgets. A no-evidence run is a separate control. Count tool responses and retries, distinguish one-off preparation from per-question costs, retain failures and report variation over repeated runs. Fix the evaluation question and source window before comparing. The source notes express an intended advantage; the demonstration must test it rather than assume it.

### Demo 2: ten-minute excerpt

Show the official source-to-field mapping, a human correction in the synthetic form, a real discovery/invocation in the chosen host, equivalent validation through the agent route, exact-state confirmation, and a single fictional receipt. Deliberately change an answer after review and demonstrate that confirmation must be renewed. If tools are registered but not callable, show the working human route and report the blocked agent capability.

The official [Pension Credit form page](https://www.gov.uk/government/publications/pension-credit-claim-form--2) lists PC1, its notes and PC1H and records an update on 3 March 2026. The page was inspected; this design does not claim to have extracted or validated every PDF field. P10 is gated on acquiring and inspecting those exact artefacts. A whole claim form must not be reduced to the inputs of a benefit calculation.

[CASA's package documentation](https://www.npmjs.com/package/@dwp/govuk-casa) is the source for the framework role. Pin and test the selected package rather than assuming a repository or cached version is current. [The WebMCP specification](https://webmachinelearning.github.io/webmcp/) informs the capability exercise; it is not proof that any particular browser/agent host exposes callable tools. The tools listed in P11 are proposed operations, not claims about an existing application API.

### Demo 3: ten-minute excerpt

Trace one source passage through a candidate proposition, an explicit interpretation decision, a typed rule table and synthetic boundary tests. Remove a required exception or date and show an indeterminate or blocked result. Finish with the review and promotion blockers. The demo repository's calculator ambition becomes a testable learning objective, not permission to represent the current experimental bundle as definitive law. No production calculator or real claim submission is part of this design.

## Reader implementation hand-off

The [draft presentation projection](reader-presentation.DRAFT.json) uses the existing `okf-large-learning-presentation.v1` fields and satisfies the 12/24 limits. It deliberately points to **112 proposed lesson records** under `learning/pNN/sNN`, not to existing evidence records masquerading as lessons. Do not add it to a published descriptor yet: those routes do not exist in the current corpus.

A separate lesson record is needed for each activity because the Reader requires unique routes within a path, while good teaching revisits the same source with a different task. Each lesson should contain the objective, exercise, artefact template, source anchors, gaps and assessment instructions. A persona route is a role-orientation anchor, not technical or legal proof. P09–P12 also depend on experiment records, form artefacts, technical documentation or test results described above; an existing persona record cannot satisfy those dependencies. Multiple lesson records may reference the same evidence without duplicating or redefining it. Do not imply semantic identity or legal applicability from a teaching link.

Implementation sequence:

1. Review this curriculum with the demonstration owner and benefits specialists; validate the projected personas through user research.
2. Author lessons in okf-dwp's governed semantic source family, preserving stable identities, authority and rights; treat the design JSON as a proposal, not a second semantic authority.
3. Generate lesson records, links and the additive combined Reader projection through the producer. Preserve the earlier pilot and full-DMG snapshots.
4. Validate every lesson route and evidence dependency, the exact 40-question mapping, the prerequisite graph, unique routes and the 12/24 ceilings. Fail rather than silently truncate a path or outcome.
5. Bind the generated presentation into the authored descriptor source and regenerate it. Keep the additional assessment schema outside the current Reader presentation contract unless a separately reviewed version supports it.
6. Deliver the facilitator ledger first, or implement and test the proposed assessment gates. Cover attempts to bypass prerequisites, self-award a pass, reuse stale evidence, or lose a failed attempt.
7. Rehearse desktop, narrow-screen and keyboard journeys; deep links, back/forward, missing records, source inspection, source-version changes and bundle switching. Confirm targeted hydration remains bounded.
8. Refresh exact-build acceptance, then perform the repository's required publication and real-browser checks before advertising a live curriculum.

## Current validation and remaining work

The design checks pass: 12 paths, 112 unique proposed lesson routes, maximum 20 steps, all 40 occurrences assigned, all 42 source candidates present, 79 distinct existing persona/evidence anchors valid, and no prerequisite cycles. The build script also verifies exact question matching and records file hashes.

The exact pinned Reader parser accepts all 12 paths and 112 steps without truncation. Parsing acceptance proves shape and bounds, not lesson availability. No learner study, specialist marking, field-level PC1 validation, callable WebMCP integration, lesson publication, enforced gating or public deployment is claimed.

To regenerate the design, set `OKF_DWP_ROOT`, `AI_DEMO_ROOT` and `OKF_EXPLORER_ROOT` to the pinned checkouts, with Explorer’s locked dependencies installed, and run `node build-design.mjs`. The script rejects a different Git revision. File hashes identify the inspected inputs; review both these and the declared revisions deliberately when rebasing the design. The outputs are design artefacts, not generated production bundle files.
