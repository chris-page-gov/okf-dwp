# Logical-unit implementation work log

Started 22 September 2026 following the owner's explicit unattended implementation
request. The earlier Monday deadline and paused heartbeat remain historical.

## Starting state and ownership

DWP main: `82bd0a18e9941752798e5f4446eaa8bfb8b46936`.
Explorer main: `74e29f551776b27b08bfe3bacd774282f0408ffd`.
Both changes use isolated `codex/logical-evidence-units` branches.

| Owner | Exclusive implementation area | Initial state |
| --- | --- | --- |
| Producer agent | DWP segmentation producer, tests and `logical-units/` | In progress |
| Source agent | `domain-profile/logical-units/` and independent source fixtures | In progress |
| Explorer agent | Reusable unit/corpus v2 support, dependency loading, UI and tests | In progress |
| Integrator | DWP logical runtime/Reader, evaluation, contracts, documentation, backlog and reviewed PRs | In progress |

The source/page and earlier bundle projections remain unchanged. No new source
acquisition or model-provider calls are required to start. Private `.email.md`
and unrelated research remain outside this change. Root Git checks found no
competing feature writer; existing unrelated PRs are preserved.

## Decisions

- Add new unit identities and projections instead of redefining old page IDs.
- Keep source segmentation status distinct from semantic and specialist review.
- Preserve old corpus v1 validation; v2 separates physical-page and unit counts.
- Keep aggregate literal hashes separate from exact fragment/span hashes.
- Load only bounded, hash-bound declared dependencies. Requirements do not
  become hidden retrieval seeds.
- Publish a new service default only after meaningful source, retrieval,
  qualification, delivery and live checks justify it.

Implementation checkpoints, failures and measured outcomes will be appended as
they occur. An implementation package is not complete merely because its design
is recorded here.

## Source and implementation checkpoint

- Full source producer: 513 documents, 19,090 pages, 49,680 unit records and
  35,143,443 extracted bytes accounted exactly; no unassigned source bytes.
- The 46 authored excerpts cover 42,864 source bytes in six documents, including
  18 cross-page excerpts. The other 49,634 units remain uncertain machine
  candidates. These are different review denominators.
- Source authoring includes 28 scoped relationship proposals, two new neutral
  concepts, five task profiles and eight explicitly unresolved references.
- Producer: 19 controls pass. Independent source fixtures: 12 controls pass,
  including 43 qualification/example checks and a rehashed missing-footnote
  rejection. Every unit passes the new consumer shape and fragment-hash checks.
- The new corpus and indexed Reader have been generated from the same units;
  their final consumer and publication checks are still in progress.

## Retained integration failures and corrections

1. The first generated catalogue became stale while the source reviewer corrected
   fixture keys and spans. The integration build refused the mismatch. Final
   source input was rebuilt and frozen before the comparison resumed.
2. The [first allocation failure](../validation/logical-context/initial-allocation-failure/README.md)
   exposed a context authority mismatch: model-derived assertions had used the
   publication vocabulary class `editorial`. The producer now uses the existing
   context class `model-assisted`. The engine's governance check was preserved.
3. A natural temporary-care phrase did not resolve its existing concept. An
   explicit source-backed alias addition is being tested; the corpus does not
   silently infer permanent residence from generic care-home wording.
4. Peer review required explicit proposal-specific scope, cross-document
   references, bounded decompression and source recomputation before admission.
   These are implemented; final regression and publication results follow below.

No failed run has been represented as successful. No legal answer, specialist
acceptance, model-quality improvement or new public service default is claimed.

5. Actual browser loading initially refused the endpoint index: 100,507 entries
   exceeded the existing 100,000-entry safety bound because every unit duplicated
   its PDF resource. The Reader now shares one resource per source PDF, preserving
   unit-specific page spans. The consumer bound was not raised. Superseded
   unpublished generated resources were preserved in the local temporary archive;
   none belonged to a frozen release. Empty-source PDFs remain in the catalogue.
6. Peer review added source-document owner consistency and guarded temporary-care
   alias authoring. All 11 context/Reader tests and 12 source tests then passed.
   The new resource-census regression is being added before final verification.

## Final local checks and browser observation

- Completed the 19 producer, 12 independent source and 14 Reader/context controls.
  Reader census: 50,524 records, 513 unique resources, 51,884 endpoint labels,
  69,163 search tokens and 2,734,358 uncapped postings.
- Actual browser Search found a second inherited bound mismatch: the producer
  declared total records (50,524) as the maximum postings for a token. It now
  reports the actual 49,635 maximum and rejects future overflow. No postings were
  removed and no consumer bound was weakened.
- Independent review strengthened the evaluation itself: exact four-module
  allowlist and immutable Git blobs before execution; actual serialised bytes,
  node/edge/path bounds, fragment integrity, bounded archive decoding and
  exclusive observation-directory creation.
- The final 184-assembly comparison and seven controls pass; 20 focused packages
  and the exact evaluator are retained. Preliminary observations remain in
  `preliminary-run/` and `pre-search-run/`; they are not the final build receipt.
- Browser UI and actual read-only WebMCP calls returned the same PC-abroad context
  ID. The gateway unit displays both complete examples across PDF pages 8–9,
  exact spans and hashes; the UI shows source references and support dependencies.
  Insufficiency, unresolved references, candidate truncation and byte omissions
  remain visible. No external model answered this test.
- At 32 KiB every focused unit case retains zero evidence. At 512 KiB all 24
  new focused paths are retained; this does not establish complete legal scope
  or migrate all older profiles. These limits are explicit backlog packages.
- `.email.md` remains ignored and untracked. Frozen source, pilot, full-DMG and
  combined projections remain unchanged. Exact public CI and deployment verification are recorded in the
  [DWP PR handover](https://github.com/chris-page-gov/okf-dwp/pull/28), separately
  from the checked-in local observation.

- Full DWP Python regression suite: **578 tests passed**, including expected negative
  CLI controls. Canonical repository contracts, private-input check and exact
  4,900-file logical-context rebuild pass. The [local browser observation](../validation/logical-context/browser-local.json)
  records separate source/app bindings; it is not a public deployment receipt.

- Final independent editorial review corrected three claims before publication:
  machine candidates are not all complete passages; the care-home profile keeps
  temporary/permanent alternatives; the ADM memo is an unresolved reference,
  not a resolved graph destination. These corrections do not change the source
  or evaluated projection.

- Delivery PRs: [DWP 28](https://github.com/chris-page-gov/okf-dwp/pull/28)
  and [Explorer 140](https://github.com/chris-page-gov/okf-explorer/pull/140).
  The pinned DWP Reader source is `adfa7137d3b24033d7265123c739a9ffcfb06584`;
  later documentation corrections preserve its unit and context bytes. Exact
  merge/deployment observations belong to the PR handover, not an inferred
  deployment status from this source document.
- Updated the portable methodology and retrospective: establish source-bound
  logical units before semantic generation; keep boundary accuracy, dependency
  completeness, source census and answer quality as separate checks.

## Public Reader verification and CI correction

- [Explorer PR 140](https://github.com/chris-page-gov/okf-explorer/pull/140) merged
  as `69d38b1c3c17939236f880e391746bf794623dda`; all required head checks passed.
  [Pages run 35741046500](https://github.com/chris-page-gov/okf-explorer/actions/runs/35741046500)
  rebuilt and publicly verified that exact merge.
- The [separate DWP public observation](../validation/logical-context/public-adfa7137/browser-observation.json)
  verified 50,524 Reader records, 513 sources, seven Search results for 077001,
  complete cross-page examples and directed support. The public UI JSON equals
  the actual WebMCP build result; explain returns the same context ID. The
  440,273-byte package remains insufficient, with 18 records and eight edges.
  Exact public HTTP hashes and the Explorer deployment receipt are retained
  beside that observation. Old local warnings are identified separately.
- [DWP CI 35740413305](https://github.com/chris-page-gov/okf-dwp/actions/runs/35740413305)
  caught unregistered work-package evidence: child entries referenced new files
  missing from their parent evidence lists. Registered those same existing files
  at the parent level; the validator was not weakened. Moved its cheap check
  before expensive corpus validation so future errors fail promptly. The failed
  run remains available; successful unit/source checks are not represented as
  an overall successful CI run.
