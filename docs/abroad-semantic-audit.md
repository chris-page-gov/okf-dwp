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
  the Advice for decision making manual. In the current wider audit, 27 of the
  40 staff cases (27 of the 38 containing ADM pages) have selected ADM pages
  without any recorded relationship path. The case-level findings below
  distinguish this selection issue from missing source coverage.

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

### What the current 40 packages actually contain

This read-only audit inspected the `after` package in each of the 40 retained
staff cases (39 distinct questions), checking every decoded package hash against
the [evaluation at commit `c203a4bd…`](https://github.com/chris-page-gov/okf-dwp/blob/c203a4bd621e57c99273b3933df0207e101c5a85/evaluation/semantic-expansion/evaluation.json).
These are 512 KiB packages made with the pinned `c4f2de0a…` engine and semantic
index SHA-256 `92a8871b8f1f2e51f1feace0b1f57c67dfd0ddcb0434cf4574795e5942e95fd6`.
No new assembly, model call or public-service test was run for this audit.
All 40 packages remain **insufficient**, truncated and without an AI answer;
all 203 obligations remain open.

In the case lists below, `012` means `staff-012`. The
[retained case directory](https://github.com/chris-page-gov/okf-dwp/tree/c203a4bd621e57c99273b3933df0207e101c5a85/evaluation/semantic-expansion/cases)
contains compressed JSON files with `before` and `after` packages. A package is
the selected evidence and its explanations; it is not the entire source corpus.

**ADM connections:** 38/40 packages contain ADM pages. In 27 of those 38,
none of the selected ADM pages has a recorded relationship path:
**001, 002, 004–011, 014–025, 027, 028 and 038–040**.
The other 11 cases have at least one ADM page reached through relationships:
**003, 026 and 029–037**. Cases **012 and 013** contain no ADM pages.
This does not establish whether the selected ADM material is relevant or whether
the full corpus lacks relationships. It identifies where the returned package
provides lexical discovery without a semantic route to its ADM evidence.

To inspect this distinction, use `after.selected[].record.route` for `page/adm/`
and look for non-empty `after.selected[].paths[].assertions`. The evaluation
summary reports `cases[].after.adm_pages` and `semantic_adm_pages`. A page can
have both a lexical match and a relationship path.

### Task profiles activate too broadly in some cases

A **task profile** declares the evidence needed for a recognised task. It is
activated by a combination of resolved concepts. In 24/40 packages, more than
one profile activates. Additional context can be useful, but a shared benefit
name or the word “rates” does not establish that two questions need the same
investigation.

| Profile | Current activation | Concrete scope issue to review |
| --- | --- | --- |
| 019: Pension Credit overview | 16/40: 006, 007, 009–017, 019–023 | A Pension Credit mention activates the overview in 15 questions other than its own. |
| 004: State Pension components | 5/40: 002–005, 022 | The State Pension concept alone triggers a component investigation. |
| 008: SDA rates | 4/40: 007–009, 021 | Cases 007 and 021 contain no SDA term, yet “rates” activates the instruction to resolve that acronym. |
| 038: Carer's Allowance conditions | 3/40: 038–040 | A benefit mention also activates the conditions profile for interaction and caring questions. |

Some triggers are duplicated across different staff questions: **012/013** share
Pension Credit plus care home, and **014/017** share Pension Credit plus partner.
The duplicate **026/033** question profiles both activate for cases **026, 029,
033 and 036**; the DLA plus PIP trigger does not require the child context in the
original question. The two funding questions also activate both care-home
profiles regardless of their different wording. Keep every original question
for traceability while testing whether repeated requirements can be shared and
task-specific conditions represented more precisely.

The inspectable fields are `after.requirements[].id`, `when_all` and `scope`,
compared with `requirements[].when_all` in the semantic index. These activation
counts describe modelling and selection behaviour, not legal answerability.

### Unresolved terms mix domain questions with ordinary wording

23/40 packages retain unresolved tokens. Material examples include benefit
scope in **001, 005 and 039**; birth-date fragments in **002**; component, amount,
maximum or element wording in **004, 006, 008 and 010**; self-funding and stopping
payment wording in **012/013**; and scenario, variation or weekly-rate wording
in **018/037**. The original question still contains these facts, but they are
not all represented as structured constraints.

Other unresolved tokens, such as “your”, “someone” and “them”, are question
wording rather than necessarily missing domain concepts. The full affected case
list is **001, 002, 004–006, 008–010, 012–015, 017–023 and 037–040**.
Inspect `after.unresolved_terms` alongside `after.question`. Adding every token
to an ontology would conceal this distinction; benefit scope, dates, negation
and the requested decision need separate tests from ordinary wording.

### Required paths and support dependencies are different checks

A **required path** is a declared chain of records and relationships for an
activated task. A **support dependency** is material required by another
selected item, even when that material is outside the task's declared paths.
Retaining every task path does not prove that every selected interpretation
retains its supporting evidence.

Across the 40 packages, **118/776 activated required-path occurrences are
missing**. Only **012 and 013** lose declared paths: each retains 94/153 and
misses 59/153. Some paths occur in both activated care-home profiles. Counting
identical paths once within each package gives **62/463 missing**, or **31/79**
for each of those two cases. These are two stated denominators for the same
selection, not two different results. The expected paths were counted from the
activated authored profiles, not only the requirements surviving in a package.

The missing records in each care-home case include Chapter 77 pages 9–11, 19 and
35; Chapter 78 pages 5–6 and 18–24; Chapter 84 page 128; Chapter 85 page 30;
Chapter 57 page 5; and the normal-residence concept. These records exist in the
index. Their omission is a package-selection gap, not evidence that the source
has never been acquired.

Separately, **15/40 packages report 86 `missing_dependency` entries**:
**001, 005, 008, 009, 011–014, 018, 024, 030, 031 and 038–040**.
All referenced dependency endpoints exist in the index. Case **018** retains
all four task paths but has 17 dependency diagnostics. Case **014** lacks six
household support dependencies while **017** lacks none; they activate the same
profiles, but 014 also resolves benefit interaction, so this is not a controlled
one-variable comparison. Case **030** reaches custody-related concepts in an
IIDB/PIP interaction question, producing five scope-support gaps. That needs a
graph-relevance review before treating those gaps as legal requirements for the
question.

Check the index's `requirements[].required_paths` against
`after.selected[].record.id` and `after.relationships[].id`: every record and
relationship in a required path must survive. Inspect dependencies separately
in `after.missing_evidence`, where `code` is `missing_dependency`. A missing path,
a missing dependency and an open specialist-review obligation are not
interchangeable measures.

### Where this work is tracked

The [machine-readable backlog](../evaluation/backlog.json) separates these tasks:

- **DWP-BL-005.abroad-connectivity:** aliases and connected existing international
  concepts with source-scoped definitions.
- **DWP-BL-005.cross-benefit-coverage:** reviewed mappings for other benefits and
  variants, including ADM; territory, duration, purpose and dates must be visible.
- **DWP-BL-007.abroad-qualification:** full supporting passages and budget checks for
  Pension Credit abroad, without promoting the broad question to sufficient.
- **DWP-BL-007.task-discrimination:** distinguish an overview mention from the actual
  task, reducing irrelevant graph expansion without losing required support.
- **DWP-BL-009.lexical-version-competition:** measure historical amendments and
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
