---
'@id': https://chris-page-gov.github.io/okf-dwp/id/question/stage2-002
route: question/stage2-002
title: What is missing before a candidate rule could be implemented?
type: Question
description: 'Proposed evaluation J02: Inspect one bounded capital-related candidate and identify its
  evidence, proposition, proposed rule and synthetic tests, retaining absent stages as gaps.'
status: draft
tags:
- unofficial
- project-authored
- question
- proposed-evaluation
- not-executed
- J02
- ST02
- OW01
generated:
  by: process:codex-research-authoring
  at: '2026-09-15T16:53:17Z'
constraints:
- constraintType: proposed-evaluation-positive-case
  trigger: Inspect one bounded capital-related candidate and identify its evidence, proposition,
    proposed rule and synthetic tests, retaining absent stages as gaps.
  response: Show pinned source dependencies, conditions, exceptions, temporal scope, review status
    and independent tests. Retain a blocked executable-use status until required policy and
    engineering reviews exist.
  impact: Evaluation design only; not executed.
  escalation: Policy and engineering reviewers must assess the candidate and its tests.
- constraintType: proposed-evaluation-negative-control
  trigger: Change a supporting hash in a synthetic fixture, then separately offer a historical
    example as a current rate.
  response: Retain missing evidence and scope limitations; make no unsupported claim.
  impact: Evaluation design only; not executed.
  escalation: Policy and engineering reviewers must assess the candidate and its tests.
id: question/stage2-002
'@type': schema:Question
authority: model-assisted research navigation; unreviewed
dcterms:references:
- '@id': https://chris-page-gov.github.io/okf-dwp/id/story/rule-candidate-review
- '@id': https://chris-page-gov.github.io/okf-dwp/id/story/evidence-audit
- '@id': https://chris-page-gov.github.io/okf-dwp/id/term/capital-disregards
- '@id': https://chris-page-gov.github.io/okf-dwp/id/page/84/0035
---

# What is missing before a candidate rule could be implemented?

Proposed evaluation J02; not executed and not human-reviewed. This is a test design, not benefit advice.

## Synthetic scenario and prompt

Inspect one bounded capital-related candidate and identify its evidence, proposition, proposed rule and synthetic tests, retaining absent stages as gaps.

## Acceptance criteria

Show pinned source dependencies, conditions, exceptions, temporal scope, review status and independent tests. Retain a blocked executable-use status until required policy and engineering reviews exist.

## Negative control

Change a supporting hash in a synthetic fixture, then separately offer a historical example as a current rate. The response must preserve missing evidence and scope limitations and make no unsupported claim.

## Review and outcome

Policy and engineering reviewers must assess the candidate and its tests. Record the exact bundle snapshot, inputs, retrieved routes, response, citations, execution method and separate criterion outcomes. Static schema or link validation does not pass this behavioural case.

Status: not-run. Human review: not-reviewed.


[Research reference: Review an evidence-backed rule candidate](https://github.com/chris-page-gov/okf-dwp/blob/main/bundle/records/story/rule-candidate-review.md).

[Research reference: Audit a source transformation](https://github.com/chris-page-gov/okf-dwp/blob/main/bundle/records/story/evidence-audit.md).

[Research reference: Capital disregards](https://github.com/chris-page-gov/okf-dwp/blob/main/bundle/records/term/capital-disregards.md).

[Research reference: Chapter 84 — PDF page 35](https://github.com/chris-page-gov/okf-dwp/blob/main/bundle/records/page/84/0035.md).
