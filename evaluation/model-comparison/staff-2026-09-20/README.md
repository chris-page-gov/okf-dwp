# Paired staff question trials

Read [the beginner guide](../../../docs/staff-model-trials.md), then [the protocol](protocol.json), [fixed inputs](contexts.json) and [results ledger](../../../validation/model-comparison/staff-2026-09-20/results.json).

The four substantive cases and one unknown control are selected before substantive model calls. Each provider receives the same public package, authored prompts and schema. All substantive packages remain insufficient and truncated. Neither model output nor agreement is a gold answer.

## Retained history

- `budget-controls/65536/`: initial pre-fix small-budget failures.
- `budget-controls/262144/`: initial pre-fix larger-budget observations.
- `budget-controls/65536-corrected/`: corrected small-budget observations with evidence records but no paths.
- `contexts/`: final corrected 262,144-byte paired inputs.
- `input-snapshots/`: digest-named earlier protocols, manifests and executable harness text for retained attempt provenance. They are historical artefacts; use the current script for offline verification.

The first Claude unknown control is rejected under the initial strict event policy. The documented amendment permits only its internal schema formatter; a separate second control is retained. External evidence tools remain unavailable.

The final input package SHA-256 digests and the shared engine file digests are recorded in `contexts.json`. The exact shared Explorer consumer commit is `602622771e222db880a9d53b299db1d79d612409`.

## Historical input archive after publication projection

[input-snapshots/assembly-index.json](input-snapshots/assembly-index.json) preserves the exact pre-projection index (SHA-256 `8c22f9a259a8b07cbc41b837693aa4f7ad4da48175fca8753cfcc3b0172d6d97`). The original exporter is also retained under its recorded digest. The current replay script permits only `--check` and uses these archived bytes; it does not pretend the subsequently rebuilt semantic index is the trial input.

The legal metadata's unused opaque effect identifiers were subsequently omitted in a documented public projection. Trial source hashes therefore describe the earlier metadata observation, not today's bytes at a mutable source URL. [The projection ledger](../../../source/legal-discovery-2026-09-20/publication-projection.json) reconciles the old and current hashes. No original trial context, context catalogue, model answer or receipt was rewritten.
