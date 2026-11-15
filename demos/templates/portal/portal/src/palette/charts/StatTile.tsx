import type { ReactNode } from 'react';
import { ResponsiveContainer, AreaChart, Area } from 'recharts';
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';
import { useCountUp } from '../../lib/motion';
import { brandColor, statusPalette } from './tokens';

export interface StatTileProps {
  label: string;
  /** The metric value — always a number the caller computed from real data, never invented (same discipline as CitedMetric). */
  value: number;
  /** Formats the count-up value for display, e.g. (v) => `${v}%`. */
  format?: (v: number) => string;
  /** Optional trend vs. a prior period. Sign decides the icon + status colour — never colour alone. */
  delta?: { value: number; label: string; goodDirection?: 'up' | 'down' };
  /** Optional sparkline series (recent values, oldest→newest). */
  spark?: number[];
  icon?: ReactNode;
}

/** A single KPI figure with count-up, an honestly-signed trend, and an optional sparkline. Composes into a TileGrid/DashboardGrid. */
export function StatTile({ label, value, format = (v) => String(v), delta, spark, icon }: StatTileProps) {
  const animated = useCountUp(value);
  const status = statusPalette();
  const goodDirection = delta?.goodDirection ?? 'up';
  const positive = delta ? (goodDirection === 'up' ? delta.value >= 0 : delta.value <= 0) : null;
  const DeltaIcon = !delta ? null : delta.value === 0 ? Minus : delta.value > 0 ? ArrowUpRight : ArrowDownRight;
  const deltaColor = delta == null ? undefined : delta.value === 0 ? 'var(--ink-400, #9ba0b8)' : positive ? status.good : status.critical;

  return (
    <div className="card relative overflow-hidden p-4">
      <div className="flex items-start justify-between gap-2">
        <p className="text-eyebrow uppercase text-ink-400">{label}</p>
        {icon && <span style={{ color: 'var(--brand)' }}>{icon}</span>}
      </div>
      <p className="mt-1.5 font-display text-[1.85rem] font-semibold tabular-nums leading-none text-ink-900 dark:text-ink-50">
        {format(animated)}
      </p>
      <div className="mt-2 flex items-center justify-between gap-2">
        {delta ? (
          <span className="inline-flex items-center gap-1 text-xs font-semibold" style={{ color: deltaColor }}>
            {DeltaIcon && <DeltaIcon size={13} />}
            {delta.value > 0 ? '+' : ''}{delta.value}% <span className="font-normal text-ink-400">{delta.label}</span>
          </span>
        ) : <span />}
        {spark && spark.length > 1 && (
          <div className="h-8 w-20 shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={spark.map((v, i) => ({ i, v }))} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
                <defs>
                  <linearGradient id="statTileFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={brandColor()} stopOpacity={0.35} />
                    <stop offset="100%" stopColor={brandColor()} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Area type="monotone" dataKey="v" stroke={brandColor()} strokeWidth={2} fill="url(#statTileFill)" isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
