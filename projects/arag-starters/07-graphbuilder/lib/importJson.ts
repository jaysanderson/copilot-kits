import { z } from 'zod';
import type { TaxonomyModel } from './types';

const NodeSchema = z.object({
  id: z.string(),
  prefLabel: z.string(),
  altLabels: z.array(z.string()),
  definition: z.string(),
  parentId: z.string().nullable(),
  depth: z.number(),
  seedQueries: z.array(z.string()),
  sortOrder: z.number().default(0),
});

const TaxonomyModelSchema = z.object({
  scheme: z.object({
    id: z.string(),
    title: z.string(),
    language: z.string(),
    baseUri: z.string(),
    createdAt: z.string(),
  }),
  nodes: z.array(NodeSchema),
  settings: z.object({
    maxDepth: z.number(),
    maxChildrenPerNode: z.number(),
    initialPrompt: z.string().default(''),
  }),
  metrics: z.object({
    generationSeconds: z.number(),
  }),
});

export function validateImportedJson(raw: unknown): { valid: true; model: TaxonomyModel } | { valid: false; errors: string[] } {
  const result = TaxonomyModelSchema.safeParse(raw);
  if (result.success) {
    return { valid: true, model: result.data as TaxonomyModel };
  }
  return {
    valid: false,
    errors: result.error.errors.map(e => `${e.path.join('.')}: ${e.message}`),
  };
}

export function readFileAsJson(file: File): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        resolve(JSON.parse(reader.result as string));
      } catch {
        reject(new Error('File is not valid JSON'));
      }
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
}
