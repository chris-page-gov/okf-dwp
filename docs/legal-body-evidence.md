# Statutory body evidence for Pension Credit household questions

The project now retains **20 complete selected statutory units from 16 provisions**, linked to staff questions 012, 013, 014, 017, 018 and 020. Previously, the legal reconciliation supplied identifiers and metadata, without the statutory wording. This additive increment supplies inspectable wording and 43 navigation relationships. It does **not** establish a complete legal answer, current applicability or specialist acceptance. This remains an independent experimental publication, not an official DWP document.

## Start with the distinction

A **statute** is legislation. An Act contains sections; regulations commonly contain regulations and schedules. A **provision** is a particular part of that legislation. The Department for Work and Pensions (DWP) **Decision makers’ guide (DMG)** explains departmental decision-making and cites legislation, but guidance and legislation remain different sources.

A **body extract** here contains the complete selected numbered unit: for example, regulation 5, rather than one sentence containing “care home”. Numbering, conditions and exceptions remain in the text. Its **provenance** records where it came from, the requested source version and the capture time. A **hash** is a digital fingerprint used to detect a changed file or passage; it does not establish that an interpretation is legally correct.

Follow this learning path:

1. Read the exact staff question and its ambiguities in [the coverage report](../domain-profile/legal-bodies/coverage.json).
2. Follow a DMG citation to the selected statutory unit. A navigation relationship means “inspect this source”; it does not mean “this rule necessarily applies”.
3. Inspect the full numbered wording, its headings and the original official link. Inspect the retained structured projection for amendment markers, commentary and restriction attributes.
4. Check the unresolved requirements before attempting an answer. Keep questions about the whole Pension Credit award separate from questions about an additional amount or payment of a qualifying disability benefit.

## What was acquired

The following official links request the version for **20 September 2026**. That is a requested point-in-time version, not an inferred publication or commencement date. Acquisition receipts record 20 September 2026 in UTC. The `2026-09-21` directory name identifies the Monday workstream and is not an assertion that acquisition occurred on that date.

| Official source | Complete selected units | Why inspect it |
| --- | --- | --- |
| [State Pension Credit Act 2002](https://www.legislation.gov.uk/ukpga/2002/16/2026-09-20) | Sections 1, 2, 3, 4 and 15 | The supplied questions cite entitlement, credit components and financial concepts. |
| [State Pension Credit Regulations 2002, regulation 5](https://www.legislation.gov.uk/uksi/2002/1792/regulation/5/2026-09-20) | Regulation 5 | Household treatment and conditional mixed-age routes. |
| [Schedule I](https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/2026-09-20) | Paragraphs 1 and 2 | Severe-disability conditions and associated household provisions. The no-partner and partner branches must remain distinct. |
| [Schedule II](https://www.legislation.gov.uk/uksi/2002/1792/schedule/II/2026-09-20) | Paragraphs 1, 3, 4 and 5 | Housing-cost conditions, occupancy, liability and temporary absence. These are not a statement that the whole Pension Credit award ends. |
| [Schedule III](https://www.legislation.gov.uk/uksi/2002/1792/schedule/III/2026-09-20) | Paragraph 1 | The source heading is “Special groups”; the selected paragraph concerns polygamous marriages. It is not a capital-disregards schedule. |
| [State Pension Credit Regulations, regulation 1](https://www.legislation.gov.uk/uksi/2002/1792/regulation/1/2026-09-20) | Regulation 1 | Interpretation context, selected by the project and identified as additional context. |
| [Regulation 6](https://www.legislation.gov.uk/uksi/2002/1792/regulation/6/2026-09-20), [regulation 8](https://www.legislation.gov.uk/uksi/2002/1792/regulation/8/2026-09-20) and [regulation 15](https://www.legislation.gov.uk/uksi/2002/1792/regulation/15/2026-09-20) | Regulations 6, 8 and 15 | Component and financial context cited or explicitly routed from selected sources. |
| [Social Security Administration Act 1992, section 1](https://www.legislation.gov.uk/ukpga/1992/5/section/1/2026-09-20) | Section 1 | The frozen DMG claim-requirement citation. |
| [Housing Benefit Regulations 2006, regulation 12](https://www.legislation.gov.uk/uksi/2006/213/regulation/12/2026-09-20) | Regulation 12 | The separate Housing Benefit citation on the housing-cost guidance page. |
| [Universal Credit Regulations 2013, regulation 3](https://www.legislation.gov.uk/uksi/2013/376/regulation/3/2026-09-20) | Regulation 3 | A destination explicitly referenced in Pension Credit regulation 5. |

The resulting normalised statutory text contains 93,953 characters. Twelve units have **no observed extent attribute** in the selected unit or its ancestors: their territorial scope remains unknown. The other eight preserve the observed attributes without treating them as a complete applicability assessment. Full restriction attributes, commentary identifiers and the exact projected XML trees remain in the source files.

The producer creates four explicit, source-checked statutory navigation routes: regulation 5 to Universal Credit regulation 3; Schedule I paragraph 1 and Schedule II paragraph 1 to regulation 6; and Schedule II paragraph 5 to paragraph 4. It verifies each retained literal anchor. It does not infer legal applicability from a matching keyword. Regulation 1 is retained as additional interpretation context but has no incoming navigation edge in this overlay; its acquisition does not guarantee its selection by Ask OKF.

Schedule-level DMG citations are labelled as links to **selected paragraph context**, not as exact mappings of every cited subparagraph. The source-citation text is retained verbatim. In particular, the literal `SPC Regs, s 5` and `s 12(2)(d)` remains unresolved: acquiring regulation 5 does not correct that citation or silently substitute a different Act.

## Source retention and rights

Two new snapshots preserve the acquisition sequence:

- [First attempt](../source/legal-bodies-2026-09-21/manifest.json): 18 requests, comprising 16 provision XML requests and two rights checks. Thirteen projections failed the local opaque-identifier publication guard. Their failure receipts remain failed; three provision projections succeeded.
- [Corrected attempt](../source/legal-bodies-2026-09-21-v2/manifest.json): 13 fresh provision requests after a documented projection correction, with the three successful provision projections and two rights observations reused byte for byte. All 20 selected units are present. There were no automatic retries.

Before these declared acquisitions, six bounded preflight requests occurred: three successful XML probes, two successful rights probes and one 404 from an obsolete copyright URL. The preflight note is explicit, but those probe bodies are not the retained public acquisition evidence. There were 31 requests in the two retained acquisition censuses. Each response had an 8 MiB read limit and the request count was bounded. The acquisition script checked its 64 MiB total-response threshold after the parallel responses completed: that threshold controls publication, not a hard aggregate transfer ceiling. The corrected attempt observed about 1.01 MB of response bodies; no further requests were needed.

The official [regulation 5 page](https://www.legislation.gov.uk/uksi/2002/1792/regulation/5/2026-09-20) footer states that content is available under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/), except where otherwise stated. Selected footer and licence text, acquisition receipts and limitations are retained under `rights/`. Attribution is retained. Source-specific exceptions still apply; no logos or third-party material are intentionally selected.

The public projection is deliberately **lossy**. It retains selected complete XML subtrees and their normalised text, referenced editorial commentary, metadata and omitted-attribute digests. Opaque effect/change identifiers and key-shaped source identifiers are excluded. Key-shaped commentary references are represented by explicit SHA-256 identifiers so the relationship can be inspected without publishing those opaque source values. The first attempt's failure was preserved and corrected; no secret-scanner bypass was used.

Original HTTP response bytes were hashed during acquisition but are **not retained publicly**. Offline checks can verify the retained projection and reproduce its text; they cannot reconstruct or independently replay the original HTTP byte stream. Editorial commentary and amendment markup remain distinguishable from the normalised operative-unit text. Whitespace and inline presentation are flattened in the text view. Independent structural review found six punctuation-only `AppendText`/`Addition` fragments outside recognised text blocks in Schedule III paragraph 1: the full tree retains them, while the normalised block-text view omits them. No substantive qualification loss was identified by that review; it is not specialist legal acceptance. An empty effects list is not evidence of a complete amendment history.

## What remains unresolved

All six cases continue to report `evidence_status: insufficient`. The technical acquisition milestone is complete within the declared bounds; legal acceptance remains pending.

- The cited **R(IS)1/99** judgment body has not been acquired. The treatment of both partners in care must not be reduced to an unqualified rule from one statutory sentence.
- Qualifying-benefit continuation or cessation, all funding arrangements, transitional protections and every cross-reference are not a closed dependency set.
- Version, commencement, amendment completeness and territorial applicability require reconciliation and specialist review. A requested date and a captured XML attribute do not settle these questions.
- The differing “carer support component” and “carer support payment component” wording reported in DMG memo 01/26 remains a reconciliation question; this acquisition does not silently correct departmental wording.
- The scope of “all scenarios”, household facts, ages, award dates, funding and qualifying-benefit payment remain unresolved. No claimant information is requested and no individual entitlement decision is made.

See [the household evidence expansion](household-evidence-expansion.md) for the accompanying conditional guidance concepts. Acquiring these statutory bodies does not remove or satisfy the existing specialist-review obligations.

## Reproduce and integrate

The implementation adds files without rewriting the existing metadata-only legal records, frozen DMG/ADM releases or previous model trials.

```sh
uv sync --locked
uv run --locked python scripts/build_legal_body_evidence.py --check
uv run --locked python -m unittest discover -s scripts -p test_legal_body_evidence.py -v
```

The offline producer verifies source manifest censuses, hashes, acquisition-script identities, reused projections, full text/tree equality, frozen citation-page hashes, literal citation inclusion, question wording and routing anchors. It rejects unresolved selected units rather than emitting them as complete. Checks make no network requests. The acquisition script requires explicit `--acquire` and refuses to overwrite its destination; any further acquisition needs a new named snapshot and an explicit bounded request plan.

Integration uses [context-overlay.json](../domain-profile/legal-bodies/context-overlay.json), with runtime-compatible `records` and `assertions`, source bindings and limitations. Every new record and relationship is `normalized` with `derived` authority and an HTTPS authority source; its label identifies the official origin and unreviewed extraction. Existing engine authority rules remain unchanged. [evidence.yamlld](../domain-profile/legal-bodies/evidence.yamlld) contains both direct navigation triples and their provenance-bearing reified statements; [coverage.json](../domain-profile/legal-bodies/coverage.json) records the granular source and question census. The root integration work must explicitly consume this overlay; simply generating it does not deploy it to Ask OKF.
