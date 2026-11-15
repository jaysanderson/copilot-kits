// ─────────────────────────────────────────────────────────────────────────────
// Knowledge-graph shaping - ported from the shipped portal (library.js).
//
// Nuclia's /graph path search returns subject/relation/object triples straight
// from the graph it built during processing. This normalises that raw payload
// into the { nodes, edges } shape the GraphSurface force layout consumes:
//   - drops noisy entity groups (dates, quantities…) that bury the real graph,
//   - merges surface-form variants of the same entity onto one node,
//   - drops nodes left with no edge after filtering (they read as render faults).
// ─────────────────────────────────────────────────────────────────────────────

// Groups that add noise rather than insight: extraction tags every date and
// quantity it sees, so an unfiltered graph is mostly "48 minutes" and "mid-April".
const NOISY_GROUPS = new Set([
  'DATE', 'TIME', 'CARDINAL', 'ORDINAL', 'PERCENT', 'MONEY', 'QUANTITY',
]);

/** Case, possessives and punctuation folded away, for merging entity variants. */
function normaliseEntity(value) {
  return String(value)
    .toLowerCase()
    .replace(/['’]s\b/g, '')
    .replace(/[.,]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Picks the better of two surface forms for display. Title Case beats ALL CAPS
 * (speaker labels) and lower case, and a form without a trailing possessive wins.
 */
function preferredLabel(a, b) {
  const score = (value) => {
    let points = 0;
    if (!/['’]s$/.test(value)) points += 2;
    if (value !== value.toUpperCase()) points += 2;
    if (/^[A-Z]/.test(value)) points += 1;
    return points;
  };
  return score(a) > score(b) ? a : b;
}

/**
 * The KB's own built-in NER and our registered llm-graph entity_defs tag the
 * SAME real-world entity with different-cased group vocabularies (e.g. the
 * built-in extractor's "PRODUCT" vs our entity_defs' "Product" for the same
 * part number) - found live 5 Sep 2026 on RH-4420, which was arriving as two
 * separate nodes (Product::rh-4420 AND PRODUCT::rh-4420) purely because the
 * merge key below used to include the group. Prefer the friendlier, non-ALL-
 * CAPS form (our own entity_defs vocabulary) for display once merged.
 */
function preferredGroup(a, b) {
  const isAllCaps = (v) => v === v.toUpperCase();
  if (isAllCaps(a) && !isAllCaps(b)) return b;
  if (!isAllCaps(a) && isAllCaps(b)) return a;
  return a;
}

/** Turns Nuclia's raw /graph response into { nodes, edges, pathCount }. */
export function shapeGraph(raw, { includeAllGroups = false } = {}) {
  const nodes = new Map();
  const edges = [];
  const seenEdges = new Set();

  const addNode = (node) => {
    if (!node?.value) return null;
    // Relations to whole documents arrive with a UUID value - a meaningless node.
    if (node.type === 'resource') return null;
    const group = node.group || 'entity';
    if (!includeAllGroups && NOISY_GROUPS.has(String(group).toUpperCase())) return null;

    // Keyed on the entity value ALONE, not group + value - the built-in NER and
    // our own llm-graph entity_defs both tag the same real thing under
    // different-cased group vocabularies (see preferredGroup above), and keying
    // on both split one entity into two visible nodes.
    const key = normaliseEntity(node.value);
    if (!nodes.has(key)) {
      nodes.set(key, { id: key, label: node.value, group, degree: 0 });
    } else {
      const existing = nodes.get(key);
      if (preferredLabel(node.value, existing.label) === node.value) existing.label = node.value;
      existing.group = preferredGroup(group, existing.group);
    }
    return key;
  };

  for (const path of raw.paths || []) {
    const from = addNode(path.source);
    const to = addNode(path.destination);
    if (!from || !to || from === to) continue;

    const label = path.relation?.label || '';
    const key = `${from}|${label}|${to}`;
    if (seenEdges.has(key)) continue;
    seenEdges.add(key);

    edges.push({ from, to, label });
    nodes.get(from).degree++;
    nodes.get(to).degree++;
  }

  return {
    nodes: [...nodes.values()]
      .filter((node) => node.degree > 0)
      .sort((a, b) => b.degree - a.degree),
    edges,
    pathCount: (raw.paths || []).length,
  };
}
