# Check the public staff evidence reader

The compact reader is a small web page for inspecting evidence returned by Ask OKF. It shows a catalogue first, then retrieves selected source text and provenance in bounded parts. **A catalogue is an index to evidence; it is not an answer.**

The [browser verifier](../scripts/check_staff_service_browser.mjs) checks that a person using the public reader sees the same evidence as the separately verified Model Context Protocol (MCP) client. The software development kit (SDK) receipt records that client check. The hosting receipt identifies the deployment. Neither receipt alone proves what a browser displayed.

## Before running

Use an Explorer checkout with its existing locked browser dependencies installed. This script does not install packages, alter browser security settings or deploy anything. Use a successful SDK receipt and the corresponding hosting receipt for the target release.

The verifier reads the exact question, source version, context identity and budget from `compact_delivery` in the SDK receipt. It does not hard-code a DWP question, six records or a release version. Questions must already be public evaluation questions: do not enter claimant or other personal data.

First check the receipts offline:

```sh
node scripts/check_staff_service_browser.mjs \
  --service-url https://ask-okf.crpage.chatgpt.site \
  --sdk-receipt validation/compact-delivery/v0.4.0/sdk-receipt.json \
  --deployment validation/compact-delivery/v0.4.0/deployment.json \
  --check-inputs
```

This checks their declared identities; it makes no network request. It does not claim that the declared deployment is still live.

## Run the public check

Once that release is deployed and the SDK check has passed:

```sh
node scripts/check_staff_service_browser.mjs \
  --explorer-root /path/to/okf-explorer \
  --service-url https://ask-okf.crpage.chatgpt.site \
  --sdk-receipt validation/compact-delivery/v0.4.0/sdk-receipt.json \
  --deployment validation/compact-delivery/v0.4.0/deployment.json \
  --output validation/compact-delivery/v0.4.0/browser/staff
```

Chrome, Firefox and WebKit run independently by default. `--engines chrome` requests a narrower observation; its receipt must not be described as a three-browser pass. Output directories must be new, so a rerun cannot erase a failure. Use a new dated or numbered directory for each attempt.

Environment-variable equivalents are `OKF_EXPLORER_CHECKOUT`, `OKF_STAFF_SERVICE_URL`, `OKF_STAFF_SDK_RECEIPT`, `OKF_STAFF_DEPLOYMENT_RECEIPT`, `OKF_STAFF_BROWSER_OUTPUT` and `OKF_STAFF_BROWSER_ENGINES`.

## What it checks

The script uses the actual HTTPS service without substituting source files, routing requests or replacing responses. A read-only observer clones each native fetch response and calls the browser’s own `Response.text()` method. The original request, response and promise are unchanged. This avoids a Chromium driver path which can misdecode non-ASCII server-sent events. Native and driver response digests are recorded separately; no repaired or guessed text is accepted. Exact rendered evidence and the reconstructed package must still match the SDK hashes. It checks:

1. Opening the shared link leaves its question inert: no evidence request occurs until **Recreate evidence** is selected.
2. The returned context identity, status, record count and relationships match the SDK receipt.
3. **Show more records** reaches the complete ordered catalogue, with no duplicate records. Every catalogue field, including title, source URL and locator, text fingerprint, authority and review status, must match its record in the hash-verified full package.
4. **Read exact text** and **Inspect provenance and inclusion reasons** show the SDK-selected source record and its original source link.
5. **Read next part** advances contiguously through source text, metadata, diagnostics, relationships and the full machine package.
6. Joining the rendered parts reproduces each SDK SHA-256 digest. SHA-256 is a fingerprint of exact bytes: matching fingerprints establish byte identity, not legal correctness.
7. Provenance, inclusion reasons, graph paths and declared gaps agree with the reconstructed full package.
8. The HTML retains the exact restricted content security policy directives and `no-transform` instruction to intermediaries. This is a response-header observation, not a guarantee about every hosting feature.

A single request pacer is shared across all requested browsers. Each evidence call waits until at least 750 milliseconds after the preceding observed MCP request started (at most about 80 requests per minute). This stays below the service’s 120-request-per-minute limit when this verifier is the only client. SDK checks and other clients share the service limit: allow their rate-limit window to clear before starting. The receipts record the pacing. There are no automatic retries; an HTTP 429 response remains a functional failure.

There are limits of 201 catalogue pages, 256 parts per value, 512 evidence calls and a 12-minute observation budget per browser, checked before each call. A pending request may take up to 90 seconds to finish. The reader's service-side response limits also remain enforced.

## Read the result correctly

Each browser writes a receipt and screenshots. `run-summary.json` links the receipts. A failed assertion or unavailable browser is recorded, and the other requested browsers still run.

- `functional_status` reports the evidence journey.
- `strict_console_status` reports browser console and page errors separately.
- `overall_clean_browser_acceptance` is true only when both pass.
- `all_three_engines_requested` records the requested engines. `all_three_engines_observed` requires each to reach the public HTML shell; inspect their outcomes before claiming acceptance.

An error exit is preserved even when the evidence journey succeeds but the console check fails. Console messages are bounded and URL query/fragment values are omitted; no cookies, account details or raw network traces are retained. Screenshots and the declared question contain public evaluation/source content.

This checks one question and one source record per browser. It does not establish legal applicability, full semantic coverage, accessibility conformance, ChatGPT integration or AI-answer accuracy. The original model-trial packages remain separate immutable observations.

## Offline regression controls

```sh
node --test scripts/test_staff_service_browser.mjs
```

The controls also check pacing across callers, early timer wake-ups, source/catalogue tampering, weakened security policy directives, credential-bearing receipt URLs and native Unicode response observation without changing the application result. These controls reject mismatched deployment identities, altered replay questions or budgets, absent verified read receipts, tool failures, changed source identity, discontinuous pagination and incorrect byte limits. They use historical retained receipts and make no network requests.
