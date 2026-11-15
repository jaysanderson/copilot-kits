// ─────────────────────────────────────────────────────────────────────────────
// Standard B13 (arag-demo-app skill, 17 Aug 2026) — charts, not tables, for any
// reporting/metrics/telemetry surface. Built to the `dataviz` skill's method:
// form-first, color-by-job, a validated categorical order, never a rainbow.
//
// The categorical/sequential/diverging/status values below are the dataviz
// skill's own reference palette (references/palette.md) — a pre-validated set:
// worst adjacent CVD ΔE 9.1 light / 8.4 dark (OKLab ×100, ≥8 target), worst
// adjacent normal-vision ΔE 19.6 light / 19.3 dark (≥15 floor). Because a
// demo's `--brand`/`--accent` are arbitrary per-build hex values (theme.ts),
// they CANNOT safely stand in for a validated multi-series categorical ramp —
// the skill is explicit that swapping in brand hues requires re-running the
// validator, which isn't possible for an unknown future brand. So charts stay
// on this fixed, pre-cleared order; `--brand` is used only where a SINGLE
// series/highlight needs to feel on-brand (a stat tile accent, a single-series
// trend line) where CVD separation from other series is a non-issue.
// ─────────────────────────────────────────────────────────────────────────────

export interface Swatch { light: string; dark: string }

/** Fixed categorical order — never cycle, never reorder per chart. Cap at 3 for scatter/bubble/small-multiples (all-pairs forms); the first 6 clear the adjacent gate used by bars/lines/stacks. */
export const CATEGORICAL: Swatch[] = [
  { light: '#2a78d6', dark: '#3987e5' }, // 1 blue
  { light: '#eb6834', dark: '#d95926' }, // 2 orange
  { light: '#1baf7a', dark: '#199e70' }, // 3 aqua
  { light: '#eda100', dark: '#c98500' }, // 4 yellow
  { light: '#e87ba4', dark: '#d55181' }, // 5 magenta
  { light: '#008300', dark: '#008300' }, // 6 green
  { light: '#4a3aa7', dark: '#9085e9' }, // 7 violet
  { light: '#e34948', dark: '#e66767' }, // 8 red
];

/** Sequential (magnitude) — one hue, light→dark, 8 steps. */
export const SEQUENTIAL: Swatch[] = [
  { light: '#cde2fb', dark: '#cde2fb' },
  { light: '#9ec5f4', dark: '#9ec5f4' },
  { light: '#6da7ec', dark: '#6da7ec' },
  { light: '#3987e5', dark: '#3987e5' },
  { light: '#256abf', dark: '#256abf' },
  { light: '#1c5cab', dark: '#1c5cab' },
  { light: '#184f95', dark: '#184f95' },
  { light: '#0d366b', dark: '#0d366b' },
];

/** Diverging (polarity) — blue/red poles, gray neutral midpoint. */
export const DIVERGING = {
  negative: { light: '#2a78d6', dark: '#3987e5' },
  neutral: { light: '#f0efec', dark: '#383835' },
  positive: { light: '#e34948', dark: '#e66767' },
};

/** Status (state) — fixed, never reused as a categorical series. Icon + label always accompany color (never color alone). */
export const STATUS = {
  good: { light: '#0ca30c', dark: '#0ca30c' },
  warning: { light: '#fab219', dark: '#fab219' },
  serious: { light: '#ec835a', dark: '#ec835a' },
  critical: { light: '#d03b3b', dark: '#d03b3b' },
};

function isDark(): boolean {
  return typeof document !== 'undefined' && document.documentElement.classList.contains('dark');
}

/** Resolve N categorical series colors for the current colour scheme, in fixed order. */
export function categoricalPalette(count = CATEGORICAL.length): string[] {
  const dark = isDark();
  return CATEGORICAL.slice(0, count).map((s) => (dark ? s.dark : s.light));
}

/** Resolve the sequential ramp for the current colour scheme. */
export function sequentialPalette(): string[] {
  const dark = isDark();
  return SEQUENTIAL.map((s) => (dark ? s.dark : s.light));
}

/** Resolve the fixed status colours for the current colour scheme. */
export function statusPalette(): Record<'good' | 'warning' | 'serious' | 'critical', string> {
  const dark = isDark();
  return {
    good: dark ? STATUS.good.dark : STATUS.good.light,
    warning: dark ? STATUS.warning.dark : STATUS.warning.light,
    serious: dark ? STATUS.serious.dark : STATUS.serious.light,
    critical: dark ? STATUS.critical.dark : STATUS.critical.light,
  };
}

/** Read the demo's own on-brand colour (for single-series accents, never multi-series identity). */
export function brandColor(): string {
  if (typeof window === 'undefined') return CATEGORICAL[0].light;
  return getComputedStyle(document.documentElement).getPropertyValue('--brand').trim() || CATEGORICAL[0].light;
}

/** Chart chrome tokens — ink/gridline/surface, resolved from the live theme so a chart matches its page. */
export function chartChrome() {
  if (typeof window === 'undefined') {
    return { ink: '#383F55', inkMuted: '#7d8299', grid: 'rgba(148,163,184,0.22)', surface: '#ffffff' };
  }
  const css = getComputedStyle(document.documentElement);
  return {
    ink: isDark() ? '#f4f5f8' : '#1c2033',
    inkMuted: css.getPropertyValue('--hairline-strong').trim() ? (isDark() ? '#9ba0b8' : '#6b7089') : '#7d8299',
    grid: css.getPropertyValue('--hairline').trim() || 'rgba(148,163,184,0.18)',
    surface: css.getPropertyValue('--surface-1').trim() || '#ffffff',
  };
}
