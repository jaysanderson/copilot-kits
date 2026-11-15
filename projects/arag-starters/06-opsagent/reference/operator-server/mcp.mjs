// ─────────────────────────────────────────────────────────────────────────────
// POST /mcp - the app's own MCP server. ARAG's Retrieval Agent is the MCP
// CLIENT here (not the other way around): the dashboard-configured agent
// workflow calls this endpoint as its registered tool source, forwarding the
// signed-in user's bearer JWT (see the "authorization forward-header" trap in
// the rao-workflow skill). Every tool call dispatches through the exact same
// domain-handlers.mjs functions the app's own REST UI uses, so RBAC is
// enforced once, in one place, for both callers.
//
// JSON-RPC 2.0, Streamable HTTP, stateless - methods: initialize, tools/list,
// tools/call. Public endpoint (no static auth); the per-request forwarded JWT
// carries RBAC, exactly like the app's own REST API.
// ─────────────────────────────────────────────────────────────────────────────

import { Router } from 'express';
import { userFromAuthHeader } from './auth.mjs';
import * as handlers from './domain-handlers.mjs';
import { HandlerError } from './domain-handlers.mjs';

export const router = Router();

// ARAG namespaces registered-agent tool names with a trailing
// "__<agent-uuid>" - strip it before matching our catalogue, or every call 404s.
const UUID_SUFFIX = /__[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
const stripAgentSuffix = (name) => String(name || '').replace(UUID_SUFFIX, '');

// Tool catalogue: name → { description, inputSchema, handler }. Kept small and
// curated (list/query/trace tools, no blind get-by-id the planner can't seed)
// per the skill's "uncurated catalogue makes the planner mis-plan" lesson - // every get-by-id tool here is reachable from a list tool's own output.
const TOOL_DEFS = [
  {
    name: 'list_units_due_for_service',
    description: 'Lists fleet units due for scheduled service within a given number of days, with the service type and parts required for each. Technician logins see only their own site; manager logins see the whole fleet.',
    inputSchema: { type: 'object', properties: { withinDays: { type: 'integer', description: 'Look-ahead window in days (default 14).' } } },
    handler: handlers.listUnitsDueForService,
  },
  {
    name: 'get_parts_required_for_unit',
    description: 'Gets the parts required for a specific unit\'s next scheduled service, with live inventory levels for each part.',
    inputSchema: { type: 'object', properties: { unitId: { type: 'string', description: 'Unit id, e.g. unit-07.' } }, required: ['unitId'] },
    handler: handlers.getPartsRequiredForUnit,
  },
  {
    name: 'check_parts_inventory',
    description: 'Checks live stock on hand for a specific part number, including whether it is below its reorder threshold and its supplier lead time.',
    inputSchema: { type: 'object', properties: { partNumber: { type: 'string', description: 'e.g. RH-4420.' } }, required: ['partNumber'] },
    handler: handlers.checkPartsInventory,
  },
  {
    name: 'list_my_work_orders',
    description: 'Lists work orders assigned to the signed-in caller (all work orders for a manager login, only their own for a technician login).',
    inputSchema: { type: 'object', properties: {} },
    handler: handlers.listMyWorkOrders,
  },
  {
    name: 'get_work_order',
    description: 'Gets a single work order by id.',
    inputSchema: { type: 'object', properties: { workOrderId: { type: 'string' } }, required: ['workOrderId'] },
    handler: handlers.getWorkOrder,
  },
  {
    name: 'get_units_by_component_supplier',
    description: 'Lists live fleet units that use a component from a given supplier (e.g. "Ridgeback Hydraulics", "Pinnacle Hose & Seal"), with each unit\'s fault counts. Use this alongside the knowledge base to cross-check a supplier or component question against the live fleet.',
    inputSchema: { type: 'object', properties: { supplier: { type: 'string' } }, required: ['supplier'] },
    handler: handlers.getUnitsByComponentSupplier,
  },
  {
    name: 'get_fault_history',
    description: 'Gets the live logged fault-code history for a specific unit.',
    inputSchema: { type: 'object', properties: { unitId: { type: 'string' } }, required: ['unitId'] },
    handler: handlers.getFaultHistory,
  },
  {
    name: 'get_service_history',
    description: 'Gets the live service/maintenance history for a specific unit (dates, technicians, work performed).',
    inputSchema: { type: 'object', properties: { unitId: { type: 'string' } }, required: ['unitId'] },
    handler: handlers.getServiceHistory,
  },
  {
    name: 'get_inspection_status',
    description: 'Gets a single unit\'s current safety-inspection / tilt-sensor clearance status. Returns whether that specific unit has a completed inspection on file.',
    inputSchema: { type: 'object', properties: { unitId: { type: 'string' } }, required: ['unitId'] },
    handler: handlers.getInspectionStatus,
  },
  {
    name: 'list_fleet_inspection_status',
    description: 'Gets a fleet-wide SUMMARY of safety-inspection completion (counts of units cleared vs. not yet inspected). Does NOT return a single fleet-wide roadworthy yes/no verdict, because no such verdict exists in the system of record - some units are always individually pending.',
    inputSchema: { type: 'object', properties: {} },
    handler: handlers.listFleetInspectionStatus,
  },
];

const TOOL_BY_NAME = new Map(TOOL_DEFS.map((t) => [t.name, t]));

function toolsListPayload() {
  return TOOL_DEFS.map(({ name, description, inputSchema }) => ({ name, description, inputSchema }));
}

function jsonRpcResult(id, result) {
  return { jsonrpc: '2.0', id, result };
}
function jsonRpcError(id, code, message) {
  return { jsonrpc: '2.0', id, error: { code, message } };
}

router.post('/mcp', async (req, res) => {
  const { jsonrpc, id, method, params } = req.body || {};
  if (jsonrpc !== '2.0' || !method) {
    return res.status(400).json(jsonRpcError(id ?? null, -32600, 'Invalid JSON-RPC 2.0 request.'));
  }

  if (method === 'initialize') {
    return res.json(jsonRpcResult(id, {
      protocolVersion: '2024-11-05',
      serverInfo: { name: 'operator-fleet-mcp', version: '1.0.0' },
      capabilities: { tools: {} },
    }));
  }

  if (method === 'tools/list') {
    return res.json(jsonRpcResult(id, { tools: toolsListPayload() }));
  }

  if (method === 'tools/call') {
    const rawName = params?.name;
    const name = stripAgentSuffix(rawName);
    const tool = TOOL_BY_NAME.get(name);
    if (!tool) {
      return res.json(jsonRpcError(id, -32601, `Unknown tool "${rawName}" (resolved "${name}").`));
    }
    // The RBAC identity is the CALLER's own JWT, forwarded by the ARAG agent
    // node (configured to forward the "authorization" header) - never a
    // service credential. No forwarded/valid token = no data, same as the UI.
    const user = userFromAuthHeader(req.headers.authorization);
    try {
      const result = tool.handler(user, params?.arguments || {});
      return res.json(jsonRpcResult(id, {
        content: [{ type: 'text', text: JSON.stringify(result) }],
      }));
    } catch (err) {
      const status = err instanceof HandlerError ? err.status : 500;
      // Surface as a normal (non-error-envelope) tool result with isError, so
      // the agent can reason about "no data" / "not authorised" instead of
      // the call hard-failing - but never fabricate a result in its place.
      return res.json(jsonRpcResult(id, {
        content: [{ type: 'text', text: JSON.stringify({ error: err.message, status }) }],
        isError: true,
      }));
    }
  }

  return res.json(jsonRpcError(id, -32601, `Unknown method "${method}".`));
});
