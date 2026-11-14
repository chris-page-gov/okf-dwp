# Ask OKF 0.8.0: separate graph verification

The [hosting record](../../compact-delivery/v0.8.0/deployment.json) records
service 0.8.0 as published on 14 November 2026. The graph is admitted from DWP
producer `2e12f20cfd20e62a67197e7aade4ea612b873684`, independently of the legacy
default corpus. Its graph SHA-256 is
`ff51d877ed13f7089e7512224a4a8dcd356d0ae8e5964fe33349edf0a263b426` and engine is
`urn:okf:graph-engine:sha256:c75b01d322236e4c13fc1ad72a7e3424203dbae2413c4e6be64b960d8566cb42`.

Use the generated [graph status](../../../docs/graph-service-publication.md)
for the independently selected public SDK and native client observations.
The [actual public SDK run](sdk/attempt-01/summary.json) passed 106 unique
questions across 108 case occurrences: **355/355 positive source-target checks**,
representing 352 distinct question/target pairs. It completed 8,265 HTTP requests
with no retries or model calls and received 60,985,809 response bytes. The largest
complete evidence HTTP body was **7,469 bytes**, below the 8,192-byte ceiling.
Empty-target controls remain outside positive recall. SDK v2 ran the complete
matrix; SDK v1 independently reconstructed the fixed UC package and matched
the tool rows and package identity.
The portable client checks complete packages, source-text hashes, scoped paths,
open obligations and complete HTTP evidence responses of at most 8,192 bytes.
The frozen wording cases are an attempt-02 regression replay, not a new blind trial.

Replay the archived public packet without network access:

```sh
uv run --locked python validation/graph-evidence/v0.8.0/sdk/attempt-01/verify_graph_packet.py --packet-root validation/graph-evidence/v0.8.0/sdk/attempt-01
```

The [case fixture](sdk/attempt-01/expected-cases.json) was extracted from the
unchanged pinned verifier and producer inputs. It binds each of the 108 cases
to its exact expected records and source hashes, preserving all 355 checks
rather than multiplying the question-level union by its case count. The audit
recomputes package and source-text hashes, checks every case against that
fixture and validates the wire-event census and response-size classes.
It retains the original directed-path gate rather than repeating path resolution.
Wire response bodies are not retained: their digests and byte counts are recorded
metadata. [Eight mutation controls](sdk/archive-controls.txt) rejected altered
case counts, fixture bytes, unknown wire routes, tools and methods, and oversized
requests and responses. The [unaltered run log](sdk/attempt-01-run.log) retains
one non-fatal Node timer warning; the final pacing minimum was 750.0035 ms and
all run gates passed.

The [public Chrome observation](browser/chrome/observation.json) records the
0.8.0 landing page and health response with a separate screenshot. It is a public
browser check. A [fresh post-SDK browser observation](browser/chrome/post-sdk-observation.json)
returned HTTP 200 for the landing page and health route with the same graph
and engine identities and no page errors. The [initial native availability observation](native/attempt-01/availability.json)
records that both available tool contexts lacked the new graph actions; no
native graph call or no-truncation pass was made. An installed-state message
does not establish that the intended conversation can call those actions.

The actions subsequently became available in the primary conversation. The
separate [native observation](sdk/attempt-01/native-observation.json) records
five actual tool calls and four complete UC source-text hashes, with a maximum
observed MCP result JSON size of 6,370 bytes. The [raw native results](sdk/attempt-01/native-results.json)
retain the source slices and identities. This representative native read does
not claim the complete SDK matrix, native full-package reconstruction or HTTP
envelope measurement. The earlier unavailable observation remains unchanged.

Replay the retained native evidence without contacting the service or a model:

```sh
uv run --locked python validation/graph-evidence/v0.8.0/sdk/attempt-01/verify_native_observation.py --dwp-root .
```

The local Git object database must contain producer commit `2e12f20cfd20e62a67197e7aade4ea612b873684`.
CI fetches that exact public object before the offline replay. The replay checks
the receipt-bound raw results, capture order, normalised result sizes, UTF-16
slices and the four source hashes against the frozen graph and evaluation.

The [legacy SDK packet](../../compact-delivery/v0.8.0/README.md) has its own
successful replay and source/engine identities. No legacy result is substituted
for a graph or native result. Hosted Worker bytes are not independently attested
by these client checks. All graph packages remain insufficient with no AI answer;
current law, case-law reasoning, human accessibility review and specialist
acceptance remain outside the retrieval and delivery gates.
