import { h, fmtN } from '../util.js';
import { catalogue } from '../data.js';
import { state } from '../state.js';
import { mountAsk } from '../ask.js';
import { failState, thumb, countBadge } from '../cards.js';
import { plain } from '../md.js';

export async function mount(main) {
  main.append(h('section', { class: 'phead' }, h('div', { class: 'wrap' }, h('h1', {}, 'Films'), h('p', {}, 'Ask a question and the answer comes from what is said in the films, with each part traceable to the passage that supports it.'))));
  const page = h('div', { class: 'wrap page' }); main.append(page);
  let cat; try { cat = await catalogue(); } catch { page.append(failState('The films did not load.', () => location.reload())); return; }
  const films = (cat.assets || []).filter((a) => a.kind === 'film');
  const askHost = h('div', { class: 'dark', style: 'background:var(--navy);border-radius:16px;padding:20px 20px 24px;margin-bottom:28px' });
  askHost.append(h('p', { class: 'eyebrow', style: 'color:#B9C8EE' }, `Ask across ${fmtN(films.filter((f) => f.has_transcript !== false).length)} films with a transcript`));
  page.append(askHost);
  const ask = mountAsk(askHost, { scope: 'kind:film', total: films.length, autofocus: false });
  askHost.after(ask.answerHost); ask.answerHost.classList.add('flat');
  page.append(h('div', { class: 'rail-head' }, h('h2', { style: 'font-size:26px' }, 'All films'), countBadge(films.length)));
  if (!films.length) { page.append(h('div', { class: 'empty' }, 'No films are indexed yet.')); return () => ask.destroy(); }
  const player = h('div', { style: 'scroll-margin-top:150px' });
  const grid = h('div', { class: 'grid' }, ...films.map((f) => {
    const noT = f.has_transcript === false;
    const b = h('button', { class: 'card', type: 'button' }, thumb(f, { onFail: () => {} }), h('div', { class: 'body' }, h('h4', {}, f.title), noT ? h('span', { class: 'meta' }, 'No transcript, so questions cannot be answered from what is said in it') : (f.has_transcript === true ? h('span', { class: 'meta' }, 'Transcript indexed') : null), f.excerpt ? h('p', {}, plain(f.excerpt)) : null));
    b.addEventListener('click', () => play(f)); return b;
  }));
  page.append(player, grid);
  function play(f) {
    if (f.media_url) state.filmPlayed = true;
    if (f.media_url) player.replaceChildren(h('div', { style: 'margin-bottom:24px' }, h('h3', { style: 'margin-bottom:8px' }, f.title), h('video', { src: f.media_url, controls: true, autoplay: true, playsinline: true, preload: 'metadata', poster: f.thumb || null, style: 'width:100%;max-height:70vh;background:#000;border-radius:12px' })));
    else player.replaceChildren(h('div', { class: 'qa', style: 'margin-bottom:24px' }, h('h3', {}, f.title), f.excerpt ? h('p', {}, plain(f.excerpt)) : null, f.has_transcript === false ? h('p', { class: 'mono', style: 'margin:0' }, 'No transcript is indexed for this film, so it cannot be asked about.') : h('button', { class: 'btn btn-line btn-sm', type: 'button', onclick: () => { window.scrollTo({ top: 0, behavior: 'smooth' }); ask.ask(`What is said in the film "${f.title}"?`); } }, 'Ask about this film')));
    player.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  const want = new URL(location.href).searchParams.get('asset'); const target = films.find((f) => f.asset_id === want); if (target) play(target);
  return () => ask.destroy();
}
