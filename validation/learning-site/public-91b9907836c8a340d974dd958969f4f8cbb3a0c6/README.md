# Published learning website: 91b99078

The actual public learning website matched exact source commit
`91b9907836c8a340d974dd958969f4f8cbb3a0c6` on **21 September 2026 at
01:53:10–01:53:16 BST**. This is a separate observation, preserving the
[earlier receipt](../public-7815b17bb3db3903738c745d3fb9508919ebab15/README.md).

## What passed

- 119 tracked Markdown source files checked against immutable Git blobs.
- 123 actual HTTPS responses: the manifest and all 122 listed outputs.
- 1,777,711 received bytes, four bounded readers and no retries.
- 120 received HTML pages with 2,382 internal links checked.
- No missing targets, missing section anchors or duplicate IDs.
- 1,468 external links counted and left unfetched.

The [observation](observation.json) records each response and the HTML audit.
The [expected manifest](expected-site-manifest.json) came from the exact local
publication build before network verification. The [executed verifier](verify_public.py)
differs from its predecessor only in the approved source commit. The six
[offline controls](test_verify_public.py) remain unchanged. The
[canonical gate](canonical-status.json) and [Pages gate](pages-status.json)
identify the successful publication workflows.

## Recheck retained integrity

```sh
uv run --locked python validation/learning-site/public-91b9907836c8a340d974dd958969f4f8cbb3a0c6/check_observation.py
```

The [artefact manifest](artifact-manifest.json) binds the retained inputs,
verifier, receipt, checks and documentation. The checker verifies these bytes
without contacting the website or rerunning the past HTML audit. A fresh real
check needs a new unused output path and the exact expected manifest; changed
publication content should fail this historical comparison.

This observation establishes publication bytes and internal links at the stated
time. It does not establish browser layout, assistive-technology acceptance,
external source availability, legal accuracy, AI answers or Voice access. The
later disability and partner source increments need their own checks.
