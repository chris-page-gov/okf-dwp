# Dependency target review, 22 September 2026

This is an independent, source-backed project review. It identifies and preserves
passages in the frozen DWP corpus; it does not establish current law, individual
entitlement, specialist acceptance or a complete answer.

## Scope and result

`closure-dependencies.yamlld` adds **20 exact units across six destination
PDFs**, with **12 cross-page units**, **51,900 source bytes**, **16 relationship
proposals**, **eight reference dispositions** and **14 source-phrase control
groups**. Its ten document entries include four existing source documents which
supply links but no new units. None of the old source or authoring files is
replaced. The source producer must merge these declarations before checking
non-overlap and the existing source, extraction, inventory and literal hashes.

All eight earlier reference rows retain `status: unresolved` and
`legal_effect_status: unresolved`. Identifying a destination answers **where to
look**; it does not mean that its conditions apply or that all dependent law has
been reconciled.

| Earlier reference | What the frozen source supports now | What remains unresolved |
| --- | --- | --- |
| DMG 077001 → 04642 | Chapter 4 PDF page 102 contains the exact rule, advance/arrears alternatives and explicit 04643–04644 exception. The complete late-notification continuation on page 103 and the page 106 benefit-week definition are separate units. Named exceptions and their examples are retained separately. | Other chapter exceptions, 04204–04218 time extensions, underlying provisions, claimant facts and applicable version. |
| DMG 077013, “falls within 12 above” | The literal wording and preceding 077012 birthday rule remain visible in the old complete unit. | The intended cross-reference cannot be uniquely established from this wording. No guessed correction or new edge. |
| DMG → ADM E2092 and F1093 | E2090–E2095 is retained as the complete child/QYP definition group, including cross-page conditions, exclusion, notes and training/education definitions. | Frozen F1 has **F1085–F1099 as a reserved range**, not a substantive F1093 definition. The range is linked as an explicit mismatch, never as supporting eligibility evidence. UC definitions do not replace the SPC definition. |
| ADM C1988 → memo 09/25 | C1988 explicitly names the memo. The memo explicitly lists C1988 under Annotations. Paragraphs 10–11 contain the emergency-absence branch, all five conditions, two notes and citations. Source-stated decision-date scope, benefit/territorial scope and the complete UC example are separately available. | Amendment consolidation, current law/version, emergency dates and facts, which branch applies, other entitlement conditions and specialist review. |
| ADM C1987 → Chapter E2 | The exact child/QYP definition group E2090–E2095 is available. | Whether a particular person and household satisfy it. |
| ADM P1013 → Chapter P4 | P4076–P4086 contains the complete relevant-age section, including continuing awards, further claims, both examples and ADP branches. | Memo ADM 6/25; required-period and transfer references; revisions/supersessions from P4087; applicable law and claimant circumstances. |
| ADM P4019 → P4051 | The exact P4051–P4052 target concerns **overlapping mobility payments**, with a care-home note. | P4019 says that the target concerns hospital rules, but the target passage concerns overlapping payments. This source-scope mismatch remains explicit. A route to the exact paragraph does not supply a hospital exception. |
| ADM P5106 → Chapter C2 | The whole domestic absence section C2056–C2069 is available: general and medical absence, definitions, a complete example, worker/Forces conditions and family provisions. | The wider chapter's residence/presence/EU routes, memo ADM 11/25, transfer interactions and legal applicability. This is partial destination coverage of a broad chapter reference. |

## Why the memo is divided this way

Memo 09/25 contains different tests. Habitual-residence and past-presence
exemptions must not be mistaken for temporary-absence conditions. Its source
sections become distinct units: introduction (1–4), HRT/PPT (5–9), temporary
absence (10–11), benefit scopes (12–14), dated HRT/PPT lists (15–16), humanitarian
routes (17), each of the three complete examples, and annotations/footer.

The temporary-absence unit preserves all five conditions and both following
notes. Its dependency proposals retain the introduction's unchanged-entitlement
qualification and the benefit/territorial lists. A separate reference retains
the full Jack example, including absence already spent before evacuation.
The “six months” UC period is not converted into the “26 weeks” period used for
other benefits in the source. The dated emergency lists concern HRT/PPT; they
are not treated as a verified live emergency catalogue or a new absence award.

The memo's third example uses a claim date of 17 July 2025 and describes an award
from that date. Its introduction says that the regulations should apply to
decisions made from 18 July 2025. Both statements are retained for specialist
interpretation. The source words are not rewritten to remove a possible tension.
The August 2025 footer, later dates within the memo, capture date and publication
page update remain separate facts. No document publication date is inferred.

## Evidence and verification

The authoring file includes every destination's frozen inventory, PDF and
extraction path/hash, source URL, observation time, date roles and exact ordered
UTF-8 spans. This review uses those already acquired official-source bytes;
there was no new acquisition, provider trial or legal-status check.

The PDF skill was used for a bounded visual comparison of Chapter 4 PDF pages
102–103, memo 09/25 pages 5–6, and ADM P4 page 10, rendered by Poppler at 65 dpi.
The cross-page 04644 continuation, all five memo conditions, the following notes,
and P4051's overlapping-payment list and care-home note were visible. These
renders are temporary review aids, not new published source evidence. The other
new passages were inspected in the frozen extracted text; this is not a claim
that every new page received visual or specialist review.

Ten independent offline regression tests in
`scripts/test_logical_closure_sources.py` check original bindings, non-overlap,
source qualifiers/citations/continuations, complete examples, the dual memo
reference, F1093's missing definition, P4051's scope mismatch, explicit destination
ownership and unchanged unresolved legal effects. They passed with the original
producer's `check_override` validator before integration. These tests do not grade
AI answers or prove source applicability.

Run in the repository's locked environment:

```sh
uv sync --locked
uv run --locked python -m unittest discover -s scripts -p test_logical_closure_sources.py
```

The authoring input uses JSON-compatible YAML-LD, with schema
`okf-dwp-logical-closure-authoring.v1`. Memo units have empty `paragraph_labels`
because the existing shared schema accepts DMG/ADM paragraph identifiers, not
single-digit memo numbers; their exact source numbers remain in the literal text.
All edges use the existing Dublin Core `references` or `requires` predicates.
No new DWP-only predicate, hidden source fetch, current-law claim or specialist
approval is introduced.
