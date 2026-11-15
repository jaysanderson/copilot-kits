import { h, fmtN, debounce } from '../util.js';
import { SIGNUP } from '../chrome.js';
import { postJSON } from '../api.js';
import { readout, failState, skeleton, tierNote } from '../cards.js';
import { plain } from '../md.js';
import { TRIAL, trialOffer, loadTrial, pricingData } from '../trial.js';

// The server owns the arithmetic and validates every input; ranges here mirror its limits so a slider cannot ask for an invalid number.
const INPUTS = [
  ['staff', 'People who search for answers', 'people', 1, 100000, 1],
  ['searches_per_week', 'Searches per person per week', 'searches', 0, 500, 1],
  ['minutes_per_search', 'Minutes per search', 'minutes', 0, 240, 1],
  ['time_saved_pct', 'Share of that time recovered', '%', 0, 100, 1],
  ['hourly_cost_usd', 'Loaded hourly cost', 'USD', 0, 2000, 5],
  ['subscription_usd_month', 'Your quoted subscription per month', 'USD', 0, 1000000, 50],
  ['weeks_per_year', 'Working weeks per year', 'weeks', 1, 52, 1],
];
const usd = (v) => (typeof v === 'number' ? (v < 0 ? '-' : '') + 'US$' + Math.abs(Math.round(v)).toLocaleString('en-AU') : null);
const OUTPUTS = [['hours_spent_searching_per_year', 'Hours spent searching per year', (v) => fmtN(Math.round(v)) + ' hours'], ['hours_recovered_per_year', 'Hours recovered per year', (v) => fmtN(Math.round(v)) + ' hours'], ['value_recovered_usd_per_year', 'Value of those hours per year', usd], ['subscription_usd_per_year', 'Subscription per year', usd], ['net_usd_per_year', 'Net per year', usd], ['payback_months', 'Payback', (v) => v + ' months']];

export async function mount(main) {
  main.append(h('section', { class: 'phead' }, h('div', { class: 'wrap' }, h('h1', {}, 'Pricing and the value model'), h('p', {}, 'Published tiers, how you grow, and a calculator you drive with your own numbers. The calculator is arithmetic, not generation, and lists every assumption.'))));
  const page = h('div', { class: 'wrap page' }); main.append(page);
  page.append(tierNote());
  // Prices come from GET /api/pricing (the verified record, served with its source and date). No figure is typed in this file.
  let P = null;
  try { P = await pricingData(); } catch (e) { /* the honest unavailable state below */ }
  await loadTrial();
  const tiers = P && Array.isArray(P.tiers) ? P.tiers.filter((t) => t && t.name && t.price) : [];
  if (!tiers.length) {
    page.append(h('div', { class: 'sh' }, h('h2', {}, 'Published pricing')), failState('Pricing is not available right now. No price is shown rather than a stale one.', () => { import('../router.js').then((m) => m.run()); }));
    return;
  }
  const fmtDate = (iso) => { const d = new Date(iso + 'T00:00:00Z'); return isNaN(d) ? null : d.toLocaleDateString('en-AU', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }); };
  const verified = typeof P._verified_utc === 'string' ? fmtDate(P._verified_utc.slice(0, 10)) : null;
  const source = typeof P._source === 'string' && /^https:\/\//.test(P._source) ? P._source : null;
  const byName = (n) => tiers.find((t) => t.name === n);
  const starter = byName(TRIAL.appliesTo || 'Starter') || tiers[0], pro = byName('Pro');
  const boxLimit = (t) => ((t && t.limits) || []).find((l) => /knowledge box/i.test(l));
  const stamp = h('p', { class: 'readout', style: 'margin-top:14px' }, h('span', {}, 'All prices in US dollars, as published'), verified ? h('span', {}, '·') : null, verified ? h('span', {}, 'checked ' + verified) : null, source ? h('span', {}, '·') : null, source ? h('a', { href: source, target: '_blank', rel: 'noopener noreferrer' }, 'Progress pricing page') : null);
  page.append(h('div', { class: 'sh' }, h('h2', {}, 'Published pricing'), h('p', { class: 'lede' }, `Self-serve starts with ${trialOffer()}${TRIAL.appliesTo ? ' on ' + TRIAL.appliesTo : ''}. Prices below are the published ones, with the date they were checked.`), stamp),
    h('div', { class: 'pillars', style: 'align-items:start' }, ...tiers.map((t) => h('article', { class: 'pillar' }, h('h3', {}, t.name),
      h('div', { class: 'big', style: t.period ? '' : 'font-size:40px' }, t.price), t.period ? h('div', { class: 'biglbl' }, t.period) : h('div', { class: 'biglbl' }, 'Ask Progress for a quote'),
      (t.limits || []).length ? h('ul', { style: 'margin:0;padding-left:18px' }, ...t.limits.map((l) => h('li', {}, l))) : null,
      t.tokens ? h('p', { style: 'font-size:14px' }, t.tokens) : null,
      (t.capabilities || []).length ? h('h4', { style: 'font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#3D3D42' }, 'Capabilities') : null, (t.capabilities || []).length ? h('ul', { style: 'margin:0;padding-left:18px' }, ...t.capabilities.map((l) => h('li', {}, l))) : null,
      (t.support || []).length ? h('h4', { style: 'font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#3D3D42' }, 'Support') : null, (t.support || []).length ? h('p', { style: 'margin:0' }, t.support.join(', ')) : null,
      t === starter ? h('a', { class: 'btn btn-primary', href: TRIAL.url, target: '_blank', rel: 'noopener noreferrer', style: 'margin-top:8px', 'data-trial-cta': '' }, TRIAL.cta) : null,
      !t.period && source ? h('a', { class: 'btn btn-line', href: source, target: '_blank', rel: 'noopener noreferrer', style: 'margin-top:8px' }, 'See the published page') : null))),
    // Expansion is a surface, stated plainly from the published rows above - printed verbatim, never paraphrased into a different figure.
    h('section', { id: 'grow', style: 'margin-top:56px' }, h('div', { class: 'sh' }, h('p', { class: 'eyebrow' }, 'Growing'), h('h2', {}, 'How you grow from here'), h('p', { class: 'lede' }, 'You expand by understanding what changes, not by being called.')),
      h('div', { class: 'fitgrid' },
        pro ? h('div', { class: 'qa' }, h('h3', {}, 'Starter to Pro'), h('p', {}, `${starter.name} is ${starter.price} ${starter.period || ''}; ${pro.name} is ${pro.price} ${pro.period || ''}. ${pro.name} adds ${(pro.capabilities || []).filter((c) => !(starter.capabilities || []).includes(c)).map((c) => c.replace(/^([A-Z])([a-z])/, (m, x, y) => x.toLowerCase() + y)).join(', ')}.`)) : null,
        (boxLimit(starter) || boxLimit(pro)) ? h('div', { class: 'qa' }, h('h3', {}, 'More knowledge boxes'), ...[starter, pro].filter(boxLimit).map((t) => h('p', { style: 'margin:0 0 6px' }, h('b', {}, t.name + ': '), boxLimit(t)))) : null,
        h('div', { class: 'qa' }, h('h3', {}, 'The second use case'), h('p', {}, 'Expand when the first one is good enough that someone who does not work for you uses it unprompted. Then ask the guide how.'), h('a', { href: '/?q=' + encodeURIComponent('When should I expand to a second use case?') }, 'Ask it on the home page →')))),
    h('div', { style: 'height:24px' }));
  const box = h('div', { class: 'roi' }), right = h('div', {});
  page.append(h('div', { class: 'sh', style: 'margin-top:48px' }, h('h2', {}, 'Value model'), h('p', { class: 'lede' }, 'Change a number and it recalculates on the server. Defaults are placeholders, not measurements and not Progress claims. The subscription starts at the published Starter price; change it to the price you are quoted.')), box);
  const values = {}, touched = new Set(), invalid = new Map(); let model = null;
  const LABEL = Object.fromEntries(INPUTS.map((x) => [x[0], x[1]]));
  const inputs = h('div', {});
  for (const [k, label, unit, min, max, step] of INPUTS) {
    const id = 'roi-' + k;
    const num = h('input', { id, class: 'field', type: 'number', inputmode: 'decimal', min, max, step, style: 'width:100%' });
    const hint = h('span', { class: 'help' }, `${unit} · ${fmtN(min)} to ${fmtN(max)}`);
    const err = h('span', { class: 'help', role: 'alert', style: 'color:#8C1F2E;font-weight:600' });
    num.addEventListener('input', () => {
      const raw = num.value.trim(), v = raw === '' ? NaN : Number(raw);
      if (!Number.isFinite(v) || v < min || v > max) {
        // Never show a result computed from values the visitor cannot see: say what is wrong and withhold the numbers.
        invalid.set(k, `${label}: enter a number from ${fmtN(min)} to ${fmtN(max)}.`); err.textContent = invalid.get(k); num.setAttribute('aria-invalid', 'true'); draw(); return;
      }
      invalid.delete(k); err.textContent = ''; num.removeAttribute('aria-invalid'); values[k] = v; touched.add(k); if (!invalid.size) recalc(); else draw();
    });
    inputs.append(h('div', { class: 'inp' }, h('label', { for: id }, label), num, hint, err)); inputs.__f = inputs.__f || {}; inputs.__f[k] = num;
  }
  box.append(inputs, right);
  right.append(skeleton(4));
  async function load(first) {
    try {
      model = await postJSON('/api/roi', first ? {} : { ...values }, { label: 'Value model' });
      if (first) {
        for (const a of model.assumptions || []) if (inputs.__f[a.name]) { inputs.__f[a.name].value = a.value; values[a.name] = a.value; }
        // Never open on a flattering net with no cost entered: start the subscription at the published Starter price.
        const starterPrice = Number(String(starter.price).replace(/[^0-9.]/g, ''));
        if (starterPrice > 0) { values.subscription_usd_month = starterPrice; inputs.__f.subscription_usd_month.value = starterPrice; return load(false); }
      }
      draw();
    } catch (e) { right.replaceChildren(failState(e.kind === 'http' && e.message ? e.message : 'The value model did not load.', () => load(first))); }
  }
  const recalc = debounce(() => load(false), 250);
  function draw() {
    if (invalid.size) { right.replaceChildren(h('div', { class: 'stat', role: 'status' }, h('p', { style: 'margin:0 0 6px;font-weight:600' }, 'No result yet'), h('p', { style: 'margin:0' }, [...invalid.values()].join(' ')), h('p', { style: 'margin:8px 0 0;color:#3D3D42' }, 'Fix the highlighted number and the result comes back. Nothing is shown from a value you cannot see.'))); return; }
    const outs = OUTPUTS.filter(([k]) => model[k] != null).map(([k, label, f]) => h('div', { class: 'out' }, h('span', {}, label), h('b', {}, f(model[k]))));
    right.replaceChildren(...outs,
      h('h3', { style: 'margin:18px 0 6px;font-size:16px' }, 'Assumptions'),
      h('ul', {}, ...(model.assumptions || []).filter((a) => LABEL[a.name]).map((a) => h('li', {}, h('span', { class: 'mono' }, `${LABEL[a.name]}: ${a.value}`), h('br'), h('span', { style: 'font-size:13px;color:#3D3D42' }, touched.has(a.name) ? 'Your input' : a.name === 'subscription_usd_month' ? 'Set to the published Starter price. Change it to the price you are quoted.' : 'Placeholder default: not a measurement and not a Progress claim')))),
      ...(model.formulas ? [h('h3', { style: 'margin:14px 0 6px;font-size:16px' }, 'How it is calculated'), h('ul', {}, ...model.formulas.map((f) => h('li', { class: 'mono' }, plain(f))))] : []),
      ...((model.not_included || []).length ? [h('h3', { style: 'margin:14px 0 6px;font-size:16px' }, 'Not included'), h('p', { style: 'margin:0' }, model.not_included.map(plain).join(', ') + '.')] : []),
      model.note ? h('p', { style: 'margin-top:12px' }, plain(model.note)) : null, readout(model._trace || []));
  }
  load(true);
}
