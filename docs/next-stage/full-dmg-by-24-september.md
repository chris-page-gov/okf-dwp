# Full DMG exemplar by 24 September 2026

## Proposed outcome

Aim for a source-complete, navigable experimental OKF+ of the DMG collection by Thursday 24 September 2026, with an explicit route to ADM where DWP says it applies. Separate coverage of acquired source material from coverage of reviewed meaning. A complete source inventory can coexist with unresolved extraction, temporal or legal questions; those questions must remain visible.

This is a proposed delivery plan based on a metadata census, not a commitment that all policy can be encoded or reviewed by that date. It does not authorise an entitlement engine or change the current demonstration's assurance status.

## What the official sources say

The [DMG collection](https://www.gov.uk/government/collections/decision-makers-guide-staff-guide) presents guidance for DWP staff making benefit and pension decisions. It directs decision makers to ADM for Universal Credit, Personal Independence Payment and contribution-based Jobseeker’s Allowance and Employment and Support Allowance for people eligible for Universal Credit. The [ADM publication](https://www.gov.uk/government/publications/advice-for-decision-making-staff-guide) confirms that division and points to DMG for the remaining cases.

The [DMG memos publication](https://www.gov.uk/government/publications/decision-makers-guide-memos-staff-guide) uses the labels New Style Jobseeker’s Allowance and New Style Employment and Support Allowance. Preserve the source terminology and model its relationship to the collection's wording explicitly; a shared abbreviation or a benefit name alone is insufficient to select applicable guidance.

The [Universal Credit eligibility guide](https://www.gov.uk/universal-credit/eligibility) is claimant-facing information. It is useful evidence for journey discovery, including mixed-age couples and the relationship between a Universal Credit claim and Pension Credit. It is not a complete decision specification. Keep it separate from staff guidance and retain a dated link to the relevant section.

These are relationships stated by the official publication pages. They do not establish that all related legislation, case law, operational processes or evidence requirements have been captured.

## Measured metadata scope

**Acquisition update, 15 September 2026:** all 331 DMG PDFs have now been acquired and verified, measuring 14,743 pages. [Acquisition evidence and extraction gaps](full-dmg-acquisition.md) supersede the acquisition status in the original census planning text below. The source denominator and the original metadata receipts are unchanged.

The [frozen census](../../source/discovery-2026-09-15/census.json) records all direct members of the DMG collection at `2026-09-15T16:55:17.923154Z` to `2026-09-15T16:55:18.464057Z`: **11 publication pages, 14 volumes and 331 unique PDF URLs**. GOV.UK declares **14,743 PDF pages**. These are publisher metadata counts; the new PDFs have not been acquired or measured. Each of the 14 API responses, including the collection and the two contextual sources, has a URL, timestamp and SHA-256 in the [receipts](../../source/discovery-2026-09-15/receipts.json).

| Publication grouping | PDFs | Declared pages |
| --- | ---: | ---: |
| [Volume 1: decision making and appeals](https://www.gov.uk/government/publications/decision-makers-guide-vol-1-decision-making-and-appeals-staff-guide) | 20 | 1,063 |
| [Volume 2: international subjects](https://www.gov.uk/government/publications/decision-makers-guide-vol-2-international-subjects-staff-guide) | 21 | 1,449 |
| [Volume 3: common subjects](https://www.gov.uk/government/publications/decision-makers-guide-vol-3-subjects-common-to-all-benefits-staff-guide) | 25 | 1,134 |
| [Volumes 4 to 7: JSA and Income Support](https://www.gov.uk/government/publications/decision-makers-guide-vols-4-5-6-and-7-jobseekers-allowance-and-income-support-staff-guide) | 68 | 4,251 |
| [Volumes 8 and 9: ESA](https://www.gov.uk/government/publications/decision-makers-guide-vols-8-and-9-employment-and-support-allowance-staff-guide) | 40 | 2,752 |
| [Volume 10: incapacity, disability, maternity and bereavement](https://www.gov.uk/government/publications/decision-makers-guide-vol-10-benefits-for-incapacity-disability-maternity-and-bereavement-staff-guide) | 21 | 618 |
| [Volume 11: industrial injuries](https://www.gov.uk/government/publications/decision-makers-guide-vol-11-industrial-injuries-benefits-staff-guide) | 20 | 815 |
| [Volume 12: pensions](https://www.gov.uk/government/publications/decision-makers-guide-vol-12-pensions-staff-guide) | 10 | 566 |
| [Volumes 13 and 14: Pension Credit](https://www.gov.uk/government/publications/decision-makers-guide-vols-13-and-14-state-pension-credit-staff-guide) | 36 | 1,524 |
| [DMG memos](https://www.gov.uk/government/publications/decision-makers-guide-memos-staff-guide) | 66 | 534 |
| [DMG abbreviations and references](https://www.gov.uk/government/publications/decision-makers-guide-abbreviations-staff-guide) | 4 | 37 |
| **DMG total** | **331** | **14,743** |
| [ADM, separately](https://www.gov.uk/government/publications/advice-for-decision-making-staff-guide) | **182** | **4,347** |

The existing Pension Credit acquisition covers 36 of the 331 DMG PDF URLs. If those URLs and bytes remain unchanged, the remaining direct DMG inventory is **295 PDFs**, with **13,219 publisher-declared pages**. Reuse of the existing snapshot still requires identity checks against the refreshed manifest.

The 261 volume PDFs break down by title as follows:

| Planning class | PDFs | Declared pages | Treatment |
| --- | ---: | ---: | --- |
| Listed substantive chapter files | 78 | 8,097 | Main discovery view, with unreviewed status |
| Transitional chapter files | 3 | 88 | Explicit applicability and temporal review |
| Spare chapter files | 11 | 11 | Accounted for in inventory, no invented content |
| Annex files | 4 | 71 | Inspect as potential substantive content |
| Amendment records | 151 | 5,849 | Version evidence; do not flatten into chapter text |
| Change summaries | 14 | 56 | Administrative change evidence |

Chapter 7 is split into seven PDFs, so file counts are not chapter counts. The other 70 DMG PDFs comprise 66 memos, one abbreviation list, two legislative abbreviation lists and one change summary. A memo may still apply: its age alone cannot establish supersession. The 182 ADM PDFs are a separate family, comprising 97 chapter files including spare and transitional chapters, 13 annexes including spare annexes, 69 memos and three reference or change documents. Neither family's reference lists amount to acquisition of the legislation itself.

## Delivery sequence

These checkpoints are proposed dates. Review capacity and measured extraction quality determine promotion at each checkpoint.

| Date | Work | Reviewable result and exit gate |
| --- | --- | --- |
| 15 to 16 September | Agree what “full DMG” means, freeze the manifest and select policy-review owners. Confirm the DMG/ADM routing boundary and whether any ADM subset is required for the first demonstration. | Every collection member and attachment accounted for; source classes and exclusions explicit; no claim of full ADM coverage. |
| 16 to 18 September | Acquire the remaining DMG PDFs with bounded parallel workers. Record hashes, byte lengths, measured page counts, HTTP failures and redirects. Extract page text and identify tables, diagrams and reading-order risks. | The 331-file denominator reconciles to successful acquisitions or named failures. Source completeness is claimed only when all are acquired and hashes verified. |
| 18 to 20 September | Build the cross-benefit concept and source-navigation layer. Prioritise common decision-making, evidence, international and household topics alongside Pension Credit. Preserve page and paragraph locators. | Every authored relationship has source evidence, scope and review status. Terms shared across benefits do not imply identical rules. |
| 20 to 22 September | Map amendment, memo and legislation references. Separate publication dates, source revision dates, stated effective dates and unresolved applicability. Populate personas, questions and counterexamples against the mapped corpus. | No undated rule promoted as current. Any unresolved supersession or source conflict is surfaced in retrieval and recorded for expert review. |
| 22 to 23 September | Run source, semantic, retrieval, accessibility and Explorer checks. Review representative and known-risk source pages, including tables and examples. Re-census publication metadata to identify changes since acquisition. | Exact candidate bytes pass reproducibility and schema checks; retrieval citations resolve; omissions and source drift are explicit; a reviewed demonstration route works in the browser. |
| 24 September | Freeze the assured content/site candidate for the 30 September seminar and publish coverage, gaps and review status. | Source completeness, semantic coverage and human-review coverage are reported separately. The official-source/unofficial-interpretation boundary is visible throughout. |

Full ADM acquisition is a separate expansion: it adds 182 PDFs and 4,347 declared pages to the plan. Capture the routing boundary and selected cross-benefit references now; do not silently turn a full-DMG milestone into a full-DMG-plus-ADM promise.

## Acceptance gates

1. **Source accounting:** every direct DMG attachment has a stable identity and a recorded acquisition outcome; unique-URL counts reconcile with the frozen census. Source refreshes create new snapshots instead of rewriting old evidence.
2. **Extraction fidelity:** original PDFs remain available; page totals reconcile; empty extraction, broken spacing, list numbering, formulae, tables and reading order are flagged. Corrected text is a separately attributed derivative. Known material errors are excluded from rule inference until resolved.
3. **Authority and time:** guidance, statutory references, judgments, claimant information and authored interpretation remain distinct. Old memos are assessed for applicability rather than discarded by date. Publication time is not substituted for the legal effective date.
4. **Semantics:** stable identifiers, pinned contexts and the existing OKF 0.2 plus additive Bundle Wiki profile are used. YAML-LD and generated projections agree; every assertion is evidence-bearing and its review status is preserved.
5. **Retrieval and evaluation:** each persona's questions have expected evidence sets and explicit no-answer conditions. Cross-benefit ambiguity, historical-only matches, missing source content and opposing examples are tested. Answers point to the original source and page rather than presenting an inferred award.
6. **Publication:** the candidate is reproducible, its exact files are browser-checked and the review record names what was and was not reviewed. The independent experimental notice remains visible. A full corpus does not imply a validated benefits engine.

## Material gaps and decisions

- **Policy review capacity:** identify people who can review terminology, applicability and selected rule interpretations. Agent self-review is not a substitute for a named expert decision.
- **Fraud, error and operational evidence:** discover these requirements separately with the service team; staff guidance alone does not define the complete application or change-of-circumstances journey.
- **Legislation and case law:** enumerate cited instruments and judgments, resolve authoritative locations and record version/applicability before treating them as acquired dependencies. Legislative abbreviation lists are navigation aids.
- **Memo and amendment status:** the metadata census does not establish whether an amendment is incorporated or a memo remains operative. Old-looking guidance may still be relevant to historical cases.
- **Source-date coverage:** CPAG is currently the only runtime record with an explicit structured publication date. Map each DMG document's advertised publication or revision date to its supporting source statement, retaining month/year precision where applicable. Keep collection-page updates, source dates, capture and record generation separate; labelled fallback dates in Timeline do not establish publication or legal applicability.
- **Extraction scale:** publisher metadata does not reveal scanned pages, table complexity or the cost of recovering malformed text. Measure these after acquisition and revise the schedule from the evidence.
- **Large-bundle behaviour:** a corpus of this size needs measured search, loading and graph-navigation performance. Decide between one bundle and a navigable family of bundles after profiling the generated content. The current Timeline correction covers Explorer's small-bundle path; verify date roles and precision separately if the wider corpus uses the indexed path.
- **Jurisdiction and benefit regime:** record geographical scope and the DMG/ADM applicability boundary explicitly. Do not assume similarly named legacy and New Style benefits share a rule set.
- **External adviser material and calculator evaluation:** retain these as independently scoped work, with access and reuse terms established before acquisition. They are not part of the 331-PDF DMG denominator.

## Reproduce the planning evidence

```sh
python3 source/discovery-2026-09-15/acquire_metadata.py --check
```

The command validates frozen HTTP-response hashes and byte-for-byte census reproduction without network access or new dependencies. It does not build the bundle or validate unacquired PDFs. The [census README](../../source/discovery-2026-09-15/README.md) documents the classification method, source licence and exact metadata digest.
