<a id="pension-credit-guidance-as-an-okf-bundle"></a>

# DWP guidance as an OKF+ bundle

**An independent, unofficial experimental exemplar. Not an official DWP document, benefits advice or an entitlement calculator.**

This repository turns the public [DWP Decision makers’ guide](https://www.gov.uk/government/collections/decision-makers-guide-staff-guide) into source-linked records, a YAML-LD semantic graph and an indexed OKF Explorer research candidate. It began with a [Pension Credit pilot covering volumes 13 and 14](https://www.gov.uk/government/publications/decision-makers-guide-vols-13-and-14-state-pension-credit-staff-guide). It demonstrates how a specialist or an AI can find evidence, inspect relationships and see what remains uncertain.

[Verified Pension Credit semantic exemplar](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F7d3c69df0571b8d5206c8edce92963d99979cb5c%2Fbundle%2Fokf-bundle.yamlld&view=graph#term/capital-disregards) · [Original meeting demonstration](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F79d21c758e37948fd6d4bde0f1b4d97b266e2e4f%2Fbundle%2Fokf-bundle.yamlld&q=84351#question/pc001) · [Read the pilot bundle](bundle/index.md) · [Ten-minute meeting walkthrough](docs/meeting-walkthrough.md) · [Discovery findings](docs/discovery.md) · [AI interrogation guide](AI_USAGE.md) · [Public notice and rights](NOTICE.md)

## What is here

**The full-DMG research candidate is prepared; final browser verification and publication are pending.** The owner authorised unattended processing against the frozen 331-PDF census, with a 24 September content freeze for the 30 September seminar. The [completion plan](docs/next-stage/unattended-completion.md) and [current checkpoint](evaluation/full-dmg-progress.json) record the acceptance gates. The links above remain the verified Pension Credit demonstrations.

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

Its Explorer entry point is `full-dmg/okf-explorer.json` (or `full-dmg/okf-explorer.yamlld`). `full-dmg/okf-bundle.yamlld` is a semantic control document pointing to bounded graph shards; it is not a small-bundle import. Final launch links will name the immutable candidate actually checked in the browser. The trial verifier checks retained evidence and reproduces the assessment summary; it does not run new model answers or assign grades.

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

Source acquisition and bounded research attempts are complete for the declared full-DMG scope. The final browser/publication gate, full Foundry production gate sequence, comprehensive accessibility assurance, expert legal review and automatic legal rule modelling are **not complete**. [Repository status](REPOSITORY_STATUS.md) records the candidate boundary and validation evidence. No claimant case data was acquired.

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

All **331 DMG PDFs** are now acquired and indexed. The separate **182 ADM
PDFs** remain metadata discovery and are not part of this full-text corpus.
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

[Open the stage-two semantic graph in Explorer](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F7d3c69df0571b8d5206c8edce92963d99979cb5c%2Fbundle%2Fokf-bundle.yamlld&view=graph#term/capital-disregards). The [current browser receipt](validation/cpag-timeline-browser.json) binds this graph and the corrected CPAG Timeline to the checked content commit; the [earlier semantic receipt](validation/stage-two-browser.json) records the detailed relationship journeys.
