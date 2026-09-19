# Public historical review journeys: service 0.3.1

On 19 September 2026, all 12 browser journeys completed their functional
assertions against [the public evidence review page](https://ask-okf.crpage.chatgpt.site/review/).
**All 12 strict tests failed at the final empty-console assertion.** No
console error was suppressed and the content security policy was not weakened.

## Results

| Browser | Functional journeys completed | Strict tests passed | Strict failures |
| --- | ---: | ---: | --- |
| Chrome | 4 of 4 | 0 | Host inline script blocked by the content security policy |
| Firefox | 4 of 4 | 0 | Same policy block, plus an invalid-domain cookie rejection |
| WebKit | 4 of 4 | 0 | Host inline script blocked by the content security policy |

The four journeys cover:

1. Recreating a historical context, paging its evidence catalogue, reading
   exact source text and its hash, viewing provenance and diagnostics, and
   requesting bounded portions of the context package.
2. Creating a replay link for question A, changing to question B, checking
   that A's link disappears, then verifying that B's new link contains B's
   exact question, source version and context identity. Repeating a request
   and changing the source version also remove the previous link.
3. Changing the question while a response is delayed, then checking that
   the old response cannot populate the new context.
4. Rejecting an invalid replay fragment and displaying deliberately hostile
   returned markup as inert text, without creating its links or elements.

The first two journeys use the actual public service responses. The third
holds a real response in the browser to test ordering. The fourth deliberately
alters test responses to check hostile content handling. These controls are
not observations of hostile source material in the corpus.

The same four journeys passed all 12 strict tests against the built local
0.3.1 service. The public failures are retained because the hosting environment
also forms part of the deployed experience. They remain an unresolved host
compatibility issue.

## Inspect the evidence

- [Run summary](run-summary.json) records all 12 outcomes and the exact
  source, harness and deployment bindings.
- [Functional gates](functional-summary.json) retains each failed assertion
  and its actual console messages. The [progress log](functional-progress.jsonl)
  records when each test reached its final assertion.
- [Chrome receipt](chrome-receipt.json), [Firefox receipt](firefox-receipt.json)
  and [WebKit receipt](webkit-receipt.json) record the main source-evidence
  journey, calls, selected record hash and limitations.
- Source-text screenshots: [Chrome](chrome-source-evidence.png),
  [Firefox](firefox-source-evidence.png), [WebKit](webkit-source-evidence.png).
- [Artifact hashes](artifacts.json) bind these retained files to their bytes.
- [Deployment receipt](../../deployment.json) identifies Sites version 7,
  service 0.3.1 and runtime commit
  `8493b323ca664e645a2548ebb48bf7917d7f6eb1`.
- [SDK receipt](../../sdk-receipt.json) independently checks the service tools.

A temporary reporting observer recorded the start of each existing final
`expect(errors).toEqual([])` assertion. Reaching that assertion means all
preceding functional assertions completed. It did not alter test behaviour
or results. Its source hash, the test harness hash and the original report
hash are retained in the run summary. Raw traces and browser metadata remain
outside the repository. The screenshots were visually inspected before
retention and contain only the evidence review page.

## Scope and limits

The historical source version is
`efb05c66616a9cd4328a86cf412780fe7bc7cf0b`. The main journey selects 52
records and reads Chapter 12, PDF page 3, whose complete text hash is
`efad9105dc1ffba4f4e2f2e60e8c675c185cef41c6299f90d9a32c746a2ec014`.
The historical context's sufficiency status is preserved research metadata;
it does not establish current law or an individual's entitlement.

This observation does not establish full-corpus answerability, model answer
quality or specialist review. Deployment identity comes from the separate
deployment receipt. These are dated observations, not perpetual assurance.
Earlier 0.3.0 observations remain unchanged.

## Repeat the checks

From the Explorer repository at the runtime commit above, use its documented
locked installation and service build, then run:

```sh
ASK_OKF_REVIEW_BASE_URL="https://ask-okf.crpage.chatgpt.site" \
ASK_OKF_REVIEW_OUTPUT="/tmp/ask-okf-public-review-repeat" \
pnpm --dir apps/okf-explorer exec playwright test \
  --config playwright.service-review.config.ts
```

This runs all four journeys in Chrome, Firefox and WebKit. It retains the
strict console assertions. A later deployment may produce different results;
retain those as a new observation instead of overwriting these files.
