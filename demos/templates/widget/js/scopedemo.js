// Retrieval-scope demonstration. The SERVER runs one question through three scopes and returns per scope: assets in reach,
// whether an answer is within reach, and titles for the PUBLIC scope only. The visitor picks from a FIXED set; they cannot type.
// COPY RULE (lead): lead on ANSWERABILITY, never on the counts. 49 against 55 side by side implies a content gap that is not
// there, so counts sit in small type with the payload's own unit string. A scope whose differential is 'none' renders no row.
import { h, fmtN } from './util.js';
import { getJSON } from './api.js';
import { readout, failState, skeleton } from './cards.js';
import { plain } from './md.js';

const SHORT = { starter: 'Starter', pro: 'Pro' };
const NAMES = { public: 'A visitor', starter: 'A Starter customer', pro: 'A Pro customer' };

function headline(sc) {
  const by = Object.fromEntries(sc.map((s) => [s.scope, s]));
  const pub = by.public, st = by.starter, pro = by.pro;
  if (!pub) return null;
  if (!pub.answerable && !(st && st.answerable) && !(pro && pro.answerable)) return ['No one gets an answer to this question, at any level.', 'The mechanism shows nothing when there is nothing to show.'];
  if (!pub.answerable && st && st.answerable) return ['A visitor gets no answer to this question. A Starter customer does.', null];
  if (!pub.answerable && pro && pro.answerable) return ['A visitor gets no answer to this question. A Pro customer does.', null];
  if (pub.answerable) return ['A visitor already gets an answer to this one.', 'Scoping removes nothing here, because nothing about this question is restricted.'];
  return null;
}

export function scopeDemo() {
  const root = h('section', { id: 'scope', class: 'sec', style: 'margin-bottom:44px' });
  const out = h('div', {}), chooser = h('div', { class: 'chips', role: 'group', 'aria-label': 'Choose a question' });
  root.append(h('div', { class: 'sh' }, h('p', { class: 'eyebrow' }, 'Scoping at retrieval'), h('h2', {}, 'See who can be answered from what'),
    h('p', { class: 'lede' }, 'The same question, run through three scopes on this site\'s server. Pick one. You cannot type your own: a yes or no over restricted content, for any question you invent, would show the shape of what is restricted.')), chooser, out);
  let current = null, token = 0, questions = [];
  // The server owns the fixed question set ([{id, text, is_control}]); no question string lives here and no item is labelled as the control.
  const draw = () => { chooser.replaceChildren(...questions.map((q) => h('button', { class: 'chip', type: 'button', 'data-id': q.id, 'aria-pressed': String(q.id === current), style: 'white-space:normal;text-align:left', onclick: () => run(q) }, q.text))); };
  async function run(q) {
    const my = ++token; out.replaceChildren(skeleton(3));
    if (q) { current = q.id; draw(); }
    try {
      const url = q ? '/api/scope-demo?id=' + encodeURIComponent(q.id) : '/api/scope-demo';
      const j = await getJSON(url, { label: 'Scope demonstration' });
      if (my !== token) return;
      if (!questions.length && Array.isArray(j.questions)) { questions = j.questions.filter((x) => x && x.id != null && x.text).map((x) => ({ id: String(x.id), text: x.text, lead: x.public_answers === true })).sort((a, b) => Number(b.lead) - Number(a.lead)); const m = questions.find((x) => x.text === j.question); current = m ? m.id : null; draw(); }
      const sc = (j.scopes || []).filter((s) => NAMES[s.scope]);
      const hl = headline(sc);
      // differential: 'answerability' = the verdict flipped (the headline); 'assets' = more reachable, same verdict (small note only);
      // 'none' = render no row; absent on a restricted scope = unknown, row shown without a claim. The public scope has no differential.
      const rows = sc.filter((s) => s.scope === 'public' || s.differential !== 'none');
      const hidden = sc.filter((s) => !rows.includes(s));
      const note = (s) => (s.differential === 'assets' ? 'More assets are reachable here, but the answer verdict is the same.' : s.differential === 'answerability' ? 'The verdict changes here.' : null);
      out.replaceChildren(
        h('div', { class: 'stat', style: 'margin-top:16px', 'aria-live': 'polite' },
          h('p', { class: 'eyebrow', style: 'margin:0 0 6px' }, plain(j.question || '')),
          hl ? h('h3', { style: 'font-size:clamp(1.4rem,3vw,2rem);font-weight:560;margin:0 0 8px' }, hl[0]) : null,
          hl && hl[1] ? h('p', { style: 'margin:0 0 12px' }, hl[1]) : null,
          h('div', { class: 'fitgrid', style: 'margin-top:12px' }, ...rows.map((s) => h('div', { class: 'qa' }, h('h3', {}, NAMES[s.scope]),
            h('p', { style: 'margin:0 0 6px;font-weight:600' }, s.answerable ? 'An answer is within reach' : 'No answer in reach'),
            Array.isArray(s.titles) && s.titles.length ? h('ul', { style: 'margin:0 0 6px;padding-left:18px' }, ...s.titles.map((t) => h('li', {}, plain(t)))) : null,
            note(s) ? h('p', { style: 'margin:0 0 6px;font-size:14px;color:#3D3D42' }, note(s)) : null,
            typeof s.assets_in_reach === 'number' ? h('p', { class: 'mono', style: 'margin:0;color:#3D3D42;font-size:12px' }, `${fmtN(s.assets_in_reach)} ${j.unit || 'assets'} in scope`) : null))),
          hidden.length ? h('p', { style: 'margin:12px 0 0;color:#3D3D42' }, `${hidden.map((s) => SHORT[s.scope]).join(' and ')} reach${hidden.length === 1 ? 'es' : ''} this no differently from the level below.${hidden.some((s) => s.scope === 'pro') || sc.some((s) => s.scope === 'pro' && s.differential === 'assets') ? ' Pro\'s value is the capability set on the pricing page, not a larger library.' : ''}`) : null,
          h('p', { style: 'margin:14px 0 0;font-size:14px;color:#3D3D42' }, plain(j.statement || '')),
          h('div', { style: 'margin-top:8px' }, readout(j._trace || []))));
    } catch (e) { if (my === token) out.replaceChildren(failState(e.kind === 'http' && e.message ? e.message : 'The demonstration did not come back in time.', () => run(q))); }
  }
  run(null);
  return root;
}
