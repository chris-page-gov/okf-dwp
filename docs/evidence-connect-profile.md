# Evidence connect successor profile

This is an independent experimental navigation candidate over the existing full DMG and ADM structured corpus. It does not make entitlement decisions or establish current law. The frozen corpus, Chapter 84 pilot, staff question registry and earlier evaluations remain unchanged.

## Authored and generated inputs

`domain-profile/evidence-connect/profile.json` authors ten source-bound capital groups, search wording and proposed navigation links. The group text and page spans come from the existing Chapter 84 capital pilot. The successor assigns new group IDs under `id/unit/zz-evidence-connect/` so the ten records append after the existing sorted record shards; `structured-context/evidence-connect-manifest.json` reuses all 420 original record shards. Only a new ten-record shard and affected discovery, posting and adjacency shards are written. The manifest binds the frozen full-corpus manifest, pilot index and authoring by SHA-256.

Four previously captured but unlinked dependency groups now have directed links to exact records already in the full corpus: Chapter 77 definitions, the Chapter 85 income definition, the diminishing notional capital entry, and manual abbreviation tables. These links are unreviewed navigation proposals to entry records, not expansion of `et seq` ranges or proof of legal prerequisite. The source target IDs are checked against bound full-corpus record shards during generation. All 11 dependency groups remain open in the authored census, including ambiguous disregard routes, the DMG memorandum requiring specialist interpretation, and incomplete primary legislation and reported decisions. Ten added requirements retain open obligation IDs for formal capital concepts.

The U07 card has one explicitly scoped discovery pattern. It requires a Pension Credit phrase, an asset phrase and a disposal or deprivation phrase. This affects source navigation only: it does not resolve a legal concept, assert applicability or upgrade the package's evidence status. Unscoped aliases remain in the scored discovery card but cannot bypass the candidate shortlist. The generic v2 engine checks the pattern against the hash-bound card and gates lexical selection of this card by the declared benefit scope.

`structured-context/evidence-connect-explorer.json` is an additive Reader descriptor with a hash-bound successor context manifest and base index. It keeps the original Reader snapshot because the data, overview, presentation and endpoint-label planes are unchanged. The new context manifest has its own overlay bundle snapshot and names that Reader snapshot as `semantic_source_snapshot`; its base index is bound to the Reader snapshot as Explorer requires. The old descriptor and service defaults stay unchanged. A live Ask OKF view can load this descriptor through an immutable repository commit URL; the learning Pages workbench needs only the fixed 40 packages and bounded delivery parts. It does not need a second copy of the full corpus.

## Reproduce and check

Run with the pinned Explorer checkout used for the build. The same checkout must supply `packageDelivery.ts` after integration.

```sh
uv sync --locked
uv run --locked python scripts/build_evidence_connect.py
node scripts/build_evidence_workbench.mjs --explorer-root /path/to/pinned/okf-explorer
node scripts/check_evidence_workbench.mjs --explorer-root /path/to/pinned/okf-explorer
node scripts/test_evidence_connect_descriptor.mjs --explorer-root /path/to/pinned/okf-explorer
uv run --locked python scripts/check_structured_context_with_successor.py
node scripts/compare_evidence_connect.mjs --explorer-root /path/to/pinned/okf-explorer
node scripts/probe_evidence_connect.mjs --explorer-root /path/to/pinned/okf-explorer --pattern
node scripts/probe_evidence_connect.mjs --explorer-root /path/to/pinned/okf-explorer --confirmation
```

Use `scripts/build_evidence_connect.py --check`, `scripts/build_evidence_workbench.mjs --check`, `scripts/compare_evidence_connect.mjs --check` and the two probe commands with `--check` for exact retained-output replay. The descriptor test checks unchanged Reader bindings, then calls Explorer's actual `loadLargeCorpus` and `assembleCorpusContext` with a local source-backed fetcher. Its temporary Vitest file is removed after the run. The workbench producer binds the registry, corpus manifest, engine files and delivery code; no network or answer-model call is made. The independent checker reads all 40 raw contexts and bounded part responses, verifies each SHA-256 and reconstructs the exact canonical context through the Explorer delivery helper.

The structured-context base checker owns the frozen projection tree and rejects unknown files. The wrapper verifies each successor file against its independent producer, sets only those exact files aside while running the unchanged base checker, restores them even if that check fails, and verifies them again. It leaves the base projection and producer hashes unchanged.

## Measured development boundary

The same-overlay comparison runs all 40 staff questions with identical source and discovery shards and fixed budgets under v1 and v2 selection. Its `comparison.json` lists every gained and lost record and source span, requirements and omission codes. Source-span retention, requirement delivery and answerability are separate measures; all 40 final packages remain `insufficient`.

The diagnosed U07 wording is a development case. In the initial exact-alias prospective set, U07 appeared in 0 of 6 relevant paraphrases and 0 of 4 unrelated queries. Pattern work first improved recall but exposed unrelated navigation in three of five negatives; the original result is retained as `probes-pattern-initial.json`. The scoped intermediate result is also retained. The final fixed pattern set selects U07 and its 84861 entry in five of six relevant development queries and zero of five negatives. A separately fixed confirmation set selects three of four relevant queries and zero of five negatives. The missed relevant queries ask about a transfer to someone else; generic transfer wording was excluded because it also selected own-account transfers. These are small local development probes, not independent user or specialist validation.

The workbench manifest preserves the exact 40 supplied questions and per-case ambiguities and required evidence. Raw packages are canonical JSON; each published part has a content hash and is at most 32,768 bytes. The aggregate manifest intentionally omits a single source or capture date because DMG and ADM records have different provenance dates. Individual selected records retain their original source and extraction locators.
