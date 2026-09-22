# Staff-question semantic coverage audit

Read-only triage against `bd94537742aeab0dcd016efaf04f898ef84c7f8e`. Machine-readable ledger: [okf-dwp-semantic-coverage-audit.json](okf-dwp-semantic-coverage-audit.json). No acquisition, model trial, source mutation or specialist legal acceptance was performed.

## Main finding

The logical-unit source partition is complete as byte accounting, but the task model is not. Only **3 of the 40 supplied question occurrences** activate a logical-unit requirement in the retained 512 KiB evaluation: `staff-012`, `staff-013` and `staff-023`. **37 have no active logical-unit task profile; 24 return no relationships. All 40 remain insufficient.** There are 39 distinct questions; `staff-026` and `staff-033` are intentionally identical occurrences.

This is an explicit migration gap. `scripts/logical_context_profiles.py` retains old concepts and concept-to-concept relationships, but deliberately does not pretend that page requirements are satisfied by a fragment. Five new scoped profiles exist; they do not replace the 40 earlier staff development profiles. The ledger preserves all **203 old obligations** and maps every question to its exact current result, declared concepts, old requirement, candidate evidence, proposed next cluster and learning lessons.

There are **49,680 units**, **46 with agent-authored boundaries**, and **49,634 uncertain machine candidates**. Those totals cannot be reported as semantic review coverage.

## Next independent source-review groups

| Order | Group | Primary staff occurrences | Reason |
|---|---|---|---|
| 1 | PC entitlement, inputs, capital and income | 006, 010, 015, 016, 019, 020, 021, 022 | Eight questions share the Chapter 77 gateways/formulas, Chapter 84 deemed capital income and Chapter 85 income treatment. Complete cross-page passages and scoped dependencies provide more value than more aliases. |
| 2 | Partner, household and mixed-age | 014, 017, 018 | Chapter 77 references and household definitions are not equivalent to general partner effects. `staff-018` omits a benefit in its exact standalone question; do not silently insert PC from its section. |
| 3 | Existing care-home profiles | 012, 013 | Four declared paths survive, but funding, continued qualifying payments, household and housing-cost requirements remain open. PIP is a conditional qualification route, not universal care-home evidence. |
| 4 | Carer’s Allowance conditions/multiple caring | 038, 040 | Chapter 60 explicitly separates one carer/multiple people (60044) from multiple carers/one person (60026). Both need the full caring/qualification chain. |
| 5 | Child DLA to PIP | 026, 033 | P5 definitions, child invitation exceptions, claims and continuity are acquired but not authored into task units. Preserve duplicate-package equality. |
| 6 | PIP pension-age continuation | 032 | P1013 is a gateway. Actual P4 age exceptions are P4076–P4086 and revisions P4087 onward. |
| 7 | State Pension regime/age/components | 002, 004 | Separate age schedule, entitlement, claim, payment and pre/post-2016 regimes. |
| 8 | Dated rates and additions | 007, 008, 009 | Scope the time period, preserve SDA ambiguity, and review complete tables. Memo 02/26 points outside the frozen excerpt to a separate rate schedule. |
| 9 | Abroad | 001, 023 | Keep existing PC evidence. Generic “benefits” remains unbounded; existing PC/UC/SP/PIP-branch passages do not cover every benefit. |
| 10 | IIDB pension-age distinction | 025 | Do not transfer Reduced Earnings Allowance pension-age provisions to IIDB. |
| 11 | Directional interaction matrix | 003, 005, 011, 024, 027–031, 034–037, 039 | Split by benefit variant/component, own award versus cared-for person, entitlement, payment, income and passported additions. This broad group needs several bounded pairs. |

These are triage priorities, not a promise to close legal applicability. The existing eight unresolved references are assigned to a separate reviewer and are not closed here.

## PIP correction that must survive implementation

Existing authored P4 passages concern **institutional payment and linking periods**, not pension-age exceptions. Existing P5 `P5093–P5097` concerns **transfer while in hospital or a care home**, not general child-DLA transition. `P5106` covers transfer while temporarily abroad. These passages must not be used to give a broad child-transition or pension-age profile the appearance of completeness.

The actual acquired P4 PDF pages 13–15 contain P4076–P4084; the further-claim section cites memo ADM 6/25. P4 pages 18–19 contain mobility revision/supersession restrictions. P5 page 6 contains P5018–P5020; page 7 adds the material under-18 hospital exception at P5021 and its two examples. Stopping at page 6 would repeat the original page-boundary error.

## Exact evidence and limits

The JSON verifies all 42 old candidate PDF/page bindings and excerpt hashes, translates their Unicode offsets to UTF-8 spans, and maps overlaps to actual versioned logical IDs. **An overlapping unit is still candidate evidence, not a semantically reviewed equivalent.** Every case retains its required-evidence statements and ambiguities.

The current observed results come from the bound `evaluation/logical-units/run/summary.json`; this audit did not invoke an evaluator or infer the IDs of selected records that are not in that summary. Historical registry scope-gap strings are preserved, but old “ADM not acquired” wording must not be repeated as a current census claim.

## Learning-path preservation

Preserve all question hashes, duplicate occurrences, `pXX-sXX` lesson IDs and `/learning/pXX/sXX` routes. The ledger lists each lesson’s exact evidence routes. Most currently point to frozen page records; retain those as source locations and add versioned unit references. Do not silently retarget a page assessment to a newly interpreted unit, replace old evidence IDs, or rewrite earlier assessments. Root programmes and generated `docs/learning/question-coverage.json` must remain consistent.

## Independent CI review

The separate three-file capacity repair in `/Users/crpage/tmp/okf-dwp-ci-capacity` was reviewed: **no blockers**. It changes the aggregate CI allowance from 30 to 45 minutes only, drops no checks, and documents the cancelled exact-merge run and skipped Pages without treating the timeout change as successful publication.
