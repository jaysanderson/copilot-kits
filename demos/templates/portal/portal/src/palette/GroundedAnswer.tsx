import { useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { Compass } from 'lucide-react';
// Kendo-free: plain elements + Tailwind so the answer/citation guarantee holds
// identically in both the KendoReact and open-source UI modes.
import type { AskState } from './hooks';
import { renderMarkdown } from '../lib/markdown';
import { getDomainNoun } from '../lib/config';
import { Citations } from '../components/Citations';
import { TypingDots, ErrorBanner, UngroundedWarning } from '../components/States';
import { AnswerJourney } from '../components/journey/AnswerJourney';

// ─────────────────────────────────────────────────────────────────────────────
// GroundedAnswer — the incorruptible answer pigment.
//
// It renders the streamed answer AND its sources together, and it is structurally
// incapable of presenting an uncited claim as fact: when an answer resolves with
// zero citations it renders an explicit ungrounded/refusal warning instead of
// clean prose. Every composition that shows an ARAG answer should use this rather
// than printing `answer` directly — that is what keeps "an ungrounded answer is a
// bug" true no matter how freely the page is composed.
// ─────────────────────────────────────────────────────────────────────────────
export function GroundedAnswer({ state, journey = true, trust }: { state: AskState; journey?: boolean; trust?: ReactNode }) {
  const navigate = useNavigate();
  const [journeyOpen, setJourneyOpen] = useState(false);
  const { answer, citations, streaming, error, done, ungrounded, refusalLike, query } = state;

  if (error) return <ErrorBanner>{error}</ErrorBanner>;
  if (!answer && !streaming) return null;

  const hasCitations = !!citations && citations.length > 0;

  return (
    // Standard B24 (GM review, 18 Aug 2026): the grounded answer takes the FULL
    // WIDTH, then its trust score and its source tiles lay out ACROSS the page
    // beneath it - never a short answer in a narrow column beside a tall vertical
    // rail of sources with a dead void, which the GM "really dislikes". The reader
    // takes in the answer and the evidence it stands on together, no full-page
    // scroll to reach the sources.
    <div className="space-y-5">
      <div className="card p-5">
        <div className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-500">Grounded answer</div>
        <div className="answer-prose max-h-[52vh] overflow-y-auto scroll-slim" dangerouslySetInnerHTML={{ __html: renderMarkdown(answer) }} />
        {streaming && <div className="mt-2"><TypingDots /></div>}
        {ungrounded && (
          <div className="mt-4">
            {/* Fix 2 (flagship rebuild, Section 3.A): domain-noun token, never "Knowledge Box". */}
            <UngroundedWarning>
              {refusalLike
                ? `The portal correctly declined: the ${getDomainNoun()} holds nothing that supports this question, so it did not invent an answer. That refusal is the behaviour to trust.`
                : `The ${getDomainNoun()} returned no citations for this answer. Do not rely on the text above - an uncited answer is treated as ungrounded here.`}
            </UngroundedWarning>
          </div>
        )}
      </div>

      {hasCitations ? (
        <div className="space-y-4">
          {/* The live trust score sits full-width directly under the answer (its
              three REMi rings read as a horizontal band), so it leaves no dead
              void beside a rail. */}
          {trust}
          {/* The sources lay out ACROSS the page as a horizontal grid of tiles. */}
          <Citations variant="grid" citations={citations!} onOpen={(rid) => navigate(`/r/${rid}`)} />
          {journey && done && (
            <button
              type="button"
              onClick={() => setJourneyOpen(true)}
              className="inline-flex items-center justify-center gap-2 rounded-lg border px-3.5 py-2 text-sm font-medium text-ink-700 transition hover:bg-ink-50 dark:text-ink-200 dark:hover:bg-ink-800"
              style={{ borderColor: 'var(--hairline)' }}
            >
              <Compass size={15} />
              Journey through the context
            </button>
          )}
        </div>
      ) : streaming ? (
        <div className="card card-flat p-4 text-sm text-ink-400">Resolving sources…</div>
      ) : null}

      {journey && (
        <AnswerJourney
          open={journeyOpen}
          query={query}
          citedIds={(citations || []).map((c) => c.resourceId)}
          onClose={() => setJourneyOpen(false)}
        />
      )}
    </div>
  );
}
