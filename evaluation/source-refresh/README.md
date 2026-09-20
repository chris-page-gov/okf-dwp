# Source refresh evaluation

- [Actual observed comparison](observed-comparison.json): frozen DMG/ADM inventory
  identities against 20 September official listing metadata. All 513 remain
  present; fresh PDF and extraction hashes remain unknown.
- [Baseline self-check](baseline-self-check.json): old inventories compared with
  themselves; a consistency check, not a fresh currency claim.
- [Synthetic controls](synthetic-controls.json): explicitly synthetic added,
  removed, changed-content, changed-extraction, date, classification and
  failed-publication cases.

All three outputs are generated offline by `scripts/compare_source_census.py`.
Its `--check` mode compares exact output bytes. The
[source-refresh guide](../../docs/source-refresh.md) explains the evidence and
the separate approval of any future source/runtime binding change.
