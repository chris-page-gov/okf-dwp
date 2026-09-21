# Publishing retained evidence examples

A retained example is a recorded evidence package that someone can reopen and check. It is not a new answer, a live search, an official decision or a finding that the evidence is sufficient. The example keeps the package's original gaps, source dates, authority labels and review status.

The learning-site publisher can now include a small, explicitly approved set of these examples. This change supplies the publication mechanism. It does not itself approve examples, acquire evidence, call a model, contact the public service or publish a website.

## What a reader gets

The generic OKF Explorer archive exporter produces a small index and a browser reader. The reader requests selected evidence and metadata from files in the same archive. A SHA-256 hash is a fingerprint of the exact file bytes: it detects changes, but does not establish that a statement is correct.

Each example retains its original complete package alongside smaller files for its catalogue, records, provenance, directed relationships and diagnostics. Diagnostics explain unresolved concepts, missing evidence and limits. There is no AI answer in this archive format. Source material remains untrusted text, with the source's rights and qualification boundaries intact.

Only a declared archive is copied to the website. Other JSON files, acquisition folders, private correspondence and untracked research remain outside this publication route. A link to an ordinary repository evidence file still opens its exact GitHub version.

## Two separate declarations

The generic exporter uses `okf-context-archive-registry.v1`. Its registry lists the approved cases, exact original package and receipt bindings, question hash, source version, engine identities, observation kind and publication note. Keep it under `evaluation/`, with original packages and receipts under `evaluation/` or `validation/`.

The DWP publisher additionally requires `evidence-examples/registry.json`, using `okf-dwp-retained-evidence-publication.v1`. It contains a `releases` array. Every release has exactly these fields:

| Field | Meaning |
| --- | --- |
| `id` | A unique lowercase release name, using letters, numbers and hyphens; at most 64 characters. |
| `archive_root` | Exactly `evidence-examples/<id>`. |
| `registry` | The generic export registry's repository-relative `path`, positive `bytes` and SHA-256 `sha256`. |
| `artifact_manifest` | The same binding for `<archive_root>/artifact-manifest.json`. |
| `exporter` | The fixed Explorer repository URL, full 40-character `commit`, and approved `files` list of module/schema path, size and hash bindings. |
| `approved_publication` | Must be `true`; this is an explicit project publication declaration. |
| `publication_note` | A short explanation of what was recorded and its limits. |

The exporter repository is `https://github.com/chris-page-gov/okf-explorer`. Its file list must match the complete `exporter_files` list in the archive manifest. Review and bind the actual exporter revision before authorising a release.

**The publisher does not independently fetch or attest that remote Explorer commit.** It checks the module hash list against the DWP Git-approved declaration. The exact DWP Git blobs of the declaration, original inputs and all copied archive files are independently checked against the requested publication commit. These are different checks, and the site manifest records the distinction.

The wrapper is not a place to publish arbitrary questions or automatically retain submissions. Only reviewed, named examples enter this route. Do not put personal claimant information, private correspondence or subscription-only source text into an approval registry.

## Bounds and file layout

This DWP route permits at most three examples in total, across at most three releases. This is deliberately smaller than the generic exporter's 20-case limit.

An archive contains only:

- `index.html`, `index.json`, `reader.mjs`, `shared.mjs` and `reader.css`;
- `artifact-manifest.json`;
- `<package-sha256>/descriptor.json` and `<package-sha256>/package.json`;
- `<package-sha256>/data/<content-sha256>.json`.

A case is limited to 1,024 files and 8 MiB. The original uncompressed package is at most 512 KiB. Descriptors and read slices are at most 64 KiB; catalogue and record-index pages are at most 16 KiB. The DWP archive inventory is at most 1 MiB. The existing 32 MiB combined site-payload limit also applies. Large or malformed declarations fail before a site is written.

The publisher rejects missing, duplicate, unexpected and unreferenced archive files; changed committed bytes; unsafe paths; symbolic links in roots, parents or files; non-regular files; oversized input files; duplicate JSON keys; and non-finite JSON numbers. It bounds compressed input and decompression separately. It never executes an archive's JavaScript during admission.

It also checks the package's node, relationship, byte and traversal-depth limits against its recorded usage and selected paths. It then checks the content, beyond individual file hashes:

- the index and descriptor match the approved case and original package;
- the HTML binds the exact root index;
- every evidence stream has contiguous UTF-16 offsets and a matching whole-value hash;
- reconstructed complete package bytes equal the original package;
- record text and metadata, including provenance, equal the original selected records;
- catalogue source links and authority labels equal the original record metadata;
- relationships and diagnostics equal their original package values;
- all referenced archive members exist, with no unexplained extra members.

A complete delivery can still contain insufficient evidence. No check upgrades authority, specialist review or legal applicability.

## Preparing and checking a release

Use an independently reviewed, immutable Explorer exporter checkout. Replace the uppercase placeholders with the exact approved paths and release name:

```sh
node --experimental-strip-types OKF_EXPLORER_CHECKOUT/tools/context-archive/export.ts --registry EXPORT_REGISTRY --input-root . --output evidence-examples/RELEASE_ID
```

The exporter requires a fresh output directory. Prepare the DWP approval wrapper from the actual export inventory; do not invent successful receipts or substitute a different source package. Review the complete change through the repository's protected publication process.

After the declaration and retained files are committed, verify them without writing a site:

```sh
uv run --locked --project tools/learning-site python scripts/build_learning_site.py --commit COMMIT_SHA --check-examples
```

Build into a fresh directory using the same immutable commit:

```sh
uv run --locked --project tools/learning-site python scripts/build_learning_site.py --commit COMMIT_SHA --output _site
```

Run the portable offline controls:

```sh
uv run --locked --project tools/learning-site python -m unittest discover -s tools/learning-site -p test_learning_site.py
```

No new dependency is required. The locked learning-site environment remains unchanged.

## Publication identity and compatibility

Without a committed approval registry, the existing Markdown-only site keeps the `okf-dwp-learning-site.v1` manifest and existing output behaviour. An untracked registry is not admitted. Ordinary Markdown rendering and its inert-HTML protections remain unchanged.

With approved examples, the publisher writes `okf-dwp-learning-site.v2`. Its existing `source_pages` and `page_count` still describe Markdown pages. The new `retained_evidence` field lists the approval, releases and every admitted input hash. The existing `files` list covers the exact copied archive assets as well as rendered documentation. HTML, JavaScript, CSS and JSON archive bytes are preserved unchanged.

Authored Markdown links to explicitly copied archive files become local website links. Other evidence links remain bound to the declared Git commit. A future public-site observation must verify the v2 manifest and exact published files; earlier v1 observations remain historical and unchanged. An offline build alone is not a live browser or deployment verification.
