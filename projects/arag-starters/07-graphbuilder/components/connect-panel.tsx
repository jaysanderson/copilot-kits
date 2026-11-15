'use client';

import { useAragEnv, useTestConnection } from '@/hooks/use-test-connection';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, CheckCircle2, XCircle, Plug, AlertTriangle } from 'lucide-react';

export function ConnectPanel() {
  const envQuery = useAragEnv();
  const testMutation = useTestConnection();

  return (
    <div className="space-y-6 max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plug className="h-5 w-5" />
            Knowledge base connection
          </CardTitle>
          <CardDescription>
            Verify connectivity to your Progress Agentic RAG knowledge base. The credential and
            host are configured on the server and never sent to the browser.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {envQuery.isError ? (
            <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
              Could not load the connection details from the server.
            </div>
          ) : (
            <div className="grid gap-3 min-w-0">
              <div className="flex items-center justify-between gap-3 rounded-md border px-4 py-3 bg-muted/50 min-w-0">
                <span className="text-sm font-medium text-muted-foreground shrink-0">Knowledge base ID</span>
                <code className="text-sm font-mono truncate min-w-0">
                  {envQuery.data?.kbId || 'Loading...'}
                </code>
              </div>
              <div className="flex items-center justify-between gap-3 rounded-md border px-4 py-3 bg-muted/50 min-w-0">
                <span className="text-sm font-medium text-muted-foreground shrink-0">Server configuration</span>
                <span className="text-sm truncate min-w-0 text-right">
                  {envQuery.data === undefined
                    ? 'Loading...'
                    : envQuery.data.configured
                      ? 'Present'
                      : 'Missing - set the environment variables'}
                </span>
              </div>
            </div>
          )}

          <div className="flex items-center gap-3 pt-2">
            <Button
              onClick={() => testMutation.mutate()}
              disabled={testMutation.isPending}
              className="min-w-[160px]"
            >
              {testMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Testing...
                </>
              ) : (
                'Test connection'
              )}
            </Button>

            {testMutation.isSuccess && (
              <Badge
                variant="outline"
                className="border-transparent"
                style={{ color: 'hsl(var(--arag-success-fg))', backgroundColor: 'hsl(var(--arag-success-bg))' }}
              >
                <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                Connected
              </Badge>
            )}

            {testMutation.isError && (
              <Badge variant="outline" className="text-destructive border-destructive/30 bg-destructive/10">
                <XCircle className="mr-1 h-3.5 w-3.5" />
                {testMutation.error.message}
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
