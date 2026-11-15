"""The five ARAG value levers - Python port of static/js/levers.js, kept in
lockstep with content/enablement/roi-value-model.md v2.0 (5 Sep 2026).

This is the server-side twin used for financial modelling (NPV/IRR/Payback,
sensitivity, exports), where the arithmetic must run without a browser.
The client-side copy still does live, per-keystroke entry; both must
compute an identical figure for the same inputs - do not let the two drift.
"""

MONTH_PER_WEEK = 52 / 12  # matches the model doc's own worked-example rounding

LEVERS = [
    {
        "id": "time-to-answer",
        "number": "01",
        "title": "Time-to-answer",
        "subtitle": "Internal knowledge work",
        "period": "recurring",
        "inputs": [
            {"key": "people", "label": "People doing knowledge lookups regularly", "unit": "people"},
            {"key": "lookupsPerWeek", "label": "Lookups per person per week", "unit": "per week"},
            {
                "key": "minutesSaved",
                "label": "Minutes saved per lookup, once a cited answer replaces a manual search",
                "unit": "minutes",
                "povEligible": True,
            },
            {"key": "hourlyCost", "label": "Loaded hourly cost per person", "unit": "US$/hr"},
        ],
        "formula_text": "people x lookups/week x minutes saved / 60 x hourly cost = value per week",
    },
    {
        "id": "deflected-effort",
        "number": "02",
        "title": "Deflected effort",
        "subtitle": "Customer- or member-facing self-serve",
        "period": "recurring",
        "inputs": [
            {"key": "contactsPerMonth", "label": "Monthly contacts of the types this assistant could genuinely answer", "unit": "contacts/mo"},
            {"key": "deflectedFraction", "label": "Fraction realistically deflected", "unit": "%", "povEligible": True, "isPercent": True},
            {"key": "costPerContact", "label": "Fully loaded cost per contact (call, email or ticket)", "unit": "US$"},
        ],
        "formula_text": "contacts/month x deflected fraction x cost per contact = value per month",
    },
    {
        "id": "faster-path-to-production",
        "number": "03",
        "title": "Faster path to production",
        "subtitle": "Time value of starting now, versus a DIY build (one-time)",
        "period": "one-time",
        "inputs": [
            {"key": "diyMonths", "label": "Estimated months to a working, grounded, quality-measured DIY pipeline", "unit": "months"},
            {"key": "engMonthlyCost", "label": "Fully loaded monthly cost of the engineering team that would build it", "unit": "US$/mo"},
        ],
        "formula_text": "estimated DIY months x loaded monthly engineering cost = one-time time value",
    },
    {
        "id": "avoided-build-cost",
        "number": "04",
        "title": "Avoided DIY-build cost",
        "subtitle": "The ongoing engineering opportunity cost",
        "period": "recurring",
        "inputs": [
            {"key": "engineers", "label": "Engineers who would otherwise build and maintain retrieval infrastructure", "unit": "engineers"},
            {"key": "timeFraction", "label": "Fraction of their time this would consume, ongoing", "unit": "%", "isPercent": True},
            {"key": "loadedCostPerEngineer", "label": "Fully loaded cost per engineer", "unit": "US$/mo"},
        ],
        "formula_text": "engineers x time fraction x loaded cost = ongoing avoided cost per month",
    },
    {
        "id": "product-economics",
        "number": "05",
        "title": "Product economics",
        "subtitle": "ISV embed - incremental revenue",
        "period": "recurring",
        "inputs": [
            {"key": "endCustomers", "label": "End customers the feature would reach", "unit": "customers"},
            {"key": "upliftPerCustomer", "label": "Monthly price uplift (or retention effect), per end customer", "unit": "US$/mo"},
            {"key": "adoptionRate", "label": "Expected adoption rate among those end customers", "unit": "%", "isPercent": True},
        ],
        "formula_text": "end customers x uplift x adoption = incremental revenue per month",
    },
]

LEVERS_BY_ID = {l["id"]: l for l in LEVERS}

PRICING = {"starter": 700.0, "pro": 1925.0}


def input_is_percent(lever_id: str, input_key: str) -> bool:
    lever = LEVERS_BY_ID.get(lever_id)
    if not lever:
        return False
    inp = next((i for i in lever["inputs"] if i["key"] == input_key), None)
    return bool(inp and inp.get("isPercent"))


def clamp_input_value(lever_id: str, input_key: str, value):
    """Server-side twin of the client's blur-time clamp (levers-view.js) -
    added 22 Sep 2026 after roi-case-tester proved a raw API PUT bypasses
    the UI entirely (a 150% fraction, or a negative count, was accepted and
    stored verbatim). Every write path funnels through here so the database
    can never hold a value the UI itself would refuse, regardless of how
    the write arrived. Same semantics as the client: negative -> 0 always;
    a percent field additionally caps at 100. None passes through
    unchanged (a genuinely empty/cleared field, not a value to clamp)."""
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return value
    if v < 0:
        v = 0.0
    if input_is_percent(lever_id, input_key) and v > 100:
        v = 100.0
    return v


def compute_lever(lever_id: str, values: dict):
    """values: {input_key: float}. Returns (period, amount) or (None, None)
    if any required input is missing/non-numeric. Never guesses a missing
    value - an incomplete lever contributes nothing to any total."""
    lever = LEVERS_BY_ID[lever_id]
    for inp in lever["inputs"]:
        v = values.get(inp["key"])
        if v is None:
            return None, None
        try:
            float(v)
        except (TypeError, ValueError):
            return None, None

    if lever_id == "time-to-answer":
        weekly = values["people"] * values["lookupsPerWeek"] * (values["minutesSaved"] / 60) * values["hourlyCost"]
        return "recurring", weekly * MONTH_PER_WEEK
    if lever_id == "deflected-effort":
        return "recurring", values["contactsPerMonth"] * (values["deflectedFraction"] / 100) * values["costPerContact"]
    if lever_id == "faster-path-to-production":
        return "one-time", values["diyMonths"] * values["engMonthlyCost"]
    if lever_id == "avoided-build-cost":
        return "recurring", values["engineers"] * (values["timeFraction"] / 100) * values["loadedCostPerEngineer"]
    if lever_id == "product-economics":
        return "recurring", values["endCustomers"] * values["upliftPerCustomer"] * (values["adoptionRate"] / 100)
    raise ValueError(f"unknown lever {lever_id}")


def case_scenario_totals(selected_lever_ids, values_by_lever_input, pov_by_lever_input, scenario):
    """values_by_lever_input: {(lever_id, input_key): {scenario: value}}
    pov_by_lever_input: {(lever_id, input_key): bool}
    Returns (recurring_monthly_total, one_time_total, incomplete_lever_ids, pov_lever_ids)."""
    recurring_total = 0.0
    one_time_total = 0.0
    incomplete = []
    pov_levers = []
    for lever_id in selected_lever_ids:
        lever = LEVERS_BY_ID.get(lever_id)
        if not lever:
            continue
        any_pov = any(pov_by_lever_input.get((lever_id, inp["key"])) for inp in lever["inputs"])
        if any_pov:
            pov_levers.append(lever_id)
            continue
        values = {}
        ok = True
        for inp in lever["inputs"]:
            cell = values_by_lever_input.get((lever_id, inp["key"]), {})
            v = cell.get(scenario)
            if v is None:
                ok = False
                break
            values[inp["key"]] = v
        if not ok:
            incomplete.append(lever_id)
            continue
        period, amount = compute_lever(lever_id, values)
        if period is None:
            incomplete.append(lever_id)
            continue
        if period == "one-time":
            one_time_total += amount
        else:
            recurring_total += amount
    return recurring_total, one_time_total, incomplete, pov_levers
