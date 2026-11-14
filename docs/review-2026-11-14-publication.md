# Producer and publication review: 14 November 2026

This review examines DWP baseline `77ef16047415ee48dcb93b80adf1ba057ea00d9b`
against Explorer `40e65940` as checked out on 14 November 2026. Findings below
describe that baseline; the accompanying feature branch may address them.
This is an independent experimental publication. Source integrity and delivery
checks do not establish current legal applicability or specialist acceptance.

## Findings requiring attention

| Priority | Baseline finding | Practical consequence | Recommended treatment |
| --- | --- | --- | --- |
| Medium | README's current-release section and Ask OKF introduction foreground the dated 0.6.0 observation, while the selected generated status records 0.7.0. See baseline README lines 43–67 and 372–383, and `docs/service-publication.md` lines 13–27. | A reader can choose an earlier source/engine pair while believing it is the current recorded service. The date labels and link to the generated status reduce, but do not remove, the confusion. | Put the selected 0.7.0 observation and exact source/engine pair first. Preserve 0.6.0 as explicitly historical. Do not describe a new producer branch as an adopted service default. |
| Medium | The publication contract's verification journeys enumerate the historical pilot, full-corpus baseline and logical-unit candidate, with no current consumer compatibility check. See `okf.publication.json`, `verification.journeys`. | Historical receipts can pass while a later Explorer deployment changes its runtime or browser behaviour. Existing receipts correctly bind their original scope; they cannot attest a new deployment. | Add a separate current-Explorer compatibility gate and fresh browser observation, retaining every historical source and engine pin. |
| Low | README lines 576–578 and the final CI limitation in `okf.publication.json` say the protected gate requires “both jobs”. The baseline workflow actually requires legacy, structured and workbench jobs. | The prose understates the release gate and will become more misleading when another independent gate is added. | Describe all required jobs, or use “every required validation job” so the statement remains accurate when the gate grows. |
| Low | The current overview in `REPOSITORY_STATUS.md` is dated 26 September; `docs/remaining-work.md` still directs room rehearsal before 30 September. | A returning reader receives seminar preparation as current work and has to reconstruct later progress from the changelog and specialist reports. | Add a dated current overview and preserve the September checkpoints as history. Keep source-selection progress separate from the still-open legal and specialist obligations. |

The truncation and semantic-routing investigation has a separate report. These
publication findings should not be interpreted as a second diagnosis of the
retrieval mechanism.

## Candidate treatment and fresh evidence

The accompanying candidate addresses the four publication findings: current
entry points foreground the selected service observation, September work logs
remain explicitly historical, every required CI job is named accurately and a
fourth current-Explorer gate preserves all earlier immutable engine pins.
The protected aggregate name remains `validate`.

The [context review guide](context-review.md) links the new source-retrieval
evaluation, retained initial failures, persona coverage, frozen withheld wording
trial, statutory crosswalk and exact local Chrome/Edge inspector observation.
Local verification passed 985 repository Python tests (one existing skip), six
additional statutory-crosswalk tests, 85 candidate Node tests and the earlier
83 historical Node checks. The renderer correction was then checked with its
eight affected tests. Deterministic source and pilot-projection checks passed.
These results do not represent remote service or connected-client acceptance.

The graph runtime and client were frozen before the separate agent's withheld
wording trial. All 263 persona target occurrences, 35 custody targets, four UC
targets and 45 withheld targets were reached through admitted directed source
paths, with complete bounded delivery. Twelve withheld negative controls
passed. All original requirements and 203 obligations remain open. Directed
navigation repairs and concept bridges retain model-derived, unreviewed status.

## Release identity

The current DWP baseline already has the annotated tag
`demo-2026-09-30-reading-help-v2`. The tag resolves to exactly
`77ef16047415ee48dcb93b80adf1ba057ea00d9b`; its annotation binds Explorer
`b633038c6173f1405199df9f08e8d8aa2ff51c0b`, DWP and Explorer CI/Pages runs,
and the recorded public browser checks. It explicitly retains the experimental
status and all 40 insufficient packages. There is no justification for moving
or replacing that tag. A later candidate needs its own identity.

## Contracts and authority boundaries

Both repository contracts were read as complete JSON documents. The semantic
contract declares the generated projections, source-bound identity policy,
absolute predicate identifiers and required assertion provenance. The
publication contract declares 22 source families, six validation planes and
141 build/check commands at the reviewed baseline. It separates authored
inputs, generated outputs, acquisitions, ordinary offline checks and public
verification. Unknown change paths fail closed into full validation.

The three canonical schemas for the semantic contract, publication contract
and source families are byte-identical to the same files in the current
Explorer checkout:

| Schema | SHA-256 |
| --- | --- |
| `profiles/bundle-wiki/v1/repository-contract.schema.json` | `783f81c5c785b3a13cfdedce3a89dd1e5c3f64a007cfe370bc82e37e2caa5ba8` |
| `profiles/publication-method/v1/repository-publication.schema.json` | `04c5d229a2900616d7a194d256ae1edb162d2c18beec7e2354723ce711b4eec3` |
| `profiles/publication-method/v1/source-family.schema.json` | `8c4734f554920fd34157ce90172a53ced492198d3761e7a62ebebf51036b3f6b` |

No schema migration is needed merely because Explorer's framework, bundler,
PDF.js and analytical-data support changed. This comparison covers those
schema bytes; it is not a claim that every current browser journey passes.

The existing notices correctly distinguish official source material from
machine extraction and project-authored interpretation. Source mentions,
navigation proposals and discovery cards do not create legal applicability.
Historical classification, exact source hashes, the 513-document denominator
and the 203 original open obligations should be preserved. The CPAG reference
remains metadata only, with no handbook-body acquisition or reuse permission.
The source snapshots remain dated September captures; verification of their
integrity is not a current GOV.UK refresh.

## Verification performed

These commands ran against the isolated feature checkout using the existing
locked Python environment, with Python bytecode writing disabled. No new
dependencies, acquisition, model inference or paid API calls were used.

| Check | Observed result |
| --- | --- |
| `scripts/acquire_full_dmg.py --check` | Passed: 331 complete DMG documents; PDF, extracted-text and page hashes verified; frozen original inputs unchanged. |
| `scripts/acquire_adm.py --check` | Passed: 182 complete documents and 4,347 pages; no page/byte mismatches or acquisition failures. The retained 91 pages without extracted text and 27 possible letter-spacing flags remain visible. |
| `scripts/build_bundle.py --check` | Passed: all 835 generated pilot files byte-equivalent, totalling 32,574,096 bytes. |
| `scripts/check_private_inputs.py` | Passed: no `.email.md` in the Git index, with root and nested ignore probes checked without reading correspondence. |
| `scripts/check_browser_evidence.py` | Passed: retained public-browser observation consistent with its frozen Explorer and evidence identities. The command explicitly reports `browser_launched: false`; it is not a fresh browser test. |
| `scripts/build_service_publication.py --check` | Passed: selected recorded service 0.7.0; seven deployment receipts, seven successful SDK receipts and 14 receipt files checked offline. |
| `tools/learning-site/test_learning_site.py` | Passed: 28 tests covering tracked allowlisting, inert rendering, safe source paths, commit-bound links and repeatable publication. |

The publication workflow checks that its candidate is still protected `main`,
builds the exact validated commit and deploys the single uploaded artefact.
The learning-site tests confirm that untracked material is not admitted and
that changed source bytes cannot masquerade as the declared commit. No
publication-boundary regression was found in the checks above.

## Limits and next decisions

This review does not establish current statutory or guidance applicability,
whole-corpus visual extraction quality, accessibility acceptance, Voice
operation, answer accuracy or human specialist approval. Those remain
separate tasks with their own evidence. New recovery and progressive-delivery
code should enter through an additive, independently identified candidate;
publishing its documentation does not change the remote Ask OKF default.

For evaluation, compare the new candidate with the retained failure at equal
assembly budgets and inspect exact sources and omissions. Admit a new remote
service pair only after the intended client verifies that exact source,
engine and delivery contract. Keep the original failures and historical
receipts available for replay.
