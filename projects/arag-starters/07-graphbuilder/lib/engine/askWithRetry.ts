import type { LimiterFn } from './run';

interface AskOptions {
  body: Record<string, unknown>;
  limiter: LimiterFn;
  signal?: AbortSignal;
  maxRetries?: number;
  label?: string;
}

const RETRY_DELAYS = [1000, 2000, 4000];

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) return reject(new Error('Aborted'));
    const timer = setTimeout(resolve, ms);
    signal?.addEventListener('abort', () => {
      clearTimeout(timer);
      reject(new Error('Aborted'));
    }, { once: true });
  });
}

export async function askWithRetry(options: AskOptions): Promise<Record<string, unknown>> {
  const { body, limiter, signal, maxRetries = 3, label = '' } = options;
  let lastError: Error | null = null;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    if (signal?.aborted) throw new Error('Aborted');

    try {
      const result = await limiter(async () => {
        if (signal?.aborted) throw new Error('Aborted');
        const res = await fetch('/api/arag/generate-taxonomy', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
          signal,
        });

        if (!res.ok) {
          const text = await res.text().catch(() => '');
          const err = new Error(
            `Ask failed${label ? ` for ${label}` : ''}: ${res.status} ${text.slice(0, 200)}`
          );
          (err as RetryableError).statusCode = res.status;
          throw err;
        }

        return res.json();
      });
      return result as Record<string, unknown>;
    } catch (err) {
      if (err instanceof Error && err.message === 'Aborted') throw err;

      lastError = err instanceof Error ? err : new Error(String(err));
      const statusCode = (err as RetryableError).statusCode;
      const isRetryable = statusCode !== undefined && statusCode >= 500;

      if (!isRetryable || attempt >= maxRetries - 1) break;

      const delay = RETRY_DELAYS[attempt] ?? 4000;
      await sleep(delay, signal);
    }
  }

  throw lastError ?? new Error(`Ask failed after ${maxRetries} attempts`);
}

interface RetryableError extends Error {
  statusCode?: number;
}
