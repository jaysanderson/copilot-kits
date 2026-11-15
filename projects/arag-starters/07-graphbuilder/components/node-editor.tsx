'use client';

import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Save, RefreshCw, Trash2, Merge, Move, X, Loader2, AlertTriangle } from 'lucide-react';
import type { TaxonomyNode } from '@/lib/types';

interface NodeEditorProps {
  node: TaxonomyNode;
  allNodes: TaxonomyNode[];
  onSave: (id: string, updates: Partial<TaxonomyNode>) => void;
  onDelete: (id: string) => void;
  onRerunChildren: (id: string) => void;
  onMerge: (sourceId: string, targetId: string) => void;
  onMove: (nodeId: string, newParentId: string | null) => void;
  rerunning?: boolean;
  rerunError?: string | null;
}

export function NodeEditor({ node, allNodes, onSave, onDelete, onRerunChildren, onMerge, onMove, rerunning, rerunError }: NodeEditorProps) {
  const [prefLabel, setPrefLabel] = useState(node.prefLabel);
  const [definition, setDefinition] = useState(node.definition);
  const [altLabels, setAltLabels] = useState<string[]>(node.altLabels);
  const [seedQueries, setSeedQueries] = useState<string[]>(node.seedQueries);
  const [altInput, setAltInput] = useState('');
  const [seedInput, setSeedInput] = useState('');
  const [mergeTarget, setMergeTarget] = useState('');
  const [moveTarget, setMoveTarget] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showMergeDialog, setShowMergeDialog] = useState(false);
  const [showMoveDialog, setShowMoveDialog] = useState(false);

  useEffect(() => {
    setPrefLabel(node.prefLabel);
    setDefinition(node.definition);
    setAltLabels([...node.altLabels]);
    setSeedQueries([...node.seedQueries]);
    setAltInput('');
    setSeedInput('');
  }, [node]);

  const handleSave = useCallback(() => {
    onSave(node.id, { prefLabel, definition, altLabels, seedQueries });
  }, [node.id, prefLabel, definition, altLabels, seedQueries, onSave]);

  const addAltLabel = () => {
    const v = altInput.trim();
    if (v && !altLabels.includes(v)) {
      setAltLabels([...altLabels, v]);
      setAltInput('');
    }
  };

  const addSeedQuery = () => {
    const v = seedInput.trim();
    if (v && !seedQueries.includes(v)) {
      setSeedQueries([...seedQueries, v]);
      setSeedInput('');
    }
  };

  const siblings = allNodes.filter(n => n.parentId === node.parentId && n.id !== node.id);
  const validMoveTargets = allNodes.filter(n => {
    if (n.id === node.id) return false;
    let current: string | null = n.id;
    const visited = new Set<string>();
    while (current) {
      if (current === node.id) return false;
      if (visited.has(current)) break;
      visited.add(current);
      current = allNodes.find(x => x.id === current)?.parentId ?? null;
    }
    return true;
  });

  const childCount = allNodes.filter(n => n.parentId === node.id).length;

  return (
    <div className="space-y-4 p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-semibold text-lg truncate min-w-0">{node.prefLabel}</h3>
        <Badge variant="secondary" className="shrink-0">Depth {node.depth}</Badge>
      </div>

      {rerunError && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700 flex items-start gap-2">
          <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
          <span>{rerunError}</span>
        </div>
      )}

      <div className="grid gap-3">
        <div className="grid gap-1.5">
          <Label htmlFor="prefLabel">Preferred Label</Label>
          <Input id="prefLabel" value={prefLabel} onChange={e => setPrefLabel(e.target.value)} />
        </div>

        <div className="grid gap-1.5">
          <Label htmlFor="definition">Definition</Label>
          <Textarea id="definition" value={definition} onChange={e => setDefinition(e.target.value)} rows={3} />
        </div>

        <div className="grid gap-1.5">
          <Label>Alternative Labels</Label>
          <div className="flex flex-wrap gap-1.5 mb-1">
            {altLabels.map((label, i) => (
              <Badge key={i} variant="secondary" className="gap-1">
                {label}
                <button onClick={() => setAltLabels(altLabels.filter((_, j) => j !== i))}>
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              value={altInput}
              onChange={e => setAltInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addAltLabel())}
              placeholder="Add alt label..."
            />
            <Button type="button" variant="outline" size="sm" onClick={addAltLabel}>Add</Button>
          </div>
        </div>

        <div className="grid gap-1.5">
          <Label>Seed Queries</Label>
          <div className="flex flex-wrap gap-1.5 mb-1">
            {seedQueries.map((q, i) => (
              <Badge key={i} variant="outline" className="gap-1">
                {q}
                <button onClick={() => setSeedQueries(seedQueries.filter((_, j) => j !== i))}>
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              value={seedInput}
              onChange={e => setSeedInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addSeedQuery())}
              placeholder="Add seed query..."
            />
            <Button type="button" variant="outline" size="sm" onClick={addSeedQuery}>Add</Button>
          </div>
        </div>
      </div>

      <Card className="p-3 text-center w-fit">
        <div className="text-xl font-bold">{childCount}</div>
        <div className="text-[11px] text-muted-foreground">Children</div>
      </Card>

      <div className="flex flex-wrap gap-2 pt-3 border-t">
        <Button onClick={handleSave} size="sm">
          <Save className="mr-1 h-3.5 w-3.5" />
          Save
        </Button>

        <Button variant="outline" size="sm" onClick={() => onRerunChildren(node.id)} disabled={rerunning}>
          {rerunning ? (
            <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
          ) : (
            <RefreshCw className="mr-1 h-3.5 w-3.5" />
          )}
          {rerunning ? 'Regenerating...' : 'Re-run Children'}
        </Button>

        {siblings.length > 0 && (
          <Dialog open={showMergeDialog} onOpenChange={setShowMergeDialog}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <Merge className="mr-1 h-3.5 w-3.5" />
                Merge
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Merge Node</DialogTitle>
                <DialogDescription>
                  Select a sibling node to merge &quot;{node.prefLabel}&quot; into.
                </DialogDescription>
              </DialogHeader>
              <Select value={mergeTarget} onValueChange={setMergeTarget}>
                <SelectTrigger>
                  <SelectValue placeholder="Select sibling..." />
                </SelectTrigger>
                <SelectContent>
                  {siblings.map(s => (
                    <SelectItem key={s.id} value={s.id}>{s.prefLabel}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <DialogFooter>
                <Button
                  disabled={!mergeTarget}
                  onClick={() => { onMerge(node.id, mergeTarget); setMergeTarget(''); setShowMergeDialog(false); }}
                >
                  Merge
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}

        <Dialog open={showMoveDialog} onOpenChange={setShowMoveDialog}>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm">
              <Move className="mr-1 h-3.5 w-3.5" />
              Move
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Move Node</DialogTitle>
              <DialogDescription>
                Select a new parent for &quot;{node.prefLabel}&quot;.
              </DialogDescription>
            </DialogHeader>
            <Select value={moveTarget} onValueChange={setMoveTarget}>
              <SelectTrigger>
                <SelectValue placeholder="Select new parent..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__root__">(Top Level - No Parent)</SelectItem>
                {validMoveTargets.map(t => (
                  <SelectItem key={t.id} value={t.id}>{t.prefLabel}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <DialogFooter>
              <Button
                disabled={!moveTarget}
                onClick={() => {
                  onMove(node.id, moveTarget === '__root__' ? null : moveTarget);
                  setMoveTarget('');
                  setShowMoveDialog(false);
                }}
              >
                Move
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
          <DialogTrigger asChild>
            <Button variant="destructive" size="sm">
              <Trash2 className="mr-1 h-3.5 w-3.5" />
              Delete
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Node</DialogTitle>
              <DialogDescription>
                This will delete &quot;{node.prefLabel}&quot; and all its descendants ({childCount} children). This cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowDeleteConfirm(false)}>Cancel</Button>
              <Button variant="destructive" onClick={() => { onDelete(node.id); setShowDeleteConfirm(false); }}>
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
