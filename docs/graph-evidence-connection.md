# Read graph-guided evidence in small parts

[Recorded graph publication and client checks](graph-service-publication.md) ·
[Persona coverage and evidence limits](persona-coverage-and-evidence-limits-2026-11-14.md) ·
[Offline inspector](context-review.md)

This is an independent experiment, not an official DWP service. It retrieves
source evidence and unresolved dependencies. It does not decide entitlement,
calculate an award or ask for claimant personal data.

## Check the connection's actual tools

The graph release is designed to use
`https://ask-okf.crpage.chatgpt.site/mcp` with two tools. Check the
[recorded status](graph-service-publication.md) for a matching deployment before
using this route:

| Tool | Purpose |
| --- | --- |
| `plan_okf_evidence` | Return a small catalogue of the selected source plan and its identities. Follow the catalogue's continuation offsets. |
| `read_okf_planned_evidence` | Read contiguous parts of that plan, including source text, metadata, relationships, diagnostics or the complete package. |

The [recorded status](graph-service-publication.md) distinguishes deployment,
public SDK checks and actual native client observations. A public service URL
does not establish that this conversation has its tools. Check the two names
above before starting. If the conversation only exposes `ask_okf`,
`ask_okf_manifest` and `read_okf_evidence`, it has the separate historical
connection at `/okf/mcp`.

Sites provides its own connection for a published MCP-enabled Site. Use that
connection when it is available in the intended account. For an existing custom
MCP connection, OpenAI's [connection and testing guidance](https://developers.openai.com/plugins/deploy/connect-chatgpt#refresh-metadata)
describes refreshing changed metadata and testing in a new conversation.
Account and workspace policies still apply. Record unavailable tools as a
client-access gap; do not treat an SDK result as a successful native call.

Direct public SDK checks use `/graph/mcp`. That alias serves the same two-tool
handler, but its transport observation has a different scope from the Sites
connection. The original `/okf/mcp` interface retains historical replay.

## A source-retrieval starter

Use this as a general source-research example.

```text
Use only the graph evidence tools available in this conversation. If
plan_okf_evidence or read_okf_planned_evidence is unavailable, report that
limitation and stop.

Find the captured DWP guidance relevant to this research question:
"Which captured DWP guidance passages and cross-references are relevant to
the timing of a higher disabled-child addition in Universal Credit after a
highest-rate DLA care-component award is reported late? Identify the temporal
conditions and unresolved dependencies that a qualified reviewer would need
to check."

Call plan_okf_evidence with bundle "okf-dwp" and delivery_bytes 8192.
Preserve the exact question and returned graph_sha256, engine_id and plan_id
on every continuation. Follow delivery.next_offset until it is null.

Use read_okf_planned_evidence with delivery_bytes 8192 to read the relevant
record_text, record_metadata and diagnostics. Use only record_id values from
the returned catalogue. Follow each next_offset until null. To reconstruct
the complete package, read section "package" through every continuation and
verify its digest. If you cannot verify a digest, say that explicitly.

Report source locators, extraction and review limits, retrieval_complete,
assembly_truncated and the reasons evidence remains insufficient. Distinguish
the received source text from any interpretation. Do not decide the date of
an individual's award or fill gaps from memory. A failed or truncated read
must remain a reported failure; do not silently skip the missing part.
```

Each call defaults to an 8,192-byte complete response budget. A small catalogue
is not the source text, and the first slice is not a complete package. Preserve
UTF-16 offsets exactly as returned rather than estimating an offset from
visible characters. Complete delivery establishes that the selected package
arrived intact; the separate evaluation checks whether its declared target
passages and directed dependencies were retrieved.

All graph packages retain `evidence_status: insufficient` and `ai_answer: null`.
The original 203 open obligations remain visible. Source retrieval and delivery
do not establish current legal applicability, case-law reasoning, specialist
approval, human accessibility acceptance or Voice compatibility.
