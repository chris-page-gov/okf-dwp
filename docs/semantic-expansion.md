# Staff-question semantics and evidence requirements

This stage addresses **DWP-BL-005** (neutral domain concepts) and **DWP-BL-007**
(task-specific evidence requirements). It implements the reviewable modelling
work for the supplied questions. Independent specialist approval and complete
legal applicability remain outstanding. These are separate acceptance gates,
not missing implementation hidden behind a general “semantic modelling” label.

## Start with the practical difference

Previously, the phrase **Pension Credit** could resolve to a *prisoner credit
rates* concept. JSA and ESA had similar custody-specific aliases. That worked
for the first imprisonment demonstration but was a poor starting point for
questions about savings, partners, care homes or benefit interactions.

The new, additive projection resolves these names to neutral benefit concepts.
It distinguishes variants, components, circumstances, assessment inputs,
entitlement and payment. The custody concepts and their evidence remain in the
graph, with their specific labels. The old published projections are unchanged.

A **concept** is an explicitly named meaning, such as Pension Credit or capital.
An **alias** is wording that the resolver may recognise for that meaning.
An **assertion** is a directed relationship with its own status and provenance.
A **profile** declares the evidence and unresolved obligations for a task.
These are inspectable project proposals; they are not official DWP interpretations.

## Required support for a summary

A reference helps a reader find related material. A **required dependency** says
that an interpretation needs particular material to be inspected with it. The
[initial household checkpoint](household-qualification-budget-review.md#additive-authoring-implementation)
uses the existing `dcterms:requires` relationship for that purpose. Seven captured
pages support the complete household summary; the care-home overview also
requires that summary. The [component follow-up](carehome-component-dependency-review.md)
adds five housing-cost and two temporary-residence page dependencies: 15 support
relationships in total. Staff 012 and 013 declare the household and housing-cost
paths explicitly. Temporary-residence support stays attached to its own summary,
without becoming mandatory for every permanent-care-home question. These
declarations remain project-authored and unreviewed.

The [disability-addition increment](disability-addition-qualification-review.md)
adds 14 dependencies: four pages for the limited overview and ten for the
no-partner explanation. These groups preserve receipt exceptions, partner-only
patient scope and dated memo qualifications. Staff 012 and 013 investigate the
branch conditionally; its inclusion does not establish the claimant's household
status. The support census is now 29, with two captured pages newly selected
into the semantic index.

The [joint comparison](../validation/qualification-context/2026-09-21/README.md)
verifies that the generic allocator retains the declared paths within its budget.
It runs DWP `7f9feb9634e3d94004853b838462aca132c505a5` with Explorer
`c4f2de0a99b7bc2f8b8c8a06a3c715fb56b66d8e`, separately from the earlier public
service. The final pair retains all 433 activated path occurrences at 256 KiB
and 512 KiB, including all seven household pages for Staff 012 and 013. This is
bounded evidence retention, not complete domain modelling. All 203 obligations
remain open; protected publication and fresh public checks remain pending.

## What is implemented

| Item | Delivered scope |
| --- | --- |
| Authored concepts | 51, including neutral benefits, variants, components and circumstances |
| Source-grounded conceptual associations | 254, including directed source references, qualified concept relationships and 29 explicit support dependencies |
| Selected exact source pages | 98 across DMG and ADM, with PDF/extraction hashes and page locators |
| Legislative references in Ask | 44 staff-linked provision identities, 62 source-page citation links and one separately recorded metadata bridge |
| Selected statutory bodies | 20 complete selected units and 43 evidence-bearing navigation links; derived and unreviewed |
| Staff task profiles | 40 occurrences, preserving all 39 distinct questions and the repeated DLA/PIP question |
| Explicit open obligations | 203, across five named categories |
| Existing discovery graph | All 712 original record identities and 1,105 assertion identities retained |
| Current source candidate index | 903 records and 1,464 assertions; 4,683,061 bytes, within the 8 MiB semantic-index limit |

The current source candidate is `dwp-staff-semantics-91e16565bd7c97e72f3b`, with
index SHA-256 `8aea634f7623a61475156a116fcebf2ae64cbb4b17507a731a7de73edee0ddd7`.
Its current 40-case evaluation retains 177 of 177 candidate occurrences at
512 KiB. The richer care-home requirements no longer all fit 256 KiB: the
package exposes missing support. The earlier four-cell comparison above retains
its separate 901-record source and does not attest this larger increment.
The initial household-dependency checkpoint had 1,435 assertions. The earlier
public service source `3ef0e786…` had 1,427 assertions and a 4,581,721-byte index;
its immutable linked evaluation remains an observation of those earlier bytes.

The concepts are authored in
[domain-profile/staff-semantic](../domain-profile/staff-semantic/).
They are kept outside the legacy knowledge-folder scan because adding inputs
there would change the identities of the frozen pilot and its dependent
releases. This follows the separate additive navigation pattern.

The [catalogue](../evaluation/semantic-expansion/catalogue.json) records each
definition, type, source-page association, alias reassignment and projection
refinement. Source text remains the exact whole-page extraction. Adjacent-page
links are explicit: the page next door is available in the full corpus but
is not silently treated as selected or reviewed.

## Relationships carry qualifications

Examples include:

- State Pension is distinguished from its new and earlier Retirement Pension
  regimes, with DMG 74001 as the source route.
- Guarantee Credit and Savings Credit retain distinct assessment dependencies.
- Housing Benefit's treatment as income in Pension Credit is separate from
  Housing Benefit eligibility and housing-cost additional amounts.
- Carer’s Allowance and the Pension Credit carer additional amount are linked
  through their stated conditions; payment and underlying entitlement are
  separate questions.
- PIP daily living is linked to the named qualifying-benefit conditions,
  without asserting automatic entitlement to another benefit.
- JSA and ESA variants are explicitly represented. The broad benefit label
  does not choose a variant.
- PIP upper-age and DLA-transition research has direct source routes into
  ADM P1, P4 and P5. This corrects the earlier reliance on a DMG AA/DLA
  page as a candidate for those questions.

These associations use established SKOS relationships and Dublin Core
references. SKOS is a vocabulary for describing concepts; Dublin Core
provides general metadata relationships. A broader-concept relationship is
a navigation hierarchy, not an executable legal rule or an OWL class axiom.

~~~mermaid
flowchart TD
    Staff["39 distinct staff questions<br/>40 recorded occurrences"]
    Concepts["51 model-authored concepts<br/>benefit, variant, component, circumstance"]
    Profiles["40 proposed task profiles"]
    Relations["232 source-grounded associations<br/>including 15 explicit support dependencies"]
    DMG["Frozen DMG source pages<br/>exact text, hashes and PDF locators"]
    ADM["Frozen ADM source pages<br/>including PIP age and transition guidance"]
    Legal["44 verified provision references<br/>metadata only"]
    Bodies["20 selected dated statutory units<br/>derived and unreviewed"]
    Open["203 named open obligations<br/>scope, closure, applicability, law version, review"]
    Package["Bounded inspectable context<br/>remains insufficient"]
    Staff --> Concepts
    Staff --> Profiles
    Concepts --> Relations
    Relations --> DMG
    Relations --> ADM
    DMG -->|"62 citation links"| Legal
    Legal -->|"explicit source-backed references"| Bodies
    Bodies --> Package
    Profiles --> Open
    Relations --> Package
    Profiles --> Package
    Open --> Package
~~~

## Why the result still says insufficient

The [profile register](../evaluation/semantic-expansion/profiles.json) separates:

| Obligation category | Meaning |
| --- | --- |
| evidence_closure_unverified | Candidate pages exist, but all necessary conditions, continuations and exceptions have not been established |
| question_scope_unresolved | The question leaves material choices open, such as date, variant, territory or what “all” includes |
| applicability_unresolved | Applicability to the agreed regime and time has not been established |
| legal_version_unreconciled | Verified legal identities are available, but the relevant law, amendments and effects have not been reconciled |
| independent_review_pending | An attributable specialist has not approved the meanings or evidence requirements |

Each obligation has a stable identifier, a readable label and a resolution
action. The identifier is intentionally absent from source evidence. Retrieving
a page, a legal hyperlink or a second model opinion cannot fabricate its
completion. The requirements checker consequently reports the missing
obligation rather than declaring a complete answer.

**SDA remains deliberately ambiguous.** It may mean Severe Disablement Allowance
or informal shorthand for a Pension Credit severe-disability additional amount.
The resolver shows both candidates instead of choosing silently. “War Pensions
Constant Allowance” also retains its unresolved scheme-name boundary.

The earlier legal reference nodes remain scope records labelled **reference-only-unreviewed**. The new [statutory-body increment](legal-body-evidence.md) adds separate derived evidence records for 20 selected units, connected through 43 source-backed references. A metadata record does not become source text, and a source passage does not establish applicability. All 203 obligations remain open. The separate [legal reconciliation](legal-reconciliation.md) retains the earlier identity and footnote work.

## Current source-only comparison

The [current evaluation](../evaluation/semantic-expansion/evaluation.json) compares
the original discovery base with the final semantic source using the same
Explorer `c4f2de0a…` engine. This differs from the four-cell joint comparison,
which also changes the engine independently. Both preserve their input hashes.

Both runs use the **same shared Explorer engine, budgets and frozen lexical
shards**. Only the explicitly authored semantic base differs.

| Diagnostic | Before | After |
| --- | ---: | ---: |
| Known candidate-page hits across the 40 occurrences | 12 of 177 | 177 of 177 |
| Questions retaining at least one candidate page | 12 of 40 | 40 of 40 |
| Own declared task profile activated | 0 | 40 of 40 |
| Contexts declared sufficient | 0 | 0 |
| AI answers or specialist approvals produced | 0 | 0 |

This is a **development-case comparison**: the supplied questions and candidate
pages were known during modelling. It is not a held-out accuracy result.
A page hit does not prove the page supports a claim or supplies every exception.
The earlier released staff model retained 169 of 177 candidates. The separate
[ambiguity/loading experiment](context-performance.md) retained 171, and the
[immutable household-source evaluation](https://github.com/chris-page-gov/okf-dwp/blob/3ef0e786e9a18e76fa17c7d925ff509d6d6c9f84/evaluation/semantic-expansion/evaluation.json)
retained 176. Those historical counts do not refer to the newly regenerated
local evaluation. The current candidate retains all 177 occurrences, including
the formerly omitted Staff 005 page, while all 43 evidence-closure obligations
remain open. These are distinct development comparisons, not accuracy scores.

Every after-run also contains ADM pages and reports truncation. **ADM presence
is not a relevance score.** The lexical stage finds broad matches in both
manuals, and traversal may supply additional source paths. The receipt separates
all ADM pages from those reached by a semantic path and reports actual truncation
codes. Candidate, node, relationship and byte limits remain visible.

[Full comparison and controls](../evaluation/semantic-expansion/evaluation.json) ·
[Exact before/after context archives](../evaluation/semantic-expansion/cases/)

Ten shared-engine controls cover neutral resolution, explicit SDA ambiguity,
no results, missing source evidence, reversed relationships, three paraphrases,
the original imprisonment routing question and a counterfactual entitlement
premise. Thirty-one producer controls check source hashes, exact spans, all
question occurrences, qualification dependencies, legal-reference boundaries,
preserved scopes and rejected governance/authoring mutations.

## Context sizes and practical limits

A **byte budget** limits the complete returned package: passages, relationships,
question interpretation, missing-evidence diagnostics and provenance all count.
The shared engine now includes requirement diagnostics before trimming records.
Previously, it could trim until the records fitted, append the diagnostics and
then discard everything as an oversized result. The generic fix retains whole
passages that fit and still refuses when metadata alone exceeds the budget.
It does not shorten evidence text or suppress missing obligations.

The reproducible `budget_observations` in the evaluation receipt cover four
staff questions also used in earlier model trials. These are new engine/source
observations, not replacements for their frozen trial inputs:

| Case | At 64 KiB: records / relationships | At 256 KiB: records / relationships |
| --- | ---: | ---: |
| staff-006 | 4 / 3 | 41 / 46 |
| staff-012 | **0 / 0: metadata refusal** | 27 / 63 |
| staff-026 | 11 / 1 | 54 / 41 |
| staff-038 | 9 / 2 | 41 / 41 |

All eight packages remain **insufficient** and disclose truncation. At 64 KiB,
Staff 012 returns a **1,926-byte `metadata_budget` refusal**: its interpretation
and evidence obligations cannot fit, so no records, relationships or requirements
are returned. The other seven observations retain non-empty evidence. A zero-record
refusal does not mean that the source has no requirements; the independent joint
harness counts activated authored requirements before output trimming.

At 256 KiB, Staff 012 retains its seven household support pages. The separate
512 KiB joint observation retains 62 records and 124 relationships, but also
reports a missing `temporary-care-home` → `page/78/0024` dependency. That optional
summary is not an unconditional requirement of the permanent-care-home profile.
The no-partner and severe-disability overview dependency expansions remain open.
These sizes are observations for these questions and this snapshot, not a
universal minimum. One question can activate several task profiles when their
concept conditions overlap: these four activate 4, 3, 2 and 1 respectively.
Profile activation is a conservative evidence obligation, not a relevance score.

## Reproduce

Use the locked environment and an Explorer checkout containing the corpus
context engine:

~~~sh
uv sync --locked
# Use a separate Explorer checkout at the recorded consumer version.
git clone https://github.com/chris-page-gov/okf-explorer.git ../okf-explorer-staff
export EXPLORER_STAFF_ROOT="$(cd ../okf-explorer-staff && pwd)"
git -C "$EXPLORER_STAFF_ROOT" checkout c4f2de0a99b7bc2f8b8c8a06a3c715fb56b66d8e
uv run --locked python scripts/build_staff_semantic.py --check
uv run --locked python scripts/test_staff_semantic.py
node --experimental-strip-types scripts/evaluate_staff_semantic.mjs \
  --explorer-root "$EXPLORER_STAFF_ROOT" --check
~~~

Without the check flag, the two build/evaluation commands write their additive
outputs. The evaluation makes no network or model calls. Its local fake-origin
fetcher serves only hash-bound repository files; it is not a public deployment
observation. The receipt records the exact engine file hashes.

The current evaluation is rebuilt when source-metadata or authored-input bytes
change, even if their meanings and selected evidence stay the same. The paired
model trials retain their original [archived assembly index](../evaluation/model-comparison/staff-2026-09-20/input-snapshots/assembly-index.json)
and exact context packages. Their answers were not rerun after the legal
metadata publication projection and whitespace-only YAML clean-up. Replaying
those trials checks the archived inputs; it does not claim they used the newer
current snapshot.

The index is compact JSON. The first staff projection shortened one repeated generic discovery scope string in the **new projection only**. The household projection preserves this declared normalisation and whole source pages; it requires the explicitly tested 8 MiB semantic-index bound. Ordinary search and record shards remain limited to 4 MiB each; returned packages keep their existing limits. The catalogue retains the exact before/after mapping.
Specialised custody scopes, source text, source hashes, provenance and the
original frozen index remain unchanged.

## Remaining modelling work

The bounded staff-question model is now implemented and executable. A complete
departmental knowledge model is not claimed. Remaining work includes:

1. Specialist review of meanings, alias choices and task requirements.
2. Closing each profile's source-continuation, exception and scope gaps.
3. Applicable legislation, effects, commencement, territorial and case-law review.
4. Additional task families and genuinely held-out question evaluation.
5. More precise relation types or rule models where reviewed evidence justifies
   them; current SKOS associations do not implement a benefits engine.
6. Further retrieval selection and evidence-size work without concealing
   truncation or weakening the completeness boundary.

These acceptance gates should stay separately visible in the backlog rather
than being collapsed into either “done” or “broader modelling incomplete”.
