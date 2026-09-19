<a id="pension-credit-guidance-as-an-okf-bundle"></a>

# DWP guidance as an OKF+ bundle

**An independent, unofficial experimental exemplar. Not an official DWP document, benefits advice or an entitlement calculator.**

This repository turns public Department for Work and Pensions (DWP) guidance into source-linked records, a YAML-LD semantic graph and an indexed OKF Explorer research candidate. It began with a [Pension Credit pilot covering volumes 13 and 14](https://www.gov.uk/government/publications/decision-makers-guide-vols-13-and-14-state-pension-credit-staff-guide), expanded to the [full Decision makers’ guide (DMG)](https://www.gov.uk/government/collections/decision-makers-guide-staff-guide), and now also preserves the separate [Advice for decision making (ADM) manual](docs/adm-acquisition.md). It demonstrates how a specialist or an AI can find evidence, inspect relationships and see what remains uncertain.

**New to the project?** Follow the [practical learning path](docs/learning-path.md),
then use the [plain-English glossary](docs/glossary.md) when a benefit name or
technical term appears. It explains Search, Ask OKF and AI answering through
short tasks, including how to connect and why a browser can show HTTP 405.

[Verified Pension Credit semantic exemplar](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F7d3c69df0571b8d5206c8edce92963d99979cb5c%2Fbundle%2Fokf-bundle.yamlld&view=graph#term/capital-disregards) · [Original meeting demonstration](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F79d21c758e37948fd6d4bde0f1b4d97b266e2e4f%2Fbundle%2Fokf-bundle.yamlld&q=84351#question/pc001) · [Read the pilot bundle](bundle/index.md) · [Ten-minute meeting walkthrough](docs/meeting-walkthrough.md) · [Discovery findings](docs/discovery.md) · [AI interrogation guide](AI_USAGE.md) · [Public notice and rights](NOTICE.md)

## Current source and question coverage

**The two acquired manuals contain 513 PDFs and 19,090 measured pages.**
Acquisition preserves documents; it does not establish complete policy modelling
or specialist acceptance.

| Source family | Captured | PDFs | Measured pages | Pages with nonempty extracted text | Pages with no extracted text |
| --- | --- | ---: | ---: | ---: | ---: |
| [DMG](source/full-dmg-2026-09-15/inventory.json) | 15 September 2026 | 331 | 14,743 | 13,941 | 802 |
| [ADM](source/adm-2026-09-19/inventory.json) | 19 September 2026 | 182 | 4,347 | 4,256 | 91 |
| Total | Separate frozen observations | 513 | 19,090 | 18,197 | 893 |

Every page remains represented, including the 893 pages with no extracted text.
Those pages retain original PDF links; no OCR or whole-corpus visual review has
established whether they are blank or image-only. Nonempty text can still contain
extraction defects. Original capture dates and source publication dates remain
separate.

The [staff-question registry](evaluation/staff-questions/cases.json) contains
**40 occurrences and 39 distinct questions**. The [recorded remote baseline](validation/staff-questions/receipt.json)
tested every occurrence against the preserved 52-record custody profile: all
40 packages matched the Explorer engine, and all 40 were **insufficient**, without
assembly-budget truncation. Forty-two source candidates were separately verified.
These are honest coverage gaps, not 40 answered questions or expert-approved
benefits conclusions. No token or monetary saving has been established.

The [first full-corpus local run](validation/corpus-questions/receipt.json) now
tests all 40 questions and three boundary controls against the combined manuals.
All 40 staff questions return candidate evidence, including ADM pages. Ten retain
an independently located candidate page and 19 retain a page from a candidate
document. These measures show where retrieval helps and where it needs work;
they are not answer-quality scores. All 43 results remain **insufficient**, with
no AI answers or specialist acceptance. This is a local, pre-publication result;
live-service and browser acceptance remain separate gates.
The [staff-question results and Monday walkthrough](evaluation/staff-questions/results.md)
compare the two runs and explain the remaining work.

Full-corpus retrieval ranks literal question terms and takes bounded whole-page
candidates. Existing concept aliases and relationships keep their original
scopes, including custody-specific concepts. A lexical match does not establish
which rules apply or that every necessary exception is represented. The
immutable baseline receipts below retain their original scope. CPAG remains an
external reference, with no handbook-body acquisition or reuse permission
established.

The [relationship audit](docs/relationship-audit.md) separately distinguishes
authored links preserved in the data, sparse domain modelling and Explorer
display defects. The [repository governance record](docs/repository-governance.md)
records required pull requests, the `validate` merge check and private-input
protections.

## Ask OKF: governed context assembly

This section preserves the custody acceptance case at its immutable content
version. The 52-record evidence profile is narrower than the acquired manuals.

[Open the public Ask OKF demonstration](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2Fefb05c66616a9cd4328a86cf412780fe7bc7cf0b%2Ffull-dmg%2Fokf-explorer.json&q=imprisonment#overview),
then select **Ask OKF** and use the exact question in the
[five-minute demonstration script](docs/context-assembly-demo.md). It assembles a
traceable evidence package for JSA, Income Support, State Pension Credit and ESA.
It resolves declared concepts, traverses directed source relationships and checks
whole evidence, provenance, scope and budgets before reporting scoped sufficiency.
The [independent A–H acceptance case](evaluation/context-assembly/imprisonment-case.json)
checks source and graph identities rather than keyword overlap. It is separate
from the earlier 160 model answer trials. No AI answer or individual entitlement
decision is generated; specialist and native tool-host acceptance remain separate gates.

The [public browser check](validation/ask-okf/public-browser.json) verified
52 context records, 127 relationships, chapter routing, source provenance,
inspectable JSON and an insufficient result under a constrained byte budget.
The package matched a fresh direct engine run. DWP's 56 unit tests and all
context controls passed; the unchanged earlier answer trials remain separate.
This context release uses content commit `efb05c66616a9cd4328a86cf412780fe7bc7cf0b`;
the full-corpus and pilot links below preserve their earlier release scopes.

## Remote Ask OKF acceptance

The remote MCP adapter lives in OKF Explorer and imports its existing context
engine. This repository supplies the [remote acceptance cases and replay
instructions](evaluation/remote-mcp/README.md), including the hospital question.
The [hospital coverage review](docs/remote-mcp-hospital-coverage.md) distinguishes
material acquired in the wider corpus from evidence governed by the pinned Ask
custody index. Hospital evidence in that profile is insufficient; retrieved custody records
must not be presented as hospital guidance. Deployment and actual ChatGPT
invocation are separate gates recorded in the [remote demonstration guide](docs/remote-mcp-demo.md).

## What is here

**The full-DMG research candidate is publicly available at an immutable, browser-checked content commit.** [Try the full corpus](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F80b6f08426aea39dd2934fb8795b61215e2cc0ad%2Ffull-dmg%2Fokf-explorer.json&q=84351&view=narrative#page/84/0035) or follow the [full-DMG walkthrough](docs/full-dmg-walkthrough.md). Publication and canonical CI history are tracked in [PR 5](https://github.com/chris-page-gov/okf-dwp/pull/5); the immutable browser receipt applies to the content commit named below. The owner authorised unattended processing against the frozen 331-PDF census, with a 24 September content freeze for the 30 September seminar. The [completion plan](docs/next-stage/unattended-completion.md) and [current checkpoint](evaluation/full-dmg-progress.json) record the acceptance gates. The earlier links retain their original Pension Credit scope.

The [full-DMG acquisition](docs/next-stage/full-dmg-acquisition.md) contains **331 PDFs and 14,743 measured pages**, with original bytes, source hashes and extraction-quality flags. Eight wider authoring batches add **245 concepts and 328 source-backed proposals** across **78 of 78 substantive PDF units**. Including the pilot, the candidate has **271 concepts and 343 semantic proposals**, within **15,390 entities, 16,210 assertions and 15,363 resource records**. [Measured coverage](evaluation/full-dmg-coverage.json) distinguishes selected-passage research from complete policy modelling. Specialist acceptance remains **zero**.

| Layer | Full-DMG research candidate | Preserved Pension Credit pilot |
| --- | --- | --- |
| Frozen sources | 331 PDFs; 14,743 measured pages | Original 36 PDFs; 1,524 pages |
| Searchable content | Every extracted page, including labelled memos, amendments, transitional and reference material | Seven substantive chapters; 744 default page records; other acquired roles require explicit inclusion |
| Authored concepts and proposals | 271 concepts; 343 proposals, including the pilot | 26 concepts; 15 proposals; eight personas, ten stories and 14 questions |
| Semantic delivery | YAML-LD control, bounded JSON-LD/RDF shards and lazy indexed records | Small YAML-LD/JSON-LD bundle and Markdown records |
| External adviser reference | CPAG metadata and links only | Same access and rights boundary |
| Reproducibility | Locked dependencies, source/output hashes, deterministic build, consumer and evidence checks | Original source identities, routes, frozen domain profile and immutable demonstration links retained |

All 253 remaining source-family units have a recorded research outcome: **242 completed with documented gaps and 11 spare units marked not applicable with evidence**. This is bounded accounting, not full-body review or a finding that memos and annexes contain no substantive rules. See the [source-family review](evaluation/full-dmg-source-family-review.json).

The **160 observed, context-aware, source-guided answer trials** have separate model assessments: **90 supported, 56 partial and 14 with underspecified rubrics**. These are assessor categories, not an accuracy score or a blind end-to-end retrieval benchmark. Original prompts, reads, responses, omissions and assessments are retained in the [trial summary](evaluation/full-dmg-behavioural/summary.json). Indexed retrieval controls are separate evidence; no specialist approval, comparative model result, voice or WebMCP performance is inferred.

The capture date is **15 September 2026**. The original Pension Credit landing page reported **20 July 2026** as its latest update. Neither capture nor listing dates establish a provision’s current applicability. The [original pilot coverage](bundle/coverage.json) and [original extraction report](source/extraction-quality.json) retain their 36-PDF scope; [full-DMG coverage](full-dmg/coverage.json) describes the larger candidate.

## Try it

Open the full-DMG candidate at content commit `80b6f08426aea39dd2934fb8795b61215e2cc0ad`, snapshot `dwp-full-dmg-2026-09-15-2dd78242297c`:

- [JSON entry: find paragraph 84351](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F80b6f08426aea39dd2934fb8795b61215e2cc0ad%2Ffull-dmg%2Fokf-explorer.json&q=84351&view=narrative#page/84/0035).
- [YAML-LD entry: read chapter 84, PDF page 35](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F80b6f08426aea39dd2934fb8795b61215e2cc0ad%2Ffull-dmg%2Fokf-explorer.yamlld&view=narrative#page/84/0035).
- [ESA Graph: exceptional limited capability for work risk](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F80b6f08426aea39dd2934fb8795b61215e2cc0ad%2Ffull-dmg%2Fokf-explorer.json&view=graph#term/esa-exceptional-lcw-risk).
- [CPAG Timeline: April 2026 publication month](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F80b6f08426aea39dd2934fb8795b61215e2cc0ad%2Ffull-dmg%2Fokf-explorer.json&view=timeline&q=CPAG#resource/cpag-welfare-benefits-handbook).

The [public browser receipt](validation/full-dmg-browser.json) records the exact content and consumer identities. Checked journeys include both entry formats, source text and a direct PDF link, labelled Graph relationships, PDF resource cards, CPAG's month-precision Timeline and bounded search controls. The observed ESA Graph had 11 nodes and 10 edges with no missing labels; `84351` returned six labelled PDF resources. These checks establish those interactions, not every route or policy interpretation. See the [ten-minute full-DMG walkthrough](docs/full-dmg-walkthrough.md).

Explorer can expand an unmatched search string into an indexed term: `unavailableclaimantdetails` returned seven results for `unavailable` in the public check. Inspect the displayed query interpretation and the source evidence. The nonsense control `zzzxqvnomatch` returned an unmatched term and no results; the exact Python retrieval controls test a separate path.

[Launch the original meeting demonstration](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F79d21c758e37948fd6d4bde0f1b4d97b266e2e4f%2Fbundle%2Fokf-bundle.yamlld&q=84351#question/pc001). It uses the immutable captured bundle and starts with the capital-disregard question and matching evidence. [Browser verification](validation/browser.json) records the exact snapshot and journeys. You can also load `bundle/okf-bundle.json` as a local file in Explorer.

Start with **Where does the guide explain capital disregards?** (`question/pc001`). Follow the question to chapter 84, PDF page 35, inspect the original source and its hash, then explore the relationships. Use `question/pc003` to examine historical context and extraction limits, and `question/pc008` for the scope boundary.

An AI can read the repository or the generated bundle directly. The [AI guide](AI_USAGE.md) provides a prompt requiring chapter/page citations, source hashes and explicit missing-evidence handling. Loading the files does not create an MCP server or connect to DWP systems.

## Build and verify

Install [uv](https://docs.astral.sh/uv/) and run:

```sh
uv sync --locked
uv run --locked python scripts/build_bundle.py
uv run --locked python scripts/build_bundle.py --check
uv run --locked python scripts/validate_bundle.py
uv run --locked python domain-profile/validate.py
uv run --locked python scripts/evaluate_queries.py
```

For the full-DMG candidate:

```sh
uv run --locked python scripts/build_full_dmg.py
uv run --locked python scripts/build_full_dmg.py --check
uv run --locked python scripts/validate_full_dmg.py
node --experimental-strip-types scripts/check_full_dmg_consumer.mjs
uv run --locked python scripts/report_full_dmg_coverage.py --check
uv run --locked python scripts/evaluate_full_dmg.py --check
uv run --locked python scripts/reconcile_full_dmg_references.py --check
uv run --locked python scripts/verify_full_dmg_trials.py --check
```

Its Explorer entry point is `full-dmg/okf-explorer.json` (or `full-dmg/okf-explorer.yamlld`). `full-dmg/okf-bundle.yamlld` is a semantic control document pointing to bounded graph shards; it is not a small-bundle import. The launch links above name the immutable candidate checked in the browser. The original 15 September release recorded 43 passing local tests. The trial verifier checks retained evidence and reproduces the assessment summary; it does not run new model answers or assign grades.

For the separately acquired ADM manual, staff-question baseline and publication
guards:

```sh
uv run --locked python scripts/acquire_adm.py --check
uv run --locked python scripts/test_acquire_adm.py
uv run --locked python scripts/build_context_discovery.py --check
uv run --locked python scripts/build_context_corpus.py --check
uv run --locked python scripts/audit_relationships.py --check
uv run --locked python scripts/check_private_inputs.py
uv run --locked python scripts/test_private_inputs.py
node --experimental-strip-types scripts/evaluate_staff_questions.mjs --check --explorer-root ../okf-explorer
node --experimental-strip-types scripts/test_staff_questions.mjs --explorer-root ../okf-explorer
```

The staff-question replay needs the matching Explorer context implementation;
the retained receipt binds its exact file hash. It replays saved remote responses
without calling a model or a live endpoint. The private-input check rejects
tracked or staged `.email.md` files without reading their contents; run it before
committing or pushing, not only in CI. The [governance guide](docs/repository-governance.md)
explains these boundaries.

The consumer check uses Node 26.7.0 in CI and unmodified, hash-pinned Explorer validation code under `profiles/explorer-runtime/`. It verifies the research notice and every route label against the actual consumer contract. Publisher titles retain their original bytes; display labels normalise whitespace only.

The [reference register](evaluation/full-dmg-dependencies/index.json) accounts for literal DMG paragraph, memo and legal-reference candidates across all 331 sources. It distinguishes single candidate locations, ambiguous matches and unresolved identifiers. A match supplies navigation; it does not establish legal identity, incorporation or present applicability.

These commands use the frozen source snapshot. They do not redownload the collection. Build `--check` rebuilds in memory and compares generated bytes with retained artefacts; the other checks validate their named evidence and projections.

For keyword retrieval with JSON citations:

```sh
uv run --locked python scripts/query.py '84351' --limit 5
uv run --locked python scripts/query.py 'part-week payments' --limit 5
```

`--include-history` explicitly includes all acquired document roles within the selected inventory. `--scope full-dmg` selects the 331-PDF inventory; the default remains the original Pension Credit inventory. Results identify the exact inventory hash and source role. Broad terms can rank scenario-specific examples above general rules; the CLI is retrieval, not legal reasoning. No-result queries return no invented evidence.

A deliberate source refresh is separate: inspect `scripts/acquire_sources.py --help` and [source instructions](source/README.md), acquire a new snapshot, review changes and repeat discovery and assurance. Do not silently overwrite the meaning of an existing release.

## Authoring and format boundaries

- `knowledge/**/*.yamlld` contains project-authored concepts, navigation and semantic proposals. `knowledge/full-dmg/` is additive and excluded from the original pilot build.
- `source/` preserves captured evidence and extracted representations.
- `domain-profile/` preserves the researched handoff, evidence, gaps, prompt hashes and consumer lock.
- `bundle/` is generated: Markdown, runtime JSON, YAML-LD, JSON-LD, canonical RDF, checksums and coverage.
- `full-dmg/` is the generated indexed corpus and sharded semantic delivery.
- `profiles/bundle-wiki/` vendors the 16 canonical Explorer profile files with an unchanged vendor lock.
- `okf.semantic.json` and `okf.publication.json` declare the semantic and publication boundaries.

OKF 0.2 is the Markdown core. “OKF+” here means that core plus the additive Explorer Bundle Wiki semantic profile; it is not a separate universal OKF standard. YAML-LD 1.0 remains a W3C Working Draft. The build uses pinned local contexts and URDNA2015 RDF normalisation; it does not claim RDFC-1.0 or SHACL conformance.

## What the exemplar does not establish

The source PDFs contain historical examples, dates, scenario-specific treatments and references to memos, legislation and case law. These have not been exhaustively consolidated or legally reviewed. Machine extraction has known defects, particularly letter spacing in chapter 83. Across the **331-PDF capture, 802 pages have no extracted text**; no exhaustive visual review or OCR has established whether those pages are blank or image-only. The original 36-PDF pilot had 85 such pages, including ten within its default 744 page records.

Source acquisition and bounded research attempts are complete for the declared full-DMG scope. The public browser receipt covers its named interactions. The full Foundry production gate sequence, comprehensive accessibility assurance, expert legal review and automatic legal rule modelling are **not complete**. [Repository status](REPOSITORY_STATUS.md) records the candidate boundary and validation evidence. No claimant case data was acquired.

## Reuse and next steps

[Open the CPAG reference in Explorer](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F7d3c69df0571b8d5206c8edce92963d99979cb5c%2Fbundle%2Fokf-bundle.yamlld&view=timeline&q=CPAG#resource/cpag-welfare-benefits-handbook).

The [CPAG handbook access review](docs/cpag-handbook.md) explains the new
searchable external reference and the permission required before handbook
content could be processed or redistributed. Search **CPAG** in the updated
bundle to inspect it. The original meeting link above preserves its earlier
snapshot; the CPAG reference requires the updated bundle.

Contains public sector information licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Original project code and original material use the [MIT licence](LICENSE); source extracts retain Crown copyright, attribution and applicable exceptions. See [NOTICE.md](NOTICE.md).

The [later-source log](docs/future-sources.md) records tribunal decisions, benefits calculators and CASA for later assessment. They are not incorporated into this snapshot. The [product backlog](docs/backlog.md) records wider persona/journey evaluation, a benefits engine and application/change-of-circumstances journeys. The recorded source-guided trials do not deliver those operational journeys.

## Semantic stage two and seminar preparation

[Read the next-stage assessment and delivery plan](docs/next-stage/README.md).
The preserved Pension Credit pilot has **26 individual concept files**,
**15 source-backed semantic proposals**, a non-executable capital-disregard
review candidate, **eight personas, ten stories and 14 questions**.
[Its semantic map](bundle/semantic-map.md) retains that bounded scope. The
full-DMG candidate adds the wider concepts and observed trials described
above. Model assessment does not make either layer specialist-reviewed.

All **331 DMG PDFs** are acquired and indexed. The separate **182 ADM PDFs**
have now also been [acquired with original bytes and page text](docs/adm-acquisition.md),
giving 513 documents and 19,090 measured pages across the two source families.
The first combined-corpus evaluation is recorded locally; live-service and
browser acceptance remain separate delivery gates. The earlier custody profile
and its receipts have not been rewritten.
[The 24 September plan](docs/next-stage/full-dmg-by-24-september.md)
separates source acquisition, semantic coverage and expert review. Content
freezes on 24 September for the 30 September seminar; website, WebMCP and Mac
voice/audio feasibility are [tracked separately](docs/next-stage/seminar-webmcp-and-audio.md).

Concept authoring now uses `knowledge/**/*.yamlld`. Additional checks:

```sh
uv run --locked python scripts/evaluate_semantics.py
python3 source/discovery-2026-09-15/acquire_metadata.py --check
```

The earlier Explorer links remain pinned to their original snapshots. Stage-two
browser verification and publication state are recorded in [repository status](REPOSITORY_STATUS.md).

[Open the stage-two semantic graph in Explorer](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F7d3c69df0571b8d5206c8edce92963d99979cb5c%2Fbundle%2Fokf-bundle.yamlld&view=graph#term/capital-disregards). The [pilot browser receipt](validation/cpag-timeline-browser.json) binds this graph and the corrected CPAG Timeline to the checked content commit; the [earlier semantic receipt](validation/stage-two-browser.json) records the detailed relationship journeys.
