# Passage review release — 25 September 2026

The 28-case passage workbench is published. It lets a reviewer compare a frozen
PDF, exact extracted text and proposed boundaries, inspect how a passage was
built, preview a correction and export a local suggestion. Export does not
adopt that suggestion or change any frozen evidence.

Start with the [beginner guide](../../../docs/passage-boundary-review.md).

## Released identities and observations

| Component | Exact revision or evidence |
| --- | --- |
| Explorer implementation | [PR 155](https://github.com/chris-page-gov/okf-explorer/pull/155), merge `4d76cddb152caa1f95bade1f6f1aeee2e4c5c94d` |
| DWP producer and isolated parser | [PR 44](https://github.com/chris-page-gov/okf-dwp/pull/44), merge `c971e4cdf63f8784e355621aa6e667cbc60a2d00` |
| Pinned review data | `65924955745c4ed1b8ce66252c4748902b5403ba`; manifest SHA-256 `488df312d1672270e9d458ad0944a30e07d2fc56062896ad3d9e8ca2ad0a21f2` |
| Public application | [Browser and file receipt](public/observation.json): all 34 declared application files match tree `5dda237278ebbc52a3a3140dbd3b53af82a43b9140af9a41953417fbed6dfbd1` |
| Public workflow | All 28 cases navigate and pass their default byte-preservation preview. PDF rendering and page synchronisation, parser settings, case 014's unresolved warning, case 019's successor reference table and local review export pass. No uncaught page errors. |
| Separate direct observation | [In-app browser record](public/interactive-observation.json), including PDF page 16 to 17 and the case 014/019 displays |
| DWP learning website | [Four-file byte comparison](public/dwp-learning-site.json): publication manifest, passage guide, learning path and backlog page match a clean build of `c971e4cd` |

The release directory retains the [Explorer PR checks](release/explorer-pr-validation.json),
[merged-commit checks](release/explorer-merged-validation.json) and
[Pages checks](release/explorer-pages-validation.json), plus the
[DWP PR checks](release/dwp-pr-validation.json),
[merged-commit checks](release/dwp-merged-validation.json) and
[Pages checks](release/dwp-pages-validation.json). The two dependencies PRs,
Explorer 153 and 154, are merged; superseded Dependabot PRs were closed with
explanations following the owner's approval.

The first duplicate DWP push run was cancelled and temporarily left a failed
required check. Its [original attempt](release/dwp-cancelled-duplicate-attempt.json)
and [successful rerun](release/dwp-required-validation.json) are separate. Normal
protected merging was used; branch protections were not bypassed. A duplicate
workflow should not be cancelled without checking which required commit status
it supplies.

## What is and is not complete

The reusable inspection and isolated-preview implementation is delivered.
Its local checks include 822 Vitest tests and the real 28-case fixture. The
three-engine Explorer regression suite passed. The final local Heritage
regression receipt retains 100/100 questions above its required floor and three
journeys; these are Explorer regression measures, not benefits-answer scores.

The narrowed parser was reviewed against all 513 documents and all nine
substantive chapters affected by the rejected broad proposal. It preserves
35,143,443 extracted source bytes and 75 authored units, changes 125 historical
amendments and leaves substantive chapter records unchanged. Its 54,577 units
are an isolated successor to the frozen 53,727-unit baseline. The broad
bare-Appendix rule was rejected because it split a wrapped sentence. Four-case,
then eight-case checks and held-out cross-page controls passed.

**Source acceptance remains open:** 15 named target boundaries are corrected,
12 are partial and one is unresolved. Partial cases are 003, 009, 011, 012, 015,
016, 017, 020, 023, 025, 026 and 027. Their case records expose untyped fragments,
an unreviewed internal appendix table or possible trailing paragraph markers.
Case 014's scrambled extraction does not support a confident correction.
Source bytes and explicit incompleteness remain preserved.

The equal-budget replay retains all 40 question packages and its offline hash
receipt. Selected sets change in 21 cases, ordering in 22 and paths in four.
Matched declared candidate pages and evidence requirements do not improve;
**all 40 packages remain insufficient**. There were no answer-model calls.

An isolated browser correction reports its local unit delta and source-byte
accounting. Full document/corpus after-counts and the correction's dependency,
discovery, question-package and budget effects remain `unknown` until a wider
producer replay. Previously measured producer results are labelled separately.
Neither a passed preview nor this release establishes legal answerability.

## Continue safely

1. Inspect the partial and unresolved cases in the workbench; include new,
   independently reviewed examples and genuine cross-page continuations.
2. Export source-bound suggestions, including uncertainty and rationale.
3. Review any adoption in a separate producer PR. Keep prior source, identifiers
   and snapshots; repeat structural checks and equal-budget question replay.
4. Evaluate retrieval improvement and specialist/legal acceptance separately.

`DWP-BL-007.passage-review-workbench` records this delivered increment.
`DWP-BL-007.remaining-structural-review` remains open, as do
[Explorer #150](https://github.com/chris-page-gov/okf-explorer/issues/150) and
[DWP #42](https://github.com/chris-page-gov/okf-dwp/issues/42) for the wider workflow
and source acceptance. Optional model defect-detection trials still need an
agreed call budget; none was run here.

## Reproduce

The [beginner guide](../../../docs/passage-boundary-review.md#reproduce-the-review-data)
lists locked producer and retained-replay commands. The portable
[browser runner](runner/observe-passage-workbench.mjs) records the public check;
set `PLAYWRIGHT_PACKAGE` to the existing locked Playwright installation and pass
`--explorer-commit 4d76cddb152caa1f95bade1f6f1aeee2e4c5c94d`. Pass `--output` with a new directory whose parent exists; the runner rejects
an existing directory so earlier observations cannot be overwritten. Its receipt
records the Playwright version and runner hash without a local installation path.
Public observations are version-bound, not a continuous health claim.
The [file index](files.json) records the hashes of the retained evidence and
runner; it excludes itself to avoid a circular hash.

Screenshots: [verified PDF](public/case-001-verified-pdf.png),
[unresolved extraction](public/case-014-source-boundary.png),
[successor table](public/case-019-source-boundary.png).
The [exported review](public/passage-review-case-028.json) is a local unreviewed
proposal retained to test delivery; it is not an adopted source correction.
