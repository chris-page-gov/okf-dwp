# Reading-help rollout work log

## 26 September 2026: baseline and bounded parallel work

The owner authorised deterministic DMG and ADM processing, scalable reading help, focused legal citation improvements and a separately gated legislation-format reconciliation. The presentation target is 28 September at 18:00 Europe/London. No new automated content-processing or answer-model comparisons are authorised for this phase.

The [baseline receipt](../evaluation/reading-help-rollout/baseline.json) records exact DWP, Explorer, source-manifest and service-observation identities. It is an observation, not proof of continuous service availability.

- DWP baseline: `2c46fbd4e0807b1c9dfa0e9d79e33987d245ef21`.
- Explorer baseline: `0326460034345c7b5227c530065b7f21cb4e3970`.
- Structural baseline: 513 documents, 19,090 pages, 893 pages without extracted text and 53,727 units.
- The later 54,577-unit amendment candidate remains separately identified. Its existence does not authorise silent replacement of the structural baseline.
- Existing statutory evidence: 20 units, 16 provisions, 43 navigation relationships.
- A new live health request returned HTTP 403. The earlier recorded service 0.7.0 deployment and verification receipts retain their historical meaning; fresh health was not established by this attempt.

### Writer ownership

| Work | Branch | Responsibility |
| --- | --- | --- |
| Reader legal URLs and complete text | `codex/legislation-reader-repair` | One Sol medium implementation agent |
| Deterministic corpus reading help | `codex/corpus-reading-help` | One Sol medium implementation agent |
| Baseline, bounded legal bridge and integration | `codex/reading-help-legal-bridge` | Coordinator |

Both agent launches initially failed because of model capacity. One retry succeeded. At most two implementation agents are active; no content-analysis model batch was started. Worktrees and cache are on EXTSSD. The primary DWP checkout's unrelated client-report edit and private email remain untouched.

### Gates and outstanding work

1. Review and merge the Reader URL/full-text repair before admitting additional statutory text to a consumer.
2. Validate the shared catalogue/document/passage contracts and their consumer. Preserve the Chapter 60 v1 demonstration and URLs.
3. Produce a complete processing/gaps ledger; validate 12 cases and, only on success, 24 fresh held-out cases.
4. Replay the 40 staff-question occurrences at equal source scope and budgets, with source evidence and legal answerability reported separately.
5. Reuse recorded 28-case structural outcomes and retain unresolved case 014; do not repeat completed parser work without a changed rule or new concern.
6. Validate explicit admission of the [bounded legal bridge](reading-help-legislation-bridge.md).
7. Reconcile the legislation repository in isolation after the first consumer increment. Preserve dirty migration work and `v0.3.0`.
8. Verify exact merged commits, public Pages, workbench and service separately. Tag only a passing paired consumer/data release, retaining the earlier demo fallback.

The term **full processing coverage** means that every captured document has a recorded outcome. It does not mean every passage has an explanation or every question has a legally complete answer. Completed stages must link to retained checks and receipts before their backlog status changes.
