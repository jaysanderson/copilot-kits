// Small DOM + formatting helpers. Explicit maps only: an unknown value renders NOTHING (never a default).
// Element.replaceChildren/append/prepend turn a null or false argument into the visible text "null"/"false". Several surfaces pass
// `cond ? node : null`; drop empty arguments here, once, so no call site can print a literal null.
for (const m of ['replaceChildren', 'append', 'prepend']) {
  const orig = Element.prototype[m];
  Element.prototype[m] = function (...nodes) { return orig.apply(this, nodes.flat().filter((x) => x != null && x !== false)); };
}
export const $ = (s, r = document) => r.querySelector(s);
export const $$ = (s, r = document) => [...r.querySelectorAll(s)];
export function h(tag, attrs = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === 'class') e.className = v;
    else if (k === 'html') e.innerHTML = v;
    else if (k.startsWith('on') && typeof v === 'function') e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v === true ? '' : v);
  }
  for (const c of kids.flat()) if (c != null && c !== false) e.append(c.nodeType ? c : document.createTextNode(String(c)));
  return e;
}
export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
export const KINDS = { film: 'Film', deck: 'Deck', document: 'Document', whitepaper: 'Whitepaper', guide: 'Guide', demo: 'Demo', podcast: 'Podcast', calculator: 'Calculator', reference: 'Reference' };
export const KIND_PLURAL = { film: 'Films', deck: 'Decks', document: 'Documents', whitepaper: 'Whitepapers', guide: 'Guides', demo: 'Demos', podcast: 'Podcasts', calculator: 'Calculators', reference: 'References' };
export const STAGES = { awareness: 'Awareness', discovery: 'Discovery', 'business-case': 'Business case', technical: 'Technical', delivery: 'Delivery' };
export const VERTICALS = { 'cross-industry': 'Cross-industry', 'government-research': 'Government and research', manufacturing: 'Manufacturing', automotive: 'Automotive', 'dxp-retail': 'Digital experience and retail', insurance: 'Insurance', 'financial-services': 'Financial services', media: 'Media', 'professional-services': 'Professional services', associations: 'Associations', logistics: 'Logistics', 'tourism-hospitality': 'Tourism and hospitality' };
export const LENSES = { build: 'Build with it', buy: 'Bring it in', research: 'Research with it', partner: 'Deliver it' };
export const LABELSETS = { journey: ['Path', LENSES], stage: ['Stage', STAGES], vertical: ['Industry', VERTICALS], kind: ['Type', KINDS] };
export const fmtMs = (ms) => (typeof ms !== 'number' ? null : ms >= 1000 ? (ms / 1000).toFixed(1) + ' s' : Math.round(ms) + ' ms');
export const fmtN = (n) => (typeof n === 'number' ? n.toLocaleString('en-AU') : null);
export function utcStamp(iso) {
  const d = new Date(iso); if (isNaN(d)) return null;
  return d.toISOString().slice(11, 16) + ' UTC';
}
export const debounce = (fn, ms) => { let t; const f = (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; f.cancel = () => clearTimeout(t); return f; };
export const SEARCH_ICON = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>';
export const DOC_ICON = '<svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"><path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/></svg>';
export const PLAY_ICON = '<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
