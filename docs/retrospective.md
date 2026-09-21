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

### Later evidence: qualifications need modelling and allocation

The [21 September comparison](../validation/qualification-context/2026-09-21/README.md)
separately changed the source model and the context engine, using both versions
of each with the same questions and two byte budgets. The revised pair retained
all 433 declared path occurrences and all 177 candidate occurrences. Those are
development measures, not correct-answer counts; all contexts remained
insufficient and the 203 obligations remained open.

Changing the engine alone displaced six useful household pages at the larger
budget because the earlier model had never declared them required. Changing the
source alone still lost paths under budget pressure. The combined change kept
all seven household pages for both care-home questions. A remaining optional
temporary-care dependency was still missing at 512 KiB and was reported.

Independent review also found that counting only requirements returned in a
package could hide omissions when a very small budget cleared that metadata.
The comparison now derives its denominator from the authored requirements and
pre-budget concept resolution. A separate 64 KiB check records an explicit
metadata refusal for the expanded care-home task. It does not pretend that an
empty package contained zero expected requirements.

For another department, name the qualifications an interpretation needs, preserve
their complete passages and measure source and engine changes independently.
Do not promote a navigation overview into a complete rule. Preserve unsuccessful
observations and keep candidate overlap, path retention and claim accuracy as
different measures.

The separate [partner increment](../validation/partner-context/2026-09-21/README.md)
extends that lesson: 177/177 candidate occurrences survive both budgets, but
449/585 declared paths survive 256 KiB and all 585 survive 512 KiB. The care-home
packages come close to the larger limit. A richer model can therefore expose
new omissions even when a headline discovery score stays unchanged. Preserve
the denominator, whole qualifications and every failed observation; use bounded
progressive reads for delivery rather than treating a smaller response as a
complete answer.

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

## 20 September: make hidden work and integration defects visible

The [work-package ledger](backlog-work-packages.md) now separates unfinished
implementation from independent acceptance. Neutral benefit aliases had also
been attached to custody-specific concepts. The [additive staff model](semantic-expansion.md)
corrects that association without rewriting historical evidence. Its candidate
overlap is a development measure, not proof that answers are accurate.

Independent integration review found a direct-context file overwritten by a
search shard and a citation parser carrying a recognised instrument into an
unknown one. Both had been masked by successful nearby paths. The regression
checks now exercise the fallback input and the unknown-instrument boundary.
Source identity, normalised citation identity and substantive legal applicability
must remain separate.

The fixed-evidence export also exposed a budget edge case in the consumer:
missing-evidence diagnostics were appended after trimming source records. A
package could therefore collapse to an empty refusal even when useful evidence
would fit. Keep small-budget failures as test artefacts and correct the reusable
engine; increasing every limit would conceal the defect.

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

### Preserve experimental inputs when publication metadata changes

The September staff trial exposed another repeatability boundary: an upstream
opaque legislation identifier matched a hosting secret-scanner pattern. Official
unauthenticated XML confirmed its public origin. The publication was minimised to
omit unused opaque fields while retaining substantive metadata, source locators
and digests. No protection bypass was used.

That small metadata change still changed the semantic provenance hashes. The
correct response was to archive the trial's exact original input, regenerate the
current view, and rerun browser observations. Rewriting old answer receipts to
look as though they used the new source would have destroyed the experiment.
HMRC repeats should freeze inputs before model calls and distinguish historical
replay from verification of the current release.

### Treat the build environment as part of reproducibility

The service's local dependency symlink changed esbuild's emitted path comments
and added dependency paths to its input receipt. CI's real locked installation
therefore produced a different build even though the source and lockfile matched.
Preserving logical dependency paths and testing a relocated real-versus-linked
installation restored identical Worker, Node and receipt bytes. The build script
itself now participates in that identity. Original observations were archived
and integration rerun; integrity checks were not relaxed to accept mismatches.


### Release checks are observations, not labels

The final service publication exposed a dependency-path portability defect: a
linked local installation built different bytes from CI. Locked installation and
a linked-versus-real build regression corrected the producer; historical receipts
were retained. Public Reader verification also retained an initial five-second
loading timeout before bounded reruns with phase timings. Neither failure was
erased by updating a status label. For HMRC, allocate separate checks for exact
source, generated outputs, model inputs, deployed application and human-visible
evidence. Passing one does not establish the others.


## Household continuation: lessons for another department

A missing result had three different causes. Six candidate pages needed explicit
source-backed graph paths; two belonged to unresolved meanings of SDA. A nearby
node-budget warning did not establish the cause. Keep coverage, resolution,
traversal and truncation diagnostics separate before changing limits. The
[portable engine experiment](context-performance.md) holds the old source index
fixed and records its own gains; the larger domain increment is a separate test.

A model can quote a sentence exactly and still omit its controlling heading.
The new household work preserves full pages and highlights no-partner and
temporary-absence qualifications. The [next paired trial](monday-model-trials.md)
changes both evidence and instructions, so it cannot attribute any answer change
to just the engine, prompt or model. Independent review also caught incomplete
CLI event streams being accepted as proof of no tool use: absence of a recorded
tool is meaningful only when the event census is complete.

The learning website needed a Markdown renderer. Adding its dependency to the
main lock changed a frozen corpus build identity, even though no legal content
changed. A separate locked website environment keeps that boundary explicit.
Similarly, new statutory acquisitions must enter the source-plane fingerprint,
not just appear in a graph. Independent review checks these cross-workstream
interfaces before publication. HMRC can reuse these controls and the
[discovery-first method](methodology.md), while rediscovering its own terms, law,
source rights, personas and questions.


### Keep delivery, model output and review separate

The 0.5.0 public service passed exact SDK reconstruction and three functional
browser journeys. Firefox still reported hosting-cookie warnings. An explicit
observation layout now says when historical journeys were not run, so a new
release cannot borrow an older release's pass. Keep successful delivery separate
from source completeness and from the quality of an AI's claims.

The original household model experiment retained five failures or rejections.
A separately frozen successor uses an exactly reversible dictionary for repeated
JSON values and stricter recognition of observed CLI events. The substantive
packets are 12–15% smaller; the small no-evidence control is larger. This is a
byte measurement, not proof of lower cost, faster responses or better answers.
A changed event parser cannot retrospectively accept an old rejected attempt.

A service-only pull request also skipped the documentation job and then failed
Pages publication. The correction checks documentation lockstep before selecting
expensive CI jobs. For an HMRC repeat, classify assurance requirements separately
from expensive test selection: a cheap mandatory publication check must remain
mandatory even when the app or corpus has not changed.

### More complete modelling can expose less complete context

The ignored-person increment makes previously implicit conditions explicit. It
preserves source text and open obligations, but its larger required evidence set
does not fit the same 512 KiB package. Candidate overlap remains 177/177 there.
This is a capacity regression, not proof that the new modelling is unnecessary.
For an HMRC repeat, freeze both the source version and requirement denominator,
measure whole evidence and repeated metadata separately, and investigate staged
component context or reversible delivery before enlarging a demonstration claim.
Keep the prior approved experiment fixed while evaluating a richer successor.

### Freeze the client protocol as well as the evidence

The direct-v3 run delivered no accepted answer because both empty controls exposed client metadata outside its frozen allowlist. We retained those failures and made no substantive calls. Direct-v4 kept the exact complete packages, prompt and answer schema, recognised documented installed-client fields in separately reviewed code, then reran the control-first experiment. Both controls and the one paired care-home question passed mechanical checks.

This demonstrates a portable engineering lesson for HMRC: a protocol compatibility failure is not a model reasoning failure. Keep immutable experiments, bounded value-free diagnostics, explicit event census and separate source/engine/client identities. Review scalar accounting fields as scalars; accepting an object in a numeric tool counter can conceal activity. Finally, inspect every claim and qualification: matching quotations, successful transport and a completed pair do not establish legal accuracy or affordable production operation.

The v4 critique demonstrates the last distinction concretely: its main statements match the source, yet one answer adds a condition list that omits selected exceptions and labels selected continuation evidence absent. Review summaries and qualifications as claims too. Preserve the original answer and attach the critique; do not repair history to make the demonstration appear successful.
