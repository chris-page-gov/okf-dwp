# Demonstration learning programme

This implementation adds 12 paths and 112 learning activities to the combined
Reader. The largest path has 20 steps. It covers the 40 supplied question
occurrences (39 unique questions), using the eight projected personas already
present in the corpus. These are independent teaching proposals, not validated
DWP training, benefits advice or a competency qualification.

The authoritative curriculum is [programme.yamlld](../../domain-profile/learning/programme.yamlld).
The combined builder generates real `learning/pNN/sNN` records, bounded search
and locator entries, semantic identities and the Reader's v2 teaching overlay.
Teaching references link existing evidence without creating legal assertions.
The preserved pilot, full-DMG release and logical-unit corpus are not rebuilt.

This branch builds on DWP `311f7ff9`, including the parallel logical-evidence-unit
work. Source-page anchors remain valid. The curriculum explicitly distinguishes
page locations from complete logical units, governing headings, cross-page
continuations, attached examples, qualifications and unresolved references.
No old whole-page evidence requirement is silently satisfied by a fragment.
The logical-unit Reader remains a separate corpus, linked from the repository's
[logical-unit guide](../logical-evidence-units.md).

[Path design](DESIGN.md), [lesson specifications](LESSONS.md) and
[question coverage](question-coverage.json) retain the original design baseline.
They are historical design artefacts; the authored YAML-LD and generated Reader
are the current implementation. The earlier design's statements about absent
lesson records and absent assessment software describe that earlier baseline.

## Demonstrate in ten minutes

1. Open the generated combined descriptor in the matching Explorer build.
2. Expand **Read evidence before trusting an answer**. Open **Baseline and role**,
   then inspect its supporting persona record. Use Back to return to the lesson.
3. Open **Distinguish the layers**. Explain why a source page, a complete logical
   unit and an interpretation have different roles. The logical-unit guide
   supplies the separate exact-span demonstration; do not claim all combined
   records have been replaced by logical units.
4. Use the household path and its changed-scenario exercise to show how a
   plausible answer can omit a controlling qualification.
5. Open **Evidence and assessment**. Show that an artefact can be submitted for
   the foundation path but dependent assessment requires an assessed pass.
6. Export a fictional foundation submission. A facilitator reviews it, applies
   the rubric and returns a signed decision using Explorer's `learning_assessor.mjs`.
   Import that decision; demonstrate that the dependent assessment unlocks.
7. Reload: the verified decision persists. Explain that a new programme version
   or bundle snapshot needs a new review. Export the journal as a backup.
8. Finish with the fair-comparison path. Show measured results only where a
   retained experiment exists. The form and calculator paths teach design and
   assurance; they are not a delivered CASA claim service or an award calculator.

For a short meeting, use this excerpt. Do not imply that attending it completes
112 activities or awards a pass for omitted assessments.

## Assessment and operator setup

The authored roster contains the local demonstration facilitator's public key.
Its private key stays outside the repository; it is not included in a shared
bundle. Recipients can browse and prepare submissions without it. To run their
own assessments, they generate their own key, replace the authored public roster
and rebuild, producing a new snapshot. A signature establishes configured key
ownership, not specialist competence. Legal interpretation requires a qualified
reviewer; no automatic grading or official credential is claimed.

The rubric has five scores (0–2): traceability, scope, reasoning, counterexample
and communication. Pass requires 8/10, full marks for traceability, scope and
counterexample, and no critical failure. Browser journals retain attempts and
verified decisions. They are local teaching aids, not a managed training record
system. Use fictional examples and export a backup before clearing browser data.

## Reproduce

```sh
uv sync --locked
uv run --locked python scripts/build_combined_reader.py
uv run --locked python scripts/build_combined_reader.py --check
uv run --locked python -m unittest discover -s scripts -p test_learning_paths.py
```

The generator rejects unknown source/persona routes, incomplete question
coverage, changed question-registry bytes, duplicate lesson identities,
prerequisite cycles and text exceeding Reader limits. Assessor decisions bind
the learner, exact artefact, programme version and generated bundle snapshot.
