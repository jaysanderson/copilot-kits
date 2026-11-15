import { h, LENSES, KINDS, KIND_PLURAL, fmtN, fmtMs } from '../util.js';
import { state, subscribe, setLens } from '../state.js';
import { mountAsk, renderExample } from '../ask.js';
import { lensChips, lensNote, SIGNUP, sessionTotals } from '../chrome.js';
import { lensData, catalogue, revealData, groupByKind } from '../data.js';
import { getJSON } from '../api.js';
import { TRIAL, loadTrial } from '../trial.js';
import { plain, render } from '../md.js';
import { FIT_SUMMARY } from '../fit-data.js';
import { assetCard, filmTile, failState, countBadge, skeleton, thumb, rail, nextAction } from '../cards.js';

// A chosen path must serve at least this many suggested questions; fewer is a defect that announces itself (console.error fails the QA gate).
const MIN_PATH_CHIPS = 3;
const PILLARS = [
  { n: 'Agentic retrieval, not a chatbot on a vector store', p: 'Agents enrich content as it is ingested, then plan multi-step retrieval at question time, calling your own tools over MCP with the caller\'s permissions applied.', q: 'agentic retrieval agents MCP tools', num: (c, r) => [r?.knowledge_base?.reachable_by_path?.build, 'resources on the Build path'] },
  { n: 'Trust you can measure, per query', p: 'Every answer can be scored for groundedness and context relevance by a purpose-built evaluation model, and is cited back to its sources.', q: 'measure answer quality groundedness evaluation', num: () => [2, 'quality scores shown with every answer: groundedness and context relevance'] },
  { n: 'Scoped at retrieval, not filtered afterwards', p: 'What an answer may be built from is settled before anything is read. Every customer\'s content can live in one shared index, labelled so a filter separates it, and the filter is applied to retrieval rather than to the answer afterwards. This page is doing it right now: the path you are browsing as decides what it can reach.', link: ['/fit#scope', 'See it run'], q: 'scoping who can be answered from what permission aware retrieval', num: () => [3, 'scopes on this site, each a filter over one index'] },
];

export async function mount(main, url) {
  const un = [];
  const hero = h('section', { class: 'hero' });
  const wrap = h('div', { class: 'wrap hero-grid' });
  hero.append(h('div', { class: 'loopbox', 'aria-hidden': 'true' }, h('img', { class: 'loop', src: '/img/hex-loop-rgb.svg', alt: '' })), wrap);
  wrap.append(h('h1', {}, h('span', { style: 'display:block' }, 'Ask the product.'), h('span', { style: 'display:block' }, 'Watch it answer.')),
    h('p', { class: 'sub' }, 'This page runs on the product it is selling. Every search, answer and recommendation is a real call, and each one shows you its sources and the time it took.'));
  const askHost = h('div', {}); const exHost = h('div', { class: 'hero-example', 'aria-label': 'Example answer' }); const strip = h('div', { class: 'hero-strip' }); const right = h('div', { class: 'hero-right' }, exHost, strip); wrap.append(askHost, right);
  const qblock = h('div', { class: 'hero-block' });
  const chipsBlock = h('div', { class: 'hero-block' }, h('h2', {}, 'Choose a path (optional)'), lensChips({ onChange: drawQs }), h('div', { style: 'margin-top:8px' }, lensNote()));
  wrap.append(chipsBlock, qblock);
  if (url.searchParams.get('notice') === 'not-found') { const n = h('p', { class: 'readout', style: 'padding:10px var(--gut);background:var(--blue-soft);color:var(--navy)', role: 'status' }, 'That page is not on this site. You are on the home page instead.'); main.append(n); setTimeout(() => n.remove(), 8000); }
  main.append(hero);

  // First paint never waits on data: the box is usable at once (a visitor who knows what they want must not wait on a demonstration they did
  // not ask for), the example area shows its own quiet state, and everything else fills in as the calls land.
  loadTrial();
  const ask = mountAsk(askHost, { total: null, onAsked: () => hero.classList.add('asked') });
  hero.after(ask.answerHost);
  const q0 = url.searchParams.get('q'); if (q0) ask.ask(q0);
  exHost.classList.add('loading'); exHost.append(h('div', { class: 'ex-quiet', 'aria-hidden': 'true' }, h('div', { class: 'sk' }), h('div', { class: 'sk', style: 'width:80%' }), h('div', { class: 'sk', style: 'width:60%' })));
  const [cat, rev, lenses] = await Promise.all([catalogue().catch(() => null), revealData().catch(() => null), lensData().catch(() => null)]);
  const total = rev?.knowledge_base?.reachable_public ?? cat?.total ?? null;
  if (total != null) ask.setTotal(total);

  // ---- the headline's cheque, cashed: a real answer on arrival, and the library's own evidence under the box ----
  const exQ = lenses && lenses.hero_example && typeof lenses.hero_example.question === 'string' && lenses.hero_example.source !== 'printed' ? lenses.hero_example.question : null;  // a printed hero is refused outright (CONTRACT-FIELDS-05 s7)
  exHost.classList.remove('loading'); exHost.replaceChildren();
  if (exQ) renderExample(exHost, exQ, lenses.hero_example.source || null).then((ok) => { if (!ok) hero.classList.add('no-example'); }); else hero.classList.add('no-example');
  drawStrip(strip, cat);

  // Source of the chips: no path chosen = the server's `suggested` list; a path chosen = ALL of that path's `entry_questions`.
  // The surface must be INCAPABLE of dropping chips silently: after drawing, the DOM is checked against the list it was
  // given, and any shortfall is shown as an error state (and logged), never as a quiet subset.
  const qText = (x) => (typeof x === 'string' ? x : x && (x.q || x.text));
  function wanted() {
    const L = state.lens && lenses?.lenses?.find((x) => x.id === state.lens);
    if (L && Array.isArray(L.entry_questions)) return L.entry_questions.map(qText).filter(Boolean);
    const sug = lenses?.suggested || [];
    return (state.lens ? sug.filter((x) => x.lens === state.lens) : sug).map(qText).filter(Boolean);
  }
  function drawQs() {
    const qs = wanted();
    if (!qs.length) { qblock.replaceChildren(...(lenses ? [] : [failState('The suggested questions did not load.', () => location.reload())])); return; }
    const warmMap = new Map((lenses?.suggested || []).map((x) => [qText(x), x.warm === true]));
    qblock.replaceChildren(h('h2', {}, state.lens ? `Suggested for ${LENSES[state.lens]}` : 'Or start with one of these'),
      h('div', { class: 'qchips', 'data-expected': String(qs.length) }, ...qs.map((q) => h('button', { class: 'qchip', type: 'button', onclick: () => ask.ask(q) }, q, warmMap.get(q) ? h('span', { class: 'tag', title: 'Answered in advance by a real call; the answer shows when' }, 'pre-computed') : null))));
    { const L2 = state.lens && lenses?.lenses?.find((x) => x.id === state.lens); const na = nextAction(L2); if (na) qblock.append(na); }
    const w = (state.withheld || []).filter((x) => qs.includes(x.q)); if (w.length) console.error(`suggested question(s) withheld: ${w.map((x) => x.q).join(' | ')}`);
    if (state.lens && qs.length < MIN_PATH_CHIPS) console.error(`path ${state.lens} serves ${qs.length} suggested questions, under the minimum of ${MIN_PATH_CHIPS}`);
    const drawn = qblock.querySelectorAll('.qchip').length;
    if (drawn !== qs.length) { console.error(`suggested questions: rendered ${drawn} of ${qs.length}`); qblock.replaceChildren(failState(`Only ${drawn} of ${qs.length} suggested questions could be shown.`, drawQs)); }
  }
  drawQs();

  // ---- narrative ----
  const s1 = h('section', { class: 's' }, h('div', { class: 'wrap' }, h('div', { class: 'sh' }, h('p', { class: 'eyebrow' }, 'What it does'), h('h2', {}, 'Three things, shown on this page'), h('p', { class: 'lede' }, 'Each card pairs a capability with a film retrieved for it just now.')), (() => { const g = h('div', { class: 'pillars' }); PILLARS.forEach((P, i) => g.append(pillar(P, i, cat, rev))); return g; })()));
  const s3 = economics();
  const s4 = fitTeaser();
  main.append(s1, s3, s4);
  un.push(subscribe(() => {}));
  return () => { ask.destroy(); un.forEach((f) => f()); };
}

function pillar(P, i, cat, rev) {
  const [num, lbl] = P.num(cat, rev);
  const film = h('div', {}, skeleton(1));
  const el = h('article', { class: 'pillar' }, num != null ? h('div', { class: 'big' }, fmtN(num)) : null, num != null ? h('div', { class: 'biglbl' }, lbl) : null, h('h3', {}, P.n), h('p', {}, P.p), P.link ? h('a', { href: P.link[0], style: 'font-weight:600' }, P.link[1] + ' →') : null, film);
  getJSON(`/api/search?q=${encodeURIComponent(P.q)}&facets=kind:film${state.lens ? '&lens=' + state.lens : ''}`, { label: 'Pillar film' }).then((j) => {
    const a = (j.hits || [])[0];
    film.replaceChildren(...(a ? [filmTile(a), h('p', { class: 'readout', style: 'margin-top:8px' }, 'Closest film by meaning')] : []));
  }).catch(() => film.replaceChildren(failState('The film did not load.', () => { const n = pillar(P, i, cat, rev); el.replaceWith(n); })));
  return el;
}
// The evidence strip: live counts by type, and real previews from the catalogue, picked to span the range (films first, then a demo, a document,
// a deck), never by score. Titles and thumbnails come from the catalogue at run time; a kind with nothing in it is skipped.
function drawStrip(host, cat) {
  if (!cat || !(cat.assets || []).length) return;
  const pool = cat.assets, pick = (k, skip = 0) => pool.filter((a) => a.kind === k && a.thumb)[skip] || (skip ? null : pool.find((a) => a.kind === k));
  const picks = [pick('film'), pick('demo'), pick('document'), pick('film', 1), pick('deck')].filter(Boolean).filter((a, i, arr) => arr.findIndex((b) => b.asset_id === a.asset_id) === i).slice(0, 5);
  const counts = Object.keys(KINDS).filter((k) => cat.facets?.kind?.[k]).map((k) => h('span', { class: 'count-pill' }, h('b', {}, fmtN(cat.facets.kind[k])), ' ' + KIND_PLURAL[k].toLowerCase()));
  const r = rail(...picks.map((a) => { const t = thumb(a); return h('a', { class: 'scard' + (t ? '' : ' noimg'), href: a.href || '/explore' }, t, h('div', { class: 'sbody' }, !t && KINDS[a.kind] ? h('span', { class: 'kind' }, KINDS[a.kind]) : null, h('span', { class: 'stitle' }, a.title))); }));
  host.append(h('div', { class: 'strip-head' }, h('p', { class: 'strip-count' }, h('b', {}, fmtN(cat.total)), ' assets you can ask across'), h('div', { class: 'strip-pills' }, ...counts), r.nav, h('a', { class: 'strip-all', href: '/explore' }, `Browse all ${fmtN(cat.total)} →`)), r.el);
}
function economics() {
  const figs = { ret: h('div', { class: 'fig' }, '-'), gen: h('div', { class: 'fig' }, '-'), warm: h('div', { class: 'fig' }, '-') };
  const draw = () => { const s = sessionTotals(); figs.ret.textContent = fmtN(s.ret); figs.gen.textContent = fmtN(s.gen); figs.warm.textContent = fmtN(s.warm); };
  draw(); subscribe(() => { if (figs.ret.isConnected) draw(); });
  const t = (code, title, body, f, unit) => h('div', { class: 'tier' }, h('span', { class: 't' }, code), h('h3', {}, title), h('p', {}, body), f, h('span', { class: 't' }, unit));
  return h('section', { class: 's' }, h('div', { class: 'wrap' }, h('div', { class: 'sh' }, h('p', { class: 'eyebrow' }, 'The economics'), h('h2', {}, 'Retrieval first. Writing only when you ask in words.'), h('p', { class: 'lede' }, 'Search, recommendations and related content never call a language model. Only a question typed as a question does. The counters below are this visit, counted as they happen.')),
    h('div', { class: 'econ' }, t('RETRIEVAL', 'Found, not written', 'Results as you type, recommendations and filters.', figs.ret, 'calls this visit'), t('GENERATED', 'Written when asked', 'Cited answers to questions you typed.', figs.gen, 'calls this visit'), t('CACHED', 'Answered before', 'Suggested questions answered in advance, labelled with when.', figs.warm, 'served from cache this visit')),
    h('p', { style: 'margin-top:24px' }, h('a', { class: 'btn btn-line', href: '/pricing' }, 'Model your own numbers'), ' ', h('a', { class: 'btn btn-primary', href: SIGNUP, target: '_blank', rel: 'noopener noreferrer', 'data-trial-cta': '' }, TRIAL.cta))));
}
function fitTeaser() {
  const sum = FIT_SUMMARY.split(/\n\s*\n/).map((x) => x.trim()).filter((x) => x && !x.startsWith('## '));
  return h('section', { class: 's alt' }, h('div', { class: 'wrap' }, h('div', { class: 'sh' }, h('p', { class: 'eyebrow' }, 'Where it fits'), h('h2', {}, 'The honest summary'), h('p', { class: 'lede' }, 'Stated first, because anyone evaluating this seriously will work out the limits anyway.')),
    h('div', { class: 'prose' }, ...sum.map((p) => h('div', { html: render(p) }))),
    h('p', { style: 'margin-top:24px' }, h('a', { class: 'btn btn-primary', style: 'background:var(--navy);color:#fff', href: '/fit#not-for' }, 'Who it is not for, and what to use instead'))));
}
