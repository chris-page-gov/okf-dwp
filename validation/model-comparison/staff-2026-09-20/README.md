# Retained paired model observations

Every attempt has a receipt. `model-output.json` retains the response and allow-listed usage only; `answer.json` is present when the harness accepted the output transport for checking. A failed mechanical result remains a failure even when a structured answer exists. The original answer bytes are never repaired to improve scores.

[Results](results.json) are rebuilt by `uv run --locked python scripts/run_staff_model_trials.py --report`. This verifies every retained attempt, historical input snapshots, artefact hashes, literal quotations, source locators and package boundaries without contacting a provider. The ledger preserves the first strict-policy Claude formatter rejection and subsequent control separately.

No raw CLI initialisation, reasoning traces, session identifiers, account data or stderr are published. Standard-output and standard-error hashes are retained, but the raw event stream is not reconstructable from these sanitised projections. Claude formatter arguments are hashed and not copied as tool arguments. Answer content remains explicitly model-generated and unreviewed.

The authored context, prompt and schema are identical across providers; provider host instructions and wrappers differ. Codex did not expose its actual model identity. Provider-reported helper model usage must not be confused with the model that authored the response. Recorded costs are accounting observations, not verified subscription charges or an affordability benchmark.

The [claim-level model critique](claim-level-model-critique.json) binds all 49 claims to exact answer and context digests. The [execution note](execution-provenance.json) documents the retained on-disk-versus-loaded harness hash distinction. Both are fallible engineering/review evidence, not specialist acceptance. The timeout has no retained tool-event census; do not interpret it as zero events.
