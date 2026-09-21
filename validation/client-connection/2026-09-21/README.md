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

## Repeatable acceptance

The [client guide](../../../docs/chatgpt-connection.md) supplies the empty-control
and fixed care-home prompts. Retain subsequent attempts separately; do not
replace the rejected call with a passing one. A new target session must actually
invoke its tools before its own integration gap can be marked complete.
