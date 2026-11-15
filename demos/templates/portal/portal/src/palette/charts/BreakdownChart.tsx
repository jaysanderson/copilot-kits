import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, LabelList } from 'recharts';
import { categoricalPalette, chartChrome } from './tokens';
import { ChartTooltip } from './TrendChart';

export interface BreakdownRow {
  label: string;
  value: number;
}

export interface BreakdownChartProps {
  data: BreakdownRow[];
  height?: number;
  format?: (v: number) => string;
  /** A single semantic colour (e.g. status) instead of the categorical ramp — pass for a one-hue comparison. */
  singleColor?: string;
}

/**
 * A horizontal bar comparison — thin marks, rounded data-ends, value labels
 * at the bar end (the relief the dataviz skill requires for any series colour
 * under the 3:1 contrast floor). Category identity is the y-axis label, never
 * colour alone, so this reads correctly even for a reader who can't see hue.
 */
export function BreakdownChart({ data, height, format = (v) => String(v), singleColor }: BreakdownChartProps) {
  const colors = singleColor ? data.map(() => singleColor) : categoricalPalette(data.length);
  const chrome = chartChrome();
  const rowHeight = 34;

  return (
    <div style={{ width: '100%', height: height ?? Math.max(120, data.length * rowHeight + 24) }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 44, bottom: 4, left: 4 }} barCategoryGap="28%">
          <CartesianGrid stroke={chrome.grid} horizontal={false} />
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="label"
            width={120}
            tick={{ fill: chrome.ink, fontSize: 12 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<ChartTooltip format={format} />} cursor={{ fill: chrome.grid }} />
          <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={18} isAnimationActive={false}>
            {data.map((_, i) => <Cell key={i} fill={colors[i]} />)}
            <LabelList
              dataKey="value"
              position="right"
              formatter={(v: unknown) => format(Number(v))}
              style={{ fill: chrome.ink, fontSize: 11, fontWeight: 600 }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
