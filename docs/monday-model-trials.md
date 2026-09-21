# Paired evidence trials for Monday

**The latest paired question is the [direct-v4 care-home trial](../validation/model-comparison/household-direct-v4/README.md): both controls and both substantive responses pass mechanical checks with no observed tools. The separate agent review of six claims and seven citations records omitted exceptions and an overstated evidence gap in one answer; specialist acceptance remains pending.**

The earlier [separate successor outcomes](../validation/model-comparison/household-compact-v2/README.md).** The successor uses the same governed evidence through a reversible, ID-referenced representation and separately reviewed CLI event recognition. Its nine attempts include seven parser-accepted responses, one formatter rejection and one timeout. Six responses pass mechanical checks; Staff 008 fails a source-locator check. Both unknown-term controls abstain correctly, but no substantive pair is complete. The [claim-level model critique](../validation/model-comparison/household-compact-v2/claim-level-model-critique.json) records scope, qualification and attribution concerns in the five substantive answers. An accepted output format and exact quotations do not establish legal correctness.

The [successor protocol and frozen manifest](../evaluation/model-comparison/household-compact-v2-candidate/README.md) bind reviewed source commit `78a8beea97242d646eb9159860dea190ca5e2998`; the manifest SHA-256 is `faefc7f42282c2f8dfdee119ff6d30f26b537b73b43b1b9ed133c3befbef4678`. Repeated JSON values move to a dictionary: all six original contexts reconstruct byte for byte, including headings, exceptions, source metadata and missing-evidence declarations. The substantive packets are 11.8–14.9% smaller; the empty control is 916 bytes larger. No accuracy, latency or affordability improvement follows from those size measurements.

## Preserved direct-v3 controls

A [separately frozen v3 experiment](../validation/model-comparison/household-direct-v3/README.md) used the actual 0.6.0 public packages. Both empty-evidence controls exited successfully but were rejected for unrecognised CLI metadata. No substantive calls were made. These are harness compatibility failures, not assessed benefits answers. Earlier accepted responses, rejected attempts and claim critiques remain unchanged below.

## Historical first household experiment

**The original five subscription attempts remain unchanged: none yielded a response accepted by its frozen controls. No further calls or retries use that experiment.** Its six context packages and offline replay bind DWP commit `3ef0e786e9a18e76fa17c7d925ff509d6d6c9f84` and Explorer engine commit `0e6a639f87c4060123b72d82c1ebe30405d475f1`. This is also separate from the [retained 20 September trials](staff-model-trials.md); their inputs, scripts, results and failures remain unchanged.

The [frozen catalogue](../evaluation/model-comparison/household-2026-09-21/frozen/manifest.json) has SHA-256 `9fd2755fa6b0ac36345c4245162da97565f1a27b37b8b11e990a803c5f6a7719`. The [pre-model input review](../evaluation/model-comparison/household-2026-09-21/pre-model-input-review.json) confirms that the no-partner heading is present for Staff 012 and records relevant neighbouring pages that the budget omitted. All five substantive packages remain insufficient and truncated; the unknown-term control contains no records. This is a model-authored source comparison, not specialist acceptance.

A **paired trial** gives two AI clients the same question, evidence and authored instructions. It helps us inspect whether their claims preserve the evidence. It does not establish accuracy, affordability, a preferred model or a specialist-approved benefits answer.

## Questions chosen before answers

The [protocol](../evaluation/model-comparison/household-2026-09-21/protocol.json) selects six cases:

| Case | Reason for inclusion |
| --- | --- |
| Staff 012: permanent care-home residence and self-funding | Both previous answers omitted the no-partner heading above DMG 78088. |
| Staff 020: Pension Credit entitlement | Inspect the expanded household and mixed-age paths without assuming all eligibility conditions are established. |
| Staff 005: additional benefits alongside State Pension | Inspect new benefit-specific paths and whether the model avoids treating a qualifying link as automatic entitlement. |
| Staff 026: Child DLA and PIP | Preserve the dated cohort and benefit-variant restrictions highlighted by the earlier review. |
| Staff 008: SDA | Keep the two possible meanings visible; do not silently select one. |
| Unknown-term control | Require no claims when the supplied package has no evidence. |

The supplied question wording remains unchanged in the staff registry. **DLA** means Disability Living Allowance; **PIP** means Personal Independence Payment. **SDA** is ambiguous here: it may refer to Severe Disablement Allowance or an informal shorthand for a severe-disability additional amount. Those meanings are not interchangeable.

Every case and provider uses the same whole-package limit: **262,144 bytes (256 KiB)**, with at most 64 records, 128 relationships and six traversal steps. The exporter requires substantive cases to retain evidence and requires the unknown-term control to retain none. It preserves `insufficient` rather than upgrading the package to an answer.

## What the instructions change

The new prompt explicitly requires reading headings, selected continuations, exceptions and dated amendments before forming claims. It asks for exact quotation characters and line breaks, with additional citations when a heading or continuation supplies an operative condition. A quote ending before a condition is a weak citation even when every quoted character matches.

This is a new experiment: **both the context and prompt change from the earlier trials**. The engine and provider defaults may differ too. A better or worse answer cannot be attributed to any single change. No before/after accuracy ranking or causal improvement claim is justified by this design.

## Freeze the evidence, then inspect it

An **immutable commit** identifies an exact saved repository version. The exporter requires explicit DWP and Explorer commits, compares each relevant file with its committed bytes, and archives the semantic index, corpus manifest, question registry, prompts, schema and runner sources. It also records engine digests and every locally read corpus file. It performs no web retrieval.

Freezing creates a new `frozen/` directory. A second freeze refuses to overwrite it. An offline replay must reproduce the context packages exactly from the archived inputs and matching engine. The context catalogue remains inspectable before either provider sees it. The actual-call command additionally names the chosen catalogue’s SHA-256 hash, a fingerprint of its bytes.

A **schema** defines the allowed answer fields. The same existing answer schema is used for both clients. Changes to the schema, helper code, prompt or fixed package cause a refusal rather than silently creating a different trial under the same name.

## Subscription and tool boundaries

The harness uses the installed subscription clients without a model override or a fallback-model override. It changes no persistent configuration and supplies no API credential. Each invocation first checks the CLI’s authentication status. An API-key login or unknown method is refused. The process environment excludes ambient API, alternative-provider and model-selection settings.

Read-only checks on 20 September observed Codex CLI 0.146.1 using ChatGPT authentication. Claude CLI 2.1.278 reported no authentication inside this sandbox, but an authorised unsandboxed status check reported `claude.ai` authentication with the first-party provider. No account details or credentials were retained. Future calls check authentication afresh; this observation is not a guarantee of continuing access.

Both CLIs provide session model-selection flags, but this protocol retains defaults. Claude response and accounting model identities are recorded separately when exposed; auxiliary accounting identities can differ from the response model. Codex may expose no actual model identity in its JSON events. In that case it stays **unknown**: neither the surrounding agent’s name nor a catalogue listing proves which model answered. These are not controlled single-model trials.

The established process-local CLI settings request tools, web access, shell execution and MCP to be disabled. Claude safe mode suppresses project customisations; Codex disables the discovered user skill paths and runs in an empty temporary directory. Host or system additions may still differ: these controls establish identical authored public inputs, not identical whole provider system contexts. No absence of a warning proves otherwise.

Claude’s `StructuredOutput` schema formatter is the sole documented exception. Event and message-content allowlists reject unknown event categories. The stream must end with exactly one explicit provider completion event before any answer can be retained. Incomplete or unrecognised streams have an unknown tool census, not zero tools. Four synthetic regression controls exercise missing, duplicate and misplaced completion, unknown top-level and nested events, refusal to retain answers, and the allowed formatter.

Only structured final answers, sanitised output metadata, numerical usage, timings and digests are retained. Raw logs, reasoning, account/session identifiers, private correspondence, credentials, skill paths and stderr are excluded. Each attempt has a 240-second time limit and bounded output streams. Failures are retained in separate, non-overwritten attempt directories; the harness never retries automatically.

## Review in layers

1. Check that both answers name the same package and preserve its insufficient or conflicting status.
2. Check exact quotations, record identifiers and source URL/locator pairs.
3. Read each claim against the heading, whole condition, continuation, exception and date. This remains semantic review, not a string check.
4. Inspect gaps, ambiguity and truncation statements. More retrieved pages do not prove completeness.
5. Retain a claim-level model critique and request independent specialist review separately. A model critique is not a gold answer.

The [validation note](../validation/model-comparison/household-2026-09-21/README.md) and [verified results ledger](../validation/model-comparison/household-2026-09-21/results.json) record all five attempts. Codex Staff 012 and the unknown-term control completed with an unrecognised `item:error` event and were rejected. The original error text was not retained, so its cause is unknown. Claude Staff 012 and Staff 020 exceeded the fixed 240-second limit. Claude's small control completed but exposed unrecognised `thinking_tokens`, `rate_limit_event` and `tool_result` categories alongside the permitted formatter, so it was rejected too. This is an event-format and execution-boundary finding, not evidence of inaccurate answers or established external tool use. Further cases are on hold; the frozen harness has not been relaxed and no retry has occurred. No failed or rejected output counts as an accepted answer. Provider usage accounting, when available, is not verified subscription charges or future affordability.

## Offline checks and historical commands

Check the successor without making a model call:

```sh
uv run --locked python scripts/project_monday_model_contexts.py
uv run --locked python scripts/run_monday_compact_trials.py
uv run --locked python scripts/run_monday_compact_trials.py --check-report
uv run --locked python scripts/check_monday_compact_critique.py
```

The independent critique checker verifies seven retained answers, 14 claims,
21 citation diagnostics and four additional selected records against the frozen
inputs. It recomputes quotation and source-locator checks, including the recorded
invalid locator. It makes no model, network or Git calls. It checks the evidence
behind the review, not the truth of the model's opinions: human review remains
pending and no answer-quality score is assigned.

The commands below describe the **original, now closed experiment** for reproducibility. They are not instructions to rerun its failed cases. Keep the original catalogue, attempts and runner unchanged; new experiments require their own reviewed inputs and identity.

The following are offline and make no model calls:

```sh
uv run --locked python scripts/run_monday_model_trials.py
node scripts/export_monday_trial_contexts.mjs --check-preregistration
uv run --locked python -m unittest discover -s scripts -p test_monday_model_trials.py
node --test scripts/test_monday_trial_export.mjs
```

After the root task confirms both final immutable commits, substitute those exact values:

```sh
node --experimental-strip-types scripts/export_monday_trial_contexts.mjs --freeze \
  --dwp-commit DWP_COMMIT --explorer-commit EXPLORER_COMMIT \
  --explorer-root /path/to/exact-explorer-checkout
node --experimental-strip-types scripts/export_monday_trial_contexts.mjs --check \
  --explorer-root /path/to/exact-explorer-checkout
```

Inspect the frozen catalogue and its digest before a real subscription call. The command below is intentionally explicit; it performs one real provider invocation only after all input and authentication checks pass:

```sh
uv run --locked python scripts/run_monday_model_trials.py --run \
  --provider claude-subscription --case staff-012 --attempt attempt-01 \
  --manifest-sha256 REVIEWED_FROZEN_MANIFEST_SHA256
```

Use the same catalogue digest and case for `codex-subscription`. A retry needs a new attempt identifier. Omitting `--run` verifies an existing attempt or the frozen inputs without making a model call. `--report` writes a new deterministic results ledger; a different existing ledger is refused and must be preserved before a later one is published. `--check-report` checks the retained ledger without rewriting it.

## Separate direct JSON successor

The [direct-trial protocol](monday-direct-trial-protocol.md) and 30 offline controls are ready. It binds complete evidence received through the versioned compact service to the source, assembler and hosting observation. Claude is asked to return JSON directly; all tools remain forbidden. The protocol is still pending final input freeze, and no provider call or new answer is claimed. Earlier failed, rejected and accepted attempts remain unchanged.
