# Independent review of the direct v4 answers

21 September 2026. **Machine-assisted source review; human review is pending and specialist acceptance is false.** This review does not change any answer, receipt or frozen input.

## What the evidence supports

Both empty controls correctly abstain. Both substantive answers retain `partial_evidence_only` and explain that the whole Pension Credit award cannot be determined from this package. Each preserves the controlling **no-partner** heading, separates the severe-disability and housing-cost additional amounts from the whole award, and recognises the separate household question where a partner is involved.

There are **four mechanically accepted attempts, six substantive claims and seven citations**. All seven quotations are verbatim selected text with matching source URLs and page locators. The machine checks replay exactly. These checks establish traceability; they do not make the answers legally complete or accurate in every qualification.

## Qualifications requiring further review

The Claude-subscription answer’s C1 main statement matches DMG 78088, but its added condition list needs revision. “Actual receipt” and an unqualified exclusion whenever a carer receives CA/UC omit selected treated-receipt rules at DMG 78060 and the transitional-protection exception at DMG 78036. A broader caveat about current applicability does not replace these specific exceptions.

Its gap saying there is no continuation material beyond the four-week note also overlooks the selected Heather example at DMG 78055. That example records later AA cessation and says the additional amount was correctly payable while AA remained in receipt. It does not establish a general continuation rule; the real remaining gap is complete applicable rules.

The description of memos 02/25,06/25 and01/26 should distinguish disability-benefit additions from the later carer-support terminology and treatment. The additional entitlement and 13/52-week statements have selected support but need their own claim-level citations. The original wording remains retained for inspection.

The Codex-subscription answer keeps its three claims narrow; no comparable substantive overstatement was identified in this bounded review. Its summary contains the editorial typo “no-partartner”. This observation is not a model ranking or a claim that every possible defect has been excluded.

## How to inspect the record

- [Hash-bound review and citation diagnostics](independent-claim-review.json)
- [Codex-subscription substantive answer](codex-subscription/staff-012/attempt-01/answer.json)
- [Claude-subscription substantive answer](claude-subscription/staff-012/attempt-01/answer.json)
- [Exact selected substantive package](../../../evaluation/model-comparison/household-direct-v4/frozen/contexts/staff-012.json)
- [Frozen manifest](../../../evaluation/model-comparison/household-direct-v4/frozen/manifest.json)

The JSON binds all four original receipt, answer, model-output and context hashes, and the 21 additional selected records examined for qualifications. Freeze SHA-256: `6463e054b034d7f33df7fcad61be337f01136f996f2a00da7e428acbbae8d934`.

**Next step:** a benefits specialist should examine the conditions, exceptions, legal dates and household facts. Keep DWP-BL-010 open for qualification repair and human assessment. Do not silently repair the retained outputs, present this as benefits advice, or infer comparative accuracy from one substantive question per client.
