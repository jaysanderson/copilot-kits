/* ARAG starter chassis - page script. Talks only to this app's /api routes. */
(function () {
  const $ = (id) => document.getElementById(id);
  const md = (t) => (window.MuMd ? window.MuMd.md(t) : t);
  const esc = (t) => (window.MuMd ? window.MuMd.esc(t) : String(t));

  async function api(path, body) {
    const r = await fetch(path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {});
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.error || "Something went wrong talking to the knowledge service.");
    return data;
  }

  async function boot() {
    const cfg = await api("/api/config");
    document.title = cfg.name;
    $("productName").textContent = cfg.name;
    $("promise").textContent = cfg.promise;
    $("chips").innerHTML = (cfg.suggested || []).map((s) => `<button type="button" class="chip">${esc(s)}</button>`).join("");
    $("howList").innerHTML = (cfg.how_it_works || []).map((s) => `<li>${esc(s)}</li>`).join("");
    $("chips").addEventListener("click", (e) => {
      if (e.target.classList.contains("chip")) { $("q").value = e.target.textContent; ask(); }
    });
    $("howBtn").addEventListener("click", () => {
      const open = $("how").hidden; $("how").hidden = !open; $("howBtn").setAttribute("aria-expanded", String(open));
    });
    $("askForm").addEventListener("submit", (e) => { e.preventDefault(); ask(); });
  }

  // Inline superscript markers come from the server's sentence alignment, never from the browser guessing.
  function proseWithMarkers(sentences, answer) {
    if (!sentences || !sentences.length) return md(answer);
    return sentences.map((s) => {
      const mark = s.source === null || s.source === undefined ? "" : `<sup><a href="#src-${s.source + 1}">${s.source + 1}</a></sup>`;
      return md(s.text).replace(/<\/p>\s*$/, mark + "</p>");
    }).join("");
  }

  async function ask() {
    const q = $("q").value.trim(); if (q.length < 3) return;
    $("askBtn").disabled = true; $("result").hidden = false;
    $("badge").className = "badge"; $("badge").textContent = "Reading the sources";
    $("meta").textContent = ""; $("answer").innerHTML = ""; $("sources").innerHTML = "";
    try {
      const lang = $("lang").value || null;
      const d = await api("/api/ask", { question: q, lang });
      $("badge").className = "badge " + (d.confidence.tone || "");
      $("badge").textContent = d.confidence.label; $("badge").title = d.confidence.detail || "";
      $("answer").className = "answer" + (d.withheld ? " withheld" : "");
      $("answer").innerHTML = proseWithMarkers(d.sentences, d.answer);
      $("answer").dir = /[؀-ۿ]/.test(d.answer) ? "rtl" : "ltr";
      $("meta").textContent = d.withheld ? "" : `${d.sources.length} sources shown of ${d.retrieved} retrieved`;
      $("sources").innerHTML = d.sources.map((s, i) => `
        <li class="source" id="src-${i + 1}">
          <span class="n">${i + 1}</span>
          <div><div class="t">${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a>` : esc(s.title)}</div>
          <div class="x">${esc(s.excerpt)}</div></div>
          <span class="r">${s.relevance === null ? "" : "relevance " + s.relevance}</span>
        </li>`).join("");
    } catch (err) {
      $("badge").className = "badge low"; $("badge").textContent = "Not available";
      $("answer").className = "answer withheld"; $("answer").innerHTML = `<p>${esc(err.message)}</p>`;
    } finally { $("askBtn").disabled = false; }
  }

  boot().catch((e) => { $("promise").textContent = "The app could not load its configuration."; console.error(e); });
})();
