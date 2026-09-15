# Authored full-DMG behavioural evaluation plan

Status: prepared, not executed. The immutable full 78-unit candidate has not yet been bound. These files are temporary orchestration inputs; the repository review packets remain unchanged.

## Exact proposed scope

Run all **160 existing authored cases**, comprising **78 source-grounding cases and 82 boundary controls**, across all 78 substantive source units. Pension-regimes contains four additional negative cases; do not collapse these into one positive/negative pair per chapter. These are selected semantic scenarios, not a test of every paragraph or complete benefit law.

| Authored packet | Cases |
| --- | ---: |
| Common decision | 20 |
| Pension Credit | 14 |
| Pension regimes | 10 |
| International chapter 7 parts | 14 |
| JSA and Income Support income/capital | 14 |
| Common and JSA extension | 28 |
| ESA | 26 |
| Non-income and industrial benefits | 34 |

The existing finite plan also contains **14 baseline persona/story question routes** and **22 family controls**. Existing `evaluate_full_dmg.py` checks their navigation/no-result behaviour; it does not execute the baseline conversations or validate legal boundaries. Keep these counts separate. A second conversational baseline run would add 14 cases, after loading their actual authored scenario and acceptance criteria. Do not describe the 160-case run as having executed those 14 original stakeholder journeys.

## Prepared files

- `normalise_cases.py`: read-only assembly from the eight packets, finite plan and frozen source. Preserves every original case object, ID, prompt, expected passage and declared link, with JSON pointers and hashes.
- `case-registry.json`: assessor registry. It also records source identities, original case hashes, prompt origins and explicit design gaps.
- `prepare_answerer_tasks.py`: verifies original case/prompt equality and exports the prompt-only answerer view.
- `answerer-tasks.json`: answerer questions and unit scope, without expected answers, quoted passages, concept targets, rubrics or exemplars. Candidate binding is deliberately null.

Recreate after the final packet corrections are stable:

```sh
UV_CACHE_DIR=/Users/crpage/tmp/okf-dwp-uv-cache uv run --locked python /Users/crpage/tmp/okf-dwp-authored-evaluation/normalise_cases.py
UV_CACHE_DIR=/Users/crpage/tmp/okf-dwp-uv-cache uv run --locked python /Users/crpage/tmp/okf-dwp-authored-evaluation/prepare_answerer_tasks.py
```

Both scripts prepare and check inputs. Neither executes retrieval or generates an answer.

## Design gaps retained explicitly

1. The 14 Pension Credit entries contain authored response exemplars but no question string. The registry references their exact existing finite-plan prompts, with a separate provenance label. The exemplars remain unreviewed design context, never actual model outputs or approved gold answers.
2. Twenty-seven negative cases have no direct expected passage. Their paired positive case is linked as derived context for the assessor, without silently adding new evidence to the original case.
3. Forty ESA/international cases have journey-question links but no explicit persona or story field. Those original omissions remain visible. A later persona navigation join must record its basis separately.
4. Twenty-seven positives lack explicit behavioural criteria beyond the question and source expectations. Apply the generic dimensions below, record that limitation, and use an independent reviewer to examine whether the answer actually addresses the question. An authority label is not a grading rubric.
5. Some cases declare only a page, or a locator with a quoted context elsewhere in the packet. The registry preserves that precision. It never fabricates a quote or chooses a wider passage as though the author had explicitly required it.

## Bind the actual candidate before execution

Use one immutable checkout or preserved candidate directory. Confirm the candidate contains the final 78-unit authored set and passes the repository's existing compiler, source-integrity and consumer gates.

Record:

- Commit and clean/dirty state, if Git-backed; otherwise an explicit frozen-directory identity.
- Full-DMG snapshot identifier, descriptor SHA-256, checksums-file SHA-256 and every file identity covered by those checksums.
- Inventory and source-document/page identities used by the candidate.
- Case-registry and answerer-input hashes; all eight original packet hashes.
- Harness/controller and retrieval-tool source hashes, tool versions and actual start/finish times.
- Exact runtime model identifier and settings when exposed; otherwise state that they are unavailable. Do not infer an Astra variant, usage or cost.

Verify every expected route and quoted passage against the candidate's hydrated record and underlying checked source. Verify persona/story/question routes when declared. Missing or changed evidence is a preflight failure, not a model failure and not a reason to rewrite the case silently.

Any packet/candidate change invalidates the relevant binding. Regenerate input snapshots before executing; preserve already observed runs with their original identities.

## Retrieval and response execution

The existing `scripts/evaluate_full_dmg.py` exposes `IndexedEvidence`, whose search reads the built postings and whose passage check binds the hydrated record to the source page. Its current evaluation loop replays paragraph locators and synthetic no-result tokens. That loop is a useful separate regression gate, **not** a substitute for this behavioural run.

Use a controller around the built corpus with two read-only operations:

- Search: record the answerer's exact query, any document filter, actual ordered results, result count and returned record identities.
- Get record: return the complete requested candidate record, including source role, body, provenance and relationships; log the route and exact returned content hash. Neighbouring source-page requests use this same operation.

The controller is still to be implemented or selected by the root task; no executable model runner is claimed here. `scripts/query.py --scope full-dmg` searches source extractions directly and is useful separately, but does not establish that the **built bundle** supplied the answer. Do not use it as a silent replacement for the bound candidate operations.

For each case:

1. Start a fresh answerer context from the prompt-only task. A fresh subagent must use `fork_turns="none"`; the current authoring context already contains assessor material. Do not give it the original review packet, registry, criteria, expected locators, exemplars or earlier answers. A locator already present in the original question remains present.
2. Supply the immutable corpus identity and read-only tools. Allow the answerer to choose shorter keyword queries and inspect context, while retaining every actual query and output. Token-AND search is not natural-language question answering; query refinement must be observable.
3. Capture the actual response verbatim, its citations and any explicit uncertainty or missing evidence. No response may be replaced by an expected answer from the case design.
4. Record an explicit failure or incomplete result if retrieval is unavailable, a response is missing, limits are exhausted or the worker stops. Do not manufacture a successful empty trace.
5. Only after the response is fixed should the assessor receive it, the trace, the original expected material and applicable source context.

Execution can be divided into disjoint batches across available workers. Keep each case isolated, preserve the same tools and candidate, and never have a worker grade its own answer as independent review. The existing 160 cases remain the denominator even if some cannot be completed.

## Grading dimensions

Record separate criterion outcomes with response excerpts and evidence, rather than a single unsupported pass label:

- **Source grounding:** substantive claims and citations are supported by evidence actually returned in this case. A valid source URL alone is insufficient.
- **Requested distinction:** the response addresses the actual question and relevant concepts or exceptions. A generic disclaimer without answering the evidence question does not pass.
- **Scope:** benefit, component, territory, regime, source-era and material exceptions are retained; similarly named concepts are not treated as equivalent without evidence.
- **Authority and dates:** departmental guidance, machine extraction and model interpretation remain distinct. Capture dates do not become source-publication dates or legal commencement, and no current-law or specialist-approval claim is invented.
- **Boundary behaviour:** the negative proposition is rejected or carefully qualified with relevant evidence. Missing evidence is named rather than replaced with confident knowledge from outside the corpus.
- **Individual outcomes:** no personal entitlement decision, award calculation, diagnosis, claimant-data request or operational approval is generated.

Mechanically check returned quotation substrings, source/page hashes, candidate membership, route validity and citation-to-trace links. Semantic correctness and whether a qualification is material require independent assessment. A model assessor remains a model assessor; specialist approval stays unrecorded until a named authorised specialist actually reviews it.

## Required per-case receipt

Each observed result must contain the original/registry case IDs, prompt and hash, candidate/input bindings, actual start and finish, exposed model/tool identity, full ordered retrieval trace, verbatim answer and hash, parsed citations, explicit execution status and separate grading entries. Every grading entry should identify assessor type, criterion, outcome, rationale and supporting response/evidence references. Preserve null or unavailable fields honestly.

A retrieval trace entry needs the tool name, exact arguments, time, success/error, returned payload or stable payload path, payload hash, and bound candidate identity. A citation needs the source route, original source URL, quoted text if any, source PDF hash and page-text hash. Merely copying the registry's expected evidence into a result is not an observed trace.

## Completion reporting

Report attempted, completed, failed, incomplete and not-run counts independently; report source-grounding and boundary cases separately. Keep deterministic locator controls, actual conversational evaluations, independent model grading, browser checks and human specialist acceptance separate.

Retain failures and any later retries with their original hashes and times. A later correction creates a new run; it does not edit an earlier observation into a pass. Publishing a receipt should follow the same reviewed repository process as the corpus. A passing selected-case run does not establish exhaustive domain coverage, current law or fitness for an operational benefits engine.

## Additional source-grounded trial stream

The root task has separately authorised observed answer trials using the frozen raw source extractions. Those receipts must explicitly say that they do not test built-bundle retrieval. They retain actual read traces, source hashes, responses, citations and rubric gaps. The current authoring contexts have seen some designs; disclose that exposure and any self-authored family. This stream does not fulfil the blind, immutable-bundle procedure above or record specialist approval. Original design packets remain unchanged.
