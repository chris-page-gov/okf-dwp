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

## Choose the right route

| Route | What it reads | What it can do |
| --- | --- | --- |
| [Saved Evidence workbench](evidence-workbench.md) | Forty retained, hash-checked question packages from the immutable [inspection manifest](https://raw.githubusercontent.com/chris-page-gov/okf-dwp/d31f16fb7143d04b9de73e14cd493cfb832ae83e/evaluation/evidence-workbench/tools-manifest.json). | A person can inspect saved evidence. A compatible browser can expose seven **page tools** to inspect it or change the displayed view. Opening a package does not assemble a new answer. |
| [Explorer Reader and Ask OKF](evidence-workbench.md) | The additive [source descriptor](https://raw.githubusercontent.com/chris-page-gov/okf-dwp/7eeded763042ddd0070f4fed834c6074149e8e2f/structured-context/evidence-connect-explorer.json), which points to the reviewed full DMG and ADM corpus. | Assemble **fresh evidence** for a general question in the browser, then inspect its source text and gaps. This is separate from the saved forty cases. |
| [Remote Ask OKF MCP service](service-publication.md) | Only source and engine versions admitted by that deployment. | Three read-only tools can assemble and deliver versioned evidence to a connected client. This service has its own publication and client checks; page tools and a Reader link do not update it. |

The saved inspection manifest at `d31f16fb…` reuses packages produced from the
additive `7eeded763…` source. Those Git commits identify different artefacts,
not two interchangeable service versions. The **recorded** remote publication
is on the [shared service status page](service-publication.md); a newer service
must pass its own release and client checks before this guide can describe it as
available. None of these routes determines entitlement or calculates an award.

For the saved workbench route, the [Edge sidebar observations](workbench-sidebar-demo.md)
include a successful, developer-assisted staff-016 Requirements view in a fresh
conversation on 25 September. An earlier attempt that day failed before a
prompt could be sent. The success used authorised native page tools through
the existing CDP connection; it did not discover the remote MCP tools or prove
automatic WebMCP availability in other clients.

## What was observed on 25 September 2026

Service 0.7.0 admits the additive Evidence Connect source at `7eeded763…`.
Its exact merged build passed twelve public SDK cases in 135 requests,
including older replay combinations. See the [release evidence](../validation/compact-delivery/v0.7.0/README.md).

The existing Codex task could call the compact catalogue immediately, but its
exact read was rejected because the connector still advertised older source
and engine values. Refreshing the existing connection, with permissions
unchanged, admitted those values. The same task then reconstructed and
hash-checked all diagnostics in eleven bounded reads. The
[before/after record](../validation/client-connection/2026-09-25/remote/README.md)
retains both outcomes. This is separate from the successful sidebar page-tool
demonstration and does not prove Voice or a complete benefits answer.

## What was observed on 21 September 2026

| Surface | Observation | What remains unproved |
| --- | --- | --- |
| Public service | [Service 0.6.1 was published and its SDK check passed](../validation/compact-delivery/v0.6.1/README.md): 11 cases reconstructed through 121 requests, with the source and engines unchanged. | Access from each ChatGPT conversation or Data Agent task. |
| Existing ChatGPT Ask OKF connection | Refresh displayed “Actions refreshed.” Three read-only tools now advertise the corrected question pattern, five source versions and two engines. Permissions were unchanged. | Compact-tool calls from the intended new conversation or Data Agent task. |
| Existing Codex task | The same multi-character unknown-term question rejected before the patch now returned an empty, insufficient package. Its tool catalogue still exposes only the full `ask_okf` tool. | The compact catalogue and exact-read tools becoming callable in that task. |
| Staff 012 small-budget check | The exact supplied question reached the service, but its 16 KiB package budget returned zero records and an explicit byte-budget omission. | Useful substantive evidence, a complete client evidence journey or an AI answer. |

The [before-and-after client observations](../validation/client-connection/2026-09-21/README.md)
retain the original rejection and both later returned packages. The successful
unknown-term call demonstrates that this connector now accepts that longer
question. It does not establish that every conversation receives the same tools.
The first refresh had still advertised the old pattern; the later refresh
observed the corrected pattern after publication.

Consult the [generated service status](service-publication.md) for recorded
deployment and SDK results; it does not report real-time availability. No Data
Agent or Voice acceptance is claimed here. The [paired model trials](monday-model-trials.md)
used a different, explicitly recorded workflow. Private broker metadata is
excluded from the client observations.

## 1. Refresh the existing remote connection after a recorded release

Check the [shared service status](service-publication.md), then inspect the
connection in the account and conversation you intend to use. The earlier
0.6.1 refresh does not update every already-open task or admit a later source.

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

For the recorded 0.6.1 observation, five approved source versions included
`723bcc5b015ab38a026625c2148edbd784edf7c7`, and an `engine_id` field.
The expected corrected question pattern is `^[\s\S]*\S[\s\S]*$`.
These are historical schema checks, not a promise about a later release. If a
new [recorded service publication](service-publication.md) has different
source/engine versions but this conversation still shows the older schema,
refresh the existing connection and use a new conversation before testing.
An older cached schema cannot admit a newer corpus. A refresh establishes
advertised capability, not a successful call; do not broaden permissions.

## 2. Start a new Work conversation

On the ChatGPT homepage, select **Work**, start a new conversation, type `@`
and select **Ask OKF**. This is the test route in OpenAI's
[plugin quickstart](https://developers.openai.com/plugins/quickstart).
Mentioning only Data, or pasting a service URL, does not establish that Ask OKF's
tools are callable in that task. If Work or Ask OKF is unavailable, record the
visible limitation. Do not substitute browsing or model knowledge for this test.

### A short remote evidence read

After starting a new conversation and confirming that it exposes both compact
tools, this starter uses an ordinary, non-personal example question. It asks
for a fresh package from the service's **advertised default**; it makes no
claim that a later source has already been deployed. This phrasing is
illustrative, not a frozen acceptance case.

```text
Use only this conversation's Ask OKF tools. For this general question
"What DWP guidance is relevant when someone receiving Pension Credit moves
permanently into a care home and pays their own fees?", call
ask_okf_manifest with bundle "okf-dwp" and budget
{"max_nodes":64,"max_relationships":128,"max_depth":6,"max_bytes":524288},
and delivery_bytes 16384.
Omit version and engine_id only for this new default-engine question.

Preserve the returned question, version, engine_id, context_id and exact
replay budget. Follow catalogue delivery.next_offset until null with those
same identities. Call read_okf_evidence for diagnostics and the relevant
selected passages, source metadata and qualifications with delivery_bytes
16384; follow each read result's next_offset until null. For record_text and
record_metadata, use the exact selected record_id from the catalogue. If a
tool is unavailable or a read cannot be completed, report that and stop
rather than filling gaps from memory.

Explain only what the received guidance supports. Name the source locators,
evidence_status, missing evidence and any budget omissions. Do not decide an
individual's entitlement, invent a current legal version or call another
plugin. List the actual tools and identities used.
```

This is a **low-context inspection**, not proof that the complete package was
delivered or independently hash-verified. The longer controlled journey below
shows how to read every package slice when that is required. The [OpenAI site
tools guide](https://help.openai.com/en/articles/20001423-using-site-tools-in-the-chatgpt-desktop-app)
and [browser extension guide](https://learn.chatgpt.com/docs/chrome-extension)
describe different host routes; check the tools actually available in this
conversation rather than assuming one host's support transfers to another.

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

The [recorded 0.6.1 SDK control](../validation/compact-delivery/v0.6.1/README.md)
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

The native 16 KiB Staff 012 check was deliberately a smaller package than this
512 KiB comparison. It returned only a 2,032-byte refusal, with no selected
evidence. By contrast, the SDK reconstructed the 523,326-byte package at the
comparison budget, containing 55 records and 115 relationships. Both results
remain **insufficient**. Small delivery slices let a client receive the larger
bounded package; shrinking the package itself can discard all useful evidence.
The intended compact-client journey above still needs its own observation.

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
Selecting **Ask OKF** in a parent chat also does not prove that a separate Data
Agent run receives those tools. Record that agent's own call and result; tool
availability must be established at the point where the agent runs.

For a separate analysis when a host cannot expose these tools, an explicitly
supplied [retained evidence example](retained-evidence-publication.md) can still
give an AI the same inspectable material. Label that a **frozen evidence
handoff**, preserve its recorded identities and gaps, and keep the failed live
connection test. It is not a fresh MCP invocation or a substitute acceptance pass.
