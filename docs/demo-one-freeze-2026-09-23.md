# Demo 1: freeze plan for 23 September 2026

**Target: a stable demonstration by 15:00 BST on 23 September, for presentation
on 29 September.** This is an independent experimental publication, not official
DWP guidance or specialist acceptance.

## Start here

[Open the pinned Demo 1 corpus in Explorer](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F9f6e316925f1550559733e34d8d91cd7a245c94b%2Fstructured-context%2Fokf-explorer.json#overview).
The source is fixed at `9f6e316925f1550559733e34d8d91cd7a245c94b`. The hosted
Explorer application can still advance independently; the observed application
release was `dc54fac4f98fa5bc9db38bf843854ce24a4c130d`.

1. Open the [beginner manual guide](source-led-manual-guide.md) to explain DMG
   (Decision makers' guide), ADM (Advice for decision making), a source unit and
   a checking location.
2. Open the [question ledger](demo-one-question-ledger.md) and select staff-012.
3. In Explorer, choose **Ask OKF**, paste that exact question, keep the 512 KiB
   default and choose **Build evidence package**. This step uses no answer model.
4. Show the insufficient/truncated status, selected sources and directed
   relationships. Open **Read whole source passage** for DMG 78088, including
   its heading, conditions, note and example.
5. Open **Inspect package JSON**. Explain that a machine client can receive the
   same source text. The native in-app WebMCP observation checked this directly.
6. Show the [retained answer comparison and claim review](demo-one-pair-results.md).
   Reuse the saved answers. Point out the quotation/qualification faults and the
   higher observed token use; do not run another model for rehearsal.

If a live client connection fails, use the retained audit package and answer
review. Do not substitute an older remote source silently: the new corpus's
remote-service admission is separate from the observed browser/WebMCP path.

## Scope agreed from the supplied brief

[Nick's public Demo 1 brief](https://github.com/bitsls2/ai-demo/blob/977193212c23923824b54d4e0766ffcad9d17bf0/demo-1-overview.md)
contains exactly the same 40 question occurrences as the existing evaluation,
in the same order and with unchanged wording. The
[readiness record](../evaluation/demo-1-freeze/readiness-2026-09-23.json) binds
the brief, question set and retained trial by their exact hashes.

The brief asks for an OKF bundle, an account of problems such as omissions or
conflicts, and answers with and without the bundle for several questions.
Improved answers and fewer tokens are hypotheses to test, not conclusions to
promise. A result showing no improvement must be retained just as clearly.

## Where the work stands

| Component | Verified state | Remaining freeze work |
| --- | --- | --- |
| Captured source | 513 DMG/ADM PDFs and 19,090 pages accounted for | Preserve the captured version and source limitations |
| Source-led candidate | 53,727 units; complete byte/span checks; four-case and doubled eight-case structural gates pass | Publish the exact tested candidate |
| Staff questions | 40 exact brief matches; 37 activate source-read profiles | Present the three scope ambiguities and all open obligations |
| Larger evidence packages | 40/40 retain source and relationships; 436/436 declared source-selection path incidences retained | Verify the chosen public source/engine pair |
| Answer sufficiency | All 40 still report insufficient; 203 original obligations remain open | Do not present discovery measures as complete benefits answers |
| Explorer | PR 144 merged and its deployment verified | Reuse the tested engine for this freeze |
| Python and learning site | 825 Python tests pass; new learning journey passes desktop/mobile checks | Exact release CI and public navigation checks |
| AI comparison | Four new answers retained; format and interpretation faults recorded | Use the claim review; no further answer calls |

## Keep the freeze affordable

- Use one coordinating agent. Do not restart the parallel full-corpus work.
- Reuse existing source, evaluations, scripts and model observations. Ordinary
  offline scripts may run checks without making model calls.
- Do not run another forty-question model sweep. The owner has selected two questions with and without OKF: a hard cap of
  **four new answer calls in total**, including failed invocations.
- Use staff-006 (Pension Credit savings) and staff-012 (a permanent self-funded
  care-home move). Compare the same subscription model without supplied evidence
  against the complete selected OKF source text and explicit limitations. Both
  arms have tools and web browsing disabled. This tests unassisted versus
  evidence-grounded answering, not ordinary web retrieval or a Data Agent.
- Keep question, model identity where available, answer limit and assessment
  criteria fixed within a pair. Record input/output tokens and tool activity
  where reported. Do not equate different providers' accounting with costs or
  claim a general accuracy improvement from two questions.
- Record whether the no-bundle arm uses general model knowledge, ordinary web
  retrieval or another source method. Those are different baselines and must
  not be labelled interchangeably.
- Preserve every failure. Do not rerun a model merely to obtain a better result.
- Do not purchase services, consume reset credits or change account permissions.

The [forty-question ledger](demo-one-question-ledger.md) gives each question a
source/gap record. The [four-answer results](demo-one-pair-results.md) retain
actual token usage, exact citations, failures and interpretation concerns.

The [frozen pair protocol](demo-one-pair-protocol.md) defines the exact inputs,
assessment boundary and no-retry execution policy.

## Release sequence and stop points

1. Confirm the brief mapping and name the exact candidate source and engine.
2. Publish through a normal reviewed pull request and required CI. Reuse the
   already deployed Explorer engine; do not introduce a new runtime for this demo.
3. Verify the public evidence entry point and learning walkthrough. If the new
   remote transport is not ready, retain the working service and demonstrate the
   browser/package route explicitly; do not claim a connection that was not tested.
4. Complete only the chosen bounded answer comparison and its claim review.
5. **At noon BST, stop feature changes.** Use the remaining period for checks,
   rehearsal, links, a frozen handout and an honest completion/gaps statement.
6. **At 15:00 BST, freeze.** If a candidate fails a release gate, retain it as a
   candidate and use the latest verified version. Do not weaken the gate.

## Parked work

The follow-up context-allocation repair and historical-amendment parser repair
have separate branches and retained tests. They are not required to reproduce
the current 40-question results. The original imprisonment question is a
separate acceptance case, outside Nick's Demo 1 question list.

Historical amendment contents, cover letters and appendix boundaries have
known structural defects in the current candidate. These remain disclosed;
the queued parser repair must receive its own source and context evaluation.
Machine boundary uncertainty, missing rates or qualifications, ambiguous benefit
names and current legal applicability must remain visible in the demonstration.

The freeze is a reproducible research demonstration. It is not certification of
40 complete benefit decisions, token savings or specialist approval.
