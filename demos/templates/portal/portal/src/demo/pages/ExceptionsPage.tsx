import { useEffect, useState } from 'react';
import { ShieldAlert, ScanSearch, Lightbulb } from 'lucide-react';
import { useAsk, useRemi, GroundedAnswer, RemiPanel } from '../../palette';
import type { DemoConfig } from '../../lib/config';
import { useClaimsDesk, type Claim } from '../store';
import { ClaimWorkbench } from '../ui';

// ─────────────────────────────────────────────────────────────────────────────
// Use case 4 - Exception / integrity check. ARAG reads across the whole claim
// file and surfaces inconsistencies a handler should flag before paying - a
// date-of-loss mismatch between the FNOL and the police report, a premium in
// arrears at the date of loss, a value that exceeds a sub-limit. The honest
// case matters here: on a clean claim ARAG says so rather than inventing a
// problem, and where the grounding is thinner the REMi score shows it (Standard
// B8 principle 8 - honesty designed in), never a false all-clear.
//
// FIX (demo-tester finding 1, 28 Aug 2026): the prior prompt let the model
// treat a category the documents were simply SILENT on (e.g. no mention of
// premium status) as if it were itself a red flag - it rendered a "Premium in
// Arrears" heading on a claim whose file never says the premium was in
// arrears, contradicting the page's own "it never invents a red flag" promise.
// REMi caught the thin grounding (2.0/5) but the false heading still rendered.
// Two changes close this, verified live both directions before shipping
// (Delacroix CLM-2026-0501 no longer shows the false arrears flag; Tomas Ruiz
// CLM-2026-0466, who genuinely has both a date mismatch and arrears, still
// surfaces both; Priya Anand CLM-2026-0492's genuine sub-limit exception also
// still surfaces - all three tested to confirm the fix doesn't overcorrect
// into suppressing real findings):
//   1. The prompt now requires every listed exception to be an explicit
//      quote/close-paraphrase from a named document, forbids listing a
//      category as a finding just because the documents don't address it, and
//      forces an opening line that matches what was actually found ("N
//      exception(s)" vs "consistent") so the heading can never contradict the
//      body text the way the invented arrears line did.
//   2. The query is now hard-scoped to THIS claim's own three documents via
//      claim_number (arag-kb gotcha 2) - exceptions checking only ever needs
//      the claim's own FNOL/adjuster/schedule, never another claim's file or
//      the general PDS, so scoping removes any chance of cross-claim leakage
//      as a side benefit (found live while fixing this: an earlier, longer
//      draft of this prompt caused one unscoped retrieval to pull Tomas
//      Ruiz's documents into a Delacroix query - scoping makes that
//      structurally impossible, not just unlikely).
// ─────────────────────────────────────────────────────────────────────────────

function exceptionQuestion(claim: Claim): string {
  return `Review the whole claim file for ${claim.claimNumber} (${claim.claimant.name}) against the ${claim.policyNumber} policy for genuine integrity exceptions a claims handler should flag before this claim is paid - specifically: a date-of-loss mismatch between documents, a premium in arrears or lapsed at the date of loss, or a claimed value that exceeds a policy sub-limit.

Only list something as a numbered exception if the retrieved documents contain EXPLICIT evidence of it - name the specific document and quote or closely paraphrase the exact text that proves it. Do NOT list a category as an exception just because the documents are silent about it: the ABSENCE of information on a topic (for example, no mention of premium status) is not itself a red flag and must never be listed, headed or bolded as if it were a finding. If a category is not addressed by the documents at all, leave it out of the numbered exception list entirely.

Open with ONE of these two framings, matching what you actually found: if you have at least one genuine, evidenced exception, open with "This file shows N exception(s) requiring review:" (N = the real count) and then list them, numbered, each with its evidence and source document. If you found none, open with "This file is consistent - no genuine exceptions were found." and support that by citing the specific date of loss, claimant and policy details as recorded in the First Notice of Loss, Adjuster Report and Policy Schedule, so the clean result is itself grounded in the documents. Either way, you may close with one short sentence noting which categories the documents simply did not address, phrased as a gap in the file record - never as a suspected problem or worded to resemble a red-flag heading.`;
}

const claimScope = (claimNumber: string) => [`/classification.labels/claim_number/${claimNumber}`];

export function ExceptionsPage({ config }: { config: DemoConfig }) {
  const { activeClaim, addEntry } = useClaimsDesk();
  const ask = useAsk({ filters: claimScope(activeClaim.claimNumber) });
  const remi = useRemi(ask);
  const [logged, setLogged] = useState(false);

  useEffect(() => { ask.reset(); setLogged(false); /* eslint-disable-next-line */ }, [activeClaim.id]);
  useEffect(() => { setLogged(false); }, [ask.answer]);
  useEffect(() => {
    if (!ask.done || logged || remi.loading) return;
    if (!ask.citations || ask.citations.length === 0 || !remi.score) return;
    addEntry({ claimNumber: activeClaim.claimNumber, claimant: activeClaim.claimant.name, route: 'exceptions', query: ask.query, answer: ask.answer, citationCount: ask.citations.length, remi: remi.score });
    setLogged(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ask.done, remi.loading, remi.score, logged]);

  const flagged = activeClaim.angle === 'exception';
  const probes = config.probes?.answerable || [];

  return (
    <ClaimWorkbench kicker="Exception Check">
      <div className="rounded-2xl p-4 sm:p-5" style={{ background: 'var(--surface-1)', border: '1px solid var(--hairline)' }}>
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white" style={{ background: `linear-gradient(155deg, ${flagged ? '#b91c1c' : 'var(--brand-strong)'}, ${flagged ? '#dc2626' : 'var(--brand)'})` }}>
            <ShieldAlert size={18} />
          </span>
          <div className="min-w-0">
            <p className="font-display text-base font-semibold text-ink-900 dark:text-ink-50">Check this claim for exceptions</p>
            <p className="mt-0.5 text-sm text-ink-500">
              ARAG reads across every document in the file and the policy and surfaces integrity exceptions - a date
              mismatch, a premium in arrears, a value over a sub-limit - each grounded in the documents. On a clean file
              it says so; it never invents a red flag.
            </p>
            {flagged && (
              <span className="mt-2 inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-[11px] font-semibold" style={{ background: 'color-mix(in srgb, #dc2626 14%, transparent)', color: '#dc2626' }}>
                <ShieldAlert size={12} /> This claim is under investigation - exceptions expected
              </span>
            )}
          </div>
        </div>
        <button type="button" onClick={() => ask.run(exceptionQuestion(activeClaim))} disabled={ask.streaming} className="btn btn-primary mt-4">
          <ScanSearch size={15} /> {ask.streaming ? 'Checking the file…' : `Run the exception check on ${activeClaim.claimNumber}`}
        </button>
        {probes.length > 0 && (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wide text-ink-400"><Lightbulb size={12} /> Try</span>
            {probes.slice(0, 2).map((p) => (
              <button key={p} type="button" onClick={() => ask.run(p)} className="rounded-md border px-2.5 py-1 text-xs text-ink-600 transition hover:bg-ink-50 dark:text-ink-300 dark:hover:bg-ink-800" style={{ borderColor: 'var(--hairline)' }}>
                {p}
              </button>
            ))}
          </div>
        )}
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
