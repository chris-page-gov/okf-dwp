# Bounded manual listing refresh — 20 September 2026

The [manifest](manifest.json) binds 13 complete official GOV.UK content API metadata
responses and their [request receipts](receipts.json). The source set is the DMG
collection, its 11 publication pages and the ADM publication. No PDF download,
text extraction or change to an existing source/runtime binding occurred.

The [refresh policy](../../domain-profile/source-refresh-policy.json) limits
requests and bytes. All requests succeeded in this run; future failure or budget
omission must be retained as unknown coverage. A metadata match does not prove
unchanged PDF content. These source files are additive and must not be overwritten.

Reproduce the [comparison](../../evaluation/source-refresh/observed-comparison.json)
offline with `uv run --locked python scripts/compare_source_census.py --check`.
See [source refresh and drift](../../docs/source-refresh.md) for definitions,
actual counts, limitations and review steps before adopting a new source version.
