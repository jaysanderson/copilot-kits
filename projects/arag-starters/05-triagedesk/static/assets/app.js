// Shared shell + components for the AkademDocs Pre-Check officer console.
// This file only ever talks to this app's own /api/* surface - no ARAG
// endpoint names, keys or host strings anywhere here (gate 5/6/9).

// ------------------------------------------------------------------ basics
function escapeHtml(s) {
  if (s === null || s === undefined) return "";
  return String(s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

async function fetchJSON(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) {
    let detail = r.statusText;
    try { detail = (await r.json()).detail || detail; } catch (e) {}
    throw new Error(detail);
  }
  return r.json();
}

function fmtDate(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, { year: "numeric", month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit" });
  } catch (e) { return iso; }
}
function fmtDateShort(iso) {
  try { return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "2-digit" }); }
  catch (e) { return iso; }
}
function scriptDir(text) {
  return /[֐-׿]/.test(text || "") ? "rtl" : "ltr";
}

// ------------------------------------------------------------------ icons (inline, functional only - no decorative icon-in-square filler)
const ICONS = {
  queue: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="4" rx="1"/><rect x="3" y="10" width="18" height="4" rx="1"/><rect x="3" y="16" width="18" height="4" rx="1"/></svg>`,
  upload: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16V4"/><path d="M6 10l6-6 6 6"/><path d="M4 20h16"/></svg>`,
  chart: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20V10"/><path d="M12 20V4"/><path d="M20 20v-7"/><path d="M2 20h20"/></svg>`,
  book: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`,
  info: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 8h.01"/></svg>`,
  browser: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18"/><circle cx="6.5" cy="6.5" r=".6" fill="currentColor" stroke="none"/></svg>`,
  server: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="6" rx="1.5"/><rect x="3" y="14" width="18" height="6" rx="1.5"/><path d="M7 7h.01M7 17h.01"/></svg>`,
  spark: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v3M12 18v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M3 12h3M18 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/><circle cx="12" cy="12" r="3.2"/></svg>`,
  scan: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8V5a1 1 0 0 1 1-1h3M20 8V5a1 1 0 0 1-1-1h-3M4 16v3a1 1 0 0 0 1 1h3M20 16v3a1 1 0 0 1-1 1h-3"/><path d="M4 12h16"/></svg>`,
  check: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>`,
  checkCircle: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="m8.5 12.3 2.3 2.3 4.7-4.9"/></svg>`,
  alertCircle: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v5"/><path d="M12 16h.01"/></svg>`,
  reviewCircle: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M15 9l-6 6M9 9l6 6"/></svg>`,
  question: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9.2 9a2.8 2.8 0 1 1 3.8 2.6c-.8.4-1.2 1-1.2 1.9"/><path d="M12 17h.01"/></svg>`,
  arrowDown: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v15"/><path d="m5 13 7 7 7-7"/></svg>`,
};

// ------------------------------------------------------------------ vocab labels (single source - never render a raw enum)
const DOC_TYPE_LABEL = {
  DIPLOMA: "Diploma",
  TRANSCRIPT: "Academic transcript",
  NAME_CHANGE_CERTIFICATE: "Name-change certificate",
  INSTITUTION_NAME_CHANGE_CERTIFICATE: "Institution name-change certificate",
  EQUIVALENCY_CERTIFICATE: "Equivalency certificate",
  UNRECOGNISED: "Unrecognised document",
};
function docTypeLabel(t) { return DOC_TYPE_LABEL[t] || t; }

const STATUS_LABEL = { READY: "Ready", NEEDS_ATTENTION: "Needs attention", NEEDS_HUMAN_REVIEW: "Needs human review" };
function statusPill(status) {
  return `<span class="pill ${escapeHtml(status)}"><span class="dot"></span>${escapeHtml(STATUS_LABEL[status] || status)}</span>`;
}
function severityPill(sev) {
  const label = { INFO: "Info", ATTENTION: "Attention", REVIEW: "Review" }[sev] || sev;
  return `<span class="pill ${escapeHtml(sev)}"><span class="dot"></span>${escapeHtml(label)}</span>`;
}

// Qualitative confidence badge (B34/B39) - derived server-side from a live
// REMi groundedness read scored against the full retrieved context, never a
// raw numeral shown by default. See app/pipeline.py's REMi aggregation.
function confidenceBadge(level) {
  const cfg = {
    High: { icon: ICONS.checkCircle, label: "High confidence extraction" },
    Moderate: { icon: ICONS.alertCircle, label: "Moderate confidence extraction" },
    Low: { icon: ICONS.reviewCircle, label: "Low confidence - verify manually" },
  }[level] || { icon: ICONS.question, label: "Confidence unavailable" };
  return `<span class="confidence-badge ${escapeHtml(level)}" title="Derived from a live REMi groundedness read against this document's full retrieved page context">${cfg.icon}${cfg.label}</span>`;
}

// ------------------------------------------------------------------ signed-in persona chip (B14 - name + role, never a bare name)
const OFFICER = { name: "L. Kessler", role: "Reviewing Officer, Credential Recognition Unit" };

// ------------------------------------------------------------------ shell
const NAV = [
  ["/", "Queue", ICONS.queue],
  ["/submit", "New submission", ICONS.upload],
  ["/insights", "Insights", ICONS.chart],
  ["/codes", "Feedback codes", ICONS.book],
];

function railHtml(active) {
  const links = NAV.map(([href, label, icon]) => `
    <a href="${href}" class="${active === href ? "active" : ""}">${icon}<span>${label}</span></a>
  `).join("");
  return `
    <div class="rail">
      <div class="rail-brand">
        <div class="name"><span class="mark">&#9673;</span>AkademDocs</div>
        <div class="sub">Credential Pre-Check Service</div>
      </div>
      <div class="rail-persona">
        <div class="who">${escapeHtml(OFFICER.name)}</div>
        <div class="role">${escapeHtml(OFFICER.role)}</div>
      </div>
      <div class="rail-nav">${links}</div>
      <div class="rail-foot">Synthetic demonstration data - no real applicant records. Runs on Progress Agentic RAG.</div>
    </div>`;
}

function tabbarHtml(active) {
  const links = NAV.map(([href, label, icon]) => `
    <a href="${href}" class="${active === href ? "active" : ""}">${icon}<span>${label.split(" ")[0]}</span></a>
  `).join("");
  return `<div class="mobile-tabbar">${links}</div>`;
}

function topstripHtml(routeKey) {
  return `
    <div class="topstrip">
      <div style="display:flex;align-items:center;gap:16px;">
        <img class="arag-lockup" src="/assets/brand/primary-horizontal-alternate.svg" alt="Progress Agentic RAG">
        <span class="tagline">Case-management integration demo for ICT &amp; Solutions leaders</span>
      </div>
      <button class="hiw-trigger" id="hiwBtn" type="button">${ICONS.info}How this works</button>
      <div class="hexcrop"><img src="/assets/brand/hex-loop-rgb.svg" alt=""></div>
    </div>`;
}

function mountShell(active, routeKey) {
  document.getElementById("topstrip").innerHTML = topstripHtml(routeKey);
  document.getElementById("rail").innerHTML = railHtml(active);
  document.getElementById("tabbar").innerHTML = tabbarHtml(active);
  document.getElementById("hiwHost").innerHTML = renderHowItWorksModal(routeKey);
  wireHowItWorks();
}

// ------------------------------------------------------------------ how-this-works: page-specific, three-part, real diagram (B12)
const HIW_SPECS = {
  queue: {
    title: "How the queue works",
    intro: "Every case below was already pre-checked end to end at submission time - the queue is a read of stored, structured verdicts, not a live model call.",
    what: "You're looking at every submission this service has pre-checked, grouped by how much officer attention it needs. Nothing here was typed in by a person - every document type, status and flag came out of the pipeline described on the New submission page.",
    why: "An officer with 40 files in their tray can go straight to the 3 that need human review instead of reading all 40 top to bottom. The pre-check does the first pass; the officer still makes the decision.",
    diagram: [
      { icon: ICONS.browser, title: "Your browser", detail: "Requests the case list from this app's own API.", arag: false },
      { icon: ICONS.server, title: "This app's server", detail: "Reads already-computed verdicts from its local case store (SQLite) and groups them by review priority - no new ARAG call on this page.", arag: false },
      { icon: ICONS.browser, title: "Back to your browser", detail: "Renders the grouped queue with real counts per group.", arag: false },
    ],
  },
  submit: {
    title: "How a new submission is pre-checked",
    intro: "This is the page where Agentic RAG actually reads the documents. Everything below is this specific request's real flow, not a marketing diagram.",
    what: "You upload one or more files (a single messy multi-page PDF is fine). The service splits them into pages, checks each page's scan quality locally, sends each page to Agentic RAG to be read and classified, then assembles everything into one structured, closed-vocabulary verdict.",
    why: "A human clerk doing this by hand might take 10-15 minutes per application and still miss an inconsistency across five documents. This turns unstructured scans into a structured, checkable verdict in seconds - and every fact it states links back to the exact source page.",
    diagram: [
      { icon: ICONS.browser, title: "Your browser", detail: "Uploads the file(s). This app's ARAG credential never reaches the browser - every ARAG call below happens server-side.", arag: false },
      { icon: ICONS.server, title: "This app's server", detail: "Splits the PDF into individual pages with real page numbers, and runs local deterministic legibility checks (blur / dark / cropped / rotated) so the same page always scores the same way.", arag: false },
      { icon: ICONS.spark, title: "Agentic RAG - document ingest", detail: "Each page is ingested into this service's document repository. ARAG's own visual-extraction pipeline reads the page - no third-party OCR vendor anywhere in this pipeline.", arag: true },
      { icon: ICONS.spark, title: "Agentic RAG - classification & extraction", detail: "A scoped, synchronous grounded query classifies the document type and extracts the applicant name, institution, degree, date and authenticity indicators, with citations back to the source text. A background Labeler DA task (registered on this document repository, inspectable in the ARAG console) independently double-checks the same classification; when it has already landed, its label is preferred.", arag: true },
      { icon: ICONS.spark, title: "Agentic RAG - REMi groundedness read", detail: "A live call to Agentic RAG's REMi quality engine scores that answer against the FULL page context it was retrieved from (never just the trimmed display snippet) - genuine groundedness, answer-relevance and context-relevance scores, never fabricated. The result becomes the confidence badge on the case detail page, shown qualitatively - the raw REMi score is never surfaced to the officer.", arag: true },
      { icon: ICONS.server, title: "This app's server, again", detail: "Transliterates and fuzzy-matches the declared name, merges same-type pages into logical documents, checks completeness and duplicates, and assembles the closed-vocabulary verdict - only codes from a fixed catalogue, never free text.", arag: false },
      { icon: ICONS.browser, title: "Back to your browser", detail: "Redirects to the case detail view with the full structured result.", arag: false },
    ],
  },
  detail: {
    title: "How this case view stays auditable",
    intro: "Every extracted fact you can see traces back to the exact page and passage Agentic RAG read it from - that's the point of the numbered source markers.",
    what: "This is one stored verdict, rendered in full: the documents Agentic RAG identified, the fields it extracted from each, the authenticity indicators it read, and the closed-vocabulary messages the pipeline generated. Numbered markers next to a fact open the real page image with the grounding passage highlighted. Each document's confidence badge is a live REMi groundedness read - Agentic RAG's own quality engine scoring the classification answer against its full retrieved context - shown qualitatively, never as a raw score. A document that never got a usable REMi read falls back honestly to a field-completeness signal instead of pretending REMi ran.",
    why: "A black-box AI verdict is not defensible in a government process. This view lets an officer (or an auditor) check any single claim against the actual source document in two clicks, and check HOW MUCH to trust it via a real quality read, not take the system's word for either.",
    diagram: [
      { icon: ICONS.server, title: "This app's server", detail: "Reads the stored verdict, including each citation's page number and snippet, and each document's REMi groundedness read - all saved at pre-check time.", arag: false },
      { icon: ICONS.browser, title: "Your browser", detail: "Renders the verdict with inline numbered markers at each grounded fact and a qualitative confidence badge. Clicking a marker opens the real scanned page with the cited passage highlighted.", arag: false },
    ],
  },
  insights: {
    title: "How these insights are built",
    intro: "Every chart on this page is aggregated from what Agentic RAG actually extracted from unstructured scans across every processed case - not manually entered statistics.",
    what: "This page counts real outcomes across every case this service has pre-checked: which document types appear, which legibility and authenticity issues recur, which languages show up, how often Agentic RAG's synchronous read agreed with its independent background Labeler task, and the real distribution of REMi groundedness scores behind every confidence badge in the estate.",
    why: "A single case view proves the pipeline works once. This view is the program-level evidence: where applicants across the whole intake genuinely struggle (poor scans, missing certificates, unsupported languages), and whether the system's own confidence in its reads is holding up at scale - the kind of signal that should change policy or resourcing, not just one officer's queue.",
    diagram: [
      { icon: ICONS.server, title: "This app's server", detail: "Aggregates every stored verdict's document types, legibility issues, authenticity flags, classification source and REMi groundedness band - all values Agentic RAG derived from reading unstructured page images, not fields a human typed in.", arag: false },
      { icon: ICONS.browser, title: "Your browser", detail: "Renders the aggregates as charts, never a raw table of every case.", arag: false },
    ],
  },
  codes: {
    title: "How the feedback-code catalogue works",
    intro: "This page never calls Agentic RAG - it serves a fixed, versioned vocabulary so every applicant sees consistent, pre-translated wording.",
    what: "The full closed set of feedback codes this service can ever emit, in five languages, each marked honestly as to whether this build's pipeline can actually detect it today.",
    why: "Free-text AI explanations to an applicant are a liability in a government process - inconsistent wording, and a translation risk. A closed, versioned, pre-translated vocabulary is auditable and safe to publish.",
    diagram: [
      { icon: ICONS.server, title: "This app's server", detail: "Serves the fixed code catalogue from its own configuration.", arag: false },
      { icon: ICONS.browser, title: "Your browser", detail: "Renders it with a live language toggle - the same catalogue, re-rendered instantly.", arag: false },
    ],
  },
};

function renderHowItWorksModal(routeKey) {
  const spec = HIW_SPECS[routeKey] || HIW_SPECS.queue;
  const nodes = spec.diagram.map((n, i) => `
    <div class="hiw-node ${n.arag ? "arag" : ""}" style="animation-delay:${i * 90}ms">
      <div class="n-icon">${n.icon}</div>
      <div><div class="n-title">${escapeHtml(n.title)}</div><div class="n-detail">${escapeHtml(n.detail)}</div></div>
    </div>
    ${i < spec.diagram.length - 1 ? `<div class="hiw-arrow">${ICONS.arrowDown}</div>` : ""}
  `).join("");
  return `
    <div class="hiw-overlay" id="hiwOverlay">
      <div class="hiw-modal">
        <button class="hiw-close" id="hiwClose" aria-label="Close">&times;</button>
        <h2>${escapeHtml(spec.title)}</h2>
        <p class="hiw-intro">${escapeHtml(spec.intro)}</p>
        <div class="hiw-section">
          <div class="hiw-kicker">What this page is doing</div>
          <div class="hiw-body">${escapeHtml(spec.what)}</div>
        </div>
        <div class="hiw-section">
          <div class="hiw-kicker">The real flow behind it</div>
          <div class="hiw-diagram">${nodes}</div>
        </div>
        <div class="hiw-section" style="margin-bottom:0;">
          <div class="hiw-kicker">Why it matters</div>
          <div class="hiw-body">${escapeHtml(spec.why)}</div>
        </div>
      </div>
    </div>`;
}

function wireHowItWorks() {
  const btn = document.getElementById("hiwBtn");
  const overlay = document.getElementById("hiwOverlay");
  const close = document.getElementById("hiwClose");
  if (!btn || !overlay) return;
  btn.addEventListener("click", () => overlay.classList.add("open"));
  close.addEventListener("click", () => overlay.classList.remove("open"));
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.classList.remove("open"); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") overlay.classList.remove("open"); });
}

// ------------------------------------------------------------------ citation lightbox (B23 - opens scrolled to + highlighting the passage)
function highlightSnippet(snip, query) {
  return escapeHtml(snip || "");
}
function openCitationLightbox(imgUrl, pageLabel, snip, score) {
  let lb = document.getElementById("citeLightbox");
  if (!lb) {
    lb = document.createElement("div");
    lb.id = "citeLightbox";
    lb.className = "lightbox";
    lb.innerHTML = `<button class="close" id="lbClose">&times;</button><div class="lightbox-inner"><img id="lbImg"><div class="lb-panel"><h4 id="lbTitle"></h4><div class="snip" id="lbSnip"></div></div></div>`;
    document.body.appendChild(lb);
    lb.addEventListener("click", (e) => { if (e.target === lb) lb.classList.remove("open"); });
    lb.querySelector("#lbClose").addEventListener("click", () => lb.classList.remove("open"));
  }
  lb.querySelector("#lbImg").src = imgUrl;
  lb.querySelector("#lbTitle").textContent = pageLabel;
  lb.querySelector("#lbSnip").innerHTML = `<mark>${escapeHtml(snip || "(no OCR excerpt captured for this page)")}</mark>`;
  lb.classList.add("open");
}

// ------------------------------------------------------------------ minimal bar chart (dataviz-style: one categorical series, legend, real counts)
const CHART_PALETTE = ["#2b2bb2", "#00b563", "#5777ea", "#ffd000", "#8a1f2f", "#4b4bf7", "#7a5400"];
function renderBarChart(el, rows, opts) {
  opts = opts || {};
  const max = Math.max(1, ...rows.map(r => r.value));
  el.innerHTML = rows.map((r, i) => `
    <div class="bar-row">
      <div class="lbl">${escapeHtml(r.label)}</div>
      <div class="track"><div class="fill" style="width:${(r.value / max * 100).toFixed(1)}%;background:${r.color || CHART_PALETTE[i % CHART_PALETTE.length]}"></div></div>
      <div class="val">${r.value}</div>
    </div>`).join("") || `<div class="empty">No data yet.</div>`;
}
