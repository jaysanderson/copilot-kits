'use client';

import { useMutation, useQuery } from '@tanstack/react-query';

export function useAragEnv() {
  return useQuery({
    queryKey: ['arag-env'],
    queryFn: async () => {
      const res = await fetch('/api/arag/env');
      if (!res.ok) throw new Error('Failed to fetch env');
      return res.json() as Promise<{ kbId: string; configured: boolean }>;
    },
    staleTime: Infinity,
  });
}

export function useTestConnection() {
  return useMutation({
    mutationFn: async () => {
      const res = await fetch('/api/arag/test', { method: 'POST' });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || 'Connection failed');
      return data as { ok: boolean; kbId: string; generativeModel: string };
    },
  });
}
