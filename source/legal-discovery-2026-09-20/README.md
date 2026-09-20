# Official legal metadata observation — 20 September 2026

This is an additive metadata snapshot. The [manifest](manifest.json) binds 49
selected official legislation responses, six bounded tribunal searches and 18
decision metadata observations. Full statutory and judicial bodies were parsed
only to select metadata where necessary and were not retained or republished.
Hidden indexed judgment text is explicitly excluded.

Original request/resolved addresses, response byte counts and hashes, observation
times, source-native identifiers, version restrictions and dates remain in each
receipt. The original source XML/JSON body is not retained, so its response hash
is an acquisition observation, not an offline source-body reconstruction claim.
Each retained metadata file is independently bound by the manifest.

The acquisition is bounded by the [authored seeds](../../domain-profile/legal-reconciliation/seeds.json).
All 49 provision identifiers were observed. Every tribunal query was truncated
to its first three default-relevance results. No result has been selected as an
applicable precedent, and no complete amendment or commencement chain is claimed.

The offline [producer](../../scripts/build_legal_reconciliation.py) verifies the
seed and metadata hashes, then creates the candidate-page census and additive
reference records. It never reacquires sources. The explicit network acquisition
command refuses to overwrite this snapshot; preserve it when creating a refresh.

See [legal reconciliation](../../docs/legal-reconciliation.md) for counts,
limitations, rights boundaries, definitions and review instructions. This is an
independent experimental publication, not an official legal or DWP decision.

## Public projection of effect identifiers

GitHub publication protection flagged the literal form of 179 opaque `EffectId` values as possible Mailgun credentials. A bounded unauthenticated check of 14 official legislation XML responses found every value in an `Effect` or `UnappliedEffect` element. [The verification receipt](effect-identifier-verification.json) records response hashes, identifier digests and element positions; it contains neither credentials nor the opaque values. Two associated effect URLs differ from simple identifier concatenation, and that observation is preserved explicitly.

The values are unused by semantic reasoning. The public metadata now deliberately omits `EffectId` and its associated effect `URI`, retaining SHA-256 digests, one-based XML effect-element positions, amendment descriptions, source rows, dates and extent attributes. This is a **lossy projection**, not reversible encoding. No protection was disabled or bypassed. Original pre-publication metadata was preserved locally outside the repository; no original XML bodies were retained.

The [projection ledger](publication-projection.json) binds the previous and projected bytes of all 21 changed metadata files and preserves the original acquisition response hashes. The current manifest binds the projected files. Historical trial packages retain their earlier hashes and replay against an archived index; they must not be presented as products of this revised projection.

To make a separate future official verification receipt, explicitly run `uv run --locked python scripts/verify_legal_reconciliation_effect_origins.py --verify-official --output /path/to/new-receipt.json`. Existing receipts are never overwritten. Offline tests verify the retained proof without network access.
