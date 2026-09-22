# Independent review of the terminology discovery probe

Reviewed on 22 September 2026 by the coverage-review agent, read-only, against
`/Users/crpage/tmp/okf-dwp-discovery-cards-pilot` commits `f00d299a` (protocol)
and `64c9cc1d` (implementation and retained result). Production source is pinned
to DWP `7412d1d02e023794ebb1d5a5f385f08f59be7ee2`; admitted Explorer engine is
`2e557f4b78db10cf69471e4a106a98d3a6c43c5b`.

## Result

No blocker found for the stated **unpublished diagnostic** scope. This review
does not approve runtime adoption or establish relevance, answer accuracy,
specialist acceptance, affordability or summary-card effectiveness.

## Independent checks

- Confirmed the protocol commit precedes the results and its exact bytes remain
  unchanged. Production source, units, logical context, domain profiles and the
  existing logical evaluation have no diff from the pinned source commit.
- Verified all 234 input length/hash bindings and the exact retained runner copy.
- Recomputed all 80 top-16 candidate ordinal/score lists independently in Python
  from the frozen postings, using the recorded query and expansion tokens,
  integer inverse-document-frequency formula and canonical ordinal tie-break.
  Every result matched.
- Used the approved engine's pure tokenisation and concept-resolution functions
  to recompute all 40 question-token, resolved-concept and alias-expansion rows.
  Every result matched the protocol's token limits and expansion ordering.
- Inspected the runner's actual-engine comparison: it asserts that arm A's full
  candidate order equals the approved assembler's lexical candidate order for
  each question. The retained result records all 40 passing. This review did not
  perform a second full assembly run.
- Recomputed total candidate-location overlap as 4 for A and 2 for B0, with zero
  gains, losses only for Staff 018 and 025, and 38 unchanged occurrences. Median
  total candidate text is 367,376 bytes for A and 469,267 bytes for B0.
- Confirmed the Staff 026/033 duplicate yields identical arm-A results; duplicate
  occurrences are disclosed rather than presented as independent generalisation.

## Method and interpretation

Arm B0 doubles every original query term's weight and gives expansion terms
weight one. Uniformly doubling original scores preserves their relative ranking;
the relative alias weight is stated in the pre-implementation protocol. The
result does not conceal a post-observation weight adjustment. Absolute scores
from the two arms should not be compared as if they had the same scale.

B0 breaks declared labels and aliases into independent tokens, including
multiword aliases. This is the deliberately simple token-expansion method being
tested. It is not phrase-aware or a test of checked hierarchical cards,
principal-subject annotations, model summaries, embedding search or a different
field-ranking method.

The 42 earlier candidate locations are incomplete review leads. Geometric
overlap is not an independent relevance judgement or a gold-standard answer
measure. The README correctly limits its findings to this shortcut, its
pre-graph candidate ranking and its increased candidate-text burden. It does not
claim that final evidence packages or model answers deteriorated by these exact
counts. Rejecting adoption without demonstrated benefit is supported; rejecting
all semantic discovery or summary-card approaches would not be.

No repository edits, source acquisition, provider/model calls, live-service
changes or publication were made during this review.
