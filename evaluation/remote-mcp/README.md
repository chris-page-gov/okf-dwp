# Remote MCP acceptance

These evaluations check whether a remote `ask_okf` call preserves the governed evidence package produced by Explorer's existing context assembler. They do not grade conversational prose or claim current legal accuracy.

## Cases

- **Imprisonment:** reuses the [existing A–H case](../context-assembly/imprisonment-case.json). Required source identities, exact passages, directed relationships, traversal paths, declared requirements and authority boundaries are assessed. Keyword overlap is not a pass condition.
- **Hospital admission:** the [hospital case](hospital-case.json) must expose insufficient context for the approved snapshot. It checks missing evidence, unresolved terms, zero applicable requirements and no budget truncation. Selected custody passages must not be mistaken for a hospital answer.

The [hospital source review](hospital-source-review.json) identifies relevant frozen material outside the Ask index. Ten PDF identities and 52 complete page literals were reverified on 19 September 2026. It is a bounded research inventory, not an approved hospital profile. Read the [coverage explanation](../../docs/remote-mcp-hospital-coverage.md) before interpreting these results.

## Run real MCP calls

The public test endpoint below has a [retained HTTPS acceptance receipt](../../validation/remote-mcp/receipt.json). Its protocol-client results and actual ChatGPT observations remain distinct in the [demonstration guide](../../docs/remote-mcp-demo.md):

```sh
node --experimental-strip-types scripts/test_remote_mcp.mjs \
  --endpoint https://ask-okf.crpage.chatgpt.site/okf/mcp \
  --explorer-root ../okf-explorer
```

For local development, use `--endpoint http://127.0.0.1:8787/mcp` and a separate output directory, for example `--output /tmp/okf-dwp-mcp-local`. HTTP is accepted only for loopback hosts. Redirects, embedded credentials, query strings and fragments are rejected. Endpoint selection is a test-client option; the service's bundle selection remains an immutable allow-list.

The independent raw HTTP client:

1. initialises MCP protocol `2025-11-25`, then sends `notifications/initialized`;
2. discovers `ask_okf` and checks its read-only annotations and bounded input schema;
3. makes one `tools/call` per exact question, using bundle `okf-dwp` and version `efb05c66616a9cd4328a86cf412780fe7bc7cf0b`;
4. requires structured content and the JSON text block to contain the same existing context package;
5. assembles locally through the unchanged Explorer core, with identical question, budget and immutable index binding;
6. compares canonical package bytes and runs the evidence/path/provenance assessment;
7. records the real transport observations and raw tool results.

The case expectations never become engine inputs. The response size and request time are bounded. No model call, web search or source refresh is part of this procedure.

## Retained evidence

The default output is `validation/remote-mcp/`:

| File | Meaning |
| --- | --- |
| `receipt.json` | Dated observation: exact endpoint, local/HTTPS scope, negotiated protocol, client/server identities, core/index/client hashes, package identities, assessments and call durations |
| `tools.json` | Discovered tool descriptions, schemas and annotations; these are untrusted service data |
| `imprisonment-tool-result.json.gz` | Complete decoded MCP tool result, including the structured evidence package and matching JSON text |
| `hospital-tool-result.json.gz` | Complete decoded MCP tool result reporting the hospital evidence gap |
| `sdk-receipt.json` | Separate official SDK HTTPS-client verification under MCP `2026-07-28`, with exact runtime input and build assurance |
| `deployment.json` | Hosting release identifiers, code and approved source identities, and acceptance-receipt hashes |
| `public-explorer-observation.json` | Displayed context identity/counts observed in the live Explorer UI; separate from raw package verification |
| `chatgpt-observation.json` | Actual Pro-account connection and model-access observations, including host truncation and the successful bounded hospital gap response |
| `bounded/receipt.json` and `bounded/budget-*/` | Six complete HTTPS input/package/response captures at explicit 32,768-, 85,000- and 98,304-byte budgets, with hashes and unchanged-core parity |

Raw HTTP envelope digests are recorded separately from decoded tool-result and canonical package digests. A context identifier binds the evidence package, not network duration or observation time. Compression is checked against its retained archive hash and the decompressed bytes; replay does not assume that different operating systems produce identical gzip streams.

The receipt preserves source version, scope, provenance, missing evidence and truncation information. A loopback result is labelled `local-loopback-mcp`; it cannot establish remote HTTPS access. A successful protocol client call does not establish ChatGPT, another AI client or Voice invocation. Their separate observations must identify the client surface and actual tool use.

## Replay without contacting the endpoint

```sh
node --experimental-strip-types scripts/test_remote_mcp.mjs \
  --check --explorer-root ../okf-explorer
```

Replay rechecks the retained archive, raw result, case, source-index and implementation hashes; reruns the unchanged core; compares the complete packages; and reassesses evidence requirements. It does not rerun the network request and cannot show current endpoint availability. Use the real-call command for that purpose.

Changing the engine, rubric, client, source index or approved version requires new evidence. Do not edit receipts to make stale results pass. Ordinary CI uses offline replay, so it does not depend on public endpoint uptime.

## Bounded client demonstrations

Actual ChatGPT invocation exposed a separate host limit: the complete default imprisonment result was returned by the service but truncated for the model. The service's `budget.truncated: false` does not describe downstream host behaviour. The tested 32,768-byte hospital request instead deliberately returns an insufficient package with 8 authored concepts, no relationships and `budget.truncated: true`; the model reported access to that bounded result and declined a hospital answer.

The [bounded receipt](../../validation/remote-mcp/bounded/receipt.json) preserves both questions at three explicit budgets. All six HTTPS packages match the unchanged core. They remain insufficient and deliberately truncated; increasing the budget does not introduce missing hospital knowledge. No service default or adapter summary was substituted.

Replay all six without contacting the endpoint:

```sh
node --experimental-strip-types scripts/check_bounded_remote_mcp.mjs \
  --explorer-root ../okf-explorer
```

These are bounded transport and boundary tests, not passes of the full imprisonment sufficiency rubric. A larger byte budget does not currently guarantee that the package retains more useful evidence: an additional local 131,072-byte imprisonment probe returned a `metadata_budget` failure. The receipt records that engine limitation; this adapter change does not fix it. Use the exact rehearsed question and budget and inspect the returned status rather than assuming a monotonic improvement.
