# Examine the 40 questions in the Evidence workbench

This workbench makes the evidence behind a question visible. It is an
independent research tool, not an official Department for Work and Pensions
(DWP) service or an entitlement decision.

The **Decision makers' guide (DMG)** and **Advice for decision making (ADM)** are
staff guidance manuals. Their numbered paragraphs identify guidance; PDF page
numbers identify where text was printed. Neither manual is itself legislation.

## Start with one question

[Open the Evidence workbench](https://chris-page-gov.github.io/okf-explorer/evidence/?manifest=https%3A%2F%2Fchris-page-gov.github.io%2Fokf-dwp%2Fevaluation%2Fevidence-workbench%2Fmanifest.json&case=staff-001).
This link uses the current published review catalogue; each downloaded package
is checked against that catalogue's recorded fingerprint.

1. Choose one of the 40 public staff-question occurrences. One question is
   repeated in the register, so there are 39 distinct wordings.
2. Check the evidence status. **Insufficient** means the package cannot establish
   that all evidence needed for the task is present. It does not mean every
   selected paragraph is irrelevant.
3. Open a selected passage and its cited PDF page. GOV.UK blocks embedded PDF
   display, so use the page-linked original-document button to open a separate
   browser tab. Compare the extracted text
   with the original, including qualifications and examples.
4. Inspect the interpretation tabs: passage boundaries, concepts and
   relationships, dependencies, and the explanation of why the text was selected.
5. Read the missing requirements and budget omissions. Export a review proposal
   if something should change; it stays local until separately reviewed.

## What the terms mean

| Term | Meaning in this workbench |
| --- | --- |
| Source | The preserved official document and its exact downloaded version. |
| Extraction | Machine-readable text taken from the document; it can contain extraction errors. |
| Logical unit | A passage grouped because its text belongs together, possibly across PDF pages. |
| Discovery card | A short project-authored description and alternative wording used to find a passage. It is not evidence. |
| Concept | A named idea, such as capital or payment, with a stable identifier. |
| Relationship | A labelled connection between records. Its provenance and review status matter. |
| Dependency | Other text needed to interpret a passage, such as an exception, definition or cross-reference. |
| Provenance | Where an item came from and how it was transformed. |
| Evidence package | The selected text, relationships, explanations, source references and explicit gaps for one question. |
| Checksum | A fingerprint used to detect whether the delivered bytes differ from the declared version. |

## Why the capital question failed

The question about treating capital as still held after someone disposed of it
had relevant text in the corpus. The complete passage was labelled using terms
such as *notional capital*. The question used ordinary wording instead. Its
passage ranked below the 16 lexical candidates admitted by the earlier engine,
and the available conceptual route did not activate. A larger final byte budget
would not fix that selection failure.

The additive repair connects ten already repaired capital passages to the full
DMG/ADM corpus, improves source-bound discovery, and follows the best passage's
dependencies before broad graph expansion. It preserves the original PDFs,
extractions, earlier releases and failed trial results. Everyday-wording routes
are project-authored navigation proposals, not a change to the meaning or legal
status of the guidance. Test results distinguish familiar development questions
from new phrasings; finding the original question alone is not proof of general
retrieval quality.

## Small downloads, complete retained text

A package can be up to 512 KiB. It is delivered in separately checked responses
of at most 32 KiB and reconstructed exactly. This avoids treating a small
response limit as a reason to discard qualifications. It does not recover text
which was never selected: selection gaps remain visible in the package.

Only the chosen question's evidence is downloaded. The catalogue lists all 40;
private correspondence and unpublished questions are outside it. Source dates
are not replaced by the date this catalogue was generated.

## What review can and cannot establish

Source-byte integrity, useful selection, complete legal evidence and a good AI
answer are different tests. All 40 cases can be examined without asserting that
all 40 can be answered. Unresolved applicability, uncaptured legal provisions,
ambiguous references and specialist acceptance stay open. No new answer-model
trial is part of this repair.

See the [implementation work log](evidence-workbench-work-log.md), the
[backlog work packages](backlog-work-packages.md), and the preserved
[capital source repair](pc-capital-bounded-repair.md).

## Demonstration sequence

Choose a staff question, open its source, show the complete passage and its
page spans, then show a dependency and the reason it was selected. Finish with a
missing requirement and the machine-readable package. This demonstrates an
inspectable grounding process, without turning an incomplete package into a
complete benefits answer.

## Ask a new question against the repair

[Open the updated DMG and ADM source in Explorer](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F7eeded763042ddd0070f4fed834c6074149e8e2f%2Fstructured-context%2Fevidence-connect-explorer.json),
then select Ask OKF. This link fixes the source version to the reviewed release.
Earlier pinned bundle links keep their original data; they do not silently
acquire this repair. The 40-question workbench opens retained results, whereas
Ask OKF assembles a new package for the words you enter.

## Reproduce the retained evidence

The producer and the Explorer consumer must use the versions recorded in the
workbench manifest. With a checkout containing the integrated delivery helper:

```sh
uv sync --locked
uv run --locked python scripts/build_evidence_connect.py --check
node scripts/test_evidence_connect_descriptor.mjs --explorer-root /path/to/okf-explorer
node scripts/build_evidence_workbench.mjs --explorer-root /path/to/okf-explorer --check
node scripts/check_evidence_workbench.mjs --explorer-root /path/to/okf-explorer
```

After dependency setup, these commands check the corpus projection, exercise
Explorer's actual Reader-to-Ask loader, repeat the 40 assemblies and compare
every byte, then independently reconstruct all retained packages without
rerunning retrieval. The loader check also needs Explorer's locked JavaScript
dependencies installed with `pnpm install --frozen-lockfile`. None calls an answer model.
See the [source connection profile and measured tests](evidence-connect-profile.md).

The retained offline replay uses a virtual `example.invalid` index address.
That address is an identity within the replay, not a public download link; the
manifest's corpus path and checksum bind the committed source. Use the updated
Explorer link above for a new live assembly, or the documented producer commands
for byte-for-byte replay.

The new live Ask OKF entry uses `structured-context/evidence-connect-explorer.json`
from an immutable GitHub revision. In Ask OKF, the retained-case comparison
uses limits of 64 records, 128 relationships, depth 6 and 524,288 bytes; a
32 KiB delivery part is a different limit. The workbench consumes only its retained
public question packages. Remote MCP service admission and an observed ChatGPT
client journey are separate from this browser release.
