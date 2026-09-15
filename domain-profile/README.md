# Draft discovery contract

The [discovery report](../docs/discovery.md) explains the decisions in plain English. This folder records the machine-readable contract and its evidence.

| File | Purpose |
| --- | --- |
| [domain-profile.yaml](domain-profile.yaml) | Authored discovery contract, deliberately `draft` |
| [domain-profile.json](domain-profile.json) | Equivalent JSON representation |
| [domain-profile.schema.json](domain-profile.schema.json) | Exact vendored Explorer authoring schema |
| [consumer-lock.json](consumer-lock.json) | Inspected Explorer commit, prompt digests and initial validator identity |
| [impact-graph.json](impact-graph.json) | Which source, build and consumer checks changes affect |
| [evidence/](evidence/) | Bounded official-reference retrieval receipts and the collection-link coverage receipt |
| [validation.json](validation.json) | Initial profile/schema/inventory checks |
| [check.json](check.json) | Reproducible schema, YAML 1.2, local evidence and ledger checks |

Run the read-only checks from the repository root:

```sh
uv run --locked python domain-profile/validate.py
```

Use `--output domain-profile/check.json` to record the result. This command does not fetch remote sources or claim legal correctness, expert review, Explorer acceptance or full Foundry conformance.

The profile binds the exact source inventory bytes. Update its inventory digest, equivalent JSON and evidence references when replacing that inventory, then rerun validation. Do not silently reuse an old validation receipt.

The standards register records applicability separately from implementation. Conditional and reference-only standards do not imply implemented features. A 403 receipt is a recorded access gap; an HTTP 200 receipt is evidence of acquisition, not of full semantic or legal verification.

The collection-link ledger covers a single collection identity and its official publication page. Its 1-of-1 result must not be presented as coverage of every document, paragraph or legal citation.
