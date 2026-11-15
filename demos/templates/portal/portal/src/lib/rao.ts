// Module 4.3 — client for the RAO streaming proxy (server/rao.mjs). Mirrors
// lib/arag.ts's ask() streaming pattern so the two feel identical to compose.

/** A knowledge-box document the Retrieval Agent grounded on (Standard B26). */
export interface KbSource {
  resourceId: string;
  title: string;
  excerpt?: string;
}

export interface RaoEvent {
  stage: 'plan' | 'tool_call' | 'tool_result' | 'doc_search' | 'composing' | 'answer' | 'error' | 'no_grounded_data' | 'unverified_negative' | 'disclosed_gap' | 'heartbeat' | 'kb_sources';
  text?: string;
  ok?: boolean;
  message?: string;
  error?: string;
  /** The tool name, when this step is a tool call/result (server/rao.mjs extractToolName). */
  tool?: string;
  /** A trimmed excerpt of the step's own raw value — call arguments or result body. */
  detail?: string;
  /** The knowledge-box documents grounded on this session (stage: 'kb_sources'). */
  sources?: KbSource[];
}

export interface RaoHandlers {
  onEvent?: (e: RaoEvent) => void;
  onDone?: () => void;
  onError?: (err: Error) => void;
}

/** Streams a RAO agent session. Returns an abort function. */
export function runAgent(query: string, { onEvent, onDone, onError }: RaoHandlers): () => void {
  const controller = new AbortController();
  (async () => {
    try {
      const res = await fetch('/api/agent/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
        signal: controller.signal,
      });
      if (!res.ok || !res.body) throw new Error(`${res.status} ${res.statusText}`);
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (!line.trim()) continue;
          try { onEvent?.(JSON.parse(line)); } catch { /* ignore malformed line */ }
        }
      }
      onDone?.();
    } catch (err: any) {
      if (err?.name !== 'AbortError') onError?.(err);
    }
  })();
  return () => controller.abort();
}
