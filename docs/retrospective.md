# What the DWP exemplar established

**Recorded baseline: 19 September 2026.** This account describes inspectable
artefacts and observed behaviour. It does not estimate time saved, costs avoided
or future model capability. Later work has separate backlog entries and receipts.

## From a document collection to inspectable evidence

| Stage | What happened | What it did not establish |
| --- | --- | --- |
| Initial discovery | A draft domain profile, source/rights research and consumer lock preceded a 36-PDF Pension Credit exemplar | An approved, complete welfare ontology or full production assurance |
| Wider DMG | All 331 frozen PDFs and 14,743 pages were acquired; source-led proposals and navigation were generated | Every legal provision, exception or current benefit regime had been modelled |
| Separate ADM | 182 PDFs and 4,347 pages were acquired without rewriting DMG evidence | ADM and DMG were legally interchangeable |
| Ask OKF | A general deterministic context engine was added separately from Search; the custody case exercised directed evidence routing | General search had become an answer engine, or every question was answerable |
| Full-corpus questions | Forty staff-question occurrences, 39 distinct wordings and three controls were run against all nonempty captured pages | The 43 insufficient packages were 43 successful answers |
| Remote and browser delivery | SDK, raw HTTP, published Explorer and native WebMCP checks retained exact source/context identities | Every client, full model context, Voice or room audio worked |
| Governance repair | Protected-branch settings and canonical semantic/publication checks were recorded; unsupported descriptive fields were preserved separately | Configuration was perpetual assurance or model interpretation was official |

Evidence: [source acquisition](adm-acquisition.md), [question results](../evaluation/staff-questions/results.md),
[Ask design and acceptance](context-assembly-demo.md), [public client observations](remote-mcp-demo.md),
[repository governance](repository-governance.md) and [publication boundaries](../okf.publication.json).

The combined inventory contains **513 PDFs and 19,090 pages**. Of those,
18,197 pages have extracted text and 893 do not. These are separate denominators
from concepts, assertions, questions and answerable tasks.

## Findings that changed the design

### 1. A search failure can be several different failures

The imprisonment question needed benefit resolution, the payment/entitlement
distinction, chapter routing and source passages. Lexical discovery alone did
not provide that chain. The diagnosis therefore separated missing bundle
semantics, retrieval, graph visibility and context assembly. The reusable engine
uses declared relationships; no DWP paragraph routing is hard-coded into it.

### 2. More source text does not automatically mean a complete answer

The wider run returned candidate evidence for all 40 staff questions, including
ADM pages. All 43 packages matched the shared engine and remained insufficient.
The frozen custody profile's narrower sufficiency cannot be transferred to the
new full-corpus default. Completeness needs a reviewed task-specific evidence
requirement, not just a larger index.

### 3. A real client found a retrieval defect

ChatGPT initially received irrelevant pages because ordinary words such as
“your” and “go” dominated ranking. A general query filter changed the same
bounded abroad case to six international-guidance pages. The fixed staff run's
independent research-page overlap rose from 10 to 12 cases and document overlap
from 19 to 21. These are narrow retrieval diagnostics, not answer-accuracy scores.
Both attempts remain in the [comparison evidence](../validation/corpus-questions/retrieval-comparison.json).

### 4. Successful transport is not complete model access

The service could deliver a complete large package while ChatGPT reported host
truncation. A 32,768-byte request produced a 31,312-byte abroad package which the
model could inspect. The same complete bounded content was checked in the public
UI and native WebMCP. Public service 0.3.0 introduced progressive manifests and
exact evidence reads under **DWP-BL-008**; corrected version 0.3.1 retains them.
Its [SDK receipt](../validation/compact-delivery/v0.3.1/sdk-receipt.json)
reconstructs that same package and rejects stale or invalid reads. The
[local Claude observation](../validation/compact-client/README.md) distinguishes
seven real calls from an earlier zero-call model fabrication. Actual tool-call
receipts matter more than a model's claim that it used a tool.

### 5. Declaring a contract is not validating it

Final review found inherited fields and enum values outside the shared schemas.
They were mapped to supported fields or preserved in descriptive sidecars,
without modifying canonical schemas or source evidence. Canonical schema and
reference checks now run early. Future departmental projects should do this on
their first tiny fixture, rather than discovering drift near publication.

### 6. Final review needs to test state changes and dependency boundaries

Independent review caught a stale replay link after changing or resubmitting a
question. The [new browser regression](https://github.com/chris-page-gov/okf-explorer/blob/8493b323ca664e645a2548ebb48bf7917d7f6eb1/apps/okf-explorer/tests/service-review/evidence-review.spec.ts)
checks question A → B and the replacement context identity. Test transitions,
not just a successful first display. The correction is deployed as 0.3.1;
separate hosting-console failures remain open.

The assembled documentation also reused a cache that omitted transitive service
Markdown. Its renderer knew about a newly linked changelog but its cache did
not. The [cache regression](https://github.com/chris-page-gov/okf-explorer/blob/8493b323ca664e645a2548ebb48bf7917d7f6eb1/tests/test_build_site.py)
now proves linked changes invalidate the cache while unrelated files do not.
Portable lesson: derive cache inputs from the renderer's bounded dependency
closure, including exact-source alternates. Independent integration checks must
cover the interfaces between workstreams as well as each agent's own files.

## What to repeat

- Research terminology, legislation and standards before semantic generation.
- Keep immutable source bytes separate from interpretation and runtime projections.
- Give independent workstreams explicit files, interfaces and review boundaries.
- Retain failed attempts and unchanged baselines alongside improvements.
- Test actual consumers and clients; compare complete content, not just HTTP 200.
- Use the same readable evidence in the human and AI paths.
- Keep beginner documentation, current status and reproducible commands together.
- Link the changelog prominently. Keep notable reader changes separate from
  agent ownership, technical handovers and work still in progress.

## What still needs work

The [backlog](backlog.md) keeps stable identifiers, dependencies and acceptance
checks. Literal navigation and smaller reconstructable delivery now have scoped
producer/local-client or public-service receipts. Priority gaps remain independent
claim-level answer review, complete
benefit/time/territory profiles and provision-level legal reconciliation.
Projected personas still need user research. CPAG body access, calculators,
tribunal decisions, operational journeys, a benefits engine and Voice/audio
require their own work; none follows automatically from source capture.

The new [fixed-package model trials](../evaluation/answer-review/README.md) are
separate from engineering acceptance and remain subject to independent human
review. They do not yet establish a fair Claude-versus-Astra comparison or an
affordability conclusion.
