"""Hand-verification of finance.py against known arithmetic, run before this
module is trusted (per the build plan sent to the lead: this maths is
general finance convention, not KB-grounded, so it gets its own explicit
correctness check rather than the ARAG-claim verification gate).

Run:  ../../.venv/bin/python tests_finance_selftest.py
"""
from finance import (
    annual_to_monthly_rate, build_cashflows, npv, irr_monthly,
    monthly_to_annual_rate, payback_months, evaluate_case,
)

FAILS = []


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        FAILS.append(label)


def approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


# 1. Classic textbook case: -1000 upfront, +300/year for 5 years, discounted
#    annually at 10%. Known result (standard finance textbook value):
#    NPV(10%) = -1000 + 300*annuity_factor(10%,5) = -1000 + 300*3.790787 = 137.24
#    IRR of this series is 15.238% (a widely published reference value for
#    this exact classic problem). Model here in ANNUAL steps by treating
#    "month" as "year" for this one comparison test (the arithmetic - NPV
#    and IRR bisection - is period-agnostic; only the annual<->monthly
#    conversion helpers are monthly-specific and are checked separately).
annual_flows = [-1000, 300, 300, 300, 300, 300]
check("NPV(10%) matches textbook 137.24 for -1000/+300x5", approx(npv(annual_flows, 0.10), 137.24, tol=0.5))
irr_annual_direct = irr_monthly(annual_flows, lo=-0.99, hi=5.0)
check("IRR matches textbook 15.238% for -1000/+300x5", approx(irr_annual_direct, 0.15238, tol=0.001))
check("NPV at the solved IRR is ~0 (self-consistency)", approx(npv(annual_flows, irr_annual_direct), 0.0, tol=1e-4))

# 2. Payback with constant flows: -1200 upfront, +100/month -> pays back
#    in exactly 12 months.
flows_constant = build_cashflows(one_time_benefit=0, monthly_net_benefit=100, monthly_cost=0,
                                  one_time_cost=1200, horizon_months=24)
pb = payback_months(flows_constant)
check("Payback = 12.0 months for -1200 upfront / +100 per month", approx(pb, 12.0, tol=1e-6))

# 3. Undefined IRR when every cash flow is positive (no upfront cost) - the
#    common real case for this tool (a low-cost SaaS purchase with no
#    negative outflow anywhere).
flows_all_positive = build_cashflows(one_time_benefit=0, monthly_net_benefit=500, monthly_cost=100,
                                      one_time_cost=0, horizon_months=24)
irr_should_be_none = irr_monthly(flows_all_positive)
check("IRR is None (undefined) when every cash flow is positive", irr_should_be_none is None)

# 4. Monthly<->annual rate round-trip.
m = annual_to_monthly_rate(0.12)
check("annual_to_monthly_rate/monthly_to_annual_rate round-trip on 12%", approx(monthly_to_annual_rate(m), 0.12, tol=1e-9))

# 5. evaluate_case end-to-end sanity: a realistic case (no upfront cost,
#    $3,870/mo benefit per the model doc's own worked example, Starter
#    $700/mo cost) should produce a positive NPV, an undefined IRR (all
#    flows positive), and a payback of 0 months (benefit exceeds cost from
#    month 1).
result = evaluate_case(
    recurring_monthly_benefit=3870, one_time_benefit=0, monthly_cost=700, one_time_cost=0,
    discount_rate_annual=0.10, horizon_months=24,
)
check("evaluate_case: NPV positive on the model doc's own worked example", result.npv > 0)
check("evaluate_case: IRR undefined (all-positive cash flows) with a clear reason string", result.irr_annual is None and bool(result.irr_undefined_reason))
check("evaluate_case: payback is 0 months (benefit exceeds cost from month 1)", approx(result.payback_months, 0.0, tol=1e-6))

print()
if FAILS:
    print(f"{len(FAILS)} check(s) FAILED: {FAILS}")
    raise SystemExit(1)
print("All finance self-checks passed.")
