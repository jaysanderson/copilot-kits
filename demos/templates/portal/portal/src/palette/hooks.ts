// ─────────────────────────────────────────────────────────────────────────────
// The palette — grounded data hooks ("pigments").
//
// Every hook here draws from the Knowledge Box through the portal's own /api
// proxy (see lib/arag, lib/augment). None of them can invent data: they return
// what ARAG returned, plus loading/error/provenance. Compose them freely — the
// truthfulness lives in the materials, not in any particular page.
// ─────────────────────────────────────────────────────────────────────────────
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ask as askApi, search as searchApi, catalog as catalogApi, graph as graphApi,
  entities as entitiesApi, getHealth, remi as remiApi,
  type Citation, type SearchResult, type CatalogResult, type GraphResult,
  type EntityGroups, type Health, type RemiScore,
} from '../lib/arag';

// Phrases that mark a well-behaved refusal — the KB declined rather than confabulated.
const REFUSAL_MARKERS = [
  'not enough data', 'does not contain', 'no information', 'not provided',
  'cannot answer', "don't have", 'does not provide', 'not covered', 'no supporting',
  'unable to', 'no relevant',
];

export interface AskState {
  query: string;
  answer: string;
  citations: Citation[] | null;
  /** Module 4.1: the full retrieved context this answer grounded on (up to 8, by score) — feed to useRemi/remi(), never just the cited excerpts. */
  contexts: string[];
  streaming: boolean;
  error: string | null;
  /** Answer finished with zero citations — treat as ungrounded (a bug to surface, not hide). */
  ungrounded: boolean;
  /** Ungrounded AND the text reads like an explicit, correct refusal. */
  refusalLike: boolean;
  done: boolean;
  run: (q: string) => void;
  stop: () => void;
  reset: () => void;
}

/**
 * Streamed, grounded Ask. The load-bearing pigment: it streams answer tokens and
 * resolves citations, and exposes ungrounded/refusal state so a UI can NEVER
 * present an uncited answer as fact. `resourceId` scopes the answer to one source
 * (used by the Journey's "how does this relate?").
 */
export function useAsk(opts: { resourceId?: string; filters?: string[]; claimScope?: string } = {}): AskState {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [citations, setCitations] = useState<Citation[] | null>(null);
  const [contexts, setContexts] = useState<string[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<null | (() => void)>(null);

  const run = useCallback((q: string) => {
    const text = q.trim();
    if (!text) return;
    abortRef.current?.();
    setQuery(text); setAnswer(''); setCitations(null); setContexts([]); setError(null); setStreaming(true);
    abortRef.current = askApi(
      { query: text, resourceId: opts.resourceId, filters: opts.filters, claimScope: opts.claimScope },
      {
        onToken: (t) => setAnswer((prev) => prev + t),
        onCitations: (c) => setCitations(c),
        onContexts: (c) => setContexts(c),
        onDone: () => setStreaming(false),
        onError: (e) => { setError(e.message); setStreaming(false); },
      }
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opts.resourceId, JSON.stringify(opts.filters), opts.claimScope]);

  const stop = useCallback(() => { abortRef.current?.(); setStreaming(false); }, []);
  const reset = useCallback(() => { abortRef.current?.(); setStreaming(false); setQuery(''); setAnswer(''); setCitations(null); setContexts([]); setError(null); }, []);
  useEffect(() => () => abortRef.current?.(), []);

  const done = !streaming && !!answer;
  const ungrounded = done && citations !== null && citations.length === 0;
  const refusalLike = ungrounded && REFUSAL_MARKERS.some((m) => answer.toLowerCase().includes(m));
  return { query, answer, citations, contexts, streaming, error, ungrounded, refusalLike, done, run, stop, reset };
}

// ── on-demand async pigments ────────────────────────────────────────────────
interface AsyncState<T> { data: T | null; loading: boolean; error: string | null; run: (...a: any[]) => void; }

// Fix 8 (Section 3.B) — standing convention, enforced HERE for any future
// per-user-auth build: this base template has no SessionProvider (the KB
// service-account token is server-side only, never a per-user JWT), so the
// transient-401 bug's precondition doesn't exist in the stock scaffold. If a
// build adds one (e.g. an RBAC-by-label demo, or the `rao-agent` capability
// forwarding a user JWT), route its data-fetch through THIS shared hook and
// gate on token/session readiness centrally, right here — e.g.
// `if (immediate && !sessionReady) return;` — rather than leaving every
// page author to remember an `if (!token) return;` guard per fetch. A build
// that skips this hits a real, un-suppressible 401 in the console/network
// log on first render, even though the UI silently recovers
// (feedback_arag_demo_factory_recurring_bug_classes, point 1 - hit 3-4 pages
// per app across an 8 Aug sweep in earlier builds).
function useArag<T>(fn: (...a: any[]) => Promise<T>, { immediate = false }: { immediate?: boolean } = {}): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState<string | null>(null);
  const fnRef = useRef(fn); fnRef.current = fn;
  const run = useCallback((...args: any[]) => {
    setLoading(true); setError(null);
    fnRef.current(...args).then((d) => setData(d)).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, []);
  useEffect(() => { if (immediate) run(); /* eslint-disable-next-line */ }, [immediate]);
  return { data, loading, error, run };
}

/** Semantic retrieval (/find) — the ranked source list behind an answer. */
export const useSearch = () => useArag<SearchResult>((body) => searchApi(body));
/** Faceted browse over the corpus (metadata, not semantic). */
export const useCatalog = (immediate = false) => useArag<CatalogResult>((body = {}) => catalogApi(body), { immediate });
/** Knowledge-graph path search. */
export const useGraph = () => useArag<GraphResult>((body = {}) => graphApi(body));
/** Entity groups discovered in the corpus. */
export const useEntities = (immediate = false) => useArag<EntityGroups>(() => entitiesApi(), { immediate });
/** KB liveness + resource count. */
export const useHealth = (immediate = true) => useArag<Health>(() => getHealth(), { immediate });

// ── Module 4.1: REMi trust panel ────────────────────────────────────────────

export interface RemiState {
  score: RemiScore | null;
  loading: boolean;
  error: string | null;
  /** Manually (re-)score the current answer — auto-fires once per completed answer, but exposed for a re-score control. */
  run: () => void;
}

/**
 * Real RAG-triad score for a completed useAsk() answer — groundedness /
 * answer relevance / context relevance, straight from POST {kb}/predict/remi
 * (server-proxied, KB service-account token). Fires automatically the moment
 * `askState.done` flips true with real citations, scored against the FULL
 * retrieved context (`askState.contexts`), never just the cited excerpts —
 * see the module's docstring in lib/arag.ts's `remi()` for why. Never a
 * hand-typed number: <RemiPanel> only ever renders what this hook returns.
 */
export function useRemi(askState: Pick<AskState, 'query' | 'answer' | 'contexts' | 'done' | 'citations'>): RemiState {
  const [score, setScore] = useState<RemiScore | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const lastScoredAnswer = useRef<string | null>(null);

  const run = useCallback(() => {
    if (!askState.answer || !askState.query) return;
    setLoading(true); setError(null);
    remiApi({ question: askState.query, answer: askState.answer, contexts: askState.contexts })
      .then((s) => { setScore(s); lastScoredAnswer.current = askState.answer; })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [askState.query, askState.answer, askState.contexts]);

  useEffect(() => {
    if (!askState.done) return;
    if (!askState.citations || askState.citations.length === 0) return; // ungrounded — nothing to score
    if (lastScoredAnswer.current === askState.answer) return; // already scored this exact answer
    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [askState.done, askState.answer]);

  return { score, loading, error, run };
}

export type { Citation, RemiScore };
