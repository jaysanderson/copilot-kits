// The ask surface: instant retrieval rail while typing (T1, no LLM), streamed cited answer on Enter (T2).
import { h, SEARCH_ICON, debounce, fmtN, fmtMs } from './util.js';
import { state, recordTrace } from './state.js';
import { LENSES } from './util.js';
import { getJSON, streamAsk, ApiError } from './api.js';
import { render, plain } from './md.js';
import { readout, hitCard, failState, skeleton, langTag } from './cards.js';

const BANDS = { 'well-supported': ['well', 'Well supported'], moderate: ['mod', 'Moderate confidence'], weak: ['weak', 'Weak support'] };

// PRINTED answers were not generated, so they carry no quality score and no badge: they carry their provenance instead.
// The renderer branches on the BAND (never on whether citations are present), maps known bands explicitly, and renders nothing for
// any band outside the set. A missing or empty href is never rendered as an empty link: the title shows unlinked and the gap is logged.
// CONTRACT-FIELDS-04: printed = { label, kind, source_title, href, verified, document_asset, document_title }. Exactly these names, no aliases.
// A violating entry is WITHHELD WHOLE at render time (see card.withhold): never a red box, never an empty link, never a label with no source.
export function printedProblem(conf) {
  const p = conf && conf.printed;
  if (!p || typeof p !== 'object') return 'printed object missing';
  if (typeof p.label !== 'string' || !p.label) return 'label missing';
  if (p.kind !== 'published-page' && p.kind !== 'document') return `unknown kind ${JSON.stringify(p.kind)}`;
  if (typeof p.source_title !== 'string' || !p.source_title) return 'source_title missing';
  if (typeof p.href !== 'string' || !(p.kind === 'published-page' ? /^https:\/\//.test(p.href) : /^\/(?!\/)/.test(p.href))) return `unusable href ${JSON.stringify(p.href)} for kind ${p.kind}`;
  return null;
}
export function provenance(conf) {
  const p = conf.printed, ext = p.kind === 'published-page';
  const verified = typeof p.verified === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(p.verified) ? `verified ${p.verified}` : '';
  return h('span', { class: 'badge printed', 'data-printed': 'true' }, h('i'), p.label + ': ',
    h('a', { href: p.href, ...(ext ? { target: '_blank', rel: 'noopener noreferrer' } : {}) }, p.source_title), verified ? h('span', { style: 'font-weight:400' }, ` (${verified})`) : null);
}
// History is sent for GENERATION only. A courtesy cap (the server enforces its own, binding one): the question in full, and the answer cut at a
// UNIT boundary - a sentence, list item or table row - dropping whole units from the end until under budget. Never a character cut: a cut after a
// lead-in puts an EMPTY STEM into the prompt, and a cut mid-figure severs a number from its unit ("$700 a" / "once per"). If the first unit alone
// is over budget, send nothing for the turn rather than half of it. A kept answer never ends on a lead-in (a trailing colon).
export function boundedAnswerInfo(text, budget = 400) {
  const units = String(text || '').split(/\n+/).flatMap((ln) => plain(ln).split(/(?<=[.!?])\s+(?=[A-Z0-9"\u201c(\[])/)).map((u) => u.trim()).filter(Boolean);
  const kept = []; let len = 0;
  for (const u of units) { const add = (kept.length ? 1 : 0) + u.length; if (len + add > budget) break; kept.push(u); len += add; }
  while (kept.length && /:$/.test(kept[kept.length - 1])) kept.pop();
  return { text: kept.join(' '), shortened: kept.length > 0 && kept.length < units.length, emptyBecause: kept.length ? null : (!units.length ? 'no answer text' : len === 0 && units[0].length > budget ? 'first-unit-over-budget' : 'only-lead-in') };
}
export const boundedAnswer = (text, budget = 400) => boundedAnswerInfo(text, budget).text;
export function badge(conf, q) {
  if (!conf) return h('span', { class: 'badge pending', 'aria-live': 'polite' }, h('i'), 'Checking support...');
  if (conf.band === 'printed') return printedProblem(conf) ? null : provenance(conf);
  const b = BANDS[conf.band]; if (!b) return null; // unknown band renders NOTHING
  const n = fmtN(conf.contexts);
  return h('span', { class: 'badge ' + b[0], title: 'How well the wording is supported by the passages retrieved. Not a guarantee the passages are correct.' }, h('i'), b[1], n ? h('span', { class: 'mono', style: 'font-weight:400' }, ` · ${n} passages checked`) : '');
}

// One real answer shown on arrival, so the headline's promise is visible without typing. It is a REAL call to this site's own answer
// endpoint made when the page loads (an entry the server names (a pre-warmed generated answer, or a printed one as the fallback)), labelled as an example, kept out of the
// conversation (no turn, no URL change, no history) and out of "your last action". Optional: anything but a clean printed answer removes
// it silently rather than showing a refusal or an error where a showcase should be. The server counts this call apart (page_load_example) because it is the PAGE asking, so the label says Example.
export async function renderExample(host, q, source = null) {
  const ctl = new AbortController();
  const card = answerCard(q, ctl, null, 'Example answer', () => [], { example: true });
  host.replaceChildren(card.el);
  host.style.visibility = 'hidden';  // nothing of a refused (printed) answer may flash before the band arrives
  let bad = false;
  try {
    await streamAsk({ question: q, lens: '' }, (ev, d) => { if (ev === 'refusal' || ev === 'error') bad = true;
      if (ev === 'confidence' && d) {
        // The hero is never a deterministic answer (CONTRACT-FIELDS-05 s7): a printed band here is REFUSED, whatever the server's `source` claimed, and the
        // block simply does not render (same as a null hero_example) - no substitute and nothing shown to the visitor.
        if (d.band === 'printed') { bad = true; ctl.abort(); return; }
        card.setLabel('Example answer \u00b7 pre-computed'); host.style.visibility = '';
      }
      if (!bad) card.on(ev, d, performance.now()); }, { signal: ctl.signal });
  } catch { bad = true; }
  if (bad || card.refused) { host.replaceChildren(); host.style.visibility = ''; return false; }
  host.style.visibility = '';
  card.finish(); return true;
}
export function mountAsk(host, { scope = null, compact = false, questions = [], total = null, onAsked, autofocus = true } = {}) {
  const input = h('input', { type: 'text', id: 'ask-input', autocomplete: 'off', enterkeyhint: 'search', placeholder: 'Ask a question...', 'aria-label': 'Ask a question', maxlength: 400 });
  const form = h('form', { class: 'ask', role: 'search' }, h('span', { html: SEARCH_ICON }), input, h('button', { type: 'submit' }, 'Ask'));
  const meta = h('div', { class: 'ask-meta' }, h('p', { class: 'hint', id: 'ask-hint' }, ...(total != null ? [h('b', {}, fmtN(total)), ' resources searched as you type', h('span', { class: 'hint-more' }, ' · Enter for a written answer')] : ['Results appear as you type', h('span', { class: 'hint-more' }, ' · Enter for a written answer')])));
  const sugg = h('div', { class: 'suggest', 'aria-live': 'polite' });
  const suggMeta = h('div', {});
  const answerHost = h('div', {});
  host.append(form, meta, sugg, suggMeta);
  host.__answer = answerHost;
  let sctl = null, runId = 0;
  const hint = meta.querySelector('#ask-hint');

  const typeahead = debounce(async () => {
    const q = input.value.trim();
    if (sctl) sctl.abort();
    if (q.length < 2) { sugg.replaceChildren(); suggMeta.replaceChildren(); return; }
    sctl = new AbortController();
    try {
      const j = await getJSON(`/api/suggest?q=${encodeURIComponent(q)}${state.lens ? '&lens=' + state.lens : ''}${scope ? '&scope=' + scope : ''}`, { signal: sctl.signal, label: 'Typeahead', retry: false });
      if (input.value.trim() !== q) return;
      const hits = (j.hits || []).slice(0, 6);
      sugg.replaceChildren(...hits.map((a, i) => hitCard(a, i)));
      suggMeta.replaceChildren(h('div', { class: 'ask-meta' }, readout(j._trace || (typeof j.ms === 'number' ? [{ generative: false, ms: j.ms }] : []), { extra: [hits.length ? `${hits.length} resources` : 'Nothing close in the library'] })));
    } catch (e) { if (e.kind !== 'abort') { sugg.replaceChildren(); suggMeta.replaceChildren(failState('Search did not come back in time.', typeahead)); } }
  }, 140);

  input.addEventListener('input', typeahead);
  input.addEventListener('keydown', (e) => { if (e.key === 'Escape') { input.value = ''; sugg.replaceChildren(); suggMeta.replaceChildren(); } });
  input.addEventListener('ask-this', (e) => ask(e.detail));
  form.addEventListener('submit', (e) => { e.preventDefault(); ask(input.value); });
  const slash = (e) => { if (e.key === '/' && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) { e.preventDefault(); input.focus(); } };
  document.addEventListener('keydown', slash);

  // A conversation, not a single reply: every turn stays on screen under its own lens label, and the question history
  // travels with each request so a follow-up can depend on the last answer. Changing the path re-scopes the CURRENT turn.
  const turns = [];
  let running = null;
  const lensName = () => (state.lens ? LENSES[state.lens] : 'All paths');
  // Returns what is ACTUALLY sent and an account of what was not, so the reveal can describe the request rather than the design.
  const historyFor = (idx) => {
    const prior = turns.slice(0, idx).filter((t) => t.card && !t.card.refused && t.card.text());
    const dropped = [], sent = []; let shortened = 0;
    prior.forEach((t) => {
      if (t.q.length > 300) return dropped.push({ q: t.q, why: 'question over 300 characters' });
      const info = boundedAnswerInfo(t.card.text(), 400);
      if (!info.text) return dropped.push({ q: t.q, why: info.emptyBecause === 'first-unit-over-budget' ? 'first sentence of its answer over the 400-character budget' : 'answer would end on a lead-in with nothing after it' });
      if (info.shortened) shortened++;
      sent.push({ question: t.q, answer: info.text });
    });
    const history = sent.slice(-2);
    sent.slice(0, Math.max(0, sent.length - 2)).forEach((x) => dropped.push({ q: x.question, why: 'older than the last two turns' }));
    return { history, report: { available: prior.length, sent: history.length, shortened, dropped } };
  };
  async function ask(q, { retried = false, turn = null } = {}) {
    q = (q || '').trim(); if (q.length < 2) return;
    typeahead.cancel && typeahead.cancel(); if (sctl) sctl.abort();
    input.value = ''; sugg.replaceChildren(); suggMeta.replaceChildren();
    if (running && running !== turn && running.ctl) running.ctl.abort();
    const t = turn || { q, idx: turns.length };
    if (!turn) turns.push(t);
    t.q = q; t.lens = state.lens || ''; t.ctl = new AbortController(); running = t; state.asks++;
    onAsked && onAsked(q);
    const u = new URL(location.href); u.searchParams.set('q', q); history.replaceState(null, '', u);
    const prevFups = () => { const p = turns.slice(0, t.idx).reverse().find((x) => x.card && !x.card.refused && x.card.followups().length); return p ? p.card.followups() : []; };
    const card = answerCard(q, t.ctl, () => ask(q, { turn: t }), lensName(), prevFups);
    if (t.card) t.card.el.replaceWith(card.el); else answerHost.append(card.el);
    t.card = card; hint.textContent = '';
    if (retried) card.retrying();
    const calm = matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
    if (turns.length === 1) { form.style.scrollMarginTop = '84px'; form.scrollIntoView({ block: 'start', behavior: calm }); }
    else { card.el.style.scrollMarginTop = '84px'; card.el.scrollIntoView({ block: 'start', behavior: calm }); }
    const hist = historyFor(t.idx); state.lastHistory = hist.report;
    const t0 = performance.now(), my = ++runId; t.run = my;
    try {
      await streamAsk({ question: q, lens: state.lens || '', ...(scope ? { scope } : {}), history: hist.history }, (ev, d) => { if (t.run === my) card.on(ev, d, t0); }, { signal: t.ctl.signal });
      if (t.run !== my) return;
      card.finish(); running = running === t ? null : running;
      if (!card.refused) loadRecs(card, q);
    } catch (e) {
      if (t.run !== my || e.kind === 'abort') return card.stopped();
      if ((e.kind === 'stall' || e.kind === 'network') && !retried) return ask(q, { retried: true, turn: t });
      running = running === t ? null : running;
      card.fail(e);
    }
  }
  const onLens = () => { const last = turns[turns.length - 1]; if (last && last.lens !== (state.lens || '')) ask(last.q, { turn: last }); };
  window.addEventListener('lenschange', onLens);
  async function loadRecs(card, q) {
    card.recsLoading();
    try {
      const j = await getJSON(`/api/recommend?context=${encodeURIComponent(q)}${state.lens ? '&lens=' + state.lens : ''}`, { label: 'Recommendations' });
      const cards = (j.cards || []).slice(0, 6); if (!cards.length) return card.recsClear();
      card.recs(cards, j._trace);
    } catch { card.recsClear(); }
  }
  if (autofocus) queueMicrotask(() => input.focus({ preventScroll: true }));
  const setTotal = (n) => { if (!turns.length) hint.replaceChildren(h('b', {}, fmtN(n)), ' resources searched as you type', h('span', { class: 'hint-more' }, ' · Enter for a written answer')); };
  return { input, ask, answerHost, setTotal, destroy() { document.removeEventListener('keydown', slash); window.removeEventListener('lenschange', onLens); turns.forEach((t) => t.ctl && t.ctl.abort()); } };
}

// Every answer card gets its own id namespace: the hero example and each chat turn all have a source 1, and a bare `#src-1` always resolves to the FIRST one in the DOM (often a hidden card).
let CARD_SEQ = 0;
function answerCard(q, ctl, retry, lensLabel, prevFups = () => [], opts = {}) {
  const idp = `c${++CARD_SEQ}-`;
  let lensTagEl = null, withheld = false, fupList = [], streamErr = null, toks = [], text = '', cites = [], conf = null, raf = 0, ttft = null, rows = null, refused = false, done = false;
  const head = h('div', { class: 'answer-head' }, h('h2', {}, 'Answer'), lensLabel ? (lensTagEl = h('span', { class: 'lens-tag' }, lensLabel)) : null, badge(null));
  const ro = h('div', {});
  const rv = h('div', { class: 'review hide' });
  const prose = h('div', { class: 'prose', 'aria-live': 'polite' });
  const stop = h('button', { class: 'btn btn-line btn-sm', type: 'button', onclick: () => ctl.abort() }, 'Stop');
  const actions = h('div', { class: 'actions' }, stop);
  const srcs = h('div', { class: 'sec hide' }), fups = h('div', { class: 'sec hide' }), recs = h('div', { class: 'sec hide' });
  const el = h('div', { class: 'answer-wrap wrap' }, h('div', { class: 'answer' }, head, h('p', { class: 'answer-q' }, q), prose, rv, ro, actions, srcs, fups, recs));
  // The server gives each citation its character offsets (`at`) into the answer; the marker belongs at the end of the
  // sentence that contains each offset. Placement is the server's claim, the client only renders it (B33).
  const marked = () => {
    if (!cites.some((c) => Array.isArray(c.at)) || !toks.length) return text;
    return toks.map((t) => {
      const core = t.text.trimEnd(), tail = t.text.slice(core.length);
      const here = cites.filter((c) => (c.at || []).some((p) => p >= t.offset && p <= t.offset + core.length)).map((c) => c.n);
      return core + here.sort((a, b) => a - b).map((n) => `[${n}]`).join('') + tail;
    }).join('');
  };
  const draw = () => { raf = 0; prose.innerHTML = render(marked(), { citations: cites, streaming: !done, idp }); };
  const sched = () => { if (!raf) raf = requestAnimationFrame(draw); };
  // CONTRACT-FIELDS-05 s9: a pre-warmed generated answer a person read before it was served. Only known edit actions render; review null renders nothing.
  const drawReview = (r) => {
    rv.replaceChildren(); rv.classList.add('hide');
    if (!r || typeof r !== 'object' || r.read_by_person !== true) return;
    const edits = r.edited === true && Array.isArray(r.edits) ? r.edits.filter((e) => e && (e.action === 'removed' || e.action === 'replaced') && e.text) : [];
    rv.classList.remove('hide');
    const line = h('span', { class: 'review-label' }, 'Read by a person before it was served');
    if (!edits.length) { rv.append(line); return; }
    const list = h('ul', { class: 'review-edits hide' }, ...edits.map((e) => h('li', {}, e.action === 'removed' ? h('span', {}, 'Removed: ', h('del', {}, e.text)) : h('span', {}, 'Replaced: ', h('del', {}, e.text), ' with ', h('ins', {}, e.with || '')), e.reason ? h('em', {}, ` - ${e.reason}`) : null)));
    const btn = h('button', { class: 'review-btn', type: 'button', 'aria-expanded': 'false', onclick: () => { const open = list.classList.toggle('hide') === false; btn.setAttribute('aria-expanded', String(open)); } }, `Edited (${edits.length}) - see what changed`);
    rv.append(line, ' · ', btn, list);
  };
  const setBadge = () => { const b = badge(conf, q); if (conf && conf.band === 'printed') drawSources(); head.lastChild.replaceWith(...(b ? [b] : [document.createComment('')])); };
  const paintRo = () => ro.replaceChildren(...(opts.example || (conf && conf.band === 'printed') ? [] : [readout(rows || [], { extra: [ttft != null && ttft >= 1 ? `first word ${fmtMs(ttft)} in your browser` : null] })]));
  function on(ev, d, t0) {
    if (withheld) return;
    if (ev === 'token') { if (ttft == null) ttft = performance.now() - t0; text += d.text ?? ''; if (typeof d.offset === 'number') toks.push({ text: d.text ?? '', offset: d.offset }); sched(); }
    else if (ev === 'citations') { cites = (d.citations || []).filter((c) => c && c.title); drawSources(); sched(); }
    else if (ev === 'confidence') {
      const bad = d && d.band === 'printed' ? printedProblem(d) : null;
      if (bad) return card.withhold(bad);
      conf = d; state.lastConfidence = d; setBadge(); drawReview(d.review);
    }
    else if (ev === 'followups') { if (!opts.example) drawFups(d.followups || []); }
    else if (ev === 'refusal') refuse(d.message, d.reason);
    else if (ev === '_trace') { rows = d.trace || d._trace || []; recordTrace(opts.example ? 'Example' : 'Answer', rows); paintRo(); }
    else if (ev === 'error') streamErr = d;
    else if ((ev === 'searching' || ev === 'sources') && !text) {
      // The early event carries a COUNT only; titles arrive with the committed response. State what is actually happening.
      const n = [d.count, d.resources, d.n].find((x) => typeof x === 'number');
      if (n != null) prose.replaceChildren(h('p', { class: 'readout' }, `Searching ${fmtN(n)} resources on the public tier. A written answer is held until the scope check passes.`));
    }
  }
  function drawSources() {
    if (!cites.length) return;
    srcs.classList.remove('hide');
    srcs.replaceChildren(h('h3', {}, 'Sources', h('span', { class: 'count' }, String(cites.length))),
      h('div', { class: 'srcs' }, ...cites.map((c, i) => h('a', { class: 'src', id: `src-${idp}${c.n ?? i + 1}`, href: c.href || '#', ...(/^https?:/.test(c.href || '') ? { target: '_blank', rel: 'noopener noreferrer' } : {}) }, conf && conf.band === 'printed' ? null : h('span', { class: 'n' }, String(c.n ?? i + 1)), h('div', {}, h('h4', {}, c.title, langTag(c)), c.passage ? h('p', {}, plain(c.passage)) : null)))));
  }
  function drawFups(list) {
    list = list.filter((f) => f && f.text); if (!list.length) return;
    fupList = list;
    fups.classList.remove('hide');
    fups.replaceChildren(h('h3', {}, 'Keep asking'), h('div', { class: 'fups' }, ...list.map((f) => h('button', { class: 'chip', type: 'button', onclick: () => document.getElementById('ask-input').dispatchEvent(new CustomEvent('ask-this', { detail: f.text, bubbles: true })) }, f.text, langTag(f)))));
  }
  function refuse(msg, reason) {
    refused = true; card.refused = true; done = true;
    // withhold the WHOLE response: no text, sources, badge or follow-ups of THIS turn. The server's message is shown as sent (it names what was
    // asked); for needs_standalone the PREVIOUS answer's self-contained follow-ups sit right beside it, because the conversation carries forward
    // through those, not through carried context.
    const a = el.firstChild; const prev = reason === 'needs_standalone' ? prevFups().filter((f) => f && f.text) : [];
    a.replaceChildren(h('div', { class: 'refusal' }, h('h3', {}, msg || 'No answer was returned for this question.'),
      prev.length ? h('div', {}, h('p', { style: 'margin:0 0 8px' }, 'Self-contained questions that follow from the last answer:'), h('div', { class: 'fups' }, ...prev.map((f) => h('button', { class: 'chip', type: 'button', onclick: () => document.getElementById('ask-input').dispatchEvent(new CustomEvent('ask-this', { detail: f.text, bubbles: true })) }, f.text, langTag(f)))))
      : reason === 'refreshing' ? h('p', { style: 'margin:0' }, h('button', { class: 'btn btn-line btn-sm', type: 'button', onclick: retry }, 'Try again'))
      : h('p', { style: 'margin:0' }, 'Rephrase it, or browse what the library does cover.'),
      h('p', { style: 'margin:10px 0 0' }, h('a', { href: '/explore' }, 'Browse the library'))));
  }
  const card = {
    el, on, refused: false, text: () => text, followups: () => fupList, setLabel(t) { if (lensTagEl) lensTagEl.textContent = t; },
    // A printed entry that violates the contract is withheld WHOLE. The visitor gets the ordinary failure state with a working retry;
    // the violation is counted and named in the reveal (state.withheld) and logged for whoever is watching.
    withhold(reason) {
      withheld = true; done = true; text = ''; cites = []; toks = [];
      console.error(`printed answer withheld (${q}): ${reason}`);
      state.withheld.push({ q, reason, at: new Date().toISOString() });
      el.firstChild.replaceChildren(failState('The answer could not be completed.', retry)); card.refused = true;
    },
    finish() { if (withheld) return; if (streamErr) return card.failMsg(streamErr); if (opts.example) { done = true; draw(); stop.remove(); return; } done = true; draw(); stop.remove(); if (!refused) { const t = text; actions.append(h('button', { class: 'btn btn-line btn-sm', type: 'button', onclick: (e) => { navigator.clipboard && navigator.clipboard.writeText(plain(t)); e.target.textContent = 'Copied'; } }, 'Copy answer'), h('button', { class: 'btn btn-line btn-sm', type: 'button', onclick: retry }, 'Ask again')); } },
    stopped() { done = true; draw(); stop.remove(); if (!text) prose.replaceChildren(failState('Stopped.', retry)); },
    retrying() { prose.replaceChildren(h('p', { class: 'readout' }, 'Still working - trying once more.')); },
    failMsg(d) { done = true; stop.remove(); head.lastChild.remove(); prose.replaceChildren(failState(d.message || 'The answer could not be completed.', d.retry === false ? null : retry)); card.refused = true; },
    fail(e) {
      done = true; stop.remove(); head.lastChild.remove();
      // every failure path gets a working retry; the copy names what actually happened
      const msg = e.kind === 'stall' ? 'The answer did not start in time.' : e.kind === 'network' ? 'The connection dropped before the answer arrived.' : (e.message && e.kind === 'http' ? e.message : 'The answer could not be completed.');
      prose.replaceChildren(failState(msg, e.kind === 'http' && e.status < 500 && e.retry === false ? null : retry)); card.refused = true;
    },
    recsLoading() { recs.classList.remove('hide'); recs.replaceChildren(h('h3', {}, 'Keep going'), h('p', { class: 'readout', 'aria-busy': 'true' }, 'Finding similar items...'), skeleton(2)); },
    recsClear() { recs.classList.add('hide'); recs.replaceChildren(); },
    recs(cards, tr) { recs.classList.remove('hide'); recs.replaceChildren(h('h3', {}, 'Keep going', h('span', { class: 'count' }, String(cards.length))), h('div', { class: 'suggest', style: 'grid-template-columns:repeat(auto-fill,minmax(260px,1fr));max-width:none;margin-top:0' }, ...cards.map((c, i) => hitCard(c, i))), h('div', { style: 'margin-top:10px' }, readout(tr || [{ generative: false }]))); },
  };
  return card;
}
