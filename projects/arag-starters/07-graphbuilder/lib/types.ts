export interface TaxonomyNode {
  id: string;
  prefLabel: string;
  altLabels: string[];
  definition: string;
  parentId: string | null;
  depth: number;
  seedQueries: string[];
  sortOrder: number;
}

export interface TaxonomyScheme {
  id: string;
  title: string;
  language: string;
  baseUri: string;
  createdAt: string;
}

export interface TaxonomySettings {
  maxDepth: number;
  maxChildrenPerNode: number;
  initialPrompt: string;
}

export interface TaxonomyMetrics {
  generationSeconds: number;
}

export interface TaxonomyModel {
  scheme: TaxonomyScheme;
  nodes: TaxonomyNode[];
  settings: TaxonomySettings;
  metrics: TaxonomyMetrics;
}

export interface GenerationProgress {
  step: 'top-level' | 'recursing' | 'normalizing' | 'complete' | 'error';
  currentNode?: string;
  currentDepth?: number;
  maxDepth?: number;
  nodesCreated: number;
  elapsedMs: number;
  message: string;
  warnings: string[];
}

export interface NodeDraft {
  prefLabel: string;
  altLabels: string[];
  definition: string;
  seedQueries: string[];
}

/** Hard bounds on generation size (hard rule 15 - cost safety). Each level of
 *  depth multiplies the call count by up to maxChildrenPerNode, so both are
 *  capped low enough that even the worst case stays a bounded, cheap run -
 *  see lib/engine/estimate.ts. */
export const SETTINGS_LIMITS = {
  maxDepth: { min: 1, max: 3 },
  maxChildrenPerNode: { min: 2, max: 8 },
} as const;

export const DEFAULT_SETTINGS: TaxonomySettings = {
  maxDepth: 2,
  maxChildrenPerNode: 6,
  initialPrompt: '',
};

export const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'he', label: 'Hebrew' },
  { code: 'ar', label: 'Arabic' },
  { code: 'fr', label: 'French' },
  { code: 'de', label: 'German' },
  { code: 'es', label: 'Spanish' },
  { code: 'pt', label: 'Portuguese' },
  { code: 'it', label: 'Italian' },
  { code: 'nl', label: 'Dutch' },
  { code: 'ru', label: 'Russian' },
  { code: 'zh', label: 'Chinese' },
  { code: 'ja', label: 'Japanese' },
  { code: 'ko', label: 'Korean' },
] as const;
