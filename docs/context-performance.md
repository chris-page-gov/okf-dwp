# Context retrieval, allocation and loading experiments

## Current qualification allocation result

The [joint source/engine comparison](../validation/qualification-context/2026-09-21/README.md)
records 320 deterministic assemblies and verified replay across two source
versions, two engines, 40 tasks and two budgets. DWP `7f9feb9634e3d94004853b838462aca132c505a5`
and Explorer `c4f2de0a99b7bc2f8b8c8a06a3c715fb56b66d8e` retain 177 of 177 candidate
occurrences and 433 of 433 activated declared paths at 256 KiB and 512 KiB.
All seven household pages remain inspectable for Staff 012 and 013. All contexts
remain insufficient; 203 named obligations remain open. These candidates await
protected publication and separate public service/browser checks.

The comparison separates source modelling from allocation. With the earlier
source at 512 KiB, the new allocator displaces six incidentally selected household
pages because those pages were not declared required. Adding explicit qualification
paths restores all seven at both budgets. This is a useful measured trade-off,
not a guarantee that unmodelled qualifications will survive. The larger-budget
permanent-care-home package still exposes a missing optional temporary-residence
dependency. [Current budget controls](semantic-expansion.md#context-sizes-and-practical-limits)
also retain a legitimate zero-record metadata refusal for Staff 012 at 64 KiB.

The joint receipt's timings are single local observations. They do not establish
a speed gain. The separate controlled loading experiment below is historical
and retains its original inputs, counts and interpretation.

## Historical ambiguity and loading experiment

The retained candidate Ask OKF assembler shows evidence for each possible meaning of an ambiguous term and
loads up to four corpus files at a time. This improves inspection and reduces
serial waiting. It does not choose the meaning or establish a correct answer.

## What was held fixed

The experiment uses the previously published 40 staff questions and semantic
index, before the additional household relationships and statutory bodies. Both
engines read the same frozen inputs. Every corpus file must match its recorded
length and SHA-256 digest: a digest is a content fingerprint used to detect a
changed file.

The [retained experiment](../validation/context-performance/2026-09-21/README.md)
includes its exact harness, both engine versions, input index, question registry,
corpus manifest, full comparison and file digests. It makes no web or model calls.
The retained question set is a development set that informed the work, not an
independent test of unfamiliar questions.

## Retrieval result

| Measure | Earlier engine | Candidate engine |
| --- | ---: | ---: |
| Expected source-page hits across the 40 cases | 169 of 177 | 171 of 177 |
| Sufficient packages | 0 | 0 |
| AI answers generated | 0 | 0 |

Thirty-eight packages are byte-identical. Only staff-008 and staff-009 change:
both contain an ambiguous abbreviation. The assembler now retains labelled
alternative branches while leaving the ambiguity unresolved. It does not merge
the alternatives or activate their evidence requirements as if a meaning had
been selected.

The other six missing candidate pages had no directed path from the resolved
concepts in this frozen index. Increasing the number of selected records cannot
create a missing relationship. Their later source-grounded authoring belongs to
the [household evidence expansion](household-evidence-expansion.md), which must be
evaluated separately.

These are page-retrieval counts, not legal accuracy, claim-level correctness or
proof that the evidence answers a question completely.

## Loading result and its limits

The harness adds an artificial ten-millisecond delay to each read from cached
local bytes. Three repetitions alternate engine order. The table shows the
median, or middle, duration for each case from the retained portable run.

| Case | Earlier serial loading | Four-file loading |
| --- | ---: | ---: |
| staff-005 | 392.89 ms | 174.21 ms |
| staff-008 | 366.84 ms | 192.81 ms |
| staff-020 | 304.24 ms | 155.42 ms |
| staff-024 | 340.72 ms | 164.78 ms |
| staff-025 | 330.49 ms | 169.57 ms |

The peak number of concurrent reads was four. This isolates scheduling under a
controlled delay. It is **not** a public-network or service benchmark, a promise
about Monday's room network, or a measure of AI answer speed. Hardware load,
browser behaviour, caches and real network latency change elapsed time.

The semantic index may be up to 8 MiB; ordinary corpus manifests, search files and
source-record files remain capped at 4 MiB each. Each assembly retains its 16 MiB
transfer and 32 MiB decompressed limits, with reservations made before parallel
reads. Output remains bounded at 524,288 bytes. These are per-operation data
limits, not a guarantee about total process memory. The remote service's existing
8 MiB cache stays bounded; a large base index can cause eviction and refetching.

## Reproduce without replacing the observation

From this repository, use the Node version supported by the Explorer consumer:

```sh
node validation/context-performance/2026-09-21/verify.mjs
OKF_CONTEXT_COMPARISON_OUTPUT=/tmp/okf-context-comparison-new.json node --experimental-strip-types validation/context-performance/2026-09-21/compare.mjs
```

Choose an output filename that does not exist. The harness refuses to overwrite
a previous observation. `OKF_DWP_CHECKOUT` optionally points to another checkout
containing the same frozen corpus shards; their digests still have to match.

An [earlier harness warning](../validation/context-performance/2026-09-21/earlier-attempt/README.md)
is preserved separately. Its exact pre-fix runner was not retained, so that
attempt is not presented as independently replayable. The final run has its own
executed harness digest and unchanged earlier observations.
