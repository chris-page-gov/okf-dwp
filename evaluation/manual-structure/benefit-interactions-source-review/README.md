# Benefit interaction source-reading proposal

This independent, experimental source-selection proposal adds **78 complete retained units from 10 frozen documents**, **12 conditional profiles** and **132 declared guarded paths**. It does not change a source, paragraph boundary, inherited requirement, deployed service or default corpus. It is agent source-reading, **not specialist acceptance** or proof of legal answerability.

The authored input is [benefit-interactions.yamlld](../../../domain-profile/structured-units/benefit-interactions.yamlld). This relative link resolves through GitHub when reading the source tree; the linked file is the input, not a generated answer.

## What was read

[Source-read record](source-read.json) retains the full text of every selected unit with exact source, catalogue, record and byte-span identities. [Source identities](source-identities.json) keeps frozen PDF and extraction paths, acquisition observations, declared date limits and publication-family metadata separate. All 78 PDF/extraction hashes, exact literal spans and complete joined unit texts passed the local control.

[DMG Chapter 17 PDF page 10](dmg-ch17-pdf-10.png) and [page 11](dmg-ch17-pdf-11.png) were rendered from the frozen PDF and visually inspected. Paragraph 17085 is a complete two-page table. The RP/ESA/CA row continues across pages; the PIP daily living row refers to specified attendance benefits. Its `18092` citation differs from paragraph 17086's `17092` route. The source discrepancy is retained as an unresolved obligation.

The six examples in DMG 71776 remain one complete three-page unit. No example is clipped to fit a desired answer. Existing machine boundary uncertainty remains attached to all selected units; complete retained text is not proof of complete legal scope.

Independent review also identified different US wording: DMG 64020 says no new claims from 8 April 1987; DMG 28065 and 51033 say removed from the scheme on 6 April 1987, with continued payment possible. The proposal retains both as potentially different events requiring reconciliation, not one corrected closure date.

## Staff-question coverage proposed

| Staff case | Conditional profile | Evidence supplied | What remains open |
| --- | --- | --- | --- |
| 024 | IIDB and additional benefits | Industrial scheme components; CAA primary conditions; REA conditions | No exhaustive additional-benefit list; full supplement conditions, individual facts and dates |
| 025 | IIDB and pension age | IIDB/REA/RP distinction; later REA/RA transitions; first-claim qualification, employment examples and restrictions | Earlier/frozen REA branches, exact pension regime, individual award and date-specific rates |
| 027 | IIDB and JSA | JSA(IB) income treatment and attendance exceptions; separate overlap definitions | Concurrent entitlement, contribution/New Style variant and remaining income qualifications |
| 028 | IIDB and ESA | ESA(IR) income treatment and attendance exceptions; separate overlap definitions | Concurrent entitlement, contribution/New Style variant and remaining income qualifications |
| 030 | IIDB and PIP | Distinct schemes, PIP components and specific attendance adjustment | Full assessment conditions, exact industrial supplement and payment sequence |
| 031 | PIP and additional benefits | CA qualifying-benefit route; no-partner PC severe-disability route | No exhaustive passporting list; claimant/carer distinction, PC conditions and household exceptions |
| 034 | PIP and JSA | Explicit component disregard in JSA(IB) | Full JSA/PIP entitlement, variant and memo reconciliation |
| 035 | PIP and ESA | Explicit component disregard in ESA(IR) | Full ESA/PIP entitlement, variant and assessment conditions |
| 037 | PIP and War Pensions attendance | Complete adjustment table, scheme and component distinctions | Ambiguous scheme name; no date/rates; no weekly calculation or all-variation claim |
| 038 | CA introductory conditions | Caring, qualifying benefit, breaks, earnings timing, age and education qualifications | Residence, full earnings/education/devolved rules, memo overlays and individual facts |
| 039 | CA and interactions | Named income effects, overlap, underlying entitlement and cared-for person's PC effects | Unbounded other benefits; direction, full adjustment, household exceptions and dates |
| 040 | CA and multiple cared-for people | Complete dated hours-aggregation rule; distinct multiple-carer election case | Actual care pattern, full other conditions and no inferred multiple-award amount |

These are source-selection scopes, not twelve passed answer-quality cases. The current task inputs lack facts needed for a lawful award decision. Every profile keeps applicability, legal-version and specialist-review obligations plus its own unresolved branches. The previous 40 staff requirements and 203 obligations are untouched.

## Reproduce the bounded checks

Use the repository's locked environment:

```sh
.venv/bin/python -m unittest discover -s scripts -p 'test_structured_benefit_interactions.py' -v
```

[Four passing controls](tests.txt) check frozen source/PDF/span conservation, exact conjunction guards and inherited-data preservation, cross-page examples and contrasting care cases, and retained source/rate uncertainty. They call the pure selection compiler against the frozen baseline; they do not run a model, acquire material, rebuild a corpus or replay Ask OKF.

The initial test adapter guessed the full-DMG path for Chapter 78 and failed. It was corrected to use the exact hash-bound inventory path, which preserves the reused pilot source. [Initial failure](initial-control-failure.txt) remains recorded.

## Integration boundary

This file alone is inactive. Register it explicitly only after independent review, preserve exact source identities and all guard conditions, then rebuild and freeze the additive structured projection. Evaluate the resulting contexts separately for source selection, traversed paths, unresolved obligations and answerability. A profile resolving a question is not evidence that every required item fits the delivery budget.
