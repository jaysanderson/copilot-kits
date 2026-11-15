type AragResponse<T = unknown> = {
  ok: boolean;
  status: number;
  data: T | null;
  error: string | null;
};

function getEnv() {
  const baseUrl = process.env.ARAG_BASE_URL;
  const apiKey = process.env.ARAG_API_KEY;
  const kbId = process.env.KB_ID;

  if (!baseUrl || !apiKey || !kbId) {
    throw new Error('Missing ARAG environment variables (ARAG_BASE_URL, ARAG_API_KEY, KB_ID)');
  }

  return { baseUrl, apiKey, kbId };
}

/** Cheapest capable generative tier by default (hard rule 15 - cost safety).
 *  Override via ARAG_GENERATIVE_MODEL if the Knowledge Box needs a different one. */
export function getGenerativeModel(): string {
  return process.env.ARAG_GENERATIVE_MODEL || 'gemini-2.5-flash-lite';
}

export function aragUrl(path: string): string {
  const { baseUrl, kbId } = getEnv();
  return `${baseUrl}/kb/${kbId}${path}`;
}

export function getKbInfo() {
  const { baseUrl, kbId } = getEnv();
  return { baseUrl, kbId };
}

export async function aragFetch<T = unknown>(
  path: string,
  options: {
    method?: string;
    body?: unknown;
    timeout?: number;
    headers?: Record<string, string>;
  } = {}
): Promise<AragResponse<T>> {
  const { apiKey } = getEnv();
  const url = aragUrl(path);
  const { method = 'GET', body, timeout = 30000, headers: extraHeaders } = options;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);

  try {
    const res = await fetch(url, {
      method,
      headers: {
        'X-NUCLIA-SERVICEACCOUNT': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'X-Synchronous': 'true',
        ...extraHeaders,
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    clearTimeout(timer);

    if (!res.ok) {
      const text = await res.text().catch(() => '');
      // Full detail server-side only - never forwarded to the browser verbatim
      // (error-paths-leak rule: backend host/mechanism names never reach the UI).
      console.error(`[arag] ${method} ${path} -> ${res.status}: ${text.slice(0, 1000)}`);
      return {
        ok: false,
        status: res.status,
        data: null,
        error: text.slice(0, 500),
      };
    }

    const data = (await res.json()) as T;
    return { ok: true, status: res.status, data, error: null };
  } catch (err) {
    clearTimeout(timer);
    const message = err instanceof Error ? err.message : 'Unknown error';
    console.error(`[arag] ${method} ${path} failed:`, message);
    return {
      ok: false,
      status: 0,
      data: null,
      error: message.slice(0, 500),
    };
  }
}
