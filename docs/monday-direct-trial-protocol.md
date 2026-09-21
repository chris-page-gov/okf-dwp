# Proposed direct-JSON evidence trial

21 September 2026. **Offline candidate only. No source package is frozen for this
trial, no provider has been called and no new model success is claimed.** The
protocol remains `pending-final-source-package-runner-freeze`; execution refuses
before binary discovery, version checks or authentication.

## Purpose and scope

The earlier Claude trial used a provider formatting tool. This successor asks
for one JSON object directly and rejects every tool event, including that
formatter. It is a new experiment, not a correction to earlier results. The
retained observations establish that a terminal result string can contain JSON;
they do not establish how a schema-free invocation will behave.

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

- [Protocol](../evaluation/model-comparison/household-direct-v3/protocol.json)
- [Trusted prompt](../evaluation/model-comparison/household-direct-v3/prompt.md)
- [Answer schema](../evaluation/model-comparison/household-direct-v3/answer.schema.json)
- [Runner](../scripts/run_monday_direct_trials.py)
- [Versioned event recogniser](../scripts/monday_direct_events_v3.py)
- [Offline controls](../scripts/test_monday_direct_trials.py)

The new runner does not import historical trial runners, parsers or assessors.
The earlier protocols, contexts, outputs and reviews remain unchanged. Different
source content, prompts and provider output mechanisms prevent a causal speed,
accuracy, cost or formatter comparison with those observations.

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
   `evaluation/model-comparison/household-direct-v3/frozen/contexts/{case}.json`.
   Obtain SDK cases for **both exact questions**, with exact local-engine and
   compact-service reconstruction equality. The control is independently assembled, not created by
   deleting records from the substantive package.
2. Change only the reviewed protocol phase to `ready-for-freeze`. Commit the
   reviewed runner, helper, schema, prompt, protocol, packages and actual public
   SDK/deployment observations. Record separate exact DWP source, Explorer
   engine, service and trial-input commits. No commit is inferred from `main`.
3. Create a new `frozen/manifest.json` with schema
   `okf-direct-trial-freeze.v3` and the exact fields below. This manifest is
   created after the trial-input commit, avoiding a self-referential commit hash.
   Hash and independently review it before any call.

| Field | Required value |
| --- | --- |
| `trial_commit`, `source_commit`, `explorer_commit`, `service_commit` | Four explicit 40-character Git commit identifiers; identities may coincide only when the actual commits do. |
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
match its declared digest, size and immutable Git blob. The loaded Python files
must still match those frozen bytes. Root/parent/member symlinks and oversized
files are rejected before bounded reads.

The SDK observation must use `okf-versioned-remote-verification.v1` and identify
an actual successful public HTTP run. It binds the exact source, service comparator,
engine catalogue and expected local Worker digest. The runner verifies the
executed verifier’s digest against its immutable service commit. For both exact
questions, it checks source and engine identifiers, the complete four-field budget,
canonical package hash, bytes, record and relationship counts, evidence status,
provenance digest, ordered catalogue, compact text/structured value equality and
complete-package equality with the local reference. The empty control has its own
case classification. A recorded complete package read must carry the same digest.

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
uv run --locked python scripts/run_monday_direct_trials.py
uv run --locked python -m unittest discover -s scripts -p test_monday_direct_trials.py
```

After a reviewed freeze, preflight also requires the Explorer checkout containing
the exact engine and service commits:

```sh
uv run --locked python scripts/run_monday_direct_trials.py \
  --explorer-root /path/to/okf-explorer
```

**Future authorised execution only:** each explicit call adds `--run`, a named
provider and case, `--freeze-sha256` with the reviewed manifest digest, and
`--authorisation controls` or `--authorisation substantive`. The stage flag is
an explicit operator declaration, not an approval that the program grants
itself. Both verified empty-control receipts are required for the substantive
stage. All output goes to the fixed, fresh `attempt-01` directory under
`validation/model-comparison/household-direct-v3/{provider}/{case}/`.

The runner retains an attempt receipt even for authentication refusal, timeout,
overflow or rejected output. It publishes no raw CLI streams, reasoning, account
identifiers, local paths or arbitrary errors. Recognised model identities remain
separate for response and accounting roles; unknown identity strings are withheld
with a digest, and multiple identities are explicitly labelled. Numerical usage
is provider accounting, not a verified subscription charge or affordability
forecast. Executable hashes do not freeze dynamically loaded provider internals.

## Offline verification

**29 controls pass** using synthetic fixtures and local Python child processes.
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
