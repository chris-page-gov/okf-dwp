# Public Chrome observation: household qualifications

This directory preserves an actual public Chrome observation made on **21
September 2026 at 01:23 British Summer Time**. It checked the published Explorer
against an immutable DWP bundle. A separate offline checker verifies the retained
files; running that checker does not open a browser or establish present website
availability.

## Exact versions

- DWP source: `7f9feb9634e3d94004853b838462aca132c505a5`.
- Explorer assembler source: `c4f2de0a99b7bc2f8b8c8a06a3c715fb56b66d8e`.
- Observed application manifest SHA-256:
  `9fc8cb1bbf10e4e5182efd69d56f2b5ed39a2e6ecf942dce64357c4a529d1ce8`.
- Browser: Chrome `153.0.8010.52`.
- [Original observation](attempt-01-chrome/observation.json),
  [executed browser harness](attempt-01-chrome/executed-harness.mjs) and
  [application manifest](attempt-01-chrome/app-manifest.json).

An **immutable version** is a saved revision whose contents do not change. A
**SHA-256 digest** identifies exact bytes, helping detect accidental alteration.
The [approval manifest](approval-manifest.json) records the separately approved
identities. The [artefact manifest](artifact-manifest.json) binds all 11 original
files and records the later offline checks. It does not claim that the checker
was part of the browser execution.

## What was observed

The browser used real HTTPS responses without interception or replacement.
All 21 application materials were checked, and 14 of those materials were also
observed loading in the page. The corpus census records 294 responses totalling
36,995,106 bytes, covering 270 distinct source paths. The harness retained 273
source-input identities, including its supporting reference inputs.

The journeys showed:

- A conceptual household facet with eight records.
- Twenty statutory units in the legislation view, with requested legal-version
  dates kept out of the source-publication timeline.
- The exact captured regulation 5 text and incoming/outgoing graph connections.
- Staff 012's care-home question, including the controlling no-partner heading.
- Staff 008's ambiguous “SDA” question, with both meanings still unresolved.

| Retained Ask context | Records | Relationships | Complete compact JSON | Evidence status |
| --- | ---: | ---: | ---: | --- |
| [Care home](attempt-01-chrome/care-home-context.json) | 62 | 124 | 515,316 bytes | Insufficient |
| [SDA](attempt-01-chrome/sda-context.json) | 64 | 99 | 477,761 bytes | Insufficient |

Both use a 524,288-byte context limit and explicitly report truncation. The
care-home package includes the seven household support pages, while other
declared gaps remain. These are evidence packages, not generated AI answers or
entitlement decisions.

The relationship counts include 42 care-home and 35 SDA rows whose targets were
not selected because of the budget. All such targets exist in the frozen source
graph and have explicit omission diagnostics (37 and 31 distinct targets).
Those rows are references to omitted material, not evidence that its content was
supplied. The checker preserves and verifies this distinction.

The selected items separately contain 108 care-home and 128 SDA traversal-path
references. Every step matches the direction of an immutable source assertion;
all records and edges in those particular paths are retained. All 39 care-home
and 12 SDA returned required-path occurrences are also retained (including
repeated paths across requirements). These path counts do not remove the other
declared evidence or applicability gaps and do not establish answerability.

Screenshots: [concept facet](attempt-01-chrome/concept-facet.png),
[statutory Reader](attempt-01-chrome/statutory-reader.png),
[timeline](attempt-01-chrome/statutory-source-timeline.png),
[graph](attempt-01-chrome/statutory-graph.png),
[care-home Ask](attempt-01-chrome/care-home-ask.png) and
[SDA alternatives](attempt-01-chrome/sda-alternatives.png).

## Offline integrity checks

From the repository root, with the locked environment installed:

```sh
uv run --locked python scripts/check_pinned_public_household_observation.py
uv run --locked python scripts/test_pinned_public_household_observation.py
```

The checker makes no network or model call. It verifies:

- All 273 observed source files against their exact immutable Git blobs.
- The application manifest, complete unique material census and observed loaded
  asset identities.
- Descriptor, corpus manifest, semantic snapshot and package identity bindings.
- Every selected record and relationship against the frozen corpus, with whole
  text hashes for 44 care-home and 46 SDA evidence items. Those are occurrences
  across two packages, not a claim of 90 distinct source pages.
- Directed traversal paths, exact questions, byte/node/relationship/depth budgets,
  unchanged insufficient status, and absence of an AI answer.
- File admission, symlink/escape rejection, bounded reads and decompression,
  duplicate-key rejection and a complete artefact inventory.

The executable checker pins the approved source/application/observation
identities outside the observation itself. Changing a receipt and its adjacent
manifest cannot silently approve another release.

## Boundaries

This is one dated Chrome observation. It establishes neither cross-browser nor
assistive-technology acceptance. The offline checks cannot reconstruct the
network event or independently infer what a screenshot means. The original
harness's response-body limits were checked after receipt, not enforced as a
hard network transfer ceiling. No remote Ask OKF service or model was called.

The exact source release above predates the later disability-addition
qualification increment. This observation does not attest that newer source.
Earlier [3ef public observations](../3ef0e786/README.md), including their failed
first attempt, and their original checker remain unchanged. Source extracts and
project interpretations remain unreviewed; specialist review and evidence
closure are separate work.
