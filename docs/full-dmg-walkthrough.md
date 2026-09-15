# Full DMG research walkthrough

This is an independent, unofficial research exemplar. It demonstrates source navigation and inspectable semantic proposals, with visible uncertainty. It does not make benefit decisions.

## Prepare

Open the immutable candidate in Explorer: [JSON entry](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F80b6f08426aea39dd2934fb8795b61215e2cc0ad%2Ffull-dmg%2Fokf-explorer.json&q=84351&view=narrative#page/84/0035) or [YAML-LD entry](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F80b6f08426aea39dd2934fb8795b61215e2cc0ad%2Ffull-dmg%2Fokf-explorer.yamlld&view=narrative#page/84/0035). Both name content commit `80b6f08426aea39dd2934fb8795b61215e2cc0ad`, snapshot `dwp-full-dmg-2026-09-15-2dd78242297c`.

Use a desktop browser and allow the first index and selected record to load. The [preserved Pension Credit walkthrough](meeting-walkthrough.md) is a smaller alternative for the original meeting journey. Publication and canonical CI history are tracked in [PR 5](https://github.com/chris-page-gov/okf-dwp/pull/5); the immutable browser receipt applies to the content commit above.

## Ten-minute demonstration

1. **Find a familiar passage.** Search `84351`. Open chapter 84, PDF page 35 in Narrative. Read the machine-extracted paragraphs 84351–84353 and use **Verify the original PDF page 35** to compare them with the source. Page numbers refer to the captured PDF; hashes identify the exact evidence. The direct PDF link remains available even if the separately loaded Evidence Sources tab initially shows zero sources.
2. **Show what wider coverage changes.** Switch the `84351` search to Resources. The checked view returned six labelled PDF resource groups, including chapter and historical material. Read the source role before treating a result as applicable. Search `reversionary` to find text beyond short result snippets: the checked view returned 24 results, including this page. Acquisition covers 331 PDFs and 14,743 pages; it does not establish current law.
3. **Inspect a proposed relationship.** Open the [ESA exceptional limited capability for work risk Graph](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F80b6f08426aea39dd2934fb8795b61215e2cc0ad%2Ffull-dmg%2Fokf-explorer.json&view=graph#term/esa-exceptional-lcw-risk). The checked view had 11 nodes and 10 relationships with human labels. Follow the related evidence-assessment concept and inspect the exact DMG 42320 passage, source locator and hashes. Distinguish a model-authored association from deterministic page containment and from DWP's own text. The proposal remains unreviewed by a specialist.
4. **Check provenance dates.** Open the [CPAG Timeline](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F80b6f08426aea39dd2934fb8795b61215e2cc0ad%2Ffull-dmg%2Fokf-explorer.json&view=timeline&q=CPAG#resource/cpag-welfare-benefits-handbook). The nine matching records include the referenced handbook's April 2026 publication month, separately from September project observation. Month precision remains month precision. The other eight matching records explicitly label their catalogue timestamp fallbacks. This is metadata navigation, not a legal applicability timeline or access to handbook text.
5. **Show a limitation honestly.** Open the [source-family research gap register](../evaluation/full-dmg-source-family-review.json): Annex M page 43 contains a diagram that extraction omitted; Memo 14/25 includes citations the automated recogniser missed. Neither zero extracted text nor zero recognised citations proves the source is empty. Across the full capture, 802 pages have no extracted text; there has been no exhaustive visual review or OCR.
6. **Inspect an answer trial.** Open the [recorded trial summary](../evaluation/full-dmg-behavioural/summary.json), then an original answer and its separate assessment. There are 160 retained answers: 90 categorised as supported, 56 partial and 14 with underspecified rubrics. These context-aware, source-guided model judgements are not an accuracy score, a blind end-to-end retrieval benchmark or specialist acceptance. Read an omission rather than hiding it.

## Search and Graph limits

Read the displayed query interpretation. In the public check, `unavailableclaimantdetails` expanded to the indexed term `unavailable` and returned seven results. The nonsense control `zzzxqvnomatch` returned an unmatched term and no results. Exact Python retrieval controls do not establish identical browser search behaviour.

Graph membership views are bounded. The checked Concept facet showed 200 loaded records out of 271 exact index matches. Do not describe that view as the complete semantic graph. Source acquisition, authored relationships and specialist acceptance are different coverage measures.

## For staff and advisers

The useful next review is concrete: check a concept's definition, source scope, exceptions, dates and relationship evidence; identify the required correction and expected answer to a persona's question. Record disagreement without overwriting the original evidence. Specialist acceptance is currently zero.

The wider legislation catalogue supplies navigation references. Provision versions, effects and applicability still need reconciliation. CPAG remains public metadata and links; subscription-body processing needs the publisher's written permission. The separate 182-PDF ADM census remains metadata discovery and is outside this full-text corpus.

## What this session proves

The [public browser receipt](../validation/full-dmg-browser.json) names the exact producer commit, consumer revision and journeys checked in Edge. It records both entry formats, source navigation, selected relationships and labels, CPAG's Timeline, bounded search controls and final desktop visual inspection, with no captured warning or error logs. It proves only those observations, not every interaction or comprehensive accessibility. The source and semantic validators cover broader mechanical integrity, with separate model-trial records. The [repository status](../REPOSITORY_STATUS.md) tracks PR promotion independently.

Website tools, live WebMCP invocation, ChatGPT live voice and the MacBook-to-PA audio path require a separate seminar rehearsal. Loading this bundle does not itself provide those integrations.
