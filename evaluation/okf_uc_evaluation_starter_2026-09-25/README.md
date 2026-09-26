# OKF / Universal Credit evaluation starter
**Prepared 25 September 2026. Model-derived design and reference interpretation; independent specialist review pending.**

This is an evaluation starter, not a completed comparative study, an official DWP decision, or a complete bounded evidence package. It contains one live Ask OKF diagnostic observation, proposed evaluation materials and documentation-grounded client setup examples. No repositories, deployments, account permissions or client settings were changed.

## Start
Read `protocol.md`. Keep `assessor/` inaccessible to tested models. Supply only the chosen participant prompt, permitted evidence and the relevant client instructions. The 12 supplied questions are development candidates, not an independently authored holdout. Do not upload this entire ZIP to a model you intend to test blind.

`assessor/reference-answer.md` gives the provisional legal reference and the evidence chain. Current official text and the relevant PDF page images were checked, but a full point-in-time statutory reconciliation was not completed. Attempts to retrieve dated statutory representations did not succeed. Freeze the historical texts and obtain independent welfare-rights review before describing the answer key as validated.

`observations/live-ask-okf-summary.json` is a transcription of selected fields and observations from four actual tool calls for one question/context. It is not a raw protocol trace. The complete selected-record catalogue and F1123 passage were inspected; only the first diagnostics slice was inspected. The entire package was not downloaded or independently hash-verified. No answer-quality trial across models was run.

`client-access.md` and `client-config/` describe candidate connections. Only this conversation's Ask OKF invocation was tested here; other client routes require their own recorded handshake, read and replay checks. Repository descriptions of previous sidebar and M365 trials are attributed observations, not new tests.

`implementation-brief.md` sets out a bounded local evaluation task for an implementation agent. It is a proposed work order, not permission to publish or change access controls.

## Integrity
`checksums.json` records hashes of the other delivered files. Run `python verify_kit.py` from this directory to check the kit. These checks verify delivery bytes, not legal correctness or source authenticity. No source PDFs, full BEP or production-ready cross-client adapters are included.
