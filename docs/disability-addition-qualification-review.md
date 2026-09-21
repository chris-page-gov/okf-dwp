# Disability-addition qualification support

21 September 2026. **Model-authored source review and bounded implementation; not specialist acceptance, current legal advice or an entitlement decision.** This increment changes authored interpretations and evidence requirements. It does not change the captured manuals, legal acquisitions, historical trial packages or public observations.

## What changed and why

The previous no-partner definition said that DMG 78055–78057 distinguished actual
payment from underlying entitlement. That compressed statement could be read as
a cash-payment test for every qualifying disability benefit. The captured guidance
is more specific:

- **DMG 78057** concerns Carer’s Allowance (CA) or Universal Credit (UC) including
  the carer element, paid for caring for the claimant or partner. It says this
  must actually be in payment before it affects the Pension Credit additional
  amount. The transitional-protection qualification in 78035–78036 remains relevant.
- **DMG 78060** treats specified disability benefits as received for particular
  periods before an award is made but in respect of which it is awarded, or with
  payment in lieu of an award. It does not say every pending or underlying
  entitlement qualifies. The captured source specifies that the payment-in-lieu
  period is not covered by an award.
- **DMG 78060’s separate patient provision** expressly concerns a claimant who
  has a partner. Its over-28-days treatment must not become a universal no-partner
  or temporary-care-home rule. Its final provision treats CA or UC including the
  carer element as not received before the award is first paid.

The complete 78060 paragraph spans **Chapter 78 PDF pages 16 and 17**. Both were
already captured in the full corpus but absent from the smaller semantic index.
They are now selected as whole-page evidence. Page 17 keeps its actual first-payment
wording as the acquisition anchor; the producer does not invent a repeated
`78060` paragraph number on that page.

**DMG** means the Department for Work and Pensions’ *Decision makers’ guide*.
An **additional amount** is a component of Pension Credit, not necessarily the
whole award. A **dependency** here means evidence that must be inspectable with
an authored statement; it does not mean a legal rule has been found applicable.

## Two existing concepts with different jobs

No new concept or ontology predicate was needed. The existing identifiers, types,
aliases and unreviewed authority remain in place.

### Small overview

`staff-domain/severe-disability-addition` is now a navigation and identity overview:

> Navigation to the Pension Credit additional amount for people who are severely disabled. The captured guidance identifies separate no-partner and partner branches in DMG 78034 and 78045. The permanent-care-home paragraph 78088 is headed Claimants who have no partner (including self-funders) and requires all its conditions to be satisfied. This additional amount is distinct from the Severe Disablement Allowance benefit described in DMG 57001. This overview does not set out the full qualifying conditions or a consolidated current-law rule.

Its four required pages support only those limited statements. It does not
require the detailed no-partner, partner, Scottish-memo or legacy-benefit concept.
For example, page 12 establishes the existence of the partner branch; explaining
that branch’s conditions would also require its later pages. The overview does
not promise that fuller explanation.

**SDA** remains ambiguous between Severe Disablement Allowance and informal
shorthand for the Pension Credit severe-disability additional amount. Both
case-sensitive aliases remain. Neither meaning is silently selected.

### Bounded no-partner explanation

`staff-domain/no-partner-disability-addition` now says:

> Bounded reading of the captured lower-rate branch for a claimant with no partner. DMG 78034–78036 set receipt, residence and caring conditions and the stated transitional-protection exception. In DMG 78057, Carer’s Allowance or Universal Credit including the carer element, in respect of caring for the claimant or partner, must actually be in payment before it affects entitlement to this additional amount. That is not a universal cash-payment test for disability benefits: DMG 78060 treats specified disability benefits as received for periods before an award is made but in respect of which it is awarded, or periods not covered by an award but with payment in lieu of an award, and treats CA or UC including the carer element as not received before its first payment. Its separate patient provision expressly concerns a claimant who has a partner and must not be transferred to a no-partner care-home case. Under the no-partner heading, DMG 78088 requires all conditions to remain satisfied; funding status alone does not settle them. Read these captured passages with the separate dated changes in memos 02/25, 06/25 and 01/26. This component does not consolidate those changes or determine every residence, ignored-person, funding or hospital rule.

This definition removes the earlier compressed account of ignored-person rules
and the first four weeks. Those sources remain available for separate conditional
investigation. A shorter definition does not make their detailed rules complete
or irrelevant to an eventual answer.

## Exact support groups

The [concept authoring](../domain-profile/staff-semantic/concepts.yamlld) uses
the existing `required_source_ids` field. The producer verifies that every target
belongs to the concept’s captured source selection, then emits the existing
Dublin Core `dcterms:requires` relationship with model-derived, unreviewed status.

| Concept | Required whole-page evidence |
| --- | --- |
| Overview | `page/78/0011`, `page/78/0012`, `page/78/0025`, `page/dmg-vol10-ch57/0005` |
| No-partner component: chapter | `page/78/0011`, `page/78/0012`, `page/78/0015`, `page/78/0016`, `page/78/0017`, `page/78/0025` |
| No-partner component: dated memos | `page/dmg-memo-02-25-e03b36ce3e/0005`, `page/dmg-memo-06-25-5fee4f859a/0003`, `page/dmg-memo-06-25-5fee4f859a/0009`, `page/dmg-memo-01-26-0605724317/0003` |

Each page identifier has the stable prefix
`https://chris-page-gov.github.io/okf-dwp/id/`. Page numbers are one-based PDF
pages, not paragraph numbers. The overview requires **four pages**, the
no-partner component **ten**, and their union contains **eleven distinct pages**.

There are **14 new support relationships**, giving **29** alongside the existing
15 household, housing-cost and temporary-residence relationships. Each new link
goes directly to evidence, so the overview cannot create a dependency cycle or
force every detailed branch into its own required context.

Ordinary `dcterms:references` and `skos:related` relationships remain navigation
unless an explicit dependency is declared. The no-partner record’s existing
references to pages 21–23 and the wider Scottish-memo concept remain available;
they are not all converted into requirements.

## Dated changes and provenance

The four memo pages are required alongside the no-partner receipt explanation
because known changes are already available. They are not a silently consolidated
rule or a universal list of equivalent benefits:

- **Memo 02/25, page 5, paragraphs 13–15:** Pension Age Disability Payment (PADP),
  its role in the meaning of “AA”, qualifying benefits and ignored-person rules;
  the source states **21 October 2024**.
- **Memo 06/25, page 3:** introduction and source-stated **21 March 2025** date
  for Scottish Adult Disability Living Allowance (SADLA) changes.
- **Memo 06/25, page 9, paragraph 30:** the Pension Credit qualifying-benefit
  change for the claimant or applicable partner. Other housing-cost and
  polygamous-marriage material on that whole page is not thereby adopted into
  this definition.
- **Memo 01/26, page 3, paragraph 5:** the source-stated **15 March 2026** Carer
  Support terminology change. Paragraphs 5 and 6 use different component wording;
  the exact text is preserved, not reconciled into a fabricated synonym.

The [captured Chapter 78 PDF](https://assets.publishing.service.gov.uk/media/69e10327f5069cdc54868955/dmg-Ch-78.pdf)
has SHA-256 `d5e17de1d343fc6a6498089897b222a4989914fa53f85af9ddc8c9c05471e2b8`.
The [page extraction](../source/pages/dmg-vol13-ch78.json) has SHA-256
`f90fb5e92c5aebf4c07fb3383ca8bc0bb1ded55448949d987ed87e360c6b4894`.
Acquisition was `2026-09-15T14:21:01Z`; the retained HTTP Last-Modified observation
was `2026-04-16T15:41:27Z`. Neither becomes legal commencement or assurance of
current applicability. The [earlier component review](carehome-component-dependency-review.md)
retains the memo and Chapter 57 PDF/extraction fingerprints and source dates.

| Added semantic evidence | Actual anchor | Exact text SHA-256 |
| --- | --- | --- |
| `page/78/0016` | `78060` | `d460401ebba54c108a6211f3e2eaa02e8dffb75177de1efacc17b70b4996f293` |
| `page/78/0017` | `which the award is first paid` | `8b22b67c0956490c0b399c262554da6cd8a8e781875f497b72fc42d53c89b706` |

These are exact whole-page machine extractions with source locators and hashes.
They remain normalised evidence with derived authority, not human-reviewed text.

## Staff 012 and 013: inspect a possible branch

The [task-profile authoring](../domain-profile/staff-semantic/profiles.yamlld)
adds the overview and no-partner component alongside the existing household and
housing-cost qualification concepts. Both profiles still start with exactly
`pension-credit` and `care-home`; no presumed no-partner fact becomes a trigger.

Their existing source-closure obligation labels now explicitly say:

> Conditional branch investigation only; inspecting the no-partner branch does not establish that the claimant has no partner.

The existing producer carries that warning into machine-readable requirement
limitations. Staff 013’s label also now says qualifying-benefit **receipt**, with
treated-as-receipt qualifications, rather than suggesting actual payment is the
only question. These are **two intentional label clarifications**. Every
obligation identifier, category and status remains unchanged; the obligation
objects as a whole are not claimed byte-identical.

Every new path begins at the already resolved care-home concept, follows its
existing `skos:related` relationship to the overview or no-partner component,
then a direct `dcterms:requires` relationship to the page. The producer does not
seed an intermediate concept merely to retrieve it.

Each profile now has **32 required identifiers and 33 paths**, including five
still-absent obligation identifiers. Its qualification support covers **22
distinct pages** across the four concept groups. Candidate identifiers, question
wording, recorded ambiguities and original triggers remain unchanged. All **203
obligations remain open** and all 40 profiles remain labelled insufficient.

## Verification and measured boundary

The locked environment and existing producer were used; no dependency or
producer/schema change was required:

```sh
uv sync --locked
uv run --locked python scripts/build_staff_semantic.py
uv run --locked python scripts/build_staff_semantic.py --check
uv run --locked python -m unittest discover -s scripts -p test_staff_semantic.py
uv run --locked python -m unittest discover -s scripts -p test_household_semantic.py
```

**35 staff controls and 11 household controls pass.** They check whole-page
hashes, an invented page-17 anchor rejection, the exact four/ten-page groups,
the 29-edge census, unchanged earlier evidence, receipt and patient qualifiers,
memo wording, directed paths from existing triggers, conditional-investigation
warnings, open obligations and the preserved `SDA` alternatives. The existing
housing wording test was aligned with the previously corrected “not being let
or sublet” wording; its meaning and evidence requirement were not weakened.

A direct probe of the existing Explorer validator accepts the generated index.
The resolver returns no resolved concept for `SDA` and exposes both candidates.
This checks identity and ambiguity handling; it is not a package-retention run.

Current semantic source: **903 records, 1,464 assertions, 51 authored concepts,
98 selected source pages, 29 support dependencies and two qualification profiles**.
The index is **4,683,061 bytes**, within the existing 8 MiB bound.
Snapshot: `dwp-staff-semantics-91e16565bd7c97e72f3b`.
Index SHA-256: `8aea634f7623a61475156a116fcebf2ae64cbb4b17507a731a7de73edee0ddd7`.

An independent read-only review verified the source qualifications, whole-page
bindings, acyclic support groups and conditional paths, and repeated all 46
controls successfully. This is agent review, not specialist acceptance.

Only the four semantic producer outputs were regenerated. Combined Reader
integration, new 256/512 KiB context-retention comparisons, publication and any
model-answer run remain separate work. Earlier observations
retain their original source and engine bindings.

## Still unresolved

- A detailed ignored-person explanation needs pages 21–24, including the
  twelve-week limit, close-relative qualifications, shared-lives restriction and
  complete example. The shorter definition does not provide that full rule.
- Detailed partner lower/higher-rate conditions need pages 12–14 and their
  receipt/hospital qualifications; the no-partner branch cannot settle them.
- Funding-specific AA/DLA/PIP/Scottish-benefit cessation, normal-residence facts,
  hospital routes, legal versions, territorial scope and transitions remain to
  reconcile. Source dates alone do not settle applicability.
- The inspected statutory-body overlay still lacks the complete relevant
  judgment and provision dependencies, including Schedule I paragraph 3 and
  R(IS) 11/98 for the detailed ignored-person material.
- A bounded package may still omit support. Any surviving summary must expose
  its missing dependencies; additional pages or model agreement cannot close
  the recorded evidence, scope, legal or specialist-review obligations.
