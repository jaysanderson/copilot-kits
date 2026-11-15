// SVG chart builders - no charting library, per house stack preference.
import { fmtUSD } from "./levers-data.js";
import { escapeXml as esc } from "./dom.js";

function colorVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

// Simple horizontal bar chart - value case vs subscription pricing.
export function barChart(bars) {
  const width = 640, barHeight = 30, gap = 22, leftLabelWidth = 170, rightLabelWidth = 110;
  const chartWidth = width - leftLabelWidth - rightLabelWidth;
  const max = Math.max(...bars.map((b) => b.amount), 1) * 1.08;
  const height = bars.length * (barHeight + gap) + gap;
  let svg = `<svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bar chart">`;
  bars.forEach((bar, i) => {
    const y = gap + i * (barHeight + gap);
    const barW = Math.max(4, (bar.amount / max) * chartWidth);
    const color = colorVar(bar.colorVar) || "#2B2BB2";
    const valueLabel = fmtUSD(bar.amount);
    const labelFitsRight = width - (leftLabelWidth + barW + 10) > valueLabel.length * 7.5;
    const labelX = labelFitsRight ? leftLabelWidth + barW + 10 : leftLabelWidth + barW - 8;
    svg += `<text x="0" y="${y + barHeight / 2 + 5}" class="chart-bar-label">${esc(bar.label)}</text>`;
    svg += `<rect x="${leftLabelWidth}" y="${y}" width="${barW}" height="${barHeight}" rx="4" fill="${color}"></rect>`;
    svg += `<text x="${labelX}" y="${y + barHeight / 2 + 5}" text-anchor="${labelFitsRight ? "start" : "end"}" class="chart-value-label">${esc(valueLabel)}</text>`;
  });
  svg += `</svg>`;
  return svg;
}

function truncateLabel(s, max) {
  return s.length > max ? s.slice(0, max - 1).trimEnd() + "…" : s;
}

// Tornado chart for the sensitivity view - one horizontal bar per input,
// centred on the base value, spanning low..high, widest swing on top.
export function tornadoChart(rows) {
  if (rows.length === 0) return "";
  const width = 820, rowHeight = 34, gap = 12, labelWidth = 340, top = 20;
  const height = rows.length * (rowHeight + gap) + top * 2;
  const allVals = rows.flatMap((r) => [r.low, r.high, r.base]);
  const maxAbs = Math.max(...allVals.map(Math.abs), 1) * 1.1;
  const plotWidth = width - labelWidth - 20;
  const center = labelWidth + plotWidth / 2;
  const scale = (plotWidth / 2) / maxAbs;

  // NOTE: no overflow:visible here (a prior fix added it to stop labels
  // clipping, before label truncation existed) - with truncateLabel now
  // bounding every label to labelWidth, letting content paint outside the
  // SVG's own box was found live to push the PAGE into horizontal scroll
  // at 390px (demo-tester finding 3, 22 Sep 2026), which is worse than the
  // clipping it was meant to fix. Default SVG clipping is the safe choice
  // once the content is properly bounded.
  let svg = `<svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sensitivity tornado chart">`;
  svg += `<line x1="${center}" y1="${top - 5}" x2="${center}" y2="${height - top + 5}" stroke="${colorVar("--arag-border") || "#C9D9EE"}" stroke-width="1"></line>`;
  rows.forEach((r, i) => {
    const y = top + i * (rowHeight + gap);
    const x1 = center + r.low * scale;
    const x2 = center + r.high * scale;
    const barX = Math.min(x1, x2);
    const barW = Math.max(2, Math.abs(x2 - x1));
    const label = `${truncateLabel(r.lever_title, 18)} - ${truncateLabel(r.input_label, 34)}`;
    svg += `<text x="${labelWidth - 12}" y="${y + rowHeight / 2 + 4}" text-anchor="end" class="chart-bar-label"><title>${esc(r.lever_title + " - " + r.input_label)}</title>${esc(label)}</text>`;
    svg += `<rect x="${barX}" y="${y}" width="${barW}" height="${rowHeight - 8}" rx="3" fill="${colorVar("--arag-blue-p3") || "#4B4BF7"}"></rect>`;
  });
  svg += `</svg>`;
  return svg;
}

// Monthly cumulative cash-flow line, crossing zero at payback.
export function cashflowChart(flows, paybackMonths) {
  const width = 720, height = 260, padL = 60, padR = 20, padT = 20, padB = 30;
  const plotW = width - padL - padR, plotH = height - padT - padB;
  let cumulative = 0;
  const points = flows.map((f) => (cumulative += f));
  const minV = Math.min(0, ...points), maxV = Math.max(0, ...points);
  const range = maxV - minV || 1;
  const xFor = (i) => padL + (i / (points.length - 1)) * plotW;
  const yFor = (v) => padT + plotH - ((v - minV) / range) * plotH;
  const zeroY = yFor(0);

  let path = points.map((v, i) => `${i === 0 ? "M" : "L"}${xFor(i).toFixed(1)},${yFor(v).toFixed(1)}`).join(" ");

  let svg = `<svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cumulative cash flow chart">`;
  svg += `<line x1="${padL}" y1="${zeroY}" x2="${width - padR}" y2="${zeroY}" stroke="${colorVar("--arag-border") || "#C9D9EE"}" stroke-width="1"></line>`;
  svg += `<path d="${path}" fill="none" stroke="${colorVar("--arag-blue-p2") || "#2B2BB2"}" stroke-width="2.5"></path>`;
  if (paybackMonths !== null && paybackMonths !== undefined && paybackMonths <= points.length - 1) {
    const px = xFor(paybackMonths);
    svg += `<line x1="${px.toFixed(1)}" y1="${padT}" x2="${px.toFixed(1)}" y2="${height - padB}" stroke="${colorVar("--arag-green-p3") || "#00D364"}" stroke-width="1.5" stroke-dasharray="4,3"></line>`;
    svg += `<text x="${px.toFixed(1)}" y="${padT - 6}" text-anchor="middle" class="chart-value-label">Payback</text>`;
  }
  svg += `<text x="${padL}" y="${height - 6}" class="chart-bar-label">Month 0</text>`;
  svg += `<text x="${width - padR}" y="${height - 6}" text-anchor="end" class="chart-bar-label">Month ${points.length - 1}</text>`;
  svg += `</svg>`;
  return svg;
}
