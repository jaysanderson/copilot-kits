'use client';

import { useState, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Play, Square, Loader2, CheckCircle2, AlertTriangle, Gauge } from 'lucide-react';
import { useTaxonomyStore } from '@/hooks/use-taxonomy-store';
import { runTaxonomyGeneration } from '@/lib/engine/run';
import { estimateGeneration } from '@/lib/engine/estimate';
import type { GenerationProgress } from '@/lib/types';

export function GeneratePanel() {
  const store = useTaxonomyStore();
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState<GenerationProgress | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [showReplaceConfirm, setShowReplaceConfirm] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const existingNodeCount = store.model?.nodes.length ?? 0;

  const addLog = useCallback((msg: string) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
  }, []);

  const runGeneration = useCallback(async () => {
    if (!store.model) {
      setError('Save settings first before generating.');
      return;
    }

    setRunning(true);
    setError(null);
    setLogs([]);
    setWarnings([]);
    abortRef.current = new AbortController();

    addLog('Starting taxonomy generation...');

    try {
      await store.updateProject({ status: 'generating' });

      const result = await runTaxonomyGeneration({
        settings: store.model.settings,
        scheme: store.model.scheme,
        signal: abortRef.current.signal,
        onProgress: (p) => {
          setProgress({ ...p });
          setWarnings(p.warnings ?? []);
          addLog(p.message);
        },
      });

      await store.saveNodes(result.nodes);
      await store.updateProject({
        status: 'complete',
        metrics: result.metrics,
      });

      addLog(`Generation complete: ${result.nodes.length} nodes in ${result.metrics.generationSeconds.toFixed(1)}s`);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Generation failed';
      if (message === 'Aborted') {
        addLog('Generation stopped by user.');
        await store.updateProject({ status: 'draft' });
      } else {
        setError(message);
        addLog(`Error: ${message}`);
        await store.updateProject({ status: 'draft' });
      }
    } finally {
      setRunning(false);
      abortRef.current = null;
    }
  }, [store, addLog]);

  const handleGenerateClick = useCallback(() => {
    // A completed taxonomy already exists (possibly hand-edited in Review) -
    // running generation again replaces it entirely, so confirm first
    // rather than silently discarding a user's edits.
    if (existingNodeCount > 0) {
      setShowReplaceConfirm(true);
      return;
    }
    void runGeneration();
  }, [existingNodeCount, runGeneration]);

  const handleConfirmReplace = useCallback(() => {
    setShowReplaceConfirm(false);
    void runGeneration();
  }, [runGeneration]);

  const handleStop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const formatTime = (ms: number) => {
    const s = Math.floor(ms / 1000);
    const m = Math.floor(s / 60);
    return m > 0 ? `${m}m ${s % 60}s` : `${s}s`;
  };

  const depthProgress = progress?.maxDepth
    ? ((progress.currentDepth ?? 1) / progress.maxDepth) * 100
    : 0;

  return (
    <div className="space-y-6 max-w-3xl">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="h-5 w-5" />
            Generate taxonomy
          </CardTitle>
          <CardDescription>
            Build a hierarchical taxonomy from your knowledge base documents.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!store.model && (
            <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700">
              <AlertTriangle className="inline mr-1 h-4 w-4" />
              Configure and save settings before generating.
            </div>
          )}

          {store.model && !store.model.settings.initialPrompt && (
            <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700">
              <AlertTriangle className="inline mr-1 h-4 w-4" />
              No generation prompt set. Go to Settings to describe what this taxonomy should cover.
            </div>
          )}

          {store.model?.settings.initialPrompt && (
            <div className="rounded-md border bg-muted/40 p-3 text-sm">
              <span className="font-medium text-muted-foreground">Prompt: </span>
              <span className="text-foreground">{store.model.settings.initialPrompt}</span>
            </div>
          )}

          {!running && existingNodeCount > 0 && (
            <div className="rounded-md border bg-muted/40 p-3 text-sm flex items-start gap-2.5">
              <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" style={{ color: 'hsl(var(--arag-success-fg))' }} />
              <span>
                You already have a <strong>{existingNodeCount}-concept</strong> taxonomy from a
                previous run. Generating again will replace it entirely - review or export it
                first if you want to keep it.
              </span>
            </div>
          )}

          {store.model && (() => {
            const est = estimateGeneration(store.model.settings.maxDepth, store.model.settings.maxChildrenPerNode);
            return (
              <div className="rounded-md border bg-muted/40 p-3 flex items-start gap-2.5 text-sm">
                <Gauge className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground" />
                <span>
                  This run will make up to <strong>{est.calls}</strong> retrieval-and-answer calls
                  and produce up to <strong>{est.maxNodes}</strong> concepts. Adjust in Settings if
                  you want a smaller or larger taxonomy.
                </span>
              </div>
            );
          })()}

          <div className="flex items-center gap-3">
            <Button
              onClick={handleGenerateClick}
              disabled={running || !store.model}
              className="min-w-[180px]"
            >
              {running ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  {existingNodeCount > 0 ? 'Regenerate Taxonomy' : 'Generate Taxonomy'}
                </>
              )}
            </Button>

            {running && (
              <Button variant="destructive" onClick={handleStop}>
                <Square className="mr-2 h-4 w-4" />
                Stop
              </Button>
            )}
          </div>

          {progress && (
            <div className="space-y-3 pt-4 border-t">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium capitalize">{progress.step.replace('-', ' ')}</span>
                <span className="text-muted-foreground">{formatTime(progress.elapsedMs)}</span>
              </div>

              <Progress value={depthProgress} className="h-2" />

              <div className="rounded-md border p-3 text-center w-fit">
                <div className="text-2xl font-bold">{progress.nodesCreated}</div>
                <div className="text-xs text-muted-foreground">Nodes Created</div>
              </div>

              {progress.currentNode && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-3 w-3 animate-spin shrink-0" />
                  <span className="truncate min-w-0 flex-1">{progress.currentNode}</span>
                  {progress.currentDepth && (
                    <Badge variant="secondary" className="text-xs shrink-0">
                      Depth {progress.currentDepth}/{progress.maxDepth}
                    </Badge>
                  )}
                </div>
              )}

              {progress.step === 'complete' && (
                <div className="flex items-center gap-2 text-sm text-emerald-600">
                  <CheckCircle2 className="h-4 w-4" />
                  Generation complete
                </div>
              )}
            </div>
          )}

          {warnings.length > 0 && (
            <div className="rounded-md border border-amber-200 bg-amber-50 p-3 space-y-1">
              <div className="flex items-center gap-1.5 text-sm font-medium text-amber-800">
                <AlertTriangle className="h-4 w-4" />
                {warnings.length} node{warnings.length > 1 ? 's' : ''} skipped due to LLM errors
              </div>
              <ul className="text-xs text-amber-700 space-y-0.5 pl-5 list-disc">
                {warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {logs.length > 0 && (
            <div className="pt-4 border-t">
              <h4 className="text-sm font-medium mb-2">Generation Log</h4>
              <ScrollArea className="h-48 rounded-md border bg-muted/30 p-3">
                <div className="space-y-1 font-mono text-xs">
                  {logs.map((log, i) => (
                    <div
                      key={i}
                      className={
                        log.includes('Warning:')
                          ? 'text-amber-600'
                          : log.includes('Error:')
                          ? 'text-red-600'
                          : 'text-muted-foreground'
                      }
                    >
                      {log}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={showReplaceConfirm} onOpenChange={setShowReplaceConfirm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Replace the current taxonomy?</DialogTitle>
            <DialogDescription>
              This will discard your existing {existingNodeCount}-concept taxonomy, including any
              edits, merges or moves made in Review, and generate a brand new one. This cannot be
              undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowReplaceConfirm(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleConfirmReplace}>Discard and regenerate</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
