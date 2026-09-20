# Frozen context performance observation

This directory retains a local development comparison of generic Explorer
retrieval and file scheduling. It is not a deployment receipt, current-law
assessment or model-answer trial. All 40 resulting packages remain insufficient.

## Files

- `baseline/`: the three engine files from Explorer commit
  `fc71d65b8f5cfc860d52afe98a5e45b88231f3e5`.
- `candidate/`: exact candidate engine files executed by this harness.
- `overlay.json`: frozen published staff semantic index; SHA-256
  `79ac30aef41ac467db83ec6b79ed20e4a4cc9330461d08713f45ea5830cb6e2d`.
- `cases.json`: unchanged public question registry and expected source candidates.
- `manifest.json`: the original corpus manifest. The harness explicitly rebinds
  its semantic base to the frozen overlay; record and search shards stay bound
  to the original file digests.
- `compare.mjs`: exact executed, repository-relative harness. It imports the
  retained engines and reads local corpus files only.
- `comparison.json`: 40 before/after package comparisons and 30 scheduling
  observations: five cases, two engines, three repetitions.
- `artifacts.json`: byte counts and SHA-256 digests for every retained file other
  than that manifest itself.
- `verify.mjs`: offline integrity and internal-consistency checker.
- `earlier-attempt/`: the separately labelled initial harness warning and its
  preservation limitation.

The input is deliberately older than the subsequent household and statutory-body
expansion, so the comparison isolates engine behaviour from changed semantics.
No private correspondence or raw model reasoning is included.

## Reproduce

From the repository root:

```sh
node validation/context-performance/2026-09-21/verify.mjs
OKF_CONTEXT_COMPARISON_OUTPUT=/tmp/okf-context-comparison-new.json node --experimental-strip-types validation/context-performance/2026-09-21/compare.mjs
```

The output path must be new. The default output is the retained `comparison.json`
and therefore fails early on an ordinary replay. Use a fresh path as above.
If the corpus resides elsewhere, set `OKF_DWP_CHECKOUT` to that checkout. No
dependencies are downloaded and no network requests are made.

Timings vary across machines and runs. The method adds ten milliseconds per
cached local file read; it measures scheduling, not public network performance.
The deterministic checks are package identifiers, candidate coverage and bounded
fail-closed results. The [explanation](../../../docs/context-performance.md)
describes the findings and limits.
