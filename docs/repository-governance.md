# Repository governance

This independent experimental publication uses feature branches and reviewed pull
requests, as required by [the working agreements](../AGENTS.md). It is not an
official DWP publication and these controls do not confer official authority or
specialist approval on its contents.

## Protected main branch

On 19 September 2026, the GitHub API showed that `main` had no branch protection
and no applicable rulesets. Validation already ran, but GitHub did not require a
successful result before changes reached `main`.

The owner then enabled classic branch protection. An independent API read at
16:11:08 UTC confirmed these settings:

| Control | Configured value |
| --- | --- |
| Pull request before merging | Required |
| Required check | `validate`, from GitHub Actions (app ID `15368`) |
| Branch up to date before merging | Required (`strict: true`) |
| Administrator enforcement | Enabled |
| Review conversations resolved | Required |
| Stale approvals dismissed after new commits | Enabled |
| Formal approving-review count | `0` |
| Code-owner review / approval of latest push | Not required |
| Force pushes / branch deletion | Disallowed |
| Linear history / signed commits | Not required |
| Repository rulesets | None; classic protection supplies these controls |

The zero formal approval count permits the owner to merge a reviewed pull request
without a second GitHub account's approval. It does not establish that independent
review occurred: record review findings and validation evidence in the pull
request. The required check name is the job name `validate`, not the workflow
title “Validate experimental OKF bundle”.

The [machine-readable observation](../validation/repository-governance.json)
records the before and after state. It is a dated configuration receipt, not
continuous monitoring or proof that future changes will pass validation. Review
the [GitHub settings](https://github.com/chris-page-gov/okf-dwp/settings/branches)
and check results when changing governance. GitHub describes these controls in
its [protected branches documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).

## Private correspondence

Files named `.email.md` are local private inputs and must not be committed at any
directory depth. The root ignore rule protects this basename. Before committing,
run:

```sh
uv run --locked python scripts/check_private_inputs.py
uv run --locked python scripts/test_private_inputs.py
```

The checker examines Git index path names, the public root ignore rule and Git's
ignore decisions for the root, a nested probe and existing tracked directories.
It rejects tracked or staged `.email.md` files, including force-added files, and
ignore rules overridden in those directories. It never opens correspondence or
scans private research. Tests use temporary repositories and synthetic text only.

This is a filename-specific guard, not a content scanner or a review of Git
history. Other private files still require deliberate exclusion. A failed CI
check cannot undo a disclosure already pushed to a public branch: run the local
check before committing and inspect the staged paths before pushing.
