import { useMemo, useState } from 'react';
import { Play, CheckCircle2, ShieldAlert, X } from 'lucide-react';
import { Button } from '@progress/kendo-react-buttons';
import { Input } from '@progress/kendo-react-inputs';
import { Card, CardBody } from '@progress/kendo-react-layout';
import { Grid, GridColumn, type GridCustomCellProps } from '@progress/kendo-react-grid';
import {
  Chart,
  ChartSeries,
  ChartSeriesItem,
  ChartSeriesLabels,
  ChartLegend,
} from '@progress/kendo-react-charts';
import type { SurfaceProps } from './types';
import { ask, remi, type Citation } from '../lib/arag';
import { PageHeader } from '../components/PageHeader';
import { chartPalette } from '../lib/chartTheme';
import { ErrorBanner } from '../components/States';

// Groundedness dashboard (REMi surface) — module 4.1, ported to the REAL
// scoring call. Fix 9 (spec Section 3.A): this used to score "grounded"
// purely on `citations.length > 0` — a citation-COUNT proxy, not the RAG-triad
// score the `remi` capability is named and sold as. Every probe now runs the
// same grounded /ask path AND a real POST {kb}/predict/remi call scored
// against the full retrieved context (never just the cited excerpt — see
// lib/arag.ts's `remi()` docstring for why that distinction is load-bearing).
// The dashboard reports the mean groundedness score, not a citation-presence rate.

interface Probe {
  q: string;
  state: 'idle' | 'running' | 'scored' | 'ungrounded' | 'error';
  sources?: number;
  groundedness?: number | null;
  answerRelevance?: number | null;
  contextRelevance?: number | null;
  note?: string;
}
type ProbeRow = Probe & { _i: number };

function askOnce(query: string): Promise<{ answer: string; citations: Citation[]; contexts: string[] }> {
  return new Promise((resolve, reject) => {
    let answer = '';
    let citations: Citation[] = [];
    let contexts: string[] = [];
    ask(
      { query },
      {
        onToken: (t) => { answer += t; },
        onCitations: (c) => { citations = c; },
        onContexts: (c) => { contexts = c; },
        onError: reject,
        onDone: () => resolve({ answer, citations, contexts }),
      }
    );
  });
}

function scriptProbes(config: SurfaceProps['config']): string[] {
  const out: string[] = [];
  for (const s of config.demoScript || []) {
    const m = (s.show || '').match(/[‘'"“]([^’'"”]{6,})[’'"”]/);
    if (m) out.push(m[1]);
  }
  return out;
}

export function RemiSurface({ surface, config }: SurfaceProps) {
  const initial = useMemo(() => scriptProbes(config), [config]);
  const [probes, setProbes] = useState<Probe[]>(initial.map((q) => ({ q, state: 'idle' })));
  const [draft, setDraft] = useState('');
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const scored = probes.filter((p) => p.state === 'scored' || p.state === 'ungrounded');
  const groundednessScores = probes
    .map((p) => p.groundedness)
    .filter((v): v is number => typeof v === 'number');
  // Mean REAL groundedness (0-5), not a citation-presence rate — the fix 9 replacement metric.
  const meanGroundedness = groundednessScores.length
    ? groundednessScores.reduce((a, b) => a + b, 0) / groundednessScores.length
    : null;
  const rate = meanGroundedness == null ? null : Math.round((meanGroundedness / 5) * 100);
  const ungroundedCount = probes.filter((p) => p.state === 'ungrounded').length;

  const runAll = async () => {
    if (!probes.length || running) return;
    setRunning(true);
    setError(null);
    for (let i = 0; i < probes.length; i++) {
      setProbes((prev) => prev.map((p, idx) => (idx === i ? { ...p, state: 'running' } : p)));
      try {
        const { citations, contexts, answer } = await askOnce(probes[i].q);
        const n = citations.length;
        if (n === 0) {
          // No citations at all — nothing for REMi to score; an honest refusal/ungrounded state.
          setProbes((prev) => prev.map((p, idx) => (idx === i ? { ...p, state: 'ungrounded', sources: 0 } : p)));
          continue;
        }
        // Fix 9: the REAL RAG-triad score, scored against the FULL retrieved
        // context (not just the cited excerpt) — same call shape as useRemi().
        const score = await remi({ question: probes[i].q, answer, contexts });
        setProbes((prev) =>
          prev.map((p, idx) =>
            idx === i
              ? {
                  ...p,
                  state: 'scored',
                  sources: n,
                  groundedness: score.groundedness,
                  answerRelevance: score.answerRelevance,
                  contextRelevance: score.contextRelevance,
                }
              : p
          )
        );
      } catch (e: any) {
        setError(e.message);
        setProbes((prev) => prev.map((p, idx) => (idx === i ? { ...p, state: 'error', note: e.message } : p)));
      }
    }
    setRunning(false);
  };

  const addProbe = () => {
    const q = draft.trim();
    if (!q) return;
    setProbes((prev) => [...prev, { q, state: 'idle' }]);
    setDraft('');
  };
  const removeProbe = (i: number) => setProbes((prev) => prev.filter((_, idx) => idx !== i));

  const rows: ProbeRow[] = probes.map((p, i) => ({ ...p, _i: i }));

  // Custom Grid cells ------------------------------------------------------
  const StatusCell = (props: GridCustomCellProps) => {
    const p = props.dataItem as ProbeRow;
    return (
      <td>
        <span className="inline-flex items-center gap-2">
          <StateGlyph state={p.state} />
          <span className="text-sm">
            {p.state === 'scored' &&
              `Groundedness ${p.groundedness?.toFixed(1)}/5 · relevance ${p.answerRelevance?.toFixed(1)}/5 · ${p.sources} source${p.sources === 1 ? '' : 's'}`}
            {p.state === 'ungrounded' && 'Ungrounded — no citations, nothing for REMi to score'}
            {p.state === 'running' && 'Asking, then scoring with REMi…'}
            {p.state === 'idle' && 'Not yet run'}
            {p.state === 'error' && (p.note || 'Error')}
          </span>
        </span>
      </td>
    );
  };
  const ProbeCell = (props: GridCustomCellProps) => {
    const p = props.dataItem as ProbeRow;
    return <td><span className="text-sm font-medium text-ink-900 dark:text-ink-100">{p.q}</span></td>;
  };
  const RemoveCell = (props: GridCustomCellProps) => {
    const p = props.dataItem as ProbeRow;
    return (
      <td>
        <Button fillMode="flat" size="small" onClick={() => removeProbe(p._i)} aria-label="Remove probe">
          <X size={15} />
        </Button>
      </td>
    );
  };

  return (
    <div>
      <PageHeader
        icon={surface.icon}
        title="Groundedness"
        actions={
          <Button themeColor="primary" onClick={runAll} disabled={running || !probes.length} startIcon={<Play size={15} />}>
            {running ? 'Running sweep…' : 'Run REMi sweep'}
          </Button>
        }
      >
        A live check that scores every answer with REMi's real RAG-triad — groundedness, answer relevance,
        context relevance, each 0-5 — scored server-side against the retrieved context. Not a
        citation-count proxy: an answer with citations can still score low if the answer strays from what
        those sources actually say.
      </PageHeader>

      {error && <div className="mb-4"><ErrorBanner>{error}</ErrorBanner></div>}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[18rem_1fr]">
        {/* Quality chart */}
        <Card>
          <CardBody className="flex flex-col items-center justify-center p-6">
            <GroundedDonut scored={scored.length} ungrounded={ungroundedCount} rate={rate} />
            <p className="mt-3 text-center text-sm font-medium text-ink-700 dark:text-ink-200">
              Mean REMi groundedness
            </p>
            <p className="mt-1 text-center text-xs text-ink-500">
              {meanGroundedness != null
                ? `${meanGroundedness.toFixed(1)}/5 across ${groundednessScores.length} scored answer${groundednessScores.length === 1 ? '' : 's'}`
                : 'Run the sweep to measure'}
            </p>
          </CardBody>
        </Card>

        {/* Probes */}
        <div className="space-y-3">
          <Card>
            <CardBody className="flex items-center gap-2 p-2">
              <Input
                value={draft}
                onChange={(e) => setDraft(String(e.value))}
                onKeyDown={(e) => e.key === 'Enter' && addProbe()}
                placeholder="Add a probe question…"
                className="flex-1"
              />
              <Button fillMode="outline" onClick={addProbe}>Add</Button>
            </CardBody>
          </Card>

          {probes.length === 0 ? (
            <p className="text-sm text-ink-500">No probes yet — add a few questions to measure groundedness.</p>
          ) : (
            <Grid data={rows} className="bg-transparent">
              <GridColumn field="q" title="Probe" cells={{ data: ProbeCell }} />
              <GridColumn title="Status" width="220px" cells={{ data: StatusCell }} />
              <GridColumn title="" width="60px" cells={{ data: RemoveCell }} />
            </Grid>
          )}
        </div>
      </div>
    </div>
  );
}

function StateGlyph({ state }: { state: Probe['state'] }) {
  if (state === 'scored') return <CheckCircle2 size={18} className="shrink-0 text-emerald-500" />;
  if (state === 'ungrounded' || state === 'error') return <ShieldAlert size={18} className="shrink-0 text-amber-500" />;
  if (state === 'running')
    return <span className="h-3.5 w-3.5 shrink-0 animate-spin rounded-full border-2 border-ink-300 border-t-transparent" />;
  return <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-ink-300" />;
}

// Mean REMi groundedness as a KendoReact donut chart — the vendor control,
// themed to the demo's brand/accent and animated in on data. A soft brand
// glow sits AROUND the chart (CSS only) so it reads as a luminous score dial
// while the chart itself stays a Kendo component. `rate` is the mean real
// groundedness score (0-5) expressed as a percentage, not a citation rate.
function GroundedDonut({ ungrounded, rate }: { scored: number; ungrounded: number; rate: number | null }) {
  const { brand, accent, track } = chartPalette();
  const data =
    rate == null
      ? [{ category: 'Not run', value: 1, color: track }]
      : [
          { category: 'Groundedness', value: rate, color: brand },
          { category: 'Remaining', value: Math.max(0, 100 - rate), color: track },
          ...(ungrounded > 0 ? [{ category: 'Ungrounded probes', value: ungrounded, color: accent }] : []),
        ];
  return (
    <div className="relative h-44 w-44">
      {/* Brand light bloom behind the vendor chart. */}
      {rate != null && (
        <div
          className="pointer-events-none absolute inset-4 rounded-full blur-2xl"
          style={{ background: 'radial-gradient(circle, color-mix(in srgb, var(--brand) 42%, transparent), transparent 70%)' }}
          aria-hidden
        />
      )}
      <Chart style={{ height: 176, width: 176 }} className="relative" transitions>
        <ChartLegend visible={false} />
        <ChartSeries>
          <ChartSeriesItem
            type="donut"
            data={data}
            field="value"
            categoryField="category"
            colorField="color"
            holeSize={58}
            startAngle={90}
          >
            <ChartSeriesLabels visible={false} />
          </ChartSeriesItem>
        </ChartSeries>
      </Chart>
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <span className="font-display text-2xl font-bold text-ink-900 dark:text-ink-50">
          {rate == null ? '—' : `${rate}%`}
        </span>
      </div>
    </div>
  );
}
