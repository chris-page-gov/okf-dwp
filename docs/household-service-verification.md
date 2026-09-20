# Verify the household evidence service

Service **0.5.0 was deployed and checked on 20 September 2026**. The
[retained observation](../validation/compact-delivery/v0.5.0/README.md) binds the
actual deployment, SDK comparison and three-browser care-home journey. The SDK
passed seven full-package and four compact cases across four approved versions.
All three browsers passed the evidence journey; Chrome and WebKit passed strict
console checks, while Firefox retained two hosting-cookie warnings. Historical
browser journeys were not run for this release. Earlier
[0.4.0 observations](../validation/compact-delivery/v0.4.0/README.md) remain
separate and unchanged.

The source is `3ef0e786e9a18e76fa17c7d925ff509d6d6c9f84`. It adds 20 selected
statutory units while leaving all 203 obligations open. The broader development
evaluation retains 176 of 177 expected candidate-page occurrences; all 40 staff
tasks remain insufficient. These are evidence-discovery results, not an answer
accuracy score. The [Monday handover](monday-handover-2026-09-21.md) explains the
demonstration in plain English.

The service's software development kit (SDK) check compares an external client's
evidence with the shared context engine. The browser check then verifies that a
person can inspect the same selected records, official links, provenance,
relationships and gaps. **Complete delivery does not mean a complete answer.**
The household package remains insufficient; no individual entitlement decision
or specialist legal acceptance follows from these checks.

## 1. Retain the actual deployment and SDK checks

The completed release is frozen under `validation/compact-delivery/v0.5.0/`.
For a new observation, choose a **fresh directory**, replacing `YYYYMMDD` in the
examples below, and retain the new actual checks there. Never replace an old
receipt or manifest.

Retain these files in `validation/compact-delivery/v0.5.0-followup-YYYYMMDD/`:

- `deployment.json`: the actual hosting result, immutable runtime commit and
  Worker hash, using `okf-compact-delivery-deployment.v1`.
- `sdk-receipt.json`: the successful real SDK verification, using
  `okf-remote-mcp-sdk-verification.v1`.

Do not substitute the service's offline integration receipt for either file.
The SDK and deployment runtime identities must agree. Service 0.5.0's primary
compact case is the supplied self-funded permanent care-home question, at
262,144 bytes; the actual public run selected 35 records and 50 relationships.
The verifier uses the actual SDK receipt's identities and counts rather than
hard-coding those observations. Source revision, context identifier and budget
must remain identical across the SDK and browser checks.

The service's remote SDK verifier paces HTTP requests by at least 750 ms and
does not automatically retry. Wait at least 60 seconds after it finishes before
starting the browser run, to leave the previous service rate-limit window.
Other clients may still share that limit. Retain any failure, including HTTP
429; do not silently repeat it.

## 2. Check the inputs and run the browsers

From the DWP repository root, first validate the new receipts without network access:

```sh
node scripts/check_staff_service_browser.mjs \
  --service-url https://ask-okf.crpage.chatgpt.site \
  --sdk-receipt validation/compact-delivery/v0.5.0-followup-YYYYMMDD/sdk-receipt.json \
  --deployment validation/compact-delivery/v0.5.0-followup-YYYYMMDD/deployment.json \
  --check-inputs
```

Then use the reviewed Explorer checkout with its installed Playwright browsers:

```sh
node scripts/check_staff_service_browser.mjs \
  --explorer-root /path/to/reviewed/okf-explorer \
  --service-url https://ask-okf.crpage.chatgpt.site \
  --sdk-receipt validation/compact-delivery/v0.5.0-followup-YYYYMMDD/sdk-receipt.json \
  --deployment validation/compact-delivery/v0.5.0-followup-YYYYMMDD/deployment.json \
  --output validation/compact-delivery/v0.5.0-followup-YYYYMMDD/browser/staff
```

The output directory must be new. Chrome, Firefox and WebKit run sequentially
with shared 750 ms pacing. The observer reads browser-native response clones;
it does not replace responses, intercept routes or weaken the security policy.
Rendered text and the reconstructed full package are checked against the SDK
hashes. Catalogue labels, source URLs, locators, authority and review status are
checked against that same verified package.

Retain the exact executed `scripts/check_staff_service_browser.mjs` alongside
the browser receipts as `verifier-<SHA-256>.mjs`, using the digest recorded in
`run-summary.json` under `binding.script.sha256`. Retain screenshots and every
receipt, including unsuccessful attempts. Record functional outcomes and strict
console outcomes separately. A known hosting warning remains a failed strict
console check; it is not converted to a clean-browser pass.

## 3. Declare the scope and bind the artefacts

Add a release README describing what actually ran. Once the SDK, deployment,
browser receipts, exact harness and screenshots are present, create a manifest:

```sh
uv run --locked python scripts/check_staff_service_observations.py \
  --directory validation/compact-delivery/v0.5.0-followup-YYYYMMDD \
  --write-manifest --staff-attempt staff --historical-suite not_run
```

This command refuses to replace an existing manifest. It verifies the declared
runs before writing. Repeat `--staff-attempt` for every retained attempt, for
example `--staff-attempt staff-first --staff-attempt staff-second`; names are
single safe directory names below `browser/`. An undeclared browser attempt,
missing engine receipt or missing expected screenshot cannot pass. Retained
failures remain failures.

Use `--historical-suite present` only after the separate four-journey,
three-browser historical suite has actually run against this deployment and its
public-safe projection has been retained under `browser/historical/`. Otherwise,
`not_run` produces null historical pass counts and
`historical_strict_status: "not_run"`. A successful current staff run does not
establish historical regression coverage.

The new manifest declares its layout explicitly under
`okf-compact-delivery-observation-layout.v1`. Unknown schemas or fields, duplicate
or unsafe names, symlinks, unbound files and altered bytes are rejected. Reads
are bounded to 128 KiB per manifest, 10 MiB per member, 256 members and 32 MiB
total. The checker makes no network request and launches no browser.

## 4. Repeat the offline integrity check in CI

```sh
uv run --locked python scripts/check_staff_service_observations.py \
  --directory validation/compact-delivery/v0.5.0
uv run --locked python -m unittest discover -s scripts \
  -p test_staff_service_observations.py
```

Verification reads the frozen layout from the manifest; command-line flags
cannot override it. The existing command without `--directory` still checks
the exact 0.4.0 layout and preserves its original outcomes. Add the explicit
release-specific CI command when its actual receipts exist. The 0.5.0 command
above now verifies its 14 retained artefacts: three functional browser passes,
two strict console passes and historical status `not_run`.

ChatGPT tool invocation, complete receipt of evidence in that client, Voice
access, answer quality and specialist review each need their own observations.
