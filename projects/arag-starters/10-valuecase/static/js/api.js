// Thin fetch wrapper. Every call carries the httpOnly session cookie
// automatically (same-origin); a 401 anywhere means the passphrase gate
// needs to show again, never a silent failure.
export class AuthError extends Error {}

async function call(method, path, body) {
  const res = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    credentials: "same-origin",
  });
  if (res.status === 401) throw new AuthError("Not authenticated");
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = j.detail || detail;
    } catch (e) {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res.blob();
}

// Per-case write queue (demo-tester finding 2, 22 Sep 2026): three rapid
// saves against the same case could previously resolve out of order and
// let an earlier response's local-state update stomp a later one. Every
// mutating call for a given case id is chained onto that case's own
// promise, so writes to one case run strictly in the order they were
// initiated - never concurrently, never out of order. Different cases
// queue independently (a seller working two tabs on two different
// accounts sees no cross-case slowdown).
const writeQueues = new Map();
function enqueueWrite(caseId, task) {
  const prior = writeQueues.get(caseId) || Promise.resolve();
  const settled = prior.then(task, task);
  writeQueues.set(caseId, settled.catch(() => {})); // keep the chain alive even if a write fails
  return settled;
}

export const api = {
  login: (passphrase) => call("POST", "/api/login", { passphrase }),
  logout: () => call("POST", "/api/logout"),
  session: () => call("GET", "/api/session"),
  listCases: () => call("GET", "/api/cases"),
  createCase: (account_name, seller_name) => call("POST", "/api/cases", { account_name, seller_name }),
  getCase: (id) => call("GET", `/api/cases/${id}`),
  updateCase: (id, fields) => enqueueWrite(id, () => call("PUT", `/api/cases/${id}`, fields)),
  deleteCase: (id) => call("DELETE", `/api/cases/${id}`),
  putInput: (id, leverId, inputKey, body) =>
    enqueueWrite(id, () => call("PUT", `/api/cases/${id}/levers/${leverId}/inputs/${inputKey}`, body)),
  putOwner: (id, leverId, body) => enqueueWrite(id, () => call("PUT", `/api/cases/${id}/levers/${leverId}/owner`, body)),
  compute: (id) => call("POST", `/api/cases/${id}/compute`),
  exportUrl: (id, kind) => `/api/cases/${id}/export/${kind}`,
  purge: (passphrase) => call("POST", "/api/admin/purge", { passphrase }),
};
