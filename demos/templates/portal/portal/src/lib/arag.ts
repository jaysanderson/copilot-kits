// Client for the portal's own /api/* surface. The browser NEVER talks to Nuclia
// directly and never holds the service-account token — every call goes to the
// Express server, which proxies to the KB.
//
// Ported from the shipped research portal (rp-grdc/ui/src/api.js): the /ask
// NDJSON streaming, retrieval-paragraph indexing, and citation grouping by
// document are the load-bearing bits and are reproduced faithfully here in TS.

export interface Citation {
  index: number;
  title: string;
  url: string | null;
  resourceId: string;
  text: string;
  excerptCount: number;
  spans: [number, number][];
}

interface ParagraphInfo {
  text: string;
  title: string;
  url: string | null;
  resourceId: string;
  score?: number;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error((detail as any).error || `${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error((detail as any).error || `${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

// ── retrieval / browse ────────────────────────────────────────────────────────

export interface SearchResult {
  resources?: Record<string, any>;
  best_matches?: string[];
  [k: string]: any;
  latencyMs?: number;
}
export function search(body: {
  query: string;
  filters?: string[];
  pageSize?: number;
  searchConfig?: string;
  features?: string[];
}): Promise<SearchResult> {
  return postJson('/api/search', body);
}

export interface CatalogCard {
  id: string;
  slug: string | null;
  title: string;
  summary: string;
  /** DA Generator highlights (bullet points), when the demo has one registered. */
  highlights: string[];
  /** True when title/summary came from a DA Generator agent, not Nuclia's native fields. */
  generated: boolean;
  /** Platform-native extracted thumbnail/frame (Nuclia produces this for video), or null. */
  thumbnail: string | null;
  icon: string | null;
  created: string | null;
  sourceUrl: string | null;
  docType: string;
  mediaType: string | null;
  durationMinutes: number | null;
  labels: Record<string, string[]>;
  /** Arbitrary KV-schema fields the Generator extracted — render as scannable chips. */
  structuredFields: Record<string, string | number | boolean>;
  authors: string[];
}
export interface CatalogResult {
  items: CatalogCard[];
  facets: Record<string, { label: string; count: number }[]>;
  total: number;
  page: number;
  pageSize: number;
}

/**
 * Standard B19 (arag-demo-app skill, 17 Aug 2026) — the shared catalog()
 * helper is THE place label filtering is built, so no page re-solves the
 * 412. The server now builds a `filter_expression` (server/filters.mjs),
 * empirically verified live to compose AND-across-labelsets/OR-within-
 * labelset in ONE call — the old client-side per-value multi-call-and-merge
 * workaround (needed because the legacy `filters` array can only AND) is no
 * longer necessary and has been removed; this is always a single request.
 */
export async function catalog(body: {
  query?: string;
  filters?: string[];
  pageSize?: number;
  page?: number;
} = {}): Promise<CatalogResult> {
  return postJson('/api/catalog', body);
}

export interface GraphNode { id: string; label: string; group: string; degree: number }
export interface GraphEdge { from: string; to: string; label: string }
export interface GraphResult { nodes: GraphNode[]; edges: GraphEdge[]; pathCount: number }
export function graph(body: { entity?: string; topK?: number } = {}): Promise<GraphResult> {
  return postJson('/api/graph', body);
}

export interface EntityGroups {
  groups: { id: string; title: string; count: number; entities: string[] }[];
}
export function entities(): Promise<EntityGroups> {
  return getJson('/api/entities');
}

export function getResource(id: string): Promise<any> {
  return getJson(`/api/resource/${encodeURIComponent(id)}`);
}

export interface Health { ok: boolean; kb: string; resources?: number | null; error?: string }
export function getHealth(): Promise<Health> {
  return getJson<Health>('/api/health').catch((err) => ({ ok: false, kb: 'unreachable', error: err.message }));
}

// ── streamed, grounded answer ─────────────────────────────────────────────────

export interface AskHandlers {
  onToken?: (text: string) => void;
  onCitations?: (citations: Citation[]) => void;
  /**
   * Module 4.1 (REMi trust panel): the FULL retrieved paragraph set /ask
   * actually grounded on (up to 8, by score) - not just each citation's
   * single excerpt. Fires alongside onCitations. Feed this straight to
   * `remi()` as `contexts`; scoring against only the cited excerpts made
   * groundedness swing wildly on the same accurate answer (ResearchOS
   * Milestone 1 finding) because the comparison context was too thin.
   */
  onContexts?: (contexts: string[]) => void;
  onDone?: () => void;
  onError?: (err: Error) => void;
}

/**
 * Streamed grounded answer. Calls onToken as text arrives and onCitations as
 * soon as sources resolve — usually before generation finishes, so the sources
 * panel populates while the answer is still being written. Returns an abort fn.
 */
export function ask(
  body: { query: string; filters?: string[]; searchConfig?: string; resourceId?: string; claimScope?: string },
  { onToken, onCitations, onContexts, onDone, onError }: AskHandlers
): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch('/api/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      if (!res.ok || !res.body) {
        const detail = await res.json().catch(() => ({}));
        throw new Error((detail as any).error || `${res.status} ${res.statusText}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let citationsSent = false;

      // Citations arrive keyed by paragraph id with no title or text of their
      // own — just character spans into the answer. The retrieval event, which
      // always precedes them, carries the paragraph text and its parent document
      // title, so index it as it goes past.
      const paragraphs = new Map<string, ParagraphInfo>();

      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          let event: any;
          try {
            event = JSON.parse(trimmed.startsWith('data:') ? trimmed.slice(5) : trimmed);
          } catch {
            onToken?.(trimmed);
            continue;
          }

          if (event.item?.type === 'answer' && event.item.text) onToken?.(event.item.text);
          else if (typeof event.answer === 'string') onToken?.(event.answer);

          if (event.item?.type === 'retrieval') {
            indexParagraphs(event.item.results || event.item, paragraphs);
          }

          const citations = event.citations || event.item?.citations;
          if (citations && !citationsSent) {
            citationsSent = true;
            onCitations?.(normalizeCitations(citations, paragraphs));
            onContexts?.(topContexts(paragraphs));
          }
        }
      }

      if (!citationsSent) {
        onCitations?.([]);
        onContexts?.([]);
      }
      onDone?.();
    } catch (err: any) {
      if (err?.name !== 'AbortError') onError?.(err);
    }
  })();

  return () => controller.abort();
}

/** Flattens a retrieval payload into `paragraphId → { text, title, url }`. */
function indexParagraphs(results: any, into: Map<string, ParagraphInfo>) {
  for (const [rid, resource] of Object.entries<any>(results?.resources || {})) {
    const title = resource.title || rid;
    const url = resource.origin?.url || null;
    for (const field of Object.values<any>(resource.fields || {})) {
      for (const [paragraphId, paragraph] of Object.entries<any>(field.paragraphs || {})) {
        into.set(paragraphId, {
          text: (paragraph.text || '').trim(),
          title,
          url,
          resourceId: rid,
          score: paragraph.score,
        });
      }
    }
  }
  return into;
}

/**
 * Module 4.1: the full retrieved context /ask actually grounded on, ranked by
 * score, capped at 8 - the payload REMi must be scored against (never just
 * the cited excerpts; see AskHandlers.onContexts).
 */
function topContexts(paragraphs: Map<string, ParagraphInfo>): string[] {
  return [...paragraphs.values()]
    .filter((p) => p.text?.trim())
    .sort((a, b) => (b.score || 0) - (a.score || 0))
    .slice(0, 8)
    .map((p) => p.text);
}

/**
 * Turns Nuclia's citations into what the sources panel renders. The payload is
 * `{ "<paragraphId>": [[start,end], …] }` — spans into the answer, no title or
 * excerpt. Both come from the retrieval index built while the stream was read.
 * Multiple cited paragraphs often belong to one document, so they are grouped by
 * document: eleven paragraph citations across four reports read as four sources.
 */
function normalizeCitations(raw: any, paragraphs: Map<string, ParagraphInfo>): Citation[] {
  const entries: [string, any][] = Array.isArray(raw)
    ? raw.map((c: any, i: number) => [c.id || `source-${i}`, c])
    : Object.entries(raw || {});

  const byDocument = new Map<string, {
    resourceId: string; title: string; url: string | null; excerpts: string[]; spans: [number, number][];
  }>();

  for (const [key, value] of entries) {
    const found = paragraphs.get(key);
    const resourceId = found?.resourceId || String(key).split('/')[0];
    const spans: [number, number][] = Array.isArray(value)
      ? (value.filter((s: any) => Array.isArray(s) && s.length >= 2) as [number, number][])
      : [];

    if (!byDocument.has(resourceId)) {
      byDocument.set(resourceId, {
        resourceId,
        title: found?.title || (typeof value === 'object' && value?.title) || String(key),
        url: found?.url || null,
        excerpts: [],
        spans: [],
      });
    }
    const entry = byDocument.get(resourceId)!;
    if (found?.text) entry.excerpts.push(found.text);
    entry.spans.push(...spans);
  }

  return [...byDocument.values()].map((entry, i) => ({
    index: i + 1,
    title: entry.title,
    url: entry.url,
    resourceId: entry.resourceId,
    // Longest excerpt first — most likely to show why the document was cited.
    text: entry.excerpts.sort((a, b) => b.length - a.length)[0] || '',
    excerptCount: entry.excerpts.length,
    spans: entry.spans,
  }));
}

// ── Module 4.1: REMi trust score (real RAG-triad, not a citation-count proxy) ──

export interface RemiScore {
  answerRelevance: number | null;
  answerRelevanceReason: string;
  contextRelevance: number | null;
  groundedness: number | null;
}

/**
 * The REAL REMi score for one answer, via the server proxy at POST /api/remi
 * -> POST {kb}/predict/remi (KB service-account token, never the NUA key).
 * `contexts` MUST be the full retrieved paragraph set (AskState.contexts /
 * AskHandlers.onContexts), not just cited excerpts - see the docstring on
 * `/api/remi` in server/index.mjs for why that distinction is load-bearing.
 * Every number this returns comes straight from the live API response -
 * never hand-typed (the same truthful-by-construction discipline as
 * <GroundedAnswer> and <CitedMetric>).
 */
export function remi(body: { question: string; answer: string; contexts: string[] }): Promise<RemiScore> {
  return postJson('/api/remi', body);
}

// ── structured extraction (query-time answer_json_schema) ─────────────────────
// The WORKING structured-JSON path (arag-kb skill): POST {kb}/ask with an
// answer_json_schema returns a schema-conformant object grounded in real
// retrieved content. Used by Claim Intake to read a claim's own documents into
// typed intake fields. Server-proxied; the schema is fixed server-side, the
// client only names the claim to extract.

export interface ExtractField { key: string; label: string; value: string | number | boolean | null }
export interface ExtractSource { resourceId: string; title: string }
export interface ExtractResult {
  fields: ExtractField[];
  sources: ExtractSource[];
  /** True when ARAG returned a schema-conformant object; false when nothing grounded. */
  grounded: boolean;
}

export function extractClaim(body: { claimNumber: string; claimant?: string }): Promise<ExtractResult> {
  return postJson('/api/extract', body);
}

// ── underwriting risk synthesis (query-time answer_json_schema) ───────────────
// Use case 7 - Underwriting Risk Summary: the same working structured-JSON
// mechanism as Claim Intake, applied to an underwriting application's own
// application form, inspection report and risk-data summary, scoped to that
// application's own documents via the application_number label.

export interface UnderwritingSummary {
  applicantName: string;
  productLine: string;
  overallRiskRating: string;
  keyRiskFactors: string[];
  recommendedAction: string;
  rationale: string;
}
export interface UnderwritingResult {
  summary: UnderwritingSummary | null;
  sources: ExtractSource[];
  grounded: boolean;
}

export function underwritingSummary(body: { applicationNumber: string; applicant?: string }): Promise<UnderwritingResult> {
  return postJson('/api/underwriting-summary', body);
}
