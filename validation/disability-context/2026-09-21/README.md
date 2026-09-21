# Disability qualification retention

This separate offline experiment compares the reviewed **901-record qualification
source** with the **903-record disability-addition source**. Earlier experiments,
model attempts and public observations remain unchanged. All resulting packages
remain **insufficient**, with `ai_answer: null` and 203 named open obligations.

## Exact inputs

- Earlier source: `7f9feb9634e3d94004853b838462aca132c505a5`.
- Disability source: `8ea4465a4cb5a867d82c87e635f2ef1d1df18d8a`.
- Disability index SHA-256: `8aea634f7623a61475156a116fcebf2ae64cbb4b17507a731a7de73edee0ddd7`.
- Earlier Explorer allocator: `b9a3b68b6dbf222f9a73cc8f450dd53f126e1b55`.
- Required-evidence allocator: `c4f2de0a99b7bc2f8b8c8a06a3c715fb56b66d8e`.
- [Protocol](protocol.json) SHA-256: `6d6e8a9b95ea8457c1d739b6368cd34c862a37d502d7dc31f2829af9165744d4`.

The two sources contain identical questions and original candidate identifiers.
Their source requirements differ deliberately: 433 activated declared path
occurrences become 497. The source comparison preserves all 203 obligation
identifiers; two source-closure labels now explicitly qualify the no-partner
investigation. This does not claim that every obligation object is byte-identical.

## Results

Two sources, two engines, two budgets and 40 question occurrences produce
**320 assemblies**, recorded as 160 paired rows in [attempt 01](attempt-01/comparison.json).

| Budget | Source | Earlier engine: candidate / path occurrences | Current engine: candidate / path occurrences |
| --- | --- | ---: | ---: |
| 256 KiB | Qualification | 169/177; 346/433 | 177/177; 433/433 |
| 256 KiB | Disability | 164/177; 340/497 | 177/177; **407/497** |
| 512 KiB | Qualification | 176/177; 418/433 | 177/177; 433/433 |
| 512 KiB | Disability | 176/177; 462/497 | 177/177; **497/497** |

**Candidate overlap conceals missing qualifications.** For Staff 012 and 013,
the current engine still selects every original candidate at 256 KiB but retains
only 26 of 71 activated paths across the three applicable profiles. Each package
has 15 records and 60 relationships; only one of the seven household-support
pages survives. Both packages expose 21 missing-dependency diagnostics and 37
distinct absent identifiers from the declared required set, including the 15
still-open obligations. The returned diagnostics also name four absent
intermediate concepts and 24 missing path assertions: 65 distinct identifiers
across those different roles, not 65 required source records.
No requirement metadata is omitted from these outputs.

At 512 KiB each case retains all 71 activated paths, all seven household-support
pages and the complete newly declared qualification groups: 61 records and 124
relationships. The exact sizes are 521,257 and 521,261 bytes for this experiment's
binding URL. The remaining required identifiers are the 15 open obligations
across the three profiles. One optional temporary-care-home dependency is still
missing and reported. A complete declared-path result is not complete legal
coverage or support for every optional record.

The source-only evaluation uses a different binding URL and therefore has
slightly different package bytes and context identifiers. Do not compare IDs
without comparing every input. The actual public Reader and MCP service need
separate version-bound observations; this experiment makes no network or model
calls and does not certify a deployed release.

Receipt SHA-256: `ece6b2468056cfe143d84cb36f0dce60f53e0f8d06a8c19c66fac05a29e3edc6`
(10,327,973 bytes). Exact deterministic replay and fourteen offline admission
and denominator controls pass.
Whole selected evidence passages retain their exact literal hashes.

## Reproduce and inspect

The runner and guards derive from the
[earlier frozen comparison](../../qualification-context/2026-09-21/README.md).
This successor changes only the independently declared source pair and preserves
the archived-engine admission, no-symlink checks, bounded Git reads, fresh-output
rule and pre-budget denominator calculation. Both engines must match their
named immutable commits before import. The original comparison is not rewritten.

```sh
node --test validation/disability-context/2026-09-21/*.test.mjs
node --experimental-strip-types validation/disability-context/2026-09-21/compare.mjs \
  --dwp-root /path/to/okf-dwp \
  --explorer-root /path/to/okf-explorer \
  --check validation/disability-context/2026-09-21/attempt-01
```

For a new observation, replace `--check` and its value with `--output` and an
unused absolute directory. The runner refuses to overwrite retained evidence.
Replay compares every substantive field, excluding local timing/runtime labels.
These are known development questions, not a held-out benchmark. No model
ranking, entitlement determination or specialist acceptance follows.
