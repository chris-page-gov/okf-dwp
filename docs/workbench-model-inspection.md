# Blocked calculation inspection model

This additive candidate lets the Evidence workbench display source-bound calculation **dependencies**. It does not calculate a Pension Credit award, decide entitlement, request claimant details or change any of the 40 retained evidence packages. The model is an authored, unreviewed proposal. Every cited package remains `insufficient` and truncated.

## Rebuild and inspect

```sh
uv sync --locked
uv run --locked python scripts/build_workbench_models.py
uv run --locked python scripts/build_workbench_models.py --check
uv run --locked python -m unittest discover -s scripts -p test_workbench_models.py -v
```

The authored input is [inspection.json](../domain-profile/workbench-models/inspection.json). The producer checks the original [workbench manifest](../evaluation/evidence-workbench/manifest.json) SHA-256, each cited package SHA-256, selected record ID, assertion status, source URL, PDF page locator, source and literal hashes, capture time, unit-boundary status and a short exact text snippet. These checks compare the proposal with the retained, hash-bound package; they do not rehash the official PDFs or rerun source extraction. It then creates [tools-manifest.json](../evaluation/evidence-workbench/tools-manifest.json) with the original 40 questions and package references unchanged. This successor manifest is an opt-in source file for Explorer; it is not part of the version 3 learning-site publication allowlist. A consumer should use an immutable DWP Git revision and verify its manifest digest. The projection is under Explorer's 256 KiB manifest limit.

The `calculation_models` and `interaction_proposals` fields follow Explorer's `CalculationModel` and `InteractionProposal` contracts. The model status is always `blocked`, its authority is `authored-unreviewed-proposal`, its jurisdiction and effective dates are null, and there is no formula or arithmetic field. The source snippets are verification anchors, not executable expressions. `required: null` records that mandatory facts have not been settled. Units distinguish capital stock (`GBP`) from weekly income (`GBP/week`) without implying a rate or calculation.

## Try the five data tabs

Load the opt-in `tools-manifest.json` through a compatible Explorer Evidence workbench after both repositories have reviewed revisions. Until then, the existing public workbench continues to use its original manifest. An immutable raw GitHub URL at the reviewed DWP commit can serve the new manifest and its unchanged `packages/` and `parts/` neighbours; this is separate from the bounded learning-site publication.

1. Open **staff-016** (“Given these inputs what is the formula for calculating Pension Credit?”). The package itself says `insufficient`; the model is blocked.
2. Use **Graph** to inspect directed retained relationships and their source references. An edge is not automatically a calculation dependency.
3. Use **Interactions** on **staff-039**. Read the separate carer-income, carer-addition and cared-for-person directions, and the Chapter 17 overlap reference. Do not reverse an arrow or infer an award change.
4. Use **Requirements** to see the missing input, applicability, legal-version and review obligations. A selected passage does not close these requirements.
5. Use **Rates** to see that no reviewed typed rates contract or effective period is admitted. To inspect a number mentioned in guidance, follow its source passage separately; do not use an historic example as a current rate.
6. Use **Calculation stages** to inspect the five input groups and five source-linked stages. It reports `blocked`, unknown required fields, null effective dates and explicit gaps. It cannot accept personal details or return an amount.

These are the five data tabs (`graph`, `interactions`, `requirements`, `rates`, `calculation`). The original source, extraction, passage, ontology, definitions, trace and review tabs remain useful for checking the underlying evidence.

## Try the seven page tools

In a compatible browser, a page may register seven WebMCP tools. Start with `okf_get_state` to obtain the current snapshot and page revision. Use `okf_search_evidence` to find staff-015, staff-016 or staff-039; `okf_get_evidence` to read one selected passage and its provenance; `okf_get_relationships` to inspect directed assertions; `okf_get_view_data` to obtain a bounded table or graph for one of the five data tabs; `okf_get_calculation` to inspect the blocked model by ID or stage; and `okf_show_view` to display a referenced case or record. State-changing presentation uses the current snapshot and revision; a stale call should be rejected and retried from `okf_get_state`.

For example, a reviewer can search for “Pension Credit formula”, open `staff-016`, request the calculation data view, then call `okf_get_calculation` with model ID `pension-credit-source-inspection-v1` and section `inputs` or `stages`. The result should identify evidence and gaps, **not** an award. A separate `staff-039` journey can show why Carer’s Allowance effects must be read by direction and by person. Each tool response should be checked against its snapshot ID and source links; a compact response may require continuation.

Registration or local tool tests do not prove that an assistant panel can discover or invoke the page tools. Native browser registration, actual host invocation, rendered page state and any panel visualisation need separate observations. The workbench remains usable through its ordinary controls when WebMCP is unavailable.

## Source-led inspection stages

| Stage | Captured passage | What can be inspected |
| --- | --- | --- |
| Scope and component | DMG 77302 and 77304, Chapter 77 PDF pages 32–33 | Guarantee Credit and Savings Credit have different named dependencies. Household, relevant date, territory and legal version are unresolved. |
| Income | DMG 85091 and 85130, Chapter 85 PDF pages 30 and 39 | Income category pointers, including Carer’s Allowance and retirement pensions; complete treatment and disregards are unresolved. |
| Capital | DMG 84001 and 84911, Chapter 84 PDF pages 2 and 128 | Actual and notional capital precede deemed weekly income. The captured numeric passage is not a reviewed, dated universal threshold. |
| Guarantee Credit | DMG 77302, 77303, 77331, 77333 and 77334, Chapter 77 PDF pages 32–35 | Standard minimum guarantee, additions, appropriate minimum guarantee and payable passage; no executable ordering or rates model. |
| Savings Credit | DMG 77304, Chapter 77 PDF page 33 | Qualifying income, savings credit threshold, appropriate minimum guarantee and maximum Savings Credit are named; formula and dated conditions are unresolved. |

The selected records retain official PDF URLs, page locators, source hashes and literal-span hashes. Their unit boundaries are machine-detected and completeness is unresolved. A PDF capture date is not an effective date. Examples and historic figures in extracted passages are not current rates.

The separate [GOV.UK adviser guide (April 2026, updated 8 May 2026)](https://www.gov.uk/government/publications/pension-credit-technical-guidance/a-detailed-guide-to-pension-credit-for-advisers-and-others#overview-of-how-guarantee-credit-is-calculated) describes a Guarantee Credit calculation sequence, dated rates, Savings Credit Amount A/B and worked examples. It is a useful **source lead** for a future bounded, versioned acquisition and review. Its page content has not been admitted to this frozen package or model, so it does not change the `blocked` status or supply executable rates here.

For Carer’s Allowance, the source proposes separate directions: CA may enter the **carer’s own** income assessment (DMG 85091); CA entitlement or treated qualifying conditions may lead to the **carer’s own** Pension Credit carer additional amount (DMG 78105); CA or a UC carer element **in payment for caring for the claimant or partner** may affect the **cared-for person’s** severe-disability additional amount (DMG 78057). DMG 60109 only points to Chapter 17 for overlapping benefits; the retained passage does not decide another benefit's outcome. These are directional, qualified review prompts, not a symmetric interaction rule or award result.

## What blocks execution

The source-linked stages do not establish a complete input contract, versioned rates, jurisdiction, legal applicability, exceptions, precedence, ordering or rounding. Savings Credit and special-group provisions need separate review. All four relevant staff packages (010, 015, 016 and 039) explicitly retain missing evidence and insufficient status. Source closure and independent specialist review are required before a rule or calculation could be approved. The repository's current prohibition on individual awards and claimant data remains in force.

The separately supplied Guarantee Credit calculation brief (`research/overview-of-how-guarantee-credit-is-calculated.md` in the owner's checkout) asks for a future chain of source passage → proposition → reviewed rule and calculation model → deterministic Java implementation → scenario → explanation. Each future Java rule would need a stable ID, legal version and effective period, source passage/page/hash, dependencies, exception precedence, units, rounding, source-derived tests and reviewer decision. A later MongoDB service would need separate **valid time** for the benefit circumstances and **recorded time** for when a change was stored, immutable rule/model versions, replayable retrospective events and controlled query access. Projection without persistence would use the same approved deterministic engine but would not store the hypothetical scenario. None of that backend is implemented by this manifest.

A future synthetic calculation demonstrator needs a separately reviewed scope and an explicit amendment to the project agreement or architecture decision record. It must remain separate from operational use with real claimant data. The current workbench model is safe to inspect precisely because execution stays blocked.
