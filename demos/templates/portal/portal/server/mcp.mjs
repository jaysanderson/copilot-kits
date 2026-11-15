// ─────────────────────────────────────────────────────────────────────────────
// Module 4.3 (flagship rebuild) — the app's own /mcp exposure, so ARAG's
// Retrieval Agent (RAO) can call back OUT to this app as its tool source.
// Packaged from the rao-workflow skill's proven Build step 1 pattern — not new
// discovery, this is the skill's own verified code, made reusable.
//
// ARAG namespaces every tool name it calls with a trailing agent-uuid suffix
// (`<tool>__<uuid>`) — this is a literal Hyperforge internal constant
// (`hyperforge_smart/agent.py`'s TOOL_NAME_SEPARATOR = "__"), not an
// ARAG-specific quirk. Strip it before matching or every call 404s.
// ─────────────────────────────────────────────────────────────────────────────

const UUID_SUFFIX = /__[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

export function stripAgentSuffix(name) {
  return String(name || '').replace(UUID_SUFFIX, '');
}

/**
 * Registers a stateless JSON-RPC 2.0 "Streamable HTTP" MCP endpoint at the
 * given path (default `/mcp`) on an Express app.
 *
 * `tools` is a map of `{ [toolName]: { description, inputSchema, handler } }`.
 * `handler(args, { authorization }) -> Promise<any>` — every call dispatches
 * back through the app's OWN REST/business logic (never a second DB path), so
 * auth/RBAC/validation stay uniform between the human UI and the agent — the
 * rao-workflow skill's idea #2. The caller's bearer is forwarded through
 * unchanged; an unauthenticated call on a protected tool should return
 * whatever 401 the underlying handler already returns for the human path.
 */
export function registerMcpServer(app, { path = '/mcp', tools = {} } = {}) {
  app.post(path, async (req, res) => {
    const { jsonrpc = '2.0', id = null, method, params } = req.body || {};
    const authorization = req.headers.authorization || '';

    const reply = (result) => res.json({ jsonrpc, id, result });
    const error = (code, message) => res.json({ jsonrpc, id, error: { code, message } });

    try {
      if (method === 'initialize') {
        return reply({ protocolVersion: '2024-11-05', capabilities: { tools: {} }, serverInfo: { name: 'flagship-demo-mcp', version: '1.0.0' } });
      }
      if (method === 'tools/list') {
        return reply({
          tools: Object.entries(tools).map(([name, t]) => ({
            name,
            description: t.description || '',
            inputSchema: t.inputSchema || { type: 'object', properties: {} },
          })),
        });
      }
      if (method === 'tools/call') {
        const rawName = params?.name || '';
        const name = stripAgentSuffix(rawName);
        const tool = tools[name];
        if (!tool) return error(-32601, `Unknown tool: ${rawName} (stripped: ${name})`);
        const result = await tool.handler(params?.arguments || {}, { authorization });
        return reply({ content: [{ type: 'text', text: JSON.stringify(result) }], isError: false });
      }
      return error(-32601, `Unknown method: ${method}`);
    } catch (err) {
      // A 401/403 the underlying handler threw is real RBAC working correctly
      // — surface it as a tool error, not a 500, so the agent's trace shows an
      // honest failure rather than a transport crash.
      return error(-32000, err.message || 'Tool call failed');
    }
  });
}
