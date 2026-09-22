# Legacy candidate locations and new source units

The old combined corpus has 40 authored staff research requirements and 203 explicit unresolved obligations. The logical-unit projection kept its new unit profiles but dropped the old page routes and requirements. The [location policy](legacy-location-policy.yamlld) restores those requirements unchanged and adds a separate navigation layer into complete source units.

This is a location migration, not source review or a declaration that any question is answerable. A page locates source material. A unit supplies its full retained text, including any continuation beyond that page. Geometric overlap between them does not establish relevance, legal applicability or completeness.

## What the compiler preserves

The [compiler](../../scripts/structured_location_migration.py) appends every original requirement byte-for-byte as a parsed record: identifiers, required pages, existing concept requirements, required paths, triggers, limitations and all 203 obligation identifiers. It does not substitute unit identifiers for old required pages or replace an original required-path assertion. New unit navigation therefore cannot satisfy the old requirement merely by overlapping its source location.

For each of the 42 original candidates, the compiler checks its frozen extraction hash, PDF identity, exact page and excerpt literal. It converts the original Unicode-character offsets to exact UTF-8 byte offsets. A destination is the complete existing unit whose source spans intersect that location; complete-record hashes and every source span, including continuation pages, must match. Source text, source roles and original machine or author-declared boundary status remain unchanged.

Two kinds of navigation remain distinct:

1. **Restored original route:** retain the original concept prefix and point a new final navigation assertion at the overlapping unit. The original required path stays unchanged and unsatisfied by this new assertion. Every inherited prefix assertion must exist identically in the actual semantic input; an absent or changed prefix is recorded as unresolved and no complete restored route is emitted.
2. **Inferred profile-candidate route:** where the old profile names a required candidate but has no original path, the policy explicitly permits a new research association from its last declared trigger. The missing original route remains recorded. This is model-derived navigation, not restoration of a source assertion or a legal dependency.

Both kinds require all the profile's declared concepts through the reusable `context_guard`. The compiler never examines question wording to choose a route and never invents a source or a concept. Each assertion retains its original candidate/profile scope and the destination's source provenance.

## Initial diagnostic and limits

The bounded preview against the 52,841-unit catalogue finds navigation for all 40 profiles: 312 restored route observations and 32 inferred route observations, producing 344 new assertions. There are 28 original profile-candidate associations with no original path; they remain explicit even where inferred navigation is added.

Thirty-nine candidate locations map fully. Three retain small gaps totalling eight whitespace bytes, because empty spans have no runtime evidence record. Their exact offsets and literal hashes remain visible as partial mappings. This is a byte-location observation, not a substantive evidence gap or a reason to invent an empty evidence unit.

**Zero requirements are closed by this migration.** Report location coverage, original profile activation, source-read unit-profile support and specialist/legal acceptance separately. A large full unit can still exceed a context budget; the engine must disclose that omission. New routes do not remove the need to review qualifications or follow unresolved references.

The [twelve controls](../../scripts/test_structured_location_migration.py) verify unchanged requirements, the 203 open identities, separate old/new path identities, full cross-page examples, exact Unicode conversion, explicit missing locations, guarded scopes, inferred/restored distinctions, source tampering, duplicate application and registered input binding. This authoring review does not itself activate or publish the projection.

Independent review found that the first draft checked prefix assertions against the legacy index without checking their presence in the new graph. The test adapter also initially omitted the v3 adjacency shards. Both were corrected: the adapter loads the hash-bound frozen logical index with its complete inherited graph, and the compiler fails closed for an absent prefix. A negative control removes that graph and retains 25 unresolved original prefixes, affecting 55 potential unit routes. The initial failed adapter observations do not count as runtime or source acceptance.

The [later catalogue compatibility check](../../evaluation/manual-structure/selection-proposals/final-catalogue-compatibility-2026-09-23.json) repeats the 16 selection and 12 migration controls against `dwp-structured-units-9d7908c23642199bb048` (53,727 units). All declared selection identities and the 344 location-navigation routes remain unchanged. The preceding receipts retain their original, earlier catalogue identities.
