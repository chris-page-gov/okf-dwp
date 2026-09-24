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

## Final local integration checks

The successor descriptor now retains the original Reader snapshot while binding
the additive context overlay separately. An actual Reader-to-Ask loader test
caught the previous snapshot mismatch; the corrected descriptor selects U07
without changing the source Reader. All 40 packages and the comparison/probes
were regenerated against context manifest
`4e65253f72b2d771164d5ddd64374ed8142cf66b4a249f193a1fe44d5679f519`.

Local Chrome journeys cover the abroad, care-home and Pension Credit abroad
questions, original review briefs, source links, passage and relationship views,
local proposal export and a 390-pixel layout. GOV.UK PDFs reject embedded
display: the page-linked source document opens separately. An iframe element is
not proof that a PDF rendered. The earlier local receipt is preserved under
`validation/evidence-workbench/2026-09-24/local-before-descriptor-fix/`, including
its absent timestamp/build identity and failed PDF requests.

Review also corrected a double browser-history entry when following a passage
from a relationship. Explorer's required CI exposed an obsolete Heritage app
fingerprint; its old acceptance files are preserved. The new deterministic app build passed
the actual 100-question browser acceptance and all three Heritage journeys. The non-DWP
study-club trial has a separate new execution receipt; its old receipt remains
unchanged. These checks test reuse and regression, not DWP legal completeness.

Public deployment remains pending at this checkpoint. The workbench's
implementation package is recorded complete; its public-verification and
specialist-review packages remain separate and open.

The older structured-corpus checker initially rejected the new additive namespace
as unbound surplus. Its source inputs and frozen outputs were not rewritten. A
separate wrapper verifies every successor byte, temporarily sets aside only its
288 declared files for the exact base check, restores them and verifies them
again. The full 53,727-record base check and five restoration/containment controls
pass. CI runs the base and successor planes independently.

The final local Reader-to-Ask browser journey loaded the new
`structured-context/evidence-connect-explorer.json`, asked the exact original
capital question, and selected U07, the DMG 84861 entry and their direct link.
At 64 records, 128 relationships, depth 6 and 524,288 bytes, the result contains
44 records and 68 relationships using 522,919 bytes. It reports budget
truncation and remains insufficient. Browser console, page and request errors
were absent. The receipt and screenshot are in `local-final/reader-ask.json`
and `local-final/reader-ask.png`; the earlier combined-descriptor check is
retained separately and is not used as evidence of the successor working.

Explorer PR145 merged as `e6084059f9b09633cfb8385be20099b952915e82`
after all required checks, including Chrome, Firefox and WebKit. Its Git tree
exactly matches the reviewed candidate. DWP's new workbench CI now pins that
protected-main consumer commit; the recorded engine and delivery file hashes
are unchanged. This is merge evidence, separate from the subsequent public
deployment observation.

## Merged and public verification — 24 September 2026

Explorer PR145 merged as `e6084059f9b09633cfb8385be20099b952915e82`.
DWP PR36 merged as `7eeded763042ddd0070f4fed834c6074149e8e2f`;
the reviewed candidate had the same Git tree. All protected checks passed.
The subsequent DWP main validation run `35972890182` and Pages deployment
`35975520154` succeeded. Explorer's Pages run `35969493742` also passed;
these run identities are separate from browser and content acceptance.

The version 3 public-site verifier matched **1,141 of 1,141** declared public
responses against a locally rebuilt site bound to merged commit `7eeded763`:
the site manifest and 1,140 listed outputs. The [site receipt](../validation/evidence-workbench/2026-09-24/public-release/site/observation.json)
records the immutable Git inputs, exact bytes, fixed host, bounded concurrency
and zero retries. The [public browser receipt](../validation/evidence-workbench/2026-09-24/public-release/browser/receipt.json)
records the 40-entry workbench catalogue, three representative case inspections, deep
links, a locally exported unreviewed proposal and the live Reader-to-Ask
journey. External GOV.UK PDF embeds did not render reliably; the source page
links remain the intended way to open those documents.

In the public capital journey, the original question selects U07, the DMG
84861 source entry and their direct dependency. The package contains 44 records
and 68 relationships, uses 522,995 of 524,288 bytes, and reports truncation
and `insufficient` evidence. The earlier local journey's 522,919 bytes belong
to its separate receipt and are not a substitute for this public observation.

Capital delivery and additive-overlay adoption, bounded workbench delivery,
and BL025 public verification are now recorded complete for these exact
revisions. Eleven declared capital dependency groups remain open overall,
even though four captured groups gained exact entry links. BL025 remains in
progress because independent specialist review is open. See the
[handover](evidence-workbench-handover.md) for source, engine, site and browser
identities and the continuing limitations.
