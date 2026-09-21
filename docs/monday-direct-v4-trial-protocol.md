# Direct-JSON evidence trial v4: metadata compatibility candidate

21 September 2026. **Offline candidate only. No source package is frozen for this
trial, no provider has been called and no new model success is claimed.** The
protocol remains `pending-final-source-package-runner-freeze`; execution refuses
before binary discovery, version checks or authentication.

## Purpose and scope

Both actual v3 controls exited successfully but were rejected by their strict
parsers. Claude reported `unknown-or-missing-wrapper-field`; Codex reported
`unrecognised-usage-shape`. Their tool censuses remain unknown and no v3 substantive
call was made. The old recogniser retained neither the rejected field name nor the
answers, so this successor cannot recover or reclassify those calls.

V4 admits only additional metadata supported by the installed CLI or previously
public, value-free shape receipts. It retains bounded structural diagnostics on
failure. It still asks for one direct JSON object and rejects every tool event,
including the formatter used in older experiments. No actual v4 result exists.

The two providers receive exactly the same complete evidence bytes for each case:

1. The existing unknown-term control, `xylophonicquasarteleportation`, assembled
   independently into an empty, insufficient package.
2. The original Staff 012 question, preserving its wording and typo:
   “Does Pension Credit stop is a citizen moves into a care home permanently if
   they are self-funding?”

The question must equal `package.question`. No no-partner fact is added. The
preregistered package budget is **512 KiB**, with the existing 64-record,
128-relationship and six-hop limits. Final source and service replay evidence
must show what that actual package contains and omits before freezing it.

Both empty controls must produce accepted event formats, valid JSON and correct
abstention before a separately authorised substantive attempt. There is one
`attempt-01` per provider and case: at most four model calls, no automatic retry,
no alternative attempt name, no repaired JSON and no replacement evidence.

## Files and separation from earlier trials

- [Protocol](../evaluation/model-comparison/household-direct-v4/protocol.json)
- [Trusted prompt](../evaluation/model-comparison/household-direct-v4/prompt.md)
- [Answer schema](../evaluation/model-comparison/household-direct-v4/answer.schema.json)
- [Runner](../scripts/run_monday_direct_v4_trials.py)
- [Versioned event recogniser](../scripts/monday_direct_events_v4.py)
- [Offline controls](../scripts/test_monday_direct_v4_trials.py)

The new runner does not import historical trial runners, parsers or assessors.
The earlier protocols, contexts, outputs and reviews remain unchanged. The exact public source packages, question, authored prompt and answer schema
must equal v3; parser compatibility and catalogue handling are the changes.
The earlier compact experiments changed source/prompt/mechanism as well. None of
these small runs supports causal accuracy, speed, cost or formatter claims.

## Provider and output controls

Claude keeps its subscription CLI, safe mode, empty tools and strict empty MCP
configuration, disabled Chrome integration and slash commands, no persisted
session, `dontAsk` permission mode, and `stream-json --verbose` output. It omits
`--json-schema`. Codex keeps the previously used isolated subscription command,
read-only sandbox, ignored user configuration/rules, disabled execution, apps,
agents, web, memories, hooks and remote plugins, ephemeral session and local
`--output-schema` mechanism. Discovered user skill paths are disabled with
process-local settings. Persistent user configuration is never edited.

These are requested controls, not proof of identical provider system context.
In particular, the exact previously observed Codex skill-catalogue warning is
recognised and recorded as a limitation. Unknown errors are rejected. No model
or fallback-model argument is added. The environment removes API credentials,
provider-routing, proxy and model overrides while retaining CLI/keychain paths
needed for the existing subscription. Fresh authentication must report the
subscription category; failure consumes the attempt and does not trigger repair.

The model process has a **240-second timeout**, **2 MiB stdout** and **512 KiB
stderr** ceilings. Process termination and stream cleanup can take additional
bounded time; authentication and version observations have separate 15- and
10-second bounds. A timeout or overflow is retained as a failure. Stream hashes
on an incomplete capture describe only captured bytes. A process-group kill
that is unavailable on the host is recorded; the runner falls back to killing
its direct child and rejects unsuccessful cleanup.

Accepted streams need exactly one successful terminal event, at the end, and
process exit code zero. Only explicitly recognised wrappers, scalar types,
content and telemetry shapes are admitted. Every tool-use/result event is
rejected, including `StructuredOutput`; unknown categories leave the census
unknown. No unknown category is printed as a dynamic telemetry key.

The final answer must be one JSON object. Duplicate keys, non-finite numbers,
unpaired Unicode surrogates, fences, trailing text and multiple answer candidates
are rejected. Claude’s terminal result must agree with its sole assistant text
when present; absence of that confirmation is recorded. Codex must have exactly
one completed assistant message. Neither provider’s output is repaired.

The schema permits at most **three claims**, **two citations per claim** and
**16 KiB** for the raw final answer and retained answer file. Insufficient
packages permit only `partial_evidence_only` or `cannot_establish`; abstention
cannot contain claims. Mechanical checks verify case/context identity, unchanged
evidence status, exact selected-record quotations and matching provenance URL
and locator. Truncated packages require an explicit summary statement. These
checks cannot establish that a quotation supports its claim or preserves all
controlling qualifications; independent claim review remains necessary.

## Final freeze interface

The freeze is deliberately absent. After source/service integration and review:

1. Assemble the two actual packages at the fixed budget. Preserve their complete
   canonical bytes under
   `evaluation/model-comparison/household-direct-v4/frozen/contexts/{case}.json`.
   Obtain SDK cases for **both exact questions**, with exact local-engine and
   compact-service reconstruction equality. The control is independently assembled, not created by
   deleting records from the substantive package.
2. Change only the reviewed protocol phase to `ready-for-freeze`. Commit the
   reviewed runner, helper, schema, prompt, protocol, packages and actual public
   SDK/deployment observations. Record separate exact DWP source, Explorer
   engine, deployed service, SDK verifier and trial-input commits. No commit is inferred from `main`.
3. Create a new `frozen/manifest.json` with schema
   `okf-direct-trial-freeze.v4` and the exact fields below. This manifest is
   created after the trial-input commit, avoiding a self-referential commit hash.
   Hash and independently review it before any call.

| Field | Required value |
| --- | --- |
| `trial_commit`, `source_commit`, `explorer_commit`, `service_commit`, `verifier_commit` | Five explicit 40-character Git commit identifiers. `service_commit` identifies the deployed runtime; `verifier_commit` identifies the successful SDK comparison and verifier. A verifier-only correction does not change the deployment identity. |
| `worker_sha256`, `service_version` | The separately recorded hosting Worker digest and service version; the SDK compares local Worker bytes but does not attest hosted bytes. |
| `sdk_receipt`, `deployment` | Explicit public paths `validation/compact-delivery/vX.Y.Z/sdk/attempt-NN/observation.json` and the same release’s `deployment.json`. A failed attempt stays preserved; a later attempt needs separate authorisation and its exact path. |
| `inputs` | Exactly the runner’s `TRIAL_FILES`, `SOURCE_FILES`, both public receipt paths, the two context paths and the two original compressed package artefacts named by the cases. Each entry contains `path`, `bytes`, `sha256`, `commit`. Source files bind to `source_commit`; other files bind to `trial_commit`. |
| `engine_modules` | An object with `index.ts`, `corpus.ts`, `types.ts` mapped to exact SHA-256 digests. The runner checks original Git bytes at the engine commit against the vendored adapter bytes and manifest at the service commit. It does not assume that the service’s current app files represent every versioned adapter. |
| `engine_id` | The content-addressed engine identifier derived from the exact vendored engine manifest. |
| `cases` | Exactly `control-unknown`, then `staff-012`; each entry contains `id`, `context_id`, `bytes`, `sha256`, `sdk_case_id` and `received_package`. The last two name the actual observation case and original compressed artefact below that observation directory. |

`TRIAL_FILES` includes the three specification files, both executable Python
files, `pyproject.toml` and `uv.lock`. `SOURCE_FILES` includes
`combined/context/corpus/manifest.json`, its `base-index.json` and the original
staff-question register. The actual corpus bundle identity differs from the
authored semantic index identity; the trial uses the corpus identity. Every file must
match its declared digest, size and immutable Git blob. Historical corpus and
question-register data are read from their explicit source commit, so a later
working-tree bundle cannot substitute newer evidence. Executable and trial
inputs additionally have to match the reviewed working files. The loaded Python files
must still match those frozen bytes. Root/parent/member symlinks and oversized
files are rejected before bounded reads.

The SDK observation must use `okf-versioned-remote-verification.v1` and identify
an actual successful public HTTP run. It binds the exact source, verifier comparator,
engine catalogue and expected local Worker digest. The runner requires its
`comparison_commit` to equal `verifier_commit` and verifies the executed verifier’s
digest against that immutable commit. Deployment and vendored engine bindings
continue to use `service_commit`. For both exact
questions, it checks source and engine identifiers, the complete four-field budget,
canonical package hash, bytes, record and relationship counts, evidence status,
provenance digest, ordered catalogue, compact text/structured value equality and
complete-package equality with the local reference. The empty control has its own
case classification. A recorded complete package read must carry the same digest.

A verifier-only correction is admitted only when the two commits have identical
Git object inventories for the runtime and local comparator dependencies:
service source and vendor directories, package manifests/lock, build and approved
comparison helpers, the four shared context modules and two context schemas.
The census includes additions and deletions, rejects symlink modes, and is bounded
to 256 entries/1 MiB/10 seconds per commit. Only Git objects are read; neither
revision is executed by this check. The verifier and its tests/documentation are
outside that runtime census. The expected Worker hash must still match both the
SDK observation and separate deployment evidence.

The reviewed correction `03d0264c02a6d59d75013df4bffba279b3d4aa9c` and deployed
runtime `0472b75a9dd353d6094a83ca9f752c4d78914168` have the same 44-entry runtime
inventory, SHA-256 `003c291ec51b93fb7483a959c0b58cd6cedc54009995ab9f62a9408a045b64aa`.
This local source comparison does not replace the actual successful SDK or
hosting receipts required before freezing a trial.

The original compressed package artefacts must match both their SDK artefact
bindings and immutable Git inputs. Bounded decompression must reproduce the exact
frozen context bytes. No second full `ask_okf` call is required or claimed: the
observation explicitly records zero full-tool and model calls. The package’s bundle
and manifest binding must match the combined corpus manifest, whose base-index
bytes are checked. Every package also has exact protocol limits, consistent used
counts, bounded actual counts and depth, and verified source literal hashes.

Hosting proof remains separate. The deployment record must bind the source,
service commit/version, Worker and archive digests, a site version and a successful
publication of that same version at the observed origin. The SDK explicitly
retains `deployed_worker_bytes_independently_verified: false`: health and successful
compact delivery cannot themselves prove which Worker bytes the host deployed.
A service URL alone cannot satisfy these gates. This preflight verifies retained
observation evidence; it makes no network call and does not replay the assembler.

The reviewer must confirm the SDK’s actual replay and source coverage before
approving the freeze. This small trial harness is not a replacement for the
service SDK, source builders or whole-corpus integrity checks.

## Commands

The current default is safe and offline:

```sh
uv run --locked python scripts/run_monday_direct_v4_trials.py
uv run --locked python -m unittest discover -s scripts -p test_monday_direct_v4_trials.py
```

After a reviewed freeze, preflight also requires the Explorer checkout containing
the exact engine and service commits:

```sh
uv run --locked python scripts/run_monday_direct_v4_trials.py \
  --explorer-root /path/to/okf-explorer
```

**Future authorised execution only:** each explicit call adds `--run`, a named
provider and case, `--freeze-sha256` with the reviewed manifest digest, and
`--authorisation controls` or `--authorisation substantive`. The stage flag is
an explicit operator declaration, not an approval that the program grants
itself. Both verified empty-control receipts are required for the substantive
stage. All output goes to the fixed, fresh `attempt-01` directory under
`validation/model-comparison/household-direct-v4/{provider}/{case}/`.

The runner retains an attempt receipt even for authentication refusal, timeout,
overflow or rejected output. It publishes no raw CLI streams, reasoning, account
identifiers, local paths or arbitrary errors. Recognised model identities remain
separate for response and accounting roles; unknown identity strings are withheld
with a digest, and multiple identities are explicitly labelled. Numerical usage
is provider accounting, not a verified subscription charge or affordability
forecast. Executable hashes do not freeze dynamically loaded provider internals.

## Offline verification

**39 controls pass** using synthetic fixtures and local Python child processes.
They exercise stream and answer bounds, malformed wrappers, duplicate JSON,
terminal success, unknown events, zero formatter exceptions, model-identity
privacy, literal/source checks, changed freeze bindings, immutable commit checks,
symlink and raced-FIFO guards, authentication categories, reused directories and
both-control gating. New controls cover the combined source versus authored-index
identity, versioned compact reconstruction, compressed artefact tampering and
inflation, separate hosting evidence, complete budget counts and oversized integer
telemetry. Numeric telemetry is bounded to the exact JSON integer range; malformed
usage is rejected while preserving an attempt receipt. A retained public Claude terminal string is wrapped only as a labelled
synthetic parser fixture; its historical formatter invocation remains unchanged.

Passing these tests is an engineering result. Actual direct-JSON provider
behaviour, model answers, semantic correctness and specialist acceptance remain
unmeasured. A failed control stops progression; it does not authorise a new
exception or an automatic retry.

## Exact metadata additions and evidence

[Local format evidence](../evaluation/model-comparison/household-direct-v4/local-format-evidence.json)
records installed binary digests, bounded schema/emitter fragments with byte offsets,
and prior public diagnostic receipt digests. It contains no account history or raw
provider output. Installed Claude is 2.1.278 and Codex is 0.146.1, matching the failed
v3 receipts. Local installed code, rather than guessed documentation, supports the
new field names. Historical rejected fields themselves remain unknown.

| Area | New recognition | Bounds and refusal policy |
| --- | --- | --- |
| Codex `turn.completed.usage` | `cache_write_input_tokens`, `reasoning_output_tokens` | Non-negative finite JSON-safe numbers, excluding booleans; other unknown usage keys reject. The native exec serialisation lists all five field names. |
| Claude `system/init` | `betas`, `capabilities`, analytics/product-feedback flags, fast-mode reason, messaging/scratchpad/PowerShell paths, worker epoch, optional effort and empty diagnostics/terminal-command arrays | Fixed field list; strings at most 4,096 characters, string catalogues at most 128 entries; optional effort is null or its documented enum. Path values are never retained. Unobserved extensions remain rejected. |
| Claude advertised catalogues | `agents` and structurally validated `plugins` | Counts and canonical digests only, maximum 128 agents / 32 plugins. Advertising is not execution. Tools/MCP must be empty; slash commands and skills remain empty. |
| Claude assistant wrapper | `timestamp`, `request_id` | Bounded strings, withheld from public output. |
| Claude assistant message | null `container`, `stop_details`, `diagnostics`, `context_management`; empty `input_transformations` | Any substantive content in these fields rejects. Tool/use/result blocks still reject, including hidden wire-tool fields. |
| Claude result | Observed timing fields, queued-turn/result counters, fast-mode metadata, null API error status, `terminal_reason`, `subagent_stats` | Terminal reason must be `completed`; queued turns must be 0; the exact documented subagent structure must contain only zero counters and empty `by_type`. |
| Claude accounting | Thinking-token counters, `webSearchRequests`, bounded canonical/provider/cost-basis labels; nullable documented counters; per-iteration counter arrays | Labels do not establish the response model and are not retained. Every web-tool counter must be 0. At most 64 iterations with only the observed fields; unknown extensions reject. |

Claude's prior safe-mode diagnostic advertised four agents and a plugin. V3's
assumption that every advertised catalogue must be empty was stronger than the
actual isolation evidence. V4 records their bounded counts/digests and explicitly
states that provider system contexts are not proved empty or identical. This
change does not admit a tool call: any tool-use/result event, nonzero server-tool
counter, nonzero subagent counter, formatter output or unknown wrapper still
fails. Zero observed tools is a statement about the complete recognised stream,
not proof of unobservable provider infrastructure activity.

### Failure diagnostics

The recogniser retains a value-free structural census before event acceptance:
fixed public field names, scalar types, array lengths and bounded child shapes.
Unknown keys and all dynamic-map keys are hashed. Text, reasoning, model answers,
credentials, paths, identifiers and arbitrary error values are never retained in
this diagnostic. The failing event index and last validated index are recorded;
this does not mark the stream complete. Caps are 128 events, eight levels, 2,048
visited nodes, 64 fields/object, eight samples/array and 32 KiB formatted shape data.
Overflow returns a labelled cutoff/hash rather than accepting the stream.

Additional controls cover the two Codex counters, full synthetic Claude observed
metadata, catalogue-versus-execution distinction, zero subagent/server-tool
counters, unknown extensions, dynamic key privacy and diagnostic size bounds.
These are synthetic compatibility checks. If an actual control still rejects,
stop and inspect its value-free diagnostic; do not relax unknown-field rejection
or retry the frozen experiment.

## Historical failure preservation and next gate

[V3 control receipts](../validation/model-comparison/household-direct-v3/README.md)
remain rejected, immutable and independently inspectable. V4 has its own names,
protocol, freeze, attempts and outputs. Its copied runner still requires exact
same-source public reconstruction, five immutable commit identities, loaded-code
integrity and both accepted control receipts before a separately authorised
substantive pair. No paid API, model override, formatter, automatic retry or
persistent setting change is introduced.

### Independent review correction

The independent reviewer reproduced malformed scalar counters accepted as objects,
including `webSearchRequests={"input_tokens":1}`. V4 now permits dictionary values
only for the explicitly structured usage keys, with a separate child-key allowlist
and numeric leaves for each. Scalar counters cannot recurse. Negative controls
cover both Codex additions, the Claude web counter in main and per-model accounting,
wrong child fields, nested objects, booleans and numeric substitutes for structures.
Documented nullable usage forms remain distinct from numerical zero. The protocol
lifecycle test accepts only a pending draft or a ready protocol with its frozen
manifest present; pending refusal is always tested with a synthetic pending value.
