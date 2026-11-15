/* Clinic Knowledge Desk - client.
   Every answer rendered here is produced by a live retrieval call made by this
   application's own server. Nothing on any surface is pre-written. */

const view = document.getElementById('view');
const navEl = document.getElementById('nav');
const modalRoot = document.getElementById('modalRoot');
let CFG = null;

/* ------------------------------------------------------------- helpers */
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const num = n => (n == null ? '-' : Number(n).toLocaleString('en-AU'));

/* One markdown renderer, used by EVERY surface that renders generated text -
   an answer, an explanation, a market position, a suggested rewrite. Generated
   text routinely carries bold, emphasis and lists; rendering it raw is a defect. */
function mdInline(s) {
  let t = esc(String(s == null ? '' : s).replace(LIST_RE, ''));
  t = t.replace(/\[([^\]\n]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  t = t.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');
  t = t.replace(/__([^_\n]+)__/g, '<strong>$1</strong>');
  t = t.replace(/(^|[\s(])\*([^*\n]+)\*/g, '$1<em>$2</em>');
  t = t.replace(/`([^`\n]+)`/g, '<code>$1</code>');
  return t;
}

const LIST_RE = /^\s*(?:[-*•]\s+|\d+[.)]\s+)/;

/* A model frequently returns a list on ONE line - "...neuroma management. *
   Handling: Remplir can be used..." - which no sentence split breaks, so the
   marker survives into the prose as a literal asterisk. Split those out before
   rendering. Deliberately NOT on a bare "-": a spaced hyphen is this app's own
   house punctuation and splitting on it would shatter ordinary sentences.
   The lookbehind tolerates trailing emphasis characters because this model
   BOLDS each bullet's label - "...reinnervation.** * **Neurolysis:**" - so the
   character before the separating space is the closing "**", not the full stop.
   A first version required punctuation immediately before the space, which
   split the FIRST bullet (after a plain colon) and missed every later one. */
const INLINE_LIST_RE = /(?<=[.!?:;][*_]{0,2})\s+(?=(?:[*•]|\d+[.)])\s+\S)/;

function splitInlineLists(units) {
  const out = [];
  for (const u of units) {
    // normalise here so no downstream step can be handed a null text
    // newlines first, then inline markers. The server splits on lines already,
    // so a multi-line unit should not reach here - but a unit that does must not
    // collapse two list items into one.
    const text = String(u.text == null ? '' : u.text);
    const parts = text.split(/\n+/).flatMap(line => line.split(INLINE_LIST_RE));
    if (parts.length === 1) { out.push(Object.assign({}, u, { text })); continue; }
    parts.forEach((t, i) => {
      if (!t.trim()) return;
      // the citation marker belongs to the claim it was aligned to, not to
      // every fragment that claim turned out to contain
      out.push(Object.assign({}, u, { text: t.trim(), source: i === 0 ? u.source : null }));
    });
  }
  return out;
}

/* Renders an array of {text, source} units as markdown blocks, placing each
   unit's citation marker inline at the end of its own claim. */
function renderUnits(units, marker) {
  units = splitInlineLists(units);
  const out = [];
  let list = null, para = null;
  const flushList = () => { if (list) { out.push(`<ul>${list.join('')}</ul>`); list = null; } };
  const flushPara = () => { if (para) { out.push(`<p>${para.join(' ')}</p>`); para = null; } };
  for (const u of units) {
    const heading = u.text.match(/^(#{1,6})\s+(.*)$/);
    const isItem = LIST_RE.test(u.text);
    const inner = mdInline(u.text.replace(LIST_RE, '').replace(/^#{1,6}\s+/, '')) + (marker ? marker(u) : '');
    if (heading) { flushList(); flushPara(); out.push(`<h4>${inner}</h4>`); }
    else if (isItem) { flushPara(); (list = list || []).push(`<li>${inner}</li>`); }
    else { flushList(); (para = para || []).push(inner); }
  }
  flushList(); flushPara();
  return out.join('');
}

const mdBlock = text => renderUnits(
  String(text || '').split('\n').map(l => l.trim()).filter(Boolean).map(t => ({ text: t })), null);

const niceDate = d => {
  if (!d) return '';
  const p = d.split('-');
  const m = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${Number(p[2])} ${m[Number(p[1]) - 1]} ${p[0]}`;
};

async function api(path, body, timeoutMs = 30000, retries = 1, slowMs = 90000) {
  // A fetch with no timeout can hang indefinitely on a stalled connection and
  // leave the surface sitting on a loading state with nothing to show. Every
  // call is bounded. A STALL is retried once - measured on this deployment the
  // retrieval service stalls roughly one call in thirty, and a stalled call is
  // not a failed one. A real error (a 4xx or 5xx) is never retried; it is shown.
  // The two attempts are deliberately ASYMMETRIC. The first is short so a
  // genuine stall still surfaces fast; the second is patient so a platform that
  // is merely SLOW gets served rather than refused. Measured 29 Sep 2026: the
  // retrieval service answered correctly at 49-59s for about ten minutes
  // against its 6-9s norm, and a flat 30s budget turned every one of those into
  // an error box - the demo did not look slow, it looked broken. A flat raise
  // would have doubled how long a real stall takes to surface in a room, which
  // is the wrong trade on a live demo.
  for (let attempt = 0; ; attempt++) {
    const budget = attempt === 0 ? timeoutMs : Math.max(timeoutMs, slowMs);
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), budget);
    try {
      const r = await fetch(path, Object.assign({ signal: ctrl.signal },
        body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}));
      if (!r.ok) {
        let msg = 'The desk could not complete that request just now.';
        try { const j = await r.json(); if (j.detail && typeof j.detail === 'string') msg = j.detail; } catch (e) { /* keep default */ }
        throw new Error(msg);
      }
      return await r.json();
    } catch (e) {
      if (e.name === 'AbortError') {
        if (attempt < retries) { markSlow(); continue; }
        throw new Error('The desk took too long to answer and the request was stopped.');
      }
      throw e;
    } finally { clearTimeout(timer); }
  }
}

/* Says so on screen when a call is being retried - never a fake progress bar. */
function markSlow() {
  // The market surface shows skeleton cards rather than a spinner, so its own
  // note is the honest place to say a retry is running.
  const stage2 = document.getElementById('stage2');
  if (stage2 && !stage2.dataset.slow) {
    stage2.dataset.slow = '1';
    stage2.innerHTML += ' <b style="color:var(--amber)">Taking longer than usual - trying again.</b>';
  }
  document.querySelectorAll('.thinking').forEach(el => {
    if (el.dataset.slow) return;
    el.dataset.slow = '1';
    const t = document.createElement('span');
    t.className = 'tiny';
    t.style.cssText = 'color:var(--amber);margin-left:4px';
    t.textContent = '(taking longer than usual - trying again)';
    el.appendChild(t);
  });
}

const thinking = (label) => `<div class="thinking"><span class="dot"></span><span class="dot"></span><span class="dot"></span>${esc(label)}</div>`;
const errorBox = m => `<div class="errorbox fade">${esc(m)}
  <div style="margin-top:12px"><button class="btn small" data-retry>Try again</button></div></div>`;

/* Any surface that can fail gets a working retry - never a dead end. */
function wireRetry(scope, fn) {
  const b = scope.querySelector('[data-retry]');
  if (b) b.addEventListener('click', fn);
}

/* ------------------------------------------------------------- routes */
const ROUTES = {
  '/': { nav: 'Desk', title: 'Knowledge Desk' },
  '/vac-desk': {
    nav: 'VAC desk', title: 'Hospital approval desk',
    n: '01',
    blurb: 'Every hospital Value Analysis Committee submission has to answer the same evidence questions. This desk drafts the response from Clinic\'s own published clinical and regulatory material, cites every claim, and says plainly what the published evidence does not yet establish.',
    who: 'US commercial team, market access, medical affairs'
  },
  '/surgeon-desk': {
    nav: 'Surgeon desk', title: 'Surgeon and rep desk',
    n: '02',
    blurb: 'The same cited answer on technique, indications and evidence, whoever asks it - so a rep in Ohio and a surgeon in Perth get the same compliant response, and neither gets one the published material cannot support.',
    who: 'US reps, surgeons, theatre teams, clinical specialists'
  },
  '/market-access': {
    nav: 'Regulatory', title: 'Regulatory positions by market',
    n: '03',
    blurb: 'TGA, FDA and every other regime Clinic has published a position in, answered separately and quoted verbatim from the announcement that stated it - plus an explicit list of what has not been stated.',
    who: 'Regulatory affairs, quality, country managers'
  },
  '/claim-check': {
    nav: 'Claim check', title: 'Claim substantiation check',
    n: '04',
    blurb: 'Draft a sentence for a brochure, a congress booth or a sales email, and find out whether Clinic\'s published content actually supports it before it goes out.',
    who: 'Marketing, medical affairs, regulatory review'
  },
  '/evidence-library': {
    nav: 'Library', title: 'Evidence library',
    n: '05',
    blurb: 'Everything the desk reads, browsable by product, document type and audience, with semantic search across the whole set.',
    who: 'Anyone who needs the underlying document'
  },
  '/investor-signal': {
    nav: 'Investor signal', title: 'Investor signal',
    n: '06',
    blurb: 'Fifteen years of Clinic market announcements, grouped by what they were about, with a grounded briefing over any theme.',
    who: 'Investor relations, corporate affairs, board reporting'
  },
  '/patient-guide': {
    nav: 'Patient guide', title: 'Patient guide',
    n: '07',
    blurb: 'Plain-language answers drawn only from Clinic\'s patient-facing pages, with a standing reminder to speak to a treating clinician.',
    who: 'Patients, carers, referring practices'
  }
};

function renderNav() {
  navEl.innerHTML = Object.entries(ROUTES).filter(([p]) => p !== '/').map(([p, r]) =>
    `<a href="${p}" data-link class="${location.pathname === p ? 'on' : ''}">${esc(r.nav)}</a>`).join('');
}

document.addEventListener('click', e => {
  const a = e.target.closest('a[data-link]');
  if (a) { e.preventDefault(); go(a.getAttribute('href')); }
});
window.addEventListener('popstate', () => render());

function go(path) {
  history.pushState({}, '', path);
  navEl.classList.remove('open');
  window.scrollTo(0, 0);
  render();
}

document.getElementById('burger').addEventListener('click', () => {
  const open = navEl.classList.toggle('open');
  document.getElementById('burger').setAttribute('aria-expanded', String(open));
});

/* ------------------------------------------------------------- surface head */
function head(path, extra = '') {
  const r = ROUTES[path];
  return `<section class="surface-head"><div class="wrap">
    <div class="eyebrow">${esc(r.n)} &nbsp;/&nbsp; ${esc(r.who)}</div>
    <h1>${esc(r.title)}</h1>
    <p class="lead">${esc(r.blurb)}</p>
    ${extra}
  </div></section>`;
}

/* ------------------------------------------------------------- answer block */
function answerHTML(res, opts = {}) {
  const src = res.sources || [];
  // The server labels WHICH decline this is. A model refusal means the material
  // does not state it; a scope withhold means it does, elsewhere, and this desk
  // does not read that part. Saying the first sentence on the second path tells
  // a patient that information about their own procedure does not exist.
  const reason = res.decline || (/^NOT IN PUBLISHED CONTENT/i.test((res.answer || '').trim())
    ? 'not_published' : null);
  const declined = !!reason;
  // Keyed on (is this surface scoped, which decline fired). A scoped surface
  // hands the model a filtered slice, so a decline there can only ever mean the
  // slice lacked it - the corpus-wide sentence is a claim the code cannot
  // support, whichever path produced the decline. The two scoped notes differ by
  // exactly one claim, and the difference is the evidence: a scope WITHHOLD
  // fired because out-of-scope material actually grounded the answer, so we know
  // it exists; a model decline on a scoped surface tells us nothing about
  // elsewhere, so it stays silent about it.
  const DECLINE_NOTE = {
    'false|not_published': "Clinic's published material does not state this, so nothing has been generated to fill the gap.",
    'true|not_published': "This is not on the pages this desk reads. Nothing has been generated to fill the gap.",
    'true|scope': "The material exists - it is simply not on the pages this desk reads. Nothing has been generated to fill the gap.",
    'false|scope': "The material exists - it is simply not on the pages this desk reads. Nothing has been generated to fill the gap."
  };
  const noteKey = `${!!res.scoped}|${reason}`;
  // An unrecognised reason means the code does not know what happened, and the
  // default for not knowing is the NARROWER claim. Falling back to the
  // corpus-wide sentence would restore the original defect through the default
  // the moment a third decline reason exists - which is exactly how the first
  // one arrived. A scoped surface can never speak for the corpus, known reason
  // or not, so its fallback asserts only about this desk's own pages.
  // Only resolved when a decline is actually rendering. `reason` is null on
  // every normal answer, so an eager lookup asserts on the one case that is not
  // a decline at all - which is what the assertion caught on its first run.
  let note = '';
  if (declined) note = DECLINE_NOTE[noteKey];
  if (declined && !note) {
    console.error(`[decline] unrecognised decline key ${noteKey} - falling back to the narrower claim. Add it to DECLINE_NOTE.`);
    note = res.scoped
      ? "This is not on the pages this desk reads. Nothing has been generated to fill the gap."
      : "Nothing has been generated to fill the gap.";
  }
  const units = (res.sentences && res.sentences.length ? res.sentences : [{ text: res.answer, source: null }]);
  const body = renderUnits(units, u => (u.source != null && src[u.source]
    ? `<sup class="cite" data-src="${u.source}" title="${esc(src[u.source].title)}">${u.source + 1}</sup>` : ''));


  const sourcesHTML = src.map((s, i) => `
    <a class="sourcecard" id="src-${i}" href="${esc(s.url)}" target="_blank" rel="noopener">
      <div class="t">${i + 1}. ${esc(s.title)}</div>
      ${s.excerpt ? `<div class="x">${esc(s.excerpt)}</div>` : ''}
      <div class="f">
        ${s.doctype ? `<span class="tag">${esc(s.doctype)}</span>` : ''}
        ${s.date ? `<span>${esc(niceDate(s.date))}</span>` : ''}
        ${s.relevance != null ? `<span class="relbar"><i style="width:${Math.round(Math.min(1, s.relevance) * 100)}%"></i></span><span>${Math.round(Math.min(1, s.relevance) * 100)}% relevance</span>` : ''}
      </div>
    </a>`).join('');

  return `<div class="answer-block fade">
    <div class="answer-head">
      ${opts.question ? `<div class="qline">${esc(opts.question)}</div>` : '<div></div>'}
      ${declined ? '<span class="badge unknown"><span class="pip"></span>Answer withheld</span>'
        : `<span style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
          ${res.statements ? `<span class="badge neutral"><span class="pip"></span>${res.matched} of ${res.statements} statement${res.statements === 1 ? '' : 's'} matched to a source</span>` : ''}
          <span class="badge ${esc(res.confidence.tone)}" title="${esc(res.confidence.detail)}">
          <span class="pip"></span>${esc(res.confidence.label)}</span></span>`}
    </div>
    ${declined ? `<div class="declinebox">
        <b>The desk declined to answer.</b><br>${mdInline(res.answer.replace(/^NOT IN PUBLISHED CONTENT\s*[-:]*\s*/i, ''))}
        <br><span class="tiny">${esc(note)}</span>
      </div>`
      : `<div class="answer-body">${body}</div>`}
    ${declined ? '' : `<p class="tiny muted" style="margin-top:18px">${esc(res.confidence.detail)}</p>`}
    ${opts.safety ? `<div class="saferail"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2 4 6v6c0 5 3.4 9.3 8 10 4.6-.7 8-5 8-10V6z"/><path d="M12 8v4M12 16h.01"/></svg><div>${esc(opts.safety)}</div></div>` : ''}
    <!-- The SERVER is the guarantee here: a decline returns zero sources, so
         src.length is already 0 on every decline path and this gate renders
         nothing to hide. The !declined half is a second layer for a surface
         that might later compose its own payload without routing through
         declined() - it is not what makes the guarantee true, and the reveal
         says so. This heading is why the gate matters: "Sources read for this
         answer" asserts they were read FOR an answer that was refused. -->
    ${!declined && src.length ? `<div class="sect"><h4>Sources read for this answer &middot; ${src.length} of ${num(res.retrieved)} retrieved</h4>
      <div style="display:grid;gap:12px">${sourcesHTML}</div></div>` : ''}
  </div>`;
}

function wireCitations(scope) {
  scope.querySelectorAll('sup.cite').forEach(el => el.addEventListener('click', () => {
    const t = scope.querySelector('#src-' + el.dataset.src);
    if (!t) return;
    t.scrollIntoView({ behavior: 'smooth', block: 'center' });
    t.classList.add('flash');
    setTimeout(() => t.classList.remove('flash'), 1600);
  }));
}

/* ============================================================= HOME */
function home() {
  const c = CFG.corpus;
  view.innerHTML = `
  <section class="hero"><div class="wrap">
    <div class="hero-inner">
      <div class="hero-copy">
        <div class="eyebrow">Clinic Knowledge Desk</div>
        <h1>The evidence your team keeps <strong>re-assembling by hand</strong></h1>
        <p class="lead">Hospital approval submissions, rep and surgeon questions, TGA and FDA positions - all answered from the same body of Clinic material, with the source behind every claim.</p>
        <p class="lead" style="font-size:1rem">Seven desks over ${num(c.documents)} pages Clinic has published, including ${num(c.announcements)} market announcements going back to ${c.earliest.slice(0, 4)}. Every answer is generated at the moment it is asked. Where the content does not say, the desk says so rather than filling the gap.</p>
      </div>
      <div class="hero-art" style="background-image:url('/assets/img/Hand-doctor-and-patient.jpeg')"></div>
    </div>
    <div class="rule"></div>

    <div class="stats">
      <div class="stat"><div class="v">${num(c.documents)}</div><div class="k">published Clinic pages read</div></div>
      <div class="stat"><div class="v">${num(c.announcements)}</div><div class="k">market announcements, ${c.earliest.slice(0, 4)} to ${c.latest.slice(0, 4)}</div></div>
      <div class="stat"><div class="v">${num(c.practitioner + c.patient)}</div><div class="k">practitioner and patient pages</div></div>
      <div class="stat"><div class="v">7</div><div class="k">working desks over one body of content</div></div>
    </div>
  </div></section>

  <section class="wrap" style="padding:56px 0 20px">
    <div class="eyebrow blue">Seven desks, one body of content</div>
    <h2>Pick the job you are trying to do</h2>
    <div class="desk-grid">
      ${Object.entries(ROUTES).filter(([p]) => p !== '/').map(([p, r]) => `
        <a class="desk-card" href="${p}" data-link>
          <div class="n">${esc(r.n)}</div>
          <h3>${esc(r.title)}</h3>
          <p>${esc(r.blurb)}</p>
          <div class="go">${esc(r.who)} &rarr;</div>
        </a>`).join('')}
    </div>
  </section>

  <section class="wrap" style="padding:26px 0 70px">
    <div class="cta-band">
      <div style="max-width:60ch">
        <h3 style="margin-bottom:6px">Built on Clinic's live website, in a morning</h3>
        <p style="margin:0">Nothing here was hand-written for the demonstration, and no record is simulated. The desk read ${num(c.documents)} pages from clinic.com and every answer is generated against them at the moment you ask.</p>
      </div>
      <button class="btn" id="openReveal2">See how this works</button>
    </div>
  </section>`;
  const b = document.getElementById('openReveal2');
  if (b) b.addEventListener('click', () => openReveal());
}


/* ============================================================= 01 VAC DESK */
function pipelineChart(series) {
  if (series.length < 2) return '';
  const W = 320, H = 96, pad = 22;
  const max = Math.max(...series.map(r => Math.max(r.approvals, r.in_progress)));
  const bw = (W - pad) / series.length;
  let bars = '';
  series.forEach((r, i) => {
    const x = pad + i * bw;
    const ha = (H - 26) * (r.approvals / max), hp = (H - 26) * (r.in_progress / max);
    bars += `<rect x="${x + bw * .12}" y="${H - 20 - ha}" width="${bw * .32}" height="${Math.max(2, ha)}" rx="2" fill="#004D7E"><title>${r.date}: ${r.approvals} approvals</title></rect>`;
    bars += `<rect x="${x + bw * .5}" y="${H - 20 - hp}" width="${bw * .32}" height="${Math.max(2, hp)}" rx="2" fill="#AFB936"><title>${r.date}: ${r.in_progress} in progress</title></rect>`;
    bars += `<text x="${x + bw * .47}" y="${H - 6}" text-anchor="middle" font-size="10" fill="#7C8A95" font-family="Poppins,sans-serif">${niceDate(r.date).split(' ').slice(1).join(' ')}</text>`;
  });
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" height="${H}" role="img" aria-label="Published VAC approvals and applications in progress over time">${bars}</svg>`;
}

async function vacDesk() {
  view.innerHTML = head('/vac-desk') + `<div class="wrap"><div id="out">${thinking('Loading the published approval pipeline...')}</div></div>`;
  const out = document.getElementById('out');
  let data;
  try { data = await api('/api/vac-pipeline'); }
  catch (e) { out.innerHTML = errorBox(e.message); wireRetry(out, vacDesk); return; }
  const L = data.latest || {};

  out.innerHTML = `
    <div class="vac-strip">
      <div class="vac-stats">
        ${[['Approvals secured', L.approvals], ['Hospitals reached', L.hospitals], ['Applications in progress', L.in_progress]]
          .filter(x => x[1] != null).map(([k, v]) => `<div class="vstat"><div class="v">${num(v)}</div><div class="k">${esc(k)}</div></div>`).join('')}
      </div>
      <div class="vac-chart">
        <div class="tiny muted" style="font-family:var(--head);font-weight:600;margin-bottom:6px">
          <span style="color:var(--blue)">&#9632;</span> approvals secured &nbsp;
          <span style="color:var(--olive-deep)">&#9632;</span> applications in progress</div>
        ${pipelineChart(data.series)}
      </div>
    </div>
    <p class="vac-quote">&ldquo;${esc(L.quote || '')}&rdquo;
      <a href="${esc(L.url || '')}" target="_blank" rel="noopener">${esc(L.title || '')}</a>, ${esc(niceDate(L.date))}</p>

    <div class="vac-context">
      ${data.context.map(c => `<div class="vcard">
        <div class="l">${esc(c.label)}</div>
        <p>&ldquo;${esc(c.quote)}&rdquo;</p>
        <a class="tiny" href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.title)}</a> <span class="tiny muted">&middot; ${esc(niceDate(c.date))}</span>
      </div>`).join('')}
    </div>

    <div class="vac-work">
      <div>
        <div class="eyebrow blue">Draft a response</div>
        <h2 style="margin-bottom:6px">What is the committee asking?</h2>
        <p class="muted" style="max-width:60ch">These are the standard evidence criteria a hospital Value Analysis Committee works through. Pick one and the desk drafts the response from Clinic's published material.</p>
        <div class="criteria">${data.criteria.map(c => `<button class="crit" data-q="${esc(c.q)}">
          <span class="c">${esc(c.criterion)}</span><span class="q">${esc(c.q)}</span></button>`).join('')}</div>
        <div id="draft"></div>
      </div>
      <aside class="rail">
        <div class="card" style="padding:22px">
          <h4>What is powering this</h4>
          <p style="font-size:.93rem">Every figure above is transcribed from a sentence Clinic published, shown next to it and linked. The draft below is generated at the moment you ask it, from ${num(CFG.corpus.documents)} pages of their own published clinical, regulatory and commercial material.</p>
          <p style="font-size:.93rem;margin:0"><b style="color:var(--blue);font-family:var(--head)">No submission record is simulated here.</b> In a live deployment this desk reads the real submission files, committee correspondence and evidence dossiers. It is shown here against published material only, so nothing on screen is invented.</p>
        </div>
        <div class="card" style="padding:22px;margin-top:16px">
          <h4>Why the gaps panel matters</h4>
          <p style="font-size:.93rem;margin:0">A committee submission fails on what it cannot substantiate, not on what it can. The desk names those gaps before the submission goes out, rather than after the committee finds them.</p>
        </div>
      </aside>
    </div>`;

  const draft = document.getElementById('draft');
  let runToken = 0;

  async function run(q) {
    const mine = ++runToken;
    out.querySelectorAll('.crit').forEach(b => b.classList.toggle('on', b.dataset.q === q));
    // Two panes, two calls, painted independently - the draft appears as soon as
    // it is written rather than waiting for the reviewer pass behind it.
    draft.innerHTML = `<div id="pane-review"></div><div id="pane-draft">${thinking('Drafting from the published evidence...')}</div><div id="pane-gaps"></div>`;
    draft.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    // If the draft declines, the reviewer's output is withheld too. A strongest
    // point beside "the published content does not say" reads as an answer to a
    // question that was just refused, even when the sentence itself is real.
    const state = { declined: false, review: null, painted: false };
    function paintReview() {
      if (mine !== runToken || !state.review) return;
      const res = state.review;
      const rev = document.getElementById('pane-review'), gaps = document.getElementById('pane-gaps');
      if (!rev || !gaps) return;
      if (state.declined) {
        rev.innerHTML = '';
        gaps.innerHTML = `<p class="tiny muted" style="margin-top:18px">The desk declined to answer this from the published material, so the submission review is withheld as well - there is nothing here for it to review.</p>`;
        return;
      }
      rev.innerHTML = res.strongest_point ? `<div class="strongest fade">
          <div class="eyebrow" style="color:var(--olive-deep);margin-bottom:8px">Strongest published point</div>
          <div class="sp">${mdInline(res.strongest_point)}</div>
          ${res.strongest_source ? `<p class="tiny" style="margin:10px 0 0">Quoted from <a href="${esc(res.strongest_source.url)}" target="_blank" rel="noopener">${esc(res.strongest_source.title)}</a></p>` : ''}
        </div>` : '';
      gaps.innerHTML = `
        ${(res.gaps || []).length ? `<div class="gaps fade">
          <div class="eyebrow" style="color:var(--amber)">What the published evidence does not establish</div>
          <p style="margin-bottom:16px">The desk raises these before the submission goes out. Nothing below is a finding about the product - it is what a committee would reasonably ask for that the published material does not answer.</p>
          ${res.gaps.map(g => `<div class="gap"><b>${esc(g.gap)}</b><p>${esc(g.why_it_matters)}</p></div>`).join('')}
        </div>` : ''}
        ${(res.attachments || []).length ? `<div class="sect"><h4>Documents a submission should attach</h4>
          <ul class="attach">${res.attachments.map(a => `<li>${esc(a)}</li>`).join('')}</ul>
          <p class="tiny muted">Categories of document, not specific files - the desk does not invent a document it has not read.</p></div>` : ''}`;
    }

    api('/api/vac-desk/draft', { question: q }, 35000).then(res => {
      if (mine !== runToken) return;
      state.declined = !!(res.decline || /^NOT IN PUBLISHED CONTENT/i.test((res.answer || '').trim()));
      const pane = document.getElementById('pane-draft');
      pane.innerHTML = answerHTML(res, { question: 'Drafted response' });
      wireCitations(pane);
      paintReview();
    }).catch(e => {
      if (mine !== runToken) return;
      const pane = document.getElementById('pane-draft');
      pane.innerHTML = errorBox(e.message); wireRetry(pane, () => run(q));
    });

    document.getElementById('pane-gaps').innerHTML = thinking('Reviewing it for what the evidence does not establish...');
    api('/api/vac-desk/review', { question: q }, 35000).then(res => {
      if (mine !== runToken) return;
      state.review = res;
      paintReview();
    }).catch(e => {
      if (mine !== runToken) return;
      const pane = document.getElementById('pane-gaps');
      pane.innerHTML = errorBox(e.message); wireRetry(pane, () => run(q));
    });
  }
  out.querySelectorAll('.crit').forEach(b => b.addEventListener('click', () => run(b.dataset.q)));
}

/* ============================================================= 02 SURGEON */
const SURGEON_QS = [
  'What is Remplir made from and how does it support nerve repair?',
  'In which procedures can Remplir be used?',
  'How should Striate+ be handled and prepared before placement?',
  'What is the difference between OrthoACI and OrthoATI?',
  'Is the instructions-for-use document the same in every country?',
  'What clinical evidence has been published for OrthoATI in lateral epicondylitis?'
];

function surgeon() {
  view.innerHTML = head('/surgeon-desk', `<div class="metaline">
      <span>Reads <b>${num(CFG.corpus.documents)}</b> published pages</span>
      <span>Every sentence carries its source</span>
      <span>Declines rather than infers</span>
    </div>`) + `
  <div class="wrap"><div class="two-col">
    <div>
      <div class="asklab">
        <div class="grow">
          <label class="tiny muted" for="q" style="display:block;margin-bottom:7px;font-family:var(--head);font-weight:600">Ask a clinical question</label>
          <input type="text" id="q" placeholder="e.g. What is Remplir made from and how does it support nerve repair?">
        </div>
        <button class="btn" id="askBtn">Ask the desk</button>
      </div>
      <div class="prompts">${SURGEON_QS.map(q => `<button class="chip" data-q="${esc(q)}">${esc(q)}</button>`).join('')}</div>
      <div id="out"></div>
    </div>
    <aside class="rail">
      <div class="card" style="padding:22px">
        <h4>What this desk will not do</h4>
        <p style="font-size:.93rem">It will not state a clinical outcome, efficacy figure, approval status, indication or safety conclusion that Clinic has not published. Ask it one and it will tell you the content does not say.</p>
        <p style="font-size:.93rem;margin:0">Try: <button class="chip small" data-q="How does Remplir compare with a competitor nerve wrap in a head-to-head randomised trial?" style="margin-top:8px;text-align:left;white-space:normal">How does Remplir compare with a competitor nerve wrap in a head-to-head randomised trial?</button></p>
      </div>
      <div class="card" style="padding:22px;margin-top:16px">
        <h4>Need a person</h4>
        <p style="font-size:.93rem">Clinical and product questions beyond the published material go to the Clinic team.</p>
        <a class="btn ghost small" href="https://clinic.com/contact/" target="_blank" rel="noopener">Contact Clinic</a>
      </div>
    </aside>
  </div></div>`;

  const out = document.getElementById('out');
  const input = document.getElementById('q');

  async function ask(q) {
    if (!q || q.trim().length < 3) return;
    input.value = q;
    out.innerHTML = thinking('Reading Clinic\'s published material...');
    try {
      const res = await api('/api/surgeon-desk', { question: q });
      out.innerHTML = answerHTML(res, { question: q });
      wireCitations(out);
    } catch (e) { out.innerHTML = errorBox(e.message); wireRetry(out, () => ask(q)); }
  }
  document.getElementById('askBtn').addEventListener('click', () => ask(input.value));
  input.addEventListener('keydown', e => { if (e.key === 'Enter') ask(input.value); });
  view.querySelectorAll('[data-q]').forEach(b => b.addEventListener('click', () => ask(b.dataset.q)));
}

/* ============================================================= 02 MARKET */
const STATUS_COLOUR = {
  'Regulatory approval or clearance stated': ['#3B6B33', '#5F8C45'],
  'Commercially available or launched': ['#00557F', '#1D6390'],
  'Distribution or supply arrangement stated': ['#4A5C6B', '#7C8A95'],
  'Restricted or special access pathway stated': ['#85560D', '#C77A14'],
  'Submission or application stated, outcome not stated': ['#6B5B8A', '#8A7CB0']
};

function market() {
  const prods = Object.entries(CFG.corpus.products);
  view.innerHTML = head('/market-access', `
    <div class="prodpick">${prods.map(([p, n], i) =>
      `<button class="chip ${i === 0 ? 'on' : ''}" data-p="${esc(p)}">${esc(p)}<span class="n">${n}</span></button>`).join('')}</div>`) + `
  <div class="wrap" style="padding:30px 0 70px"><div id="out"></div></div>`;

  const out = document.getElementById('out');
  let token = 0;

  function skeleton(p) {
    return `<div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap">
        <h2 style="margin:0">${esc(p)}</h2>
        <span class="muted" id="stage1">Reading the published announcements...</span>
      </div>
      <div class="matrix">${[0, 1, 2, 3, 4, 5].map(() => `<div class="mcard skel">
        <div class="bar" style="background:var(--line)"></div>
        <div class="body"><div class="sk sk-t"></div><div class="sk sk-s"></div>
          <div class="sk sk-p"></div><div class="sk sk-p"></div><div class="sk sk-p" style="width:62%"></div></div>
      </div>`).join('')}</div>
      <p class="tiny muted" style="margin-top:18px" id="stage2">Composing the position for each market from those pages. This takes a few seconds - each card is quoted verbatim from the page it came from.</p>`;
  }

  async function load(p) {
    const mine = ++token;
    view.querySelectorAll('[data-p]').forEach(b => b.classList.toggle('on', b.dataset.p === p));
    out.innerHTML = skeleton(p);

    // stage one paints the real retrieval count in about a second
    api('/api/market-access/pages', { product: p }, 20000).then(pg => {
      if (mine !== token) return;
      const el = document.getElementById('stage1');
      if (el) el.textContent = `${num(pg.retrieved)} published pages retrieved`;
    }).catch(() => { /* stage two still carries the surface */ });

    try {
      const res = await api('/api/market-access', { product: p }, 35000);
      if (mine !== token) return;
      if (!res.markets.length) {
        out.innerHTML = `<div class="declinebox">
          <b>No market position is stated in the published content for ${esc(p)}.</b><br>
          The desk found ${num(res.retrieved)} pages mentioning this product but none that state a regulatory or commercial position by market, so nothing has been assembled.</div>`;
        return;
      }
      out.innerHTML = `
        <div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap">
          <h2 style="margin:0">${esc(p)}</h2>
          <span class="muted">${res.markets.length} market position${res.markets.length === 1 ? '' : 's'} found across ${num(res.retrieved)} retrieved pages</span>
        </div>
        <div class="matrix">${res.markets.map((m, i) => {
          const c = STATUS_COLOUR[m.status] || ['#4A5C6B', '#7C8A95'];
          return `<div class="mcard fade" style="animation-delay:${Math.min(i * 60, 420)}ms">
            <div class="bar" style="background:linear-gradient(90deg,${c[0]},${c[1]})"></div>
            <div class="body">
              <div class="market">${esc(m.market)}</div>
              <div class="status" style="color:${c[0]}">${esc(m.status)}</div>
              <div class="pos">&ldquo;${mdInline(m.position)}&rdquo;</div>
            </div>
            ${m.source ? `<div class="src">Quoted from <a href="${esc(m.source.url)}" target="_blank" rel="noopener">${esc(m.source.title)}</a>${m.source.date ? ` &middot; ${esc(niceDate(m.source.date))}` : ''}</div>` : ''}
          </div>`;
        }).join('')}</div>
        ${(res.mentioned_only || []).length ? `<p class="tiny muted" style="margin-top:16px">
          Named in passing in other announcements but with no position statement of their own, so no card is shown:
          <b>${res.mentioned_only.map(esc).join(', ')}</b>.</p>` : ''}
        ${res.not_stated.length ? `<div class="notstated">
          <div class="eyebrow" style="color:var(--amber)">Not stated in the published content</div>
          <p style="margin-bottom:12px">The desk records these gaps rather than reasoning across them. Nothing below has been inferred from what is published.</p>
          <ul>${res.not_stated.map(x => `<li>${mdInline(x)}</li>`).join('')}</ul></div>` : ''}
        <div class="sect"><h4>Pages this position was assembled from</h4>
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px">
          ${res.sources.map(s => `<a class="sourcecard" href="${esc(s.url)}" target="_blank" rel="noopener">
            <div class="t">${esc(s.title)}</div>
            <div class="f">${s.doctype ? `<span class="tag">${esc(s.doctype)}</span>` : ''}${s.date ? `<span>${esc(niceDate(s.date))}</span>` : ''}</div></a>`).join('')}</div></div>`;
    } catch (e) {
      if (mine !== token) return;
      out.innerHTML = errorBox(e.message);
      wireRetry(out, () => load(p));
    }
  }
  view.querySelectorAll('[data-p]').forEach(b => b.addEventListener('click', () => load(b.dataset.p)));
  load(prods[0][0]);
}

/* ============================================================= 03 CLAIM */
const CLAIM_EXAMPLES = [
  'Remplir is a resorbable collagen nerve wrap for the management of peripheral nerve injuries.',
  'Remplir has been shown to restore full sensation in the majority of patients within six months.',
  'Striate+ is distributed globally by BioHorizons.',
  'OrthoATI is approved in Australia for the treatment of tendinopathy.',
  'Clinic manufactures to ISO 13485 and is licensed by the TGA.'
];

function claim() {
  view.innerHTML = head('/claim-check', `<div class="metaline">
      <span>Conservative by design</span>
      <span>Quotes the supporting wording, or says there is none</span>
      <span>Suggests wording that stays inside the evidence</span>
    </div>`) + `
  <div class="wrap"><div class="claim-stage">
    <label class="tiny muted" for="c" style="display:block;margin-bottom:8px;font-family:var(--head);font-weight:600">Paste the sentence you are thinking of using</label>
    <textarea id="c" rows="3" placeholder="Remplir has been shown to restore full sensation in the majority of patients within six months."></textarea>
    <div style="display:flex;gap:12px;align-items:center;margin-top:14px;flex-wrap:wrap">
      <button class="btn" id="checkBtn">Check this claim</button>
      <span class="tiny muted">Checked against Clinic's own published content only.</span>
    </div>
    <div class="sect"><h4>Try one of these</h4>
      <div class="prompts">${CLAIM_EXAMPLES.map(c => `<button class="chip" data-c="${esc(c)}" style="white-space:normal;text-align:left;max-width:100%">${esc(c)}</button>`).join('')}</div></div>
    <div id="out"></div>
  </div></div>`;

  const out = document.getElementById('out');
  const ta = document.getElementById('c');

  const VERDICT_CLASS = {
    'Supported by published content': 'ok',
    'Partly supported - wording goes further than the content': 'part',
    'Not supported by published content': 'no'
  };

  async function check(text) {
    if (!text || text.trim().length < 8) return;
    ta.value = text;
    out.innerHTML = thinking('Checking the claim against the published content...');
    try {
      const res = await api('/api/claim-check', { claim: text });
      // The server declined: nothing came back close enough to check against,
      // so there is no verdict, no quote and no pages-checked list. Rendered as
      // a decline rather than as a verdict, because "not supported" would be a
      // finding about the published content that this run has no evidence for.
      if (res.declined) {
        out.innerHTML = `<div class="fade" style="margin-top:34px"><div class="declinebox">
          <b>The desk declined to check this claim.</b><br>
          Nothing in Clinic's published content came back closely enough to check this
          wording against, so no verdict has been reached and no evidence has been assembled.
          <br><span class="tiny">A decline is not a finding either way - it does not mean the
          claim is unsupported, only that this desk found nothing to judge it against.</span>
        </div></div>`;
        return;
      }
      const cls = VERDICT_CLASS[res.verdict] || 'part';
      out.innerHTML = `<div class="fade" style="margin-top:34px">
        <div class="verdict ${cls}">
          <div class="v">${esc(res.verdict || 'No verdict returned')}</div>
          <div style="margin:12px 0 0">${mdBlock(res.explanation || '')}</div>
        </div>
        ${res.evidence_quote ? `<div class="sect"><h4>Closest published wording</h4>
          <div class="quote">&ldquo;${mdInline(res.evidence_quote)}&rdquo;</div>
          ${res.source ? `<p class="tiny" style="margin-top:10px">From <a href="${esc(res.source.url)}" target="_blank" rel="noopener">${esc(res.source.title)}</a></p>` : ''}</div>`
          : `<div class="sect"><h4>Closest published wording</h4><p class="muted">No wording in the published content comes close enough to quote.</p></div>`}
        ${(res.unsupported_elements || []).length ? `<div class="sect"><h4>Parts the published content does not state</h4>
          <ul class="unsup">${res.unsupported_elements.map(u => `<li>${mdInline(u)}</li>`).join('')}</ul></div>` : ''}
        ${res.safer_wording ? `<div class="sect"><h4>Wording that stays inside the evidence</h4>
          <div class="rewrite"><div style="margin:0 0 14px;color:var(--ink)">${mdBlock(res.safer_wording)}</div>
            <button class="btn ghost small" id="copyBtn">Copy this wording</button></div></div>` : ''}
        <div class="sect"><h4>Pages checked &middot; ${num(res.retrieved)} retrieved</h4>
          <div style="display:grid;gap:12px">${(res.sources || []).map(s =>
            `<a class="sourcecard" href="${esc(s.url)}" target="_blank" rel="noopener">
              <div class="t">${esc(s.title)}</div>${s.excerpt ? `<div class="x">${esc(s.excerpt)}</div>` : ''}
              <div class="f">${s.doctype ? `<span class="tag">${esc(s.doctype)}</span>` : ''}${s.relevance != null ? `<span class="relbar"><i style="width:${Math.round(Math.min(1, s.relevance) * 100)}%"></i></span><span>${Math.round(Math.min(1, s.relevance) * 100)}% relevance</span>` : ''}</div></a>`).join('')}</div></div>
      </div>`;
      const cb = document.getElementById('copyBtn');
      if (cb) cb.addEventListener('click', () => {
        navigator.clipboard.writeText(res.safer_wording).then(() => { cb.textContent = 'Copied'; setTimeout(() => cb.textContent = 'Copy this wording', 1800); });
      });
    } catch (e) { out.innerHTML = errorBox(e.message); wireRetry(out, () => check(text)); }
  }
  document.getElementById('checkBtn').addEventListener('click', () => check(ta.value));
  view.querySelectorAll('[data-c]').forEach(b => b.addEventListener('click', () => check(b.dataset.c)));
}

/* ============================================================= 04 INVESTOR */
const THEME_COLOUR = {
  'Regulatory and approvals': '#004D7E',
  'Market entry and commercial': '#1D6390',
  'Clinical and evidence': '#346D68',
  'Capital and corporate': '#7C8A95',
  'Manufacturing and operations': '#5F8C45',
  'Intellectual property': '#6B5B8A',
  'Media and analyst coverage': '#8A9328',
  'Recognition and events': '#AFB936',
  'Company update': '#C9D4DC'
};

function chartSVG(data, hidden) {
  const themes = data.themes.filter(t => !hidden.has(t));
  const years = data.years;
  const W = Math.max(720, years.length * 52), H = 300, PADL = 38, PADB = 34, PADT = 14;
  const max = Math.max(1, ...years.map(y => themes.reduce((a, t) => a + data.matrix[y][t], 0)));
  const bw = (W - PADL - 12) / years.length;
  const scale = v => (H - PADB - PADT) * (v / max);
  let bars = '';
  years.forEach((y, i) => {
    let acc = 0;
    themes.forEach(t => {
      const v = data.matrix[y][t];
      if (!v) return;
      const h = scale(v);
      acc += h;
      bars += `<rect x="${PADL + i * bw + bw * 0.16}" y="${H - PADB - acc}" width="${bw * 0.68}" height="${Math.max(1, h - 1)}" fill="${THEME_COLOUR[t]}" rx="2"><title>${y} &middot; ${t}: ${v}</title></rect>`;
    });
    if (i % (years.length > 12 ? 2 : 1) === 0) {
      bars += `<text x="${PADL + i * bw + bw / 2}" y="${H - PADB + 17}" text-anchor="middle" font-size="11" fill="#7C8A95" font-family="Poppins,sans-serif">${y.slice(2)}</text>`;
    }
  });
  let grid = '';
  for (let g = 0; g <= 4; g++) {
    const v = Math.round(max * g / 4), y = H - PADB - scale(v);
    grid += `<line x1="${PADL}" y1="${y}" x2="${W - 8}" y2="${y}" stroke="#EEF2F5"/>
             <text x="${PADL - 8}" y="${y + 4}" text-anchor="end" font-size="10" fill="#7C8A95" font-family="Poppins,sans-serif">${v}</text>`;
  }
  return `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="Clinic announcements by year and theme">${grid}${bars}</svg>`;
}

async function investor() {
  view.innerHTML = head('/investor-signal') + `<div class="wrap"><div id="out">${thinking('Loading the announcement record...')}</div></div>`;
  const out = document.getElementById('out');
  let data;
  try { data = await api('/api/investor-signal'); }
  catch (e) { out.innerHTML = errorBox(e.message); wireRetry(out, investor); return; }

  const hidden = new Set();
  let activeTheme = data.themes[0];

  function paint() {
    out.innerHTML = `
      <div class="inv-grid">
        <div>
          <div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin-bottom:6px">
            <h2 style="margin:0">${num(data.total)} announcements</h2>
            <span class="muted">${data.years[0]} to ${data.years[data.years.length - 1]} &middot; ${data.themes.length} themes</span>
          </div>
          <div class="chart">${chartSVG(data, hidden)}</div>
          <div class="legend">${data.themes.map(t =>
            `<button data-t="${esc(t)}" class="${hidden.has(t) ? 'off' : ''}"><span class="sw" style="background:${THEME_COLOUR[t]}"></span>${esc(t)} <b style="color:var(--blue)">${data.theme_totals[t]}</b></button>`).join('')}</div>

          <div class="sect" style="margin-top:38px">
            <h4>Brief me on a theme</h4>
            <div class="prompts">${data.themes.map(t =>
              `<button class="chip ${t === activeTheme ? 'on' : ''}" data-brief="${esc(t)}">${esc(t)}<span class="n">${data.theme_totals[t]}</span></button>`).join('')}</div>
            <div id="digest"></div>
          </div>
        </div>
        <aside>
          <h4 style="font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;color:var(--grey-soft);font-weight:700">Most recent</h4>
          ${data.recent.map(a => `<a class="annrow" href="${esc(a.url)}" target="_blank" rel="noopener">
            <div class="d">${esc(niceDate(a.date))}</div>
            <div><div class="t">${esc(a.title)}</div><div class="th">${esc(a.theme)}</div></div></a>`).join('')}
        </aside>
      </div>`;

    out.querySelectorAll('[data-t]').forEach(b => b.addEventListener('click', () => {
      const t = b.dataset.t;
      hidden.has(t) ? hidden.delete(t) : hidden.add(t);
      paint();
    }));
    out.querySelectorAll('[data-brief]').forEach(b => b.addEventListener('click', () => brief(b.dataset.brief)));
    if (loadedDigest) document.getElementById('digest').innerHTML = loadedDigest;
  }

  let loadedDigest = '';
  async function brief(theme) {
    activeTheme = theme;
    const d = document.getElementById('digest');
    d.innerHTML = thinking(`Reading the ${theme.toLowerCase()} announcements...`);
    out.querySelectorAll('[data-brief]').forEach(b => b.classList.toggle('on', b.dataset.brief === theme));
    try {
      const res = await api('/api/investor-digest', { theme });
      loadedDigest = answerHTML(res, { question: `${theme} - ${res.scope.announcements} announcements` });
      d.innerHTML = loadedDigest;
      wireCitations(d);
    } catch (e) { d.innerHTML = errorBox(e.message); loadedDigest = ''; wireRetry(d, () => brief(theme)); }
  }
  paint();
}

/* ============================================================= 05 PATIENT */
const JOURNEY = [
  { q: 'What is Remplir and why might my surgeon use it?', h: 'Nerve repair' },
  { q: 'What happens during OrthoACI cartilage treatment?', h: 'Cartilage' },
  { q: 'What is a Striate+ dental membrane used for?', h: 'Dental' },
  { q: 'Is Remplir made from human tissue?', h: 'What it is made of' },
  { q: 'What is it like to recover after nerve repair surgery?', h: 'Recovery' },
  { q: 'How do I find a surgeon who uses these treatments?', h: 'Next step' }
];

function patient() {
  view.innerHTML = `
  <section class="patient-hero"><div class="wrap">
    <div class="eyebrow" style="color:#DDE4A8">05 &nbsp;/&nbsp; Patients and carers</div>
    <h1 style="max-width:20ch">Plain answers about <strong>your treatment</strong></h1>
    <p class="lead" style="max-width:62ch">Written from Clinic's own patient pages, in everyday language. This desk will never tell you whether a treatment is right for you - that is a conversation with your surgeon.</p>
    <div class="journey">${JOURNEY.map(j => `<button class="jcard" data-q="${esc(j.q)}"><div class="h">${esc(j.h)}</div><div class="q">${esc(j.q)}</div></button>`).join('')}</div>
  </div></section>
  <div class="wrap"><div style="padding:36px 0 70px;max-width:840px">
    <div class="asklab">
      <div class="grow">
        <label class="tiny muted" for="q" style="display:block;margin-bottom:7px;font-family:var(--head);font-weight:600">Or ask in your own words</label>
        <input type="text" id="q" placeholder="e.g. What is Remplir and why might my surgeon use it?">
      </div>
      <button class="btn" id="askBtn">Ask</button>
    </div>
    <div id="out"></div>
    <div class="cta-band">
      <div style="max-width:52ch">
        <h3 style="margin-bottom:6px">Talk to someone about your treatment</h3>
        <p style="margin:0">Your surgeon or treating clinician is the right person to answer questions about your own care. Clinic can help you find a practitioner.</p>
      </div>
      <div style="display:flex;gap:12px;flex-wrap:wrap">
        <a class="btn" href="https://clinic.com/contact/" target="_blank" rel="noopener">Contact Clinic</a>
        <a class="btn ghost" href="https://clinic.com/patients/" target="_blank" rel="noopener">Patient information</a>
      </div>
    </div>
  </div></div>`;

  const out = document.getElementById('out');
  const input = document.getElementById('q');
  async function ask(q) {
    if (!q || q.trim().length < 3) return;
    input.value = q;
    out.innerHTML = thinking('Reading the patient pages...');
    try {
      const res = await api('/api/patient-guide', { question: q });
      out.innerHTML = answerHTML(res, { question: q, safety: res.safety });
      wireCitations(out);
    } catch (e) { out.innerHTML = errorBox(e.message); wireRetry(out, () => ask(q)); }
  }
  document.getElementById('askBtn').addEventListener('click', () => ask(input.value));
  input.addEventListener('keydown', e => { if (e.key === 'Enter') ask(input.value); });
  view.querySelectorAll('[data-q]').forEach(b => b.addEventListener('click', () => ask(b.dataset.q)));
}

/* ============================================================= 06 LIBRARY */
const DOCICON = { 'Product page': 'PROD', 'Instructions for use': 'IFU', 'Surgical technique': 'TECH', 'Clinical evidence': 'EVID', 'Patient information': 'PAT', 'Practitioner resource': 'PRAC', 'Patient story': 'STORY', 'Announcement': 'ASX', 'Corporate': 'CORP' };

/* Real Clinic product imagery, used only where it genuinely depicts that product. */
const PRODUCT_IMG = {
  'Remplir': '/assets/img/img.png',
  'OrthoACI': '/assets/img/orthoaci.png',
  'OrthoATI': '/assets/img/orthoati.png',
  'Striate+': '/assets/img/striate.png'
};

function libCard(d) {
  const prod = (d.products || []).find(p => PRODUCT_IMG[p]);
  const art = prod
    ? `background-image:url('${PRODUCT_IMG[prod]}');background-color:#F1F5F8`
    : (d.doctype === 'Announcement' ? 'background:linear-gradient(150deg,#004D7E,#1D6390)' : 'background:var(--grad-deep)');
  return `<a class="libcard" href="${esc(d.url)}" target="_blank" rel="noopener">
    <div class="thumb" style="${art}">
      <span class="mono">${esc(DOCICON[d.doctype] || 'DOC')}</span>
      <span class="kind">${esc((d.products || []).filter(p => p !== 'Company-wide').join(' / ') || 'Clinic')}</span>
    </div>
    <div class="b">
      <div class="t">${esc(d.title)}</div>
      <div class="f" style="margin:6px 0 0;font-weight:500;text-transform:none;letter-spacing:0">${esc(new URL(d.url).pathname)}</div>
      <div class="x">${esc((d.excerpt || '').slice(0, 130))}${(d.excerpt || '').length > 130 ? '...' : ''}</div>
      <div class="f">${esc(d.doctype)}${d.date ? ' &middot; ' + esc(niceDate(d.date)) : ''}${d.relevance != null ? ' &middot; ' + Math.round(Math.min(1, d.relevance) * 100) + '% relevance' : ''}</div>
    </div></a>`;
}

async function library() {
  view.innerHTML = head('/evidence-library') + `<div class="wrap"><div id="out">${thinking('Loading the library...')}</div></div>`;
  const out = document.getElementById('out');
  let data;
  try { data = await api('/api/library'); }
  catch (e) { out.innerHTML = errorBox(e.message); wireRetry(out, library); return; }

  const sel = { Product: null, 'Document type': null, Audience: null };

  function facetBlock(name) {
    return `<h4>${esc(name)}</h4>` + Object.entries(data.facets[name]).map(([k, v]) =>
      `<button data-f="${esc(name)}" data-v="${esc(k)}" class="${sel[name] === k ? 'on' : ''}">
        <span>${esc(k)}</span><span class="n">${v}</span></button>`).join('');
  }

  function paint(results) {
    out.innerHTML = `<div class="lib">
      <aside class="facets">
        <div style="display:flex;gap:10px">
          <input type="search" id="lq" placeholder="Search ${num(data.total)} pages" value="${esc(lastQuery)}">
        </div>
        <button class="btn small" id="searchBtn" style="width:100%;margin-top:10px">Search</button>
        ${facetBlock('Product')}${facetBlock('Document type')}${facetBlock('Audience')}
        <button class="btn ghost small" id="clearBtn" style="width:100%;margin-top:22px">Clear filters</button>
      </aside>
      <div>${results ? results : data.rails.map(r => `
        <div class="rail-row">
          <div class="hd"><h3>${esc(r.title)}</h3><span class="muted tiny">${r.count} page${r.count === 1 ? '' : 's'}</span></div>
          <div class="scroller">${r.items.map(libCard).join('')}</div>
        </div>`).join('')}</div>
    </div>`;

    out.querySelectorAll('[data-f]').forEach(b => b.addEventListener('click', () => {
      sel[b.dataset.f] = sel[b.dataset.f] === b.dataset.v ? null : b.dataset.v;
      search();
    }));
    document.getElementById('searchBtn').addEventListener('click', () => { lastQuery = document.getElementById('lq').value; search(); });
    document.getElementById('lq').addEventListener('keydown', e => { if (e.key === 'Enter') { lastQuery = e.target.value; search(); } });
    document.getElementById('clearBtn').addEventListener('click', () => {
      sel.Product = sel['Document type'] = sel.Audience = null; lastQuery = ''; paint(null);
    });
  }

  let lastQuery = '';
  async function search() {
    const anyFacet = sel.Product || sel['Document type'] || sel.Audience;
    if (!lastQuery && !anyFacet) { paint(null); return; }
    if (!lastQuery) {
      // facet-only browse resolves against the seeded record, no query needed
      const prod = sel.Product, dt = sel['Document type'], aud = sel.Audience;
      const rails = data.rails.flatMap(r => r.items);
      const seen = new Set();
      const items = rails.filter(d => {
        if (seen.has(d.url)) return false; seen.add(d.url);
        return (!prod || (d.products || []).includes(prod)) && (!dt || d.doctype === dt) && (!aud || d.audience === aud);
      });
      paint(`<div style="margin-bottom:16px" class="muted">${items.length} page${items.length === 1 ? '' : 's'} in this selection ${items.length >= 12 ? '(showing the most recent from each shelf - add a search term for the full set)' : ''}</div>
        <div class="resultgrid">${items.map(libCard).join('')}</div>`);
      return;
    }
    paint(thinking('Searching...'));
    try {
      const res = await api('/api/library/search', {
        query: lastQuery, product: sel.Product, doctype: sel['Document type'], audience: sel.Audience
      });
      paint(res.results.length
        ? `<div style="margin-bottom:16px" class="muted">${res.results.length} page${res.results.length === 1 ? '' : 's'} match &ldquo;${esc(lastQuery)}&rdquo;</div>
           <div class="resultgrid">${res.results.map(libCard).join('')}</div>`
        : `<div class="declinebox">Nothing in the library matches &ldquo;${esc(lastQuery)}&rdquo; closely enough to show. Try different words or clear the filters.</div>`);
    } catch (e) { paint(errorBox(e.message)); wireRetry(out, () => search()); }
  }
  paint(null);
}

/* ============================================================= REVEAL */
const REVEAL = {
  '/': {
    lead: 'Six desks, one retrieval stack. Nothing on any surface was written in advance - every answer is generated at the moment you ask it, against Clinic\'s own published pages.',
    nodes: [
      ['Clinic website', 'clinic.com pages read and stored as searchable records'],
      ['This application', 'Holds the retrieval credential server side; the browser never sees it'],
      ['Semantic retrieval', 'Finds the passages that actually relate to the question'],
      ['Grounded answer call', 'Writes the answer from those passages only'],
      ['Support check', 'Scores how well the answer is carried by the passages']
    ],
    mechs: [
      ['Content', `Every page in the desk came from clinic.com. No content was written, summarised or invented for the demonstration.`],
      ['Classification', 'Product, document type, audience and region are set from each page\'s own address and title at load time - deterministic rules, no model, no cost. A model is never asked to judge what kind of document something is.'],
      ['Retrieval scope', 'Each surface narrows retrieval to the right slice using those labels, so the patient guide cannot answer from a regulatory announcement.'],
      ['Refusal', 'Every surface is instructed to say the content does not state something rather than infer it. That refusal is a designed outcome, not a failure.'],
      ['A refusal carries nothing with it', 'When any surface declines, the server returns the refusal alone - no sources, no quotes, no highlighted passages, no support reading - rather than the client hiding them after the fact. This matters because the retrieved pages are real and on-topic enough to have been retrieved: asked which hospitals offer a procedure, the patient desk correctly refuses, and the pages it had retrieved genuinely name hospitals. Left standing under a refusal, headed as the sources read for this answer, they read as the answer that was just withheld. There are two reasons a surface declines - the material does not state it, or it does and this desk does not read that part - and both now carry nothing, which was true of the second from the start and is newly true of the first.']
    ]
  },
  '/vac-desk': {
    lead: 'Two calls running together over the same published material: one drafts the submission response, the other reviews it for what the evidence does not establish.',
    nodes: [
      ['Committee criterion', 'The evidence question a hospital committee actually works through'],
      ['Semantic retrieval', 'Finds the published clinical, regulatory and commercial passages that bear on it'],
      ['Grounded answer call', 'Drafts the response in submission register, from those passages only'],
      ['Structured answer call', 'Reviews the same passages for gaps, against a fixed response schema'],
      ['Support check', 'Scores the draft against what was retrieved']
    ],
    mechs: [
      ['The pipeline figures', 'Not generated. Each number is transcribed from a verbatim sentence in a real Clinic announcement, the sentence is shown on screen next to it and linked, and this application re-checks at start-up that the sentence genuinely appears in the page it claims - a figure whose sentence cannot be found is dropped rather than displayed.'],
      ['The draft', 'A grounded answer call over the published material, instructed to write in submission register and to refuse rather than infer. Every claim carries its source.'],
      ['The gaps panel', 'A separate structured answer call over the same passages, with a fixed response schema. It is the reviewer, not the author - which is why it is a second call and not a second paragraph of the first.'],
      ['What is NOT here', 'No hospital is named by this application, no application status is simulated, and no committee correspondence exists in this content. A production deployment reads the real submission files; this is the same mechanism shown against published material, and the page says so.']
    ]
  },
  '/surgeon-desk': {
    lead: 'A clinical question goes to semantic retrieval across all published pages, then to a grounded answer call that may only use what came back.',
    nodes: [
      ['Your question', 'Sent to this application, never to a third party from the browser'],
      ['Semantic retrieval', 'Ranks passages across every published page'],
      ['Neighbouring context', 'Pulls the passages either side so a sentence is not read out of context'],
      ['Grounded answer call', 'Generates the answer from those passages, with its own source list'],
      ['Support check', 'Scores the finished answer against the same passages']
    ],
    mechs: [
      ['Citation markers', 'The source list comes back from the grounded answer call itself. This application then aligns each sentence of the answer to the passage it most closely matches, so the marker sits at the claim rather than in a footnote. The alignment is ours; the sources are the platform\'s.'],
      ['Confidence badge', 'The platform scores the finished answer against the full set of retrieved passages. It is shown as a qualitative reading, never a number, because a number invites a precision the score does not have.'],
      ['What it measures, and where it is blunt', 'The check measures whether the answer\'s WORDING is carried by the retrieved passages - not whether the answer is clinically correct. Measured on this content: a single-claim explanatory answer scores high, a fabricated answer scores zero, and a LIST or a summary also scores low, because it restates rather than echoes. So the reading is shown next to a second, separate number - how many of the answer\'s own statements this application could match to a cited source - and next to the sources themselves. Neither is presented as a verdict.'],
      ['Refusal', 'The prompt forbids stating any clinical outcome, efficacy figure, approval, indication or safety conclusion that is not written in the retrieved content.']
    ]
  },
  '/market-access': {
    lead: 'Retrieval finds the real pages. Every market card is then built by this application, deterministically, from those pages\' own sentences - no model ever decides which markets appear.',
    nodes: [
      ['Product selected', 'Narrows retrieval to pages labelled with that product'],
      ['Semantic retrieval', 'Returns the real pages and their real text'],
      ['Deterministic scan', 'Every country and region this application knows how to name is checked against those pages\' own sentences'],
      ['Position rule', 'A market gets a card only if a real sentence states a position for it, close to the words that state it'],
      ['Rendered', 'Each card links to the page the position was stated on']
    ],
    mechs: [
      ['Why not ask the model which markets exist', 'This surface used to. A structured call was asked to name each market itself, and this application verified the answer afterwards. The verification worked - but by the time there were two entries to check for a merge, the model had already decided there were two entries, and on other runs it decided there was only one. A real Clinic submission covering the EU and UK together intermittently rendered as a UK-only position, understating the company\'s own regulatory footprint. Re-checking a proposal cannot fix a proposal that was never made. So the model is no longer asked, at all, which markets to show.'],
      ['The deterministic rule', 'For every market this application knows the name and aliases of, it looks for a real sentence in the retrieved pages that names that market within a short distance of a status word, and that itself resolves to one of five fixed outcomes (approved, launched, submitted, restricted, or a distribution arrangement) - not just a sentence that happens to sit near status-shaped language. A sentence about clinical evidence "forming part of the documentation for certification" sits right next to the word certification and names nothing about the market\'s status; the rule rejects it. Same input, same pages, same output, every run.'],
      ['One statement, one card', 'A single announcement can state one combined position across two markets - the EU and UK submission is one sentence, not two. When two markets resolve to the exact same sentence, they are shown as one card, worded from the announcement\'s own text, never a name pulled from a synonym table.'],
      ['Status values', 'The status on each card comes from that fixed list of five, derived from the quoted sentence itself - so an "approved" badge can never sit above wording that describes a submission, or wording that says a product is NOT listed.'],
      ['What the model still does here', 'One remaining call reviews the same retrieved pages for gaps - aspects a reader would expect a market position to cover that the content simply does not state. It proposes nothing about markets, quotes or status; it only ever adds an absence to the list.'],
      ['Honesty limit', 'This surface reports published positions only. It is not a regulatory register and must not be used as one.']
    ]
  },
  '/claim-check': {
    lead: 'The drafted claim is used as the retrieval query itself, so the check runs against whatever the published content most closely says.',
    nodes: [
      ['Drafted claim', 'Used directly as the retrieval query'],
      ['Semantic retrieval', 'Finds the closest published wording, if any exists'],
      ['Response schema', 'Verdict from a fixed list; source locked to retrieved titles'],
      ['Structured answer call', 'Returns verdict, quote, gaps and a safer rewrite'],
      ['Rendered', 'The quote is verbatim from the content, not paraphrased']
    ],
    mechs: [
      ['Conservative prompt', 'The instruction is explicit that plausibility is not support. A claim about an outcome, efficacy figure, regulatory status, indication or safety conclusion is unsupported unless the content states that exact thing.'],
      ['Fixed verdicts', 'Supported, partly supported, or not supported. A free-text verdict would drift; three values do not.'],
      ['When it reaches no verdict at all', 'Semantic retrieval never comes back empty - it returns the closest matches it has, scored, trailing towards nothing - so the closest match is thresholded before the check runs. Below that threshold this desk declines rather than returning a verdict, and the decline carries no quote, no source and no pages-checked list. "Not supported" is deliberately not used for this: that is a finding about the published content, and finding nothing to judge a claim against is not evidence that the claim is unsupported.'],
      ['The rewrite', 'Generated from the same retrieved passages, so the suggested wording cannot reach beyond what the check just verified.'],
      ['Not a regulatory sign-off', 'This surface is a first pass that catches the obvious overreach early. It does not replace medical, regulatory or legal review.']
    ]
  },
  '/investor-signal': {
    lead: 'The chart is arithmetic over the real announcement record. The briefing underneath it is a live grounded answer over the announcements themselves.',
    nodes: [
      ['Announcement record', 'Every announcement page with its real publication date'],
      ['Deterministic themes', 'Grouped by keyword rules over the announcement title'],
      ['Chart', 'Counted directly - no model, no estimate, no rounding'],
      ['Grounded answer call', 'Briefing generated over the announcements in that theme'],
      ['Support check', 'Scores the briefing against what was retrieved']
    ],
    mechs: [
      ['The chart', 'Counts are real: one bar segment is one announcement. Dates come from each page\'s own published date.'],
      ['The themes', 'Assigned by keyword rules over the title, so the grouping is reproducible and free. A model was deliberately not used - it would cost a call per announcement and would classify by subject matter rather than by the deterministic property we want.'],
      ['The briefing', 'Scoped to announcement pages only, then generated from what retrieval returned. It never forecasts, values or interprets.'],
      ['Limit', 'This is Clinic\'s published announcement record as it appears on the website. It is not a substitute for the company\'s formal filings.']
    ]
  },
  '/patient-guide': {
    lead: 'Same stack as the surgeon desk, pointed at a deliberately smaller slice of content and given a very different brief.',
    nodes: [
      ['Your question', 'Sent to this application'],
      ['Scoped retrieval', 'Restricted to patient-facing pages only'],
      ['Grounded answer call', 'Plain-language brief, no clinical register'],
      ['Support check', 'Scores the answer against the retrieved passages'],
      ['Safety rail', 'Always returns the reader to their own clinician']
    ],
    mechs: [
      ['Why the scope matters', 'Retrieval here is restricted to pages whose AUDIENCE is patients - one axis, not a mix of audience and document type. That distinction is load-bearing: a page can carry the document type "patient information" while being written for practitioners, and four such pages qualified under the earlier rule. A single axis cannot be satisfied by a naming coincidence. Eleven of the 249 pages are in scope.'],
      ['The scope is a control, not a preference', 'Restricting retrieval is only the first layer, and it can fail open - the answer call does not honour a scope restriction as reliably as retrieval does, so an excluded page can ground an answer intermittently. So after the answer is written, and before anything is composed, this application checks every source that contributed to it against the same entitlement. If ANY page outside it contributed, the whole response is withheld - answer, sources, confidence reading and all - rather than the out-of-scope parts being quietly removed. Proven in both directions: twenty consecutive runs of a real question served cleanly with nothing out of scope, and five runs with the first layer deliberately removed were all withheld.'],
      ['Why the whole response', 'A true sentence left standing beside a withheld answer reads as the answer. Withholding the parts would leave the reader with something that looks like a reply and is not one. The same now applies when this desk simply refuses because the patient pages do not state something: the refusal comes back alone, with no source cards beneath it. That was the sharper risk of the two on this surface, because the cards retrieved for an unanswerable question are still real patient pages - and on "which hospitals offer this procedure" they named a hospital and a surgeon.'],
      ['Register', 'The same content can be answered clinically or plainly. The difference is the instruction, not a second body of content.'],
      ['Hard limits', 'No medical advice, no suitability judgement, no outcome, success rate or recovery time that is not written in the published pages.'],
      ['Where it sends you', 'Every answer ends at a clinician, and the page carries a real route to the Clinic team.']
    ]
  },
  '/evidence-library': {
    lead: 'The shelves and counts are the real loaded record. The search box is live semantic retrieval over the same content the other five desks read.',
    nodes: [
      ['Loaded record', 'Every page loaded, with its real labels'],
      ['Counts', 'Taken from that record directly'],
      ['Search', 'Semantic retrieval over the whole set'],
      ['Label filters', 'Applied as a scoping expression on the retrieval call'],
      ['Results', 'Each card links to the live page on clinic.com']
    ],
    mechs: [
      ['Counts', 'Derived from the loaded record this application owns, not from a platform aggregation - aggregation is a known weak point and is deliberately avoided here.'],
      ['Filters', 'Applied as a scoping expression on the retrieval call itself, so a filtered search genuinely searches less, rather than searching everything and hiding results afterwards.'],
      ['Thresholding', 'Retrieval always returns something. Weak matches are dropped by this application so an irrelevant search honestly returns nothing.'],
      ['Every card is a real page', 'Each one opens the live page on clinic.com that the desks are reading.']
    ]
  }
};

function openReveal() {
  const r = REVEAL[location.pathname] || REVEAL['/'];
  const title = (ROUTES[location.pathname] || ROUTES['/']).title;
  modalRoot.innerHTML = `<div class="modal-back" id="mback"><div class="modal" role="dialog" aria-modal="true" aria-label="How this works">
    <div class="mhead">
      <div>
        <div class="eyebrow" style="margin-bottom:8px">How this works &middot; ${esc(title)}</div>
        <h3 style="margin:0 0 8px">Built on Progress Agentic RAG</h3>
        <p style="margin:0;max-width:66ch">${esc(r.lead)}</p>
      </div>
      <button class="x" id="mx" aria-label="Close">&times;</button>
    </div>
    <div class="mbody">
      <div class="flow">${r.nodes.map((n, i) => `<div class="flownode" data-i="${i}">
        <div class="ic"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">${
          ['<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18"/>',
           '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M8 12h8M12 8v8"/>',
           '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
           '<path d="M4 5h16v11H7l-3 3z"/>',
           '<path d="M20 6 9 17l-5-5"/>'][i] || '<circle cx="12" cy="12" r="9"/>'
        }</svg></div>
        <div class="l">${esc(n[0])}</div><div class="d">${esc(n[1])}</div></div>`).join('')}</div>
      ${r.mechs.map(m => `<div class="mech"><b>${esc(m[0])}</b><p>${esc(m[1])}</p></div>`).join('')}
      <div class="gapnote">
        <b style="font-family:var(--head);color:#85560D">Where the platform's own mechanism was not used</b>
        <p style="margin:8px 0 0">Clinic's content has no confidential clinical or patient data in it, so nothing here needed a private-data pathway. Classification and the announcement themes were set by deterministic rules rather than by an ingestion-time model: the properties involved are intrinsic to each document, a model would judge them by subject matter instead, and it would cost one model call per paragraph across the whole corpus for no gain. Both are engineering choices, stated here rather than left implicit.</p>
      </div>
      <p class="tiny muted" style="margin-top:22px">Progress Agentic RAG holds the content, does the retrieval, writes every answer and scores its own support. This application holds the credential, scopes each surface and renders the result.</p>
    </div>
  </div></div>`;
  const nodes = modalRoot.querySelectorAll('.flownode');
  nodes.forEach((n, i) => setTimeout(() => n.classList.add('lit'), 180 + i * 230));
  const close = () => { modalRoot.innerHTML = ''; document.body.style.overflow = ''; };
  document.body.style.overflow = 'hidden';
  document.getElementById('mx').addEventListener('click', close);
  document.getElementById('mback').addEventListener('click', e => { if (e.target.id === 'mback') close(); });
  document.addEventListener('keydown', function esckey(e) {
    if (e.key === 'Escape') { close(); document.removeEventListener('keydown', esckey); }
  });
}
document.getElementById('revealBtn').addEventListener('click', openReveal);

/* ============================================================= router */
const VIEWS = {
  '/': home, '/vac-desk': vacDesk, '/surgeon-desk': surgeon, '/market-access': market, '/claim-check': claim,
  '/investor-signal': investor, '/patient-guide': patient, '/evidence-library': library
};

function render() {
  renderNav();
  const fn = VIEWS[location.pathname];
  if (!fn) {
    // an unknown address returns to the desk rather than dead-ending
    view.innerHTML = `<div class="wrap" style="padding:80px 0"><h1>That page is not part of the desk</h1>
      <p class="lead">Taking you back to the six desks.</p><a class="btn" href="/" data-link>Go to the desk</a></div>`;
    setTimeout(() => { if (!VIEWS[location.pathname]) go('/'); }, 2200);
    return;
  }
  fn();
}

(async function start() {
  try { CFG = await api('/api/config'); }
  catch (e) {
    view.innerHTML = `<div class="wrap" style="padding:80px 0">${errorBox('The desk could not load its content record.')}</div>`;
    wireRetry(view, () => location.reload());
    return;
  }
  document.getElementById('footnote').textContent =
    `Clinic Knowledge Desk - a demonstration built by Progress on ${CFG.corpus.documents} pages published on clinic.com. Every answer is generated live from that published content. No clinical, patient or confidential data is used, and no result, approval or claim is generated that the published content does not state.`;
  render();
})();
