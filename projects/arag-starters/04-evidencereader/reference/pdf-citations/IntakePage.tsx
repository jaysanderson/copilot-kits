import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileInput, FileText, ScanLine, CheckCircle2, ArrowRight } from 'lucide-react';
import { arag } from '../../palette';
import type { ExtractResult } from '../../lib/arag';
import type { DemoConfig } from '../../lib/config';
import { useClaimsDesk } from '../store';
import { ClaimWorkbench } from '../ui';

// ─────────────────────────────────────────────────────────────────────────────
// Use case 1 - Claim Intake. The submitted paperwork (a First Notice of Loss, a
// policy schedule) read into structured intake fields by ARAG's query-time
// answer_json_schema path (the working structured-JSON mechanism, NOT the broken
// ingest-time Generator task - see the architecture reveal for this route). The
// handler sees the unstructured documents on the left turning into clean, typed
// fields on the right - extracted, never re-keyed. Each source document is
// clickable through to its own page (table-stakes gate 4).
// ─────────────────────────────────────────────────────────────────────────────

export function IntakePage({ config }: { config: DemoConfig }) {
  const navigate = useNavigate();
  const { activeClaim } = useClaimsDesk();
  const [result, setResult] = useState<ExtractResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fresh extraction whenever the active claim changes.
  useEffect(() => { setResult(null); setError(null); setLoading(false); }, [activeClaim.id]);

  const run = () => {
    setLoading(true); setError(null); setResult(null);
    arag.extractClaim({ claimNumber: activeClaim.claimNumber, claimant: activeClaim.claimant.name })
      .then(setResult)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  return (
    <ClaimWorkbench kicker="Claim Intake">
      <div className="rounded-2xl p-4 sm:p-5" style={{ background: 'var(--surface-1)', border: '1px solid var(--hairline)' }}>
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white" style={{ background: 'linear-gradient(155deg, var(--brand-strong), var(--brand))' }}>
            <FileInput size={18} />
          </span>
          <div className="min-w-0">
            <p className="font-display text-base font-semibold text-ink-900 dark:text-ink-50">Read the claim into structured fields</p>
            <p className="mt-0.5 text-sm text-ink-500">
              ARAG reads this claim's own First Notice of Loss and policy schedule and returns clean, typed intake fields -
              extracted from the paperwork, not re-keyed by a handler. Every value traces back to the source document.
            </p>
          </div>
        </div>
        <button type="button" onClick={run} disabled={loading} className="btn btn-primary mt-4">
          <ScanLine size={15} /> {loading ? 'Reading the documents…' : `Read the documents for ${activeClaim.claimNumber}`}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Left: the unstructured documents being read. */}
        <div className="rounded-2xl p-4 sm:p-5" style={{ background: 'var(--surface-1)', border: '1px solid var(--hairline)' }}>
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-400">Submitted documents</p>
          <div className="space-y-2.5">
            {[`First Notice of Loss - ${activeClaim.claimNumber}`, `Policy schedule - ${activeClaim.policyNumber}`].map((label) => (
              <div key={label} className="flex items-center gap-3 rounded-xl px-3 py-2.5" style={{ background: 'var(--surface-2)', border: '1px solid var(--hairline)' }}>
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg" style={{ background: 'var(--brand-soft)', color: 'var(--brand)' }}>
                  <FileText size={15} />
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-ink-800 dark:text-ink-100">{label}</p>
                  <p className="text-[11px] text-ink-400">{activeClaim.claimant.name} &middot; {activeClaim.productLine}</p>
                </div>
                {loading && <ScanLine size={15} className="ml-auto shrink-0 animate-pulse" style={{ color: 'var(--accent)' }} />}
              </div>
            ))}
          </div>
          <p className="mt-3 text-[11px] leading-relaxed text-ink-400">
            Unstructured PDFs a claimant submits. ARAG extracts the fields on the right against them.
          </p>
        </div>

        {/* Right: the structured intake fields (generative UI). */}
        <div className="rounded-2xl p-4 sm:p-5" style={{ background: 'var(--surface-1)', border: '1px solid var(--hairline)' }}>
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-400">Extracted intake fields</p>

          {error && <p className="rounded-lg px-3 py-2 text-sm" style={{ background: 'color-mix(in srgb, #dc2626 12%, transparent)', color: '#dc2626' }}>{error}</p>}

          {!result && !loading && !error && (
            <div className="flex flex-col items-center justify-center rounded-xl py-10 text-center" style={{ background: 'var(--surface-2)' }}>
              <ScanLine size={22} className="text-ink-300" />
              <p className="mt-2 max-w-xs text-sm text-ink-500">Run the read to turn the paperwork into structured claim fields.</p>
            </div>
          )}

          {loading && (
            <div className="space-y-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-9 animate-pulse rounded-lg" style={{ background: 'var(--surface-2)' }} />
              ))}
            </div>
          )}

          {result && (
            <>
              <dl className="grid grid-cols-1 gap-px overflow-hidden rounded-xl" style={{ background: 'var(--hairline)', border: '1px solid var(--hairline)' }}>
                {result.fields.map((f) => {
                  const stated = f.value != null && String(f.value).toLowerCase() !== 'not stated';
                  return (
                    <div key={f.key} className="flex items-baseline gap-3 px-3 py-2" style={{ background: 'var(--surface-1)' }}>
                      <dt className="w-32 shrink-0 text-[11px] font-semibold uppercase tracking-wide text-ink-400">{f.label}</dt>
                      <dd className={`min-w-0 flex-1 text-sm ${stated ? 'font-medium text-ink-900 dark:text-ink-50' : 'italic text-ink-400'}`}>
                        {stated ? String(f.value) : 'not stated'}
                        {stated && <CheckCircle2 size={12} className="ml-1.5 inline shrink-0" style={{ color: '#16a34a' }} />}
                      </dd>
                    </div>
                  );
                })}
              </dl>
              {result.sources.length > 0 && (
                <div className="mt-3">
                  <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-ink-400">Read from</p>
                  <div className="flex flex-wrap gap-2">
                    {result.sources.map((s) => (
                      <button key={s.resourceId} type="button" onClick={() => navigate(`/r/${s.resourceId}`)} className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition hover:brightness-95" style={{ background: 'var(--brand-soft)', color: 'var(--brand)' }}>
                        <FileText size={12} /> {s.title} <ArrowRight size={11} />
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {!result.grounded && (
                <p className="mt-3 rounded-lg px-3 py-2 text-[12px]" style={{ background: 'color-mix(in srgb, #d97706 14%, transparent)', color: '#b45309' }}>
                  ARAG returned no grounded values for this claim - it did not invent fields. Check the documents are in the file.
                </p>
              )}
            </>
          )}
        </div>
      </div>
      {config ? null : null}
    </ClaimWorkbench>
  );
}
