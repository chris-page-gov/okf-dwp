# Client connection observations — 21 September 2026

These observations concern the existing Codex desktop task and the owner's
installed ChatGPT connection. They are separate from SDK transport checks,
model trials, Data Agent acceptance and Voice access.

## Before the schema correction

The [public-safe observation](before-patch.json) records two actual native tool
calls. At 11:10:53 BST the ordinary unknown-term question was rejected by
connector schema validation against `\S`. At 11:11:38 BST the one-character
control completed and returned an empty, insufficient context. Its exact
structured JSON value is retained in [the control package](single-character-context.json).
This is a JSON serialisation of the returned value, not a raw HTTP response.

The older tool metadata advertised two source versions and no engine field;
the returned package identifies the newer `723bcc5…` corpus through its binding.
This demonstrates why advertised metadata and actual returned identity must
both be inspected. It does not prove ordinary questions worked in that client.

The error record uses an explicit field allowlist. Broker metadata, location,
account and session identifiers are omitted. No raw connector error envelope is
published. MCP initialisation and discovery messages were not exposed by this
brokered tool interface, so no raw protocol transcript is claimed.

The installed ChatGPT connection was separately refreshed through its visible
**Refresh** control: all three read-only tools, five approved source versions
and two engines became visible. That first refresh still advertised `\S`.
Permissions were unchanged. This interface observation is not an invocation.

## After the 0.6.1 publication

The [later public-safe observation](after-patch.json) retains two further calls
from the same existing Codex task. Neither overwrites the earlier rejection.

| Actual call | Recorded result |
| --- | --- |
| Unknown term, 11:54:14–11:54:16 BST | The exact previously rejected question, `xylophonicquasarteleportation`, now succeeds with the same 32 KiB budget. The [4,381-byte context](unknown-term-after-patch.json) has no selected records or relationships, is not budget-truncated and remains `insufficient`. |
| Exact Staff 012 question, 11:54:31–11:54:33 BST | The [2,032-byte context](staff-012-small-budget-context.json) contains no selected records or relationships. Its 16 KiB package budget produced an explicit `byte_budget` omission and `insufficient` status. This proves bounded invocation, not useful answerability. |

These sizes are the complete canonical JSON package sizes reported by the
assembler. The readable files here serialise the returned structured values;
they are not raw HTTP captures. Both packages retain `ai_answer: null`.

The later ChatGPT settings refresh displayed all three read-only tools with
`^[\s\S]*\S[\s\S]*$`, the existing 1–2,000-character limit, five sources and two
engines. Permissions were unchanged. The observation time, 11:53:28 BST, is the
clock read after refresh rather than an exact click timestamp. The already-open
Codex task still exposed only `ask_okf`; it did not call the compact tools.

The [separate 0.6.1 public SDK observation](../../compact-delivery/v0.6.1/README.md)
reconstructed all 11 cases, including the larger 55-record Staff 012 package.
Those SDK calls do not prove compact tools are available to this Codex task,
a new ChatGPT conversation or a nested Data Agent. No Data Agent, Voice or AI
answer acceptance follows from these diagnostic calls.

## Repeatable acceptance

The [client guide](../../../docs/chatgpt-connection.md) supplies the empty-control
and fixed care-home prompts. Retain subsequent attempts separately; do not
replace the rejected call with a passing one. A new target session must actually
invoke its tools before its own integration gap can be marked complete.
