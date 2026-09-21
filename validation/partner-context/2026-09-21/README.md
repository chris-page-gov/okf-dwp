# Partner qualification retention

This separate offline comparison checks the reviewed partner component against
its disability-only predecessor. Both sources contain 903 records; the partner
increment adds ten supporting dependencies and conditional support declarations
in four task profiles.
It preserves all captured evidence bytes and all 203 open obligation identities
and statuses. Four obligation labels are deliberately clearer.

## Exact inputs

- Previous source: `8ea4465a4cb5a867d82c87e635f2ef1d1df18d8a`.
- Partner source: `7e5fdb9b906052914b307c17c0fd19feb2d008a7`.
- Partner index SHA-256: `685353567b90db880f1bd1ba33b57ae7ecc430673332ce69e47512a9ae606886`.
- Earlier assembler: `b9a3b68b6dbf222f9a73cc8f450dd53f126e1b55`.
- Required-evidence assembler: `c4f2de0a99b7bc2f8b8c8a06a3c715fb56b66d8e`.
- [Protocol](protocol.json) SHA-256: `de2c512644349e314bb9b42b9d4775eb74f6605b8dbfc253eb50f08d6f0a97a2`.

The [source review](../../../docs/partner-addition-qualification-review.md)
explains the qualifications and the correction of an extracted superscript.
The comparison uses identical questions and candidate identifiers. It counts
expected paths from the authored source before applying output budgets.

## Results

Two sources, two assemblers, two budgets and 40 question occurrences produce
**320 assemblies**, retained as 160 paired rows in
[attempt 01](attempt-01/comparison.json). Exact replay and 14 admission and
path-denominator controls pass. Every package remains insufficient and has no
AI answer. All whole selected evidence retains its literal source hash.

| Budget | Source | Earlier assembler: candidate / path occurrences | Current assembler: candidate / path occurrences |
| --- | --- | ---: | ---: |
| 256 KiB | Disability | 164/177; 340/497 | 177/177; 407/497 |
| 256 KiB | Partner | 164/177; 329/585 | 177/177; **449/585** |
| 512 KiB | Disability | 176/177; 462/497 | 177/177; 497/497 |
| 512 KiB | Partner | 176/177; 503/585 | 177/177; **585/585** |

The new denominator reflects additional declared evidence, not improved accuracy.
The original candidate-page count remains 177/177 even when qualifications are
missing from the smaller package.

### The four affected questions

| Case | Budget | Records / relationships | Retained declared paths | Package bytes |
| --- | ---: | ---: | ---: | ---: |
| Staff 012 | 256 KiB | 14 / 46 | 25/93 | 258,930 |
| Staff 013 | 256 KiB | 14 / 46 | 25/93 | 258,934 |
| Staff 014 | 256 KiB | 33 / 46 | 37/37 | 256,784 |
| Staff 017 | 256 KiB | 34 / 46 | 37/37 | 260,603 |
| Staff 012 | 512 KiB | 55 / 115 | 93/93 | 524,089 |
| Staff 013 | 512 KiB | 55 / 115 | 93/93 | 524,093 |
| Staff 014 | 512 KiB | 64 / 128 | 37/37 | 520,839 |
| Staff 017 | 512 KiB | 64 / 125 | 37/37 | 519,958 |

These path occurrences include every activated profile, rather than only the
question's own profile. At 256 KiB Staff 012/013 retain only one of the seven
household support pages and explicitly report missing dependencies and paths.
At 512 KiB both retain all seven and the complete declared component groups.
The fifteen missing requirement identifiers then identify open obligations
across three profiles. Staff 014/017 retain their declared paths at both sizes;
the larger packages can also include optional summaries whose missing support
is reported separately. No missing requirement description was trimmed from
these observations.

The 512 KiB care-home packages have little spare room. A different binding URL
or additional evidence changes complete package bytes and identity. The current
source-only evaluation uses a shorter binding and produces 524,075/524,079 bytes;
public Reader and service combinations need separate checks. None of these
results establishes continuing partner status, receipt of a qualifying benefit,
legal completeness or an award amount.

Receipt SHA-256: `1ce17c7e5faf82daa9584a4a16d06d3093188737ed9e7cfc44d124df87034503`
(11,644,881 bytes). The [previous experiment](../../disability-context/2026-09-21/README.md)
and all historical model/browser observations remain unchanged.

## Reproduce

The runner changes only the declared source pair from the previous experiment;
its guards, metrics and six archived assembler modules are byte-identical.
The approved module hashes and immutable Git blobs are checked before import.
No network or model calls occur; source bytes are read from local immutable Git objects.

```sh
node --test validation/partner-context/2026-09-21/*.test.mjs
node --experimental-strip-types validation/partner-context/2026-09-21/compare.mjs \
  --dwp-root /path/to/okf-dwp \
  --explorer-root /path/to/okf-explorer \
  --check validation/partner-context/2026-09-21/attempt-01
```

For a fresh observation, use `--output` with an unused directory instead of
`--check`. Existing evidence is never overwritten. These are known development
questions, not a held-out model benchmark or specialist acceptance.
