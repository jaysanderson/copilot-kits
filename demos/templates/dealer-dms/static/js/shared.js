/* Ignition DMS - shared frontend utilities.
   No client-side ARAG key or endpoint host ever appears here - every ARAG call
   goes through this app's own /api/* proxy. */

const IGN = (() => {

  // ---- brand mark: a faithful recreation of Revolution's own emblem (rev.com.au) -
  // a segmented ring in two blue tones on a dark navy chip, echoing the ring motif
  // that stands in for the "O" in their "REVOLUTION" wordmark (Field Rule 8 - this
  // app's real captured identity, not a generic factory glyph). See
  // content/demos/revolution-brand-capture.md for the source screenshot and hex values.
  function logoSVG(size = 30) {
    return `<svg class="mark" width="${size}" height="${size}" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="20" cy="20" r="19" fill="#050b26"/>
      <circle cx="20" cy="20" r="19" stroke="#2964f6" stroke-opacity=".4" stroke-width="1"/>
      <circle cx="20" cy="20" r="14" stroke="url(#ignGrad)" stroke-width="4.2" stroke-linecap="round" stroke-dasharray="52 200" stroke-dashoffset="-2" fill="none"/>
      <circle cx="20" cy="20" r="14" stroke="#7ea3ff" stroke-width="4.2" stroke-linecap="round" stroke-dasharray="18 200" stroke-dashoffset="-62" fill="none" opacity="0.85"/>
      <circle cx="20" cy="20" r="14" stroke="#2964f6" stroke-width="4.2" stroke-linecap="round" stroke-dasharray="26 200" stroke-dashoffset="-88" fill="none"/>
      <defs><linearGradient id="ignGrad" x1="4" y1="6" x2="36" y2="34" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="#2964f6"/><stop offset="1" stop-color="#7ea3ff"/>
      </linearGradient></defs>
    </svg>`;
  }

  // ---- dash normalisation: dash codepoints ONLY, explicit escape (B44) ----
  function normaliseDashes(s) {
    if (!s) return s;
    return String(s).replace(/\s*[—–]\s*/g, ' - ');
  }

  // ---- minimal markdown renderer, loose-list aware (gate 8 / B46) ----
  function renderMarkdown(src) {
    if (!src) return '';
    src = normaliseDashes(src);
    // Nuclia's extracted plain text collapses a real markdown line/paragraph
    // break into a run of 2+ spaces rather than preserving it as a newline
    // (confirmed on this corpus: "Standard     Applies" - 5 spaces where the
    // source had a blank line, vs single spaces for genuine word gaps).
    // Left uncorrected, a heading like "## Inspection standard   Every..."
    // ends up on one physical line with its own body text and never matches
    // as a heading - B46 raw "##" visible on screen. Normalise every 2+-space
    // run back into a real newline BEFORE line-based parsing.
    src = src.replace(/[ \t]{2,}/g, '\n');
    const lines = src.replace(/\r\n/g, '\n').split('\n');
    let html = '';
    let i = 0;
    let inList = null; // 'ul' | 'ol'

    function closeList() {
      if (inList) { html += `</${inList}>`; inList = null; }
    }
    function inline(text) {
      text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      text = text.replace(/(?<!\*)\*([^*\n]+?)\*(?!\*)/g, '<em>$1</em>');
      text = text.replace(/`([^`]+?)`/g, '<code>$1</code>');
      text = text.replace(/\[\[(\d+)\]\]/g, (m, n) => `<a href="#src-${n}" class="cite-mark" data-cite="${n}">${n}</a>`);
      return text;
    }
    // peek helper: does the list continue past a blank line? (B46 loose-list trap)
    function listContinues(fromIdx) {
      let j = fromIdx;
      while (j < lines.length && lines[j].trim() === '') j++;
      return j < lines.length && /^\s*([-*]|\d+\.)\s+/.test(lines[j]);
    }

    while (i < lines.length) {
      const line = lines[i];
      if (line.trim() === '') {
        if (inList && listContinues(i + 1)) { i++; continue; }
        closeList();
        i++;
        continue;
      }
      let m;
      if ((m = line.match(/^(#{1,4})\s+(.*)$/))) {
        closeList();
        const level = Math.min(m[1].length + 1, 4);
        html += `<h${level}>${inline(m[2])}</h${level}>`;
        i++;
        continue;
      }
      if ((m = line.match(/^\s*[-*]\s+(.*)$/))) {
        if (inList !== 'ul') { closeList(); html += '<ul>'; inList = 'ul'; }
        html += `<li>${inline(m[1])}</li>`;
        i++;
        continue;
      }
      if ((m = line.match(/^\s*\d+\.\s+(.*)$/))) {
        if (inList !== 'ol') { closeList(); html += '<ol>'; inList = 'ol'; }
        html += `<li>${inline(m[1])}</li>`;
        i++;
        continue;
      }
      closeList();
      // gather a paragraph (consecutive non-blank, non-list, non-heading lines)
      let para = [line];
      i++;
      while (i < lines.length && lines[i].trim() !== '' &&
             !/^\s*([-*]\s+|\d+\.\s+|#{1,4}\s+)/.test(lines[i])) {
        para.push(lines[i]); i++;
      }
      html += `<p>${inline(para.join(' '))}</p>`;
    }
    closeList();
    return html;
  }

  // ---- qualitative confidence badge: groundedness-primary (B34/B39) ----
  function confidenceLabel(remi) {
    if (!remi || remi.groundedness == null) return { label: 'Trust read unavailable', cls: 'moderate' };
    const g = remi.groundedness, ar = remi.answer_relevance ?? remi.answerRelevance ?? 5;
    if (g >= 4) return { label: 'High confidence', cls: 'high' };
    if (g >= 2.5) return { label: 'Moderate confidence', cls: 'moderate' };
    return { label: 'Low confidence', cls: 'low' };
  }

  // ---- resolved source deep-link: /r/{id}?hl=start-end (Standard B23) ----
  function sourceHref(source) {
    if (!source) return '#';
    if (source.hl_start != null && source.hl_end != null) {
      return `/r/${source.resource_id}?hl=${source.hl_start}-${source.hl_end}`;
    }
    return `/r/${source.resource_id}`;
  }

  async function api(path, opts = {}) {
    const res = await fetch(path, {
      method: opts.method || 'GET',
      headers: { 'Content-Type': 'application/json' },
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`Request failed (${res.status})`);
    }
    return res.json();
  }

  // ---- solution-architecture reveal (gate 11 / B12) ----
  function mountReveal(flowSpec) {
    const btn = document.getElementById('how-it-works-btn');
    const backdrop = document.getElementById('reveal-backdrop');
    if (!btn || !backdrop) return;
    const title = backdrop.querySelector('.reveal-title');
    const flow = backdrop.querySelector('.flow-diagram');
    const whatEl = backdrop.querySelector('.reveal-what');
    const whyEl = backdrop.querySelector('.reveal-why');
    const techEl = backdrop.querySelector('.reveal-tech');

    title.textContent = flowSpec.title;
    flow.innerHTML = flowSpec.nodes.map((n, idx) => {
      const arrow = idx < flowSpec.nodes.length - 1 ? '<span class="flow-arrow">&#8594;</span>' : '';
      return `<div class="flow-node ${n.active ? 'pulsing' : ''}">${n.label}<span class="tag">${n.tag}</span></div>${arrow}`;
    }).join('');
    whatEl.textContent = flowSpec.what;
    whyEl.textContent = flowSpec.why;
    techEl.textContent = flowSpec.tech;

    btn.addEventListener('click', () => { backdrop.hidden = false; });
    backdrop.addEventListener('click', (e) => { if (e.target === backdrop) backdrop.hidden = true; });
    backdrop.querySelector('.modal-close').addEventListener('click', () => { backdrop.hidden = true; });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') backdrop.hidden = true; });
  }

  function escHtml(s) {
    return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // For any PLAIN-TEXT (non-markdown) render of LLM-generated copy - catalogue
  // titles/summaries, structured diagnosis fields - that only ever goes
  // through escHtml, never renderMarkdown (which normalises dashes as part of
  // its own pipeline). Server-side generation already scrubs at cache-write
  // time (arag.scrub_dashes); this is the client-side second layer so a
  // render path can never regress silently (hard rule 2 applies to model
  // output, not just hand-written copy - the revolution-dms lesson).
  function cleanText(s) {
    return escHtml(normaliseDashes(s));
  }

  return { logoSVG, normaliseDashes, renderMarkdown, confidenceLabel, api, mountReveal, escHtml, sourceHref, cleanText };
})();
