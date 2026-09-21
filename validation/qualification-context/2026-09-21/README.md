# Joint qualification and allocator comparison

**The full frozen experiment and its deterministic replay both pass.** This separate offline experiment measures what changes when source declarations and the context allocator change independently.

## Four cells, the same questions

| Source | Earlier allocator | Required-evidence allocator |
| --- | --- | --- |
| Immutable household source `3ef0e786` | Original source and engine control | Engine-only change |
| Final qualification source `7f9feb96` | Source-only change | Joint change |

Each cell uses all **40 registered staff-question occurrences** at **256 KiB and 512 KiB**. That is 320 deterministic assemblies, recorded as 160 paired source/case/budget observations. The question and original candidate registry must be identical between the two source commits. Both sources must retain the same 203 named open obligations.

The earlier engine comes from Explorer commit `b9a3b68b6dbf222f9a73cc8f450dd53f126e1b55`. The candidate is Explorer commit `c4f2de0a99b7bc2f8b8c8a06a3c715fb56b66d8e`. Both engines' three archived modules have exact hashes in [the protocol](protocol.json); the candidate's main engine hash starts `cc9fe1c1`. Both archived module sets must match their containing commits. No changing Explorer worktree code is imported.

The new source is DWP commit `7f9feb9634e3d94004853b838462aca132c505a5`, with index SHA-256 `7ffc9d00e71fef6aed5531373510df82998123e89fdb28091cfb82384adf2876`. The protocol SHA-256 is `7f188ccfbbfb02329f14b66b5e870f63fdf9d843979c8ffca721b0e45a9fa1c3`.

## Results

[Attempt 01](attempt-01/comparison.json) records all **320 assemblies**. Every context remains **insufficient**, with `ai_answer: null`. The source and question registry checks pass: both sources contain 901 records and the same 203 named obligations; the final source has 1,442 assertions, compared with 1,427 earlier.

| Budget | Source | Engine | Candidate matches | Retained / activated declared paths | Household pages selected / 7, each case | Household pages with declared path / 7, each case |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 256 KiB | Earlier | Earlier | 169 / 177 | 330 / 377 | 1 | 1 |
| 256 KiB | Earlier | Candidate | 177 / 177 | 377 / 377 | 1 | 1 |
| 256 KiB | Final | Earlier | 169 / 177 | 346 / 433 | 1 | 1 |
| 256 KiB | Final | Candidate | 177 / 177 | **433 / 433** | **7** | **7** |
| 512 KiB | Earlier | Earlier | 176 / 177 | 362 / 377 | 7 | 1 |
| 512 KiB | Earlier | Candidate | 177 / 177 | 377 / 377 | 1 | 1 |
| 512 KiB | Final | Earlier | 176 / 177 | 418 / 433 | 7 | 7 |
| 512 KiB | Final | Candidate | 177 / 177 | **433 / 433** | **7** | **7** |

Candidate and path counts are case/source or case/path occurrences, not unique pages or accuracy scores. The final source declares additional qualification paths, so its denominator differs from the earlier source. Both engines independently activate the same 91 requirement occurrences in each source/budget slice. No returned requirement metadata was omitted in these runs; the negative controls separately show that such omission would remain counted if a smaller-budget refusal occurred.

The trade-off is visible: at 512 KiB, the earlier source incidentally supplied all seven household pages with the earlier allocator. Prioritising its existing declarations displaced six pages that were not declared required. The final source explicitly declares the seven-page qualification chain, so the candidate preserves it at both budgets. This supports explicit source modelling; it does not establish that every unmodelled qualification will survive.

For Staff 012 and Staff 013, the final candidate at 256 KiB retains **27 records and 63 relationships**, including all **39 activated path occurrences** across three applicable profiles. Each question's own profile declares 17 paths. The only absent required identifiers are 15 named obligations across those profiles. At 512 KiB it retains **62 records and 124 relationships** and all 39 paths, but also selects an optional temporary-care-home concept while omitting its dependency `page/78/0024`; the package explicitly reports that dependency gap. The declared permanent-care-home path census is not a claim that all optional context is supported.

The unchanged 203 obligations comprise 43 evidence-closure checks, 40 applicability questions, 40 legal-version reconciliation checks, 40 independent-review gates and 40 question-scope questions. Unresolved terms and budget omissions remain in the receipt. More retained guidance has not closed those obligations or supplied specialist acceptance.

Receipt SHA-256: `45fb3ce7b768833eb6f94b6461f1531f56293de419665bd5adaf606d9bfdc3ac` (9,129,250 bytes). Fourteen offline controls cover archive admission and the independent path census, including metadata refusal, ambiguity, reversed paths and existing-output protection.

## Measurements

- Known case/source candidate matches, declared path occurrences and missing paths. Path and requirement denominators come from the source requirements and each engine’s pre-budget alias resolution, independently of returned context metadata. If a byte-pressure refusal clears the output requirements, those expected paths remain missing and the omitted requirements are counted explicitly. Both source variants and both engines retain their own denominators.
- Exact package identities for each cell, and whether changing only the engine preserves the package byte for byte.
- Whole selected records and literal-text digest verification, source/bundle bindings, retained dependency issues, ambiguity, missing evidence and budget omissions.
- Staff 012 and Staff 013: whether each of seven household pages is present, explicitly required, and retained through its declared path. Incidental page selection and satisfied declared paths are separate fields.
- The complete list and categories of the 203 open obligations, with a check that the new source does not remove them.

The seven page routes are `page/77/0007`, `page/77/0019`, `page/77/0021`, `page/77/0023`, `page/77/0024`, `page/77/0025` and `page/78/0025`. These are the chapter/page routes in the captured corpus, not paragraph numbers. Their source text, hashes and exact declared chains remain inspectable in the named immutable source commit and deterministic replay.

All contexts must remain **insufficient**, with no AI answer. Better evidence retention is not proof of an accurate legal answer, resolved claimant circumstances, current legal applicability or specialist approval. Single local timings are diagnostic and are affected by execution order and caches; they do not establish a causal or deployed speed improvement.

## Admission and historical integrity

The runner reads only named public files from exact Git commits. Git blob sizes are checked before reads. It never reads private correspondence or uses changing source files in the checkout. The fake `example.test` corpus URLs are handled entirely by a local, path-restricted adapter; there are no network calls. The shared corpus engine still checks the declared compressed and decoded hashes and retrieval limits.

Both engine sets, protocol, runner, guard helper and metric helper are copied into a fresh output directory. Replay admits an exact file allowlist and checks the runner, both helpers, protocol and engine hashes **before importing archived engines**. Parent directories, directories and files cannot be symlinks; reads are bounded and use no-follow file handles. An existing output directory is refused. The baseline also has to match the named immutable Explorer commit.

The earlier allocator comparison, source snapshots and every fixed-evidence model observation remain unchanged. This experiment creates new identities; it cannot retrospectively repair a model answer or certify an earlier browser observation. Invoke the reviewed repository runner below, rather than treating an arbitrary archived runner as executable instructions.

## Reproduce the frozen comparison

The final source and engines are pinned in the protocol. An unapproved pending protocol refuses execution before creating an output directory; a retained output cannot be overwritten. From the DWP checkout:

```sh
node --test validation/qualification-context/2026-09-21/*.test.mjs
node --experimental-strip-types validation/qualification-context/2026-09-21/compare.mjs \
  --dwp-root /path/to/okf-dwp \
  --explorer-root /path/to/okf-explorer \
  --output /private/tmp/okf-qualification-new-observation
node --experimental-strip-types validation/qualification-context/2026-09-21/compare.mjs \
  --dwp-root /path/to/okf-dwp \
  --explorer-root /path/to/okf-explorer \
  --check validation/qualification-context/2026-09-21/attempt-01
```

Choose an unused output directory for a fresh run; the example `/private/tmp/okf-qualification-new-observation` must not already exist. The `--check` command verifies the retained first observation. Both local repositories must contain the named commits. No dependency installation, model credentials or unlocked desktop is needed. Replay compares all substantive fields exactly while excluding the recorded time and local runtime labels. Its receipt is limited to 32 MiB; each engine module is limited to 2 MiB and its protocol to 32 KiB.
