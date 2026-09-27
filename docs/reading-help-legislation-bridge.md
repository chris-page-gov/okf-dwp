# Reading help and the legislation bridge

This is an independent experimental publication, not official DWP guidance or benefits advice.

## What the bridge adds

A **citation** is a pointer to another source. For example, “SS CB Act 92, s 70” points to section 70 of the Social Security Contributions and Benefits Act 1992. It does not, by itself, establish which version applies to a person's circumstances.

The [machine-readable bridge](../domain-profile/reading-help-law/bridge.json) maps four abbreviated work titles to full titles, stable identifiers and official links. Each expansion retains its exact location in a captured DWP abbreviation table:

- Social Security Contributions and Benefits Act 1992;
- Social Security (Invalid Care Allowance) Regulations 1976;
- State Pension Credit Act 2002;
- State Pension Credit Regulations 2002.

The **comparison date** is 20 September 2026, matching the earlier statutory snapshot. It is distinct from the date of capture, commencement of a provision, and the date relevant to a benefits question. Applicability remains unresolved.

## Select a body marker or its reference row

The separate [Chapter 60 reference-row manifest](../reading-help-ch60-references.json) keeps the v1 reading-help format and all original source bytes. Twenty explicit pairs connect a body marker to its exact footer occurrence through the existing card identity. The original `reading-help-ch60.json` and pinned demonstration URL remain unchanged.

A compatible Reader can select either occurrence and navigate to its partner. Equal digits in paragraphs 60025 and 60033 are different identities. Mixed reference 12 remains unresolved, and the extra printed 2 is not assigned an invented body partner. This is a reference interaction repair, not a correction to the DWP source or a new legal conclusion.

## Existing evidence is reused

DWP already retained **20 selected statutory units from 16 provisions, with 43 navigation relationships**. A unit is a selected section, regulation or schedule paragraph. Those existing records and their limitations remain unchanged. The bridge links to relevant existing identities instead of copying or reacquiring their text.

This corrects the earlier legislation review's overly broad claim that there were no retained statutory bodies. The legislation catalogue itself is mainly work metadata and representation links. That does not describe DWP's separate, later body-evidence overlay. The [existing evidence report](legal-body-evidence.md) explains that overlay.

## Three new targets, four observed variants

The bounded capture requested section 70 of the 1992 Act and regulations 3 and 6 of the 1976 Regulations. It also made two rights checks. Each response was capped at 8 MiB, the aggregate at 32 MiB, with no automatic retries or redirects. The [request census](../source/reading-help-law-2026-09-26/request-census.json) records the outcome.

Section 70 contained **two geographical versions**: England and Wales, and Scotland. They share a canonical identifier but have different dated source URLs. The first projection selected one and failed its version check. That [original failed projection](../source/reading-help-law-2026-09-26/provisions/ukpga--1992--4--section--70.json) is preserved.

The [second projection](../source/reading-help-law-2026-09-26-v2/manifest.json) reused the same captured bytes, with **zero additional requests**, and retains both variants independently. No system should infer which applies merely from the shared identifier.

All four observed units retain the complete selected XML subtree, normalised text, source hash, source-native dated URL, surrounding restriction attributes and separate editorial commentary. Normalisation changes spacing and presentation; it does not summarise the wording. The public tree omits opaque source attributes with their hashes, so it is a **lossy projection**, not a reconstructible copy of the raw response. Exact successful responses remain in the content-addressed local audit cache on EXTSSD.

## What this does not establish

- A complete provision is not a complete set of its dependencies, exceptions, amendments and applicable case law.
- A reading-help link is navigation. It does not satisfy an evidence requirement or create a legal applicability relationship.
- The [context overlay](../domain-profile/reading-help-law/context-overlay.json) is admitted only into the separate [optional context index](../domain-profile/reading-help-law/assembly-index.json), after source and consumer-contract validation. This selected-evidence index is not full-corpus search. The deployed service and frozen question results remain unchanged.
- Malformed printed references remain unresolved. No new model-generated explanations or answer comparisons were run.

## Reproduce the offline checks

```sh
uv sync --locked
uv run --locked python scripts/build_reading_help_law.py --check
uv run --locked python scripts/build_reading_help_references.py --check
uv run --locked python -m unittest discover -s scripts -p test_reading_help_references.py
uv run --locked python -m unittest discover -s scripts -p test_reading_help_law.py
```

The acquisition and raw-cache re-projection commands are separate explicit operations. Ordinary validation never contacts legislation.gov.uk. Never rerun acquisition into an existing snapshot or replace an earlier failed attempt.

## Optional admission and measured limits

The [admission receipt](../domain-profile/reading-help-law/admission.json) records 16 citation mappings, two retained source passages, four work identities and four statutory variants. Exact source-page overlap links the passages to existing navigation. All 40 original evidence requirements and their unresolved obligations are preserved.

The new [Chapter 60 legal-links manifest](../reading-help-ch60-law.json) adds dated official targets while preserving the separate original demonstration. Five unsupported or malformed citation cards remain unresolved. A resolved link means the target identity was found; it does not mean the legal question is resolved.

**The first bounded natural-language retrieval probe failed to retain the bridge.** The [retained observation](../evaluation/reading-help-rollout/law-context-probe.json) records the unchanged 128 KiB, 32-record, 64-relationship, depth-three budget. The older selected-staff index resolves the broad alias “DMG” to imprisonment routing; broad relationships and byte pressure then omit the new passages. The new links are present and structurally valid, but this is not evidence of improved natural-language retrieval. Neither the question nor its budget was changed to hide the result. The optional index is not the default service release.

Run the independent engine-shape and retained-probe check with:

```sh
node --experimental-strip-types scripts/check_reading_help_law_context.mjs --explorer-root ../okf-explorer
```

The [first admission attempt](../evaluation/reading-help-rollout/failed-admission-01/law-context-probe.json) is preserved: it exposed missing source-capture timestamps and fragment hashes incorrectly supplied as complete-record hashes. The successor uses the original capture receipts, keeps each source-fragment digest in `evidence_unit.spans`, and binds every provenance literal digest to the complete record text. The engine now checks governance and fragment integrity for every added record and relationship before the unchanged retrieval probe. It still does not retain the bridge.

This check distinguishes valid admission from a failed selection observation. Broader semantic routing remains an open task.
