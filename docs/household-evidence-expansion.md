# Household and care-home evidence expansion

This is a **model-authored research proposal**, prepared on 20 September 2026. It is not an official Department for Work and Pensions (DWP) interpretation, a current-law assurance or a decision about anyone’s benefit. No human or specialist approval is claimed.

The increment addresses staff questions 012, 013, 014, 017, 018 and 020. It also supplies six missing directed candidate paths for questions 005, 020, 024 and 025. The source pages were already captured; the new work identifies their relationships and preserves the conditions needed to interpret them.

## What changed and why

The **Decision makers’ guide (DMG)** is DWP staff guidance. A paragraph’s heading and neighbouring paragraphs can restrict what its words mean. Two fixed-evidence model trials failed to carry the heading above DMG 78088 into their claims: **“Claimants who have no partner (including self-funders)”**. The PDF’s page layout was visually checked as well as its extracted text. The new concept and relationship explicitly retain that qualification.

The source-backed paths distinguish the following branches. They guide investigation; they do not select a branch for a real claimant.

| Question or branch | Source to inspect | Important condition retained |
| --- | --- | --- |
| What counts as a couple or household? | DMG 77013, 77102; chapter 77 PDF pages 7 and 19 | A shared building is not necessarily a shared domestic establishment. |
| One partner moves into a care home permanently | DMG 77117, 77128; chapter 77 pages 21 and 24 | The one-partner branch changes household treatment. The other conditions for an award still need checking. |
| Both partners live permanently in a care home | DMG 77121, 77128–77131; chapter 77 pages 23–25 | Decide household membership on the facts. The seven factors are non-exhaustive; no one factor decides the matter. |
| Severe-disability addition, no partner | DMG 78034–78036, 78055–78057, 78077–78080, 78088; chapter 78 pages 11–12, 15, 21–23 and 25 | Qualifying-benefit payment, residence and caring-payment conditions and their exceptions all matter. Self-funding alone is insufficient. |
| Severe-disability addition, partner | DMG 78045–78050; chapter 78 pages 12–14 | Lower-rate and higher-rate branches have their own conditions, including the hospital qualification. Paragraph 78088 is not a substitute for them. |
| Temporary care-home stay | DMG 78084–78086 and the continuing example; chapter 78 pages 24–25 | Household treatment may continue; more than 28 days with DLA payability ceasing requires a review. It is not a universal end to Pension Credit after 28 days. |
| Housing costs | DMG 78240–78242, 78254–78257, 78270; chapter 78 pages 53–58 | The exclusion concerns claimants in a care home; its temporary-absence exception does not establish payment of care-home fees. A housing-cost additional amount is separate from the whole award. Trial stays and longer temporary absences have different duration, intention-to-return and unlet-home conditions. |
| Mixed-age couples | DMG 77035, 77140–77184; chapter 77 pages 15–16 and 26–30; DMG memo 04/24 pages 2 and 5 | The general exclusion has protected-award and migration exceptions, with dates and prior-award requirements. |
| Scottish disability and carer dependencies | DMG memos 02/25 page 5, 06/25 pages 3 and 9, 01/26 page 3 | Qualifying benefits and carer definitions are amended on stated dates. The memoranda do not make every benefit name interchangeable. |

A **component** is one part of an award. Pension Credit’s Guarantee Credit, Savings Credit, severe-disability additional amount and housing-cost additional amount are not interchangeable. **Payability** means whether money is payable; **entitlement** means meeting the relevant entitlement rules. A person’s underlying entitlement to another benefit need not prove actual payment, which can matter to a different award.

### Mixed-age protection is a conditional route

A mixed-age couple has one member below and one at or above the relevant pension age. The captured DMG 77035 distinguishes new claims from 15 May 2019 and protection associated with awards on 14 May 2019. Memo 04/24 paragraphs 15–17 adds a route for specified protected couples sent a migration notice: it names a three-month period following the end of the relevant award. Its introduction gives 8 June 2024 as the effective date of the amendments. This does not establish a general right for any mixed-age couple.

The new path from Pension Credit to this conditional concept reaches DMG 77140, which the previous profile could not reach from its resolved concepts. It still leaves the **Advice for decision making (ADM)** counterpart, statutory versions and individual facts unresolved.

### Dated Scottish-benefit dependencies

The authored concept names Pension Age Disability Payment (PADP), Scottish Adult Disability Living Allowance (SADLA) and Carer Support Payment (CSP), with the exact memorandum pages. The source states dates of 21 October 2024, 21 March 2025 and 15 March 2026 respectively for the particular changes described. Those are source statements about changes, not inferred publication dates.

Memo 01/26 paragraph 5 says “carer support component”; paragraph 6 uses “carer support payment component”. The source wording is preserved. The model has not silently corrected the difference or decided its legal effect.

## Other missing paths and neutral Income Support

Six candidate pages previously had no directed route from their question’s resolved concepts. New `skos:related` associations supply investigation paths:

| Staff case | Path | Boundary |
| --- | --- | --- |
| 005 | Additional benefits → Carer’s Allowance → DMG 60025 | A separate set of caring, work, age, education and residence conditions; State Pension receipt alone is insufficient. |
| 005 | Additional benefits → Attendance Allowance → chapter 61 PDF page 5, with page 4 | Pension age, disability conditions and competing benefits require separate checks. |
| 020 | Pension Credit → mixed-age conditions → DMG 77140 | General entitlement requires the exceptions and migration memo too. |
| 024 | Industrial Injuries Disablement Benefit (IIDB) → income → DMG 85091 | The passage concerns Pension Credit income assessment, not automatic entitlement to an IIDB supplement. The list’s continuation is selected. |
| 025 | IIDB → benefit interaction → DMG 17085–17086 | Read both pages of the table and match its component and adjustment direction. IIDB, Constant Attendance Allowance and Unemployability Supplement are not interchangeable. |
| 025 | IIDB → Reduced Earnings Allowance → DMG 71748–71754 | The cited branch concerns retirement by 5 April 1987. Other cohorts have separate rules; it does not prove that IIDB stops at pension age. The continuation is selected. |

The neutral Income Support concept uses DMG 20002 and 20022, including the latter’s mixed-age Note 2. Only its broad aliases are moved from the previous custody-specific concept. That concept’s identifier, meaning and evidence remain intact. The alias `IS` remains case-sensitive, so the ordinary word “is” does not resolve to Income Support.

A `skos:related` edge means a proposed conceptual association. It does not assert legal causation, automatic entitlement, specialist approval or exhaustive coverage. The author and source evidence remain explicit.

## Provenance and reproduction

Authoring lives in [concepts.yamlld](../domain-profile/staff-semantic/concepts.yamlld) and [profiles.yamlld](../domain-profile/staff-semantic/profiles.yamlld). The compiler reads exact frozen page text, checks document and extraction hashes, binds local page routes and records the exact source page’s text hash. It does not fetch current web content. Added conditional text is labelled `model-derived`; page text remains machine extraction of the identified official source.

All pages listed here are **one-based PDF pages**, not paragraph numbers or printed page labels. Original capture times remain in the acquisition inventory. The inventory does not declare a publication date for these attachments. It would be misleading to use the capture date as their publication or legal commencement date. The chapter 71 pages carry a February 2019 amendment footer; their historic retirement branches remain historic.

The following source identities bind this authoring review. Full source URLs, page locators and exact page-text digests are emitted by the normal semantic compiler into its catalogue; the table below additionally pins the source document and extraction files used for this review.

| Document | Source PDF SHA-256 | Extracted-pages SHA-256 |
| --- | --- | --- |
| [dmg-memo-01-26-0605724317](https://assets.publishing.service.gov.uk/media/69d8f55d96c86b751317022e/dmg-memo-01-26.pdf) | `3f9046be5c3e80ca1e96cf59e5b648a358d07cf0ede104bd1d91daf785887db7` | `14de5319b76d1d512343dac8e9273fea16331cd6a02f0c555b8b84fc8d8fede3` |
| [dmg-memo-06-25-5fee4f859a](https://assets.publishing.service.gov.uk/media/67ffaac1ed87b816085467a8/dmg-memo-06-25.pdf) | `006a34df1aa517d8441cb77ada09bc4376e6876c2293130420de039ecf4505da` | `b760e928b19f28460b7ebe877e347aa8bc48f2bb048cd3ebc47254ef7dba4683` |
| [dmg-memo-02-25-e03b36ce3e](https://assets.publishing.service.gov.uk/media/67b72f6978dd6cacb71c6aa6/dmg-memo-02-25.pdf) | `33ca59d7b36288d35b50242927aa4c8a2921b28eb78922bdf74a3a5983fdab4c` | `1803b26fbd5f5536dae404d87eb5598f906b0aa1ad1f040de40802f0da133314` |
| [dmg-memo-04-24-282c3cef22](https://assets.publishing.service.gov.uk/media/66867768899a6f92e5d9ccf0/dmg-memo-04-24.pdf) | `35741a2aae92c4082f3cf9fe493674d3c33d998bdf9ecd8bc40a3014edb4ae75` | `96a341849256210150e02de5b6a8d71808a501e7a73733e93c0e1402191a239b` |
| [dmg-vol3-ch17](https://assets.publishing.service.gov.uk/media/62d7b8d5d3bf7f2865c6fe43/dmgch17.pdf) | `ce6967960168b301ae0b454df6824017202f6d3f6a14282a7ef0d4778bdac19a` | `c00f0acadb11047d22fe6c046a756a164cc7be254aaebfb91470f2f38201af99` |
| [dmg-vol4-ch20](https://assets.publishing.service.gov.uk/media/67ffaf91694d57c6b1cf8e0e/dmgch20.pdf) | `0474580014a697c47370992feee115d49c80b105b9c43270bf89afff0e4b0aa5` | `ed007251fa43ff9c63f5116f603798f2279c84006af8539bbbfd50194ab0ab56` |
| [dmg-vol10-ch61](https://assets.publishing.service.gov.uk/media/695ba618295a95414df21af4/dmg-ch-61.pdf) | `884dc79907770bd9e178fe4122c0b7d404697f4ccc882b067e9220b34a0f002a` | `23b4405d725de2fde124df29a8c753b9fcb7530405c83d588bd321e1e83226cc` |
| [dmg-vol11-ch71](https://assets.publishing.service.gov.uk/media/5d11f8c6e5274a065e721738/dmgch71.pdf) | `e001c101fb7be9bc739a8a5b9c1281637a93f34a099658e7dafef6fbb2b5d4f5` | `1414e514cf78c7a2e0a3ce66e2d88727d3fda28f764fd2e8654361dc569356d6` |
| [dmg-vol13-ch77](https://assets.publishing.service.gov.uk/media/68401a731d85c6606009cce4/dmgch77.pdf) | `0528f2fb95ac3bd71bdff0d91cdaba5df76ab4260396ca99608c840004ff5708` | `f7c34c30310a5e1f4700fb00b291e2bdec89554a89d4c244a9762c16c7448f19` |
| [dmg-vol13-ch78](https://assets.publishing.service.gov.uk/media/69e10327f5069cdc54868955/dmg-Ch-78.pdf) | `d5e17de1d343fc6a6498089897b222a4989914fa53f85af9ddc8c9c05471e2b8` | `f90fb5e92c5aebf4c07fb3383ca8bc0bb1ded55448949d987ed87e360c6b4894` |
| [dmg-vol14-ch85](https://assets.publishing.service.gov.uk/media/690b7db588a98da87e292365/dmg-ch-85.pdf) | `fe6fe79a4ff52271d6edf97af6b01ebd4290867b30d6288c38eb5e3a6d613c74` | `5b06b8fe3c59d46f5943d6c27006840e324bdca152086ed38e223e4385ea53ee` |

## What remains open

All 203 existing obligations remain open: 43 evidence-closure obligations and 40 each for applicability, legal versions, independent review and question scope. Six household profile descriptions are more specific; none has been removed or marked complete.

This increment does **not** close:

- the payment/cessation rules for every disability benefit and every public, private or mixed care-funding arrangement;
- the applicable statutory text, amendments, commencement, jurisdiction and cited judgments, including the household cases;
- the ADM counterpart and all cross-references in the mixed-age and migration rules;
- complete financial aggregation, rates and all Guarantee Credit or Savings Credit conditions;
- the relevant facts or the intended scope of “all scenarios”;
- independent specialist acceptance of the proposed meanings and evidence requirements.

The separate legal-body work can make statutory passages inspectable. Acquisition by itself does not close legal applicability or the need for independent review.

## Validation boundary

Run the focused source and authoring controls with the repository’s locked environment:

```sh
uv run --locked python -m unittest discover -s scripts -p test_household_semantic.py -v
```

The nine controls cover the no-partner heading, one/both-partner distinction, whole-page continuations, dated migration exception, Scottish component-wording discrepancy, case-sensitive `IS`, six new directed paths, exact frozen hashes and preservation of open obligations. They are development controls, not independent answer-accuracy or specialist-approval tests.

The authored expansion produces an index larger than the previous 4 MiB consumer limit. Whole qualifying source pages must be preserved. Integration therefore requires an explicitly versioned larger base-index bound with consumer regressions, or another governed projection; a cap bypass used only for in-memory inspection is not evidence of a passing consumer. No frozen outputs or original model-trial inputs are changed by this authoring handover.
