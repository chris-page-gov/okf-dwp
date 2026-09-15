# Full DMG source acquisition

All **331 PDF URLs** in the frozen 15 September 2026 DMG census have been acquired and verified. The source inventory measures **14,743 pages**, **146,090,882 PDF bytes** and **27,613,797 extracted characters**. Declared and measured page and byte totals agree. There are no acquisition failures.

The run reused 36 original Pension Credit files after checking their URLs and hashes, preserving their original observation times and paths. It downloaded the remaining 295 files with four bounded workers. See the [inventory](../../source/full-dmg-2026-09-15/inventory.json), [verification receipt](../../source/full-dmg-2026-09-15/verification.json) and [quality report](../../source/full-dmg-2026-09-15/extraction-quality.json).

## What source completeness means

Every direct PDF in this frozen DMG census is accounted for. This does not establish that the guidance is legally current or that all references, source relationships, statutory provisions or case law have been acquired. ADM remains separately scoped. The original Pension Credit snapshot and its discovery handoff remain intact.

Automated quality checks identify **802 pages without extracted text**, **176 sparse pages** and **512 pages with possible letter-spacing defects**. These categories are signals, not diagnoses. The limited rendered sample includes one visibly blank no-text page and an amendment with damaged extracted spacing; it does not classify all 802 pages. No OCR or automatic source-word correction has been performed.

## Dates and references

The [evidence index](../../evaluation/full-dmg-evidence/index.json) covers all acquired pages with a bounded, reproducible recogniser. It retains exact spans and page hashes for date mentions, explicitly labelled revision statements, DMG paragraph and memo references, and candidate legal-reference lines.

**178 documents contain recognised explicit revision statements.** This is not a count of known publication or commencement dates. Multiple dates are retained, and unlabelled dates remain context-dependent. The recogniser does not establish the current effect of an amendment, resolve statutory versions or exhaust every citation format. Its output is a worklist with evidence for further reconciliation.

## Verify locally

Use the locked Python environment and installed Poppler tools:

```sh
uv run --locked python scripts/acquire_full_dmg.py --check
uv run --locked python scripts/discover_full_dmg_evidence.py --check
uv run --locked python scripts/query.py '84351' --scope full-dmg --limit 5
uv run --locked python scripts/query.py '84351' --scope full-dmg --include-history --limit 5
```

The checks do not fetch remote sources. The retrieval command identifies its inventory hash and document role, and the history option includes memos and amendment material. Search results remain evidence for inspection, not benefit decisions.
