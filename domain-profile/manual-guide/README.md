# Source-linked manual guide

This additive authoring layer explains how to read the captured **Decision makers’ guide (DMG)** and **Advice for decision making (ADM)**. Both are Department for Work and Pensions (DWP) guidance. This project’s guide is an independent reading aid, not departmental or specialist acceptance.

## What the guide contains

`guide.yamlld` is JSON-compatible YAML-LD: structured YAML data with an inline Linked Data context and stable identifiers. It contains source-supported observations and a suggested learning sequence. The schema is [`profiles/manual-guide/v1/manual-guide.schema.json`](../../profiles/manual-guide/v1/manual-guide.schema.json).

Twenty page-text conventions cite 30 exact excerpts from 15 documents. A further convention adds four explicitly separate quotations from retained PDF structure trees, bringing the directly supported document count to 16. The 21 conventions cover document roles, chapter and benefit scope, local definitions, numbering, mixed contents and body text, cross-page conditions, examples, notes, citations, abbreviations, statutes, statutory instruments, memos, update histories and declared PDF structure. **These are scoped examples, not a reviewed grammar for all 513 documents.**

A **regime** is the particular set of rules and conditions being discussed, such as old style or new style Employment and Support Allowance. A **memo** is supplementary guidance whose scope and dates need checking. A **statutory instrument** is a form of legislation; the abbreviation tables identify instruments but do not contain their operative legal text.

## Sources, observations and suggestions are different

- Source support contains an exact PDF URL, PDF page number and a half-open UTF-8 byte range into the frozen extracted page text, with its SHA-256 checksum. The checksum is a fingerprint used to detect changed bytes. The generated document record binds that page extraction and PDF to the frozen inventory.
- A convention’s confidence distinguishes a direct source statement from an observed extracted-text layout. Its scope names only directly supported documents and excerpts. A source statement can itself be incomplete, historical or in tension with another statement.
- Every document retains its original inventory role. The generated marker census records signs such as `Subpages`, `Note:` or a paragraph number; it does not declare a complete rule, heading hierarchy or legal applicability.
- The frozen PDF metadata reports 427 documents as tagged and 86 as untagged. A tagged PDF can contain declared structure such as headings or lists, but this flag alone does not verify the structure, reading order or accessibility. Actual inspection and matching to frozen text are separate work.
- Declared-tree quotations bind the PDF, the retained Poppler observation, its raw tree and the bounded parser replay. Their line numbers locate the tree output, not a PDF page. Heading/list tags are source-backed structural candidates; matching their text to frozen page offsets is a separate operation. Partial or unavailable structure cannot support this convention.
- Learning prerequisites describe a useful reading order. They are project-authored suggestions and **do not assert legal dependencies**. Source references and memo annotations still need exact-target and applicability review.
- The conflicting footer statements in Volume 1 Amendments 60 and 61 are both retained. The reference role and quotation-sensitive abbreviations are also preserved. Source instructions, including printing instructions, remain inert data.

## Reproduce and review

```sh
uv run --locked python scripts/build_manual_guide.py
uv run --locked python scripts/build_manual_guide.py --check
uv run --locked python -m unittest discover -s scripts -p 'test_manual_guide.py'
```

The producer verifies the exact inventories, PDFs and extracted pages before constructing `manual-guide/`. It accounts for 331 DMG and 182 ADM documents, including historical amendments and reference lists. It follows each inventory’s exact paths, including reused pilot captures. It does not acquire new sources, overwrite earlier logical units or promote a title-based classification to reviewed scope.

`manual-guide/documents.jsonl` contains one JSON object per PDF. `guide.json` contains the reading conventions. `manifest.json` binds the producer, schema, authoring and source inputs to the generated outputs. Builds contain no wall-clock timestamps; rerunning `--check` must find the same bytes. Marker samples are explicitly bounded and omitted samples are counted.

For another department, first freeze and inventory the manual sources, then author source-supported reading conventions and ambiguous cases, preregister independent structural tests, and only then evaluate a candidate parser. This guide supplies orientation and testable source observations; coherent-unit parsing, discovery cards and legal dependency review are separate stages.
