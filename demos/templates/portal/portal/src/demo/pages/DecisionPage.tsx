import { useEffect, useMemo, useState } from 'react';
import { Scale, CheckCircle2, XCircle, HelpCircle } from 'lucide-react';
import { useAsk, useRemi, GroundedAnswer, RemiPanel } from '../../palette';
import type { DemoConfig } from '../../lib/config';
import { useClaimsDesk, type Claim } from '../store';
import { ClaimWorkbench } from '../ui';

function determinationQuestion(claim: Claim): string {
  const p = claim.productLine === 'Motor' ? 'TideDrive Motor'
    : claim.productLine === 'Commercial Property' ? 'TideCommercial Property'
    : 'TideProtect Home and Contents';
  return `Coverage determination for claim ${claim.claimNumber} (${claim.claimant.name}, ${claim.peril.toLowerCase()} under the ${p} policy ${claim.policyNumber}): is this loss payable, not payable, or does it need more information? State the outcome and give the reasons, grounded in the policy wording and this claim's file.`;
}

type Verdict = 'payable' | 'not-payable' | 'needs-info' | null;
function readVerdict(answer: string): Verdict {
  const a = answer.toLowerCase();
  if (/\bnot payable\b|\bnot covered\b|\bexcluded\b|\bdecline/.test(a)) return 'not-payable';
  if (/\bneeds? more info|\bneed more information|\binsufficient|\bcannot be decided|\brefer/.test(a)) return 'needs-info';
  if (/\bpayable\b|\bis covered\b|\bcovered peril\b/.test(a)) return 'payable';
  return null;
}
const VERDICT_META: Record<Exclude<Verdict, null>, { label: string; icon: typeof Scale; tone: string }> = {
  'payable': { label: 'Payable', icon: CheckCircle2, tone: '#16a34a' },
  'not-payable': { label: 'Not payable', icon: XCircle, tone: '#dc2626' },
  'needs-info': { label: 'Needs more info', icon: HelpCircle, tone: '#d97706' },
};

// Use case 3 - Coverage Decision: a payable / not-payable / needs-more-info
// determination reasoned from the policy and the claim file, with cited reasons
// and a prominent, live REMi trust score. A low-confidence decision is flagged.
export function DecisionPage({ config }: { config: DemoConfig }) {
  const { activeClaim, addEntry } = useClaimsDesk();
  // Fix (team-lead finding, 28 Aug 2026): hard-scope to this claim's own
  // documents plus the general policy wording and claims manual - the
  // insurance video QA caught the Delacroix decision citing OTHER claimants'
  // policy schedules (THP-77321, THP-88213) as sources on a similar Home &
  // Contents question. See server/index.mjs's COVERAGE_REFERENCE_DOC_TYPES.
  const ask = useAsk({ claimScope: activeClaim.claimNumber });
  const remi = useRemi(ask);
  const [logged, setLogged] = useState(false);

  useEffect(() => { ask.reset(); setLogged(false); /* eslint-disable-next-line */ }, [activeClaim.id]);
  useEffect(() => { setLogged(false); }, [ask.answer]);
  useEffect(() => {
    if (!ask.done || logged || remi.loading) return;
    if (!ask.citations || ask.citations.length === 0 || !remi.score) return;
    addEntry({ claimNumber: activeClaim.claimNumber, claimant: activeClaim.claimant.name, route: 'decision', query: ask.query, answer: ask.answer, citationCount: ask.citations.length, remi: remi.score });
    setLogged(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ask.done, remi.loading, remi.score, logged]);

  const verdict = useMemo(() => (ask.done ? readVerdict(ask.answer) : null), [ask.done, ask.answer]);
  const vMeta = verdict ? VERDICT_META[verdict] : null;
  const config_ = config; // config reserved for future persona framing

  return (
    <ClaimWorkbench kicker="Coverage Decision">
      <div className="rounded-2xl p-4 sm:p-5" style={{ background: 'var(--surface-1)', border: '1px solid var(--hairline)' }}>
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white" style={{ background: 'linear-gradient(155deg, var(--brand-strong), var(--brand))' }}>
            <Scale size={18} />
          </span>
          <div className="min-w-0">
            <p className="font-display text-base font-semibold text-ink-900 dark:text-ink-50">Make the coverage call</p>
            <p className="mt-0.5 text-sm text-ink-500">
              ARAG reasons a payable / not-payable / needs-more-info determination only from the policy wording and this
              claim's file, cites each reason, and the answer carries a live REMi trust score - so a low-confidence
              call is caught before a cheque goes out, not after.
            </p>
          </div>
        </div>
        <button type="button" onClick={() => ask.run(determinationQuestion(activeClaim))} disabled={ask.streaming} className="btn btn-primary mt-4">
          {ask.streaming ? 'Determining…' : `Run the coverage determination for ${activeClaim.claimNumber}`}
        </button>
      </div>

      {vMeta && (
        <div className="flex items-center gap-3 rounded-xl px-4 py-3" style={{ background: `color-mix(in srgb, ${vMeta.tone} 12%, var(--surface-1))`, border: `1px solid color-mix(in srgb, ${vMeta.tone} 40%, transparent)` }}>
          <vMeta.icon size={22} style={{ color: vMeta.tone }} />
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-400">ARAG's determination</p>
            <p className="font-display text-lg font-semibold" style={{ color: vMeta.tone }}>{vMeta.label}</p>
          </div>
        </div>
      )}

      {(ask.answer || ask.streaming || ask.error) && (
        <GroundedAnswer
          state={ask}
          journey={false}
          trust={(ask.done || remi.loading) && ask.citations && ask.citations.length > 0 ? <RemiPanel remi={remi} variant="panel" /> : undefined}
        />
      )}
      {config_ ? null : null}
    </ClaimWorkbench>
  );
}
