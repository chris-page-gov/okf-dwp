# Review how a passage was built

A **passage** is a piece of guidance that belongs together. A PDF page is a
place to find it. A passage may cross a page boundary, and a single page can
contain several different things: a rule, an example, a contents list and a
note about an amendment. Mixing those things can make an evidence search less
useful even when every source byte has been captured.

The passage-boundary workbench lets a reviewer examine those decisions. It is
an independent experimental tool, not an official Department for Work and
Pensions (DWP) service or a benefits decision.

## Start with the 28 known cases

The review queue contains 28 previously identified large passages in historical
amendments to the **Decision makers' guide (DMG)**. These were selected because
their structure looked suspicious. They are not a random sample and cannot tell
us the error rate of the whole corpus. **Advice for decision making (ADM)** is
the other DWP manual in the wider corpus; its chapters are included in the
separate parser impact checks.

[Open the 28-case passage review](https://chris-page-gov.github.io/okf-explorer/evidence/passages/?manifest=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F65924955745c4ed1b8ce66252c4748902b5403ba%2Fevaluation%2Fpassage-boundary-review%2Fmanifest.json&case=case-001). This link pins the DWP review
data to `65924955` and opens Explorer's **Evidence workbench → Passage boundaries** view. The generic route
requires the companion Explorer implementation to be published. The
[review manifest](../evaluation/passage-boundary-review/manifest.json) is also
available for local inspection.
The manifest is the small catalogue of cases and their fingerprints. The viewer
loads a case and its extraction only when selected. The original
[findings](../evaluation/manual-structure/large-paragraph-review-2026-09-23/findings.json)
and frozen source observations remain available.

1. Choose a case. Read its finding and uncertainty before deciding whether to
   change the passage.
2. Select a source page. The original PDF and exact extracted text use the same
   page locator. Compare the before and proposed after passages, including
   examples, qualifications, references and unfinished fragments.
3. Open **How this passage was built**. A parser is the program that recognises
   document structure. Its version, rules, recorded settings, settings fingerprint and source
   evidence explain the proposal. A hash (SHA-256) is a fingerprint of exact
   bytes; matching hashes do not establish that the interpretation is correct.
4. Use **Isolated correction preview** to inspect a proposed split, join or
   structural-role change. The JSON editor accepts structured data, not commands.
   A successful preview checks identities and source-byte accounting; it does
   not establish a correct legal interpretation.
5. Read the impact and missing information. A change can affect the passage,
   other units in its document, identifiers and dependencies, and evidence
   selected for questions. Unknown downstream effects remain unknown.
6. Enter a reviewer, date and reason, then download the review JSON. This file
   records a reproducible suggestion for a separate reviewed producer change.
   It does not modify published evidence.

## What to look for

- **False split:** a sentence, example or qualification is cut in two.
- **False join:** unrelated material, such as an amendment letter and a rule,
  appears as one passage.
- **Structural role:** a heading, contents entry or administrative note is
  mistaken for substantive guidance.
- **Reference:** a paragraph number or cited appendix loses its destination.
- **Incomplete fragment:** the preserved source really ends mid-sentence.
  Keep that uncertainty visible; do not invent a continuation from another
  edition.
- **Identifier migration:** when an old passage becomes several new ones,
  record each proposed connection. Shared source bytes do not prove that two
  passages mean the same thing.

The initial review queue preserves the parked parser's proposal. Its status is
**pending independent review**. It remains an auditable comparison even when a
later, narrower parser change rejects part of that proposal. Read the recorded
parser and source identities before comparing results from different runs.

## What the parser review found

The earlier broad proposal treated a standalone word **Appendix** as a new
section everywhere. In DMG Chapter 5, PDF page 152, that word is the wrapped end
of a sentence. Splitting there would damage the passage. The
[nine-chapter source review](../evaluation/passage-boundary-candidate/substantive-scope-review.json)
therefore rejected that broad rule for substantive chapters.

The successor confines the new navigation and bare-Appendix rules to historical
amendment documents. Its
[full census](../evaluation/passage-boundary-candidate/versioned-census-02/report.json)
accounts for all **513 documents**, **35,143,443 extracted source bytes** and
**75 authored units**. It produces **54,577 units**, compared with the frozen
baseline's **53,727**. It changes 125 historical amendment documents and leaves
every substantive chapter's records unchanged. The parked proposal's 54,581
units are a different, preserved experiment.

The 28 case records distinguish the **target boundary** from remaining
structure and legal completeness: 15 target boundaries are corrected, 12 are
partly corrected, and case 014 remains unresolved. For example, the successor
also separates case 019's overlap reference table from paragraph 070594.
Case 014's extracted text does not support a confident new boundary. Abbreviation
continuations, unlabelled fragments and some trailing number markers remain
explicit residuals. These figures are an engineering assessment of selected
known defects, not specialist acceptance or an estimate of corpus accuracy.

The parser first passed four source cases, then eight. Separate controls cover
an unseen amendment replacement sheet and two genuine cross-page passages:
DMG 01013's example and ADM A2022's conditions and examples. Independent PDF
inspection confirmed both continuations. Source-byte preservation alone would
not have established that those passages stayed together.

## What changed in the 40-question replay

The [retained comparison](../evaluation/passage-boundary-candidate/question-replay.json)
uses the same 40 questions, source scope, assembler and delivery code. Both arms
have a 512 KiB package budget, 64 records, 128 relationships and traversal depth
six. It uses no answer-model calls. The exact candidate packages and their
hashes are retained, so verification does not depend on temporary local files.

| Observation | Result |
| --- | --- |
| Questions whose selected evidence identifiers changed | 21 of 40 |
| Questions whose evidence order changed | 22 of 40 |
| Questions whose selected traversal paths changed | 4 of 40 |
| Text or source-span changes for an identifier retained in both arms | None |
| Changes in matched declared candidate pages | None |
| Changes to evidence requirements | None |
| Packages whose byte size changed | 34 of 40; 2,709 bytes larger in total |
| Complete answers established | None; all 40 remain `insufficient` |

The new structural units affect selection and omission reports, but this replay
**does not demonstrate improved retrieval of the declared expected pages**.
Page overlap is a limited coverage measure, not a claim-level answer score.
The report preserves gains, losses, order and traversal changes, and both kinds
of omission: candidates outside retrieval limits and records outside assembly
limits. The earlier 54,576-unit replay remains separately archived.

## Separate the three decisions

| Decision | What would support it? |
| --- | --- |
| Is the structure sound? | Exact source comparison, qualifications retained, suitable roles, valid references and no lost or duplicated source bytes. |
| Does retrieval improve? | The same questions, expected evidence and budgets tested against baseline and candidate, with gains and losses recorded. |
| Can we give a complete legal answer? | Applicable, complete and current evidence, reconciled legal versions and the required specialist review. |

Passing the first test does not pass the other two. All 40 staff-question
occurrences must remain in the replay, including insufficient results. No
answer-model comparison or optional automated defect detector is needed to
inspect the cases.

## Reproduce the review data

From the DWP repository, using its locked environment:

```sh
uv sync --locked
uv run --locked python scripts/build_passage_boundary_review.py
uv run --locked python scripts/build_passage_boundary_review.py --check
uv run --locked python -m unittest discover -s scripts -p 'test_passage_boundary_review.py'
uv run --locked python -m unittest discover -s scripts -p 'test_passage_boundary*.py'
uv run --locked python scripts/build_passage_boundary_units.py --profile passage-boundary-v1
uv run --locked python scripts/build_passage_boundary_units.py --profile passage-boundary-v1 --check
uv run --locked python scripts/compare_passage_boundary_replay.py --candidate-root evaluation/passage-boundary-candidate/replay-projection --check
```

The producer checks the original PDF, extracted text, baseline passages and
proposed spans before generating the review projection. It does not rewrite
frozen sources or earlier evidence packages.

The successor parser is explicitly selected by `passage-boundary-v1`. Its
output lives under `evaluation/passage-boundary-candidate/structured-units/`.
The original `scripts/build_structured_units.py --check` still checks the frozen
baseline. This makes the before/after comparison repeatable.

The [versioned replay protocol](../domain-profile/passage-boundary-review/replay-protocol.json)
explains how to regenerate the candidate in a disposable checkout. It substitutes
only the explicitly identified parser and navigation module, checks their hashes
and the resulting structural catalogue, and retains the exact 40 packages.
Normal surplus-output guards stay enabled. The scratch rerun initially found
an unrelated `.DS_Store` and older generated projection files; those were moved
aside only in the disposable copy before the unchanged producer passed.

The offline comparison above validates the retained receipt, exact packages,
questions, source and implementation identities. It does not rerun an AI or
change the normal published evidence selection.

See the [40-question workbench guide](evidence-workbench.md),
[authored delivery register](../evaluation/backlog.json) and
[generated work-package status](backlog-work-packages.md).
