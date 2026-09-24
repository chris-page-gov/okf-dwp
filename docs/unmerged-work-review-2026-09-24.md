# Unmerged work review — 24 September 2026

## Decision

The review found no implementation branch ready for an additional merge.
Most apparently unmerged work is already on `main` through squash merges.
A squash merge records several feature commits as one new commit, so Git's
ancestry list alone can make delivered work look unfinished.

This review compared the 43 existing local branches, remote branches, 25
worktrees and GitHub pull requests with fetched `main` at
`d31f16fb7143d04b9de73e14cd493cfb832ae83e`. It inspected tracked changes and
untracked files without changing the owner's checkout. A separate new branch
records the findings and the [tested sidebar demonstration](workbench-sidebar-demo.md).
No source capture, model-answer comparison or corpus rebuild was run.

## Already incorporated

The feature-tip trees exactly match their recorded merged trees for PRs
[5](https://github.com/chris-page-gov/okf-dwp/pull/5),
[6](https://github.com/chris-page-gov/okf-dwp/pull/6),
[4](https://github.com/chris-page-gov/okf-dwp/pull/4),
[14](https://github.com/chris-page-gov/okf-dwp/pull/14),
[16](https://github.com/chris-page-gov/okf-dwp/pull/16),
[36](https://github.com/chris-page-gov/okf-dwp/pull/36),
[37](https://github.com/chris-page-gov/okf-dwp/pull/37) and
[39](https://github.com/chris-page-gov/okf-dwp/pull/39).
These include the full DMG, imprisonment acceptance, semantic pilot, learning
site, earlier model checks, evidence connection and latest workbench models.

Other single-commit branches have equivalent patches on `main`, including the
remote-client, public-demo, staff-handover and household-evidence changes.
The local learning focus/CSP fix `bd762822` has the same stable patch identity
as merged commit `a27f3a70`. No duplicate PR is needed. Remaining older feature
tips are ancestors of `main`. No branch or worktree was deleted.

## Work which must remain separate

| Work | Finding | Next action |
| --- | --- | --- |
| Historical amendment parser, `codex/amendment-structure`, `6ae66224` | Unique implementation plus untracked experiment outputs. The retained census changes 134 documents: 125 historical amendments and nine substantive chapters. Unit count changes from 53,727 to 54,581; 283 identifiers disappear and 1,137 appear. | Continue `DWP-BL-007.remaining-structural-review`; do not merge the parser directly. |
| [PR 23: Monday handover](https://github.com/chris-page-gov/okf-dwp/pull/23), `54eb15f7` | Open and conflicting at the initial review; closed as superseded during the owner's requested tidy-up on 24 September. Its pending-publication statements belong to the 21 September checkpoint. | Preserve the PR history and branch. Use the later handovers and current status rather than merging stale current-status wording. |
| Earlier direct-trial working files | The disability worktree contains duplicates and older versions of the runner, tests, protocol and documentation. Current tracked versions add freeze and verification controls. | Preserve locally; do not copy them over current files or launch new trials. |

The amendment experiment's retained four-case and eight-case reports pass, and
its census accounts for the source bytes and 75 authored units. These are
retained reports, not tests rerun by this review. All 28 outlier probes still
require independent boundary review, and the census performed zero context
assemblies. Bare `APPENDIX` recognition also changes substantive chapters.
Its candidate manifest differs from the frozen structured-unit manifest;
the current build check would require regenerated, reviewed successor outputs.

Before adoption, review those source boundaries, port the change onto current
`main`, run the manual-navigation and PDF-structure controls, repeat the fixed
four-to-eight case sequence, and verify the complete corpus census. Then
reconcile changed identifiers and authored selections and rerun the staff and
original acceptance cases. Preserve the earlier source, units and failed
results. This is already an open package in the
[backlog](backlog-work-packages.md#dwp-bl-007-broader-semantic-modelling-task-specific-evidence-profiles).

## Local files excluded from this PR

- `.email.md` remains ignored and absent from Git. Its contents were not read
  for this review.
- The 40 lines in `research/Architecture AI Demo Questions.md` each exactly
  match a question in the tracked [staff register](../evaluation/staff-questions/cases.json).
  A second public question source would add duplication.
- `research/calculation.md` and
  `research/overview-of-how-guarantee-credit-is-calculated.md` are byte-identical
  design prompts, not a captured calculation guide or implemented calculator.
  Preserve the originals locally; any future specification needs explicit
  status and source reconciliation before adoption.
- The local CPAG contents export is navigation metadata. Its own README labels
  it a local research export and does not establish redistribution rights.
  Keep it separate pending the recorded [access and reuse review](cpag-handbook.md).
- Browser scratch directories and the raw Chrome crash report are local
  diagnostic material. They are not curated release evidence and have not had
  a complete privacy review. Do not stage them wholesale.

## How to repeat the review

Fetch the current remote state, then inspect `git status --short`,
`git worktree list --porcelain`, `git branch -vv` and open PRs. Compare each
apparently unmerged feature tip with its recorded merge commit: identical Git
trees or stable patch identities can establish that a squash or cherry-pick
already incorporated it. Review actual remaining changes against current
`main`, not just the branch name or commit count. Inspect dirty worktrees
without resetting or cleaning them. Run `scripts/check_private_inputs.py`
through the locked environment before publishing any candidate.

The scope of this audit is the available branches and worktrees at the recorded
revision; it does not claim recovery of deleted branches or unreachable objects.
