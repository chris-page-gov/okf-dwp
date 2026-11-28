# Pension Credit Core 0.3 candidate

This is a development review candidate for the frozen Pension Credit pilot.
The records concern retained staff guidance. Use the linked official source
to check what it said at the cited page. The candidate makes no entitlement
decision or finding on current law.

The generator reads the immutable pilot at commit
`3fee61fb4980f0684443c78cd3806b886eb6b772`. It checks the known SHA-256
of the pilot checksum catalogue before verifying all 834 listed files.
It writes the candidate outside the repository and leaves the earlier
publication bytes intact.

The candidate declares [OKF Core 0.3][spec]. It preserves 821 concept
identities, 964 typed assertions and their authority, rights and provenance.
The generated Markdown rebases 977 links into the candidate,
covering 971 distinct concept pairs. One historical
`experimental` lifecycle value maps to the Core `draft` value and remains
available under `x-okf-dwp-status`.

## Reproduce and check the candidate

```sh
uv sync --locked
uv run --locked python scripts/build_core03_pilot.py --output /tmp/dwp-core03-review
uv run --locked python scripts/build_core03_pilot.py --output /tmp/dwp-core03-review --check
uv run --locked python -m unittest discover -s scripts -p test_core03_pilot.py
```

Choose a new output directory for each build. `manifest.json` binds the
candidate files by length and SHA-256. The `source/` directory contains the
Markdown bundle, `okf-explorer.json` is its Reader projection, and
`evidence.json` is the bounded capital-disregards question packet.

The visual walkthrough is designed for the local Reader test mirror. Serve
the candidate at `/candidate/` and the matching Explorer app at
`/reader/` on the same local origin. Follow its links from the question
to Chapter 84, PDF page 35, and open the assertion’s relationship
evidence. The evidence packet identifies the pinned record and original
source PDF.

## Publication scope

The local candidate covers the Pension Credit pilot. Four other retained
Reader modes have their own migration and acceptance work. Their runtime
descriptors and data manifests at the pinned source revision report these
counts. Modes can share sources, so their counts cannot be totalled to
measure source coverage.

| Retained Reader mode | Core version | Records | Relationships |
| --- | --- | ---: | ---: |
| Full Decision makers’ guide | 0.2 | 15,404 | 16,336 |
| Combined DMG and ADM | 0.2 | 20,158 | 21,313 |
| Structured context | 0.2 | 54,578 | 19,193 |
| Logical context | 0.2 | 50,470 | 553 |

Each mode requires its own source and graph parity tests, including its
sharded records, relationship indexes and source references. Publishing a
public candidate requires an explicit asset inventory and the repository’s
normal exact-revision assurance.

The [Explorer standards register][register] records the current and historical
versions and links to the estate catalogue.

[spec]: https://github.com/open-knowledge-format/open-knowledge-format/blob/527e81aff55992be21507e97004286789126f88c/SPEC.md
[register]: https://github.com/chris-page-gov/okf-explorer/blob/main/docs/okf-standards.md
