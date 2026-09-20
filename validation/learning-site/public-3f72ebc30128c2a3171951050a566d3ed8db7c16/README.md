# Published learning-site identity check

**Passed**, observed on 20 September 2026 at 22:20:19 UTC (23:20:19 BST).
The published [learning website](https://chris-page-gov.github.io/okf-dwp/)
matched the independently generated site for source commit
`3f72ebc30128c2a3171951050a566d3ed8db7c16`.

The verifier made 109 real HTTPS requests: the manifest and all 108 listed output
files. Every response returned HTTP 200 at its expected URL with the expected
byte length and SHA-256. Total downloaded content was 1,473,921 bytes. There were
no retries, browser interception, corpus downloads or private correspondence
reads.

The manifest describes 105 authored public Markdown pages. These produce 106
HTML files because the learning path is also the home-page alias, plus one
stylesheet and `.nojekyll`. The manifest hash was
`803be764db4d0e03189e01c7f093f43e7cc9789422da47a18912a104fd634b80`.

- [Actual observation and every response identity](observation.json)
- [Expected generated site manifest](expected-site-manifest.json)
- [Exact executed verifier](verify-public.mjs)
- [Retained artefact hashes](artifact-manifest.json)

From the repository root, repeat the read-only check into a **new** output file:

```sh
node validation/learning-site/public-3f72ebc30128c2a3171951050a566d3ed8db7c16/verify-public.mjs \
  /tmp/learning-site-new-observation.json
```

The command refuses an existing output file. It compares the live site against
this historical expected build and will fail if a newer publication has replaced
it. A mismatch must be retained and investigated; it must not be relabelled as a
pass by changing the expected commit.

This verifies publication bytes at one time. It does not check browser layout,
assistive-technology access, linked external evidence, complete answerability or
legal correctness. The root agent records its separate visual learning-path and
glossary checks.
