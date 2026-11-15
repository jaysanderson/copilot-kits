// ONE shared markdown renderer for every text surface (answers, summaries, persona text, reveal copy, widget).
// Escapes first, then applies a small safe subset. Raw markdown must never reach the screen.
import { esc } from './util.js';

function inline(s, ctx) {
  s = esc(s);
  s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/(^|[^*\w])\*([^*\s][^*]*)\*(?!\w)/g, '$1<em>$2</em>');
  s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  s = s.replace(/\s+(\[\d{1,2}\])/g, '$1');
  // citation markers [n] -> superscript at the grounded claim (B33)
  s = s.replace(/\[(\d{1,2})\]/g, (m, n) => {
    const i = +n, c = ctx && ctx.citations;
    if (c && c.length) return c.some((x, k) => (x.n ?? k + 1) === i) ? `<sup class="cite"><a href="#src-${(ctx && ctx.idp) || ''}${i}" data-cite="${i}" aria-label="Source ${i}">${i}</a></sup>` : '';
    return ctx && ctx.streaming ? `<sup class="cite"><span>${i}</span></sup>` : '';
  });
  return s;
}

// While streaming, drop an unterminated trailing marker so half-written syntax never shows.
function trimPartial(t) {
  t = t.replace(/\[\d{0,2}$/, '').replace(/\[[^\]\n]*$/, (m) => (/^\[\d/.test(m) ? '' : m));
  if ((t.match(/```/g) || []).length % 2) t = t.replace(/```[\s\S]*$/, '');
  if ((t.match(/`/g) || []).length % 2) t = t.replace(/`[^`]*$/, '');
  if ((t.match(/\*\*/g) || []).length % 2) t = t.replace(/\*\*[^*]*$/, '');
  else if ((t.replace(/\*\*/g, '').match(/\*/g) || []).length % 2) t = t.replace(/\*[^*\n]*$/, '');
  return t;
}

export function render(text, ctx = {}) {
  let t = String(text ?? '').replace(/\r/g, '');
  if (ctx.streaming) t = trimPartial(t);
  const out = [], lines = t.split('\n');
  let i = 0;
  while (i < lines.length) {
    const L = lines[i];
    if (/^```/.test(L)) {
      const buf = []; i++;
      while (i < lines.length && !/^```/.test(lines[i])) buf.push(lines[i++]);
      i++; out.push(`<pre><code>${esc(buf.join('\n'))}</code></pre>`); continue;
    }
    const hd = /^(#{1,4})\s+(.*)$/.exec(L);
    if (hd) { out.push(`<h4>${inline(hd[2], ctx)}</h4>`); i++; continue; }
    if (/^\s*[-*]\s+/.test(L)) {
      const it = []; while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) it.push(`<li>${inline(lines[i++].replace(/^\s*[-*]\s+/, ''), ctx)}</li>`);
      out.push(`<ul>${it.join('')}</ul>`); continue;
    }
    if (/^\s*\d+[.)]\s+/.test(L)) {
      const it = []; while (i < lines.length && /^\s*\d+[.)]\s+/.test(lines[i])) it.push(`<li>${inline(lines[i++].replace(/^\s*\d+[.)]\s+/, ''), ctx)}</li>`);
      out.push(`<ol>${it.join('')}</ol>`); continue;
    }
    if (!L.trim()) { i++; continue; }
    const p = []; while (i < lines.length && lines[i].trim() && !/^(```|#{1,4}\s|\s*[-*]\s|\s*\d+[.)]\s)/.test(lines[i])) p.push(lines[i++]);
    out.push(`<p>${inline(p.join(' '), ctx)}</p>`);
  }
  return out.join('');
}
export const renderInline = (t) => render(t).replace(/^<p>/, '').replace(/<\/p>$/, '').replace(/<\/p><p>/g, ' ');
// Plain text for single-line surfaces (card excerpts): strip markdown syntax instead of rendering it.
export function plain(text) {
  return String(text ?? '').replace(/```[\s\S]*?```/g, ' ').replace(/`([^`]*)`/g, '$1').replace(/\*\*?([^*]+)\*\*?/g, '$1')
    .replace(/^#{1,6}\s+/gm, '').replace(/\[([^\]]+)\]\([^)]*\)/g, '$1').replace(/\[\d{1,2}\]/g, '').replace(/\s+/g, ' ').trim();
}
