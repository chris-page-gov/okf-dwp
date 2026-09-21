# Use the Data agent to propose a semantic review

[Learning path](learning-path.md) · [Portable methodology](methodology.md) ·
[Check the ChatGPT connection](chatgpt-connection.md)

**Proposed trial — not run.** This guide describes a small, reviewable experiment,
not an automatic ontology feature or a completed Data Agent evaluation. OKF-DWP
is an independent experiment, not an official DWP service or benefits advice.

## What the documented workflow adds

A **connector** gives an AI access to permitted information and operations in
another system. An analysis workflow helps it decide what to investigate, check
the inputs and produce a useful result. OpenAI's documentation separates these
server-backed tools from **skills**: reusable instructions for doing a task.
[Plugin architecture](https://developers.openai.com/plugins/concepts/plugins)

The documented **Data Analytics workflow in ChatGPT Work** covers gathering
source context, checking missing values and duplicates, joining datasets,
exploring hypotheses, modelling, validating and producing reports, notebooks,
charts or dashboards. It asks for visible assumptions and limitations, with
original inputs preserved. This is more than connecting to a database.
[Analyse datasets and ship reports](https://learn.chatgpt.com/use-cases/datasets-and-reports)

The product announcement of **10 September 2026** explicitly names the **Data
agent in ChatGPT Work**, listed as **Data** in the Plugins directory. It can
investigate questions, use organisational definitions and data relationships,
combine permitted data and documents, explain evidence, and produce or refine
interactive dashboards. Connected actions require their own authorisation.
It consumes trusted semantic context; the announcement does not promise
automatic legal ontology generation.
[Data agent announcement](https://openai.com/index/put-data-to-work/)

The January 2026 article about OpenAI's **in-house data agent** describes a
separate custom internal system. Its layered context, human annotations,
code-derived meanings and evaluation are useful design lessons, not proof that
every internal capability is exposed in the public Data plugin.
[Internal engineering account](https://openai.com/index/inside-our-in-house-data-agent/)

An **ontology** defines a domain's kinds of things and relationships. OpenAI's
knowledge-graph cookbook demonstrates a custom pipeline that turns documents
into statements, dated relationships and resolved entities. That supports the
feasibility of model-assisted proposals. It is an engineering example with
June 2025 benchmarks, not a promise that ChatGPT Data Agent supplies that
pipeline or understands a whole corpus.
[Temporal knowledge-graph cookbook](https://developers.openai.com/cookbook/examples/partners/temporal_agents_with_knowledge_graphs/temporal_agents)

## A small proposal-and-review trial

Use the existing [discovery-first method](methodology.md), rather than starting
another vocabulary from scratch. A **concept** is a named meaning; an
**assertion** links records in a stated direction. **Provenance** records where
that assertion and its supporting material came from.

1. **Fix the question and inputs.** Select one topic and an initial 10–20 public
   source pages, including headings and necessary continuations. Record the
   source versions, file hashes, page identifiers, rights and exclusions. A
   hash identifies exact bytes. Log missing supporting pages; do not fill their
   content from memory or quietly expand the trial.
2. **Supply the existing model.** Give the agent the relevant
   [concept catalogue](../evaluation/semantic-expansion/catalogue.json),
   [vocabulary guide](ontology-use.md) and task requirements. Reuse stable
   identifiers where meanings match. Keep benefit variants, components,
   entitlement and payment distinct. Similar names do not establish identical
   meanings; an ambiguous abbreviation must retain its alternatives.
3. **Request proposals with evidence.** For each proposed concept or directed
   relationship, record its definition or meaning, existing or proposed
   identifier, source quotation and locator, supporting heading, conditions,
   exceptions, territory and date limits. Keep source publication, capture and
   applicability dates separate. Use existing predicates where their meaning
   fits: a reference is not legal applicability; `dcterms:requires` identifies
   supporting material that must accompany an interpretation.
4. **Keep an explicit gap list.** Mark each interpretation `model-derived` and
   unreviewed, separately from source authority. Retain uncertainty, conflicting
   passages and missing dependencies. An AI's confidence is not a specialist's
   approval. Do not change an open obligation to complete because another model
   agrees.
5. **Review before integration.** Return a proposal table, supporting evidence
   inventory, unresolved questions and the exact run settings. Accepted changes
   go through the established additive authoring and producer workflow in
   [staff-question semantics](semantic-expansion.md). Do not hand-edit generated
   bundles or rewrite frozen source releases.

For example, a page mentioning a benefit can justify a candidate for navigation.
It does not establish that its rule applies to everyone receiving that benefit.
A useful review finds the limiting heading and exceptions as well as the term.

## Three different checks

| Check | What it can establish | What it cannot establish alone |
| --- | --- | --- |
| Mechanical validation | Identifiers resolve, quotations match the retained extraction, hashes agree and required fields are present | That extraction is faithful to the original or an interpretation is correct |
| Source review | The original passage, heading, continuation and qualifications support the proposed meaning within its stated scope | Complete legal coverage or applicability to an individual |
| Specialist review | A named reviewer accepts a stated interpretation and evidence requirement within a defined scope | Automatic approval of the rest of the corpus |

A second AI can help identify defects but is not a benefits or legal specialist.
The proposal and each review decision need separate authorship and status.

## Measure improvement without teaching to the test

The supplied staff questions are **development cases**: they helped shape this
bundle. Paraphrasing them does not make an independent accuracy benchmark.
Before a new trial, reserve additional questions and expert-reviewed expected
evidence that the proposal process will not see. These are **held-out questions**.

Compare the existing and proposed semantic models with the same source pages,
engine and budgets. Report counts and denominators for source-supported
assertions, unsupported relationships, missed conditions or exceptions, and
required evidence paths retained. Include an ambiguous term, an unavailable
source, an unknown term and a budget too small to hold required support.
Expected behaviour may be a clear refusal or an unresolved alternative.

Evaluate AI answers separately against the exact supplied evidence: each claim
needs support and its qualifications. More graph edges, valid citations or more
retrieved pages do not by themselves mean more accurate answers. Retain failed
attempts and unchanged baseline results. This proposed trial has no scores yet.

## Establish access at the point of use

OpenAI directs authors to test the installed plugin's actual tool selection,
arguments, results and errors; capabilities depend on the chat's tools and
permissions. A plugin visible in a parent conversation does not prove that a
separate Data Agent can call it.
[Plugin permissions](https://learn.chatgpt.com/docs/plugins) ·
[Connection and testing guidance](https://developers.openai.com/plugins/deploy/connect-chatgpt)

For a live Ask OKF trial, follow the [client check](chatgpt-connection.md) and
preserve source, engine, context identity, budgets and actual evidence reads.
Stop on missing tools or a rejected call. Do not relabel website browsing as a
successful tool invocation.

A separately supplied [retained evidence package](retained-evidence-publication.md)
can support an offline proposal exercise. Label it a **frozen evidence handoff**,
verify its contents where possible and retain its gaps. It is not a fresh MCP
call, proof of Data Agent access or a complete representation of the source
corpus. Keep claimant information and private account material out of this
public trial.
