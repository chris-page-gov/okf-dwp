# Public household Reader observation

**One real public Chrome journey passed**, observed on 20 September 2026 at
22:54:29 UTC (23:54:29 BST). Source commit:
`3ef0e786e9a18e76fa17c7d925ff509d6d6c9f84`.

The [guide and repeat command](../../../docs/household-reader-public-verification.md)
explain the scope and limits. This is separate from the local three-browser
observations and from the compact service: no service or MCP request was made.

- [Passing observation, public URLs, response hashes and phase timings](attempt-02-chrome/observation.json)
- [Executed passing harness](attempt-02-chrome/executed-harness.mjs)
- [Actual public application manifest](attempt-02-chrome/app-manifest.json)
- [Care-home package](attempt-02-chrome/care-home-context.json)
- [SDA package](attempt-02-chrome/sda-context.json)
- Screenshots: [concept facet](attempt-02-chrome/concept-facet.png),
  [statutory Reader](attempt-02-chrome/statutory-reader.png),
  [statutory graph](attempt-02-chrome/statutory-graph.png),
  [source timeline](attempt-02-chrome/statutory-source-timeline.png),
  [care-home Ask](attempt-02-chrome/care-home-ask.png),
  [SDA alternatives](attempt-02-chrome/sda-alternatives.png).
- [Retained failed first attempt](attempt-01-chrome/failure.json),
  [its exact harness](attempt-01-chrome/executed-harness.mjs) and
  [actual reset state](attempt-01-chrome/failure.png).
- [Hashes of all 16 execution files](artifact-manifest.json).
- [Exact comparison with the earlier local packages](local-comparison.json).

The first attempt successfully checked the public application and eight-record
concept reduction. Its harness then expected a toolbar that the application
intentionally hides after resetting the view. The screenshot shows the correct
20,044-record unfiltered state. The second harness checks the Reader result
summary instead. The product, application fingerprint and corpus were unchanged;
the failure has not been removed or counted as a pass.

The passing run verified all 21 application files independently, plus 14 files
actually loaded by the browser. It observed 294 corpus responses covering 270
unique files, with 36,913,216 response-body bytes. Every listed response matched
bytes read from the exact Git commit. There was no routing, interception, local
substitution or model call, and no console or network error.

The public packages retain the same source and semantic content as the local
ones. Only `binding.index_url`, `budget.used_bytes` and `context_id` differ: the
public URL adds 69 bytes and changes the derived context identity. Both remain
insufficient and truncated. This exact comparison is recorded, rather than
claiming identical package IDs across different locations.

Check retained evidence offline:

```sh
uv run --locked python scripts/check_public_household_observations.py
node --test scripts/test_public_household_reader.mjs
uv run --locked python -m unittest discover -s scripts -p test_public_household_observations.py
```

An offline pass verifies retained bytes and source bindings; it does not rerun
the public browser or attest a later deployment. No physical mobile device,
human screen-reader session, cross-browser public household run or complete
legal assessment is claimed here.

The checker rejects oversized files and symbolic links, including linked parent
directories, before reading evidence. It size-checks immutable Git blobs and
caps their capture. The public observations were moved intact to this separate
directory so the earlier local inventory remains unchanged; all 16 retained
execution-file hashes still match their original manifest.
