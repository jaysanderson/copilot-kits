'use client';

import Image from 'next/image';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Info } from 'lucide-react';

const STEPS = [
  {
    title: 'Your browser',
    body: 'The taxonomy builder UI runs here. It never talks to the knowledge base directly and never holds a credential - every request goes through this application\'s own server first.',
  },
  {
    title: 'This application\'s server',
    body: 'A small proxy layer holds the one service-account credential for your knowledge base. It adds that credential to every request, then forwards a retrieval-and-answer call and returns only the result - the credential itself never reaches the browser.',
  },
  {
    title: 'Progress Agentic RAG',
    body: 'Each call asks your knowledge base to propose categories - grounded in your actual documents - and return them as a validated structured object, not free text. A cheap, fast model is pinned on every call by design, and depth and breadth are capped so a run always stays small.',
  },
  {
    title: 'Your taxonomy',
    body: 'Proposed concepts come back as a reviewable tree. Edit, merge, move or regenerate any branch, then export governed SKOS-XL Turtle for Progress Semaphore or a JSON model you can re-import later.',
  },
];

export function HowItWorksDialog() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" aria-label="How this works" className="gap-1.5">
          <Info className="h-3.5 w-3.5" aria-hidden="true" />
          <span className="hidden sm:inline">How this works</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Image
              src="/brand/progress-agentic-rag-lockup.svg"
              alt="Progress Agentic RAG"
              width={180}
              height={21}
              className="h-5 w-auto"
            />
          </DialogTitle>
          <DialogDescription>
            What actually happens when you generate a taxonomy.
          </DialogDescription>
        </DialogHeader>

        <ol className="space-y-4">
          {STEPS.map((step, i) => (
            <li key={step.title} className="flex gap-3">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-semibold">
                {i + 1}
              </span>
              <div>
                <p className="text-sm font-medium">{step.title}</p>
                <p className="text-sm text-muted-foreground">{step.body}</p>
              </div>
            </li>
          ))}
        </ol>
      </DialogContent>
    </Dialog>
  );
}
