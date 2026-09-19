# HMRC discovery brief template

Copy this brief into the separate domain-discovery stage. Replace the bracketed
values. It is not a completed HMRC domain profile, a source acquisition request
or a claim of tax expertise. The output must be validated against the chosen
canonical domain-profile schema before it becomes build input.

## Run inputs

- Department/source owner: HM Revenue & Customs.
- Starting catalogue: https://www.gov.uk/government/collections/hmrc-manuals
- Chosen manual and exact initial source URLs: **[select; do not assume all manuals]**.
- User and task: **[one actual task, its stakes and expected evidence]**.
- Competency questions: **[positive, ambiguous, historical and unanswerable cases]**.
- Jurisdiction, relevant tax/benefit, period and language: **[state or unresolved]**.
- Research cut-off: **[ISO date]**.
- Repository/publication target and owner authorisation: **[state explicitly]**.
- Source access and model-processing/redistribution rights: **[per operation]**.
- Consumer versions, supported interfaces and fixture size: **[pin exact versions]**.
- Source, time and model budget: **[finite bounds; no implied paid API authority]**.
- Private material: **excluded unless a separately authorised governed route exists**.

## Required discovery outputs before generating assertions

### A. Inventory and authority

Name each source family and its exact denominator. Distinguish manual pages,
updates, withdrawn material, legislation, regulations, tribunal/court decisions,
external explanations and calculators. Identify unavailable sources without
inventing their content. Treat technical guidance and law as distinct evidence.

### B. Departmental terminology

Create a term register with: term ID, preferred label, abbreviation, source-native
definition, variants, language, scope, time/jurisdiction, confusable terms,
source URL/locator/hash and review state. Do not import benefit-specific DWP
meanings for words such as income, residence, capital, assessment or payment.
Each disputed meaning remains unresolved until evidenced.

### C. Legislation, regulations and decisions

Preserve each literal citation. Research the official target, work versus
provision identity, version, territorial extent, commencement/effects and
relevant amendments for the chosen question. Record which parts were actually
inspected and which need specialist review. A catalogue match or shared title
is not proof of current legal applicability. Record apparent contradictions.

### D. Ontologies, standards and conventions

Research departmental/public identifiers, official glossaries, existing tax or
legal vocabularies and the reusable OKF stack. For each candidate record:

| Field | Required content |
| --- | --- |
| Identity | Official URI, title, publisher, version/date and publication status |
| Decision | Normative, projection, source-native, conditional, reference-only or not-applicable |
| Scope | Exact classes/predicates used and the competency question they support |
| Mapping | Source-native value, target meaning, direction, strength and uncertainty |
| Evidence | Precise source, observation time, source hash and review state |
| Validation | Artefact/validator and what passing it would actually establish |

Do not preselect every vocabulary, claim a formal ontology import merely because
a prefix is declared, or use similarity to assert identity. Draw an actual
`flowchart TD` namespace map after inspection, with proposed standards separate.

### E. Build handoff and stopping conditions

Produce the versioned domain profile, source-family inventory, evidence register,
consumer lock, impact graph, unresolved decisions and tiny-fixture acceptance
checks. A build starts only for the declared useful scope. Material rights,
authority or legal-meaning gaps stay explicit; they are not erased to meet a demo.
The first public artefact remains independent and exploratory unless its own
review and publication gates establish a stronger status.
