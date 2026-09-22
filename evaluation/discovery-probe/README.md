# Terminology expansion probe

**Result: reject this simple ranking variant for adoption.** This is an offline
diagnostic, not a production retrieval change or an answer-quality evaluation.
It supports the proposed discovery-card work by testing a cheaper explanation
first: whether adding the vocabulary already declared in the bundle is enough.

The protocol was committed as `f00d299a` before implementation and observation.
Source inputs are bound to DWP `7412d1d0`; the approved Explorer engine is
`2e557f4b`. All 40 original question occurrences are unchanged. No new profiles,
aliases, summaries, source acquisitions or model calls were made.

## Observed result

| Measure | A: current literal ranking | B0: declared terminology expansion |
| --- | ---: | ---: |
| Earlier source-candidate location overlaps | 4 | 2 |
| Median total text in the first 16 candidates | 367,376 bytes | 469,267 bytes |
| Cases gaining an earlier candidate location | — | 0 |
| Cases losing an earlier candidate location | — | 2 |

The reconstructed baseline agrees with the actual approved engine's lexical
candidate order for **40/40** questions. These are the 16 lexical candidates
before graph expansion and final context selection. They are not the full
returned evidence packages or their assembly byte budgets.

The 42 earlier source locations are incomplete review leads, not a complete gold
standard. Geometric overlap with them does not establish relevance or answer
support. Therefore the result rules out adopting this particular shortcut; it
does not prove that every conceivable alias-based approach is ineffective.
All cases and candidate IDs, scores, declaring concepts, source URLs and byte
counts are retained in [comparison.json](run/comparison.json).

## Examples explaining the failure

- **Staff 006, maximum savings and Pension Credit:** adding capital/SPC and other
  declared terms still favours long tax-credit migration memos and mixed source
  units. The candidate text total rises from 352,349 to 660,520 bytes. Neither
  arm retrieves a previously listed candidate location among its first 16.
- **Staff 018, partner and permanent care home:** the known candidate location
  drops out; the question's missing benefit remains unresolved. Extra household
  and residence terms do not establish which benefit's rules should apply.
- **Staff 025, IIDB and State Pension age:** the known candidate drops out while
  historical amendments and abbreviation lists enter the highest ranks.
- **Staff 038, Citizen and Carer's Allowance:** the unusual question word Citizen
  helps citizenship and international-competence material outrank basic claim
  conditions. Expanding Carer/CA alone does not repair task interpretation.

Long fragments can contain many of a question's terms across unrelated rules,
examples and citations. The current matching score adds those term contributions
without distinguishing main subject from an incidental mention. Some long
fragments are explicitly unresolved fallback material. A larger matching-word
set amplifies that problem in this probe.

## Consequence for the summary-card idea

The next experiment needs a separate subject-and-scope discovery representation:

1. Check the section hierarchy and rule boundaries before inheriting headings.
2. Identify principal benefit/variant, circumstance and important qualification;
   distinguish these from mentions in examples or citations.
3. Search short structured cards alongside full text, recording why they match.
4. Fetch complete original units and their declared dependencies before using
   them as evidence. A summary never stands in for missing source text.
5. Judge relevance and preserved qualifications independently, then test any AI
   answers against the delivered evidence at claim level.

This does not change the current release's `insufficient` results. It also does
not justify bulk generation of unchecked summaries. The proposed structural and
semantic-card arms remain unimplemented.

## Separate length-aware experiment

A subsequent [fixed-parameter ranking probe](length-ranking.md) tests the
long-fragment diagnosis. It retains its own protocol and observation. Its
results do not change this alias probe or validate summary cards.

## Independent check

The [independent review](independent-review.md) verified all 234 input bindings,
recomputed every candidate ranking and checked the interpretation. It found no
blocker for this diagnostic scope. It did not endorse runtime adoption or claim
that structured cards had been tested.

A separate [publication review](publication-review.md) checked preservation,
confinement and documentation. Its minor reproduction clarification is addressed
in `6acb36d1`: the instructions below explicitly preserve existing outputs in an
isolated scratch checkout.

## Reproduction and retained failure

Use an isolated scratch checkout of this research revision. A clean checkout
already contains the committed `run/` observation, so preserve that directory
outside the scratch checkout before replaying. The runner deliberately refuses
to overwrite it. Run these commands from the scratch repository root:

```sh
probe_archive="$(mktemp -d)"
mv evaluation/discovery-probe/run "$probe_archive/run"
node --experimental-strip-types scripts/probe_discovery_terminology.mjs --explorer-root /path/to/approved/okf-explorer
```

The runner verifies the fixed protocol inputs and four immutable engine modules
before execution. It uses confined, hash-bound local corpus reads. Its output
leaf must not exist. Keep the original directory in `probe_archive` for the
byte comparison; do not delete or amend the original research checkout.
`run/runner.mjs` preserves the exact executed script.

An initial probe attempted the unsupported budget key `max_edges`. The engine
rejected it before any observation was written. The corrected baseline call
uses the same supported `{max_bytes: 524288}` budget as the retained DWP
comparison. No engine bound or validator was changed.
