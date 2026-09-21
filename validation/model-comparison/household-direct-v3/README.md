# Direct JSON trial v3: both controls rejected

This is a separately frozen two-client experiment using the exact public evidence delivered by service 0.6.0. It does not replace or repair earlier attempts. No substantive care-home call was made.

## Actual attempts

On 21 September 2026 at 08:27 BST, both subscription clients received the identical 4,385-byte empty-evidence context and authored prompt, with no model override and tools disabled.

| Client | Recorded CLI | Outcome | Elapsed |
| --- | --- | --- | --- |
| Codex subscription | 0.146.1 | Exit 0, but strict event parsing rejected an unrecognised usage shape. | 9.993 seconds |
| Claude subscription | 2.1.278 | Exit 0, but strict event parsing rejected unknown or missing wrapper fields. | 19.579 seconds |

Both transport captures completed within bounds. Neither response was accepted as an answer. The rejected event streams leave the tool census **unknown**, not verified zero. Codex also reported the retained skill-catalogue shortening warning. Account credentials, raw reasoning, stderr and account identifiers are not published. The original stdout/stderr byte counts and hashes are retained in each receipt.

The protocol requires both controls to pass before either substantive call. That gate correctly remained closed. There were **two provider attempts, no retries and no substantive attempts**. This result demonstrates a client-format compatibility gap in the trial harness. It does not establish that either model can or cannot answer the benefits question accurately.

## Reproduction and identity

The [freeze manifest](../../../evaluation/model-comparison/household-direct-v3/frozen/manifest.json) has SHA-256 `a6b85c1db3d4ae6c9d6d182c3138e03de660d19a6fb32881f4f7e5e2390a6ea3` and binds 16 exact inputs. The [protocol guide](../../../docs/monday-direct-trial-protocol.md) describes its bounds and control-first gate. Thirty-two offline controls passed before execution; those synthetic controls did not predict these actual wrapper differences.

The source, runtime, verifier and model inputs have distinct immutable identities. Exact public delivery and successful freeze admission are separate from model output acceptance. Do not alter the frozen runner to make these attempts appear successful. A successor requires a new reviewed format contract, new inputs and separately recorded attempts.

Raw client event bodies were deliberately not retained, so these rejection categories cannot reconstruct the precise omitted wrapper fields. The next harness needs value-free structural diagnostics to make a format failure actionable without publishing private client metadata.

## Check these recorded outcomes offline

```sh
uv run --locked python scripts/check_monday_direct_observations.py --explorer-root OKF_EXPLORER_CHECKOUT
```

The checker reuses the frozen input admission, verifies the exact two receipt and artefact fingerprints, rejects extra experiment files and confirms that the frozen substantive gate stays closed. Eight negative controls pass. It verifies the retained projections; it cannot replay raw client events that were deliberately not retained. It makes no provider or network calls.
