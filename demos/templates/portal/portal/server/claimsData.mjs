// Synthetic live app data for the Claims Copilot's /mcp tools — never KB
// documents. Deliberately consistent with the seeded corpus's named entities
// (research/publisher-claims.md and the per-claim documents) so a live agent
// answer and a cited document answer never contradict each other (Field Rule 7).
//
// This is the "live operational systems" the Retrieval Agent reaches over MCP:
// the policy master, the claimant claims-history register, and the claim record
// — the data that lives in an insurer's core systems, not in the document KB.

// ── policy master ────────────────────────────────────────────────────────────
export const POLICIES = [
  {
    policyNumber: 'THP-55190', holder: 'The Delacroix Family', productLine: 'Home & Contents',
    inForce: true, premiumStatus: 'current', excess: 500,
    floodCoverSelected: false,
    endorsements: [],
    notes: 'Optional flood cover was NOT selected on this schedule, so riverine flood damage is excluded.',
  },
  {
    policyNumber: 'TDM-33871', holder: 'Tomas Ruiz', productLine: 'Motor',
    inForce: true, premiumStatus: 'in arrears',
    excess: 900, floodCoverSelected: null, endorsements: [],
    notes: 'Premium was unpaid (in arrears) at the recorded date of loss, 12 March 2026 - a ground under the motor wording to reduce or refuse the claim.',
  },
  {
    policyNumber: 'THP-88213', holder: 'Helena Vaughn', productLine: 'Home & Contents',
    inForce: true, premiumStatus: 'current', excess: 400,
    floodCoverSelected: true, endorsements: [],
    notes: 'Sudden and accidental water damage is covered; standard excess applies.',
  },
  {
    policyNumber: 'THP-62255', holder: 'Priya Anand', productLine: 'Home & Contents',
    inForce: true, premiumStatus: 'current', excess: 400,
    floodCoverSelected: false,
    endorsements: [],
    notes: 'Unspecified single-item contents sub-limit is $2,500; the diamond ring was not listed as a specified item.',
  },
  {
    policyNumber: 'TDM-40027', holder: 'Raj Malhotra', productLine: 'Motor',
    inForce: true, premiumStatus: 'current', excess: 750, floodCoverSelected: null,
    endorsements: [], notes: 'Comprehensive motor cover; standard excess $750.',
  },
  {
    policyNumber: 'THP-77321', holder: 'George Mensah', productLine: 'Home & Contents',
    inForce: true, premiumStatus: 'current', excess: 400, floodCoverSelected: true,
    endorsements: [], notes: 'Covers sudden and accidental water damage only; gradual deterioration is excluded.',
  },
  {
    policyNumber: 'TCP-71004', holder: 'Brightwater Cafe Pty Ltd', productLine: 'Commercial Property',
    inForce: true, premiumStatus: 'current', excess: 2500, floodCoverSelected: null,
    endorsements: ['Business interruption (sub-limit $50,000)'],
    notes: 'Fire is a covered peril; business-interruption sub-limit applies to the BI portion.',
  },
  {
    policyNumber: 'TDM-51188', holder: 'Sofia Bianchi', productLine: 'Motor',
    inForce: true, premiumStatus: 'current', excess: 800, floodCoverSelected: null,
    endorsements: ['Glass Excess Waiver'],
    notes: 'Glass Excess Waiver endorsement held - nil excess on a windscreen or glass-only claim.',
  },
];

// ── claimant claims-history register ─────────────────────────────────────────
export const CLAIMANT_HISTORY = [
  {
    claimant: 'Tomas Ruiz',
    priorClaims: [
      { claimNumber: 'CLM-2024-1180', peril: 'Theft', year: 2024, outcome: 'Withdrawn by policyholder' },
      { claimNumber: 'CLM-2022-0733', peril: 'Windscreen', year: 2022, outcome: 'Paid' },
    ],
    notes: 'Two prior motor claims; one theft claim in 2024 was withdrawn before assessment completed.',
  },
  { claimant: 'The Delacroix Family', priorClaims: [{ claimNumber: 'CLM-2023-0410', peril: 'Storm', year: 2023, outcome: 'Paid' }], notes: 'One prior storm claim, paid.' },
  { claimant: 'Helena Vaughn', priorClaims: [], notes: 'No prior claims on record.' },
  { claimant: 'Priya Anand', priorClaims: [], notes: 'No prior claims on record.' },
  { claimant: 'Raj Malhotra', priorClaims: [{ claimNumber: 'CLM-2021-0288', peril: 'Windscreen', year: 2021, outcome: 'Paid' }], notes: 'One prior windscreen claim, paid.' },
  { claimant: 'George Mensah', priorClaims: [], notes: 'No prior claims on record.' },
  { claimant: 'Brightwater Cafe Pty Ltd', priorClaims: [], notes: 'No prior commercial claims on record.' },
  { claimant: 'Sofia Bianchi', priorClaims: [], notes: 'No prior claims on record.' },
];

// ── claim record (the core claims system) ────────────────────────────────────
export const CLAIM_RECORDS = [
  { claimNumber: 'CLM-2026-0501', claimant: 'The Delacroix Family', policyNumber: 'THP-55190', peril: 'Flood', dateOfLoss: '2026-05-28', amount: 42000, status: 'Needs more info' },
  { claimNumber: 'CLM-2026-0466', claimant: 'Tomas Ruiz', policyNumber: 'TDM-33871', peril: 'Theft', dateOfLoss: '2026-03-12', amount: 31500, status: 'Under investigation' },
  { claimNumber: 'CLM-2026-0473', claimant: 'Helena Vaughn', policyNumber: 'THP-88213', peril: 'Water damage', dateOfLoss: '2026-06-14', amount: 18400, status: 'In assessment' },
  { claimNumber: 'CLM-2026-0492', claimant: 'Priya Anand', policyNumber: 'THP-62255', peril: 'Burglary', dateOfLoss: '2026-06-30', amount: 7800, status: 'In assessment' },
  { claimNumber: 'CLM-2026-0488', claimant: 'Raj Malhotra', policyNumber: 'TDM-40027', peril: 'Collision', dateOfLoss: '2026-06-20', amount: 9250, status: 'Awaiting decision' },
  { claimNumber: 'CLM-2026-0510', claimant: 'George Mensah', policyNumber: 'THP-77321', peril: 'Water damage', dateOfLoss: '2026-06-02', amount: 14200, status: 'Needs more info' },
  { claimNumber: 'CLM-2026-0455', claimant: 'Brightwater Cafe Pty Ltd', policyNumber: 'TCP-71004', peril: 'Fire', dateOfLoss: '2026-04-11', amount: 128000, status: 'Payable' },
  { claimNumber: 'CLM-2026-0480', claimant: 'Sofia Bianchi', policyNumber: 'TDM-51188', peril: 'Windscreen', dateOfLoss: '2026-07-01', amount: 680, status: 'Fast-tracked' },
];

const norm = (s) => String(s || '').toLowerCase().trim().replace(/^the\s+/, '');

// Standard B29 (realism, GM directive 18 Aug 2026): a real claims system keys on
// an identifier and behaves like a competent handler - it never silently returns
// ONE confident record when the request could mean several. These matchers return
// ALL matches (an EXACT identifier match wins outright and is unique); the tool
// handlers then disambiguate honestly - resolve a single hit, ask which one on a
// multi-hit, decline on none - rather than `.find()` picking the first and
// fabricating certainty. An exact policy/claim number is authoritative; a
// name/partial can legitimately be ambiguous and is surfaced as such.
export function matchPolicies(q) {
  const n = norm(q);
  if (!n) return [];
  const exact = POLICIES.filter((p) => p.policyNumber.toLowerCase() === n);
  if (exact.length) return exact;
  return POLICIES.filter((p) => norm(p.holder) === n || norm(p.holder).includes(n) || n.includes(norm(p.holder)));
}
export function matchHistories(q) {
  const n = norm(q);
  if (!n) return [];
  return CLAIMANT_HISTORY.filter((h) => norm(h.claimant) === n || norm(h.claimant).includes(n) || n.includes(norm(h.claimant)));
}
export function matchClaims(q) {
  const n = norm(q);
  if (!n) return [];
  const exact = CLAIM_RECORDS.filter((c) => c.claimNumber.toLowerCase() === n);
  if (exact.length) return exact;
  return CLAIM_RECORDS.filter((c) => norm(c.claimant) === n || norm(c.claimant).includes(n) || n.includes(norm(c.claimant)));
}
