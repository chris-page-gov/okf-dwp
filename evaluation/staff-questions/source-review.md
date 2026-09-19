# Staff question source review

Reviewed on 19 September 2026 for the 21 September demonstration. This is an independent, unreviewed research assessment, not benefits advice, a legal answer key or an entitlement calculator.

## What this baseline measures

The [case registry](cases.json) retains all 40 supplied question occurrences in their original sections and exact wording. There are 39 distinct questions: `staff-026` and `staff-033` repeat the Child DLA/PIP question. Both occurrences remain in the evaluation. Related but differently worded questions also remain separate.

The approved remote service version is pinned to `efb05c66616a9cd4328a86cf412780fe7bc7cf0b`. Its Ask OKF index has 52 records, 127 assertions and six imprisonment-specific evidence requirements. This is much narrower than the acquired and searchable full DMG corpus: 331 PDF documents and 14,743 extracted pages. The presence of a source in that wider corpus does not mean it is available to this version of Ask OKF.

Local calls using all 40 exact questions and the unchanged assembly core returned `insufficient`, with no applicable declared evidence requirements and no default-budget truncation. Twenty-four questions resolved some generic concepts from the imprisonment profile; 16 resolved none. Generic benefit resolution does not demonstrate sufficient evidence for another subject.

The registry's expected insufficiency is a task-scope judgement supported by the missing evidence profiles and the reviews below. Exact diagnostic codes are regression expectations observed for this immutable index, not legal propositions or requirements for a future expanded index. Preserve this registry and its baseline receipts when assessing a broader projection; give the later projection its own binding and expectations.

## Candidate source evidence

The registry identifies 42 candidate pages across 14 captured documents. Each candidate has a stable semantic identifier and route, official PDF URL and page position, acquisition time, PDF hash, extracted-page-file hash, whole-page literal hash and an exact anchor. These identities and routes were checked against the frozen inventory, page files and full-DMG generated records.

`source_role` is the inventory's literal `role`; `source_classification` is its literal `discovery_classification`. They describe different source properties. A missing source publication date remains `null`; capture dates and listing updates are not substituted for publication or legal commencement dates.

Candidates are assessor material, not hidden retrieval seeds, verified answer passages or complete chains of authority. They identify useful material already captured while preserving gaps in extraction, qualifications, historical applicability and linked sources. No candidate is upgraded to specialist-reviewed or official project interpretation. The machine-extracted text may still damage tables, footnotes and reading order.

| Question area | Captured candidate material | Principal review boundary |
| --- | --- | --- |
| Travel and moving abroad | Chapter 7 parts 1 and 6 | Benefit, territory, temporary/permanent absence, duration, purpose and date need resolution. A common absence rule is not a rule for every benefit. |
| State Pension | Chapter 74, including its age table and transitional provisions | Pensionable age, entitlement, claim timing and first payment are distinct. New State Pension and earlier retirement-pension regimes must be separated. No individual entitlement date is calculated. |
| Pension Credit conditions and calculation | Chapters 77, 78, 84 and 85 | Guarantee Credit/Savings Credit, household, mixed-age protections, income/capital disregards and exceptions need connected evidence. A savings question must not assume a universal capital ceiling. |
| Pension Credit rates | Chapter 77 appendix pages 59–68; DMG memo 02/26 page 2 | The captured appendix contains historical 2021–2025 uprating periods. The 2026 memo is captured, but routes main benefit rates to a separate uprating schedule and desk aids. It is not a complete 2026/27 Pension Credit rate table. |
| Care-home scenarios | Chapter 78 page 25 and related household/housing passages | Base credit, disability/carer additions, housing, qualifying benefits, partner status and funding arrangements must be distinguished. “All scenarios” needs a bounded scenario inventory. |
| Disability and overlapping benefits | Chapters 17, 57, 60, 61 and 69 | PIP component and age/transition rules, exact allowance scheme, underlying entitlement and actual payment require separate evidence. SDA is ambiguous between Severe Disablement Allowance and an informal severe-disability additional-amount label. |
| Industrial injuries and pension age | Chapters 69 and 71 | IIDB, Reduced Earnings Allowance and Retirement Allowance are distinct. A pension-age rule for one cannot be silently transferred to another. Industrial Injuries Constant Attendance Allowance is not automatically the war-pension allowance. |
| Carer's Allowance | Chapter 60, plus Pension Credit and overlap candidates | A carer's award and its effect on the cared-for person's benefits differ. One carer caring for several people must be distinguished from several carers for one person. |

## Missing scope and evidence

- Full ADM and PIP source bodies are outside this DMG acquisition. Contemporary New Style JSA/ESA and PIP questions cannot be completed by silently treating a legacy DMG page as the whole applicable regime.
- “Last five years” lacks an agreed date anchor and calendar-year, tax-year or uprating-period definition. Current-period rate questions require the complete relevant dated schedules and all requested variants.
- Broad questions about “other benefits”, “how it works” and “all variations” need an explicit scope and evidence requirements before completeness can be assessed.
- Standalone questions must not silently inherit missing context. `staff-016` refers to “these inputs”; `staff-018` does not name Pension Credit in its question text even though it appears in that section.
- Source capture, semantic modelling, retrieval and answerability are separate. Additional material in the full DMG can improve context assembly while a package correctly remains insufficient for an unbounded or unresolved question.

The registry records source coverage, semantic coverage, retrieval, traversal, context assembly, provenance, boundaries and answerability separately for every case. No legal entitlement answer or award calculation has been supplied. A future review should assess the actual returned evidence against those requirements, not merely check for keywords or a larger record count.
