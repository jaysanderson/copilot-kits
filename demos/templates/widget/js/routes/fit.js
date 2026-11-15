import { h, LENSES } from '../util.js';
import { lensData } from '../data.js';
import { render, plain } from '../md.js';
import { failState, hitCard, readout, nextAction, tierNote } from '../cards.js';
import { mountAsk } from '../ask.js';
import { getJSON } from '../api.js';
import { scopeDemo } from '../scopedemo.js';

import { FIT_FOR, FIT_NOT_FOR, FIT_SUMMARY } from '../fit-data.js';

// Split a fenced block into its heading and its bold-led items. Items render through the shared markdown renderer.
function items(md) {
  const parts = md.split(/\n\s*\n/).map((x) => x.trim()).filter(Boolean);
  const head = parts[0].startsWith('## ') ? parts.shift().slice(3) : '';
  return { head, rows: parts.map((p) => { const m = /^\*\*(.+?)\*\*\s*([\s\S]*)$/.exec(p); return m ? { t: m[1].replace(/\.$/, ''), b: m[2] } : { t: '', b: p }; }) };
}
const card = (r, n) => h('div', { class: 'qa' }, n ? h('span', { class: 'kind' }, String(n)) : null, r.t ? h('h3', { style: 'margin-top:8px' }, r.t) : null, h('div', { class: 'prose', html: render(r.b) }));

export async function mount(main) {
  main.append(h('section', { class: 'phead' }, h('div', { class: 'wrap' }, h('h1', {}, 'Where it fits, and where it does not'), h('p', {}, 'Who this is not for, and what to use instead, comes first. Then who it is for, and the questions buyers raise.'))));
  const page = h('div', { class: 'wrap page' }); main.append(page);
  page.append(tierNote());
  const no = items(FIT_NOT_FOR), yes = items(FIT_FOR), sum = items(FIT_SUMMARY);
  // NOT-FOR is the centre of gravity of this page: first, and above the fold.
  page.append(h('section', { id: 'not-for', class: 'sec', style: 'margin-bottom:44px' }, h('h2', { style: 'font-size:clamp(1.6rem,3.2vw,2.4rem);font-weight:560;margin-bottom:14px' }, no.head),
    h('div', { class: 'fitgrid', style: 'grid-template-columns:repeat(auto-fit,minmax(300px,1fr))' }, ...no.rows.map((r, i) => card(r, i + 1)))));
  page.append(h('section', { id: 'for', class: 'sec', style: 'margin-bottom:44px' }, h('h2', { style: 'font-size:clamp(1.4rem,2.8vw,2rem);font-weight:560;margin-bottom:14px' }, yes.head),
    h('div', { class: 'fitgrid', style: 'grid-template-columns:repeat(auto-fit,minmax(300px,1fr))' }, ...yes.rows.map((r) => card(r)))));
  page.append(h('section', { id: 'summary', class: 'stat', style: 'margin-bottom:44px' }, h('h2', { style: 'font-size:1.5rem;font-weight:560;margin-bottom:8px' }, sum.head), ...sum.rows.map((r) => h('div', { class: 'prose', html: render(r.b) }))));
  // A working ask beneath the printed statement is a demonstration; the page is honest without it.
  const askBox = h('div', { class: 'dark', style: 'background:var(--navy);border-radius:16px;padding:20px 20px 24px;margin-bottom:28px' }, h('p', { class: 'eyebrow', style: 'color:#B9C8EE' }, 'Ask it'));
  const ask = mountAsk(askBox, { autofocus: false });
  const chipRow = h('p', { style: 'margin:14px 0 0' }, h('button', { class: 'btn btn-line btn-sm', type: 'button', onclick: () => ask.ask('When is Progress Agentic RAG the wrong tool?') }, 'Ask it: when is this the wrong tool?'));
  askBox.append(chipRow);
  page.append(askBox, ask.answerHost);
  ask.answerHost.classList.add('flat');
  page.append(scopeDemo());
  let L; try { L = await lensData(); } catch { L = null; }
  if (L) {
    page.append(h('h2', { style: 'font-size:1.6rem;font-weight:560;margin:20px 0 6px' }, 'What buyers ask'), h('p', { style: 'color:#3D3D42;margin:0 0 20px' }, 'Objection handling, by path. This is a different thing from the statement above.'));
    for (const l of L.lenses || []) {
      if (!LENSES[l.id]) continue;
      page.append(h('section', { id: l.id, class: 'sec', style: 'margin-bottom:36px' }, h('h3', { style: 'font-size:22px;margin-bottom:6px' }, LENSES[l.id]),
        l.blurb ? h('p', { class: 'eyebrow' }, plain(l.blurb)) : null,
        nextAction(l),
        h('div', { class: 'fitgrid', style: 'margin-top:12px' }, ...(l.objections || []).map((o) => ({ q: o.q ?? o.objection, a: o.a ?? o.response })).filter((o) => o.q && o.a).map((o) => h('div', { class: 'qa' }, h('h3', {}, plain(o.q)), h('div', { class: 'prose', html: render(o.a) }))))));
    }
  }
  return () => ask.destroy();
}
