// ─────────────────────────────────────────────────────────────────────────────
// Underwriting Risk Summary — the three live applications on the underwriter's
// desk. A second real object alongside CLAIMS (store.tsx), same discipline: every
// identifier here (application number, applicant, product line) matches the
// seeded corpus exactly (Field Rule 7), so a live ARAG synthesis and the
// application card can never contradict each other. Deliberately a SMALL,
// self-contained set (three, not eight) — underwriting referral is a lower-
// volume, higher-judgement desk than the claims queue, and the page carries its
// own compact selector rather than the claims desk's full queue rail.
// ─────────────────────────────────────────────────────────────────────────────

export type UWProductLine = 'Home & Contents' | 'Motor' | 'Commercial Property';
export type RiskAngle = 'bushfire' | 'young-driver-modified' | 'fire-severity';

export interface Application {
  id: string;
  applicationNumber: string;
  applicant: { name: string; role: string };
  productLine: UWProductLine;
  riskAngle: RiskAngle;
  submitted: string;
  summary: string;
}

export const APPLICATIONS: Application[] = [
  {
    id: 'uw-1214',
    applicationNumber: 'UW-2026-1214',
    applicant: { name: 'Nadia and Simon Cheng', role: 'Applicants' },
    productLine: 'Home & Contents',
    riskAngle: 'bushfire',
    submitted: '14 Jul 2026',
    summary: 'New-build home adjoining bushland, BAL-29 construction, ember-guard mesh installation still outstanding.',
  },
  {
    id: 'uw-1229',
    applicationNumber: 'UW-2026-1229',
    applicant: { name: 'Jack Petrovic', role: 'Applicant' },
    productLine: 'Motor',
    riskAngle: 'young-driver-modified',
    submitted: '2 Jul 2026',
    summary: '19-year-old P2 driver applying for a modified turbocharged hatchback, one prior at-fault claim.',
  },
  {
    id: 'uw-1241',
    applicationNumber: 'UW-2026-1241',
    applicant: { name: 'Southbank Import Traders Pty Ltd', role: 'Applicant, commercial' },
    productLine: 'Commercial Property',
    riskAngle: 'fire-severity',
    submitted: '20 Jun 2026',
    summary: 'Warehouse storing packaged aerosol stock, no sprinkler system, one prior fire claim two years ago.',
  },
];

export const APPLICATIONS_BY_ID: Record<string, Application> = Object.fromEntries(APPLICATIONS.map((a) => [a.id, a]));

export function riskRatingTone(rating: string | null | undefined): string {
  const r = (rating || '').toLowerCase();
  if (r === 'high') return '#dc2626';
  if (r === 'medium') return '#d97706';
  if (r === 'low') return '#16a34a';
  return '#64748b';
}

export function recommendedActionTone(action: string | null | undefined): string {
  const a = (action || '').toLowerCase();
  if (a.includes('decline')) return '#dc2626';
  if (a.includes('refer')) return '#dc2626';
  if (a.includes('loading') || a.includes('condition')) return '#d97706';
  if (a.includes('standard')) return '#16a34a';
  return '#64748b';
}
