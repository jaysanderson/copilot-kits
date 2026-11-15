// Network layer. Every await carries a timeout and a visible failure path. Stalls retry ONCE (short first
// attempt, longer second); real 4xx/5xx are never retried - they are shown. No keys here: server-side proxy only.
import { state, recordTrace } from './state.js';

export class ApiError extends Error { constructor(m, kind, status, retry) { super(m); this.kind = kind; this.status = status; this.retry = retry; } }
// The server labels its own failures ({error:{code,message,retry}}); the client shows that message, never a string it matched.
async function httpError(r) { let m = null, retry = false; try { const j = await r.json(); m = j.error && j.error.message; retry = !!(j.error && j.error.retry); } catch {} return new ApiError(m || 'Request failed', 'http', r.status, retry); }

async function once(url, opts, ms) {
  const ctl = new AbortController();
  const outer = opts.signal;
  if (outer) { if (outer.aborted) ctl.abort(); else outer.addEventListener('abort', () => ctl.abort(), { once: true }); }
  const t = setTimeout(() => ctl.abort('timeout'), ms);
  try {
    const r = await fetch(url, { ...opts, signal: ctl.signal });
    return r;
  } catch (e) {
    if (outer && outer.aborted) throw new ApiError('aborted', 'abort');
    throw new ApiError('stall', 'stall');
  } finally { clearTimeout(t); }
}

export async function getJSON(path, { signal, label, retry = true, track = true } = {}) {
  let r;
  try { r = await once(path, { headers: { Accept: 'application/json' }, signal }, 6000); }
  catch (e) {
    if (e.kind === 'abort' || !retry) throw e;
    r = await once(path, { headers: { Accept: 'application/json' }, signal }, 15000).catch((e2) => { throw e2; });
  }
  if (!r.ok) throw await httpError(r);
  const j = await r.json().catch(() => { throw new ApiError('bad body', 'http', r.status); });
  if (track && j && Array.isArray(j._trace)) recordTrace(label || path, j._trace);
  return j;
}
export async function postJSON(path, body, { signal, label } = {}) {
  const r = await once(path, { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify(body), signal }, 15000);
  if (!r.ok) throw await httpError(r);
  const j = await r.json();
  if (j && Array.isArray(j._trace)) recordTrace(label || path, j._trace);
  return j;
}

// SSE over fetch. Events: token, citations, confidence, followups, refusal, _trace, done.
export async function streamAsk(body, on, { signal, firstByteMs = 10000 } = {}) {
  const ctl = new AbortController();
  if (signal) signal.addEventListener('abort', () => ctl.abort('user'), { once: true });
  let got = false;
  const timer = setTimeout(() => { if (!got) ctl.abort('stall'); }, firstByteMs);
  let r;
  try {
    r = await fetch('/api/answer', { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' }, body: JSON.stringify(body), signal: ctl.signal });
  } catch (e) { clearTimeout(timer); const kind = signal && signal.aborted ? 'abort' : ctl.signal.reason === 'stall' ? 'stall' : 'network'; throw new ApiError(kind, kind); }
  if (!r.ok || !r.body) { clearTimeout(timer); throw await httpError(r); }
  const rd = r.body.getReader(), dec = new TextDecoder();
  let buf = '';
  try {
    for (;;) {
      const { value, done } = await rd.read();
      if (done) break;
      got = true; clearTimeout(timer);
      buf += dec.decode(value, { stream: true });
      let ix;
      while ((ix = buf.indexOf('\n\n')) >= 0) {
        const frame = buf.slice(0, ix); buf = buf.slice(ix + 2);
        let ev = 'message', data = [];
        for (const ln of frame.split('\n')) {
          if (ln.startsWith('event:')) ev = ln.slice(6).trim();
          else if (ln.startsWith('data:')) data.push(ln.slice(5).replace(/^ /, ''));
        }
        if (!data.length) continue;
        let j; try { j = JSON.parse(data.join('\n')); } catch { continue; }
        on(ev, j);
      }
    }
  } catch (e) {
    clearTimeout(timer);
    const kind = signal && signal.aborted ? 'abort' : ctl.signal.reason === 'stall' ? 'stall' : 'network';
    throw new ApiError(kind, kind);
  }
  clearTimeout(timer);
  if (!got) throw new ApiError('empty', 'stall');
}
