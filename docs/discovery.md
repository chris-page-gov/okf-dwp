# Pension Credit staff-guide discovery

**Exploratory — independent and unofficial.** This is a public research demonstration by Chris Page, prepared on 15 September 2026. It is not an official DWP document, a benefits service, legal advice or an entitlement calculator. Check the cited official sources. The source collection contains historical material, and machine extraction can introduce errors.

## Mandate and boundary

The owner requested an OKF+ exemplar of the [Decision makers’ guide, volumes 13 and 14](https://www.gov.uk/government/publications/decision-makers-guide-vols-13-and-14-state-pension-credit-staff-guide), using YAML-LD and the existing OKF Explorer discovery-before-build prompts, for a 4pm meeting with a pensions representative. The owner explicitly authorised parallel document processing and a public repository under `chris-page-gov`.

This authorisation supports an experimental publication. It does not supply independent domain review, imply DWP endorsement or turn planned validation into a completed production release. The [machine-readable domain profile](../domain-profile/domain-profile.yaml) is deliberately **draft**.

The method follows the Explorer [domain warm-up](https://github.com/chris-page-gov/okf-explorer/blob/167d54dd924ce496f173105a8b390744b3b2a311/docs/prompts/okf-domain-warm-up.md) and [bundle-build prompt](https://github.com/chris-page-gov/okf-explorer/blob/167d54dd924ce496f173105a8b390744b3b2a311/docs/prompts/okf-bundle-build.md). Their exact file digests and the inspected Explorer commit are in the [consumer lock](../domain-profile/consumer-lock.json). The time-bounded build is an explicit exploratory exception to the full approved-profile Foundry handoff; it must not be described as having passed that complete process.

## What is in this snapshot?

The boundary is the PDF attachment list on one named GOV.UK publication page, observed on 15 September 2026. The page was first published on 1 June 2013 and records its most recent update as 20 July 2026. DWP describes the material as guidance for staff making benefits and pensions decisions and publishes it to explain how decisions are made. The page also distinguishes this guide from Advice for decision making used for specified other benefits. [DWP publication page](https://www.gov.uk/government/publications/decision-makers-guide-vols-13-and-14-state-pension-credit-staff-guide)

The acquisition census reports:

| Source role | Documents | PDF pages | Treatment |
| --- | ---: | ---: | --- |
| Substantive chapter documents | 7 | 744 | Searchable source guidance, still subject to temporal context |
| Transitional chapter | 1 | 14 | Preserve transitional role |
| Spare chapters | 2 | 2 | Preserve the source-labelled placeholders |
| Volume change summaries | 2 | 7 | Describe changes; do not treat as complete replacement chapters |
| Historical amendments | 24 | 757 | Clearly distinguish from chapter guidance |
| **Total** | **36** | **1,524** | **One document per named PDF attachment** |

The [source inventory](../source/inventory.json) records all 36 successful acquisitions, 23,475,769 PDF bytes and 2,752,384 extracted characters. The exact acquisition receipts and individual PDF digests provide the evidence; these are not estimated totals. A paragraph or passage created by extraction is a **derived evidence unit**, not an additional source document.

The corpus boundary excludes other DMG volumes, separately published memos, the whole body of amending legislation and case law, and claimant case records. External law and standards links in this discovery are references, not silently added corpus material. A complete census of these attachments does not establish completeness of pension law or all relevant DWP guidance.

## Why this is a demanding collection

1. **Temporal layers coexist.** The same landing page links chapter documents, summaries and historical replacement pages. An old amendment can repeat a paragraph that also appears in a newer chapter. Neither repeated text nor a shared paragraph number proves two versions are interchangeable.
2. **Legal citations are compact.** Chapter text can refer to Acts, regulations, schedules, DMG paragraphs and memos through abbreviated references. Preserve the original citation before resolving it; record unresolved targets.
3. **PDF structure carries meaning.** Footnotes, numbered lists, tables and printed paragraph identifiers can be separated by extraction. Keep the PDF link and page locator alongside the extracted text.
4. **Document dates differ from rule dates.** Acquisition time, page update time, labelled amendment time and commencement/effective dates are separate fields. None substitutes for the others.
5. **Source authority differs from project interpretation.** The DWP guide is official departmental guidance. An editorial topic, generated summary or inferred connection in this project is a project assertion with its own provenance and review state.

The practical model therefore keeps **collection → document snapshot → evidence passage**, with small editorial topic labels and explicit source links. It retains original numbering, labelled spare chapters and amendment roles. It does not attempt to convert prose directly into executable eligibility rules.

## Domain vocabulary and legal references

Preserve source-native labels including Pension Credit/State Pension Credit, Guarantee Credit, Savings Credit, assessed income period, capital, earnings, income other than earnings, additional amounts and payment questions. Keep **Pension Credit** distinct from **State Pension**, and keep the chapter labels for **earnings** and **income other than earnings** separate. These are discovery terms, not a newly asserted legal ontology. [DWP advisers guide](https://www.gov.uk/government/publications/pension-credit-technical-guidance/a-detailed-guide-to-pension-credit-for-advisers-and-others)

The initial official reference register is intentionally small:

| Reference | Why it matters to discovery | Boundary |
| --- | --- | --- |
| [State Pension Credit Act 2002](https://www.legislation.gov.uk/ukpga/2002/16/contents) | Benefit framework, component headings, income and capital, assessed income periods | Contents inspected; full provision and effects reconciliation not performed |
| [State Pension Credit Regulations 2002](https://www.legislation.gov.uk/uksi/2002/1792/contents) | Detailed regulations and schedules; source-native citation targets | No claim that every cited or amending instrument is represented |
| [Social Security Administration Act 1992](https://www.legislation.gov.uk/ukpga/1992/5/contents) | Administration and claims framework | Reference only |
| [Social Security Act 1998](https://www.legislation.gov.uk/ukpga/1998/14/contents) | Decision-making and appeals framework | Reference only |
| [Social Security and Child Support (Decisions and Appeals) Regulations 1999](https://www.legislation.gov.uk/uksi/1999/991/contents) | Procedural citation family | Reference only |
| [Pensions Act 2014, section 28](https://www.legislation.gov.uk/ukpga/2014/19/section/28) | Demonstrates the importance of historical assessed-income-period context | Preserve dates and conditions; do not derive a case decision |

At observation, the Act's contents page included outstanding-effects information alongside a general current-date notice. This is a concrete reason to inspect each provision's annotations and commencement state before claiming a complete consolidated legal model. [Act contents and revision notices](https://www.legislation.gov.uk/ukpga/2002/16/contents)

A further **review candidate** appears in the advisers guide: a document headed April 2026 includes a child-amount subsection explicitly labelled with April 2024 rates. This is preserved as a source-level temporal observation, not silently corrected or used to calculate an award. A document heading alone cannot establish the applicable date of every figure. [Advisers guide, “The extra amount for children”](https://www.gov.uk/government/publications/pension-credit-technical-guidance/a-detailed-guide-to-pension-credit-for-advisers-and-others#the-extra-amount-for-children)

## Standards and ontology decisions

OKF+ here means **OKF 0.2 with explicit additional semantic and consumer contracts**. It is not a claim that every advanced production feature is implemented.

| Standard or vocabulary | Decision for this exemplar |
| --- | --- |
| [OKF 0.2, pinned specification commit](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/3fcbb9f828c2f23d109c855ee403c3a4c81f3a96/okf/SPEC.md) | Portable Markdown core; validate the actual generated structure |
| [YAML 1.2.2](https://yaml.org/spec/1.2.2/) | Use a restricted JSON-compatible authoring representation; preserve dates and identifiers as strings |
| [YAML-LD 1.0, 10 September 2026](https://www.w3.org/TR/2026/WD-yaml-ld-10-20260910/) | **W3C Working Draft**, not a Recommendation; record exact draft and avoid a full processor-conformance claim |
| [JSON-LD 1.1](https://www.w3.org/TR/2020/REC-json-ld11-20200716/) | Machine-readable semantic projection; parser success alone does not prove meaningful links |
| [PROV-O](https://www.w3.org/TR/2013/REC-prov-o-20130430/) | Provenance vocabulary for source entities and derivation |
| [Dublin Core Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/2020-01-20/) | Document labels and source/part/reference predicates; direct reference retrieval returned 403 |
| [SKOS](https://www.w3.org/TR/2009/REC-skos-reference-20090818/) | Conditional for a reviewed concept scheme; no `exactMatch` or `owl:sameAs` based on name similarity |
| [JSON Schema 2020-12](https://json-schema.org/draft/2020-12/json-schema-core.html) | Structural profile/control validation; direct specification retrieval returned 403, local pinned profile schema available |
| [RDF 1.1](https://www.w3.org/TR/2014/REC-rdf11-concepts-20140225/) | Reference model; keep RDF semantics distinct from required-field validation |
| [RDF Dataset Canonicalization 1.0](https://www.w3.org/TR/2024/REC-rdf-canon-20240521/) | Deferred unless canonical RDF dataset digests are published; file SHA-256 is a different check |
| [SHACL](https://www.w3.org/TR/2017/REC-shacl-20170720/) | Deferred pending a closed-world RDF publication contract |
| [WCAG 2.2](https://www.w3.org/TR/2024/REC-WCAG22-20241212/) | Accessibility design reference; formal conformance audit is not claimed |

The vocabulary answers concrete tasks: source (`dcterms:source`), containment (`dcterms:isPartOf`) and explicit references (`dcterms:references`). A hyperlink does not automatically imply a legal dependency. Do not assert broad/narrow/exact equivalence from a matching label. Local identifiers describe this independent representation, not official DWP identifiers.

The profile's semantic-link ledger covers **one collection identity linked to its official page**. Its 100% result is only 1 of 1 collection links, not a measure of document, paragraph or legislative mapping coverage. Those require their own inventories and reconciliation.

## Rights, privacy and presentation

GOV.UK permits reuse of content published under the applicable Open Government Licence, subject to its conditions and exceptions. OGL v3 permits adaptation and redistribution with attribution; it excludes specified material and does not grant permission to imply endorsement. [GOV.UK terms](https://www.gov.uk/help/terms-conditions), [OGL v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)

Use this attribution with the source link and acquisition date:

> Contains public sector information licensed under the Open Government Licence v3.0.

Document-specific third-party notices still matter. Project-authored code, navigation labels and prose need their own stated licence. No claimant personal data or private casework is in scope. Use an independent visual identity and retain an exploratory notice, original sources, historical markers and extraction limitations.

## Meeting questions and review priorities

These are candidate evaluation questions, not independently checked expected answers:

- Where would a researcher find earnings guidance, and how is it distinguished from income other than earnings?
- Can a reader follow a passage back to its original PDF and page?
- Can a reader tell a historical amendment from a chapter document?
- Does the system retain an unresolved legal or DMG reference instead of inventing a target?
- Does it decline to determine a person's entitlement from this snapshot?

The [profile validation receipt](../domain-profile/validation.json) records structural checks actually run. The [impact graph](../domain-profile/impact-graph.json) says which checks a source, schema, builder or route change should invalidate. Actual Explorer/browser results and source extraction validation are separate receipts owned by the build.

The next domain review should inspect a few representative paragraphs with the pensions representative, check legal abbreviation resolution, test table/footnote extraction and challenge historical-document labelling. Full Foundry fixture assurance, bidirectional consumer compatibility, provision-level law mapping and independent answer evaluation remain explicit follow-on work.
