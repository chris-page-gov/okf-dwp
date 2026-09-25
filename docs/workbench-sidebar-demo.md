# Demonstrate the workbench from the ChatGPT sidebar

The Edge ChatGPT sidebar successfully read registered page tools, changed the
Evidence workbench view and explained the returned evidence on 24 September
2026. This is a recorded working route through an existing developer connection.
Automatic discovery through a dedicated WebMCP connection remains unverified
in that host.

This demonstration uses the **saved Evidence workbench** and its seven page
tools. For a new evidence assembly, use [Explorer Reader and Ask OKF](evidence-workbench.md).
For the separate three-tool remote MCP service, use the [connection guide](chatgpt-connection.md)
and its [recorded publication status](service-publication.md). The workbench
manifest at `d31f16fb…` contains saved packages from the additive source at
`7eeded763…`; neither link admits that source to the remote service.

## Open the interactive page

[Open the reviewed workbench](https://chris-page-gov.github.io/okf-explorer/evidence/?manifest=https%3A%2F%2Fraw.githubusercontent.com%2Fchris-page-gov%2Fokf-dwp%2Fd31f16fb7143d04b9de73e14cd493cfb832ae83e%2Fevaluation%2Fevidence-workbench%2Ftools-manifest.json&case=staff-016&tab=requirements).
The DWP documentation page is a guide; the interactive page runs in Explorer.
This link fixes the DWP evidence version. Explorer itself may later serve a
newer application, so repeat the interaction before a demonstration.

In the tested sidebar conversation, the following ordinary follow-up worked:

> Now open question staff-039, show its Interactions table on the webpage, and
> explain the first three entries with their limitations. Use only the
> workbench's returned evidence.

ChatGPT opened the Carer's Allowance question, displayed rows 1–3 of 4, and
explained those rows with the unreviewed status and unresolved conditions.
It called `okf_get_state`, `okf_get_view_data` and `okf_show_view`. The displayed
question and table were independently checked. The earlier turn displayed
staff-016 Requirements and explained three gaps.

Continue in the same sidebar conversation. A blank **New chat** does not
inherit its connection instructions. Use the conversation selector if the
sidebar looks empty after a successful run.

## Starting a fresh conversation

If the assistant reports `Capability is not available: webmcp`, it has checked
the dedicated interface only. In the tested Edge profile the available
developer connection (`cdp`) could still invoke the page's native registered
tools. That error alone does not establish that a browser setting needs to be
enabled. Reloading the page does not add a missing host capability, and a
prompt that says to stop at that check will still stop after a refresh.

The starter below includes the observed fallback. It must respect the actual
developer connection's permissions; it does not install or inject a substitute
tool registry. When that connection is unavailable or denied too, report that
specific blocker.

Use this starter when the existing connection supports developer access:

> Use this Evidence Workbench page's registered tools to show the Requirements
> view for staff-016 and explain the first three gaps. Use only returned
> evidence. Discover the supported page-tool interface first. In the tested
> Edge setup, restricted read-only inspection returned `undefined` for
> `document.modelContext`, although the interface existed in the native page
> context. If the dedicated WebMCP interface is absent and the existing
> developer connection is available and authorised, read the native registered
> schemas through that connection. The observed Edge calling convention is
> `document.modelContext.executeTool(theMatchingRegisteredTool, JSON.stringify(arguments))`,
> choosing the tool object from `getTools()`. Call `okf_get_state`,
> `okf_get_view_data` and `okf_show_view` with the returned snapshot, result and
> revision identities. Verify the displayed result. Do not change permissions,
> inject replacement tools, search the web or calculate an award. If access is
> blocked, report the blocker.

CDP means **Chrome DevTools Protocol**, a developer connection which can
inspect and operate a browser page. It is a broader interface than these seven
workbench operations. In the recorded run the user separately approved access
to the public page origin in the sidebar. No browser flag or extension setting
was changed by the coordinating task. This guide grants no new permission;
a fresh session may need its own user approval and must respect a denial.

## What the observation establishes

The Edge build reported `153.0.0.0`. Its connected client advertised `cdp` and
`pageAssets`, with no dedicated `webmcp` capability. Restricted read-only
inspection and native page inspection returned different availability results
in the same tab. Therefore, `undefined` in the restricted inspection alone is
not proof that registration is broken or that an Edge update disabled it.

The actual sidebar calls used the native registered tools, not a replacement
registry. The DWP manifest SHA-256 was
`294c665de0060769fe05c8e4774d864c540f9b24678791771ee9ed5054b3a65f`.
The retained Requirements and Interactions results were respectively
`v-438c1cc6-f6ed-4a58-bf44-cba2d6ef00e0` and
`v-4d2eaa3d-f849-4139-a77e-407d341fb769`. These are observation identifiers;
they expire and must not be reused as instructions for another session.

This demonstrates one host's evidence-read and page-presentation route. It
does not prove universal client support, a custom visualisation inside the
sidebar, complete legal evidence or correct award calculations. All 40 saved
packages remain **insufficient**. Interaction rows are unreviewed proposals;
partial tables and source references requiring further checks remain explicit.

## Fresh-session checks on 25 September

An initial attempt to repeat the journey in a fresh session did **not** reach
an accepted tool test. The native interface repeatedly appeared blank or
unavailable, and clipboard/window errors interrupted the browser interaction.
No demonstration prompt was sent and no model or page-tool call followed. The
user's existing sidebar draft was left untouched. This records the observed
limit only; it does not diagnose its cause.

A later fresh conversation succeeded after the interaction used field setting
instead of the failing clipboard path. The user asked, “Show staff-016
requirements gaps.” The sidebar displayed **5.6 Sol Medium**, found no
dedicated `webmcp` capability and, with the existing authorised CDP connection,
used native `document.modelContext.getTools()` and `executeTool()`. Initial
tool-descriptor serialisation attempts failed; the subsequent calls to
`okf_get_state`, `okf_get_view_data` and `okf_show_view` succeeded. The first
view-data response was bounded, so the sidebar repeated it with
`max_bytes: 32768`.

The view result `v-8a0d7bd9-e5c8-44d0-9c4d-8d2002d3b43a` was shown with
`expected_revision: 2`; the returned page revision was 3. The DWP manifest
snapshot was `sha256:294c665de0060769fe05c8e4774d864c540f9b24678791771ee9ed5054b3a65f`.
Independent page inspection saw the URL move from **Calculation stages** to
**Requirements** and rows 1–3 of six. The sidebar explained gaps associated
with staff-010, staff-015 and staff-016, kept the package `insufficient`, said
the response supplied no source references and calculated no award. The result
ID and revision are session-local, not reusable inputs. The public observation
omits the private conversation identifier.

The owner later reported a separate successful reproduction using the same
fallback, after their first prompt had stopped at the missing `webmcp`
capability. That [user-reported observation](https://github.com/chris-page-gov/okf-dwp/blob/main/validation/client-connection/2026-09-25/sidebar/user-reproduction.json)
retains its own result identifier and partial-response limits; it is separate
from the independently inspected observation above.

This is one independently inspected fresh-session, developer-assisted page-tool journey,
not an answer-quality trial. It supports scoped repeatability of the 24
September route. Automatic discovery through a dedicated WebMCP connection,
universal host support, Voice and room audio remain unverified. No new
permissions or browser settings were introduced; the user's other sidebar
draft was untouched.
