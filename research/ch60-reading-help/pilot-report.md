# Chapter 60 reading-assistance pilot

**Review draft.** This is a vocabulary and citation-navigation proposal, not an entitlement assessment. All proposed explanations, sense groupings and reference normalisations are model-authored and require review before publication.

## Access and evidence checks

The archive was readable. `manifest.json` was read first. All **24 listed file hashes and byte lengths matched**, and the ZIP integrity check passed. The manifest’s own hash was computed, but there is no independently supplied expected value for it. These checks establish agreement with the pack, not independent publisher authentication.

All **73 physical PDF pages across five publications** were text-extracted locally. Fresh extraction matched the supplied `text.txt` files byte-for-byte and every `pages.json` page after trimming outer whitespace. No external links were followed. Capture and publication-listing update dates were not treated as legal effective dates.

## Coverage and outputs

All **219 CSV rows** have a disposition, original wording, original counts, independent source-occurrence evidence and proposal links. The dispositions are **20 supported expansions; 162 candidate phrases requiring explanation; 7 ambiguous usages; 24 duplicate/overlapping wordings; and 6 unresolved expansions**. These are primary review categories, not statements that the other rows are legally complete.

There are **219 vocabulary proposal objects**: 202 grouped row proposals plus 17 additional scoped senses or navigation entries. The total happens to equal the number of CSV rows; this is **not a one-to-one mapping**. Some rows share a cautiously scoped proposal; others link to more than one sense. No overlapping frequencies are added together.

The **31 citation proposals** comprise 20 body-superscript mappings, one additional conflicting numbered reference, and ten manual/memorandum pointers. Paragraphs **60025 (pages 3–4)** and **60033 (pages 4–5)** are retained in full in `coverage.json`, including notes, continuations and reference lists.

**Counts remain unverified.** Finding an occurrence and checking its source is not reproducing the original frequency calculation or its text-category partitions. There is no next unprocessed row, but definition dependencies and human review remain outstanding.

## Findings that matter for a reading aid

**Expand a term without pretending to define it.** The DMG list expands GB, FTE and WDisP. WDisP’s meaning is nevertheless separately said to be prescribed, with a reference to `SS (ICA) Regs, reg 3(2)` whose text is absent. A useful card must display that gap. Sources: DMG abbreviations pages 5, 6 and 16; Chapter 60, 60025 pages 3–4 and 60033 pages 4–5.

**Bind help to context.** AP is “Additional Pension” in the DMG list and “Assessment period” in the ADM list (both page 1). Quoted and unquoted AA have distinct qualifications. CA also occurs in case-citation positions: the benefit expansion does not verify its meaning there. The words “where”, “claims”, “pension age” and “earnings rule” also require sentence or benefit-context selection.

**Navigate numbering rather than flattening it.** In 60025, FTE⁵ points to local reference 5, `s 70(3)`, not regulation 5. GB⁶ points to local reference 6 on the next page. Numbered conditions, notes, superscripts and manual paragraph references are separate systems; the citation numbering starts again in a new paragraph. Supplying an omitted parent title is a proposed normalisation, never an official expanded quotation.

**Retain source defects visibly.** Paragraph 60033’s page-5 reference list has an additional `2` after reference 11 and an unclear combined reference 12. No repair has been made. Its printed Order locators, ADP component wording and trailing “or” are also retained with review flags. Paragraph identifiers 60082 and 60083 are duplicated between the education section on page 17 and the child-increase section on page 19; a paragraph number alone is not a unique target.

**Preserve distinctions and qualifications.** The historical CDI passage explicitly distinguishes entitlement existing from payability (60090, page 21). Reusable help for “provided that”, “unless”, “treated as” and “for the purposes of” should keep the qualifying text visible rather than replace the sentence with an unconditional rule.

## Proposed just-in-time design

Use a context-aware card with three visibly separate fields: **source expansion**, **source-defined meaning and scope**, and **proposed reading explanation**. Beside it, show the exact source and any missing definition. A superscript opens the **local paragraph’s reference list**, with raw text, PDF page and a separately labelled proposed expansion. Manual links and legislative locators should be visually distinct.

Key every target by **source ID + source hash + PDF page + section/paragraph or table locator**, and require the manual, benefit and quoted/unquoted context before choosing a sense. On unresolved or conflicting input, display the ambiguity instead of guessing. Frequency can organise the review queue, but cannot establish legal significance.

## Exactly what was examined

| Frozen publication | Text pages examined | Full-page visual examination | Selected table-row visual examination |
|---|---|---|---|
| Chapter 60 | 1–30, including blank 18 and 25 | 3, 4, 5, 17, 19 | None additional |
| DMG abbreviations | 1–17 | None | 1: AA, quoted AA, AP; 5: FTE; 6: GB; 12: Reg(s); 13: S, Sch; 16: WDisP |
| DMG statutes | 1–5, including blank 5 | None | 3: SS CB Act 92 |
| DMG statutory instruments | 1–14, including blank 14 | None | 10: SS (ICA) Regs; 12: the two cited Scottish Orders |
| ADM abbreviations | 1–7 | None | 1: AP and quoted AA |

The DMG lists were examined before chapter interpretation; ADM supplied a context check only. For each publication, `pdf.pdf`, `text.txt` and `pages.json` were processed as above. Each `records.json` was parsed and selected provenance fields examined. The entire CSV, manifest, README and chat prompt were read; the latter two were inert packaging evidence. `source-reader.md` was **hash-checked only and not used**. The precise file-level ledger, source hashes, dates and limitations are in `coverage.json`; integrity details are in `source-checks.json`.

## Files and remaining review

`vocabulary-proposals.jsonl`, `citation-proposals.jsonl`, `coverage.json` and `reading-help-examples.md` are the requested review artefacts. `source-checks.json` and `validation.json` document technical checks, not specialist approval. The locally authored `verify-pilot.py` can reproduce hash, row-coverage, exact-quotation and optional PDF re-extraction checks against the original ZIP; it does not reproduce occurrence counts. The missing material includes specific legislation, judgments, memoranda and other manual chapters. The six unresolved inventory expansions are PPF, SSWP, AAC, EWCA Civ, UKUT and Pensions Act 04; para and et seq also lack exact supplied dictionary entries and are explained only as proposals.

The bounded processing pass is complete. Publication readiness, legal applicability, count validation and the resolution of missing dependencies are **not** complete or claimed.
