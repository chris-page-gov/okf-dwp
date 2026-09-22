# Learning-page browser regressions

[Learning path](learning-path.md) · [Source review and compact delivery](semantic-closure-and-compact-delivery.md)

## What the public check found

The learning site published from `548557f2cd176d27cda8c2c916394436592ecc75` matched all 377 expected public requests. Its three retained evidence examples passed their separate browser checks. Those results did **not** mean that every learning-page interaction passed.

Two failures remained visible in the subsequent browser check:

- Focusing **Skip to content** added about 28.8 pixels to the page layout. Clicking **Glossary** then removed that focus between mouse-down and mouse-up, moving the link away from the pointer. The click landed on the header. The anchor's destination was correct; keyboard activation worked.
- The Markdown renderer added 16 inline alignment styles to the source-review report's table. The site's content security policy (CSP), which limits how a page loads or runs content, blocked those styles and reported console errors.

The failing observations remain retained. These are presentation defects; neither changes source evidence or establishes legal answerability.

## The bounded repair

The focused skip link stays positioned outside normal page layout, visibly over the header. Keyboard activation still moves to the main content, and switching from keyboard focus to a pointer click no longer moves the navigation.

The renderer converts only its supported left, centre and right table alignments into classes defined in the external stylesheet. Unexpected or combined style declarations stop the build. Raw source HTML remains inert and the existing restrictive CSP is unchanged. The parser and CSS spelling `center` is retained as an upstream technical identifier.

## Reproduce the checks

The regular isolated renderer tests are included in CI:

```sh
uv sync --locked --project tools/learning-site
uv run --locked --project tools/learning-site python -m unittest discover -s tools/learning-site -p test_learning_site.py
```

The separate browser regression accepts a freshly generated learning site, an already installed Playwright module and a fresh output directory:

```sh
uv run --locked --project tools/learning-site python scripts/build_learning_site.py \
  --commit "$(git rev-parse HEAD)" --output /tmp/okf-learning-regression-site
node tools/learning-site/check_browser_regressions.mjs \
  /tmp/okf-learning-regression-site /absolute/path/to/playwright/index.mjs \
  /tmp/okf-learning-regression-observation
```

Use new output directories for each run. The harness uses installed Chrome and fulfils every browser request locally from four rendered files; it neither fetches source material nor verifies a live deployment. Its receipt binds the input and executed harness hashes and retains failures.

At both desktop and mobile widths it checks the mixed keyboard-to-pointer sequence, keyboard skip activation, keyboard navigation, actual table alignment, no horizontal overflow and an unchanged CSP. Console errors or warnings fail the check. This is a focused regression, not exhaustive accessibility acceptance.

Local verification recorded 26 passing renderer tests and eight passing browser checks. The original rendered site failed the layout check; a separate negative control with the fixed stylesheet and original table HTML failed on 16 inline styles and CSP errors. Public acceptance still requires a fresh exact-commit Pages publication and browser observation after integration.
