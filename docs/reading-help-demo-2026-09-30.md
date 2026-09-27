# Demonstrate source-linked reading help

This is an independent experimental reading aid, not official DWP guidance or a
benefits calculator. DMG means **Decision makers’ guide**; ADM means **Advice for
decision making**. Both are DWP staff manuals with different scopes and histories.

Publication state: candidate under technical checks. The release record will
supply exact pinned links after paired data and consumer verification. Keep the
[verified Chapter 60 demonstration](reading-help-ch60.md) as the fallback.

## Pinned candidate links

These immutable data links require the companion Explorer consumer from PR 158.
They become presentation links only after the public verification receipt passes.

- [Corpus reading help — Chapter 60, paragraph 60025](https://chris-page-gov.github.io/okf-explorer/reading-help/corpus/?catalogue=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F115397c19e0b1e1e16d476df788c33a1196a3990%2Freading-help-corpus%2Fmanifest.json&catalogue_sha256=acb63e18d10c1a8a0a6c7d57f8ebfc41948e3837cd27c4589d4540061507d8a6&catalogue_bytes=260797&family=dmg&document=dmg-vol10-ch60&unit=https%3A%2F%2Fchris-page-gov.github.io%2Fokf-dwp%2Fid%2Funit%2Fdmg%2Fdmg-vol10-ch60%2Fmanual-structure-v1%2Fsource-0000002117-000-5fac0d6d5c5e)
- [Paired body/footer references and dated statutory links](https://chris-page-gov.github.io/okf-explorer/reading-help/?manifest=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2Fa314fc708e512bb4827a1cdacb8158709a02c3d9%2Freading-help-ch60-law.json&passage=dmg-60025)
- [All 40 staff questions — start at the calculation question](https://chris-page-gov.github.io/okf-explorer/evidence/?manifest=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2Fa314fc708e512bb4827a1cdacb8158709a02c3d9%2Fevaluation%2Fevidence-workbench%2Freading-help-manifest.json&case=staff-016)

## A five-minute walkthrough

1. Open the corpus reading-help catalogue. Explain that **513 processed
   documents** means every captured PDF has a recorded outcome. It does not mean
   every rule or explanation has been reviewed.
2. Choose DMG, then Chapter 60 and paragraph 60025. Select an abbreviation.
   Compare the exact extracted source with the separately labelled proposed
   expansion. Open the original PDF and check the locator.
3. Open the bounded Chapter 60 reference demonstration. Select a raised body
   marker, follow its exact paired footer occurrence and return. Explain that
   a repeated number elsewhere is a different occurrence. Unresolved references
   stay unresolved.
4. Follow a dated statutory link. A **provision** is a section or regulation
   within a legal work. Show its complete retained text, any bounded excerpt,
   date and geographical variant. A complete provision is still not a complete
   set of legal dependencies.
5. Open the 40-question evidence workbench. Choose a retained evidence record
   and open its exact reading-help passage. The retained packages, evidence
   requirements and insufficient status have not been changed by this link.
6. Show an extraction gap and a proposed meaning. This makes the boundary of the
   processing visible rather than presenting machine extraction as reviewed law.

## What the measurements mean

The full processing ledger accounts for 19,090 pages and 53,727 original
structural units; 893 pages have no extracted text. Missing extraction does not
show that a PDF page is blank. The later amendment candidate is separate.

The [40-question replay](../evaluation/reading-help-rollout/replays/reading-help-20260927-01/report.json)
used the same frozen source, engine and budgets in both arms. All 40 packages
were byte-identical and remain insufficient. This establishes non-regression,
not retrieval improvement or better model answers. No new answer-model calls
were made.

For the source-led small and held-out controls, use the results linked from the
[rollout report](reading-help-rollout.md). Failed attempts are retained. Passing
hash, span and navigation checks does not replace independent specialist review.

## Questions to ask during review

- Does the complete passage retain its heading, qualifications and continuation?
- Does an abbreviation's proposed meaning belong to this manual and source scope?
- Does a citation link to the intended work, provision, date and territory?
- What remains unresolved, and which evidence would resolve it?

The [glossary](glossary.md) explains terminology as it is encountered. The
[work log](reading-help-rollout-work-log.md) and generated
[delivery ledger](backlog-work-packages.md) distinguish implementation from
publication, legal answerability and specialist acceptance.
