# Combined Reader verification

[Published three-browser and conceptual-facet checks](public/README.md) now
record the separate real-HTTPS acceptance of the immutable content commit.

The [build receipt](build.json) binds every generated input/output. The browser observations below use the actual pinned Explorer application with source files supplied byte-for-byte from the local combined projection. They are **local candidate observations**, not a public deployment attestation or specialist legal review.

The [superseded observation archive](history/dwp-combined-80a1236a793a4828ae6e/README.md)
retains the earlier descriptor, build receipt and browser artefacts unchanged.
The current observations were rerun after the metadata-only rebind for the
official-effect-identifier secret-scanner false positive. Old observations are
not relabelled as proof of the replacement corpus.

The 14 combined-corpus controls and deterministic regeneration passed. These include direct-context JSON validity, canonical assertion provenance, unchanged captured source shards, full-text coverage and agreement between the direct Linked Data graph and its evidence-bearing reified assertions. The additive semantic export has 20,015 nodes and 21,082 assertions; source-page bodies remain in bound Reader records.

## Browser journeys

- [Chrome](browser/chrome/observation.json), [Firefox](browser/firefox/observation.json) and [WebKit](browser/webkit/observation.json) each passed the source-manual selection, Reader/Graph/Timeline consistency, source/audit date separation, P1001 search, exact official ADM PDF page link, PIP semantic graph and supplied Child DLA/PIP question.
- Each engine verified the same 21 application files and fetched 249 corpus files. Console errors: zero.
- Each also completed a 390 × 844 viewport journey through Ask using keyboard navigation, returned the same package as desktop, retained focus on the JSON disclosure and had no page-level horizontal overflow. Targeted Axe checks reported zero violations for desktop Ask and the narrow Ask/panel controls. Chrome and Firefox used Tab/Shift+Tab; the installed macOS WebKit used Alt+Tab/Alt+Shift+Tab (Option on a Mac). These are recorded key events with no browser preference override. No physical mobile device or screen-reader session was tested.
- All three produced the same context identifier. The staff question remained **insufficient**, with no model answer. The exact returned context is retained beside each observation.
- The [conceptual-facet observation](browser/facets/observation.json) separately checks all five facet groups across Reader, Graph and Timeline using the existing Explorer acceptance harness. It includes targeted accessibility checks; no violations were found in those controls. This is not a whole-application accessibility certification.

The Explorer application tree is `fa442a5f0806c0c9c7f5ab19c1f1362fe48be5cf2a1628414f2bc17114c9dc58`, with manifest hash `1a08fe787725fc48c132068d08161c090fd6fae6395ffd01ec47309187e10087`. Its upstream implementation is pinned to `f8daf84a4c04afb4839695d38a97cbf21b0ed0a0` in [Explorer PR 126](https://github.com/chris-page-gov/okf-explorer/pull/126). The dated observations identify the separate combined corpus snapshot and descriptor hash.

## Screenshots

- [PIP concept and source relationships](browser/chrome/pip-graph.png)
- [ADM source page](browser/chrome/adm-source-page.png)
- [ADM audit dates](browser/chrome/adm-timeline.png)
- [Staff question in Ask OKF](browser/chrome/ask-staff-question.png)
- [Narrow-screen keyboard inspection](browser/chrome/mobile-keyboard-ask.png)
- [Benefit mentions](browser/facets/benefit-reader.png)
- [Circumstance selection in Timeline](browser/facets/circumstance-timeline.png)

## Repeat the checks

See [the combined Reader guide](../../docs/combined-reader.md) for browser commands. The [artefact manifest](browser/artifacts.json) fingerprints the retained observations, packages and screenshots. `scripts/check_combined_reader_observations.py` verifies those fingerprints and checks that all fetched corpus files still match this candidate; it does not launch a browser or certify a later public deployment.
