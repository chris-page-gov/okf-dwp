# Model and affordability evaluation

**Status: designed, not run. No measured cost or comparative accuracy claim.**

The owner chose Astra Ultra to demonstrate current capability and explore what might become affordable within roughly a year. Future model capability and prices are uncertain. Build a repeatable benchmark so that this hypothesis can be tested without rebuilding the corpus.

## Proposed processing mix

| Work | Candidate |
| --- | --- |
| Downloads, byte identities, PDF extraction, syntax and exact citation checks | Deterministic scripts |
| Simple classification and constrained metadata extraction | GPT-5.6 Luna trial |
| Bounded concept drafting and document analysis | GPT-5.6 Terra trial |
| Ambiguity, semantic reconciliation and challenge review | GPT-6 Astra; compare ordinary high reasoning with Ultra on difficult cases |
| Acceptance of policy, legal applicability and executable rules | Named domain reviewers |

This is a workload-specific recommendation, not an established result. [Official OpenAI guidance](https://developers.openai.com/tracks/building-agents#how-to-choose), checked 15 September 2026, recommends beginning with Astra and evaluating lower-cost Terra/Luna for simpler work. The current Codex model selection remains unchanged. Codex subscription allowances and API token prices are different cost measures; do not infer one from the other.

## Frozen benchmark design

Select a stratified set before comparing models: ordinary prose, lists/exceptions, tables, footnotes, chapter 83 damaged text, cross-chapter references, historical/amendment material, ambiguous benefit applicability, CPAG metadata-only and missing legal evidence. Use the same input hashes, evidence budget, tools and output schema. Save prompts and record model identifier, reasoning effort, date, observed token use, elapsed time, retries and failures. Adapt prompts transparently to each model; retain a common task definition and scoring rubric.

Score extraction completeness, exact evidence support, paragraph/page accuracy, unsupported assertions, preserved conditions/exceptions, temporal/jurisdiction boundaries, appropriate abstention, accessibility of explanations and staff task completion. Use independently reviewed expected evidence and outcomes. Astra output is a candidate reference, not the gold standard; an agreement between two models is not independent legal assurance.

Report per-task results and uncertainty, not just an average. Record reviewer corrections and time. The useful affordability measure is **cost per accepted result**, including retries, challenge review and staff correction time. Keep direct machine processing cost separate from estimated human cost, with explicit assumptions. Do not invent missing usage or pricing.

Promotion gate: no unsupported decision-critical propositions in the accepted benchmark, complete required provenance, and domain-owner approval of the bounded use. A finite test set still does not establish safety across the full corpus.

## Next action

Agree the source sample and expected answers with reviewers, then run the same six proposed journey cases plus extraction controls through the candidate models. Paid API runs or changes to subscription/model settings have not been initiated by this plan. Preserve today's artefacts as the high-capability baseline and repeat against affordable models at future dated checkpoints.
