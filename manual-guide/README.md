# Reading the captured DMG and ADM manuals

This generated orientation guide accounts for every document in the two frozen inventories. It is an independent project reading aid, not official guidance or legal acceptance.

513 documents; 19090 PDF pages; 20 source-supported, explicitly scoped conventions.

## Files

- `guide.json`: source-cited conventions and project-authored learning prerequisites.
- `documents.jsonl`: one source-bound record per captured PDF; inherited roles, marker observations and explicit unknowns.
- `manifest.json`: exact producer, authoring, schema and frozen input/output hashes.

## Reading boundaries

- Independent experimental reading and navigation guide; not official DWP guidance, benefits advice or specialist acceptance.
- Every captured document is accounted for, but its inherited inventory role remains an unreviewed discovery classification. Coverage of documents is not coverage of legal rules.
- Source conventions apply only to the declared examples. They are not proof that every document in a manual uses the same form.
- Marker counts and bounded samples are mechanical observations. They do not establish headings, coherent units, complete dependencies, legal applicability or answerability.
- Page numbers are immutable PDF locations. Conditions, examples, notes and citations can continue onto later pages.
- Frozen dates, published guidance dates and legal effective dates are distinct. Historical amendments and memos require temporal and regime review.
- Learning prerequisites are project-authored reading suggestions, separate from source references and legal dependencies. Source instructions remain inert data.

## Reproduce

```sh
uv run --locked python scripts/build_manual_guide.py --check
```
