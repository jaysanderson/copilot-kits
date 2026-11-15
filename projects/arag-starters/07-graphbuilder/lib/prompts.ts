import type { TaxonomyNode } from './types';

export function buildTopLevelPrompt(
  maxChildren: number,
  language: string,
  initialPrompt?: string
): string {
  const contextBlock = initialPrompt
    ? `\nUSER CONTEXT:\n${initialPrompt}\n`
    : '';

  return `You are a taxonomy expert. Based on the documents in this knowledge base, propose top-level categories that would effectively organise the entire corpus.
${contextBlock}
INSTRUCTIONS:
- Create between 3 and ${maxChildren} top-level categories.
- Categories must be mutually distinct. Do not create synonyms as separate categories.
- Use the language and terminology found in the documents.
- All labels and definitions must be in ${language}.
- Each category needs:
  - prefLabel: the primary name
  - altLabels: alternative names or synonyms (can be empty)
  - definition: a clear 1-2 sentence definition grounded in the corpus content
  - seedQueries: 3-8 search queries that would find documents belonging to this category

Return ONLY valid JSON matching the required schema. No explanations.`;
}

export function buildChildrenPrompt(
  parentNode: Pick<TaxonomyNode, 'prefLabel' | 'definition' | 'altLabels' | 'seedQueries'>,
  maxChildrenPerNode: number,
  language: string,
  initialPrompt?: string
): string {
  const queriesBlock = parentNode.seedQueries.length > 0
    ? `\n- seedQueries: [${parentNode.seedQueries.map(q => `"${q}"`).join(', ')}]`
    : '';

  const contextBlock = initialPrompt
    ? `\nUSER CONTEXT:\n${initialPrompt}\n`
    : '';

  return `You are a taxonomy expert. Given a parent concept, propose child concepts that subdivide it based on documents in this knowledge base.

PARENT CONCEPT:
- prefLabel: "${parentNode.prefLabel}"
- definition: "${parentNode.definition}"
- altLabels: [${parentNode.altLabels.map(l => `"${l}"`).join(', ')}]${queriesBlock}

INSTRUCTIONS:
- Propose up to ${maxChildrenPerNode} child concepts that subdivide the parent topic.
- Base your proposals on actual document content in the knowledge base about this topic.
- All labels and definitions must be in ${language}.
- Each child needs: prefLabel (string), altLabels (string array), definition (string), seedQueries (array of 3-8 strings).
- If no meaningful split exists, return {"children": []}.
- Children must be mutually distinct with no overlapping scope.
${contextBlock}
Return a JSON object with key "children" containing an array of child objects.`;
}

export function buildRepairPrompt(
  originalPrompt: string,
  validationErrors: string[]
): string {
  return `The previous response had JSON validation errors. Please fix and return corrected JSON only.

VALIDATION ERRORS:
${validationErrors.map((e, i) => `${i + 1}. ${e}`).join('\n')}

ORIGINAL REQUEST:
${originalPrompt}

Return ONLY the corrected JSON. No explanations.`;
}
