# Published combined Reader checks

**Observed on 20 September 2026.** These checks used the real published Explorer
and immutable GitHub corpus responses. No requests were intercepted and no local
corpus responses were substituted. This is a dated observation, not perpetual
deployment assurance or specialist approval of benefits guidance.

[Open the checked combined Reader](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F9de52acf1db84b27f8933d80480eaa850e74fa33%2Fcombined%2Fokf-explorer.json#overview)
· [PIP relationship demonstration](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F9de52acf1db84b27f8933d80480eaa850e74fa33%2Fcombined%2Fokf-explorer.json&view=graph#staff-domain/pip)

## Exact identities and outcomes

- Content commit: `9de52acf1db84b27f8933d80480eaa850e74fa33`.
- Snapshot: `dwp-combined-e288cc6c7cfdf1edf101`.
- Descriptor SHA256: `cdda143ca4a5e44f46d66bdaebc344b684b4b54da747bc508d1f5f3193f24f77`.
- Application manifest SHA256: `1a08fe787725fc48c132068d08161c090fd6fae6395ffd01ec47309187e10087`.
- Application tree SHA256: `fa442a5f0806c0c9c7f5ab19c1f1362fe48be5cf2a1628414f2bc17114c9dc58`.

After [Explorer PR 127](https://github.com/chris-page-gov/okf-explorer/pull/127)
and its [successful Pages deployment](https://github.com/chris-page-gov/okf-explorer/actions/runs/35534787876),
a separate [public fingerprint check](post-service-merge.json) fetched the manifest
and all 21 application files again. Their byte lengths and hashes were identical
to those bound by the three-browser observations below. This checked application
files only: it did not rerun journeys, accessibility checks or corpus requests,
and it does not attest the separately hosted evidence service. The original
observations and timestamps remain unchanged. The receipt also records a corrected
checker error in its first material-tree calculation; no application bytes changed.

[Chrome](chrome/observation.json), [Firefox](firefox/observation.json) and
[WebKit](webkit/observation.json) each verified all 21 application files and 249
fetched corpus files. All passed the ADM selection, Reader/Graph/Timeline
consistency, source/audit date distinction, P1001 search, exact official PDF page
link, PIP relationship graph and staff question in Ask OKF. Console errors were
zero. Desktop and narrow-screen targeted accessibility checks found no violations.

The narrow-screen journey used a 390 × 844 viewport and actual keyboard events.
Chrome and Firefox used Tab/Shift+Tab; installed macOS WebKit used
Alt+Tab/Alt+Shift+Tab, without a browser preference override. Each retained JSON
disclosure focus, returned the same package as desktop and had no page-level
horizontal overflow. No physical mobile device or screen-reader session was tested.

The separate [public five-facet check](facets/observation.json) verified Source
manual, Benefit mentions, Circumstance mentions, Topic mentions and Authored
concept references across Reader, Graph and Timeline. It checked 235 fetched
corpus files and reported no console errors or targeted accessibility violations.
Mention classifications and graph visibility do not establish legal applicability.

## The actual context budget

The question was **“What is the interaction between Child DLA and PIP?”**
All three engines returned context
`urn:sha256:60a1c8b165a6578101d21c3b84747e5b88084d55b47ad52ee8e000d596acdf16`:
50 records, 36 relationships, `insufficient`, and no AI answer. The exact
[Chrome package](chrome/context.json) retains all provenance and missing evidence.

| Budget field | Observed value |
| --- | ---: |
| Maximum records | 64 |
| Maximum relationships | 128 |
| Maximum depth | 6 |
| Maximum package bytes | 524,288 |
| Used package bytes | 216,464 |
| Reached depth | 3 |

The package is still truncated by the lexical candidate limit. A partly unused
byte budget does not mean all potentially relevant evidence was included.
The SDK compact examples use a different 262,144-byte budget. Context identifiers
also bind source addresses and other inputs: these observations do not claim
byte-for-byte SDK parity across different budgets or bindings.

## Loading observations and retained attempts

Times below are cumulative seconds from the start of each timed harness run,
including earlier checks and interactions. They are not isolated network latency,
a cold-cache benchmark or a service-level promise.

| Browser | Descriptor verified | ADM facet ready | Source page ready | Desktop Ask ready | Narrow keyboard journey complete |
| --- | ---: | ---: | ---: | ---: | ---: |
| Chrome | 3.21 s | 4.54 s | 7.11 s | 8.47 s | 10.59 s |
| Firefox | 3.27 s | 5.24 s | 8.50 s | 10.08 s | 13.52 s |
| WebKit | 3.09 s | 4.53 s | 8.52 s | 10.08 s | 12.98 s |

The [first Chrome attempt](failed-attempts/chrome-initial-five-second-wait.json)
exceeded the inherited five-second assertion wait while the ADM reduction still
said “Updating…”. It is retained as a failure. Public assertion waits were then
bounded at sixty seconds; the application and source bytes did not change. The
[first successful run](prior-observations/chrome-before-phase-timings/observation.json)
is preserved separately from the final runs with explicit phase timings. Later
attempts must likewise preserve failures; do not relabel them as passing receipts.

For Monday, load the intended route before speaking and allow the loading state
to finish. The timed reruns do not erase the earlier slow-load observation.

## Inspect and reproduce

- [PIP graph](chrome/pip-graph.png)
- [Official ADM page](chrome/adm-source-page.png)
- [Source and audit dates](chrome/adm-timeline.png)
- [Machine-readable Ask package](chrome/ask-staff-question.png)
- [Narrow keyboard journey](chrome/mobile-keyboard-ask.png)
- [Benefit filter](facets/benefit-reader.png)

Use the [combined Reader guide](../../../docs/combined-reader.md) for the ordinary
build and local checks. From the DWP checkout matching the published candidate:

```sh
OKF_EXPLORER_CHECKOUT=/path/to/okf-explorer \
OKF_COMBINED_APP_URL=https://chris-page-gov.github.io/okf-explorer/explore/ \
OKF_COMBINED_BUNDLE_URL=https://raw.githubusercontent.com/chris-page-gov/okf-dwp/9de52acf1db84b27f8933d80480eaa850e74fa33/combined/okf-explorer.json \
OKF_COMBINED_APP_MANIFEST_SHA256=1a08fe787725fc48c132068d08161c090fd6fae6395ffd01ec47309187e10087 \
OKF_COMBINED_BROWSER=chrome \
OKF_COMBINED_OUTPUT=/tmp/combined-public-repeat \
node scripts/check_combined_reader_browser.mjs
```

The app must still match the named manifest; a later deployment needs a new
observation. Choose a new, non-existent output directory for each public run:
an existing directory, file or symlink is rejected before browser dependencies
are loaded or a browser is launched. This preservation guard was added after
the observations above and checked offline; no browser journey was rerun for it.
The [prior harness source](harness-history/before-output-preservation-guard.mjs)
and [change record](harness-history/output-preservation-guard.json) preserve the
previous script. The historical observations did not bind a harness source hash;
this later archive does not retroactively add such a binding.
The [artefact manifest](artifacts.json) fingerprints retained outputs.
`uv run --locked python scripts/check_combined_reader_observations.py` checks their
integrity offline. It does not launch a browser or establish fresh availability.
