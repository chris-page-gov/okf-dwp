# Claude repository-access example: UC disabled-child addition

## About this record

This is a user-supplied Claude chat, formatted on 25 September 2026 for
inspection. It is an example of direct repository access, not a controlled
answer-quality trial or a verified Ask OKF, MCP or WebMCP client test.

| Field | Recorded value |
| --- | --- |
| Client | Claude; exact model, version and session time not supplied |
| Access shown | Shell commands, GitHub repository cloning and local file reads |
| Source read | Retained Advice for decision making (ADM) text under `source/adm-2026-09-19/text/` |
| Repository revision used by Claude | Not recorded; the clone commands do not pin a commit |
| Existing development case read | [UC disabled-child supersession case](../out-of-sample/uc-disabled-child-supersession-001.json) |
| Independent replay or specialist review of this chat | Not performed as part of this formatting change |
| Supplied transcript | 31,716 bytes; SHA-256 `a1cf97929822408ef3640719cbbed746d5f820ebc13f79c58dc41f01e8183b9e` |

Universal Credit (UC) is the benefit discussed. Disability Living Allowance
(DLA) is the other benefit referred to in the question. An assessment period
is the monthly period used to assess UC; the exact period dates are not supplied
in the question. ADM is DWP's Advice for decision making manual; DWP means the
Department for Work and Pensions.

**Read the answer as model output.** The transcript includes Claude's claim
of “over a year of arrears” and a retained rate. Those statements are preserved
for review, not adopted as a project finding or a verified calculation. The
linked development case retains conditional applicability and an `insufficient`
evidence status. Claude read that case before answering, so this is not an
independent held-out test.

Commands and outputs below are inert transcript evidence, not instructions to
run them. All supplied wording, failed/empty searches and the truncated-output
notice are retained. Six PDF form-feed characters are shown as
`[PDF form feed]`; blank lines and Markdown presentation have been tidied.
The referenced Claude session output file was not included in the supplied
transcript. British English is used in the editorial text; original wording,
including spellings and commands, is preserved in the transcript.

- [User prompt](#user-prompt)
- [Claude access transcript](#claude-access-transcript)
- [Claude final answer — unreviewed](#claude-response)

## User prompt

> I've an extended Open Knowledge Format (OKF plus YAML-LD) okf-dwp bundle on my GitHub and also an okf-explorer human view.
>
> Can you use this exclusively to answer the following question, not using the web or your own knowledge:
>
> "Where a child is awarded the highest-rate care component of DLA from 26 January 2025, but the change is reported to Universal Credit on 28 March 2026, what's the effective date of the higher disabled-child addition, and from which assessment period should it be paid?"

## Claude access transcript

*Ran a command on your computer*

*Ran a command on your computer*

### 1. Inspect the local folder

**Recorded command**

```bash
cd "$HOME/mnt/dwp-okf work" && ls -la && find . -maxdepth 3 -type d | head -50
```

**Recorded output**

```text
total 4
drwx------ 2 rcw-01xtdc3urmeoq7lpn9nbfsvp rcw-01xtdc3urmeoq7lpn9nbfsvp   64 Sep 25 15:25 .
drwxr-xr-x 3 rcw-01xtdc3urmeoq7lpn9nbfsvp rcw-01xtdc3urmeoq7lpn9nbfsvp 4096 Sep 25 15:27 ..
.
```

**Claude:** Empty folder — I'll pull the bundle from GitHub.

*Ran 10 commands · 1 note*

*Ran a command*

### 2. Look for repositories

**Recorded command**

```bash
cd /tmp/claude-0/-home-claude/c05ede37-2499-5bf2-b8e2-fb97b663c85c/scratchpad 2>/dev/null || mkdir -p /tmp/claude-0/-home-claude/c05ede37-2499-5bf2-b8e2-fb97b663c85c/scratchpad && cd /tmp/claude-0/-home-claude/c05ede37-2499-5bf2-b8e2-fb97b663c85c/scratchpad; gh repo list chris-page-gov --limit 100 2>&1 | grep -i -E "dwp|explorer|okf"
```

**Recorded output**

```text
(Bash completed with no output)
```

*Ran a command*

### 3. Clone the repositories

**Recorded command**

```bash
cd /tmp/claude-0/-home-claude/c05ede37-2499-5bf2-b8e2-fb97b663c85c/scratchpad; for r in okf-dwp okf-explorer; do git clone -q --depth 1 https://github.com/chris-page-gov/$r.git 2>&1 | tail -2; done; ls; curl -s "https://api.github.com/users/chris-page-gov/repos?per_page=100" | grep -o '"full_name": "[^"]*"' | grep -i -E "okf|dwp|explor"
```

**Recorded output**

```text
okf-dwp
okf-explorer
```

*Ran a command*

### 4. Inspect the repository and search for the topic

**Recorded command**

```bash
cd /tmp/claude-0/-home-claude/c05ede37-2499-5bf2-b8e2-fb97b663c85c/scratchpad/okf-dwp; ls; find . -type f | wc -l; cat README.md | head -80; grep -ril "disabled.child\|disabled child" . | head -40
```

**Recorded output**

```text
AGENTS.md
AI_USAGE.md
CHANGELOG.md
LICENSE
LICENSE_DECISIONS.md
NOTICE.md
README.md
REPOSITORY_STATUS.md
SECURITY.md
bundle
capital-pilot
combined
context
docs
domain-profile
evaluation
evidence-examples
full-dmg
knowledge
logical-context
logical-units
manual-guide
okf.delivery.json
okf.publication.json
okf.semantic.json
pdf-structure
profiles
pyproject.toml
scripts
source
structured-context
structured-units
tools
uv.lock
validation
35286
---
okf_version: "0.2"
---

<a id="pension-credit-guidance-as-an-okf-bundle"></a>

# DWP guidance as an OKF+ bundle

[Evidence workbench guide](docs/evidence-workbench.md): inspect the 40 public
staff questions, their selected source passages, relationships and explicit gaps.
Read the [24 September handover](docs/evidence-workbench-handover.md) for the
verified public release, demonstration steps and remaining limitations.
The [blocked calculation inspection guide](docs/workbench-model-inspection.md)
explains the opt-in, source-bound Pension Credit model and directional carer
interactions. It does not calculate an award.

[Demo 1 freeze plan for 23 September](docs/demo-one-freeze-2026-09-23.md):
tested source-led evidence, forty-question gaps and a four-call comparison cap.

**An independent, unofficial experimental exemplar. Not an official DWP document, benefits advice or an entitlement calculator.**

**[What changed: changelog](CHANGELOG.md)** · [Current work log](docs/evidence-workbench-work-log.md)
· [Backlog and acceptance checks](docs/backlog.md) · [How to repeat the method](docs/methodology.md)
· [What we learned](docs/retrospective.md)
· [Monday handover and demonstration](docs/monday-handover-2026-09-21.md)

This repository turns public Department for Work and Pensions (DWP) guidance into source-linked records, a YAML-LD semantic graph and an indexed OKF Explorer research candidate. It began with a [Pension Credit pilot covering volumes 13 and 14](https://www.gov.uk/government/publications/decision-makers-guide-vols-13-and-14-state-pension-credit-staff-guide), expanded to the [full Decision makers’ guide (DMG)](https://www.gov.uk/government/collections/decision-makers-guide-staff-guide), and now also preserves the separate [Advice for decision making (ADM) manual](docs/adm-acquisition.md). It demonstrates how a specialist or an AI can find evidence, inspect relationships and see what remains uncertain.

**New to the project?** Open the [learning website](https://chris-page-gov.github.io/okf-dwp/docs/learning-path.html)
or follow its [Markdown source](docs/learning-path.md),
or read [how the web edition is published](docs/learning-website.md),
then use the [plain-English glossary](docs/glossary.md) when a benefit name or
technical term appears. It explains Search, Ask OKF and AI answering through
short tasks, including how to connect and why a browser can show HTTP 405.

For the semantic design, see [the ontologies and namespaces actually used](docs/ontology-use.md).
For the separate model trials, see [fixed-evidence answer review](evaluation/answer-review/README.md).
The changelog records dated deliveries; the backlog keeps unfinished work
explicit. Neither replaces the exact receipts below.

[Verified Pension Credit semantic exemplar](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F7d3c69df0571b8d5206c8edce92963d99979cb5c%2Fbundle%2Fokf-bundle.yamlld&view=graph#term/capital-disregards) · [Original meeting demonstration](https://chris-page-gov.github.io/okf-explorer/explore/?bundle=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2F79d21c758e37948fd6d4bde0f1b4d97b266e2e4f%2Fbundle%2Fokf-bundle.yamlld&q=84351#question/pc001) · [Read the pilot bundle](bundle/index.md) · [Ten-minute meeting walkthrough](docs/meeting-walkthrough.md) · [Discovery findings](docs/discovery.md) · [AI interrogation guide](AI_USAGE.md) · [Public notice and rights](NOTICE.md)

<a id="current-public-release-household-evidence"></a>

## Current public release: versioned evidence and paired review

Use the **[latest recorded service publication status](docs/service-publication.md)**
for the selected deployment and SDK observations. This generated page is the shared
status reference for DWP and Explorer; it does not claim real-time health.

### Dated observation: 21 September 2026

The [public evidence service](https://ask-okf.crpage.chatgpt.site/) was recorded as **0.6.0**,
using the partner-qualified source `723bcc5b015ab38a026625c2148edbd784edf7c7`.
Its [actual public SDK check](validation/compact-delivery/v0.6.0/README.md)
reconstructed 11 evidence cases in 121 requests, including exact historical
replay. The current care-home package has 55 records and 115 relationships and
remains insufficient. [Three retained examples](docs/retained-evidence-examples.md)
let a person inspect small evidence parts and the same complete package;
publication and public-browser checks have their own dated receipts.

The [paired direct-v4 trial](validation/model-comparison/household-direct-v4/README.md)
retains both clients' answers to the original care-home question and both empty
controls. All four pass mechanical checks with zero observed tool calls.
The separate agent critique records omitted exceptions and an overstated gap in
one answer. Specialist acceptance and comparative accuracy are not established.
Use the [Monday handover](docs/monday-handover-2026-09-21.md) for the current
source distinctions, remaining work and ten-minute demonstration.

## Earlier public 0.5.0 checkpoint: household evidence

The earlier [public evidence service](https://ask-okf.crpage.chatgpt.site/) ran
**0.5.0**, using fixed DWP source
`3ef0e786e9a18e76fa17c7d925ff509d6d6c9f84`. The
[Monday handover](docs/monday-handover-2026-09-21.md) gives a ten-minute route
through the evidence and its limits.

The [household evidence increment](docs/household-evidence-expansion.md) adds
complete qualifying pages and [selected dated statutory text](docs/legal-body-evidence.md).
Its [source-version evaluation](https://github.com/chris-page-gov/okf-dwp/blob/3ef0e786e9a18e76fa17c7d925ff509d6d6c9f84/evaluation/semantic-expansion/evaluation.json) retained **176 of 177 known candidate-page occurrences** across the staff
./evaluation/model-comparison/household-compact-v2-candidate/packets/staff-026.json
./evaluation/model-comparison/household-compact-v2-candidate/packets/staff-020.json
./evaluation/model-comparison/household-2026-09-21/frozen/contexts/staff-026.json
./evaluation/model-comparison/household-2026-09-21/frozen/contexts/staff-020.json
./evaluation/model-comparison/staff-2026-09-20/contexts/staff-026.json
./evaluation/model-comparison/staff-2026-09-20/budget-controls/65536-corrected/contexts/staff-026.json
./evaluation/model-comparison/staff-2026-09-20/budget-controls/262144/contexts/staff-026.json
./evaluation/backlog.json
./evaluation/manual-structure/auxiliary-review/previous-role-census-leads.json
./evaluation/evidence-workbench/packages/staff-026.json
./evaluation/evidence-workbench/packages/staff-033.json
./evaluation/evidence-workbench/parts/staff-033-008.json
./evaluation/evidence-workbench/parts/staff-026-007.json
./evaluation/evidence-workbench/parts/staff-033-007.json
./evaluation/evidence-workbench/parts/staff-026-008.json
./evaluation/out-of-sample/uc-disabled-child-supersession-001.json
./bundle/records/page/78/0088.md
./bundle/okf-bundle.yamlld
./bundle/okf-bundle.jsonld
./bundle/okf-bundle.nq
./bundle/okf-bundle.json
./source/adm-2026-09-19/publication.json
./source/adm-2026-09-19/text/adm-memo-05-25.txt
./source/adm-2026-09-19/text/adm-memo-05-26.txt
./source/adm-2026-09-19/text/adm-chapter-h6.txt
./source/adm-2026-09-19/text/adm-memo-01-25.txt
./source/adm-2026-09-19/text/adm-chapter-m6.txt
./source/adm-2026-09-19/text/adm-adm-summary-of-changes.txt
./source/adm-2026-09-19/text/adm-chapter-f1.txt
./source/adm-2026-09-19/text/adm-chapter-a3.txt
./source/adm-2026-09-19/text/adm-chapter-e2.txt
./source/adm-2026-09-19/text/adm-memo-06-25.txt
./source/adm-2026-09-19/text/adm-chapter-f3.txt
./source/adm-2026-09-19/text/adm-chapter-h1.txt
./source/adm-2026-09-19/pages/adm-memo-05-25.json
./source/adm-2026-09-19/pages/adm-chapter-f1.json
./source/adm-2026-09-19/pages/adm-chapter-h1.json
./source/adm-2026-09-19/pages/adm-memo-05-26.json
./source/adm-2026-09-19/pages/adm-chapter-e2.json
./source/adm-2026-09-19/pages/adm-chapter-a3.json
```

*Shell cwd was reset to /home/claude*

*Ran a command*

### 5. Read the existing development case

**Recorded command**

```bash
cd /tmp/claude-0/-home-claude/c05ede37-2499-5bf2-b8e2-fb97b663c85c/scratchpad/okf-dwp; cat evaluation/out-of-sample/uc-disabled-child-supersession-001.json | head -150
```

**Recorded output**

```text
{
  "schema": "okf-dwp-out-of-sample-evidence-case.v1",
  "id": "uc-disabled-child-supersession-001",
  "status": "prospective-follow-up-after-initial-observation",
  "question": "Where a child is awarded the highest-rate care component of DLA from 26 January 2025, but the change is reported to Universal Credit on 28 March 2026, what is the effective date of the higher disabled-child addition, and from which assessment period should it be paid?",
  "question_sha256": "c224ca359a090e29fbca4e58127f5e94968aab1808e2e1ae3801b395a39eb3e8",
  "scope": {
    "benefit": "Universal Credit",
    "topic": "higher disabled-child addition after DLA highest-care award",
    "not_in_frozen_staff_40": true,
    "personal_data": "none; hypothetical dates only"
  },
  "source_binding": {
    "corpus_manifest": "structured-context/evidence-connect-manifest.json",
    "corpus_sha256": "4e65253f72b2d771164d5ddd64374ed8142cf66b4a249f193a1fe44d5679f519",
    "engine_files": {
      "index.ts": "689f8b8ab1cfb5ccc21b6dd9b5527fcad04de01f5876b44cbb2dc0240fceb010",
      "corpus.ts": "a770352c6e4628f0c391b0c12bbdaf185b476a714ca212e99459d135f8f57f6f",
      "corpusV3.ts": "944617e1630362b7a41d60da92651007b96252eff3075eb4c4b852f420f5a5c0",
      "types.ts": "febf83b5c65153fd2e49ac070b6117525463034fb1b33534a086a1cc7bbb42cc"
    },
    "model_calls": 0,
    "network_calls_in_replay": 0
  },
  "source_targets": [
    {
      "role": "higher-rate condition",
      "document": "adm-chapter-f1",
      "pdf_page": 18,
      "source_sha256": "124b7e41af2b491209f694941482e6e4bb69e78692a84a343299dc53f25b8731",
      "paragraph": "F1123",
      "unit_id": "https://chris-page-gov.github.io/okf-dwp/id/unit/adm/adm-chapter-f1/manual-structure-v1/source-0000024273-000-64312571d5f1",
      "observed_selected": true
    },
    {
      "role": "child addition context",
      "document": "adm-chapter-f1",
      "pdf_page": 17,
      "source_sha256": "124b7e41af2b491209f694941482e6e4bb69e78692a84a343299dc53f25b8731",
      "paragraph": "F1120–F1121",
      "unit_id": "https://chris-page-gov.github.io/okf-dwp/id/unit/adm/adm-chapter-f1/manual-structure-v1/source-0000023318-000-bec866c4cfa0",
      "observed_selected": false
    },
    {
      "role": "ordinary late notification and explicit exception pointer",
      "document": "adm-chapter-a4",
      "pdf_page": 34,
      "source_sha256": "4933d66a1cd118687bbc10e30faf9ee8214d09b3e465e58efdbd9b832a58a8e8",
      "paragraph": "A4352",
      "unit_id": "https://chris-page-gov.github.io/okf-dwp/id/unit/adm/adm-chapter-a4/manual-structure-v1/source-0000055420-000-9e9c31f56b39",
      "observed_selected": false
    },
    {
      "role": "other-benefit effective-date branch and examples",
      "document": "adm-chapter-a4",
      "pdf_pages": [
        36,
        37
      ],
      "source_sha256": "4933d66a1cd118687bbc10e30faf9ee8214d09b3e465e58efdbd9b832a58a8e8",
      "paragraph": "A4361",
      "unit_id": "https://chris-page-gov.github.io/okf-dwp/id/unit/adm/adm-chapter-a4/manual-structure-v1/source-0000059337-000-65ba8377e1e6",
      "observed_selected": false
    }
  ],
  "observed_replay": {
    "method": "one deterministic file-backed assembleCorpusContext call; manifest-listed bytes and hashes checked; no model or network calls",
    "budget": {
      "max_bytes": 524288,
      "max_nodes": 64,
      "max_relationships": 128,
      "max_depth": 6
    },
    "context_id": "urn:sha256:43f4938a16557acbdb593e9f74687b682e7630a08bcd7a5be8185bf9bad9fcf2",
    "used_bytes": 522141,
    "selected_evidence_count": 35,
    "retrieval_candidate_count": 24158,
    "evidence_status": "insufficient",
    "omission_codes_observed": [
      "retrieval_query_budget",
      "retrieval_candidate_budget",
      "retrieval_resource_budget"
    ],
    "unrelated_requirement_id": "https://chris-page-gov.github.io/okf-dwp/id/requirement/staff/staff-008",
    "interpretation": "F1123 source discovery succeeds; A4361 and the late-rule exception are absent. The unrelated requirement and budgets make this a navigation and task-routing gap, not an answer-quality score.",
    "replay_command": "node scripts/replay_uc_supersession_case.mjs --explorer-root /path/to/pinned-okf-explorer"
  },
  "conditional_source_reading": {
    "if": "DLA highest-care entitlement legally began 26 January 2025; the child was a UC family member and otherwise qualified; A4361 governs this change",
    "then": "first day of the UC assessment period containing 26 January 2025",
    "exact_calendar_date": "unknown: assessment-period start and end absent",
    "payment_period": "the assessment period containing the established DLA entitlement date, conditional on applicability and award review",
    "decision_status": "not established"
  },
  "required_unknowns": [
    "UC assessment-period boundaries and UC award throughout the retrospective period",
    "Legal start date of highest-rate DLA entitlement, distinct from administrative award date",
    "Responsibility for the child and child-element/addition conditions, including age, absence and looked-after qualifications",
    "Other UC notifications, intervening decisions or changes, jurisdiction and operative statutory version",
    "Independent review of Schedule 1 paragraph 31 and UC regulation 24 and their application to this addition"
  ],
  "acceptance_boundary": {
    "navigation_next": "Test source-bound A4361, A4352 and F1120 selection with the F1123 hit, exact spans and bounded delivery, on frozen positive and negative controls. Record omissions and task-profile activation separately.",
    "answerability": "Keep insufficient and null answer until legal-body, scope, dependency and specialist review are complete. Do not infer entitlement or arrears.",
    "negative_controls": [
      "DLA entitlement starts later than asserted",
      "Only lower-rate DLA care",
      "Child outside claimant UC family",
      "Notification within the change assessment period",
      "Other change governed by ordinary late rule"
    ]
  },
  "limitations": [
    "The initial question is now a development case; freeze independent future wording before tuning.",
    "A4361 examples include DLA and the UC carer element, not a specific disabled-child addition determination.",
    "The official A4 PDF was read on 24 September 2026. The official F1 URL was not accessible through the web reader; its retained 19 September PDF was read.",
    "Live legislation.gov.uk provision requests returned HTTP 429; statutory bodies were not verified in this investigation.",
    "Machine-detected unit boundaries and retained source capture do not establish current legal applicability."
  ]
}
```

*Shell cwd was reset to /home/claude*

**Claude:** The bundle already has this as a development case. Let me read the underlying source paragraphs directly.

*Ran a command*

### 6. Read the retained ADM paragraphs

**Recorded command**

```bash
cd /tmp/claude-0/-home-claude/c05ede37-2499-5bf2-b8e2-fb97b663c85c/scratchpad/okf-dwp/source/adm-2026-09-19/text; ls | grep -E "f1|a4"; awk '/^F1120/,/^F1125/' adm-chapter-f1.txt | head -60
```

**Recorded output**

```text
adm-chapter-a4.txt
adm-chapter-f1.txt
F1120 In addition to the child element described at F1055, a further amount is included in the calculation

of the UC maximum amount for each child or qualifying young person who is disabled 1. This will be
awarded at either a lower or a higher rate.


                                                                                        1 UC Regs, reg 24(2)


F1121 Disabled is not defined but for the purpose of this addition should be taken to mean a person who
is


1. blind or


2. entitled to DLA, CDP, ADP, SADLA or PIP.



Rate of disabled child addition



F1122 Unless F1123 applies, the lower rate of disabled child addition 1 is included where the child or
qualifying young person is


1. entitled to DLA or


2. entitled to SADLA or


3. entitled to CDP or


4. entitled to ADP or


5. entitled to PIP.


                                                                                     1 UC Regs, reg 24(2)(a)
[PDF form feed]F1123 The higher rate of disabled child addition1 is included where the child or qualifying young person is


1. entitled to the care component of DLA at the highest rate or


2. entitled to the care component of SADLA at the highest rate or


3. entitled to the care component of CDP at the highest rate or


4. entitled to the daily living component of ADP at the enhanced rate or


5. entitled to the daily living component of PIP at the enhanced rate or
```

*Shell cwd was reset to /home/claude*

*Ran a command*

### 7. Inspect the effective-date rules — output truncated

**Recorded command**

```bash
cd /tmp/claude-0/-home-claude/c05ede37-2499-5bf2-b8e2-fb97b663c85c/scratchpad/okf-dwp/source/adm-2026-09-19/text; awk '/^F1123/,/^F1126/' adm-chapter-f1.txt | sed -n 18,40p; echo =====; awk '/^A4350/,/^A4364/' adm-chapter-a4.txt | grep -v '^\s*$'
```

**Recorded output**

```text
<persisted-output>
Output too large (79.7KB). Full output saved to: /root/.claude/projects/-home-claude/c05ede37-2499-5bf2-b8e2-fb97b663c85c/tool-results/bkosujhsp.txt

Preview (first 2KB):
=====
A4350 Decisions which are advantageous to the claimant include those where
1. the amount of benefit is increased, or is awarded for a longer period 1 or
2. the amount of benefit in payment would be increased but for the application of a provision in the law 2
restricting or suspending payment of a benefit or disqualifying a claimant from receiving benefit or
3. a denial or disqualification for receiving benefit is lifted whether in whole or in part (a partial lifting of a
disqualification would include, for example, where the period of a JSA sanction is reduced in length) 3 or
4. a decision to pay benefit to a third party is reversed4 or
5. an overpayment is not recoverable or the amount recoverable is reduced 5 or
6. the claimant gains financially6.
Note: See ADM Chapter D1 for guidance on overpayment decision making.
                                                 1 UC, PIP, JSA & ESA (D&A) Regs, reg 52(5)(a); 2 reg 52(5)(b);
                                                     3 reg 52(5)(c); 4 reg 52(5)(d); 5 reg 52(5)(e); 6 reg 52(5)(f)
Example
Anna is in receipt of UC. Her assessment period runs from 16th of the month to 15th of the following
month. She rings up on Saturday 16th February to notify a change of circumstances. The office is closed.
She rings up again on Monday 18th February. The DM supersedes the award of UC from 16th January.
[PDF form feed]Effective dates when changes notified within the time limits
A4351 Where an appropriate office is notified of an advantageous change of circumstances within the
relevant notification period or within such longer period as may be allowed under A4310 - A4315, the
effective date of the supersession will be
1. for ESA and JSA1, the first day of the benefit week in which the change occurs or is expected to occur
2. for PIP2, the day on which the change occurs or is expected to occur
3. for UC3, the first day of the assessment period in which the change occurs or is expected to occur
...
</persisted-output>
```

*Shell cwd was reset to /home/claude*

*Ran a command*

### 8. Locate paragraph boundaries

**Recorded command**

```bash
cd /tmp/claude-0/-home-claude/c05ede37-2499-5bf2-b8e2-fb97b663c85c/scratchpad/okf-dwp/source/adm-2026-09-19/text; grep -n -E "^A43(5[1-9]|6[0-5])" adm-chapter-a4.txt | head; grep -n -E "^F112[3-6]" adm-chapter-f1.txt
```

**Recorded output**

```text
1703:A4351 Where an appropriate office is notified of an advantageous change of circumstances within the
1737:A4352 Where an advantageous change of circumstances is notified later than one month after it
1755:A4353 In the case of PIP1,
1797:A4354 In the case of PIP where the claimant becomes entitled to another relevant benefit under
1812:A4360 In the case of a UC claimant where
1839:A4361 In the case of UC where the claimant or a member of their family becomes entitled to another
1881:A4362 - A4364
1887:A4365 Where a DM supersedes on their own initiative to deal with a change of circumstances and the
801:F1124 Where
819:F1125 – F1138
```

*Shell cwd was reset to /home/claude*

*Ran a command*

### 9. Read the exception and worked examples

**Recorded command**

```bash
cd /tmp/claude-0/-home-claude/c05ede37-2499-5bf2-b8e2-fb97b663c85c/scratchpad/okf-dwp/source/adm-2026-09-19/text; sed -n 780,825p adm-chapter-f1.txt | grep -v '^\s*$'; echo =====; sed -n 1737,1760p adm-chapter-a4.txt | grep -v '^\s*$'; echo ====; sed -n 1812,1890p adm-chapter-a4.txt | grep -v '^\s*$'
```

**Recorded output**

```text
6. blind2
                                                                             1 UC Regs, reg 24(2)(b); 2 reg 2
Additional amount for disabled child or qualifying young person
Lower rate                             £164.79
Higher rate                            £514.71
Run on after death
F1124 Where
1. a claimant’s award of UC includes a disabled child addition for a child or qualifying young person for
whom they are responsible and
2. that child or qualifying young person dies
the disabled child addition will continue in payment until the end of the second assessment period
following the assessment period in which the death occured 1.
                                                                                           1 UC Regs, reg 37
F1125 – F1138
[PDF form feed][PDF form feed]Definitions F1139 - F9999
Blind F1139
=====
A4352 Where an advantageous change of circumstances is notified later than one month after it
occurred, or for UC after the end of the assessment period in which the change occurred (or such longer
period as the DM may have allowed under A4310 - A4315) then the effective date of the supersession
will be
1. for ESA and JSA1, from the beginning of the benefit week in which the notification was made
2. for PIP2, from the date of notification of the change (but see A4353)
3. for UC3, from the first day of the AP in which the notification was made (but see A4360 - A4361)
      1 UC, PIP, JSA & ESA (D&A) Regs Sch 1, part 1, para 6; 2 Sch 1, part 2, para 14; 3 Sch 1, part 3, para 21
A4353 In the case of PIP1,
1. where the change is relevant to entitlement to a particular rate and
====
A4360 In the case of a UC claimant where
1. the relevant change is that the person’s employed earnings are reduced and
2. the claimant provides such information for calculating those earnings at such times as may be
required
[PDF form feed]the superseding decision takes effect1 from the first day of the assessment period in which that change
occurred.
                                                     1 UC, PIP, JSA & ESA (D&A) Regs, Sch 1, Part 3, para 22
Example
Tony is in receipt of UC and works part time in a bingo hall. His assessment period starts on the 15th of
each month. His hours are reduced on 28 February. He informs DWP of this change and is asked to
provide details of his new earnings. Tony does this and the DM supersedes the award of UC from 15
February to take into account his reduced earnings.
UC and award of other benefits
A4361 In the case of UC where the claimant or a member of their family becomes entitled to another
relevant benefit, ceases to be entitled or the rate of another such benefit alters then the superseding
decision takes effect1 from the first day of the assessment period in which entitlement to the other
benefit or an alteration in its rate arises or entitlement ends.
 1 SS Act 98, s 8(3); DAWAP(S)Regs, reg 2; DACYP (S)Regs, reg 2; UC, PIP, JSA & ESA (D&A) Regs, Sch 1,
                                                                                 Part 4, para 31(1) & 31(2)(a)
Example 1
Sam has been in receipt of UC from 21.11.19. On 28.5.20 she was awarded CA from 30.3.20 meaning that
she is also entitled to the carer element in UC. Sam didn't notify the change until 24.9.20. The
supersession effective date rule means that she did not have to report the change within a certain
period. The UC award is superseded on the grounds of a relevant change of circumstances and the carer
element is awarded from 21.3.20.
Example 2
Connor has been in receipt of UC from 14.12.18. On 11.5.21 his daughter was awarded DLA at the middle
rate from 8.2.21. He didn't notify the change until 26.5.21. The DM is satisfied that Connor had regular
and substantial caring responsibilities for a severely disabled person since 8.2.21 and so there is a clear
and direct link between the award of DLA and entitlement to the carer element. The supersession
effective date rule means that he did not have to report the change within a certain period. The UC award
is superseded on the grounds of a relevant change of circumstances and the carer element is awarded
from 14.1.21.
Example 3
Matt is in receipt of UC and JSA. He starts part time work and receives payment from this employment in
the final week of his assessment period. His award of JSA is terminated. The DM supersedes the award
[PDF form feed]of UC from the first day of the assessment period so that JSA is no longer taken into account when
determining the amount of UC payable.
A4362 - A4364
DM’s own initiative
A4365 Where a DM supersedes on their own initiative to deal with a change of circumstances and the
result is advantageous to the claimant the supersession takes effect
```

*Shell cwd was reset to /home/claude*

*Ran a command*

### 10. Search for a definition — empty result

**Recorded command**

```bash
cd /tmp/claude-0/-home-claude/c05ede37-2499-5bf2-b8e2-fb97b663c85c/scratchpad/okf-dwp/source/adm-2026-09-19/text; grep -n -i -B2 -A8 "relevant benefit.*means\|\"relevant benefit\"\|relevant benefit is\|relevant benefits are" adm-chapter-a4.txt | head -40
```

**Recorded output**

```text

```

*Shell cwd was reset to /home/claude*

*Ran a command*

### 11. Search the retained manual for the term

**Recorded command**

```bash
cd /tmp/claude-0/-home-claude/c05ede37-2499-5bf2-b8e2-fb97b663c85c/scratchpad/okf-dwp/source/adm-2026-09-19/text; grep -l -i "relevant benefit" *.txt; grep -n -i -A10 "relevant benefit\" means\|“relevant benefit”\|relevant benefit means" *.txt | head -40
```

**Recorded output**

```text
adm-adm-summary-of-changes.txt
adm-annex-d.txt
adm-chapter-a1.txt
adm-chapter-a3.txt
adm-chapter-a4.txt
adm-chapter-a5.txt
adm-chapter-b2.txt
adm-chapter-c4.txt
adm-chapter-e5.txt
adm-chapter-l5.txt
adm-chapter-r1.txt
adm-chapter-u1.txt
adm-chapter-v2.txt
adm-memo-01-23.txt
adm-memo-02-25.txt
adm-memo-06-21.txt
adm-memo-06-25.txt
adm-memo-08-18.txt
adm-memo-10-23.txt
adm-memo-11-22.txt
adm-memo-14-21.txt
adm-memo-17-23.txt
adm-memo-18-23.txt
adm-memo-19-20.txt
adm-memo-33-20.txt
```

*Shell cwd was reset to /home/claude*

<a id="claude-response"></a>

## Claude final answer — unreviewed

*Verbatim response with paragraph and list formatting added.*

Going only by your okf-dwp bundle (the retained ADM text from 19 September 2026), the short answer is that the late report doesn't push the date forward.

Effective date: the first day of the Universal Credit assessment period that contains 26 January 2025. It is not the period that contains 28 March 2026, when the change was reported.

Paid from: that same assessment period, the one containing 26 January 2025. The award is backdated from there, which means over a year of arrears.

### Why, from the source

- The addition applies. ADM F1123 says the higher rate of disabled child addition is included where the child is "entitled to the care component of DLA at the highest rate". The legal reference given is UC Regs reg 24(2)(b), and the retained rate is £514.71.

- The normal late-reporting rule would give the wrong date. ADM A4352 says that for UC, a helpful change reported after the end of its assessment period takes effect "from the first day of the AP in which the notification was made". On that rule alone, the addition would start in the 28 March 2026 period. But A4352 itself says "but see A4360 - A4361".

- A4361 overrides it. Where a claimant or a family member "becomes entitled to another relevant benefit… or the rate of another such benefit alters", the change takes effect "from the first day of the assessment period in which entitlement to the other benefit or an alteration in its rate arises". The legal reference is D&A Regs Sch 1 Part 4 para 31.

- The worked examples support this. In A4361 Example 1, the claimant "did not have to report the change within a certain period". In Example 2, a child's DLA was awarded from 8.2.21 and reported late on 26.5.21. The UC award was changed back to 14.1.21, the start of the assessment period that contained 8.2.21.

### What the bundle can't settle

- Exact calendar date. It depends on when the claimant's assessment periods start, which the question doesn't say. For example, if they run from the 14th, the answer would be 14 January 2025.

- What 26 January 2025 means. The answer assumes it is the date DLA entitlement legally began, not the date the decision was made. It also assumes the child was in the UC family and met the other conditions throughout.

- Examples cover a different element. A4361's examples are about the carer element, not the disabled child addition itself. The bundle's own development case (evaluation/out-of-sample/uc-disabled-child-supersession-001.json) marks this reading as conditional and "not established". It notes that the statutory text hasn't been checked independently.

- Gap in your retrieval. That same case file records that a replay of the engine found F1123 but not A4361 or the A4352 exception pointer. So a user relying on the Explorer's automatic evidence selection alone could get the wrong answer, the notification-period date.

This reads the bundle's retained guidance. It isn't benefits advice or a decision on entitlement.
