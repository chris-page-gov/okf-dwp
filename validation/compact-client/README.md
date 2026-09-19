# Actual Claude compact-tool observation

This is a **local client check on 19 September 2026**, separate from both the
[fixed-package answer trials](../../evaluation/answer-review/README.md) and any
public-service acceptance. It does not establish current benefit rules or
specialist answer quality.

## What was observed

The first attempt used Claude Code safe mode, which disables MCP servers. The
proxy captured **zero HTTP requests**, but the model narrated a manifest call and
emitted an invented catalogue, context ID and evidence status. The
[failed observation](claude-local-2026-09-19/observation.json) and its model output
are preserved. They are not service evidence.

The explicit-MCP retry retained the identical public question and prompt. It
used an empty temporary working directory, no built-in tools, strict explicit
MCP configuration, disabled optional hooks/memory/skills/plugins, no session
persistence and no model override. Only `ask_okf_manifest` and
`read_okf_evidence` were permitted. It made **seven real tool calls**:

1. One catalogue for “What happens to your benefits if you go abroad?”, with a
   32,768-byte context budget.
2. Two contiguous diagnostics slices.
3. Exact text and provenance/inclusion metadata for each of two source records.

All seven returns retained context
`urn:sha256:2cdfa5feb6310f58166d66e814bd3b2fbe2e9e146e25b25a65453b48e3dffabd`.
The [offline verification](verification.json) compares every captured source
value with the retained whole context, checks exact hashes and UTF-16 offsets,
and reconstructs all five requested values. It verifies structured/text parity,
byte limits, source identity, missing evidence and truncation. The question
remains **insufficient**; only two of the six selected source records were read.

The retry captured 13 HTTP exchanges in total. Four `subscriptions/listen`
probes received the service's unsupported-method response; catalogue and read
calls still succeeded. Discovery and tool listing account for the other two.
The [observation](claude-local-explicit-mcp-2026-09-19/observation.json) lists all
actual request and response files and their hashes. No account or credential
metadata is retained.

## Model and deployment boundaries

The retry's output acknowledged the two-record limit, insufficiency and
truncation. Its claims and quotations still require independent human review;
transport fidelity does not establish legal entailment, complete exceptions or
verbatim quotation by the model. Its review URL uses the service's public origin,
but this local observation does not prove that the public review route was
already deployed.

The CLI reported usage entries for `claude-haiku-4-5-20251001` and
`claude-sonnet-5` in the successful local call; the safe-mode failure reported
Haiku and `claude-opus-5`. No model was selected explicitly. The configuration
change and differing reported models mean this is **not a fair model comparison**.
Provider cost fields do not establish a subscription charge or saving.

## Recheck without model or network calls

```sh
uv run --locked python scripts/check_compact_client.py
uv run --locked python scripts/test_compact_client.py
```

The five regression controls verify the retained observation and reject altered
source slices, upgraded status, forged delivery sizes and erased no-call failure.
