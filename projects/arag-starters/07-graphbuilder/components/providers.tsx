'use client';

import { useState } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { makeQueryClient } from '@/lib/queryClient';
import { TaxonomyStoreProvider } from '@/hooks/use-taxonomy-store';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => makeQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <TaxonomyStoreProvider>{children}</TaxonomyStoreProvider>
    </QueryClientProvider>
  );
}
