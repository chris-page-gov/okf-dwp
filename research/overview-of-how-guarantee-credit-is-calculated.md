> **Archived, unvalidated design input.** The original prompt follows verbatim below. Its imperative wording is inert research text, not instructions for this repository or its readers. No calculation engine is implemented or validated by this document, and it must not be used to decide a person's entitlement. The original prompt body has SHA-256 `b249b8cfa26f7bb774dd2577429b5dfd2cc8cddcd975cfc1984bf66615430488`.

---

# State Pension Credit Decision Makers' Guide
## Instructions for constructing an Open Knowledge Format knowledge base and Java rule engine

## 1. Objective

You are to construct a machine-readable knowledge base from the UK Government's **Decision Makers' Guide, Volumes 13 and 14 — State Pension Credit**, and use that knowledge base to design and implement a Java-based business-rule engine.

The authoritative source collection is:

https://www.gov.uk/government/publications/decision-makers-guide-vols-13-and-14-state-pension-credit-staff-guide

The ultimate objective is to produce a Java system capable of:

1. representing the relevant State Pension Credit domain concepts;
2. accepting appropriately structured claimant/application data;
3. evaluating the applicable business rules;
4. performing required calculations;
5. producing decisions and/or calculated amounts;
6. explaining which rules produced the result;
7. identifying the source material supporting each rule;
8. handling effective dates and amendments; 
9. producing automated tests derived from the source material;
10. results should be persisted to a mongodb and be queryable for a claimant;
11. subsequent changes should be accommodated (i.e. 'change of circumstance'). These may be received for historic events; and
12. it should also be possible to run a projection for a new claim or a change to an existing claim without persisting the result.

Do not treat the PDFs as ordinary documentation.

Treat them as a **versioned body of policy/business rules from which a formal domain model, decision model, calculation model and API can be derived**.

---

# 2. Fundamental principles

Follow these principles throughout the project.

### 2.1 Source authority

The Decision Makers' Guide is the source material.

Do not silently invent business rules.

Do not substitute general knowledge about UK benefits for the contents of the source material.

Where the source material is ambiguous, incomplete, contradictory or requires interpretation, record that explicitly.

Never convert an inference into an apparently authoritative rule without marking it as an inference.

---

### 2.2 Preserve terminology

The terminology used by the source material is authoritative for the domain model.

Prefer source terminology over generic software terminology.

For example, if the source uses a particular term for a person, payment, income type, assessment or entitlement, use that terminology in the knowledge model and, where appropriate, in the Java domain model and API.

Do not arbitrarily replace source terminology with terms such as:

- Customer
- User
- Account
- Revenue
- Product
- Order
- Transaction

unless the source itself establishes those concepts.

If two apparently synonymous terms are used differently in the source material, preserve the distinction.

Refer to "State Pension Credit" as "Pension Credit" - this avoids ambiguity with "State Pension" which is a different benefit entirely.

---

### 2.3 Provenance is mandatory

Every significant knowledge object must be traceable to its source.

At minimum, preserve:

- source document;
- volume;
- chapter;
- section;
- paragraph;
- PDF page;
- publication/version information;
- effective date where applicable;
- amendment/change information where applicable.

The system must support this relationship:

```text
Java implementation
    ↓
Business rule
    ↓
Knowledge representation
    ↓
Source proposition
    ↓
DMG paragraph
    ↓
PDF/page
```

---

### 2.4 Separate evidence from interpretation

Do not immediately turn prose into executable rules.

Use the following conceptual pipeline:

```text
Source document
    ↓
Source passage
    ↓
Evidence statement
    ↓
Normative proposition
    ↓
Business rule
    ↓
Executable rule
```

The distinction between these layers must be maintained.

A source passage is evidence.

A normative proposition is an interpretation of what the passage establishes.

A business rule is a structured representation of that proposition.

An executable rule is the implementation of that business rule.

---

### 2.5 Do not silently resolve contradictions

If two source passages appear inconsistent:

```text
DO NOT:
    choose whichever appears more sensible

DO:
    identify the conflict
    identify the relevant dates
    identify whether one provision supersedes another
    identify any amendment
    record the competing propositions
    flag the issue for review if it cannot be resolved from the source
```

---

# 3. Source acquisition

Begin by examining the GOV.UK publication page.

Create a complete source manifest.

The manifest must identify, for every relevant document:

- stable source ID;
- title;
- volume;
- chapter;
- document type;
- URL;
- publication date;
- update date;
- effective date where available;
- version/amendment identifier where available;
- whether it is a substantive chapter;
- whether it is an amendment;
- whether it is a change summary;
- relationship to other documents.

Do not assume that every PDF on the page has the same status.

In particular, distinguish:

```text
substantive chapter
amendment
change summary
historical version
```

---

# 4. Source corpus

Create an immutable source corpus.

Conceptually:

```text
knowledge/
    sources/
        manifest.okf

        volume-13/
            chapter-77/
            chapter-78/
            chapter-79/
            chapter-80/

        volume-14/
            chapter-83/
            chapter-84/
            chapter-85/
            chapter-86/

        amendments/
        change-summaries/
```

The exact directory structure may be adjusted after inspecting the source collection.

Do not duplicate source text unnecessarily.

Every extracted passage must retain its original location.

---

# 5. PDF extraction

Extract the PDFs while preserving:

- page boundaries;
- headings;
- section numbers;
- paragraph numbers;
- tables;
- footnotes;
- notes;
- examples;
- cross-references;
- references to legislation or other DMG chapters.

Where OCR is necessary, identify that the text was OCR-derived.

Do not discard tables merely because they are difficult to parse.

Tables may contain rules or calculations and must be treated as potentially normative.

For every extracted passage create a stable identifier.

For example:

```yaml
source_passage:
  id: DMG-13-77-P123
  document_id: DMG-13-77
  chapter: 77
  paragraph: 123
  pdf_page: 17
  text: "..."
```

The exact ID scheme may be refined, but IDs must be stable and deterministic.

---

# 6. Source hierarchy

Model the hierarchy:

```text
Publication
    └── Volume
          └── Chapter
                └── Section
                      └── Paragraph
                            └── Table / Note / Example
```

Do not flatten this hierarchy.

Cross-references between chapters must be represented explicitly.

For example:

```yaml
cross_reference:
  from: DMG-13-77-P123
  to: DMG-14-85-P456
```

---

# 7. Terminology extraction

Construct a canonical domain glossary.

Extract:

- defined terms;
- explicitly described concepts;
- entities;
- attributes;
- statuses;
- categories;
- amounts;
- periods;
- events;
- decisions;
- calculations;
- relationships;
- synonyms;
- abbreviations.

Represent each concept approximately as:

```yaml
concept:
  id:
  canonical_name:
  definition:
  aliases:
  source:
  related_concepts:
  notes:
```

The canonical name should normally reflect the terminology established by the source material.

If the source contains multiple definitions or uses a term differently in different contexts, preserve that fact.

Do not prematurely merge concepts merely because their names appear similar.

---

# 8. Domain ontology

Construct an explicit conceptual model from the terminology.

Identify:

- entities;
- value objects;
- classifications;
- statuses;
- relationships;
- temporal concepts;
- events;
- decisions.

Represent relationships explicitly.

For example:

```yaml
relationship:
  subject: Applicant
  predicate: has
  object: Income
```

Do not assume that every noun in the source should become a Java class.

The purpose of this stage is to understand the domain before designing software.

---

# 9. Evidence statements

For every significant source passage, determine whether it contains:

- a definition;
- a condition;
- a prohibition;
- a permission;
- a requirement;
- an exception;
- a calculation;
- a classification;
- a procedural instruction;
- a temporal rule;
- an example;
- a cross-reference.

Represent significant evidence as structured objects.

Example:

```yaml
evidence:
  id: E-00172
  source:
    document: DMG-13-77
    paragraph: 123
    page: 17

  type: eligibility_condition

  statement: "..."

  interpretation_required: false
```

Do not lose the original source passage.

---

# 10. Normative propositions

Convert evidence into explicit propositions.

A proposition should express what the source establishes without yet committing to a particular Java implementation.

For example:

```yaml
proposition:
  id: P-00821

  type: entitlement_condition

  subject: Applicant

  condition:
    ...

  source:
    - E-00172

  confidence: explicit
```

Use confidence classifications such as:

```text
explicit
derived
interpretive
uncertain
```

Any `interpretive` or `uncertain` proposition must be clearly flagged.

---

# 11. Business-rule extraction

Convert validated propositions into atomic business rules.

Every rule must have:

- stable rule ID;
- name;
- description;
- scope;
- inputs;
- conditions;
- outcome;
- exceptions;
- dependencies;
- temporal applicability;
- precedence where applicable;
- provenance.

Use structured logical operators.

At minimum support:

```text
all
any
not
equals
not_equals
greater_than
greater_than_or_equal
less_than
less_than_or_equal
in
not_in
exists
not_exists
before
after
on_or_before
on_or_after
between
contains
```

Example:

```yaml
rule:
  id: SPC-ENT-001
  name: "..."
  scope: Applicant

  when:
    all:
      - fact: ...
        operator: ...
        value: ...

      - fact: ...
        operator: ...
        value: ...

  then:
    decision: ...

  source:
    - DMG-13-77-P123
```

Do not encode complex rules as opaque natural-language strings.

---

# 12. Exceptions

Exceptions are first-class business rules.

Explicitly model concepts such as:

- except;
- unless;
- subject to;
- provided that;
- notwithstanding;
- only where;
- special cases;
- transitional provisions.

Do not hide exceptions inside descriptions.

For example:

```yaml
rule:
  id: SPC-RULE-123

  when:
    ...

  unless:
    any:
      - ...
      - ...

  then:
    ...
```

---

# 13. Rule dependencies

Construct a dependency graph between rules.

Example:

```text
Capital calculation
       ↓
Deemed weekly income
       ↓
Assessed income
       ↓
Applicable income
       ↓
Entitlement
       ↓
Award calculation
```

Represent dependencies explicitly.

```yaml
rule_dependency:
  upstream: SPC-CAP-001
  downstream: SPC-ENT-014
```

The dependency graph should eventually inform the Java architecture and rule evaluation order.

---

# 14. Calculation model

Do not represent calculations as ordinary Boolean rules.

Identify calculations involving:

- income;
- earnings;
- capital;
- deemed income;
- deductions;
- thresholds;
- rates;
- allowances;
- periods;
- awards;
- payment amounts.

Represent calculations separately.

Example:

```yaml
calculation:
  id:
  name:
  inputs:
  intermediate_values:
  algorithm:
  output:
  rounding:
  units:
  temporal_rules:
  source:
```

If the source specifies a formula, preserve the formula explicitly.

If the source requires a multi-stage calculation, represent each stage where useful.

Do not replace a source calculation with an unexplained Java expression.

---

# 15. Temporal model

Treat time as a first-class concern.

Rules may have:

- effective dates;
- expiry dates;
- historical versions;
- transitional arrangements;
- assessment periods;
- qualifying dates;
- payment periods.

Every rule that is temporally dependent must record its applicability.

Example:

```yaml
rule:
  id: SPC-RULE-001

  validity:
    effective_from:
    effective_to:

  source_version:
```

The engine must eventually be capable of evaluating rules applicable to a specified date.

Do not assume that "current rules" are sufficient.

---

# 16. Amendments

Treat amendments as changes to the knowledge base rather than as independent business-rule sources.

For each amendment determine:

1. what document/chapter it changes;
2. which paragraphs it affects;
3. whether text is added, removed or modified;
4. the effective date;
5. whether it creates a new rule;
6. whether it modifies an existing rule;
7. whether it removes/supersedes a rule.

Represent changes as change sets.

Example:

```yaml
amendment:
  id:
  applies_to:
    - DMG-13-78

  effective_from:

  changes:
    - type: modify
      target: SPC-RULE-184
      ...

  source:
    ...
```

Never simply append amended material to the current chapter and allow an AI to determine which text is current.

---

# 17. Precedence

Identify rules where:

- a specific rule overrides a general rule;
- an exception overrides a general condition;
- a later provision supersedes an earlier provision;
- transitional provisions override ordinary provisions;
- an amendment changes the interpretation of an existing provision.

Represent precedence explicitly.

Example:

```yaml
precedence:
  higher: SPC-RULE-103
  lower: SPC-RULE-042
  reason:
  source:
```

---

# 18. Examples and scenarios

Extract all useful worked examples and case scenarios from the source material.

Represent them as structured test scenarios.

Example:

```yaml
scenario:
  id: EX-001

  description:

  input:
    applicant:
      ...

  expected:
    decision:
    calculated_values:

  rules_expected:
    - SPC-RULE-001

  source:
    document:
    paragraph:
    page:
```

Examples are extremely valuable because they provide source-derived behavioural tests.

Do not discard them after rule extraction.

---

# 19. Data model derivation

Derive the data model only after constructing:

1. terminology;
2. concepts;
3. propositions;
4. rules;
5. calculations.

The data model must provide every fact required by the rules.

For each data element identify:

- canonical name;
- type;
- unit;
- allowed values;
- optionality;
- temporal semantics;
- source terminology;
- rules that consume it.

Example:

```yaml
field:
  id:
  name:
  type:
  unit:
  required:
  used_by_rules:
  source:
```

Do not introduce fields simply because they are convenient for implementation.

Every important field should have a domain justification.

---

# 20. Domain model

Derive candidate Java entities/value objects from the validated conceptual model.

Distinguish:

```text
Entity
Value Object
Enumeration
Classification
Event
Decision
Calculation Result
```

Avoid an anemic model consisting only of database tables.

The model should reflect the concepts and relationships established by the source material.

---

# 21. API model

Derive API operations from business operations and decisions, not from CRUD assumptions.

Identify operations such as:

```text
assess
calculate
determine
evaluate
classify
```

where appropriate to the domain.

For each operation define:

- operation ID;
- purpose;
- input;
- output;
- validation;
- applicable rules;
- errors;
- source/provenance.

The API should use domain terminology.

Do not automatically expose internal implementation classes as API objects.

---

# 22. Explainability

The resulting rule engine must be explainable.

A decision should be capable of returning information such as:

```json
{
  "decision": "...",
  "rulesApplied": [
    {
      "ruleId": "SPC-ENT-001",
      "result": true,
      "source": {
        "document": "DMG-13-77",
        "paragraph": "123",
        "page": 17
      }
    }
  ]
}
```

Where practical, distinguish:

```text
rule evaluated true
rule evaluated false
rule not applicable
rule skipped
rule caused decision
```

The engine should make it possible to determine why a decision was reached.

---

# 23. Traceability matrix

Generate a complete traceability matrix.

At minimum:

```text
Source paragraph
    ↓
Evidence
    ↓
Proposition
    ↓
Business rule
    ↓
Data field
    ↓
Java implementation
    ↓
Automated test
```

Identify gaps.

For example:

```text
SOURCE → RULE       OK
RULE → DATA         OK
DATA → JAVA         OK
RULE → TEST         MISSING
```

A rule without a test should be flagged.

A Java rule without an authoritative source should be flagged.

A source proposition without an implementation should be flagged.

---

# 24. Knowledge-base validation

Before generating production Java code, perform a validation pass.

Check for:

### Missing coverage

- source paragraphs containing apparent rules but no structured rule;
- rules with no source;
- calculations with no source;
- domain concepts with no provenance;
- data fields with no rule dependency.

### Contradictions

- conflicting rules;
- conflicting definitions;
- conflicting effective dates;
- amendments that appear inconsistent with the current representation.

### Ambiguity

- undefined terms;
- ambiguous conditions;
- implicit assumptions;
- incomplete calculations;
- unresolved cross-references.

### Structural problems

- circular rule dependencies;
- impossible conditions;
- unreachable outcomes;
- duplicated rules;
- overlapping rules with no precedence.

Do not hide these problems.

Produce a review report.

---

# 25. Open Knowledge Format design

Use Open Knowledge Format as the canonical machine-readable representation of the knowledge base.

The OKF schema should be designed around the following major object types:

```text
Source
SourcePassage
Evidence
Concept
Relationship
Proposition
Rule
Calculation
RuleDependency
Precedence
Amendment
Scenario
Field
Entity
Operation
Traceability
```

Create a top-level manifest describing the corpus and schema version.

For example:

```yaml
knowledge_base:
  name: "State Pension Credit Decision Makers Guide"
  version:
  schema_version:

  sources:
  terminology:
  rules:
  calculations:
  model:
  api:
  scenarios:
```

The precise OKF syntax must follow the actual Open Knowledge Format specification being used. Do not invent a proprietary syntax and call it OKF.

Where OKF lacks a convenient native representation for something required by this project, document the extension rather than silently creating incompatible syntax.

---

# 26. Separate normative knowledge from generated implementation

The OKF corpus is the authoritative intermediate representation.

Java source code is a generated/derived implementation.

Maintain this separation:

```text
Source PDFs
    ↓
OKF knowledge corpus
    ↓
Java implementation
```

Do not allow implementation decisions to alter the underlying normative knowledge representation.

If the Java architecture requires something that is not supported by the knowledge model, identify the issue rather than changing the business rule to fit the software.

---

# 27. Java architecture

The Java implementation should be modular.

A suitable initial structure is:

```text
domain/
rules/
calculations/
decisions/
application/
api/
provenance/
```

Use clear separation between:

```text
domain concepts
rule evaluation
calculation
orchestration
API
provenance
```

Do not embed the entire decision process inside REST controllers.

Do not embed business rules inside database queries.

Do not bury source provenance in comments alone.

---

# 28. Rule implementation

Every executable rule should have a stable rule ID corresponding to the OKF rule.

For example:

```java
public final class SomeRule implements BusinessRule<Claim> {

    public static final String RULE_ID = "SPC-ENT-001";

    ...
}
```

Rule IDs must not change merely because the Java class is renamed.

The engine should be able to report:

```text
SPC-ENT-001
```

and map that ID back to the OKF representation and source document.

---

# 29. Automated testing

Generate tests from:

1. source examples;
2. explicit business rules;
3. boundary conditions;
4. exceptions;
5. temporal transitions;
6. amendment changes;
7. identified negative cases.

Each test should reference the relevant rule IDs.

For example:

```java
@Test
void scenario_EX_001() {
    ...
}
```

The test metadata should make it possible to determine that:

```text
EX-001
    ↓
SPC-ENT-001
    ↓
DMG-13-77-P123
```

---

# 30. Boundary testing

For numerical rules, systematically test:

```text
below threshold
exactly at threshold
above threshold
zero
negative values where relevant
maximum values where relevant
missing values
invalid values
```

For dates:

```text
day before
effective date
day after
period boundary
assessment-period boundary
```

For categorical rules:

```text
every permitted category
every excluded category
unknown category
missing category
```

Do not rely only on examples found in the PDFs.

Use the formalised rules to derive additional tests.

---

# 31. Regression testing and amendments

When a new source version or amendment is incorporated:

1. identify affected propositions;
2. identify affected rules;
3. identify affected calculations;
4. identify affected Java components;
5. identify affected tests;
6. run the complete regression suite;
7. report behavioural changes.

Do not regenerate the entire system blindly if a change can be isolated.

Produce a change-impact report.

---

# 32. Human review gates

Do not proceed automatically through every stage.

Require review at these boundaries:

```text
Source extraction
       ↓ REVIEW

Terminology
       ↓ REVIEW

Propositions
       ↓ REVIEW

Rules
       ↓ REVIEW

Calculations
       ↓ REVIEW

Domain model
       ↓ REVIEW

API model
       ↓ REVIEW

Java implementation
       ↓ TEST / REVIEW
```

At minimum, the following must be explicitly reviewable:

- interpretation;
- ambiguity;
- contradiction;
- precedence;
- calculation logic;
- temporal applicability;
- amendment effects.

---

# 33. AI behaviour rules

When working on this project:

### Never:

- invent a rule;
- silently resolve ambiguity;
- silently resolve contradictions;
- replace source terminology without justification;
- assume the latest document applies retrospectively;
- ignore amendment documents;
- discard tables;
- discard examples;
- omit provenance;
- implement an unsupported interpretation as fact;
- claim complete coverage without measuring it.

### Always:

- cite source passages internally;
- preserve stable IDs;
- distinguish fact from interpretation;
- distinguish rule from calculation;
- model exceptions explicitly;
- model temporal applicability;
- identify uncertainty;
- maintain traceability;
- generate tests;
- report gaps.

---

# 34. Deliverables

Produce the following artefacts.

## A. Source manifest

```text
sources/manifest.okf
```

## B. Normalised source corpus

```text
sources/
```

## C. Terminology model

```text
terminology/
```

## D. Evidence and propositions

```text
evidence/
propositions/
```

## E. Business rules

```text
rules/
```

## F. Calculation model

```text
calculations/
```

## G. Temporal/amendment model

```text
versions/
amendments/
```

## H. Domain model

```text
model/
```

## I. API model

```text
api/
```

## J. Source-derived scenarios

```text
scenarios/
```

## K. Traceability matrix

```text
traceability/
```

## L. Validation reports

```text
validation/
```

## M. Java implementation

```text
java/
```

## N. Automated test suite

```text
java/src/test/
```

---

# 35. Recommended execution sequence

Execute the project in these phases.

### Phase 1 — Discovery

Inspect the GOV.UK publication page and construct the source manifest.

Do not begin Java development.

### Phase 2 — Acquisition

Acquire and normalise all relevant PDFs.

### Phase 3 — Extraction

Extract structured source passages while preserving page and paragraph provenance.

### Phase 4 — Terminology

Build the canonical glossary and conceptual model.

### Phase 5 — Evidence

Identify rule-bearing passages and create evidence objects.

### Phase 6 — Propositions

Convert evidence into normative propositions.

### Phase 7 — Rule extraction

Convert validated propositions into atomic business rules.

### Phase 8 — Calculations

Model calculation algorithms independently of Boolean decision rules.

### Phase 9 — Temporal/version analysis

Model amendments, effective dates, transitional provisions and rule precedence.

### Phase 10 — Scenarios

Extract examples and construct source-derived tests.

### Phase 11 — Validation

Run coverage, contradiction, ambiguity and dependency analysis.

### Phase 12 — Domain model

Derive the data/domain model.

### Phase 13 — API

Derive the API model and contract.

### Phase 14 — Java design

Design the Java architecture from the validated knowledge model.

### Phase 15 — Implementation

Implement the rule engine, calculations, domain model, provenance and API.

### Phase 16 — Testing

Generate and execute the complete source-derived and generated test suite.

### Phase 17 — Traceability

Verify that every important Java behaviour maps back to an OKF rule and source passage.

---

# 36. Definition of done

Do not declare the project complete merely because the Java application compiles.

The project is complete only when:

- the relevant source corpus has been catalogued;
- source passages retain provenance;
- terminology has been formalised;
- business rules have been extracted;
- calculations have been formalised;
- temporal applicability has been modelled;
- amendments have been incorporated;
- exceptions have been represented;
- contradictions and ambiguities have been identified;
- domain concepts have been modelled;
- the API reflects the domain terminology;
- every implemented rule has a stable rule ID;
- every significant rule has source provenance;
- source examples have become automated tests;
- boundary tests exist for important numerical/date rules;
- traceability is available from Java → rule → source;
- the validation report contains no unexplained critical issues.

Any remaining uncertainty must be explicitly documented.

---

# 37. First task

Do not start by writing Java.

First inspect the GOV.UK publication page:

https://www.gov.uk/government/publications/decision-makers-guide-vols-13-and-14-state-pension-credit-staff-guide

Construct the source manifest and report:

1. every substantive chapter;
2. every amendment/change document;
3. publication/update dates;
4. chapter/version relationships;
5. apparent effective-date information;
6. dependencies between chapters;
7. any immediately apparent gaps or ambiguities in the source collection.

Then propose the initial OKF schema.

Do not proceed to rule extraction until the source inventory and schema have been reviewed.