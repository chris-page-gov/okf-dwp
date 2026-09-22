# PIP transition and relevant-age source review

This is an additive, model-assisted source-boundary review for the DLA/PIP and PIP pension-age staff questions. It is not official DWP training, an entitlement decision, current-law assurance or independent specialist acceptance.

- **DLA** means Disability Living Allowance.
- **PIP** means Personal Independence Payment.
- **ADM** means Advice for decision making, the DWP guidance manual.
- A **transition** is the process by which a claimant moves from one benefit to another. A source explaining transfer during a hospital stay does not describe the complete transition process.
- A **relevant age** is the expression used by the captured PIP guidance. Reaching that age, continuing an existing award and making a new claim are separate questions.

## Source and scope

Authoring is in [closure-pip-transition.yamlld](../domain-profile/logical-units/closure-pip-transition.yamlld). It adds nine passages from the frozen [ADM P5 extraction](../source/adm-2026-09-19/pages/adm-chapter-p5.json) and two bounded context profiles. The P5 PDF has SHA-256 `0231da4591e999a909e35ddec62209fe3278bddcf97be4eb87689758302677d3`. PDF, extraction and acquisition-inventory hashes remain bound in the authoring; capture is not a publication or effective date.

The new P5 passages contain **21,438 original source bytes**, with presentation joiners declared separately by the producer. They cover the following sections:

| Passage | PDF pages | Why it is kept together |
|---|---|---|
| P5004–P5012 definitions and following reserved range | 3–4 | The relevant-date definition continues onto page 4. |
| P5015 claim method and date | 6 | Keeps the complete paragraph, note and citation. |
| P5016–P5023 invitations | 6–8 | Keeps the age and relevant-date conditions, terminal-illness and hospital exceptions, and both Katy and Declan examples. |
| P5025 claimants under 16 | 8 | Keeps the separate age restriction and citation. |
| P5034–P5040 written invitation and claim period | 9–10 | Keeps defective-claim and discretionary extension alternatives; the P5036 citation crosses the page. |
| P5046–P5052 no claim | 10–12 | Keeps suspension, a second opportunity, reinstatement and termination; the notice conditions continue on page 12. |
| P5062–P5064 determination and transfer timing | 14–15 | Keeps the complete notification conditions and unchanged source wording. |
| P5065 terminal-illness alternative | 15–16 | Keeps every condition, both notes and both complete historical examples. |
| P5066–P5070 fixed-term extensions | 16–17 | Keeps the under-16 and working-age alternatives; the P5067 exceptions continue on page 17. |

The first profile, `logical-dla-pip-transition`, is relevant to `staff-026` and its intentional duplicate `staff-033`. It can also supply bounded transfer evidence when another task mentions both DLA and PIP. It explicitly retains an unresolved scope obligation: mentioning both benefits does not establish that transfer is the intended relationship, or make every DLA/PIP interaction covered.

The second, `logical-pip-pension-age`, is relevant to `staff-032`. It reuses the P1011/P1013 gateway and the separate dependency review's `pip-relevant-age-p4076-086` passage. That passage contains the acquired age exceptions; the earlier P4016–P4021 institutional-payment passages do not replace it.

Every selected profile still contains absent obligations for legal version, applicability, question scope and specialist review. New paths do not remove those obligations or replace any old staff review requirement.

## What the source inspection changed

Page 6 alone would miss the material hospital exception at **P5021 on page 7**. The new invitation passage therefore spans pages 6–8 and retains the complete examples. The existing P5093–P5097 passage concerns transfer while in hospital or a care home; it is a conditional branch, not the general child-DLA transition rule.

P5064 really contains the wording “DLA is not awardedand” in the frozen extraction; the PDF shows the same joined wording. P5063 also points to the P5035 timing wording. These are retained, with interpretation unresolved. The process does not silently correct an official source or invent a calculated date.

A reference from the P5021 Declan example literally names **ADM Chapter P3** for hospitalisation. The authoring preserves that pointer as unresolved rather than changing it to the separately selected P4 institutional-payment material.

## Still missing

The P5 profile does not close the P2077 terminal-illness definition, current territorial/identified-area rules or legal versions. Voluntary transfers, pending DLA claims, defective voluntary claims, failures to provide information, withdrawal/death and later change-of-circumstance/qualifying/linking branches remain expressly outside the selected scope. Historic example amounts are not current rate evidence.

The relevant-age profile does not close P4087–P4097 mobility revision/supersession and residence/presence branches, the update effect of memo ADM 6/25, the DMG 74022 age schedule or all P1/P5 dependencies. It preserves the source's P4083 pointer to P4080 3.1/3.2 as unresolved.

## Verification and retained learning references

The PDF skill was used to render and visually inspect P5 pages **3, 4, 6–12 and 14–17**. The check confirmed the governing headings, list continuations, footnotes and complete examples for these boundaries. It is agent source/layout review, not legal review. No source was acquired or repaired.

Run the focused controls with:

```sh
uv run --locked python -m unittest discover -s scripts -p test_logical_pip_transition_closure.py
```

The nine controls cover source hashes, exact contiguous spans, non-overlap with earlier authored units, meaningful exception/example retention, page-cut and source-tampering failures, declared profile paths, unresolved pointers, authority boundaries, and the duplicate staff question/learning hashes. The first control run rejected the test phrase “age 16 or over”; it was corrected to the source's “aged 16 or over”. The source was unchanged.

These source controls do not claim that a new projection, evaluation, service release or public website has been delivered. Integration and exact-version results belong in the implementation work log and PR handover.

The old question strings, hashes, lesson IDs and page evidence routes are preserved. Additive unit references must not silently replace those frozen learning/assessment anchors.
