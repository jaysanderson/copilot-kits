import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts';
import { categoricalPalette, chartChrome } from './tokens';

export interface TrendSeries {
  key: string;
  label: string;
}

export interface TrendChartProps {
  /** One row per x-value, e.g. `{ x: 'Mon', calls: 12, escalations: 2 }`. */
  data: Record<string, number | string>[];
  series: TrendSeries[];
  xKey?: string;
  height?: number;
  /** Formats the y-axis / tooltip values, e.g. (v) => `${v}%`. */
  format?: (v: number) => string;
}

// Minimum vertical gap (px) enforced between two end-of-line labels so two
// series that converge to nearly the same value (a REMi trend stabilised at
// 5/5/5 is the common case in this app) never render their labels stacked on
// top of each other at the line ends - the exact "legend/key overlapping,
// series labels colliding" defect (GM correction, 17 Aug 2026).
const LABEL_MIN_GAP = 13;

/**
 * A single-axis trend line (never dual-axis — two measures of different scale
 * get two charts, not two y-scales). A legend renders for 2+ series; up to 4
 * also get a direct end-label so identity never rests on colour alone. End
 * labels are collision-resolved against each other (see LABEL_MIN_GAP) - a
 * naive per-line label at the raw data y-position is what collided when
 * series values converge.
 */
export function TrendChart({ data, series, xKey = 'x', height = 220, format = (v) => String(v) }: TrendChartProps) {
  const colors = categoricalPalette(series.length);
  const chrome = chartChrome();
  const directLabels = series.length > 1 && series.length <= 4;
  // Reset fresh each render; recharts invokes each Line's `label` callback
  // synchronously, in series order, during this same render pass, so a
  // plain array closed over by every callback below is a safe, simple way
  // to track which vertical slots are already taken.
  const takenY: number[] = [];

  const placeLabel = (y: number): number => {
    let placed = y;
    // Push down until clear of every already-placed label this render.
    let guard = 0;
    while (takenY.some((t) => Math.abs(t - placed) < LABEL_MIN_GAP) && guard < 20) {
      placed += LABEL_MIN_GAP;
      guard += 1;
    }
    takenY.push(placed);
    return placed;
  };

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: directLabels ? 64 : 16, bottom: 0, left: 0 }}>
          <CartesianGrid stroke={chrome.grid} vertical={false} />
          <XAxis
            dataKey={xKey}
            tick={{ fill: chrome.inkMuted, fontSize: 11 }}
            axisLine={{ stroke: chrome.grid }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: chrome.inkMuted, fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={36}
            tickFormatter={(v) => format(Number(v))}
          />
          <Tooltip content={<ChartTooltip format={format} />} cursor={{ stroke: chrome.grid, strokeWidth: 1 }} />
          {series.length > 1 && <Legend content={<ChartLegend />} />}
          {series.map((s, i) => (
            <Line
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.label}
              stroke={colors[i]}
              strokeWidth={2}
              dot={data.length <= 14 ? { r: 3, fill: colors[i], strokeWidth: 0 } : false}
              activeDot={{ r: 5 }}
              isAnimationActive={false}
              label={directLabels ? (props: any) => {
                if (props.index !== data.length - 1) return <g />;
                const y = placeLabel(props.y + 4);
                return (
                  <text x={props.x + 8} y={y} fontSize={11} fontWeight={600} fill={colors[i]}>
                    {s.label}
                  </text>
                );
              } : undefined}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Shared tooltip — matches the page surface, values in text tokens (never the series colour on the number itself). */
export function ChartTooltip({ active, payload, label, format }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="card-elevated rounded-lg border px-3 py-2 text-xs shadow-lg" style={{ borderColor: 'var(--hairline)', background: 'var(--surface-1)' }}>
      {label != null && <p className="mb-1 font-semibold text-ink-500">{label}</p>}
      <div className="space-y-0.5">
        {payload.map((p: any) => (
          <div key={p.dataKey || p.name} className="flex items-center gap-1.5">
            <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: p.color || p.fill }} />
            <span className="text-ink-500">{p.name}</span>
            <span className="ml-auto font-semibold tabular-nums text-ink-900 dark:text-ink-50">
              {format ? format(Number(p.value)) : p.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/** Shared legend — identity swatches, wraps on small widths, never repaints on filter (colour follows the entity). */
export function ChartLegend({ payload }: any) {
  if (!payload?.length) return null;
  return (
    <ul className="mt-2 flex flex-wrap items-center justify-center gap-x-4 gap-y-1">
      {payload.map((entry: any) => (
        <li key={entry.value} className="flex items-center gap-1.5 text-xs text-ink-500">
          <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: entry.color }} />
          {entry.value}
        </li>
      ))}
    </ul>
  );
}
