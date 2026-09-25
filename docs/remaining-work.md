# Remaining work and next priorities

Status reviewed on 25 September 2026. This is the current short guide to the
work queue; the [backlog register](backlog-work-packages.md) retains the detailed
tasks and evidence. Older reports retain the results for their own versions.

## What works now

- The declared **Decision makers' guide (DMG)** and **Advice for decision making
  (ADM)** capture contains 513 PDFs and 19,090 pages. These are DWP staff manuals,
  not legislation or a continually updated service.
- Search and Ask OKF can use the source-led corpus. The capital repair connects
  previously missed passages to source-bound discovery routes and dependencies.
- The Evidence workbench opens all 40 retained staff-question cases. It shows
  source passages, relationships, why evidence was selected and what is missing.
  Large retained packages can be reconstructed from checked, small downloads.
- The optional interaction and calculation-inspection views are implemented.
  The [Edge sidebar route](workbench-sidebar-demo.md) has been demonstrated.
  Calculation inspection explains proposed dependencies; it does not calculate
  an award.

**All 40 packages still say `insufficient`.** This means the system has not
established that every required condition, exception and applicable source is
present. It does not mean that nothing useful was retrieved. Conversely, a
working page or successful download does not make an answer complete.

## Recommended order

| Order | Work and backlog IDs | What success would look like | Who can do it |
| --- | --- | --- | --- |
| 1 | Next after the service/sidebar release: [passage-boundary workbench design](https://github.com/chris-page-gov/okf-explorer/pull/151), [Explorer #150](https://github.com/chris-page-gov/okf-explorer/issues/150) and [DWP #42](https://github.com/chris-page-gov/okf-dwp/issues/42). **BL007.remaining-structural-review** | First make all 28 known candidates inspectable against synchronised PDF, extraction and before/after passages. Later phases validate isolated corrections, nine-chapter impact, identifier migration and all 40 equal-budget question replays, including held-out controls. | Agent prepares generic Explorer capability and DWP fixtures; independent reviewers assess structure. |
| 2 | Repair the known question failures: capital transfer wording and the new Universal Credit (UC) disabled-child case. Verify the dated legal source before classifying the UC dependency. **BL005, BL006, BL007** | The intended passages and conditional dependencies are selected for fixed positive cases and new wordings, while negative cases stay excluded. Gaps and uncertain applicability remain explicit. | Agent prepares and tests; benefits specialist assesses meaning. |
| 3 | Extend concepts and complete declared evidence requirements across the question set. **BL005, BL006, BL007, BL009** | Benefit variants, dates, territory, household roles, definitions and exceptions have traceable relationships. Eleven capital dependency groups and the 43 original evidence-closure obligations are examined rather than hidden by larger retrieval counts. | Agent prepares scoped increments; specialist reviews applicability. |
| 4 | Measure selection, package size and delivery separately; restore the original acceptance cases in the newer corpus. **BL007, BL008** | Whole relevant passages and qualifications survive bounded assembly; exact small reads reconstruct the selected package. The original imprisonment/hospital checks remain visible. The intended remote client is tested against the admitted source version. | Agent, with account-specific checks where needed. |
| 5 | Evaluate answers after evidence improves. **BL010, BL018** | A fixed-source comparison checks each claim and qualification against delivered evidence, with independent review. Actual model identity and usage are recorded before claiming accuracy or affordability. | Agent prepares; specialist reviews. Further answer calls require an agreed usage budget. |

The boundary-review increment is scheduled without restarting acquisition or
running all 40 questions through more expensive models. An optional defect
detector comparison requires an agreed model-call budget first: 12 varied
cases, followed by 24 fresh cases only if the fixed criteria pass. The original notional-capital
question is repaired, but transfer-to-another-person wording still misses.
The [UC follow-up](uc-disabled-child-supersession-follow-up.md) selected one
relevant passage but missed required conditional guidance. Both are measurable
failures with existing source leads.

The amendment experiment is promising but **not merge-ready**: its retained
census changes 134 documents and performs no new context assembly. Its small
source-case passes do not establish that the wider changes improve retrieval.
See the [branch review](unmerged-work-review-2026-09-24.md) before resuming it.

## What still needs people or a particular environment

- **Benefits specialists:** review legal meaning, exceptions, effective dates
  and source completeness. The 203 original obligations include 43 source-closure
  requirements and 40 each for applicability, legal version, independent review
  and question scope. Engineering cannot mark these accepted on its own.
- **Presenter:** rehearse the intended ChatGPT account, microphone, MacBook
  sound, projection and room PA before the **30 September** conference. A text
  sidebar demonstration does not prove Voice or room-audio operation. **BL016**.
- **Representative users:** check keyboard, screen-reader and other assistive
  technology journeys. Resolve the separately recorded Firefox hosting result.
  **BL019, BL023**.
- **Rights and maintenance decisions:** CPAG substantive reuse remains a
  separate rights question. A fresh source snapshot must be explicitly scoped
  and compared with the frozen evidence. **BL012, BL020**.

The benefits engine, application/change-of-circumstances journeys, external
calculator comparison and CASA interface framework remain later work
(**BL002, BL003, BL014, BL015**). They depend on established evidence and service
requirements; they are not implied by the inspection prototype.

## Repository housekeeping

PR 23 is closed as superseded; its history and branch remain available. The
reviewed implementation is already on `main`. Local research, failed experiments,
private correspondence and older source snapshots are preserved. The amendment
branch remains separate. Documentation and backlog corrections from
[PR 40](https://github.com/chris-page-gov/okf-dwp/pull/40) are merged and published.
The service/sidebar follow-up and scheduled boundary-review package are in
[PR 41](https://github.com/chris-page-gov/okf-dwp/pull/41); its checks and Pages
publication remain separate release gates.

Future progress should update the authored [backlog JSON](../evaluation/backlog.json),
regenerate its work-package page and record the exact tests and release in the
changelog. A delivered implementation, a passed test, a public observation and
specialist acceptance are separate milestones.
