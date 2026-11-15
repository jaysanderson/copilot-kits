// ─────────────────────────────────────────────────────────────────────────────
// Module 4.3 (flagship rebuild) — the RAO streaming proxy + honest gate.
// Packaged from the rao-workflow skill's proven Build step 5 pattern.
//
// ARAG's own Retrieval Agent, NOT a homegrown planner, drives this — this
// server only relays ARAG's live trace and applies the honest-refusal gate on
// top; it never calls the app's /mcp tools itself (hard rule: "ARAG is the
// agent, not our code").
// ─────────────────────────────────────────────────────────────────────────────

import { drainKbSources } from './kbTap.mjs';

const trimUrl = (u) => (u || '').replace(/\/+$/, '');

// Non-substantive tools never count toward "the agent actually found
// something" on their own (bare catalogue lists, settings/notifications/auth
// endpoints). Extend this per app via `nonSubstantiveTools`.
const DEFAULT_NON_SUBSTANTIVE = new Set(['list_all', 'health', 'ping', 'whoami']);

// Negative-claim backstop: an all-clear-sounding answer is the dangerous
// direction to get wrong — never assert an absence-of-problem that wasn't
// actually verified by a status-checking tool call.
const NEGATIVE_CLAIM_RE =
  /\bno (stoppage|issue|problem)s?\b|\brunning without\b|\bnothing (is )?(holding|blocking)\b|\bnot currently (blocked|held|on hold)\b/i;

/**
 * Registers `POST <mountPath>` (default `/api/agent/session`) which proxies
 * to ARAG's `{agentBaseUrl}/api/v1/agent/{agentKbId}/session/ephemeral`,
 * streams the NDJSON trace straight through (never buffered), and applies the
 * honest safety gate before letting a composed answer reach the client.
 *
 * Required env (server-side only, never client code — hard rule 6):
 *   ARAG_AGENT_KEY       PAT, sent as `Authorization: Bearer <PAT>`
 *   ARAG_AGENT_BASE_URL  the dp host, e.g. https://<zone>.dp.progress.cloud
 *   ARAG_AGENT_KB_ID     the agent id (a mode:"agent" KB)
 *   ARAG_AGENT_TIMEOUT_S optional, default 55
 *
 * Disclosed-gap mode: when any of the three required env vars is missing, OR
 * `RAO_DISCLOSED_GAP=true` is set, this responds with a single honest
 * `disclosed_gap` event instead of attempting a call — the rao-workflow
 * skill's own unresolved section documents `registered_agents` node-graph
 * persistence as a real, contradictory-across-builds platform fragility
 * (never a silent DB-lookup-plus-narration substitute).
 */
export function registerRaoProxy(app, { mountPath = '/api/agent/session', nonSubstantiveTools = [] } = {}) {
  const nonSubstantive = new Set([...DEFAULT_NON_SUBSTANTIVE, ...nonSubstantiveTools]);
  const AGENT_KEY = process.env.ARAG_AGENT_KEY;
  const AGENT_BASE = trimUrl(process.env.ARAG_AGENT_BASE_URL);
  const AGENT_KB_ID = process.env.ARAG_AGENT_KB_ID;
  const TIMEOUT_S = Number(process.env.ARAG_AGENT_TIMEOUT_S || 55);
  const forcedGap = String(process.env.RAO_DISCLOSED_GAP || '').toLowerCase() === 'true';

  app.post(mountPath, async (req, res) => {
    res.setHeader('Content-Type', 'application/x-ndjson');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    const emit = (obj) => { res.write(JSON.stringify(obj) + '\n'); if (res.flush) res.flush(); };

    if (forcedGap || !AGENT_KEY || !AGENT_BASE || !AGENT_KB_ID) {
      // Honest, visible disclosure — same pattern as revolution-dms's
      // "Live agent trace unavailable" label. This is NOT a silent fallback
      // to deterministic DB lookups narrated by a raw LLM; it says plainly
      // that ARAG's own Retrieval Agent mechanism isn't wired up for this
      // demo, and why, so the demo never quietly looks more capable than it is.
      emit({
        stage: 'disclosed_gap',
        message:
          "ARAG's own Retrieval Agent (RAO) is not configured for this demo. " +
          'registered_agents node-graph persistence is a known, disclosed platform ' +
          'fragility (see the rao-workflow skill) - this app does not silently ' +
          "substitute a homegrown planner or a deterministic DB lookup narrated by " +
          "a raw LLM in its place. Set ARAG_AGENT_KEY / ARAG_AGENT_BASE_URL / " +
          'ARAG_AGENT_KB_ID to wire up a real agent.',
      });
      return res.end();
    }

    const { query } = req.body || {};
    const authorization = req.headers.authorization || '';
    // Standard B26: capture the KB documents the agent grounds on during THIS
    // session. The search_claim_documents MCP handler records each retrieval to
    // kbTap; anything recorded from here on belongs to this session, drained and
    // emitted as `kb_sources` alongside the tool trail once the answer resolves.
    const sessionStart = Date.now();
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_S * 1000);
    res.on('close', () => { clearTimeout(timer); if (!res.writableEnded) controller.abort(); });

    let substantiveSuccessCount = 0;
    let sawStatusVerifyingTool = false;
    let composedAnswer = '';
    // Standard B26 / trace visibility: the KB document search doesn't reliably
    // surface as a labelled tool step in ARAG's own smart-agent trace (it maps to
    // a generic reasoning lane), so we announce it from the server-side tap - a
    // real signal that the search_claim_documents handler actually ran this
    // session - as a proper tool_call lane the first time it fires, so the KB
    // grounding is visibly part of the orchestration alongside the data tools.
    let kbAnnounced = false;

    try {
      const upstream = await fetch(`${AGENT_BASE}/api/v1/agent/${AGENT_KB_ID}/session/ephemeral`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${AGENT_KEY}`, 'Content-Type': 'application/json' },
        // Bug fix (ported upstream 17 Aug 2026, confirmed independently by both
        // demo-A compliance-co-compliance-desk and demo-B home-co-home): the
        // /session/ephemeral endpoint's real request schema requires `question`,
        // not `query` - this module previously sent `query` and 422'd on every
        // single call. Confirmed via the live 422:
        // {"detail":[{"loc":["body","question"],"msg":"Field required"}]}.
        body: JSON.stringify({ question: query, headers: { authorization } }),
        signal: controller.signal,
      });
      if (!upstream.ok || !upstream.body) {
        emit({ stage: 'error', error: `agent session ${upstream.status}` });
        return res.end();
      }

      const reader = upstream.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        // The moment the KB search handler has recorded a retrieval this session,
        // show it as a real tool_call lane in the live trace (once).
        if (!kbAnnounced && drainKbSources(sessionStart).length) {
          kbAnnounced = true;
          emit({ stage: 'tool_call', tool: 'search_claim_documents', text: 'Searching the policy and claim documents', detail: 'Retrieval over the policy wording and the claim file' });
        }
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (!line.trim()) continue;
          let raw;
          try { raw = JSON.parse(line); } catch { continue; }

          // The rao-workflow skill's critical, hard-won finding: the real
          // fields live nested under `step`, not flat top-level fields. A
          // proxy checking flat fields silently sees nothing and false-
          // refuses on every question even when the agent is working fine.
          const step = raw.step || {};

          // Bug fix (ported upstream 17 Aug 2026, confirmed independently by
          // both demo-A compliance-co-compliance-desk and demo-B home-co-home,
          // via raw calls to /session/ephemeral bypassing this proxy entirely):
          // the ORIGINAL `if (step.module && step.module !== 'smart') continue`
          // above dropped every non-"smart" step - including `module:"mcp"`
          // steps - before it could ever be inspected, so real tool evidence
          // that only ever shows up on those steps was silently discarded. The
          // ORIGINAL success check (`step.module === 'smart' && step.title
          // .includes('Tool')`) also never matched in practice: the smart
          // module's own step titles are "Reactive/Execution iteration N/M" -
          // the literal word "Tool" only ever appears inside step.value (e.g.
          // "Tool calls: get_x(...)" / "Results: ..."), never in step.title.
          // Net effect: substantiveSuccessCount stayed 0 and a genuinely
          // working agent (real tool calls, real grounded answer) was reported
          // as `no_grounded_data` on every single question.
          //
          // Fix: recognise BOTH real tool-success signals seen live (trace
          // shape apparently varies by agent config, so check both rather than
          // picking one):
          //   1. an `mcp`-module step titled "MCP: Tool result", or
          //   2. a `smart`-module "Execution iteration" step whose VALUE
          //      (not title) starts with "Results: ...".
          const isMcpToolResult = step.module === 'mcp' && /Tool result/i.test(step.title || '');
          const isSmartExecutionResult =
            step.module === 'smart' && /Execution iteration/i.test(step.title || '') && /^Results:/i.test(step.value || '');
          if (isMcpToolResult || isSmartExecutionResult) {
            const toolName = extractToolName(step.title, step.value);
            const ok = !step.error;
            if (ok && toolName && !nonSubstantive.has(toolName)) substantiveSuccessCount += 1;
            // This demo's tools (get_client_holdings, check_restricted_list,
            // get_advisor_licence_status) ARE the compliance-status-verifying
            // calls - any real success on any of them counts as status
            // verification (kept from this app's own local fix; the generic
            // fleet-vertical /status|hold|defect|root.?cause/ regex upstream
            // would silently miss check_restricted_list, the most safety-
            // critical of the three).
            if (ok && toolName) sawStatusVerifyingTool = true;
          }

          // Only emit smart-module steps to the UI trace (skip the MCP node's
          // own duplicate mirror of the same calls - display-only; the
          // success/grounding accounting above already inspected it when present).
          if (!step.module || step.module === 'smart') {
            const mapped = mapStepToEvent(step, raw);
            if (mapped) emit(mapped);
          }

          if (typeof raw.answer === 'string') composedAnswer = raw.answer;
          else if (step.title?.toLowerCase().includes('compos') && typeof step.value === 'string') composedAnswer = step.value;
        }
      }

      // The KB documents grounded on this session - real retrieval (via the tap),
      // used both as honest grounding for the gate below and shown as sources.
      const kbSources = drainKbSources(sessionStart);

      // Honest gate 1: nothing substantive retrieved from EITHER the live tools
      // OR the knowledge box - refuse to compose an answer from nothing.
      if (substantiveSuccessCount === 0 && kbSources.length === 0) {
        emit({ stage: 'no_grounded_data', message: 'No tool call returned usable data - refusing to compose an answer from nothing.' });
        return res.end();
      }
      // Honest gate 2: negative-claim backstop — the dangerous direction.
      if (NEGATIVE_CLAIM_RE.test(composedAnswer) && !sawStatusVerifyingTool) {
        emit({ stage: 'unverified_negative', message: 'The answer reads as an all-clear, but no status-verifying tool ran - refusing to assert an unverified negative.' });
        return res.end();
      }

      // Standard B26: show the KB search as a labelled tool RESULT (closing the
      // tool_call lane emitted mid-stream) AND surface the documents it grounded
      // on, so the trace and the sources rail both show BOTH kinds of source.
      if (kbSources.length) {
        emit({ stage: 'tool_result', ok: true, tool: 'search_claim_documents', text: `Retrieved ${kbSources.length} policy/claim document${kbSources.length > 1 ? 's' : ''}`, detail: kbSources.map((s) => s.title).join('; ') });
        emit({ stage: 'kb_sources', sources: kbSources });
      }

      emit({ stage: 'answer', text: composedAnswer });
      res.end();
    } catch (err) {
      if (controller.signal.aborted) { emit({ stage: 'error', error: 'timeout' }); return res.end(); }
      emit({ stage: 'error', error: err.message });
      res.end();
    } finally {
      clearTimeout(timer);
    }
  });
}

// Standard B11 (arag-demo-app skill, 17 Aug 2026): the "watch it work" surface
// must render whatever the real NDJSON stream carries — plan / tool call /
// tool result / composing, each visually distinct — not a flat log line. This
// is the ONE place that maps ARAG's raw step shape onto the vocabulary the
// client renders, so it stays a single source of truth (RaoEvent in lib/rao.ts
// mirrors this exactly). Every event now also carries `tool` (the extracted
// tool name, when the step is a tool call/result) and `detail` (a trimmed
// excerpt of the step's own raw value — arguments or result body) so the UI
// can show a real "Tool: get_fleet_status(vehicle_id=42)" chip and an
// expandable result, not just a humanised sentence.
// Human language for each MCP tool this app registers — so a lane reads
// "Looking up the client's holdings", never "Execution iteration 1/5" or a bare
// code symbol. Steve Jobs review, 17 Aug 2026: retire the machine log jargon.
// This is the single source of truth for what a tool step SAYS (the code chip
// still shows the real tool name separately, for the technical viewer).
const TOOL_PHRASES = {
  get_policy_status: 'Checking the policy status, cover and premium standing',
  get_claimant_history: "Looking up the claimant's prior claims history",
  get_claim: 'Pulling the claim record',
  search_claim_documents: 'Searching the policy wording and claim documents',
  task_complete: 'Finalising the answer',
};

function toolPhrase(tool, fallback) {
  if (tool && TOOL_PHRASES[tool]) return TOOL_PHRASES[tool];
  if (tool) return `Calling ${tool.replace(/_/g, ' ')}`;
  return fallback;
}

// ARAG's own smart-agent trace text embeds a raw resource UUID and a
// Python-dict-repr parameter blob (e.g. "get_client_holdings__7a836717-... of
// 7a836717-... with parameters {'client': 'Ashwell family trust'}: <payload>").
// That is genuinely what the agent called, but rendered verbatim it reads as a
// stack trace, not a compliance answer. Reformat to "tool_name · key: value" -
// same real tool + parameters, human-readable - and drop the UUID(s) and any
// trailing raw payload. Falls back to the plain human tool phrase when there's
// nothing recognisable to parse (never renders the raw string as a last resort).
function prettifyToolDetail(raw, tool) {
  const body = String(raw || '');
  const label = tool ? tool.replace(/_/g, ' ') : 'tool';
  const paramsMatch = /with parameters\s*(\{[^}]*\})/i.exec(body);
  if (!paramsMatch) return tool ? toolPhrase(tool) : undefined;
  const pairs = [...paramsMatch[1].matchAll(/'([^']+)'\s*:\s*'([^']*)'/g)]
    .map(([, k, v]) => `${k}: ${titleCase(v)}`);
  return pairs.length ? `${label} · ${pairs.join(', ')}` : label;
}

function titleCase(s) {
  return String(s).replace(/\w\S*/g, (w) => w[0].toUpperCase() + w.slice(1));
}

function mapStepToEvent(step, raw) {
  if (!step.module && !step.title) return null;
  const title = step.title || '';
  const rawDetail = typeof step.value === 'string' ? step.value.trim().slice(0, 800) : undefined;
  const tool = extractToolName(title, step.value) || undefined;
  // The KB document search is surfaced deterministically from the server-side
  // tap as a single tool_call + tool_result pair (registerRaoProxy), so suppress
  // any lane the real trace ALSO emits for it - the trace shape varies per run,
  // and a duplicate KB lane would otherwise appear whenever it does classify.
  if (tool === 'search_claim_documents') return null;
  const detail = prettifyToolDetail(rawDetail, tool) ?? rawDetail;

  const value = typeof step.value === 'string' ? step.value : '';
  if (/plan/i.test(title)) return { stage: 'plan', text: 'Planning the check', detail: rawDetail };
  if (/tool.*error/i.test(title)) {
    return { stage: 'tool_result', ok: false, tool, text: `That lookup didn't return usable data${tool ? ` (${tool.replace(/_/g, ' ')})` : ''}.`, detail };
  }
  // Smart-module reasoning loops surface tool activity as "Tool calls: get_x(...)"
  // then "Results: get_x of ..." — and (confirmed live, 17 Aug 2026) this agent
  // puts that string in the step TITLE, not the value. Classify either shape as
  // real tool_call / tool_result lanes so the client can build the sources list
  // + REMi contexts from them (the tool results ARE the Concierge's retrieved
  // context).
  if (/^\s*Results:/i.test(title) || /^\s*Results:/i.test(value)) {
    const body = /^\s*Results:/i.test(value) ? value : title;
    const trimmedBody = (body || '').trim().slice(0, 800);
    return { stage: 'tool_result', ok: !step.error, tool, text: toolPhrase(tool, 'Retrieved the result'), detail: prettifyToolDetail(trimmedBody, tool) ?? trimmedBody };
  }
  if (/tool calls?:/i.test(value) || /tool calls?:/i.test(title) || /tool/i.test(title)) {
    const ok = !step.error;
    return {
      stage: ok ? 'tool_call' : 'tool_result',
      ok,
      tool,
      text: ok ? toolPhrase(tool, 'Calling a compliance tool') : `That lookup didn't return usable data${tool ? ` (${tool.replace(/_/g, ' ')})` : ''}.`,
      detail,
    };
  }
  if (/compos/i.test(title)) return { stage: 'composing', text: 'Composing a grounded answer' };
  if (raw.heartbeat) return { stage: 'heartbeat' };
  // Everything else (reasoning-loop bookkeeping) is humanised; carry `tool`
  // through so any tool named in these steps is still attributable client-side.
  return { stage: 'doc_search', text: humaniseTitle(title, tool), tool, detail };
}

function humaniseTitle(title, tool) {
  const t = String(title || '').replace(/^Smart agent:\s*/i, '').replace(/^MCP:\s*/i, '');
  if (tool && TOOL_PHRASES[tool]) return TOOL_PHRASES[tool];
  if (/execution iteration/i.test(t)) return tool ? toolPhrase(tool) : 'Running the next lookup';
  if (/reactive iteration/i.test(t)) return 'Reviewing what it has gathered so far';
  if (/reactive mode completed/i.test(t)) return 'Finished reviewing the evidence';
  if (/execution mode completed/i.test(t)) return 'Finished gathering the data';
  if (/mode completed/i.test(t)) return 'Step complete';
  if (/plan/i.test(t)) return 'Planning the check';
  if (/compos/i.test(t)) return 'Composing a grounded answer';
  return t;
}

function extractToolName(title, value) {
  const both = `${title || ''}\n${value || ''}`;
  const m =
    /Used tool:\s*([\w.-]+)/i.exec(both) ||
    // Confirmed live: the smart-module "Results: ..." string names the tool as
    // "Results: <tool_name> of ..." — and it can live in EITHER title or value.
    /Results:\s*([\w.-]+)\s+of/i.exec(both) ||
    /Tool calls?:\s*([\w.-]+)/i.exec(both) ||
    /tool[:=]\s*([\w.-]+)/i.exec(both);
  // rao-workflow trap (CLAUDE.md): tool names arrive with a `__<uuid>` suffix
  // (e.g. get_advisor_licence_status__7a836717-...). Strip it so the name maps
  // to its human phrase and reads clean in the UI.
  return m ? m[1].replace(/__[0-9a-f-]{6,}$/i, '') : null;
}
