# Pension Credit guidance as an OKF+ bundle

**An independent, unofficial experimental exemplar. Not an official DWP document, benefits advice or an entitlement calculator.**

This repository turns the public [DWP Decision makers’ guide, volumes 13 and 14](https://www.gov.uk/government/publications/decision-makers-guide-vols-13-and-14-state-pension-credit-staff-guide) into source-linked Markdown, a YAML-LD semantic graph and an OKF Explorer bundle. It demonstrates how a pensions specialist or an AI can find source evidence, inspect relationships and see what remains uncertain.

[Open the current semantic exemplar](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F7d3c69df0571b8d5206c8edce92963d99979cb5c%2Fbundle%2Fokf-bundle.yamlld&view=graph#term/capital-disregards) · [Original meeting demonstration](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F79d21c758e37948fd6d4bde0f1b4d97b266e2e4f%2Fbundle%2Fokf-bundle.yamlld&q=84351#question/pc001) · [Read the bundle](bundle/index.md) · [Ten-minute meeting walkthrough](docs/meeting-walkthrough.md) · [Discovery findings](docs/discovery.md) · [AI interrogation guide](AI_USAGE.md) · [Public notice and rights](NOTICE.md)

## What is here

**Full-DMG completion is now under way.** The owner has authorised unattended processing and publication against the frozen 331-PDF census, with content frozen by 24 September. The [completion plan](docs/next-stage/unattended-completion.md) and [current checkpoint](evaluation/full-dmg-progress.json) distinguish work in progress from delivered coverage. The existing links above remain the verified Pension Credit demonstration.

The [full-DMG acquisition](docs/next-stage/full-dmg-acquisition.md) is complete: **331 PDFs and 14,743 measured pages**, with source hashes and extraction-quality flags. An indexed consumer has passed local source, search and semantic checks; live consumer verification is in progress. The first five wider authoring batches add **123 concepts and 161 proposals** across 34 substantive PDF units. [Measured coverage](evaluation/full-dmg-coverage.json) keeps the 44 remaining substantive units and specialist-review gaps visible.

| Layer | Delivered scope |
| --- | --- |
| Frozen source collection | All 36 linked PDFs, 1,524 pages, original bytes, source URLs and SHA-256 hashes |
| Default Explorer content | Seven substantive chapters, 744 page records with machine-extracted text and explicit extraction gaps |
| Additional captured material | Transitional chapter 80, spare chapters 81–82, two change summaries and 24 historical amendments; outside default page search |
| Authored discovery and semantic pilot | 26 individual concepts, eight personas, ten user stories, 14 questions and cross-chapter navigation; specialist review pending |
| External adviser reference | CPAG Welfare Benefits Handbook metadata and publisher links; subscription text is not included |
| Semantics | YAML-LD and JSON-LD, evidence-bearing containment and navigation, 15 source-backed semantic proposals, stable identities and local routes |
| Reproducibility | Locked dependencies, offline build from frozen inputs, source and output hashes, all-assertion validation and retrieval controls |

The capture date is **15 September 2026**. The source landing page reported its latest update as **20 July 2026**. Neither date establishes that every provision is currently applicable. See [coverage](bundle/coverage.json) and [extraction quality](source/extraction-quality.json).

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
uv run --locked python scripts/report_full_dmg_coverage.py --check
uv run --locked python scripts/evaluate_full_dmg.py --check
```

Its Explorer entry point is `full-dmg/okf-explorer.json` (or `okf-explorer.yamlld`). `full-dmg/okf-bundle.yamlld` is a semantic control document pointing to bounded graph shards; it is not a small-bundle import. Final launch links will name the immutable candidate actually checked in the browser.

These commands use the committed source snapshot. They do not redownload the collection. The final `--check` rebuilds in memory and compares every generated byte with the committed artefacts.

For keyword retrieval with JSON citations:

```sh
uv run --locked python scripts/query.py '84351' --limit 5
uv run --locked python scripts/query.py 'part-week payments' --limit 5
```

`--include-history` explicitly includes all acquired document roles within the selected inventory. Once the full-DMG inventory exists, `--scope full-dmg` selects it; the default remains the original Pension Credit inventory. Results identify the exact inventory hash and source role. Broad terms can rank scenario-specific examples above general rules; the CLI is retrieval, not legal reasoning. No-result queries return no invented evidence.

A deliberate source refresh is separate: inspect `scripts/acquire_sources.py --help` and [source instructions](source/README.md), acquire a new snapshot, review changes and repeat discovery and assurance. Do not silently overwrite the meaning of an existing release.

## Authoring and format boundaries

- `knowledge/**/*.yamlld` contains project-authored concepts, navigation and semantic proposals.
- `source/` preserves captured evidence and extracted representations.
- `domain-profile/` preserves the researched handoff, evidence, gaps, prompt hashes and consumer lock.
- `bundle/` is generated: Markdown, runtime JSON, YAML-LD, JSON-LD, canonical RDF, checksums and coverage.
- `profiles/bundle-wiki/` vendors the 16 canonical Explorer profile files with an unchanged vendor lock.
- `okf.semantic.json` and `okf.publication.json` declare the semantic and publication boundaries.

OKF 0.2 is the Markdown core. “OKF+” here means that core plus the additive Explorer Bundle Wiki semantic profile; it is not a separate universal OKF standard. YAML-LD 1.0 remains a W3C Working Draft. The build uses pinned local contexts and URDNA2015 RDF normalisation; it does not claim RDFC-1.0 or SHACL conformance.

## What the exemplar does not establish

The source PDFs may contain historical examples, dates, scenario-specific treatments and references to external memos, legislation and case law. These have not been exhaustively consolidated or legally reviewed. Machine extraction has known defects, particularly letter spacing in chapter 83; 85 pages across the full capture have no extracted text and have not been classified as blank or image-only. Ten of those pages fall within the default 744 page records.

The original 36-PDF Pension Credit collection has been captured. The full Foundry production gate sequence, comprehensive accessibility assurance, expert legal review and automatic legal rule modelling are **not complete**. [Repository status](REPOSITORY_STATUS.md) records the preview boundary and validation evidence. No claimant case data was acquired.

## Reuse and next steps

[Open the CPAG reference in Explorer](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F7d3c69df0571b8d5206c8edce92963d99979cb5c%2Fbundle%2Fokf-bundle.yamlld&view=timeline&q=CPAG#resource/cpag-welfare-benefits-handbook).

The [CPAG handbook access review](docs/cpag-handbook.md) explains the new
searchable external reference and the permission required before handbook
content could be processed or redistributed. Search **CPAG** in the updated
bundle to inspect it. The original meeting link above preserves its earlier
snapshot; the CPAG reference requires the updated bundle.

Contains public sector information licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Original project code and original material use the [MIT licence](LICENSE); source extracts retain Crown copyright, attribution and applicable exceptions. See [NOTICE.md](NOTICE.md).

The [later-source log](docs/future-sources.md) records tribunal decisions, benefits calculators and CASA for later assessment. They are not incorporated into this snapshot. The [product backlog](docs/backlog.md) records extensive persona/journey evaluation, a benefits engine and application/change-of-circumstances journeys for later work.

## Semantic stage two and seminar preparation

[Read the next-stage assessment and delivery plan](docs/next-stage/README.md).
The authored layer now has **26 individual concept files**, **15 source-backed
semantic proposals**, a non-executable capital-disregard review candidate,
**8 personas, 10 stories and 14 questions**. All new interpretations and
behavioural cases remain unreviewed. [Inspect the semantic map](bundle/semantic-map.md)
and its evidence register.

The wider source census identifies **331 DMG PDFs** and a separate **182 ADM
PDFs**. This is metadata discovery: only the existing 36 Pension Credit PDFs
are acquired for full-text search. [The 24 September plan](docs/next-stage/full-dmg-by-24-september.md)
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
