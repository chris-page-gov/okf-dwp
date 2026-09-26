# Access routes to test

Documentation checked 25 September 2026. These are setup examples, not proof that each host has successfully invoked this service. Retain normal confirmation and tenant approval controls; do not enable blanket trust to make a test pass.

The existing remote endpoint is:

```text
https://ask-okf.crpage.chatgpt.site/okf/mcp
```

## Codex
The official documentation supports remote MCP and CLI configuration. [OPENAI-CODEX]

```sh
codex mcp add ask-okf --url https://ask-okf.crpage.chatgpt.site/okf/mcp
codex mcp list
```

A configuration fragment is in `client-config/codex.toml`. Merge it into the applicable existing configuration; do not overwrite the entire file.

## Claude
Use the account's custom remote connector route and the endpoint above. Team/Enterprise installation may require the organisation owner. Remote connector traffic originates from Anthropic infrastructure, not necessarily from the device running Claude. [CLAUDE-MCP]

Adding a connector does not prove that the current chat has its tools enabled. Check discovery, call the manifest, then perform an exact record read and a continuation before marking the client verified.

## Gemini CLI
The documented Streamable HTTP route can be configured as follows. This does not establish support in the Gemini consumer app or a Chrome side panel. [GEMINI-MCP]

```sh
gemini mcp add --scope user --transport http ask-okf https://ask-okf.crpage.chatgpt.site/okf/mcp
gemini mcp list
```

A merge-only settings fragment is in `client-config/gemini.json`; it leaves tool confirmations enabled.

## Microsoft 365 Copilot
Use an MCP-backed declarative agent or a configured Copilot Studio agent. Current Microsoft documentation describes these routes, including publishing, authentication and administrative prerequisites. Adding a URL to an ordinary chat is not the same operation. [M365-MCP; STUDIO-MCP]

The existing Explorer project also reports a SharePoint Word-derivative retrieval trial. It concerns configured service-family retrieval, not this DLA question, arbitrary JSON upload, full graph traversal or a general permission-boundary guarantee. Treat a Word projection as an additional indexed condition with source IDs, exact locators, dates, limitations and a canonical evidence link retained. [REPO-M365]

## Browser page tools and side panels
OpenAI documents Site tools in the ChatGPT desktop app's built-in browser, subject to account/model access and website support. That documentation does not establish automatic support in Chrome or Edge extensions. [OPENAI-SITE]

DWP's sidebar guide records an Edge ChatGPT route using an already-authorised developer connection to the page's native registered tools on 24 and 25 September. Dedicated automatic WebMCP discovery remained unverified. Do not install broader developer permissions or inject a replacement registry merely to claim compatibility. This is an attributed existing observation; it was not rerun here. [REPO-SIDEBAR]

For a saved Workbench case, establish state, search the admitted catalogue/case, read source and provenance, follow relevant relationships, and show the returned view with a fresh revision. The documented search is not whole-corpus search. For a new question, use the Reader's appropriate assembly route or remote MCP. [REPO-PAGE]

## Universal fallback and future UI
Provide a small source-bound Markdown/text/HTML evidence rendering, with canonical package identity, exact citations, gaps and a link back to inspection. Supply files only in formats the particular host accepts. Verify actual received content rather than assuming a model follows every URL. A Word derivative can support the separate M365 condition.

The design target is one source/evidence contract and multiple tested adapters, not a separate knowledge interpretation per vendor. Tool transport, access to the currently selected browser tab, display changes, visual widgets and model answer quality require separate acceptance tests. A remote MCP call does not by itself control the user's open Workbench tab.

References resolve in `sources.json`.
