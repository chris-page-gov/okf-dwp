# Ignored-person source and allocator comparison

The additional ignored-person and normal-residence qualifications expand the
represented evidence dependencies, but **the care-home cases no longer retain
all required paths within 512 KiB**. This is a measured capacity regression, not
an improvement in answer quality. No expectations, obligations or byte limits
were reduced to make the result pass.

The [observation](attempt-01/comparison.json) records 320 offline assemblies:
40 staff-question occurrences × two immutable sources × two engines × two byte
budgets. All 320 remain `insufficient`, with `ai_answer: null`. Exact replay
passed; selected source text was checked against its literal digest. There were
no metadata-only fallbacks and no omitted activated requirement descriptions.
No model or public-service calls were made.

## Immutable inputs

| Input | Commit or SHA-256 |
|---|---|
| Earlier partner source | `7e5fdb9b906052914b307c17c0fd19feb2d008a7` |
| Ignored-person source | `c44bc3a111d18b6d4098a148a9a1b67c1411882b` |
| New semantic index | `5cba980ec155a5fdc20610aaa95898374a933abf084f94cb72ef71657ab882a6` |
| Earlier engine | `b9a3b68b6dbf222f9a73cc8f450dd53f126e1b55` |
| Required-evidence allocator | `c4f2de0a99b7bc2f8b8c8a06a3c715fb56b66d8e` |
| Protocol | `d467d0bb0b55f596000d4b7c8a059d52e150b26792d1a8065fdb297b6c7cd5e9` |
| Observation | `c45dcc69170db2d74ca144f3b9cdbbbb8fe514dbaef1e0c8695d372e82fed785` |

The source changes from 903 records/1,482 assertions to 913/1,526. All 203
complete obligation objects are unchanged, including 43 unverified evidence
closure obligations. Questions and their candidate-page registry are identical.
This does not establish current legal applicability or specialist approval.

[Protocol](protocol.json), [runner](compare.mjs) and both engines are retained
with the observation. The guards, metrics, tests and engine modules were copied
unchanged from the [partner comparison](../../partner-context/2026-09-21/README.md);
the runner changes only its approved earlier-source commit. The declared-path
census is calculated independently before output trimming, so missing output
cannot remove requirements from the denominator.

## Results across all 40 cases

Candidate hits are case–candidate-page occurrences, out of 177. Paths are
activated requirement-path occurrences, not distinct graph edges. The richer
source raises their denominator from 585 to 765; compare those denominators
explicitly. Each cell activates 91 requirement occurrences.

| Budget | Source | Earlier engine: candidates; paths | Allocator: candidates; paths |
|---|---|---|---|
| 256 KiB | Partner | 164/177; 329/585 | 177/177; 449/585 |
| 256 KiB | Ignored-person | 159/177; 309/765 | **171/177; 393/765** |
| 512 KiB | Partner | 176/177; 503/585 | 177/177; 585/585 |
| 512 KiB | Ignored-person | 176/177; 465/765 | **177/177; 647/765** |

The allocator improves retention relative to the earlier engine on either
source. Adding the new dependencies nevertheless reduces retention at a fixed
budget. This experiment does not change the approved service source or engine.
Single in-process timings are diagnostic only: cache and execution order prevent
causal performance claims.

## Conditional household cases

The following rows use the ignored-person source and allocator. The 17-page
group is the union of the new ignored-person and normal-residence dependencies.
Some of these pages existed in the earlier source but were not declared required
through these new concepts; their absence is not scored against that old source.

| Case | KiB | Records | Paths retained/declared | Required records absent | Open obligation IDs | Diagnostic union IDs | 17-page group selected |
|---|---:|---:|---:|---:|---:|---:|---:|
| Staff 012 | 256 | 5 | 6/153 | 46 | 15 | 133 | 0 |
| Staff 013 | 256 | 5 | 6/153 | 46 | 15 | 133 | 0 |
| Staff 014 | 256 | 18 | 27/67 | 21 | 15 | 59 | 1 |
| Staff 017 | 256 | 19 | 29/67 | 20 | 15 | 56 | 2 |
| Staff 012 | 512 | 36 | 94/153 | 18 | 15 | 54 | 5 |
| Staff 013 | 512 | 36 | 94/153 | 18 | 15 | 54 | 5 |
| Staff 014 | 512 | 56 | 67/67 | 0 | 15 | 23 | 17 |
| Staff 017 | 512 | 55 | 67/67 | 0 | 15 | 15 | 17 |

At 512 KiB, Staff 012/013 retain six of seven household support pages: Chapter 77
page 19 is missing. At 256 KiB they retain none of those seven pages and no source
evidence records. The old partner source retained seven at 512 KiB and one at
256 KiB. The larger declared-path counts above include other activated profiles,
not just each case's own authored profile.

**A diagnostic union is not a missing-record count.** Staff 012's 54 diagnostic
identifiers at 512 KiB include three retained concepts. Its 18 absent directly
required source records and 15 registered obligation identifiers are distinct
categories. Likewise, Staff 014 retains all declared required records at 512 KiB
but still has unresolved obligations and optional-dependency diagnostics.

[Derived census](derived-census.json) lists the exact IDs, omitted paths and
budget reasons. Across all 40 cases, the allocator's absent directly required
record occurrences rise from 93 to 174 at 256 KiB, and from 41 to 77 at 512 KiB.
These are sums of per-package counts, not unique corpus records. Even retaining
all declared paths does not establish completeness: required IDs may also exist
without an explicit path. All 203 underlying obligations remain open.

## Actual evidence and metadata bytes

A separate [byte census](byte-census.json) replayed 16 allocator packages
(012/013/014/017, both sources and both budgets). Each complete canonical package
had to match its original observation hash before any byte measurement was
accepted. The frozen 320-run observation was not modified.

For Staff 012:

| Source | Budget KiB | Whole package bytes | Selected evidence text bytes | Requirements property bytes | Relationships property bytes | Missing-evidence property bytes |
|---|---:|---:|---:|---:|---:|---:|
| Partner | 256 | 258,930 | 6,043 | 77,216 | 76,336 | 24,139 |
| Ignored-person | 256 | 255,592 | **0** | 140,211 | 26,134 | 32,956 |
| Partner | 512 | 524,089 | 86,756 | 64,076 | 176,668 | 2,645 |
| Ignored-person | 512 | 521,393 | **45,608** | 124,383 | 170,815 | 12,863 |

Evidence text sizes include JSON escaping and quotation marks, as represented
in the actual canonical package. Top-level property sizes include the property
name, colon and value. The receipt provides an additive top-level partition and
a separate nested partition of `selected`; **do not sum the nested partition a
second time**. Raw text and provenance sizes are explicitly overlapping metrics.

Most remaining bytes describe record identity, provenance, paths, requirements,
relationships, scope and gaps. They are not all disposable overhead. This shows
representation cost alongside selected evidence; it does not measure all omitted
required text, model tokens, or prove that a proposed compact format would fit.

## Reproduce and inspect

Run from an OKF-DWP checkout containing both frozen source commits; the Explorer
checkout must contain both engine commits. Set the paths to your own local
checkouts. Node.js must support `--experimental-strip-types`.

```sh
node --test validation/ignored-person-context/2026-09-21/*.test.mjs
node --experimental-strip-types validation/ignored-person-context/2026-09-21/compare.mjs \
  --dwp-root "$DWP_CHECKOUT" --explorer-root "$EXPLORER_CHECKOUT" \
  --check validation/ignored-person-context/2026-09-21/attempt-01
node validation/ignored-person-context/2026-09-21/summarise.mjs \
  "$DWP_CHECKOUT" validation/ignored-person-context/2026-09-21/attempt-01 \
  | cmp - validation/ignored-person-context/2026-09-21/derived-census.json
node --experimental-strip-types validation/ignored-person-context/2026-09-21/byte-census.mjs \
  "$DWP_CHECKOUT" "$EXPLORER_CHECKOUT" validation/ignored-person-context/2026-09-21/attempt-01 \
  | cmp - validation/ignored-person-context/2026-09-21/byte-census.json
```

For a new 320-assembly observation, replace `--check` with `--output` and choose
an **unused** directory, for example `/private/tmp/okf-ignored-person-new-observation`.
Existing files, directories and symlinks are refused. Engine hashes, archive
allowlists and immutable source identities are checked before archived imports.
No arbitrary external recipe is executed.

Validation completed: 18 offline controls; exact 320-package replay; 16 exact
supplementary package hashes; deterministic derived-census reproduction. These
are local engineering observations, not public-browser acceptance or a model
accuracy trial. Earlier observations and frozen model packages remain unchanged.
