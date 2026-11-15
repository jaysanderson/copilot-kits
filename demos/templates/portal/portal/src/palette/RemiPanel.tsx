import { useEffect, useRef, useState } from 'react';
import { ShieldCheck, ShieldAlert, Loader2 } from 'lucide-react';
import type { RemiState } from './hooks';
import { usePrefersReducedMotion } from '../lib/motion';
// Kendo-free by design — same reasoning as CitedMetric: the trust layer must
// render identically in both UI modes and never depend on a commercial
// component library.

// ─────────────────────────────────────────────────────────────────────────────
// RemiPanel — module 4.1, the flagship trust panel.
//
// Renders the REAL RAG-triad score from POST {kb}/predict/remi via useRemi() —
// groundedness, answer relevance, context relevance, each 0-5 — and, like
// <CitedMetric>, is structurally incapable of showing a hand-typed number: it
// only ever renders what the hook's live API response actually returned.
//
// Steve Jobs review, 17 Aug 2026 — "make REMi an EVENT, beside the answer":
// the rings now DRAW (the arc sweeps in) and COUNT UP (0.0 -> the real score)
// the moment the panel mounts, i.e. the instant the answer lands. The `rail`
// variant is a tall, narrow trust card that sits directly under the citations
// in the answer's own right rail, so answer + sources + score read as ONE
// tight payoff instead of a static trio a full scroll below in a dead column.
//
// `threshold` (module spec: "optional reject-below-threshold mode", off by
// default, on for the Quality Desk archetype): when set, an answer whose
// LOWEST of the three scores falls below it renders as a withheld/rejected
// state instead of the scores — umbraco-arag-perso's proven pattern.
// ─────────────────────────────────────────────────────────────────────────────
export function RemiPanel({
  remi,
  threshold = null,
  compact = false,
  variant = 'panel',
}: {
  remi: RemiState;
  /** 0-5. When set, the lowest of the three scores below this withholds the answer outright. */
  threshold?: number | null;
  compact?: boolean;
  /** `rail` = a tall, narrow trust card for the answer's own right rail (the money-shot layout). */
  variant?: 'panel' | 'rail';
}) {
  if (remi.loading) {
    return (
      <div className={variant === 'rail'
        ? 'card ring-hairline flex items-center gap-2 p-4 text-xs text-ink-500'
        : 'card card-flat flex items-center gap-2 p-3 text-xs text-ink-500'}>
        <Loader2 size={14} className="animate-spin" style={{ color: 'var(--brand)' }} />
        Scoring this answer with REMi…
      </div>
    );
  }
  if (remi.error) {
    return (
      <div className="card card-flat p-3 text-xs text-red-600 dark:text-red-400">
        REMi scoring failed: {remi.error}
      </div>
    );
  }
  if (!remi.score) return null;

  const { groundedness, answerRelevance, contextRelevance } = remi.score;
  const values = [groundedness, answerRelevance, contextRelevance].filter(
    (v): v is number => typeof v === 'number'
  );
  const lowest = values.length ? Math.min(...values) : null;
  const rejected = threshold != null && lowest != null && lowest < threshold;

  if (rejected) {
    return (
      <div className="flex items-start gap-3 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900 dark:border-red-800/70 dark:bg-red-950/40 dark:text-red-200">
        <ShieldAlert size={18} className="mt-0.5 shrink-0" />
        <div>
          <p className="font-semibold">Answer withheld - below the REMi quality threshold.</p>
          <p className="mt-0.5 text-red-800 dark:text-red-300/90">
            Lowest score {lowest?.toFixed(1)}/5, threshold {threshold}/5. The Quality Desk pattern:
            a low-trust answer is never shown as if it were reliable - it is rejected outright, not
            just labelled.
          </p>
        </div>
      </div>
    );
  }

  const metrics: { key: string; label: string; value: number | null }[] = [
    { key: 'groundedness', label: 'Groundedness', value: groundedness },
    { key: 'answerRelevance', label: 'Answer relevance', value: answerRelevance },
    { key: 'contextRelevance', label: 'Context relevance', value: contextRelevance },
  ];

  // ── rail variant: the money-shot trust card, in the answer's own right rail ──
  if (variant === 'rail') {
    const overall = lowest;
    const tone = overall == null ? '#94a3b8' : overall >= 4 ? '#16a34a' : overall >= 2.5 ? '#d97706' : '#dc2626';
    return (
      <div className="card ring-hairline overflow-hidden animate-fade-up">
        <div className="flex items-center gap-2 border-b px-4 py-3" style={{ borderColor: 'var(--hairline)' }}>
          <ShieldCheck size={15} style={{ color: 'var(--brand)' }} />
          <span className="text-xs font-semibold uppercase tracking-wide text-ink-600 dark:text-ink-300">REMi trust score</span>
          {overall != null && (
            <span className="ml-auto rounded-md px-2 py-0.5 text-xs font-bold tabular-nums" style={{ color: tone, background: `color-mix(in srgb, ${tone} 14%, transparent)` }}>
              {overall.toFixed(1)}/5
            </span>
          )}
        </div>
        <div className="space-y-3 p-4">
          {metrics.map((m, i) => (
            <RemiMetricRow key={m.key} label={m.label} value={m.value} delay={i * 140} />
          ))}
        </div>
        {remi.score.answerRelevanceReason && (
          <p className="border-t px-4 py-3 text-xs leading-relaxed text-ink-500" style={{ borderColor: 'var(--hairline)' }} title="REMi's own scoring rationale">
            {remi.score.answerRelevanceReason}
          </p>
        )}
      </div>
    );
  }

  // ── default panel / compact ──
  return (
    <div className={compact ? 'flex flex-wrap items-center gap-3' : 'card p-4'}>
      {!compact && (
        <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-ink-500">
          <ShieldCheck size={14} style={{ color: 'var(--brand)' }} />
          REMi trust score
        </div>
      )}
      <div className={compact ? 'flex flex-wrap gap-3' : 'grid grid-cols-3 gap-3'}>
        {metrics.map((m, i) => (
          <RemiScoreTile key={m.key} label={m.label} value={m.value} delay={i * 140} />
        ))}
      </div>
      {remi.score.answerRelevanceReason && !compact && (
        <p className="mt-3 text-xs text-ink-500" title="REMi's own scoring rationale">
          {remi.score.answerRelevanceReason}
        </p>
      )}
    </div>
  );
}

// Eased draw + count-up for a REMi value, gated on reduced-motion. Returns the
// live displayed value (0..value) so both the arc and the number animate in
// lockstep the instant the ring mounts (i.e. the moment the answer lands).
function useDraw(value: number | null, delay = 0, duration = 900): number {
  const reduced = usePrefersReducedMotion();
  const [shown, setShown] = useState(reduced ? value ?? 0 : 0);
  const raf = useRef(0);
  useEffect(() => {
    if (value == null) { setShown(0); return; }
    if (reduced) { setShown(value); return; }
    let start = 0;
    let stopped = false;
    const tick = (t: number) => {
      if (!start) start = t + delay;
      if (t < start) { raf.current = requestAnimationFrame(tick); return; }
      const k = Math.min((t - start) / duration, 1);
      const eased = 1 - Math.pow(1 - k, 3);
      setShown(value * eased);
      if (k < 1 && !stopped) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    // Safety floor: if requestAnimationFrame is throttled (a backgrounded tab)
    // and never completes the draw, guarantee the real value still lands so the
    // rings can never read a misleading mid-draw number. On a focused demo RAF
    // finishes first and this is a harmless no-op.
    const settle = setTimeout(() => { if (!stopped) setShown(value); }, delay + duration + 400);
    return () => { stopped = true; cancelAnimationFrame(raf.current); clearTimeout(settle); };
  }, [value, delay, duration, reduced]);
  return shown;
}

function ringTone(value: number | null): string {
  return value == null ? '#94a3b8' : value >= 4 ? '#16a34a' : value >= 2.5 ? '#d97706' : '#dc2626';
}

function AnimatedRing({ value, size, shown }: { value: number | null; size: number; shown: number }) {
  const r = 15.5;
  const circ = 2 * Math.PI * r;
  const pct = value == null ? 0 : Math.max(0, Math.min(100, (shown / 5) * 100));
  const tone = ringTone(value);
  return (
    <div className="relative shrink-0" style={{ height: size, width: size }}>
      <svg viewBox="0 0 36 36" className="-rotate-90" style={{ height: size, width: size }}>
        <circle cx="18" cy="18" r={r} fill="none" stroke="var(--hairline)" strokeWidth="3.2" />
        <circle
          cx="18" cy="18" r={r} fill="none" stroke={tone} strokeWidth="3.2" strokeLinecap="round"
          strokeDasharray={`${(pct / 100) * circ} ${circ}`}
        />
      </svg>
      {/* Standard: the NUMBER shows the settled score immediately - never a
          misleading low count-up frame (e.g. 0.1 flashing on a correct 5/5/5
          answer, which breaks the trust beat, GM review 18 Aug 2026). Only the
          ARC sweeps in (pct is driven by `shown`); the figure is always real. */}
      <span className="absolute inset-0 flex items-center justify-center text-xs font-bold tabular-nums text-ink-800 dark:text-ink-100">
        {value == null ? '-' : value.toFixed(1)}
      </span>
    </div>
  );
}

function RemiMetricRow({ label, value, delay }: { label: string; value: number | null; delay: number }) {
  const shown = useDraw(value, delay);
  return (
    <div className="flex items-center gap-3">
      <AnimatedRing value={value} size={42} shown={shown} />
      <div className="min-w-0">
        <p className="text-sm font-medium text-ink-800 dark:text-ink-100">{label}</p>
        <p className="text-[10px] uppercase tracking-wide text-ink-400" title="Scored server-side on the retrieved context">Scored on retrieved context</p>
      </div>
    </div>
  );
}

function RemiScoreTile({ label, value, delay }: { label: string; value: number | null; delay: number }) {
  const shown = useDraw(value, delay);
  return (
    <div className="flex flex-col items-center gap-1 rounded-lg border px-3 py-2 text-center" style={{ borderColor: 'var(--hairline)' }}>
      <AnimatedRing value={value} size={48} shown={shown} />
      <span className="text-[10px] uppercase tracking-wide text-ink-500">{label}</span>
      <span className="text-[9px] text-ink-400" title="Scored server-side on the retrieved context">
        Scored on retrieved context
      </span>
    </div>
  );
}
