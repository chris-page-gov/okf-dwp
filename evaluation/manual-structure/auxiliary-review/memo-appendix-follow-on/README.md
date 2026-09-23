# Memo references and appendix boundaries

This independent source review follows two defects found by the complete-corpus
outlier check. It adds regression controls without changing earlier experiments,
source captures or published projections. The source expectations and generic
repair were developed concurrently; this was not a blinded or preregistered
experiment.

## Source findings

- **ADM memo 06/21, PDF page 5:** `C2130` begins an extracted line, but continues
  `see ADM` inside memo paragraph 11. It is a reference, not the memo's own
  numbering. The actual annotation list is separate, on page 21. The
  [rendered source page](adm06-21-page5.png) shows the paragraph and reference.
- **DMG volume 8 amendment 27, PDF pages 107–109:** paragraph 44650 includes
  Example 1 on [page 107](dmg-amendment27-page107.png) and the complete Example 2
  on [page 108](dmg-amendment27-page108.png). A separate Appendix 3 starts on
  [page 109](dmg-amendment27-page109.png). The historical PDF's extracted heading
  is `A p p e n di x 3`. Its spacing is an extraction artefact, not a reason to
  attach the appendix to paragraph 44650.

The [source fixtures](source-fixtures.json) bind the original PDF, extraction and
inventory hashes, exact source spans and expected limits. They retain the
historical amendment role. The images were rendered from those frozen PDFs with
`pdftoppm`, at a maximum dimension of 1,100 pixels, and visually inspected.
They are source-review aids under the repository's [source notice](../../../../NOTICE.md).

## Retained checks

The [previous-parser observation](before-repair.json) rejects all three final
controls. The [repaired-parser observation](after-repair.json) passes all three:

1. The wrapped memo citation never becomes a main paragraph.
2. Actual source-declared memo sections and final annotation references remain
   separate, with legal dependency status unresolved.
3. The appendix starts a new section after the full continuation example, while
   every original source byte remains accounted for.

[The implementation review](integration-review.json) binds the reviewed code,
source-tree inputs and tests. The repair is generic: memo inventory roles govern
the numbering distinction; standalone appendix literals create boundaries. It
does not contain these document identifiers or paragraph numbers.

An [initial reviewer expectation failed](initial-review-expectation-failure.json):
the test expected the visible “Past presence test” topic to be an admitted PDF
heading tag. That was not supported by the retained tree alignment. The
[initial test](initial-review-test.py) is preserved. The corrected control uses
the genuinely admitted Introduction and Background headings. This correction
does not establish fine-grained memo structure: the Background section still
spans pages 2–8, and its complete legal dependencies remain unknown.

## Reproduce the bounded controls

```sh
uv run --locked python -m unittest discover -s scripts -p 'test_manual_memo_appendix_sources.py' -v
```

These tests read frozen local evidence and replay existing PDF structure. They
do not acquire source documents, run Poppler, rebuild the corpus or call a model.
Exact byte coverage, source-declared headings and passing boundary controls do
not establish legal applicability, answerability or specialist acceptance.

[The artefact manifest](artifact-manifest.json) binds this follow-on evidence;
the earlier auxiliary and wrapped-reference manifests remain unchanged.
