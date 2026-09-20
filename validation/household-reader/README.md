# Household Reader candidate browser evidence

These are **local candidate observations**, not public deployment receipts or
specialist acceptance. No existing combined-Reader observation was overwritten.
The [verification guide](../../docs/household-reader-verification.md) explains the
scope, exact identities, limits and reproduction commands.

## Passing executions

| Engine | Receipt | Source and graph screenshots | Ask packages |
| --- | --- | --- | --- |
| Chrome | [Observation](attempt-03-chrome/observation.json) | [Reader](attempt-03-chrome/statutory-reader.png), [graph](attempt-03-chrome/statutory-graph.png), [source timeline](attempt-03-chrome/statutory-source-timeline.png) | [Care home](attempt-03-chrome/care-home-context.json), [SDA](attempt-03-chrome/sda-context.json) |
| Firefox | [Observation](attempt-01-firefox/observation.json) | [Reader](attempt-01-firefox/statutory-reader.png), [graph](attempt-01-firefox/statutory-graph.png), [source timeline](attempt-01-firefox/statutory-source-timeline.png) | [Care home](attempt-01-firefox/care-home-context.json), [SDA](attempt-01-firefox/sda-context.json) |
| WebKit | [Observation](attempt-01-webkit/observation.json) | [Reader](attempt-01-webkit/statutory-reader.png), [graph](attempt-01-webkit/statutory-graph.png), [source timeline](attempt-01-webkit/statutory-source-timeline.png) | [Care home](attempt-01-webkit/care-home-context.json), [SDA](attempt-01-webkit/sda-context.json) |

Each directory also retains care-home and SDA UI screenshots, the narrow keyboard
view and the exact executed harness. All three executions retained the limiting
no-partner heading and unresolved SDA branches. Both packages remain insufficient
and report truncation; this is not evidence of complete answers.

## Retained unsuccessful attempts

- [Chrome attempt 1](attempt-01-chrome/failure.json): the harness inspected the
  Relationships control before opening it. All 20 literal body comparisons had
  passed. The application was unchanged.
- [Chrome attempt 2](attempt-02-chrome/failure.json): the harness incorrectly
  required Reader and context snapshot strings to be identical. Their distinct
  identities are connected through the context manifest. The application and
  corpus were unchanged.

Their screenshots and exact harness copies remain alongside the failures. They
are not counted as passing evidence or attributed to a product regression.

The [artifact manifest](artifact-manifest.json) binds all 41 retained execution
files by length and SHA-256. The offline checker verifies inventory completeness,
harness bindings, three-engine parity, the six package counts and byte limits,
ambiguity boundaries and retained failures. It does not execute the browser anew.

```sh
uv run --locked python scripts/check_household_reader_observations.py
```
