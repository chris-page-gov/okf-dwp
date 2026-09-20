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
[household qualification increment](household-qualification-budget-review.md#additive-authoring-implementation)
uses the existing `dcterms:requires` relationship for that purpose. Seven captured
pages support the complete household summary; the care-home overview also
requires that summary. The two care-home task profiles declare the resulting
paths explicitly. These declarations remain project-authored and unreviewed.

This makes an omitted qualification detectable. It does not make a small context
package complete: a separate allocator must retain the paths within its budget,
or report the missing support. All 203 existing obligations remain open.

## What is implemented

| Item | Delivered scope |
| --- | --- |
| Authored concepts | 51, including neutral benefits, variants, components and circumstances |
| Source-grounded conceptual associations | 217, including directed source references and qualified concept relationships |
| Selected exact source pages | 96 across DMG and ADM, with PDF/extraction hashes and page locators |
| Legislative references in Ask | 44 staff-linked provision identities, 62 source-page citation links and one separately recorded metadata bridge |
| Selected statutory bodies | 20 complete selected units and 43 evidence-bearing navigation links; derived and unreviewed |
| Staff task profiles | 40 occurrences, preserving all 39 distinct questions and the repeated DLA/PIP question |
| Explicit open obligations | 203, across five named categories |
| Existing discovery graph | All 712 original record identities and 1,105 assertion identities retained |
| New context index | 901 records and 1,427 assertions; 4,581,721 bytes, within the new 8 MiB semantic-index limit |

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
    Relations["217 source-grounded associations<br/>SKOS and Dublin Core"]
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

## Measured before and after

Both runs use the **same shared Explorer engine, budgets and frozen lexical
shards**. Only the explicitly authored semantic base differs.

| Diagnostic | Before | After |
| --- | ---: | ---: |
| Known candidate-page hits across the 40 occurrences | 12 of 177 | 176 of 177 |
| Questions retaining at least one candidate page | 12 of 40 | 40 of 40 |
| Own declared task profile activated | 0 | 40 of 40 |
| Contexts declared sufficient | 0 | 0 |
| AI answers or specialist approvals produced | 0 | 0 |

This is a **development-case comparison**: the supplied questions and candidate
pages were known during modelling. It is not a held-out accuracy result.
A page hit does not prove the page supports a claim or supplies every exception. The previous released staff model retained 169 of 177 candidates. The separate [engine-only experiment](context-performance.md) retained 171; the expanded household candidate retains 176. One candidate in staff-005 remains omitted under the node bound. These are distinct comparisons, not an answer-accuracy score.

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
premise. Twenty-two producer tests check source hashes, exact spans, all question
occurrences, legal-reference boundaries, preserved scopes and rejected
governance/authoring mutations.

## Context sizes and practical limits

A **byte budget** limits the complete returned package: passages, relationships,
question interpretation, missing-evidence diagnostics and provenance all count.
The shared engine now includes requirement diagnostics before trimming records.
Previously, it could trim until the records fitted, append the diagnostics and
then discard everything as an oversized result. The generic fix retains whole
passages that fit and still refuses when metadata alone exceeds the budget.
It does not shorten evidence text or suppress missing obligations.

The reproducible `budget_observations` in the evaluation receipt cover four
staff questions used for the paired model trial:

| Case | At 64 KiB: records / relationships | At 256 KiB: records / relationships |
| --- | ---: | ---: |
| staff-006 | 3 / 0 | 43 / 47 |
| staff-012 | 4 / 0 | 35 / 50 |
| staff-026 | 11 / 0 | 54 / 41 |
| staff-038 | 8 / 0 | 41 / 41 |

All eight packages remain **insufficient** and disclose truncation. At 64 KiB,
retained lexical passages do not retain the semantic paths; this is a poor
budget for demonstrating relationship-led interpretation of these tasks.
The 256 KiB trial budget preserves useful paths, while retaining its omissions.
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
git -C "$EXPLORER_STAFF_ROOT" checkout 0e6a639f87c4060123b72d82c1ebe30405d475f1
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
