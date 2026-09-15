# Full DMG semantic coverage workplan

Prepared on 15 September 2026. **Authored worklist, not execution results.** Content freeze: 24 September; seminar: 30 September.

The goal is a source-complete research bundle and a precise report of attempted semantic work. It is not a promise of a complete ontology, legally current rule system or specialist-approved benefit decisions. The [machine worklist](../../evaluation/full-dmg-coverage-plan.json) binds the frozen census and current authored inputs by SHA-256.

## Fixed denominators

| Work | Units |
|---|---:|
| DMG PDF source units | 331 |
| Direct publication groups | 11 |
| Listed substantive PDF units | 78 |
| Distinct substantive chapter numbers | 72 |
| Chapter source-grounding and boundary cases | 156 |
| Baseline journey / source-family cases | 14 / 22 |
| Enumerated cases before profile-specific negative mutations | 192 |
| Existing concepts / personas / stories / questions | 26 / 8 / 10 / 14 |

Chapter 7 is seven separate source units. Its parts must not overwrite one another under a single chapter key. The 78 substantive-file classification is based on publisher metadata; it is a worklist input, not a conclusion that every passage is current or usable. Existing concept descriptions remain source-discovery material unless separately developed and reviewed.

## Source-family work queues

Every one of the 331 PDFs has an explicit source-unit ID, official URL, acquisition task, research task and profile in the JSON. No source class silently disappears from coverage.

| Profile | PDFs | Required research outcome |
|---|---:|
| Listed substantive chapters | 78 | Paragraph/evidence coverage, term candidates, relationship proposals or reasoned abstention, dependencies and two chapter cases |
| Annexes | 4 | Establish substantive role, parent scope, tables/rates/date risks and source locators |
| Transitional chapters | 3 | Explicit transition cohorts, dates and unresolved applicability |
| Memos | 66 | Exact referenced chapters/provisions and applicability/incorporation state, or unresolved state |
| Amendment records | 151 | Change events and affected locators; never flatten into current chapter text |
| Change summaries | 15 | Administrative change evidence, distinguished from legal effective dates |
| Abbreviations and legislation reference lists | 3 | Candidate expansions and resolvable work/provision citations; no implied legal acquisition |
| Spare chapters | 11 | Inspect/account for source and any discrepancy; no invented concepts |

## Order and depth

All PDFs enter acquisition and source accounting. P0 prioritises common decision-making, evidence, appeals, international questions and the Pension Credit/pension boundary. P1 adds cross-benefit and operational comparisons. P2 completes the remaining specialist-benefit research queue. Priority changes order, not the denominator.

For each substantive source unit, complete RQ01–RQ08 and RQ09 where the JSON requires it:
- **RQ01:** Acquire/resolve exact PDF bytes and SHA-256; measure pages; retain original URL, source family, publisher dates and acquisition time. Record failed sources without fabricated text.
- **RQ02:** Segment contents, body paragraphs, examples, tables and footnotes with page/paragraph locators. Preserve raw extraction and mark uncertain boundaries; headings alone remain navigation.
- **RQ03:** Review candidate terms against body evidence. For each retain preferred label, aliases if evidenced, benefit/date/jurisdiction scope, definition or definition gap, evidence and unreviewed status. Resolve reuse of existing terms explicitly.
- **RQ04:** Review possible relationships using exact source passages. Retain direction, predicate meaning, rationale, conditions/exceptions, source role and evidence. A supported proposal or reasoned abstention closes the research task; no relationship quota forces an assertion.
- **RQ05:** Record source publication, revision, acquisition and stated effective dates separately, including precision. Inspect transitional text, old examples, memo changes and incorporation claims; unknown applicability remains unknown.
- **RQ06:** Extract explicit legislation, case-law, memo and cross-guide citations with exact citation strings and locators. Resolve work/provision/version separately; mark unacquired, ambiguous, broken or conflict states. Do not claim legal interpretation from a URL.
- **RQ07:** Author and execute one chapter source-grounding case and one boundary case, linked to existing persona/story/question routes. Separate deterministic checks, model outputs and specialist judgement.
- **RQ08:** Publish a source-unit coverage row with task state, counts, attempted areas, unresolved issues, evidence links and the reviewer type. Reconcile counts against the pinned 331-unit denominator.
- **RQ09:** Compare shared terminology only through scoped mapping candidates. Record DMG/ADM, legacy/New Style, Pension Credit/UC and territorial distinctions; do not infer equivalence or transfer a rule.

A research task can conclude that no supported relation was found. There is no numerical quota for new concepts or edges. A heading becomes a navigation entry; a concept definition needs body evidence, benefit/date/jurisdiction scope and an explicit review state. Use exact source identifiers and retain uncertain segmentation.

The existing four predicate definitions remain the current contract. General thematic association may use the documented SKOS relation. Do not apply the three capital-specific experimental predicates to other benefits merely because a heading looks similar. A new predicate requires an explicit definition, source evidence, inverse/direction decision and separate contract review.

## Complete substantive chapter worklist

The focus column contains research prompts inferred from titles, not validated terminology or approved definitions. Each row has two finite evaluation tasks and exact source-unit references in the JSON.

| Task | Priority | Source title | Candidate focus |
|---|---|---|---|
| `chapter-01` | P0 | DMG Vol 1 Ch 1: Principles of decision making and evidence | decision-making authority; evidence; burden and standard of proof |
| `chapter-02` | P0 | DMG Vol 1 Ch 2: Claims | claim; claim date; information supporting a claim |
| `chapter-03` | P0 | DMG Vol 1 Ch 3: Revision | revision; grounds; time limits |
| `chapter-04` | P0 | DMG Vol 1 Ch 4: Supersession, suspension and termination | supersession; suspension; termination; change of circumstances |
| `chapter-05` | P1 | DMG Vol 1 Ch 5: Work-focused interviews | work-focused interview; participation requirement; exceptions |
| `chapter-06` | P0 | DMG Vol 1 Ch 6: Making appeals and staying | appeal; staying; decision notice |
| `chapter-07-part-1` | P0 | DMG Vol 2 Ch 7 Part 1: Common subjects [070000 to 070699] | coordination; territorial scope; common international terms |
| `chapter-07-part-2` | P0 | DMG Vol 2 Ch 7 Part 2: AA, DLA and CA to dependency increases, and ESA [071700 to 072769] | AA/DLA/CA; dependency increase; ESA international boundary |
| `chapter-07-part-3` | P0 | DMG Vol 2 Ch 7 Part 3: Habitual residence and right to reside IS, JSA and SPC [072770 to 073779] | habitual residence; right to reside; IS/JSA/Pension Credit scope |
| `chapter-07-part-4` | P0 | DMG Vol 2 Ch 7 Part 4: Incapacity Benefit to Industrial Injuries Benefit [073780 to 075329] | Incapacity Benefit; industrial injuries; international scope |
| `chapter-07-part-5` | P0 | DMG Vol 2 Ch 7 Part 5: JSA to Retirement Pension [075330 to 076959] | JSA; Retirement Pension; international scope |
| `chapter-07-part-6` | P0 | DMG Vol 2 Ch 7 Part 6: SDA, SPC, WB/Bereavement Benefit and Winter Fuel Payments [076960 to 078059] | Pension Credit; bereavement; Winter Fuel Payment international scope |
| `chapter-07-part-7` | P0 | DMG Vol 2 Ch 7 Part 7: Offshore workers and Her Majesty's forces [078060 to 079999] | offshore worker; armed forces; territorial scope |
| `chapter-08` | P0 | DMG Vol 3 Ch 8: Payment of benefit and deductions from benefit | payment; deduction; payee |
| `chapter-09` | P0 | DMG Vol 3 Ch 9: Overpayments, offsets and recoverability | overpayment; offset; recoverability |
| `chapter-10` | P0 | DMG Vol 3 Ch 10: Evidence of age, marriage and death | age evidence; marriage evidence; death evidence |
| `chapter-11` | P0 | DMG Vol 3 Ch 11: Living together as husband and wife or as civil partners | household; living together; civil partnership |
| `chapter-12` | P1 | DMG Vol 3 Ch 12: Imprisonment | imprisonment; payment restriction; exceptions |
| `chapter-13` | P1 | DMG Vol 3 Ch 13: Incapacity for work | incapacity for work; evidence; assessment |
| `chapter-15` | P1 | DMG Vol 3: Ch 15: Earnings for non-income-related benefits | earnings; assessment period; non-income-related benefit scope |
| `chapter-16` | P1 | DMG Vol 3 Ch 16: Dependency increases | dependency; increase; relationship conditions |
| `chapter-17` | P0 | DMG Vol 3 Ch 17: Overlapping benefits | overlapping benefit; priority; interaction |
| `chapter-18` | P1 | DMG Vol 3 Ch 18: Hospital in-patients | hospital in-patient; duration; payment treatment |
| `chapter-20` | P1 | DMG Vol 4: Ch 20, JSA and IS, conditions of entitlement | JSA; Income Support; conditions of entitlement |
| `chapter-21` | P1 | DMG Vol 4 Ch 21: Jobseeker’s Allowance Labour market questions, special conditions for JSA(Cont) and jobseeking periods | labour market condition; jobseeking period; contribution-based JSA scope |
| `chapter-22` | P1 | DMG Vol 4 Ch 22: Membership of the family | family membership; couple; dependant |
| `chapter-23` | P2 | DMG Vol 4 Ch 23: Normal amount payable | normal amount; applicable amount; components |
| `chapter-24` | P2 | DMG Vol 4 Ch 24: Special cases | special case; exception; JSA/IS scope |
| `chapter-25` | P1 | DMG Vol 5 Ch 25: General rules on income | income; assessment period; attribution |
| `chapter-26` | P1 | DMG Vol 5 Ch 26: Employed earners | employed earnings; deduction; assessment |
| `chapter-27` | P1 | DMG Vol 5 Ch 27: Self-employed earners and share fishermen | self-employed earnings; share fisherman; calculation inputs |
| `chapter-28` | P1 | DMG Vol 5 Ch 28: Income other than earnings | income other than earnings; disregard; attribution |
| `chapter-29` | P1 | DMG Vol 5 Ch 29: Capital | capital; ownership; disregard |
| `chapter-30` | P2 | DMG Vol 6 Ch 30: Students, young claimants and their partners | student; young claimant; partner |
| `chapter-32` | P2 | DMG Vol 6 Ch 32: Trade disputes | trade dispute; participation; payment effect |
| `chapter-33` | P2 | DMG Vol 6 Ch 33: Payment questions | payment question; period; JSA/IS scope |
| `chapter-34` | P2 | DMG Vol 6 Ch 34: Sanctions | sanction; trigger; duration |
| `chapter-35` | P2 | DMG Vol 6 Ch 35: Hardship | hardship; conditions; evidence |
| `chapter-39` | P2 | DMG Vol 7 Ch 39: Social Fund payments | Social Fund; payment category; service boundary |
| `chapter-40` | P2 | DMG Vol 7 Ch 40: Winter Fuel Payments - pre winter | Winter Fuel Payment; relevant period; pre-winter scope |
| `chapter-41` | P1 | DMG Vol 8 Ch 41: ESA conditions of entitlement | ESA; conditions of entitlement; regime |
| `chapter-42` | P1 | DMG Vol 8 Ch 42: Limited capability for work and limited capability for work-related activity | limited capability for work; work-related activity; assessment evidence |
| `chapter-43` | P1 | DMG Vol 8 Ch 43: Membership of the household | household membership; couple; dependant |
| `chapter-44` | P2 | DMG Vol 8 Ch 44: Normal amount payable and components | ESA amount; component; phase |
| `chapter-45` | P1 | DMG Vol 8 Ch 45: IB, SDA and IS, claims and reassessment | reassessment; legacy benefit; transition |
| `chapter-46` | P2 | DMG Vol 8 Ch 46: ESA, Payment questions | ESA payment; period; restriction |
| `chapter-48` | P1 | DMG Vol 9 Ch 48: General rules on income | income; assessment period; ESA scope |
| `chapter-49` | P1 | DMG Vol 9 Ch 49: Earnings of employed earners | employed earnings; deduction; ESA scope |
| `chapter-50` | P1 | DMG Vol 9 Ch 50: Self-employed earners | self-employed earnings; assessment; ESA scope |
| `chapter-51` | P1 | DMG Vol 9 Ch 51: Income other than earnings | income other than earnings; disregard; ESA scope |
| `chapter-52` | P1 | DMG Vol 9 Ch 52: Capital | capital; ownership; disregard |
| `chapter-53` | P1 | DMG Vol 9 Ch 53: ESA –  WfI, WRA, sanctions and hardship, disqualification and advance awards | work-focused interview; work-related activity; sanction and hardship |
| `chapter-54` | P2 | DMG Vol 9 Ch 54: Special cases | special case; exception; ESA scope |
| `chapter-56` | P2 | DMG Vol 10 Ch 56: Incapacity Benefit | Incapacity Benefit; conditions; historical regime |
| `chapter-57` | P2 | DMG Vol 10 Ch 57: Severe Disablement Allowance | Severe Disablement Allowance; conditions; historical regime |
| `chapter-58` | P2 | DMG Vol 10 Ch 58: Widows Benefits | Widows Benefits; conditions; historical regime |
| `chapter-59` | P2 | DMG Vol 10 Ch 59: Bereavement support payment | Bereavement Support Payment; conditions; payment period |
| `chapter-60` | P1 | DMG Vol 10 Ch 60: Carer’s Allowance | Carer’s Allowance; care; overlapping benefit |
| `chapter-61` | P1 | DMG Vol 10 Ch 61: Attendance Allowance and Disability Living Allowance | Attendance Allowance; Disability Living Allowance; care and mobility |
| `chapter-62` | P1 | DMG Vol 10 Ch 62: Maternity benefits | maternity benefit; conditions; evidence |
| `chapter-63` | P2 | DMG Vol 10 Ch 63: Bereavement Benefit | Bereavement Benefit; conditions; historical regime |
| `chapter-64` | P2 | DMG Vol 11 Ch 64:  Background to the Industrial Injuries scheme | industrial injuries scheme; scope; source roles |
| `chapter-66` | P2 | DMG Vol 11 Ch 66: Industrial accidents | industrial accident; employment; causation |
| `chapter-67` | P2 | DMG Vol 11 Ch 67: Prescribed diseases | prescribed disease; occupation; evidence |
| `chapter-69` | P2 | DMG Vol 11 Ch 69: Disablement benefits | disablement; assessment; benefit |
| `chapter-71` | P2 | DMG Vol 11 Ch 71: Reduced earnings allowance | reduced earnings; comparison; allowance |
| `chapter-72` | P2 | DMG Vol 11 Ch 72: Unemployability supplement | unemployability supplement; conditions; historical scope |
| `chapter-73` | P2 | DMG Vol 11 Ch 73: Old cases | old case; date of event; transitional regime |
| `chapter-74` | P0 | DMG Vol 12 Ch 74: State Pension | State Pension; qualifying conditions; regime date |
| `chapter-75` | P0 | DMG Vol 12 Ch 75: Retirement Pension | Retirement Pension; qualifying conditions; regime date |
| `chapter-76` | P0 | DMG Vol 12 Ch 76: Forfeiture Act 1982 | forfeiture; statutory dependency; scope |
| `chapter-77` | P0 | DMG Vol 13 Ch 77: Conditions of entitlement, membership of the household and normal amount payable | Pension Credit; household; qualifying age |
| `chapter-78` | P0 | DMG Vol 13 Ch 78: State Pension Credit: additional amounts and special groups | additional amount; special group; conditions |
| `chapter-79` | P0 | DMG Vol 13 Ch 79: Payment questions | Pension Credit payment; part-week; change |
| `chapter-83` | P0 | DMG Vol 14 Ch 83: Assessed income periods | assessed income period; historical applicability; source quality |
| `chapter-84` | P0 | DMG Vol 14 Ch 84: Deemed weekly income from capital | capital disregard; ownership; deemed weekly income |
| `chapter-85` | P0 | DMG Vol 14 Ch 85: Income other than earnings | income other than earnings; attribution; disregard |
| `chapter-86` | P0 | DMG Vol 14 Ch 86: Earnings | earnings; employment status; assessment |

## Bounded ADM context

Start with the following seven ADM files, totalling **370 publisher-declared pages**, for the specific cross-guide questions. They remain a separate acquisition and research family; no present acquisition or substantive comparison is claimed by this plan.

| Chapter | Reason |
|---|---|
| A1 | Compare decision/evidence terminology with DMG1 without assuming shared rules. |
| A2 | Scope the application journey and claims evidence. |
| E1 | Identify the UC entitlement scope boundary, without implementing entitlement. |
| E4 | Test household/couple terminology against Pension Credit scope. |
| H1 | Compare capital concepts across UC and Pension Credit. |
| H2 | Provide a bounded capital-disregard comparison against the Pension Credit pilot. |
| M6 | Identify transition issues before linking UC and legacy/Pension Credit journeys. |

The JSON names six conditional files: A4, A5, C1, M5, R2 and U1. Activate one only when an existing journey has a recorded unresolved dependency that needs it. Initial plus conditional selection is bounded at 13 of 182 ADM PDFs; the other 169 are not queued. Expanding further needs a separate scope decision. The claimant-facing UC eligibility source supports service discovery and scope questions; it does not replace staff guidance or legislation.

## Evaluation and staff needs

Reuse all eight personas, ten stories and fourteen questions listed in the JSON; do not replace the original Pension Credit questions when widening coverage. The 156 chapter cases provide broad coverage. Fourteen explicitly enumerated baseline cases preserve the original questions, and 22 family cases cover source navigation and a boundary check for each publication group. The six existing stage-two journeys remain the staff-facing end-to-end tests.

| Staff need | Work to verify |
|---|---|
| ST01: guidance and law | Exact statutory/memo/case citation register, authority distinctions, unresolved provision/version/applicability |
| ST02 and MP01: route to rules | Evidence → proposed meaning → dependencies → independently reviewed synthetic cases for the bounded capital pilot |
| ST03: fraud, error and evidence | Separate source statements from operational evidence requirements; unresolved ownership recorded |
| ST04: adviser and calculator perspective | Coverage and controlled synthetic comparison design; no fabricated CPAG interpretation or calculator execution |
| OW01: extensive evaluation | Every source unit, priority group and existing persona/story/question mapped to recorded cases and outcomes |
| OW02: apply and change journeys | Separate invented application and change scenarios, including assisted support and no-decision limits |
| OW03: full DMG | All 331 units accounted for, with semantic depth and specialist review reported independently |

For every substantive unit, the positive case asks for a source-backed statement, exact locator and scope; its expected evidence must be authored after acquiring and checking the source. The negative case asks whether a heading or isolated passage authorises a rule for another benefit/date. Executed answer text, input/output digests, method, errors and reviewer state must be retained. A prompt and expected-behaviour description are not a passing result.

Thirteen reusable negative controls are defined in the JSON: missing support; heading-only promotion; benefit/regime confusion; wrong locator; unsupported supersession; date-role/precision substitution; reversed direction; example-as-rule; unavailable CPAG text; unacquired legal content; unsupported specialist status; individual entitlement demand; and source-byte replacement. Apply relevant controls by profile and the directed-relation control to the capital pilot.

## Temporal and legal dependency work

Every explicit dependency receives a ledger entry with the literal citation, source page/paragraph, possible target identity, acquisition state and resolution confidence. Distinguish work, provision, version and digital file. Retain unresolved abbreviations, case identifiers, memo references and conflicting interpretations. The sibling legislation catalogue helps identity resolution; its metadata is not captured provision text or a Pension Credit effects graph.

Do not infer that an amendment was incorporated, a memo expired or a rule commenced merely from a document date. Publication, revision, observation, acquisition and stated legal effect are different fields, with precision preserved. A legal dependency that cannot be acquired can close an accounting task with a gap, but it cannot support a legal proposition or specialist acceptance.

## Unattended execution and honest completion

Resume work using `(source unit, source hash, requirement, tooling revision)`. Keep completed attempts immutable and link retries to prior attempts. Queue independent source units in bounded batches; report acquisition, extraction and semantic errors separately. Every task produces a receipt with method/model identity, exact inputs, outcome, evidence paths and unresolved dependencies. Never manufacture a model identity or usage value when unavailable.

| Completion label | Required evidence |
|---|---|
| Source complete | All 331 PDFs acquired and hashed; measured pages and extraction outcomes reconciled. Any inaccessible source means source-accounted-with-failures instead. |
| Research coverage complete | All 331 profile outcomes terminal; all 78 chapter requirements attempted; all 156 cases and family/cross-cutting checks have actual outcomes or explicit blockers. This can include documented semantic gaps. |
| Specialist accepted | A qualified reviewer accepts explicitly named statements/tasks and exact hashes; no automatic promotion from machine checks or whole-chapter assumptions. |
| Publication ready | Source and all-assertion validation, deterministic generation, negative controls, measured consumer performance and exact-byte browser journeys pass; scope/limitations visible. |

Pass/fail/not-run/blocked counts must remain separate. A documented blocker satisfies accounting, not a passing evaluation. Report how many source units have a definition, a supported proposal, a rejected proposal and an unresolved legal/temporal dependency; none of those counts estimates all possible concepts in welfare law.

The report columns are fixed in the JSON, including source identity, priority, acquisition, page/text quality, segmentation, candidate/proposal counts, unresolved dependencies, evaluation outcomes, research state, specialist state and receipts. Render those columns as the human coverage report. This gives a finite stopping rule while leaving expert-review gaps visible.

## Practical release checks

1. Reproduce the frozen census with `python3 source/discovery-2026-09-15/acquire_metadata.py --check`; reconcile acquisition output to the worklist by exact official URL and source hash.
2. Run the repository’s governed build, `scripts/validate_bundle.py`, `scripts/evaluate_queries.py` and `scripts/evaluate_semantics.py` through `uv run --locked python` after the full-corpus pipeline is integrated. These current scripts alone do not yet prove every new coverage requirement.
3. Add report checks that join every source-unit ID and requirement to a receipt, reject unknown IDs and duplicate terminal outcomes, and reconcile all source/class/family/chapter/persona totals. Keep the plan unchanged; execution results are separate artefacts.
4. Validate every exact quotation and original-page locator, proposed endpoint/predicate, authority/review state and hash; include the applicable negative mutations.
5. Measure loading, search, graph navigation and memory on the actual expanded corpus. Use bounded projections or source-family bundles if the existing consumer limits are exceeded; do not silently omit records.
6. Check a representative route from every source family and semantic priority, plus all seven Pension Credit substantive chapters, in the installed consumer against the frozen bytes.
7. Freeze content on 24 September with all completion labels computed independently. Website/WebMCP/voice remain separate implementation and rehearsal gates for 30 September.

## Decisions still requiring people

The original stakeholder plan, named specialist reviewers, accepted synthetic outcomes and any wider ADM scope remain open. Those decisions do not prevent source acquisition, provenance validation, conservative research proposals or a coverage report. Unattended work must finish at a candid research result when specialist decisions remain unavailable, not invent acceptance or a complete ontology.
