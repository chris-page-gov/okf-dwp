# Reading-help release candidate — draft notes

**Status: candidate.** This is an independent experimental publication, not official DWP guidance or an entitlement decision. Consumer PR 158 merged as `936da562e4629ed2021bb09fcc55c6ac53ca3a9c`; public Pages bytes, the follow-up consumer increment and a paired browser receipt are pending. Do not describe the candidate as publicly verified or specialist accepted.

## What is implemented

- The deterministic corpus accounts for **513 DMG and ADM documents**, **19,090 pages**, **53,727 adopted structured units** and **893 pages without usable extracted text**. It publishes 54,299 bounded passage segments in 1,455 compressed leaves, with 197,564 delivered occurrence candidates. Processing coverage records gaps; it does not mean complete explanations. The later 54,577-unit amendment candidate remains separate.
- The catalogue has SHA-256 `6c53b659b519aa4cbf7529e7e10eb4ad3bfe8efcac18055ec2a5ade724998b46` at data commit `cbada7bf544106bdceb2445fc379c8b3e5b73ee4`; corpus PR 50 merged as `239f974c6cba23a2a37182af722ebba0803504b6`. The additive workbench integration is recorded at `2ad33add6d8660fec98bf34fb98480a9d0de9e27` and still needs its paired publication identity.
- Exact unit and source identity links cover **401 of 403** distinct retained workbench records across all **40** cases. The two unmatched capital composites, U06 and U10, remain unlinked. The workbench does not rewrite their packages or evidence requirements.
- The original Chapter 60 v1 reading aid remains unchanged at fallback tag `demo-2026-09-30-reading-help-v1` (pinned manifest commit `46a85142e0fe3a73b686b91029d357770b68591d`). Separate v1-compatible manifests add 20 body-to-footer occurrence pairs and dated candidate statutory links.

## Checks and retained results

- A source-led 12-case gate and a separately frozen fresh 24-case gate passed their stated structural controls. The first held-out attempt remains **23 passed and one failed**: H05 expected only DMG 070831 while the frozen source prints a range to 070834, which the producer correctly retained unresolved. A further pre-execution fixture was rejected over `et seq` and coverage. Later producer regressions replayed unchanged expectations; none is specialist legal review.
- The full consumer compatibility audit found zero shape/size violations across 513 indexes and 1,455 leaves, including the printed 166-abbreviation table. The integrated focused reading-help suite recorded 50 passing controls. The 28-case passage review recheck reproduces all 55 files and passes four controls. The nine previously reviewed substantive chapters retain exact PDF/extraction hashes and every recorded source span. This is a non-regression check of the retained review; **case 014 remains unresolved**.
- Cold and warm equal-budget replay passed **40/40 package-integrity checks**, with all 40 still **insufficient** and exact retained packages unchanged. The fixed limits were 512 KiB, 64 records, 128 relationships and depth six. Cold fetches totalled 158,837,842 bytes; warm fetches totalled zero bytes. This is a non-regression result, not improved retrieval or answer quality. There were **zero content-processing or answer-model calls** for this increment.
- The optional legal bridge reuses the existing **20 statutory units, 16 provisions and 43 navigation relationships**. It requested three new provision targets and retained four observed bodies because section 70 has distinct England and Wales and Scotland variants. Four source-span-bound full-title mappings and 16 citation bindings passed structural admission; five unsupported citation cards remain unresolved. The optional context adds 10 records and 51 relationships while preserving all 40 original evidence requirements. The unchanged ordinary natural-language probe still misses the bridge at its fixed budget; it is not the default service.

## Boundaries before publication

The catalogue is machine-proposed and unreviewed. The 893 extraction gaps are not blank-page findings. Mixed-case abbreviations such as `WDisP` may remain unrecognised, and repeated-phrase proposals are capped at 100 per document. A source-verified literal proves its location and bytes, not the correctness of an expansion, a citation or legal applicability. No new statutory request, OCR, content model or answer model is needed to reproduce these deterministic artefacts.

Before public release, bind the merged consumer commit, exact DWP and Explorer Pages identities, and a real Chrome browser receipt. Preserve the verified Chapter 60 fallback tag and every failed control. Specialist review of candidate meanings, the territorial and date variants, unresolved references and case 014 remains open.

## Draft evidence pointers

- `reading-help-corpus/manifest.json` — catalogue and processing ledger.
- `evaluation/reading-help-rollout/heldout-gate-02.json` and `heldout-03-producer-replay-03.json` — retained failure and current unchanged-expectation controls.
- `evaluation/reading-help-rollout/consumer-compatibility-01.json` — complete leaf/index contract audit.
- `evaluation/reading-help-rollout/replays/reading-help-20260927-01/report.json` — fixed-budget cold/warm non-regression.
- `evaluation/reading-help-rollout/workbench-link-report.json` — 401/403 exact target mapping.
- `domain-profile/reading-help-law/admission.json` and `evaluation/reading-help-rollout/law-context-probe.json` — optional legal admission and failed ordinary selection.
- [Release manifest](../evaluation/reading-help-rollout/release-20260927/manifest.json) — candidate hashes and identities for release binding.

## Verify the retained release evidence

Run this offline check from the repository root:

```sh
uv run --locked python scripts/check_reading_help_release.py \
  --root . \
  --manifest evaluation/reading-help-rollout/release-20260927/manifest.json
```

CI runs the same check. It verifies the bound artefacts, the separate 12/24
controls, all 40 unchanged insufficient packages and the exact public verifier.
A candidate can be structurally valid while public verification remains false.
A technically verified status requires the complete passing public receipt,
matching consumer and data identities, and the exact verifier script hash.
These checks do not establish legal completeness or specialist acceptance.
