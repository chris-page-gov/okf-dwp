# Source refresh and drift

**Observed on 20 September 2026.** A *refresh* checks a newer source observation.
*Drift* means a recorded difference from an earlier observation. Neither word
means that the published evidence bundle has been replaced.

The new [official metadata observation](../source/discovery-2026-09-20/manifest.json)
checks the DMG collection, its 11 publication pages and the ADM publication page.
It made **13 bounded API requests**, retaining **1,043,407 bytes** of official
listing metadata. All requests succeeded. No PDFs were downloaded and no existing
source or live-service binding changed.

## Actual result

The [generated comparison](../evaluation/source-refresh/observed-comparison.json)
accounts for all **513 attachments** in the earlier acquisitions: 331 DMG and
182 ADM PDFs. Their attachment identifiers are still present. No added or removed
attachments, changed comparable metadata or changed DMG collection links were
observed in this snapshot.

**The contents of all 513 PDFs remain unknown in this fresh observation.**
Matching a title, size, attachment identifier or download address does not prove
that a PDF has unchanged bytes. Extraction hashes are also unknown because this
refresh did not redownload or re-extract the documents. The old acquisitions keep
their original verified hashes; those hashes are not copied into the new
observation as if they had been measured again.

## What the comparator distinguishes

| Result | Meaning |
| --- | --- |
| Added | A newly observed attachment identity is absent from the earlier census |
| Removed | An earlier identity is absent from a successfully observed complete attachment list |
| Presence unknown | Its publication was unavailable or outside the declared request budget |
| Metadata changed | Comparable title, URL, declared size/pages, date or classification differs |
| Content changed/unchanged | Both observations contain measured source hashes that differ/match |
| Content unknown | At least one observation has no measured source hash |
| Extraction changed/unchanged/unknown | A separate comparison of extracted-page-file hashes |

“Removed” is an attachment-list observation, not a declaration that a provision
was repealed or a document disappeared from every official service. A changed
URL with the same attachment identifier is reported as a metadata change. Where
an attachment identifier is absent, the exact URL is the fallback identity;
replacements then need manual reconciliation. Duplicate identities fail closed.

Publication-page update dates remain publication-page dates. They are never
substituted for PDF publication dates or legal commencement. A fresh listing does
not inherit the earlier snapshot's semantic classification merely because its
title matches; the new classification is explicitly unknown.

## Review before changing a demonstration

1. Inspect added, removed and changed entries, plus all unknown outcomes. A failed
   publication request must not be mistaken for hundreds of document removals.
2. Acquire changed or uncertain bodies into a **new** snapshot if needed. Preserve
   earlier files and hashes. Check extraction quality separately from byte changes.
3. Identify the affected paragraphs, semantic proposals, task profiles, evaluation
   cases and fixed-evidence model trials. Changes in law need the relevant legal
   and policy review, not just a successful download.
4. Rebuild additive projections and rerun their checks against explicit source
   versions. Review their proposed publication before changing an approved
   runtime binding or Monday demonstration link.

This run completes the bounded observation and comparison mechanism. It does
not approve a future legal or service-version transition.

## Reproduce

These commands are offline and preserve old source files:

```sh
uv run --locked python scripts/compare_source_census.py
uv run --locked python scripts/compare_source_census.py --check
uv run --locked python -m unittest discover -s scripts -p test_source_census.py
```

The [baseline self-check](../evaluation/source-refresh/baseline-self-check.json)
compares the frozen inventories with themselves. It establishes comparator
consistency, not fresh source currency. The
[synthetic controls](../evaluation/source-refresh/synthetic-controls.json)
exercise real differences, removals, additions, failed requests and unknown
content. They are explicitly labelled synthetic.

The separate network operation is:
`uv run --locked python scripts/compare_source_census.py --acquire`.
It refuses to overwrite the dated observation. A future acquisition requires a
separately named destination and reviewed policy. The
[refresh policy](../domain-profile/source-refresh-policy.json) limits the run to
20 official metadata requests, 8 MiB per response and 64 MiB in total. It permits
no linked PDF downloads.

## Evidence retention

Unlike the legal-provision metadata-only projection, this refresh retains the
complete **GOV.UK content API metadata responses**. The manifest and request
receipts bind their exact bytes, enabling offline reconstruction of the listing
census. These responses contain publication metadata and attachment links; they
do not contain the linked PDF bodies. No private correspondence or claimant
records were consulted.

This remains an independent experimental publication, not official DWP guidance.
