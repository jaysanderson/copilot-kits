// ─────────────────────────────────────────────────────────────────────────────
// Shared label-filter builder — the ONE place every route constructs a Nuclia
// `filter_expression`. Standard B19 (arag-demo-app skill, 17 Aug 2026): a
// catalogue/facet label filter that 412s (or silently returns nothing) is a
// defect in the SHARED helper, not something each page re-solves.
//
// Empirically verified live against a real KB (bioscience-demo, 17 Aug 2026) —
// four request shapes tried against POST /catalog and POST /ask on the same
// KB/label so the failure modes are real, not inferred from docs:
//
//   A. filter_expression: { resource: { prop:'label', labelset, label } }
//        -> 200, correct results.                                    (used)
//   B. legacy `filters: ["/doc_type/<label>"]` (leading slash, 2-seg)
//        -> 200 but ZERO results — no error, silently wrong.
//   C. legacy `filters: ["/classification.labels/doc_type/<label>"]`
//        (leading slash, full 4-seg facet path) -> 200, correct results.
//   D. filter_expression: { resource: "/doc_type/<label>" } (bare string)
//        -> 422 union_tag_not_found — filter_expression is never a string.
//   G. legacy `filters: ["doc_type/<label>"]` (NO leading slash)
//        -> 412 "Invalid label. It must start with a `/`: doc_type/<label>"
//        — this is the exact 412 Standard B19 names.
//
// Conclusion: the legacy `filters` array is real but fragile (must be the
// FULL `/classification.labels/{labelset}/{label}` path or it 412s or
// silently drops to zero) and it can only AND across entries — a single
// multi-value facet (2 doc_types selected) needs one call per value, merged
// client-side (the old workaround in lib/arag.ts). `filter_expression` is
// strictly better: one documented, schema-validated shape (Appendix F,
// "Label"), and it composes AND/OR/NOT natively (see `and`/`or` below) — one
// call for either the "any of these values in a labelset" case (OR) or the
// "match several labelsets at once" case (AND), no merge step needed.
//
// So this module ALWAYS builds `filter_expression`, never the legacy array,
// and — per B19's literal instruction, belt-and-braces — still normalises any
// input path to carry a leading `/` before parsing it, so a path arriving in
// ANY of the shapes other pages already use in this app (`doc_type/x`,
// `/doc_type/x`, `/classification.labels/doc_type/x`) resolves to the same
// {labelset, label} pair.
//
// Endpoint quirk (also confirmed live): the SAME Label object is wrapped
// differently per endpoint — `{ resource: <expr> }` on /catalog (filters
// resources), `{ field: <expr> }` on /find and /ask (filters at the
// paragraph/field level). Pass `keyBy` accordingly.
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Parses one filter path string into a `{labelset, label}` pair. Accepts:
 *   "doc_type/compliance-bulletin"
 *   "/doc_type/compliance-bulletin"
 *   "/classification.labels/doc_type/compliance-bulletin"
 * A label value may itself contain '/', so only the FIRST segment after an
 * optional "classification.labels" is the labelset — everything else is the
 * label.
 */
export function parseLabelPath(raw) {
  const path = String(raw || '').trim();
  const segments = path.split('/').filter(Boolean); // drop leading/empty segments
  if (!segments.length) return null;
  if (segments[0] === 'classification.labels') segments.shift();
  if (segments.length < 2) return null;
  const [labelset, ...rest] = segments;
  return { labelset, label: rest.join('/') };
}

/** One Nuclia `Label` filter-expression leaf. */
function labelExpr({ labelset, label }) {
  return { prop: 'label', labelset, label };
}

/**
 * Builds a `filter_expression` value from a flat list of label-path strings —
 * OR within a labelset (any of these doc_types), AND across labelsets (this
 * doc_type AND this status). Returns `undefined` when there is nothing to
 * filter on, so callers can `if (expr) body.filter_expression = expr`.
 */
export function buildLabelFilterExpression(paths) {
  const parsed = (Array.isArray(paths) ? paths : [])
    .map(parseLabelPath)
    .filter(Boolean);
  if (!parsed.length) return undefined;

  const byLabelset = new Map();
  for (const p of parsed) {
    if (!byLabelset.has(p.labelset)) byLabelset.set(p.labelset, []);
    byLabelset.get(p.labelset).push(p);
  }

  const perLabelset = [...byLabelset.values()].map((group) =>
    group.length === 1 ? labelExpr(group[0]) : { or: group.map(labelExpr) }
  );

  return perLabelset.length === 1 ? perLabelset[0] : { and: perLabelset };
}

/** Wraps a built expression for /catalog (resource-scoped). */
export function catalogFilterExpression(paths) {
  const expr = buildLabelFilterExpression(paths);
  return expr ? { resource: expr } : undefined;
}

/** Wraps a built expression for /find and /ask (field-scoped). */
export function fieldFilterExpression(paths) {
  const expr = buildLabelFilterExpression(paths);
  return expr ? { field: expr } : undefined;
}
