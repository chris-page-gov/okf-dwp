# Connect ChatGPT to Ask OKF and check what works

[Learning path](learning-path.md) · [Recorded service status](service-publication.md) · [Backlog](backlog.md)

**An available service is not proof that a particular chat can call it.** A
plugin connects ChatGPT to tools. A tool is a named operation the AI can request;
its **schema** defines the accepted inputs. Each conversation must have the
right tools and schemas available before it can use Ask OKF.

Ask OKF supplies evidence, provenance and gaps. **Provenance** means where the
material came from and which version was used. An AI's explanation is a separate
output. This is an independent experiment, not an official DWP service or an
individual entitlement decision. Use only the public demonstration questions.

## What was observed on 21 September 2026

| Surface | Observation | What remains unproved |
| --- | --- | --- |
| Public service | The [recorded 0.6.0 SDK check](../validation/compact-delivery/v0.6.0/README.md) reconstructed 11 cases in 121 requests. | Access from each ChatGPT conversation or Data Agent task. |
| Existing ChatGPT Ask OKF connection | Refresh displayed “Actions refreshed.” Three read-only tools, five source versions and two engine identifiers appeared. Permissions were unchanged. | Successful calls from a new conversation using those refreshed schemas. |
| Existing Codex task | Its available metadata still described only the old `ask_okf` tool and two source versions. A single-character control succeeded; a longer question was rejected by input validation. | Updated tools becoming available in that existing task. |
| Planned 0.6.1 correction | A schema correction addresses clients interpreting the old `\S` pattern as a whole-string match. | Deployment, another refresh and a successful multi-character client check. |

These are separate observations. The first refresh still advertised the old
question pattern. Do not treat it as verification of the correction. Consult the
[generated service status](service-publication.md) for recorded deployment and
SDK results; it does not report real-time availability. No Data Agent or Voice
acceptance is claimed here. The [paired model trials](monday-model-trials.md)
used a different, explicitly recorded workflow.

The [client observation record](../validation/client-connection/2026-09-21/README.md)
retains the rejected call and the returned one-character control package, with
private broker metadata removed.

## 1. Refresh the existing connection after release

Once the corrected release has been recorded:

1. Open [ChatGPT Plugins](https://chatgpt.com/plugins) in the intended account.
2. Open **Ask OKF → Plugin actions → Manage**. This was the observed route for
   the existing developer-mode connection.
3. Check that its address is `https://ask-okf.crpage.chatgpt.site/okf/mcp`.
4. Select **Refresh** and confirm that the advertised metadata changed.
5. Check for the three tools below, then start a **new** conversation.

Refreshing metadata follows OpenAI's [connection and testing guidance](https://developers.openai.com/plugins/deploy/connect-chatgpt).
It does not require broader permissions or reinstalling this existing connection.
If the connection is absent, stop this refresh procedure and record that fact;
connection setup is a separate step subject to the account's policy.

| Tool | Purpose |
| --- | --- |
| `ask_okf_manifest` | Start with a small catalogue: selected records, identities and gap counts. It does not contain the full source passages. |
| `read_okf_evidence` | Read exact parts of that package, including source text, relationships and diagnostics. |
| `ask_okf` | Return the complete package at once; this can be too large for a client. |

For this release family, check for five approved source versions, including
`723bcc5b015ab38a026625c2148edbd784edf7c7`, and an `engine_id` field.
The expected corrected question pattern is `^[\s\S]*\S[\s\S]*$`.
These checks establish advertised capability, not a successful call.

## 2. Start a new Work conversation

On the ChatGPT homepage, select **Work**, start a new conversation, type `@`
and select **Ask OKF**. This is the test route in OpenAI's
[plugin quickstart](https://developers.openai.com/plugins/quickstart).
Mentioning only Data, or pasting a service URL, does not establish that Ask OKF's
tools are callable in that task. If Work or Ask OKF is unavailable, record the
visible limitation. Do not substitute browsing or model knowledge for this test.

## 3. Run the empty-evidence control first

Paste this after selecting Ask OKF. The invented word deliberately tests whether
the client acknowledges missing evidence. It is not a benefits question.

```text
Use only the Ask OKF tools available in this conversation. If
ask_okf_manifest or read_okf_evidence is unavailable, report
NO CALL: REQUIRED ASK OKF TOOL UNAVAILABLE and stop. Do not browse,
call another plugin or answer from memory.

Call ask_okf_manifest with bundle "okf-dwp", version
"723bcc5b015ab38a026625c2148edbd784edf7c7", engine_id
"urn:okf:context-engine:sha256:e94ce301033de019d1051684acfd02803a3fe306fd963b44bd3f4b7dba16f652",
question "xylophonicquasarteleportation", and budget
{"max_nodes":64,"max_relationships":128,"max_depth":6,"max_bytes":524288}.

Preserve the returned version, engine_id, context_id and exact replay
budget. Read diagnostics with read_okf_evidence using that same
question and those identities; follow next_offset until null.
Report the actual status, selected-record count, unresolved terms
and missing evidence. Do not invent a meaning or make benefits claims.
If a call fails, record its tool, arguments and error and stop.
```

The [recorded SDK control](../validation/compact-delivery/v0.6.0/README.md)
returned no selected records and insufficient evidence. Check the new response;
do not copy that expected result into an observation.

## 4. Try the fixed care-home question

Only continue after the control succeeds. This preserves the supplied Staff 012
wording, including its typo, so results can be compared.

```text
Use the same Ask OKF source, engine and budget as the successful control.
Start a NEW context with ask_okf_manifest, omitting the control's
context_id. Use this exact question:
"Does Pension Credit stop is a citizen moves into a care home permanently if they are self-funding?"

Preserve this new result's version, engine_id, context_id and replay
budget for every subsequent call. Follow catalogue delivery.next_offset
until null. Use read_okf_evidence to read diagnostics and the complete
package in contiguous section="package" slices; follow next_offset until
null and check context identity and content_sha256 on every part.

Concatenate the parts exactly. Verify the complete content_sha256 only
if a suitable local hash facility is available; otherwise explicitly
record HASH NOT INDEPENDENTLY VERIFIED. Do not claim complete delivery
if a part is missing, truncated or unavailable. If any tool is missing
or fails, stop and report the actual limitation without external retrieval.

Using only the received evidence, give a cautious partial explanation.
Separate the whole award from each additional amount. Retain headings,
household conditions, exceptions, dates and gaps. Link each substantive
claim to its selected record and source locator. Keep the bundle's
evidence_status and distinguish quoted source from your interpretation.
Do not decide an individual's entitlement or fill gaps from memory.
Finish with the actual tools called, identities, delivery limits and
unresolved evidence needed for a fuller answer.
```

A **context identifier** identifies the assembled result. An **engine identifier**
identifies the assembler implementation. A **budget** limits selected material;
it is different from each small response's delivery limit. A **hash** checks
exact bytes. Reading every slice completes transport of that bounded package;
it cannot restore evidence omitted during assembly. See the
[evidence-delivery lesson](evidence-delivery-learning.md).

## 5. Record acceptance without overstating it

Retain a public-safe observation with:

- date and time, client surface and reported model if visible;
- advertised tools/schema and whether refresh or a new conversation was needed;
- exact public question, actual tool names, arguments, responses and errors;
- source version, engine, context identifier, budget and any continuation gaps;
- selected evidence and source links, sufficiency status and missing information;
- whether complete-byte reconstruction and its hash were independently checked;
- the AI's claims and qualifications, separately from the tool evidence.

Use **no call**, **rejected**, **partial delivery** or **completed delivery** as
appropriate. Record failures as well as successes. Keep account identifiers,
private conversations, credentials and claimant information out of the public
record. A completed call is not specialist review or proof of answer accuracy.

Client acceptance remains **DWP-BL-008.client-connection**; Voice and room audio
remain **DWP-BL-016**. A Data Agent test needs its own observed tool calls and
evidence checks. There is no automatic acceptance transfer between clients.
