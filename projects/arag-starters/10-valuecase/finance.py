"""Time-phased financial modelling - NPV, IRR, Payback, sensitivity and the
Shark-Finesse-style credibility check.

This is the one piece of new maths in this rebuild that is NOT grounded in
content/enablement/roi-value-model.md - it is general corporate-finance
convention (monthly discounting, standard NPV/IRR/payback definitions), not
an ARAG product claim, so the KB-verification gate (hard rule 3) does not
apply to it. It is instead verified against a textbook worked example in
tests_finance_selftest.py - run that before trusting this module.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from levers import LEVERS_BY_ID, compute_lever


def annual_to_monthly_rate(annual_rate: float) -> float:
    return (1 + annual_rate) ** (1 / 12) - 1


def build_cashflows(one_time_benefit: float, monthly_net_benefit: float, monthly_cost: float,
                     one_time_cost: float, horizon_months: int) -> List[float]:
    """Month 0 carries any one-time benefit (Lever 3) minus any real,
    buyer-supplied one-time cost. Months 1..horizon carry the recurring
    monthly value minus the subscription cost, every month."""
    flows = [0.0] * (horizon_months + 1)
    flows[0] = one_time_benefit - one_time_cost
    for m in range(1, horizon_months + 1):
        flows[m] = monthly_net_benefit - monthly_cost
    return flows


def npv(flows: List[float], monthly_rate: float) -> float:
    return sum(cf / ((1 + monthly_rate) ** t) for t, cf in enumerate(flows))


def irr_monthly(flows: List[float], lo: float = -0.99, hi: float = 10.0, tol: float = 1e-9,
                 max_iter: int = 200) -> Optional[float]:
    """Bisection on the monthly rate that zeroes NPV. Returns None when the
    cash-flow series never changes sign within [lo, hi] - i.e. every flow is
    the same sign, so no discount rate solves it (a genuinely undefined IRR,
    not a bug). This is expected and common here: a low-cost SaaS case with
    no negative outflow anywhere has no true IRR, exactly Shark Finesse's
    own documented "drop the misleading metric" case."""
    f_lo, f_hi = npv(flows, lo), npv(flows, hi)
    if f_lo == 0:
        return lo
    if f_hi == 0:
        return hi
    if (f_lo > 0) == (f_hi > 0):
        return None
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        f_mid = npv(flows, mid)
        if abs(f_mid) < tol:
            return mid
        if (f_lo > 0) == (f_mid > 0):
            lo, f_lo = mid, f_mid
        else:
            hi, f_hi = mid, f_mid
    return (lo + hi) / 2


def monthly_to_annual_rate(monthly_rate: float) -> float:
    return (1 + monthly_rate) ** 12 - 1


def payback_months(flows: List[float]) -> Optional[float]:
    """Simple (undiscounted) payback - the month the cumulative cash flow
    first reaches zero, interpolated to a fractional month. None if the
    case never pays back within the modelled horizon."""
    cumulative = 0.0
    for t, cf in enumerate(flows):
        prev = cumulative
        cumulative += cf
        if cumulative >= 0:
            if t == 0:
                return 0.0
            if cf == 0:
                return float(t)
            frac = -prev / cf
            return (t - 1) + frac
    return None


@dataclass
class FinancialResult:
    recurring_monthly_benefit: float
    one_time_benefit: float
    monthly_cost: float
    one_time_cost: float
    discount_rate_annual: Optional[float]
    horizon_months: int
    cashflows: List[float]
    npv: Optional[float]
    irr_annual: Optional[float]
    irr_undefined_reason: Optional[str]
    payback_months: Optional[float]
    credibility_flags: List[str] = field(default_factory=list)


def evaluate_case(recurring_monthly_benefit: float, one_time_benefit: float, monthly_cost: float,
                   one_time_cost: float, discount_rate_annual: Optional[float],
                   horizon_months: int) -> FinancialResult:
    flows = build_cashflows(one_time_benefit, recurring_monthly_benefit, monthly_cost, one_time_cost, horizon_months)
    monthly_rate = annual_to_monthly_rate(discount_rate_annual) if discount_rate_annual else 0.0
    npv_value = npv(flows, monthly_rate) if discount_rate_annual is not None else None

    irr_m = irr_monthly(flows)
    irr_annual = monthly_to_annual_rate(irr_m) if irr_m is not None else None
    irr_reason = None
    if irr_m is None:
        if all(f >= 0 for f in flows):
            irr_reason = (
                "Every modelled cash flow is positive - there is no upfront outflow for a return to be "
                "measured against, so IRR is mathematically undefined here (common for a low-cost, no-upfront-cost "
                "SaaS purchase). NPV and payback are the meaningful numbers for this case."
            )
        elif all(f <= 0 for f in flows):
            irr_reason = "Every modelled cash flow is negative - this case never turns positive within the modelled horizon, so no IRR exists."
        else:
            irr_reason = "IRR did not converge for this cash-flow shape - treat NPV and payback as the reliable numbers."

    payback = payback_months(flows)

    flags = []
    if irr_annual is not None and irr_annual > 10.0:  # > 1000% annualised
        flags.append(
            f"An annualised IRR over 1,000% will not read as credible to a finance audience, even though the "
            f"arithmetic is correct - consider leading with NPV and payback instead, or narrowing the case "
            f"(Shark Finesse's own published guidance is to drop a misleading IRR rather than show it)."
        )
    if payback is not None and payback < 1:
        flags.append(
            "A payback under one month is technically correct but reads as implausible in the room - "
            "lead with the monthly value figure and the multi-year NPV instead of the payback headline."
        )
    if npv_value is not None and npv_value < 0:
        flags.append(
            "NPV is negative over this horizon at this discount rate - the case does not currently clear the cost "
            "of capital. Check the discount rate and horizon are right for this buyer, or the case is genuinely marginal."
        )

    return FinancialResult(
        recurring_monthly_benefit=recurring_monthly_benefit,
        one_time_benefit=one_time_benefit,
        monthly_cost=monthly_cost,
        one_time_cost=one_time_cost,
        discount_rate_annual=discount_rate_annual,
        horizon_months=horizon_months,
        cashflows=flows,
        npv=npv_value,
        irr_annual=irr_annual,
        irr_undefined_reason=irr_reason,
        payback_months=payback,
        credibility_flags=flags,
    )


def sensitivity_ranking(selected_lever_ids, values_by_lever_input, pov_by_lever_input, scenario="expected", swing=0.20):
    """For every filled, non-POV input across the selected levers, perturb
    it +/-`swing` (holding every other input at its scenario value) and
    measure the swing in that lever's own monthly/one-time output. Ranked
    by absolute swing, largest first - this is the tornado-chart data."""
    rows = []
    for lever_id in selected_lever_ids:
        lever = LEVERS_BY_ID.get(lever_id)
        if not lever:
            continue
        if any(pov_by_lever_input.get((lever_id, inp["key"])) for inp in lever["inputs"]):
            continue
        base_values = {}
        complete = True
        for inp in lever["inputs"]:
            cell = values_by_lever_input.get((lever_id, inp["key"]), {})
            v = cell.get(scenario)
            if v is None:
                complete = False
                break
            base_values[inp["key"]] = v
        if not complete:
            continue
        period, base_amount = compute_lever(lever_id, base_values)
        if period is None:
            continue
        for inp in lever["inputs"]:
            low_values = dict(base_values)
            high_values = dict(base_values)
            low_values[inp["key"]] = base_values[inp["key"]] * (1 - swing)
            high_values[inp["key"]] = base_values[inp["key"]] * (1 + swing)
            _, low_amount = compute_lever(lever_id, low_values)
            _, high_amount = compute_lever(lever_id, high_values)
            rows.append(
                {
                    "lever_id": lever_id,
                    "lever_title": lever["title"],
                    "input_key": inp["key"],
                    "input_label": inp["label"],
                    "period": period,
                    "base": base_amount,
                    "low": min(low_amount, high_amount),
                    "high": max(low_amount, high_amount),
                    "swing": abs(high_amount - low_amount),
                }
            )
    rows.sort(key=lambda r: r["swing"], reverse=True)
    return rows
