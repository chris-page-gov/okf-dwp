# Public evidence service 0.6.0

Independent experimental evidence delivery, not an official DWP service or a complete benefits answer.

## Observed result

The [second public SDK observation](sdk/attempt-02/observation.json) ran on 21 September 2026 from 08:19:12 to 08:21:01 BST. It passed 11 evidence cases with 121 requests and 10,322,602 received bytes, without automatic retries. It checked nine explicitly approved source/engine combinations, an empty control and the original engine-unspecified 0.5.0 care-home package. Complete reconstructed packages, selected-record provenance and compact text/structured values match the local reference. Negative controls reject invalid or incompatible identities without returning evidence.

Both installed SDKs return the same complete tool definitions. Their protocol envelopes are checked separately. These are real public HTTP observations. No model calls or full `ask_okf` calls were made; complete packages were reconstructed from bounded reads.

The current care-home example contains 55 records and 115 relationships in 523,326 bytes. Its full package SHA-256 is `cb7e8e6f62a49a15907b09d2a32d525539c6853d5344ebcd5566bf616315e8f7`. It remains **insufficient**. The unknown-term control contains no selected records or relationships. The original historical package remains exactly 257,105 bytes, with its earlier identity and limitations intact.

## Separate immutable identities

| Layer | Identifier |
| --- | --- |
| DWP source | `723bcc5b015ab38a026625c2148edbd784edf7c7` |
| Current context engine source | `c4f2de0a99b7bc2f8b8c8a06a3c715fb56b66d8e` |
| Deployed service runtime | `0472b75a9dd353d6094a83ca9f752c4d78914168` |
| SDK verifier | `03d0264c02a6d59d75013df4bffba279b3d4aa9c` |
| Local Worker SHA-256 | `9e8840a9e31bac105dce0b40037300423cffe9dec90bbbab29b7541dd29b28ac` |

The [hosting record](deployment.json) records the successful public deployment at 08:03:29 BST. Its uploaded gzip digest and the hosting platform's normalised tar digest are different identities and are retained separately. The public health endpoint reports service/source/engine identities; it does not independently attest hosted Worker bytes. The corrected verifier has the same 44 runtime/comparator Git inputs as the deployed service, without relabelling the deployed runtime.

## Retained failure

[Attempt 01](sdk/attempt-01/failure.json) completed all 11 evidence cases but rejected the subsequent SDK v1 discovery comparison. The original verifier compared the whole SDK response, although v2 includes server/cache metadata omitted by v1. The corrected verifier checks both exact envelope contracts and compares every complete tool row. Fifteen offline controls include actual local SDKs and altered schemas, annotations and metadata. Attempt 01 remains unchanged; attempt 02 is separately recorded.

## Limits

Successful delivery is not legal correctness, complete evidence, specialist acceptance, an AI quality result or ChatGPT/Voice acceptance. No fresh public browser journey is claimed for 0.6.0. The earlier [0.5.0 observations](../v0.5.0/README.md) retain their own browser results, warnings, sources and engine boundaries. Anonymous user questions are not sampled or retained.
