'use client';

import { useState, useCallback } from 'react';
import pLimit from 'p-limit';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';
import { ScrollArea } from '@/components/ui/scroll-area';
import { TaxonomyTree } from '@/components/taxonomy-tree';
import { NodeEditor } from '@/components/node-editor';
import { useTaxonomyStore } from '@/hooks/use-taxonomy-store';
import { generateChildrenForNode } from '@/lib/engine/recurse';
import type { LimiterFn } from '@/lib/engine/run';
import type { TaxonomyNode } from '@/lib/types';

export function ReviewPanel() {
  const store = useTaxonomyStore();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [rerunningId, setRerunningId] = useState<string | null>(null);
  const [rerunError, setRerunError] = useState<string | null>(null);

  const nodes = store.model?.nodes ?? [];
  const selectedNode = nodes.find(n => n.id === selectedId) ?? null;

  const handleSave = useCallback(async (id: string, updates: Partial<TaxonomyNode>) => {
    await store.updateNode(id, updates);
  }, [store]);

  const handleDelete = useCallback(async (id: string) => {
    await store.deleteNode(id);
    setSelectedId(null);
  }, [store]);

  const handleRerunChildren = useCallback(async (id: string) => {
    if (!store.model) return;
    const node = store.model.nodes.find(n => n.id === id);
    if (!node) return;

    setRerunError(null);
    setRerunningId(id);

    try {
      const allDescendantIds = new Set<string>();
      const collectDescendants = (parentId: string) => {
        store.model!.nodes.filter(n => n.parentId === parentId).forEach(n => {
          allDescendantIds.add(n.id);
          collectDescendants(n.id);
        });
      };
      collectDescendants(id);

      const remainingNodes = store.model.nodes.filter(n => !allDescendantIds.has(n.id));
      const existingIds = new Set(remainingNodes.map(n => n.id));
      const limiter = pLimit(3) as unknown as LimiterFn;

      const newChildren = await generateChildrenForNode(
        node,
        store.model.settings,
        store.model.scheme.language,
        existingIds,
        limiter
      );

      await store.saveNodes([...remainingNodes, ...newChildren]);
    } catch (err) {
      setRerunError(err instanceof Error ? err.message : 'Could not regenerate children for this concept.');
    } finally {
      setRerunningId(null);
    }
  }, [store]);

  const handleMerge = useCallback(async (sourceId: string, targetId: string) => {
    if (!store.model) return;
    const source = store.model.nodes.find(n => n.id === sourceId);
    const target = store.model.nodes.find(n => n.id === targetId);
    if (!source || !target) return;

    const mergedAltLabels = Array.from(new Set([...target.altLabels, source.prefLabel, ...source.altLabels]));

    await store.updateNode(targetId, {
      altLabels: mergedAltLabels,
    });

    const sourceChildren = store.model.nodes.filter(n => n.parentId === sourceId);
    for (const child of sourceChildren) {
      await store.updateNode(child.id, { parentId: targetId });
    }

    await store.deleteNode(sourceId);
    setSelectedId(targetId);
  }, [store]);

  const handleMove = useCallback(async (nodeId: string, newParentId: string | null) => {
    if (!store.model) return;
    const node = store.model.nodes.find(n => n.id === nodeId);
    if (!node) return;

    const newDepth = newParentId
      ? (store.model.nodes.find(n => n.id === newParentId)?.depth ?? 0) + 1
      : 1;

    await store.updateNode(nodeId, { parentId: newParentId, depth: newDepth });
  }, [store]);

  return (
    <div className="h-[calc(100vh-200px)] border rounded-lg overflow-hidden">
      <ResizablePanelGroup direction="horizontal">
        <ResizablePanel defaultSize={35} minSize={25}>
          <div className="h-full flex flex-col">
            <div className="px-3 py-2 border-b bg-muted/30">
              <h3 className="text-sm font-semibold">Taxonomy Tree</h3>
              <p className="text-xs text-muted-foreground">{nodes.length} nodes</p>
            </div>
            <ScrollArea className="flex-1">
              <TaxonomyTree
                nodes={nodes}
                selectedId={selectedId}
                onSelect={setSelectedId}
              />
            </ScrollArea>
          </div>
        </ResizablePanel>

        <ResizableHandle withHandle />

        <ResizablePanel defaultSize={65} minSize={40}>
          <ScrollArea className="h-full">
            {selectedNode ? (
              <NodeEditor
                node={selectedNode}
                allNodes={nodes}
                onSave={handleSave}
                onDelete={handleDelete}
                onRerunChildren={handleRerunChildren}
                onMerge={handleMerge}
                onMove={handleMove}
                rerunning={rerunningId === selectedNode.id}
                rerunError={rerunError}
              />
            ) : (
              <div className="flex items-center justify-center h-full text-sm text-muted-foreground p-8">
                Select a node from the tree to edit it.
              </div>
            )}
          </ScrollArea>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
