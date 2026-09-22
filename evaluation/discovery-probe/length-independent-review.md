# Independent review of the length-aware discovery probe

Reviewed on 22 September 2026 by the coverage-review agent, read-only, in
`/Users/crpage/tmp/okf-dwp-discovery-cards-pilot`. Protocol `e1654a4f` was committed
before the implementation; the runner and result were still uncommitted when
reviewed. Their SHA-256 identities were:

- `scripts/probe_discovery_length.mjs`:
  `b24442457c64926d3662ebaaa49b1e32714f75e6acc667a003965a497d8ad76f`
- `evaluation/discovery-probe/length-run/comparison.json`:
  `df1b98376da89304f7f26707979b8f943bbbdeb1fd11f78fa26c47394d0bd958`

## Result

No arithmetic or ranking-method blocker found for this **unpublished diagnostic**.
No production adoption, complete evidence retention, answer quality or
summary-card effectiveness is established by the result.

## Checks performed

- Verified all 399 recorded input length/hash bindings, the unchanged committed
  protocol and the exact retained runner copy.
- Independently reconstructed document token frequencies, document frequencies,
  lengths and corpus totals in Python from all frozen source-unit shards.
  The corpus contains 49,626 units and 4,485,353 tokens, with mean length
  90.38312578084069 tokens.
- Recomputed both ranking arms for all 40 questions. Every top-16 ordinal list
  matched; all scores matched to relative tolerance `1e-12`.
- The implementation retains repeated document tokens for term frequency, while
  checking that their unique normalised tokens match the approved engine's
  corpus tokeniser. Query tokens remain the original hash-bound arm-A tokens.
- BM25 uses the declared formula, `k1=1.2`, `b=0.75`, the whole corpus denominator
  and canonical ordinal tie-break. No alias expansion, heading, benefit filter,
  summary or question-specific rule was introduced.
- Recomputed candidate-location overlap of 4→8, four gains (Staff 003, 004, 006
  and 040), zero losses and median candidate text of 13,617 bytes for B1.
- Confirmed that 626 of 640 B1 selections remain unresolved machine units.
  Staff 038 includes the 63-byte Chapter 7 paragraph 073462 citizenship fragment;
  this is one selected result, not the first result.

## Interpretation

The result is a useful lead that length and term-frequency treatment can reduce
long-fragment domination and recover additional previously listed candidates.
The review register is incomplete, so “four gains” means four gains on that
specific location-overlap measure. It is not independently judged relevance or
recall over a complete answer set.

Shorter selected material does not establish adequate boundaries: a short
fragment can be irrelevant or omit the condition needed to interpret it. The
retained unresolved-unit count and citizenship example make this limitation
concrete. B1 has not undergone graph expansion, final context-budget assembly,
claim-level answer grading, unseen evaluation or remote-latency measurement.

The later development experiment is explicitly motivated by B0's long-fragment
failure. Its preregistered parameters help prevent retrospective tuning, but do
not make the known questions held out. Structured discovery cards and summary
cards remain separate experiments.

No repository edits, provider/model calls, source acquisition or runtime changes
were made during this review.
