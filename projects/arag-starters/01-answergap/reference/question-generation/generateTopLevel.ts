import slugify from 'slugify';
import type { TaxonomyNode } from '../types';
import { TopLevelSchema } from '../schemas';
import { topLevelJsonSchema } from '../jsonSchemas';
import { buildTopLevelPrompt, buildRepairPrompt } from '../prompts';
import { getCached, setCached, makeCacheKey } from './cache';
import { askWithRetry } from './askWithRetry';
import type { LimiterFn } from './run';

export async function generateTopLevelNodes(
  maxChildren: number,
  language: string,
  limiter: LimiterFn,
  signal?: AbortSignal,
  initialPrompt?: string
): Promise<TaxonomyNode[]> {
  const prompt = buildTopLevelPrompt(maxChildren, language, initialPrompt);

  const askBody = {
    query: prompt,
    answer_json_schema: topLevelJsonSchema,
  };

  const cacheKey = makeCacheKey(askBody);
  let cached = getCached<{ answer_json: unknown }>(cacheKey);

  if (!cached) {
    cached = await askWithRetry({
      body: askBody,
      limiter,
      signal,
      maxRetries: 3,
      label: 'top-level categories',
    }) as { answer_json: unknown };
    setCached(cacheKey, cached);
  }

  let answerJson = cached?.answer_json ?? cached;
  if (typeof answerJson === 'string') {
    try { answerJson = JSON.parse(answerJson); } catch { /* keep as-is */ }
  }

  let parsed = TopLevelSchema.safeParse(answerJson);

  if (!parsed.success) {
    const errors = parsed.error.errors.map(e => `${e.path.join('.')}: ${e.message}`);
    const repairPrompt = buildRepairPrompt(prompt, errors);
    const repairBody = {
      query: repairPrompt,
      answer_json_schema: topLevelJsonSchema,
    };

    const repairResult = await askWithRetry({
      body: repairBody,
      limiter,
      signal,
      maxRetries: 2,
      label: 'top-level repair',
    });

    let repairJson = repairResult?.answer_json ?? repairResult;
    if (typeof repairJson === 'string') {
      try { repairJson = JSON.parse(repairJson as string); } catch { /* keep */ }
    }

    parsed = TopLevelSchema.safeParse(repairJson);
    if (!parsed.success) {
      throw new Error(`LLM output invalid after repair: ${parsed.error.message}`);
    }
  }

  return parsed.data.nodes.map((draft, i) => {
    const id = slugify(draft.prefLabel, { lower: true, strict: true }) || `node-${i}`;
    return {
      id,
      prefLabel: draft.prefLabel,
      altLabels: draft.altLabels,
      definition: draft.definition,
      parentId: null,
      depth: 1,
      seedQueries: draft.seedQueries,
      sortOrder: i,
    };
  });
}
