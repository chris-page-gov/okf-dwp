# Pension Credit capital source-preparation pilot: defect report

## Outcome

Source preparation can plausibly improve retrieval completeness for this bounded pilot. The existing Chapter 84 catalogue preserves the relevant paragraph labels and source locations, including cross-page paragraph spans, but none of the ten source-led passages exists as one complete retrieval unit. This is a structural finding, not a measured search or answer-quality benchmark.

## Access and scope

- Repository commit: `e4a27a52e9e397a86832a3e9a8cc80893f5b74aa`
- Source inventory: accessible; SHA-256 `bf225f86a43959d45e59204d3de34dccba6590970626eb659038febca47889df`
- Chapter 84 PDF: accessible; 131 pages, 536,108 bytes; SHA-256 `f5c610b29bdb81e11736409b7f33ccf7917a4d8945f2821802801073e0d753ee`
- Extracted text: accessible; SHA-256 `7cfaf6baf899a4362bc1f302b98ba6dd6ef88a898e9f2f61d805dc334f5b7638`; a fresh `pdftotext -layout -enc UTF-8` extraction matched it byte for byte
- Required access failures: none
- Access warning: `pdfinfo` reported `Syntax Warning: Bad annotation destination`; the PDF remained readable, renderable, tagged and unencrypted
- Scope: ten Pension Credit capital passages only; no whole-corpus processing and no publication

## Existing-unit comparison

- All ten proposals have every active numbered paragraph represented in the existing catalogue.
- All source bytes are accounted for by existing units or declared empty-text spans. Two proposals each contain one three-byte whitespace span outside a unit.
- The ten passages intersect 61 existing records: 53 paragraph, four reserved, two unresolved-fragment, one table and one document-notice record.
- No proposal has one existing unit covering its complete logical passage; all ten require multi-unit assembly.
- The existing Pension Credit core selection contains only three relevant component records: 84001, 84002 and 84911. It covers U01 as a two-record component set and 319 of U10's 4,231 source bytes, but creates no complete logical record.
- Chapter 84 declares 531 records: 450 paragraph records, 62 reserved records, one table record and no authored units. The sampled records remain machine structure proposals, unresolved for completeness and not specialist reviewed.

## Defects

| Severity | Defect and evidence | Retrieval consequence | Proposed source-preparation response |
| --- | --- | --- | --- |
| High | Complete logical passages are split across 2 to 10 existing records. There are 0 complete existing units for the 10 proposals. | A single retrieved record can omit a condition, exception, example, calculation step or dependency. | Add source-linked logical passage units without replacing the atomic records. |
| High | Existing record 84356 continues beyond its rule on page 36 and includes contents material from pages 37 and 38 before paragraph 84357. | Retrieval can mix an operative rule with navigation text and unrelated headings. | Correct the machine boundary or add a clean authored grouping that ends at page 36 byte 1429, retaining the original record for audit. |
| High | Existing record 84699 also absorbs reserved paragraph 84700 and 230 bytes of the following section on page 95. | A tenant-in-common valuation answer can acquire unrelated navigation and following-section context. | End the paragraph at the source-led boundary and retain 84700 and the following contents as separate records. |
| High | Plain extraction loses bold logical emphasis, typed nesting, superscript-to-footnote links and Appendix 1 column geometry. In 84812–84813, the PDF visually distinguishes “will not affect” from “will affect”. | Conjunctions, contrasts, authority and table ranges can be weakened or misread. | Keep the unchanged text and source bytes, and add separately reviewable formatting-aware annotations and typed table rows. |
| High | Visible cross-references 84367 and 84494 do not lead to substantive target paragraphs; apparently related content is at 84357 and 84499. The six-digit reference 070880 also needs reconciliation. | Dependency traversal can miss required annuity, trust or location guidance. | Preserve the printed references and add labelled reconciliation candidates; do not silently correct them. |
| Medium | Appendix 1 is one unresolved flattened-text table record, separate from paragraphs 84911 and 84921–84924. | The threshold rule, account treatment and lookup rows are not retrievable as one calculation context; whitespace normalisation may corrupt ranges. | Link the raw table to typed rows and the calculation passage; keep the page 131 disclaimer outside the typed rows. |
| Medium | Reference parsing is incomplete: for example, 84352 has no structured references; 84353 loses all four Schedule V paragraph citations; 84921 retains only the first part of its citation; 84922 loses `R(PC) 3/08`. | Authority and dependency retrieval is incomplete even where the source text is preserved. | Parse and test complete footnote/citation spans while keeping legal applicability unresolved. |
| Medium | Several generated labels fall back to broad section names even when local headings are present, and the `Deemed weekly income` heading is attached to the end of 84923 rather than the start of 84924. | Discovery results are less precise and may describe the wrong local question. | Build discovery labels from validated local heading paths and logical passages. |
| Medium | PDF annotations are not dependable relationship evidence: repeated headings misroute and a spurious annotation is attached to the last digit of 84351. | Link-derived relationships can point to the wrong page or concept. | Resolve visible paragraph labels against the inventory and record, then validate targets separately. |
| Medium | Existing relationships and boundaries remain machine proposals with legal dependency and specialist review not established. | Structural convenience could be mistaken for current legal applicability or reviewed guidance. | Keep proposal, source, specialist-review and legal-applicability statuses explicit and separate. |

## Boundary of the finding

The pilot supports testing logical, dependency-aware source units against the current atomic units. It does not show that retrieval scores or answer accuracy have already improved, does not establish current legal applicability and does not support an individual entitlement decision.
