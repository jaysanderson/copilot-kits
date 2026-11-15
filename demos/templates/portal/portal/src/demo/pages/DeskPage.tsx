import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FolderOpen, Gavel, Timer, ShieldCheck, ArrowRight, Sparkles, ChevronRight,
} from 'lucide-react';
import { StatTile } from '../../palette';
import type { DemoConfig } from '../../lib/config';
import {
  CLAIMS, PORTFOLIO, formatMoney, lowestScore, useClaimsDesk, type Claim,
} from '../store';
import { ClaimCard } from '../ui';

// ─────────────────────────────────────────────────────────────────────────────
// Use case landing - the Claims Desk (route "/"). The whole book of work on one
// screen: the priority claims that need a decision now, the desk's live KPIs
// computed from the seeded portfolio (never a hand-typed headline number), the
// claims book as the tactile hero object (Standard B8 - the content is the
// hero), and the recent trust-scored decisions. Desk-level: full width, no
// queue pane. Manual throughout (Standard B15) - nothing auto-advances.
// ─────────────────────────────────────────────────────────────────────────────

const NEEDS_DECISION = new Set(['Needs more info', 'Awaiting decision', 'Under investigation']);

export function DeskPage({ config }: { config: DemoConfig }) {
  const navigate = useNavigate();
  const { setActiveClaim, log } = useClaimsDesk();

  const kpis = useMemo(() => {
    const open = PORTFOLIO.filter((r) => r.status !== 'Payable' && r.status !== 'Fast-tracked').length;
    const needDecision = PORTFOLIO.filter((r) => NEEDS_DECISION.has(r.status)).length;
    const settled = PORTFOLIO.filter((r) => r.cycleTimeDays > 0);
    const avgCycle = settled.length ? Math.round(settled.reduce((s, r) => s + r.cycleTimeDays, 0) / settled.length) : 0;
    const exposure = PORTFOLIO.filter((r) => r.status !== 'Payable' && r.status !== 'Fast-tracked')
      .reduce((s, r) => s + r.amount, 0);
    return { open, needDecision, avgCycle, exposure };
  }, []);

  // Priority queue - the claims a handler actually has to move today, hardest first.
  const priority = useMemo(
    () => CLAIMS.filter((c) => NEEDS_DECISION.has(c.status)).concat(CLAIMS.filter((c) => !NEEDS_DECISION.has(c.status))),
    [],
  );
  const topClaim = priority[0];

  const openClaim = (claim: Claim, route = '/coverage') => { setActiveClaim(claim.id); navigate(route); };
  const recent = log.slice(0, 4);

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-6 sm:px-6">
      {/* Hero - narrative hook + honest grounding line + a primary CTA. */}
      <section
        className="relative overflow-hidden rounded-3xl p-6 text-white sm:p-8"
        style={{ background: 'linear-gradient(150deg, var(--brand-strong), color-mix(in srgb, var(--brand) 85%, black))', boxShadow: '0 26px 60px -30px rgba(0,0,0,0.75)' }}
      >
        <div className="relative z-10 max-w-2xl">
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-white/60">Publisher Mutual &middot; Claims Desk</p>
          <h1 className="mt-2 font-display text-2xl font-semibold leading-tight sm:text-[2rem]">
            Every claim read, cited and trust-scored before a cheque goes out.
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-white/75">
            {config.elevatorPitch || 'Open a claim and its documents are read into structured fields, the coverage question is answered against the actual policy wording with the clause cited, and the payable call carries a live trust score.'}
          </p>
          <p className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-white/10 px-3 py-1.5 text-[12px] font-medium text-white/85">
            <ShieldCheck size={14} /> Real synthetic claim files - every answer is retrieved from these documents, never invented.
          </p>
          <div className="mt-5 flex flex-wrap gap-2.5">
            {topClaim && (
              <button type="button" onClick={() => openClaim(topClaim)} className="btn btn-primary">
                Work the priority claim <ArrowRight size={15} />
              </button>
            )}
            <button type="button" onClick={() => navigate('/reports')} className="inline-flex items-center gap-1.5 rounded-lg border border-white/25 bg-white/5 px-3.5 py-2 text-sm font-medium text-white transition hover:bg-white/12">
              See the portfolio
            </button>
          </div>
        </div>
      </section>

      {/* Live KPIs - computed from the seeded portfolio, no hand-typed number. */}
      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Open claims" value={kpis.open} icon={<FolderOpen size={16} />} />
        <StatTile label="Awaiting a decision" value={kpis.needDecision} icon={<Gavel size={16} />} />
        <StatTile label="Avg cycle time" value={kpis.avgCycle} format={(v) => `${v} days`} icon={<Timer size={16} />} />
        <StatTile label="Open exposure" value={kpis.exposure} format={formatMoney} icon={<ShieldCheck size={16} />} />
      </section>

      {/* The claims book - the tactile hero object (Standard B8). */}
      <section>
        <div className="mb-3 flex items-end justify-between">
          <div>
            <h2 className="font-display text-lg font-semibold text-ink-900 dark:text-ink-50">The claims book</h2>
            <p className="text-sm text-ink-500">Open a claim to read its file, answer coverage, decide and check for exceptions.</p>
          </div>
          <span className="hidden rounded-md px-2 py-1 text-xs font-semibold text-ink-500 sm:inline" style={{ background: 'var(--surface-2)' }}>{CLAIMS.length} live files</span>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {priority.map((c) => (
            <ClaimCard key={c.id} claim={c} onClick={() => openClaim(c)} />
          ))}
        </div>
      </section>

      {/* Recent trust-scored decisions - real texture from the log. */}
      {recent.length > 0 && (
        <section className="rounded-2xl p-5" style={{ background: 'var(--surface-1)', border: '1px solid var(--hairline)' }}>
          <div className="mb-3 flex items-center gap-2">
            <Sparkles size={15} style={{ color: 'var(--accent)' }} />
            <h2 className="font-display text-base font-semibold text-ink-900 dark:text-ink-50">Recent grounded decisions</h2>
          </div>
          <ul className="divide-y" style={{ borderColor: 'var(--hairline)' }}>
            {recent.map((e) => {
              const low = lowestScore(e.remi);
              const tone = low == null ? '#64748b' : low >= 4.5 ? '#16a34a' : low >= 3.5 ? '#d97706' : '#dc2626';
              return (
                <li key={e.id} className="flex items-center gap-3 py-2.5">
                  <span className="font-mono text-[11px] text-ink-400">{e.claimNumber}</span>
                  <span className="min-w-0 flex-1 truncate text-sm text-ink-700 dark:text-ink-200">{e.answer}</span>
                  {low != null && (
                    <span className="inline-flex shrink-0 items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-semibold" style={{ color: tone, background: `color-mix(in srgb, ${tone} 14%, transparent)` }}>
                      REMi {low.toFixed(1)}
                    </span>
                  )}
                  <span className="hidden text-[11px] uppercase tracking-wide text-ink-400 sm:inline">{e.route}</span>
                  <ChevronRight size={14} className="shrink-0 text-ink-300" />
                </li>
              );
            })}
          </ul>
        </section>
      )}
    </div>
  );
}
