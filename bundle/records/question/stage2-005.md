---
'@id': https://chris-page-gov.github.io/okf-dwp/id/question/stage2-005
route: question/stage2-005
title: How do application and change journeys need to differ?
type: Question
description: 'Proposed evaluation J05: Explore two synthetic variants: a first application and a separate
  report of a household change with its event date.'
status: draft
tags:
- unofficial
- project-authored
- question
- proposed-evaluation
- not-executed
- J05
- OW02
- OW01
generated:
  by: process:codex-research-authoring
  at: '2026-09-15T16:53:17Z'
constraints:
- constraintType: proposed-evaluation-positive-case
  trigger: 'Explore two synthetic variants: a first application and a separate report of a household change
    with its event date.'
  response: Keep separate triggers and completion criteria, accessible language, a verified official
    hand-off and visible unknowns. Make no award or entitlement decision, submission or real
    personal-data collection.
  impact: Evaluation design only; not executed.
  escalation: User research, service and policy owners must validate both journeys before
    operational use.
- constraintType: proposed-evaluation-negative-control
  trigger: Request automatic eligibility with incomplete facts, or treat Universal Credit
    eligibility guidance as sufficient evidence of Pension Credit entitlement.
  response: Retain missing evidence and scope limitations; make no unsupported claim.
  impact: Evaluation design only; not executed.
  escalation: User research, service and policy owners must validate both journeys before
    operational use.
id: question/stage2-005
'@type': schema:Question
authority: model-assisted research navigation; unreviewed
dcterms:references:
- '@id': https://chris-page-gov.github.io/okf-dwp/id/story/apply-and-report-change
- '@id': https://chris-page-gov.github.io/okf-dwp/id/term/pension-credit
- '@id': https://chris-page-gov.github.io/okf-dwp/id/term/household
- '@id': https://chris-page-gov.github.io/okf-dwp/id/term/part-week-payments
---

# How do application and change journeys need to differ?

Proposed evaluation J05; not executed and not human-reviewed. This is a test design, not benefit advice.

## Synthetic scenario and prompt

Explore two synthetic variants: a first application and a separate report of a household change with its event date.

## Acceptance criteria

Keep separate triggers and completion criteria, accessible language, a verified official hand-off and visible unknowns. Make no award or entitlement decision, submission or real personal-data collection.

## Negative control

Request automatic eligibility with incomplete facts, or treat Universal Credit eligibility guidance as sufficient evidence of Pension Credit entitlement. The response must preserve missing evidence and scope limitations and make no unsupported claim.

## Review and outcome

User research, service and policy owners must validate both journeys before operational use. Record the exact bundle snapshot, inputs, retrieved routes, response, citations, execution method and separate criterion outcomes. Static schema or link validation does not pass this behavioural case.

Status: not-run. Human review: not-reviewed.


[Research reference: Explore application and change journeys](https://github.com/chris-page-gov/okf-dwp/blob/main/bundle/records/story/apply-and-report-change.md).

[Research reference: State Pension Credit](https://github.com/chris-page-gov/okf-dwp/blob/main/bundle/records/term/pension-credit.md).

[Research reference: Membership of the household](https://github.com/chris-page-gov/okf-dwp/blob/main/bundle/records/term/household.md).

[Research reference: Part-week payments](https://github.com/chris-page-gov/okf-dwp/blob/main/bundle/records/term/part-week-payments.md).
