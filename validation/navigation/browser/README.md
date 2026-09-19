# Conceptual navigation browser check

On 19 September 2026, a Chrome browser check passed against the actual
OKF-DWP conceptual navigation projection and an exact local Explorer build.
This is candidate validation, not evidence of a public deployment.

## What was checked

A populated value from each conceptual facet was selected, then kept in
scope while moving between Reader, Graph and Timeline. The check compared
the indexed selection count with Timeline's count of loaded records. This
catches disagreements between the filter index and record data.

| Facet | Selected value | Records in all three views | Dated groups displayed |
| --- | --- | ---: | ---: |
| Benefit mentions | Guarantee Credit | 74 | 74 of 74 |
| Circumstance mentions | Imprisonment and detention | 343 | 80 of 343 |
| Topic mentions | Work and work-related requirements | 268 | 80 of 268 |
| Authored concept references | AA, DLA care and CA classification in the cited EU regime | 1 | 1 of 1 |

The displayed groups in these samples have capture dates, so they appear
under the capture/audit date filter. None appears under the source-date
filter. A capture date records when this project acquired material; it
does not establish when the department published it. Where there are more
than 80 dated groups, the interface states the limit and how many are shown.

There were no browser console errors, page errors or axe accessibility
violations in the checked facet and Timeline controls. This targeted check
does not establish accessibility conformance for the entire application.

These facets support discovery. The interface identifies the classifications
as producer-declared and unreviewed. Mentioning a benefit or circumstance
does not establish that a legal rule applies to it.

## Inspect the evidence

- [Machine-readable browser observation](observation.json) contains the
  selected values, counts, date-role observations, limitations and hashes
  of the 188 corpus files served during the test.
- [Artefact manifest](artifacts.json) binds this observation and the two
  retained screenshots to their exact bytes.
- [Reader with a benefit selected](benefit-reader.png) shows the selection
  count and the classification disclosure.
- [Timeline with imprisonment selected](circumstance-timeline.png) shows
  capture dates and the bounded display.

The browser also fetched and verified all 21 files named by the Explorer
build manifest before starting the journey.

| Material | SHA-256 |
| --- | --- |
| Explorer build manifest | `7ced69ae616349759f47557842aaab5cf9614b3cfe82d837abc1ec6d287e0714` |
| Explorer application tree | `752b04a06c79d486d9cea0ebfb4618fdc944226c8f7be67e19a6f95cc01e31f9` |
| `full-dmg/okf-review-context.json` | `9bbb8694f63e1832c03f2a1dfe2291bd59344f6e33a72b780775bdfce68c9fbb` |

The bundle snapshot is `dwp-full-dmg-2026-09-16-a26a93daa9f5`.
The observations were recorded at `2026-09-19T20:17:13.766Z`.

## Repeat the check

Use the Explorer repository's documented locked installation and site build,
then serve that built site locally. The command below assumes the site is
served at `http://127.0.0.1:8002` and that this DWP checkout is at
`~/repos/okf-dwp`. Run it from the Explorer repository:

```sh
OKF_CONCEPT_CORPUS_ROOT="$HOME/repos/okf-dwp/full-dmg" \
OKF_CONCEPT_OUTPUT="/tmp/okf-dwp-navigation-repeat" \
OKF_CONCEPT_APP_MANIFEST_URL="http://127.0.0.1:8002/okf-explorer-build-manifest.json" \
OKF_CONCEPT_APP_MANIFEST_SHA256="7ced69ae616349759f47557842aaab5cf9614b3cfe82d837abc1ec6d287e0714" \
PLAYWRIGHT_BASE_URL="http://127.0.0.1:8002/explore/" \
pnpm --dir apps/okf-explorer exec playwright test \
  tests/ui/conceptual-corpus-acceptance.spec.ts --project=chrome
```

The supplied manifest hash deliberately rejects a different application
build. When assessing a later build, supply its verified manifest hash and
retain a new observation rather than overwriting this historical evidence.

The test serves public corpus files from the supplied directory through a
bounded browser fixture. It preserves compressed bytes and their hashes;
it does not copy the corpus into Explorer's source tree. The test is skipped
in ordinary Explorer CI unless `OKF_CONCEPT_CORPUS_ROOT` is supplied. Its
portable synthetic companion runs independently of this DWP checkout.

This Reader projection covers the full DMG material. The separate full
DMG plus ADM classification audit must not be confused with this browser
scope. See [the navigation build evidence](../build.json) for coverage and
input hashes, and [the navigation manifest](../../../full-dmg/context/navigation/manifest.json)
for the classification methods and limitations.
