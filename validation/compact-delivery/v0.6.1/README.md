# Service 0.6.1: public delivery and connector observations

[Shared recorded status](../../../docs/service-publication.md) · [Client guide](../../../docs/chatgpt-connection.md) · [Preserved 0.6.0 observations](../v0.6.0/README.md)

Service **0.6.1** was published on **21 September 2026 at 11:52:32 BST** as
Sites version **11**. Its patch changes the advertised question pattern so
clients using whole-string matching can accept ordinary questions. The source,
engine implementations, evidence selection and non-blank/length constraints
remain unchanged. This is an independent experiment, not an official DWP
service or an individual benefits decision.

## Exact publication identities

The [hosting receipt](deployment.json) records the reviewed build, final archive,
stored upload and successful publication separately. The immutable receipt
commit is `a13a291f8b61161d60b9745ba7623ecc04839998`.

| Identity | Recorded value |
| --- | --- |
| Reviewed runtime and SDK comparator commit | `1420c3165f32b49afca6b33adcccadfdd956cd50` |
| Merged Explorer commit | `687439840b241c0a1d7f55ee61cee08aa771069f` |
| Shared complete Git tree | `67eb52f727701bdf9961a8cbadb73f3e2e041d22` |
| DWP source commit | `723bcc5b015ab38a026625c2148edbd784edf7c7` |
| Current engine source | `c4f2de0a99b7bc2f8b8c8a06a3c715fb56b66d8e` |
| Local Worker SHA-256 | `bd3283e5413bd2b13428ea599e8b3e4b8897004603094327525163afccfc7467` |
| Build receipt SHA-256 | `efaa9b0731b15013060575977cf967e1ef0441c2e8842be72cd8cac3038c62f9` |
| Sites source commit | `a8c2dc2adc9084f4629c4ced0124f21076dca15e` |
| Final archive SHA-256 | `a6c4dbe8e6124cb0019da42c48686a6345647f759c1de9415b8111ff81056aff` |
| Stored upload content hash | `57d40e05d289fea757a587a436002947acf58f9990a9b3d2df907d316dcd08cb` |

The reviewed runtime and merged Explorer commit have identical complete Git
trees. Keeping the original runtime identity in the receipt therefore preserves
what was built; the merge is not retrospectively substituted for it. The final
stored tar contains two files and is 4,198,400 bytes. Its storage identifier and
the complete Sites version identifier remain in the hosting receipt.

A first archive save was rejected **before version creation** because its
entrypoint layout was wrong. The layout was corrected without changing the
Worker bytes. That packaging rejection is separate from the successful final
archive and publication; it was not a failed evidence call or an SDK retry.

## Actual public SDK check

The [first 0.6.1 SDK observation](sdk/attempt-01/observation.json) ran from
**11:53:33 to 11:55:35 BST** and passed:

- all **nine approved source/engine combinations** across five source versions
  and two explicitly compatible assemblers;
- the separately identified **original 0.5.0 care-home replay**;
- the **empty-evidence control**, for **11 cases** in total;
- **121 HTTP requests**, comprising 120 HTTP 200 responses and one HTTP 202;
- **10,322,722 received bytes**, with no automatic retries, model calls or full
  `ask_okf` calls.

SDK means software development kit: these test clients invoke the real tools
over HTTPS. Both SDK generations checked the complete tool definitions. Small
catalogue pages and contiguous evidence reads reconstructed every selected
package and matched the local reference exactly. The retained compressed files
contain the actual received packages. All 11 context identifiers and complete
canonical package hashes also match the preserved 0.6.0 observation.

The current Staff 012 case contains **55 records and 115 relationships** in a
**523,326-byte** package under a 512 KiB assembly budget. It remains
**insufficient**. Delivering every byte of a bounded package does not restore
material omitted during assembly or establish complete legal evidence.

The [executed verifier](sdk/attempt-01/executed-verifier.ts),
[plan](sdk/attempt-01/plan.json) and [build receipt](sdk/attempt-01/build-receipt.json)
are retained with the observation. No later verifier is substituted for this run.
The hosting record and expected local Worker hash are distinct evidence: the
public health response does **not** independently attest the hosted Worker bytes.

## Native client checks: narrower acceptance

The [separate before-and-after observations](../../client-connection/2026-09-21/README.md)
show that the same multi-character unknown-term question previously rejected
by the connector now succeeds in the same Codex task. It returns an empty,
insufficient context. An exact Staff 012 check also reaches the service, but
its deliberately smaller **16 KiB** package budget returns zero records and
an explicit byte-budget omission. Neither diagnostic is an AI answer trial.

The refreshed ChatGPT settings show all three read-only tools, the anchored
question pattern, five sources and two engines, with permissions unchanged.
The already-open Codex task still exposes only the full-package tool. Compact
tools were advertised in ChatGPT settings, not invoked by that task. The
intended Data Agent and new compact-client journey remain unaccepted; parent
chat tools do not prove propagation into a nested agent. Voice and room audio
also need their own observations. **DWP-BL-008.client-connection stays open.**

## Status drift control

After the new receipts were saved, the shared status checker was run with its
old 0.6.0 selection. It refused with **“A newer successful deployment is not
represented”**. Once the selection pinned the new receipts at `a13a291f…`,
generation and check mode passed for 0.6.1, together with all 19 synthetic status
controls. This observed refusal prevents old publication wording from silently
surviving new recorded evidence. It is an offline consistency check, not a live
health probe. Earlier observations, including failed attempts, remain unchanged.
