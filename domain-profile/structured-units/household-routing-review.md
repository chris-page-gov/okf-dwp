# Household and Housing Benefit selection review

This is a source-read proposal for three supplied question occurrences:

- `staff-011`: How does Housing Benefit impact Pension Credit?
- `staff-014`: What is the impact of someone’s partner on their Pension Credit?
- `staff-017`: What difference to Pension Credit does having a partner make?

The last two questions share a bounded introductory profile. This slice does not
claim to answer the separate `staff-018` request for every permanent-care-home
scenario. It creates no benefit rules, claimant decision or specialist approval.

## What was read and selected

The [authoring file](household-routing.yamlld) selects 15 complete existing unit
records from frozen DMG chapters 77 and 85. DMG means the Department for Work and
Pensions' Decision makers' guide. Selection preserves the original PDF and text
hashes, every recorded source span, machine boundary status and open obligations.
It does not promote those boundaries to human-reviewed units. No source text was
rewritten and no record was selected merely because it overlapped a candidate
page.

| Source paragraphs | Purpose of the bounded selection | Limit that remains visible |
| --- | --- | --- |
| 77013, 77015, 77102 | Couple, partner and household meanings; the separate-households example | Living in one dwelling does not alone establish one household. Case facts remain unspecified. |
| 77100, 77115 | Why household membership affects the amount, income, earnings and capital; possible members | Membership and the treatment of each resource need separate evidence. |
| 77117, 77121–77123 | Full introductory exclusions, the both-partner permanent-residence distinction, and the exception to an absence exceeding 52 weeks with both examples | Further absence, care-home and domestic-establishment branches are not made complete by these selected passages. |
| 77035, 77140, 77350 | Different mixed-age definitions, source dates, savings notes and Savings Credit restrictions | The definitions apply to different purposes. Dated protections, migration and memo effects are not reconciled here. |
| 85016 | Partner-income attribution, including the express immigration-control qualification | This does not establish every income, capital or component effect, or an award amount. |
| 85302, 85230 | Housing Benefit in the PC income assessment and the claimant-landlord route | This is not the reverse question of PC entitlement creating HB entitlement, or complete landlord-income treatment. |

PC means Pension Credit; HB means Housing Benefit. The source abbreviation
**PSIC** means a person subject to immigration control. Its appearance identifies
an evidence branch to review, not a conclusion about anyone's immigration status.

The complete selected units retain notes, conditions, examples and citations.
For context, the review also read DMG 77118–77120, 77128–77130, 77141,
77150–77161, 77170–77184 and 85231. These are leads and qualifications, not
silently added mandatory evidence or closed dependencies.

## Source defects and open branches

Two findings must remain separate from any interpretation of the law:

- DMG 77117, point 1.2, directs its exception for an absence exceeding 52 weeks
  to 77119. The captured 77119 concerns death-related temporary absence, while
  77122 expressly addresses the 52-week exception. The proposal retains this
  source-reference discrepancy as an open obligation. It does not repair the
  citation or decide the legal effect.
- On PDF page 28, the reference from 77161 to `77162 - 77164` wraps across lines.
  The earlier machine parser mislabelled the second line as paragraph 77164.
  The [independent source regression](../../evaluation/manual-structure/auxiliary-review/README.md#further-source-finding-a-wrapped-reference-is-not-a-paragraph)
  retains the failure and the generic repair. No false 77164 body is selected here.

The source names ADM chapter E2 and dated memos in the mixed-age routes. ADM is
the separate Advice for decision making manual. Finding a cited memo does not
establish its amendment effect, relevant date or applicability. Those dependencies,
the complete household branches, financial assessment and statutory sources remain
open. All existing staff-question obligations are preserved.

## Binding and activation boundary

Initial independent reading used the preserved unit catalogue at `9736d30c` while
the corrected producer ran. On 23 September 2026, all 15 selections were checked
against the stable 52,841-unit catalogue, snapshot
`dwp-structured-units-cb1770fc4dfc61ad4a87`, whose manifest SHA-256 is
`0c3545fb33f52cf3063cbc84fe64cc1586f6b102b4d6029e3687644c5ec116a3`.
Every complete-record hash and span remained unchanged. The check also verified
the frozen PDF and extraction hashes, each exact UTF-8 span and its hash, and
reconstruction of the selected record text using the producer's explicit newline
separator between source spans. The authoring file compiled in memory into two
profiles and 16 scoped assertions; no generated corpus was changed. Matching
paragraph labels alone were not used to rebind it.

The profiles require both PC and the relevant topic. The compiler and runtime
must enforce that conjunction on traversal as well as requirement activation.
A globally reachable edge from the generic partner or HB concept could otherwise
bring PC-specific evidence into another benefit's question. Before activation,
test at least PC with partner, PC with HB, a different benefit with partner, HB
without PC, and an unrelated unknown task. The profiles do not become complete
merely because their source records and paths are retained.

This file proposes source selection only. No source acquisition, model trial,
corpus rebuild, runtime activation, public deployment or specialist acceptance
was performed by this review.
