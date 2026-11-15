'use client';

import { useState, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Download, Upload, FileCode, FileJson, Eye } from 'lucide-react';
import { useTaxonomyStore } from '@/hooks/use-taxonomy-store';
import { exportSkosXlTurtle } from '@/lib/exportSkosXlTurtle';
import { exportModelAsJson, downloadFile } from '@/lib/exportJson';
import { readFileAsJson, validateImportedJson } from '@/lib/importJson';

export function ExportPanel() {
  const store = useTaxonomyStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  const model = store.model;
  const hasNodes = model && model.nodes.length > 0;

  const handleExportTurtle = useCallback(() => {
    if (!model) return;
    const ttl = exportSkosXlTurtle(model);
    const filename = `${model.scheme.title.replace(/\s+/g, '_')}.ttl`;
    downloadFile(ttl, filename, 'text/turtle');
  }, [model]);

  const handleExportJson = useCallback(() => {
    if (!model) return;
    const json = exportModelAsJson(model);
    const filename = `${model.scheme.title.replace(/\s+/g, '_')}.json`;
    downloadFile(json, filename, 'application/json');
  }, [model]);

  const handlePreview = useCallback(() => {
    if (!model) return;
    const ttl = exportSkosXlTurtle(model);
    setPreview(ttl);
  }, [model]);

  const handleImport = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImportError(null);

    try {
      const raw = await readFileAsJson(file);
      const result = validateImportedJson(raw);

      if (!result.valid) {
        setImportError(`Validation errors:\n${result.errors.join('\n')}`);
        return;
      }

      await store.loadFromJson(result.model);
      setImportError(null);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Import failed');
    }

    if (fileInputRef.current) fileInputRef.current.value = '';
  }, [store]);

  const maxDepth = model ? Math.max(0, ...model.nodes.map(n => n.depth)) : 0;

  return (
    <div className="space-y-6 max-w-3xl">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Export taxonomy
          </CardTitle>
          <CardDescription>
            Download your taxonomy as SKOS-XL Turtle for Semaphore or as JSON for re-editing.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {model && (
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-md border p-3 text-center">
                <div className="text-lg font-bold">{model.nodes.length}</div>
                <div className="text-xs text-muted-foreground">Concepts</div>
              </div>
              <div className="rounded-md border p-3 text-center">
                <div className="text-lg font-bold">{maxDepth}</div>
                <div className="text-xs text-muted-foreground">Max Depth</div>
              </div>
              <div className="rounded-md border p-3 text-center">
                <div className="text-lg font-bold">{model.scheme.language}</div>
                <div className="text-xs text-muted-foreground">Language</div>
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-3 pt-2">
            <Button onClick={handleExportTurtle} disabled={!hasNodes}>
              <FileCode className="mr-2 h-4 w-4" />
              Download SKOS-XL Turtle (.ttl)
            </Button>
            <Button variant="outline" onClick={handleExportJson} disabled={!hasNodes}>
              <FileJson className="mr-2 h-4 w-4" />
              Download JSON Model
            </Button>
            <Button variant="outline" onClick={handlePreview} disabled={!hasNodes}>
              <Eye className="mr-2 h-4 w-4" />
              Preview Turtle
            </Button>
          </div>

          {preview && (
            <div className="pt-4 border-t">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium">Turtle Preview</h4>
                <Button variant="ghost" size="sm" onClick={() => setPreview(null)}>Close</Button>
              </div>
              <ScrollArea className="h-80 rounded-md border bg-muted/30">
                <pre className="p-4 text-xs font-mono whitespace-pre-wrap">{preview}</pre>
              </ScrollArea>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Import JSON model
          </CardTitle>
          <CardDescription>
            Load a previously exported taxonomy JSON file to continue editing.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleImport}
            className="block w-full text-sm text-muted-foreground
              file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0
              file:text-sm file:font-medium file:bg-primary file:text-primary-foreground
              hover:file:bg-primary/90 cursor-pointer"
          />

          {importError && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700 whitespace-pre-wrap">
              {importError}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
