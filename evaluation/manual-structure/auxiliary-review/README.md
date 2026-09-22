# Reserved ranges and notice boundary review

This follow-on source review addresses a defect found in the complete 513-document
census: a reserved-number line or a short illustrative-examples notice could
continue as a structural label until the next recognised numbered paragraph,
absorbing an appendix, table or ordinary guidance. It is additional to the
original four-case then eight-case experiment, not a retrospective change to
those registered expectations.

## Evidence and sequence

1. The [earlier role-census leads](previous-role-census-leads.json) retain 132
   units over 4 KiB labelled reserved or document notice. The parent analysis
   measured 2,697,517 bytes labelled reserved and 840,594 labelled notice across
   the earlier complete corpus. These are classification counts, not legal or
   semantic completeness measures.
2. [Four registered source fixtures](registered-fixtures.json) bind original
   PDF/extraction identities, exact page offsets and expected short literals.
   They were recorded before the helper implementation. Their test-file hash
   names that initial fixture-only file, not the later expanded test suite.
3. The [literal-region census](literal-region-census.json) independently reads
   every frozen extraction and checks its hash. The bounded helper identifies
   **5,721 reserved-line regions containing 101,767 bytes** and **298 notices
   containing 32,097 bytes**. This read-only observation does not rebuild the
   corpus or certify the classification of the remaining text.
4. The [helper and integration review](helper-integration-review.json) records
   exact code hashes, the 13 passing helper controls, and the parent-reported
   ten parser controls. Original temporary receipt paths are preserved as
   historical metadata; the equivalent files are all in this directory.

The source-bound tests are in
[the auxiliary test module](../../../scripts/test_manual_auxiliary_structure.py).
The [helper](../../../scripts/manual_auxiliary_structure.py) ends a standalone
reserved range at its own line. It ends a notice at its own sentence or bounded
paragraph, with explicit uncertainty if the sentence is incomplete. The caller
retains all other original bytes for supported classification or unresolved
fallback. No source text is discarded or rewritten.

## Rendered source checks

The source review also inspected these four rendered pages from the frozen PDFs:

- [DMG chapter 67, PDF page 152](dmg67-152.png): `67956 - 67999` is a standalone line.
- [DMG chapter 67, PDF page 153](dmg67-153.png): Appendix 1 begins a table; it is not part of that reserved line.
- [DMG chapter 42, PDF page 112](dmg42-112.png): the illustrative-examples notice occupies two lines.
- [DMG chapter 42, PDF page 113](dmg42-113.png): Appendix 2 begins a separate memo.

The images are review aids derived from the already captured public DWP source,
not new acquisitions or official project interpretations. Source licensing and
exceptions remain in [the notice](../../../NOTICE.md).

## Boundaries and reproduction

```sh
uv run --locked python -m unittest discover -s scripts -p 'test_manual_auxiliary_structure.py'
```

The helper also records numbered memo candidates without accepting them as
paragraph boundaries. ADM memo 09/25 illustrates why caution is needed: both
main text and nested points can have the same PDF `P` tag, while some main
paragraphs are represented as `LI`. Here `P` means a source-declared paragraph
and `LI` a list item. Indentation and ancestry are observations, not enough to
establish a complete rule. These candidates never become events automatically.

[The artefact manifest](artifact-manifest.json) binds the retained evidence files.
The original failed classifications, source experiments and frozen projections
remain unchanged. The correction may increase explicitly unresolved material;
it does not establish legal applicability, complete semantic modelling or
specialist acceptance. Final rebuilt-corpus results are recorded separately.

## Further source finding: a wrapped reference is not a paragraph

Independent household source reading found `77161` ending a line with
`See DMG 77162 -`, followed by `77164 for further details.` on original chapter
77 PDF page 28. The second line continues the reference. The earlier parser
mistook it for a new paragraph, separating the following note and citation from
77161. The actual next standalone range is `77162 - 77169`.

The [source fixture](wrapped-reference-fixture-v2.json) retains the complete
expected 77161 passage. Its [original registration](wrapped-reference-fixture.json)
is also retained: one unused label in that first record incorrectly named the
next page's 77172. The corrected one-page expectation is 77161, 77170 and 77171;
the exact expected passage and source hashes did not change. The first
[boundary check failed](wrapped-reference-before-fix.json), while the
[post-repair check passes](wrapped-reference-after-fix.json) and reconstructs
all original page bytes. These expectations and parser implementation were
prepared concurrently; this is an independent regression, not an experiment
preregistered before all implementation.

The generic repair recognises an explicit manual or paragraph-reference range
ending on the preceding nonblank line. It does not encode these paragraph
numbers. Run the bounded source control with:

```sh
uv run --locked python -m unittest discover -s scripts -p 'test_manual_wrapped_reference.py'
```

[The follow-on manifest](wrapped-reference-artifact-manifest.json) binds these
additional receipts. The original auxiliary evidence manifest is unchanged.
