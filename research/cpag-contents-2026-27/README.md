# CPAG public contents harvest

[Read the linked contents](contents.md), or use [JSON](contents.json) and
[YAML-LD](contents.yamlld).

The owner requested this harvest from the live 2026/27 handbook page.
The capture retains only publicly displayed navigation labels, URLs, CPAG
identifiers, parent relationships and source order. It covers the table of
contents at part/chapter/appendix level, including front/back-matter links.

## Acquisition

The web text tool could not retrieve AskCPAG, so the public page was read in
installed Edge. The root exposed 17 navigation links. All 10 part pages
exposed their chapter links, and the appendices page exposed five appendix
links. Those 12 page observations produced 90 unique entries. No login or
trial was used. No chapter body, prose preview or index entry was retained.

A compact tuple fingerprint computed in the browser matched the exported
data, checking transcription across tool boundaries. It is explicitly a
non-cryptographic check. The files also have SHA-256 checksums. The validation
report checks uniqueness, hierarchy and numbered part/chapter sequences;
it does not claim that every destination was independently fetched.

## Reproduce the local projections

From the repository root, using its existing locked environment:

```sh
python3 research/cpag-contents-2026-27/validate_contents.py \
  research/cpag-contents-2026-27/contents.json \
  --expect-chapters 68 --expect-parts 10 \
  --output research/cpag-contents-2026-27/validation.json
uv run --locked python research/cpag-contents-2026-27/render_contents.py
```

These commands operate on the captured metadata without fetching the site.
The YAML-LD is a standalone linked-data projection, not an Explorer runtime
bundle. It uses the observed publication hierarchy and makes no substantive
legal or policy assertions.

CPAG attribution and applicable terms remain in place. This is a local
research export, not a newly published handbook mirror or an addition to
the public OKF bundle. It does not establish a general reuse licence or
CPAG endorsement.
