# Full DMG relationship audit

## What is preserved

The [reproducible audit](../scripts/audit_relationships.py) checks every authored semantic relationship and ordinary research reference against the semantic shards, runtime relationship shards, direct triples, endpoint labels and incoming/outgoing adjacency index. The [receipt](../evaluation/relationship-audit.json) binds all inspected inputs by SHA-256.

For snapshot `dwp-full-dmg-2026-09-16-a26a93daa9f5`:

| Check | Result |
| --- | ---: |
| Authored semantic relationships preserved | 343 of 343, across 224 files |
| Authored research references preserved | 787 of 787 |
| Semantic assertions matching runtime relationships | 16,336 of 16,336 |
| Resolved record endpoints | All 15,404 records |
| Incoming and outgoing incident rows preserved | 32,672 |
| Missing authored relationships, changed supporting passages or duplicate triples | 0 |

This rules out missing authored relationships, unresolved endpoint identities and missing incoming adjacency as the explanation for this snapshot's graph. It does not establish that the domain has been fully modelled.

## What is still sparse

Of the 16,336 assertions, 15,074 express document/page containment. They say where material belongs, rather than describing a benefit rule or a useful cross-reference. Only 419 of the 14,743 source pages have a relationship beyond containment; 14,324 have only containment. There are 282 authored concepts.

The separate dependency reconciliation records 46,144 literal citation candidates. These include 16,927 single acquired-location candidates, 538 ambiguous locations and unresolved legal identifiers or locations. They are not automatically graph assertions. A mechanical location match is not proof of legal equivalence, applicability or a correct relationship. More source-backed relationships can be modelled without pretending that every extracted reference is already resolved policy knowledge.

## Explorer display defects identified

Inspection of the pre-fix large-corpus UI identified separate display losses even though the underlying edges were present:

1. A selected graph used only the first 120 incident rows before grouping. Forty-six routes exceed that limit. Chapter 78 has 211 incident rows; the 91 later rows include the imprisonment routing edge from `page/dmg-vol3-ch12/0003`, a research question and a child-responsibility concept reference. This is a rendering selection problem, not absent source relationships.
2. With no selected record, Links accepted only sources whose route started with `dataset/`. The DWP records use routes such as `term/`, `page/`, `chapter/` and `document/`; none of its 16,336 relationship sources has that prefix. Consequently the overview Links list could be empty despite a fully loaded relationship index.
3. Relationship stacks toggled the graph's expanded-state list, but their rendering did not read that state. A stack could therefore look interactive without opening its member relationships.

These findings come from the checked data and implementation, not a claim that all browser states have been tested. The Explorer fixes and their UI regressions are tracked separately from this publication-data audit.

Both directions are available in the adjacency index. Explorer groups edges by direction relative to the selected record and can hide groups, authority classes and node types. These filters are empty by default but can be restored from a shared URL. The data has no optional model-enrichment sidecar, so an unavailable sidecar is not the cause here. The full index is below Explorer's 100,000-relationship UI hydration safety limit and its 300,000-row loader limit.

## Reproduce the publication-data check

```sh
uv sync --locked
uv run --locked python scripts/audit_relationships.py --check
```

Regenerate with the same command without `--check` only after reviewing changed authored or generated inputs. The script uses no network and writes only the receipt when explicitly run in regeneration mode. A passing receipt verifies preservation and identity; it does not certify live rendering, full semantic coverage, source legal currency or answerability.
