---
name: rao-workflow
description: Stand up a Progress Agentic RAG "RAO" (Retrieval Agent Orchestrator) over any app's live data via MCP - ARAG's own Retrieval Agent plans, calls the app's MCP tools (carrying the user's JWT for RBAC), grounds and answers, with a streaming "watch it work" UI and honest guardrails. Use when a demo or product needs ARAG to BE the agent rather than the app orchestrating MCP itself. Self-contained: every step, endpoint, code pattern and hard-won trap is inline - works in any environment against any app that has (or can add) a REST API.
---

# RAO workflow - ARAG Retrieval Agent over an app's MCP

Build the pattern where **Progress Agentic RAG's own Retrieval Agent** plans a question, calls
the app's **`/mcp`** server as its tool source (ARAG is the MCP client, forwarding the user's
JWT so the app's RBAC applies), grounds in a Knowledge Box, and answers - while the app
**exposes** MCP and streams the agent's live trace to a "watch it work" UI.

The app must NOT run its own planner that calls `/mcp` directly, and must NOT do deterministic
DB lookups + a raw-LLM narration (the "hybrid" pattern this replaces). ARAG is the agent.

This skill is self-contained - it works against any app with a REST API, in any environment.
It was proven end-to-end on 2026-07-21; the traps below each cost hours to find, so read them
before touching the dashboard.

## What RAO runs on (confirmed by Jay, 5 Aug 2026)

RAO is Progress's product name for a retrieval agent built on **Nuclia's own open-source
`hyperforge` framework** (`github.com/nuclia/hyperforge`, "Progress Data Platform Agentic
Framework"), deployed on Progress's own cloud. This isn't circumstantial anymore - Jay
confirmed it directly. Knowing this explains several of the traps below rather than them just
being empirically-discovered quirks to memorise blind:
- The `__<uuid>` tool-name suffix trap two lines down is a **literal Hyperforge internal
  constant** (`hyperforge_smart/agent.py`'s `TOOL_NAME_SEPARATOR = "__"`), not an ARAG-specific
  design choice - expect the same convention on anything else built on this engine.
- `hyperforge_mcp` is Hyperforge's own MCP-client agent package - it's the literal mechanism
  behind "ARAG calls the app's `/mcp` as its tool source."
- `hyperforge_remi` implements REMi scoring (Answer Relevance / Context Relevance /
  Groundedness) verbatim - the same feature this factory cites throughout decks and demos.
- `hyperforge_smart` is a planner+executor (plan/execute + reactive prompt templates) - the
  actual implementation behind the dashboard's "Smart Agent" node.
If a future RAO build hits an unexplained quirk, checking the relevant `hyperforge_*` agent
package source is a legitimate way to understand *why*, not just work around it - this is
Nuclia's own public repo, not proprietary internals off-limits to read.

## The 3 ideas (design + the pitch)
1. **API-first single source of truth** - one REST API; the web UI, the AI, and MCP all go through it, nothing bypasses to the DB.
2. **MCP makes the app agent-addressable with the UI's guarantees** - each MCP tool call dispatches back through the REST handlers, so auth/RBAC/validation are automatic; ARAG calls `/mcp` carrying the user's JWT.
3. **Grounded, streamed, honest** - the agent answers only from what it retrieved, streams every step, and refuses to state anything it didn't verify.

## READ FIRST - the traps (each cost hours)
- **RESOLVED (3 Aug 2026 - the whole "dashboard-only node graph" framing below was wrong. A PAT
  drives the ENTIRE agent/workflow build via plain REST, no dashboard, no browser automation, no
  human login beyond the one-time PAT mint already documented in Build step 2.** Confirmed live
  against Revolution DMS's real agent, using `Authorization: Bearer <PAT>` (not the NUA-key
  header) on the dp-host agent API:
  - `POST /agent/{agent_id}/preprocess` `{"module":"rephrase"}` -> creates a real Rephrase node.
  - `POST /agent/{agent_id}/generation` `{"module":"summarize"}` -> creates a real Summarize node.
  - **`POST /agent/{agent_id}/context`** - this is the "Retrieval Context" stage's endpoint,
    and it is **not documented anywhere in the 910-page reference guide's Appendix B** (a real
    gap in Progress's own docs, not a research miss - grepped the whole guide, confirmed absent).
    Accepts `{"module":"ask"|"perplexity"|"pandas"|"mcp"|"smart", ...}`. An `mcp`-module context
    agent needs `"source"` = the driver's `identifier` (from `GET /agent/{id}/drivers`); the
    already-existing "Smart Agent" node (created by an earlier dashboard session) shows up here
    too as `module:"smart"` with a `registered_agents` array (empty) - this is the exact field
    the dashboard's "Registered Agents" port writes.
- **RESOLVED (3 Aug 2026, corrected same day) - the `registered_agents` 500 was NEVER a platform
  bug. It was a malformed request shape on our end, and a missing node.** Two real, fixable
  causes, found by reading a genuinely WORKING agent's live config (Plant-demo ERP,
  `reference-repos/plant-demo-erp`) via `GET /agent/{agent_id}/context` and diffing it against what
  we'd been sending:
  1. **`registered_agents` must be an array of the FULL NESTED context-agent OBJECT, not an array
     of bare id strings.** `["<mcp_id>"]` crashes the backend with a bare `Internal Server Error`
     (no JSON detail - an unhandled exception, not a validation error) - reproduced twice this
     way before the fix was found. The working shape: `GET` the MCP context node first, then
     PATCH the Smart Agent with `registered_agents: [<that full object, verbatim>]` and
     `registered_agents_exposed_functions: {"<mcp_id>": []}` (a dict, not `null`). Confirmed live:
     this PATCH returns `null` (success) instead of 500, and `registered_agents` genuinely
     persists on a follow-up `GET`.
  2. **You also need a `generation` node with `module:"summarize"` and a real `system_prompt`.**
     Without it, the Smart Agent's tool calls succeed and gather real context (visible as
     `tool_call`/`tool_result` events and a populated `sources` list) but there is nothing to
     compose the final prose - the `answer` event's `text` comes back as an empty string despite
     real grounded data underneath. Easy to miss because everything else *looks* like it worked.
  Verified end-to-end on Revolution DMS after both fixes: a real multi-tool agent trace
  (`list_vehicles_due_for_recon` -> `check_parts_inventory` -> ...) followed by a real cited
  answer with bracketed source references. **Do not escalate this to Progress/Nuclia support -
  it was always a client-side request-shape issue, not their bug.** The one MARTY VDR hit via
  the dashboard (`MCPHTTPDriver.client() missing 4 required positional arguments`) may be the
  same root cause manifesting differently through the UI, or a separate issue - re-test via the
  API with the corrected shape above before assuming it's still broken.
  - So: the entire pipeline - drivers, preprocess, retrieval context (including Smart Agent +
    MCP), generation, postprocess, rules - is 100% API-settable with a PAT, and now fully working
    end to end. **If someone reports managing RAO agents without touching the dashboard, they are
    right and this is how.**
- **The agent config surface is NOT credential-type gated the way the note below (now superseded)
  claimed** - a PAT reaches every endpoint above with plain `Authorization: Bearer`. The one
  human login is still required once, to mint that PAT (see Build step 2) - that has not changed.
- **The agent lives on the data-platform host, not the KB host.** Config + interaction are at `https://<zone>.dp.progress.cloud/api/v1/agent/{agentId}/...` (e.g. `<zone>.dp.progress.cloud`), **not** `rag.progress.cloud` and **not** a `/kb/{kb}/agent/*` path (that 404s). Derive the dp host from the rag host: replace `.rag.progress.cloud` -> `.dp.progress.cloud`.
- **The agent is created as a `mode:"agent"` Knowledge Box**; its `id` IS the agent id used in the ephemeral URL. Agents don't appear in the ordinary `/account/{acc}/kbs` list - find them in the dashboard's **Retrieval agents** page.
- **CORRECTED (3 Aug 2026 - see the "RESOLVED" note above): the node graph is NOT dashboard-only,
  and nothing about it is a platform bug.** Every node type (preprocess, context including Smart
  Agent, generation, postprocess, drivers) is fully API-settable with a PAT via
  `POST/PATCH /agent/{agent_id}/{preprocess|context|generation|postprocess}`, including the
  Smart-Agent-registers-MCP-node step - the fix is sending `registered_agents` as full nested
  objects (see above), not switching interfaces. Build the whole graph via the API; it's faster
  and scriptable, and the dashboard offers no advantage.
- **MCP works fine as a direct retrieval-context "mcp" module OR wrapped under a Smart Agent -
  the "direct module crashes" claim below was never isolated from the registered_agents shape
  bug and should be re-tested with the corrected shape before trusting it.** If you still see
  `MCPHTTPDriver.client() missing 4 required positional arguments` after using the full-object
  `registered_agents` shape, that's a genuine new data point - update this note either way.
- **A registered node silently won't save if a required field is empty** - notably the **Description**. If a node vanishes after refreshing the editor, a required field (Description, HTTP transport, Source) was blank. The Save button only enables when all are valid.
- **UNRESOLVED, CONTRADICTORY RESULTS (1 Aug 2026) - do NOT treat this as a settled platform
  bug yet.** Two builds applied the identical `li.pa-option`-ancestor-click + disabled-attribute
  JS-verification fix (see the theory above) with opposite outcomes:
  - **MARTY VDR build:** Source selected via a direct `li.pa-option` ancestor `.click()`, Save's
    `disabled` attribute verified `false` via JS twice, a real trusted `computer`-tool click
    landed on Save (confirmed genuine by the page's own GA4 beacon,
    `ep.click_text=Save`/`ep.click_classes=pa-button-label`). Network log cleared immediately
    before the click showed **zero requests** afterward, and a full reload showed the graph
    back to the bare `PREPROCESS -> RETRIEVAL CONTEXT -> GENERATION -> POSTPROCESS` skeleton -
    nothing persisted.
  - **Operator Fleet build, same day, same fix:** node graph (Retrieval Context -> Smart Agent
    -> registered MCP node -> Summarize) reported as persisted across a page reload, AND a live
    "Test agent" run produced a real trace showing ARAG's Smart Agent actually invoking the
    app's `/mcp` tool through that exact node - which is only possible if the save genuinely
    took. This is stronger evidence than a reload check alone.
  These cannot both be a clean "the save handler never fires, full stop" - something differs
  between the two runs (timing, exact agent/KB state, order of operations, browser/session
  specifics, or the bug is genuinely intermittent). **Until this is reconciled, don't copy
  either build's conclusion wholesale** - if you hit the zero-persistence symptom, apply the
  `li.pa-option`/disabled-attribute fix, retry at least twice, and check whether a live "Test
  agent" run (not just a reload) confirms or refutes persistence before deciding it's dead. If
  it's still failing after that, ship with RAO disclosed as a known gap (see MARTY VDR's DAM
  submission, 1 Aug 2026) rather than burning further turns - but report back here with your
  result either way so this note can be corrected to something we actually trust.
  **Update (2 Aug 2026): MARTY VDR retested clean on a completely fresh login/session and
  still fails the same way**, this time with the double-reload check above (ruling out the
  false-positive-soft-nav trap) - so this isn't stale-session residue or a one-off, it
  reproduces for this specific agent across multiple fresh sessions. Meanwhile a third build
  (Revolution DMS / Ignition, same day) is attempting the same node graph fresh - if it also
  persists cleanly like Operator Fleet did, that would point at something specific to the
  MARTY VDR agent/KB rather than a general platform issue; if it fails like MARTY VDR, that
  strengthens the platform-bug read. Update this note with whichever way that lands.
  **Export/Import is not a workaround** (checked 1 Aug 2026) - Export requires a 16+ char
  password and produces an encrypted file, so hand-editing the exported JSON to inject the
  missing node isn't feasible. Export's own API call *does* succeed (real `POST
  .../agent/{id}/export` -> 200) though, which narrows the bug: normal persist operations on
  the agent work fine, it's specifically the Smart-Agent-registered-agent save handler that's
  dead - useful framing for the platform-team report, not a path to route around it.
  **Update (2 Aug 2026) - Revolution DMS / Ignition build result: persists cleanly, like
  Operator Fleet.** Added the Smart Agent node under Retrieval Context, saved with a real
  trusted `computer`-tool click (Save's `disabled` verified `false` via JS first), reloaded
  the whole page, and the node graph came back with the Smart Agent's ports (Fallback
  agent/Next agent/Registered agents) intact - genuine persistence, not a stale-DOM false
  positive. This is the third data point and it lines up with Operator Fleet, not MARTY
  VDR - strengthens the read that the save-persistence bug is specific to the MARTY VDR
  agent/KB (or that specific session/account state) rather than a general platform issue.
  **New, separate symptom found on this same build: the MCP Agent node's Source field
  (a `pa-select` listbox) sometimes returns ZERO options even though the MCP source
  genuinely exists** (confirmed via the standalone Sources page - `ignition-dms-mcp`,
  provider `mcphttp`, listed and correct). Reproduced twice in a row on two freshly-added
  MCP Agent nodes in the same session; typing into the field to trigger a filter/search
  did nothing (it isn't a text-filterable combobox). Earlier in the same session the
  identical field, on an earlier MCP Agent node instance, DID show `ignition-dms-mcp` as a
  real listbox option and let it be selected - so the source list can hydrate correctly,
  it just doesn't reliably do so on every node instance. Not yet root-caused (no fix
  found this session); if you hit it, the workaround that worked once was simply
  clicking the Source field again after a beat - but this was not reliably reproducible
  on retry, so don't assume it always resolves on a second click. Log whether you see it
  again and whether any specific action (reload vs. re-add node vs. wait longer)
  reliably clears it, so this note can gain a real fix.
  **Update (2 Aug 2026) - ruled out session/DOM staleness as the cause.** Closed the tab
  entirely, opened a brand-new tab, navigated fresh via a full URL load (not an in-app
  nav) straight to the workflow page, added a new MCP Agent node, and opened its Source
  field: identical empty result (only the untranslated `no-source` placeholder, zero real
  options). Since a genuinely fresh tab/session reproduces it exactly, this is NOT the
  "dead session looks alive" pattern documented elsewhere in this skill - it's either a
  real intermittent platform bug in how this dropdown's option list loads, or something
  scoped to this specific agent/workflow's saved state (worth testing against a
  brand-new agent next time, not just a fresh tab, to narrow further). Ignition/Revolution
  DMS shipped with RAO wiring incomplete as a result - Smart Agent node persists, MCP
  Agent node does not have a working Source selection. Everything else (KB, RBAC, deploy)
  verified working.
- **ARAG namespaces tool names** with a trailing `__<agent-uuid>`, e.g. `customers_list_customers__2f527fa6-4f88-4260-bd2f-865701d23619`. Your `/mcp` server MUST strip the `__<uuid>` suffix before matching, or every tool call 404s "Unknown tool".
- **JWT doesn't forward to tool calls unless you list it.** Add `authorization` to the MCP node's **"Valid headers to forward to the agent"** field, then have the app forward the user's bearer in the ephemeral request's `headers.authorization`. Without it every tool call 401s.
- **The default workflow is named "Do NOT use"** - build/populate a real one.
- **PAT auth header: `Authorization: Bearer <PAT>`, never `X-NUCLIA-SERVICEACCOUNT`.** A PAT is
  an ACCOUNT-level credential like the NUA key, not a KB-scoped service-account token; the
  agent-config surface rejects it under `X-NUCLIA-SERVICEACCOUNT` with "wrong header key".
  Verified live: only `Authorization: Bearer` works on the dp-host agent-config endpoints.
- **Never click unrecognised dashboard chrome near account/session controls** (an icon that
  looks like a sidebar-collapse toggle, etc). One stray click triggered an account-wide logout
  + PAT revocation across every open tab on the account, mid-build, for two parallel sessions
  at once. If unsure what an icon does, don't click it - navigate by known menu items only.
- **Suspected short access-token lifetime with no silent refresh (1 Aug 2026, unconfirmed but
  a strong lead).** At least 3 account-wide logouts in one session weren't all explained by a
  stray click - `JWT_KEY`/`JWT_ID_TOKEN_KEY` in localStorage were observed with `exp` only
  ~90 seconds out from check-time shortly before one such logout, and all open tabs on the
  account dropped to `auth.progress.cloud` login pages within ~10-15s of each other. A
  multi-step node-graph edit (add 2 nodes, fill 4+ fields, open dropdowns) can easily exceed a
  90s window. **This is a plausible root cause for the "Save fires zero network requests"
  bug above**: if the frontend does a client-side token-expiry pre-check before attempting the
  persist call, an expired token would produce exactly zero requests (not a request-then-401,
  which would show in the network log) with no visible error - matching what's been observed.
  If you're mid-edit on a long form, consider checking `JWT_KEY`'s `exp` via
  `javascript_tool` periodically and finishing fast, or re-triggering auth just before Save if
  it's stale. Not yet confirmed as the actual mechanism - update this note if it is (or isn't).
- **A dead session can look alive until something forces a real auth check.** The dashboard's
  Angular app keeps running on stale in-memory state after the underlying session dies - a tab
  can screenshot as fully authenticated and interactive (forms fillable, node editor open) with
  zero visual sign anything's wrong, right up until a real network call or hard navigation hits
  the dead session and it redirects to login. This produced a real false negative: a "Save"
  button that stayed permanently disabled looked like a form-validation bug for a while, but was
  actually a dead session underneath a stale-but-responsive UI. If a save/action mysteriously
  won't complete, don't assume it's a UI bug - reload the tab (or make a real API call) to force
  an honest auth check before spending more time on it.
- **A "reload" can be a false positive too - an in-app Angular soft-navigation isn't a real
  refetch.** Confirmed 2 Aug 2026: after a Save that (per the network-log check) never
  persisted, the FIRST reload still showed the node on canvas - looked like a genuine save.
  A SECOND reload (which showed a real loading spinner, unlike the first) came back to the
  bare skeleton with the node gone. The first "reload" was almost certainly an in-app
  soft-nav that just re-rendered stale in-memory component state rather than hitting the
  server fresh. **Don't trust a single reload as proof of persistence** - do it twice, and
  treat the presence of a genuine loading indicator (not just new content) as the signal
  that a real refetch actually happened. This is the same failure class as the dead-session
  false negative above, just producing the opposite (false positive) result - both come from
  this dashboard's willingness to show you stale state instead of an honest one.
- **The MCP node panel's field schema is not stable - re-check it each session, don't assume
  it matches an earlier description in this skill.** Observed 2 Aug 2026: a rebuild found NO
  "Description" field at all (fields were Transport/Source/Tool-choice-model/Read-timeout),
  contradicting the "Description is required" trap documented earlier the same day. Read
  the actual live form each time rather than filling fields from memory of a prior build.
- **Extracting a freshly-minted NUA key/PAT value via browser automation: the read-back
  channels (`get_page_text`, DOM `.value` reads, `javascript_exec` returning the string) can
  come back redacted as `[BLOCKED: JWT token]` - a safety filter on JWT-shaped strings, not a
  bug. It also doesn't live in a plain `<input>` you can `querySelectorAll` for (component
  libraries like Pastanaga render it behind a closed shadow root). Working pattern: click the
  page's own **Copy** button (a real trusted click, so the Clipboard API write succeeds
  silently, no permission prompt) - then, if the browser session is on the same machine as your
  shell, read it straight from the OS clipboard via `pbpaste` (Bash) rather than back through
  any browser-tool channel. Never print the value into your own chat output; write it directly
  into `.env` from the shell (e.g. Python reading `subprocess.run(['pbpaste'])` and rewriting
  the file in place) and then clear the clipboard (`printf '' | pbcopy`).
  **`pbpaste` only works when a real UI Copy button exists to click** (the NUA key page has
  one) - clicking it is genuine trusted user activation, so the page's own
  `clipboard.writeText()` succeeds. A PAT has no such UI in this dashboard; it's minted via
  your own injected `fetch` to `POST /api/v1/user/pa_tokens`, which is not a trusted user
  gesture, so any `clipboard.writeText()` you then call yourself hangs/times out waiting for a
  permission grant that never comes.
  **CORRECTED (2 Aug 2026 - the file-download advice below this used to carry was wrong,
  don't follow it): a triggered file download (Blob + programmatic anchor click) is NOT a
  reliable fallback in this automation context.** Verified directly, repeatedly: a download
  triggered by script (even with a real dispatched `MouseEvent`, even for a harmless
  non-secret test file) reports success but the file never lands on disk - checked directly
  in the actual Downloads folder each time, confirmed absent. `window.open()` on a blob URL
  from a script has the same failure mode - no new tab appears at all, silently swallowed
  (both are almost certainly blocked by the same missing-trusted-gesture issue as
  `clipboard.writeText()`, just failing differently: downloads report false success,
  `window.open` no-ops, `clipboard.writeText()` hangs).
  **Working pattern, proven end-to-end for both a NUA key and a PAT: inject a visible
  on-page button via JS whose `onclick` calls `navigator.clipboard.writeText(<value>)`
  directly, then click it with a REAL `computer`-tool click (not `javascript_tool`'s
  `.click()`, not a dispatched `MouseEvent`).** A `computer`-tool click is a genuine
  OS-level/CDP-dispatched input event and counts as trusted user activation even on an
  injected element - this is the same class of trust as the GA4 click-beacon confirming a
  real Save click elsewhere in this skill. `clipboard.writeText()` then resolves immediately
  instead of hanging. **Test the mechanism first with a harmless dummy string** (click the
  injected button, have the operator `pbpaste` and confirm the dummy string, before spending
  a real mint on it) - cheap to verify, expensive to guess wrong on a real credential.
  Have the account owner (or, for this exact clipboard-to-file handoff, a script run by
  whoever holds the shell on the same machine) read it via `pbpaste` and write it straight
  into `.env` - never printed to any tool output, never routed through the browser's own
  read-back channels, then clear the clipboard (`printf '' | pbcopy`). Do NOT try to read
  the Downloads folder yourself looking for a file that may never arrive (correctly
  blocked as out-of-scope file access, and now also known to be unreliable even when
  permitted).
  **Revoking a PAT: `DELETE https://nuclia.cloud/api/v1/user/pa_token/{id}` - singular
  `pa_token`, NOT the plural `pa_tokens` used for list (`GET .../pa_tokens`) and create
  (`POST .../pa_tokens`).** Guessing plural on delete 404s. Clean up orphaned PATs minted
  during a credential churn like the above once the working one is confirmed deployed -
  re-list afterward to confirm only the intended one remains.
  **Never write a secret into `document.title` as a way to read it back through tab-list
  tooling.** It's a tempting way around the JS-return-value redaction, but tab titles are
  NOT redacted, are visible on-screen in the browser's own tab strip, and get echoed in
  plaintext by any tool that lists open tabs - a strictly more exposed channel than the ones
  being worked around (a real incident, 1 Aug 2026: a PAT sat visible in a tab title for
  multiple turns before another agent caught it). `pbpaste` after a trusted Copy click is the
  only sanctioned extraction path - use it, don't invent a new one.
- **An uncurated large tool catalogue makes the planner slow and mis-plan** (e.g. calling get-by-id tools without an id). Curate the MCP node's exposed **Functions** to a focused set (list/query/trace/composite tools; drop get-by-id tools needing ids the planner lacks). Cuts latency too.
- **The PAT login is account-wide; the dashboard node-graph editor is not multi-agent-safe.** One human login mints a PAT reusable across every app/KB in that account - don't re-ask for a login if a PAT already exists this session. But if two builds are happening in parallel, **each agent must use its own browser tab**, never share one: the node editor silently drops a node on a blank required field, and one agent navigating a shared tab mid-edit can pull it out from under another agent working the same tab. Check for an idle vs. active tab before touching a shared one (a KB/agent picker screen is safe; a node-graph or workflow-config URL means someone else is mid-flow - back off and open a fresh tab instead).
- **The dashboard renders at 2x DPI - pixel-coordinate clicks land on the wrong element.**
  `window.innerWidth` is genuinely ~485px while screenshots render at ~1017px. A coordinate
  click computed from a screenshot is off by ~2x and silently hits a neighbouring or stale
  element - this is what actually causes "Add node doesn't auto-connect" and "error occurred
  while saving the node" symptoms, not a real connection/save bug (cost most of a session to
  find, 1 Aug 2026). **Never click node-editor elements by screenshot coordinate.** Use
  `read_page` (filter `interactive` or `all`) to get element refs, then click by `ref`, or use
  a natural-language element-find tool that returns refs directly. Refs target the real DOM
  node regardless of the rendering scale.
- **Creating an MCP source mid-node-config loses your in-progress node.** The MCP Agent node's
  "Create an MCP source" button navigates away to a `/sources` page and does not preserve the
  node config panel you were filling in. Do it in two passes in one continuous session: first
  create the source stand-alone (Sources -> Add source -> MCP HTTP Driver -> Name/Provider/
  Uri = your app's public `https://<slug>.fly.dev/mcp`/Timeout -> Create), **then** go back to
  the node editor and add the MCP Agent node fresh, selecting the now-existing source from the
  dropdown - don't try to create the source from inside an unsaved node.

## Build steps

### 1. App side - expose `POST /mcp` (do this first; ARAG calls the PUBLIC url)
- Auto-generate the MCP tool catalogue from the app's own OpenAPI doc (deterministic tool names). Each `tools/call` dispatches back through the REST handlers in-process (e.g. an in-process transport) so auth/RBAC/validation apply uniformly. Pass the caller's bearer through - an unauthenticated tool call on a protected endpoint must return the API's own 401.
- **Strip the agent-uuid suffix before lookup.** Minimal pattern (Python; port as needed):
  ```python
  import re
  _UUID_SUFFIX = re.compile(r"__[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
  def strip_agent_suffix(name: str) -> str:
      return _UUID_SUFFIX.sub("", name)
  # look up strip_agent_suffix(name) in your catalogue, not name
  ```
- Endpoint: `POST /mcp`, JSON-RPC 2.0, Streamable HTTP, stateless. Public (no static auth) is fine for a demo - the per-request forwarded JWT carries RBAC.
- Deploy it to a PUBLIC url. ARAG reaches `https://<app-host>/mcp`; localhost won't work for the live agent.

### 2. One human login -> a PAT (the only manual step, one-time)
- Have the account owner sign in to the ARAG dashboard once (`https://nuclia.cloud`). Capture the authenticated session (any headed-browser login-capture works - e.g. a small Playwright script that opens a headed window, waits for the dashboard to load, and saves the storage state).
- Mint a Personal Access Token from that session: `POST https://nuclia.cloud/api/v1/user/pa_tokens` (default ~1-year). Store it **server-side only** as the agent key. After this, everything is API/dashboard-driven - no more logins.

### 3. Create + configure the agent, and set the app's env
- Create the agent (a `mode:"agent"` KB) via the account's KB-create API in the right zone; its `id` is the agent id.
- The app needs, server-side only (Fly/hosting secrets, never client-side):
  - `ARAG_AGENT_KEY` = the PAT
  - `ARAG_AGENT_BASE_URL` = the **dp** host (e.g. `https://<zone>.dp.progress.cloud`)
  - `ARAG_AGENT_KB_ID` = the agent id
  - `ARAG_AGENT_TIMEOUT_S` = a live budget (55 is good)
  (If deployed and these secrets are missing, the app silently falls back to cached - set them.)

### 4. Build the workflow via the API (PAT, `Authorization: Bearer` - no dashboard needed)
All calls below are `POST`/`PATCH` on `https://<dp-host>/api/v1/agent/{agent_id}/...` with
`Authorization: Bearer <PAT>`. Find your MCP driver's `identifier` first via
`GET /agent/{agent_id}/drivers` (create one via `POST .../drivers` if it doesn't exist yet -
`provider` is `mcphttp`, `config.uri` = your app's public `/mcp`).
**Two driver shapes to know, both measured 21 Oct 2026 and neither documented.** `POST
.../drivers` REQUIRES a top-level `identifier` - omitting it returns a 422 naming the field,
which is at least an honest error. And `GET .../drivers` returns each driver WRAPPED as
`{"config": {identifier, name, provider, config}}`, so the driver's own fields are one level
deeper than the list implies and a `d["identifier"]` read returns nothing with no error.
Unwrap the envelope before matching on a name.
1. **MCP context node**: `POST /agent/{agent_id}/context` with
   `{"module":"mcp","source":"<driver identifier>"}` -> returns an id. Then `PATCH
   /agent/{agent_id}/context/{that_id}` with the full object (GET the node back first to see
   every field) setting `"transport":"HTTP"` (the default is `"SSE"` and does NOT match a
   Streamable-HTTP `/mcp` endpoint), `"valid_headers":["authorization"]`, and
   `"published_functions"` to the real tool names from your app's own `tools/list` response.
2. **Smart Agent node**: check `GET /agent/{agent_id}/context` for an existing `module:"smart"`
   entry (a prior dashboard session may have already created one - reuse its id) or create one
   via `POST .../context` with `{"module":"smart","planning_mode":"reactive","max_iterations":5}`.
3. **Register the MCP node under the Smart Agent** - `PATCH /agent/{agent_id}/context/{smart_id}`
   with the full Smart Agent object, `registered_agents` set to **`[<the full MCP context
   node object, verbatim, as GET returned it>]`**, `registered_agents_descriptions` set to
   `{<mcp node id>: "queries the live <domain> data: <entities>"}`, and
   `registered_agents_exposed_functions` set to `{<mcp node id>: []}` (a dict, never null).
   **NOT BROKEN. Measured clean 21 Oct 2026 (Forge-co), first attempt, no retry.** This
   step used to say `registered_agents` takes `[<mcp node id>]` - an array of bare id
   STRINGS - and then warned that the call was KNOWN BROKEN and 500s server-side. Both
   halves were wrong, and they were wrong together: **the bare-id shape IS the 500.** The
   trap note near the top of this skill had already recorded the correction on 3 Aug 2026
   and this build step was never updated to match, so a reader following the steps in order
   hit the crash and then read a note telling them it was a platform bug with no workaround.
   At least three builds (Revolution DMS, MARTY VDR, and the ones that copied them) shipped
   with RAO disclosed to the DAM as a platform gap that did not exist.
   Two lessons worth more than the fix. **A correction is not encoded until the superseded
   text is removed from every home** - leaving the old shape in the procedure while fixing
   the prose above it is how a corrected fact keeps costing. And **"known broken" is the most
   expensive sentence you can write in a skill**, because it stops the next reader
   investigating: the honest form names what was tried, on what date, with what shape, so a
   later reader can tell "we proved the platform is broken" from "we sent the wrong body".
   If you do hit a 500 here, check the shape first: bare strings crash with a bare
   `Internal Server Error` and no JSON detail, which reads like a platform fault and is not one.
4. **Generation -> Summarize node**: `POST /agent/{agent_id}/generation` with
   `{"module":"summarize"}`, then `PATCH` in a grounding prompt: "Answer using ONLY the
   retrieved data; cite identifiers; if lookups failed or returned nothing, say you could not
   determine it - never assert a status you did not verify."
5. **Global rules**: `POST /agent/{agent_id}/rules` to reinforce grounding/refusal.
6. Confirm via `GET /agent/{agent_id}/context` (and `/generation`, `/preprocess`) that
   everything you created is actually there - these calls are cheap and instant, unlike
   waiting on a dashboard reload to (maybe honestly) reflect state.

**Dashboard fallback** (only if you genuinely need it - the API above covers everything except
the one broken write): Dashboard -> **Retrieval agents** -> your agent -> **Agent workflows**
-> open a workflow (create one if only "Do NOT use" exists) -> **Add node** on Retrieval
Context for Smart Agent, its **Registered Agents** port -> "+" -> **MCP Agent**, same broken
`registered_agents` write, same 500 either way.

### 5. App side - streaming proxy + honest gate + "watch it work" UI
- Proxy: `POST <dp-host>/api/v1/agent/{agentId}/session/ephemeral`, forwarding the user's JWT in the request body's `headers.authorization`. Stream ARAG's NDJSON straight through to the browser (SSE / chunked), event by event - never buffer to the end. Emit a heartbeat when ARAG goes quiet so the UI never looks dead.
- **Event mapping**: ARAG's raw trace -> `plan | tool_call | tool_result | doc_search | composing | answer | error`. Humanise tool names to friendly verbs EVERYWHERE (including the grounding footer). Suppress "No tool used"/empty-arg sentinels. Gotchas: tools sometimes announce as "Used tool: X with arguments Y" inline (no preceding plan line); the agent may fetch a curated prompt instead of a tool.
- **CRITICAL (3 Aug 2026): the raw NDJSON's real fields live nested under `step: {module, title,
  value, reason, error, agent_path}`, NOT flat top-level fields like `raw.type`/`raw.tool`/
  `raw.result`.** A proxy that checks flat fields will silently see nothing on every event,
  count zero substantive tool successes regardless of what actually happened server-side, and
  emit a false `no_grounded_data` refusal EVERY time - even when the live agent is working
  perfectly and a raw call to ARAG succeeds. This produced a real, hard-to-spot bug: the app
  looked broken (honest refusal on every question) while the underlying agent was actually
  fine. Parse `step.module` (`"smart"` for the orchestrator's own steps, `"mcp"` for the
  registered MCP node's own duplicate trace of the same calls - filter to just `module:"smart"`
  steps to avoid double-counting/double-rendering), `step.title` (e.g. "Smart agent: Execution
  iteration N/5", "MCP: Tool error"), `step.value` and `step.error` for the actual content.
  Verify by testing against the RAW `/session/ephemeral` endpoint directly (bypass your own
  proxy) before assuming a `no_grounded_data` result means the agent itself is broken.
- **Before declaring an agent broken, confirm the deployed app's `ARAG_AGENT_KB_ID` Fly secret
  actually points at the agent you've been configuring.** A real incident: after iterating
  through several agent ids during raw-API testing (a "v2" dead-end, the real one), the secret
  was left pointing at the abandoned one - the live app had been silently talking to a totally
  unconfigured agent the whole time, independent of and hiding whatever fixes were made
  elsewhere. `flyctl secrets list --app <slug>` (names only, not values) at least confirms the
  secret exists; cross-check its value was actually set to the CURRENT agent id after any
  agent-id churn, not just once at initial setup.
- **Honest safety gate (critical - stops confident-wrong answers):**
  - Count only **substantive** tool successes. Keep a denylist of non-substantive tools (bare catalogue lists like a plain "list all lines", plus settings/notifications/auth/etc.) that don't count on their own. If `success_count == 0` at the answer, emit `error stage:"no_grounded_data"` -> honest state (do NOT render the composed answer).
  - **Negative-claim backstop**: a regex for all-clear phrasing ("no stoppage", "running without", "no issues", "nothing holding", "not currently blocked/held/on hold"...). If the answer matches AND none of the status-verifying tools (holds/defects/status/root-cause queries) succeeded, refuse (`stage:"unverified_negative"`) regardless of any other success. Negative operational claims are the dangerous direction - never assert an absence-of-problem you didn't verify.
  - Fallback rule: **only a `timeout` on a question that has a MATCHING cached golden** shows that golden; every other failure stage (`no_grounded_data`, `unverified_negative`, transport, config, catch-all) shows the honest message ALONE - never a mismatched example.
  - Cache a golden per hero question so the flagship never dead-airs.
- **UI**: a live "Watching the agent work" step list - plan, each tool call as a friendly action with a spinner then a tick + a one-line result summary, doc reads, composing, then the grounded answer + a collapsible "How this was answered" trace. Track tool cards in a **map keyed by tool name/id** (not a single slot) or multi-step traces leave a stuck spinner. Show an elapsed timer; animate steps in. NEVER render a raw HTTP/pydantic error - format failed steps as "Couldn't complete this lookup - <friendly> didn't return usable data".
- **The final answer text MUST go through a real markdown renderer, never a plain text/`<p>`
  node** (binding, real defect caught 2 Aug 2026: Operator Fleet shipped with literal
  `**Unit 14**` and `1. **Unit 07**...` visible on screen instead of bold text and a real
  list). ARAG's composed answers routinely contain markdown - bold, numbered lists,
  sub-bullets. Pipe `raw.answer` through a markdown-to-HTML component (e.g. `marked` /
  `react-markdown` / equivalent for the stack in use), not straight into text content. Check
  this on the actual rendered answer, not just the streamed JSON - the happy-path capture
  screenshot used for the deck can look fine while the live app still shows raw syntax if
  the screenshot was taken mid-stream or off a different code path.

## Verify (acceptance checklist)
- `POST /mcp` tools/call with a `__<uuid>`-suffixed name resolves (401 unauth; real data authed).
- Ephemeral smoke: a question the data can answer streams a real trace and a grounded answer, and the trace shows ARAG calling the MCP tools (proves ARAG drives MCP, not the app).
- No key/host/region string in any client-side payload or streamed event; keys server-side only.
- Honesty: a question whose tools fail must NEVER assert an unverified status - honest state instead. Cross-check against the app's own UI for contradictions.
- UI: friendly labels (no raw tool names/paths/UUIDs), no stuck spinner on multi-step fallback, correct list numbering, honest fallback stands alone.

## Reference implementation (optional - if you have it)
Proven in a FastAPI + SQLite ERP demo: an MCP server with the suffix-strip, a streaming
`/session/ephemeral` proxy with the substantive-success + negative-claim gate, and a
"Watching the agent work" UI; the ARAG side mirrors Progress's own maintenanceOS reference
(`arag-client` + a hand-built dashboard "mos" workflow: Retrieval Context -> Smart agent ->
registered MCP node -> Summarize). The steps above stand alone without these files.
