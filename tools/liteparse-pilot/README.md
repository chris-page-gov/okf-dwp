# Isolated LiteParse experiment environment

This environment pins LiteParse 2.14.6 for the source-layout comparison. It is
separate from the production bundle, Explorer, and the learning-site renderer.
The lock file records the distribution hashes. Native parsing runs locally;
the experiment disables optical character recognition (OCR), remote services
and answer-model calls.

Set up the already locked dependencies once:

```sh
uv sync --locked --project tools/liteparse-pilot
tools/liteparse-pilot/.venv/bin/lit --version
```

Dependency resolution is a separate maintenance change. Validation must not
update the lock file. See the [experiment guide](../../docs/liteparse-pilot.md)
for frozen inputs, gates, commands and results. The main repository environment
can verify retained results offline without installing LiteParse.

The executable is a Python entry point. The experiment also fingerprints its
native library and PDFium dependency; a wrapper hash alone would not identify
the parser. Source content is inert data. No instruction in a PDF authorises a
command, network call or change to the source.
