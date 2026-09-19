# Broader context discovery

The full DMG capture and the Ask OKF context index are different projections.
The frozen collection contains 331 PDFs and 14,743 measured pages. The original
Ask OKF acceptance profile selects 52 records for the imprisonment case.

`context/discovery/assembly-index.json` adds a separate research discovery view
of the existing full-DMG semantic graph. It does not modify the original index,
source release, published service version or acceptance receipts.

## What is projected

- All existing authored concepts, using their exact definition or description,
  existing scope note and original authored file provenance.
- Whole extracted source pages cited by those concepts, verified against the
  frozen PDF and extraction hashes. These remain normalised machine extractions,
  not official or human-reviewed interpretations.
- Existing chapter scope records and the custody profile's continuation pages,
  date observations and source-routing context.
- Original directed assertions between projected records, preserving identifiers,
  predicates, authority, assertion status and evidence provenance.

The projection contains 712 records: 282 concepts, 417 source pages, two source
metadata observations and 11 scope records. Its 1,105 relationships include four
DWP-specific predicates that the current shared engine does not traverse. Those
predicates remain unchanged and visible as unsupported relationships when reached.
Source containment remains in the full graph and is excluded from this view;
page provenance still identifies the source document.

## What this does not establish

There are **no completeness requirements** in this discovery profile. The engine
must return `evidence_status: insufficient`, even when it finds useful passages.
Full capture, concept coverage, successful retrieval and an answer supported for
a particular scope are separate things.

This build creates no aliases, semantic relationships, legal conclusions or
question-specific answer expectations. Existing aliases in the custody profile
are retained. Other concepts currently resolve through exact labels; ordinary
phrasing can fail to match a concept whose source evidence is present.

The snapshot identifier remains that of the frozen semantic source. The new
index digest identifies this distinct projection. A consumer integration must
bind the new index bytes explicitly; it must not silently replace a previously
approved immutable service version.

ADM bodies, consolidated legislation, tribunal judgments and subscriber-only
CPAG handbook text remain outside the acquisition. Capture dates are not dates
of publication, revision or legal commencement. All source instructions remain
inert data. No individual entitlement decision is supported.

## Reproduce and inspect

```sh
uv run --locked python scripts/build_context_discovery.py
uv run --locked python scripts/build_context_discovery.py --check
uv run --locked python -m unittest discover -s scripts -p 'test_context_discovery.py'
node --experimental-strip-types scripts/test_context_discovery.mjs --explorer-root ../okf-explorer
```

The adjacent `manifest.json` binds every input and the generated index by hash.
The producer verifies compressed and decoded semantic shards, source inventory,
selected PDFs, exact extracted pages, authored concept literals and relationship
evidence. No network access or model call is part of the build or context assembly.

The reusable consumer retains its 4 MiB index limit and normal context budgets.
Putting every source page into one context index would exceed both its 10,000
record limit and its byte limit. This view instead exposes the existing semantic
coverage while the complete text remains available through full-DMG search.
