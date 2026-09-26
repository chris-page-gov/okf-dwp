# Comparing PDF extraction with LiteParse

This experiment asks whether a different local PDF parser can preserve more
useful structure before OKF builds passages. A **parser** is a program that
reads a file and identifies its contents. A **passage** groups guidance that
belongs together; it can span several PDF pages.

The Department for Work and Pensions (DWP) publishes the **Decision makers'
guide (DMG)** and **Advice for decision making (ADM)**. This is an independent
experimental comparison of frozen copies, not official guidance or an
assessment of current entitlement.

## Result: useful signals, no replacement admitted

The first run on **26 September 2026** processed **12 windows covering 15 PDF
pages**. All extractions completed, original page indices matched and the
reported block rectangles were within their page bounds. The retained report
verifies offline, but **the source-quality gate failed**.

| Check | Observed result | What it means |
| --- | --- | --- |
| Exact declared anchors, allowing only the frozen whitespace rules | 8 of 12 windows pass | The four failures need interpretation; they are not four established losses of substantive guidance. |
| Amendment Remove/Insert table | Fails | Only its first four rows became a typed table. Later chapter references became headings and paragraphs, losing the declared cell associations. |
| Capital-band table | Fails the complete table check | The three expected numeric rows occupy the correct columns. However, the column headings are not fully associated: the top heading is outside the table, while `From £` and `To £` are combined cells. |
| Known case 014 | Literal content passes the declared whitespace-insensitive check | Extracted words remain letter-spaced. This has not repaired the existing extraction defect. |
| Both text and structure checks together | 7 of 12 windows pass | This is a small source-selected diagnostic set, not a whole-corpus accuracy estimate. |

The four exact-anchor failures are in s1-02, s1-03, s1-10 and s1-12. Inspection
finds curly quotes/apostrophes changed to straight forms, en dashes changed to
hyphens, and a superscript footnote marker joined to adjacent words. In s1-02,
the example sentence is present with a straight apostrophe. Its literal failure
does not establish a broken cross-page example. The frozen test intentionally
does not normalise these characters; we retain its failure and describe the
representation difference separately.

The observed total subprocess elapsed times were 0.598 seconds for LiteParse
and 0.478 seconds for Poppler across the 12 windows. Each case ran once on the
same Mac. Different output richness and startup/cache effects prevent a general
speed comparison. No answer-model or defect-detector calls were made.

**The 24 reserved windows and conditional 40-question replay did not run.**
The published extraction and passage-builder defaults are unchanged. A useful
next experiment would evaluate a separately versioned **spatial sidecar**:
additional coordinates and table suggestions linked to the original PDF, with
uncertain alignments kept visible. It would need to address header association,
partial tables and reversible punctuation alignment before another admission
gate. We have not demonstrated improved retrieval or better benefits answers.

Read the [retained run](../evaluation/liteparse-pilot/stage-1-001/REPORT.md),
[machine-readable metrics](../evaluation/liteparse-pilot/stage-1-001/report.json)
and [review record](../validation/liteparse-pilot/README.md). In the generated
case table, a structure pass on a non-table case means no table expectation
was declared; it is not a general structural assessment.

## Why compare another extractor?

Our retained Poppler extraction preserves text, spacing and page locations.
Separate PDF structure tags supply some headings, lists and tables. They do
not give the current passage builder a complete, reliably aligned map of text
coordinates and table cells.

LiteParse can return **blocks** labelled as headings, paragraphs, lists and
tables, together with **bounding boxes**: rectangles locating their content on
the PDF page. Its optional complexity signals distinguish pages needing OCR
(text recognition from an image) from readable pages with difficult layouts.
Those signals are heuristics, not proof that a page was read correctly.

The first source inspection found that the PDF for known boundary case 014 is
visually readable while its frozen extraction inserts spaces within words.
The pilot therefore preserves the old extraction and compares another reading
of the same PDF. It does not assume that better spacing proves a correct
passage boundary.

## What is fixed before execution?

The [protocol](../domain-profile/liteparse-pilot/protocol.json) and
[case catalogue](../domain-profile/liteparse-pilot/cases.json) specify the
selected page windows, original PDF and extraction fingerprints, expected text
and table relationships. A SHA-256 **fingerprint** identifies exact file bytes;
it does not establish that an interpretation is correct.

- Stage 1 uses 12 varied windows, including amendment navigation, a substantive
  table, damaged extracted spacing, DMG and ADM, and existing cross-page controls.
- Stage 2 reserves 24 fresh, disjoint windows. It runs only if the declared
  stage 1 gate passes. These examples are new to the candidate parser, not a
  blinded or independently human-reviewed sample of the whole corpus.
- Wider comparison is conditional: the 28 known outliers, nine substantive
  chapter controls and 40 staff questions require passing source checks and a
  separately tested passage-assembly adapter. Page order alone does not prove
  that a qualification remains joined to its governing paragraph.

The proposed source expectations were prepared with GPT-6 Sol at medium
reasoning and checked against source PDFs where recorded. Integration and
review remain separate. These are model-assisted engineering checks; no
independent benefits-specialist acceptance is claimed.

## Cost and preservation

LiteParse 2.14.6 runs in an [isolated locked environment](../tools/liteparse-pilot/README.md).
The parser trial makes no LLM answer or model defect-detection calls. Codex
implementation and review still use the owner's subscription allowance.
OCR and remote processing are disabled. Small text, headers and footers are
explicitly retained rather than silently discarded as page decoration.

The runner has a 240-second subprocess timeout and checks retained-output size
bounds. Temporary files can grow during execution before those checks.
On failure it records diagnostics, hashes and any truncation explicitly. These
are bounded retained artefacts, not a claim of operating-system memory isolation.

Both extraction versions remain separate and refer to the same frozen PDF.
Changing extractors can legitimately change spaces, characters and reading
order. The experiment reports differences and uncertain alignments; it never
overwrites the frozen page text or reuses its byte offsets for different text.

Cache entries bind the PDF fingerprint, page window, parser implementation and
settings. Unchanged, hash-checked entries can be reused. A cached runtime is
not a new timing measurement. Wall-clock observations include process startup
and are not a general speed benchmark.

## How to interpret a result

1. **Source reconstruction:** did the parser retain the declared text, reading
   order and table-cell associations, with valid page coordinates?
2. **Passage construction:** did numbered paragraphs, examples and exceptions
   stay together? This needs a tested assembly adapter and source review.
3. **Retrieval:** do the same staff questions retain more of the expected
   evidence with the same limits? The conditional comparison keeps 512 KiB,
   64 records, 128 relationships and traversal depth six in both arms.
4. **Answerability:** are all applicable qualifications and legal dependencies
   established? Successful parsing does not settle this question.

The existing [passage-boundary replay](passage-boundary-review.md) retains all
40 insufficient staff packages. This experiment must measure a new result
before claiming improvement. A failed early gate is retained evidence and
stops the larger run; it is not permission to relax the expected source text
or rerun until a preferred outcome appears.

## Reproduce and check

Set up the existing repository validation environment with `uv sync --locked`.
For an **offline check of the retained result**, no LiteParse installation or
new DWP extraction is required. The unit suite also checks a synthetic five-page
PDF when the optional candidate is installed; CI skips that runtime-only test:

```sh
uv run --locked python -m unittest discover -s scripts -p test_liteparse_pilot.py
uv run --locked python scripts/run_liteparse_pilot.py --check --output evaluation/liteparse-pilot/stage-1-001
```

To perform a **new extraction**, separately install the pinned candidate with
`uv sync --locked --project tools/liteparse-pilot` and have Poppler's
`pdftotext` executable available. Use a new directory so an earlier result
cannot be overwritten:

```sh
uv run --locked python scripts/run_liteparse_pilot.py --stage 1 --output evaluation/liteparse-pilot/stage-1-new-observation
```

Stage 2 requires `--stage 2`, a new `stage-2-…` output directory and
`--stage1-dir` pointing to a verified, passing stage-one result. Changing the
parser, rules, fixtures or settings requires a separately versioned experiment;
a failed frozen run stays failed. The initial fixture freeze is commit
`b8a6013b`. Hashes and committed artefacts make the experiment reproducible;
they are not signatures or independent certification of a local machine.

CI recomputes the retained metrics offline. It does not silently install or run
a different PDF parser, and a valid record of a failed experiment is a passing
integrity check.

## Upstream material

- [LiteParse September 2026 update](https://www.llamaindex.ai/blog/liteparse-updates-september-2026).
- [Structured extraction options](https://developers.llamaindex.ai/liteparse/guides/extraction/).
- [Document complexity signals](https://developers.llamaindex.ai/liteparse/guides/complexity/).
- [LiteParse source and licence](https://github.com/run-llama/liteparse).

Upstream benchmarks justify a local comparison. They do not measure the DMG
and ADM's cross-page qualifications or the project's 40 staff questions.
