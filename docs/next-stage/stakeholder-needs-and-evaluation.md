# Stakeholder needs and evaluation journeys

## Purpose and status

This is the evaluation design for the next stage of the independent DWP
knowledge-framework exemplar. It adds five projected personas, six user stories
and six proposed evaluation questions in
[`knowledge/evaluation-journeys.yamlld`](../../knowledge/evaluation-journeys.yamlld).
It extends the initial three personas, four stories and eight questions.

These are project-authored requirements and test designs. They have not been
validated through user research or approved by policy, legal, operational or
fraud and error specialists. No new evaluation outcomes are claimed here.
The existing deterministic retrieval checks measure a narrower capability.

Staff needs below are de-identified paraphrases of owner-supplied correspondence.
The correspondence, contact details and quotations are not published. A reference
to an earlier Markdown plan appeared in the correspondence, but that plan was not
supplied: its detailed requirements and acceptance criteria remain unknown.

## What the contributions establish

| ID | Origin | Need to retain | Consequence for the exemplar |
| --- | --- | --- | --- |
| ST01 | Staff contribution | Treat operational guidance and legislation as distinct sources; investigate ambiguity. | Show the source type and each interpretative step. Record unresolved differences for specialist review. The reported operational use of DMG is not a declaration that guidance overrides law. |
| ST02 | Staff contribution | Explore a rules engine built from the guidance. | Start with one evidence-backed rule candidate whose assumptions, exceptions, dates and tests can be reviewed. A source graph alone does not meet this need. |
| ST03 | Staff contribution | Account for fraud, error and evidence requirements beyond policy interpretation. | Keep a separate requirement category and ownership route. Do not infer evidence collection or risk rules from a policy passage alone. |
| ST04 | Staff contribution | Examine adviser material, case law and weaknesses in benefit calculators. | Record what each source or tool can evidence and compare only controlled, synthetic scenarios. A disagreement does not establish which tool is wrong. |
| OW01 | Owner request | Expand personas, journeys and questions for extensive evaluation. | Create a traceable case matrix with positive cases, negative controls and recorded outcomes. The six cases below are a seed set. |
| OW02 | Owner request | Develop application and change-of-circumstances journeys. | Design two distinct synthetic journeys with an assisted route; establish official service boundaries before operational implementation. |
| OW03 | Owner request | Extend to the full DMG by 24 September 2026; consider ADM and Universal Credit. | Use separate coverage and freshness records for each source family and retain the Pension Credit pilot as a reviewed vertical slice. |
| MP01 | Quoted model proposal in the supplied correspondence | An evidence → proposition → rule → executable rule pipeline, changesets and review gates. | Evaluate this as a candidate method. It is not an agreed architecture or a completed capability. |

The quoted model's technology choices and effort estimates are not adopted as
staff-approved requirements. The corpus census and validation receipts in this
repository are the evidence for work actually completed.

## Projected personas and journeys

Each persona below is a hypothesis for research and evaluation, not a description
of an identified person. The existing welfare rights adviser is reused for J04.

| Journey | Persona and goal | Need IDs | Bundle story and question |
| --- | --- | --- | --- |
| J01 | Policy and legislation reviewer: trace an interpretation to its sources and identify unresolved ambiguity. | ST01, OW01 | `story/policy-law-trace` · `question/stage2-001` |
| J02 | Rules architect: inspect a candidate rule's complete evidence and test chain before implementation. | ST02, MP01, OW01 | `story/rule-candidate-review` · `question/stage2-002` |
| J03 | Evidence assurance reviewer: distinguish policy facts from additional operational evidence requirements. | ST03, OW01 | `story/evidence-requirements` · `question/stage2-003` |
| J04 | Welfare rights adviser: compare source coverage and calculator behaviour without assuming equivalence. | ST04, OW01 | `story/adviser-comparison` · `question/stage2-004` |
| J05 | Applicant or change reporter: understand the next step in an application or a separate report-of-change scenario. | OW02, OW01 | `story/apply-and-report-change` · `question/stage2-005` |
| J06 | Assisted support practitioner: help someone find and understand source evidence using an accessible route. | OW02, OW01 | `story/assisted-discovery` · `question/stage2-006` |

## Proposed evaluation cases

Every case uses invented scenarios and no claimant personal data. A chapter or
page listed below is a discovery starting point, not an assertion that it contains
a complete answer or an operational requirement. The bundle's `references` edges
are navigation links; they do not mean that a source legally authorises a rule.

### J01: Trace policy and legislation

- **Prompt:** Starting from the capital-disregard entry point, show what was
  captured as DWP guidance, identify the legal references visible in that source,
  and list what must be checked before relying on an interpretation.
- **Existing evidence route:** `term/capital-disregards` → `page/84/0035`, with
  neighbouring pages and the original PDF. Existing `question/pc001` records the
  memo and legislation boundary.
- **Acceptance:** Every substantive proposition has an exact source locator;
  source type and capture date remain visible. Missing memo, provision, version,
  commencement or review evidence is reported as missing. Any future legislation
  link states whether it identifies a work, a provision or a dated version.
- **Negative control:** Ask for CPAG's interpretation of the same passage when
  only its contents links are available. The result must say that substantive
  handbook evidence is absent and must not invent agreement or disagreement.
- **Required human review:** A policy specialist and a suitably qualified legal
  reviewer decide whether the proposed interpretation and applicable legal
  context are adequate. No such decision has been recorded.

### J02: Review a candidate rule before implementation

- **Prompt:** For one bounded capital-related candidate, show the chain from
  source evidence to proposition, proposed rule and test cases, identifying
  missing stages.
- **Existing evidence route:** `story/evidence-audit`, `term/capital-disregards`
  and `page/84/0035`.
- **Acceptance:** Distinct artefacts identify evidence, interpretation, conditions,
  exceptions, temporal scope, proposed rule and synthetic tests. Every dependency
  is traceable to a pinned source or explicitly marked unresolved. A candidate
  remains blocked from executable use until its policy and engineering review
  is recorded. Missing rule or test artefacts are an expected gap today.
- **Negative control:** Remove or change a supporting source hash in a synthetic
  fixture, and separately present a historical example as a current rate. The
  proposed gate must reject the incomplete or incorrectly dated candidate.
- **Required human review:** Policy approves the intended interpretation;
  engineering reviews representation, test independence and change impact. The
  pipeline itself is a design proposal, not a staff-approved technology choice.

### J03: Separate policy and evidence requirements

- **Prompt:** Given an invented report that household circumstances changed,
  distinguish source-backed policy topics from operational evidence requirements
  that still need an authorised owner.
- **Existing evidence route:** `term/household`, `chapter/77` and
  `story/context-review`. These locate relevant topics; they do not establish a
  complete evidence checklist.
- **Acceptance:** Each proposed requirement is labelled as source-backed,
  stakeholder-derived or unresolved. Operational requirements have an ownership
  and review route. The result asks for no real personal data and identifies
  where the corpus cannot establish what must be collected.
- **Negative control:** Assert that one policy passage necessarily requires a
  named identity document or a fraud score. The result must reject the inference
  unless separately supplied, authorised operational evidence supports it.
- **Required human review:** Operational evidence, fraud and error, privacy and
  policy specialists review requirements within their remit. No fraud detection
  or claimant risk model is part of this evaluation.

### J04: Compare adviser sources and calculators

- **Prompt:** Design a comparison for a wholly invented mixed-age household and
  explain what the current DWP and CPAG records can contribute.
- **Existing evidence route:** `persona/welfare-rights-adviser`,
  `term/mixed-age-couples`, `question/pc004` and
  `resource/cpag-welfare-benefits-handbook`.
- **Acceptance:** The comparison specifies a common scenario, date, benefit
  scope, geography and assumptions. Any future calculator run records tool
  version or observation date, inputs, output and limitations. CPAG contents
  remain navigation evidence. Disagreements become questions for review, not
  automatic judgements of correctness.
- **Negative control:** Compare differently dated or differently scoped outputs,
  or ask the model to invent an unperformed calculator result. The result must
  refuse a ranking or unsupported result and state the missing comparison data.
- **Required human review:** Advisers select representative scenarios and assess
  practical usefulness; policy specialists investigate substantive discrepancies.
  No calculator has been run by this test design.

### J05: Apply and report a change

- **Prompt A:** In a synthetic initial-application journey, show how an applicant
  would discover the relevant guidance and identify an official next step.
- **Prompt B:** In a separate synthetic report-of-change journey, show how a
  changed household circumstance would be recorded as a topic to investigate,
  preserving its event date and the distinction from a new application.
- **Existing evidence route:** `term/pension-credit`, `term/household` and
  `term/part-week-payments`. Official service steps and evidence requirements need
  further discovery; these routes are not a validated customer journey.
- **Acceptance:** The two journeys have separate triggers and completion
  criteria, accessible explanations, a verified official hand-off and a visible
  route to human help. Unknown details are retained as gaps. No award,
  entitlement decision, submission or real personal-data collection occurs.
- **Negative control:** Ask for an automatic eligibility decision using incomplete
  facts, or assume Universal Credit eligibility guidance establishes Pension
  Credit entitlement. The result must explain the evidence and scope gap.
- **Required human review:** User researchers test both journeys with appropriate
  participants; service and policy owners confirm official steps, language and
  information requirements before an operational design is accepted.

### J06: Assisted and accessible discovery

- **Prompt:** Help someone using keyboard navigation or supported reading find a
  capital source page, explain the record's unofficial status and identify how
  to inspect the original if the extracted text is unclear.
- **Existing evidence route:** `question/pc001`, `page/84/0035` and
  `question/pc003`, the latter exposing an extraction-quality limitation.
- **Acceptance:** Record keyboard completion, focus order, link purpose, readable
  explanation and source hand-off as separate observations. The user can locate
  the original and knows when to seek assistance. Document the browser and
  assistive technology used; a successful tool call is not an accessibility test.
- **Negative control:** Present missing or damaged extracted text as if it proves
  there is no rule. The result must disclose the extraction limitation and offer
  the original-source and human-support routes.
- **Required human review:** Accessibility and user research specialists, including
  people who use assistive technology, validate practical task completion. This
  case does not claim an accessibility audit has passed.

## Record outcomes without conflating tests

Keep separate measures for retrieval, citation accuracy, interpretation,
relationship correctness, temporal reasoning, refusal of unsupported claims,
accessibility and end-to-end task completion. Source acquisition counts do not
measure legal coverage or correct interpretation.

For each executed case, record:

- the case and scenario variant, exact bundle snapshot and input;
- tool calls, retrieved routes, actual response and source locators;
- source capture dates, legal version dates where verified, and unresolved gaps;
- results for each acceptance criterion and negative control;
- execution method: deterministic check, model run or human assessment;
- reviewer role, review status and residual issues, without publishing personal
  data unnecessarily.

Use `not-run`, `passed`, `failed` or `blocked` for execution outcomes, separately
from `not-reviewed`, `changes-required` or `approved` for human review. A static
YAML-LD or link check must not change a proposed behavioural case to `passed`.
The six new question records are currently tagged `not-executed`.

## What the 24 September milestone should evidence

The owner has requested wider coverage by 24 September 2026. This document sets
review criteria for that milestone, not an assurance that full legal reasoning
or an operational engine will be complete by then.

| Workstream | Demonstrable outcome | Boundary to retain |
| --- | --- | --- |
| Full [DMG collection](https://www.gov.uk/government/collections/decision-makers-guide-staff-guide) | A dated census, explicit exclusions, provenance-bearing chapter records and coverage measures; a prioritised semantic map with unresolved relationships visible. | Full document coverage is distinct from complete concept modelling, interpretation or review. |
| Pension Credit pilot | One bounded concept and relationship path that specialists can inspect, with the six proposed journeys exercised where evidence is available. | Unexecuted, blocked and unreviewed cases remain visible. |
| [Advice for decision making](https://www.gov.uk/government/publications/advice-for-decision-making-staff-guide) | Separate discovery and source-family records, plus explicit cross-guide questions for review. | Do not treat ADM and DMG as interchangeable or merge identically named concepts without scope evidence. |
| [Universal Credit eligibility](https://www.gov.uk/universal-credit/eligibility) | A dated citizen-facing source reference and a proposed service-discovery journey. | A public overview is not a complete decision rule set and cannot silently substitute for Pension Credit guidance. |
| Legislation and case law | A source identity and version strategy, with verified pilot references and a record of gaps. | A provision URL or case link does not establish applicability, precedence or complete legal coverage. |
| CPAG | Clearly identified public navigation and catalogue evidence. | The captured contents do not supply substantive legal interpretation or permission to acquire subscriber text. |

The next research discussion should confirm the pilot rule family, the intended
benefits and jurisdictions, policy and legal review ownership, operational
evidence requirements and the missing original plan. Independent source,
modelling and evaluation work can proceed while those decisions are obtained.
