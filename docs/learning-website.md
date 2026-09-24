# Reading the learning path on the web

The project publishes its public Markdown documentation as a small static website.
**Static** means the server returns ready-made pages: no account, browser script
or AI service is needed to read them. The learning path is the home page, with
links to the glossary, Monday demonstration, remaining work and Ask OKF.

Open the [learning website](https://chris-page-gov.github.io/okf-dwp/) or its
[direct learning-path address](https://chris-page-gov.github.io/okf-dwp/docs/learning-path.html).
The first public release was verified on 20 September 2026 against source commit
`3f72ebc30128c2a3171951050a566d3ed8db7c16`: the manifest and all 108 output files
returned HTTP 200 and matched their expected byte counts and hashes.
The [retained observation](../validation/learning-site/public-3f72ebc30128c2a3171951050a566d3ed8db7c16/README.md)
is a dated publication check, not a guarantee about future availability or later
versions. A separate browser check opened the learning path and glossary without
console errors or page-level horizontal overflow.

## Where the words come from

The Markdown files in this repository remain the authored source. The build
renders Git-tracked files in `docs/`, `evaluation/` and a small explicit set of
root documents. It excludes private correspondence, untracked research and the
large corpus bodies. The separately admitted Evidence workbench catalogue
also publishes 40 selected evidence packages and their checked delivery parts.
It does not copy arbitrary evaluation folders. A source link on each page opens that exact Git version.
Links between published guides stay on the website; evidence files open their
commit-bound repository location. The page footer links a manifest listing the
source and output hashes. A **hash** is a fingerprint used to detect changed bytes.

The renderer escapes source HTML and runs no page scripts. The learning path's
source-roles Mermaid diagram has a checked static SVG for this website, with its
full explanation and links in the table below it. GitHub can render the authored
Mermaid diagram. Other Mermaid blocks remain readable diagram source on the
website. Browser keyboard and narrow-screen checks are reported separately
from publication success.

## Rebuild and publish

```sh
uv sync --locked --project tools/learning-site
uv run --locked --project tools/learning-site python -m unittest discover -s tools/learning-site -p test_learning_site.py
uv run --locked python scripts/source_roles_diagram.py --check
uv run --locked --project tools/learning-site python scripts/build_learning_site.py --commit "$(git rev-parse HEAD)"
```

The output directory must be new: the build refuses to overwrite a candidate.
The renderer has its own locked environment under `tools/learning-site/`; this
keeps the frozen evidence producers’ dependency identity unchanged. It is the
same Markdown renderer family used by OKF Explorer.
Do not edit generated HTML. Change the Markdown, build and test, then use a normal
reviewed pull request. After protected main passes the full bundle validation,
GitHub Actions builds its exact commit and uploads that single artefact to Pages.
The Pages job does not regenerate or change evidence bundles.

Verify the retained first-publication receipt without contacting the website:

```sh
uv run --locked python scripts/check_learning_site_observation.py
```

Publication of a guide does not establish complete answerability, specialist
acceptance or a source document's current legal applicability. Read the
[notice](../NOTICE.md) and [remaining work](backlog.md).

## Verify a workbench publication

The current exporter uses a version 3 manifest when the 40-question workbench
is present. It admits only the declared public packages and parts, within a
64 MiB total website limit. The older version 2 verifier remains available for
its historical publications.

```sh
node --test scripts/test_learning_site_v3.mjs
node scripts/verify_learning_site_v3.mjs --repo REPOSITORY --site BUILT_SITE --commit FULL_COMMIT --output FRESH_OBSERVATION_DIRECTORY
```

The version 3 check compares the live files with an exact local build and its
immutable Git inputs. It reads at most four public resources concurrently,
bounds downloads and records failures without silently retrying. This checks
publication identity; the separately pinned all-question reconstruction test
checks the delivery contract, and browser journeys check actual use. None
establishes a correct benefits answer.
