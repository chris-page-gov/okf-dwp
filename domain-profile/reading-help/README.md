# Chapter 60 reading help: authored review overlay

`ch60.json` is an occurrence-specific, project-authored review overlay for two frozen Decision makers’ guide passages: 60025 on PDF pages 3–4 and 60033 on pages 4–5. The original Chat proposals remain in `research/ch60-reading-help/` with their bytes and SHA-256 identities unchanged. The overlay records three corrections and two explicit exclusions without rewriting those proposals.

The producer checks the original proposal hashes, the frozen PDFs and page extractions, then resolves every passage, occurrence and support quotation to a page-local, half-open UTF-8 byte span. It emits the root-level `reading-help-ch60.json` for the separate Explorer reading-help view. A matching word elsewhere in the chapter is not selected automatically. The source’s printed extra `2` and mixed reference `12` remain unresolved.

Expansion from an abbreviation list, a source pointer to a definition, and a project-authored reading explanation have different `kind` and `authority` values. Every card has exact source support and retains unreviewed status. Source markers, condition numbers, numbered alternatives and notes have separate occurrence identities. A citation to absent legislation stays unresolved; an internal link is allowed only where this bounded manifest contains the exact passage target.

```sh
uv sync --locked
uv run --locked python scripts/build_reading_help.py
uv run --locked python scripts/build_reading_help.py --check
uv run --locked python -m unittest discover -s scripts -p test_reading_help.py
```

The build is local and deterministic. It does not acquire sources, call a model or change the frozen pilot, full-DMG or combined Reader projections. A successful check establishes source and import integrity for these two passages, not legal applicability, explanation quality, corpus coverage or specialist acceptance. The [reading guide](../../docs/reading-help-ch60.md) gives the demonstration and remaining work.
