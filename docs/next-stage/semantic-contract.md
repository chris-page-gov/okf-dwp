# Semantic pilot contract

## Meaning and authoring

Each concept has its own file under `knowledge/concepts/`, a stable absolute IRI, the existing Explorer route, a preferred British English label, a scope note and source references. Four newly authored capital concepts also have provisional definitions. Existing discovery descriptions are not retrospectively described as complete definitions.

`references` remains ordinary `dcterms:references` navigation. `semantic_relations` is an explicit authored proposal with a registered predicate, existing concept target, rationale and one or more exact source passages. The compiler emits both an evidence-bearing assertion and its direct RDF triple; the source input is the single place to edit a relationship.

| Predicate | Domain and range | Meaning in this pilot |
| --- | --- | --- |
| `http://www.w3.org/2004/02/skos/core#related` | Concept → concept | A thematic association evidenced by the captured guidance; no identity or legal implication |
| `https://chris-page-gov.github.io/okf-dwp/ns#hasEvidenceRequirement` | Concept → concept | The captured guidance identifies this evidence requirement for considering a capital disregard |
| `https://chris-page-gov.github.io/okf-dwp/ns#hasDisregardPeriod` | Concept → concept | Duration is a separate aspect of the disregard considered in the captured guidance |
| `https://chris-page-gov.github.io/okf-dwp/ns#precedesAssessmentOf` | Concept → concept | The captured paragraph places the source assessment before the target assessment |

The three project predicates are local experimental vocabulary, not DWP standards. Their IRI identifiers do not claim a separate deployed ontology endpoint. Predicate definitions are maintained here and in the compiler allow-list.

[SKOS](https://www.w3.org/TR/skos-reference/#semantic-relations) defines related concepts as associative rather than hierarchical; a `skos:related` association is symmetric. The file stores one asserted direction with matching forward/inverse labels; no reasoner materialises reverse edges. Counts measure stored assertions, not an inferred closure. No `owl:sameAs`, `skos:exactMatch` or transitive reasoning is introduced.

## Authority and evidence

All 15 semantic proposals have `assertion_status: model-derived`, authority `model-assisted` and `review_status: unreviewed-specialist-review-required`. The profile requires a confidence score: the fixed `0.5` is an explicitly uncalibrated placeholder, not a measured probability and not a threshold for promotion or decisions.

Evidence binds the authored specification and rationale to its YAML-LD SHA-256, then separately binds each exact quotation to a frozen page extraction, original PDF hash, source URL and paragraph/page locator. The compiler rejects absent quotations, unknown endpoints, unsupported predicates, self-relations and unsupported locators. Validation checks projection equality, RDF triples and source hashes. These checks establish traceability and structural integrity, not the truth or completeness of an interpretation.

No age, rate, duration or current-law assumption is promoted from a captured example. The capital-disregard packet calls out Memo 11/20 and statute/provision reconciliation as dependencies. Missing evidence must remain a question for review; it must not silently become an automated adverse decision.

## Coverage and extension

The generated [map](../../bundle/semantic-map.md) shows all 26 authored concepts and 15 proposals. It is deliberately incomplete. Future additions require a competency question, benefit and temporal scope, exact source evidence, consistent predicate meaning, counterexamples and a review record. Context-only CPAG contents links cannot support a substantive policy relationship.
