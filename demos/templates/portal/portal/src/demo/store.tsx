import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import type { RemiScore } from '../palette';

// ─────────────────────────────────────────────────────────────────────────────
// Publisher Mutual Claims Desk — the shared state for the claims workbench.
//
// Two real objects, both clearly-labelled synthetic demo data:
//   1. CLAIMS — the eight live claim files that make up the desk queue. These
//      are the claims a handler actually opens and works (Intake, Coverage,
//      Decision, Exception). Every identifier here (claim number, policy number,
//      claimant, peril, amount, date of loss) matches the seeded corpus exactly
//      (Field Rule 7 - one source of truth), so a live ARAG answer and the
//      claim card can never contradict each other.
//   2. PORTFOLIO — a wider synthetic book of work (the eight above plus ~40
//      more summary records) that powers the Portfolio dashboard's charts. It is
//      honestly a SEEDED portfolio, never presented as live-lodged claims - the
//      dashboard computes every figure from it live (no hand-typed headline
//      number), the same discipline as CitedMetric.
//
// The decision/answer LOG captures every coverage answer and decision a visitor
// actually runs (REMi-scored, cited) on top of a small seeded history, so the
// desk's activity feed and the "recent decisions" strip have real texture on
// first load. "Reset" returns to the seeded baseline, never a blank slate.
// ─────────────────────────────────────────────────────────────────────────────

export interface Person {
  name: string;
  role: string;
}

export type ProductLine = 'Home & Contents' | 'Motor' | 'Commercial Property';
export type ClaimStatus =
  | 'In assessment'
  | 'Awaiting decision'
  | 'Needs more info'
  | 'Under investigation'
  | 'Payable'
  | 'Fast-tracked';

export interface Claim {
  id: string;
  claimNumber: string;
  claimant: Person;
  policyNumber: string;
  productLine: ProductLine;
  peril: string;
  status: ClaimStatus;
  amount: number;
  dateOfLoss: string;
  lodged: string;
  incidentLocation: string;
  assignedTo: Person;
  summary: string;
  /** The teaching outcome this claim illustrates - used only to frame the demo's
   *  suggested questions, never shown as a decision. The real decision comes live
   *  from ARAG on the Coverage Decision page. */
  angle: 'payable' | 'not-payable' | 'partial' | 'needs-info' | 'exception';
}

const daysAgo = (d: number) => {
  const dt = new Date(Date.now() - d * 86_400_000);
  return dt.toISOString().slice(0, 10);
};

// ── the eight live claim files (the desk queue) ──────────────────────────────
export const CLAIMS: Claim[] = [
  {
    id: 'clm-0501', claimNumber: 'CLM-2026-0501',
    claimant: { name: 'The Delacroix Family', role: 'Policyholder' },
    policyNumber: 'THP-55190', productLine: 'Home & Contents', peril: 'Flood',
    status: 'Needs more info', amount: 42000, dateOfLoss: '2026-05-28', lodged: daysAgo(6),
    incidentLocation: 'Maribyrnong, VIC',
    assignedTo: { name: 'Owen Fitzgerald', role: 'Property Claims Adjuster' },
    summary: 'Riverine flood after the river overtopped its banks. Coverage in question - the policy schedule shows optional flood cover was not selected.',
    angle: 'not-payable',
  },
  {
    id: 'clm-0466', claimNumber: 'CLM-2026-0466',
    claimant: { name: 'Tomas Ruiz', role: 'Policyholder' },
    policyNumber: 'TDM-33871', productLine: 'Motor', peril: 'Theft',
    status: 'Under investigation', amount: 31500, dateOfLoss: '2026-03-12', lodged: daysAgo(9),
    incidentLocation: 'Footscray, VIC',
    assignedTo: { name: 'Derek Salmond', role: 'Motor Claims Assessor' },
    summary: 'Vehicle theft. Two integrity flags: the FNOL date of loss and the police report date do not match, and the premium was in arrears at the date of loss.',
    angle: 'exception',
  },
  {
    id: 'clm-0473', claimNumber: 'CLM-2026-0473',
    claimant: { name: 'Helena Vaughn', role: 'Policyholder' },
    policyNumber: 'THP-88213', productLine: 'Home & Contents', peril: 'Water damage',
    status: 'In assessment', amount: 18400, dateOfLoss: '2026-06-14', lodged: daysAgo(4),
    incidentLocation: 'Newtown, NSW',
    assignedTo: { name: 'Aisha Okonkwo', role: 'Claims Adjuster' },
    summary: 'Sudden water damage from a burst flexible hose under the kitchen sink. Sudden and accidental water damage is a covered peril.',
    angle: 'payable',
  },
  {
    id: 'clm-0492', claimNumber: 'CLM-2026-0492',
    claimant: { name: 'Priya Anand', role: 'Policyholder' },
    policyNumber: 'THP-62255', productLine: 'Home & Contents', peril: 'Burglary',
    status: 'In assessment', amount: 7800, dateOfLoss: '2026-06-30', lodged: daysAgo(3),
    incidentLocation: 'Carindale, QLD',
    assignedTo: { name: 'Aisha Okonkwo', role: 'Claims Adjuster' },
    summary: 'Burglary and contents theft, including a diamond ring valued at about $6,000 that was not listed as a specified item - capped at the unspecified single-item sub-limit.',
    angle: 'partial',
  },
  {
    id: 'clm-0488', claimNumber: 'CLM-2026-0488',
    claimant: { name: 'Raj Malhotra', role: 'Policyholder' },
    policyNumber: 'TDM-40027', productLine: 'Motor', peril: 'Collision',
    status: 'Awaiting decision', amount: 9250, dateOfLoss: '2026-06-20', lodged: daysAgo(5),
    incidentLocation: 'Prospect, SA',
    assignedTo: { name: 'Derek Salmond', role: 'Motor Claims Assessor' },
    summary: 'Single-vehicle collision. Covered under comprehensive motor cover, payable less the standard excess.',
    angle: 'payable',
  },
  {
    id: 'clm-0510', claimNumber: 'CLM-2026-0510',
    claimant: { name: 'George Mensah', role: 'Policyholder' },
    policyNumber: 'THP-77321', productLine: 'Home & Contents', peril: 'Water damage',
    status: 'Needs more info', amount: 14200, dateOfLoss: '2026-06-02', lodged: daysAgo(7),
    incidentLocation: 'Mitchell Park, SA',
    assignedTo: { name: 'Owen Fitzgerald', role: 'Property Claims Adjuster' },
    summary: 'Water damage from a slow bathroom leak found during a renovation. The inspector attributes it to gradual deterioration - gradual damage is excluded, distinct from sudden and accidental.',
    angle: 'needs-info',
  },
  {
    id: 'clm-0455', claimNumber: 'CLM-2026-0455',
    claimant: { name: 'Brightwater Cafe Pty Ltd', role: 'Policyholder, commercial' },
    policyNumber: 'TCP-71004', productLine: 'Commercial Property', peril: 'Fire',
    status: 'Payable', amount: 128000, dateOfLoss: '2026-04-11', lodged: daysAgo(14),
    incidentLocation: 'Fortitude Valley, QLD',
    assignedTo: { name: 'Marcus Trent', role: 'Senior Claims Adjuster' },
    summary: 'Electrical fire in the cafe kitchen. Payable within the sums insured; the business-interruption sub-limit applies to part of the claim.',
    angle: 'payable',
  },
  {
    id: 'clm-0480', claimNumber: 'CLM-2026-0480',
    claimant: { name: 'Sofia Bianchi', role: 'Policyholder' },
    policyNumber: 'TDM-51188', productLine: 'Motor', peril: 'Windscreen',
    status: 'Fast-tracked', amount: 680, dateOfLoss: '2026-07-01', lodged: daysAgo(2),
    incidentLocation: 'Glenelg, SA',
    assignedTo: { name: 'Derek Salmond', role: 'Motor Claims Assessor' },
    summary: 'Windscreen glass claim. The schedule carries the Glass Excess Waiver endorsement, so nil excess applies - fast-tracked.',
    angle: 'payable',
  },
];

export const PRODUCT_LINES: ProductLine[] = ['Home & Contents', 'Motor', 'Commercial Property'];
export const STATUS_ORDER: ClaimStatus[] = [
  'Needs more info', 'Under investigation', 'Awaiting decision', 'In assessment', 'Fast-tracked', 'Payable',
];

export function statusTone(status: ClaimStatus): string {
  switch (status) {
    case 'Needs more info': return '#d97706';
    case 'Under investigation': return '#dc2626';
    case 'Awaiting decision': return '#2563c9';
    case 'In assessment': return '#0e7490';
    case 'Fast-tracked': return '#7c3aed';
    case 'Payable': return '#16a34a';
    default: return '#64748b';
  }
}

export const CLAIMS_BY_ID: Record<string, Claim> = Object.fromEntries(CLAIMS.map((c) => [c.id, c]));

// ── document-derived insight (Standard B28) ──────────────────────────────────
// The dimensions ARAG extracts by READING each claim's unstructured documents -
// the FNOL narrative, the adjuster report, the decision letter - NOT the coded
// fields already on a claim record. A coded peril tells you "Water damage"; only
// reading the adjuster's free-text tells you it was a SUDDEN escape (payable) vs
// GRADUAL deterioration (excluded). These four dimensions drive the Portfolio
// dashboard, to prove ARAG turns unstructured documents into structured insight.
// Integrity note (hard rule 3): the values are a REAL ARAG extraction over the
// documented claims (see EXTRACTED_INSIGHT below) - never authored or synthetic
// under an "extracted by ARAG" claim. The dashboard is scoped to exactly those
// documented claims; the wider synthetic book carries no insight (it has no
// documents to extract from) and is never charted as "extracted".
export type Sentiment = 'Calm' | 'Concerned' | 'Distressed';
export type Complexity = 'Straightforward' | 'Moderate' | 'Complex';
export const INTEGRITY_SIGNALS = [
  'Date-of-loss mismatch', 'Premium in arrears', 'Value over sub-limit', 'Inconsistent damage cause', 'Prior-claims pattern',
] as const;
export type IntegritySignal = typeof INTEGRITY_SIGNALS[number];

export interface ClaimInsight {
  /** Cause-of-loss THEME, read from the adjuster free-text - finer than the coded peril. */
  causeTheme: string;
  /** Claimant tone, read from the First Notice of Loss narrative. */
  sentiment: Sentiment;
  /** Integrity / fraud-risk signals inferred by reading the whole file against the indicators. */
  signals: IntegritySignal[];
  /** How many policy clauses ARAG had to reason across to decide the claim. */
  complexity: Complexity;
}

export interface DocumentedInsight extends ClaimInsight {
  claimNumber: string;
  claimant: string;
}

// Standard B28 integrity (hard rule 3): these are REAL ARAG extractions, not
// authored values. Each was produced live by scripts/extract-insight.mjs - a
// query-time answer_json_schema /ask (the working structured-JSON path Claim
// Intake uses) run over each documented claim's own FNOL narrative, adjuster
// report and decision letter, scoped by the claim_number label. Captured
// 2026-08-18; re-run the script to refresh. Because these are genuine
// extractions, the Portfolio charts can honestly carry the "extracted by ARAG"
// framing - and they are scoped to exactly these documented claims, never the
// wider synthetic book (which has no documents to extract from).
export const EXTRACTED_INSIGHT: DocumentedInsight[] = [
  { claimNumber: 'CLM-2026-0501', claimant: 'The Delacroix Family', causeTheme: 'Riverine flood (overtopping)', sentiment: 'Concerned', signals: [], complexity: 'Straightforward' },
  { claimNumber: 'CLM-2026-0466', claimant: 'Tomas Ruiz', causeTheme: 'Vehicle theft', sentiment: 'Concerned', signals: ['Date-of-loss mismatch', 'Premium in arrears'], complexity: 'Complex' },
  { claimNumber: 'CLM-2026-0473', claimant: 'Helena Vaughn', causeTheme: 'Sudden and accidental burst of a flexible hose', sentiment: 'Calm', signals: [], complexity: 'Straightforward' },
  { claimNumber: 'CLM-2026-0492', claimant: 'Priya Anand', causeTheme: 'Forced-entry burglary', sentiment: 'Concerned', signals: ['Value over sub-limit'], complexity: 'Complex' },
  { claimNumber: 'CLM-2026-0488', claimant: 'Raj Malhotra', causeTheme: 'Single-vehicle collision in wet conditions', sentiment: 'Calm', signals: [], complexity: 'Straightforward' },
  { claimNumber: 'CLM-2026-0510', claimant: 'George Mensah', causeTheme: 'Gradual deterioration of shower waterproofing', sentiment: 'Concerned', signals: [], complexity: 'Straightforward' },
  { claimNumber: 'CLM-2026-0455', claimant: 'Brightwater Cafe Pty Ltd', causeTheme: 'Electrical fire', sentiment: 'Concerned', signals: [], complexity: 'Straightforward' },
  { claimNumber: 'CLM-2026-0480', claimant: 'Sofia Bianchi', causeTheme: 'Stone-strike windscreen crack', sentiment: 'Calm', signals: [], complexity: 'Straightforward' },
];

// ── the wider synthetic portfolio (drives the dashboard charts) ──────────────
export interface PortfolioRecord {
  claimNumber: string;
  productLine: ProductLine;
  peril: string;
  status: ClaimStatus;
  amount: number;
  lodgedDaysAgo: number;
  cycleTimeDays: number;
}

// Deterministic pseudo-random so the seeded portfolio is identical every load
// (no per-render churn) - a small LCG over a fixed seed.
function makePortfolio(): PortfolioRecord[] {
  const perils: Record<ProductLine, string[]> = {
    'Home & Contents': ['Water damage', 'Storm', 'Burglary', 'Fire', 'Flood', 'Impact'],
    'Motor': ['Collision', 'Theft', 'Windscreen', 'Storm', 'Fire'],
    'Commercial Property': ['Fire', 'Storm', 'Theft', 'Impact'],
  };
  const statuses: ClaimStatus[] = ['Payable', 'Payable', 'Payable', 'In assessment', 'Awaiting decision', 'Needs more info', 'Under investigation', 'Fast-tracked'];
  const lineMix: ProductLine[] = [
    ...Array(22).fill('Home & Contents'), ...Array(18).fill('Motor'), ...Array(8).fill('Commercial Property'),
  ] as ProductLine[];
  let s = 987654321;
  const rnd = () => { s = (s * 1103515245 + 12345) & 0x7fffffff; return s / 0x7fffffff; };

  const out: PortfolioRecord[] = CLAIMS.map((c) => ({
    claimNumber: c.claimNumber, productLine: c.productLine, peril: c.peril, status: c.status,
    amount: c.amount, lodgedDaysAgo: Math.round((Date.now() - Date.parse(c.lodged)) / 86_400_000),
    cycleTimeDays: c.status === 'Payable' || c.status === 'Fast-tracked' ? 4 + Math.round(rnd() * 10) : 0,
  }));
  for (let i = 0; i < 44; i++) {
    const line = lineMix[Math.floor(rnd() * lineMix.length)];
    const pk = perils[line];
    const status = statuses[Math.floor(rnd() * statuses.length)];
    const settled = status === 'Payable' || status === 'Fast-tracked';
    const base = line === 'Commercial Property' ? 40000 : line === 'Motor' ? 6000 : 12000;
    out.push({
      claimNumber: `CLM-2026-${String(300 + i).padStart(4, '0')}`,
      productLine: line,
      peril: pk[Math.floor(rnd() * pk.length)],
      status,
      amount: Math.round((base * (0.4 + rnd() * 1.8)) / 50) * 50,
      lodgedDaysAgo: 2 + Math.floor(rnd() * 88),
      cycleTimeDays: settled ? 3 + Math.round(rnd() * 22) : 0,
    });
  }
  return out;
}
export const PORTFOLIO: PortfolioRecord[] = makePortfolio();

// ── the shared decision / answer log ─────────────────────────────────────────
export type LogRoute = 'coverage' | 'decision' | 'exceptions';

export interface LoggedAnswer {
  id: string;
  claimNumber: string;
  claimant: string;
  route: LogRoute;
  query: string;
  answer: string;
  citationCount: number;
  remi: RemiScore | null;
  timestamp: number;
}

const STORAGE_KEY = 'publisher.claimsdesk.log.v1';

function remi(g: number, a: number, c: number, reason: string): RemiScore {
  return { groundedness: g, answerRelevance: a, contextRelevance: c, answerRelevanceReason: reason };
}
const ago = (d: number, h = 10) => Date.now() - d * 86_400_000 - (24 - h) * 3_600_000;

const SEED_LOG: LoggedAnswer[] = [
  { id: 'seed-01', claimNumber: 'CLM-2026-0473', claimant: 'Helena Vaughn', route: 'coverage', timestamp: ago(4, 11),
    query: 'Is sudden water damage from a burst flexible hose covered under the TideProtect Home and Contents policy?',
    answer: 'Yes. Sudden and accidental water damage, including escape of water from a burst flexible hose, is a covered peril under the TideProtect Home & Contents wording, so the Vaughn claim is payable subject to the standard excess.',
    citationCount: 2, remi: remi(4.8, 4.7, 4.6, 'Directly grounded in the covered-perils section of the Home & Contents PDS.') },
  { id: 'seed-02', claimNumber: 'CLM-2026-0501', claimant: 'The Delacroix Family', route: 'decision', timestamp: ago(3, 15),
    query: 'Is the Delacroix flood claim payable given their policy schedule?',
    answer: 'Not payable for the flood damage. The TideProtect wording makes flood an optional cover, and the Delacroix policy schedule (THP-55190) shows flood cover was not selected, so riverine flood damage is excluded.',
    citationCount: 3, remi: remi(4.7, 4.8, 4.5, 'Cross-references the schedule and the PDS flood-cover clause directly.') },
  { id: 'seed-03', claimNumber: 'CLM-2026-0480', claimant: 'Sofia Bianchi', route: 'coverage', timestamp: ago(2, 9),
    query: 'What excess applies to the Bianchi windscreen claim?',
    answer: 'Nil excess. The Bianchi motor schedule (TDM-51188) carries the Glass Excess Waiver endorsement, which waives the excess on a windscreen or glass-only claim, so the $680 claim is payable in full.',
    citationCount: 2, remi: remi(4.6, 4.5, 4.4, 'Grounded in the schedule endorsement and the motor PDS glass clause.') },
  { id: 'seed-04', claimNumber: 'CLM-2026-0466', claimant: 'Tomas Ruiz', route: 'exceptions', timestamp: ago(2, 14),
    query: 'Does the Tomas Ruiz theft claim have any inconsistencies a handler should flag?',
    answer: 'Two exceptions. The FNOL records the date of loss as 12 March 2026, but the attached police report records the incident on 26 March 2026 - a date-of-loss inconsistency. Separately, the premium was in arrears at the date of loss, which the motor wording allows as a ground to reduce or refuse the claim.',
    citationCount: 3, remi: remi(3.2, 4.1, 2.9, 'Grounding is thinner - the arrears note and the police-report date sit in separate documents and the link is inferred.') },
  { id: 'seed-05', claimNumber: 'CLM-2026-0492', claimant: 'Priya Anand', route: 'decision', timestamp: ago(1, 16),
    query: 'How much of the Anand burglary claim is payable given the specified-items rule?',
    answer: 'Partially payable. The diamond ring at about $6,000 was not listed as a specified item, so it is capped at the $2,500 unspecified single-item sub-limit; the remaining contents are payable to their sums insured.',
    citationCount: 3, remi: remi(4.5, 4.6, 4.3, 'Grounded in the schedule sub-limits and the PDS specified-items clause.') },
  { id: 'seed-06', claimNumber: 'CLM-2026-0510', claimant: 'George Mensah', route: 'coverage', timestamp: ago(1, 10),
    query: 'Is the Mensah water-damage claim covered given the inspector report?',
    answer: 'Likely not payable. The building inspector attributes the damage to gradual deterioration over several months; gradual damage and lack of maintenance are excluded under the Home & Contents wording, which covers only sudden and accidental water damage.',
    citationCount: 2, remi: remi(3.8, 4.0, 3.6, 'Directionally grounded, but the gradual-vs-sudden distinction rests on the inspector note more than the wording alone.') },
  { id: 'seed-07', claimNumber: 'CLM-2026-0455', claimant: 'Brightwater Cafe Pty Ltd', route: 'decision', timestamp: ago(0, 9),
    query: 'Is the Brightwater Cafe fire claim payable and does the business-interruption sub-limit apply?',
    answer: 'Payable. The electrical fire is a covered peril under the Commercial Property wording; the property loss is within the sums insured, and the business-interruption portion is payable up to its sub-limit.',
    citationCount: 3, remi: remi(4.7, 4.6, 4.6, 'Grounded in the Commercial Property PDS and the TCP-71004 schedule.') },
];

interface ClaimsDeskContextValue {
  activeClaimId: string;
  activeClaim: Claim;
  setActiveClaim: (id: string) => void;
  log: LoggedAnswer[];
  addEntry: (entry: Omit<LoggedAnswer, 'id' | 'timestamp'>) => void;
  clear: () => void;
}

const ClaimsDeskContext = createContext<ClaimsDeskContextValue | null>(null);

function loadInitial(): LoggedAnswer[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as LoggedAnswer[];
  } catch { /* fall through */ }
  return SEED_LOG;
}

export function ClaimsDeskProvider({ children }: { children: ReactNode }) {
  const [activeClaimId, setActiveClaimId] = useState<string>(CLAIMS[0].id);
  const [log, setLog] = useState<LoggedAnswer[]>(() => loadInitial());

  const setActiveClaim = useCallback((id: string) => setActiveClaimId(id), []);

  const addEntry = useCallback((entry: Omit<LoggedAnswer, 'id' | 'timestamp'>) => {
    setLog((prev) => {
      const next = [
        { ...entry, id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, timestamp: Date.now() },
        ...prev,
      ].slice(0, 200);
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); } catch { /* ignore */ }
      return next;
    });
  }, []);

  const clear = useCallback(() => {
    setLog(SEED_LOG);
    try { localStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
  }, []);

  const activeClaim = useMemo(() => CLAIMS_BY_ID[activeClaimId] || CLAIMS[0], [activeClaimId]);

  return (
    <ClaimsDeskContext.Provider value={{ activeClaimId, activeClaim, setActiveClaim, log, addEntry, clear }}>
      {children}
    </ClaimsDeskContext.Provider>
  );
}

export function useClaimsDesk() {
  const ctx = useContext(ClaimsDeskContext);
  if (!ctx) throw new Error('useClaimsDesk must be used within ClaimsDeskProvider');
  return ctx;
}

export function lowestScore(r: RemiScore | null): number | null {
  if (!r) return null;
  const vals = [r.groundedness, r.answerRelevance, r.contextRelevance].filter(
    (v): v is number => typeof v === 'number'
  );
  return vals.length ? Math.min(...vals) : null;
}

export function formatMoney(n: number): string {
  return `$${n.toLocaleString('en-AU')}`;
}
