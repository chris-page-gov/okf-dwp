# Repository status

**Lifecycle: experimental public preview.** The owner explicitly authorised a public `chris-page-gov/okf-dwp` repository, an OKF+ YAML-LD exemplar and a demonstration for a pensions representative on 15 September 2026. The owner later supplied three links with an instruction to log them without changing the 4pm workstream.

The initial repository scaffold was committed separately before feature work. Source acquisition, discovery, build and independent review ran in parallel; publication proceeds through a feature pull request. Source and generated artefacts remain distinct.

## Evidence

- `source/inventory.json`: complete attachment census and byte identities.
- `source/extraction-quality.json`: extraction counts and sampled visual inspection.
- `source/review-samples.json`: seven representative chapter samples and caveats.
- `domain-profile/check.json`: schema, evidence and snapshot binding checks.
- `validation/bundle.json`: all-assertion, projection, hash and source-coverage checks.
- `validation/retrieval.json`: six positive and two negative retrieval controls.
- `validation/browser.json`: initial meeting consumer evidence against its immutable candidate.
- `validation/cpag-browser.json`: CPAG reference checks in both YAML-LD and JSON imports against the updated immutable candidate.
- GitHub Actions: canonical branch validation status.

## Foundry boundary

The pre-existing Explorer Foundry warm-up and build prompts informed this work; their exact pins are in the domain profile. This is a bounded preview, not a claim that the complete Foundry production process has run. In particular, expert legal/terminology review, exhaustive external legislation and memo acquisition, full accessibility and cross-browser assurance, full positive/negative locked-consumer fixtures before acquisition, backwards compatibility assurance and production release-gate closure are deferred. The time-bounded user request authorised progressing a reviewable exemplar; no deferred gate is marked passed.

The draft domain profile's `blocking_for_build` entries describe blockers for a later governed production build. They do not revoke the owner's explicit authority for this documented preview. The limited build and browser receipts establish only their stated checks.

## Editorial check

Original project material uses British English and sentence case. Official titles, exact source extracts, schema/API fields, code identifiers, URLs and unmodified vendored profile bytes retain upstream wording intentionally. Source text is not silently edited for spelling, contemporary rates or apparent inconsistencies.

The initial meeting browser-verified snapshot is `dwp-pension-credit-2026-09-15-bdee692f1126`: 791 nodes and 850 evidence-bearing assertions. Direct JSON and YAML-LD imports both passed in the live Explorer. All 744 source pages also passed literal-text rendering checks after a numbering defect was found and corrected.

Publication consists of the public GitHub repository, immutable commit URLs and the verified Explorer demonstration. No separate GitHub prerelease or uploaded release assets have been created.

## CPAG external reference addition

The owner subsequently requested a CPAG handbook assessment and bundle addition.
The updated snapshot `dwp-pension-credit-2026-09-15-e49131bd7ef0` contains 792 records and
852 navigation/containment assertions, including one metadata-only external
reference. The 744 DWP source-page records are data-equivalent to the initial
meeting snapshot. The original domain-profile handoff remains frozen; the
CPAG access review is separate under `docs/cpag-handbook.md`.

Publication timestamps now follow the latest recorded source or authoring
observation. YAML whitespace is normalised only when decoding proves that
the data is unchanged. Existing source-rendering and initial browser receipts
remain scoped to their named snapshot; the CPAG browser check is recorded
separately.

The CPAG reference passed live Explorer checks in Edge using both YAML-LD and
JSON. Search, access wording, publisher links, Graph and the exact snapshot
notice were checked; neither tab captured warning or error logs. See
`validation/cpag-browser.json` for the immutable content commit and hashes.

## Semantic stage two

Started following the owner's request to move beyond the meeting preview and
prepare a wider exemplar. The working candidate adds individual concepts,
source-backed semantic proposals, a non-executable rule review packet,
legislation catalogue references and expanded evaluation journeys. The new
full-DMG/ADM census contains publication metadata only. No additional PDF
content is claimed as acquired.

The original domain profile and earlier browser receipts remain frozen. New
behavioural cases are designed but not run, and no specialist approval is
recorded. The CPAG public contents harvest remains a separate local research
artefact; this change does not publish its 90-entry outline or incorporate
handbook text. The semantic pilot does not depend on those local files.

Content freeze is 24 September 2026; the seminar is 30 September. WebMCP and
MacBook/PA integration are at feasibility stage, with ChatGPT live voice identified and its actual
Mac/task/browser/audio integration awaiting rehearsal. No new website, audio configuration or voice-tool
integration is delivered by this candidate.

The initial stage-two candidate snapshot was
`dwp-pension-credit-2026-09-15-42c0a30e120c`: **821 records and 964 assertions**
(744 page-containment, 205 navigation and 15 model-derived semantic proposals).
All 744 source-page runtime records are unchanged from the previous public
baseline. Local deterministic generation, all-assertion/RDF validation,
12 semantic negative controls, eight retrieval controls and the frozen wider
metadata census pass. Independent agent review covered semantic wording and
validation failure modes; this is not human domain review. See
`validation/semantics.json` and `validation/semantic-review.json`.

The exact stage-two content commit `48abaff6c640e4a3e206af1adc71e21efd12738f` passed live Explorer import checks in installed Edge for YAML-LD and JSON, semantic relationship inspection, graph labels, the non-executable candidate and its original PDF-page link. No warning or error logs were captured in either test tab. [Browser receipt](validation/stage-two-browser.json).

### CPAG source date correction

The updated candidate `dwp-pension-credit-2026-09-15-1b84574268ad` preserves the
same 821 records, 964 assertions and source pages. CPAG's public metadata
establishes April 2026 as the handbook release month. The referenced book now
records that month separately from the original 15 September metadata capture,
record generation and later publication-metadata review. The source statement
does not establish an exact release day or a legal effective date. Earlier
browser receipts retain their original snapshot scope.
