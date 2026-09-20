# Team handover: 20 September 2026

**For the meeting on Monday 21 September.** This is an independent experimental
publication. It is not official DWP guidance, a benefits calculator or an
individual entitlement service.

## What the team can use now

The published baseline is [DWP PR 10](https://github.com/chris-page-gov/okf-dwp/pull/10),
merged as `5dab65d2ad21138c47e2ea364e5f74805b4e141f`, and
[Explorer PR 125](https://github.com/chris-page-gov/okf-explorer/pull/125), merged
as `8a38d4bfe07a6797deacc148a2859911d8e2a68e`. The
[DWP main-branch validation](https://github.com/chris-page-gov/okf-dwp/actions/runs/35471049668)
passed. Its source inventories, generated outputs, question replays, privacy
controls and 147 Python tests are reproducible from the repository.

- [Five-minute demonstration](compact-evidence-demo.md): exact replay links,
  source inspection, gaps and the read-only AI tool instructions.
- [Forty staff evidence packs](../evaluation/staff-review/README.md): the supplied
  40 question occurrences, including one repeated wording, with 42 shared source
  excerpts and review checklists. Original questions are retained exactly.
- [Verified DMG Reader](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F0c59f476602a49d4293e46112a0ca1ebf1486ff0%2Ffull-dmg%2Fokf-review-context.json#overview):
  benefit, circumstance and topic filters, relationships and source/capture date
  distinctions. Its [published browser observation](../validation/navigation/browser/public/README.md)
  records exact application and corpus identities.
- [Human evidence reader](https://ask-okf.crpage.chatgpt.site/review/): request
  a small catalogue and read exact evidence progressively. Source identity is
  checked on replay; a replay link does not store an AI conversation.
- [Actual Claude trials](../evaluation/answer-review/README.md) and
  [seven verified compact-tool calls](../validation/compact-client/README.md).
  Failed trials are retained alongside successful mechanical checks.

The captured corpus contains 331 DMG PDFs and 182 ADM PDFs: 19,090 pages in
total. Ask OKF searches both captured manuals. The baseline Reader projection
contains DMG; the combined Reader is active work below.

## What remains incomplete, precisely

The 43 full-corpus evaluation cases still report **insufficient**. More captured
pages and a working tool interface do not establish complete answers. The
preserved custody example has a narrower, declared legacy-DMG evidence profile;
its sufficiency does not transfer to the broader corpus or establish current law.

“Broader semantic modelling” means two specific unfinished deliverables:

1. **DWP-BL-005:** neutral benefit and variant concepts, source-backed definitions,
   meaningful relationships, aliases, confusions and qualifiers across the
   supplied question families. Literal mention tags are not these relationships.
2. **DWP-BL-007:** task-specific evidence requirements and paths, including
   conditions, exceptions, legal references, dates and explicitly missing evidence.

The old aggregate `needs_domain_review` label obscured unfinished implementation.
The [work-package ledger](backlog-work-packages.md) now separates delivery from
independent review and external permission. Implementation can proceed as clearly
unreviewed work; that does not imply specialist acceptance.

The live compact reader also has an unresolved hosting-console issue: functional
journeys pass, but host-injected code and a Firefox cookie warning fail the strict
console checks. See BL023. ChatGPT Voice and the room PA have not been rehearsed.

## Work proceeding in dependency order

| Order | Deliverable | Backlog items | Completion evidence required |
| --- | --- | --- | --- |
| 1 | Supplied-question persona, journey and requirement matrix | BL001 | Every occurrence accounted for; projected personas labelled; ambiguity and negative cases explicit |
| 2 | Neutral semantic concepts and relationships | BL005 | Exact source locators, compatible generated graph, meaningful before/after retrieval and traversal checks |
| 3 | Official legal identities and bounded tribunal discovery | BL006, BL013 | Exact queries, sources, dates and unresolved provision/version/applicability gaps |
| 4 | Executable evidence profiles and question evaluation | BL007 | All 39 distinct questions and both duplicate occurrences; missing requirements remain visible |
| 5 | Fixed-evidence claim-level trials | BL010, BL018 | Actual fixed inputs and model outputs, literal checks, independent review records and honest usage accounting |
| 6 | Combined DMG/ADM Reader and usability checks | BL024, BL019 | Both-manual source/semantic routes, facet parity, bounded browser and keyboard observations |
| 7 | Source drift checks and supported hosting repair | BL020, BL023 | Additive change report; exact deployment checked without weakening security controls |

Parallel research and producers may proceed where they do not depend on unfinished
inputs. Their integration and publication still follow these dependencies. The
completed BL004/008/009 baseline is preserved and tested, not rewritten. BL011,
BL017, BL021 and BL022 continue to apply to every delivery.

CPAG substantive content remains subject to its separate rights gate (BL012).
Actual user research, specialist acceptance and the room rehearsal require people
or facilities; they are not replaced by agent agreement. P2 operational journeys,
the benefits engine, calculators and CASA remain outside this run's implementation.

## How to follow progress

Use the [backlog](backlog.md), [delivery and acceptance ledger](backlog-work-packages.md),
[current work log](work-log-2026-09-20.md) and [changelog](../CHANGELOG.md).
Only a merged change with its named checks establishes a delivered increment.
An active branch, an agent assignment or a proposal is not a completion claim.
This dated handover describes its baseline; later increments have separate evidence.

Private correspondence is ignored and uncommitted. Local browser logs and research
scratch files are not part of this handover. No new messages have been sent to staff.
