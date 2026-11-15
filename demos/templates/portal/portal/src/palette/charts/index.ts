// Standard B13 — charts, not tables, for any reporting/metrics/telemetry
// surface. Built to the `dataviz` skill (form-first, colour-by-job, a
// validated categorical order — see tokens.ts for the exact validation run).
export { StatTile, type StatTileProps } from './StatTile';
export { TrendChart, ChartTooltip, ChartLegend, type TrendChartProps, type TrendSeries } from './TrendChart';
export { BreakdownChart, type BreakdownChartProps, type BreakdownRow } from './BreakdownChart';
export { ShareChart, type ShareChartProps, type ShareRow } from './ShareChart';
export {
  categoricalPalette, sequentialPalette, statusPalette, brandColor, chartChrome,
  CATEGORICAL, SEQUENTIAL, DIVERGING, STATUS,
} from './tokens';
