# Restoring the original custody acceptance case

This is an independent experimental publication, not official DWP guidance. The work below proposes source navigation and research context. It does not decide entitlement or establish current law.

## Why a separate check was needed

The original difficult question concerned imprisonment and four benefits: Jobseeker's Allowance (JSA), Income Support (IS), State Pension Credit (SPC) and Employment and Support Allowance (ESA). It asked for the difference between entitlement, payment and the benefit-specific consequences.

The later 40 staff questions are a different evaluation set. Passing their delivery checks does not establish that the original question still works. In the new structured corpus, the nine original expected concepts survived and all 33 original PDF source entries matched the captured document hashes. However, only seven of 27 expected assertions survived. Those seven joined concepts; none of the original expected concepts had an outgoing unit-evidence route. The four original requirements applicable to the broad question were absent.

The cause was the earlier concept-only projection: it retained concept records and concept-to-concept relationships, then introduced separately authored unit profiles. It omitted the original page/document routes and custody profiles. This was a semantic migration gap, not an absence of the captured PDF material.

The [bound baseline review](../evaluation/manual-structure/original-acceptance/baseline-review.json) preserves the exact inspected source, index and case identities. It makes no new assembly, model or acquisition calls.

## What the additive translation proposes

The [authored translation](../domain-profile/structured-units/custody-restoration.yamlld) keeps three separate layers:

1. **Original expectations:** all six historical custody requirements remain unchanged. The original question used four; the other two cover the separately named ESA variants. Original page identifiers and source expectations are not silently replaced with unit identifiers.
2. **Location mapping:** the 33 original PDF page locations intersect 137 complete retained source units. This mapping is navigation, not a declaration that all those units are relevant or legally complete. Seven old paragraph selectors fail to identify a governing paragraph at their stated locations; they remain explicit unresolved observations.
3. **Source-read selection:** six new scoped profiles select a narrower union of 53 whole units. They preserve the primary rules, named qualifications and complete examples read for this increment. Each profile retains four open obligations covering regime/date, remaining qualifications, boundaries and specialist/legal review. Other mapped units remain outside this selection and are listed separately.

Every new route requires an actually resolved imprisonment concept. Benefit-specific selections also require the relevant neutral benefit concept. Merely asking about Pension Credit, JSA, IS or ESA does not activate these routes. Broad benefit names are not restored as aliases of custody-specific meanings.

## Source distinctions that must remain visible

- **DMG 12003 refers to “these benefits”.** Its list is at 12002. The translation adds an explicit source-context dependency between these two whole units. The payability statement does not establish a blanket rule that entitlement to every benefit survives imprisonment.
- **DMG 12015 names Chapters 24, 78, 53 and 54.** Four literal routes lead to the exact historical document scope records. No route fans out to every paragraph in a chapter or claims that chapter membership establishes applicability.
- **The benefits use different mechanisms.** The selected text includes legacy JSA availability and its limited 96-hour exception; IS applicable amounts and remand/hospital qualifications; separate Guarantee Credit and Savings Credit provisions; and ESA suspension, disqualification, limited capability for work and entitlement-day qualifications. These are source-reading selections, not new legal conclusions.
- **Examples and exceptions matter.** The selection retains the whole examples carried by the selected units, including the ESA examples explaining different payment and entitlement effects. Omitted definition and exception branches remain named gaps, not assumed irrelevant.
- **DMG 12016 routes other regimes to ADM.** The old profile said ADM bodies had not been acquired. That statement describes the older release. The later corpus contains ADM, including U6 and its U6060–U6062 custody passages; current-regime reconciliation remains separate work.
- **Catalogue statements are dated observations.** The captured Memo 07/20 removal statement and ADM M1 title remain exact text under distinct scope identifiers. Neither supplies a memo body, establishes current law or means that all ADM material is absent from the later corpus.

## Hospital is a separate boundary

The original hospital fixture was explicitly an evidence-gap control for the custody-only index. It was not a previously sufficient hospital answer. All ten PDFs in the later hospital source-review record are present with matching hashes, but this custody translation does not create a complete four-benefit hospital profile.

## Verification and integration boundary

The pure [compiler](../scripts/structured_custody_restoration.py) returns an additive semantic index and a translation ledger. Its focused tests check exact source and record bindings, unchanged inherited concepts and requirements, guarded routing, explicit chapter paths, dated scope records, unresolved obligations and rejection of altered inputs. Tests do not grade a legal answer.

The integration hook is `project(inputs, semantic, records, units) -> (semantic, ledger)`. The ledger includes the exact added scope records for explicit admission in the evaluation protocol. Two catalogue-derived scope records have new identities; the other five scopes are unchanged historical records. This authoring increment must be built, separately frozen and evaluated before its runtime or browser delivery is claimed. Earlier failed and accepted trials remain unchanged.

## Separate original-case evaluation

The [original-case protocol](../evaluation/manual-structure/original-acceptance/protocol.json) binds the exact two original question fixtures, engine, new source manifest, translation ledger and independent helpers before execution. It adds an unrelated-vocabulary control and runs each question at 32 KiB and 512 KiB: six assemblies in total. The 40 staff questions keep their separate evaluation.

Run the focused controls without assembling a corpus:

```sh
node --test scripts/test_original_acceptance_metrics.mjs scripts/test_original_acceptance_runner.mjs
```

Run a new retained attempt only after freezing its source protocol:

```sh
node scripts/evaluate_original_acceptance.mjs --explorer-root /path/to/pinned/okf-explorer --attempt acceptance-01
```

Add `--check` to replay that exact attempt against its pinned source and engine. A fresh run refuses to overwrite an existing attempt. Failures preserve their completed rows and input identities.

The report separates all six original requirements from active translated profiles, retained and omitted whole units, exact paths, the 12003-to-12002 dependency and the four literal chapter routes. It also retains budget omissions, source-boundary warnings, the dated ADM scope caveat and unmatched original selectors. An integrity error is a failed evaluation, not an acceptable insufficient answer. All three questions are expected to remain insufficient; the hospital question must not activate custody profiles, and unrelated vocabulary must not acquire source evidence.

### First retained result

The [first six-assembly run](../evaluation/manual-structure/original-acceptance/runs/acceptance-01/README.md) passes source-integrity and boundary controls but does **not** deliver the complete original demonstration chain. At 512 KiB, imprisonment retains 20 of 53 selected source units and 43 of 89 declared path occurrences. DMG 12002, 12003, 12015 and 12016 are present, but the explicit 12003-to-12002 dependency is pruned and all four chapter scope routes are incomplete. Retrieval and allocation limits remain visible. At 32 KiB no source evidence fits.

The hospital control retains 38 source units at 512 KiB without acquiring custody profiles; unrelated vocabulary retains none. All packages remain insufficient. A later generic runtime correction must be evaluated separately and preserve this result.
