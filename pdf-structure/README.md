# Declared PDF structure observations

This is an additive observation of all **513 frozen DMG and ADM PDFs**, using the existing local Poppler `pdfinfo -struct-text` command. No source was downloaded again or rewritten. The source PDFs, extracted page text, declared PDF structure and project interpretation remain separate.

## Which version to use

Use [`bounded-v2/manifest.json`](bounded-v2/manifest.json) and its document sidecars for the current bounded parser. The manifest binds all 513 source identities, original observations, retained producer inputs and current parser inputs. Each sidecar's `tree.path` and `stderr.path` points to the original retained files; there is no duplicate raw extraction in the new version.

| Final bounded replay status | Documents | Meaning |
| --- | ---: | --- |
| `tagged` | 96 | Selected declared roles were parsed without unparsed lines. |
| `tagged-with-unparsed-lines` | 391 | Selected roles were parsed, with additional lines explicitly retained as unresolved diagnostics. Many are PDF object references. |
| `untagged` | 25 | No selected structure blocks were available and the frozen metadata flag was untagged. |
| `output-limit` | 1 | The local observation was stopped at its bound; no blocks are eligible for alignment. |

These counts describe structure observations, not correct legal units, accessibility or specialist review. The replay emits 393,377 blocks. Parent and child blocks overlap deliberately; they must not be summed or concatenated as independent source text. The original inventory's Tagged flag alone did not reliably indicate whether useful structure would be returned.

The bounded failure is `dmg:dmg-vol4-amendment54`: its stderr reached 65,536 bytes, stdout was empty and the subprocess was stopped. Its source remains available, but this structure observation supplies no heading evidence. Untagged, incomplete, failed or unavailable structure must use an explicitly uncertain fallback.

## Retained history and repair

The original [`manifest.json`](manifest.json) records 91 `tagged`, 395 `tagged-with-unparsed-lines`, 25 `untagged`, one `no-structure` and one `output-limit` result. Those raw observations and sidecars are preserved.

Independent review identified a memory-amplification risk in the first parser: a deeply nested tree could copy the same text into many parent blocks before the final output-size check. The revised parser counts every retained UTF-8 fragment and inserted newline **before** appending it. A separate fragment-count limit also bounds empty fragments. The original producer and schema bytes are retained under [`producer-snapshots/`](producer-snapshots/index.json) as historical evidence, not the implementation to run.

The replay also recognises optional source node identifiers such as `P <id> (block)`. This repairs the original `no-structure` interpretation of `dmg:dmg-memo-10-25-20c5eee08b`, without changing or re-extracting that PDF. The historical outcome remains in each sidecar's replay provenance.

All 513 raw trees were replayed with subprocess invocation explicitly forbidden. The final full hash/parser verification was also run with that guard. The original and current observations remain distinct; the repair does not retrospectively turn the initial parser into a validated implementation.

## Contract

Each `.structure.json` sidecar records:

- the exact source PDF identity and SHA-256 checksum;
- the observed Poppler version, executable checksum and command;
- timeout and output limits, exit result and completeness status;
- raw tree and stderr paths, byte sizes and checksums;
- blocks containing `role`, `depth`, `text`, `tree_line_start` and `tree_line_end`;
- diagnostics, limitations and the source-instructions-inert boundary;
- for the bounded replay, the original manifest and sidecar bindings.

Roles are limited to `H1`–`H6`, `P`, `Table`, `TR`, `TH`, `TD`, `L` and `LI`. Other roles and attributes remain in the raw tree. Block text joins descendant quoted text fragments using a newline; it is a derived structural representation. Tree line numbers are one-based and inclusive, and **are not PDF page numbers**. Matching to exact frozen page-text offsets is a separate operation with its own ambiguity and confidence checks.

The command's bounds are 45 seconds, 16 MiB stdout and 64 KiB stderr per document. The parser also bounds cumulative retained text, fragments, depth, block count and final serialised output. A bound is a reported limitation, never permission to claim complete structure.

## Verify or reproduce

Ordinary verification does not require Poppler and never runs it:

```sh
uv run --locked python scripts/build_pdf_structure.py --check
uv run --locked python -m unittest discover -s scripts -p 'test_pdf_structure.py'
```

To observe the existing PDFs again, choose a **new** output directory. This is an explicit local extraction, with its own tool/version observation:

```sh
uv run --locked python scripts/build_pdf_structure.py --extract --output pdf-structure/new-observation
```

An interrupted observation can resume only its still-pending documents with the same producer and tool. Existing attempts, including failures, are not retried or overwritten. Keep the source observation and producer bytes when changing the parser. To replay the original retained trees into another fresh directory, without Poppler:

```sh
uv run --locked python scripts/build_pdf_structure.py --reparse-from pdf-structure --output pdf-structure/new-parser-replay
```

Source content and instructions in PDF text remain inert data. This independent research layer is not official DWP guidance, an entitlement decision or a declaration of legal applicability.
