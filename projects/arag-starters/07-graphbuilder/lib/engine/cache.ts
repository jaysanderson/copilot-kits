const cache = new Map<string, unknown>();

export function getCached<T>(key: string): T | undefined {
  return cache.get(key) as T | undefined;
}

export function setCached<T>(key: string, value: T): void {
  cache.set(key, value);
}

export function makeCacheKey(body: unknown): string {
  return JSON.stringify(body);
}

export function clearCache(): void {
  cache.clear();
}
