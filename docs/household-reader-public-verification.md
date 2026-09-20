# Public household Reader verification

The full combined Reader passed a real public Chrome journey on **20 September
2026 at 23:54 BST**, using fixed DWP source
`3ef0e786e9a18e76fa17c7d925ff509d6d6c9f84`.

[Open this exact household source in Explorer](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F3ef0e786e9a18e76fa17c7d925ff509d6d6c9f84%2Fcombined%2Fokf-explorer.json#overview).
The link freezes the bundle version; the Explorer application can receive later
updates. This receipt binds the application bytes actually checked at the time.

**Independent experimental publication.** This is evidence of public navigation
and bounded context assembly, not official guidance, legal completeness or an
individual benefits decision. No compact-service or MCP call was made.

## What worked

- The authored concept **Pension Credit household separation and care-home
  residence** reduced 20,044 records to eight. The interface disclosed that
  these are unreviewed concept references, not legal applicability findings.
- The **Legislation** source-family facet kept the same 20-record scope in
  Reader, Graph and Timeline. The requested statutory version did not appear
  as a publication event; catalogue activity appeared separately under audit
  dates.
- Regulation 5 of the State Pension Credit Regulations 2002 displayed its
  retained literal text and exact official dated HTML link. Its graph exposed
  incoming guidance references and outgoing navigation to the Universal
  Credit Regulations 2013 couple definition.
- The care-home question retained the whole selected page containing DMG 78088,
  including the controlling **no-partner** heading, and opened that source
  passage in the interface.
- The SDA question displayed both possible meanings as labelled alternative
  branches. Neither was silently resolved as the intended meaning.

**DMG** means Decision makers’ guide. **SDA** can mean Severe Disablement Allowance
or shorthand for a severe-disability additional amount. A **context package**
contains selected evidence and the reasons for including it. **Truncation** means
its limits left some material outside the package.

| Public package | Records | Relationships | Compact JSON bytes | Result |
| --- | ---: | ---: | ---: | --- |
| Care home | 64 | 118 | 481,453 | Insufficient; truncated |
| SDA | 64 | 99 | 477,761 | Insufficient; truncated |

Both used limits of 64 records, 128 relationships, depth six and 524,288 bytes.
The complete JSON retains missing evidence, ambiguities and omissions. The
care-home selection still omits some statutory housing-cost units. Preserving a
heading does not make the overall question answerable.
The text check inspects the opened whole passage; the saved screenshot captures
its beginning, with the no-partner heading further down the passage. Scroll to
that heading during the demonstration.

The earlier [local three-browser checks](household-reader-verification.md) used
local fixture URLs. An exact comparison found just three differing fields in
each public package: the manifest URL, the derived byte count and the context ID.
The public URL adds 69 bytes; the selected evidence, relationships and every
other field match. See the [retained comparison](../validation/household-reader-public/3ef0e786/local-comparison.json).

## Identity, timing and limits

Chrome version: **153.0.8010.52**. The application manifest SHA-256 was
`a551e1601d7722cea6edfe4e613a4fcc44191d8dfc74a0368b67b6a33f8d6f0c`;
the 21-file application tree was
`c0666ae2659d3cf3eba8a19c41c5d9873adefb5514134823f54549fcabc0a0d2`.
SHA-256 is a fingerprint of exact bytes; it helps detect a changed file.

All 21 application files were fetched and checked, and 14 actual browser-loaded
application responses were checked too. The journey observed 294 corpus
responses covering 270 unique files: 36,913,216 response-body bytes, including
repeated responses. Each was compared with the named immutable Git commit.
These are observed response sizes, not a hard network-transfer limit. There
were no console or network errors, intercepted responses or retries within
the passing run.

| Phase reached | Elapsed from start |
| --- | ---: |
| Application files verified | 2.5 seconds |
| Initial Reader ready | 3.0 seconds |
| Concept facet ready | 3.8 seconds |
| Statutory facet and timeline checked | 11.4 seconds |
| Statutory literal checked | 12.5 seconds |
| Statutory graph checked | 12.8 seconds |
| Care-home package ready | 14.9 seconds |
| SDA package ready | 16.6 seconds |

These are one observed public-network journey's cumulative timings, not a
controlled performance benchmark. The first attempt is retained separately:
it used an incorrect toolbar assertion after **Reset view** and timed out after
60 seconds. The screenshot showed the correct full-corpus state. The harness
was corrected; no application or corpus change was needed.

This public run inspected one statutory body. The separate local observations
checked all 20 and three browser engines. It did not repeat those exhaustive
checks, run a human screen reader, test a physical phone, inspect current law
or use an AI to answer either question.

## Evidence and reproduction

The [evidence inventory](../validation/household-reader-public/3ef0e786/README.md)
links screenshots, both exact executed harnesses, the failed attempt, complete
packages and response hashes. The offline checker verifies all 16 execution
files, exact Git source bindings and the disclosed local/public differences.
It rejects symbolic links in files and parent directories, limits manifests to
128 KiB and individual retained files to 10 MiB, and limits the execution
inventory to 64 files and 32 MiB. Immutable Git blobs are size-checked before a
capped 8 MiB capture. Seven synthetic negative controls exercise altered,
missing, oversized and unsafe inputs. These checks make no new browser request.

From the DWP repository, use an isolated Explorer checkout with the existing
Playwright dependencies and a **new** output directory:

```sh
OKF_EXPLORER_CHECKOUT=/path/to/isolated/okf-explorer \
OKF_PUBLIC_HOUSEHOLD_COMMIT=3ef0e786e9a18e76fa17c7d925ff509d6d6c9f84 \
OKF_PUBLIC_HOUSEHOLD_APP_SHA256=a551e1601d7722cea6edfe4e613a4fcc44191d8dfc74a0368b67b6a33f8d6f0c \
OKF_PUBLIC_HOUSEHOLD_OUTPUT=/tmp/new-public-household-observation \
node scripts/check_public_household_reader.mjs
```

The installed Chrome browser must be available. The harness rejects an existing
output directory, file or symbolic link before browser launch. It allows 60
seconds per interaction and an eight-minute overall journey. A changed public
application fingerprint must fail rather than silently becoming the old result.

For offline checks, with no browser or network requests:

```sh
node --test scripts/test_public_household_reader.mjs
uv run --locked python scripts/check_public_household_observations.py
uv run --locked python -m unittest discover -s scripts -p test_public_household_observations.py
```
