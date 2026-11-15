'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Settings, Save, Gauge, RotateCcw } from 'lucide-react';
import { DEFAULT_SETTINGS, LANGUAGES, SETTINGS_LIMITS } from '@/lib/types';
import type { TaxonomySettings } from '@/lib/types';
import { useTaxonomyStore } from '@/hooks/use-taxonomy-store';
import { estimateGeneration } from '@/lib/engine/estimate';

const settingsSchema = z.object({
  schemeTitle: z.string().min(1, 'Title is required'),
  language: z.string().min(1),
  baseUri: z.string().url('Must be a valid URL'),
  initialPrompt: z.string().min(1, 'A generation prompt is required'),
  maxDepth: z.number().int().min(SETTINGS_LIMITS.maxDepth.min).max(SETTINGS_LIMITS.maxDepth.max),
  maxChildrenPerNode: z.number().int().min(SETTINGS_LIMITS.maxChildrenPerNode.min).max(SETTINGS_LIMITS.maxChildrenPerNode.max),
});

type SettingsForm = z.infer<typeof settingsSchema>;

export function SettingsPanel() {
  const store = useTaxonomyStore();

  const form = useForm<SettingsForm>({
    resolver: zodResolver(settingsSchema),
    mode: 'onChange',
    defaultValues: {
      schemeTitle: 'My Taxonomy',
      language: 'en',
      baseUri: 'http://example.org/taxonomy/',
      initialPrompt: DEFAULT_SETTINGS.initialPrompt,
      maxDepth: DEFAULT_SETTINGS.maxDepth,
      maxChildrenPerNode: DEFAULT_SETTINGS.maxChildrenPerNode,
    },
  });

  // Reset the form when a (different) project loads, not on every store
  // mutation - the shared store now updates on every tab's activity (e.g.
  // a generation run committing progress), and resetting on every one of
  // those would silently wipe whatever the user is mid-typing here.
  useEffect(() => {
    if (store.model) {
      const s = store.model.settings;
      form.reset({
        schemeTitle: store.model.scheme.title,
        language: store.model.scheme.language,
        baseUri: store.model.scheme.baseUri,
        initialPrompt: s.initialPrompt || '',
        maxDepth: s.maxDepth,
        maxChildrenPerNode: s.maxChildrenPerNode,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [store.projectId]);

  const onSubmit = async (data: SettingsForm) => {
    const settings: TaxonomySettings = {
      maxDepth: data.maxDepth,
      maxChildrenPerNode: data.maxChildrenPerNode,
      initialPrompt: data.initialPrompt,
    };

    if (store.projectId) {
      await store.updateProject({
        title: data.schemeTitle,
        language: data.language,
        baseUri: data.baseUri,
        settings,
      });
    } else {
      await store.createProject(
        {
          id: '',
          title: data.schemeTitle,
          language: data.language,
          baseUri: data.baseUri,
          createdAt: new Date().toISOString(),
        },
        settings
      );
    }
  };

  // Clamp into the valid range for the estimate display specifically - an
  // out-of-range value already shows its own inline error below the field,
  // but the estimate must never show an absurd number (a genuine finding:
  // typing 9/50 produced "up to 39 trillion calls" before this clamp).
  const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value || min));
  const watchedDepth = clamp(form.watch('maxDepth'), SETTINGS_LIMITS.maxDepth.min, SETTINGS_LIMITS.maxDepth.max);
  const watchedBreadth = clamp(form.watch('maxChildrenPerNode'), SETTINGS_LIMITS.maxChildrenPerNode.min, SETTINGS_LIMITS.maxChildrenPerNode.max);
  const estimate = estimateGeneration(watchedDepth, watchedBreadth);
  const settingsOutOfRange = Boolean(form.formState.errors.maxDepth || form.formState.errors.maxChildrenPerNode);

  return (
    <div className="space-y-6 max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Taxonomy settings
          </CardTitle>
          <CardDescription>
            Configure the taxonomy scheme and generation parameters.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Scheme</h3>

              <div className="grid gap-2">
                <Label htmlFor="schemeTitle">Scheme Title</Label>
                <Input id="schemeTitle" {...form.register('schemeTitle')} />
                {form.formState.errors.schemeTitle && (
                  <p className="text-xs text-red-500">{form.formState.errors.schemeTitle.message}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label>Language</Label>
                  <Select
                    value={form.watch('language')}
                    onValueChange={(v) => form.setValue('language', v)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {LANGUAGES.map((lang) => (
                        <SelectItem key={lang.code} value={lang.code}>
                          {lang.label} ({lang.code})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="baseUri">Base URI</Label>
                  <Input id="baseUri" {...form.register('baseUri')} placeholder="http://example.org/taxonomy/" />
                  {form.formState.errors.baseUri && (
                    <p className="text-xs text-red-500">{form.formState.errors.baseUri.message}</p>
                  )}
                </div>
              </div>
            </div>

            <div className="border-t pt-6 space-y-4">
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Generation</h3>

              <div className="grid gap-2">
                <Label htmlFor="initialPrompt">Generation Prompt</Label>
                <Textarea
                  id="initialPrompt"
                  {...form.register('initialPrompt')}
                  placeholder="e.g., Build a taxonomy covering cybersecurity threats, mitigation strategies, and compliance frameworks"
                  rows={3}
                  className="resize-y"
                />
                <p className="text-xs text-muted-foreground">
                  Describe what this taxonomy should cover. This guides how the retrieval-and-answer
                  calls analyse your knowledge base.
                </p>
                {form.formState.errors.initialPrompt && (
                  <p className="text-xs text-red-500">{form.formState.errors.initialPrompt.message}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="maxDepth">
                    Max depth ({SETTINGS_LIMITS.maxDepth.min}-{SETTINGS_LIMITS.maxDepth.max})
                  </Label>
                  <Input
                    id="maxDepth"
                    type="number"
                    {...form.register('maxDepth', { valueAsNumber: true })}
                    min={SETTINGS_LIMITS.maxDepth.min}
                    max={SETTINGS_LIMITS.maxDepth.max}
                  />
                  {form.formState.errors.maxDepth && (
                    <p className="text-xs text-red-500">{form.formState.errors.maxDepth.message}</p>
                  )}
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="maxChildrenPerNode">
                    Max children per node ({SETTINGS_LIMITS.maxChildrenPerNode.min}-{SETTINGS_LIMITS.maxChildrenPerNode.max})
                  </Label>
                  <Input
                    id="maxChildrenPerNode"
                    type="number"
                    {...form.register('maxChildrenPerNode', { valueAsNumber: true })}
                    min={SETTINGS_LIMITS.maxChildrenPerNode.min}
                    max={SETTINGS_LIMITS.maxChildrenPerNode.max}
                  />
                  {form.formState.errors.maxChildrenPerNode && (
                    <p className="text-xs text-red-500">{form.formState.errors.maxChildrenPerNode.message}</p>
                  )}
                </div>
              </div>

              <div className="rounded-md border bg-muted/40 p-3 flex items-start gap-2.5 text-sm">
                <Gauge className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground" />
                <div>
                  <span className="font-medium">
                    Up to {estimate.calls} retrieval-and-answer calls, up to {estimate.maxNodes} concepts.
                  </span>
                  {settingsOutOfRange && (
                    <p className="text-xs text-destructive mt-0.5">
                      Shown for the nearest allowed depth/breadth - fix the field above to save.
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Depth and breadth are capped so a generation run always stays small and cheap -
                    this is a worst-case estimate, not a guarantee (the model often proposes fewer).
                  </p>
                </div>
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={!form.formState.isValid}>
              <Save className="mr-2 h-4 w-4" />
              Save Settings
            </Button>
            {!form.formState.isValid && (
              <p className="text-xs text-muted-foreground text-center -mt-3">
                Fix the highlighted field{Object.keys(form.formState.errors).length > 1 ? 's' : ''} above to save.
              </p>
            )}
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <RotateCcw className="h-4 w-4" />
            Reset
          </CardTitle>
          <CardDescription>
            Clear the current taxonomy and start a fresh project. This only clears data stored in
            this browser - it does not change anything in the knowledge base.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="outline" onClick={() => store.resetProject()}>
            Reset this project
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
