import pLimit from 'p-limit';
import type { TaxonomyModel, TaxonomySettings, TaxonomyScheme, GenerationProgress } from '../types';
import { generateTopLevelNodes } from './generateTopLevel';
import { generateChildrenForNode } from './recurse';
import { normalizeNodes } from './normalize';
import { clearCache } from './cache';

export type LimiterFn = <T>(fn: () => Promise<T>) => Promise<T>;

interface RunOptions {
  settings: TaxonomySettings;
  scheme: TaxonomyScheme;
  signal?: AbortSignal;
  onProgress?: (progress: GenerationProgress) => void;
}

export async function runTaxonomyGeneration(options: RunOptions): Promise<TaxonomyModel> {
  const { settings, scheme, signal, onProgress } = options;
  const startTime = Date.now();
  const limiter = pLimit(3) as unknown as LimiterFn;

  clearCache();

  const elapsed = () => Date.now() - startTime;
  const warnings: string[] = [];

  const progress: GenerationProgress = {
    step: 'top-level',
    nodesCreated: 0,
    elapsedMs: 0,
    message: 'Generating top-level categories...',
    warnings,
  };

  const emit = (updates: Partial<GenerationProgress>) => {
    Object.assign(progress, updates, { elapsedMs: elapsed(), warnings });
    onProgress?.({ ...progress, warnings: [...warnings] });
  };

  emit({ step: 'top-level', message: 'Generating top-level categories...' });

  const topNodes = await generateTopLevelNodes(
    settings.maxChildrenPerNode,
    scheme.language,
    limiter,
    signal,
    settings.initialPrompt || undefined
  );

  emit({
    nodesCreated: topNodes.length,
    message: `Created ${topNodes.length} top-level categories`,
  });

  let allNodes = [...topNodes];
  const existingIds = new Set(allNodes.map(n => n.id));

  if (settings.maxDepth > 1) {
    emit({ step: 'recursing', currentDepth: 2, maxDepth: settings.maxDepth, message: 'Generating sub-categories...' });

    for (const node of topNodes) {
      if (signal?.aborted) throw new Error('Aborted');

      emit({ currentNode: node.prefLabel, message: `Recursing: ${node.prefLabel}` });

      const children = await generateChildrenForNode(
        node, settings, scheme.language, existingIds, limiter, signal,
        (label) => emit({ currentNode: label, nodesCreated: allNodes.length + 1, message: `Processing: ${label}` }),
        (warning) => {
          warnings.push(warning);
          emit({ message: `Warning: ${warning}` });
        }
      );

      allNodes.push(...children);
      emit({ nodesCreated: allNodes.length });
    }
  }

  emit({ step: 'normalizing', message: 'Normalising taxonomy...' });
  allNodes = normalizeNodes(allNodes);

  const skipped = warnings.length;
  const completeMsg = skipped > 0
    ? `Complete: ${allNodes.length} nodes generated (${skipped} node${skipped > 1 ? 's' : ''} skipped)`
    : `Complete: ${allNodes.length} nodes generated`;

  emit({
    step: 'complete',
    nodesCreated: allNodes.length,
    message: completeMsg,
  });

  clearCache();

  return {
    scheme,
    nodes: allNodes,
    settings,
    metrics: {
      generationSeconds: elapsed() / 1000,
    },
  };
}
