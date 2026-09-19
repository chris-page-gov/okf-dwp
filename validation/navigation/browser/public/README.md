# Public conceptual navigation observation

On 19 September 2026, the Chrome acceptance journey passed against the actual
published Explorer and the pinned public DWP navigation projection. The browser
fetched both application and corpus files directly over HTTPS; no responses
were substituted.

[Open the tested Explorer and corpus](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F0c59f476602a49d4293e46112a0ca1ebf1486ff0%2Ffull-dmg%2Fokf-review-context.json#overview).

## What passed

| Conceptual filter | Selected value | Records in Reader, Graph and Timeline |
| --- | --- | ---: |
| Benefit mentions | Guarantee Credit | 74 |
| Circumstance mentions | Imprisonment and detention | 343 |
| Topic mentions | Work and work-related requirements | 268 |
| Authored concept references | AA, DLA care and CA classification in the cited EU regime | 1 |

Each indexed filter count matched the loaded Timeline records. The sampled
records appeared under capture/audit dates and disappeared when only source
dates were selected. Where more than 80 dated groups were in scope, the
Timeline displayed the limit and the number shown. Capture records when the
project acquired material; it does not establish the source publication date.

There were no browser console errors, page errors or axe accessibility
violations in the checked facet and Timeline controls. This targeted check
does not establish accessibility conformance for the whole application.

The check independently verified all **21 application files** named by the
build manifest and all **188 corpus files** observed during the journey.

## Exact publication and evidence

- Explorer merge: `8a38d4bfe07a6797deacc148a2859911d8e2a68e`,
  [pull request 125](https://github.com/chris-page-gov/okf-explorer/pull/125).
- [Pages run 35469396749](https://github.com/chris-page-gov/okf-explorer/actions/runs/35469396749)
  completed successfully before the browser check.
- DWP corpus commit: `0c59f476602a49d4293e46112a0ca1ebf1486ff0`.
- Browser observation: `2026-09-19T21:16:55.729Z`.

| Content identity | SHA-256 |
| --- | --- |
| Explorer build manifest | `7ced69ae616349759f47557842aaab5cf9614b3cfe82d837abc1ec6d287e0714` |
| Explorer application tree | `752b04a06c79d486d9cea0ebfb4618fdc944226c8f7be67e19a6f95cc01e31f9` |
| DWP navigation descriptor | `9bbb8694f63e1832c03f2a1dfe2291bd59344f6e33a72b780775bdfce68c9fbb` |

Commit and workflow identifiers describe the publication history. The content
hashes identify the exact bytes independently; neither substitutes for the other.

- [Browser observation](observation.json): filters, counts, date roles,
  accessibility results, limitations and all observed corpus file hashes.
- [Deployment provenance](deployment.json): exact URLs, commits, Pages run
  and test harness identity.
- [Reader screenshot](benefit-reader.png): benefit selection and the explicit
  unreviewed-classification disclosure.
- [Timeline screenshot](circumstance-timeline.png): capture dates and the
  bounded display.
- [Artefact hashes](artifacts.json): retained file sizes and SHA-256 values.

The screenshots were visually inspected before retention. Raw traces and
browser metadata remain outside the repository. The [earlier local observation](../README.md)
has not been overwritten.

## Scope

This public Reader projection covers DMG material. The separate Ask OKF corpus
also includes ADM; this browser observation does not establish ADM Reader
coverage. Classifications support discovery and remain unreviewed. A literal
mention does not establish that a rule applies, and an unclassified record
does not establish that the subject is absent.

These are dated observations, not perpetual deployment assurance, a check of
current law, or a test of AI answer quality.

## Repeat the journey

Use the Explorer repository's documented locked installation. With the pinned
DWP files available locally for independent hash comparison, run from Explorer:

```sh
OKF_CONCEPT_CORPUS_ROOT="$HOME/repos/okf-dwp/full-dmg" \
OKF_CONCEPT_OUTPUT="/tmp/okf-dwp-public-navigation-repeat" \
OKF_CONCEPT_BUNDLE_URL="https://raw.githubusercontent.com/chris-page-gov/okf-dwp/0c59f476602a49d4293e46112a0ca1ebf1486ff0/full-dmg/okf-review-context.json" \
OKF_CONCEPT_APP_MANIFEST_URL="https://chris-page-gov.github.io/okf-explorer/okf-explorer-build-manifest.json" \
OKF_CONCEPT_APP_MANIFEST_SHA256="7ced69ae616349759f47557842aaab5cf9614b3cfe82d837abc1ec6d287e0714" \
PLAYWRIGHT_BASE_URL="https://chris-page-gov.github.io/okf-explorer/explore/" \
pnpm --dir apps/okf-explorer exec playwright test \
  tests/ui/conceptual-corpus-acceptance.spec.ts --project=chrome
```

The supplied hashes deliberately reject a different application or corpus.
For a later release, use its independently verified identities and retain a
new observation. Do not overwrite this one.
