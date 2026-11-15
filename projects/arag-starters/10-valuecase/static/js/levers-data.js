// The five ARAG value levers - client-side twin of levers.py. Keep both in
// lockstep with content/enablement/roi-value-model.md v2.0 (5 Sep 2026).
export const MONTH_PER_WEEK = 52 / 12;

export const LEVERS = [
  {
    id: "time-to-answer", number: "01", title: "Time-to-answer", subtitle: "Internal knowledge work",
    description: "Staff spend real, countable time hunting through documents, wikis, tickets, case files and recordings for answers that already exist inside the organisation's own content.",
    period: "recurring",
    inputs: [
      { key: "people", label: "People doing knowledge lookups regularly", unit: "people" },
      { key: "lookupsPerWeek", label: "Lookups per person per week", unit: "per week" },
      { key: "minutesSaved", label: "Minutes saved per lookup, once a cited answer replaces a manual search", unit: "minutes", povEligible: true },
      { key: "hourlyCost", label: "Loaded hourly cost per person", unit: "US$/hr" },
    ],
    formulaText: "people x lookups/week x minutes saved / 60 x hourly cost = value per week",
    compute(v) {
      const weekly = v.people * v.lookupsPerWeek * (v.minutesSaved / 60) * v.hourlyCost;
      return { period: "recurring", amount: weekly * MONTH_PER_WEEK };
    },
  },
  {
    id: "deflected-effort", number: "02", title: "Deflected effort", subtitle: "Customer- or member-facing self-serve",
    description: "A grounded, cited assistant on the public-facing site answers questions that today generate a call, an email, or a support ticket.",
    period: "recurring",
    inputs: [
      { key: "contactsPerMonth", label: "Monthly contacts of the types this assistant could genuinely answer", unit: "contacts/mo" },
      { key: "deflectedFraction", label: "Fraction realistically deflected", unit: "%", povEligible: true, isPercent: true },
      { key: "costPerContact", label: "Fully loaded cost per contact (call, email or ticket)", unit: "US$" },
    ],
    formulaText: "contacts/month x deflected fraction x cost per contact = value per month",
    compute(v) {
      return { period: "recurring", amount: v.contactsPerMonth * (v.deflectedFraction / 100) * v.costPerContact };
    },
  },
  {
    id: "faster-path-to-production", number: "03", title: "Faster path to production", subtitle: "Time value of starting now, versus a DIY build (one-time)",
    description: "Prices the time side of build-vs-buy. A DIY retrieval stack takes real engineering months before it answers a single grounded question in production; this only accrues once.",
    period: "one-time",
    inputs: [
      { key: "diyMonths", label: "Estimated months to a working, grounded, quality-measured DIY pipeline", unit: "months" },
      { key: "engMonthlyCost", label: "Fully loaded monthly cost of the engineering team that would build it", unit: "US$/mo" },
    ],
    formulaText: "estimated DIY months x loaded monthly engineering cost = one-time time value",
    compute(v) {
      return { period: "one-time", amount: v.diyMonths * v.engMonthlyCost };
    },
  },
  {
    id: "avoided-build-cost", number: "04", title: "Avoided DIY-build cost", subtitle: "The ongoing engineering opportunity cost",
    description: "Prices what the buyer's engineers would otherwise spend their time on, ongoing - ingestion, chunking, retrieval, reranking, citation, an eval harness.",
    period: "recurring",
    inputs: [
      { key: "engineers", label: "Engineers who would otherwise build and maintain retrieval infrastructure", unit: "engineers" },
      { key: "timeFraction", label: "Fraction of their time this would consume, ongoing", unit: "%", isPercent: true },
      { key: "loadedCostPerEngineer", label: "Fully loaded cost per engineer", unit: "US$/mo" },
    ],
    formulaText: "engineers x time fraction x loaded cost = ongoing avoided cost per month",
    compute(v) {
      return { period: "recurring", amount: v.engineers * (v.timeFraction / 100) * v.loadedCostPerEngineer };
    },
  },
  {
    id: "product-economics", number: "05", title: "Product economics", subtitle: "ISV embed - incremental revenue",
    description: "Revenue, not cost avoidance: an AI feature that an ISV's own end customers pay for, or that measurably improves retention.",
    period: "recurring",
    inputs: [
      { key: "endCustomers", label: "End customers the feature would reach", unit: "customers" },
      { key: "upliftPerCustomer", label: "Monthly price uplift (or retention effect), per end customer", unit: "US$/mo" },
      { key: "adoptionRate", label: "Expected adoption rate among those end customers", unit: "%", isPercent: true },
    ],
    formulaText: "end customers x uplift x adoption = incremental revenue per month",
    compute(v) {
      return { period: "recurring", amount: v.endCustomers * v.upliftPerCustomer * (v.adoptionRate / 100) };
    },
  },
];

export const LEVERS_BY_ID = Object.fromEntries(LEVERS.map((l) => [l.id, l]));
export const PRICING = { starter: 700, pro: 1925 };
export const STAGES = [
  { id: "discovery", label: "Discovery" },
  { id: "evaluation", label: "Evaluation" },
  { id: "decision", label: "Decision" },
  { id: "delivery", label: "Delivery" },
  { id: "renewal", label: "Renewal" },
];

export function fmtUSD(n) {
  if (n === null || n === undefined || !isFinite(n)) return "-";
  return "US$" + Math.round(n).toLocaleString("en-US");
}
export function fmtPct(n) {
  if (n === null || n === undefined || !isFinite(n)) return "n/a";
  return (n * 100).toFixed(1) + "%";
}
export function fmtNum(n) {
  if (n === null || n === undefined || isNaN(n)) return "-";
  return Number.isInteger(n) ? n.toLocaleString("en-US") : n.toLocaleString("en-US", { maximumFractionDigits: 2 });
}

export function leverComplete(lever, values) {
  for (const inp of lever.inputs) {
    const v = values[inp.key];
    if (v === undefined || v === null || v === "" || isNaN(v)) return false;
  }
  return true;
}
