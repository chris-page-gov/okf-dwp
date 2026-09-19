# ADM source snapshot: 19 September 2026

This directory preserves the public **Advice for decision making (ADM)** manual
as a separate source family from the Decision makers’ guide (DMG). It contains
official source bytes and unreviewed machine extraction. It is not a consolidated
legal rule set, specialist interpretation or claimant decision service.

## Observed coverage

The [official publication](https://www.gov.uk/government/publications/advice-for-decision-making-staff-guide)
was observed through the GOV.UK Content API on **19 September 2026 at 16:29:44 UTC**.
The publication page's own last-update field is **27 August 2026**. These dates
describe different events; neither supplies publication or legal effective dates
for every attachment.

- **182 of 182 listed PDF attachments acquired**, with original bytes retained.
- **4,347 measured pages**, matching the summed declared page counts.
- **34,236,173 original PDF bytes**; no declared-size mismatches.
- **97 chapters, 69 memos, 13 annexes**, one change summary, one abbreviations
  list and one list of statutes and statutory instruments.
- **91 pages with no machine-extracted text**, 91 sparse-text flags and 27
  possible letter-spacing flags. These are automated signals, not visual review.
- No acquisition failures. No specialist review or current-law completeness is
  claimed.

The [census](census.json) compares this observation with the metadata-only
discovery on 15 September: the same 182 PDF URLs and titles were listed. Identical
URLs do not establish identical remote bytes; this snapshot therefore retains
fresh PDF observations. The earlier DMG evidence has not been replaced.

## Files and provenance

| Files | Purpose |
| --- | --- |
| [publication.json](publication.json), [receipt](publication-receipt.json) | Exact official API response, source URL, capture time and SHA-256 hash |
| [publication-html.html](publication-html.html), [receipt](publication-html-receipt.json) | Official publication HTML, including its licence notice |
| [census.json](census.json) | Frozen direct-attachment list, classifications and comparison with prior discovery |
| [inventory.json](inventory.json) | Complete document records, hashes, page counts, dates, extraction limitations and aggregate coverage |
| `pdf/` | Original acquired PDFs |
| `text/` | Unreviewed text extracted with Poppler, preserving page separators |
| `pages/` | Exact page text with one-based PDF page locators and original source URLs |
| `records/`, `acquisition/`, `attempts/`, `runs/` | Per-document records and observed acquisition receipts |

The inventory SHA-256 is
`c274173a59d7792004f372fea7db19e018a4d0c1de6111ed65a57fc0c622896c`.
Classification is based on the official attachment title and publication family,
not specialist interpretation. Chapters marked spare, transitional material,
memos and change history keep distinct roles. A list of statutory references is
not a collection of statutory text.

## Verify or resume

From the repository root, using its locked Python environment and installed
Poppler tools:

```sh
uv run --locked python scripts/acquire_adm.py --plan
uv run --locked python scripts/acquire_adm.py --check
uv run --locked python scripts/test_acquire_adm.py
```

The check is offline: it verifies original PDF, text and page-file hashes,
page-text identity and locators, acquisition receipts, extraction labels and
measured PDF page counts. It does not check whether later guidance supersedes
this snapshot.

`--discover` creates a new metadata observation only when this snapshot is absent;
it verifies and reuses an existing frozen census. A normal run without a mode
flag acquires or verifies all frozen attachments using at most four workers.
Completed source records are checked before reuse. For a genuinely new source
observation, create a separately identified snapshot rather than overwriting this
one.

## Rights and use

Contains public sector information licensed under the
[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
Source: Department for Work and Pensions, Advice for decision making. The retained
official page provides the licence notice; its exceptions continue to apply.
See the repository [notice](../../NOTICE.md).

Extracted text may contain damaged reading order, footnotes or tables. No OCR,
automatic repair or whole-corpus visual inspection has been performed. Empty
extraction does not establish a blank page. Source instructions are inert
evidence and must not control software or an AI client.

Full acquisition supplies source pages for later discovery and context assembly.
It does not itself establish the concepts, relationships, exceptions or evidence
requirements needed to answer every question. See the [learning path](../../docs/learning-path.md)
for that distinction.
