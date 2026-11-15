import { api } from "./api.js";
import { el, clear } from "./dom.js";
import { fmtUSD, fmtPct } from "./levers-data.js";
import { tornadoChart, cashflowChart } from "./charts.js";

function noLeversMessage() {
  return el("div", { class: "empty-state" }, ["Select at least one lever with complete inputs on the Levers step first."]);
}

// ---------------------------------------------------------------- sensitivity

export async function renderSensitivityView(caseId, appState) {
  const view = document.getElementById("view");
  clear(view);
  view.appendChild(
    el("div", { class: "view-head" }, [
      el("div", {}, [
        el("h2", {}, ["Sensitivity"]),
        el("p", { class: "arag-caption" }, ["Which inputs actually swing the outcome, ranked by a +/-20% change on the expected case. Spend discovery time getting these right; the rest matter less."]),
      ]),
    ])
  );

  const result = await api.compute(caseId);
  if (result.sensitivity.length === 0) {
    view.appendChild(noLeversMessage());
    return;
  }

  const expected = result.scenarios.expected;
  expected.credibility_flags.forEach((flag) => {
    view.appendChild(el("div", { class: "credibility-flag" }, [flag]));
  });

  const top = result.sensitivity.slice(0, 8);
  const chartCard = el("div", { class: "card" }, [
    el("h3", {}, ["Swing in monthly/one-time value from a +/-20% change"]),
    (() => {
      const c = el("div", { class: "chart" });
      c.innerHTML = tornadoChart(top);
      return c;
    })(),
  ]);
  view.appendChild(chartCard);

  const tableCard = el("div", { class: "card" });
  tableCard.appendChild(el("h3", {}, ["Detail"]));
  const table = el("table", { class: "scenario-table" });
  table.appendChild(
    el("tr", {}, [
      el("th", {}, ["Lever"]), el("th", {}, ["Input"]), el("th", {}, ["Base"]), el("th", {}, ["Low (-20%)"]), el("th", {}, ["High (+20%)"]),
    ])
  );
  top.forEach((row) => {
    table.appendChild(
      el("tr", {}, [
        el("td", {}, [row.lever_title]),
        el("td", {}, [row.input_label]),
        el("td", { class: "figure" }, [fmtUSD(row.base)]),
        el("td", {}, [fmtUSD(row.low)]),
        el("td", {}, [fmtUSD(row.high)]),
      ])
    );
  });
  tableCard.appendChild(el("div", { class: "table-scroll" }, [table]));
  view.appendChild(tableCard);
}

// ---------------------------------------------------------------- financial

export async function renderFinancialView(caseId, appState) {
  const view = document.getElementById("view");
  clear(view);
  const c = appState.currentCase;

  view.appendChild(
    el("div", { class: "view-head" }, [
      el("div", {}, [
        el("h2", {}, ["Financial view"]),
        el("p", { class: "arag-caption" }, ["Real time-phased NPV, IRR and payback on the expected case - monthly discounting, standard finance convention. This maths is general methodology, not a Progress Agentic RAG product claim."]),
      ]),
    ])
  );

  const settingsCard = el("div", { class: "card" });
  const discountInput = el("input", { type: "text", inputmode: "decimal", placeholder: "e.g. 10" });
  if (c.discount_rate !== null && c.discount_rate !== undefined) discountInput.value = (c.discount_rate * 100).toString();
  const horizonInput = el("input", { type: "text", inputmode: "numeric" });
  horizonInput.value = c.horizon_months || 24;
  const tierSelect = el("select", { class: "field-select" }, [
    el("option", { value: "starter" }, ["Starter - US$700/mo"]),
    el("option", { value: "pro" }, ["Pro - US$1,925/mo"]),
    el("option", { value: "custom" }, ["Custom"]),
  ]);
  tierSelect.value = c.pricing_tier || "starter";
  const customCostInput = el("input", { type: "text", inputmode: "decimal", placeholder: "US$/month" });
  if (c.custom_monthly_cost) customCostInput.value = c.custom_monthly_cost;
  customCostInput.hidden = tierSelect.value !== "custom";
  const oneTimeCostInput = el("input", { type: "text", inputmode: "decimal", placeholder: "optional - implementation/migration cost, if any" });
  if (c.one_time_cost) oneTimeCostInput.value = c.one_time_cost;

  async function saveSettings() {
    const discount = discountInput.value === "" ? null : parseFloat(discountInput.value) / 100;
    const horizon = horizonInput.value === "" ? 24 : parseInt(horizonInput.value, 10);
    const customCost = customCostInput.value === "" ? null : parseFloat(customCostInput.value);
    const oneTimeCost = oneTimeCostInput.value === "" ? null : parseFloat(oneTimeCostInput.value);
    appState.currentCase = await api.updateCase(caseId, {
      discount_rate: discount, horizon_months: horizon, pricing_tier: tierSelect.value,
      custom_monthly_cost: customCost, one_time_cost: oneTimeCost,
    });
    renderFinancialView(caseId, appState);
  }
  [discountInput, horizonInput, customCostInput, oneTimeCostInput].forEach((f) => f.addEventListener("blur", saveSettings));
  tierSelect.addEventListener("change", () => { customCostInput.hidden = tierSelect.value !== "custom"; saveSettings(); });

  settingsCard.appendChild(
    el("div", { class: "owner-row" }, [
      el("label", { class: "field" }, [el("span", { class: "field__label" }, ["Discount rate, annual (buyer's WACC or hurdle rate - never assumed)"]), discountInput]),
      el("label", { class: "field" }, [el("span", { class: "field__label" }, ["Horizon (months)"]), horizonInput]),
      el("label", { class: "field" }, [el("span", { class: "field__label" }, ["Pricing tier (cost side)"]), tierSelect]),
      el("label", { class: "field" }, [el("span", { class: "field__label" }, ["Custom monthly cost"]), customCostInput]),
      el("label", { class: "field" }, [el("span", { class: "field__label" }, ["One-time cost (optional, real upfront cost only)"]), oneTimeCostInput]),
    ])
  );
  view.appendChild(settingsCard);

  if ((c.selected_levers || []).length === 0) {
    view.appendChild(noLeversMessage());
    return;
  }
  const result = await api.compute(caseId);
  const expected = result.scenarios.expected;

  expected.credibility_flags.forEach((flag) => view.appendChild(el("div", { class: "credibility-flag" }, [flag])));

  const metrics = el("div", { class: "metric-row" }, [
    el("div", { class: "card metric-tile" }, [
      el("p", { class: "metric-tile__label" }, ["NPV"]),
      el("p", { class: "metric-tile__value" }, [c.discount_rate ? fmtUSD(expected.npv) : "-"]),
      el("p", { class: "metric-tile__note" }, [c.discount_rate ? `Over ${c.horizon_months || 24} months` : "Enter a discount rate above"]),
    ]),
    el("div", { class: "card metric-tile" }, [
      el("p", { class: "metric-tile__label" }, ["IRR (annualised)"]),
      el("p", { class: "metric-tile__value" }, [expected.irr_annual !== null ? fmtPct(expected.irr_annual) : "n/a"]),
      el("p", { class: "metric-tile__note" }, [expected.irr_annual !== null ? "" : expected.irr_undefined_reason || ""]),
    ]),
    el("div", { class: "card metric-tile" }, [
      el("p", { class: "metric-tile__label" }, ["Payback"]),
      el("p", { class: "metric-tile__value" }, [expected.payback_months !== null ? `${expected.payback_months.toFixed(1)} mo` : "beyond horizon"]),
    ]),
  ]);
  view.appendChild(metrics);

  const chartCard = el("div", { class: "card" }, [
    el("h3", {}, ["Cumulative cash flow"]),
    (() => { const c2 = el("div", { class: "chart" }); c2.innerHTML = cashflowChart(expected.cashflows, expected.payback_months); return c2; })(),
  ]);
  view.appendChild(chartCard);
}

// ---------------------------------------------------------------- scenarios

export async function renderScenariosView(caseId, appState) {
  const view = document.getElementById("view");
  clear(view);
  view.appendChild(
    el("div", { class: "view-head" }, [
      el("div", {}, [
        el("h2", {}, ["Scenario comparison"]),
        el("p", { class: "arag-caption" }, ["Conservative, expected and aggressive, side by side - have the \"what if adoption is half\" answer ready before the room asks it."]),
      ]),
    ])
  );

  const result = await api.compute(caseId);
  const table = el("table", { class: "scenario-table" });
  table.appendChild(
    el("tr", {}, [
      el("th", {}, ["Scenario"]), el("th", {}, ["Recurring/mo"]), el("th", {}, ["One-time"]), el("th", {}, ["NPV"]), el("th", {}, ["IRR"]), el("th", {}, ["Payback"]),
    ])
  );
  ["conservative", "expected", "aggressive"].forEach((scenario) => {
    const s = result.scenarios[scenario];
    table.appendChild(
      el("tr", {}, [
        el("td", {}, [scenario.charAt(0).toUpperCase() + scenario.slice(1)]),
        el("td", { class: "figure" }, [fmtUSD(s.recurring_monthly)]),
        el("td", { class: "figure" }, [fmtUSD(s.one_time)]),
        el("td", {}, [s.npv !== null ? fmtUSD(s.npv) : "-"]),
        el("td", {}, [s.irr_annual !== null ? fmtPct(s.irr_annual) : "n/a"]),
        el("td", {}, [s.payback_months !== null ? `${s.payback_months.toFixed(1)} mo` : "-"]),
      ])
    );
  });
  view.appendChild(el("div", { class: "card" }, [el("div", { class: "table-scroll" }, [table])]));
}

// ---------------------------------------------------------------- export

export async function renderExportView(caseId, appState) {
  const view = document.getElementById("view");
  clear(view);
  view.appendChild(
    el("div", { class: "view-head" }, [
      el("div", {}, [
        el("h2", {}, ["Export"]),
        el("p", { class: "arag-caption" }, ["A stakeholder-ready, editable document your champion can adapt and carry into their own board deck - branded, with every input's provenance and owner."]),
      ]),
    ])
  );

  const grid = el("div", { class: "export-grid" });
  grid.appendChild(
    el("div", { class: "card export-tile" }, [
      el("h3", {}, ["Word business case"]),
      el("p", { class: "arag-caption" }, ["Full detail: every lever, input, provenance, owner, scenario comparison and financial view."]),
      el("a", { class: "btn btn--primary", href: api.exportUrl(caseId, "docx"), target: "_blank", rel: "noopener" }, ["Download .docx"]),
    ])
  );
  grid.appendChild(
    el("div", { class: "card export-tile" }, [
      el("h3", {}, ["PowerPoint deck"]),
      el("p", { class: "arag-caption" }, ["A five-slide summary ready to drop into a board deck."]),
      el("a", { class: "btn btn--primary", href: api.exportUrl(caseId, "pptx"), target: "_blank", rel: "noopener" }, ["Download .pptx"]),
    ])
  );
  view.appendChild(grid);
}
