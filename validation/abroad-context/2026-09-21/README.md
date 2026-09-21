# Abroad semantic source comparison

**Local candidate comparison; all packages are insufficient.** This is not a
public MCP observation, a model-answer trial or specialist acceptance.

The [retained summary](attempt-01/summary.json) compares source
`723bcc5b015ab38a026625c2148edbd784edf7c7` with the additive candidate on the same
Explorer engine `c4f2de0a99b7bc2f8b8c8a06a3c715fb56b66d8e`. The
[manifest](attempt-01/manifest.json) binds the runner, source manifests, base
indexes and 24 complete compressed packages. Candidate packages use an explicit
unpublished test origin: they are not live service receipts.

## Findings

Six development questions, two sources and two byte budgets produce 24
assemblies. Ten further resolution/profile controls check domestic or unspecified
absence and other benefits. No network or model calls were made.

| Question and budget | Published baseline | Additive candidate |
| --- | --- | --- |
| General benefits abroad, 32 KiB | 2 records, 1 edge | 1 concept, 0 edges |
| General benefits abroad, 512 KiB | 1 of the 7 SPC pages | 5 of the 7 SPC pages; dependencies missing |
| Pension Credit abroad, 32 KiB | Metadata-budget refusal | Metadata-budget refusal |
| Pension Credit abroad, 512 KiB | 1 of 7 SPC pages; 3 of 3 then-declared paths | 7 of 7 SPC pages; 14 of 14 now-declared paths |

The three other Pension Credit phrasings also retain all seven whole pages and
14 required paths at 512 KiB. Overseas and outside-Great-Britain wording now
resolves the abroad concept. Domestic temporary absence and an unspecified
holiday do not. JSA, ESA, PIP and Universal Credit do not activate the Pension
Credit-specific requirement; Universal Credit semantic coverage is not invented.

**The 32 KiB general-question regression is retained, not concealed.** Adding
correct supporting material creates more traversal and diagnostic metadata.
Compact delivery can split an already selected package; it does not solve
assembly capacity. This source-only result therefore does not justify silently
replacing the public service default. All 203 obligations remain open.

The changed required-path denominator matters: the old three-path pass did not
test the newly discovered passage continuations. Candidate overlap and edge
counts are not answer-quality scores. These authored controls are not a held-out
specialist benchmark.

## Reproduce

Use a checkout of the DWP revision containing these generated candidate bytes
and a separate Explorer checkout at the exact engine commit above. Node 22 or
later is required. From the DWP root:

```sh
node --experimental-strip-types scripts/evaluate_abroad_semantic.mjs \
  --explorer-root /absolute/path/to/pinned-okf-explorer
```

The evaluator checks module hashes before importing the engine, reads the
baseline from Git, and admits only hash-bound corpus files. Add `--output` with
a fresh absolute directory outside the source checkout to retain another run;
an existing output directory is rejected. The frozen [runner](evaluate.mjs)
records the original executable. No command silently contacts the public
service or a model. The script is also an explicit CI step.

Read the [source and wider-gap audit](../../../docs/abroad-semantic-audit.md)
for interpretation, independent source review and publication boundaries.
