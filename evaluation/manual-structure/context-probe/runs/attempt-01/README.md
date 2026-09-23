# First structured-context comparison: acceptance failed

This is a retained development observation. It is not an answer-quality trial.

The same forty staff question occurrences, frozen source inventories, authored concepts and requirements were checked at both budgets. The single unknown-term control was evaluated separately. No model or network calls occurred.

| Corpus | Budget | Questions with zero evidence | Median evidence units | Retained authored paths |
| --- | --- | ---: | ---: | ---: |
| logical-context | 32 KiB | 34/40 | 0 | 0/47 |
| logical-context | 512 KiB | 0/40 | 13.5 | 47/47 |
| structured-context | 32 KiB | 40/40 | 0 | 0/47 |
| structured-context | 512 KiB | 0/40 | 33.5 | 40/47 |

Every result remained insufficient. More selected units do not establish greater relevance or a better answer. The candidate is not accepted for default adoption.

## Failures and next action

- Full card diagnostics consume too much of the package. At 512 KiB their median serialised size is 51,339 bytes; at 32 KiB the engine returns an explicit bounded refusal without selected evidence.
- The larger incident-reference graph and eager lexical hydration reach a retrieval resource limit before all naturally reachable authored paths are loaded. Staff 023 and 033 lose seven previously retained path occurrences in total.
- Correct the reusable adapter: return compact bound discovery identities and scores, leave full card details accessible by their immutable reference, and prioritise actual resolved-concept traversal without using requirements as hidden retrieval seeds.
- Preserve this run. Repeat the same comparison after the independently reviewed correction; do not tune BM25 parameters or remove failed questions.

## Interpretation limits

These are known development cases, including duplicates. Timing is a local sequential cached-order observation with mixed cold and warm reads; it is not a controlled speed benchmark or remote latency. Structural and global integrity checks passed separately. They do not erase this delivery failure.

The JSON report records exact source, engine and input identities. All 164 context packages, the runner, progress and timings are retained beside this note.

## Frozen reproduction location

Both source manifests and their generated shard bytes are retained at DWP commit `9736d30c`. The engine is the immutable Explorer commit recorded in `report.json`; the exact runner is retained alongside the packages. Later producer revisions must not replace this trial or regrade its outcome.
