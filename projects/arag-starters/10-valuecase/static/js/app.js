import { api, AuthError } from "./api.js";
import { el, clear } from "./dom.js";
import { STAGES } from "./levers-data.js";
import { renderLeversView } from "./levers-view.js";
import { renderSensitivityView, renderFinancialView, renderScenariosView, renderExportView } from "./results-views.js";

const NAV_ITEMS = [
  { id: "discovery", label: "Discovery" },
  { id: "levers", label: "Levers" },
  { id: "sensitivity", label: "Sensitivity" },
  { id: "financial", label: "Financial" },
  { id: "scenarios", label: "Scenarios" },
  { id: "export", label: "Export" },
];

const state = { currentCase: null };

function parseHash() {
  const h = location.hash.replace(/^#\/?/, "");
  if (!h) return { route: "cases" };
  const m = h.match(/^case\/([^/]+)\/([a-z]+)$/);
  if (m) return { route: "case", id: m[1], tab: m[2] };
  const m2 = h.match(/^case\/([^/]+)$/);
  if (m2) return { route: "case", id: m2[1], tab: "discovery" };
  return { route: "cases" };
}

function go(hash) {
  location.hash = hash;
}

// ---------------------------------------------------------------- shell / nav

function renderRail(route) {
  const railCase = document.getElementById("railCase");
  const railNav = document.getElementById("railNav");
  clear(railNav);

  if (route.route !== "case") {
    railCase.hidden = true;
    return;
  }
  railCase.hidden = false;
  document.getElementById("railCaseAccount").textContent = state.currentCase ? state.currentCase.account_name : "Loading...";

  const stageSelect = document.getElementById("railCaseStage");
  clear(stageSelect);
  STAGES.forEach((s) => stageSelect.appendChild(el("option", { value: s.id }, [s.label])));
  if (state.currentCase) stageSelect.value = state.currentCase.stage;
  stageSelect.onchange = async () => {
    state.currentCase = await api.updateCase(route.id, { stage: stageSelect.value });
  };

  NAV_ITEMS.forEach((item) => {
    const btn = el(
      "button",
      {
        type: "button",
        class: "rail__nav-item",
        "aria-current": String(route.tab === item.id),
        onclick: () => go(`#/case/${route.id}/${item.id}`),
      },
      [item.label]
    );
    railNav.appendChild(btn);
  });
}

document.getElementById("allCasesBtn").addEventListener("click", () => go("#/"));

// ---------------------------------------------------------------- case list

async function renderCaseListView() {
  const view = document.getElementById("view");
  clear(view);
  view.appendChild(
    el("div", { class: "view-head" }, [
      el("div", {}, [
        el("h2", {}, ["Your cases"]),
        el("p", { class: "arag-caption" }, ["Every case here is persistent - reopen it next call, at renewal, or when a new stakeholder joins the deal."]),
      ]),
    ])
  );

  const formCard = el("div", { class: "card" });
  const accountInput = el("input", { type: "text", placeholder: "Account name, e.g. Riverbend Professional Association" });
  const sellerInput = el("input", { type: "text", placeholder: "Your name" });
  const form = el("form", { class: "new-case-form", onsubmit: async (e) => {
    e.preventDefault();
    if (!accountInput.value.trim() || !sellerInput.value.trim()) return;
    const { id } = await api.createCase(accountInput.value.trim(), sellerInput.value.trim());
    go(`#/case/${id}/discovery`);
  } }, [
    el("label", { class: "field" }, [el("span", { class: "field__label" }, ["Account name"]), accountInput]),
    el("label", { class: "field" }, [el("span", { class: "field__label" }, ["Your name"]), sellerInput]),
    el("button", { class: "btn btn--primary", type: "submit" }, ["New case"]),
  ]);
  formCard.appendChild(form);
  view.appendChild(formCard);

  const { cases } = await api.listCases();
  const listCard = el("div", { class: "case-list-grid" });
  if (cases.length === 0) {
    listCard.appendChild(el("div", { class: "empty-state" }, ["No cases yet - start one above."]));
  }
  cases.forEach((c) => {
    const stageLabel = (STAGES.find((s) => s.id === c.stage) || {}).label || c.stage;
    const updated = new Date(c.updated_at).toLocaleDateString("en-AU", { day: "numeric", month: "short", year: "numeric" });
    const row = el(
      "button",
      { type: "button", class: "case-row card", onclick: () => go(`#/case/${c.id}/discovery`) },
      [
        el("div", {}, [
          el("p", { class: "case-row__account" }, [c.account_name]),
          el("p", { class: "case-row__seller" }, [`Prepared by ${c.seller_name}`]),
        ]),
        el("span", { class: "stage-badge" }, [stageLabel]),
        el("span", { class: "case-row__updated" }, [`Updated ${updated}`]),
        el("button", {
          type: "button", class: "btn btn--secondary btn--small", style: "min-height:36px;",
          onclick: async (e) => {
            e.stopPropagation();
            if (confirm(`Delete the case for ${c.account_name}? This can't be undone.`)) {
              await api.deleteCase(c.id);
              renderCaseListView();
            }
          },
        }, ["Delete"]),
      ]
    );
    listCard.appendChild(row);
  });
  view.appendChild(listCard);
}

// ---------------------------------------------------------------- discovery

const DISCOVERY_FIELDS = [
  {
    key: "content_profile", label: "Content & personnel profile",
    prompt: "Is this organisation genuinely content-heavy and personnel-light? Where does more knowledge live than people can practically search?",
  },
  {
    key: "pain_use_case", label: "Pain and use-case shape",
    prompt: "What is the one, specific, nameable pain - in the buyer's own words - not \"we want to explore AI\"?",
  },
  {
    key: "budget_line", label: "Economic buyer and budget anchor",
    prompt: "Who owns the money, and which existing budget line would this sit inside?",
  },
];

async function renderDiscoveryView(caseId) {
  const view = document.getElementById("view");
  clear(view);
  view.appendChild(
    el("div", { class: "view-head" }, [
      el("div", {}, [
        el("h2", {}, ["Discovery"]),
        el("p", { class: "arag-caption" }, ["A short structured pass before any lever or number - drawn from the discovery & qualification framework's first three categories. Skip straight to Levers if discovery already happened live."]),
      ]),
    ])
  );

  const discovery = state.currentCase.discovery || {};
  const grid = el("div", { class: "discovery-grid card" });
  const inputs = {};
  DISCOVERY_FIELDS.forEach((f) => {
    const ta = el("textarea", { id: `disc-${f.key}` });
    ta.value = discovery[f.key] || "";
    inputs[f.key] = ta;
    grid.appendChild(
      el("div", { class: "discovery-category" }, [
        el("h3", {}, [f.label]),
        el("p", { class: "arag-caption" }, [f.prompt]),
        ta,
      ])
    );
  });

  const champCard = el("div", { class: "owner-row" }, [
    el("label", { class: "field" }, [
      el("span", { class: "field__label" }, ["Champion / owner name"]),
      (() => { const i = el("input", { type: "text" }); i.value = discovery.champion_name || ""; inputs.champion_name = i; return i; })(),
    ]),
    el("label", { class: "field" }, [
      el("span", { class: "field__label" }, ["Champion / owner role"]),
      (() => { const i = el("input", { type: "text" }); i.value = discovery.champion_role || ""; inputs.champion_role = i; return i; })(),
    ]),
  ]);
  grid.appendChild(champCard);
  view.appendChild(grid);

  const saveBar = el("div", { class: "export-bar" }, [
    el("button", { class: "btn btn--primary", type: "button", onclick: async () => {
      const payload = {};
      Object.entries(inputs).forEach(([k, node]) => (payload[k] = node.value));
      state.currentCase = await api.updateCase(caseId, { discovery: payload });
      go(`#/case/${caseId}/levers`);
    } }, ["Save and continue to Levers"]),
  ]);
  view.appendChild(saveBar);
}

// ---------------------------------------------------------------- router

async function loadCase(id) {
  const c = await api.getCase(id);
  state.currentCase = c;
  return c;
}

async function render() {
  const route = parseHash();

  if (route.route === "cases") {
    document.getElementById("railCase").hidden = true;
    clear(document.getElementById("railNav"));
    await renderCaseListView();
    return;
  }

  try {
    // ALWAYS re-fetch on every view mount (demo-tester finding 1, 22 Sep
    // 2026) - a prior version only re-fetched when the case id changed, so
    // switching tabs within the SAME case re-rendered from a stale
    // snapshot taken when the case was first opened, silently hiding
    // anything saved since. The extra round-trip per navigation is cheap;
    // showing a seller their own stale deal data is not.
    await loadCase(route.id);
    renderRail(route);

    if (route.tab === "discovery") await renderDiscoveryView(route.id);
    else if (route.tab === "levers") await renderLeversView(route.id, state);
    else if (route.tab === "sensitivity") await renderSensitivityView(route.id, state);
    else if (route.tab === "financial") await renderFinancialView(route.id, state);
    else if (route.tab === "scenarios") await renderScenariosView(route.id, state);
    else if (route.tab === "export") await renderExportView(route.id, state);
    else go(`#/case/${route.id}/discovery`);
  } catch (e) {
    if (e instanceof AuthError) {
      showLoginGate();
      return;
    }
    const view = document.getElementById("view");
    clear(view);
    view.appendChild(el("div", { class: "empty-state" }, [`Something went wrong: ${e.message}`]));
  }
}

window.addEventListener("hashchange", render);

// ---------------------------------------------------------------- login gate

function showLoginGate() {
  document.getElementById("loginGate").hidden = false;
  document.getElementById("appShell").hidden = true;
  document.getElementById("appFooter").hidden = true;
}

function showApp() {
  document.getElementById("loginGate").hidden = true;
  document.getElementById("appShell").hidden = false;
  document.getElementById("appFooter").hidden = false;
  render();
}

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const passphrase = document.getElementById("passphraseInput").value;
  const errorEl = document.getElementById("loginError");
  errorEl.hidden = true;
  try {
    await api.login(passphrase);
    showApp();
  } catch (err) {
    errorEl.hidden = false;
  }
});

// ---------------------------------------------------------------- init

(async function init() {
  try {
    const { authenticated } = await api.session();
    if (authenticated) showApp();
    else showLoginGate();
  } catch (e) {
    showLoginGate();
  }
})();
