import { h, $, LENSES, fmtN, fmtMs, utcStamp } from './util.js';
import { state, setLens, subscribe, isArith, VISITOR_LABELS } from './state.js';
import { getJSON } from './api.js';
import { render, renderInline, plain } from './md.js';
import { TRIAL } from './trial.js';

export const SIGNUP = TRIAL.url;
const NAV = [['/explore', 'Explore'], ['/watch', 'Films'], ['/build', 'Build'], ['/fix', 'Fix answers'], ['/pricing', 'Pricing'], ['/fit', 'Where it fits']];
const FLOW = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="12" r="2"/><circle cx="19" cy="6" r="2"/><circle cx="19" cy="18" r="2"/><path d="M7 12h4l6-5M11 12l6 5"/></svg>';

export function mountTopbar() {
  const root = $('#topbar-root');
  const sheet = h('nav', { class: 'sheet', id: 'sheet', 'aria-label': 'Menu' },
    ...NAV.map(([p, l]) => h('a', { class: 'l', href: p }, l)), h('a', { class: 'l', href: '/embed' }, 'Embed'),
    h('a', { class: 'btn btn-primary', style: 'margin-top:16px;justify-content:center', href: SIGNUP, target: '_blank', rel: 'noopener noreferrer', 'data-trial-cta': '' }, TRIAL.cta));
  const menu = h('button', { class: 'btn btn-ghost menu-btn', type: 'button', 'aria-label': 'Menu', 'aria-expanded': 'false', 'aria-controls': 'sheet' }, h('span', { html: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>' }));
  menu.addEventListener('click', () => { const o = sheet.classList.toggle('open'); menu.setAttribute('aria-expanded', o); });
  sheet.addEventListener('click', (e) => { if (e.target.closest('a')) { sheet.classList.remove('open'); menu.setAttribute('aria-expanded', 'false'); } });
  const nav = h('nav', { class: 'nav', 'aria-label': 'Primary' }, ...NAV.map(([p, l]) => h('a', { href: p, 'data-nav': p }, l)));
  const reveal = h('button', { class: 'btn btn-ghost btn-reveal', type: 'button', 'aria-haspopup': 'dialog' }, h('span', { html: FLOW }), h('span', { class: 't' }, 'How this works'));
  reveal.setAttribute('aria-label', 'How this works');
  reveal.addEventListener('click', openReveal);
  root.append(h('header', { class: 'topbar' }, h('div', { class: 'wrap' },
    h('a', { class: 'logo', href: '/', 'aria-label': 'Progress Agentic RAG - home' }, h('img', { src: '/img/primary-horizontal-alternate.svg', alt: 'Progress Agentic RAG', width: 241, height: 28, id: 'logo-img' })),
    nav, h('span', { class: 'spacer' }), reveal,
    h('a', { class: 'btn btn-primary cta', href: SIGNUP, target: '_blank', rel: 'noopener noreferrer' }, TRIAL.short), menu)), sheet);
}
export function markNav(path) { document.querySelectorAll('[data-nav]').forEach((a) => (a.getAttribute('data-nav') === path ? a.setAttribute('aria-current', 'page') : a.removeAttribute('aria-current'))); }

export function lensChips({ onChange } = {}) {
  const box = h('div', { class: 'chips', role: 'group', 'aria-label': 'Choose a path' });
  const draw = () => {
    box.replaceChildren(...Object.entries(LENSES).map(([id, label]) => {
      const b = h('button', { class: 'chip', type: 'button', 'aria-pressed': String(state.lens === id) }, label);
      b.addEventListener('click', () => { setLens(state.lens === id ? null : id); const u = new URL(location.href); state.lens ? u.searchParams.set('lens', state.lens) : u.searchParams.delete('lens'); u.searchParams.delete('journey'); history.replaceState(null, '', u); onChange && onChange(); window.dispatchEvent(new Event('lenschange')); });
      return b;
    }));
  };
  draw(); const un = subscribe(() => { if (!box.isConnected) un(); else draw(); });
  return box;
}
// Honest personalisation line: states only what the visitor DID (chose a path), never an inferred identity.
export function lensNote() {
  const p = h('p', { class: 'lens-note' });
  const draw = () => { p.textContent = state.lens ? `Showing the ${LENSES[state.lens]} path because you chose it. Choose it again to see everything.` : 'No path chosen: showing everything, in neutral order.'; };
  draw(); const un = subscribe(() => { if (!p.isConnected) un(); else draw(); });
  return p;
}
export function mountLensbar(show) {
  const root = $('#lensbar-root'); root.replaceChildren();
  if (!show) return;
  root.append(h('div', { class: 'lensbar' }, h('div', { class: 'wrap' }, h('span', { class: 'lbl' }, 'Path:'), lensChips())));
}
export function mountFooter() {
  $('#footer-root').replaceChildren(h('div', { class: 'wrap' }, h('div', { class: 'cols' },
    h('div', {}, h('img', { src: '/img/primary-horizontal-alternate.svg', alt: 'Progress Agentic RAG', height: 28, style: 'height:28px;width:auto;margin-bottom:14px' }),
      h('p', {}, 'This site is a live Progress Agentic RAG knowledge box. Every search result, answer and recommendation is a real call, and the timings you see are measured.')),
    h('div', { class: 'links' }, ...NAV.map(([p, l]) => h('a', { href: p }, l)), h('a', { href: '/embed' }, 'Embed'), h('a', { href: SIGNUP, target: '_blank', rel: 'noopener noreferrer', 'data-trial-cta': '' }, TRIAL.cta))),
    h('p', { style: 'margin-top:28px;font-size:13px' }, 'Copyright © 2026 Progress Software Corporation and/or its subsidiaries or affiliates. All rights reserved.')));
}

// ---- How this works: a composed trace of THIS visitor's last interaction ----
let revealCache = null;
export async function openReveal() {
  const root = $('#modal-root'); const opener = document.activeElement;
  const body = h('div', {}, h('p', {}, 'Loading...'));
  const close = () => { root.replaceChildren(); document.body.style.overflow = ''; opener && opener.focus && opener.focus(); document.removeEventListener('keydown', esc); };
  const esc = (e) => { if (e.key === 'Escape') close(); };
  const x = h('button', { class: 'x', type: 'button', 'aria-label': 'Close', onclick: close }, '×');
  const dlg = h('div', { class: 'dialog', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'rv-t' }, x, h('h2', { id: 'rv-t' }, 'How this works'), body);
  const ov = h('div', { class: 'overlay' }, dlg); ov.addEventListener('mousedown', (e) => { if (e.target === ov) close(); });
  root.replaceChildren(ov); document.body.style.overflow = 'hidden'; document.addEventListener('keydown', esc); x.focus();
  try { revealCache = revealCache || await getJSON('/api/reveal', { label: 'reveal' }); } catch { revealCache = null; }
  body.replaceChildren(...revealBody(revealCache));
}
const SENT = { Answer: 'your question', Typeahead: 'what you typed', Search: 'a search', 'Related trail': 'a request for related items', Recommendations: 'a request for similar items', 'Pillar film': 'a film lookup', 'Build: live search': 'the live search on the Build page', 'Value model': 'your numbers' };
// served_from (CONTRACT-FIELDS-05) is the ONLY source for "served from memory" / "replayed" / "live call". It is never inferred from "it ran at
// page load". Known values are mapped EXPLICITLY and anything outside the set (including a missing field) renders NO label: a renderer that maps an
// unrecognised value to a default silently mislabels every value added later, and these labels are no-fake claims about our own architecture.
const KIND_BY_SERVED = { memory: 'Served from memory', 'cache-replay': 'Earlier result replayed', 'knowledge-box': null };
const rowKind = (r) => (r.generative ? 'Generative' : isArith(r) ? 'Arithmetic, no model' : r.served_from === 'knowledge-box' ? 'Retrieval only' : (KIND_BY_SERVED[r.served_from] || ''));
const cacheText = (r) => {
  if (isArith(r)) return '';
  if (r.replayed) return `Original call, replayed${utcStamp(r.generated_at) ? ' from ' + utcStamp(r.generated_at) : ''}`;
  if (r.served_from === 'memory') return `Read from memory - no call left this site${utcStamp(r.stamp) ? ', catalogue read ' + utcStamp(r.stamp) : ''}`;
  if (r.served_from === 'cache-replay') return `Replayed from memory - no new call to the platform on this request${utcStamp(r.stamp) ? ', first answered ' + utcStamp(r.stamp) : ''}`;
  if (r.served_from === 'knowledge-box') return 'Live call on this request';
  return '';
};
// Which node of the flow a call belongs to: the platform node lists only calls that really reached it.
const onPlatform = (r) => !isArith(r) && r.served_from !== 'memory' && r.served_from !== 'cache-replay';
function revealBody(R) {
  const last = state.last, out = [];
  out.push(h('p', { style: 'color:#3D3D42;margin:0 0 4px' }, 'The page you are looking at is a thin layer over Progress Agentic RAG. This is what actually happened on your last action.'));
  // flow
  const loads = state.traces.filter((t) => !VISITOR_LABELS.has(t.label)).flatMap((t) => t.rows);
  const rows = last ? last.rows : loads;
  const nodes = [
    h('div', { class: 'node' }, h('h4', {}, 'Your browser'), h('p', {}, last ? (SENT[last.label] ? `Sent: ${SENT[last.label]}` : null) : 'No question or search yet. This page\'s own loads are shown on the right.'), h('p', {}, 'Holds no key and makes no call to the platform.')),
    h('div', { class: 'node' }, h('h4', {}, 'This site\'s own server'), h('p', {}, 'Adds the credentials, applies the path you chose, caches, and checks what an answer is grounded on.'), ...rows.filter((r) => !onPlatform(r)).map((r) => h('p', { class: 'readout', style: 'margin:0' }, h('span', {}, rowKind(r)), r.call ? h('b', {}, r.call) : '', fmtMs(r.ms) ? h('b', {}, fmtMs(r.ms)) : ''))),
    h('div', { class: 'node k' }, h('h4', {}, 'Progress Agentic RAG'), ...(rows.filter(onPlatform).length ? rows.filter(onPlatform).map((r) => h('p', { class: 'readout' }, h('span', {}, rowKind(r)), r.call ? h('b', {}, r.call) : '', r.model ? h('span', {}, r.model) : '', fmtMs(r.ms) ? h('b', {}, fmtMs(r.ms)) : '', cacheText(r) ? h('span', {}, cacheText(r)) : '')) : [h('p', {}, rows.length ? 'No call reached the platform for this.' : 'Nothing has been called yet.')])),
    h('div', { class: 'node' }, h('h4', {}, 'What you see'), h('p', {}, 'Results, an answer with numbered sources, and a support rating shown in words.')),
  ];
  const flow = h('div', { class: 'flow' });
  nodes.forEach((n, i) => { if (i) flow.append(h('span', { class: 'arrow', 'aria-hidden': 'true' }, '→')); flow.append(n); });
  out.push(flow);
  // per call table
  if (rows.length) {
    out.push(h('div', { class: 'sec' }, h('h3', {}, last ? 'Calls behind your last action' : 'Calls made while this page loaded'), h('div', { class: 'tw' }, h('table', { class: 't' },
      h('thead', {}, h('tr', {}, ...['Call', 'Endpoint', 'Kind', 'Model', 'Time', 'Cache'].map((c) => h('th', {}, c)))),
      h('tbody', {}, ...rows.map((r) => h('tr', {}, h('td', { 'data-l': 'Call' }, r.call ?? ''), h('td', { class: 'mono', 'data-l': 'Endpoint' }, r.endpoint ?? ''), h('td', { 'data-l': 'Kind' }, rowKind(r)), h('td', { class: 'mono', 'data-l': 'Model' }, r.model ?? ''), h('td', { class: 'mono', 'data-l': 'Time' }, fmtMs(r.ms) ?? ''), h('td', { 'data-l': 'Cache' }, cacheText(r)))))))));
  }
  if (state.lastHistory && state.last && state.last.label === 'Answer') {
    const H = state.lastHistory;
    out.push(h('div', { class: 'sec' }, h('h3', {}, 'Earlier turns sent with your last question'),
      h('p', { style: 'margin:0' }, H.available === 0 ? 'None: it was the first question, so nothing but the question itself was sent.' : `${H.sent} of ${H.available} earlier ${H.available === 1 ? 'turn' : 'turns'} sent, for writing the answer only. ${H.shortened ? `${H.shortened} ${H.shortened === 1 ? 'answer was' : 'answers were'} shortened to whole sentences. ` : ''}${H.dropped.length ? `${H.dropped.length} not sent.` : ''}`),
      ...(H.dropped.length ? [h('ul', {}, ...H.dropped.map((d) => h('li', {}, h('span', { class: 'mono' }, plain(d.q).slice(0, 90)), ' - ', d.why)))] : []),
      h('p', { style: 'margin:6px 0 0;color:#3D3D42;font-size:14px' }, 'Whether an answer is shown is decided on your question alone; earlier turns never make a thin question answerable. The server applies its own limits to this too and counts anything it trims.')));
  }
  if (state.withheld.length) out.push(h('div', { class: 'sec' }, h('h3', {}, `Answers withheld by this page (${state.withheld.length})`), h('p', { style: 'margin:0 0 6px' }, 'A printed answer whose source record broke its contract is never shown. These were withheld:'), h('ul', {}, ...state.withheld.map((w) => h('li', {}, h('span', { class: 'mono' }, plain(w.q)), ' - ', plain(w.reason))))));
  if (state.filmPlayed) out.push(h('div', { class: 'sec' }, h('h3', {}, 'Film playback'), h('p', { style: 'margin:0' }, 'A film streams from this site\'s own server in byte ranges, so you can seek. Playing a film makes no call to the knowledge box.')));
  const conf = state.lastConfidence;
  if (conf && conf.raw && typeof conf.raw === 'object') out.push(h('div', { class: 'sec' }, h('h3', {}, 'The measured support behind the rating'), h('p', { class: 'mono' }, Object.entries(conf.raw).filter(([, v]) => typeof v === 'number' || typeof v === 'string').map(([k, v]) => `${k.replace(/_/g, ' ')}: ${typeof v === 'number' ? v.toFixed(2) : v}`).join('  ·  ')), h('p', { style: 'color:#3D3D42;margin:6px 0 0' }, `Scored over the full set of ${fmtN(conf.contexts) ?? 'retrieved'} passages retrieved, not just the ones cited. The rating measures how well the wording is supported by those passages, not whether they are correct.`)));
  if (R) {
    const kb = R.knowledge_base || {}, ans = R.answering || {}, lim = R.limits || {};
    const reach = Object.entries(kb.reachable_by_path || {}).filter(([k]) => LENSES[k]);
    out.push(h('div', { class: 'sec two' },
      h('div', {}, h('h3', {}, 'The knowledge box'),
        kb.resources_total != null ? h('p', { class: 'mono', style: 'margin:2px 0' }, `${fmtN(kb.resources_total)} resources in the box`) : null,
        kb.reachable_public != null ? h('p', { class: 'mono', style: 'margin:2px 0' }, `${fmtN(kb.reachable_public)} reachable on this public site`) : null,
        ...reach.map(([k, v]) => h('p', { class: 'mono', style: 'margin:2px 0' }, `${LENSES[k]}: ${fmtN(v)} reachable`)),
        kb.catalogue_read_at ? h('p', { class: 'mono', style: 'margin:6px 0 0' }, `catalogue read ${utcStamp(kb.catalogue_read_at) || ''}`) : null),
      h('div', {}, h('h3', {}, 'Which mechanism does what'), ...(R.mechanisms || []).filter((m) => m.name).map((m) => h('p', { style: 'margin:0 0 8px' }, h('b', {}, m.name + ' '), h('span', { class: 'mono' }, m.generative ? `generative${m.model ? ' · ' + m.model : ''}` : 'retrieval only'), h('br'), m.used_for ? h('span', { html: renderInline(m.used_for) }) : '')))));
    if ((R.tiers || []).length) out.push(h('div', { class: 'sec' }, h('h3', {}, 'Three speeds'), h('div', { class: 'fitgrid' }, ...R.tiers.filter((t) => t.tier && t.what).map((t) => h('div', { class: 'qa' }, h('span', { class: 'kind' }, t.tier), h('p', { style: 'margin:8px 0 0' }, plain(t.what)), t.cache_entries != null ? h('p', { class: 'mono', style: 'margin:6px 0 0' }, `${fmtN(t.cache_entries)} cached queries held`) : null)))));
    if (ans.withheld_server_side) out.push(h('div', { class: 'sec' }, h('h3', {}, 'When it cannot answer'), h('p', { style: 'margin:0' }, `A question the library cannot support is withheld on the server before anything reaches your browser.${typeof (ans.floor || {}).value === 'number' ? ` The support floor is ${ans.floor.value}, measured against this corpus.` : ''}${ans.model_pinned ? ` Written answers use ${ans.model_pinned}, pinned explicitly on every call.` : ''}`)));
    if ((R.not_happening || []).length) out.push(h('div', { class: 'sec' }, h('h3', {}, 'What is not happening'), h('ul', { class: 'no' }, ...R.not_happening.map((t) => h('li', { html: renderInline(t) })))));
    const v = (lim.typed_answers_per_visitor || {});
    if (v.max) out.push(h('p', { class: 'mono', style: 'margin-top:14px' }, `Typed answers are limited to ${fmtN(v.max)} per visitor per ${fmtN(Math.round((v.window_s || 0) / 60))} minutes to keep the cost of a public site honest.`));
  }
  const s = sessionTotals();
  out.push(h('div', { class: 'sec' }, h('h3', {}, 'This visit so far'), h('p', { class: 'mono' }, `${s.ret} retrieval calls · ${s.gen} generative calls · ${s.warm} served from cache`)));
  return out;
}
export function sessionTotals() {
  let ret = 0, gen = 0, warm = 0;
  for (const t of state.traces) for (const r of t.rows) { if (!r.replayed) r.generative ? gen++ : ret++; if (r.cache === 'warm' || r.cache === 'hit' || r.cache === 'replay') warm++; }
  return { ret, gen, warm };
}
