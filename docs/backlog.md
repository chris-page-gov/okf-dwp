# Product and evaluation backlog

[What changed](../CHANGELOG.md) · [Current work log](work-log-2026-09-20.md) · [Retrospective](retrospective.md) · [Portable method](methodology.md)

This register keeps stable IDs for the owner’s original ideas and later findings.
**DWP-BL-001, DWP-BL-002 and DWP-BL-003 preserve the original three backlog items.**
Dates, exact dependencies and acceptance checks are in the
[machine-readable register](../evaluation/backlog.json). IDs are never reused.

`recorded_complete` means a named bounded result has evidence. `in_progress`
is not a release claim. `needs_domain_review` and `needs_external_permission`
name the missing decision; `not_started` records work that has not been done.
P0 means the next demonstration or evidence-quality priority, not an instruction
to bypass source, rights or review boundaries.

## What broader semantic modelling means

This work was incomplete; it was not recorded as done. The previous single
`needs_domain_review` label hid unfinished implementation behind a review gate.
**BL005** covers neutral concepts, variants and source-backed relationships.
**BL007** covers task-specific evidence requirements, routes, exceptions and
explicit gaps. BL001 supplies the question/persona scope; BL006 supplies legal
reference reconciliation. BL009 mention classifications do not complete either
semantic milestone.

The [work-package register](backlog-work-packages.md) now separates delivery from
independent review, external permission and live observation. A pending human
review does not prevent implementation of source-backed, clearly unreviewed
proposals. A completed implementation does not close the human review.

See the [team handover](team-handover-2026-09-20.md) for the published baseline
and the ordered work continuing towards Monday 21 September.

## Current register

| ID | Priority | Work | Status | Depends on |
| --- | --- | --- | --- | --- |
| DWP-BL-001 | P0 | Extensive persona, journey and question review | `in_progress` | — |
| DWP-BL-002 | P2 | Benefits engine feasibility | `not_started` | DWP-BL-001, DWP-BL-006, DWP-BL-007 |
| DWP-BL-003 | P2 | Application and change-of-circumstances journeys | `not_started` | DWP-BL-001, DWP-BL-006, DWP-BL-007 |
| DWP-BL-004 | P0 | Frozen full DMG and ADM capture | `recorded_complete` | — |
| DWP-BL-005 | P0 | Broader semantic modelling: neutral domain concepts and relationships | `in_progress` | DWP-BL-001, DWP-BL-004 |
| DWP-BL-006 | P0 | Legislation, regulations and case-law reconciliation | `in_progress` | DWP-BL-001 |
| DWP-BL-007 | P0 | Broader semantic modelling: task-specific evidence profiles | `in_progress` | DWP-BL-001, DWP-BL-005, DWP-BL-006 |
| DWP-BL-008 | P0 | Progressive evidence manifests and exact reads | `recorded_complete` | DWP-BL-004 |
| DWP-BL-009 | P0 | Conceptual classification and DMG Reader navigation | `recorded_complete` | DWP-BL-004 |
| DWP-BL-010 | P0 | Fixed-evidence claim-level model trials | `in_progress` | DWP-BL-004 |
| DWP-BL-011 | P1 | Source dates and provenance presentation | `recorded_complete` | — |
| DWP-BL-012 | P1 | CPAG substantive content access | `needs_external_permission` | — |
| DWP-BL-013 | P1 | Tribunal decision discovery | `in_progress` | DWP-BL-001, DWP-BL-006 |
| DWP-BL-014 | P2 | Calculator comparison | `not_started` | DWP-BL-001, DWP-BL-007 |
| DWP-BL-015 | P2 | CASA framework assessment | `not_started` | DWP-BL-003 |
| DWP-BL-016 | P0 | ChatGPT Voice and room audio rehearsal | `not_started` | — |
| DWP-BL-017 | P1 | Portable discovery-first departmental workflow | `recorded_complete` | — |
| DWP-BL-018 | P1 | Fair model and affordability benchmark | `not_started` | DWP-BL-007, DWP-BL-010 |
| DWP-BL-019 | P1 | Broader accessibility and cross-browser review | `not_started` | DWP-BL-009 |
| DWP-BL-020 | P1 | Source refresh and drift process | `not_started` | DWP-BL-004, DWP-BL-006 |
| DWP-BL-021 | P0 | Canonical contracts and protected publication | `recorded_complete` | — |
| DWP-BL-022 | P1 | Retrospective and visible multi-agent change history | `recorded_complete` | — |
| DWP-BL-023 | P1 | Hosting and Content Security Policy integration | `in_progress` | DWP-BL-008 |
| DWP-BL-024 | P1 | ADM Reader and cross-manual navigation | `in_progress` | DWP-BL-004, DWP-BL-009 |

## Acceptance before closure

Each item has an owner role, explicit acceptance checks and evidence paths in
[the register](../evaluation/backlog.json). A change from `in_progress` to
`recorded_complete` needs the completed check or observation, the exact source
and consumer versions, and any remaining limits. Model agreement does not close
a domain-review gate. Keep partial results and failed attempts.

The recorded delivery and navigation milestones have scoped receipts: public
service/SDK, local Claude, and exact local and published DMG Explorer.
Service-browser deployment checks remain separately recorded: the historical-profile
functional assertions passed, while all nine version 6 tests and all twelve
version 7 tests failed their strict console gates because of hosting errors.
See the [earlier result](../validation/compact-delivery/browser/public/run-summary.json)
and [corrected-service result](../validation/compact-delivery/v0.3.1/browser/historical/run-summary.json).
**DWP-BL-023** records the unresolved integration; those milestones do not
close domain review. Independent answer
and applicability review remain separate. Legislation integration must research
provision/version identities before adding legal implications. A benefits engine
and operational application/change journeys depend on those reviews.

**DWP-BL-009 has a deliberately narrower Reader scope.** Its classification audit
accounts for both captured manuals, and Ask OKF already retrieves from both DMG
and ADM. The current human Reader projection contains DMG records. **DWP-BL-024**
tracks an additive ADM or combined Reader, with source-family and date distinctions,
filter parity across Reader/Graph/Timeline and exact public-browser verification.
This remains unfinished; literal mentions must not become legal assertions.
The [published DMG navigation check](../validation/navigation/browser/public/README.md)
is separate from the unresolved service hosting-console issue.

The [logged sources](future-sources.md) retain the tribunal, calculators and
CASA requests. CPAG remains separately constrained. The 24 September content
freeze and 30 September seminar do not authorise an unsupported completeness or
Voice claim.

### DWP-BL-023: supported hosting follow-up

Cloudflare documents [`Cache-Control: no-transform`](https://developers.cloudflare.com/cloudflare-challenges/challenge-types/javascript-detections/#if-your-origin-sends-a-no-transform-header)
as preventing JavaScript Detections injection; its detection result then becomes
`missing`. Assess a narrow HTML-response experiment with the host maintainer,
preserving the existing `no-store` policy and Content Security Policy. This
candidate is untested: verify both functional behaviour and the strict console
gate against the exact deployment before claiming a fix. The Firefox cookie
domain error needs separate hosting assessment. Keep the
[recorded public-browser failure](../validation/compact-delivery/browser/README.md)
open until both issues are resolved and checked.

## Recheck the register

Run `uv run --locked python scripts/check_backlog.py`. It checks IDs, declared
statuses, dependency cycles, public evidence paths and consistency of this table
with the machine register. It also checks work-package evidence and rejects a
completed parent that conceals unfinished work. Regenerate the detailed ledger
with `uv run --locked python scripts/build_backlog_work_packages.py`; validate it
with the same command followed by `--check`. Regression controls run with
`uv run --locked python scripts/test_backlog.py`. These are structural checks;
they do not decide whether a domain or acceptance review has passed.
