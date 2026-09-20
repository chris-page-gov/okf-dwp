# Ask OKF 0.4.0 public evidence observations

Observed on 20 September 2026. This independent prototype presents evidence and its limits. It does not decide entitlement, establish current law or certify AI answers.

The [deployment receipt](deployment.json) identifies service 0.4.0, hosting version 8 and Explorer commit `fc71d65b8f5cfc860d52afe98a5e45b88231f3e5`. The [SDK receipt](sdk-receipt.json) independently checks the live read-only tools against the built reference. The worker SHA-256 is `cf39080fbd011f2d47bfe5aa97872cf63a36d105bf35986cca5f197bcf47f683`. A hash is a fingerprint of exact bytes; it does not establish legal correctness.

## Staff question

> What is the interaction between Child DLA and PIP?

DLA means Disability Living Allowance. PIP means Personal Independence Payment. The public source version is `9de52acf1db84b27f8933d80480eaa850e74fa33`. With a 262,144-byte context budget, the tools selected 50 records and 36 relationships. Evidence status remains **insufficient**, with truncation and gaps exposed.

The [second staff observation](browser/staff-native/run-summary.json) verified the complete catalogue and every selected record's catalogue metadata against the SDK-hash-verified package. In each browser it reconstructed and checked one source page's exact text and provenance, diagnostics, relationship paths and the complete machine package through the actual reader controls. Each browser made 24 evidence requests; all 72 completed without automatic retries. Minimum observed spacing was 768.594 milliseconds, above the declared 750-millisecond minimum. Other clients share the service's rate limit.

| Observation | Chrome | Firefox | WebKit |
| --- | --- | --- | --- |
| Staff evidence journey | Passed | Passed | Passed |
| Staff strict console check | Passed | Failed | Passed |
| Four historical journeys: functional checks | 4 passed | 4 passed | 4 passed |
| Four historical journeys: strict checks | 4 passed | 4 failed | 4 passed |

**The clean three-browser gate remains failed.** Firefox reported that the hosting `__cf_bm` cookie was rejected for an invalid domain. The errors were not suppressed and browser privacy/security settings were not changed. This does not alter the independently matched evidence hashes, but it prevents a clean browser acceptance claim. No source gaps or legal review requirements are upgraded by these results.

## Preserve the first attempt

The [first staff observation](browser/staff/run-summary.json) remains unchanged. Chrome stopped at its first manifest because the browser driver's decoded server-sent-event text did not reproduce the response's declared JSON byte count. Firefox and WebKit completed the evidence checks; Firefox retained the same cookie errors.

The second observation uses the browser's own `Response.clone().text()` for measurement. It leaves the original fetch arguments, promise and application response unchanged. It does not route requests, replace source data or change the security policy. Seventeen Chrome driver/native response digests differed; Firefox and WebKit had no such differences. All native and rendered content matched the SDK hashes. This is a documented measurement correction, not a repaired source answer or an automatic retry.

Each attempt includes its exact verifier source, named with its SHA-256. Both attempts remain part of the [artefact manifest](artifacts.json).

## Historical reader controls

The [historical suite summary](browser/historical/run-summary.json) records the exact existing four tests in Chrome, Firefox and WebKit: 12 functional journeys reached their final assertions, eight strict tests passed and four Firefox tests failed at the final console check. The suite used one worker and zero retries after the preceding service-rate window cleared.

These tests check source reading, replay-link identity when the question changes from A to B, recreating the same question, version changes, stale responses, invalid links and treating hostile markup as text. The stale-response and hostile-markup cases deliberately route a delayed real response or a synthetic response. They are UI boundary controls, not untouched source-evidence observations. The historical context's research status is not a claim of current legal sufficiency.

The exact test and configuration sources are retained by digest. Public receipts and summaries are whitelisted projections; raw Playwright results, trace archives, error snippets and network details remain local. `project_staff_service_history.py` produces these projections and records digests of local originals. Hosting and SDK identity remain separate from the browser test's local build-reference digest.

## Reproduce and check

See the [browser verification guide](../../../docs/staff-service-browser-verification.md) for the public command and its limits. The public verifier derives the question, source version and expected evidence from the SDK receipt. A new run must use a new output directory and should begin after other clients' rate-limit windows clear.

Check retained artefacts offline:

```sh
uv run --locked python scripts/check_staff_service_observations.py
node --test scripts/test_staff_service_browser.mjs
uv run --locked python -m unittest discover -s scripts -p test_staff_service_observations.py
```

The integrity check rejects changed bytes, absent or extra files, path escapes and symbolic links. It also checks that summaries preserve recorded failures and successful evidence hashes. A passing integrity check means the retained observations agree; it does not mean every browser test passed.

Run the historical suite from the pinned Explorer checkout's `apps/okf-explorer` directory, using a fresh local output directory:

```sh
ASK_OKF_REVIEW_BASE_URL=https://ask-okf.crpage.chatgpt.site \
ASK_OKF_REVIEW_OUTPUT=/path/to/new/private-observation \
node node_modules/@playwright/test/cli.js test --config=playwright.service-review.config.ts
```

Project its public-safe results from the DWP checkout:

```sh
python3 scripts/project_staff_service_history.py \
  --raw-directory /path/to/new/private-observation \
  --explorer-root /path/to/pinned/okf-explorer \
  --deployment validation/compact-delivery/v0.4.0/deployment.json \
  --output /path/to/new/public-projection
```

This release's observations are immutable. Future runs should have their own receipts and manifest.
