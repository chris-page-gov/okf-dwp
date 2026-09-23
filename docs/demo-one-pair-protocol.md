# Demo 1: two paired answers

This is a small, pre-declared research comparison for the 29 September demonstration.
It uses staff-006 (Pension Credit savings) and staff-012 (a permanent self-funded
care-home move), selected before observing these new answers. Both are known
development questions, not a blind holdout.

## What is held fixed

The exact question, requested model (`claude-opus-5`), medium effort, answer format,
output limit, no-tool policy and 240-second timeout are the same within each pair.
Actual model identity and reported token categories are recorded from the client.
Each answer starts a fresh, non-persistent session with customisations disabled.
There are **four new answer invocations maximum**, including failures. The runner
reserves each arm once and does not permit a retry or an alternative model.
Subscription authentication must be established before an answer call; no API key
or paid fallback is accepted.

The **unassisted** arm receives no evidence and may use unverified model knowledge.
The **OKF** arm receives a deterministic reading view of its retained trial-06
package at source commit `9f6e316925f1550559733e34d8d91cd7a245c94b`.
Every selected record is retained in full, including source text, spans, authority,
provenance and scope. Missing-evidence entries, requirement limitations and both
truncation flags are also retained. Detailed relationship/path, guard and ranking
diagnostics are omitted from this reading view and remain in the hash-bound audit
package. This is not a new context assembly or the full audit package itself.

The instructions to use only supplied evidence in the OKF arm are deliberately
part of the intervention. Neither arm browses the web. This is **not** a comparison
against ordinary web search, a Data Agent, another provider or an autonomous client.
No current legal correctness is inferred from a model's unsupported recollection.

## How the answers will be assessed

For each claim, an unblinded agent checks exact quotation/citation membership,
whether the stated source supports the claim, material conditions and exceptions,
and claims about current law or amounts. Useful partial answers, explicit gaps,
unsupported assertions and failures are all retained. Source support is assessed
against the supplied frozen evidence, not an independently established complete
legal ground truth. Specialist acceptance remains pending.

Report prompt bytes, client-reported input/output/cache tokens, elapsed seconds and
tool activity. Do not call bytes tokens, compare unlike token categories, infer
subscription cost or claim savings relative to an unmeasured web workflow. Two
questions with one answer per arm cannot establish general superiority or variance.

## Reproduce without spending model allowance

```sh
.venv/bin/python scripts/demo_one_pair.py check
```

`prepare` writes deterministic prompts offline. `run` explicitly invokes one
subscription answer and requires the protocol, inputs and runner to be committed.
It must not be run again for this freeze after the four recorded invocations.
All raw outputs are retained for inspection; any format or support failure remains
part of the result rather than being replaced with a better answer.
