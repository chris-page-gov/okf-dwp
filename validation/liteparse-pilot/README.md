# LiteParse pilot validation

This is a local engineering experiment, not official DWP guidance or specialist
acceptance. The [beginner guide](../../docs/liteparse-pilot.md) explains the test.

## Preparation and review

- Source cases and protocol were committed as `b8a6013b` before candidate results.
- GPT-6 Sol at medium reasoning prepared the 12 initial and 24 conditional
  source windows, and implemented the harness in a separate workstream.
- The root agent inspected the source PDFs for both table expectations and
  known case 014. The [observation](source-review-2026-09-26/observation.json)
  records hashes, page numbers, renders and the scope of this model-assisted
  review. No independent human or benefits-specialist acceptance is claimed.
- A separate read-only engineering review found failure-retention, cache-identity
  and output-path issues. These were repaired before any DWP parser outcomes.
  All 13 local synthetic controls pass and exercise incorrect table associations, missing anchors,
  malformed geometry, path confinement and retained-output integrity.

The initial implementation and review used Codex subscription capacity. The
parser harness makes no answer-model or defect-detector calls. Frozen PDF and
text evidence, published corpus defaults and private correspondence are unchanged.

The harness was separately committed as `54e09b0d` before the DWP cases ran.
The post-run read-only review confirms the distinction between punctuation or
footnote-spacing differences and actual incomplete table associations. No
fixture, criterion or parser setting changed after observing the result.

## Retained run

The [stage-one report](../../evaluation/liteparse-pilot/stage-1-001/REPORT.md)
and its machine-readable JSON, raw outputs and per-case receipts retain the
actual outcome. A verified failed gate is still a valid research result;
subsequent stages require the declared gate to pass.

The source fixtures describe content expectations, not a representative quality
score for all DWP publications. Timings are one observation per window and
must not be described as a benchmark or model-affordability result.

Observed stage-one result: all 12 extractions complete; 8/12 literal anchor checks
pass; neither full table-association expectation passes. Seven cases meet all
their declared mechanical checks. The output occupies about 1.8 MiB. Stage 2
and the conditional question replay were not run. Case 014 is still letter-spaced.
The offline checker recalculates the same failed gate from retained bytes.

Local checks cover the 13 pilot tests, source fingerprints and all 36 source
anchor preflights, offline report reconstruction, semantic/publication contract,
private-input exclusion, backlog consistency and eight documentation-publication
controls. CI, merge and public deployment must be verified separately.
