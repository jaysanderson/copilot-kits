import { Bot, FileSearch, History, ShieldCheck, BookText } from 'lucide-react';
import { AgentTrace } from '../../palette';
import type { DemoConfig } from '../../lib/config';

// ─────────────────────────────────────────────────────────────────────────────
// Use case 6 - Claims Copilot: an agent across the insurer's live operational
// systems AND the document corpus. ARAG's OWN Retrieval Agent plans, calls this
// app's /mcp tools - the structured live systems (get_policy_status,
// get_claimant_history, get_claim) AND a knowledge-box search over the
// unstructured policy and claim documents (search_claim_documents) - and blends
// both in one grounded answer (Standard B26), watched live via the real NDJSON
// trace (Standard B11). ARAG is the agent, not our code (GM directive 21 Jul
// 2026); this app only exposes the tools and relays ARAG's trace, and shows both
// the live tool calls AND the knowledge-box documents it grounded on. Desk-level:
// full width.
// ─────────────────────────────────────────────────────────────────────────────

// The REAL tools this app exposes at /mcp (server/index.mjs registry) - shown as
// an idle capability preview, never invented.
const TOOLS = [
  { name: 'get_policy_status', description: 'Policy master: product line, in-force, premium status, excess, endorsements, flood cover.', icon: ShieldCheck },
  { name: 'get_claimant_history', description: "A claimant's prior claims: claim numbers, perils, years and outcomes.", icon: History },
  { name: 'get_claim', description: 'A claim record: peril, date of loss, amount and current status.', icon: FileSearch },
  { name: 'search_claim_documents', description: 'Document library: the policy wording (PDS), claims manual, adjuster reports and claim documents - the clauses that govern the answer.', icon: BookText },
];

// Blended by design (Standard B26): each pairs a live-systems lookup with a
// question the answer can only settle from the policy/claim wording, so the
// agent reaches for both the structured tools and the knowledge box in one run.
const SUGGESTIONS = [
  'Is the Delacroix flood claim payable? Check whether flood cover is selected on their policy, and cite the flood clause in the policy wording.',
  'Was the Tomas Ruiz motor premium current at the date of loss, and what does the wording say about a claim when the premium is in arrears?',
  'For the Anand burglary claim, is the diamond ring paid in full? Confirm it was not a specified item and quote the sub-limit clause.',
];

export function CopilotPage({ config }: { config: DemoConfig }) {
  return (
    <div className="mx-auto max-w-5xl space-y-5 px-4 py-6 sm:px-6">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-white" style={{ background: 'linear-gradient(155deg, var(--brand-strong), var(--brand))' }}>
          <Bot size={20} />
        </span>
        <div className="min-w-0">
          <h1 className="font-display text-xl font-semibold text-ink-900 dark:text-ink-50">Claims Copilot</h1>
          <p className="text-sm text-ink-500">
            One agent across two worlds - the insurer's live operational systems (policy master, claims-history register,
            claim record) AND the policy and claim documents themselves. ARAG's own Retrieval Agent plans the check,
            calls the live tools, searches the wording, and blends both into one grounded answer. Watch it work, step by step.
          </p>
        </div>
      </div>

      <AgentTrace tools={TOOLS} suggestions={SUGGESTIONS} />
      {config ? null : null}
    </div>
  );
}
