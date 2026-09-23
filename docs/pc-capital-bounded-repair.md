# Bounded Pension Credit capital source repair

**Bounded development candidate, 23 September 2026.** This independent experiment prepares ten Chapter 84 Pension Credit capital passages for retrieval. It is not the production service default, official DWP guidance, a benefits decision, a specialist review or evidence of improved AI answers. The retained [protocol](../evaluation/capital-pilot/protocol.json), [attempt 03 report](../evaluation/capital-pilot/runs/attempt-03/report.json) and [source defect report](../evaluation/capital-pilot/input/defect-report.md) define the measured scope.

## What was prepared

The authoritative material is the captured [Chapter 84 PDF](../source/pdf/dmg-vol14-ch84.pdf) and its separately retained [extracted text](../source/text/dmg-vol14-ch84.txt). A **PDF page** is a location in that document. A **logical unit** is a proposed passage that keeps a question's rule, qualifications, examples or calculation steps together even when they cross pages. The [ten group definitions](../capital-pilot/groups.json) point back to exact source spans; they do not replace the PDF or certify the interpretation.

The [repair receipt](../capital-pilot/repair-receipt.json) accounts for every source byte while separating two genuinely mixed boundaries: paragraph 84356 from following contents material, and paragraph 84699 from reserved paragraph 84700 and the next contents section. The candidate also carries ten composite passage groups, separate unreviewed discovery summaries, a typed 21-row Appendix 1 representation and a literal reference from paragraph 84924 to Appendix 1. Typed rows are a reading aid; the original table and source text remain the evidence. All 11 named external dependencies remain unresolved. The candidate has had no new source acquisition and no specialist legal review.

The [original Data Agent review](data-agent-semantic-review.md) reported **4.042% overlap** with a static Pension Credit core profile. That is a comparison with that small profile's coverage, not a retrieval score and not this trial's improvement measure.

## Retained offline comparison

Attempt 03 assembled 52 packages: 13 fixed questions, two arms and two byte budgets. Ten questions concern the prepared capital passages; Staff 006 tests partial Chapter 84 support, and unknown and other-benefit questions are controls. Both arms use the **same newly authored Chapter 84 topic routing and source-selection intent**. The baseline selects component records; the candidate selects passage groups and adds discovery summaries and guarded navigation. It is therefore a local comparison of two new representations, not a comparison with the production service or an isolated test of summaries.

| Measure | Baseline | Candidate |
| --- | ---: | ---: |
| Complete declared groups at 524,288 bytes | 9 of 11 | 11 of 11 |
| Declared source-span bytes retained at 524,288 bytes | 28,015 of 28,021 | 28,021 of 28,021 |
| Staff 006 paragraph 84911 retained at 524,288 bytes | 319 of 319 | 319 of 319 |
| Source evidence delivered at 32,768 bytes | 0 in 13 packages | 0 in 13 packages |
| Packages marked insufficient across both budgets | 26 of 26 | 26 of 26 |

The baseline's two incomplete groups miss three whitespace bytes each. Both arms retain the substantive declared text at the larger budget. Across the 13 larger packages, the candidate repeats 15,888 source bytes already present elsewhere in the same package; the baseline repeats none. The candidate also selects substantially more additional source text outside declared spans; that text is context, not automatically irrelevant, but its presence does not establish a more precise or better answer. The unknown control selects no evidence. The other-benefit control remains insufficient despite lexical matches. These results give no substantial answer-quality gain. No model answer or network call was made during the comparison.

A **524,288-byte budget** is the space for one assembled evidence package; **32,768 bytes** is a much tighter assembly budget. A complete logical unit in a corpus does not guarantee that the final small package can carry its text. Here the small packages deliver no source evidence in either arm. The compact-delivery problem must be solved and measured separately from source boundary repair.

## What remains open

- Obtain specialist review of the passage groups, summaries and typed table. Agent engineering review and a visual check of the table have been completed; neither establishes legal applicability. Resolve the 11 external dependency groups before any claim of a complete answer.
- Establish a real compact-delivery result without relaxing the byte budget or concealing omitted evidence. Retain insufficient status where support is absent.
- Review any migration into the full-corpus Reader or remote service separately. Publishing this experiment and its report does not change either production default.
- Obtain specialist review separately from engineering checks. The four authorised Demo 1 model-answer calls are exhausted; this pilot made none and does not ask for more before the 30 September conference (travel begins 29 September).

The [work-package register](backlog-work-packages.md) keeps this bounded candidate under the still-open broader semantic task.

## Reproduce the experiment

Use the repository's locked Python environment and Node 26.7.0. A **locked environment** installs the dependency versions already recorded in the repository; it does not choose new versions. The comparison uses the unchanged Explorer context engine at `8a5b8d11a2d99935efca4ba8366812844061d928`.

```sh
uv sync --locked
uv run --locked python scripts/build_capital_pilot.py --check
uv run --locked python -m unittest discover -s scripts -p 'test_capital_pilot*.py'
node --test scripts/test_capital_pilot_metrics.mjs
node scripts/evaluate_capital_pilot.mjs --explorer-root /path/to/pinned-okf-explorer --attempt attempt-03 --check
```

The last command recomputes all 52 contexts from local files and requires exact agreement with their retained archives. It makes no network or model calls. The executable and input hashes are recorded in the report. `--check` preserves the earlier run; making a new experiment requires a new attempt name.

### Inspect the evidence without running an AI

1. Open the [ten group definitions](../capital-pilot/groups.json). Each group records its original component records and exact source locations.
2. Inspect the [candidate context index](../capital-pilot/candidate/index.json). Records carry separate source text, provenance, assertions and unresolved requirements. The [candidate corpus manifest](../capital-pilot/candidate/manifest.json) also supports the existing version 3 context consumer; this is not a new production service endpoint.
3. For a concrete result, decompress [the retained deemed-income question](../evaluation/capital-pilot/runs/attempt-03/candidate-capital-10-524288.json.gz). Inspect `selected`, `relationships`, `missing_evidence` and `budget` together. A summary nominates evidence; it does not replace it.
4. Compare the [typed Appendix 1 rows](../capital-pilot/appendix-1.json) with PDF pages 130–131. Every cell has its literal text and location. The printed “and so on” continuation is preserved without inventing rows.

### Preserved review history

[Attempt 01](../evaluation/capital-pilot/runs/attempt-01/report.json) and its complete inputs are preserved at commit `d821743241bcec28a0b11ba13e7b19eaa121e2db`. Review found that rewritten concept summaries incorrectly inherited older provenance, and reserved paragraph numbers were incorrectly listed as substantive group labels. Those defects were corrected before [attempt 02](../evaluation/capital-pilot/runs/attempt-02/report.json), preserved at `1fbf3f701d93165279586dbf14f80a5925fe9923`. Attempt 03 makes each summary locator an exact machine-readable JSON Pointer, such as `/groups/0/summary`. It retains the same fixed questions, engine, source text and substantive coverage result. Replay an older attempt only from its matching commit.

The trials are engineering checks, not specialist acceptance. Twenty-one Python tests and the independent source-span metric controls pass. The current CI workflow rebuilds the candidate and replays attempt 03. Earlier full-corpus sources, answer trials and obligations remain frozen.
