# Full-source context corpus

This separately generated corpus makes every non-empty captured source page
available to bounded lexical retrieval. It preserves source evidence and the
existing semantic discovery graph. It does not add completeness requirements,
consolidate current law, infer answers or replace the original custody profile.

## Consumer contract

The entrypoint is `context/corpus/manifest.json`. All runtime fetch references are
relative to that directory, never to an arbitrary remote address or parent path.
`bytes` and `sha256` bind transferred bytes; decoded fields bind the uncompressed
JSON. Each decoded shard is at most 4 MiB. The manifest is at most 4 MiB.

```json
{
  "schema": "okf-context-corpus.v1",
  "bundle": {"id": "https://example.test/id/corpus", "snapshot": "content-derived", "source_url": "https://example.test/"},
  "scope": "Frozen public-source research discovery; no completeness claim",
  "limitations": ["Source and context coverage are different"],
  "base_index": {"path": "base-index.json", "bytes": 123, "sha256": "64-hex-digits"},
  "records": {
    "count": 100,
    "shards": [
      {"first_ordinal": 0, "count": 100, "path": "records/0000.json.gz", "bytes": 123, "sha256": "64-hex-digits", "decoded_bytes": 456, "decoded_sha256": "64-hex-digits", "encoding": "gzip"}
    ]
  },
  "search": {
    "tokenisation": "nfkd-lowercase-ascii-alphanumeric-min2-v1",
    "bucket_algorithm": "fnv1a32-high-byte-hex-v1",
    "shards": {
      "00": {"path": "search/00.json.gz", "bytes": 123, "sha256": "64-hex-digits", "decoded_bytes": 456, "decoded_sha256": "64-hex-digits", "encoding": "gzip"}
    }
  },
  "source_groups": [],
  "unsearchable_pages": [],
  "inputs": []
}
```

Each records shard decodes to:

```json
{"schema":"okf-context-records.v1","first_ordinal":0,"records":[{"id":"absolute canonical IRI"}]}
```

Each entry is a complete `ContextRecord` following the existing Context Assembly
profile. Source pages are sorted by canonical identifier. Global zero-based
ordinals are contiguous across records shards. If a page already occurs in the
base discovery index, its record object is reused exactly.

Each search shard decodes to:

```json
{"schema":"okf-context-postings.v1","postings":{"hospital":[12,45,78]}}
```

Postings contain sorted unique global record ordinals, covering the complete
extracted text. There is no frequency cap, answer-specific term selection or
vocabulary truncation. Tokenisation applies Unicode NFKD, removes combining
marks, lowercases and selects ASCII `[a-z0-9]+` tokens of at least two characters.
Repeated tokens within a page contribute one posting. No stopwords are removed
from the corpus. Consumers may apply their declared query stopword policy and
must report retrieval budgets and omissions.

For each ASCII token, start FNV-1a at unsigned `0x811c9dc5`; for every byte, XOR
then multiply by `0x01000193` modulo 2³². The high byte (`hash >>> 24`) formatted
as two lowercase hexadecimal characters chooses one of 256 search shards.

`source_groups` records each source family's inventory path and hash, collection
URL, capture observation and document/page counts. An empty extracted page is
accounted for in `unsearchable_pages` with its identity, URL and
`empty-extracted-text` reason, but is not offered as evidence. A non-empty page
with no eligible lexical tokens remains in records and is separately labelled
`no-eligible-lexical-tokens`. Counts therefore distinguish acquired pages from
searchable pages and do not claim OCR recovery.

## Producer

`context/corpus-sources.json` declares the local frozen inventories to include.
The compiler accepts DMG and ADM inventories with the existing acquisition
document/page shape; source families retain separate counts and provenance.
Adding ADM data does not establish contemporary applicability or reviewed policy.

```sh
uv run --locked python scripts/build_context_corpus.py
uv run --locked python scripts/build_context_corpus.py --check
uv run --locked python scripts/build_context_corpus_explorer.py
uv run --locked python scripts/build_context_corpus_explorer.py --check
uv run --locked python -m unittest discover -s scripts -p 'test_context_corpus.py'
```

The build reads only frozen local bytes. It verifies PDF, extraction, semantic
and base-index hashes, preserves exact whole-page text, emits deterministic gzip
and binds inputs in the manifest. Its snapshot derives from source inventory,
semantic discovery and producer/configuration identities. Existing `full-dmg/`
outputs and original remote MCP receipts remain unchanged.

The additive Explorer descriptor is `full-dmg/okf-corpus-context.json`. It keeps
the DMG Reader, Search and graph release intact and adds the `context_corpus`
entrypoint for Ask OKF. Exact corpus bytes are copied under
`full-dmg/context/corpus/` so every runtime reference remains within the
descriptor directory. `context/corpus-explorer-projection.json` verifies the
copy and the original descriptor's unchanged hash. ADM pages are available to
Ask OKF; the inherited Reader and Search are explicitly still DMG-only.
