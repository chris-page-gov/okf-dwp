# Evidence review browser observations

The public evidence reader completed the functional checks in Chrome, Firefox
and WebKit on 19 September 2026. The strict browser gate **failed in all nine
tests** because the hosting layer produced console errors. This is a recorded
failure, not a clean browser acceptance result.

## What was checked

The three engines each ran these three checks against the actual public service:

1. A shared replay link remains inert until the user selects **Recreate evidence**.
   The page then shows a bounded catalogue, retrieves exact source text, verifies
   its content hash, displays the selected record's title and original source,
   retrieves provenance and gaps, pages through the machine package, and clears
   stale evidence when the question changes.
2. Changing the question while a response is in flight prevents the old response
   from being shown as evidence for the new question.
3. An invalid replay link makes no request. A separate synthetic response checks
   that hostile markup remains plain text and an unsafe source URL is not linked.
   The synthetic response is a security control, not source evidence.

All assertions before the final zero-console-error assertion passed. The live
main journey returned 52 selected records and a first catalogue page of 22. The
rendered source text matched its SHA-256 digest (a content fingerprint). No AI
answer was generated.

## Hosting issue

The public HTML adds a Cloudflare inline challenge-loader script. The reader's
content security policy permits scripts from the same origin but blocks inline
scripts, so all three engines report a blocked-script error. Firefox also reports
rejected `__cf_bm` cookies with an invalid domain. The earlier local reader had
neither error. The policy has not been weakened and the test has not suppressed
these errors.

- [Public run summary: nine strict failures](public/run-summary.json)
- [Observed hosting script metadata](public/host-script-observation.json)
- Main journey receipts: [Chrome](public/chrome-receipt.json),
  [Firefox](public/firefox-receipt.json), [WebKit](public/webkit-receipt.json)
- Exact-source screenshots: [Chrome](public/chrome-source-evidence.png),
  [Firefox](public/firefox-source-evidence.png),
  [WebKit](public/webkit-source-evidence.png)
- [Earlier local result: nine passes](local/run-summary.json)

The receipts retain the console errors. The run summary preserves the strict
failure and the failed assertion for every test. Raw browser traces and network
archives are kept outside this public repository because they can contain
short-lived hosting cookies. No private staff correspondence was used.

## Scope and identity

These browser checks deliberately use the frozen historical profile
`efb05c66616a9cd4328a86cf412780fe7bc7cf0b`. Its preserved research assessment may
say `sufficient`; that does not establish current legal correctness, individual
entitlement or full-corpus answerability. The separate
[SDK receipt](../sdk-receipt.json) covers the remote protocol and full-corpus
compact delivery. The [deployment receipt](../deployment.json) records the
hosting operation. A local build fingerprint in a browser receipt identifies its
test reference, not proof of the remote Worker bytes.

## Separate full-corpus Chrome observation

The [full-corpus receipt](public-full-corpus/chrome-receipt.json) records a
separate public Chrome journey at 20:38 UTC on 19 September: four real tool calls
returned a catalogue, exact source text, provenance and complete diagnostics.
The same bounded abroad context `2cdfa5fe…` contained six records, no
relationships, and remained insufficient with retrieval and context truncation.
Rendered ADM C2 page 18 text and metadata, and the complete diagnostic hashes,
matched the SDK evidence. See the [catalogue](public-full-corpus/chrome-catalogue.png)
and [source evidence](public-full-corpus/chrome-source-evidence.png) screenshots.

Functional checks passed, but the strict console gate failed on the host's
blocked inline script. This observation applies to hosting version 6 and runtime
`169b8c387a29435d39dc31cbb2066376d84b39a6`, before the pending 0.3.1 replay-link
correction. It is not a clean browser pass, a Firefox/WebKit full-corpus test or
an AI-answer assessment. The earlier nine-test historical suite remains intact.

## Repeat the public browser check

In an OKF Explorer checkout with the documented locked service and browser
requirements installed:

```sh
cd apps/okf-explorer
ASK_OKF_REVIEW_BASE_URL=https://ask-okf.crpage.chatgpt.site \
ASK_OKF_REVIEW_OUTPUT=/tmp/ask-okf-public-review-observation \
pnpm exec playwright test --config playwright.service-review.config.ts
```

Use a new output directory to preserve these observations. An external URL
disables automatic local server startup. Omit it to test the local built service.
The browser checks remain strict: an unresolved hosting console issue gives a
non-zero exit status even if the evidence interactions work.
