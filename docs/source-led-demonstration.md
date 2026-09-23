# Demonstrate source-led evidence discovery

This is an independent research candidate. Use it to inspect how guidance is
prepared and selected, not to decide a person's benefits. Its source-led
projection is separate from the earlier public service. Publication and client
acceptance must name their exact source and engine versions.

## 1. Understand the collection

Open the [beginner manual guide](source-led-manual-guide.md), then its linked
machine-readable conventions and document catalogue. **DMG** means Decision
makers' guide; **ADM** means Advice for decision making. These are different
DWP staff manuals with different structures and benefit regimes.

The captured collection contains 513 PDFs and 19,090 pages. A PDF page is a
checking location. A source unit is a proposed passage, which can cross pages.
The candidate has 53,727 retrievable units, including 75 earlier authored units.
An exact hash proves which bytes were used; it does not certify the interpretation.

## 2. Inspect a unit before asking a question

Load `structured-context/okf-explorer.json` in a compatible Explorer. Select a
passage, inspect its heading and source role, and follow the original PDF link.
For a passage crossing pages, inspect every span. Distinguish the original
publication date from the date the project captured or processed it.

A **discovery card** is a short source preview linked to the complete retained
passage. It helps discovery. It is not a legal summary or evidence of a complete
rule. Uncertain boundaries stay labelled. A source reference means that one
passage mentions another; a legal dependency needs separate review.

## 3. Compare Search and Ask OKF

Search for a subject such as `abroad`. Search finds candidate records.

Then open Ask OKF and paste a complete question from the
[staff-question matrix](../evaluation/staff-needs/README.md). Keep its wording,
including missing facts. The current Explorer starts with **Package bytes**
`524288` (512 KiB). Check this under **Evidence limits** if you changed a limit
earlier, then use **Build evidence package**. This is 512 times 1,024 bytes.
The recorded 32 KiB assemblies are smaller-budget controls and retain no
source evidence; selecting that budget is a useful refusal control, not a
shorter benefits answer.

Inspect these separately:

- Resolved concepts: which meanings matched, and which remain ambiguous?
- Evidence: which whole passages survived the budget?
- Relationships: does each route start at an actually resolved concept and
  follow retained, directed edges?
- Provenance: can the passage be checked against its source and exact spans?
- Gaps: what is missing, truncated, unreviewed or outside the declared scope?

Use **Read whole source passage**, the record link and **View cited source** to
move from selection to checking. An uncertain boundary can supply review
material while the result remains insufficient. Its presence is not a pass for
answerability.

## 4. Open the same package an AI would receive

Use **Inspect package JSON** or **Copy evidence package**. JSON is a structured
text format. The package records the question, selected evidence, reasons,
paths, source identity, budgets and unresolved requirements. No model has to
answer the question for this package to be useful.

When a compatible remote release is admitted, its manifest and exact reads can
deliver the package in small parts. **Delivery size** is the size of one reply;
**assembly size** is the total evidence selected. Small replies cannot recover
evidence excluded during assembly. Verify the source version, engine version,
complete-package hash and every part before claiming a complete reconstruction.
The current page tools default to 16 KiB per delivery response while keeping
the separate 512 KiB assembly default. A historical remote release may have
different defaults; check its recorded version instead of assuming parity.
See the [client-check guide](chatgpt-connection.md). A configured connection is
not proof that a particular ChatGPT, Data Agent or Voice session has its tools.

An AI may interpret the package, but its answer needs a separate claim-level
check: which exact evidence supports each claim, and which qualifications were
preserved? This experiment does not establish improved model-answer accuracy.

## 5. Read the evaluation without combining different measures

The [structural experiment](manual-structure-evaluation.md) starts with four
cases and then repeats with eight. It is development acceptance, not a blind
accuracy estimate for every paragraph. A separate census accounts for every
captured document and extracted byte.

The [question trials](../evaluation/manual-structure/context-probe/) retain all
40 staff occurrences plus an unknown-term control, in two projections and at
two budgets. In trial 06, source-read profiles activate for **37/40 occurrences**,
up from 8 in the earlier logical-unit baseline. At 512 KiB, all 40 retain source
passages and relationships. All 47 inherited, 181 previously added and 208 newly
added source-selection path occurrences are retained. These are routes through
evidence, not counts of correct answers.

Three questions still lack a suitably scoped source-read profile: unspecified
benefits abroad, an ambiguous use of SDA, and an unnamed benefit in a care home.
Their existing research leads stay available; the system does not guess the
missing facts. Location navigation activates for all 40, but does not close
their **203 original open obligations**. All results remain insufficient. The
32 KiB limit still retains no source evidence. Failed allocation attempts and
location-route trade-offs are kept alongside later repairs. See the
[separate measures and remaining work](source-led-results.md).

The original imprisonment and hospital acceptance cases are a separate check;
they must not disappear merely because the staff-question census passes.
Recorded specialist acceptance, current legal applicability and accurate AI
answers each need their own evidence.

## Reproduce the local checks

Use the locked Python environment and the immutable Explorer engine named in
`evaluation/manual-structure/context-probe/engine.json`:

```sh
uv sync --locked
uv run --locked python scripts/build_manual_guide.py --check
uv run --locked python scripts/build_structured_units.py --check
uv run --locked python scripts/build_structured_context.py --check
node --experimental-strip-types scripts/check_structured_replay.mjs \
  --explorer-root /absolute/path/to/the/pinned/okf-explorer
```

The final command requires an explicitly accepted `current.json` pointer. Its
absence means adoption is still held; do not create a pointer merely to bypass
that gate. For an individual earlier trial, use its retained runner, engine and
source identities. See the [work log](logical-units-work-log.md) and
[backlog](backlog-work-packages.md) for the exact remaining work.
