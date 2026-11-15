import './globals.css';
import type { Metadata } from 'next';
import { Providers } from '@/components/providers';

export const metadata: Metadata = {
  title: 'Progress Agentic RAG - Taxonomy Builder',
  description: 'Generate a governed taxonomy from your knowledge base with Progress Agentic RAG, review and edit it, then export SKOS-XL Turtle for Progress Semaphore.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
