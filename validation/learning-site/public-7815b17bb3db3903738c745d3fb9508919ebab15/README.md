# Published learning website: 7815b17b

**Passed.** The [learning website](https://chris-page-gov.github.io/okf-dwp/)
matched the exact generated publication for commit
`7815b17bb3db3903738c745d3fb9508919ebab15` at **00:52:52–00:52:58 BST on
21 September 2026** (`23:52:52–23:52:58 UTC` on 20 September).

The new observation follows successful
[canonical validation](https://github.com/chris-page-gov/okf-dwp/actions/runs/35545088332)
and [Pages deployment](https://github.com/chris-page-gov/okf-dwp/actions/runs/35545815942).
It does not relabel the [earlier website observation](../public-3f72ebc30128c2a3171951050a566d3ed8db7c16/README.md).

## What passed

- **118 public Markdown source files** matched their exact immutable Git blobs.
- **122 real HTTPS responses**: the public manifest and all 121 listed outputs.
  Each returned HTTP 200 at the expected URL, with the exact byte count and SHA-256.
- **1,687,650 response-body bytes** transferred, with four bounded readers and no retries.
- **119 received HTML pages**: 118 authored pages and the home-page alias.
- **2,320 internal links** checked against received target files and decoded
  fragment IDs. There were no missing targets, missing fragments or duplicate IDs.
- **1,419 external links** were counted and left unfetched, including historical
  source and demonstration links.

The verifier first matched the actual public manifest against the independent
local build, then fetched that manifest's complete output list. The HTML audit
used the received public bytes. No browser interception, model calls, corpus
downloads or private correspondence reads were involved.

## Retained evidence

- [Actual observation, every response and per-page audit counts](observation.json)
- [Exact expected generated manifest](expected-site-manifest.json)
- [Executed bounded verifier](verify_public.py) and [six offline controls](test_verify_public.py)
- [Canonical gate](canonical-status.json) and [Pages gate](pages-status.json)
- [Artefact hashes](artifact-manifest.json) and [offline integrity checker](check_observation.py)

The output count is derived from the manifest rather than copied from the old
105-page observation. Local files and their parents cannot be symlinks. Source
reads are limited to public documentation paths at the named commit. Network
reads admit at most 200 output files, 2 MiB per member and 32 MiB of reserved
response bodies; redirects are refused. Socket operations time out after 15
seconds, with a 180-second deadline checked at request starts and between body
chunks. That is not a promise about wall-clock runtime under every network fault.

## Repeat without overwriting an observation

From the DWP repository root, check the retained receipt offline:

```sh
uv run --locked python validation/learning-site/public-7815b17bb3db3903738c745d3fb9508919ebab15/check_observation.py
```

For a fresh real HTTP check, choose a new output filename and retain any failure:

```sh
uv run --locked python validation/learning-site/public-7815b17bb3db3903738c745d3fb9508919ebab15/verify_public.py \
  --dwp-root /path/to/okf-dwp \
  --expected-manifest validation/learning-site/public-7815b17bb3db3903738c745d3fb9508919ebab15/expected-site-manifest.json \
  --output /private/tmp/learning-7815-new-observation.json
```

An existing output file or symlink is refused before any source or network read.
The immutable commit must exist locally. This historical expected build will
correctly fail if a later publication replaces it; do not change its expected
identity to turn that failure into a pass.

This is a dated publication-byte and internal-link check. It does not establish
browser layout, assistive-technology acceptance, live Voice or tool access,
external-link availability, legal correctness or complete answerability. The
offline checker verifies receipt integrity and counts; it does not recreate the
past HTTP observation or rerun the HTML audit.
