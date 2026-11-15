import { h, LABELSETS, KINDS, KIND_PLURAL, fmtN, debounce, $ } from '../util.js';
import { state, setLens } from '../state.js';
import { catalogue } from '../data.js';
import { getJSON } from '../api.js';
import { assetCard, hitCard, failState, countBadge, readout, skeleton, rail } from '../cards.js';
import { render, plain } from '../md.js';

const SETS = ['kind', 'vertical', 'stage'];

export async function mount(main, url) {
  const sel = { kind: new Set(), vertical: new Set(), stage: new Set() };
  { const j = url.searchParams.get('journey'); if (j && state.lens !== j) setLens(j); }   // a path id; setLens ignores anything that is not one
  for (const k of SETS) for (const v of (url.searchParams.get(k) || '').split(',').filter(Boolean)) sel[k].add(v);
  let q = url.searchParams.get('q') || '', view = 'grid', sort = 'rel';
  main.append(h('section', { class: 'phead' }, h('div', { class: 'wrap' }, h('h1', {}, 'Explore the library'), h('p', {}, 'Browse by type, industry and stage, or search by meaning. Counts are live.'))));
  const page = h('div', { class: 'wrap page' }); main.append(page);
  const results = h('div', {}), facetBox = h('aside', { class: 'facets' });
  const search = h('input', { class: 'field', type: 'search', value: q, placeholder: 'Search by meaning...', 'aria-label': 'Search the library' });
  const viewSeg = h('div', { class: 'seg', role: 'group', 'aria-label': 'Layout' }, ...['grid', 'list'].map((v) => h('button', { type: 'button', 'aria-pressed': String(v === view), onclick: () => { view = v; viewSeg.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b.textContent.toLowerCase() === v))); draw(); } }, v[0].toUpperCase() + v.slice(1))));
  const sortSel = h('select', { class: 'field', 'aria-label': 'Sort', onchange: (e) => { sort = e.target.value; draw(); } }, h('option', { value: 'rel' }, 'Most relevant'), h('option', { value: 'title' }, 'Title A-Z'), h('option', { value: 'type' }, 'Type'));
  page.append(h('div', { class: 'toolbar' }, search, sortSel, viewSeg), h('div', { class: 'layout' }, facetBox, results));
  let cat; try { cat = await catalogue(); } catch { results.append(failState('The catalogue did not load.', () => location.reload())); return; }
  let hits = null, facets = cat.facets || {}, ro = null, token = 0;

  const inSel = (a) => SETS.every((k) => !sel[k].size || sel[k].has(a[k]));
  function drawFacets() {
    const f = [h('details', { open: matchMedia('(min-width:901px)').matches }, h('summary', { class: 'sr' }, 'Filters'))]; const d = f[0];
    for (const k of SETS) {
      const [title, map] = LABELSETS[k]; const counts = facets[k] || {};
      const vals = Object.keys(map).filter((v) => counts[v]);
      if (!vals.length) continue;
      d.append(h('h3', {}, title), ...vals.map((v) => h('label', {}, h('input', { type: 'checkbox', checked: sel[k].has(v) || null, onchange: (e) => { e.target.checked ? sel[k].add(v) : sel[k].delete(v); sync(); } }), map[v], countBadge(counts[v]))));
    }
    facetBox.replaceChildren(d);
  }
  function sync() {
    const u = new URL(location.href); u.search = '';
    if (q) u.searchParams.set('q', q);
    for (const k of SETS) if (sel[k].size) u.searchParams.set(k, [...sel[k]].join(','));
    history.replaceState(null, '', u); run();
  }
  async function run() {
    const my = ++token;
    if (!q) { hits = null; facets = cat.facets || {}; ro = null; drawFacets(); return draw(); }
    results.replaceChildren(skeleton(4));
    const fs = SETS.flatMap((k) => [...sel[k]].map((v) => `${k}:${v}`)).join(',');
    try {
      const j = await getJSON(`/api/search?q=${encodeURIComponent(q)}${state.lens ? '&lens=' + state.lens : ''}${fs ? '&facets=' + encodeURIComponent(fs) : ''}`, { label: 'Search' });
      if (my !== token) return;
      hits = j.hits || []; facets = Object.keys(j.facets || {}).length ? j.facets : cat.facets || {}; ro = j._trace; drawFacets(); draw();
    } catch (e) { if (my === token) results.replaceChildren(failState('Search did not come back in time.', run)); }
  }
  function sorted(list) { const l = [...list]; if (sort === 'title') l.sort((a, b) => (a.title || '').localeCompare(b.title || '')); if (sort === 'type') l.sort((a, b) => (a.kind || '').localeCompare(b.kind || '')); return l; }
  function draw() {
    const filtered = !!(q || SETS.some((k) => sel[k].size));
    const box = h('div', {});
    if (!filtered) {
      for (const k of Object.keys(KINDS)) {
        const list = cat.assets.filter((a) => a.kind === k); if (!list.length) continue;
        const rl = rail(...list.slice(0, 12).map((a) => assetCard(a, { onOpen: open })));
        box.append(h('div', { class: 'rail-head' }, h('h3', {}, KIND_PLURAL[k]), countBadge(cat.facets?.kind?.[k] ?? list.length), rl.nav, h('a', { href: `/explore?kind=${k}` }, 'See all →')), rl.el);
      }
    } else {
      const list = q ? (hits || []) : cat.assets.filter(inSel);
      const shown = q ? list.filter(inSel) : list;
      box.append(h('p', { class: 'readout', style: 'margin-bottom:12px' }, h('b', {}, fmtN(shown.length)), ' resources', q ? h('span', {}, `matching "${q}"`) : null), ...(ro ? [readout(ro)] : []));
      box.append(shown.length ? h('div', { class: 'grid ' + (view === 'list' ? 'list' : '') }, ...sorted(shown).map((a) => assetCard(a, { onOpen: open }))) : h('div', { class: 'empty' }, 'Nothing here. Clear a filter to widen it.'));
    }
    results.replaceChildren(box);
  }
  search.addEventListener('input', debounce(() => { q = search.value.trim(); sync(); }, 250));
  const lc = () => { run(); }; window.addEventListener('lenschange', lc);
  drawFacets(); run();
  const want = url.searchParams.get('asset');
  if (want) { const a = cat.assets.find((x) => x.asset_id === want); a ? open(a) : getJSON('/api/asset?asset_id=' + encodeURIComponent(want), { label: 'Asset', track: false }).then((j) => j.asset && open(j.asset)).catch(() => {}); }
  return () => window.removeEventListener('lenschange', lc);
}

export function open(a) {
  const root = $('#modal-root'); const opener = document.activeElement;
  const close = () => { root.replaceChildren(); document.body.style.overflow = ''; document.removeEventListener('keydown', esc); opener && opener.focus && opener.focus(); };
  const esc = (e) => e.key === 'Escape' && close();
  const recs = h('div', { class: 'sec' });
  const dlg = h('div', { class: 'dialog', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'as-t' },
    h('button', { class: 'x', type: 'button', 'aria-label': 'Close', onclick: close }, '×'),
    KINDS[a.kind] ? h('span', { class: 'kind' }, KINDS[a.kind]) : null, h('h2', { id: 'as-t', style: 'margin-top:8px' }, a.title),
    a.excerpt ? h('div', { class: 'prose', html: render(a.excerpt) }) : null,
    /^https?:/.test(a.href || '') ? h('p', {}, h('a', { class: 'btn btn-primary', href: a.href, target: '_blank', rel: 'noopener noreferrer' }, 'Open the resource')) : null, recs);
  const ov = h('div', { class: 'overlay' }, dlg); ov.addEventListener('mousedown', (e) => e.target === ov && close());
  root.replaceChildren(ov); document.body.style.overflow = 'hidden'; document.addEventListener('keydown', esc); dlg.querySelector('.x').focus();
  recs.replaceChildren(h('h3', {}, 'More like this'), h('p', { class: 'readout', 'aria-busy': 'true' }, 'Finding similar items...'), skeleton(2));
  getJSON(`/api/recommend?asset_id=${encodeURIComponent(a.asset_id)}${state.lens ? '&lens=' + state.lens : ''}`, { label: 'Recommendations' }).then((j) => {
    const c = (j.cards || []).slice(0, 6);
    recs.replaceChildren(...(c.length ? [h('h3', {}, 'More like this'), h('div', { class: 'suggest', style: 'grid-template-columns:repeat(auto-fill,minmax(240px,1fr));max-width:none;margin-top:0' }, ...c.map((x, i) => hitCard(x, i))), readout(j._trace)] : []));
  }).catch(() => recs.replaceChildren());
}
