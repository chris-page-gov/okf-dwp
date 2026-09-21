# Checking the published evidence reader

The archive browser harness checks the three named public examples after the learning website is live. It reopens recorded evidence; it does not ask a new question, call an AI or extend the evidence package.

The three journeys are:

1. Current care-home evidence: inspect a whole selected passage, its provenance and all directed relationships, then reconstruct the complete original package.
2. Unknown-term control: confirm that no evidence was selected and reconstruct the empty package without implying an answer.
3. Historical care-home evidence: inspect the earlier package and preserve the unknown original-engine label.

The harness additionally checks keyboard access to the skip link, keyboard activation of the complete-package button, resulting heading focus, and horizontal overflow at a 390-pixel mobile viewport. These are bounded interaction checks, not exhaustive accessibility acceptance or cross-browser testing.

## Source and network boundaries

Before launching Chrome, the harness captures its own script and helper, and requires both to match the supplied commit. It retains those captured bytes and fails if either local file changes during the run. It then reads the approval, export registry, archive inventory, copied assets and supporting receipt from an immutable DWP Git commit: a fixed repository version. File sizes, SHA-256 fingerprints, Git’s identifiers for stored files and the exact archive file count must agree. The selected examples must keep `insufficient` evidence status and contain no AI answer.

The browser can issue only `GET` requests for explicitly listed assets under the selected release at:

`https://chris-page-gov.github.io/okf-dwp/evidence-examples/`

External navigation, other files on the same host, query strings, credentials and unlisted assets are blocked and recorded as failures. The harness does not click official-source links, rewrite responses or replace the live reader. The page's source links and metadata are compared with the retained package.

For each substantive case, it checks one whole source record and all its displayed metadata against the original selection. It checks every displayed relationship's direction, predicate and assertion status. The complete-package button must return byte-identical JSON with the approved package hash for all three cases. This is stronger than checking that some expected words appear on the page.

The browser has a three-minute overall deadline, 20-second action timeouts, a 512-request limit and no retries. The archive admitted locally is at most 8 MiB and 1,024 files. Announced response sizes are checked before capture; response hashes and actual captured sizes are checked afterwards, with a 1 MiB per-response capture limit and 16 MiB aggregate capture limit.

**Playwright returns buffered response bodies. Those capture checks are not a hard streaming transfer ceiling inside Chrome.** Request count and elapsed-time limits are enforced separately. This limitation appears in the observation rather than being hidden behind a successful hash comparison.

## Running the check

First complete the separate [v2 publication check](retained-evidence-publication.md#publication-identity-and-compatibility), so the expected website commit and published file identities are established. Playwright is the library that drives Chrome for repeatable checks. Use its existing installed module, the library’s entry-point file; this harness installs no browser or dependency.

The supplied commit must contain the approved archive and the exact executed harness and helper. From the repository root, replace the uppercase placeholders with that immutable commit, the existing module entry point and a fresh observation directory:

```sh
node scripts/check_retained_examples_browser.mjs \
  --repo . \
  --commit FULL_DWP_COMMIT \
  --release-id monday-2026-09-21 \
  --playwright-module /ABSOLUTE/PATH/TO/playwright/index.mjs \
  --output FRESH_OBSERVATION_DIRECTORY
```

The browser uses the installed Chrome channel in a fresh context, with service workers blocked. Only the publishing operator should make this public invocation; preparing or testing the harness is not evidence that the public reader has passed.

Run the portable offline controls without opening a browser or contacting any website:

```sh
node --test scripts/test_retained_examples_browser.mjs
```

## What is retained

A fresh output directory contains the observation, the executed harness and helper, screenshots and a hash inventory. The observation records exact source inputs, browser version, provided Playwright entry-point hash, case identities, request and response results, warnings, errors, limits and failures. It does not claim that the module entry-point hash attests every transitive Playwright dependency.

A successful run requires all three journeys, matching response hashes, matching request/response counts and zero page or console errors. Warnings remain visible. Failed runs are preserved; a later justified attempt needs a different output directory. The final observation is a point-in-time result and does not establish legal applicability, specialist acceptance or AI answer correctness.

No new public browser observation is supplied merely by adding this harness. Earlier local and public observations remain unchanged.
