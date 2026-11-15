// Shared T0 loaders, memoised per page load. Failure rejects so each surface shows its own retry.
import { getJSON } from './api.js';
import { state } from './state.js';
const memo = new Map();
function once(key, fn) { if (!memo.has(key)) memo.set(key, fn().catch((e) => { memo.delete(key); throw e; })); return memo.get(key); }
export const lensData = () => once('lens', () => getJSON('/api/lens', { label: 'lens' }));
export const catalogue = (lens = state.lens) => once('cat:' + (lens || ''), () => getJSON('/api/catalogue' + (lens ? `?lens=${lens}` : ''), { label: 'catalogue' }));
export const revealData = () => once('reveal', () => getJSON('/api/reveal', { label: 'reveal' }));
export function groupByKind(assets) {
  const m = new Map();
  for (const a of assets) { if (!a.kind) continue; if (!m.has(a.kind)) m.set(a.kind, []); m.get(a.kind).push(a); }
  return m;
}
