# Full DMG and ADM metadata census

This is an independent planning snapshot of public GOV.UK publication metadata, acquired on 15 September 2026. It does not extend the existing Pension Credit PDF inventory or claim that any new attachment has been downloaded, extracted or legally reviewed.

## What was retrieved

The 14 JSON responses comprise the DMG collection, its 11 direct publication members, the separate ADM publication and the Universal Credit eligibility guide. Retrieval ran from `2026-09-15T16:55:17.923154Z` to `2026-09-15T16:55:18.464057Z`. The Universal Credit API returns the whole multi-part guide; eligibility is the part with `slug: eligibility`.

| Source family | Publications | Unique PDF URLs | Publisher-declared pages |
| --- | ---: | ---: | ---: |
| DMG grouped volumes, covering volumes 1 to 14 | 9 | 261 | 14,172 |
| DMG memos | 1 | 66 | 534 |
| DMG abbreviations and references | 1 | 4 | 37 |
| **DMG total** | **11** | **331** | **14,743** |
| ADM, separately | 1 | 182 | 4,347 |

There are 513 distinct PDF URLs across DMG and ADM. None was fetched by this census. Page counts above come from GOV.UK metadata, not PDF measurement. All listed PDFs have a declared page count. Every attachment retains its official URL, title and original metadata. Its `content_sha256` is null because no attachment bytes were acquired.

## Evidence and reproduction

- [census.json](census.json): derived counts, classification and complete attachment metadata.
- [receipts.json](receipts.json): request and final URLs, UTC retrieval times, HTTP status, byte length and SHA-256 for each response.
- [api/](api/): exact response bytes. These include publication descriptions and change logs as evidence for interpretation of the metadata.
- [acquire_metadata.py](acquire_metadata.py): standard-library-only acquisition and deterministic derivation.

Run from the repository root:

```sh
python3 source/discovery-2026-09-15/acquire_metadata.py --check
```

This verifies every frozen response hash and reproduces `census.json` without network access. Running without flags regenerates only the derived census from the same responses. `--refresh` refuses to overwrite existing receipts: a future acquisition needs a new dated directory and snapshot date. Initial acquisition used this script with `--refresh` and made no linked attachment requests.

The SHA-256 of `census.json` is `445308cd5cba91d997f21b8408cb8cfeb52e2a888f291492bcdcc41c16c2be88`.

## Classification boundaries

Classes are reproducible inferences from attachment titles and publication membership. `chapter-current-listed` means a chapter file listed on the live publication. It does not mean a legally current or consolidated rule. Transitional and spare chapters are separately labelled. Annexes can contain substantive guidance. Memos are not treated as historical merely because they have old dates. Amendment records and change summaries are separate from chapter text.

DMG statutory abbreviation lists and the ADM statute list are reference aids; their presence does not mean the underlying legislation has been acquired. This census does not recurse through document links or enumerate case law, withdrawn attachments or the complete legislative dependency graph.

Original GOV.UK metadata is Crown copyright and available under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/), except where otherwise stated. Project classifications are unofficial. Exact upstream titles and field names are preserved.
