import { useEffect, useState } from 'react';
import { ScrollText, FileText, Lightbulb } from 'lucide-react';
import { useAsk, useRemi, GroundedAnswer, RemiPanel } from '../../palette';
import type { DemoConfig } from '../../lib/config';
import { useClaimsDesk, type Claim } from '../store';
import { ClaimWorkbench } from '../ui';

// The suggested coverage question this claim is built to make vivid - grounded
// in real corpus facts, never a hardcoded answer.
export function coverageQuestion(claim: Claim): string {
  const p = claim.productLine === 'Motor' ? 'TideDrive Motor'
    : claim.productLine === 'Commercial Property' ? 'TideCommercial Property'
    : 'TideProtect Home and Contents';
  // Strip a leading "The " so a claimant whose name already carries the
  // article ("The Delacroix Family") doesn't read "the The Delacroix Family"
  // after the template's own "the ".
  const who = claim.claimant.name.replace(/^the\s+/i, '');
  switch (claim.peril) {
    case 'Flood': return `Is the ${who} flood claim (${claim.claimNumber}) payable given their ${p} policy schedule?`;
    case 'Windscreen': return `What excess applies to the ${who} windscreen claim (${claim.claimNumber}) under the ${p} policy?`;
    case 'Burglary': return `Is the diamond ring in the ${who} burglary claim (${claim.claimNumber}) paid in full or capped at the unspecified single-item sub-limit?`;
    case 'Water damage': return `Is the ${who} water-damage claim (${claim.claimNumber}) covered under the ${p} policy, or is it excluded as gradual damage?`;
    case 'Theft': return `Is the ${who} theft claim (${claim.claimNumber}) payable under the ${p} policy given the premium position at the date of loss?`;
    case 'Fire': return `Is the ${who} fire claim (${claim.claimNumber}) within the sums insured under the ${p} policy?`;
    default: return `Is the ${claim.peril.toLowerCase()} loss on claim ${claim.claimNumber} (${who}) covered under the ${p} policy?`;
  }
}

const VALUE_CHIPS = [
  { icon: ScrollText, label: 'Answered from the actual policy wording' },
  { icon: FileText, label: 'Every clause cited and clickable' },
];

// Use case 2 - Coverage Q&A: a live cited /ask against the policy wording and
// the claim file. The citation opens the real source document (table-stakes
// gate 4). REMi scores it inline against the full retrieved context.
export function CoveragePage({ config }: { config: DemoConfig }) {
  const { activeClaim, addEntry } = useClaimsDesk();
  // Fix (team-lead finding, 28 Aug 2026): hard-scope to this claim's own
  // documents plus the general policy wording and claims manual - an
  // unscoped ask could pull another claimant's policy schedule into the
  // source grid on a similar Home & Contents question. See server/index.mjs's
  // COVERAGE_REFERENCE_DOC_TYPES for what "general" means here.
  const ask = useAsk({ claimScope: activeClaim.claimNumber });
  const remi = useRemi(ask);
  const [query, setQuery] = useState('');
  const [logged, setLogged] = useState(false);

  // Prefill the claim's own coverage question whenever the active claim changes.
  useEffect(() => { setQuery(coverageQuestion(activeClaim)); ask.reset(); setLogged(false); /* eslint-disable-next-line */ }, [activeClaim.id]);
  useEffect(() => { setLogged(false); }, [ask.answer]);

  useEffect(() => {
    if (!ask.done || logged || remi.loading) return;
    if (!ask.citations || ask.citations.length === 0 || !remi.score) return;
    addEntry({ claimNumber: activeClaim.claimNumber, claimant: activeClaim.claimant.name, route: 'coverage', query: ask.query, answer: ask.answer, citationCount: ask.citations.length, remi: remi.score });
    setLogged(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ask.done, remi.loading, remi.score, logged]);

  const probes = config.probes?.answerable || [];

  return (
    <ClaimWorkbench kicker="Coverage Q&A">
      <div className="rounded-2xl p-4 sm:p-5" style={{ background: 'var(--surface-1)', border: '1px solid var(--hairline)' }}>
        <p className="mb-3 text-sm text-ink-500">
          Ask the coverage question in plain English. The answer is generated only from Publisher's own policy
          wording and this claim's file, and every clause it relies on is cited and opens the source document.
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
            placeholder="Ask a coverage question about this claim…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Ask a coverage question"
          />
          <button type="submit" className="btn btn-primary shrink-0" disabled={ask.streaming}>
            {ask.streaming ? 'Asking…' : 'Ask coverage'}
          </button>
        </form>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wide text-ink-400"><Lightbulb size={12} /> Try</span>
          <button type="button" onClick={() => { const q = coverageQuestion(activeClaim); setQuery(q); ask.run(q); }} className="rounded-md border px-2.5 py-1 text-xs text-ink-600 transition hover:bg-ink-50 dark:text-ink-300 dark:hover:bg-ink-800" style={{ borderColor: 'var(--hairline)' }}>
            This claim's coverage question
          </button>
          {probes.slice(0, 2).map((p) => (
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
    </ClaimWorkbench>
  );
}
