# Demonstrate governed context assembly

This development candidate tests whether a reusable engine can assemble the
evidence needed for a defined question. It produces a traceable context package,
not a generated answer or a decision about a claimant. The earlier published
[full-DMG walkthrough](full-dmg-walkthrough.md) retains its own immutable scope.

## The exact question

> A claimant is imprisoned. Explain the effect on JSA, IS, State Pension Credit and ESA, distinguishing loss of payment from loss of entitlement, and trace each conclusion to the relevant DMG guidance.

The case uses the captured DMG guidance, including its legacy benefit and
territorial boundaries. It does not establish current law, acquire the full ADM,
or decide individual entitlement. No claimant personal data is needed.

## Five-minute public demonstration script

Release preparation: replace `FULL_DMG_CONTEXT_COMMIT` below with the immutable
DWP content commit only after checking that exact descriptor in the public
Explorer. Record the deployed Explorer build separately in the browser receipt.
These are launch templates, not verified publication links:

```text
https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2FFULL_DMG_CONTEXT_COMMIT%2Ffull-dmg%2Fokf-explorer.json#page/dmg-vol3-ch12/0003
https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2FFULL_DMG_CONTEXT_COMMIT%2Ffull-dmg%2Fokf-explorer.json&view=graph#page/dmg-vol3-ch12/0003
```

1. **State the boundary.** “This is an unofficial research demonstrator using a
   frozen source capture. It assembles evidence; it does not decide entitlement.”
2. **Ask the question.** Select **Ask OKF**, paste the exact question above and
   select **Build evidence package**. Keep the default evidence limits.
3. **Explain the result.** Inspect **Declared evidence requirements met**, the
   snapshot, index digest and declared requirements. The local acceptance
   retains 52 records and 127 relationships; the browser must independently
   confirm its actual package and identity.
4. **Show the route.** Open **Directed relationships** and **How the evidence
   was reached**. Use the Graph template to inspect the 12015 source page,
   named chapter and benefit branch. Distinguish normalised chapter references
   from model-derived paragraph selection.
5. **Show the qualification.** Open a whole source passage and its provenance.
   Use the review table below to illustrate payment versus entitlement and the
   two ESA components. Leave missing ADM bodies and specialist review visible.
6. **Demonstrate a bounded failure.** Under **Evidence limits**, set
   **Package bytes** to `8192` and rebuild. Inspect the insufficient result and
   explicit omission; restore `524288` before building the full package again.
7. **Hand over the evidence.** Select **Copy evidence package** or
   **Inspect package JSON**. Show `ai_answer: null` and explain that a later
   answerer must be evaluated separately against this exact context package.

## What the demonstrator should show

1. Resolve the declared benefit and imprisonment concepts. Short aliases such
   as `IS` are case-sensitive; ordinary words must not silently become benefits.
2. Show DMG 12002 and 12003 together. The payment-versus-entitlement statement
   applies to the benefits listed there; it must not be generalised to every
   benefit in the question.
3. Follow DMG 12015 from its source page to chapters 24, 53, 54 and 78, then to
   the scoped benefit concepts. The source states chapter destinations. The
   selection of concepts and paragraph evidence within them is a separate,
   explicitly model-derived interpretation.
4. Inspect whole source pages, their original PDF links, source hashes, page
   locators and exact text digests. Follow continuation and qualification pages.
5. Inspect applicable evidence requirements, their directed paths, unresolved
   terms, omissions, conflicts and the package budget.
6. Export the package. `ai_answer` remains `null`. A sufficient result means the
   declared evidence requirements close within scope, not that a legal answer
   has been independently approved.

Use the candidate's **AskOKF** interface after loading its full-DMG descriptor.
The UI and a compatible page-tool host call the same deterministic library.
A host must actually expose those tools before claiming an AI used them;
opening the page alone is not a tool invocation. Browser publication and host
acceptance are separate from the local execution receipt below.

## Review the distinctions in the source

These are review targets, not individual conclusions:

| Branch | Evidence and qualification to inspect |
| --- | --- |
| Common guidance | DMG 12002–12003 and 12015–12016; preserve the listed-benefit scope and routing to other regimes |
| Legacy JSA | DMG 24185–24187; availability, entitlement and the stated short-custody exception |
| Income Support | DMG 24212 and 24214 with the prisoner definition and possible remand housing-cost treatment |
| State Pension Credit | DMG 78666–78672 and 78675–78676; distinguish component rates, nil award, remand and partner treatment |
| Contributory ESA | DMG 53256–53260, 53284–53285, 42580 and 41823/41832; distinguish disqualification, suspension, the more-than-six-week rule and continuing-entitlement qualifications |
| Income-related ESA | DMG 54213–54215 and 42581–42582; preserve the applicable-amount and limited-capability distinctions, including cases receiving both ESA components |
| External dependency | The captured Memo 07/20 removal note and ADM M1 spare catalogue title are metadata evidence only; they do not supply an ADM chapter or prove current applicability |

Whole-page extraction retains its original limitations. Source and model-derived
records remain separately labelled. Specialist acceptance remains zero.

## Run the independent acceptance

Use the locked DWP and Explorer checkouts, with Node 26.7.0 or the repository's
supported Node 26 runtime. The consumer checkout is an explicit test dependency;
the receipt binds its actual implementation hashes.

```sh
uv sync --locked
uv run --project ../okf-explorer --locked python -c 'import jsonschema, referencing'
node scripts/evaluate_context_assembly.mjs --explorer-root ../okf-explorer
node scripts/evaluate_context_assembly.mjs --explorer-root ../okf-explorer --check
node --experimental-strip-types ../okf-explorer/scripts/run_context_controls.mjs \
  --index full-dmg/context/assembly-index.json \
  --case evaluation/context-assembly/imprisonment-case.json \
  --controls evaluation/context-assembly/imprisonment-controls.json \
  --output evaluation/context-assembly/imprisonment-controls-execution.json
```

Add `--check` to the last command to replay and compare the retained control
outputs. `--check` performs fresh engine executions; it preserves the original
observation timestamp instead of relabelling old evidence as a new run.

The DWP preflight rehashes original PDFs, page artefacts and captured GOV.UK
metadata, then checks every evidence passage byte for byte. The generic runner
passes the index, question, budget and binding to the actual engine. Assessor
expectations never become retrieval seeds.

| Stage | Independent check |
| --- | --- |
| A — source | Exact source identities, page routes and frozen text |
| B — semantic | Required concept IDs, assertion IDs and directions |
| C — retrieval | Exact question and declared concept resolution |
| D — traversal | Retained seed paths and explicit source-to-chapter-to-concept chains |
| E — assembly | Complete required evidence, counts and byte/node/depth limits |
| F — provenance | Source digests, literal digests, input binding and recomputed package identity |
| G — boundaries | Access, authority, review status, scope, omissions and exclusions |
| H — answerability | Scoped requirement closure, explicit missing paths and no generated answer |

The acceptance uses identities and graph structure, not shared keywords. Its
synthetic controls remove evidence, reverse direction, corrupt text, withhold
provenance, restrict access, add ambiguity, declare conflict and constrain the
budget. A passing negative control means the expected failure was observed.

## Evidence and limits

- [Independent acceptance case](../evaluation/context-assembly/imprisonment-case.json).
- [Frozen source selectors](../evaluation/context-assembly/source-selectors.json)
  and [source verification](../evaluation/context-assembly/source-check.json).
- [Actual positive execution](../evaluation/context-assembly/imprisonment-execution.json).
- [Fresh application check with immutable public DWP content](../validation/ask-okf/fresh-candidate-browser.json)
  and [its exported context](../validation/ask-okf/pinned-context.json) verify the
  application after the optional-metadata validation fix. The public application
  deployment is checked separately; this observation uses the local application.
- [Local browser observations](../validation/ask-okf/local-browser.json) and
  [the browser-exported package](../validation/ask-okf/browser-context.json).
  These record the checked local app and package identity, not a deployed
  public release. The native Chrome host exposed no `modelContext` tools;
  these were interface checks, not an AI page-tool invocation.
- Local screenshots: [assembled package](../validation/ask-okf/screenshots/02-ask.png),
  [chapter routing](../validation/ask-okf/screenshots/04-chapter-routing.png),
  [whole source passage](../validation/ask-okf/screenshots/05-source-passage.png)
  and [insufficient byte budget](../validation/ask-okf/screenshots/07-insufficient-budget.png).
- [Declared negative controls](../evaluation/context-assembly/imprisonment-controls.json)
  and [actual control executions](../evaluation/context-assembly/imprisonment-controls-execution.json).
- [Reusable Explorer evaluation design](https://github.com/chris-page-gov/okf-explorer/blob/main/docs/context-assembly-evaluation.md).

The source author and assessor share project context. This is an engineering
acceptance case with independent requirements and negative controls, not a blind
retrieval benchmark, specialist legal assessment or model comparison. The earlier
160 source-guided answer trials remain unchanged and are a different experiment.
No model is called by these commands, and no source is refreshed from the web.

The existing DWP CI workflow also replays the positive case and all mutation
controls against an immutable Explorer checkout using its locked dependencies.
`EXPLORER_CONTEXT_COMMIT` in `.github/workflows/okf-ci.yml` must be a reviewed
40-character commit; branch names and the local preparation placeholder fail
before checkout. This test dependency pin is separate from the content commit
in the public demonstration templates. Updating either must preserve the exact
source and execution bindings.

## Existing repository-contract limitation

The additional strict repository reconciliation audit reports seven metadata
errors that are already present on `main`. The semantic contract is unchanged
from `main`, and its README also lacks the required version declaration:

- `README.md` does not declare `okf_version: 0.2`.
- The declared required output `full-dmg/**` is reported as absent.
- `reader.additional_deliveries` is unsupported by the closed contract.
- `relationship_contract.pilot_vocabulary` is unsupported.
- `relationship_contract.proposal_input` is unsupported.
- `semantic_layer.deliveries` is unsupported.
- The output role `indexed-runtime-and-sharded-semantic-projections` is not
  governed by the contract.

This feature does not migrate that existing contract. Passing the repository CI
gates and the context acceptance checks does not mean that this separate strict
audit passes. These findings concern repository declarations; they do not remove
the independently checked source hashes, directed graph paths or recorded
evidence boundaries.
