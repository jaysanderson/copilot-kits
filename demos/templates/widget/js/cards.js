import { h, KINDS, DOC_ICON, PLAY_ICON, fmtMs, fmtN, utcStamp, VERTICALS, STAGES } from './util.js';
import { summarise, isArith } from './state.js';
import { plain } from './md.js';

// Latency readout: reads ONLY what the server's _trace carried. Never prints a figure it did not receive.
// Every path declares a next_action in /api/lens; it renders as sent (label and href), never hardcoded copy.
export function nextAction(l, cls = 'next-action') {
  const a = l && l.next_action; if (!a || !a.label || !a.href) return null;
  const ext = (a.kind === 'external' || a.kind === 'contact') && /^https:\/\//.test(a.href);
  if (!(ext || (a.kind === 'internal' && String(a.href).startsWith('/')))) return null;
  return h('p', { class: cls }, h('a', { class: 'btn btn-sm btn-line', href: a.href, ...(ext ? { target: '_blank', rel: 'noopener noreferrer' } : {}) }, a.label));
}
// Shown verbatim on /pricing and /fit (lead ruling): the published pricing page does not say which plan includes the agentic features the rest of this site demonstrates.
export const TIER_NOTE = "Progress's published pricing page lists RAG and Q&A for Starter, and does not say which plan includes the Retrieval Agent, MCP tool calling or knowledge graphs. Confirm with Progress before buying on that basis.";
export const tierNote = () => h('p', { class: 'tier-note', role: 'note' }, TIER_NOTE);
export function readout(rows, { extra = [] } = {}) {
  const p = h('p', { class: 'readout', 'aria-label': 'Timing for this result' });
  if (!rows || !rows.length) return p;
  const s = summarise(rows.filter((r) => !r.replayed));
  const seg = [];
  const replays = rows.filter((r) => r.replayed);
  // CONTRACT-FIELDS-05 s10: a replay's rows describe the ORIGINAL call, not a call this visit made. They count as zero generative calls here and are
  // labelled as the original, replayed - never as a retrieval or a generation that just happened.
  const replaySeg = () => (replays.length ? [(() => { const r = replays[0]; const st = utcStamp(r.generated_at || r.stamp); return h('span', {}, 'earlier result replayed', st ? ` · answered ${st}` : ''); })()] : []);
  if (replays.length && replays.length === rows.length) {
    replaySeg().forEach((n, i) => { if (i) p.append(h('span', { 'aria-hidden': 'true' }, '·')); p.append(n); });
    for (const e of extra) if (e) p.append(h('span', { 'aria-hidden': 'true' }, '·'), h('span', {}, e));
    return p;
  }
  if (rows.length && rows.every(isArith)) {
    const t = fmtMs(rows.reduce((a, r) => a + (typeof r.ms === 'number' ? r.ms : 0), 0));
    p.append(h('span', {}, t ? h('b', {}, t) : '', t ? ' · ' : '', 'calculated on the server · no model'));
    return p;
  }
  const cw = s.warm || (s.hit && s.hit.stamp ? s.hit : null);
  if (cw) {
    const st = utcStamp(cw.stamp);
    // served_from is the ONLY source for these labels (never inferred): a pre-computed answer is not a live generation, and its timing says so.
    const label = ({ memory: 'pre-computed', 'cache-replay': 'earlier result replayed' })[cw.served_from] || 'pre-computed';
    seg.push(h('span', {}, label, st ? ` · answered ${st}` : ''));
  } else if (s.gen.length) {
    if (s.gen.some((g) => g.served_from === 'knowledge-box')) seg.push(h('span', {}, 'live call'));
    for (const g of s.gen) seg.push(h('span', {}, 'generated', fmtMs(g.ms) ? ` · ${fmtMs(g.ms)}` : ''));
    if (s.ret.length && fmtMs(s.retMs)) seg.push(h('span', {}, h('b', {}, fmtMs(s.retMs)), ' retrieval'));
  } else {
    if (s.hit) seg.push(h('span', {}, 'earlier result'));
    const t = fmtMs(s.retMs);
    seg.push(h('span', {}, t ? h('b', {}, t) : '', t ? ' · ' : '', 'retrieval only'));
  }
  if (!cw) replaySeg().forEach((n) => seg.push(n));
  for (const e of extra) if (e) seg.push(h('span', {}, e));
  seg.forEach((n, i) => { if (i) p.append(h('span', { 'aria-hidden': 'true' }, '·')); p.append(n); });
  return p;
}

// Images: the first few on a page load EAGERLY (a reviewer screenshotting must never see cards the browser had not got round to),
// the rest lazily. A failed load is retried ONCE; only then does the card fall back, to a DESIGNED text-first state
// (kind chip in the body), never to the residue of a removed element.
let eager = 8;
document.addEventListener('routing', () => { eager = 8; });
function loadImg(src, onFail) {
  const lazy = eager-- <= 0;
  const img = h('img', { src, alt: '', loading: lazy ? 'lazy' : 'eager', decoding: 'async' });
  let tried = false;
  img.addEventListener('error', () => { if (!tried) { tried = true; img.src = src + (src.includes('?') ? '&' : '?') + 'retry=1'; } else onFail(); });
  return img;
}
// No thumbnail exists for an asset => render NONE. A flat gradient-and-icon placeholder is a named FAIL; the card is text-first instead.
export function thumb(a, { onFail } = {}) {
  if (!a.thumb) return null;
  const t = h('div', { class: 'thumb' });
  t.append(loadImg(a.thumb, () => { t.remove(); onFail && onFail(); }));
  if (KINDS[a.kind]) t.append(h('span', { class: 'kind tagk' }, KINDS[a.kind]));
  return t;
}
const ext = (href) => (/^https?:/.test(href || '') ? { target: '_blank', rel: 'noopener noreferrer' } : {});
const meta = (a) => [VERTICALS[a.vertical], STAGES[a.stage], a.format && String(a.format).toUpperCase()].filter(Boolean).join(' · ');

// Catalogue/explore card: bound to one real asset. Excerpt = the resource's OWN opening (summary), not a query fragment.
export function assetCard(a, { onOpen, hrefOpen = false } = {}) {
  const chip = !a.thumb && KINDS[a.kind] ? h('span', { class: 'kind' }, KINDS[a.kind]) : null;
  const body = h('div', { class: 'body' }, chip, langTag(a), h('h4', {}, a.title || ''), a.excerpt ? h('p', {}, plain(a.excerpt)) : null, meta(a) ? h('span', { class: 'meta' }, meta(a)) : null);
  const c = h(onOpen ? 'button' : 'a', { class: 'card' + (a.thumb ? '' : ' noimg'), ...(onOpen ? { type: 'button' } : { href: a.href || '#', ...ext(a.href) }) }, thumb(a, { onFail: () => KINDS[a.kind] && body.prepend(h('span', { class: 'kind' }, KINDS[a.kind])) }), body);
  if (onOpen) c.addEventListener('click', () => onOpen(a));
  return c;
}
// Typeahead / recommendation card (retrieval result). `why` names the retrieval basis.
export function hitCard(a, i = 0) {
  const c = h('a', { class: 'rcard', href: a.href || '#', ...ext(a.href), style: `animation-delay:${i * 30}ms` },
    KINDS[a.kind] ? h('span', { class: 'kind' }, KINDS[a.kind]) : null, langTag(a),
    h('h3', {}, a.title || ''),
    a.excerpt ? h('p', {}, plain(a.excerpt)) : null,
    a.why ? h('span', { class: 'mono', style: 'color:#3D3D42' }, a.why) : null);
  return c;
}
export function filmTile(a) {
  const t = h('a', { class: 'film', href: a.href || '#', ...ext(a.href) });
  if (a.thumb) t.append(loadImg(a.thumb, () => t.classList.add('nothumb')));  // designed state: title on navy, chosen not left behind
  // A play glyph is an affordance: it appears ONLY when the film carries a playable media_url. No dead affordance.
  if (a.media_url) t.append(h('span', { class: 'play', html: PLAY_ICON }));
  t.append(h('span', { class: 'cap' }, a.title || ''));
  return t;
}
export const langTag = (x) => (x && x.language_differs === true && typeof x.language === 'string' && x.language ? h('span', { class: 'lang-tag' }, x.language) : null);
// A horizontal rail with a visible way to scroll: prev/next buttons and a right-edge fade that appears ONLY while more is hidden.
export function rail(...cards) {
  const el = h('div', { class: 'rail' }, ...cards);
  const upd = () => { el.classList.toggle('more', el.scrollLeft + el.clientWidth < el.scrollWidth - 6); el.classList.toggle('back', el.scrollLeft > 6); };
  el.addEventListener('scroll', upd, { passive: true }); new ResizeObserver(upd).observe(el); queueMicrotask(upd);
  const nav = h('span', { class: 'rail-nav' },
    h('button', { type: 'button', 'aria-label': 'Scroll back', onclick: () => el.scrollBy({ left: -el.clientWidth * 0.8, behavior: 'smooth' }) }, '←'),
    h('button', { type: 'button', 'aria-label': 'Scroll forward', onclick: () => el.scrollBy({ left: el.clientWidth * 0.8, behavior: 'smooth' }) }, '→'));
  return { el, nav };
}
export function countBadge(n) { return h('span', { class: 'count' }, fmtN(n) ?? ''); }
// Visible failure state with a working retry (every failure path gets one).
export function failState(msg, retry) {
  const d = h('div', { class: 'stat', role: 'alert' }, h('p', { style: 'margin:0' }, msg || 'That did not come back in time.'));
  if (retry) d.append(h('button', { class: 'btn btn-line btn-sm retry', type: 'button', onclick: retry }, 'Try again'));
  return d;
}
export function skeleton(n = 3) { return h('div', { 'aria-busy': 'true' }, ...Array.from({ length: n }, () => h('div', { class: 'sk', style: 'margin:10px 0;width:' + (60 + Math.random() * 35 | 0) + '%' }))); }
