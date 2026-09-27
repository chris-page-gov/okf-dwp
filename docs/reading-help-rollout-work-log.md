# Reading-help rollout work log

## 26 September 2026: baseline and bounded parallel work

The owner authorised deterministic DMG and ADM processing, scalable reading help, focused legal citation improvements and a separately gated legislation-format reconciliation. The presentation target is 28 September at 18:00 Europe/London. No new automated content-processing or answer-model comparisons are authorised for this phase.

The [baseline receipt](../evaluation/reading-help-rollout/baseline.json) records exact DWP, Explorer, source-manifest and service-observation identities. It is an observation, not proof of continuous service availability.

- DWP baseline: `2c46fbd4e0807b1c9dfa0e9d79e33987d245ef21`.
- Explorer baseline: `0326460034345c7b5227c530065b7f21cb4e3970`.
- Structural baseline: 513 documents, 19,090 pages, 893 pages without extracted text and 53,727 units.
- The later 54,577-unit amendment candidate remains separately identified. Its existence does not authorise silent replacement of the structural baseline.
- Existing statutory evidence: 20 units, 16 provisions, 43 navigation relationships.
- A new live health request returned HTTP 403. The earlier recorded service 0.7.0 deployment and verification receipts retain their historical meaning; fresh health was not established by this attempt. A [later browser-style user-agent observation](../evaluation/reading-help-rollout/service-health-observation.json) returned service 0.7.0 ready. The [connected compact-manifest tool observation](../evaluation/reading-help-rollout/service-connector-observation.json) also succeeded, while explicitly returning `metadata_budget`, no selected records and `insufficient` at the deliberately small 32 KiB selection budget. These are separate observations, not a whole-corpus answer test.

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

## 27 September 2026: retained checks and limitations

- Explorer Reader repair is under review in [PR 158](https://github.com/chris-page-gov/okf-explorer/pull/158). CI initially found the new browser suite missing from the impact registry; the correction is separately committed.
- All 40 staff occurrences replayed with the frozen source, engine and 512 KiB/64-record/128-relationship/depth-six budget in both cold and warm runs. Exact packages were unchanged. The [report](../evaluation/reading-help-rollout/replays/reading-help-20260927-01/report.json) measures local latency, fetched bytes and cache reuse. This is non-regression, not improved retrieval or a legal-answer benchmark.
- The optional Chapter 60 statutory context validates against the actual Explorer context schema. Its first broader natural-language probe failed selection under its fixed budget; see the [bridge report](reading-help-legislation-bridge.md#optional-admission-and-measured-limits). The failure remains visible and no default service data was replaced.
- The dirty legislation migration was preserved as a 2,532-file, hash-inventoried archive on EXTSSD before selectively importing 30 authored/producer files into an isolated branch based on current remote main. Frozen generated source evidence and v0.3.0 remain preserved.

Publication and paired browser gates remain outstanding until their exact receipts are recorded.

The 28-case passage review was rechecked from its frozen inputs on 27 September: 28 cases, 55 files, manifest SHA-256 `488df312d1672270e9d458ad0944a30e07d2fc56062896ad3d9e8ca2ad0a21f2`. Its recorded nine-chapter review is retained. Case 014 remains unresolved; this check does not turn that finding into acceptance.

### Independent control review

The first held-out reading-help run retained a 23/24 failure. A separate coordinator check confirmed the H05 extraction hash and surrounding source text: the source prints `see DMG 070831 to 070834`, whereas the frozen expected target named only paragraph 070831. The complete range must remain unresolved rather than being narrowed to satisfy that expectation. The original failed case and result remain unchanged. A further unexecuted set was also rejected at review because `et seq` (and the following paragraphs) needs to remain visible, and the case mix needed stronger continuation and abbreviation coverage. These are quality controls, not specialist legal acceptance.

CI verifies the retained 40-question receipt with `python scripts/check_reading_help_replay.py`: source and engine declarations, all 40 package hashes, selected text and paths, obligations, and performance totals are checked without rerunning 80 assemblies. A changed engine or evidence baseline requires a separately named replay, not an overwritten receipt.

## Admission correction, 27 September 2026

The coordinator's engine review found that the first optional legal context
omitted source-capture timestamps and confused per-fragment hashes with the
complete record text hash. The initial failed observation is preserved under
`evaluation/reading-help-rollout/failed-admission-01/`. The corrected projection
uses the original acquisition/extraction receipts, complete record digests and
separate exact fragment metadata. Every added record and relationship now
passes Explorer's governance check; fragment integrity is checked independently.
The same question and budget still fail to retain the bridge, so no retrieval
improvement is claimed. Focused local reading-help tests: 35 passed, including
six workbench-link controls whose data publication awaits the corpus commit.

### Beginner navigation integration

The glossary and authored `learning/p01/s03` activity now point to the same
reading-help walkthrough. Regenerating the additive Reader changed its snapshot
identity, so the preceding optional-context observation is preserved under
`evaluation/reading-help-rollout/pre-learning-navigation-01/`. The successor
uses the same query, engine and budget and still does not select the bridge.
The 40 frozen staff packages remain unchanged. The local focused suite now
passes 36 controls, including rejection of conflicting retained record IDs.

### Corpus and workbench integration

The corpus producer is published for review in DWP PR 50 at commit
`115397c19e0b1e1e16d476df788c33a1196a3990`. Catalogue SHA-256:
`acb63e18d10c1a8a0a6c7d57f8ebfc41948e3837cd27c4589d4540061507d8a6`.
It accounts for 513 documents, 19,090 pages, 53,727 units and 893 empty
extractions. There are 1,455 bounded leaves and 197,564 delivered literal
occurrences; proposed meanings have no specialist acceptance. Shared parser,
helper and printed-table inputs invalidate the cache when changed.

The additive workbench manifest retains all 40 cases and links 401 of 403
distinct retained evidence records by exact unit and source identity. Capital
composites U06 and U10 remain unmatched rather than receiving guessed links.
The integrated focused reading-help suite passes 48 controls. The small and
held-out gates and their failed predecessors remain separate artefacts.

A second agent independently checked the legal bridge, including all 16
resolved citation mappings, four work identities, separate territorial variants,
rights notices and the actual context-engine checks. It found no further
material fault. This technical review is separate from legal acceptance.

The independent legislation migration remains a candidate. Exhaustive semantic
validation passed 929,053 assertions, but browser release checks have not passed.
Review identified public-main escapes from pinned/local federation and narrow
graph links; these are being corrected before another candidate observation.
The first runtime attempt also stopped because the coordinator archived an old
receipt during the identity check; that failure is retained. No new legislation
release or specialist acceptance is claimed.
