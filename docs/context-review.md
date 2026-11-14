# Inspect discovery and delivery separately

This independent experimental candidate addresses the reported truncation in
four layers: question routing, bounded retrieval, whole-item assembly and host
delivery. It supplies evidence for engineering review, not benefits advice,
an award calculation or an individual entitlement decision.

## Measured source-retrieval result

The additive graph candidate passes the agreed declared-source gate. The
[retained evaluation](../evaluation/retrieval-gate/graph-evaluation.json) records
263/263 persona target occurrences, 35/35 original custody targets and 4/4 UC
targets, including their required directed source paths. Every selected package
arrives intact through responses whose complete duplicated MCP/JSON-RPC envelope
is at most 8,192 bytes. There are no assembly omissions in this run.

The [persona coverage ledger](../evaluation/retrieval-gate/persona-coverage.json)
covers all eight authored personas and all 21 declared interest areas. The
75-case protocol contains 62 positive retrieval cases, ten boundary controls,
two UI checks and one integrity check. The original 40 question occurrences are
preserved. Five underspecified prompts retain their original wording as boundary
controls and have separately documented benefit-framed positive pairs. Their
declared source targets have not been dropped. UI and specialist checks retain
their own pending status rather than being counted as successful retrieval.

The [first failed run](../evaluation/retrieval-gate/attempts/01-initial-70-case-failures.json)
is retained. After freezing the graph, runtime and client, a separate agent ran
24 withheld wording cases: 45/45 targets in 12 positives and 12/12 negative
controls passed. The [receipt](../evaluation/retrieval-gate/withheld/attempt-01/receipt.json)
binds the protocol and frozen bytes. This is a bounded withheld wording trial,
not an independent human blind benchmark or proof of complete legal reasoning.

Independent review then tightened concept-conflict admission, made resolver
budget exhaustion explicitly incomplete and increased the collector's bounded
session from three to ten minutes. The 30-second call and 8 KiB response limits
remain unchanged. The largest measured package needs at least 331 calls; a
virtual-clock regression verifies complete delivery at 750 ms per call, beyond
the old three-minute ceiling. A separate
[post-review replay](../evaluation/retrieval-gate/withheld/attempt-02/receipt.json)
passes the same 45 targets and 12 controls under the corrected identities.
It is a regression replay, not a fresh blind trial. The original trial remains
byte-for-byte replayable from producer commit
`5516e6c604793a5c98c57a3ddb9c3c13f46afe64` through the disposable-tree harness.

## How graph navigation helps

`domain-profile/retrieval-graph/*.yamlld` compiles into the separate
`retrieval-graph/graph.json`. It preserves frozen evidence and requirements,
adds 28 source-bound directed navigation repairs, 11 guarded compositional
concept bridges and three topic navigation profiles. These additions are
explicitly model-derived, unreviewed navigation hypotheses. They do not turn
mentions or graph reachability into legal applicability.

The runtime receives the research question, never the evaluation's target IDs.
It resolves concepts, applies compound-word and ambiguity guards, follows scoped
directed dependencies and checks each requirement from its own active root.
An unrelated route cannot satisfy another requirement. The graph, resolver,
runtime and client are hash-bound. Missing paths and sources remain explicit;
hard work, byte and deadline ceilings cannot be raised by caller input.

`plan_okf_evidence` returns a bounded catalogue and diagnostics;
`read_okf_planned_evidence` supplies contiguous verified parts. The collector
checks every continuation identity, the complete package hash and each source
record's text hash before reporting complete delivery. The prepared service
exposes these two tools at `/mcp`; the historical three-tool connection is
separate at `/okf/mcp`. Deployment and actual host invocation require their own
receipts.

The [diagnosis and strategy comparison](../evaluation/truncation/README.md)
explain why a larger package alone misses the required source. The candidate
preserves that baseline, optionally assembles a separate compound-alias
projection and makes at most three source-supported navigation queries. These
are unreviewed research proposals. Each result keeps its own source identity,
query, passages and omissions; they are never merged into a sufficient answer.

## Run the inspector

Use Node 26.7.0 and the separately pinned Explorer checkout
`40e659408485a7dfa0e8cb51ab27c1b0f890bc3c`. No installation or model key is
needed for this Node workflow. For repository Python checks, use
`uv sync --locked` and `uv run --locked python`; do not upgrade dependencies.

```sh
node scripts/run_context_review.mjs --explorer-root /path/to/okf-explorer
node scripts/run_context_review.mjs --explorer-root /path/to/okf-explorer --check
```

Open `evaluation/truncation/review/index.html` in Chrome or Edge. Compare the
graph-guided plan, baseline and each recovery context, search for a passage, inspect its official
PDF reference and read the retained diagnostics. The HTML is generated: change
the producer and regenerate it rather than editing it. The report runs offline
with no external scripts or network requests. Following an explicit source link
opens that reference separately.

For a different general research question, use a separate output directory:

```sh
node scripts/run_context_review.mjs --explorer-root /path/to/okf-explorer \
  --question 'Which public guidance discusses Pension Credit abroad?' \
  --output-dir /tmp/okf-dwp-abroad-review
```

Use public research questions only. Do not enter names, claim details or other
personal claimant data. A question that activates no recovery route still
produces a baseline report. The bounded policy is designed around observed
question dimensions; it is not a general legal reasoner.

## Delivery and report contract

The runner calls the graph runtime and pinned legacy engine through local
manifest/read adapters. It
does not call the deployed MCP service. The progressive client collects every
catalogue page and contiguous UTF-16 package slice, then checks the complete
context digest, record text hashes, source selection and diagnostics. Resource
and deadline limits have immutable ceilings. An individual JSON value and a
duplicated MCP envelope have different sizes; local response measurements do
not establish the host's clipping threshold.

`report.json` uses `okf-dwp-context-review.v1`. Its root records `question`,
`status`, implementation and source `identity`, `recovery_plan`, `contexts` and
`limitations`. Each context records:

- `id`, `label`, `query` and `context_id`, preserving its independent identity;
- `evidence_status`, `assembly_truncated`, `retrieval_truncated`,
  `selected_records`, `relationships` and `package_bytes` from the engine;
- `delivery_complete`, `package_complete`, `package_sha256`, `delivery` and
  `receipt` from successful progressive collection;
- exact `records` with authority, review status, provenance, selection reasons
  and paths, plus complete retained `diagnostics`.

The per-context JSON collections retain the original selection wrappers,
relationships, catalogue and delivery receipts. The report binds the policy,
runner, recovery adapter, progressive client, renderer and engine bytes.
`--check` recomputes expected artefacts and compares their bytes without
rewriting them. Completion flags are derived from verified collection, never
from the presence of a receipt. The HTML is an inspector for this trusted local
output; it is not a verifier for arbitrary third-party reports.

Builds require a fresh or empty output directory and preserve earlier reports.
Use a new `--output-dir` when implementation inputs change; keep the preceding
result as historical evidence. `--check` also rejects unexpected files and
symlinks in the declared output tree.

Complete delivery means that the selected package arrived intact. It does not
mean that retrieval selected every required source or that a passage applies.
All candidate contexts retain `insufficient` and `ai_answer: null`. All 40
original staff tasks and 203 unmet obligations retain their historical status.

## Why evidence remains insufficient

The inspector groups reasons while preserving every original code, message,
record and requirement identifier. Missing evidence in the working index does
not by itself establish that the source is absent from the acquired corpus.

| Category | Lack or uncertainty recorded |
| --- | --- |
| Source coverage | Required passage or dependency has not been established in the declared evidence set. |
| Retrieval | An available record was not selected or a bounded search was incomplete. |
| Graph connections | A required directed dependency or supported source route is missing. |
| Question scope | Benefit, period, jurisdiction or other research dimensions are unclear. |
| Legal applicability and version | Relevant law, territorial scope, commencement, amendments or case law are unresolved. |
| Source interpretation | Extraction, passage boundaries, references or authored meanings need verification. |
| Specialist review | No qualified human has accepted the interpretation and dependencies. |
| Assembly and delivery | A selected item was omitted, clipped or not reconstructed intact. |
| Access | A source could not be accessed under the applicable boundary. |

The preserved 203 obligations comprise 43 evidence-closure gaps and 40 each for
applicability, legal version, specialist review and question scope. Successful
source retrieval does not silently close them. The statutory catalogue crosswalk
is a separate source-identity aid; metadata alone supplies no provision body,
current-law assurance or case law.

## Repeat the evaluation

The [statutory crosswalk](../evaluation/retrieval-gate/legislation-crosswalk.json)
matches 20 work identities and inventories 53 provision targets: 13 existing DWP
text projections, 38 metadata-only observations and two targets with only work
metadata. It binds the July catalogue snapshot at legislation commit
`9830fde2d32052f10713298f16b8ab1e321b1928` and unchanged DWP input blobs at
baseline `77ef16047415ee48dcb93b80adf1ba057ea00d9b`. All case-law bodies remain
excluded; existing case-law mentions and unresolved citation notes are retained.
There are no new source acquisitions or closed obligations. Selected work
identity and catalogue version metadata reduce uncertainty without establishing
provision completeness, commencement, extent or temporal applicability.

For crosswalk checks, use a separate read-only legislation checkout at that
exact commit. CI checks out only its bound catalogue and fetches the DWP input
baseline. The check does not use a moving branch or treat a catalogue work as
a provision body:

```sh
uv run --locked python scripts/build_legislation_crosswalk.py \
  --legislation-root /path/to/okf-uk-legislation --check
uv run --locked python scripts/test_legislation_crosswalk.py \
  --legislation-root /path/to/okf-uk-legislation
```

```sh
OKF_EXPLORER_ROOT=/path/to/okf-explorer node --test \
  scripts/test_context_recovery.mjs scripts/test_progressive_evidence_client.mjs \
  scripts/test_context_review_html.mjs scripts/test_run_context_review.mjs \
  scripts/test_current_explorer_compatibility.mjs
node scripts/check_current_explorer_compatibility.mjs --explorer-root /path/to/okf-explorer
node scripts/evaluate_context_strategies.mjs --explorer-root /path/to/okf-explorer \
  --output evaluation/truncation/strategy-results.json --check
node scripts/evaluate_context_recovery.mjs --explorer-root /path/to/okf-explorer \
  --output evaluation/truncation/recovery-results.json --check
uv run --locked python scripts/build_evidence_route_graph.py --check
uv run --locked python scripts/build_persona_evaluation.py --check
uv run --locked python -m unittest discover -s scripts -p test_evidence_route_graph.py
uv run --locked python -m unittest discover -s scripts -p test_persona_evaluation.py
OKF_EXPLORER_ROOT=/path/to/okf-explorer node --test \
  scripts/test_graph_evidence_runtime.mjs scripts/test_graph_evidence_client.mjs \
  scripts/test_insufficiency_categories.mjs
node scripts/evaluate_graph_retrieval.mjs --explorer-root /path/to/okf-explorer \
  --output evaluation/retrieval-gate/graph-evaluation.json --check
node scripts/replay_frozen_wording.mjs --explorer-root /path/to/okf-explorer
OKF_EXPLORER_ROOT=/path/to/okf-explorer node evaluation/retrieval-gate/withheld/attempt-02/run.mjs
git diff --exit-code -- evaluation/retrieval-gate/withheld/attempt-02/receipt.json \
  evaluation/retrieval-gate/withheld/attempt-02/run-summary.json
```

The strategy matrix covers 17 known development cases. The recovery comparison
covers eight known positive and negative cases; it also checks recovery-plan
inactivity for all 40 original staff questions. That plan check is not a fresh
40-case runtime replay or independent answer-quality evaluation. The additive
`current_explorer_validation` CI job runs these checks alongside the three
historical prerequisite jobs. The protected aggregate remains `validate`.

## Publication and remaining limits

The [local browser observation](../evaluation/retrieval-gate/browser/observation.json)
binds the generated report and HTML. Installed Chrome 157.0.8103.51 and Edge
157.0.4341.46 passed five-context selection, exact F1120 search, source expansion,
keyboard radio navigation, empty search state and 390-pixel layout checks with
no console warnings or errors. Retained screenshots show desktop and mobile
layouts. These headless observations do not certify comprehensive accessibility,
a public deployment or the intended connected client.

The existing tag `demo-2026-09-30-reading-help-v2` already identifies baseline
`77ef16047415ee48dcb93b80adf1ba057ea00d9b`. It has not been moved or duplicated.
The [publication review](review-2026-11-14-publication.md) records the baseline
findings and preserved source boundaries.

The [selected service observation](service-publication.md) retains its exact
source and engine bindings. Local 0.8.0 preparation does not itself establish
public deployment or host compatibility. Wider unseen subject coverage,
benefits-specialist review, current legal applicability and answer accuracy
remain separate acceptance tasks. No new source capture or model answer call
is required by this workflow.
