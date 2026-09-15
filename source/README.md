# Acquired source and extraction evidence

This is a snapshot of the attachments listed on the [DWP publication page](https://www.gov.uk/government/publications/decision-makers-guide-vols-13-and-14-state-pension-credit-staff-guide), observed on 15 September 2026. The publication reports an update on 20 July 2026. Neither date establishes when every passage took effect or whether it applies to a particular claimant.

## Coverage

| Attachment class | Documents | PDF pages |
| --- | ---: | ---: |
| Seven substantive chapter attachments: 77, 78, 79, 83, 84, 85 and 86 | 7 | 744 |
| Chapter 80: transitional provisions | 1 | 14 |
| Chapters 81 and 82: spare | 2 | 2 |
| Volume change summaries | 2 | 7 |
| Historical amendments | 24 | 757 |
| Total | 36 | 1,524 |

All 36 PDFs listed as attachments in the observed GOV.UK content API response were downloaded. Their byte counts and page counts match the publication metadata. The original PDFs total 23,475,769 bytes. The layout-preserving text extraction contains 2,752,384 characters, including page separators and spacing.

This is attachment coverage for this publication, not completeness of Pension Credit legislation, DWP guidance, case law, external memos, or the wider Decision makers' guide. Historical amendments are retained as change evidence and must not be merged into current guidance as if every historical statement still applied.

## Files and provenance

- `publication.json`: original GOV.UK content API response.
- `publication.html`: original publication HTML response.
- `publication-receipt.json` and `publication-html-receipt.json`: requested and resolved URLs, observation times, HTTP metadata and SHA-256 hashes.
- `inventory.json`: all attachment identities, classifications, source URLs, PDF hashes, byte and page counts, observation times and extraction paths.
- `pdf/`: original PDF bytes. Each filename is a stable document identifier.
- `text/`: UTF-8 text produced by `pdftotext -layout`.
- `pages/`: the same extraction split on preserved PDF page boundaries. Each record includes a one-based PDF page index and the authoritative PDF URL with `#page=N`.
- `extraction-quality.json`: integrity checks, known extraction defects and the limited visual sample review.
- `review-samples.json`: seven representative chapter locators and clearly labelled research questions.
- `qa/`: eight PDF-page renders used for model-assisted visual checks, plus a failed alternative extraction sample.

The acquisition snapshot identifier is `dmg-pension-credit-2026-09-15`. Stable source-file hashes, not a date alone, bind evidence to exact bytes. PDF page indices are not necessarily the same as printed page labels.

## Extraction quality

Page boundaries were checked for all 1,524 pages. Of these, 85 pages have no extracted text; these pages have not been individually classified as blank or image-only. No OCR was performed.

Eight PDF pages were visually inspected by the model: chapter 77 page 15; chapter 78 page 27; chapter 79 page 9; chapter 83 pages 3 and 9; chapter 84 page 128; chapter 85 page 4; and chapter 86 page 44. Seven representative samples agreed with the visible wording, allowing for flattened or repositioned superscript footnotes. This is a limited model-assisted comparison, not human review, an accessibility audit or expert validation of the rules.

Chapter 83 page 9 is readable in the PDF but contains substantial spaces within words in extracted text. The `-raw` alternative does not fix this and also separates digits in paragraph numbers. The original extraction is retained, with no speculative normalisation. Other pages may have similar defects. Tables, footnotes, dates, cross-page paragraphs and abbreviations need particular care.

Use page-level evidence as the baseline. A five-digit number is not automatically a complete, operative rule: it may be part of a contents entry, an unused range, a historical example or a cross-reference. Paragraph-level semantic assertions require additional review.

## Reproduce acquisition

Install Poppler so that `pdfinfo` and `pdftotext` are available, then run from the repository root:

```sh
python3 scripts/acquire_sources.py
```

Existing PDFs and publication metadata are reused only after their recorded SHA-256 hashes are checked. Extraction is repeatable from those bytes. A fresh acquisition is an explicit update:

```sh
python3 scripts/acquire_sources.py --refresh
```

The refresh downloads the public publication and its current PDF attachments, then replaces the working snapshot and records new observations. Review the resulting source, inventory, coverage and generated-output changes together before publishing a new version. This acquisition command does not regenerate the model-authored visual-review records; those need a new review if their source hashes change.

## Rights and status

Contains public sector information licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Source: Department for Work and Pensions, Decision makers' guide, volumes 13 and 14. Preserve notices and third-party exceptions; see the repository's `NOTICE.md` and `LICENSE_DECISIONS.md`.

This repository is an unofficial experimental demonstrator. DWP has not endorsed it. Departmental guidance is not legislation, and the extracted or project-authored material does not decide anyone's entitlement.
