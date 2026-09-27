# First public browser attempt

The immutable source and sidecar checks passed. All eight browser journeys
reached the accessibility scanner, which rejected the verifier’s use of
`browser.newPage()` without an explicitly created browser context. This is a
verifier failure; it is not an accessibility pass or an application defect.
The successor uses `browser.newContext()` and retains the same checks.

The receipt preserves the exact script hash, observed public commit, immutable
data hashes and failed checks. Screenshots remain in the named local temporary
paths; the receipt does not depend on their availability for its failed status.
