# Reviewed logical boundaries

These authored inputs define a small set of **logical units**: complete passages such as a numbered rule with its list, examples, notes and citations. A physical PDF page remains an acquisition locator. It is not necessarily the beginning or end of a rule.

This is an independent experiment. Boundary choices and relationships are model-derived proposals reviewed by an agent. They have **not** received specialist, legal or human acceptance. “Complete within declared boundary” means that the declared passage is retained; it does not mean that all law or entitlement conditions are known.

## What is here

| File | Purpose |
| --- | --- |
| `overrides.json` | 46 exact boundaries across six frozen documents, 28 scoped relationship proposals and one empty-page observation. |
| `concepts.yamlld` | Two additional concepts: Universal Credit and temporary absence, plus three explicit temporary-care-home phrase aliases for the existing concept. Existing neutral Pension Credit, household, payment and care-home identifiers are reused. JSON syntax is valid YAML 1.2; the explicit YAML-LD context and graph remain present. |
| `profiles.json` | Five scoped evidence requirements for the additive logical mode. Every profile retains open legal-version, applicability and specialist-review obligations. |
| `reference-review.json` | Eight unresolved source references or update effects. An acquired memo is not treated as reconciled. |
| `source-controls.json` | 43 independently specified source-phrase and example checks, plus duplicate-number and source-anomaly controls. These do not grade AI answers. |

The producer in `scripts/build_logical_units.py` owns the generated `logical-units/` outputs. The logical context compiler owns routes and requirements. Neither producer is authorised to rewrite frozen source or imply that a smaller unit automatically satisfies an earlier whole-page requirement.

## Sample and boundaries

The sample is purposive, not a random or representative estimate of corpus-wide segmentation accuracy.

- **DMG Chapter 7 Part 6:** claimant absence 077001–077004; separate household conditions 077005–077007; the complete qualifying-young-person group 077008–077014; the dated 077015 transition; SPC-only 077025–077026; distinct State Pension 077027–077029; and both unrelated occurrences of paragraph number 077030.
- **ADM C1:** UC temporary absence C1986–C1990 and the separate Crown servant/Forces posting conditions C1166–C1170. UC months are not replaced with SPC weeks.
- **DMG Chapter 78:** contents, the chapter-local expanded meaning of “AA”, temporary/permanent care-home branches and a complete table for the source's stated 8 April 2024 rate period. The table does not establish current rates.
- **ADM P1:** contents, primary PIP conditions and the age rule continuing onto the next page, including the upper-age exceptions reference.
- **ADM P4:** first-residence payment conditions including the under-18 hospital exception; the cross-page residence definition; distinct care-home mobility and prison/hospital linking provisions.
- **ADM P5:** transfer-specific entitlement/payment conditions with four complete examples; temporary-absence transfer; the historical rollout appendix; and the empty extracted page 35.

The first State Pension 077030 fixture is intentionally incomplete in dependency scope: the following increment conditions remain outside it. Its identity is distinct from the bereavement 077030 on page 19. The P5 spare range `P5096 – P5105` overlaps actual preceding P5096/P5097; this source anomaly must not erase those rules. The contents typo `007715` and literal unclear reference “falls within 12 above” are preserved, not repaired by inference.

## How the files bind to source

Each document binds the frozen inventory, original PDF and page-extraction JSON hashes, the original source URL, capture time and declared source-date metadata. Document publication dates are unknown in these six inventories. Publication-page updates are a separate date role; they are not legal commencement dates.

Each unit contains ordered, contiguous UTF-8 byte spans: zero-based start, exclusive end and a hash of the exact span. Adjacent pages can form one unit. No source words are rewritten. The producer separately accounts for all bytes outside reviewed overrides. Any newline used between page fragments in a presentation is not claimed as source text.

`support_unit_keys` expresses **evidence that must travel with a passage**. For example, 077028 explicitly references the exception in 077029, and C1988 uses the definitions in C1989/C1990. These edges do not mean that a claimant satisfies either rule. Conditional qualifying-young-person branches use reference proposals rather than forcing every household definition into every claimant question.

The three additional temporary-care-home aliases are backed by DMG 78084–78086 and do not replace earlier aliases or change the previous source release. The broad care-home concept cannot establish permanent residence. Its profile retains temporary and permanent alternatives and an explicit unresolved branch choice. The claimant-only PC absence profile does not require the separate household group. Source-specific UC posting conditions are not general overseas entitlement rules.

## Visual and mechanical review

The earlier bounded review inspected the DMG and ADM overseas PDF layouts, including cross-page examples and footnotes. Additional agent visual checks rendered the exact Chapter 78 pages 25 and 146, ADM P4 page 4 and ADM P5 page 35 with Poppler at 80 dpi. The table's two columns and transition to the next dated table were visible; the P4 under-18 note and Chapter 78 permanent heading were visible. P5 page 35 was visually blank in that render. The page observation is specific; empty extraction alone is not proof that another page is blank. Render files were temporary review aids, not published evidence.

Run the offline source controls from the repository root:

```sh
uv sync --locked
uv run --locked python -m unittest discover -s scripts -p 'test_logical_unit_sources.py'
```

The 12 tests verify source hashes and date roles; exact, disjoint cross-page spans; complete examples and citations; expected qualifiers after a deliberately rehashed footnote deletion; missing-continuation and hash mutations; duplicate identities; directed required paths; distinct benefit/household/institution scopes; unresolved update effects; and navigation/table/empty-page roles.

These tests do not prove current law, complete answers, whole-corpus boundary accuracy or AI answer quality. The generated mode and its retrieval behaviour require their separate evaluations.
