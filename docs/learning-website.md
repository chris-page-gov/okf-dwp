# Reading the learning path on the web

The project publishes its public Markdown documentation as a small static website.
**Static** means the server returns ready-made pages: no account, browser script
or AI service is needed to read them. The learning path is the home page, with
links to the glossary, Monday demonstration, remaining work and Ask OKF.

The intended public address is `https://chris-page-gov.github.io/okf-dwp/`.
The learning path also has the stable route `/okf-dwp/docs/learning-path.html`.
The release handover records whether these addresses have been verified live.

## Where the words come from

The Markdown files in this repository remain the authored source. The build
renders Git-tracked files in `docs/`, `evaluation/` and a small explicit set of
root documents. It excludes private correspondence, untracked research and the
large corpus bodies. A source link on each page opens that exact Git version.
Links between published guides stay on the website; evidence files open their
commit-bound repository location. The page footer links a manifest listing the
source and output hashes. A **hash** is a fingerprint used to detect changed bytes.

The renderer escapes source HTML and runs no page scripts. Mermaid diagram
blocks remain readable diagram source in this initial script-free documentation
view; the GitHub source view can render those diagrams. Browser keyboard and
narrow-screen checks are reported separately from publication success.

## Rebuild and publish

```sh
uv sync --locked
uv run --locked python -m unittest discover -s scripts -p test_learning_site.py
uv run --locked python scripts/build_learning_site.py --commit "$(git rev-parse HEAD)"
```

The output directory must be new: the build refuses to overwrite a candidate.
The locked Markdown renderer is the same renderer family used by OKF Explorer.
Do not edit generated HTML. Change the Markdown, build and test, then use a normal
reviewed pull request. After protected main passes the full bundle validation,
GitHub Actions builds its exact commit and uploads that single artefact to Pages.
The Pages job does not regenerate or change evidence bundles.

Publication of a guide does not establish complete answerability, specialist
acceptance or a source document's current legal applicability. Read the
[notice](../NOTICE.md) and [remaining work](backlog.md).
