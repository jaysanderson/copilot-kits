import slugify from 'slugify';
import type { TaxonomyNode, TaxonomySettings } from '../types';
import { ChildrenSchema } from '../schemas';
import { childrenJsonSchema } from '../jsonSchemas';
import { buildChildrenPrompt, buildRepairPrompt } from '../prompts';
import { getCached, setCached, makeCacheKey } from './cache';
import { askWithRetry } from './askWithRetry';
import type { LimiterFn } from './run';

export async function generateChildrenForNode(
  parentNode: TaxonomyNode,
  settings: TaxonomySettings,
  language: string,
  existingIds: Set<string>,
  limiter: LimiterFn,
  signal?: AbortSignal,
  onNode?: (label: string) => void,
  onWarning?: (warning: string) => void
): Promise<TaxonomyNode[]> {
  if (parentNode.depth >= settings.maxDepth) return [];

  onNode?.(parentNode.prefLabel);

  const prompt = buildChildrenPrompt(
    parentNode,
    settings.maxChildrenPerNode,
    language,
    settings.initialPrompt || undefined
  );

  const askBody = {
    query: prompt,
    answer_json_schema: childrenJsonSchema,
  };

  const cacheKey = makeCacheKey(askBody);
  let cached = getCached<{ answer_json: unknown }>(cacheKey);

  if (!cached) {
    try {
      cached = await askWithRetry({
        body: askBody,
        limiter,
        signal,
        maxRetries: 3,
        label: `children of "${parentNode.prefLabel}"`,
      }) as { answer_json: unknown };
      setCached(cacheKey, cached);
    } catch (err) {
      if (err instanceof Error && err.message === 'Aborted') throw err;
      const msg = `Skipped children for "${parentNode.prefLabel}" after retries (${err instanceof Error ? err.message : 'unknown error'})`;
      onWarning?.(msg);
      return [];
    }
  }

  let answerJson = cached?.answer_json ?? cached;
  if (typeof answerJson === 'string') {
    try { answerJson = JSON.parse(answerJson); } catch { /* keep */ }
  }

  let parsed = ChildrenSchema.safeParse(answerJson);

  if (!parsed.success) {
    const errors = parsed.error.errors.map(e => `${e.path.join('.')}: ${e.message}`);
    const repairPrompt = buildRepairPrompt(prompt, errors);
    const repairBody = {
      query: repairPrompt,
      answer_json_schema: childrenJsonSchema,
    };

    try {
      const repairResult = await askWithRetry({
        body: repairBody,
        limiter,
        signal,
        maxRetries: 2,
        label: `repair for "${parentNode.prefLabel}"`,
      });

      let repairJson = repairResult?.answer_json ?? repairResult;
      if (typeof repairJson === 'string') {
        try { repairJson = JSON.parse(repairJson as string); } catch { /* keep */ }
      }

      parsed = ChildrenSchema.safeParse(repairJson);
      if (!parsed.success) {
        onWarning?.(`Skipped children for "${parentNode.prefLabel}" (invalid LLM output after repair)`);
        return [];
      }
    } catch (err) {
      if (err instanceof Error && err.message === 'Aborted') throw err;
      onWarning?.(`Skipped children for "${parentNode.prefLabel}" (repair failed)`);
      return [];
    }
  }

  const { children: drafts } = parsed.data;

  if (drafts.length < 2) return [];

  const childNodes: TaxonomyNode[] = drafts.map((draft, i) => {
    let id = slugify(draft.prefLabel, { lower: true, strict: true }) || `child-${i}`;
    if (existingIds.has(id)) {
      id = `${id}-${parentNode.depth + 1}-${i}`;
    }
    existingIds.add(id);

    return {
      id,
      prefLabel: draft.prefLabel,
      altLabels: draft.altLabels,
      definition: draft.definition,
      parentId: parentNode.id,
      depth: parentNode.depth + 1,
      seedQueries: draft.seedQueries,
      sortOrder: i,
    };
  });

  const grandchildren: TaxonomyNode[] = [];
  for (const child of childNodes) {
    if (signal?.aborted) throw new Error('Aborted');
    const gc = await generateChildrenForNode(
      child, settings, language, existingIds, limiter, signal, onNode, onWarning
    );
    grandchildren.push(...gc);
  }

  return [...childNodes, ...grandchildren];
}
