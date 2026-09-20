# Lossless context and CLI compatibility candidate

**Reviewed, frozen and executed: nine attempts are retained.** Both unknown-term controls passed. Codex returned five substantive parser-accepted answers; four pass mechanical checks and Staff 008 fails a source-locator check. Claude Staff 012 was rejected for formatter-result recognition and Staff 020 timed out; its remaining three cases are held. The [claim-level model critique](../../../validation/model-comparison/household-compact-v2/claim-level-model-critique.json) identifies scope and attribution concerns separately from those mechanical results. No substantive pair or comparative accuracy result is established.

This separate experiment preserves the [original five failed or rejected attempts](../../../validation/model-comparison/household-2026-09-21/results.json). It does not relabel those attempts as successful. The [frozen manifest](frozen-manifest.json) binds reviewed commit `78a8beea97242d646eb9159860dea190ca5e2998` and has SHA-256 `faefc7f42282c2f8dfdee119ff6d30f26b537b73b43b1b9ed133c3befbef4678`. Offline verification passes for all six cases. See the [retained successor outcomes and stopping decision](../../../validation/model-comparison/household-compact-v2/README.md); no further calls are authorised by this guide.

## What changes

The [protocol](protocol.json) uses the same six original governed contexts and the same four-minute execution bound. A **lossless projection** means a representation that can reconstruct the original bytes exactly. Here, repeated JSON values move to a dictionary and are replaced with explicit IDs. The trusted system prompt explains how to read those IDs; evidence text never supplies executable instructions.

Every selected record, literal quotation, status, scope, provenance item, relationship, requirement, gap, ambiguity and budget declaration reconstructs byte for byte. Each [packet](candidate-manifest.json) binds its original audit file, SHA-256 fingerprint and catalogue. These are existing repository-relative audit links. A public immutable URL is not claimed before this candidate is published.

The [byte census](byte-census.json) measures every original top-level field. Those values plus JSON key/punctuation overhead sum to the full package size. Nested text measurements overlap the selected-record total and must not be added again. Reduction includes the dictionary and audit envelope:

| Case | Original bytes | Candidate bytes | Reduction |
| --- | ---: | ---: | ---: |
| Staff 012 | 257,861 | 219,370 | 14.9% |
| Staff 020 | 258,130 | 226,085 | 12.4% |
| Staff 005 | 261,474 | 224,519 | 14.1% |
| Staff 026 | 261,532 | 230,715 | 11.8% |
| Staff 008 | 252,429 | 217,127 | 14.0% |
| Unknown-term control | 5,141 | 6,057 | **916 bytes larger** |

This modest reduction has not been shown to improve model readability, latency or accuracy, or to prevent timeouts. No information is silently removed to obtain it. The earlier two projection-metadata files are retained under `history/projection-review-01/`; a path and byte-limit guard changed the producer identity, while all six packet bytes stayed unchanged.

## Event recognition

A **CLI event** describes something the command-line client did. The first experiment rejected events it did not recognise. Separate synthetic diagnostics established the shapes below; historical payloads that were discarded remain unknown.

- Codex's exact observed skill-description-shortening warning can be retained as a warning. No other error text is accepted or published. It confirms that host or system skill catalogue material remains visible despite disabling discovered user skill paths. Whole provider system contexts are therefore not identical.
- Claude thinking-token counters and rate-limit events must match the exact observed field/type structures. Their values are not treated as evidence or instructions.
- A Claude `StructuredOutput` formatting call must have a unique ID and exactly one later matching, non-error result. An absent `is_error` flag is recorded as absent; a present flag must be boolean false. The final structured output must match a successful formatter input. Unknown tools, duplicate/reused IDs, missing results and mismatches fail closed.
- Both providers require exactly one terminal completion at the end of the stream. Unknown events and incomplete streams remain rejected. Initialisation payloads are discarded; this is not a claim that every initialisation field was schema-validated.

The [OpenAI JSONL documentation](https://learn.chatgpt.com/docs/non-interactive-mode#make-output-machine-readable) describes the event stream and completion events. Anthropic documents unique tool-use IDs and the optional error flag in its [tool-result contract](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls). Specific CLI telemetry schemas here come from the separately recorded local diagnostics, not a claim that the platform API defines every CLI wrapper.

The one-off diagnostic script was found to preserve an opaque tool identifier as a dynamic map key. The original observation is held outside the public repository. Its [public privacy projection](../../../validation/model-comparison/household-2026-09-21/diagnostics/claude-synthetic-reasoning/receipt.json) hashes dynamic keys, records the original digest and explicitly declares the transformation. The original two diagnostics are observations only: their generic redactor is not an acceptance parser or a guarantee against every possible secret string. Their current reviewed public receipts contain no observed private values.

## Review and execution gates

Independent review and a new exact committed candidate are required before freezing. The successor binds its full imported-helper chain, prompts, schema, packets and original contexts. It makes no paid API call, model override or persistent settings change. Subscription authentication is checked afresh.

After root approval, begin with the small unknown-term control for each provider. Only after accepted event formats should Staff 012 be attempted under the same 240-second limit. Further substantive calls require a decision based on those observations. There is no automatic retry or claim that a mechanical pass proves legal correctness.

Offline commands:

```sh
uv run --locked python scripts/project_monday_model_contexts.py
uv run --locked python scripts/run_monday_compact_trials.py
uv run --locked python -m unittest discover -s scripts -p 'test_monday_*v2.py'
uv run --locked python -m unittest discover -s scripts -p test_monday_model_projection.py
uv run --locked python -m unittest discover -s scripts -p test_monday_compact_trials.py
```

After review and an exact commit supplied by the root task:

```sh
uv run --locked python scripts/run_monday_compact_trials.py --freeze --source-commit REVIEWED_COMMIT
uv run --locked python scripts/run_monday_compact_trials.py
```

A real call additionally requires `--run`, one `--provider`, one `--case`, an unused `--attempt attempt-NN` and the exact `--manifest-sha256`. Do not run it merely because freezing passed. `--report` and `--check-report` verify the retained outcomes; a changed results ledger must be preserved before replacement.
