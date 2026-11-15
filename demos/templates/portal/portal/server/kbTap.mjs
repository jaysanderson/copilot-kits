// ─────────────────────────────────────────────────────────────────────────────
// KB-source tap (Standard B26, GM review 18 Aug 2026).
//
// The Claims Copilot's Retrieval Agent now blends STRUCTURED live data (its MCP
// data tools) with UNSTRUCTURED retrieval (the knowledge box), and the surface
// must show BOTH. ARAG calls the app's own `search_claim_documents` MCP tool
// server-side; that handler records the document passages it grounded on here,
// and the RAO proxy (server/rao.mjs) drains them at the end of the session and
// emits them to the UI as `kb_sources`.
//
// Correlation is by time window, not a per-user token: this demo has no login
// so the forwarded authorization is empty for every viewer, which makes a
// token key useless. The MCP tool callbacks for one session all land between
// the session's start and its end, so draining entries recorded since the
// session began captures exactly this session's KB retrievals for the common
// single-reviewer demo case - far more reliable than parsing UUIDs out of the
// agent's truncated trace text.
// ─────────────────────────────────────────────────────────────────────────────

const BUFFER = [];
const MAX_AGE_MS = 3 * 60 * 1000;

function prune(now) {
  while (BUFFER.length && now - BUFFER[0].ts > MAX_AGE_MS) BUFFER.shift();
}

/** The MCP KB-search handler calls this with the passages it retrieved. */
export function recordKbSources(sources) {
  if (!Array.isArray(sources) || !sources.length) return;
  const now = Date.now();
  prune(now);
  BUFFER.push({ ts: now, sources });
}

/** The RAO proxy calls this at session end with the session's start time. */
export function drainKbSources(sinceTs) {
  const now = Date.now();
  prune(now);
  const seen = new Set();
  const out = [];
  for (const entry of BUFFER) {
    if (entry.ts < sinceTs) continue;
    for (const s of entry.sources) {
      if (!s || !s.resourceId || seen.has(s.resourceId)) continue;
      seen.add(s.resourceId);
      out.push(s);
    }
  }
  return out;
}
