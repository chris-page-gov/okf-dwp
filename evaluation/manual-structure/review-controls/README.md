# Independent review controls and retained failures

These receipts are separate from the registered four/eight source cases and the 40 staff questions. They do not establish legal answerability. Historical plain-text test outputs retain their actual failures; they do not contain a complete per-run code snapshot and must not be used as fully reproducible version receipts. The source-case reports retain their own stronger bindings.

- `parser-review-01.txt`: three genuine generalisation failures: ambiguous repeated heading alignment, sidecar role replay, and a notice absorbing later guidance. All were fixed before the final bound source-case run.
- `parser-review-02.txt`: the additional fragmented-annotation control failed because references and offsets were inherited from the whole region. The fix extracts references from each exact fragment. The final eight review controls pass.
- `corpus-integrity-01.txt`: six producer-integrity checks passed; the preservation test failed because this new test read an `authored` flag from an old catalogue whose field is `boundary_status: author-declared`. This is a test-adapter defect, not evidence that the producer lost the 75 authored records.
- `corpus-integrity-02.txt`: after correcting that test field, all seven checks passed against the first generated context. A definitive final-generation check is still separate; these observations must not be silently upgraded to later output acceptance.
- `pdf-observer-review.md` and `manual-guide-review.md`: independent scope/code review receipts with the then-current file hashes. They retain the distinction between review and producer-owner test/extraction observations.

No failed receipt was overwritten. Changes to source or producer versions require another named result.
