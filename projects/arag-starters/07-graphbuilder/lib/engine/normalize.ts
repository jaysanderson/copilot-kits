import slugify from 'slugify';
import type { TaxonomyNode } from '../types';

export function normalizeNodes(nodes: TaxonomyNode[]): TaxonomyNode[] {
  let result = [...nodes];

  result = deduplicateLabels(result);
  result = mergeIdenticalNodes(result);
  result = ensureStableSlugs(result);
  result = preventCycles(result);

  return result;
}

function deduplicateLabels(nodes: TaxonomyNode[]): TaxonomyNode[] {
  const depthGroups = new Map<number, TaxonomyNode[]>();
  for (const node of nodes) {
    if (!depthGroups.has(node.depth)) depthGroups.set(node.depth, []);
    depthGroups.get(node.depth)!.push(node);
  }

  for (const [, group] of depthGroups) {
    const seen = new Map<string, TaxonomyNode>();
    for (const node of group) {
      const key = node.prefLabel.toLowerCase().trim();
      if (!seen.has(key)) {
        seen.set(key, node);
      }
    }
  }

  return nodes;
}

function mergeIdenticalNodes(nodes: TaxonomyNode[]): TaxonomyNode[] {
  const depthGroups = new Map<number, TaxonomyNode[]>();
  for (const node of nodes) {
    if (!depthGroups.has(node.depth)) depthGroups.set(node.depth, []);
    depthGroups.get(node.depth)!.push(node);
  }

  const merged = new Set<string>();
  const mergeMap = new Map<string, string>();

  for (const [, group] of depthGroups) {
    const byLabel = new Map<string, TaxonomyNode[]>();
    for (const node of group) {
      const key = node.prefLabel.toLowerCase().trim();
      if (!byLabel.has(key)) byLabel.set(key, []);
      byLabel.get(key)!.push(node);
    }

    for (const [, dupes] of byLabel) {
      if (dupes.length < 2) continue;

      const primary = dupes[0];
      for (let i = 1; i < dupes.length; i++) {
        const dupe = dupes[i];
        merged.add(dupe.id);
        mergeMap.set(dupe.id, primary.id);

        for (const alt of dupe.altLabels) {
          if (!primary.altLabels.includes(alt)) primary.altLabels.push(alt);
        }
      }
    }
  }

  let result = nodes.filter(n => !merged.has(n.id));

  for (const node of result) {
    if (node.parentId && mergeMap.has(node.parentId)) {
      node.parentId = mergeMap.get(node.parentId)!;
    }
  }

  return result;
}

function ensureStableSlugs(nodes: TaxonomyNode[]): TaxonomyNode[] {
  const usedIds = new Set<string>();
  const idMap = new Map<string, string>();

  for (const node of nodes) {
    let newId = slugify(node.prefLabel, { lower: true, strict: true }) || `node-${node.depth}`;
    let suffix = 0;
    const base = newId;
    while (usedIds.has(newId)) {
      suffix++;
      newId = `${base}-${suffix}`;
    }
    usedIds.add(newId);
    if (newId !== node.id) {
      idMap.set(node.id, newId);
      node.id = newId;
    }
  }

  for (const node of nodes) {
    if (node.parentId && idMap.has(node.parentId)) {
      node.parentId = idMap.get(node.parentId)!;
    }
  }

  return nodes;
}

function preventCycles(nodes: TaxonomyNode[]): TaxonomyNode[] {
  const nodeMap = new Map(nodes.map(n => [n.id, n]));

  for (const node of nodes) {
    if (!node.parentId) continue;

    const visited = new Set<string>();
    let current: string | null = node.parentId;

    while (current) {
      if (visited.has(current)) {
        node.parentId = null;
        node.depth = 1;
        break;
      }
      visited.add(current);
      const parent = nodeMap.get(current);
      current = parent?.parentId ?? null;
    }
  }

  return nodes;
}
