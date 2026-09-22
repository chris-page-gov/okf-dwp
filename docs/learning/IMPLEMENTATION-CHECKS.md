# Learning implementation checks

The curriculum branch builds on merged DWP main `bbe80471` (retrieval-unit PR 28).
The preserved pilot, full-DMG corpus and logical-unit source outputs have no diff
against that baseline. The dependent logical-context Reader and its current evaluation are regenerated for the learning descriptor dependency.

The generated combined snapshot is `dwp-combined-456f61cda2b8c20b858f`:
20,158 records, including 112 teaching activities, and 21,313 unchanged
relationships. No teaching reference is promoted to a legal relationship.

Validation performed on 22 September 2026:

- Combined producer byte-reproduction check passed.
- Frozen pilot remains byte-equivalent: 835 files.
- 21 existing combined Reader tests and 3 curriculum tests passed.
- Semantic/publication contracts and Explorer reconciliation passed.
- Eight Chrome learning journeys passed, including real DWP source routes,
  narrow-screen navigation, file switching, missing records and signed
  assessment persistence/tamper rejection.
- Explorer source type check and 660 unit tests passed, alongside build
  determinism and contract tests.

The portable rehearsal separately checks the built artefact and retains its
application and corpus hashes. These checks do not establish specialist
training acceptance, legal applicability, a complete claim form or a production
calculator.

The complete DWP Python test suite also passed: 581 tests. This includes the
retrieval-unit tests on the merged baseline and the new curriculum tests.

## Dependency correction

After the catalogue integration, the full DWP Python suite passes 582 tests.
The logical-context producer passes its byte-reproduction check, and the pinned
engine replays all 184 contexts and seven negative controls. All contexts remain
insufficient. Earlier evaluation bytes are retained in the pre-learning history.
The unit Reader excludes combined-only teaching metadata; this prevents dangling
lesson routes when its descriptor template changes.
