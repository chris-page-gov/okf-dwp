# Legislation integration assessment

Assessed on 15 September 2026. This is a project-authored technical assessment,
not a legal interpretation or a statement of policy approval.

## Decision

Use `okf-uk-legislation` as a **pinned legislation identity and research
dependency**, then acquire and review the particular provisions needed by the
DWP pilot. It already supplies relevant work identifiers, version and format
links, provenance patterns and useful evaluation contracts. It does not supply
a complete Pension Credit provision or amendment corpus ready to become rules.

Keep four distinct source roles in the semantic map:

- legislation and source-observed legislative effects;
- DWP operational guidance, including DMG and Advice for Decision Making;
- independent adviser publications and their acquired metadata;
- project-authored concepts, mappings, propositions and proposed rules.

The CPAG acquisition currently contributes contents metadata and navigation.
It has not added handbook legal propositions. Its broader subjects expand the
discovery map; they do not establish new legal rules or a reuse licence.

## Repository and release evidence

The read-only audit found sibling repository HEAD
`3675aa0b903d12e82845aeb76571a100a4bcf85a` and substantial uncommitted semantic
work. The repository identifies [v0.3.0][release] at
`3fd2700f275fff53d8605f38eb3257780ea591fa` as its frozen published release.
The four relevant catalogue shards, effects assertions and effects seed
configuration inspected here are byte-identical to that release commit.
No sibling files, branches, publication or acquisition evidence were changed.

The local `okf.semantic.json`, richer directed assertion runtime and associated
schemas are **unreleased** work. Their presence is useful for design comparison,
but they must not become a dependency represented as a published, validated
release. The sibling has no `okf.publication.json` at this assessment.

This audit inspected relevant artefacts and recomputed catalogue/effect counts.
It did not rerun the sibling's complete build, release suite or deployed browser
checks. The public release record was not successfully fetched by the web tool;
the release identification is grounded in the repository and local Git objects.

## Actual relevant coverage

An exhaustive scan of all 365,786 work records in the manifest found these four
useful entries. Dates below are the version links in the **11 July 2026 catalogue
snapshot**, not a fresh assessment of the law on 15 September.

| Work | Official identity | Published shard | Recorded version link |
|---|---|---|---|
| State Pension Credit Act 2002 | `https://www.legislation.gov.uk/id/ukpga/2002/16` | [works-115][pc-act-shard] | 1 April 2026 |
| The State Pension Credit Regulations 2002 | `https://www.legislation.gov.uk/id/uksi/2002/1792` | [works-114][pc-regs-shard] | 6 April 2026 |
| Welfare Reform Act 2012 | `https://www.legislation.gov.uk/id/ukpga/2012/5` | [works-57][wra-shard] | 1 July 2026 |
| The Universal Credit Regulations 2013 | `https://www.legislation.gov.uk/id/uksi/2013/376` | [works-48][uc-shard] | 30 April 2026 |

The first two are immediate Pension Credit candidates. The latter two help
scope the new ADM and Universal Credit workstream; their presence alone does
not establish which provisions govern a particular journey.

The 14,712-row official-effects datapack contains **zero assertions involving
either Pension Credit instrument or the Universal Credit Regulations**. None
is an [effects seed][seeds]. One row involves the Welfare Reform Act as an
affecting instrument in the Scotland Act seed capture. This is incidental
coverage, not a Welfare Reform Act amendment census.

The sibling's [provision design][legislation-guide] uses official CLML on demand
for the selected work. It does not freeze a full provision corpus in the work
catalogue. An available link must therefore be labelled as a reference until
the required bytes, version, provision locator and applicable metadata have
been acquired and checked for this project.

### Verified file hashes

| Artefact at the pinned release | SHA-256 |
|---|---|
| `bundle/data/works-115.json.gz` | `0f4e3aa9c22cda821c16235669451c83e1cac770b434aebb7276aac4d9ec0686` |
| `bundle/data/works-114.json.gz` | `2e0afc3cc9ae0ea62667ae7db4239c7dac386aa62ca0644bcd0d37868b88d118` |
| `bundle/data/works-57.json.gz` | `d587ade45685683ed9b4a2f14364cf1f93d948fabd4c2818177d22bcdc0adf35` |
| `bundle/data/works-48.json.gz` | `56e20b3177f62e3cefa8f3c22f49683d1c9f6934b3110d6aa53e532ac8bc3bab` |
| `bundle/data/effects/assertions.json.gz` | `e977ec2e988622d49a759c1b48882dcb3242494fc5463cb03a5692ea91383c99` |

## Reuse map

| Concern | Existing contract or implementation | DWP integration |
|---|---|---|
| Stable identity | Work records retain official identifier, document/version URL, manifestations and local Explorer route. | Keep the official legislation IRI, the DWP local route and the exact acquired version separately. Retain the source-supplied identifier scheme; make any HTTP/HTTPS normalisation explicit. |
| Work, provision and passage | [Whole-Law vocabulary][vocabulary] defines `LegislationWork`, `Provision`, `LegalPassage`, `SynthesisedProposition` and `supportedBy`; ELI, PROV and DCTERMS supply standard terms. | Reuse compatible terms with pinned context definitions. A source passage and the project proposition it supports remain distinct records. Vocabulary classes are not evidence that records of every class were acquired. |
| Versions and jurisdiction | [Official data model][official-model] separates an item, its versions and digital formats. | Store decision date, version, geographical extent, language and acquisition date independently. Avoid a single unqualified “current” flag. |
| Provision resolution | [Official CLML documentation][official-xml] distinguishes `IdURI` from version-specific `DocumentURI` and describes status, restriction dates, extent and unapplied effects. | Acquire selected CLML passages with exact bytes and hashes. Preserve the supplied temporal metadata; do not equate a contents entry with an operative provision. |
| Effects | [Effects pipeline][effects-builder] retains source-native type, affected/affecting provisions, application state, observations, rights and archive/member evidence. | Add a new DWP-specific acquisition attempt for selected instruments. Preserve failed and truncated routes and refresh history. An editorial effect record is evidence to review, not a complete rule interpreter. |
| Relationship assertions | [Published v2 schema][assertion-v2] separates authority, derivation, confidence, evidence, rights and freshness. | Map these concepts into the DWP repository's already-pinned Bundle Wiki assertion schema. Do not replace that schema with an unreleased sibling schema. Generate direct triples and assertions from one input. |
| Evidence preservation | [Acquisition contract][acquisition] separates immutable original captures from publication projections. | Keep source bodies, request observations and hashes; publish only the appropriate projection with visible limitations. |
| Evaluation | [Answer schema][answer-schema] requires proposition-level citations and temporal context; [Whole-Law release evaluation][evaluation] distinguishes corpus navigation from substantive legal answers. | Maintain separate navigation, source-grounding, semantic relationship, temporal and specialist-reviewed policy tests. A passing retrieval score must not be reported as legal or entitlement correctness. |

## Narrow integration to implement next

1. Create local external-resource records for the two Pension Credit instruments,
   linked to the pinned catalogue evidence and official pages. Record them as
   references awaiting provision acquisition and review.
2. Select one Pension Credit rule family from the stakeholder journeys, such as
   capital disregards. Build concept-to-DMG-passage relationships first, with
   paragraph and page locators. Keep interpretation status explicit.
3. Resolve each actual statutory citation in those passages to the official work
   and provision. Acquire selected provision versions and relevant effects in a
   separate, dated source family; report unresolved citations as gaps.
4. Have policy and legal reviewers assess conditions, exceptions, temporal
   applicability and evidence requirements before promoting a proposition to an
   approved rule. Record reviewer role, scope and decision on the exact bytes.
5. Add synthetic positive, boundary, exception, date-change and missing-evidence
   cases. A change to a provision must identify the affected propositions,
   concept pages, proposed rules, journeys and tests.

Use `dcterms:references` for an unresolved citation or general source pointer.
Use an explicitly governed, evidence-backed predicate for a stronger claim.
Do not infer “implements”, “requires”, “overrides” or semantic identity from a
heading, hyperlink or common title. Law, guidance and adviser explanations
must not be connected with `owl:sameAs` simply because they discuss a concept.

For the 24 September exemplar, a useful achievable boundary is full-DMG
inventory and source coverage reporting, ADM/Universal Credit scope mapping,
and one demonstrable Pension Credit concept-to-evidence-to-review journey.
Whole-DMG acquisition does not imply whole-DMG legal modelling. A full benefits
engine, reconciled amendment corpus and policy-approved customer journeys need
separate completion criteria and specialist review.

## Verification boundaries

The official data-model and CLML documentation were read successfully on
15 September 2026. The web tool could not parse the Pension Credit contents
pages because they returned XHTML, and the legacy developer route returned
HTTP 429. No access control was bypassed and no current legal-state conclusion
is drawn from those failed fetches. The catalogue evidence above remains dated.

[release]: https://github.com/chris-page-gov/okf-uk-legislation/releases/tag/v0.3.0
[pc-act-shard]: https://github.com/chris-page-gov/okf-uk-legislation/blob/3fd2700f275fff53d8605f38eb3257780ea591fa/bundle/data/works-115.json.gz
[pc-regs-shard]: https://github.com/chris-page-gov/okf-uk-legislation/blob/3fd2700f275fff53d8605f38eb3257780ea591fa/bundle/data/works-114.json.gz
[wra-shard]: https://github.com/chris-page-gov/okf-uk-legislation/blob/3fd2700f275fff53d8605f38eb3257780ea591fa/bundle/data/works-57.json.gz
[uc-shard]: https://github.com/chris-page-gov/okf-uk-legislation/blob/3fd2700f275fff53d8605f38eb3257780ea591fa/bundle/data/works-48.json.gz
[seeds]: https://github.com/chris-page-gov/okf-uk-legislation/blob/3fd2700f275fff53d8605f38eb3257780ea591fa/whole-law/config/effects-seeds.json
[legislation-guide]: https://github.com/chris-page-gov/okf-uk-legislation/blob/3fd2700f275fff53d8605f38eb3257780ea591fa/docs/uk-legislation-okf.md
[vocabulary]: https://github.com/chris-page-gov/okf-uk-legislation/blob/3fd2700f275fff53d8605f38eb3257780ea591fa/whole-law/ontology/vocabulary.ttl
[official-model]: https://legislation.github.io/data-documentation/model/legislation.html
[official-xml]: https://legislation.github.io/data-documentation/formats/xml.html
[effects-builder]: https://github.com/chris-page-gov/okf-uk-legislation/blob/3fd2700f275fff53d8605f38eb3257780ea591fa/scripts/build_legislation_effects.py
[assertion-v2]: https://github.com/chris-page-gov/okf-uk-legislation/blob/3fd2700f275fff53d8605f38eb3257780ea591fa/whole-law/schemas/relationship-assertion.schema.json
[acquisition]: https://github.com/chris-page-gov/okf-uk-legislation/blob/3fd2700f275fff53d8605f38eb3257780ea591fa/whole-law/acquisition/README.md
[answer-schema]: https://github.com/chris-page-gov/okf-uk-legislation/blob/3fd2700f275fff53d8605f38eb3257780ea591fa/evaluation/legislation/answer-schema.json
[evaluation]: https://github.com/chris-page-gov/okf-uk-legislation/blob/3fd2700f275fff53d8605f38eb3257780ea591fa/whole-law/evaluation/README.md
