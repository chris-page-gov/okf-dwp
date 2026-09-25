# Evidence workbench handover — 24 September 2026

## What changed

The diagnosed capital question now finds the complete relevant passage and its
linked guidance. The Evidence workbench lets a reviewer examine the evidence
selected for each of the 40 public staff-question occurrences. One wording is
repeated, so the register contains 39 distinct questions.

This is an independent research publication, not an official Department for
Work and Pensions (DWP) service or an entitlement decision. The Decision makers'
guide (DMG) and Advice for decision making (ADM) are staff guidance manuals;
their paragraph numbers identify guidance and PDF page numbers locate it.

## Why the question failed

The text was already captured. The everyday question did not activate its
specialist concept, *notional capital*, and the relevant passage ranked 29th
when only 16 initial candidates could enter the evidence package. Increasing
that package's final size could not recover an item excluded earlier.

The repair connects ten existing capital passages to the full corpus. It adds
explicit, source-bound discovery wording, prioritises the leading passage's
dependencies and delivers complete retained text in checked parts. The reusable
Explorer engine has no benefit names or paragraph numbers hard-coded into it.
The domain's authored navigation remains separate from official guidance.

## What has actually been checked

| Check | Recorded result | What it does not establish |
| --- | --- | --- |
| Original capital question | The whole U07 passage, DMG 84861 entry and their direct link were selected in actual Reader → Ask OKF browser use. | All possible exceptions, current-law applicability or a complete benefits answer. |
| Other wording | 5/6 positive development questions and 3/4 separately fixed confirmation questions selected the target; each set selected 0/5 negatives. | General success on unseen questions. Transfer-to-another-person wording still misses. |
| Forty-question delivery | 40 exact packages reconstruct from 673 parts, each no larger than 32,768 bytes. | Text never selected by retrieval is not recovered by delivery. |
| Selection comparison | An 80-assembly same-source comparison preserves gained and lost records and source spans. | Record counts are not relevance or answer-quality scores. |
| Browser inspection | Actual source links, passages, relationships, missing evidence, deep links, local proposal export and narrow layout were exercised. | A review proposal is not specialist approval. |
| Other bundles | The non-DWP study-club check and executed Heritage acceptance passed with prior receipts preserved. | DWP legal completeness. |

All 40 packages still declare **insufficient**: they do not establish that all
evidence needed for a complete answer is present. That status does not mean
that every selected passage is irrelevant. The workbench separates selected
text, the original review brief, current requirements and remaining gaps so a
reviewer can inspect the difference.

The original capital browser result contains 44 records and 68 relationships,
using 522,995 of its 524,288-byte allowance in the final public run. The earlier
local run used 522,919 bytes; each receipt retains its own URL and binding.
Its retrieval and assembly budget omissions remain visible.
No new answer-model comparison was run for this repair.

## Use it in a meeting

1. Open the [Evidence workbench](https://chris-page-gov.github.io/okf-explorer/evidence/?manifest=https%3A%2F%2Fchris-page-gov.github.io%2Fokf-dwp%2Fevaluation%2Fevidence-workbench%2Fmanifest.json&case=staff-001).
2. Select a question and read its original review brief and current evidence status.
3. Choose a passage and open its cited source page. GOV.UK blocks embedded PDFs;
   the source opens in a separate tab.
4. Inspect the extraction, passage boundaries, concepts, relationships and dependencies.
5. Show why it was selected and what is missing, then open its machine-readable
   package or export a local review proposal.

To reproduce the repaired question, [open the updated source in Ask OKF](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F7eeded763042ddd0070f4fed834c6074149e8e2f%2Fstructured-context%2Fevidence-connect-explorer.json)
and select Ask OKF. Enter:

> Can Pension Credit treat capital as still held after someone has got rid of it, and are there exceptions?

Use 64 records, 128 relationships, depth 6 and 524,288 bytes to match the recorded
run. Earlier pinned bundle links remain historical snapshots; use this new
source descriptor for the repair. The remote MCP service admitted this source
in the separately verified [0.7.0 release](../validation/compact-delivery/v0.7.0/README.md).
Older connected clients may need the [metadata refresh](chatgpt-connection.md).

The [beginner guide](evidence-workbench.md) explains the terms as they arise.
Search finds possible records; Ask OKF assembles evidence; the workbench inspects
that evidence; an AI answer would be a separate interpretation.

## Release identities

- [Explorer PR145](https://github.com/chris-page-gov/okf-explorer/pull/145)
  merged as `e6084059f9b09633cfb8385be20099b952915e82`. All required PR checks
  passed, including the full Chrome, Firefox and WebKit suite. The merged tree
  exactly matches the reviewed candidate. Its exact-commit Pages release and
  public verification passed in [run 35969493742](https://github.com/chris-page-gov/okf-explorer/actions/runs/35969493742).
- [DWP PR36](https://github.com/chris-page-gov/okf-dwp/pull/36)
  merged as `7eeded763042ddd0070f4fed834c6074149e8e2f` after both protected
  candidate runs passed. Its merged tree exactly matches the reviewed candidate.
  DWP validation pins the merged Explorer implementation. Exact merged-main
  [validation 35972890182](https://github.com/chris-page-gov/okf-dwp/actions/runs/35972890182)
  and [Pages deployment 35975520154](https://github.com/chris-page-gov/okf-dwp/actions/runs/35975520154) passed.
- The [final public byte check](../validation/evidence-workbench/2026-09-24/public-release/site/observation.json)
  matched 1,141 requests against the exact merged build, including all 1,140
  declared outputs. This checks deployment identity; exact package reconstruction
  is checked separately by the required 40-question delivery gate.
- The [final public browser observation](../validation/evidence-workbench/2026-09-24/public-release/browser/receipt.json)
  binds the permanent Pages manifest to `7eeded763`, verifies all 40 catalogue
  entries and exercises three representative cases, the repaired capital query,
  narrow layout and local export. Its [deep-link check](../validation/evidence-workbench/2026-09-24/public-release/browser/deep-link.json)
  preserves the selected question, passage and tab. Application console, page
  and HTTP errors were absent; blocked or aborted source-PDF frames are retained
  explicitly. Direct PDF links provide the fallback.
- The separate [public candidate observation](../validation/evidence-workbench/2026-09-24/public-candidate/receipt.json)
  used hosted Explorer and immutable DWP data at `61f8539f`. It is labelled
  separately from DWP's subsequent Pages release.

## Reproduce the retained packages

The retained packages come from deterministic, offline replays. Their
`binding.index_url` uses `example.invalid` as a virtual replay address; it is
not a public download endpoint. The fingerprint binds the exact corpus bytes.
Use the [immutable corpus manifest](https://raw.githubusercontent.com/chris-page-gov/okf-dwp/7eeded763042ddd0070f4fed834c6074149e8e2f/structured-context/evidence-connect-manifest.json)
and the commands in the [beginner guide](evidence-workbench.md) for reproduction,
or the live descriptor above for a new Ask OKF assembly. The cited official
source URLs and the workbench's package/part URLs are separate from that virtual
replay address.

## Remaining work

- Broaden and independently evaluate everyday-wording coverage; retain the
  transfer-wording miss and the earlier false-positive experiments.
- Review the open dependency and applicability obligations. Captured entry links
  do not silently expand every cross-reference range or replace missing legal text.
- Use the workbench for specialist review of all 40 questions. The engineering
  checks do not establish legal acceptance or improved AI answer accuracy.
- Treat remote MCP service admission and observed ChatGPT-client compatibility
  as separate releases. This browser release does not silently update that service.

The [machine-backed backlog](backlog-work-packages.md) separates implementation,
public observation and specialist acceptance. Work ran in isolated parallel
branches under one integration task; further steering can stay in that task.
