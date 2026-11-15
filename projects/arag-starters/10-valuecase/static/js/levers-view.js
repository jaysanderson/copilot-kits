// The lever workspace - scenario columns (conservative/expected/aggressive),
// per-input provenance, measure-in-POV, a labelled benchmark offer, and a
// per-lever owner. This is where MUSTs #2, #4, #5 and #8 live.
//
// Save discipline (rewritten 22 Sep 2026 after demo-tester found silent
// data loss - see the fix notes on persist() below): every save sends ONLY
// the field the user just changed, and every save's response (the fresh,
// full case from the server) replaces appState.currentCase - never a
// hand-patched local guess. Combined with app.js re-fetching the case on
// every view mount, this closes the "stale in-memory case" failure.
import { api } from "./api.js";
import { el, clear } from "./dom.js";
import { LEVERS, fmtUSD } from "./levers-data.js";

const SCENARIOS = ["conservative", "expected", "aggressive"];
const SCENARIO_LABELS = { conservative: "Conservative", expected: "Expected", aggressive: "Aggressive" };
const SANE_MAX = 1e9; // advisory-only threshold for a non-percent field - never silently altered, just flagged

// Labelled, opt-in benchmark ranges - the model doc's OWN illustrative
// worked example (section 5), not a market study. Never auto-filled;
// offered only on request, per SHOULD #11 and the honesty discipline.
const BENCHMARKS = {
  "time-to-answer.minutesSaved": { value: 5, note: "5 minutes saved per lookup - the value model doc's own illustrative worked example, not a market benchmark study." },
  "deflected-effort.deflectedFraction": { value: 40, note: "40% deflected - the value model doc's own illustrative worked example, not a market benchmark study." },
};

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

function buildInputBlock(caseId, lever, input, caseData, appState, onChange) {
  const key = `${lever.id}.${input.key}`;
  const valuesRow = (caseData.values || []).filter((v) => v.lever_id === lever.id && v.input_key === input.key);
  const metaRow = (caseData.meta || []).find((m) => m.lever_id === lever.id && m.input_key === input.key) || {};
  const cellValue = {};
  valuesRow.forEach((v) => (cellValue[v.scenario] = v.value));

  // localState mirrors what THIS render session has shown/typed - it is
  // never trusted as the source of truth for a save; every persist() call
  // below sends only the exact field that changed, so a stale localState
  // elsewhere in this object can never overwrite a value it doesn't name.
  const localState = {
    values: { ...cellValue },
    measure_in_pov: !!metaRow.measure_in_pov,
    provided_by_name: metaRow.provided_by_name || "",
    provided_by_role: metaRow.provided_by_role || "",
    provided_at: metaRow.provided_at || todayISO(),
    source_type: metaRow.source_type || "buyer-stated",
  };

  const block = el("div", { class: "scenario-input-row" });

  // persist(partial): partial carries ONLY the key(s) this specific user
  // action just changed (e.g. {expected: 400}, or {provided_by_name: "..."}).
  // Never the whole row. The server's response is the fresh, authoritative
  // case - it replaces appState.currentCase outright.
  async function persist(partial) {
    const updated = await api.putInput(caseId, lever.id, input.key, partial);
    appState.currentCase = updated;
    onChange();
  }

  const labelRow = el("p", { class: "scenario-input-row__label" }, [input.label, ` (${input.unit})`]);
  block.appendChild(labelRow);

  const cols = el("div", { class: "scenario-cols" });
  const scenarioInputs = {};
  SCENARIOS.forEach((scenario) => {
    const warningEl = el("p", { class: "field-warning", hidden: true });

    const field = el("input", {
      type: "text", inputmode: "decimal", autocomplete: "off",
      placeholder: "-",
      oninput: (e) => {
        // Live-preview only - never persists mid-keystroke.
        const raw = e.target.value;
        localState.values[scenario] = raw === "" ? null : parseFloat(raw);
        onChange({ preview: true });
      },
      onblur: async (e) => {
        const raw = e.target.value;
        let parsed = raw === "" ? null : parseFloat(raw);
        let clamp = null; // "negative" | "percent" | null

        if (raw !== "" && (typeof parsed !== "number" || isNaN(parsed))) {
          parsed = null; // unparseable leftover text (a lone "-", etc.) clears rather than showing NaN
        } else if (typeof parsed === "number" && !isNaN(parsed)) {
          if (parsed < 0) {
            parsed = 0;
            clamp = "negative";
          } else if (input.isPercent && parsed > 100) {
            parsed = 100;
            clamp = "percent";
          }
        }

        e.target.value = parsed === null ? "" : parsed;
        localState.values[scenario] = parsed;

        // Restored plausibility guardrails (demo-tester finding 4, 22 Sep
        // 2026 - the old build had these; the rebuild dropped them).
        // Prefer an honest, visible note over a silent clamp - and a
        // clamped/flagged value is corrected BEFORE it is sent, so no
        // computation downstream ever presents a dollar figure built on
        // an impossible input unflagged.
        if (clamp === "negative") {
          warningEl.hidden = false;
          warningEl.textContent = "A negative number isn't meaningful here, so this has been set to 0.";
        } else if (clamp === "percent") {
          warningEl.hidden = false;
          warningEl.textContent = "A fraction can't exceed 100%, so this has been capped at 100%.";
        } else if (!input.isPercent && parsed !== null && parsed > SANE_MAX) {
          warningEl.hidden = false;
          warningEl.textContent = "This number looks unusually large - check it before using this figure. It is still used exactly as entered.";
        } else {
          warningEl.hidden = true;
          warningEl.textContent = "";
        }

        await persist({ [scenario]: parsed });
      },
    });
    if (cellValue[scenario] !== undefined && cellValue[scenario] !== null) field.value = cellValue[scenario];
    if (localState.measure_in_pov) field.disabled = true;
    scenarioInputs[scenario] = field;
    cols.appendChild(
      el("div", { class: `scenario-col scenario-col--${scenario}` }, [
        el("p", { class: "scenario-col__label" }, [SCENARIO_LABELS[scenario]]),
        field,
        warningEl,
      ])
    );
  });
  block.appendChild(cols);

  // Measure-in-POV toggle (only where the model doc allows it).
  if (input.povEligible) {
    const povCheckbox = el("input", {
      type: "checkbox",
      onchange: async (e) => {
        const checked = e.target.checked;
        localState.measure_in_pov = checked;
        Object.values(scenarioInputs).forEach((f) => (f.disabled = checked));
        if (checked) {
          localState.source_type = "measured-in-pov";
          sourceTypeSelect.value = "measured-in-pov";
          await persist({ measure_in_pov: true, source_type: "measured-in-pov" });
        } else {
          await persist({ measure_in_pov: false });
        }
      },
    });
    povCheckbox.checked = localState.measure_in_pov;
    block.appendChild(
      el("label", { class: "pov-toggle" }, [povCheckbox, "Measure in POV (removes this input from every scenario until it's measured)"])
    );
  }

  // Labelled, opt-in benchmark.
  const benchmark = BENCHMARKS[key];
  if (benchmark && !localState.measure_in_pov) {
    const benchmarkNote = el("p", { class: "arag-caption", hidden: true }, [benchmark.note]);
    const btn = el("button", {
      type: "button", class: "benchmark-toggle",
      onclick: async () => {
        scenarioInputs.expected.value = benchmark.value;
        localState.values.expected = benchmark.value;
        localState.source_type = "benchmark";
        sourceTypeSelect.value = "benchmark";
        benchmarkNote.hidden = false;
        await persist({ expected: benchmark.value, source_type: "benchmark" });
      },
    }, ["I can't estimate this - show me a labelled benchmark"]);
    block.appendChild(btn);
    block.appendChild(benchmarkNote);
  }

  // Provenance strip - who gave this number, in what role, on what date.
  // Each field saves only its own key - never the other three.
  const nameField = el("input", {
    type: "text", placeholder: "Provided by (name)",
    onblur: async (e) => { await persist({ provided_by_name: e.target.value || null }); },
  });
  nameField.value = localState.provided_by_name;
  const roleField = el("input", {
    type: "text", placeholder: "Their role",
    onblur: async (e) => { await persist({ provided_by_role: e.target.value || null }); },
  });
  roleField.value = localState.provided_by_role;
  const dateField = el("input", {
    type: "date",
    onchange: async (e) => { localState.provided_at = e.target.value; await persist({ provided_at: e.target.value || null }); },
  });
  dateField.value = localState.provided_at;
  const sourceTypeSelect = el("select", {
    class: "field-select",
    onchange: async (e) => { localState.source_type = e.target.value; await persist({ source_type: e.target.value }); },
  }, [
    el("option", { value: "buyer-stated" }, ["Buyer-stated"]),
    el("option", { value: "measured-in-pov" }, ["Measured in POV"]),
    el("option", { value: "benchmark" }, ["Benchmark (labelled)"]),
  ]);
  sourceTypeSelect.value = localState.source_type;
  nameField.addEventListener("input", (e) => (localState.provided_by_name = e.target.value));
  roleField.addEventListener("input", (e) => (localState.provided_by_role = e.target.value));

  block.appendChild(
    el("div", { class: "provenance-row" }, [nameField, roleField, dateField, sourceTypeSelect])
  );

  return { block, localState, scenarioInputs };
}

export async function renderLeversView(caseId, appState) {
  const view = document.getElementById("view");
  clear(view);

  const caseData = appState.currentCase;
  const selected = new Set(caseData.selected_levers || []);

  view.appendChild(
    el("div", { class: "view-head" }, [
      el("div", {}, [
        el("h2", {}, ["Value levers"]),
        el("p", { class: "arag-caption" }, ["Select the lever(s) that match this deal. Fill the buyer's own number for conservative, expected and aggressive - one well-measured lever beats a hand-wavy pass across all five."]),
      ]),
    ])
  );

  const grid = el("div", { class: "lever-grid" });
  LEVERS.forEach((lever) => {
    const isSelected = selected.has(lever.id);
    grid.appendChild(
      el("button", {
        type: "button", class: "lever-card", "aria-pressed": String(isSelected),
        onclick: async () => {
          if (selected.has(lever.id)) selected.delete(lever.id);
          else selected.add(lever.id);
          appState.currentCase = await api.updateCase(caseId, { selected_levers: Array.from(selected) });
          renderLeversView(caseId, appState);
        },
      }, [
        el("span", { class: "lever-card__number" }, [lever.number]),
        el("p", { class: "lever-card__title" }, [lever.title]),
        el("p", { class: "lever-card__subtitle" }, [lever.subtitle]),
        el("p", { class: "lever-card__desc" }, [lever.description]),
        el("span", { class: "lever-card__state" }, [isSelected ? "✓ Selected" : "Select this lever"]),
      ])
    );
  });
  view.appendChild(grid);

  if (selected.size === 0) {
    view.appendChild(el("div", { class: "empty-state" }, ["Select at least one lever above to enter numbers."]));
    return;
  }

  const resultsSummary = el("div", { class: "card lever-results-summary" });
  view.appendChild(resultsSummary);

  const blocks = [];
  LEVERS.filter((l) => selected.has(l.id)).forEach((lever) => {
    const card = el("div", { class: "card lever-input-block" });
    card.appendChild(
      el("div", { class: "lever-input-block__head" }, [
        el("span", { class: "lever-card__number" }, [lever.number]),
        el("h3", {}, [lever.title]),
      ])
    );

    const ownerRow = (caseData.owners || []).find((o) => o.lever_id === lever.id) || {};
    const ownerName = el("input", {
      type: "text",
      onblur: async (e) => { appState.currentCase = await api.putOwner(caseId, lever.id, { owner_name: e.target.value, owner_role: ownerRole.value }); },
    });
    ownerName.value = ownerRow.owner_name || "";
    const ownerRole = el("input", {
      type: "text",
      onblur: async (e) => { appState.currentCase = await api.putOwner(caseId, lever.id, { owner_name: ownerName.value, owner_role: e.target.value }); },
    });
    ownerRole.value = ownerRow.owner_role || "";
    card.appendChild(
      el("div", { class: "owner-row" }, [
        el("label", { class: "field" }, [el("span", { class: "field__label" }, ["Assumption owner (buyer-side, accountable for these numbers)"]), ownerName]),
        el("label", { class: "field" }, [el("span", { class: "field__label" }, ["Their role"]), ownerRole]),
      ])
    );

    lever.inputs.forEach((input) => {
      const built = buildInputBlock(caseId, lever, input, caseData, appState, () => updateResults());
      blocks.push({ lever, input, ...built });
      card.appendChild(built.block);
    });

    view.appendChild(card);
  });

  function updateResults() {
    clear(resultsSummary);
    resultsSummary.appendChild(el("h3", {}, ["Expected-case value (live preview)"]));
    let recurring = 0, oneTime = 0;
    const pending = [];
    LEVERS.filter((l) => selected.has(l.id)).forEach((lever) => {
      const leverBlocks = blocks.filter((b) => b.lever.id === lever.id);
      if (leverBlocks.some((b) => b.localState.measure_in_pov)) {
        pending.push(lever.title);
        return;
      }
      const values = {};
      let complete = true;
      leverBlocks.forEach((b) => {
        const v = b.localState.values.expected;
        if (v === undefined || v === null || v === "" || isNaN(v)) complete = false;
        values[b.input.key] = v;
      });
      if (!complete) return;
      const result = lever.compute(values);
      if (!isFinite(result.amount)) return;
      if (result.period === "one-time") oneTime += result.amount;
      else recurring += result.amount;
    });
    resultsSummary.appendChild(
      el("p", {}, [
        el("span", { class: "lever-result-card__value" }, [fmtUSD(recurring)]),
        el("span", { class: "lever-result-card__period" }, [" / month recurring"]),
      ])
    );
    resultsSummary.appendChild(el("p", {}, [`One-time: ${fmtUSD(oneTime)}`]));
    if (pending.length) {
      resultsSummary.appendChild(el("p", { class: "arag-caption" }, [`Measured in POV, not estimated here: ${pending.join(", ")}.`]));
    }
    resultsSummary.appendChild(el("p", { class: "arag-caption" }, ["This preview uses the expected column only - see Scenarios for conservative/aggressive and Financial for NPV/IRR/Payback."]));
  }

  updateResults();
}
