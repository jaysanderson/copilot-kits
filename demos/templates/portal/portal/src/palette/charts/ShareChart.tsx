import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { categoricalPalette, chartChrome } from './tokens';
import { ChartTooltip, ChartLegend } from './TrendChart';

export interface ShareRow {
  label: string;
  value: number;
}

export interface ShareChartProps {
  data: ShareRow[];
  height?: number;
  /** Centre figure — the one place a donut earns its keep over a bar: a single headline total/percentage. */
  centerLabel?: string;
  centerValue?: string;
}

/**
 * A donut — used sparingly (a single "share of total" headline with a centre
 * figure), never for precise multi-category comparison; use BreakdownChart
 * for that. Always paired with a legend so identity never rests on hue alone.
 */
export function ShareChart({ data, height = 220, centerLabel, centerValue }: ShareChartProps) {
  const colors = categoricalPalette(data.length);
  const chrome = chartChrome();
  const total = data.reduce((s, d) => s + d.value, 0);

  return (
    <div className="relative" style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="label"
            innerRadius="62%"
            outerRadius="88%"
            paddingAngle={2}
            stroke="var(--surface-1)"
            strokeWidth={2}
            isAnimationActive={false}
          >
            {data.map((_, i) => <Cell key={i} fill={colors[i]} />)}
          </Pie>
          <Tooltip content={<ChartTooltip format={(v: number) => `${v} (${Math.round((v / (total || 1)) * 100)}%)`} />} />
        </PieChart>
      </ResponsiveContainer>
      {(centerValue || centerLabel) && (
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          {centerValue && <span className="font-display text-2xl font-semibold text-ink-900 dark:text-ink-50">{centerValue}</span>}
          {centerLabel && <span className="text-[11px] uppercase tracking-wide text-ink-400">{centerLabel}</span>}
        </div>
      )}
      <ChartLegend payload={data.map((d, i) => ({ value: d.label, color: colors[i] }))} />
      <style>{`.recharts-wrapper svg { color: ${chrome.ink}; }`}</style>
    </div>
  );
}
