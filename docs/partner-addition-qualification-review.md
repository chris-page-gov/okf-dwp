# Partner disability-addition qualification support

21 September 2026. **Model-authored source review and bounded implementation;
not specialist acceptance, current legal advice or an entitlement decision.**
This increment uses already captured guidance. It changes one existing concept,
adds explicit evidence dependencies and makes four staff profiles inspect a
conditional branch. It acquires no new source and changes no historical receipt.

## What the component explains

The Department for Work and Pensions’ **Decision makers’ guide (DMG)** separates
the Pension Credit additional amount for severe disability into no-partner and
partner branches. An **additional amount** is a component of an award, not the
whole Pension Credit award. Having a partner does not by itself establish that
any disability addition is payable.

The existing `staff-domain/partner-disability-addition` concept now says:

> Bounded reading of the captured Pension Credit severe-disability additional-amount rules for a claimant who has a partner. DMG 78045–78047 set distinct lower-rate branches, and 78048–78050 address the higher rate. Their benefit, residence and caring conditions must be read together. DMG 78047's patient branch concerns the other partner being unable to receive the specified benefit because of being a patient for over 28 days; its remaining conditions continue on the next page. DMG 78050 restricts the higher-rate condition when either partner is treated as receiving benefit under the partner-patient provision in 78060(2), and directs consideration of the lower rate. It does not exclude every form of treated receipt. Read the separate CA/UC actual-payment qualification in 78057, in respect of caring for the claimant or partner, and the complete treated-receipt provisions in 78060, with the dated changes in memos 02/25, 06/25 and 01/26. This component does not establish that partner status persists after care-home admission, consolidate current law or calculate an award.

**CA** means Carer’s Allowance. **UC** means Universal Credit; its carer element
is an amount for caring circumstances. **Treated receipt** means that the source
expressly treats a benefit as received under specified conditions. It is not a
general rule that all pending or underlying entitlement is actual payment.

## Whole passages rather than isolated paragraph matches

| Captured passage | Qualification that must remain visible |
| --- | --- |
| DMG 78045, Chapter 78 PDF page 12 | The lower-rate branch includes both partners’ specified benefit receipt, residence conditions and caring payment for only one partner. |
| DMG 78046, pages 12–13 | A separate branch covers a specified receiving partner and a blind or severely sight-impaired partner, with residence and caring conditions. The benefit list and final conditions cross a page boundary. |
| DMG 78047, pages 13–14 | The other partner’s over-28-days patient condition does not replace the remaining residence and caring conditions, which continue on page 14. |
| DMG 78048–78050, page 14 | The higher rate is a partner branch. The source addresses both partners’ receipt, residence and caring conditions, then the specific partner-patient form of treated receipt and consideration of the lower rate. |
| DMG 78055–78057, page 15 | The actual-payment qualification concerns CA or UC including the carer element in respect of caring for the claimant or partner. It is not a cash-payment test for every disability benefit. |
| DMG 78060, pages 16–17 | The complete treated-receipt provisions include the award-period qualifications, separate partner-patient provision and first-payment provision for CA/UC. |

The captured 78046 and 78047 final caring conditions literally refer to the
partner receiving “AA” or DLA, although their preceding benefit lists are wider.
The whole pages retain that wording. This increment does not silently harmonise
those clauses or infer a consolidated benefit list. “AA” is the source’s
defined abbreviation associated with Attendance Allowance and specified
equivalents; the dated amendments still need reconciliation.

### A superscript is not a new subparagraph

The extracted page 14 text says `DMG 78060 2.1.`. Inspection of the captured PDF
rendering shows item **2**, followed by superscript footnote **1** and the sentence
stop. Footnote 1 cites regulation 6(5)(b). The authored definition therefore
describes **78060(2)**, the partner-patient provision. It does not invent a
subparagraph 2.1 or exclude every form of treated receipt in 78060(1).

This is a documented source-layout interpretation. The PDF and extracted text
remain unchanged, including the flattened superscript. The interpretation
remains model-derived and subject to specialist review.

## Exact ten-page support group

The [concept authoring](../domain-profile/staff-semantic/concepts.yamlld) uses
the existing `required_source_ids` field. The unchanged producer verifies each
target against the concept’s selected source evidence, then emits an existing
Dublin Core `dcterms:requires` relationship. Here a dependency means evidence
that must accompany an explanation, not a legal finding of applicability.

| Group | Required whole-page identifiers | Purpose |
| --- | --- | --- |
| Partner branches | `page/78/0012`, `page/78/0013`, `page/78/0014` | Heading, complete lower-rate branches, higher-rate conditions and patient qualification. |
| Receipt qualifications | `page/78/0015`, `page/78/0016`, `page/78/0017` | Actual caring-payment scope and complete treated-receipt provisions. |
| Memo 02/25 | `page/dmg-memo-02-25-e03b36ce3e/0005` | Pension Age Disability Payment changes; the source states 21 October 2024. |
| Memo 06/25 | `page/dmg-memo-06-25-5fee4f859a/0003`, `page/dmg-memo-06-25-5fee4f859a/0009` | Scottish Adult Disability Living Allowance change, the source-stated 21 March 2025 date and the claimant/partner qualifying-benefit provision. |
| Memo 01/26 | `page/dmg-memo-01-26-0605724317/0003` | The source-stated 15 March 2026 Carer Support change. |

Every identifier has prefix `https://chris-page-gov.github.io/okf-dwp/id/`.
Page numbers are one-based PDF pages. The page 17 selection uses the actual
anchor `which the award is first paid`; it does not invent a repeated paragraph
number on that continuation page.

All ten pages were already present in the semantic index. This increment adds
seven concept-to-page references and ten required-support relationships. The
small severe-disability overview still requires only its existing four pages;
it does not require this partner component or every detailed branch. All ten
new dependencies end at evidence records, so they do not create a dependency
cycle between concepts.

The memo pages remain separate dated evidence. In particular, memo 01/26
paragraphs 5 and 6 use different component wording. Those literals are not
merged into an invented synonym. Other subjects on a whole page are available
for inspection, without becoming statements made by this component.

## Conditional navigation and staff-question scope

One new, evidence-backed `skos:related` relationship connects `care-home` to
`partner-disability-addition`. It says that a care-home enquiry may require
investigation of this branch after household status is examined. It explicitly
does not establish continuing couple status or satisfaction of the conditions.
Its provenance includes the care-home page 78/25 and the partner passages.
It is a navigation link, not an `appliesTo` assertion.

The [profile authoring](../domain-profile/staff-semantic/profiles.yamlld) makes
the following bounded additions:

| Staff cases | Existing triggers | Added investigation and limit |
| --- | --- | --- |
| 012 and 013 | Pension Credit and care home | Inspect the partner component alongside the existing household, housing-cost, overview and no-partner groups. This does not decide whether partner status persists after admission. |
| 014 and 017 | Pension Credit and partner | Their existing evidence scope already names rate/component effects. Inspect this partner component conditionally; qualifying disability-benefit receipt, residence and caring facts remain unknown. |
| 018 | Partner and care home | No profile change. The unnamed benefit and “all scenarios” request remain unbounded; this addition does not turn that question into a complete scenario matrix. |

Paths start at an actual existing trigger, follow `skos:related` to the partner
component, then `dcterms:requires` to each of the ten pages. The producer does not
add a partner seed to the care-home questions. Removing the care-home navigation
edge causes compilation to reject the now-unreachable qualification group.

Staff 012 and 013 each now have **35 required identifiers and 44 declared paths**,
including five still-absent obligation identifiers. Their support covers **24
distinct pages**; only pages 78/13 and 78/14 are additional to their previous
22-page group. Staff 014 and 017 each have **21 required identifiers and 16
declared paths**, with ten partner-support pages alongside their original
candidate evidence and five absent obligations.

The existing source-closure obligation label is clarified for each of these four
cases. These are **four intentional label changes**. Every obligation identifier,
category, status and resolution remains unchanged. All **203 obligations remain
open** and all 40 profiles remain insufficient. Original question wording,
triggers, candidate identifiers and ambiguities are unchanged; Staff 018’s full
authored profile is unchanged. Obligation objects as a whole are not claimed
byte-identical because their four labels changed.

## Provenance and version boundaries

The [captured Chapter 78 PDF](https://assets.publishing.service.gov.uk/media/69e10327f5069cdc54868955/dmg-Ch-78.pdf)
has SHA-256 `d5e17de1d343fc6a6498089897b222a4989914fa53f85af9ddc8c9c05471e2b8`.
The [whole-page extraction](../source/pages/dmg-vol13-ch78.json) has SHA-256
`f90fb5e92c5aebf4c07fb3383ca8bc0bb1ded55448949d987ed87e360c6b4894`.
Capture was `2026-09-15T14:21:01Z`; the retained HTTP Last-Modified observation
was `2026-04-16T15:41:27Z`. These are source observations, not legal commencement
or assurance of current applicability.

| Complete page | Text SHA-256 |
| --- | --- |
| `page/78/0013` | `57ab804200c6760c6172599735fb2b6fcb5b4826c77d63d3659a1ed5efda06cd` |
| `page/78/0014` | `0cff3b76580573871f27394292919508c2d937c6a5c7da0abba0a4e6c81a9232` |

The [earlier disability review](disability-addition-qualification-review.md)
records the receipt-page fingerprints and dated memo boundary. Generated
[catalogue bindings](../evaluation/semantic-expansion/catalogue.json) retain
the PDF, extraction and literal hashes for all selected pages. Evidence remains
normalised machine extraction with derived authority. Definitions, navigation
and support relationships remain model-derived with unreviewed, model-assisted
authority. All **520 pre-existing evidence records** are identical to the
base commit `8ea4465a4cb5a867d82c87e635f2ef1d1df18d8a`.

## Verification and integration boundary

The existing locked environment and producer were used. No schema, producer or
dependency change was needed:

```sh
uv sync --locked
uv run --locked python scripts/build_staff_semantic.py
uv run --locked python scripts/build_staff_semantic.py --check
uv run --locked python -m unittest discover -s scripts -p test_staff_semantic.py
uv run --locked python -m unittest discover -s scripts -p test_household_semantic.py
```

**38 staff controls and 14 household controls pass.** They cover the exact support
group, source hashes, page continuations, restricted patient-reference meaning,
actual caring-payment scope, existing triggers, conditional profile warnings,
the negative unreachable-route control and preservation of open obligations.
The small overview and the existing ambiguous `SDA` alternatives remain intact.

The semantic producer yields **903 records, 1,482 assertions, 51 authored
concepts, 98 selected source pages, 39 support dependencies and four qualification
profiles**. The index is **4,740,429 bytes**, within its existing 8 MiB bound.
Snapshot: `dwp-staff-semantics-10abede694e3ed57e118`.
Index SHA-256: `685353567b90db880f1bd1ba33b57ae7ecc430673332ce69e47512a9ae606886`.

Only the four semantic producer outputs were regenerated. Combined Reader
integration, new context-retention comparisons, publication and model-answer
trials are separate work. Earlier 903-record observations bind an earlier
source identity and must not be presented as measurements of these declarations.

## What this does not complete

- Residence and ignored-person rules are referenced by these passages. Detailed
  branches, including pages 18–24, are not made universally required or claimed
  complete here. The ignored-person proposal remains deferred.
- The existing statutory overlay contains regulation 6 and Schedule I paragraphs
  1 and 2 of the State Pension Credit Regulations. Links and acquired bodies do
  not reconcile the relevant version, all amendments or the applicability of
  their subprovisions. The additional residence material also depends on legal
  and judgment evidence outside this bounded support group.
- Hospital and funding-specific cessation rules, household facts, territorial
  scope, benefit-specific qualifications and memo wording remain to reconcile.
- Ten declared support pages do not guarantee their retention in a bounded
  assembled package. Actual 256/512 KiB delivery must be measured against the
  newly frozen source and engine. Missing support must remain visible.
- No source-closure, legal, factual-scope or specialist-review obligation is
  closed by this increment or by passing the engineering tests.
