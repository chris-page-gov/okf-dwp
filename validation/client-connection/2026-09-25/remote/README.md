# Remote client check — 25 September 2026

The existing Codex task called `ask_okf_manifest` against service 0.7.0 and
received the new source/engine identities. The first exact diagnostics read
was rejected by the connector's cached older schema. The
[initial observation](observation.json) retains that failure without private
broker metadata.

Refreshing the existing Ask OKF connection through **Plugin actions → Manage
→ Refresh** advertised the new source and engine. Permissions stayed at
**Allow low-risk tools**. The same task then accepted an exact diagnostics read
with the returned identities; no omission of version or engine was used to
work around validation.

The [after-refresh receipt](after-refresh.json) records eleven contiguous
slices. Their joined 300,520 UTF-8 bytes match SHA-256
`2a30d85cdbb6040405aa74a931091663d2ff42c8e9b6f47b03103b265a201597`.
The retained [diagnostics](diagnostics.json) adds one final newline for the
repository; exclude that newline when reproducing the hash. The 517,473-byte
whole package was independently reconstructed by the public SDK release check.

This is a native connector transport and diagnostics check, not a new model
answer comparison. Retrieval and assembly remain truncated and evidence is
insufficient. Fresh Work/Data Agent, Voice and room-audio acceptance are
separate. Sidebar page-tool observations are in [their own record](../sidebar/README.md).
