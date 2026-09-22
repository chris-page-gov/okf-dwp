# Preserved coverage-ledger defect

These two audit files retain the exact pre-correction bytes. Counts were correct,
but an authored short obligation ID overwrote the canonical identifier during
projection. This could conflate obligations from different cases. The current
ledger retains both the canonical `id` and `authored_id`, with uniqueness and
exact requirement-membership checks. Do not use this retained report as the
current identity ledger. No source or context package was changed by the repair.
