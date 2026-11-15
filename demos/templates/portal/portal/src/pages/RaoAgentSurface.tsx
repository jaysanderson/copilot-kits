import type { SurfaceProps } from './types';
import { PageHeader } from '../components/PageHeader';
import { AgentTrace } from '../palette/AgentTrace';

// Module 4.3's default page for the `rao-agent` capability. Watch ARAG's own
// Retrieval Agent plan, call this app's /mcp tools, and answer — streamed
// live so the room sees ARAG driving the tool calls, not the app narrating
// a deterministic lookup.
export function RaoAgentSurface({ surface }: SurfaceProps) {
  return (
    <div>
      <PageHeader icon={surface.icon} title={surface.label || 'Agent'}>
        {surface.tagline || "ARAG's own Retrieval Agent plans, calls this app's live tools, and answers — watch it work."}
      </PageHeader>
      <AgentTrace />
    </div>
  );
}
