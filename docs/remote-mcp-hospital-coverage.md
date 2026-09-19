# Hospital admission: what the remote demonstration can establish

The current Ask OKF index **cannot establish the effect of ordinary hospital admission across the four benefits**. Its correct result is `evidence_status: insufficient`. The full DMG corpus contains relevant hospital guidance, but acquired pages and general search coverage do not automatically become a governed context profile.

This is an independent experimental publication. It is not an official DWP document, a current entitlement decision, an award calculation or specialist legal advice. The review below identifies research dependencies in a frozen source snapshot; it does not settle them.

## Exact acceptance question

> A claimant is admitted to hospital. Explain the effect on JSA, Income Support, State Pension Credit and ESA, distinguishing entitlement, payment and changes in amount, and trace each conclusion to the applicable DWP guidance.

The [hospital case](../evaluation/remote-mcp/hospital-case.json) is assessed separately from the successful [imprisonment case](../evaluation/context-assembly/imprisonment-case.json). Expectations never enter the assembler as search seeds or instructions.

For the approved source version `efb05c66616a9cd4328a86cf412780fe7bc7cf0b`, the context index has SHA-256 `38159445a60d4bcabc23cb2cf728e14cbd0a4b55013276c291356e7a1452ff54`. All six evidence requirement declarations concern custody. The normal-budget hospital result must preserve:

- insufficient evidence, with no model-generated answer;
- no applicable evidence requirements;
- `no_evidence_requirements`, eight `uncovered_resolved_concept` entries and `unresolved_terms`;
- the unresolved terms `admitted`, `amount`, `applicable`, `changes`, `dwp` and `hospital`;
- the source scope, authority distinctions, limitations and provenance;
- no budget truncation.

Broad benefit and claimant aliases currently resolve to custody-scoped concepts. Their selected evidence must **not** be presented as an ordinary hospital answer. This is a scope failure even when many records are returned.

## Existing semantic material outside Ask

Six hospital-specific authored concepts already exist in `knowledge/full-dmg/`:

| Concept | Captured paragraph scope |
| --- | --- |
| [Post-2006 hospital scope](../knowledge/full-dmg/common-and-jsa-extension/common-hospital-post-2006-scope.yamlld) | 18000–18001 |
| [Individual treatment](../knowledge/full-dmg/common-and-jsa-extension/common-hospital-individual-treatment.yamlld) | 18020–18025 |
| [IS/JSA inpatient treatment](../knowledge/full-dmg/jsa-income-support/jsais-free-inpatient-treatment.yamlld) | 24007, 24097 |
| [IS/JSA family membership](../knowledge/full-dmg/jsa-income-support/jsais-hospital-family-membership.yamlld) | 24097, 24108 |
| [ESA inpatient treatment](../knowledge/full-dmg/esa/esa-free-inpatient-treatment.yamlld) | 54003–54005 |
| [ESA inpatient period](../knowledge/full-dmg/esa/esa-inpatient-period.yamlld) | 54072–54074 |

None is included in the present context index. They remain unreviewed model-assisted interpretations. A future hospital profile should reuse sound existing identities, supply complete evidence and justified directed dependencies, and keep neutral benefit identities distinct from circumstance-specific effects.

## Source gaps to resolve before a hospital answer

The [source review manifest](../evaluation/remote-mcp/hospital-source-review.json) records ten original PDF hashes and 52 inspected whole-page literal hashes. Each was checked against the preserved PDF and page JSON on 19 September 2026. The original bounded source inspection took place on 16 September. The manifest is a locator and identity audit, not a declaration that every legal dependency was reviewed.

| Area | Frozen source evidence | Outstanding modelling or reconciliation |
| --- | --- | --- |
| General scope | [Chapter 18, page 3](https://assets.publishing.service.gov.uk/media/5a80d88aed915d74e33fcbde/dmgch18.pdf#page=3), 18000–18001 | The old downrating rules and their abolition have a stated scope. Follow the separate IS/JSA and Pension Credit routes; do not infer that every payment component is unaffected. |
| JSA conditions and amount | [Chapter 24, page 9](https://assets.publishing.service.gov.uk/media/5e9f006886650c031ce2c41b/dmgch24.pdf#page=9), 24002; page 26, 24106 | Separate personal rate from entitlement conditions and distinguish contributory from income-based JSA. Chapter 24's older two-week summary routes to chapters 20 and 21. |
| JSA duration and source versions | [Chapter 20, page 136](https://assets.publishing.service.gov.uk/media/67ffaf91694d57c6b1cf8e0e/dmgch20.pdf#page=136), 20971–20974; continuation on page 137 | The captured chapter 20 adds a conditional extended sickness period up to 13 weeks and cites a memo. Reconcile these dependencies before treating chapter 24's older wording as a universal limit. |
| IS/JSA premiums and family | Chapter 24 pages 25–27, 24091–24108; chapter 23 pages 73–80, 23254–23312 | Determine qualifying-benefit, premium, housing and family conditions. Follow chapter 22/23 routes and preserve exceptions; a single duration does not answer every component. |
| Pension Credit amount and household | Chapter 78 pages 127–131, 78781 and 78805–78829 | Separate ending the former 52-week downrating effect from additional amounts, qualifying benefits, carers, housing and household membership. Guarantee Credit and Savings Credit need separate treatment. |
| Pension Credit broken reference | Chapter 78 page 130, 78827 → chapter 77 page 22, 77119 | The source points to 77119 as a hospital household exception, but the captured destination concerns temporary overseas absence connected with bereavement. Record a source/version mismatch; do not infer the missing exception. |
| ESA components and duration | [Chapter 54, page 23](https://assets.publishing.service.gov.uk/media/5e9f025dd3bf7f031b0cc9e6/dmgch54.pdf#page=23), 54091–54106; continuation on page 24 | Distinguish contributory and income-related ESA, personal rate, components, premiums, housing, partner membership and prescribed mental-health detention. Preserve the exact duration wording and follow chapter 43/44 dependencies. |
| ESA entitlement condition | Chapter 42 pages 10–12, 42070–42078 | Limited-capability-for-work treatment, professional advice, recovery and planned admission are separate from award amount and components. |
| Regime boundary | Captured DMG and separate ADM catalogue metadata | The bundle has no ADM chapter bodies. Broad JSA/ESA names do not establish whether legacy DMG or New Style ADM rules apply. Claim and regime scope must be resolved before choosing the corresponding evidence. |

All uncoupled chapter/page references above have official attachment URLs, routes, PDF hashes and page-literal hashes in the source review manifest. Existing source extracts contain old examples and historical amounts; do not calculate current awards from them. This review did not inspect CPAG body content, claimant data, all hospital-related guidance, consolidated legislation or every PDF layout.

## Dates and authority

The inspected PDF inventory does not declare a publication date. Catalogue updates, printed amendment dates, HTTP timestamps, acquisition time and legal effective dates have different meanings. The 15 September acquisition date is **not** a publication or commencement date. Older chapter 24 print footers and chapter 54's June 2017 footer remain visible in the preserved source. This adapter work does not refresh the frozen evidence or assert current applicability.

## Reproduce the transport acceptance

From this repository, with a checkout of the remote-capable Explorer branch:

```sh
node --experimental-strip-types scripts/test_remote_mcp.mjs \
  --endpoint https://ask-okf.crpage.chatgpt.site/okf/mcp \
  --explorer-root ../okf-explorer
```

The script negotiates MCP, discovers the read-only tool and calls `ask_okf` once for each exact question. It checks the returned package against the unchanged reusable core using the **same immutable index URL and hash**. The imprisonment case uses the existing exact evidence, directed path and provenance rubric, not keyword overlap. The hospital case passes only when it reports the declared evidence gap. The script records endpoint and transport scope so a loopback run cannot be mistaken for public HTTPS success.

It writes compressed raw MCP tool results, tool schemas and a dated receipt under `validation/remote-mcp/`. Recheck retained results without contacting the service:

```sh
node --experimental-strip-types scripts/test_remote_mcp.mjs \
  --check --explorer-root ../okf-explorer
```

Both commands require matching engine and evidence versions. The [retained HTTPS receipt](../validation/remote-mcp/receipt.json) records the public test calls. A raw MCP-client pass does not prove ChatGPT or Voice invocation. Those client-specific observations belong in the [demonstration guide](remote-mcp-demo.md).

## Demonstrate the honest boundary

Ask the client to use `ask_okf` with the exact hospital question and to report the returned `evidence_status`, `context_id`, source version, missing evidence and scope. It should explain that OKF-DWP has not supplied a complete hospital answer. Any separately obtained information must be visibly attributed outside the OKF result.

The next semantic stage is to reconcile regimes and source versions, model the necessary benefit/variant and hospital relationships, add complete source passages and independently assess coverage. The remote adapter cannot supply missing domain knowledge.
