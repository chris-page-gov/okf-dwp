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
- `validation/browser.json`: actual consumer identity and journey evidence recorded against the immutable candidate.
- GitHub Actions: canonical branch validation status.

## Foundry boundary

The pre-existing Explorer Foundry warm-up and build prompts informed this work; their exact pins are in the domain profile. This is a bounded preview, not a claim that the complete Foundry production process has run. In particular, expert legal/terminology review, exhaustive external legislation and memo acquisition, full accessibility and cross-browser assurance, full positive/negative locked-consumer fixtures before acquisition, backwards compatibility assurance and production release-gate closure are deferred. The time-bounded user request authorised progressing a reviewable exemplar; no deferred gate is marked passed.

The draft domain profile's `blocking_for_build` entries describe blockers for a later governed production build. They do not revoke the owner's explicit authority for this documented preview. The limited build and browser receipts establish only their stated checks.

## Editorial check

Original project material uses British English and sentence case. Official titles, exact source extracts, schema/API fields, code identifiers, URLs and unmodified vendored profile bytes retain upstream wording intentionally. Source text is not silently edited for spelling, contemporary rates or apparent inconsistencies.

The final browser-verified snapshot is `dwp-pension-credit-2026-09-15-bdee692f1126`: 791 nodes and 850 evidence-bearing assertions. Direct JSON and YAML-LD imports both passed in the live Explorer. All 744 source pages also passed literal-text rendering checks after a numbering defect was found and corrected.

Publication consists of the public GitHub repository, immutable commit URLs and the verified Explorer demonstration. No separate GitHub prerelease or uploaded release assets have been created.
