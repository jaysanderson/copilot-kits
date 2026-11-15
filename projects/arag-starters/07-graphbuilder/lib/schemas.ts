import { z } from 'zod';

export const NodeDraftSchema = z.object({
  prefLabel: z.string().min(1),
  altLabels: z.array(z.string()),
  definition: z.string().min(1),
  seedQueries: z.array(z.string()),
});

export const TopLevelSchema = z.object({
  nodes: z.array(NodeDraftSchema).min(1),
});

export const ChildrenSchema = z.object({
  children: z.array(NodeDraftSchema),
});

export type NodeDraftParsed = z.infer<typeof NodeDraftSchema>;
export type TopLevelParsed = z.infer<typeof TopLevelSchema>;
export type ChildrenParsed = z.infer<typeof ChildrenSchema>;
