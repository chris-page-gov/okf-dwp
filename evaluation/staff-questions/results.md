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
| Observation | Actual remote MCP calls, 19 September 2026 | Actual remote MCP calls, 19 September 2026, completed at 17:31:33 UTC |
| Source available to Ask | 52 governed context records | 18,197 nonempty extracted pages across 513 PDFs |
| Questions | All 40 occurrences | Same 40 occurrences, plus three boundary controls |
| Transport comparison | All 40 complete remote packages match the shared Explorer engine | All 43 complete remote packages match the shared Explorer engine |
| Candidate evidence returned | Earlier receipt preserves the selected custody evidence | All 40 staff questions; each also returns at least one ADM page |
| Independent research-page overlap | Not scored in the baseline | 12 of 40 packages include an independently located candidate page |
| Independent research-document overlap | Not scored in the baseline | 21 of 40 include a page from an independently located candidate PDF |
| Declared sufficient packages | 0 | 0 |
| AI answers generated | 0 | 0 |
| Specialist-accepted answers | 0 | 0 |

Evidence is retained in the [remote baseline receipt](../../validation/staff-questions/receipt.json)
and the [remote full-corpus receipt](../../validation/corpus-questions/receipt.json),
with per-question compressed responses, exact question text, hashes, scope,
missing evidence and implementation identity. The original baseline uses
immutable DWP revision `efb05c66616a9cd4328a86cf412780fe7bc7cf0b`. The wider run
names its own corpus version and manifest binding; it does not replace that
baseline. Its [published-browser check](../../validation/corpus-questions/public-explorer-observation.json)
and actual bounded ChatGPT rehearsal have separate completed observations below.
The new [full-corpus demonstration guide](../../docs/remote-mcp-demo.md#five-minute-full-corpus-presentation)
uses explicit version `bf50ef8d91b9f1ccc2cbdb354198eae74c9ed752`. The older
imprisonment sufficiency result must not be presented as a result of this broader
default corpus.

The [official SDK verification](../../validation/corpus-questions/sdk-receipt.json)
is a separate completed live test on 19 September: current imprisonment and
hospital packages are insufficient and truncated; the explicitly selected older
imprisonment package remains sufficient within its frozen profile. All three
match the complete shared-engine output. This complements the separate 43-case
remote run; neither proves that ChatGPT can inspect a full package.

Independent offline replay verified all 43 complete packages. All 21 corruption
controls were rejected, covering receipt identity, source and transport bindings,
and altered results. The 42 independently located source candidates were also
reverified. These checks protect the integrity of the evaluation; they do not
convert its research starting points into complete answer rubrics.

### What the real client test changed

The [actual ChatGPT observation](../../validation/corpus-questions/chatgpt-observation.json)
first exposed a cached tool schema, then an evidence-ranking defect. After the
connection was refreshed, the first bounded call succeeded, but ordinary query
words such as “your” and “go” selected five irrelevant source pages. ChatGPT
correctly declined to turn them into an abroad answer. That is a successful
transport test and an unsuccessful retrieval result.

A general query-word filter was corrected and the same sources, question and
32,768-byte budget were tested again. ChatGPT inspected six international-issues
source pages, totalling 31,312 bytes, without reporting host truncation. The
[exact bounded package](../../validation/corpus-questions/bounded-abroad/context.json)
and [HTTP receipt](../../validation/corpus-questions/bounded-abroad/receipt.json)
remain inspectable. The context is insufficient and truncated; no complete
benefits answer or specialist acceptance is claimed.

The [machine-readable comparison](../../validation/corpus-questions/retrieval-comparison.json)
binds the earlier remote receipt at commit
`697dd85c1cd5ea5191a77124de5a868d06d1652c` and the current receipt by exact hashes,
including both engines. Exact-page overlap rose from 10 to 12 cases and document
overlap from 19 to 21. `staff-004` and `staff-037` each gained a candidate;
38 other staff cases were unchanged on these measures, with no lost candidate
overlaps. The source corpus and question registry were unchanged. This is a narrow
retrieval comparison, not an answer-quality score or a claim that every selected
page is relevant.

The wider collection contains 19,090 measured pages. The 893 pages without
machine-extracted text retain their original source links and page locators,
but cannot supply a text match. Nonempty extraction can also contain defects.
See the [ADM acquisition record](../../docs/adm-acquisition.md) and the
[beginner learning path](../../docs/learning-path.md).

### Published Explorer and browser-tool agreement

The [public Explorer observation](../../validation/corpus-questions/public-explorer-observation.json)
at app commit `a8628fdb77c1c03a5d99b6d105d9e4b8722088d7` records Search, Ask,
source provenance, directed routing and machine-readable context. Its
[downloaded app files](../../validation/corpus-questions/public-explorer-build-verification.json)
matched the tested build. With **Package bytes = 32768**, the abroad question's
six source pages and 31,312 bytes matched native WebMCP build and explain calls
and the complete remote package by canonical content. All share context
`urn:sha256:2cdfa5feb6310f58166d66e814bd3b2fbe2e9e146e25b25a65453b48e3dffabd`.

The default imprisonment task separately showed eight resolved concepts, 64
records, 127 relationships and 516,146 bytes, including chapter 12 routing to
chapters 24, 53, 54 and 78. Both packages remained insufficient and truncated.
Native WebMCP was called in the Codex in-app browser; this does not establish
ChatGPT Voice or room-audio readiness.

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
- The wider remote run reports truncation for 42 of its 43 packages, including all 40
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
2. Follow the [full-corpus presentation and connection guide](../../docs/remote-mcp-demo.md#five-minute-full-corpus-presentation).
   Use the exact version named there and set Explorer's **Package bytes** to
   **32768** for the abroad comparison. The published UI, browser tools and
   remote package now match for that case. Repeat the tested bounded ChatGPT
   prompt in the intended account before the meeting.
3. Show the [public question registry](cases.json). Select one question and keep
   its original wording and ambiguity notes visible.
4. Compare the preserved baseline result with its full-corpus result. Show the
   selected pages, original PDF links, hashes and inclusion reasons. Distinguish
   a literal match from a declared relationship.
5. Show `insufficient`, missing evidence and truncation before handing evidence
   to an AI. Explain what specialist input is needed to define a complete rubric.
6. Inspect the machine-readable package. Request the same question through MCP
   and compare the version, budget and context identifier. The guide provides
   the verified bounded abroad example; a different version or budget is a
   different package.
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
