# Truncation diagnosis and strategy experiments

Independent experimental evidence, 14 November 2026. No entitlement decision,
award calculation, paid model call or source acquisition is made here.

The reported problem has four distinct mechanisms. A small delivery cannot
recover a rule that retrieval never selected. A large context cannot repair a
misrouted question. The diagnostics must retain these distinctions.

| Layer | Reproduced mechanism | Evidence |
| --- | --- | --- |
| Question routing | The alias `rate` in `highest-rate` resolves to the broad Dated benefit rates concept. Its single-concept trigger activates the unrelated `staff-008` SDA/rates task and associated Pension Credit tables. Broad benefit concepts also expand unrelated branches. | The unchanged original question activates `staff-008`; removing only `rate` in an explicitly derived, in-memory experiment reduces the package from 522,141 to 263,030 bytes, but still misses A4361. |
| Retrieval | Ranking plans 16 source units, but graph expansion follows the first ranked unit and resolved concepts before admitting the other ranked units. The fixed 64-file cap is spent on search, records, discovery and adjacency shards. | The original question has 24,158 ranking matches but only four admitted candidates. It reaches 64 files and records 43 resource omissions, although transfer and decoded bytes remain below their separate caps. |
| Context assembly | Whole assertions and records are omitted to fit 524,288 bytes. Below that, extensive question interpretation and omission metadata can itself exceed the package budget. | At 128 KiB the original yields eight records; at 32 KiB it fails closed with zero records and a metadata diagnostic. No source passage is cut mid-text. |
| Delivery | The full-package tool returns the context as both a text block and structured content. Delivery limits are separate from selection and retrieval limits. | A live original-question call returns a 522,215-byte package in a 1,071,946-byte connector result. The compact catalogue and source-slice APIs avoid sending the whole package at once. The host's precise truncation threshold has not been measured. |

The frozen original-case replay remains unchanged. Its source manifest is
`4e65253f72b2d771164d5ddd64374ed8142cf66b4a249f193a1fe44d5679f519`.
The current Explorer checkout at `40e659408485a7dfa0e8cb51ab27c1b0f890bc3c`
still matches all four engine hashes retained by that replay. The live service
uses source revision `7eeded763042ddd0070f4fed834c6074149e8e2f` and explicitly
reports its separate engine identity in [live-observation.json](live-observation.json).

## Strategy comparison

These are development experiments against known failures, not a blind legal or
answer-quality evaluation. All retain `evidence_status: insufficient` and
`ai_answer: null`. All use the same source manifest and consumer hashes.

| Strategy | Records | Context bytes | F1123 | A4361 | Interpretation |
| --- | ---: | ---: | --- | --- | --- |
| Original question | 38 | 522,141 | Yes | No | Baseline reproduces exactly. |
| Reduce assembly to 32 KiB | 0 | 6,892 | No | No | Metadata fallback; evidence lost. |
| Reduce assembly to 128 KiB | 8 | 121,180 | Yes | No | Smaller package does not repair discovery. |
| Limit graph to one hop | 26 | 431,056 | Yes | No | More candidate slots survive, still no missing rule. |
| No graph hops | 19 | 199,399 | Yes | No | All 16 lexical candidates admitted, still no missing rule. |
| Remove generic `rate` alias, derived counterfactual only | 28 | 263,030 | Yes | No | Materially less irrelevant fan-out; incomplete fix. |
| Ordinary-language timing subquery | 36 | 306,017 | No | No | Splitting dimensions without a semantic bridge fails. |
| Expert query containing `A4361` | 41 | 327,413 | Yes | Yes | Positive control proves corpus presence; user expertise still required. |
| Ordinary-language paraphrase | 40 | 321,585 | Yes | No | Confirms the discovery gap beyond the original wording. |
| `UC and award of other benefits` | 34 | 241,867 | No | Yes | Short source-heading bridge finds the missing rule without a paragraph locator. |
| Heading plus timing vocabulary | 33 | 237,832 | No | Yes | A bounded, source-bound recovery direction; applicability remains unresolved. |

Longer plausible specialist subqueries can also fail. For example, `Universal
Credit relevant benefit supersession DLA child addition` admits all 16 lexical
candidates but misses A4361. The working short heading is evidence for bounded,
inspectable source-heading navigation, not permission to invent terminology or
silently inject an answer target.

The recommended implementation combines lossless progressive delivery with a
separate, source-bound recovery candidate. Preserve the original package and
its diagnostics; keep every recovery query, derived input hash, source identity
and resulting context separate. Recovery selection must not upgrade legal
applicability, specialist review or answerability. A qualification-only DLA
question is a negative control for the timing branch.

## Additive recovery candidate

The separate local candidate in `scripts/context_recovery.mjs` now implements
that bounded source-heading strategy. Its authored policy binds exact source
text and PDF identities. It preserves the original context, optionally builds
an explicitly derived compound-alias projection, and runs at most three
independent source-supported follow-up queries. It does not modify or deploy
the public service.

| Development case | Baseline target selection | Selection across separate recovery contexts |
| --- | --- | --- |
| Original natural-language question | F1123 | F1123, F1120–F1121, A4361 |
| DLA increased retrospectively, UC told later | F1123, F1120–F1121 | F1123, F1120–F1121, A4352, A4361 |
| Child DLA backdated; higher UC child element | F1123, F1120–F1121 | F1123, F1120–F1121, A4361 |
| Highest-rate award reported a year late | F1123, F1120–F1121 | F1123, F1120–F1121, A4352, A4361 |

All eight positive/negative cases pass. The four qualification-only, rates,
hospital and age-transition controls trigger no timing recovery. All forty
original staff questions have zero follow-up activations and zero compound
alias changes. This is a plan non-regression check; their earlier acceptance
receipts are not relabelled or overwritten. Every individual context and the
recovery envelope remain insufficient with no AI answer. Combined target
selection is a navigation set comparison, not a merged legal evidence package.

The original plus paraphrases are known development cases. Independent future
wording, specialist review of the navigation policy, and live model answer
quality remain outside this deterministic result. See
[recovery-cases.json](recovery-cases.json) and
[recovery-results.json](recovery-results.json) for the bound protocol and
complete measurements, including the total bytes across separate contexts.

## Reproduce

```sh
node scripts/replay_uc_supersession_case.mjs --explorer-root /path/to/pinned-okf-explorer
node scripts/evaluate_context_strategies.mjs --explorer-root /path/to/pinned-okf-explorer --output /tmp/strategy-results.json
node scripts/evaluate_context_recovery.mjs --explorer-root /path/to/pinned-okf-explorer --output /tmp/recovery-results.json
```

The second command verifies the pinned engine and manifest, uses only manifest
allowlisted, length- and hash-checked local bytes, runs all 17 fixed cases, and
asserts the recorded target observations and unchanged baseline identity.
It never fetches a network resource or modifies a frozen corpus file. The
generic-alias ablation is labelled counterfactual and binds the exact derived
base-index hash. [strategy-cases.json](strategy-cases.json) is the fixed protocol;
[strategy-results.json](strategy-results.json) retains the full matrix.

## Code evidence

- `domain-profile/staff-semantic/concepts.yamlld:855` declares Dated benefit rates; line 866 declares `rate`.
- `domain-profile/staff-semantic/profiles.yamlld:342` declares `staff-008` and its trigger.
- Explorer `src/lib/context/corpus.ts:18` fixes 24 query tokens, 16 candidates and 64 files independently of context bytes.
- Explorer `src/lib/context/corpusV3.ts:279` enforces file, transfer and decoded resource limits; lines 579–587 fix admission and graph-expansion order.
- Explorer `src/lib/context/index.ts:665` removes whole items under byte pressure; lines 696–709 fail closed when metadata itself does not fit.
- Explorer `src/lib/context/delivery.ts:48` paginates record summaries; line 96 begins exact, hash-bound evidence slicing with Unicode boundary protection.
- Explorer `services/ask-okf-mcp/src/service.ts:139` emits duplicate package representations; lines 147–174 bind the compact manifest, replay identity and response limit.

Exact live and offline context identities differ because the live binding uses
the immutable GitHub URL while the offline replay deliberately uses
`example.invalid`. Their bytes and identities must not be relabelled as equal.
The live connector result measurement is neither HTTP transfer size nor proof
of the host's model context limit. This investigation establishes reproducible
payload pressure and explicit retrieval omissions, not a universal claim that
all reported truncation has one cause.
