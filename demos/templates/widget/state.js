// Session state (memory only). The lens lives in the URL (?lens=) so a state is reachable by link.
// The calls a VISITOR starts. Every other recorded call (catalogue, lens, pricing, the example, pillar films, reference lookups...) is the page loading
// itself and must never be described as the visitor's last action.
export const VISITOR_LABELS = new Set(['Answer', 'Typeahead', 'Search', 'Recommendations', 'Related trail', 'Build: live search', 'Value model']);
export const state = { lastHistory: null, withheld: [], filmPlayed: false, lens: null, traces: [], last: null, asks: 0, bootCache: {} };
const subs = new Set();
// Arithmetic is neither retrieval nor cached: the server labels it (verb 'calculated' / endpoint 'arithmetic'); the client reads the label.
export const isArith = (r) => !!r && (r.verb === 'calculated' || r.endpoint === 'arithmetic');
export const subscribe = (f) => (subs.add(f), () => subs.delete(f));
export const emit = () => subs.forEach((f) => f());
export function setLens(l) { state.lens = ['build', 'buy', 'research', 'partner'].includes(l) ? l : null; emit(); }
export function recordTrace(label, trace) {
  const rows = trace.filter((r) => r && typeof r === 'object');
  const entry = { label, at: new Date().toISOString(), rows };
  if (label === 'Recommendations' && state.last && state.last.label === 'Answer' && Date.now() - state.last.t < 60000) { state.last.rows = state.last.rows.concat(rows); state.traces.push(entry); emit(); return; }
  entry.t = Date.now();
  state.traces.push(entry); if (state.traces.length > 60) state.traces.shift();
  if (VISITOR_LABELS.has(label)) state.last = entry;
  emit();
}
// Summaries for the readout: only what the server's _trace carried.
export function summarise(rows) {
  const gen = rows.filter((r) => r.generative);
  const ret = rows.filter((r) => !r.generative);
  const retMs = ret.reduce((a, r) => a + (typeof r.ms === 'number' ? r.ms : 0), 0);
  return { gen, ret, retMs, warm: rows.find((r) => r.cache === 'warm'), hit: rows.find((r) => r.cache === 'hit') };
}
