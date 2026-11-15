/**
 * Worst-case cost estimate for a generation run (hard rule 15 - cost safety).
 *
 * The engine issues one retrieval-and-answer call per node that is allowed to
 * have children: one call for the top-level categories, then one call per
 * node at each subsequent depth (up to maxDepth - 1), each of which can
 * return up to maxChildrenPerNode children.
 *
 * calls = 1 + breadth^1 + breadth^2 + ... + breadth^(maxDepth - 1)
 * maxNodes = breadth^1 + breadth^2 + ... + breadth^maxDepth
 */
export function estimateGeneration(maxDepth: number, maxChildrenPerNode: number) {
  let calls = 1;
  let maxNodes = 0;
  let levelNodes = maxChildrenPerNode;

  for (let depth = 1; depth <= maxDepth; depth++) {
    maxNodes += levelNodes;
    if (depth < maxDepth) {
      calls += levelNodes;
    }
    levelNodes *= maxChildrenPerNode;
  }

  return { calls, maxNodes };
}
