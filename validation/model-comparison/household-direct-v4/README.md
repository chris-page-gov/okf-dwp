# Paired direct evidence trial v4: one question, inspectable claims

**Independent experiment, not official DWP guidance or specialist acceptance.**

Both subscription clients completed the empty-evidence control before answering the same Staff 012 question from the same complete public package. All four responses pass the frozen mechanical checks, with a complete event census and zero observed tools. No retries, model overrides or external retrieval occurred.

> Does Pension Credit stop is a citizen moves into a care home permanently if they are self-funding?

The original supplied wording, including its typo, is preserved. The answers give **partial evidence only**. Both distinguish the whole Pension Credit award from the severe-disability and housing-cost additional amounts, retain the partner/household qualification and refuse to decide whether the whole award stops or continues. The supplied package remains **insufficient** and truncated.

## Inspect the actual outputs

| Client | Empty control | Staff 012 | Elapsed seconds: control / question | Claims / citations |
| --- | --- | --- | --- | --- |
| Claude subscription | [No claims](claude-subscription/control-unknown/attempt-01/answer.json) | [Original answer](claude-subscription/staff-012/attempt-01/answer.json) | 8.800 / 35.278 | 3 / 4 |
| Codex subscription | [No claims](codex-subscription/control-unknown/attempt-01/answer.json) | [Original answer](codex-subscription/staff-012/attempt-01/answer.json) | 17.682 / 37.989 | 3 / 3 |

Each answer directory also contains `receipt.json` and `model-output.json`: recorded input hashes, command boundaries, usage and sanitised client events. Elapsed time is one observed invocation, not a performance comparison.

Read the [independent agent claim review](independent-claim-review.md) beside the answers. It checks meaning and qualifications against the whole supplied package. It is machine-assisted review, **not independent specialist acceptance**. It identifies omitted treated-receipt and transitional-protection exceptions in Claude C1, an overstated absence of continuation evidence and additional citation needs. The original answers are unchanged. A quotation matching exactly is only a mechanical check: extra assertions in a qualification or summary need review too.

## What was held fixed

- The actual public 0.6.0 care-home package: 523,326 bytes, 55 records and 115 relationships; SHA-256 `cb7e8e6f62a49a15907b09d2a32d525539c6853d5344ebcd5566bf616315e8f7`.
- The empty control: 4,385 bytes, no selected records; SHA-256 `ec71998891a0bd39e37762421e2414e49175a920816b0f88018eaf6ccc4d06b5`.
- The authored prompt, answer schema and both complete packages are byte-identical to direct-v3. The new protocol recognises documented installed-client metadata while retaining strict tool and bounded-output checks.
- [Sixteen frozen inputs](../../../evaluation/model-comparison/household-direct-v4/frozen/manifest.json), manifest SHA-256 `6463e054b034d7f33df7fcad61be337f01136f996f2a00da7e428acbbae8d934`; input commit `afeb78d1241c03c73adb593a07614cf53634eb0b`.

The package is the partner-qualified source `723bcc5b…`, not the later ignored-person source. Its [public SDK reconstruction](../../compact-delivery/v0.6.0/README.md) and [retained browser example](../../../docs/retained-evidence-examples.md) provide the same evidence for inspection. The original [v3 control failures](../household-direct-v3/README.md) remain unchanged.

## What this does not establish

This is one paired question and one empty control. It is not a representative accuracy benchmark, legal answerability result, human review or affordability forecast. Claude reports response identity `claude-opus-5`; Codex's actual response model is not reported and is not inferred from the enclosing task. Provider host context differs, including the recorded Codex skill-catalogue warning. Authored evidence was identical; whole system prompts were not controlled.

Claude's accounting fields and the clients' token counts use different categories. They are retained observations, not verified subscription charges or directly comparable costs. No API purchase or reset credit was used.

## Reproduce the checks without another model call

From the repository, with the pinned Explorer Git objects available:

```sh
uv run --locked python scripts/run_monday_direct_v4_trials.py --explorer-root /path/to/okf-explorer
uv run --locked python scripts/check_monday_direct_v4_observations.py --explorer-root /path/to/okf-explorer
uv run --locked python -m unittest discover -s scripts -p 'test_monday_direct_v4*.py'
```

These commands validate retained inputs and outputs. They do not ask either model again. See the [protocol](../../../docs/monday-direct-v4-trial-protocol.md) for exact versions, limits and distinctions.
