/* Shared safe markdown + INLINE SUPERSCRIPT CITATION rendering (table-stakes
   B33) - used by the concierge widget, the Student Support page, and the
   Study Journey milestone copy. A citation's `ranges` are real character
   offsets into the answer text that paragraph supports (from ARAG's own
   /ask citations payload) - a superscript marker is placed at the END of
   each range, not bolted on as a separate source list only. */
(function () {
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  // Real defect found live (29 Sep 2026, a pitch-deck capture of the deployed
  // app): several citations frequently report the SAME character offset (a
  // documented ARAG platform pattern - CLAUDE.md's "citations must distribute
  // per-claim" note; the very first KB probe on this build already showed 10
  // citations all mapping to range [0,71]). Multiple <sup> numbers rendered
  // back to back with no separator read as one multi-digit number
  // ("fields:34569"). Each citation now gets its own bracket - [3][4][5] -
  // which cannot visually merge into a number no matter how many collide.
  function citationMarkers(nums) {
    return nums.map((n) => `<sup class="sp-cite" data-cite="${n}" title="Source ${n}">[${n}]</sup>`).join("");
  }

  // Real defect found live in the same capture: a markdown bullet list ("* Business
  // & Management") rendered as literal asterisks on screen - table-stakes gate 8's
  // named defect. Converts a block of consecutive "* "/"- " lines into a genuine
  // <ul><li> list; runs on the already citation-marked, HTML-escaped string, so it
  // only ever matches literal "*"/"-" at a real line start, never inside an
  // inserted <sup> tag (which never begins a line).
  function renderLists(html) {
    const lines = html.split("\n");
    const out = [];
    let buf = [];
    const flushList = () => {
      if (buf.length) {
        out.push(`<ul>${buf.map((li) => `<li>${li}</li>`).join("")}</ul>`);
        buf = [];
      }
    };
    lines.forEach((line) => {
      // A citation marker can legitimately land at the very start of a bullet
      // line (its offset is the end of the PRECEDING text, which can be right
      // where the list begins) - tolerate leading <sup> marker HTML before the
      // bullet character, or the whole line silently fails to become a list
      // item (found live, 29 Sep 2026: exactly this landed the first bullet's
      // marker-prefixed line back out as raw "* Business & Management" text
      // while the unmarked bullets after it converted correctly).
      const m = line.match(/^((?:<sup[^>]*>.*?<\/sup>)*)\s*[-*]\s+(.*)$/);
      if (m) {
        buf.push(m[1] + m[2]);
      } else {
        flushList();
        out.push(line);
      }
    });
    flushList();
    return out.join("\n");
  }

  function renderAnswer(text, citations) {
    text = text || "";
    citations = citations || [];
    const insertions = {};
    citations.forEach((c) => {
      (c.ranges || []).forEach((r) => {
        const end = Array.isArray(r) ? r[1] : null;
        if (end == null || end > text.length) return;
        insertions[end] = insertions[end] || [];
        if (!insertions[end].includes(c.num)) insertions[end].push(c.num);
      });
    });
    const positions = Object.keys(insertions).map(Number).sort((a, b) => a - b);
    let out = "";
    let last = 0;
    positions.forEach((pos) => {
      out += escapeHtml(text.slice(last, pos));
      out += citationMarkers(insertions[pos]);
      last = pos;
    });
    out += escapeHtml(text.slice(last));
    // Light markdown on the escaped+marked-up string - safe, since ** and
    // leading */- never appear inside our own inserted <sup> tags.
    out = out.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    const paras = out.split(/\n{2,}/).map((p) => p.trim()).filter(Boolean);
    if (!paras.length) return "<p></p>";
    return paras
      .map((p) => {
        const withLists = renderLists(p);
        // A paragraph that became entirely a <ul> needs no <p> wrapper or <br/>
        // conversion (which would otherwise inject line breaks inside <li>s
        // via the plain-text lines already consumed into renderLists).
        if (/^<ul>[\s\S]*<\/ul>$/.test(withLists.trim())) return withLists;
        return `<p>${withLists.replace(/\n/g, "<br/>")}</p>`;
      })
      .join("");
  }

  // For short model-generated strings with no citations (Study Journey milestone
  // guidance, Find Your Path hook/highlights) - same bold/list handling as
  // renderAnswer, minus the citation-offset machinery those fields don't carry.
  // Every surface that shows generated text needs this, not only the main
  // answer panel - the same class of defect is always partial (visible on one
  // route, invisible on another) until every render path is checked.
  function renderInline(text) {
    let out = escapeHtml(text || "");
    out = out.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    return renderLists(out);
  }

  // Default-visible qualitative confidence badge (table-stakes B34/B42) - never
  // a raw REMi numeral, and a low reading names an action rather than just a
  // label. `confidence` is {label, tone, detail} from the server (tone one of
  // "high"/"medium"/"low"/"unknown"/"cited") or null/undefined when there is
  // nothing to be confident about (an honest decline carries no badge, same
  // as it carries no citation row).
  function renderConfidenceBadge(confidence) {
    if (!confidence || !confidence.label) return "";
    const tone = confidence.tone || "unknown";
    return `<div class="sp-confidence sp-confidence-${tone}">
      <span class="sp-confidence-label">${escapeHtml(confidence.label)}</span>
      <span class="sp-confidence-detail">${escapeHtml(confidence.detail || "")}</span>
    </div>`;
  }

  function renderCitationList(citations) {
    if (!citations || !citations.length) return "";
    return `<div class="sp-cite-row">${citations
      .map((c) => `<a class="sp-cite-pill" href="/r/${c.resource_id}?p=${encodeURIComponent(c.paragraph_id || "")}" data-cite-target="${c.num}">${c.num}. ${escapeHtml(c.title)}</a>`)
      .join("")}</div>`;
  }

  // Clicking an inline <sup> marker scrolls to / highlights its pill below,
  // and a click on the pill (or the marker itself, via a resolved element
  // click on desktop) opens the real cited page.
  function wireCitationClicks(container) {
    container.querySelectorAll(".sp-cite").forEach((sup) => {
      sup.addEventListener("click", () => {
        const n = sup.getAttribute("data-cite");
        const pill = container.querySelector(`[data-cite-target="${n}"]`);
        if (pill) window.location.href = pill.getAttribute("href");
      });
    });
  }

  window.SPAnswer = { escapeHtml, renderAnswer, renderInline, renderCitationList, renderConfidenceBadge, wireCitationClicks };
})();
