# Product and evaluation backlog

[What changed](../CHANGELOG.md) · [Current work log](work-log-2026-09-19.md) · [Retrospective](retrospective.md) · [Portable method](methodology.md)

This register keeps stable IDs for the owner’s original ideas and later findings.
**DWP-BL-001, DWP-BL-002 and DWP-BL-003 preserve the original three backlog items.**
Dates, exact dependencies and acceptance checks are in the
[machine-readable register](../evaluation/backlog.json). IDs are never reused.

`recorded_complete` means a named bounded result has evidence. `in_progress`
is not a release claim. `needs_domain_review` and `needs_external_permission`
name the missing decision; `not_started` records work that has not been done.
P0 means the next demonstration or evidence-quality priority, not an instruction
to bypass source, rights or review boundaries.

## Current register

| ID | Priority | Work | Status | Depends on |
| --- | --- | --- | --- | --- |
| DWP-BL-001 | P0 | Extensive persona, journey and question review | `needs_domain_review` | — |
| DWP-BL-002 | P2 | Benefits engine feasibility | `not_started` | DWP-BL-001, DWP-BL-006, DWP-BL-007 |
| DWP-BL-003 | P2 | Application and change-of-circumstances journeys | `not_started` | DWP-BL-001, DWP-BL-006, DWP-BL-007 |
| DWP-BL-004 | P0 | Frozen full DMG and ADM capture | `recorded_complete` | — |
| DWP-BL-005 | P0 | Neutral domain concepts and meaning review | `needs_domain_review` | DWP-BL-001, DWP-BL-004 |
| DWP-BL-006 | P0 | Legislation, regulations and case-law reconciliation | `not_started` | DWP-BL-001 |
| DWP-BL-007 | P0 | Task-specific evidence completeness profiles | `needs_domain_review` | DWP-BL-001, DWP-BL-005, DWP-BL-006 |
| DWP-BL-008 | P0 | Progressive evidence manifests and exact reads | `recorded_complete` | DWP-BL-004 |
| DWP-BL-009 | P0 | Whole-corpus conceptual navigation | `recorded_complete` | DWP-BL-004 |
| DWP-BL-010 | P0 | Fixed-evidence claim-level model trials | `needs_domain_review` | DWP-BL-004 |
| DWP-BL-011 | P1 | Source dates and provenance presentation | `recorded_complete` | — |
| DWP-BL-012 | P1 | CPAG substantive content access | `needs_external_permission` | — |
| DWP-BL-013 | P1 | Tribunal decision discovery | `not_started` | DWP-BL-001, DWP-BL-006 |
| DWP-BL-014 | P2 | Calculator comparison | `not_started` | DWP-BL-001, DWP-BL-007 |
| DWP-BL-015 | P2 | CASA framework assessment | `not_started` | DWP-BL-003 |
| DWP-BL-016 | P0 | ChatGPT Voice and room audio rehearsal | `not_started` | — |
| DWP-BL-017 | P1 | Portable discovery-first departmental workflow | `recorded_complete` | — |
| DWP-BL-018 | P1 | Fair model and affordability benchmark | `not_started` | DWP-BL-007, DWP-BL-010 |
| DWP-BL-019 | P1 | Broader accessibility and cross-browser review | `not_started` | DWP-BL-009 |
| DWP-BL-020 | P1 | Source refresh and drift process | `not_started` | DWP-BL-004, DWP-BL-006 |
| DWP-BL-021 | P0 | Canonical contracts and protected publication | `recorded_complete` | — |
| DWP-BL-022 | P1 | Retrospective and visible multi-agent change history | `recorded_complete` | — |

## Acceptance before closure

Each item has an owner role, explicit acceptance checks and evidence paths in
[the register](../evaluation/backlog.json). A change from `in_progress` to
`recorded_complete` needs the completed check or observation, the exact source
and consumer versions, and any remaining limits. Model agreement does not close
a domain-review gate. Keep partial results and failed attempts.

The recorded delivery and navigation milestones have scoped receipts: public
service/SDK, local Claude, and exact local Explorer. Public-browser deployment
checks remain separately recorded; those milestones do not close domain review. Independent answer
and applicability review remain separate. Legislation integration must research
provision/version identities before adding legal implications. A benefits engine
and operational application/change journeys depend on those reviews.

The [logged sources](future-sources.md) retain the tribunal, calculators and
CASA requests. CPAG remains separately constrained. The 24 September content
freeze and 30 September seminar do not authorise an unsupported completeness or
Voice claim.

## Recheck the register

Run `uv run --locked python scripts/check_backlog.py`. It checks IDs, declared
statuses, dependency cycles, public evidence paths and consistency of this table
with the machine register. Regression controls run with
`uv run --locked python scripts/test_backlog.py`. These are structural checks;
they do not decide whether a domain or acceptance review has passed.
