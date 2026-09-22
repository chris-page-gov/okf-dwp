# Testing manual structure before changing retrieval

This is an independent experimental publication, not an official DWP document.

A PDF page is a source location. A useful retrieval unit is a complete passage: for example, a numbered paragraph with its conditions, note, legal citations and examples, even when those continue on the next page. A discovery card can help find that passage, but cannot replace its complete source text or resolve its legal dependencies.

## What this experiment checks

The [registered protocol](../evaluation/manual-structure/protocol.json) fixes eight source cases, including their exact PDF, extracted text, source-page and passage hashes. A hash is a fingerprint used to detect changed bytes. The four initial cases check documented structural defects. The doubled set contains those same four plus four different structures.

The cases were selected by reading the frozen source and inspecting rendered PDF pages. They are source-led regression cases, not answers tailored to individual staff questions. The source baseline is commit `908adc45a4e22eb72ed13fe8943877307b732850`.

The protocol and all eight fixtures were committed at `bede806a` before any source-case experiment or results. Parser code was drafted concurrently with fixture preparation. The [registration note](../evaluation/manual-structure/registration-note.json) preserves the original protocol hash and makes this timing explicit. These are not blinded, held-out cases.

| Stage | Source case | Required structural behaviour |
| --- | --- | --- |
| Initial | DMG Chapter 77, paragraph 77031, PDF page 14 | The governing heading is entitlement to State Pension Credit. A linked mini-contents entry for paragraphs 77053–77099 must not become its heading. Keep all six conditions and citations. |
| Initial | ADM P4, P4087, PDF page 18 | The section concerns revision and supersession after the relevant age, for the mobility component. The later residence/presence link must not become its heading. Retain the note and cited references. |
| Initial | DMG Chapter 7 Part 6, 077001, PDF pages 8–9 | Retain the conditions, note, citations and both Jason and Nicola examples. The page break must not cut the first example. Keep the next separately headed rule distinct. |
| Initial | ADM C1, C1988, PDF pages 121–122 | Retain both branches of conditions, the definition note, citations, memo annotation and all three examples. The following definition remains a distinct passage. |
| Expanded | DMG Chapter 84, Appendix 1, PDF pages 130–131 | Retain the table headers, both pages of rows and the illustrative-use notice. The paragraph number in the appendix title is a reference, not a newly numbered rule. |
| Expanded | ADM F1, F1085–F1099, PDF page 14 | Preserve the unfilled range as a range marker. Do not invent a substantive F1093 paragraph or absorb neighbouring rules. |
| Expanded | DMG abbreviations, PDF page 3 | Retain the DLA, DM, DMA and DMG lookup entries as reference material. Their presence does not establish entitlement or applicability. This case covers one continuation page. |
| Expanded | ADM memo 09/25, PDF pages 1 and 9–10 | Distinguish contents navigation, body introduction, three complete examples, annotation targets and contact instructions. The first example crosses a page. Contact instructions remain inert source data. |

**DMG** means Decision Makers Guide. **ADM** means Advice for decision making. These manuals contain staff guidance; a correct structural boundary is not a legal decision. A memo is a separate guidance update. Finding its annotation targets does not prove its effect on every case.

## Pass gates and limits

Each case must pass every applicable check:

1. **Source identity:** the source inventory, PDF, extraction and cited page bytes match the registered fingerprints.
2. **Byte conservation:** a separate accounting partition covers every extracted source byte exactly once. A partition is an ordered division of the original text. Hierarchical navigation may overlap; this accounting division may not.
3. **Governing heading:** the passage has the expected heading, with no unrelated mini-contents entry promoted to that role.
4. **Complete passage:** a coherent unit contains the whole registered passage, including cross-page examples and qualifications. Explicitly excluded following structures stay separate.
5. **Roles:** contents, tables, reserved ranges, reference dictionaries, examples, annotations and contacts remain distinguishable.
6. **Provenance:** every selected span reconstructs from an exact source page, byte range and hash. Provenance means the record of where information came from.
7. **Reference scope:** references and annotations retain their observed kind. Their legal effect and dependency status remain unresolved unless separately reviewed.
8. **Negative controls:** known wrong headings, cut examples, lost table rows, invented reserved paragraphs, changed hashes and promoted authority must fail the appropriate check.

The denominator is **four source cases**, then **eight source cases**. Multiple checks within a case do not increase it. Passing these cases does not establish current law, specialist acceptance, legal dependency closure, answer relevance or answer quality.

The initial validator passed 13 control tests; an additional control separates declared excerpt completeness from legal acceptance. These include synthetic correct observations and deliberate errors; they do **not** demonstrate that a parser passed the eight cases. Source-case results must be read from separately retained run reports.

## How to reproduce the checks

Run commands from the repository root with the locked environment. No acquisition or model call is needed.

```sh
uv sync --locked
uv run --frozen python -m unittest scripts/test_manual_structure_acceptance.py
```

The default command checks fixture integrity and the validator controls. It does not execute a parser experiment.

Run the initial frozen baseline comparison and candidate separately. Each output directory must be new. A failed experiment returns a non-zero exit status **after retaining its report and observations**.

```sh
uv run --frozen python scripts/test_manual_structure_acceptance.py \
  --evaluate --engine baseline --stage initial \
  --output evaluation/manual-structure/runs/baseline-initial-01

uv run --frozen python scripts/test_manual_structure_acceptance.py \
  --evaluate --engine candidate --stage initial \
  --output evaluation/manual-structure/runs/candidate-initial-01
```

The baseline reads the already frozen logical-unit catalogue, verified against its manifest. It does not rerun or improve the old parser. The candidate calls `segment_source` in `scripts/manual_structure.py` on the same source documents. The adapter changes field names and offset representations, verifies source hashes and records the parser's actual structures. It does not manufacture missing headings, roles or references from the expected fixture.

Only after all four initial candidate cases pass, double the set to the already registered eight. Keep the initial results and every failed attempt. If the parser changes, rerun the initial set under a fresh run name.

```sh
uv run --frozen python scripts/test_manual_structure_acceptance.py \
  --evaluate --engine baseline --stage expanded \
  --initial-report evaluation/manual-structure/runs/candidate-initial-01/report.json \
  --output evaluation/manual-structure/runs/baseline-expanded-01

uv run --frozen python scripts/test_manual_structure_acceptance.py \
  --evaluate --engine candidate --stage expanded \
  --initial-report evaluation/manual-structure/runs/candidate-initial-01/report.json \
  --output evaluation/manual-structure/runs/candidate-expanded-01
```

A report records each case's failures, the fixed denominator, source baseline, implementation hashes, time and observations hash. New runs also bind the imported PDF-alignment/observer modules and every consumed PDF-structure sidecar, raw tree, diagnostics and observation manifest. The active observation manifest and its declared raw-tree paths are used, including bounded reparses that retain the original observations. A module or consumed observation changed during a run invalidates its pass claim. The eight-case gate requires the same implementation and retained observations as its preceding four-case pass. Earlier retained reports remain unchanged; their less complete binding is a recorded limitation. The compressed observations contain inspectable spans, headings, roles and references. Raw source conservation and joined display text are checked separately: a newline inserted between page spans is not an original source byte.

### Observation contract for another parser

The validator can also accept another implementation through an explicit adapter:

- `source`: exact document identity, role, URL and inventory/PDF/extraction bindings;
- `partition`: an ordered, non-overlapping list of source-page spans covering the whole document;
- `units`: coherent units with an ID, source spans, content hash, role, paragraph labels, heading path, scoped references and review boundaries;
- `structures`: source spans classified as navigation, notices, annotations or contacts;
- `source_instructions_inert`: an explicit boundary protecting consumers from instructions embedded in source material.

Spans use one-based PDF page numbers and zero-based UTF-8 byte offsets, with the end excluded. References record a target, kind and unresolved legal effect. Assertions of success supplied by a parser are not accepted as evidence of a passing case.

## Retained results and independent review

Every attempt remains under [the experiment runs](../evaluation/manual-structure/runs/), including failures. The [attempt notes](../evaluation/manual-structure/runs/attempt-notes.md) distinguish a validator correction from changes to the candidate parser.

| Retained attempt | Result | What the observation establishes |
| --- | --- | --- |
| `baseline-initial-01` | 0/4 | The first baseline adapter also misread an absent per-unit field as legal promotion. This diagnostic mistake is retained and corrected in the next baseline run. |
| [baseline-initial-02](../evaluation/manual-structure/runs/baseline-initial-02/report.json) | 0/4 | The frozen earlier catalogue retains complete excerpts but lacks required governing headings, explicit reference kinds or navigation roles. This is not evidence that all source text was missing. |
| `candidate-initial-01` | 0/4 | Whole passages and governing headings passed, but source citations, navigation classification and the explicit inert-source boundary were incomplete. |
| `candidate-initial-02` then `candidate-expanded-01` | 4/4, then 5/8 | The doubled set exposed unsupported table, abbreviation-table and memo-section structures. |
| `candidate-initial-03` then `candidate-expanded-02` | 4/4, then 8/8 | The text-based fallback met all registered structural expectations. |
| `candidate-initial-04` then `candidate-expanded-03` | 4/4, then 8/8 | The candidate using declared PDF structure met the same expectations. The older report format binds fewer imported inputs. |
| [candidate-initial-05](../evaluation/manual-structure/runs/candidate-initial-05/report.json) then [candidate-expanded-04](../evaluation/manual-structure/runs/candidate-expanded-04/report.json) | **4/4, then 8/8** | After independent review repairs, the same frozen cases passed with complete implementation and consumed-observation bindings; no binding changed during either run. |

Independent synthetic review controls exercise failure modes beyond those eight cases. They found and led to repairs for:

- repeated heading text being assigned to the first occurrence without enough source context;
- a sidecar's changed role being trusted without replaying its retained raw tree;
- an illustrative notice swallowing a later numbered passage;
- annotations split by the size limit inheriting references and offsets from a different fragment.

After the scoped reference and auxiliary-region follow-ups, [candidate-initial-06](../evaluation/manual-structure/runs/candidate-initial-06/report.json) passed **4/4**, followed by [candidate-expanded-05](../evaluation/manual-structure/runs/candidate-expanded-05/report.json) at **8/8**. Both new helper modules are included in those implementation bindings; earlier reports remain unchanged. A later independent source review found a wrapped citation, 77164, being mistaken for a new paragraph inside 77161. The generic cue-based repair then passed [candidate-initial-07](../evaluation/manual-structure/runs/candidate-initial-07/report.json) at **4/4**, followed by [candidate-expanded-06](../evaluation/manual-structure/runs/candidate-expanded-06/report.json) at **8/8**. The original source-bound failure and corrected observation remain in [the auxiliary review records](../evaluation/manual-structure/auxiliary-review/).

The eight review controls now pass. They also check exact Unicode byte offsets, untagged byte conservation, misleading out-of-range headings and nested memo list numbers. They increase confidence in these particular invariants; they do not turn the eight source cases into a representative legal or whole-corpus quality sample.

The separate PDF observer review found an ancestor-text memory amplification risk. Its bounded reparse now counts retained text and joiners before appending them and preserves both the original observations and the genuine bounded failure. See [the PDF observation record](../pdf-structure/README.md).

Independent production controls in [test_structured_context.py](../scripts/test_structured_context.py) check complete-record card commitments, original authored identities, exact reference offsets, global ranking totals, and both copies of directed relationship entries. The [final-generation check](../evaluation/manual-structure/review-controls/corpus-integrity-final-result.json) passed all seven controls, with unchanged manifest, producer and test bindings before and after the run. These are delivery and integrity tests. A source reference remains a navigation observation; it does not establish that the target is legally applicable or closes an evidence requirement.

## What follows the structural experiment

The full **513-document census** and **40 unchanged staff questions** are a separate corpus evaluation. They are not another small experiment with cases added until the score improves.

The [remaining-task review](../evaluation/manual-structure/remaining-task-review.json) maps the 32 previously unprofiled staff questions and their 163 outstanding obligations to the new source locations. All 203 original obligations remain. Eight profile activations out of 40 measures declared task routing; it does not mean that the other 32 questions retrieve no evidence. The location maps are migration leads, not semantic equivalence or automatic closure. Bounded, source-read authoring proposals prioritise PC foundations, household/Housing Benefit direction, and Carer conditions.

That further source reading found memo word-order, paragraph-range and chapter-part references that the first parser missed or narrowed. The separate `manual_references.py` follow-up retains ranges without expanding them, preserves unsupported/multiple qualifiers as unresolved, and inherits list scope only from explicit compatible references. Nineteen controls cover these forms, including financial numbers after an unsupported “at” cue. This follow-up does not retrospectively alter earlier frozen source-case or corpus results. The later four/eight-case runs above bind the integrated helpers; full-corpus comparisons remain separately versioned.

For the whole corpus, measure bytes conserved, document roles, uncertain boundaries, unsupported structures, unresolved headings and references, processing time and output size. Processing a document is not semantic or specialist review.

For the staff questions, keep these measures separate:

- **Discovery relevance:** does the ranked result point to material that could help with the question? Source locations need independent relevance review before reporting precision or recall. The earlier 42 candidate leads are incomplete leads, not a complete answer key.
- **Profile activation:** did an authored task profile activate? This measures declared routing, not answer accuracy. An unprofiled question may still retrieve useful evidence.
- **Whole-unit delivery:** did the consumer receive the complete passage, including examples and qualifications?
- **Relationship and dependency coverage:** were the declared paths preserved, and which referenced definitions, exceptions or other obligations remain unresolved?
- **Claim support:** can an answer's individual statements be traced to sufficient applicable evidence? This needs a separately governed answer evaluation.
- **Delivery size and performance:** what are the selected source bytes, transported bytes, latency and truncation boundaries?

Retain ambiguous-benefit, unknown-benefit, reserved-range, abbreviation-only and conflicting-version controls. If model answers are tested, use a separate fixed-evidence protocol. Neither summary cards nor structural acceptance alone demonstrate better answers or lower cost.
