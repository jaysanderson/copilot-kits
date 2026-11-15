/* Shared chrome for every route: the Progress attribution strip, the
   Studycity nav + footer, and the per-route solution-architecture reveal.
   Each page sets `window.SP_PAGE = { nav: 'find-your-path', revealKey: '...' }`
   before loading this script. */
(function () {
  const PAGE = window.SP_PAGE || {};
  const NAV_ITEMS = [
    { id: "find-your-path", label: "Find Your Path", href: "/find-your-path" },
    { id: "study-journey", label: "Study Journey", href: "/study-journey" },
    { id: "student-support", label: "Student Support", href: "/student-support" },
    { id: "community", label: "Community", href: "/community" },
  ];

  function el(html) {
    const t = document.createElement("template");
    t.innerHTML = html.trim();
    return t.content.firstElementChild;
  }

  // ---------- Progress attribution strip ----------
  const strip = el(`
    <div class="progress-strip">
      <div class="progress-strip-brand">
        <img src="/static/brand/quarter-bloom.svg" alt="" style="height:14px;width:14px;opacity:.9;filter:none;" />
        <span>Live demo built for Studycity on Progress Agentic RAG</span>
      </div>
      <button class="progress-strip-btn" id="sp-reveal-btn" type="button">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 2-3 4"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        How this works
      </button>
    </div>
  `);
  document.body.prepend(strip);

  // ---------- Nav ----------
  const navLinks = NAV_ITEMS.map(
    (n) => `<a href="${n.href}" class="${PAGE.nav === n.id ? "sp-active" : ""}">${n.label}</a>`
  ).join("");
  const nav = el(`
    <nav class="sp-nav">
      <div class="sp-wrap sp-nav-inner">
        <a href="/" class="sp-nav-brand"><img src="/static/brand/studycity-logo.svg" alt="Studycity" /></a>
        <ul class="sp-nav-links sp-nav-links-desktop">
          ${navLinks}
        </ul>
        <button class="sp-nav-toggle" id="sp-nav-toggle" aria-label="Open menu">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        </button>
      </div>
      <div class="sp-mobile-menu" id="sp-mobile-menu">${NAV_ITEMS.map((n) => `<a href="${n.href}">${n.label}</a>`).join("")}</div>
    </nav>
  `);
  strip.after(nav);
  document.getElementById("sp-nav-toggle").addEventListener("click", () => {
    document.getElementById("sp-mobile-menu").classList.toggle("sp-open");
  });

  // ---------- Footer ----------
  const footer = el(`
    <footer class="sp-footer">
      <div class="sp-wrap sp-grid sp-grid-3">
        <div>
          <h5>Studycity</h5>
          <p style="max-width:34ch;font-size:13.5px;">The first point of contact for international students looking to study, work and live in Perth, Western Australia.</p>
        </div>
        <div class="sp-footer-cols">
          <h5>Explore</h5>
          ${NAV_ITEMS.map((n) => `<a href="${n.href}">${n.label}</a>`).join("")}
        </div>
        <div class="sp-footer-cols">
          <h5>Take the next step</h5>
          <a href="#" data-external-page="how-to-apply">How to apply</a>
          <a href="#" data-external-page="subscribe">Get updates from Studycity</a>
        </div>
      </div>
      <div class="sp-wrap sp-footer-credit">
        Built on Progress Agentic RAG - every answer on this site is retrieved live from Studycity's own real published content, never invented. Internal field-sales demo, real content used with Studycity's site as the source, sourced from studycity.com.au public pages.
      </div>
    </footer>
  `);
  document.body.appendChild(footer);

  // ---------- Solution-architecture reveal ----------
  const revealKey = PAGE.revealKey || "home";
  const overlay = el(`<div class="sp-reveal-overlay" id="sp-reveal-overlay"><div class="sp-reveal-modal" id="sp-reveal-modal"></div></div>`);
  document.body.appendChild(overlay);
  let built = false;

  async function buildReveal() {
    const modal = document.getElementById("sp-reveal-modal");
    modal.innerHTML = '<div style="padding:40px;text-align:center;">Loading…</div>';
    let r;
    try {
      r = await (await fetch("/api/reveal/" + revealKey)).json();
    } catch (e) {
      r = { title: "How this page works", what: "This page is powered by Progress Agentic RAG underneath Studycity's own real content.", flow: [{ label: "Browser" }, { label: "App proxy" }, { label: "Answer" }], why: "Grounded, cited answers build trust." };
    }
    modal.innerHTML = `
      <div class="sp-reveal-head"><h2>${r.title}</h2><button class="sp-reveal-close" id="sp-reveal-close" aria-label="Close">&times;</button></div>
      <div class="sp-reveal-body">
        <div class="sp-reveal-section"><h3>What this does</h3><p>${r.what}</p></div>
        <div class="sp-reveal-section"><h3>The real flow</h3>
          <div class="sp-flow" id="sp-flow">
            ${r.flow.map((s, i) => `${i > 0 ? '<span class="sp-flow-arrow">&rarr;</span>' : ""}<div class="sp-flow-step" data-step="${i}"><div class="sp-flow-num">${i + 1}</div><strong>${s.label}</strong>${s.detail ? `<div style="margin-top:4px;color:var(--sp-ink-soft);">${s.detail}</div>` : ""}</div>`).join("")}
          </div>
        </div>
        <div class="sp-reveal-section"><h3>Why it matters</h3><p>${r.why}</p></div>
      </div>`;
    document.getElementById("sp-reveal-close").addEventListener("click", () => overlay.classList.remove("sp-open"));
  }

  document.getElementById("sp-reveal-btn").addEventListener("click", async () => {
    overlay.classList.add("sp-open");
    if (!built) { await buildReveal(); built = true; }
    const steps = overlay.querySelectorAll(".sp-flow-step");
    steps.forEach((s) => s.classList.remove("sp-flow-active"));
    let i = 0;
    const tick = () => {
      if (i > 0) steps[i - 1].classList.remove("sp-flow-active");
      if (i < steps.length) { steps[i].classList.add("sp-flow-active"); i++; setTimeout(tick, 480); }
    };
    setTimeout(tick, 150);
  });
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.classList.remove("sp-open"); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") overlay.classList.remove("sp-open"); });

  // Resolve every [data-external-page] link to its real Studycity resource id
  // via /go/<resource_id> (a server-side redirect - the raw external URL never
  // has to appear in client-facing HTML).
  fetch("/api/wellknown").then((r) => r.json()).then((map) => {
    document.querySelectorAll("[data-external-page]").forEach((a) => {
      const key = a.getAttribute("data-external-page");
      if (map[key]) a.setAttribute("href", "/go/" + map[key]);
    });
  }).catch(() => {});
})();
