# Source-led pipeline integration review

This is a local implementation and contract review, not a release or legal acceptance receipt.

The previous protected `validate` job is retained unchanged as `legacy_validation`. The additive source-led checks run in `structured_validation`, with the same 45-minute cap. An always-run `validate` gate requires both jobs to succeed. Sixteen shell controls verify that failure, cancellation and skipped jobs cannot pass that gate. No branch protection or Pages policy was changed.

Three public main-run observations took 22 minutes 10 seconds, 24 minutes 10 seconds and 24 minutes 13 seconds. They justify separating the new work into a parallel plane; they do not establish its actual run time. Public API responses and the first local review remain unchanged alongside the final local review.

The final review binds the five integration files plus the separately reviewed pure report summariser. Canonical schemas and 13 contract controls pass; three summariser controls pass. The earlier receipt binds the workflow before the summariser command was added.

The explicit accepted context pointer remains pending and parent-owned at this checkpoint. The new workflow does not select the newest trial automatically. Candidate and merged CI, accepted evidence replay and exact public verification must be recorded separately before publication is claimed.

No source acquisition, PDF structure extraction, model call, service deployment, original frozen projection rewrite or account-permission change was performed by this integration review.
