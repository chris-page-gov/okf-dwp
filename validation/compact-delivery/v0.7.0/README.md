# Service 0.7.0 release evidence

This directory retains preparation and, when present, actual publication and
public verification records for the Evidence Connect service admission.
The [shared publication record](../../../docs/service-publication.md) identifies
which deployment and SDK observation have been accepted together.

## Preparation

The service admits the immutable DWP source
`7eeded763042ddd0070f4fed834c6074149e8e2f` with the Explorer assembler from
`d6930bbcddaab616deec002d9e6efff6e3aae953`. The five earlier sources and two
historical engines remain available in their existing combinations.

The retained candidate plans cover ten permitted source/engine pairs, the
original historical replay and an unknown-term control: twelve cases. Their
138-request allowance is a predicted upper bound, not an actual request count.
Preparing a plan makes no network or model calls. Later service changes require
their own exact committed build and matching observation.

The first preparation attempt exposed a circular verifier import and exited
with an unsettled top-level await before producing a result. Its log is retained
under `preparation/history/`. A later local invocation also stopped before a
passing result; its immediate cause was not independently established and it
must not be counted as a successful observation.
The next candidate passed. CI then exposed a separate review-page regression:
editing a historical question selected an incompatible current engine. The
review and replay interfaces now share source-specific engine selection, checked
across all six sources and by four Chrome review tests. `offline-attempt05`
records the subsequently corrected candidate.

## Recorded publication and public checks

Explorer PR149 merged as `31d8c3436ed289bfd694b7889a9e5edea834ea8b`.
Its exact build was uploaded as Sites version 12 and published on 25 September.
The [hosting receipt](deployment.json) retains the source, archive and Worker
identities. The [public SDK observation](sdk/attempt-01/observation.json) passed
all twelve cases in **135 actual requests**, below the 138-request plan.
Ten permitted source/engine combinations, the original historical replay and
the unknown-term control retain exact reconstruction and bounded delivery.
The exact merged offline plan is under `preparation/offline-merged/`.

The [native client observation](../../client-connection/2026-09-25/remote/README.md)
separately records a stale schema rejection, unchanged-permission refresh and
successful exact diagnostics reconstruction in the same existing task.

## Boundaries

Small deliveries reconstruct the selected evidence package; they do not repair
missing source qualifications, establish legal applicability or prove specialist
acceptance. The hosting receipt binds the submitted archive to its source. The
public health endpoint does not independently attest deployed Worker bytes.
Sidebar page-tool observations are recorded separately under
[client connection](../../client-connection/2026-09-25/sidebar/README.md).
