---
'@id': https://chris-page-gov.github.io/okf-dwp/id/resource/okf-uk-legislation
'@type': schema:CreativeWork
route: resource/okf-uk-legislation
title: UK Legislation and Whole-Law OKF
type: External reference
description: Independent OKF catalogue and legal-source research dependency, referenced at its
  frozen v0.3.0 commit. Useful for identities, provenance and evaluation design.
status: draft
authority: Project-authored reference to an independent, non-official knowledge framework.
generated:
  by: process:codex-research-authoring
  at: '2026-09-15T16:56:35Z'
observedAt: '2026-09-15T16:56:35Z'
publisher: https://github.com/chris-page-gov
resource:
  https://github.com/chris-page-gov/okf-uk-legislation/tree/3fd2700f275fff53d8605f38eb3257780ea591fa
source:
  https://github.com/chris-page-gov/okf-uk-legislation/blob/3fd2700f275fff53d8605f38eb3257780ea591fa/docs/uk-legislation-okf.md
license: https://github.com/chris-page-gov/okf-dwp/blob/main/LICENSE
schema:about:
  '@id': https://github.com/chris-page-gov/okf-uk-legislation
dcterms:accessRights: Public repository reference. Selected local Git objects were inspected; no
  remote bundle federation or provision acquisition is performed by this record.
dcterms:rights: MIT applies to this original reference record. The external repository and each
  underlying legal source retain their own applicable rights and attribution requirements.
dcterms:extent: Dependency metadata and links only. The external catalogue, source bodies and
  effects corpus are not copied into this DWP bundle.
evidence:
- https://github.com/chris-page-gov/okf-uk-legislation/blob/3fd2700f275fff53d8605f38eb3257780ea591fa/docs/uk-legislation-okf.md
- https://github.com/chris-page-gov/okf-uk-legislation/blob/3fd2700f275fff53d8605f38eb3257780ea591fa/whole-law/config/effects-seeds.json
tags:
- legislation
- Whole-Law
- OKF
- provenance
- external reference
- metadata only
sources:
- id: uk-legislation-architecture
  title: UK Legislation OKF architecture at the v0.3.0 commit
  resource:
    https://github.com/chris-page-gov/okf-uk-legislation/blob/3fd2700f275fff53d8605f38eb3257780ea591fa/docs/uk-legislation-okf.md
  author: organisation:chris-page-gov
id: resource/okf-uk-legislation
dcterms:references:
- '@id': https://chris-page-gov.github.io/okf-dwp/id/resource/state-pension-credit-act-2002
- '@id': https://chris-page-gov.github.io/okf-dwp/id/resource/state-pension-credit-regulations-2002
---

# UK Legislation and Whole-Law OKF

**Independent external knowledge framework, referenced at a fixed commit.**

[Inspect the pinned repository](https://github.com/chris-page-gov/okf-uk-legislation/tree/3fd2700f275fff53d8605f38eb3257780ea591fa) and its [legislation architecture](https://github.com/chris-page-gov/okf-uk-legislation/blob/3fd2700f275fff53d8605f38eb3257780ea591fa/docs/uk-legislation-okf.md).

The checked catalogue contains 365,786 work records, including the State Pension Credit Act 2002 and the State Pension Credit Regulations 2002. It preserves official work identifiers and links to versions and formats. Provision trees use selected official CLML on demand; a catalogue link is not frozen provision evidence in this DWP bundle.

The 14,712-row effects datapack covers a bounded 11-work seed acquisition. It contains no effect assertion involving either Pension Credit instrument. Its completeness must not be extended to Pension Credit or the full DMG.

Reusable design patterns include work, version and provision identity; evidence-bearing assertions; separate source authority and model interpretation; and proposition-level citation tests. The local sibling also has an unreleased richer semantic migration. That work is a design reference, not a published dependency for this bundle.

No current-law determination, remote federation or legal reasoning capability is implied by this external reference.


[Research reference: State Pension Credit Act 2002](https://github.com/chris-page-gov/okf-dwp/blob/main/bundle/records/resource/state-pension-credit-act-2002.md).

[Research reference: The State Pension Credit Regulations 2002](https://github.com/chris-page-gov/okf-dwp/blob/main/bundle/records/resource/state-pension-credit-regulations-2002.md).
