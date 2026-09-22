# Product and evaluation backlog

[What changed](../CHANGELOG.md) · [Current work log](monday-delivery-work-log.md) · [Retrospective](retrospective.md) · [Portable method](methodology.md)

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

The original work was incomplete; it was not recorded as done. The previous single
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

The 20 September increment now supplies bounded implementation for BL001/005/006/007/013/020.
Their bounded delivery packages link actual outputs. Separate agent work packages
now name remaining domain expansion, legal body acquisition, evidence closure and
a controlled model benchmark; these are unfinished implementation, not blocked
behind human review. Independent acceptance remains a separate work package.
The 203 named task obligations are in [the profile register](../evaluation/semantic-expansion/profiles.json).
Do not read a delivered compiler or a denser graph as complete domain modelling.

The [qualification-retention work package](backlog-work-packages.md#dwp-bl-007-broader-semantic-modelling-task-specific-evidence-profiles)
records the preceding 15-support-dependency increment: eight for the initial household
group, five for housing costs and two for temporary residence. Staff 012 and 013
require the household and housing-cost paths. The
[component review](carehome-component-dependency-review.md) motivated a separate
no-partner and severe-disability overview increment. The original
[joint comparison](../validation/qualification-context/2026-09-21/README.md)
now passes 320 assemblies and replay: the final pair retains all 177 known candidate
occurrences and 433 declared path occurrences at both tested budgets, including
seven of seven household pages for Staff 012 and 013. This bounded retention
package is recorded complete. The [disability increment](disability-addition-qualification-review.md)
is also implemented and independently reviewed: 29 dependencies in a 903-record
index, with a [separate frozen comparison](../validation/disability-context/2026-09-21/README.md).
All 497 declared path occurrences survive 512 KiB; only 407 survive 256 KiB,
despite unchanged 177/177 candidate overlap. Its bounded implementation is
recorded complete. The [partner extension](partner-addition-qualification-review.md)
is now also implemented and independently source-reviewed: 39 dependencies,
585/585 retained path occurrences at 512 KiB and 449/585 at 256 KiB. Its source,
combined projection and [separate comparison](../validation/partner-context/2026-09-21/README.md)
are distinct from public delivery. The conditional ignored-person and
normal-residence extension is now authored and independently source-reviewed:
913 records, 53 concepts and 61 support dependencies. Its larger declared closure
exceeds even 512 KiB; this measured retention regression is tracked separately
from its completed source modelling. See the [source review](ignored-person-qualification-review.md)
and [separate comparison](../validation/ignored-person-context/2026-09-21/README.md).
Exact-version publication and public observation retain a separate in-progress
package: the qualification Reader has a new public Chrome receipt, while the
later source increments retain their own release checks. Service 0.6.0 has since passed its separate 121-request public SDK observation; the retained reader has a distinct public publication gate.
All 43 evidence-closure checks and
all 203 total obligations remain open. At 64 KiB, Staff 012 correctly refuses
because its obligation metadata does not fit; a small refusal does not erase
the underlying task requirements.

The [paired direct-v4 results](../validation/model-comparison/household-direct-v4/README.md)
now include two mechanically accepted care-home answers after both empty controls.
The independent agent critique identifies qualification omissions and an overstated
gap in one response. BL010 remains open for qualification repair and human assessment;
a completed pair does not imply complete legal answers or a model ranking.

**DWP-BL-008.client-connection** remains `in_progress`. Service 0.6.1 is
published and [its new SDK observation](../validation/compact-delivery/v0.6.1/README.md)
passes 11 cases in 121 requests. After refresh, the ChatGPT connection advertises
all three tools and the corrected question pattern. The same native control
rejected before the patch now succeeds. The exact Staff 012 question also
reaches the service, but its deliberately small 16 KiB budget returns zero
records and an explicit byte-budget omission. These [client observations](../validation/client-connection/2026-09-21/README.md)
establish neither useful answerability nor complete client integration.

The existing Codex task still exposes only the full-package tool. A new
conversation's compact catalogue and exact-read journey, and tool propagation
into the intended Data Agent, remain unaccepted. The [connection guide](chatgpt-connection.md)
preserves the fixed comparison question and budget. Neither installed metadata
nor the SDK pass establishes Data Agent or Voice acceptance.

## Abroad review and wider semantic follow-up

The [21 September audit](abroad-semantic-audit.md) traces the reported five irrelevant pages to the preserved 19 September pre-fix result, then tests the published source and engine. The exact question now resolves abroad, but overseas paraphrases, disconnected international concepts, incomplete passage continuations and broad profile activation expose remaining gaps. The machine register names separate connectivity, qualification, cross-benefit coverage, task-discrimination and historical-version competition packages; none declares the broader domain complete.

## Logical retrieval units — 22 September 2026

The owner has authorised implementation of the reviewed RQ02 correction.
[Logical evidence units](logical-evidence-units.md) and the
[implementation log](logical-units-work-log.md) track three active packages:
`DWP-BL-005.logical-units`, `DWP-BL-007.unit-qualification` and
`DWP-BL-009.logical-corpus`. Source capture, semantic coverage and specialist
acceptance remain separate. Existing page-based releases and service defaults
retain their recorded scope until new checks justify publication.

## Current register

| ID | Priority | Work | Status | Depends on |
| --- | --- | --- | --- | --- |
| DWP-BL-001 | P0 | Extensive persona, journey and question review | `needs_domain_review` | — |
| DWP-BL-002 | P2 | Benefits engine feasibility | `not_started` | DWP-BL-001, DWP-BL-006, DWP-BL-007 |
| DWP-BL-003 | P2 | Application and change-of-circumstances journeys | `not_started` | DWP-BL-001, DWP-BL-006, DWP-BL-007 |
| DWP-BL-004 | P0 | Frozen full DMG and ADM capture | `recorded_complete` | — |
| DWP-BL-005 | P0 | Broader semantic modelling: neutral domain concepts and relationships | `in_progress` | DWP-BL-001, DWP-BL-004 |
| DWP-BL-006 | P0 | Legislation, regulations and case-law reconciliation | `in_progress` | DWP-BL-001 |
| DWP-BL-007 | P0 | Broader semantic modelling: task-specific evidence profiles | `in_progress` | DWP-BL-001, DWP-BL-005, DWP-BL-006 |
| DWP-BL-008 | P0 | Progressive evidence manifests and exact reads | `in_progress` | DWP-BL-004 |
| DWP-BL-009 | P0 | Conceptual classification and DMG Reader navigation | `in_progress` | DWP-BL-004 |
| DWP-BL-010 | P0 | Fixed-evidence claim-level model trials | `in_progress` | DWP-BL-004 |
| DWP-BL-011 | P1 | Source dates and provenance presentation | `recorded_complete` | — |
| DWP-BL-012 | P1 | CPAG substantive content access | `needs_external_permission` | — |
| DWP-BL-013 | P1 | Tribunal decision discovery | `needs_domain_review` | DWP-BL-001, DWP-BL-006 |
| DWP-BL-014 | P2 | Calculator comparison | `not_started` | DWP-BL-001, DWP-BL-007 |
| DWP-BL-015 | P2 | CASA framework assessment | `not_started` | DWP-BL-003 |
| DWP-BL-016 | P0 | ChatGPT Voice and room audio rehearsal | `in_progress` | — |
| DWP-BL-017 | P1 | Portable discovery-first departmental workflow | `recorded_complete` | — |
| DWP-BL-018 | P1 | Fair model and affordability benchmark | `in_progress` | DWP-BL-007, DWP-BL-010 |
| DWP-BL-019 | P1 | Broader accessibility and cross-browser review | `in_progress` | DWP-BL-009 |
| DWP-BL-020 | P1 | Source refresh and drift process | `needs_domain_review` | DWP-BL-004, DWP-BL-006 |
| DWP-BL-021 | P0 | Canonical contracts and protected publication | `recorded_complete` | — |
| DWP-BL-022 | P1 | Retrospective and visible multi-agent change history | `recorded_complete` | — |
| DWP-BL-023 | P1 | Hosting and Content Security Policy integration | `in_progress` | DWP-BL-008 |
| DWP-BL-024 | P1 | ADM Reader and cross-manual navigation | `recorded_complete` | DWP-BL-004, DWP-BL-009 |

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
and ADM. The preserved baseline human Reader contains DMG records. **DWP-BL-024** now
supplies an additive [combined Reader](combined-reader.md), with source-family and
date distinctions and locally verified filter parity across Reader/Graph/Timeline.
The [earlier staff-source public observation](../validation/combined-reader/public/README.md)
and [household-source public observation](household-reader-public-verification.md)
retain their exact source and application versions. Neither attests the later
qualification candidate. Literal mentions are not legal assertions.
The [published DMG navigation check](../validation/navigation/browser/public/README.md)
is separate from the unresolved service hosting-console issue.

The [logged sources](future-sources.md) retain the tribunal, calculators and
CASA requests. CPAG remains separately constrained. The 24 September content
freeze and 30 September seminar do not authorise an unsupported completeness or
Voice claim.

### DWP-BL-023: supported hosting follow-up

Cloudflare documents [`Cache-Control: no-transform`](https://developers.cloudflare.com/cloudflare-challenges/challenge-types/javascript-detections/#if-your-origin-sends-a-no-transform-header)
as preventing JavaScript Detections injection; its detection result then becomes
`missing`. The later service preserves `no-store` and its Content Security Policy
while using `no-transform`. The [actual 0.5.0 observation](../validation/compact-delivery/v0.5.0/README.md)
passed all three functional browser journeys and the Chrome/WebKit strict console
checks. Firefox retained two hosting-cookie warnings, so its strict check remains
failed. Historical-profile journeys were not run for 0.5.0. Preserve the
[earlier public-browser failures](../validation/compact-delivery/browser/README.md)
and keep this work item open for the unresolved hosting acceptance.

## Recheck the register

Run `uv run --locked python scripts/check_backlog.py`. It checks IDs, declared
statuses, dependency cycles, public evidence paths and consistency of this table
with the machine register. It also checks work-package evidence and rejects a
completed parent that conceals unfinished work. Regenerate the detailed ledger
with `uv run --locked python scripts/build_backlog_work_packages.py`; validate it
with the same command followed by `--check`. Regression controls run with
`uv run --locked python scripts/test_backlog.py`. These are structural checks;
they do not decide whether a domain or acceptance review has passed.

## Logical-unit implementation — 22 September 2026

The [logical-unit guide](logical-evidence-units.md) records the completed source
producer, scoped qualification fixtures and reusable corpus v2 integration.
These are bounded implementation packages, not completion of broader semantic
modelling. Separate packages now name the 49,634 uncertain boundaries, remaining
staff-profile migration and compact-delivery admission. The five small-budget
focused packages currently retain no source evidence; the larger packages retain
24 of 24 declared paths and remain insufficient.
