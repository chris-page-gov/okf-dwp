# Length-aware ranking probe

**Status: diagnostic only; promising candidate-ranking lead, unsuitable for
runtime adoption without further review.** This is a second, separate offline
experiment motivated by the long-fragment failure in the [alias probe](README.md).
It does not test summaries or establish answer quality.

The protocol was frozen in commit `e1654a4f` before implementation and execution.
The source, approved engine, all 40 development questions, 16-candidate limit and
original question tokens are unchanged. No question-specific rules, aliases,
heading metadata, source acquisition or model calls were added. No source unit,
production index, authored relationship or completeness status changed.

## Method

The current score adds a contribution for each matching question word. A long
fragment can win by mentioning many terms across unrelated passages.

The experimental score uses **BM25**, a lexical ranking formula which considers
how often a term occurs and how long the passage is, as well as how common the
term is across the corpus. Repeating a word has diminishing benefit. The fixed
parameters are `k1=1.2` and `b=0.75`. The exact formula, normalisation and tie-break
are in [length-protocol.json](length-protocol.json). Document lengths and term
frequencies are measured from every full frozen source-unit record.

The runner independently reconstructs the old ranking from those same records;
its candidate ordinals and scores agree with the retained baseline for 40/40
questions. The earlier baseline was checked against the approved full engine.
The B1 arm performs ranking only: it does not run graph expansion, dependency
closure, final assembly or answer generation.

## Observation

| Measure | A: current literal ranking | B1: length-aware ranking |
| --- | ---: | ---: |
| Earlier candidate-location overlaps | 4 | 8 |
| Median full text in the first 16 candidates | 367,376 bytes | 13,617 bytes |
| Cases gaining an earlier candidate location | — | 4 |
| Cases losing an earlier candidate location | — | 0 |

The gains occur for Staff 003, 004, 006 and 040. These are overlaps with incomplete
source-review leads. They are **not four newly answerable questions**, a measured
increase in independently judged relevance, or evidence of preserved
qualifications. The same 40 known questions remain development cases.

Every selected ID, term contribution, document frequency, source location and
boundary status is retained in [length-run/comparison.json](length-run/comparison.json).

## Why smaller candidates are not enough

Of B1's 640 candidate occurrences, **626 are still marked unresolved**; 14 have
an authored complete-within-declared-boundary status. These are occurrences,
including repeated units across questions, not distinct units or complete
answers. A shorter candidate can omit an indispensable definition, continuation
or exception. Reduced candidate bytes therefore cannot be called an evidence
retention improvement.

- **Staff 006, savings and Pension Credit:** an earlier Chapter 77 review
  location is now among the first 16, but the leading matches still include
  Savings Credit wording and historical amendment material. This does not
  establish the capital treatment or a maximum savings limit.
- **Staff 038, claiming Carer's Allowance:** the highest ranks include tiny
  citizenship fragments, one only 63 bytes long. Length correction does not
  recognise that “Citizen” is incidental task wording or establish the benefit's
  principal claim conditions.
- **Staff 040, caring for two people:** an existing Carer's Allowance review
  location enters the candidates, while the first-ranked item concerns the UC
  carer element. The two benefits must remain distinct.
- Historical amendments and current chapter extracts can still compete or
  duplicate one another. No legal-version or applicability resolution has been
  established by this score.

## Next decision

The evidence supports testing length-aware ranking as a baseline in the
structural/card experiment. It does not justify replacing the live ranker yet.
The next comparison needs checked unit boundaries, principal subject and benefit
scope, source-version roles, complete source retrieval and independently judged
relevance and qualification retention. The [summary-card proposal](../../docs/discovery-cards-experiment.md)
remains unimplemented. Summary generation cannot substitute for those checks.

## Reproduce

```sh
node --experimental-strip-types scripts/probe_discovery_length.mjs --explorer-root /path/to/approved/okf-explorer
```

Use a fresh output leaf; the runner refuses to overwrite an earlier observation.
It verifies protocol inputs, all consumed source shards and the four approved
engine modules. The exact executed runner is retained with the result. No
network or provider calls are made.
