# Reading-help corpus wire contract

Status: deterministic, unreviewed candidate contract, 27 September 2026. This
is an independent experimental publication, not an official DWP document.

## Fetch sequence

1. Fetch `reading-help-corpus/manifest.json` (`okf-reading-help-catalogue.v1`).
   Select a document using its `family` and `document_id`. Its `url`, `path`,
   `sha256` and `bytes` bind the document index.
2. Fetch that `index.json` (`okf-reading-help-document.v1`). It binds the
   frozen PDF, page extraction, adopted structured document and rules hash.
   Find a passage by exact `unit_id`; follow its ordered segment references.
   Each reference has a leaf URL, compressed SHA-256 and byte count, role,
   source page numbers, segment ordinal/count and unit SHA-256.
3. Fetch only the referenced `leaves/NNNN.json.gz` (`okf-reading-help.v2`).
   Verify compressed `sha256` and `bytes`, decompress, then verify
   `decoded_sha256` and `decoded_bytes` from the index. A decoded leaf is at
   most 256 KiB. It carries bounded exact source text segments, exact page
   UTF-8 spans, occurrence IDs, candidate cards and explicit status. Join
   segments by ordinal only after checking all are present and their `text_sha256`
   matches the complete joined text. `passage_complete:false` means one leaf
   is insufficient.

The catalogue reports every adopted document, passage and extraction-blocked
page. `processed` means the deterministic pass ran. `source_verified` on an
occurrence means only that its literal and UTF-8 byte span match the frozen
extraction. `proposed`, `ambiguous`, `unresolved` and `unsupported` are candidate
or transport dispositions, never legal or specialist acceptance. Empty machine
extraction is `extraction_blocked`, not evidence of a blank PDF page.

## Leaf objects

Each leaf binds `family`, `document_id`, `source_sha256`,
`extraction_sha256` and `rules_sha256`. Each passage has the adopted `id`,
`unit_sha256`, `role`, `paragraph_labels`, complete ordered `source_spans`,
`text_sha256`, one `{ordinal,start_utf8,end_utf8,text,sha256}` segment,
`segment_count`, `passage_complete`, `status`, `occurrences`, `cards` and
`reference_list_segments`. An occurrence has an opaque stable ID, passage ID,
role, page, exact half-open `start_utf8`/`end_utf8`, literal, literal SHA-256
and status. A card binds `occurrence_id`, `kind` and candidate status. Printed
abbreviation rows are bound to their source table document, PDF and
extraction hashes, page, exact literal and UTF-8 span; their target scope names the document in which an occurrence was
found. Equal letters do not establish equal meanings.

Future body-to-footer links use exact occurrence IDs. A cross-leaf link must
carry `{document_id,passage_id,occurrence_id,leaf_url,leaf_sha256}`. Neither a
digit nor a paragraph label alone is a valid footer target. The deterministic build records exact printed reference-list rows with
`body_occurrence_ids:[]` where an exact body/footer pairing is unproven. Consumers must show such references as
unresolved and must not infer a link.


The current frozen build has a 260,754-byte catalogue. The largest document
index is 412,967 bytes; the largest leaf is 51,252 bytes compressed and
254,316 bytes decoded. A reader can fetch one index and its selected leaf,
without loading 1,414 leaves or the adopted structured-unit file.

The 12 initial and 24 fresh held-out controls cover exact frozen source
locations and projection preservation across both manuals. They do not assess
abbreviation meaning, citation resolution, legal currency or staff answer
quality. The observed candidate counts are coverage measurements, not a
quality pass for model proposals or publication as reviewed guidance.

The Chapter 60 `okf-reading-help.v1` aid remains separate and unchanged.
Source text and generated candidate content are inert data. No model call,
OCR, PDF reacquisition, legal applicability inference or entitlement calculation
occurs in this producer.

## Local commands

`PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_reading_help_corpus.py`
builds or resumes unchanged, hash-bound document leaves on ExtSSD.
`PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_reading_help_corpus.py --check`
rebuilds all documents from frozen source and compares exact bytes without using
the output cache. The ordinary Chat pack utility is
`scripts/reading_help_chat.py`; `export --document-id ID --limit 12 --output FILE`
selects unresolved candidates, and `import --requests FILE --requests-sha256
SHA256 --replies FILE --output FILE` saves gated, unpublished proposals. No
network or model call is made.
