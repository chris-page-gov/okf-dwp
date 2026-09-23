# Large paragraph review: historical amendment boundaries

This is a structural review of the **28 paragraph candidates over 15,000 bytes** in the frozen catalogue. All 28 are historical amendment extracts; none is a current chapter unit. A size threshold identifies things to inspect, not an error rate or a safe splitting rule.

The [individual findings](findings.json) record exact unit identities, source hashes, PDF locators, original-text spans and proposed follow-up for every candidate. The [source observations](source-observations.json) verify every original span and the complete reconstructed unit text, and record each included page's opening, ending and structural markers. Full text was scanned mechanically; each page profile was read for structure. This is not a line-by-line legal review. Fifteen [rendered PDF pages](visual/render-receipt.json) were visually inspected where table layout, a false paragraph label or an excerpt transition mattered.

## Findings

| Structural finding | Units |
| --- | ---: |
| Amendment cover, remove/insert table or reference material absorbed into a later paragraph | 17 |
| Contents run absorbed after a real paragraph | 7 |
| Contents plus reference table absorbed after a real paragraph | 1 |
| Separate appendix and equivalence table labelled as the preceding paragraph | 1 |
| Amendment-summary reference promoted to governing paragraph identity | 1 |
| Uncertain excerpt transition with severely spaced extraction | 1 |

There are **27 confirmed mixed-structure units and one uncertain transition**. No candidate was established to be one coherent long passage. These findings concern this selected historical population, not all 53,727 units.

Examples make the problem concrete:

- **DMG volume 9 amendment 26, 50018:** the rule ends on PDF page 16. Pages 17–30 are contents pages, visibly using dotted leaders and right-hand paragraph references. They are nevertheless inside the unit labelled 50018.
- **DMG volume 5 amendment 53, 28684:** the captured rule ends after numbered item 2 and the word “and”. The next page is capital contents. Cutting out the contents must leave an explicit incomplete fragment; it must not invent the missing continuation.
- **DMG volume 2 amendment 35, 072842:** the unit starts with the amendment letter and remove/insert table, includes statutory-instrument reference material and contents, then reaches the actual paragraph on page 15. Backwards heading association has absorbed entire unrelated sections.
- **DMG volume 14 amendment 43, 85067:** the number appears in a cover-letter change summary. It is not the governing rule at that location. The wrongly labelled unit then contains chapter 84 contents and stops at the business-assets heading, before the actual 84374 paragraph.
- **DMG volume 2 amendment 38, 070333:** page 16 is a reciprocal-agreement table with its own qualification. Page 17 visibly starts an `APPENDIX`, with local paragraphs 1–25 and a later article-equivalence table. All have been carried under 070333.
- **DMG volume 2 amendment 40, 071920:** the PDF shows a list ending with “or” on page 28; page 29 starts item 10 from different, unlabelled excerpt material. Text extraction inserts spaces inside words even though the rendered PDF is readable. The exact new passage identity remains unresolved.

## Smallest reusable next increment

The following are proposals, **not implemented rules**. They need source-bound positive and negative controls before a separate parser build. They must preserve original bytes and the 75 earlier authored units. Do not split solely on length, a page break, a paragraph-number mention or an arbitrary token limit.

### R1: recognise contents continuations

Recognise a bounded run of navigation rows with repeated dotted leaders and a consistent target-number column, including continuation pages without the word “Contents”. Separate the navigation region from the preceding rule and from the next actual paragraph or heading. Use source layout/tag observations when available; keep ambiguous regions uncertain.

Controls: the 50018-to-contents transition; contents between 28684 and the capital heading; a contents continuation without an opening heading. Negative controls: a single dotted form field, ellipsis within prose, a table of substantive amounts and a true example continuing onto the next page. Do not promote contents targets to paragraph bodies.

### R2: keep amendment and reference material in its own role

Use the source-observed amendment-letter, paired remove/insert columns, abbreviation list and statutory-instrument table conventions to bound front matter. Paragraph numbers in an amendment replacement table or change summary are references, not governing paragraphs. Identify these roles from source structure; a historical classification alone must not suppress actual rules later in the same PDF.

Controls: volume 2 amendment 35's two-column table; volume 14 amendment 43's change-list reference 85067; abbreviation blocks followed by the real 59052 or 83039 passage. Negative controls: an ordinary rule discussing removing an item, an inline abbreviation definition, and an actual paragraph immediately following the amendment material. Do not treat the presence of “Amendment” in a footer as a new boundary.

### R3: constrain backwards heading attachment

A proposed heading must be a local heading candidate with source support. It must not pull a later paragraph backwards across a contents region, a reference table, an amendment notice or a prior passage. Keep unclassified preceding text as a separate uncertain fragment instead of assigning it to the next paragraph merely because there is no earlier recognised paragraph marker.

Controls: the 072842 and 30110 front-matter absorptions; the 23221 unit prefixed by earlier numbered conditions. Negative controls: a genuine heading on the previous page immediately preceding a paragraph, a wrapped heading and existing cross-page examples. Preserve exact original spans and separate source-heading text from inferred hierarchy.

### R4: retain excerpt gaps honestly

Amendment packages are replacement-page collections. A page ending mid-condition or mid-example can be followed by contents or a different excerpt. Bound the observed structural transition, retain the incomplete side as such, and never fill it from a different edition without a separate reviewed dependency. Unlabelled prose after a contents run must not inherit the rule before that run.

Controls: 28684's unfinished condition; its earlier amendment's unfinished example; 83042 followed by contents and the tail of a different cottage example. Negative controls: a genuinely continuous list, note, citation or example across a page boundary. Page numbering and length alone are insufficient.

### R5: recognise a bare appendix heading

Extend appendix recognition to a source-supported standalone `APPENDIX`, not only numbered appendices. Preserve local short-numbered paragraphs and tables within their own scope. Short numbers must not be promoted into DMG chapter paragraph identifiers.

Controls: the visible appendix and equivalence table following 070333. Negative controls: “see appendix” in body text, an appendix entry in contents and a capitalised word within a quotation. Keep the page 16 table and its qualification together.

### R6: preserve damaged extraction uncertainty

For the severely spaced volume 2 amendment 40 text, any normalised view should remain a separate reversible observation with an offset map to unchanged source bytes. Do not guess a heading or apply a rule that all short-numbered lines start new paragraphs. Visually confirmed excerpt transitions can become narrowly scoped controls; general automatic handling needs further evidence.

## Acceptance boundaries

The next experiment should compare the same 28 source-bound candidates before and after a generic repair, while separately preserving the existing four/eight structural cases, the 75 authored units, full byte accounting and all fixed staff/original question receipts. Known negatives above must be chosen before results. A lower maximum unit size is not the pass condition; correct source roles, complete local passages and honest unresolved fragments are.

No source, parser, semantic profile, projection, frozen context or previous result was changed by this review. There were no network, acquisition or model calls. Source instructions visible in historical letters were read as evidence and were not executed. Specialist review, current law and benefit answerability remain outside this structural triage.
