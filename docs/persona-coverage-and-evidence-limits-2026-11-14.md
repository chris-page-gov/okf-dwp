# Persona coverage and evidence limits

## What this review covers

The eight personas and their 21 interest areas are authored projections, derived from the cited knowledge and staff-needs inputs. They are unvalidated: they do not establish that real staff or applicants need or accept these workflows. The generated [coverage map](../evaluation/retrieval-gate/persona-coverage.json) records each area’s source file, line range, locator, SHA-256, case IDs and case types; the [case registry](../evaluation/retrieval-gate/persona-cases.json) contains exact questions and assessor-only source targets. Expected targets are not runtime inputs.

The graph run recorded 263/263 declared source-record target occurrences hit across 62 retrieval cases, including 263/263 path-scoped hits, zero retrieval-case failures and zero delivery errors; the largest observed response was 8,192 bytes. These are actual machine-run receipt counts for source-record recall against the authored target set, not answer accuracy, legal sufficiency, complete evidence-chain coverage or user validation. The coverage producer marks its recall metric “not-run” because it only builds the case plan; the separate graph-evaluation receipt contains the executed counts. Ten boundary cases, two UI cases and one integrity case are excluded from recall. Boundary cases were observed but not assessed for legal sufficiency or non-fabrication. Separate automated artefacts include Chrome/Edge capital-browser captures and an 18-case hash-mutation suite (reported passing). The persona-suite UI and integrity validation fields remain not-run; neither those separate artefacts nor these run fields establish human accessibility (including assistive-technology) review or legal acceptance.

| Projected persona | Areas and question coverage |
|---|---|
| Welfare-rights adviser | `find-original-guidance`, `identify-missing-qualifications`: frozen staff questions plus stage-2 capital and unhinted absence, carer, income/capital and PIP prompts; retrieval and boundary. |
| Pensions specialist | `inspect-original-context`, `separate-income-capital`, `retain-historical-gaps`, `pension-distinctions-dates`: frozen staff questions plus unhinted income/capital, age, household and historical-rate prompts; retrieval and boundary. |
| Policy-law reviewer | `distinguish-guidance-law`, `test-temporal-jurisdictional-scope`, `separate-capture-and-effectiveness`: frozen questions, stage-2 capital/legal prompts and unhinted absence, age, historical-date and legal-hierarchy prompts; retrieval and boundary. |
| Evidence-assurance reviewer | `audit-evidence-per-claim`, `separate-policy-and-operational-evidence`, `privacy-fraud-error-owner-boundary`: frozen questions, synthetic household and operational-proof prompts; retrieval and boundary. |
| Knowledge engineer | `reproduce-evidence-transform`, `replay-semantic-retrieval-output-identity`: frozen questions, provenance-replay prompt and stage-2 provenance case; retrieval and integrity. |
| Assisted-support | `accessible-source-navigation`, `explain-extraction-limits`: stage-2 and unhinted accessibility/extraction prompts; UI and boundary. |
| Rules architect | `trace-evidence-to-rule`, `expose-rule-conditions-and-change`, `avoid-architecture-assumptions`: stage-2 rule-provenance case and unhinted rule-boundary/replay prompts; retrieval and boundary. |
| Applicant-change reporter | `separate-first-claim-from-change`, `plain-language-next-step-and-handoff`: synthetic first-claim/change comparison and unhinted official-route prompt; boundary only. |

The exact per-area case IDs and kind counts are in the linked coverage map. All 40 original staff questions remain positive retrieval cases with unchanged wording and targets. New stage-2 and unhinted questions are additive. Five broad stage-2 prompts retain their boundary controls; four also have benefit-framed positive pairs, while `stage2-005` remains boundary-only. Applicant/change and rule-boundary items currently test gap handling, not positive retrieval of an official service route or executable policy.

## Public service observation

The separate [public graph SDK verification](graph-service-publication.md) passed
355/355 declared source-target checks across 106 distinct questions and 108 case
occurrences, including the runnable persona cases, original controls and frozen
wording regression. All 352 distinct question/target pairs were retrieved with
matching source-text hashes and declared paths. Complete evidence HTTP bodies
stayed within 7,469 bytes. This broadens the observed client and protocol coverage;
it does not change the persona suite’s UI or integrity planning fields, validate
real user needs, or close legal and specialist-review obligations.

## Evidence gaps and separate checks

The bundle does not provide evidence for DWP operational policy on handoff procedures, privacy, fraud or identity-check requirements, executable rules and their approval, current legal applicability, or case-law reasoning. This is a gap in the DWP policy evidence represented in the bundle, not a claim that the prototype service lacks technical security or privacy controls. Such policy questions must remain unresolved or be referred to an authorised source or reviewer; the cases do not establish those requirements. Source metadata or guidance citations do not prove current law. No human accessibility review is claimed.

The statutory crosswalk records 20 catalogue work records and 53 provision targets: 13 targets have a DWP body projection, 38 are metadata-only, and two have work metadata only. Eighteen case-law decision metadata records are excluded from statutory work matching; six case-law citation mentions remain unresolved. These matches help identify source records but do not close legal obligations or establish commencement, extent or applicability. All 203 original obligations remain open: 43 evidence-closure, 40 scope, 40 applicability, 40 legal-version and 40 specialist-review obligations.

The 43 evidence-closure obligations concern unverified completeness of the evidence chain. They are not a count of absent source passages. The [insufficiency categories](context-review.md#why-evidence-remains-insufficient) distinguish source coverage, retrieval, graph connections, question scope, legal applicability and version, interpretation, specialist review, delivery and access. The original reason codes and identifiers remain intact.

The capital keyboard/browser review is separately recorded in [the review report](../evaluation/retrieval-gate/capital-review/index.html), with [Chrome](../evaluation/retrieval-gate/browser/capital-chrome.png) and [Edge](../evaluation/retrieval-gate/browser/capital-msedge.png) captures. The [18 hash-mutation controls](../evaluation/retrieval-gate/persona-mutation-controls.txt) are a separate automated integrity check. The screenshots and mutation controls provide automated test evidence only. They do not turn the persona evaluation’s planning fields into executed validation claims, or establish human AT review, legal acceptance or user validation.

## Sources

- Authored persona projections: [guided discovery](../knowledge/guided-discovery.yamlld), [evaluation journeys](../knowledge/evaluation-journeys.yamlld), [staff-needs journeys](../domain-profile/staff-needs/journeys.json).
- Machine results and obligation audit: [graph evaluation](../evaluation/retrieval-gate/graph-evaluation.json); statutory source-identity status: [legislation crosswalk](../evaluation/retrieval-gate/legislation-crosswalk.json).
