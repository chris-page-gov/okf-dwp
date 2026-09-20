# Service 0.5.0 public evidence delivery

Observed on **20 September 2026**. The deployed service passed the official SDK
comparison and the care-home evidence journey in Chrome, Firefox and WebKit.
**Strict console acceptance remains incomplete:** Firefox reported two hosting
cookie warnings, so the browser run correctly exited with status 1. No attempt
was retried or relabelled.

| Browser | Version | Evidence journey | Strict console | Tool requests |
| --- | --- | --- | --- | --- |
| Chrome | 153.0.8010.52 | Passed | Passed | 30 |
| Firefox | 153.0 | Passed | Failed: two `__cf_bm` invalid-domain warnings | 30 |
| WebKit | 26.5 | Passed | Passed | 30 |

The three-browser run started at 22:40:32.935 UTC (23:40:32.935 BST) and finished
at 22:42:01.292 UTC. It followed SDK completion at 22:39:02.132 UTC, leaving more
than 60 seconds before the first browser began. The harness requested at least
750 ms between tool calls; the smallest observed gap was 769.846 ms. There were
90 browser tool requests and no automatic retries.

## Exact release and context

- Service: `0.5.0`; hosting version 9.
- Runtime commit: `d538de99e6567633204253cd88b87cbe325ac39a`.
- Worker SHA-256: `e1ab74760de22aff89a943faba5f4fc382f5c9f0fbdf092e3bc29db98d9589a7`.
- DWP source commit: `3ef0e786e9a18e76fa17c7d925ff509d6d6c9f84`.
- Context: `urn:sha256:6cdc3dd154d4f11e1fb8b9dd1b99c42da59856ba7857de5a3fe04d6f3ab86078`.
- Question, preserving the supplied wording: “Does Pension Credit stop is a
  citizen moves into a care home permanently if they are self-funding?”
- Budget: 262,144 bytes; 35 selected records and 50 relationships.
- Status: **insufficient**, with context and retrieval truncation, four missing
  evidence entries, five unresolved terms and no model-generated answer.

All browsers paginated the two-part catalogue and inspected the exact text and
provenance of DMG Chapter 78, PDF page 25. Catalogue metadata, including source
URL, locator, label, authority and review status, matched the verified full
package. Source text, provenance, diagnostics, relationships and the full
machine-readable package were read in exact bounded parts. The complete package
used 17 browser slices; its reconstructed hash matched the independently checked
SDK package. This verifies delivery, not a complete answer or legal applicability.

The native browser response observer was unchanged from the reviewed harness.
Chrome's driver text differed from native UTF-8 response text on 14 responses;
those differences remain recorded. The browser-native text and exact rendered
package hashes were decisive. Firefox and WebKit had no driver/native differences.
No requests or responses were replaced and no security policy was weakened.

## SDK, deployment and browser evidence

- [Hosting deployment receipt](deployment.json)
- [Actual official SDK verification](sdk-receipt.json)
- [Three-browser summary](browser/staff/run-summary.json)
- [Chrome receipt](browser/staff/chrome-receipt.json)
- [Firefox receipt, including both warnings](browser/staff/firefox-receipt.json)
- [WebKit receipt](browser/staff/webkit-receipt.json)
- [Exact executed browser harness](browser/staff/verifier-e28c746e52e8a73c2b9b3f3798c261eb5f0e418b3503329b14f049156930d64d.mjs)
- [Artefact hashes and explicit observation layout](artifacts.json)

The SDK check passed seven full-package cases and four compact cases across all
four approved source versions. It recorded 93 HTTP 200 responses, a minimum
spacing of 750.167 ms, no network failures and no retries. The earlier staff,
discovery and custody source versions remain explicit; their compact context
identities matched the retained version-specific expectations.

**The separate historical four-journey, three-browser suite was not run for
0.5.0.** Its status is `not_run`, with null pass counts. SDK replay across the
earlier versions is a different check. The old
[0.4.0 browser observations](../v0.4.0/README.md) remain historical evidence and
are not substituted for a new run.

The application returned its restricted Content Security Policy and HTML
`no-transform` header in all three browsers. Firefox's retained warnings mean
this observation does not establish a completely clean hosting environment.
ChatGPT invocation, Voice, accessibility, answer quality and specialist legal
review are separate acceptance checks.

## Screenshots

- [Chrome catalogue](browser/staff/chrome-catalogue.png) and
  [source evidence](browser/staff/chrome-source-evidence.png)
- [Firefox catalogue](browser/staff/firefox-catalogue.png) and
  [source evidence](browser/staff/firefox-source-evidence.png)
- [WebKit catalogue](browser/staff/webkit-catalogue.png) and
  [source evidence](browser/staff/webkit-source-evidence.png)

## Recheck retained integrity offline

```sh
uv run --locked python scripts/check_staff_service_observations.py \
  --directory validation/compact-delivery/v0.5.0
```

This checks the exact retained files and preserves unsuccessful outcomes; it
makes no network request and does not launch a browser. The
[verification procedure](../../../docs/household-service-verification.md)
explains how to perform a new actual run into a fresh directory. Do not replace
this release's observations or manifest.
