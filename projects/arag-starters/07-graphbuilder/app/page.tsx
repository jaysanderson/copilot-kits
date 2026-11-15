'use client';

import Image from 'next/image';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plug, Settings, Play, PenLine, Download } from 'lucide-react';
import { ConnectPanel } from '@/components/connect-panel';
import { SettingsPanel } from '@/components/settings-panel';
import { GeneratePanel } from '@/components/generate-panel';
import { ReviewPanel } from '@/components/review-panel';
import { ExportPanel } from '@/components/export-panel';
import { HowItWorksDialog } from '@/components/how-it-works-dialog';

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <Image
                src="/brand/progress-agentic-rag-lockup.svg"
                alt="Progress Agentic RAG"
                width={220}
                height={26}
                priority
                className="h-6 w-auto shrink-0"
              />
              <span className="hidden md:inline text-sm text-muted-foreground border-l pl-3 truncate">
                Taxonomy Builder - export to Progress Semaphore
              </span>
            </div>
            <HowItWorksDialog />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Tabs defaultValue="connect" className="space-y-6">
          <TabsList className="grid w-full max-w-xl grid-cols-5">
            <TabsTrigger value="connect" aria-label="Connect" className="gap-1.5 text-xs">
              <Plug className="h-3.5 w-3.5" aria-hidden="true" />
              <span className="hidden sm:inline">Connect</span>
            </TabsTrigger>
            <TabsTrigger value="settings" aria-label="Settings" className="gap-1.5 text-xs">
              <Settings className="h-3.5 w-3.5" aria-hidden="true" />
              <span className="hidden sm:inline">Settings</span>
            </TabsTrigger>
            <TabsTrigger value="generate" aria-label="Generate" className="gap-1.5 text-xs">
              <Play className="h-3.5 w-3.5" aria-hidden="true" />
              <span className="hidden sm:inline">Generate</span>
            </TabsTrigger>
            <TabsTrigger value="review" aria-label="Review" className="gap-1.5 text-xs">
              <PenLine className="h-3.5 w-3.5" aria-hidden="true" />
              <span className="hidden sm:inline">Review</span>
            </TabsTrigger>
            <TabsTrigger value="export" aria-label="Export" className="gap-1.5 text-xs">
              <Download className="h-3.5 w-3.5" aria-hidden="true" />
              <span className="hidden sm:inline">Export</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="connect">
            <ConnectPanel />
          </TabsContent>
          <TabsContent value="settings">
            <SettingsPanel />
          </TabsContent>
          <TabsContent value="generate">
            <GeneratePanel />
          </TabsContent>
          <TabsContent value="review">
            <ReviewPanel />
          </TabsContent>
          <TabsContent value="export">
            <ExportPanel />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
