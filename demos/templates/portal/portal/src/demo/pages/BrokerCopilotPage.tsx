import { useState } from 'react';
import { Handshake, FileStack, ScrollText, Lightbulb } from 'lucide-react';
import { useAsk, useRemi, GroundedAnswer, RemiPanel } from '../../palette';
import type { DemoConfig } from '../../lib/config';

// ─────────────────────────────────────────────────────────────────────────────
// Use case 8 - Broker Copilot. Natural-language Q&A over Publisher Mutual's
// products, rates and compliance bulletins for the broker channel - scoped away
// from claim files and underwriting applications via the doc_type label, so a
// broker asking a product question never gets a live claimant's file surfaced
// as if it were product literature. Every answer is cited and REMi-scored, same
// discipline as Coverage Q&A.
// ─────────────────────────────────────────────────────────────────────────────

const BROKER_FILTERS = [
  '/classification.labels/doc_type/Product Sheet',
  '/classification.labels/doc_type/Rate Card',
  '/classification.labels/doc_type/Compliance Bulletin',
];

const SUGGESTED = [
  'Is flood cover included by default under TideProtect Home and Contents, or does it need to be selected?',
  'What loading applies to a driver under 25 with a modified vehicle under TideDrive Motor?',
  'Does a warehouse storing aerosol stock without a sprinkler system need underwriting referral for TideCommercial Property?',
  'What are my disclosure obligations for the new cyber endorsement on Commercial Property?',
];

const VALUE_CHIPS = [
  { icon: ScrollText, label: 'Answered from products, rates and compliance bulletins' },
  { icon: FileStack, label: 'Never a claim file or application, cited and clickable' },
];

export function BrokerCopilotPage({ config }: { config: DemoConfig }) {
  const ask = useAsk({ filters: BROKER_FILTERS });
  const remi = useRemi(ask);
  const [query, setQuery] = useState('');

  return (
    <div className="mx-auto max-w-5xl space-y-5 px-4 py-6 sm:px-6">
      <div className="flex items-center gap-3">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white" style={{ background: 'linear-gradient(155deg, var(--brand-strong), var(--brand))' }}>
          <Handshake size={18} />
        </span>
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-400">Broker Copilot</p>
          <h1 className="font-display text-lg font-semibold text-ink-900 dark:text-ink-50">Ask about products, rates and compliance</h1>
        </div>
      </div>

      <div className="rounded-2xl p-4 sm:p-5" style={{ background: 'var(--surface-1)', border: '1px solid var(--hairline)' }}>
        <p className="mb-3 text-sm text-ink-500">
          Ask a product, rating or compliance question in plain English, the way a broker would between quotes. The
          answer is generated only from Publisher's broker product sheets, rate card and compliance bulletins - never
          a claim file or underwriting application - and every fact it relies on is cited and opens the source
          document.
        </p>
        <div className="mb-3 flex flex-wrap gap-2.5">
          {VALUE_CHIPS.map(({ icon: Icon, label }) => (
            <span key={label} className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium" style={{ background: 'var(--brand-soft)', color: 'var(--brand)' }}>
              <Icon size={13} /> {label}
            </span>
          ))}
        </div>
        <form onSubmit={(e) => { e.preventDefault(); if (query.trim()) ask.run(query); }} className="ask-bar flex flex-col gap-2 rounded-xl p-1.5 sm:flex-row sm:items-center">
          <input
            className="ask-bar-input min-w-0 flex-1 border-0 bg-transparent px-3 py-2 text-sm outline-none"
            placeholder="Ask a product, rating or compliance question…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Ask the broker copilot"
          />
          <button type="submit" className="btn btn-primary shrink-0" disabled={ask.streaming}>
            {ask.streaming ? 'Asking…' : 'Ask'}
          </button>
        </form>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wide text-ink-400"><Lightbulb size={12} /> Try</span>
          {SUGGESTED.map((p) => (
            <button key={p} type="button" onClick={() => { setQuery(p); ask.run(p); }} className="rounded-md border px-2.5 py-1 text-xs text-ink-600 transition hover:bg-ink-50 dark:text-ink-300 dark:hover:bg-ink-800" style={{ borderColor: 'var(--hairline)' }}>
              {p}
            </button>
          ))}
        </div>
      </div>

      {(ask.answer || ask.streaming || ask.error) && (
        <GroundedAnswer
          state={ask}
          trust={(ask.done || remi.loading) && ask.citations && ask.citations.length > 0 ? <RemiPanel remi={remi} variant="panel" /> : undefined}
        />
      )}
      {config ? null : null}
    </div>
  );
}
