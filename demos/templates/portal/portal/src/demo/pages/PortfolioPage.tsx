import { useMemo } from 'react';
import { Sparkles, FileText, ShieldAlert, Layers, ScanText, CheckCircle2 } from 'lucide-react';
import { ShareChart, BreakdownChart, StatTile } from '../../palette';
import type { DemoConfig } from '../../lib/config';
import { EXTRACTED_INSIGHT, CLAIMS, PORTFOLIO, type Sentiment } from '../store';

// ─────────────────────────────────────────────────────────────────────────────
// Use case 5 - Claims insight dashboard (Standard B28 + integrity, hard rule 3).
// Every value on this page is a REAL ARAG extraction: scripts/extract-insight.mjs
// runs a query-time answer_json_schema /ask (the working structured-JSON path
// Claim Intake uses) over each documented claim's own FNOL narrative, adjuster
// report and decision letter, and reads out four dimensions that do NOT exist as
// coded fields - the cause-of-loss THEME (finer than the coded peril: sudden
// escape vs gradual deterioration), the claimant's SENTIMENT (from the FNOL
// tone), the integrity/fraud-risk SIGNALS (from the whole file) and the coverage
// COMPLEXITY. The page is scoped to exactly the claims that extraction genuinely
// covered - the documented desk claims - never the wider synthetic book (which
// has no documents to extract from), so nothing is charted as "extracted by
// ARAG" that ARAG did not extract.
// ─────────────────────────────────────────────────────────────────────────────

const PERIL_BY_CLAIM: Record<string, string> = Object.fromEntries(CLAIMS.map((c) => [c.claimNumber, c.peril]));

const SENTIMENT_TONE: Record<Sentiment, string> = { Calm: '#16a34a', Concerned: '#d97706', Distressed: '#dc2626' };
const COMPLEXITY_TONE: Record<string, string> = { Straightforward: '#16a34a', Moderate: '#d97706', Complex: '#dc2626' };

function Chip({ label, tone }: { label: string; tone: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-semibold" style={{ color: tone, background: `color-mix(in srgb, ${tone} 15%, transparent)`, border: `1px solid color-mix(in srgb, ${tone} 32%, transparent)` }}>
      {label}
    </span>
  );
}

export function PortfolioPage({ config }: { config: DemoConfig }) {
  const m = useMemo(() => {
    const rows = EXTRACTED_INSIGHT;
    const filesRead = rows.length;
    const withSignal = rows.filter((r) => r.signals.length > 0).length;
    const complexCount = rows.filter((r) => r.complexity === 'Complex').length;
    const distinctThemes = new Set(rows.map((r) => r.causeTheme)).size;

    const sentOrder: Record<string, number> = { Calm: 0, Concerned: 1, Distressed: 2 };
    const sentCounts = new Map<string, number>();
    rows.forEach((r) => sentCounts.set(r.sentiment, (sentCounts.get(r.sentiment) || 0) + 1));
    const bySentiment = [...sentCounts.entries()]
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => (sentOrder[a.label] ?? 9) - (sentOrder[b.label] ?? 9));

    const cxOrder: Record<string, number> = { Straightforward: 0, Moderate: 1, Complex: 2 };
    const cxCounts = new Map<string, number>();
    rows.forEach((r) => cxCounts.set(r.complexity, (cxCounts.get(r.complexity) || 0) + 1));
    const byComplexity = [...cxCounts.entries()]
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => (cxOrder[a.label] ?? 9) - (cxOrder[b.label] ?? 9));

    return { rows, filesRead, withSignal, complexCount, distinctThemes, bySentiment, byComplexity };
  }, []);

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-6 sm:px-6">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-white" style={{ background: 'linear-gradient(155deg, var(--brand-strong), var(--brand))' }}>
          <Sparkles size={20} />
        </span>
        <div>
          <h1 className="font-display text-xl font-semibold text-ink-900 dark:text-ink-50">From documents to insight</h1>
          <p className="max-w-3xl text-sm text-ink-500">
            ARAG read the {m.filesRead} documented claim files on the desk - each one's First Notice of Loss narrative, adjuster
            report and decision letter - and extracted the cause theme, the claimant's tone, the integrity signals and the
            coverage complexity. None of these exists as a coded field on a claim record; they come only from reading the paperwork.
          </p>
          <p className="mt-2 inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-[11px] font-semibold" style={{ background: 'var(--accent-soft)', color: 'var(--accent-strong)' }}>
            <ScanText size={12} /> Extracted live by ARAG - answer_json_schema over each claim's FNOL, adjuster report and decision letter
          </p>
        </div>
      </div>

      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Claim files read" value={m.filesRead} icon={<FileText size={16} />} />
        <StatTile label="Distinct cause themes" value={m.distinctThemes} icon={<ScanText size={16} />} />
        <StatTile label="Exceptions surfaced" value={m.withSignal} icon={<ShieldAlert size={16} />} />
        <StatTile label="Complex-coverage claims" value={m.complexCount} icon={<Layers size={16} />} />
      </section>

      {/* The hero: the per-claim extracted-fields matrix - the clearest proof of
          "unstructured document in, structured fields out", one row per file ARAG
          read. The coded peril sits beside the extracted cause theme so the finer
          read is obvious (two water-damage claims, one sudden and payable, one
          gradual and excluded). */}
      <section className="rounded-2xl p-4 sm:p-5" style={{ background: 'var(--surface-1)', border: '1px solid var(--hairline)' }}>
        <p className="mb-1 text-sm font-semibold text-ink-800 dark:text-ink-100">What ARAG read out of each file</p>
        <p className="mb-4 text-[12px] text-ink-500">The coded peril is what the record already held; the cause theme, sentiment, integrity signals and complexity are what ARAG extracted by reading.</p>
        <div className="space-y-2.5">
          {m.rows.map((r) => (
            <div key={r.claimNumber} className="grid grid-cols-1 gap-2 rounded-xl p-3 sm:grid-cols-[13rem_1fr] sm:gap-4" style={{ background: 'var(--surface-2)', border: '1px solid var(--hairline)' }}>
              <div className="min-w-0">
                <p className="truncate font-display text-sm font-semibold text-ink-900 dark:text-ink-50">{r.claimant}</p>
                <p className="font-mono text-[11px] text-ink-400">{r.claimNumber}</p>
                <p className="mt-0.5 text-[11px] text-ink-500">Coded peril: <span className="font-medium text-ink-700 dark:text-ink-300">{PERIL_BY_CLAIM[r.claimNumber] || '-'}</span></p>
              </div>
              <div className="min-w-0 space-y-2">
                <p className="text-sm text-ink-800 dark:text-ink-100"><span className="text-[11px] uppercase tracking-wide text-ink-400">Cause theme</span><br />{r.causeTheme}</p>
                <div className="flex flex-wrap items-center gap-1.5">
                  <Chip label={r.sentiment} tone={SENTIMENT_TONE[r.sentiment]} />
                  <Chip label={r.complexity} tone={COMPLEXITY_TONE[r.complexity] || '#64748b'} />
                  {r.signals.length > 0 ? (
                    r.signals.map((s) => <Chip key={s} label={s} tone="#dc2626" />)
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[11px] text-ink-400"><CheckCircle2 size={12} style={{ color: '#16a34a' }} /> No integrity signals</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-2xl p-4 sm:p-5" style={{ background: 'var(--surface-1)', border: '1px solid var(--hairline)' }}>
          <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-semibold text-ink-800 dark:text-ink-100">Claimant sentiment</p>
            <span className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide" style={{ background: 'var(--accent-soft)', color: 'var(--accent-strong)' }}><ScanText size={11} /> Read from the FNOL narratives</span>
          </div>
          <p className="mb-3 text-[12px] text-ink-500">The tone ARAG read in each First Notice of Loss - a distressed total-loss claimant reads very differently from a routine windscreen chip.</p>
          <ShareChart data={m.bySentiment} centerLabel="Files" centerValue={String(m.filesRead)} />
        </div>
        <div className="rounded-2xl p-4 sm:p-5" style={{ background: 'var(--surface-1)', border: '1px solid var(--hairline)' }}>
          <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-semibold text-ink-800 dark:text-ink-100">Coverage complexity</p>
            <span className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide" style={{ background: 'var(--accent-soft)', color: 'var(--accent-strong)' }}><ScanText size={11} /> From the clauses reasoned across</span>
          </div>
          <p className="mb-3 text-[12px] text-ink-500">How many policy clauses ARAG had to reason across to decide the claim - a single covered peril versus a multi-clause exclusion or sub-limit call.</p>
          <BreakdownChart data={m.byComplexity} />
        </div>
      </section>

      <p className="text-[12px] leading-relaxed text-ink-400">
        Scoped to the {m.filesRead} claims with full documentation on the desk - the only claims a real extraction can read. The
        wider seeded book of {PORTFOLIO.length} claims is volume context on the Claims Desk, not charted here as "extracted". No real customer data.
      </p>
      {config ? null : null}
    </div>
  );
}
