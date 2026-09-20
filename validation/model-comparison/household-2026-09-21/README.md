# Monday trial outputs: five attempts retained, further calls held

The six evidence packages have been frozen and replayed offline. Authorised subscription calls have begun under the unchanged frozen protocol. See the [frozen catalogue](../../../evaluation/model-comparison/household-2026-09-21/frozen/manifest.json) and [pre-model input review](../../../evaluation/model-comparison/household-2026-09-21/pre-model-input-review.json).

The [results ledger](results.json) has been generated and verified offline against every retained attempt and its exact frozen inputs. Outcomes:

- Codex Staff 012 and the unknown-term control both returned an unrecognised `item:error` event. Both attempts were rejected with an unknown event census; no `answer.json` was accepted. The error body was not retained, so the cause is unknown. Remaining Codex cases are on hold after the small control reproduced the same event category.
- Claude Staff 012 and Staff 020 exceeded the frozen 240-second limit. Their incomplete censuses are unknown; no answer was accepted.
- Claude's unknown-term control completed in 28.10 seconds. It reported `claude-opus-5` as both response and accounting identity, but its stream contained unrecognised `thinking_tokens`, `rate_limit_event` and `tool_result` categories alongside `StructuredOutput`. The frozen controls rejected it. The categories alone do not establish external evidence use. Remaining Claude cases are held for investigation; no parser relaxation, timeout change or retry has occurred.

Rejected provider-result text can appear inside sanitised `model-output.json`. Its presence is not acceptance and must not be counted as a completed pair. There are zero completed pairs and no accepted `answer.json` files. These outcomes establish neither model accuracy nor a preference between providers.

Future attempts will retain their exact input hashes, authentication-method observation, sanitised model identities, tool census, numerical usage and timings, final structured answer and mechanical citation checks. Every failure and retry gets a separate directory. Independent human and specialist review remain pending.

The [protocol](../../../evaluation/model-comparison/household-2026-09-21/protocol.json) and [guide](../../../docs/monday-model-trials.md) explain the scope and reproduction procedure. Original trials in `staff-2026-09-20/` remain unchanged.
