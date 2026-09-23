# Fixed-source allocation attempt: mixed result, adoption held

All 164 assemblies completed without source-integrity failures, model calls or
network calls. The corpus, protocol and runner are identical to attempt 03;
only the reviewed engine changes to
`af5f5183764afb45fe16a93e82866fffa6a29de7`. All 82 legacy packages remain
byte-identical.

At 512 KiB all 40 structured cases now return source evidence: Staff 009 rises
from zero to 21 units. However, inherited required paths fall from 47/47 to
46/47 (Staff 029), and new source-read paths fall from 139/181 to 137/181.
Staff 010 loses 15 previously retained new paths. Therefore **adoption remains
held**. More delivered units alone does not meet the acceptance condition.

The exact [report](report.json), packages and executed runner preserve this
result. The next repair must retain source and limits and address allocation
within the actual resolved graph. Requirements must never create concept seeds
or invent relationships. All 32 KiB structured contexts still retain no source
evidence; all 203 original obligations stay open and all results insufficient.
