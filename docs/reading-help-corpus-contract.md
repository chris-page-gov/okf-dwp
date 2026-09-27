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

The document index gives each segment a source-declared `label` and
`paragraph_labels` for navigation, plus sorted exact source-verified
`abbreviations` occurrence literals, alongside the exact unit ID, role, pages
and leaf binding. These labels and literals do not imply a new legal category
or a globally valid expansion.

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


The current frozen build has a 260,797-byte catalogue. The largest document
index is 498,791 bytes; the largest leaf is 51,223 bytes compressed and
254,317 bytes decoded. A reader can fetch one index and its selected leaf,
without loading 1,455 leaves or the adopted structured-unit file.

The preliminary 12+24 first-page controls check exact source locations and
projection preservation. A separate source-led initial 12-case gate passed
after its first failure was retained. The first fresh 24-case held-out gate
remains failed at 23/24: one frozen expected label omitted a printed range
qualifier. The revised fresh 24-case gate passed 24/24, including abbreviation
scope, continuing tables, explicit exceptions and unresolved references. Its
source-reviewed fixture, exact evaluator and result are under
`evaluation/reading-help-rollout/heldout-03-*`. None of these checks establishes
legal currency, specialist review or staff answer quality.

The Chapter 60 `okf-reading-help.v1` aid remains separate and unchanged.
Source text and generated candidate content are inert data. No model call,
OCR, PDF reacquisition, legal applicability inference or entitlement calculation
occurs in this producer.

## Local commands

`PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_reading_help_corpus.py`
builds or resumes unchanged, hash-bound document leaves on ExtSSD.
`PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_reading_help_corpus.py --check`
rebuilds all documents from frozen source and compares exact bytes without using
the output cache. The warm cache key binds producer, shared structured-input helper, reference
parser and every printed abbreviation-table PDF and extraction hash. Leaves
use the shared mtime-zero gzip writer with OS header byte 255, removing
the platform-dependent header from cross-platform byte checks. A change
to a supporting table invalidates dependent document caches. The ordinary Chat pack utility is
`scripts/reading_help_chat.py`; `export --document-id ID --limit 12 --output FILE`
selects unresolved candidates, and `import --requests FILE --requests-sha256
SHA256 --replies FILE --output FILE` saves gated, unpublished proposals. The exported pack includes a reply JSON
schema, total and selected candidate counts, selection truncation, a bounded
skip count and complete selected passages. Output is confined to the resolved
local quarantine and created exclusively. The abbreviation/table recognisers primarily accept uppercase forms; mixed-case
forms such as `WDisP` are not exhaustively recognised. Repeated-phrase
proposals are capped at 100 per document. `processed` therefore records a
completed deterministic pass, not exhaustive vocabulary recognition. Unsupported
forms remain for later source-led review. No network or model call is made.
