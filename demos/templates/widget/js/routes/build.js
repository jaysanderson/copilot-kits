import { h, $ } from '../util.js';
import { TRIAL, trialOffer, loadTrial } from '../trial.js';
import { getJSON } from '../api.js';
import { hitCard, readout, failState } from '../cards.js';
import { state } from '../state.js';

// Code samples use the platform's real call shape. <ZONE>, <KB_ID> and <SERVICE_TOKEN> are the visitor's own values.
const SNIP = {
  curl: `curl -X POST "https://<ZONE>.dp.progress.cloud/api/v1/kb/<KB_ID>/find" \\
  -H "X-NUCLIA-SERVICEACCOUNT: Bearer <SERVICE_TOKEN>" \\
  -H "X-Synchronous: true" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "How do I keep answers inside a users permissions?"}'`,
  python: `import os, requests

KB = "https://<ZONE>.dp.progress.cloud/api/v1/kb/<KB_ID>"
headers = {
    "X-NUCLIA-SERVICEACCOUNT": "Bearer " + os.environ["KB_SERVICE_TOKEN"],
    "X-Synchronous": "true",
}
r = requests.post(KB + "/ask", headers=headers, timeout=30,
                  json={"query": "What does per-query quality scoring measure?"})
r.raise_for_status()
print(r.json()["answer"])`,
  js: `// Run this on YOUR server. Never ship the token to a browser.
const KB = "https://<ZONE>.dp.progress.cloud/api/v1/kb/<KB_ID>";
const r = await fetch(KB + "/find", {
  method: "POST",
  headers: {
    "X-NUCLIA-SERVICEACCOUNT": "Bearer " + process.env.KB_SERVICE_TOKEN,
    "X-Synchronous": "true",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ query: "How is a knowledge box created?" }),
});
console.log((await r.json()).resources);`,
};
export const EMBED_SNIPPET = (o = location.origin) => `<div data-agentic-rag lens="build" theme="light" height="560"></div>\n<script async src="${o}/embed.js"></script>`;

export async function mount(main) {
  await loadTrial();
  main.append(h('section', { class: 'phead' }, h('div', { class: 'wrap' }, h('h1', {}, 'Build with it'), h('p', {}, 'From trial to your first cited answer, then what to do when it goes wrong. The calls below are the platform\'s real call shapes; the live panel runs this site\'s own search.'))));
  const page = h('div', { class: 'wrap page' }); main.append(page);
  const tabs = h('div', { class: 'tabs', role: 'tablist' }); const code = h('pre', { class: 'code' });
  const show = (k) => { code.textContent = SNIP[k]; tabs.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.k === k))); };
  Object.keys(SNIP).forEach((k) => tabs.append(h('button', { class: 'chip', type: 'button', 'data-k': k, onclick: () => show(k) }, { curl: 'curl', python: 'Python', js: 'JavaScript' }[k])));
  show('curl');
  const live = h('pre', { class: 'code', style: 'max-height:300px' }, 'Press Run to send a real search through this site\'s own server.');
  const lro = h('div', { style: 'margin-top:8px' });
  const run = h('button', { class: 'btn btn-primary btn-sm', type: 'button' }, 'Run a live search');
  run.addEventListener('click', async () => {
    run.disabled = true; live.textContent = 'Searching...';
    try { const j = await getJSON('/api/search?q=' + encodeURIComponent('create a knowledge box and ingest content'), { label: 'Build: live search' }); live.textContent = JSON.stringify({ total: j.total, hits: (j.hits || []).slice(0, 3).map((x) => ({ title: x.title, kind: x.kind, score: x.score })) }, null, 2); lro.replaceChildren(readout(j._trace)); }
    catch { live.replaceChildren(); live.append(failState('That search did not come back in time.', () => run.click())); }
    run.disabled = false;
  });
  const snippet = h('pre', { class: 'code' }, EMBED_SNIPPET());
  const steps = h('div', { class: 'steps' },
    h('div', { class: 'step' }, h('h3', {}, 'Start the free trial'), h('p', {}, `The published entry point is ${trialOffer()}${TRIAL.appliesTo ? ' on ' + TRIAL.appliesTo : ''}. You start it yourself: Progress publishes that you can sign up, create a knowledge box and ingest your first documents in minutes.`), h('a', { class: 'btn btn-primary', href: TRIAL.url, target: '_blank', rel: 'noopener noreferrer', 'data-trial-cta': '' }, TRIAL.cta)),
    h('div', { class: 'step' }, h('h3', {}, 'Load a first corpus that can answer'), h('p', {}, 'Choose one question, not one corpus. Load about twenty substantial documents, because thin ones cannot answer what a practitioner types. Ask it the way a real user would. Read the citation before you judge the answer. Decide your floor from measurement over your own content.'), h('div', { id: 'guide-first' })),
    h('div', { class: 'step' }, h('h3', {}, 'Ask it from your server'), h('p', {}, 'Retrieval is one call. A written answer is another. Keep the token server-side and call from your own backend.'), tabs, code),
    h('div', { class: 'step' }, h('h3', {}, 'See it on this site, live'), h('p', {}, 'This runs a real search through this site\'s own server and returns the first three hits with the measured time.'), run, live, lro),
    h('div', { class: 'step' }, h('h3', {}, 'When an answer is wrong'), h('p', {}, 'Six causes, in the order they occur, and what to change for each.'), h('a', { class: 'btn btn-line', href: '/fix' }, 'Fix a wrong answer')),
    h('div', { class: 'step' }, h('h3', {}, 'Put it on your own page'), h('p', {}, 'The same ask surface, embeddable with one tag.'), snippet, h('p', { style: 'margin-top:12px' }, h('a', { href: '/embed' }, 'Configure and preview the widget →'))),
    h('div', { class: 'step' }, h('h3', {}, 'Grow from here'), h('p', {}, 'Starter to Pro, a second knowledge box, a second use case.'), h('a', { class: 'btn btn-line', href: '/pricing#grow' }, 'See how it grows')));
  const refs = h('div', { class: 'sec' }, h('h3', {}, 'Cookbook, reference architecture and agents'), h('div', { class: 'suggest', style: 'grid-template-columns:repeat(auto-fill,minmax(260px,1fr));max-width:none' }));
  page.append(steps, refs);
  getJSON('/api/search?q=' + encodeURIComponent('your first knowledge box') + '&facets=kind:guide', { label: 'Build: first guide' }).then((j) => { const a = (j.hits || [])[0]; if (a) document.getElementById('guide-first').replaceChildren(hitCard(a, 0)); }).catch(() => {});
  const g = refs.querySelector('.suggest');
  Promise.all(['cookbook recipes examples', 'reference architecture', 'retrieval agent orchestration MCP tools'].map((q) => getJSON(`/api/search?q=${encodeURIComponent(q)}&lens=build`, { label: 'Build: references' }).catch(() => null))).then((rs) => {
    const seen = new Set(), cards = [];
    rs.forEach((r) => (r?.hits || []).slice(0, 3).forEach((a) => { if (!seen.has(a.asset_id)) { seen.add(a.asset_id); cards.push(a); } }));
    cards.length ? g.replaceChildren(...cards.map((a, i) => hitCard(a, i))) : refs.remove();
  });
}
