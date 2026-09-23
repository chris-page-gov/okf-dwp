# Fixed-source runtime repair

This is the second full comparison: 40 known staff question occurrences plus
one unknown-term control, two source projections and two budgets, giving 164
assemblies. No model or network calls were made. The source projections and
authored semantics are exactly those of attempt 01, recoverable from DWP commit
`9736d30c`. The reviewed Explorer engine is
`58776a79d00ef164b8bc94a407b21d5ba401481a`.

The [report](report.json) binds the protocol, engine modules and every consumed
source file. All context bytes and the exact runner are retained beside it.
[comparison.json](comparison.json) compares the two attempts without changing
their original results. All 82 legacy-projection packages are byte-identical.

| Structured projection, 40 occurrences | Attempt 01 | Attempt 02 |
| --- | ---: | ---: |
| Zero-evidence contexts at 32 KiB | 40 | 40 |
| Zero-evidence contexts at 512 KiB | 0 | 0 |
| Declared paths retained at 512 KiB | 40/47 | 47/47 |
| Median source units retained at 512 KiB | 33.5 | 35 |
| Median discovery diagnostic bytes at 512 KiB | 51,339 | 16,447.5 |

Resolved-concept routes now receive file allocation before lexical candidates.
Discovery cards and incident metadata have exact hash-bound lazy references;
selected source and relationship evidence still appear in the package. This
repairs the observed large-budget path regression. More selected units do not
establish better relevance, supported answers or legal completeness.

**The small-assembly limitation remains.** At 32 KiB all structured results
retain no evidence. Every staff result at both budgets remains `insufficient`.
Larger assembly and separately bounded exact delivery are distinct operations;
the card preview must not replace missing source evidence.

Local timings are retained as mixed cold/warm observations in fixed sequential
order. They are not a controlled speed or public-service latency benchmark.
The next parser and semantic-profile increment uses a separately bound trial.
