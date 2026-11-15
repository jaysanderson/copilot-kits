/* Ask widget: one script tag plus a mount point. Vanilla JS, no build step, styles scoped
   in a shadow root so the host page's CSS cannot reach in and ours cannot leak out.
   Mount: <div data-ask-widget data-langs="en,zh" data-accent="#c2410c" data-scope="study"
   data-placeholder="..."></div>. The widget only ever talks to the server that served this
   script; credentials stay on that server. */
(function () {
  'use strict';
  if (window.__askWidgetLoaded) return;
  window.__askWidgetLoaded = true;

  var script = document.currentScript;
  var BASE = (script && script.src ? new URL(script.src).origin : location.origin);

  var NAMES = { en: 'English', zh: '中文', ar: 'العربية', id: 'Bahasa Indonesia' };
  var I18N = {
    en: { ph: 'Ask a question', ask: 'Ask', working: 'Finding the answer in the pages...', slow: 'Taking longer than usual. Trying again...', fail: 'We could not get an answer right now.', retry: 'Try again', declined: 'We could not find a sourced answer to that. Try rephrasing, or contact the university directly.', scoped: 'Answers from the {s} section only', sources: 'Sources', notlang: 'This answer came back in English rather than your chosen language. The sources are linked below.' },
    zh: { ph: '请输入您的问题', ask: '提问', working: '正在网页中查找答案...', slow: '耗时比平时长，正在重试...', fail: '目前无法获取答案。', retry: '重试', declined: '没有找到有来源支持的答案。请换一种问法，或直接联系大学。', scoped: '答案仅来自“{s}”栏目', sources: '来源', notlang: '此答案以英文返回，而不是您选择的语言。来源链接见下方。' },
    ar: { ph: 'اطرح سؤالاً', ask: 'اسأل', working: 'جارٍ البحث عن الإجابة في الصفحات...', slow: 'استغرق الأمر وقتاً أطول من المعتاد. نعيد المحاولة...', fail: 'تعذّر الحصول على إجابة الآن.', retry: 'حاول مرة أخرى', declined: 'لم نجد إجابة موثقة بالمصادر. جرّب صياغة أخرى أو تواصل مع الجامعة مباشرة.', scoped: 'الإجابات من قسم «{s}» فقط', sources: 'المصادر', notlang: 'جاءت هذه الإجابة بالإنجليزية بدلاً من اللغة التي اخترتها. المصادر موضحة أدناه.' },
    id: { ph: 'Ajukan pertanyaan', ask: 'Tanya', working: 'Mencari jawaban di halaman...', slow: 'Butuh waktu lebih lama dari biasanya. Mencoba lagi...', fail: 'Kami belum bisa mendapatkan jawaban saat ini.', retry: 'Coba lagi', declined: 'Kami tidak menemukan jawaban bersumber untuk itu. Coba ubah pertanyaan, atau hubungi universitas langsung.', scoped: 'Jawaban hanya dari bagian {s}', sources: 'Sumber', notlang: 'Jawaban ini kembali dalam bahasa Inggris, bukan bahasa pilihan Anda. Sumbernya ditautkan di bawah.' }
  };

  var CSS = [
    ':host{all:initial;display:block;min-width:0;max-width:100%;--accent:#0b5fff;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:#1d1d1f;font-size:16px;line-height:1.5}',
    '*{box-sizing:border-box}',
    '.w{background:#fff;border:1px solid #d9d9de;border-radius:10px;padding:16px;max-width:100%;min-width:0;overflow-wrap:anywhere}',
    '.out,.ans,.src li,.src a,.ans a,.ans li,.ans p,.q{min-width:0;max-width:100%;overflow-wrap:anywhere}',
    '.ans a,.src a{word-break:break-word}',
    '.top{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}',
    '.top button{font:inherit;font-size:14px;padding:5px 12px;border-radius:999px;border:1px solid #c9c9d0;background:#fff;color:#1d1d1f;cursor:pointer}',
    '.top button[aria-checked=true]{background:var(--accent);border-color:var(--accent);color:#fff}',
    'form{display:flex;gap:8px}',
    'input{flex:1;min-width:0;font:inherit;padding:10px 12px;border:1px solid #9a9aa3;border-radius:8px;background:#fff;color:#1d1d1f}',
    'input:focus,button:focus-visible,a:focus-visible{outline:3px solid var(--accent);outline-offset:2px}',
    '.go{font:inherit;font-weight:600;padding:10px 18px;border:0;border-radius:8px;background:var(--accent);color:#fff;cursor:pointer}',
    '.go:disabled{opacity:.6;cursor:default}',
    '.scope{font-size:12px;color:#5b5b63;margin:8px 0 0}',
    '.out{margin-top:14px}',
    '.out[hidden]{display:none}',
    '.loading{display:flex;align-items:center;gap:10px;color:#5b5b63;font-size:14px}',
    '.spin{width:16px;height:16px;border-radius:50%;border:2px solid #d9d9de;border-top-color:var(--accent);animation:s .8s linear infinite}',
    '@keyframes s{to{transform:rotate(360deg)}}',
    '@media (prefers-reduced-motion:reduce){.spin{animation:none}}',
    '.q{font-size:13px;color:#5b5b63;margin:0 0 8px}',
    '.ans p,.ans ul,.ans ol{margin:0 0 10px}.ans h3{font-size:16px;margin:12px 0 6px}',
    '.ans a{color:var(--accent)}',
    '.ans ul ul,.ans ol ul,.ans ul ol{margin:4px 0}.ans li{margin:2px 0}.ans hr{border:0;border-top:1px solid #e6e6ea;margin:12px 0}',
    'sup.c{font-size:11px;margin-left:1px}sup.c a{text-decoration:none;font-weight:700;padding:0 1px}',
    '.src{border-top:1px solid #e6e6ea;margin-top:12px;padding-top:10px;font-size:14px}',
    '.src h4{margin:0 0 6px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:#5b5b63}',
    '.src ol{margin:0;padding:0;list-style:none}.src li{display:flex;gap:8px;margin:3px 0}',
    '.n{flex:none;width:20px;height:20px;border-radius:50%;background:var(--accent);color:#fff;font-size:11px;font-weight:700;display:inline-flex;align-items:center;justify-content:center}',
    '.src a{color:#1d1d1f;overflow-wrap:anywhere}',
    '.ctas{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}',
    '.ctas a{font-size:14px;font-weight:600;text-decoration:none;padding:8px 14px;border-radius:8px;background:var(--accent);color:#fff}',
    '.ctas a.alt{background:#fff;color:var(--accent);border:1px solid var(--accent)}',
    '.note{font-size:13px;background:#fff6dd;border:1px solid #ecd48a;border-radius:6px;padding:8px 10px;margin-top:10px}',
    '.err button{font:inherit;margin-top:6px;padding:7px 14px;border-radius:8px;border:1px solid var(--accent);background:#fff;color:var(--accent);cursor:pointer;font-weight:600}'
  ].join('\n');

  /* BEGIN mdlite (generated by seed/sync_widget_md.py from static/mdlite.js: do not edit here) */
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
var ESC0='',ESC1='';
var RTL=/[֐-ࣿ]/;
var RUN=/[A-Za-z0-9+(][A-Za-z0-9 ,.:+\-–\/%$&'@()]*[A-Za-z0-9%)]|[A-Za-z0-9]/g;
function isolate(html){
 // Only text nodes: leave tags and entities alone.
 return html.split(/(<[^>]*>|&[a-zA-Z#0-9]+;)/).map(function(part,i){
  if(i%2||!part)return part;
  return part.replace(RUN,function(run){
   var nowrap=/\d/.test(run)&&run.length<=28?' style="white-space:nowrap"':'';
   return '<bdi dir="ltr"'+nowrap+'>'+run+'</bdi>';
  });
 }).join('');
}
function inline(s,o){
 o=o||{};
 var rtl=o.rtl===undefined?RTL.test(s):o.rtl;
 s=esc(s);
 var codes=[];
 s=s.replace(/`([^`\n]+)`/g,function(_,c){codes.push(c);return '\uE002'+String.fromCharCode(0xE200+codes.length-1)+'\uE003'});
 s=s.replace(/\\([*_#\[\]()`>~|\-.!+])/g,function(_,c){return ESC0+String.fromCharCode(0xE100+c.charCodeAt(0))+ESC1});
 s=s.replace(/&lt;(https?:\/\/[^\s&]+?)&gt;/g,'<a href="$1" target="_blank" rel="noopener">$1</a>');
 s=s.replace(/\[([^\]]+)\]\(mailto:([^)\s?]+)[^)]*\)/g,'<a href="mailto:$2">$1</a>');
 s=s.replace(/\[([^\]]+)\]\(tel:(\+?[\d]+)\)/g,'<a href="tel:$2">$1</a>');
 s=s.replace(/\[([^\]]+)\]\((?!https?:\/\/|mailto:|tel:)[^)]*\)/g,'$1');
 s=s.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,'<a href="$2" target="_blank" rel="noopener">$1</a>');
 s=s.replace(/(^|[\s(])(https?:\/\/[^\s<)\u27E6]+[^\s<).,;:!?\u27E6\u27E7])/g,'$1<a href="$2" target="_blank" rel="noopener">$2</a>');
 s=s.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
 s=s.replace(/\*([^*\n]+)\*/g,'<em>$1</em>');
 if(o.cites!==false){
  s=s.replace(/⟦([\d,]+)⟧/g,function(_,n){
   return '<sup class="c">'+n.split(',').map(function(x){return '<a href="#src-'+x+'" aria-label="Source '+x+'">'+x+'</a>'}).join('')+'</sup>';
  });
 }
 if(rtl)s=isolate(s);
 s=s.replace(/\uE002([\uE200-\uE2FF])\uE003/g,function(_,i){return codes[i.charCodeAt(0)-0xE200]});
 return s.replace(new RegExp(ESC0+'([\\uE100-\\uE1FF])'+ESC1,'g'),function(_,n){return esc(String.fromCharCode(n.charCodeAt(0)-0xE100))});
}
// The model sometimes writes a bullet list on ONE line: "...including: * One. * Two" (and after full-width
// stops: "。* Two"). A "*" that follows whitespace or sentence punctuation and is itself followed by
// whitespace is a list marker, not emphasis (emphasis hugs its text), so break the line there.
function splitInlineBullets(t){
 return t.split('\n').map(function(l){
  if(/^\s*[*+\-]\s/.test(l)&&!/\s\*\s+\S.*\s\*\s+\S/.test(l))return l;
  return l.replace(/([\s\u3002\uFF01\uFF1F\uFF1A\uFF1B\uFF09:;.!?)\u201D\u06D4\u061F])\*(?!\*)\s+(?=\S)/g,function(m,p,off,str){
   var before=str.slice(0,off+1).replace(/\s+$/,'').slice(-1),after=str.charAt(off+m.length);
   if(/\d/.test(before)&&/\d/.test(after))return m; // "2 * 3" is arithmetic
   var pre=str.slice(0,off),opens=(pre.match(/(^|[\s(])\*(?=[^\s*])/g)||[]).length,closes=(pre.match(/[^\s*]\*(?=[\s.,;:!?)]|$)/g)||[]).length;
   if(opens>closes)return m; // inside an open *emphasis* span: this star closes it
   return (/\s/.test(p)?'':p)+'\n* ';
  });
 }).join('\n');
}
function md(text,o){
 o=o||{};var h='h'+(o.h||3);
 o=Object.assign({},o,{rtl:RTL.test(String(text))});
 var out=[],stack=[],lines=splitInlineBullets(String(text).replace(/\r/g,'')).split('\n');
 function closeTo(n){while(stack.length>n){out.push('</li></'+stack.pop().t+'>')}}
 lines.forEach(function(l){
  var m;
  if(!l.trim()){closeTo(0);return}
  if(/^\s*(-{3,}|\*{3,})\s*$/.test(l)){closeTo(0);out.push('<hr>');return}
  if((m=l.match(/^\s*#{1,6}\s+(.*)/))){closeTo(0);out.push('<'+h+'>'+inline(m[1],o)+'</'+h+'>');return}
  var li=l.match(/^(\s*)([*+\-]|\d+[.)])\s+(.*)/);
  if(li){
   var ind=li[1].replace(/\t/g,'    ').length,t=/\d/.test(li[2])?'ol':'ul';
   while(stack.length&&stack[stack.length-1].ind>ind)out.push('</li></'+stack.pop().t+'>');
   if(stack.length&&stack[stack.length-1].ind===ind&&stack[stack.length-1].t===t){out.push('</li><li>')}
   else if(stack.length&&stack[stack.length-1].ind===ind){out.push('</li></'+stack.pop().t+'><'+t+'><li>');stack.push({ind:ind,t:t})}
   else{out.push('<'+t+'><li>');stack.push({ind:ind,t:t})}
   out.push(inline(li[3],o));return;
  }
  closeTo(0);out.push('<p>'+inline(l,o)+'</p>');
 });
 closeTo(0);return out.join('');
}
  /* END mdlite */

  function mount(el) {
    if (el.__askMounted) return;
    el.__askMounted = true;
    var langs = (el.getAttribute('data-langs') || 'en').split(',').map(function (s) { return s.trim(); }).filter(function (l) { return I18N[l]; });
    if (!langs.length) langs = ['en'];
    var lang = langs[0];
    var accent = el.getAttribute('data-accent') || '#0b5fff';
    if (!/^#[0-9a-fA-F]{3,8}$/.test(accent)) accent = '#0b5fff';
    var customPh = el.getAttribute('data-placeholder');
    var scope = el.getAttribute('data-scope') || '';
    var scopeLabel = el.getAttribute('data-scope-label') || '';
    var scopeName = el.getAttribute('data-scope-name') || '';
    var base = el.getAttribute('data-api') || BASE;
    var T1 = window.__askT1 || 30000, T2 = window.__askT2 || 70000;

    var root = el.attachShadow({ mode: 'open' });
    root.innerHTML = '<style>' + CSS + '</style><div class="w" part="widget"><div class="top" role="radiogroup" aria-label="Language"></div>' +
      '<form><input type="text" autocomplete="off" aria-label="Question"><button class="go" type="submit"></button></form>' +
      '<p class="scope"></p><div class="out" hidden aria-live="polite"></div></div>';
    root.host.style.setProperty('--accent', accent);
    var w = root.querySelector('.w'), top = root.querySelector('.top'), input = root.querySelector('input'),
      go = root.querySelector('.go'), out = root.querySelector('.out'), scopeEl = root.querySelector('.scope');
    var busy = false;

    function t(k) { return I18N[lang][k]; }
    function paint() {
      w.dir = lang === 'ar' ? 'rtl' : 'ltr';
      w.lang = lang === 'zh' ? 'zh-Hans' : lang;
      input.placeholder = (lang === langs[0] && customPh) ? customPh : t('ph');
      go.textContent = t('ask');
      var sl = scopeLabel || (scope && scopeName ? t('scoped').replace('{s}', scopeName) : '');
      scopeEl.textContent = sl;
      scopeEl.hidden = !sl;
      el.dispatchEvent(new CustomEvent('ask-lang', { detail: lang, bubbles: true, composed: true }));
      top.hidden = langs.length < 2;
      top.innerHTML = '';
      langs.forEach(function (l) {
        var b = document.createElement('button');
        b.type = 'button'; b.textContent = NAMES[l]; b.setAttribute('role', 'radio');
        b.setAttribute('aria-checked', l === lang ? 'true' : 'false');
        b.onclick = function () { lang = l; paint(); };
        top.appendChild(b);
      });
    }
    function show(html) { out.hidden = false; out.innerHTML = html; }
    function post(q, ms) {
      var ctl = new AbortController(), timer = setTimeout(function () { ctl.abort(); }, ms);
      var body = { q: q, lang: lang };
      if (scope) body.scope = scope;
      return fetch(base + '/api/answer', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal: ctl.signal })
        .then(function (r) { clearTimeout(timer); if (!r.ok) { var e = new Error('http'); e.status = r.status; throw e; } return r.json(); },
          function (e) { clearTimeout(timer); throw e; });
    }
    function loading(msg) { show('<div class="loading"><div class="spin"></div><span>' + esc(msg) + '</span></div>'); }
    function failure(q) {
      show('<div class="err"><p>' + esc(t('fail')) + '</p><button type="button">' + esc(t('retry')) + '</button></div>');
      out.querySelector('button').onclick = function () { ask(q); };
    }
    function render(q, d) {
      var dir = d.dir || 'ltr';
      var h = '<p class="q" dir="' + dir + '">' + esc(q) + '</p>';
      if (d.declined) { show(h + '<div class="ans"><p>' + esc(t('declined')) + '</p></div>'); return; }
      h += '<div class="ans" dir="' + dir + '">' + md(d.answer) + '</div>';
      if (d.lang_ok === false) h += '<div class="note">' + esc(t('notlang')) + '</div>';
      h += '<div class="src" dir="ltr"><h4>' + esc(t('sources')) + '</h4><ol>';
      (d.sources || []).forEach(function (s) {
        h += '<li id="src-' + s.n + '"><span class="n">' + s.n + '</span>' + (s.url ? '<a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.title) + '</a>' : '<span>' + esc(s.title) + '</span>') + '</li>';
      });
      h += '</ol></div>';
      if (d.ctas && d.ctas.length) {
        h += '<div class="ctas">' + d.ctas.map(function (c, i) { return '<a class="' + (i ? 'alt' : '') + '" target="_blank" rel="noopener" href="' + esc(c.url) + '">' + esc(c.label) + '</a>'; }).join('') + '</div>';
      }
      show(h);
      // in-widget citation links: shadow ids are not reachable via the host's hash
      Array.prototype.forEach.call(out.querySelectorAll('sup.c a'), function (a) {
        a.addEventListener('click', function (ev) {
          ev.preventDefault();
          var tgt = root.getElementById ? root.getElementById(a.getAttribute('href').slice(1)) : null;
          if (tgt) tgt.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        });
      });
    }
    function ask(q) {
      q = (q || '').trim();
      if (!q || busy) return;
      busy = true; go.disabled = true; loading(t('working'));
      var stalled = function (e) { return e && (e.name === 'AbortError' || e.status === 504); };
      post(q, T1).catch(function (e) {
        if (stalled(e)) { loading(t('slow')); return post(q, T2); }
        throw e;
      }).then(function (d) { render(q, d); }, function () { failure(q); })
        .then(function () { busy = false; go.disabled = false; });
    }
    root.querySelector('form').addEventListener('submit', function (e) { e.preventDefault(); ask(input.value); });
    el.askWidget = { ask: function (q) { input.value = q; ask(q); } };
    paint();
  }

  function init() { Array.prototype.forEach.call(document.querySelectorAll('[data-ask-widget]'), mount); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
