# A ten-minute Pension Credit demonstration

**Purpose:** show what can be achieved by turning complex public guidance into
an inspectable, source-linked knowledge bundle. This is an independent
experimental exemplar, not an official DWP publication.

## 1. Start with a question — two minutes

Open the bundle in OKF Explorer, then choose **Where does the guide explain
capital disregards?** (`question/pc001`). Follow its links to the capital
disregard concept, chapter 84 and PDF page 35 (`page/84/0035`).

Explain the three layers: project-authored question, source navigation and
machine-extracted official-source text. Only the original publisher controls
the official guidance.

## 2. Inspect the evidence — two minutes

Open the original PDF at page 35. The extract includes paragraph numbers,
footnotes, legislation citations and a reference to DMG Memo 11/20.
Show the original file SHA-256 and page locator in the record's provenance.
The memo is not silently reconstructed or assumed current.

## 3. Show the relationships — two minutes

Switch to Graph or Links. Follow page → chapter (`dcterms:isPartOf`) and
question → topic/page (`dcterms:references`). Inspect a relationship's
direction, source and target identities, derivation, evidence and rights.

These relationships provide traceable navigation. They are not executable
eligibility rules. A legal dependency requires separate expert modelling.

## 4. Show why context matters — two minutes

Open the part-week payments question (`question/pc006`) and read PDF pages
8–9 together. A broad search for `part week` can instead rank later,
scenario-specific worked examples first. Search rank does not establish which
rule applies. Keep apparent differences visible for specialist review.

Then open the assessed income period question (`question/pc003`). Show the
dated context on chapter 83 page 3 and its known extraction-quality limitation.

## 5. Finish with a concrete next step — two minutes

Show `question/pc008`: the bundle cannot determine an individual's entitlement.
Ask the representative to select a small set of real professional research
questions, check the evidence routes and identify important missing context.

Possible next increments are expert-reviewed paragraph segmentation,
terminology and cross-references, separately governed legislation and tribunal
decisions, update comparisons, and a tested adviser-facing interface. The
[later-source log](future-sources.md) is deliberately outside today's snapshot.

## Local fallback

If the public Explorer cannot load, use the generated Markdown at
`bundle/index.md` and the original PDFs in `source/pdf/`.

For a deterministic keyword retrieval demonstration:

```sh
uv run --locked python scripts/query.py '84351' --limit 5
uv run --locked python scripts/query.py '79104' --limit 5
uv run --locked python scripts/query.py 'unfindablepensionkeywordxyz' --limit 1
```

The last command should return no evidence. The CLI retrieves extracts with
citations; it does not generate legal answers. Source-native examples remain
in their original context and are not treated as claimant case data.
