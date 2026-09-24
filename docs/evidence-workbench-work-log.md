# Evidence repair and workbench delivery

Started: 24 September 2026. This is the current implementation log; the Monday
21 September log remains a historical record.

## Outcome requested

Fix the diagnosed natural-language retrieval miss, connect and select captured
evidence more effectively, deliver it in bounded parts, and provide an Explorer
Evidence workbench where every one of the 40 staff-question occurrences can be
examined. All 40 being examinable does not mean all 40 are legally answerable.

## Starting evidence

DWP main is `44488b89d82f191f189e7ab57364d554959be9e6`; Explorer main is
`dc54fac4f98fa5bc9db38bf843854ce24a4c130d`. The independent capital retest
reproduced 52 assemblies without an answer-model call. The subsequent diagnostic
reproduced the failing question's chapter and full-corpus packages exactly:
the grouped passage ranked 29th against 16 lexical candidates; the everyday
wording did not resolve the notional-capital concept; the corresponding guarded
routes remained inactive. The chapter package had unused assembly capacity.
Appending the specialist term selected the passage but did not establish
evidence sufficiency. Neither diagnostic is a repair or a general quality trial.

## Parallel ownership and recovery

| Work | Owner | Branch | State |
| --- | --- | --- | --- |
| Reusable discovery and selection | Retrieval agent | `codex/evidence-retrieval-repair` | Implementation and generic regression tests |
| Full-corpus connections and 40-question projection | DWP agent | `codex/evidence-connect-workbench` | Additive producer and evaluation |
| Source-centred inspector and review proposals | Workbench agent | `codex/evidence-workbench` | UI, bounded loader and accessibility checks |
| Compact delivery, integration, documentation and publication | Integrator | `codex/evidence-delivery-integration` | Delivery and shared gates |

The agents use isolated worktrees. The integrator alone combines changes and
publishes reviewed candidates. New steering changes the relevant workstream;
unaffected workers continue. App interruption, usage limits and external service
failures can still pause execution. Resume from this log, Git state and live
agent status before starting another writer. No new answer-model experiment,
embedding job or source acquisition is included in this phase.

## Acceptance gates

1. Preserve frozen source bytes, earlier corpora, replays and trials. Keep private
   correspondence outside Git and publication.
2. Fix the original question and test varied unseen paraphrases and wrong-benefit
   controls. Compare matching representations across narrow and full corpora.
3. Add only source-backed dependency links; retain ambiguity, absent source bodies
   and specialist-review obligations. Report concept resolution separately from
   lexical discovery and legal applicability.
4. Re-run all 40 public staff-question occurrences. Record source/version, engine,
   selected and missing evidence, paths, truncation, byte use and measured timings.
5. Reconstruct each selected package exactly from responses at most 32 KiB. Report
   total transferred bodies and overhead as well as individual response limits.
6. Navigate all 40 cases in the workbench. Inspect the source PDF location, text,
   complete passages, concepts, relationships, gaps and selection reasons; export
   review proposals without modifying source evidence or claiming review acceptance.
7. Run affected contracts and tests, independent code review and browser journeys;
   merge through protected PRs, then verify the exact public versions separately.

## Publication impact

New authored DWP profiles and generators produce additive evidence projections
and a bounded workbench manifest with lazy case packages. Existing source and
historical projections remain frozen. Explorer changes the opt-in discovery
implementation, delivery helper and workbench routes. README, beginner guidance,
the machine backlog, work-package register and changelogs move with the code.
The learning-site exporter admits only explicitly listed, hash-bound workbench
artefacts; it must not copy arbitrary evaluation directories or private files.
The remote MCP deployment and actual client compatibility require their own
observations and are not implied by a static workbench or offline test.

## Checkpoints

- Initial inspection: no active implementation agents were left from the retest.
  Existing working directories and the separate security-review checkout remain
  untouched. DWP main validation and Pages checks passed. New branches start from
  the current fetched main references. An unrelated historical handover PR and
  Explorer dependency/learning PRs are left intact.
- Implementation is in progress. No new completion, merge or public deployment
  is claimed at this checkpoint.

## Integration checkpoint

- Explorer includes opt-in weighted discovery, scope-bound navigation routes and
  early source dependency traversal. The original failure is repaired; the
  development probe run retains one transfer-wording miss and all insufficient
  statuses. Earlier failed probe variants are retained.
- The workbench has seven source-to-review tabs, lazy case loading, shared raw
  and multipart integrity checks, deep links and local proposal export. Review
  found and fixed request races, stale history, and unbounded stream continuation.
- Independent publication review found restricted-record admission, source-hash
  and output-collision defects. These are corrected; eight new publisher controls
  and 26 existing website tests pass. Full JavaScript reconstruction for all 40
  retained packages is a separate required gate.
- Explorer's initial integrated full unit suite passed 767 tests. The full static
  build initially failed because a plain Vite build lacks the required canonical
  build manifest; the documented deterministic-build prerequisite is now used.
- No sources, historic snapshots or answer-model trials were changed. Current
  work is still a feature candidate; no new public deployment is claimed here.

## Reviewed feature checkpoint

The producer is committed at `bea541f2`. Explorer PR145 contains the reusable
engine, workbench and delivery implementation. Its initial CI run exposed two
compatibility issues: newly external schema references were not registered by
legacy MCP/archive consumers, and a learner-hub test assumed a generated route
number. The fixes preserve local schema loading and test actual route isolation.

The independent delivery checker passed **40 contexts and 673 parts**; maximum
part size is **32,768 bytes**, and the retained canonical text totals 20,303,318
bytes. All 40 statuses remain insufficient. The same-overlay 80-assembly
comparison records 15 cases gaining records and 14 losing records; these counts
are changes in selection, not relevance scores. Development tests select U07
and its 84861 dependency for five of six positive questions, and a separately
fixed confirmation set selects three of four. Both sets have zero of five
negative selections. Transfer-to-another-person wording remains an explicit miss.

Independent producer review confirmed unchanged text, source spans, provenance
and assertion status for all ten imported passages. It found and corrected
output-path containment and missing input-hash bindings. Case expectations are
used only after assembly for assessment. No benchmark IDs seed retrieval.

The required CI now includes a separately pinned workbench job: deterministic
projection, all-40 reassembly, independent exact reconstruction, output-path and
publication controls, and an exact-commit static-site build. The protected
aggregate check requires this job alongside both earlier validation planes.
