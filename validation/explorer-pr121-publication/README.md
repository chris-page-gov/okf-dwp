# Explorer PR 121 publication evidence

This directory preserves the public publication receipts for [Explorer PR 121](https://github.com/chris-page-gov/okf-explorer/pull/121), recorded on 15 September 2026. All 12 indexed receipts and the remaining supplementary evidence files are unchanged. This README is the only added explanatory file. The built Explorer application files are not vendored in DWP.

## Reviewed and deployed application

The reviewed commit is `8e01dfe16538c6045ee1d55b64c3f6e24bada9f7`; the merged and deployed commit is `ab2e863bd6707474e01a054f065f7da5fa2d7ff4`. Their commit identifiers differ, but the [source-tree comparison](source-tree-comparison.json) records the same Git tree, `5cd233121689e279e543958163ff8a32f69910ad`.

The [published application verification](public/public-app-verification.json) records that all 21 declared deployed application files match the reviewed application manifest. Their bytes were independently verified using the temporary reviewed build and the live HTTPS URLs. Its application tree SHA-256 is `84381f7ccc93015e9fab6a364cde40b668cbbdc65af3c12eaefdd673e0c809f1`. The [canonical application manifest](public/public-app-manifest.json) and the verifier's per-file results are retained here. These are recorded observations, not a new claim about the deployment at a later date.

## What the checks establish

- [PR CI](https://github.com/chris-page-gov/okf-explorer/actions/runs/35025588136) passed the full application and publication checks, including the Chrome, Firefox and WebKit assurance job. Details are retained in [pr-ci.json](pr-ci.json).
- [Canonical-main CI](https://github.com/chris-page-gov/okf-explorer/actions/runs/35027364360) passed the normal impact-selected workflow. Its impact plan skipped unchanged application, browser and other checks; it was not a second full three-browser run. See [main-ci.json](main-ci.json).
- [Pages CI](https://github.com/chris-page-gov/okf-explorer/actions/runs/35027352490) independently built and published the merged application and passed deployment verification. See [pages-ci.json](pages-ci.json), the [runner receipt](runner/live-deployment-receipt.json) and [local deployment receipt](local-live-deployment-receipt.json).

The deployment browser receipts cover the Explorer estate-registry journey. **Acceptance of the DWP bundle in the browser is a separate DWP receipt**, owned by the lead task. This directory does not establish DWP legal correctness, complete DWP journey acceptance, WebMCP or live-voice compatibility.

## Copy integrity and inspection

Before and after copying, all 12 entries in [evidence-index.json](evidence-index.json) were checked for byte length and SHA-256. The 21 application materials in the temporary reviewed build were checked against [the application manifest](public/public-app-manifest.json); its canonical tree digest was recomputed and the recorded HTTPS observations were cross-checked. The initially copied application directory was then removed to avoid duplicating runtime assets. All 12 index bindings remain valid.

The directory retains 15 original evidence files (99,264 bytes), including the evidence index and supplementary watch logs, plus this README: 16 files in total. Every retained original file was compared byte for byte with the supplied receipt directory. The temporary source receipts and reviewed build were left unchanged.

Inspection of the supplied evidence, including the temporary application files, found public GitHub Actions metadata and publication/hash receipts. A scan for credential tokens, private keys, credential assignments, local user paths, email addresses and private IPv4 addresses found no matches. This was a bounded inspection, not a full security audit. No source receipt was edited or redacted. The original evidence index does not cover this explanatory README.
