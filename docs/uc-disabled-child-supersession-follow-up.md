# A new UC question: finding the rule is not deciding the award

This is an anonymised, out-of-sample follow-up to the [40-question Evidence workbench](evidence-workbench.md). The [case and observed replay](../evaluation/out-of-sample/uc-disabled-child-supersession-001.json) are separate from its frozen registry and packages. No claimant details, model answer or new source acquisition were used.

## What the question asks

A child is said to have the highest care rate of Disability Living Allowance (DLA) from 26 January 2025. Universal Credit (UC) is told on 28 March 2026. The question asks when the *higher disabled-child addition* takes effect and which UC assessment period should include it. An assessment period is the monthly window used for a UC award. The question does **not** give that window's start and end dates.

**ADM** means *Advice for decision making*, DWP's staff guidance. Its codes identify numbered paragraphs: A4361 is in Chapter A4. **Supersession** means replacing an existing benefit decision because a relevant ground for changing it applies; the applicable rule determines when the replacement takes effect. Everyday terms such as “backdating” do not identify that rule by themselves.

The retained [ADM F1, F1123, PDF page 18](https://assets.publishing.service.gov.uk/media/6a86fe84c9205b515d421f44/adm-ch-f1-child-element.pdf#page=18) says the highest DLA care rate is a condition for the higher addition. [ADM A4, A4361, PDF page 36](https://assets.publishing.service.gov.uk/media/6a2172db56e988a798b38645/adm-ch-a4.pdf#page=36) gives a distinct UC effective-date branch where a claimant or family member becomes entitled to another relevant benefit or its rate changes: the first day of the assessment period containing that other-benefit change. [A4352, PDF page 34](https://assets.publishing.service.gov.uk/media/6a2172db56e988a798b38645/adm-ch-a4.pdf#page=34) expressly points from the ordinary late-notification branch to A4361 as an exception. A4361's DLA example concerns the *carer element*, so it is an analogy, not a decision about this addition.

**Conditional reading:** if the highest-rate DLA entitlement legally starts on 26 January 2025, the child qualifies within the claimant's UC family, and A4361 governs this change, the effective date would be the **first day of the assessment period containing 26 January 2025**. The higher addition would be considered from that assessment period. Without its boundaries, an exact calendar start date or named payment period is unknown. Whether the award and any retrospective payment should actually change needs the governing legislation, facts and specialist review; this page does not decide it.

## What the current system did

The retained 19 September ADM A4 PDF has SHA-256 `4933d66a…58a8e8`; F1 has `124b7e41…5b8731`. Their exact local pages and stable passage IDs are in the [case record](../evaluation/out-of-sample/uc-disabled-child-supersession-001.json). The A4 text was also checked against the [official PDF](https://assets.publishing.service.gov.uk/media/6a2172db56e988a798b38645/adm-ch-a4.pdf) on 24 September 2026. The F1 web URL could not be opened in that check; its retained PDF was available locally. These are official guidance sources, while the extracted text and passage boundaries are unreviewed project projections.

One file-backed, hash-checked replay of the unchanged source and Explorer engine used the same 512 KiB/64-record/128-relationship/depth-6 limits as the workbench. It selected **F1123** but missed **A4361**, **A4352** and F1120. It returned `insufficient`, used 522,141 bytes and reported query, candidate and resource budget omissions. It also attached the unrelated frozen Staff 008 requirement about a different benefit. This measures retrieval and task routing, not whether an AI could give a correct legal answer.

To repeat that **historical observation** with a local Explorer checkout whose
context-engine hashes match the case record, run:

```sh
node scripts/replay_uc_supersession_case.mjs --explorer-root /path/to/pinned-okf-explorer
```

The script reads only declared local source shards, verifies their bytes and
hashes, makes no model or network calls, and checks the retained result. A later
repair should have a new comparison receipt; it should not rewrite this failed
baseline.

The question still needs the UC assessment-period dates, the actual start of the highest DLA care entitlement, responsibility for the child, any earlier notifications and intervening decisions, jurisdiction and applicable legal version. ADM A4361 cites the 2013 Decisions and Appeals Regulations, Schedule 1 paragraph 31; F1123 cites UC regulation 24. Those statutory bodies were not in the retained local legal-body set, and the live legislation.gov.uk requests returned HTTP 429 in this investigation. They remain a verification task rather than a silently supplied rule.

## Next evaluation gate

Keep this observed miss intact. Add a versioned source-led route only after reviewing the statutory and guidance dependencies; then replay this case and separately frozen new phrasings with wrong-rate, wrong-family, changed DLA date and ordinary-late-rule controls. Measure passage selection, exact source spans, exception delivery, unknown dates and unrelated task activation separately. Keep `insufficient` and no individual award claim until a specialist accepts the full rule and applicable facts. The [BL007 evidence-profile work](backlog-work-packages.md#dwp-bl-007-broader-semantic-modelling-task-specific-evidence-profiles), [BL006 legal reconciliation](backlog-work-packages.md#dwp-bl-006-legislation-regulations-and-case-law-reconciliation) and [BL025 workbench review](backlog-work-packages.md#dwp-bl-025-evidence-workbench-and-all-question-inspection) remain the appropriate open gates.

## Separate leads: Demo 2 and hospital coverage

A separate public [Demo 2 overview](https://github.com/bitsls2/ai-demo/blob/main/demo-2-overview.md) describes a Pension Credit application concept with CASA and eventual submission through tools. The current workbench only inspects evidence and exports an unreviewed local proposal. A small next demonstration would use **fictional** form details to link a few [PC1/PC1H questions](https://www.gov.uk/government/publications/pension-credit-claim-form--2) to their source passages in a local preview. It would not collect details or submit a claim.

The four-benefit hospital question is another, separate lead. It is [outside the 40-case catalogue](../evaluation/evidence-workbench/manifest.json) and has a [retained remote Ask OKF case](../evaluation/remote-mcp/hospital-case.json). The [hospital coverage review](remote-mcp-hospital-coverage.md) records hospital source candidates beyond that tested index. Its existing result was `insufficient` with no answer. The cited [ESA Regulations 2013, regulation 21](https://www.legislation.gov.uk/uksi/2013/379/regulation/21) has **not** been acquired into the frozen legal-body evidence; regime, version and application remain unverified. The retained remote context was 444,815 bytes and reported `truncated: false`. A report that a browser tool response looked truncated is a different claim: no exact WebMCP call, cursor, page count or browser receipt was available to verify it. Inspect source coverage and delivery independently before changing either.
