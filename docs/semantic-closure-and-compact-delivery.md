# Semantic closure and compact evidence delivery

[Learning path](learning-path.md) · [Logical evidence units](logical-evidence-units.md) · [Work log](logical-units-work-log.md) · [Backlog](backlog-work-packages.md)

This is an independent experimental publication. **Implementation and local
verification are recorded below; exact publication checks are separate.**
Source review by an agent is not specialist acceptance or an entitlement decision.

## Start with the problem

A PDF page is a **location**. A logical unit is a passage that keeps a rule's
conditions, examples, notes and citations together, including continuations on
the next page. A **dependency** is another passage needed to interpret it, such
as a definition, exception or update. The term **closure** here means finding and
retaining those dependencies; it does not mean that the legal question is settled.

This increment adds 29 reviewed boundaries to the earlier 46. It preserves the
513 frozen documents, 19,090 page locations and every extracted source byte.
Seventy-five authored units now retain 116,202 source bytes, with 37 crossing
page boundaries. The remaining 49,551 machine candidates are still uncertain.
Merging fragments into larger complete passages changes the unit denominator:
there are now 49,626 source-unit records, not 49,680.

## What source review found

| Source | Added evidence and retained boundary |
| --- | --- |
| DMG 04642 | Supersession scope, payment-in-advance/arrears branches, explicit late-notification exceptions and benefit-week definition. Other time-extension and chapter dependencies remain unresolved. |
| ADM C1988 and Memo 09/25 | An explicit source reference and confirming annotation; the memo's conditional absence rule, benefit and territorial scope, introduction and complete Universal Credit example. A memo's presence does not establish consolidation or contemporary applicability. |
| ADM E2092 and F1093 | The qualifying-young-person definition and qualifications were found. F1093 is in the frozen reserved range F1085–F1099: no missing definition was invented. |
| ADM P4019 → P4051 | P4019 describes the destination as hospital guidance, while P4051 concerns overlapping mobility payments. Both literals and the mismatch remain visible. |
| ADM P1, P4 and P5 | PIP age gateways, relevant-age alternatives, child DLA-to-PIP invitations, claims, non-claim consequences, determination and fixed-term alternatives. Further mobility, terminal-illness, territorial and transition branches remain open. |

**DMG** means Decision makers' guide; **ADM** means Advice for decision making.
**PIP** is Personal Independence Payment and **DLA** is Disability Living Allowance.
These are distinct benefits and regimes. A **supersession** replaces an existing
benefit decision because relevant circumstances or rules have changed; its
source-specific conditions and effective date must still be checked.

Read the exact [dependency source review](../domain-profile/logical-units/closure-review.md)
and [PIP transition review](pip-transition-source-review.md). All eight earlier
unresolved references retain their original notes, followed by separate target
identification findings. Four newly identified references also remain unresolved.
The source-scope mismatch and reserved reference are not counted as resolved rules.

## What the current evaluation shows

The [retained comparison](../evaluation/logical-units/run/summary.json) uses the
same 40 staff question occurrences, five focused questions and one unknown-term
control in page and unit modes at two budgets: **184 assemblies**. Eleven
negative controls check that unrelated benefits and ambiguous wording do not
silently activate the tested profiles. There were no network or model calls.

| Measure | Before this increment | Current result |
| --- | ---: | ---: |
| Authored unit boundaries | 46 | 75 |
| Scoped unit profiles | 5 | 7 |
| Staff occurrences activating a profile | 3/40 | 8/40 |
| Staff occurrences without a profile | 37/40 | 32/40 |
| Staff 512 KiB contexts with no returned relationships | 24/40 | 22/40 |
| Preserved earlier review obligations | 203 | 203 |
| Contexts reporting insufficient evidence | 184/184 | 184/184 |

Activation means that declared concepts matched; it does not prove the profile
is sufficient or that a DLA/PIP question intends a transfer. The eight include
broader Staff 029 and 036 mentions; those retain an explicit relationship-scope
gap. The intended new cases are Staff 026/033 (the same transition question)
and Staff 032 (pension age). The profile retains ambiguity rather than assuming
a transfer. A **KiB** is 1,024 bytes; 512 KiB is 524,288 bytes.

At 512 KiB the focused cases retain 10/10 Pension Credit abroad paths, 9/9
Universal Credit absence paths, 12/12 household-absence paths, 2/2 temporary-care
paths and 4/4 permanent-care paths. Staff 026 and its duplicate 033 retain 7/7
transition paths; Staff 032 retains its 1/1 age gateway path. These are declared
source-path counts, with changed denominators, **not answer-accuracy scores**.
All five focused 32 KiB inline packages still retain zero source evidence after
adding the new dependencies. This remains an explicit capacity limitation.

The [coverage ledger](../evaluation/semantic-coverage/closure-2026-09-22/audit.md)
traces every staff question to observed profile activation, exact source
candidates, retained paths, unresolved obligations and its existing learning
lesson. The [machine-readable ledger](../evaluation/semantic-coverage/closure-2026-09-22/audit.json)
binds the inputs with hashes. A hash identifies exact bytes. Candidate overlap,
profile requirements, returned evidence and open obligations have separate
measures; they must not be compressed into one completeness percentage.

## Why compact delivery is a separate improvement

An **assembly budget** limits the evidence package itself. A **delivery budget**
limits each response carrying that package to an AI client. Asking a client to
read a 512 KiB assembly through several 32 KiB responses preserves more evidence
than making the whole assembly fit inside 32 KiB.

Explorer adds read-only WebMCP operations `okf_context_manifest` and
`okf_read_evidence`, using its existing compact-delivery implementation. A
**manifest** is a catalogue of the package's sections and identities. **Exact
reads** return bounded portions of those sections. A compatible client must read
all required portions and verify reconstruction; a catalogue alone is not evidence.
The context ID, complete units, source spans, relationships, diagnostics and
insufficient status are preserved.
The separate [current-source reconstruction receipt](https://github.com/chris-page-gov/okf-explorer/blob/d47dd936a76d59b6d8070c46efb91a65f69caead/validation/context-compact/2026-09-22/dwp-semantic-candidate.json)
verifies all five current larger packages, containing 21/19/23/15/14 source units,
through responses no larger than 32,768 bytes. It binds the actual source hashes;
the recorded DWP checkout base is not misrepresented as containing uncommitted
candidate bytes. No unit is clipped to make it appear complete.

A separate [fixed-source Explorer comparison](https://github.com/chris-page-gov/okf-explorer/blob/2e557f4b78db10cf69471e4a106a98d3a6c43c5b/validation/context-compact/2026-09-22/measurement.json)
isolates the engine change from this source expansion. With the earlier frozen
logical source, lossless grouping of repeated diagnostics changed five small
inline evidence counts from 0/0/0/0/0 to 0/0/0/1/0. Bounded reads reconstructed
larger packages containing 18/16/19/15/14 complete source units. The measurement
makes redundant whole-package and section checks, so its read counts are not a
claim about minimum production round trips or remote latency.

**WebMCP** exposes browser functions to a compatible AI host. It does not make
every ChatGPT or Voice session able to call them. This increment does not change
the separately deployed remote Ask OKF service's default source or version.
Publication, remote-source admission, client access and specialist review retain
separate acceptance gates. No new AI-answer or affordability claim is made.

## How to inspect the increment

1. Open `logical-context/okf-explorer.json` in a compatible Explorer build.
2. Search for **077001** and inspect the complete cross-page source unit.
3. In **Ask OKF**, ask **What happens to Pension Credit if I go abroad?**, using
   **524288 package bytes**. Inspect the supersession route and qualifications.
4. Ask **Explain Universal Credit during temporary absence abroad.** Follow the
   source reference to Memo 09/25; inspect its conditions and complete example.
5. Use the exact supplied question **What is the interaction between Child DLA
   and PIP?** Inspect the transfer branch and its explicit unresolved scope.
6. Inspect JSON and insufficiency warnings. Where the browser host exposes
   WebMCP, obtain the same package's manifest and exact reads. Compare the context
   identity and reconstructed content; do not treat tool registration as a live
   external-client test.

The combined teaching programme retains its own unchanged snapshot and lesson
routes. New logical-unit versions do not silently rewrite the earlier source
pages, learning evidence or historical assessment decisions.

## Reproduce and extend safely

Authored additions are listed in
[`authoring-registry.json`](../domain-profile/logical-units/authoring-registry.json).
The loader admits only named, bounded local files. It verifies document identity,
rejects conflicting keys and overlapping source spans, and preserves existing
obligations. It records each proposal's actual authoring file. YAML-LD is YAML
used to express Linked Data; these files use its JSON-compatible subset.

```sh
uv sync --locked
uv run --locked python scripts/build_logical_units.py --check
uv run --locked python scripts/build_logical_context.py --check
uv run --locked python -m unittest discover -s scripts -p 'test_logical*.py'
node --experimental-strip-types scripts/evaluate_logical_context.mjs --check --explorer-root /path/to/approved/okf-explorer
uv run --locked python scripts/build_semantic_coverage.py --output evaluation/semantic-coverage/closure-2026-09-22 --check
```

The approved engine and module hashes are in
[`engine.json`](../evaluation/logical-units/engine.json). The earlier active run
is preserved byte for byte under
[`pre-closure-2026-09-22`](../evaluation/logical-units/history/pre-closure-2026-09-22/preservation.json).
To extend coverage, review the highest-priority uncovered cluster in the ledger,
add exact whole passages and scoped dependencies, rerun the same questions, then
compare retention and remaining obligations. Preserve every old observation.
The next priority is the [discovery-card experiment](discovery-cards-experiment.md):
compare validated headings and concept aliases, then source-linked summaries,
against literal-text ranking. This is proposed work, not a measured improvement.
Pension Credit core conditions, household, carer and ADM source gaps also remain
explicitly scheduled in the ledger.
