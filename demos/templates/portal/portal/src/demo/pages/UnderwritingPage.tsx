import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ClipboardCheck, FileText, ScanLine, ArrowRight, ShieldAlert, Gauge, CheckCircle2, AlertTriangle, XOctagon,
} from 'lucide-react';
import { arag } from '../../palette';
import type { UnderwritingResult } from '../../lib/arag';
import type { DemoConfig } from '../../lib/config';
import { PersonLine } from '../../components/Person';
import { APPLICATIONS, riskRatingTone, recommendedActionTone, type Application } from '../underwriting';

// ─────────────────────────────────────────────────────────────────────────────
// Use case 7 - Underwriting Risk Summary. ARAG reads an application's own
// submitted form, the independent inspection report and the risk-data feed
// summary, and synthesises a structured risk rating, key risk factors and a
// recommended underwriting action via the same working query-time
// answer_json_schema mechanism Claim Intake uses (arag-kb skill), scoped to
// this application's own documents. Every field traces to the source triad;
// nothing is guessed from the product line alone.
// ─────────────────────────────────────────────────────────────────────────────

function ApplicationCard({ app, active, onClick }: { app: Application; active: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group block w-full shrink-0 text-left transition-transform duration-150 hover:-translate-y-0.5 focus:outline-none sm:w-auto sm:flex-1"
      aria-current={active ? 'true' : undefined}
    >
      <div
        className="h-full overflow-hidden rounded-xl p-3.5"
        style={{
          background: 'var(--surface-1)',
          border: active ? '1.5px solid var(--accent)' : '1px solid var(--hairline)',
          boxShadow: active
            ? '0 10px 28px -14px color-mix(in srgb, var(--accent) 60%, transparent)'
            : '0 6px 18px -14px rgba(0,0,0,0.55)',
        }}
      >
        <p className="truncate font-mono text-[11px] font-semibold text-ink-500">{app.applicationNumber}</p>
        <p className="mt-0.5 truncate font-display text-sm font-semibold text-ink-900 dark:text-ink-50">{app.applicant.name}</p>
        <p className="mt-1.5 line-clamp-2 text-[11px] leading-relaxed text-ink-500">{app.summary}</p>
        <span className="mt-2 inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide" style={{ background: 'var(--brand-soft)', color: 'var(--brand)' }}>
          {app.productLine}
        </span>
      </div>
    </button>
  );
}

const ACTION_ICON: Record<string, typeof CheckCircle2> = {
  standard: CheckCircle2,
  loading: AlertTriangle,
  conditions: AlertTriangle,
  refer: XOctagon,
  decline: XOctagon,
};
function actionIcon(action: string | null | undefined) {
  const a = (action || '').toLowerCase();
  if (a.includes('standard')) return ACTION_ICON.standard;
  if (a.includes('refer')) return ACTION_ICON.refer;
  if (a.includes('decline')) return ACTION_ICON.decline;
  return ACTION_ICON.loading;
}

export function UnderwritingPage({ config }: { config: DemoConfig }) {
  const navigate = useNavigate();
  const [activeId, setActiveId] = useState(APPLICATIONS[0].id);
  const active = APPLICATIONS.find((a) => a.id === activeId) || APPLICATIONS[0];
  const [result, setResult] = useState<UnderwritingResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { setResult(null); setError(null); setLoading(false); }, [activeId]);

  const run = () => {
    setLoading(true); setError(null); setResult(null);
    arag.underwritingSummary({ applicationNumber: active.applicationNumber, applicant: active.applicant.name })
      .then(setResult)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  const s = result?.summary;
  const ActionIcon = s ? actionIcon(s.recommendedAction) : null;

  return (
    <div className="mx-auto max-w-5xl space-y-5 px-4 py-6 sm:px-6">
      <div className="flex items-center gap-3">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white" style={{ background: 'linear-gradient(155deg, var(--brand-strong), var(--brand))' }}>
          <ClipboardCheck size={18} />
        </span>
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-400">Underwriting Risk Summary</p>
          <h1 className="font-display text-lg font-semibold text-ink-900 dark:text-ink-50">The underwriter's desk</h1>
        </div>
      </div>

      {/* Application selector - a small, compact desk (three live applications), not the claims queue's full rail. */}
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-400">Applications awaiting underwriting review</p>
        <div className="-mx-4 flex snap-x gap-3 overflow-x-auto px-4 pb-1 sm:mx-0 sm:grid sm:grid-cols-3 sm:gap-3 sm:overflow-visible sm:px-0">
          {APPLICATIONS.map((a) => (
            <div key={a.id} className="w-64 shrink-0 snap-start sm:w-auto">
              <ApplicationCard app={a} active={a.id === activeId} onClick={() => setActiveId(a.id)} />
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-2xl p-4 sm:p-5" style={{ background: 'var(--surface-1)', border: '1px solid var(--hairline)' }}>
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white" style={{ background: 'linear-gradient(155deg, var(--brand-strong), var(--brand))' }}>
            <Gauge size={18} />
          </span>
          <div className="min-w-0">
            <p className="font-display text-base font-semibold text-ink-900 dark:text-ink-50">Synthesise the risk summary</p>
            <p className="mt-0.5 text-sm text-ink-500">
              ARAG reads {active.applicant.name}'s application form, the independent inspection report and the risk-data
              feed summary for {active.applicationNumber}, and synthesises a risk rating, the specific risk factors and a
              recommended underwriting action - grounded only in those three documents, never guessed from the product
              line alone.
            </p>
          </div>
        </div>
        <button type="button" onClick={run} disabled={loading} className="btn btn-primary mt-4">
          <ScanLine size={15} /> {loading ? 'Synthesising the risk summary…' : `Synthesise risk summary for ${active.applicationNumber}`}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Left: the unstructured triad being read. */}
        <div className="rounded-2xl p-4 sm:p-5" style={{ background: 'var(--surface-1)', border: '1px solid var(--hairline)' }}>
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-400">Read from</p>
          <div className="space-y-2.5">
            {[
              `Underwriting Application - ${active.applicationNumber}`,
              `Inspection Report - ${active.applicationNumber}`,
              `Risk Data Summary - ${active.applicationNumber}`,
            ].map((label) => (
              <div key={label} className="flex items-center gap-3 rounded-xl px-3 py-2.5" style={{ background: 'var(--surface-2)', border: '1px solid var(--hairline)' }}>
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg" style={{ background: 'var(--brand-soft)', color: 'var(--brand)' }}>
                  <FileText size={15} />
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-ink-800 dark:text-ink-100">{label}</p>
                  <p className="truncate text-[11px] text-ink-400"><PersonLine name={active.applicant.name} role={active.applicant.role} /> &middot; {active.productLine}</p>
                </div>
                {loading && <ScanLine size={15} className="ml-auto shrink-0 animate-pulse" style={{ color: 'var(--accent)' }} />}
              </div>
            ))}
          </div>
          <p className="mt-3 text-[11px] leading-relaxed text-ink-400">
            The application form, an independent inspection and Publisher's risk-data feed - three separate sources
            ARAG reads together into the summary on the right.
          </p>
        </div>

        {/* Right: the structured risk summary (generative UI). */}
        <div className="rounded-2xl p-4 sm:p-5" style={{ background: 'var(--surface-1)', border: '1px solid var(--hairline)' }}>
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-400">Risk summary</p>

          {error && <p className="rounded-lg px-3 py-2 text-sm" style={{ background: 'color-mix(in srgb, #dc2626 12%, transparent)', color: '#dc2626' }}>{error}</p>}

          {!result && !loading && !error && (
            <div className="flex flex-col items-center justify-center rounded-xl py-10 text-center" style={{ background: 'var(--surface-2)' }}>
              <ShieldAlert size={22} className="text-ink-300" />
              <p className="mt-2 max-w-xs text-sm text-ink-500">Run the synthesis to turn the application triad into a risk rating and a recommended action.</p>
            </div>
          )}

          {loading && (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-9 animate-pulse rounded-lg" style={{ background: 'var(--surface-2)' }} />
              ))}
            </div>
          )}

          {s && (
            <>
              <div className="flex flex-wrap items-center gap-2.5">
                <span
                  className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-semibold"
                  style={{ color: riskRatingTone(s.overallRiskRating), background: `color-mix(in srgb, ${riskRatingTone(s.overallRiskRating)} 14%, transparent)`, border: `1px solid color-mix(in srgb, ${riskRatingTone(s.overallRiskRating)} 40%, transparent)` }}
                >
                  <Gauge size={15} /> {s.overallRiskRating || 'Unrated'} risk
                </span>
                {ActionIcon && (
                  <span
                    className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-semibold"
                    style={{ color: recommendedActionTone(s.recommendedAction), background: `color-mix(in srgb, ${recommendedActionTone(s.recommendedAction)} 14%, transparent)`, border: `1px solid color-mix(in srgb, ${recommendedActionTone(s.recommendedAction)} 40%, transparent)` }}
                  >
                    <ActionIcon size={15} /> {s.recommendedAction || 'Not stated'}
                  </span>
                )}
              </div>

              {s.keyRiskFactors.length > 0 && (
                <div className="mt-3">
                  <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-ink-400">Key risk factors</p>
                  <div className="flex flex-wrap gap-2">
                    {s.keyRiskFactors.map((f, i) => (
                      <span key={i} className="inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium" style={{ background: 'var(--surface-2)', color: 'var(--ink-700, #334155)', border: '1px solid var(--hairline)' }}>
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {s.rationale && (
                <p className="mt-3 text-sm leading-relaxed text-ink-700 dark:text-ink-200">{s.rationale}</p>
              )}

              {result && result.sources.length > 0 && (
                <div className="mt-3">
                  <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-ink-400">Synthesised from</p>
                  <div className="flex flex-wrap gap-2">
                    {result.sources.map((src) => (
                      <button key={src.resourceId} type="button" onClick={() => navigate(`/r/${src.resourceId}`)} className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition hover:brightness-95" style={{ background: 'var(--brand-soft)', color: 'var(--brand)' }}>
                        <FileText size={12} /> {src.title} <ArrowRight size={11} />
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {result && !result.grounded && (
            <p className="mt-3 rounded-lg px-3 py-2 text-[12px]" style={{ background: 'color-mix(in srgb, #d97706 14%, transparent)', color: '#b45309' }}>
              ARAG returned no grounded risk summary for this application - it did not invent a rating. Check the
              application, inspection and risk data are all in the file.
            </p>
          )}
        </div>
      </div>
      {config ? null : null}
    </div>
  );
}
