import { h } from '../util.js';
import { EMBED_SNIPPET } from './build.js';
import { LENSES } from '../util.js';

export async function mount(main) {
  main.append(h('section', { class: 'phead' }, h('div', { class: 'wrap' }, h('h1', {}, 'Embed the ask surface'), h('p', {}, 'One tag puts this ask-and-answer surface on your own page. It carries no key and only reaches what the public tier can reach.'))));
  const page = h('div', { class: 'wrap page' }); main.append(page);
  const cfg = { scope: '', lens: '', theme: 'light', height: 'auto' };
  const frameBox = h('div', { class: 'embedbox' }), snip = h('pre', { class: 'code' });
  const sel = (id, label, opts, k) => h('div', { class: 'inp' }, h('label', { for: id }, label), h('select', { id, class: 'field', onchange: (e) => { cfg[k] = e.target.value; draw(); } }, ...opts.map(([v, t]) => h('option', Object.assign({ value: v }, cfg[k] !== undefined && String(cfg[k]) === v ? { selected: true } : {}), t))));
  const form = h('div', { style: 'display:grid;gap:4px;max-width:420px' },
    sel('c-scope', 'Scope', [['', 'Everything'], ['kind:film', 'Films only'], ['kind:guide', 'Guides only'], ['kind:reference', 'References only']], 'scope'),
    sel('c-lens', 'Path', [['', 'None (everything)'], ...Object.entries(LENSES)], 'lens'),
    sel('c-theme', 'Theme', [['light', 'Light'], ['dark', 'Dark']], 'theme'),
    sel('c-h', 'Height', [['auto', 'Fit to content'], ['480', '480 px'], ['560', '560 px'], ['720', '720 px']], 'height'));
  function draw() {
    const qs = new URLSearchParams({ theme: cfg.theme, embed: '1', ...(cfg.scope ? { scope: cfg.scope } : {}), ...(cfg.lens ? { lens: cfg.lens } : {}) });
    const fr = h('iframe', { src: '/widget?' + qs, title: 'Embedded ask surface', style: `width:100%;height:${cfg.height === 'auto' ? 560 : cfg.height}px;border:0;border-radius:10px`, loading: 'lazy' });
    frameBox.replaceChildren(fr);
    if (cfg.height === 'auto') window.onmessage = (e) => { if (e.source === fr.contentWindow && e.data && e.data.type === 'agentic-rag-embed-height' && isFinite(e.data.height)) fr.style.height = Math.max(320, Math.min(Math.ceil(e.data.height), 1400)) + 'px'; }; else window.onmessage = null;
    snip.textContent = `<div data-agentic-rag${cfg.scope ? ` scope="${cfg.scope}"` : ''}${cfg.lens ? ` lens="${cfg.lens}"` : ''} theme="${cfg.theme}" height="${cfg.height}"></div>\n<script async src="${location.origin}/embed.js"></script>`;
  }
  draw();
  page.append(h('div', { class: 'two' }, h('div', {}, h('h2', { style: 'font-size:24px;margin-bottom:12px' }, 'Configure'), form, h('h3', { style: 'margin:20px 0 8px;font-size:16px' }, 'Your snippet'), snip, h('p', { style: 'margin-top:14px' }, h('a', { class: 'btn btn-line', href: '/embed-host' }, 'See it on a separate page that embeds it →'))), h('div', {}, h('h2', { style: 'font-size:24px;margin-bottom:12px' }, 'Live preview'), frameBox)));
}
