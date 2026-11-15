import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle2, Loader2, ShieldAlert, Bot, Compass, Wrench, FileSearch, Sparkles, ChevronDown, Terminal, ShieldCheck, FileText, ArrowRight, Layers,
} from 'lucide-react';
import { runAgent, type RaoEvent, type KbSource } from '../lib/rao';
import { renderMarkdown } from '../lib/markdown';
import { usePrefersReducedMotion } from '../lib/motion';

// ─────────────────────────────────────────────────────────────────────────────
// Standard B11 (arag-demo-app skill) — RAO "watch it work" is a rich surface
// driven by the REAL NDJSON stream, not a flat log list. Each stage the stream
// emits (plan, tool call, tool result, composing) gets its own colour, icon and
// lane on a live timeline. Nothing here is invented — every lane renders only
// what server/rao.mjs actually mapped off ARAG's own trace.
//
// Steve Jobs review, 17 Aug 2026 — two changes:
//   (a) HUMAN trace. The lane text is human language now ("Planning the check",
//       "Looking up the client's holdings", "Composing a grounded answer") -
//       machine jargon ("Reactive iteration 2/5") is retired in server/rao.mjs's
//       mapper, the single source of truth for what each lane says.
//   (b) SAME CLASS of trust furniture as every other answer surface, honestly
//       adapted. The answer no longer deflates into a plain markdown box: it
//       renders in the same grounded-answer card, with a right rail carrying a
//       "live-data grounding" trust card + the exact tool calls it grounded on
//       (the citation analog). Deliberately NOT a REMi triad here: REMi scores
//       an answer against retrieved TEXT context, but the Concierge grounds on
//       structured live tool RESULTS, and the agent trace only exposes thin
//       tool-result summary lines (not the payloads), so a /predict/remi call
//       over them flashes an artificially low groundedness on a correct answer
//       - which hard rule 3 + the REMi-stability mandate forbid showing. The
//       honest parity is the tool trail itself: every claim traces to a visible
//       tool call, which IS this surface's measurable trust.
// ─────────────────────────────────────────────────────────────────────────────

interface TraceStep {
  id: number;
  stage: RaoEvent['stage'];
  text: string;
  ok?: boolean;
  tool?: string;
  detail?: string;
}

const STAGE_META: Record<string, { label: string; icon: typeof Bot; tint: string }> = {
  plan: { label: 'Planning', icon: Compass, tint: '#7c6df2' },
  tool_call: { label: 'Tool call', icon: Wrench, tint: 'var(--brand)' },
  tool_result: { label: 'Tool result', icon: CheckCircle2, tint: '#0ca30c' },
  doc_search: { label: 'Working', icon: FileSearch, tint: 'var(--accent)' },
  composing: { label: 'Composing', icon: Sparkles, tint: 'var(--brand)' },
};

export interface AgentTraceProps {
  /** Real MCP tools this agent can call — shown as an idle capability preview so the surface has presence before a query runs (never invented; pass the app's actual server/index.mjs tool registry). */
  tools?: { name: string; description: string; icon?: typeof Bot }[];
  /** Sample prompts rendered as clickable chips in the idle state, before the first query runs. */
  suggestions?: string[];
}

export function AgentTrace({ tools, suggestions }: AgentTraceProps = {}) {
  const navigate = useNavigate();
  const [steps, setSteps] = useState<TraceStep[]>([]);
  const [answer, setAnswer] = useState<string | null>(null);
  const [kbSources, setKbSources] = useState<KbSource[]>([]);
  const [honestState, setHonestState] = useState<{ stage: string; message: string } | null>(null);
  const [running, setRunning] = useState(false);
  const [query, setQuery] = useState('');
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const idRef = useRef(0);
  const abortRef = useRef<null | (() => void)>(null);
  const timelineRef = useRef<HTMLOListElement>(null);
  const reduced = usePrefersReducedMotion();

  const run = useCallback((q: string) => {
    const text = q.trim();
    if (!text || running) return;
    abortRef.current?.();
    setSteps([]); setAnswer(null); setKbSources([]); setHonestState(null); setExpanded(new Set()); setRunning(true);
    abortRef.current = runAgent(text, {
      onEvent: (e) => {
        if (e.stage === 'heartbeat') return;
        if (e.stage === 'answer') { setAnswer(e.text || ''); return; }
        if (e.stage === 'kb_sources') { setKbSources(e.sources || []); return; }
        if (e.stage === 'no_grounded_data' || e.stage === 'unverified_negative' || e.stage === 'disclosed_gap' || e.stage === 'error') {
          setHonestState({ stage: e.stage, message: e.message || e.error || 'The agent could not complete this safely.' });
          return;
        }
        setSteps((prev) => [...prev, { id: idRef.current++, stage: e.stage, text: e.text || '', ok: e.ok, tool: e.tool, detail: e.detail }]);
      },
      onDone: () => setRunning(false),
      onError: (err) => { setHonestState({ stage: 'error', message: err.message }); setRunning(false); },
    });
  }, [running]);

  // The live tools the agent actually grounded on — the citation analog. The
  // RAO trace shape varies per query (a tool result can arrive as a classified
  // `tool_result` step OR as a raw "Results: <tool> of ..." step), so collect
  // from both, dedupe by tool name, and keep the richest detail per tool.
  // Never invented: only steps the real NDJSON stream emitted.
  const toolSources = useMemo(() => {
    const byTool = new Map<string, { tool: string; detail: string }>();
    for (const s of steps) {
      if (s.ok === false) continue;
      const isResult = s.stage === 'tool_result' || /^\s*results:/i.test(s.detail || '') || /^\s*results:/i.test(s.text || '');
      // search_claim_documents is the KB retrieval - shown in the "Policy & claim
      // documents" rail (kbSources), not the live-data tool trail (Standard B26).
      if (!isResult || !s.tool || s.tool === 'task_complete' || s.tool === 'search_claim_documents') continue;
      const detail = s.detail || '';
      const existing = byTool.get(s.tool);
      if (!existing || detail.length > (existing.detail || '').length) byTool.set(s.tool, { tool: s.tool, detail });
    }
    return [...byTool.values()];
  }, [steps]);

  // Keep the live timeline scrolled to the newest step.
  useEffect(() => {
    const el = timelineRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [steps.length]);

  const toggle = (id: number) => setExpanded((prev) => {
    const next = new Set(prev);
    next.has(id) ? next.delete(id) : next.add(id);
    return next;
  });

  return (
    <div className="card overflow-hidden p-5">
      <style>{`@keyframes aragTraceIn { from { opacity: 0; transform: translateX(-8px); } to { opacity: 1; transform: translateX(0); } }`}</style>
      <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-ink-500">
        <Bot size={14} style={{ color: 'var(--brand)' }} />
        ARAG Retrieval Agent - watch it work
        {running && <span className="ml-1 inline-flex h-1.5 w-1.5 animate-pulse rounded-full" style={{ background: 'var(--brand)' }} />}
      </div>

      <form onSubmit={(e) => { e.preventDefault(); run(query); }} className="mb-4 flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask the agent to plan, look something up, and answer…"
          className="field flex-1"
        />
        <button type="submit" disabled={running} className="btn btn-primary">
          {running ? <Loader2 size={15} className="animate-spin" /> : 'Ask agent'}
        </button>
      </form>

      {/* Idle capability preview — gives this surface presence BEFORE a query
          runs. Real tools only (the app's own registered MCP tool set). */}
      {steps.length === 0 && !answer && !honestState && !running && (tools?.length || suggestions?.length) ? (
        <div className="mb-1 space-y-4 rounded-xl border border-dashed p-4" style={{ borderColor: 'var(--hairline-strong)' }}>
          {!!tools?.length && (
            <div>
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-ink-400">Tools this agent can call</p>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                {tools.map((t) => {
                  const Icon = t.icon || Wrench;
                  return (
                    <div
                      key={t.name}
                      className="flex items-start gap-2 rounded-lg border px-3 py-2.5"
                      style={{ borderColor: 'var(--hairline)', background: 'var(--surface-2)' }}
                    >
                      <Icon size={14} className="mt-0.5 shrink-0" style={{ color: 'var(--brand)' }} />
                      <div className="min-w-0">
                        <code className="block truncate font-mono text-[11px] font-semibold text-ink-700 dark:text-ink-200">{t.name}()</code>
                        <p className="mt-0.5 text-[11px] leading-snug text-ink-500">{t.description}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          {!!suggestions?.length && (
            <div>
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-ink-400">Try asking</p>
              <div className="flex flex-wrap gap-2">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => { setQuery(s); run(s); }}
                    className="rounded-full border px-3 py-1.5 text-left text-xs text-ink-600 transition hover:bg-ink-50 dark:text-ink-300 dark:hover:bg-ink-800"
                    style={{ borderColor: 'var(--hairline)' }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : null}

      {steps.length > 0 && (
        <ol
          ref={timelineRef}
          className="relative mb-4 max-h-[26rem] space-y-0 overflow-y-auto scroll-slim border-l-2 pl-5"
          style={{ borderColor: 'var(--hairline)' }}
        >
          {steps.map((s, i) => (
            <TraceLane
              key={s.id}
              step={s}
              index={i}
              reduced={reduced}
              open={expanded.has(s.id)}
              onToggle={() => toggle(s.id)}
            />
          ))}
          {running && !answer && !honestState && (
            <li className="relative flex items-center gap-2 py-2 pl-1 text-sm text-ink-400">
              <span className="absolute -left-[calc(1.25rem+5px)] flex h-2.5 w-2.5 items-center justify-center">
                <span className="absolute h-2.5 w-2.5 animate-ping rounded-full" style={{ background: 'var(--brand)', opacity: 0.5 }} />
                <span className="h-1.5 w-1.5 rounded-full" style={{ background: 'var(--brand)' }} />
              </span>
              <Loader2 size={13} className="animate-spin" /> Working…
            </li>
          )}
        </ol>
      )}

      {honestState && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-800/70 dark:bg-amber-950/40 dark:text-amber-200">
          <ShieldAlert size={18} className="mt-0.5 shrink-0" />
          <div>
            <p className="font-semibold">
              {honestState.stage === 'disclosed_gap' ? 'RAO not configured - disclosed, not hidden' : 'Honest refusal'}
            </p>
            <p className="mt-0.5">{honestState.message}</p>
          </div>
        </div>
      )}

      {/* The payoff — the same trust furniture every answer surface shares:
          answer + sources + REMi as one unit, not a plain deflated box. */}
      {answer && (
        <div className="mt-2 grid grid-cols-1 items-start gap-6 animate-fade-up lg:grid-cols-[1fr_20rem]">
          <div className="card p-5">
            <div className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-500">Grounded answer</div>
            <style>{`
              .agent-answer-prose, .agent-answer-prose p, .agent-answer-prose li { color: #334155; }
              .agent-answer-prose h1, .agent-answer-prose h2, .agent-answer-prose h3, .agent-answer-prose strong { color: #0f172a; }
            `}</style>
            <div
              className="answer-prose agent-answer-prose max-h-[50vh] overflow-y-auto scroll-slim rounded-xl p-4"
              style={{ background: 'var(--brand-softer)' }}
              dangerouslySetInnerHTML={{ __html: renderMarkdown(answer) }}
            />
          </div>

          <aside className="space-y-3 lg:sticky lg:top-4 lg:self-start">
            {/* Standard B26: this answer blends STRUCTURED live data (the tool
                trail) with UNSTRUCTURED retrieval (the knowledge-box documents),
                and the rail shows BOTH as sources - the differentiated "one agent
                across live systems AND the corpus" story. */}
            <div className="card ring-hairline overflow-hidden animate-fade-up">
              <div className="flex items-center gap-2 border-b px-4 py-3" style={{ borderColor: 'var(--hairline)' }}>
                <ShieldCheck size={15} style={{ color: 'var(--brand)' }} />
                <span className="text-xs font-semibold uppercase tracking-wide text-ink-600 dark:text-ink-300">What it grounded on</span>
                {(toolSources.length > 0 || kbSources.length > 0) && (
                  <span className="ml-auto inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-bold tabular-nums" style={{ color: 'var(--brand)', background: 'color-mix(in srgb, var(--brand) 14%, transparent)' }} title="Structured live-data tools + the policy and claim documents">
                    <Layers size={12} /> {toolSources.length + kbSources.length}
                  </span>
                )}
              </div>
              <p className="px-4 py-3 text-xs leading-relaxed text-ink-500">
                One agent, two kinds of source: the Claims Copilot blends the insurer's live
                operational data (the tool calls below) with the policy and claim documents it
                retrieved and read. Every claim traces to a visible source - that blend is its
                measurable trust.
              </p>
            </div>
            {toolSources.length > 0 && (
              <div className="card ring-hairline overflow-hidden">
                <div className="flex items-center gap-2 border-b px-4 py-3 text-xs font-semibold uppercase tracking-wide text-ink-600 dark:text-ink-300" style={{ borderColor: 'var(--hairline)' }}>
                  <Terminal size={13} style={{ color: 'var(--brand)' }} />
                  Live data - tool calls
                </div>
                <ol className="divide-y" style={{ borderColor: 'var(--hairline)' }}>
                  {toolSources.map((t, i) => (
                    <li key={i} className="px-4 py-2.5">
                      <code className="font-mono text-[11px] font-semibold text-ink-700 dark:text-ink-200">{t.tool}()</code>
                      <p className="mt-0.5 line-clamp-2 text-[11px] leading-snug text-ink-500">{t.detail}</p>
                    </li>
                  ))}
                </ol>
              </div>
            )}
            {kbSources.length > 0 && (
              <div className="card ring-hairline overflow-hidden">
                <div className="flex items-center gap-2 border-b px-4 py-3 text-xs font-semibold uppercase tracking-wide text-ink-600 dark:text-ink-300" style={{ borderColor: 'var(--hairline)' }}>
                  <FileText size={13} style={{ color: 'var(--accent)' }} />
                  Policy & claim documents
                </div>
                <ol className="divide-y" style={{ borderColor: 'var(--hairline)' }}>
                  {kbSources.map((s) => (
                    <li key={s.resourceId}>
                      <button
                        type="button"
                        onClick={() => navigate(`/r/${s.resourceId}`)}
                        className="group flex w-full items-start gap-2 px-4 py-2.5 text-left transition hover:bg-ink-50 dark:hover:bg-white/5"
                      >
                        <FileText size={13} className="mt-0.5 shrink-0 text-ink-400" />
                        <span className="min-w-0 flex-1">
                          <span className="flex items-center gap-1 text-[12px] font-semibold text-ink-800 group-hover:underline dark:text-ink-100">
                            <span className="truncate">{s.title}</span>
                            <ArrowRight size={11} className="shrink-0 opacity-0 transition group-hover:opacity-100" style={{ color: 'var(--brand)' }} />
                          </span>
                          {s.excerpt && <span className="mt-0.5 line-clamp-2 block text-[11px] leading-snug text-ink-500">“{s.excerpt}”</span>}
                        </span>
                      </button>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}

function TraceLane({
  step, index, reduced, open, onToggle,
}: {
  step: TraceStep; index: number; reduced: boolean; open: boolean; onToggle: () => void;
}) {
  const failed = step.stage === 'tool_result' && step.ok === false;
  const meta = STAGE_META[step.stage] || STAGE_META.doc_search;
  const Icon = failed ? ShieldAlert : meta.icon;
  const tint = failed ? '#d03b3b' : meta.tint;
  const hasDetail = !!step.detail && step.detail.trim().length > 0;

  return (
    <li
      className="relative pb-3 pl-1"
      style={reduced ? undefined : { animation: 'aragTraceIn 340ms ease-out both', animationDelay: `${Math.min(index, 10) * 45}ms` }}
    >
      <span
        className="absolute -left-[calc(1.25rem+5px)] top-1 flex h-2.5 w-2.5 items-center justify-center rounded-full ring-4"
        style={{ background: tint, ['--tw-ring-color' as string]: 'var(--surface-1)' }}
        aria-hidden
      />
      <div
        className="rounded-lg border px-3 py-2 transition"
        style={{ borderColor: 'var(--hairline)', background: 'var(--surface-2)' }}
      >
        <div className="flex items-center gap-2">
          <Icon size={14} style={{ color: tint }} className="shrink-0" />
          <span className="text-[11px] font-semibold uppercase tracking-wide" style={{ color: tint }}>
            {meta.label}
          </span>
          {step.tool && (
            <code
              className="truncate rounded px-1.5 py-0.5 font-mono text-[11px] text-ink-700 dark:text-ink-200"
              style={{ background: 'var(--surface-1)' }}
              title={step.tool}
            >
              {step.tool}()
            </code>
          )}
          {hasDetail && (
            <button
              type="button"
              onClick={onToggle}
              className="ml-auto flex shrink-0 items-center gap-0.5 text-[10px] font-medium text-ink-400 hover:text-ink-700 dark:hover:text-ink-200"
            >
              {open ? 'Hide' : 'Detail'} <ChevronDown size={11} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
            </button>
          )}
        </div>
        <p className="mt-1 text-sm text-ink-700 dark:text-ink-200">{step.text}</p>
        {hasDetail && open && (
          <pre className="scroll-slim mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-md p-2 font-mono text-[11px] leading-relaxed text-ink-500" style={{ background: 'var(--surface-1)' }}>
            {step.detail}
          </pre>
        )}
      </div>
    </li>
  );
}
