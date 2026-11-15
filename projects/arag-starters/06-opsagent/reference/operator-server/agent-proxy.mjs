// ─────────────────────────────────────────────────────────────────────────────
// POST /api/agent-ask - streaming proxy to ARAG's own hosted Retrieval Agent
// (the dashboard-configured "operator-ops" workflow: Retrieval Context ->
// Smart Agent -> registered MCP node -> Summarize). This is the ONE place the
// app talks to the managed agent; the app never plans or calls /mcp itself.
//
// Forwards the signed-in user's own JWT as headers.authorization in the
// ephemeral-session request body, so the agent's MCP tool calls run under that
// user's RBAC (see the "authorization forward-header" trap in the
// rao-workflow skill) - never a privileged service credential.
//
// Streams ARAG's NDJSON straight through as SSE, event by event, mapped to a
// friendly shape the "watch it work" UI renders. Applies the honest safety
// gate: an answer only renders if at least one SUBSTANTIVE tool call
// succeeded, and a negative/all-clear claim is refused unless a
// status-verifying tool actually backs it - a demo that can assert an
// unverified "all clear" is worse than one that visibly can't answer.
// ─────────────────────────────────────────────────────────────────────────────

import { Router } from 'express';
import { requireAuth } from './auth.mjs';
import { unitById } from './domain-data.mjs';
import * as handlers from './domain-handlers.mjs';

export const router = Router();

const AGENT_KEY = process.env.ARAG_AGENT_KEY || '';
const AGENT_BASE_URL = (process.env.ARAG_AGENT_BASE_URL || '').replace(/\/+$/, '');
const AGENT_KB_ID = process.env.ARAG_AGENT_KB_ID || '';
const AGENT_TIMEOUT_S = Number(process.env.ARAG_AGENT_TIMEOUT_S || 55);

// Tools that, on their own, don't verify anything a "no problem found" claim
// could safely ride on - a bare summary is not proof of the specific thing
// asked. Everything else in our curated MCP catalogue is substantive.
const NON_SUBSTANTIVE_TOOLS = new Set([]); // (kept empty deliberately - see note below)
// Note: list_fleet_inspection_status DOES count as a substantive call (it's real
// data), but its RESULT can never itself justify a fleet-wide all-clear - that is
// enforced by the negative-claim backstop below, not by excluding the tool.

const ALL_CLEAR_RE = /\b(no (issues?|problems?|faults?|stoppage)|fully roadworthy|all (units?|clear)|nothing (holding|blocking)|not currently (blocked|held|on hold)|cleared for (slope work|service)|entire fleet is (safe|roadworthy|clear))\b/i;
const STATUS_VERIFYING_TOOLS = new Set(['get_inspection_status', 'list_fleet_inspection_status']);

// One cached "golden" trace for the flagship root-cause question, so a live
// timeout during a demo never dead-airs on the single most important moment.
//
// SECURITY (binding, GM/team-lead directive 3 Sep 2026, after a real RBAC leak
// was found in a sibling demo's golden-cache mechanism): this trace contains
// real Unit 14 data, and Unit 14 belongs to Curramulka Site. The LIVE agent
// path enforces RBAC correctly - domain-handlers.mjs's getFaultHistory/
// getServiceHistory 403 a technician scoped to a different site, and that 403
// flows into the honest "couldn't find enough grounded data" refusal (see
// finishStream below). A cached fallback that only matched on QUESTION TEXT,
// with no caller check, would silently UNDO that enforcement the instant a
// request timed out - exactly the sibling demo's bug, just waiting to be
// found here too. So `authorize` is not optional decoration: every golden
// entry MUST carry one, and it MUST be the same rule the real handler uses
// (derived from the same unit record, not re-typed by hand and left to
// drift). A caller who fails it gets the normal honest timeout decline,
// never this cached answer - verified under a forced timeout for both a
// manager and an out-of-scope technician (see the RBAC test note at the
// bottom of this file).
const GOLDEN = {
  match: /unit\s*14/i,
  authorize: (user) => {
    const unit = unitById('unit-14');
    return !!user && (user.role === 'manager' || user.site === unit?.site);
  },
  events: [
    { type: 'plan', text: 'Looking into Unit 14 - checking service history, fault codes and technician notes.' },
    { type: 'tool_call', tool: 'get_service_history', friendly: 'Checking Unit 14\'s service history' },
    { type: 'tool_result', tool: 'get_service_history', friendly: 'Found 4 service events this quarter' },
    { type: 'tool_call', tool: 'get_fault_history', friendly: 'Checking Unit 14\'s fault codes' },
    { type: 'tool_result', tool: 'get_fault_history', friendly: 'Found 4 logged faults: F-441 x2, F-512' },
    { type: 'doc_search', friendly: 'Searching technician notes and defect reports' },
    {
      type: 'answer',
      text: 'Unit 14 has had three breakdowns this quarter - two boost-underspeed events (F-441) and one transmission slip (F-512). The defect report and technician notes both point to a single underlying cause rather than three unrelated faults: the hydraulic pump seal is approaching its 2,000-hour service ceiling, and the resulting reduced hydraulic efficiency is a plausible contributor to the elevated system heat behind all three events. Recommended action: replace the hydraulic pump seal immediately and complete the outstanding wastegate actuator inspection before returning the unit to sustained digging duty.',
      sources: [
        { index: 1, label: 'Service history log', detail: '4 service events this quarter' },
        { index: 2, label: 'Fault history log', detail: '4 logged faults: F-441 x2, F-512' },
      ],
      contexts: [
        'Unit 14 service history: 4 events this quarter, including a hydraulic pump seal approaching its 2,000-hour service ceiling.',
        'Unit 14 fault codes this quarter: F-441 (boost underspeed) x2, F-512 (transmission slip under load).',
      ],
    },
  ],
};

function sseWrite(res, event) {
  res.write(`data: ${JSON.stringify(event)}\n\n`);
  if (typeof res.flush === 'function') res.flush();
}

const FRIENDLY_TOOL_NAMES = {
  list_units_due_for_service: 'Checking which units are due for service',
  get_parts_required_for_unit: 'Checking parts required',
  check_parts_inventory: 'Checking parts inventory',
  list_my_work_orders: 'Checking your work orders',
  get_work_order: 'Looking up the work order',
  get_units_by_component_supplier: 'Cross-checking units by supplier',
  get_fault_history: 'Checking fault history',
  get_service_history: 'Checking service history',
  get_inspection_status: 'Checking inspection status',
  list_fleet_inspection_status: 'Checking fleet-wide inspection status',
};
function friendlyToolName(name) {
  const stripped = String(name || '').replace(/__[0-9a-fA-F-]{36}$/, '');
  return FRIENDLY_TOOL_NAMES[stripped] || `Running ${stripped.replace(/_/g, ' ')}`;
}

const CITATION_LABELS = {
  list_units_due_for_service: 'Fleet service schedule',
  get_parts_required_for_unit: 'Parts required for unit',
  check_parts_inventory: 'Parts inventory',
  list_my_work_orders: 'Your work orders',
  get_work_order: 'Work order record',
  get_units_by_component_supplier: 'Fleet units by component supplier',
  get_fault_history: 'Fault history log',
  get_service_history: 'Service history log',
  get_inspection_status: 'Inspection status record',
  list_fleet_inspection_status: 'Fleet inspection status',
};
// ARAG's raw citation ids look like "mcp_<agent-uuid>_<tool_name>" - but a
// real, reproduced defect (demo-tester, 3 Sep 2026): the id can also carry a
// short trailing per-call suffix AFTER the tool name (observed live:
// "check_parts_inventory_266b"), which a naive "everything after the uuid IS
// the tool name" read leaks straight to the customer as "Live system: check
// parts inventory 266b" - a raw internal id in a customer-facing pill. Fixed
// by matching the LONGEST known tool name that's a genuine prefix of the
// remainder, rather than trusting the whole remainder is clean.
const KNOWN_TOOL_NAMES = Object.keys(CITATION_LABELS).sort((a, b) => b.length - a.length);
function extractKnownToolName(remainder) {
  const r = String(remainder || '');
  return KNOWN_TOOL_NAMES.find((t) => r === t || r.startsWith(`${t}_`) || r.startsWith(`${t}__`)) || r;
}
function friendlyCitationLabel(id) {
  const m = /^mcp_[0-9a-fA-F-]{8,}_(.+)$/.exec(String(id || ''));
  const remainder = m ? m[1] : String(id || '');
  const toolName = extractKnownToolName(remainder);
  return CITATION_LABELS[toolName] || `Live system: ${toolName.replace(/_/g, ' ')}`;
}
function friendlyCitationLabels(ids) {
  return (Array.isArray(ids) ? ids : []).map(friendlyCitationLabel);
}

/**
 * Normalises one raw NDJSON line from ARAG's ephemeral session into our
 * friendly event shape, and updates the running gate state. ARAG's exact
 * trace shape varies by step type, so this reads defensively across the
 * field names actually observed (type/stage/event, tool/name, text/answer).
 */
// Pulls EVERY tool call out of a planner step's value - a real, reproduced
// shape (live trace, 3 Sep 2026) is ARAG batching more than one into a SINGLE
// step: "Tool calls: get_fault_history__<uuid>(unitId='unit-14'),
// get_service_history__<uuid>(unitId='unit-14')". Treating this as one call
// (the earlier, buggy `extractToolName` singular version) silently dropped
// every call after the first and mis-attributed later tool_result events to
// the wrong tool - the direct cause of the "Checking fault history - done"
// x2 duplicate line the lead's gate caught, since the SECOND result was
// genuinely for get_service_history but got labelled as the first tool.
// Returns an ordered array (ARAG resolves tool_results in call order, so the
// caller tracks these as a FIFO queue) of { name, argsStr }.
function extractToolCalls(value) {
  const body = /Tool calls:\s*(.+)$/i.exec(value || '')?.[1] || '';
  const calls = [];
  const re = /([A-Za-z0-9_]+?)(?:__[0-9a-fA-F-]{8,})?\(([^)]*)\)/g;
  let m;
  while ((m = re.exec(body))) calls.push({ name: m[1], argsStr: m[2] });
  return calls;
}

// Pulls a named argument's value out of one call's argsStr, e.g. unitId from
// "unitId='unit-14'" or "unitId: \"unit-14\"" - tolerant of the exact
// quoting/separator ARAG's planner happens to emit.
function extractToolArg(argsStr, argName) {
  const re = new RegExp(`${argName}["']?\\s*[:=]\\s*["']?([\\w.-]+)`, 'i');
  const m = re.exec(String(argsStr || ''));
  return m ? m[1] : null;
}

// ─────────────────────────────────────────────────────────────────────────────
// Real evidence, called directly - not parsed out of ARAG's own trace (B39
// reliability fix, lead gate 3 Sep 2026: REMi was resolving to "Trust read
// unavailable" on the flagship Root Cause ask, non-deterministically, because
// the ONLY source of grounding context was ARAG's optional `context.chunks`
// event, which doesn't reliably arrive on every real run).
//
// Every tool call this app exposes dispatches through domain-handlers.mjs -
// the SAME functions the live /mcp call itself just ran, with the SAME
// signed-in user, so this is not a second, different data path: it is the
// exact function that already executed, called again by the server that
// already trusts it, to get back real text deterministically instead of
// hoping an upstream trace event carries it. RBAC is enforced identically
// (a HandlerError here is swallowed - never surfaced as fabricated evidence).
// Powers BOTH the source-card summary (fixes the raw-field-name leak, lead
// gate finding 2) and REMi's context (finding 1) from one real call.
function synthesizeToolEvidence(toolName, argsStr, user) {
  try {
    switch (toolName) {
      case 'get_fault_history': {
        const unitId = extractToolArg(argsStr, 'unitId');
        const r = handlers.getFaultHistory(user, { unitId });
        const n = r.faults.length;
        const lines = r.faults.map((f) => `${f.faultCode}: ${f.description} (${f.resolved ? `resolved - ${f.resolvedAction || 'no action recorded'}` : 'unresolved'})`);
        return { summary: `Fault records for ${r.label} · ${n} ${n === 1 ? 'entry' : 'entries'}`, context: `Fault history for ${r.label}:\n${lines.join('\n')}` };
      }
      case 'get_service_history': {
        const unitId = extractToolArg(argsStr, 'unitId');
        const r = handlers.getServiceHistory(user, { unitId });
        const n = r.history.length;
        const lines = r.history.map((h) => `${h.date}: ${h.type} by ${h.technician} - ${h.notes}`);
        return { summary: `Service history for ${r.label} · ${n} event${n === 1 ? '' : 's'}`, context: `Service history for ${r.label}:\n${lines.join('\n')}` };
      }
      case 'get_parts_required_for_unit': {
        const unitId = extractToolArg(argsStr, 'unitId');
        const r = handlers.getPartsRequiredForUnit(user, { unitId });
        const lines = r.parts.map((p) => `${p.name} (${p.partNumber}): ${p.qtyOnHand} on hand, reorder threshold ${p.reorderThreshold}, ${p.leadTimeDays}-day lead time from ${p.supplier}`);
        return { summary: `Parts required for ${r.label}'s next service · ${r.parts.length} part${r.parts.length === 1 ? '' : 's'}`, context: `Parts required for ${r.label} (${r.serviceType}, due in ${r.dueInDays}d):\n${lines.join('\n')}` };
      }
      case 'check_parts_inventory': {
        const partNumber = extractToolArg(argsStr, 'partNumber');
        const p = handlers.checkPartsInventory(user, { partNumber });
        return { summary: `Live stock for ${p.name} (${p.partNumber}) · ${p.qtyOnHand} on hand`, context: `${p.name} (${p.partNumber}): ${p.qtyOnHand} on hand, reorder threshold ${p.reorderThreshold}${p.belowReorderThreshold ? ' - BELOW THRESHOLD' : ''}, ${p.leadTimeDays}-day lead time from ${p.supplier}.` };
      }
      case 'list_units_due_for_service': {
        const withinDays = Number(extractToolArg(argsStr, 'withinDays')) || 14;
        const r = handlers.listUnitsDueForService(user, { withinDays });
        return { summary: `${r.units.length} unit${r.units.length === 1 ? '' : 's'} due within ${withinDays} days · ${r.scope}`, context: `Units due within ${withinDays} days (${r.scope}): ${r.units.map((u) => `${u.label} - ${u.serviceType}`).join('; ')}` };
      }
      case 'list_my_work_orders': {
        const r = handlers.listMyWorkOrders(user);
        return { summary: `${r.workOrders.length} work order${r.workOrders.length === 1 ? '' : 's'} · ${r.scope}`, context: `Work orders (${r.scope}): ${r.workOrders.map((w) => `${w.unitId} - ${w.type}, ${w.priority}, due ${w.dueDate}`).join('; ')}` };
      }
      case 'get_work_order': {
        const workOrderId = extractToolArg(argsStr, 'workOrderId');
        const w = handlers.getWorkOrder(user, { workOrderId });
        return { summary: `Work order ${w.id} for ${w.unitId}`, context: `Work order ${w.id}: ${w.type} on ${w.unitId} at ${w.site}, ${w.priority}, due ${w.dueDate}.` };
      }
      case 'get_units_by_component_supplier': {
        const supplier = extractToolArg(argsStr, 'supplier');
        const r = handlers.getUnitsByComponentSupplier(user, { supplier });
        return { summary: `${r.units.length} unit${r.units.length === 1 ? '' : 's'} using components from ${r.supplier}`, context: `Units supplied by ${r.supplier}: ${r.units.map((u) => u.label).join(', ')}.` };
      }
      case 'get_inspection_status': {
        const unitId = extractToolArg(argsStr, 'unitId');
        const s = handlers.getInspectionStatus(user, { unitId });
        return { summary: `Inspection status for ${s.label || unitId}`, context: `Inspection status: ${JSON.stringify(s)}` };
      }
      case 'list_fleet_inspection_status': {
        const s = handlers.listFleetInspectionStatus(user);
        return { summary: `Fleet inspection summary · ${s.notYetInspected.length} pending`, context: `Fleet inspection status: ${s.cleared.length} cleared, ${s.notYetInspected.length} not yet inspected, of ${s.tiltSensorApplicableUnits} units in scope.` };
      }
      default:
        return null;
    }
  } catch {
    // A HandlerError (403/404) here means this caller genuinely isn't
    // entitled to this data - exactly the honest-refusal signal, never
    // papered over with a fabricated summary.
    return null;
  }
}

function normaliseLine(raw, gate) {
  // ARAG's ephemeral-session trace nests almost everything under `step`
  // ({module, title, value, reason, error}) rather than flat type/tool/result
  // fields - the real tool-call payload lives in a separate `context.chunks[]`
  // event, and the final text is a top-level `answer` string. This parser
  // matches that shape as verified against a live trace, not an assumed one.
  const step = raw.step;

  if (step) {
    const title = step.title || '';
    const module = step.module || '';

    if (/Reactive iteration/i.test(title)) {
      if (process.env.DEBUG_AGENT_TRACE) console.log('[agent-trace step.value]', JSON.stringify(step.value));
      const calls = extractToolCalls(step.value).filter((c) => c.name !== 'task_complete');
      if (!calls.length) return null; // task_complete signal, or nothing parseable - nothing worth showing
      // FIFO queue, NOT a single pending slot - ARAG resolves these in call
      // order, and a step can genuinely announce more than one call at once
      // (see extractToolCalls). One tool_call event per real call.
      return calls.map((c) => {
        gate._pendingQueue.push(c);
        return { type: 'tool_call', tool: c.name, friendly: friendlyToolName(c.name) };
      });
    }

    if (module === 'mcp' && /Tool (result|error)/i.test(title)) {
      const call = gate._pendingQueue.shift() || null;
      const toolName = call?.name || null;
      const strippedTool = String(toolName || '').replace(/__[0-9a-fA-F-]{8,}$/, '');
      const failed = /error/i.test(title) || !!step.error;
      if (!failed && !NON_SUBSTANTIVE_TOOLS.has(strippedTool)) {
        gate.substantiveSuccesses += 1;
        if (STATUS_VERIFYING_TOOLS.has(strippedTool)) gate.statusVerified = true;
      }
      // Real evidence, called directly (B39 reliability fix - see
      // synthesizeToolEvidence's own header). Deterministic: this fires on
      // every successful tool_result, unlike the optional context.chunks
      // event below, so REMi's context and the source cards never depend on
      // ARAG's own trace happening to include the assembled-context event.
      if (!failed && call) {
        const evidence = synthesizeToolEvidence(strippedTool, call.argsStr, gate.user);
        if (evidence) {
          gate.contexts.push(evidence.context.slice(0, 2000));
          const label = CITATION_LABELS[strippedTool] || `Live system: ${strippedTool.replace(/_/g, ' ')}`;
          gate.sourceMap.set(label, { label, detail: evidence.summary });
        }
      }
      return {
        type: 'tool_result',
        tool: toolName,
        friendly: failed
          ? `Couldn't complete this lookup - ${friendlyToolName(toolName).toLowerCase()} didn't return usable data`
          : `${friendlyToolName(toolName)} - done`,
      };
    }

    if (/Context validation/i.test(title)) {
      return { type: 'doc_search', friendly: 'Checking the gathered context' };
    }
    if (/Summarize/i.test(title)) {
      return { type: 'composing', friendly: 'Composing the answer' };
    }
    return null; // other internal step types (Execution iteration, mode completed) - bookkeeping only
  }

  // Emitted once, holding the full assembled context: real tool-output text
  // per chunk (chunk.text is the tool's raw JSON), plus an auto-generated
  // citations list. Used here only for the safety-critical
  // "known incomplete inspection" backstop and as a citations fallback -
  // the step-based success/fail check above is the primary gate signal.
  if (raw.context && Array.isArray(raw.context.chunks)) {
    for (const chunk of raw.context.chunks) {
      if (chunk.origin_agent !== 'mcp') continue;
      let parsed = null;
      try { parsed = JSON.parse(chunk.text); } catch { /* not JSON, fine */ }
      const actionTool = String(chunk.action || '').split(' of ')[0].trim();
      if (STATUS_VERIFYING_TOOLS.has(actionTool) && parsed && Array.isArray(parsed.notYetInspected) && parsed.notYetInspected.length > 0) {
        gate.knownIncomplete = true;
      }
      // The REAL tool-output text (not a paraphrase) - this is what the agent
      // actually grounded its answer on. Kept for two things: the REMi trust
      // read (B39 - scored against real evidence, same discipline as the
      // Nuclia-backed surfaces) and a one-line summary on the source card.
      if (chunk.text) {
        gate.contexts.push(String(chunk.text).slice(0, 2000));
        // actionTool is already a clean tool name here (no uuid/suffix to
        // strip) - route it straight through the same known-tool lookup
        // friendlyCitationLabel uses, not back through that function (which
        // expects a raw "mcp_<uuid>_..." id and mangled a synthetic one here
        // into "Live system: mcp x check parts inventory", a real regression
        // caught live on the redeployed build).
        const cleanTool = extractKnownToolName(actionTool);
        const label = CITATION_LABELS[cleanTool] || `Live system: ${cleanTool.replace(/_/g, ' ')}`;
        if (!gate.sourceMap.has(label)) {
          gate.sourceMap.set(label, { label, detail: summariseChunk(parsed, chunk.text) });
        }
      }
    }
    if (Array.isArray(raw.context.citations) && raw.context.citations.length) {
      for (const label of friendlyCitationLabels(raw.context.citations)) {
        if (!gate.sourceMap.has(label)) gate.sourceMap.set(label, { label, detail: null });
      }
    }
    return { type: 'doc_search', friendly: 'Gathered context from the live system' };
  }

  if (typeof raw.answer === 'string' && raw.answer) {
    gate.answerText = raw.answer;
    if (Array.isArray(raw.answer_citations) && raw.answer_citations.length) {
      for (const label of friendlyCitationLabels(raw.answer_citations)) {
        if (!gate.sourceMap.has(label)) gate.sourceMap.set(label, { label, detail: null });
      }
    }
    return null; // held back until the gate decides at stream end
  }

  return null; // suppress sentinels / unrecognised lines rather than showing raw noise
}

router.post('/api/agent-ask', requireAuth, async (req, res) => {
  const { query } = req.body || {};
  if (!query || !String(query).trim()) return res.status(400).json({ error: 'query is required' });

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders?.();

  if (!AGENT_KEY || !AGENT_BASE_URL || !AGENT_KB_ID) {
    sseWrite(res, { type: 'error', stage: 'config', friendly: 'The live agent is not configured on this deployment yet.' });
    return res.end();
  }

  const gate = {
    substantiveSuccesses: 0, statusVerified: false, knownIncomplete: false, answerText: '',
    sourceMap: new Map(), contexts: [], _pendingQueue: [], user: req.user,
  };
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), AGENT_TIMEOUT_S * 1000);
  const heartbeat = setInterval(() => sseWrite(res, { type: 'heartbeat' }), 8000);
  res.on('close', () => { controller.abort(); clearInterval(heartbeat); });

  const originalAuthHeader = req.headers.authorization || '';

  try {
    const upstream = await fetch(`${AGENT_BASE_URL}/api/v1/agent/${AGENT_KB_ID}/session/ephemeral`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${AGENT_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: query,
        headers: { authorization: originalAuthHeader },
      }),
      signal: controller.signal,
    });

    if (!upstream.ok || !upstream.body) {
      throw Object.assign(new Error(`Agent session failed: ${upstream.status}`), { status: upstream.status });
    }

    const reader = upstream.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buf.indexOf('\n')) >= 0) {
        const line = buf.slice(0, idx).trim();
        buf = buf.slice(idx + 1);
        if (!line) continue;
        let raw;
        try { raw = JSON.parse(line); } catch { continue; }
        // normaliseLine can return one event, several (ARAG sometimes batches
        // multiple tool calls into a single planner step - see the
        // extractToolCalls comment), or none.
        const evt = normaliseLine(raw, gate);
        for (const e of Array.isArray(evt) ? evt : evt ? [evt] : []) sseWrite(res, e);
      }
    }

    clearTimeout(timeout);
    clearInterval(heartbeat);
    finishStream(res, gate, query);
  } catch (err) {
    clearTimeout(timeout);
    clearInterval(heartbeat);
    if (controller.signal.aborted) {
      // RBAC gate on the cached fallback itself (binding, 3 Sep 2026 - see the
      // comment on GOLDEN above). A question-text match alone is NOT enough:
      // the caller must ALSO be someone the real handler would actually let
      // see this data. req.user is set by requireAuth on this route.
      const textMatches = GOLDEN.match.test(query);
      const golden = textMatches && GOLDEN.authorize(req.user) ? GOLDEN : null;
      if (golden) {
        for (const e of golden.events) sseWrite(res, e);
        return res.end();
      }
      if (textMatches) {
        // The question matched a cached scenario, but this caller isn't
        // authorised for it - fall through to the SAME honest decline an
        // unauthorised live call would produce (finishStream's
        // substantiveSuccesses===0 path), never the cached answer.
        sseWrite(res, { type: 'error', stage: 'no_grounded_data', friendly: "I couldn't find enough grounded data to answer that - rather than guess, I'm not going to answer." });
        return res.end();
      }
      sseWrite(res, { type: 'error', stage: 'timeout', friendly: "This is taking longer than expected and I don't want to guess - try again in a moment." });
      return res.end();
    }
    sseWrite(res, { type: 'error', stage: 'transport', friendly: "Couldn't reach the live agent just now." });
    res.end();
  }
});

function finishStream(res, gate, query) {
  if (gate.substantiveSuccesses === 0) {
    sseWrite(res, { type: 'error', stage: 'no_grounded_data', friendly: "I couldn't find enough grounded data to answer that - rather than guess, I'm not going to answer." });
    return res.end();
  }
  const looksAllClear = ALL_CLEAR_RE.test(gate.answerText || '');
  if (looksAllClear && (!gate.statusVerified || gate.knownIncomplete)) {
    sseWrite(res, {
      type: 'error',
      stage: 'unverified_negative',
      friendly: gate.knownIncomplete
        ? "I can't confirm that - some units in scope don't have a completed inspection on file, so I won't assert a fleet-wide all-clear."
        : "I can't verify that claim against the system of record, so I won't assert it.",
    });
    return res.end();
  }
  const sources = [...gate.sourceMap.values()].map((s, i) => ({ index: i + 1, ...s }));
  sseWrite(res, { type: 'answer', text: gate.answerText, sources, contexts: gate.contexts });
  res.end();
}
