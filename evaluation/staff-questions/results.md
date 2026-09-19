# Staff-question results

**The wider source collection now produces candidate evidence for every supplied
question. It has not yet produced a complete, specialist-accepted answer to any
of them.** This is an independent experimental publication, not official DWP
guidance or individual benefits advice.

The [question registry](cases.json) preserves 40 question occurrences and 39
distinct wordings. One repeated question is retained deliberately. It contains
the questions and research annotations, without private correspondence or
contact details. Questions with unclear scope, including “SDA” and the War
Pensions wording, remain unresolved rather than being silently rewritten.

## What was tested

| Measure | Preserved custody baseline | Combined DMG and ADM candidate |
| --- | --- | --- |
| Observation | Actual remote MCP calls, 19 September 2026 | Local shared-engine run, 19 September 2026; pre-publication |
| Source available to Ask | 52 governed context records | 18,197 nonempty extracted pages across 513 PDFs |
| Questions | All 40 occurrences | Same 40 occurrences, plus three boundary controls |
| Transport comparison | All 40 complete remote packages match the shared Explorer engine | No live transport claim from this local run |
| Candidate evidence returned | Earlier receipt preserves the selected custody evidence | All 40 staff questions; each also returns at least one ADM page |
| Independent research-page overlap | Not scored in the baseline | 10 of 40 packages include an independently located candidate page |
| Independent research-document overlap | Not scored in the baseline | 19 of 40 include a page from an independently located candidate PDF |
| Declared sufficient packages | 0 | 0 |
| AI answers generated | 0 | 0 |
| Specialist-accepted answers | 0 | 0 |

Evidence is retained in the [remote baseline receipt](../../validation/staff-questions/receipt.json)
and the [local full-corpus receipt](../../validation/corpus-questions/receipt.json),
with per-question compressed responses, exact question text, hashes, scope,
missing evidence and implementation identity. The original baseline uses
immutable DWP revision `efb05c66616a9cd4328a86cf412780fe7bc7cf0b`. The local run
names its own corpus version and manifest binding; it does not replace that
baseline. Its live-service and browser checks remain separate delivery gates.

The wider collection contains 19,090 measured pages. The 893 pages without
machine-extracted text retain their original source links and page locators,
but cannot supply a text match. Nonempty extraction can also contain defects.
See the [ADM acquisition record](../../docs/adm-acquisition.md) and the
[beginner learning path](../../docs/learning-path.md).

## What the improvement means

The earlier Ask profile could expose its custody evidence and correctly report
that the staff questions exceeded its scope. The wider path can now search all
nonempty captured pages, select bounded whole-page evidence, and combine that
with existing concepts and relationships. It keeps source text, project-authored
normalisation and inferred relationships distinct.

Page and document overlap test retrieval against independently located research
starting points. The 42 source candidates have checked source hashes, page text
and locators. They are not exhaustive answer rubrics or expert-approved legal
conclusions. The overlap measures are therefore diagnostics, not accuracy,
recall or answer-quality scores. A question returning ADM text does not prove
that ADM governs its circumstances.

The combined run's three additional controls cover hospital wording, an explicit
ADM discovery query and a nonsense query. The ADM control must retrieve ADM
evidence. The nonsense control must return no evidence and no lexical candidates.
All 43 outputs remain `insufficient`, with no AI answer. The full-corpus discovery
profile declares no complete task-specific evidence requirements.

## Limits that remain visible

- Literal question terms rank candidate pages. Matching words establish a
  possible lead, not applicability or a benefits conclusion.
- Concept resolution uses declared aliases separately. Existing concepts and
  relationships retain their original scope, including custody-specific scope;
  full source capture does not broaden those assertions automatically.
- The local run reports truncation for 42 of its 43 packages, including all 40
  staff questions. The fixed candidate limit leaves other matching pages outside
  each package; output budgets can also omit whole records. The nonsense control
  has no matches to truncate. The baseline recorded no assembly-budget truncation.
- Source capture dates, publication dates and any effective dates have different
  meanings. Frozen evidence does not establish current-law applicability.
- Missing benefit variants, dates, exceptions, external legislation or territorial
  scope must be resolved in an authored evidence profile and reviewed by a
  specialist before completeness can be claimed.
- No token saving, cost saving or equivalent answer quality has been measured.
  Byte counts are not token counts. ChatGPT delivery limits, Voice access and
  browser WebMCP support have separate checks.

The [remote demonstration guide](../../docs/remote-mcp-demo.md) preserves actual
ChatGPT observations, including the host truncating a large response even when
the context assembler itself reported no truncation. The two limits must not be
confused.

## Monday demonstration

1. Start with the [learning path](../../docs/learning-path.md) and the coverage
   table above. Explain the difference between a captured manual and a complete
   evidence profile.
2. Follow the [connection and demonstration guide](../../docs/remote-mcp-demo.md).
   Use the exact published version named there. Describe any newer local run as
   local until its live acceptance is recorded.
3. Show the [public question registry](cases.json). Select one question and keep
   its original wording and ambiguity notes visible.
4. Compare the preserved baseline result with its full-corpus result. Show the
   selected pages, original PDF links, hashes and inclusion reasons. Distinguish
   a literal match from a declared relationship.
5. Show `insufficient`, missing evidence and truncation before handing evidence
   to an AI. Explain what specialist input is needed to define a complete rubric.
6. Inspect the machine-readable package. If the tested remote version supports
   the same corpus, request that same question through MCP and compare the
   version and context identifier. Do not present a different version as parity.
7. Use the nonsense control to demonstrate a legitimate no-result outcome.
   Finish with the measured progress and the remaining review work, without
   claiming a benefits engine, an entitlement decision or proven savings.

## Reproduce the preserved baseline

Use the locked setup in the [project README](../../README.md#build-and-verify)
and the Explorer revision specified by the workflow or receipt:

```sh
node --experimental-strip-types scripts/evaluate_staff_questions.mjs --check --explorer-root ../okf-explorer
node --experimental-strip-types scripts/test_staff_questions.mjs --explorer-root ../okf-explorer
```

The first command verifies retained responses against the recorded engine and
source evidence. The second rejects altered provenance, transport accounting and
forged sufficiency. Neither command calls a model or sends questions to the live
service. New full-corpus replay must use the exact implementation hashes and
binding recorded in its own receipt.
