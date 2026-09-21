# Why the abroad question exposed a semantic gap

[Learning path](learning-path.md) · [Backlog](backlog.md) ·
[Data Analytics proposal method](data-agent-semantic-review.md)

This is an independent experimental review, dated 21 September 2026. It checks
how evidence is found and connected. It does not decide benefit entitlement or
establish present-day legal applicability.

## First identify the version

The reported five irrelevant pages match the **19 September pre-fix observation**.
The retained [ChatGPT observation](https://github.com/chris-page-gov/okf-dwp/blob/697dd85c1cd5ea5191a77124de5a868d06d1652c/validation/corpus-questions/chatgpt-observation.json)
binds service 0.2.0, Explorer `75120116…` and DWP source `bf50ef8d…`.
Its 32,768-byte limit retained five records and no relationships. Ordinary words
such as “your” and “go” dominated the selection. The archived larger-budget
HTTP response contains the same first five pages; the five-record result itself
survives as the client observation, not as a separate raw HTTP capture.

A subsequent lexical filter removed that failure. An offline replay on the
published `c4f2de0a…` engine and the same older source now retains six more
relevant pages at 32 KiB. That old source still has no abroad task concept.
Neither a better page ranking nor a newer engine can supply semantic assertions
that are absent from the selected source version.

The published `723bcc5b…` source already resolves the exact question
“What happens to your benefits if you go abroad?” as **Absence abroad**.
A fresh offline replay retained two records and one relationship at 32 KiB,
using 31,229 bytes. At 512 KiB it retained 64 records and 80 relationships.
Both results remain insufficient and truncated. These are deterministic local
replays of the published source and engine, not fresh ChatGPT or Voice calls.

## What was still wrong

**A concept** is a named meaning. **A relationship** connects it to another
meaning or a source passage. Resolving a word is only the start of the task.

- “Travel overseas” did not resolve the abroad concept. Bare “temporary absence”
  is ambiguous: it can also concern hospital, custody or absence from a household.
- Four existing Pension Credit international concepts were disconnected from
  the newer abroad route. Creating duplicate concepts would hide that modelling
  defect rather than repair it.
- The newer route selected Chapter 7 Part 6, PDF page 8. That page ends midway
  through an example; following pages contain qualifications and different
  claimant, household and young-person questions.
- Pension Credit mentions also activate a broad overview profile. This expands
  the graph into other topics and competes for a fixed context budget.
- The corpus lexical filter and semantic unknown-word filter differed. For
  example, lexical search ignored “your”, but semantic diagnostics reported it
  as an unknown domain term. Substantive terms such as loss and exceptions must
  remain visible.
- Universal Credit absence rules are not made complete by finding pages in ADM,
  the Advice for decision making manual. Twenty-nine of the 40 known staff
  cases had ADM candidates found only by lexical search in the wider audit.

## The bounded repair

The additive semantic source reuses the existing international identifiers,
adds explicit overseas phrases and connects the abroad research route to
benefit-specific Pension Credit concepts. Whole frozen pages 8–14 are retained
as declared support, including continuations, distinct household conditions,
the dated 2016 transition and source-described export limits. The assertions
remain model-derived and await specialist review.

Only the **Pension Credit plus abroad** task requires that full Pension Credit
closure. The general “benefits abroad” question still lacks a named benefit and
other important circumstances. JSA, ESA, PIP or Universal Credit must not silently
inherit a Pension Credit rule. Domestic temporary absence and a holiday without
an overseas location do not automatically resolve to abroad.

Explorer's reusable repair shares the question-scaffolding filter between
lexical retrieval and unknown-word diagnostics. Declared aliases resolve first;
the filter preserves qualifications, negation and identifiers. This is generic
engine behaviour, not a list of DWP-specific answers.

**Publication boundary:** authored source, generated Reader, Explorer source and
the public MCP service are separately versioned. A source or engine change is
not live in a frozen MCP adapter until admitted and observed there. Consult the
[service publication record](service-publication.md) for its selected source
and engine; historical source versions retain their original behaviour.

## What the checks must measure

The focused evaluator compares the published source and candidate on the same
hash-bound engine, at 32 KiB and 512 KiB. It records concepts, selected pages,
required paths, missing evidence, relationships, bytes and truncation. It keeps
full packages and their hashes so a reviewer can inspect actual retained text.
The source tests inspect whole passages and qualifications, not just keywords.

The [retained comparison](../validation/abroad-context/2026-09-21/README.md)
contains all 24 packages and ten negative controls. The candidate retains seven
of seven supporting pages and 14 of 14 declared paths for the four Pension
Credit questions at 512 KiB. At 32 KiB those questions return metadata-budget
refusals. The general question regresses from two records and one edge to one
concept and no edges at 32 KiB. That measured loss remains an open capacity
problem; the semantic increment is not being substituted silently for the
published service default.

Independent agent source review found no blocking defect in the seven whole
pages, their qualifications or the benefit-specific requirement. Sixty-seven
semantic controls, 21 combined Reader controls and the current 40-case replay
pass. All 528 pre-existing evidence records and 203 obligation records remain
unchanged. The rebuilt current projection contains 916 semantic records,
57 authored concepts and 74 support dependencies. These counts describe an
increment, not complete departmental semantics.

The supplied staff questions and these deliberately authored paraphrases are
**development controls**. They are not an independent accuracy benchmark.
All 203 existing obligations stay open. An obligation is a named missing
piece of evidence or review required before a complete answer can be claimed.

The two size limits mean different things:

1. **Retrieval truncation:** matching candidate pages remain outside the fixed
   lexical candidate limit.
2. **Assembly truncation:** some records, relationships or metadata do not fit
   the requested package size. A small package can contain only a refusal.

A manifest and exact evidence reads can deliver a selected package in smaller
pieces. They do not recover material excluded from that package. Closing an
evidence gap requires another explicitly scoped assembly or a reviewed source
change, not merely another download of the same selection.

## Wider work that remains

The [machine-readable backlog](../evaluation/backlog.json) separates these tasks:

- **BL005.abroad-connectivity:** aliases and connected existing international
  concepts with source-scoped definitions.
- **BL005.cross-benefit-coverage:** reviewed mappings for other benefits and
  variants, including ADM; territory, duration, purpose and dates must be visible.
- **BL007.abroad-qualification:** full supporting passages and budget checks for
  Pension Credit abroad, without promoting the broad question to sufficient.
- **BL007.task-discrimination:** distinguish an overview mention from the actual
  task, reducing irrelevant graph expansion without losing required support.
- **BL009.lexical-version-competition:** measure historical amendments and
  current chapter competition; do not silently hide old evidence or assume
  identical text proves legal supersession.

Broader semantic modelling remains unfinished implementation as well as
unfinished specialist review. More concepts, pages or edges alone do not close
it. A [small Data Analytics proposal trial](data-agent-semantic-review.md) could
help identify missing meanings and qualifications, provided proposals remain
source-linked, unreviewed and separately evaluated.

## Why Voice and client access are a separate question

The owner's earlier successful Voice demonstration is compatible with the
retained history. Earlier recorded text-client calls also reached Ask OKF.
The lack of an instrumented Voice receipt does not prove that Voice cannot work.

Recent failures occurred at different boundaries: a question-schema mismatch
was fixed in service 0.6.1; a particular ChatGPT conversation subsequently
reported that developer MCPs were forbidden after discovering the tools.
That reported host refusal is different from a server HTTP failure or a
semantic retrieval failure. A working SDK check does not establish access for
every conversation or nested agent.

OpenAI documents that Voice follows the permissions of the tasks it directs.
Feature availability depends on the client, plan and workspace. Rehearse the
intended conversation and record an actual tool call and evidence reads, rather
than inferring capability from the microphone or installed-plugin listing.
[Voice documentation](https://learn.chatgpt.com/docs/features/voice) ·
[Connection checklist](chatgpt-connection.md) ·
[Native integration follow-up](https://github.com/chris-page-gov/okf-dwp/issues/26)
