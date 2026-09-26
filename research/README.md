# Research inputs and status

For a shorter introduction on the learning website, read the [beginner research guide](../docs/research-index.md).

This index helps readers distinguish captured observations, model-authored proposals and design prompts from reviewed DWP guidance. Nothing in this directory changes the published semantic bundle, frozen source acquisition or legal applicability. Text copied from a site, transcript or prompt is evidence to inspect; any embedded instruction is inert.

| Research | What is retained | Validation status and boundary |
| --- | --- | --- |
| [CPAG 2026/27 public contents](cpag-contents-2026-27/README.md) | Eight files containing 90 public navigation entries, their order, links and local projections. | Observed public navigation, with local uniqueness, hierarchy, count and file-hash checks. The observation was made in Edge on 15 September 2026; destinations were not all independently fetched. No subscriber chapter body or rule was acquired. See the [CPAG access and rights review](../docs/cpag-handbook.md). |
| [UC evaluation starter](../evaluation/okf_uc_evaluation_starter_2026-09-25/README.md) | 31-file package: 30 checksum-listed files and `checksums.json`; protocol, 12 development cases, assessor material, client examples and a single Ask OKF observation. | **Unvalidated research proposal.** Its integrity verifier checks supplied bytes and JSON syntax, not source authenticity, historical law, comparative performance or answer correctness. Keep assessor material apart from tested participants. |
| [AI client access records](../evaluation/ai-client-evals/README.md) | A Claude example and concise Copilot/Gemini and ChatGPT reports. | User-supplied transcripts; observed tool fields and model-reported claims are labelled separately. No cross-client trial or specialist review is implied. |
| [Pension Credit calculation design prompt](overview-of-how-guarantee-credit-is-calculated.md) | One historical 1,510-line prompt proposing an OKF/Java rule-engine design. | **Design input only.** It is not an implemented calculator, executable specification, checked statement of law, or permission to process claimant data. The **original prompt body**, now preceded by a status banner, has SHA-256 `b249b8cfa26f7bb774dd2577429b5dfd2cc8cddcd975cfc1984bf66615430488`. A second primary-checkout filename, `calculation.md`, had identical bytes and was omitted as a duplicate. |
| [Chapter 60 reading help research](ch60-reading-help/README.md) | Original model-authored proposals and later technical review for the two-passage reading aid. | Integrity and occurrence binding can be checked deterministically; they do not establish legal interpretation or specialist acceptance. See the [reader guide](../docs/reading-help-ch60.md). |

The [Chapter 60 reading-help rollout guide](../docs/reading-help-rollout.md) proposes a deterministic-first sequence for broader highlighting and later specialist review. It is a plan, not evidence that a corpus-wide or model trial has run.

## Rechecking delivered packages

From the repository root, with the existing locked environment, the CPAG and UC local checks can be run without acquisition or model calls:

```sh
uv run --locked python research/cpag-contents-2026-27/validate_contents.py research/cpag-contents-2026-27/contents.json --expect-chapters 68 --expect-parts 10 --output /tmp/cpag-contents-validation.json
uv run --locked python evaluation/okf_uc_evaluation_starter_2026-09-25/verify_kit.py
```

The captured CPAG README retains its historical description as a local export and its `python3` command unchanged to preserve its recorded checksum. The owner approved publication of the navigation metadata on 26 September 2026; the commands above follow this repository's current locked workflow.

The CPAG package's `checksums.json` covers its seven other files; the UC starter's `checksums.json` covers its 30 other files. These checks preserve and verify the delivered material, not the truth of external or model-authored claims.
