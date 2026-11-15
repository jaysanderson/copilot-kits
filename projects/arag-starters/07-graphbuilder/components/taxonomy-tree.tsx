'use client';

import { useState } from 'react';
import { ChevronRight, ChevronDown, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { TaxonomyNode } from '@/lib/types';

interface TaxonomyTreeProps {
  nodes: TaxonomyNode[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

interface TreeNodeProps {
  node: TaxonomyNode;
  childNodes: TaxonomyNode[];
  allNodes: TaxonomyNode[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  depth: number;
}

function TreeNode({ node, childNodes, allNodes, selectedId, onSelect, depth }: TreeNodeProps) {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = childNodes.length > 0;
  const isSelected = selectedId === node.id;

  return (
    <div>
      <div
        className={cn(
          'flex items-center gap-1 px-2 py-1.5 rounded-md cursor-pointer text-sm transition-colors',
          isSelected ? 'bg-primary/10 text-primary font-medium' : 'hover:bg-muted',
        )}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={() => onSelect(node.id)}
      >
        {hasChildren ? (
          <button
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
            className="p-0.5 rounded hover:bg-muted-foreground/10"
          >
            {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
          </button>
        ) : (
          <FileText className="h-3.5 w-3.5 ml-0.5 text-muted-foreground" />
        )}

        <span className="truncate flex-1 min-w-0">{node.prefLabel}</span>
      </div>

      {expanded && hasChildren && (
        <div>
          {childNodes.map(child => (
            <TreeNode
              key={child.id}
              node={child}
              childNodes={allNodes.filter(n => n.parentId === child.id)}
              allNodes={allNodes}
              selectedId={selectedId}
              onSelect={onSelect}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function TaxonomyTree({ nodes, selectedId, onSelect }: TaxonomyTreeProps) {
  const rootNodes = nodes
    .filter(n => n.parentId === null)
    .sort((a, b) => a.sortOrder - b.sortOrder);

  if (nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-muted-foreground p-4">
        No taxonomy nodes yet. Run generation first.
      </div>
    );
  }

  return (
    <div className="py-2">
      {rootNodes.map(node => (
        <TreeNode
          key={node.id}
          node={node}
          childNodes={nodes.filter(n => n.parentId === node.id).sort((a, b) => a.sortOrder - b.sortOrder)}
          allNodes={nodes}
          selectedId={selectedId}
          onSelect={onSelect}
          depth={0}
        />
      ))}
    </div>
  );
}
