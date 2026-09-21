# Public Chrome observation: disability qualifications

Six journeys passed against immutable DWP candidate
`df352daa5d1d6a99a30fddcb2db341f74c6473e5` on **21 September 2026 at 01:55 BST**.
The actual application manifest was
`9fc8cb1bbf10e4e5182efd69d56f2b5ed39a2e6ecf942dce64357c4a529d1ce8`.
The application used the reviewed `c4f2de0a…` assembler. This is a new actual
public Chrome observation; no response was intercepted or substituted.

The [original observation](attempt-01-chrome/observation.json) records 293
responses, 37,073,923 bytes and 270 distinct corpus paths. The 273 supporting
source identities and all 21 application materials were checked. Conceptual
filtering, exact statutory text, source/audit timeline distinction, directed
graph connections, care-home qualifiers and both unresolved SDA meanings passed.
There were no console or network errors.

| Package | Records | Relationships | Complete compact JSON |
| --- | ---: | ---: | ---: |
| [Care home](attempt-01-chrome/care-home-context.json) | 61 | 124 | 520,494 bytes |
| [SDA](attempt-01-chrome/sda-context.json) | 64 | 114 | 510,338 bytes |

Both packages remain **insufficient and truncated**, with no AI answer. The
[care-home screenshot](attempt-01-chrome/care-home-ask.png) shows the no-partner
heading; [SDA alternatives](attempt-01-chrome/sda-alternatives.png) stay unresolved.
Other screenshots and the exact executed harness remain beside the observation.

## Recheck retained integrity

```sh
uv run --locked python scripts/check_disability_public_observation.py
```

The [separate checker](../../../scripts/check_disability_public_observation.py)
first admits the exact reviewed shared verifier modules by hash. It supplies
this release's independently pinned identities, checks each original file and
compares whole selected records, literal hashes and directed paths with immutable
Git source. The [approval](approval-manifest.json) and
[artefact manifest](artifact-manifest.json) record that later integrity check.
It makes no network/model call and does not rerun the browser. References to
budget-omitted targets remain distinct from selected evidence.

This is one Chrome observation of a public immutable candidate, made before its
protected merge completed. It does not attest other browsers, assistive technology,
the remote MCP service, legal completeness or model answer quality. The browser
harness measured response-body limits after receipt; those were not hard transfer
ceilings. The [earlier qualification observation](../7f9feb96-c4f2de0a/README.md)
and every original file remain unchanged. The later partner increment needs its
own source-bound public observation.
