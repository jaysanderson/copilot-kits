(function () {
  var $ = function (id) { return document.getElementById(id); };
  var SEC = { study: 'study', explore: 'explore', research: 'research', collaborate: 'collaborate' };
  var trail = [], cur = null, lastReq = null;

  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function secBadge(s) { return el('span', 'sec sec-' + (SEC[s] || 'other'), s === 'home' ? 'site' : s); }
  function say(msg, retry) {
    var s = $('status'); s.textContent = msg || '';
    if (retry) { var b = el('button', 'retry', 'Try again'); b.type = 'button'; b.onclick = retry; s.appendChild(b); }
  }
  // Every network call carries a timeout and a visible failure; a stall is retried once, visibly.
  function call(url, opts, ms) {
    function once(t) {
      var ctl = new AbortController(), timer = setTimeout(function () { ctl.abort(); }, t);
      opts = opts || {}; opts.signal = ctl.signal;
      return fetch(url, opts).then(function (r) { clearTimeout(timer); if (!r.ok) { var e = new Error('http'); e.http = r.status; throw e; } return r.json(); })
        .catch(function (e) { clearTimeout(timer); throw e; });
    }
    return once(ms || 15000).catch(function (e) {
      if (e.http) throw e;
      say('That is taking longer than usual. Trying once more...');
      return once((ms || 15000) * 2);
    });
  }

  function load(id, push) {
    lastReq = function () { load(id, push); };
    say('Reading what this page connects to...');
    call('/api/wander/page?id=' + encodeURIComponent(id)).then(function (d) {
      say('');
      cur = d;
      if (push !== false) trail.push({ id: d.page.id, title: d.page.title });
      render(d);
      window.scrollTo({ top: $('stage').offsetTop - 20, behavior: 'smooth' });
    }).catch(function () { say('We could not read the connections for that page.', lastReq); });
  }

  function render(d) {
    $('stage').hidden = false; $('picks').hidden = true;
    renderTrail(); renderCentre(d); renderMap(d); renderMenu(d); renderLinks(d);
    $('ask-out').textContent = '';
  }
  function renderTrail() {
    var ol = $('trail'); ol.textContent = '';
    trail.forEach(function (t, i) {
      var li = el('li'), b = el('button', null, t.title); b.type = 'button'; b.title = t.title;
      if (i < trail.length - 1) b.onclick = function () { trail = trail.slice(0, i); load(t.id); };
      li.appendChild(b); ol.appendChild(li);
    });
  }
  function renderCentre(d) {
    var c = $('centre'); c.textContent = '';
    var l = el('div');
    l.appendChild(secBadge(d.page.section));
    l.appendChild(el('h2', null, d.page.title));
    var pathEl = el('div', 'path');
    d.page.url.replace('https://www.', '').split('/').forEach(function (seg, i) { if (i) { pathEl.appendChild(document.createTextNode('/')); pathEl.appendChild(document.createElement('wbr')); } var sp = el('span', null, seg); sp.style.whiteSpace = 'nowrap'; pathEl.appendChild(sp); });
    l.appendChild(pathEl);
    var cross = {}; d.links.forEach(function (k) { k.sections.forEach(function (s) { cross[s] = 1; }); });
    var n = Object.keys(cross).length;
    l.appendChild(el('div', 'wd-count', d.links.length + ' shared ' + (d.links.length === 1 ? 'thread' : 'threads') + ', reaching ' + n + ' ' + (n === 1 ? 'section' : 'sections') + ' of the site' + (d.capped ? ' (first 500 relations of a very busy page shown)' : '')));
    c.appendChild(l);
    var a = el('a', 'open', 'Open on university.edu.au'); a.href = d.page.url; a.target = '_blank'; a.rel = 'noopener'; c.appendChild(a);
  }
  var NS = 'http://www.w3.org/2000/svg';
  function s(tag, attrs, text) { var e = document.createElementNS(NS, tag); for (var k in attrs) e.setAttribute(k, attrs[k]); if (text != null) e.textContent = text; return e; }
  var COL = { study: '#E12744', explore: '#00737A', research: '#A5248C', collaborate: '#8A5200' };
  function trunc(t, n) { return t.length > n ? t.slice(0, n - 1) + '…' : t; }
  function renderMap(d) {
    var svg = $('map'); svg.textContent = '';
    var W = 960, H = 620, cx = W / 2, cy = H / 2, links = d.links.slice(0, 7), n = links.length;
    var g = s('g'); svg.appendChild(g);
    links.forEach(function (lk, i) {
      var a = -Math.PI / 2 + (2 * Math.PI * i) / Math.max(n, 1);
      var hx = cx + Math.cos(a) * 150, hy = cy + Math.sin(a) * 125;
      var e = s('line', { x1: cx, y1: cy, x2: hx, y2: hy, class: 'edge', id: 'he' + i }); g.appendChild(e);
      var pages = lk.pages.filter(function (p) { return p.section !== d.page.section; }).concat(lk.pages.filter(function (p) { return p.section === d.page.section; })).slice(0, 4);
      pages.forEach(function (p, j) {
        var spread = 0.42, aa = a + (j - (pages.length - 1) / 2) * spread;
        var px = cx + Math.cos(aa) * 330, py = cy + Math.sin(aa) * 255;
        g.appendChild(s('line', { x1: hx, y1: hy, x2: px, y2: py, class: 'edge', 'data-h': i }));
        var leaf = s('g', { class: 'leaf', tabindex: 0, role: 'button', 'aria-label': 'Go to ' + p.title });
        leaf.appendChild(s('circle', { cx: px, cy: py, r: 9, fill: COL[p.section] || '#495057' }));
        var right = px >= cx, tx = px + (right ? 14 : -14);
        var t = s('text', { x: tx, y: py + 4, 'text-anchor': right ? 'start' : 'end' }, trunc(p.title, 30));
        leaf.appendChild(t);
        leaf.appendChild(s('title', {}, p.title + ' - ' + lk.kind + ': ' + lk.value));
        leaf.addEventListener('click', function () { load(p.id); });
        leaf.addEventListener('keydown', function (ev) { if (ev.key === 'Enter') load(p.id); });
        g.appendChild(leaf);
      });
      var hub = s('g', { class: 'hub', tabindex: 0, role: 'button', 'aria-label': lk.kind + ' ' + lk.value });
      var label = trunc(lk.value, 26), w = Math.max(96, label.length * 7.4 + 22);
      hub.appendChild(s('rect', { x: hx - w / 2, y: hy - 19, width: w, height: 38, rx: 15 }));
      hub.appendChild(s('text', { x: hx, y: hy - 5, class: 'k' }, lk.kind));
      hub.appendChild(s('text', { x: hx, y: hy + 10 }, label));
      hub.addEventListener('click', function () { focusLink(i); });
      hub.addEventListener('keydown', function (ev) { if (ev.key === 'Enter') focusLink(i); });
      hub.id = 'hub' + i; g.appendChild(hub);
    });
    var c = s('g', { class: 'centre' });
    c.appendChild(s('circle', { cx: cx, cy: cy, r: 46 }));
    var words = trunc(d.page.title, 36).split(' '), l1 = '', l2 = '';
    words.forEach(function (w) { if ((l1 + ' ' + w).length < 15 && !l2) l1 = (l1 + ' ' + w).trim(); else l2 = (l2 + ' ' + w).trim(); });
    c.appendChild(s('text', { x: cx, y: cy - (l2 ? 3 : -4) }, l1));
    if (l2) c.appendChild(s('text', { x: cx, y: cy + 13 }, trunc(l2, 16)));
    g.appendChild(c);
    if (!n) svg.appendChild(s('text', { x: cx, y: cy + 80, 'text-anchor': 'middle', fill: '#495057', 'font-size': 14 }, 'No shared threads found for this page.'));
  }
  function focusLink(i) {
    document.querySelectorAll('.wd-link').forEach(function (e) { e.classList.remove('on'); });
    var t = $('link' + i); if (t) { t.classList.add('on'); t.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
  }
  // Reach: this page's own numbers, from the server (counted from the graph data), never typed here.
  function renderReach(m, d) {
    var r = d.reach, s = d.site; if (!r || !s) return;
    var box = el('div', 'wd-reach');
    box.appendChild(el('div', 'wd-reach-h', 'How far this page lets you go in two steps'));
    function bar(label, one, two, cls) {
      var row = el('div', 'wd-reach-row');
      row.appendChild(el('span', 'wd-reach-l', label));
      var track = el('span', 'wd-reach-t'), fill = el('span', 'wd-reach-f ' + cls);
      fill.style.width = Math.max(1, Math.round(100 * two / r.pages)) + '%'; track.appendChild(fill); row.appendChild(track);
      row.appendChild(el('span', 'wd-reach-n', two + ' pages (' + Math.round(100 * two / r.pages) + '%)'));
      row.appendChild(el('span', 'wd-reach-s', one + ' in one step'));
      return row;
    }
    box.appendChild(bar('Site tree: parent, children, siblings', r.tree_one, r.tree_two, 'tree'));
    if (r.thread_one) box.appendChild(bar('Shared threads', r.thread_one, r.thread_two, 'thread'));
    else box.appendChild(el('div', 'wd-reach-hole', 'This page shares none of our ' + 'threads yet, so the tree is all this walk can offer here. Your own taxonomy would close that.'));
    box.appendChild(el('div', 'wd-reach-f2', 'Across all ' + s.pages + ' pages, the tree reaches a median of ' + s.two_steps.tree_median + ' (' + s.two_steps.tree_share + '%) in two steps; threads reach ' + s.two_steps.thread_median + ' (' + s.two_steps.thread_share + '%). ' + s.no_thread_pages + ' pages share no thread at all.'));
    m.appendChild(box);
  }
  function renderMenu(d) {
    var m = $('menu'); m.textContent = '';
    renderReach(m, d);
    var p = el('div'); p.innerHTML = '<b>Parent and children in the site\u2019s tree (one tap each):</b> '; m.appendChild(p);
    var row = el('div', 'chips2');
    function chip(pg, pre) { var b = el('button', null, (pre || '') + pg.title); b.type = 'button'; b.onclick = function () { load(pg.id); }; row.appendChild(b); }
    if (d.parent) chip(d.parent, 'Up: ');
    d.children.slice(0, 8).forEach(function (c) { chip(c, 'Down: '); });
    if (!d.parent && !d.children.length) row.appendChild(el('span', null, 'Nothing nearby in the tree. Every route out of this page is a shared thread below.'));
    m.appendChild(row);
  }
  function renderLinks(d) {
    var box = $('links'); box.textContent = '';
    if (!d.links.length) { box.appendChild(el('p', null, 'This page does not share a thread with other pages in the graph. Try one of the tree neighbours above.')); return; }
    d.links.forEach(function (lk, i) {
      var c = el('article', 'wd-link'); c.id = 'link' + i;
      var h = el('h3'); h.appendChild(el('span', 'kind', lk.kind)); h.appendChild(document.createTextNode(lk.value)); c.appendChild(h);
      var r = el('div', 'reach'); r.appendChild(document.createTextNode(lk.total + ' pages across '));
      lk.sections.forEach(function (sx) { r.appendChild(secBadge(sx)); }); c.appendChild(r);
      if (lk.why) { var q = el('blockquote', null, '“' + lk.why + '”'); q.appendChild(el('small', null, 'From this page. This is why it is linked.')); c.appendChild(q); }
      var tiles = el('div', 'wd-tiles');
      lk.pages.forEach(function (p) {
        var t = el('button', 'wd-tile'); t.type = 'button'; t.appendChild(secBadge(p.section)); t.appendChild(el('span', 't', p.title));
        if (p.why) t.appendChild(el('span', 'w', '“' + p.why + '”'));
        t.appendChild(el('span', 'm', p.tree_steps > 1 ? p.tree_steps + ' steps apart in the site\u2019s own tree' : 'Right beside it in the site\u2019s own tree'));
        t.onclick = function () { load(p.id); }; tiles.appendChild(t);
      });
      c.appendChild(tiles); box.appendChild(c);
    });
  }

  // Start: a real search finds where the visitor is.
  $('start-form').addEventListener('submit', function (e) {
    e.preventDefault();
    var q = $('sq').value.trim(); if (!q) return;
    var go = function () {
      say('Finding your starting point...');
      call('/api/wander/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ q: q }) }).then(function (d) {
        say(''); var box = $('picks'); box.textContent = ''; box.hidden = false;
        if (!d.pages.length) { say('Nothing on the site matched that. Try different words, or start from one of the pages above.'); return; }
        box.appendChild(el('div', null, 'Pick the page closest to where you are:'));
        d.pages.forEach(function (p) {
          var b = el('button', 'wd-pick'); b.type = 'button'; b.appendChild(secBadge(p.section)); b.appendChild(document.createTextNode(p.title));
          b.onclick = function () { trail = []; load(p.id); }; box.appendChild(b);
        });
      }).catch(function () { say('We could not search just now.', go); });
    };
    go();
  });
  $('starts').addEventListener('click', function (e) { var b = e.target.closest('button[data-id]'); if (b) { trail = []; load(b.dataset.id); } });

  // Ask across the walk: the walked pages scope retrieval, the walked relations ride along as context.
  $('ask-form').addEventListener('submit', function (e) {
    e.preventDefault();
    var q = $('aq').value.trim(); if (!q || !cur) return;
    var ids = {}; ids[cur.page.id] = 1; var ctx = [];
    cur.links.forEach(function (lk) {
      lk.pages.forEach(function (p) { ids[p.id] = 1; });
      ctx.push('In the University site graph, "' + cur.page.title + '" is connected to ' + lk.pages.slice(0, 4).map(function (p) { return '"' + p.title + '"'; }).join(', ') + ' because they share the ' + lk.kind.toLowerCase() + ' "' + lk.value + '".');
    });
    var out = $('ask-out'); out.textContent = 'Reading the connected pages...';
    var go = function () {
      call('/api/wander/answer', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ q: q, ids: Object.keys(ids), context: ctx.slice(0, 6) }) }, 30000).then(function (d) {
        out.textContent = '';
        if (d.declined) { out.textContent = 'The pages on this walk do not answer that on their own. Walk somewhere else, or ask the whole site.'; var a = el('a', null, 'Ask the whole site'); a.href = '/'; a.style.marginInlineStart = '8px'; out.appendChild(a); return; }
        var ans = el('div', 'ans');
        ans.innerHTML = MuMd.md(d.answer, { h: 4 });
        out.appendChild(ans);
        var src = el('div', 'src'); src.appendChild(el('strong', null, 'Drawn from'));
        d.sources.forEach(function (p) { var b = el('button'); b.type = 'button'; b.appendChild(secBadge(p.section)); b.appendChild(document.createTextNode(p.title)); b.onclick = function () { load(p.id); }; src.appendChild(b); });
        out.appendChild(src);
      }).catch(function () { out.textContent = 'We could not answer just now. '; var b = el('button', 'retry', 'Try again'); b.type = 'button'; b.onclick = go; out.appendChild(b); });
    };
    go();
  });

  // How this works
  $('how').onclick = function () {
    $('modal').hidden = false;
    fetch('/wander/reveal').then(function (r) { return r.text(); }).then(function (t) { $('modal-content').innerHTML = t; });
  };
  $('modal-x').onclick = function () { $('modal').hidden = true; };
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') $('modal').hidden = true; });
  var sp = new URLSearchParams(location.search); if (sp.get('page')) load(sp.get('page'));
})();
