import { useState } from 'react';
import { createPortal } from 'react-dom';
import { useLocation } from 'react-router-dom';
import { Workflow, X, ExternalLink, Eye, Gem } from 'lucide-react';
import type { DemoConfig } from '../lib/config';

// ─────────────────────────────────────────────────────────────────────────────
// Module 4.2 — the solution-architecture reveal.
//
// Table-stakes gate 11 (binding, GM directive 8 Aug 2026): every demo ships a
// small, unobtrusive "How this works" button, present on every route, that
// opens a modal showing THIS demo's actual solution architecture — not a
// generic ARAG marketing diagram. Renders `config.architectureFlow`
// (create-app.js's `generateArchitectureFlow()`), a declarative, per-app list
// derived from the chosen capability set — real stages, each real or an
// honestly disclosed gap, never a hand-drawn diagram to keep in sync by hand.
//
// GM addendum (17 Aug 2026): this is the one place Progress is shown at FULL
// prominence — logo, product name, explicit "Powered by Progress Agentic RAG"
// — complementing the always-on header band and footer credit, not
// duplicating them; those stay discreet, this is deliberately not.
//
// Built to stand alone (GM clarification, 8 Aug 2026): in an async/self-serve
// review this may be the ONLY thing a prospect ever sees — it must be
// accurate and complete on its own, not a teaser for a live console
// walkthrough that may never happen.
//
// Portals to document.body (ARAKS lesson, CLAUDE.md, 11 Aug 2026): a
// `position:fixed` modal rendered inside an ancestor with `backdrop-filter`
// (e.g. this app's own frosted sticky header) gets clipped to that ancestor's
// box in Chromium even though the DOM/a11y tree looks correct — a DOM read is
// NOT proof a modal renders; only a screenshot is. createPortal sidesteps it.
//
// Standard B12 (arag-demo-app skill, 17 Aug 2026), two fixes:
//   1. Page-specific flow — each route shows ITS OWN request/data flow, not
//      one app-wide diagram. `config.architectureFlowByRoute[pathname]` (built
//      per-capability in create-app.js's generateArchitectureFlow) is tried
//      first; `config.architectureFlow` (the union/global flow) is the
//      fallback for the home page, /r/:id and anything without a specific
//      match, so every route still shows SOMETHING accurate.
//   2. Placement — the trigger sits at `--progress-header-h` (published by
//      ProgressHeader's own ResizeObserver) + a fixed gap, never a hardcoded
//      guess that drifts out of sync with the header's real, responsive
//      height. Reproduced defect this replaces: a hardcoded top-[100px] sat
//      20px INSIDE a 120px-tall desktop header band.
// ─────────────────────────────────────────────────────────────────────────────
export function ArchitectureReveal({ config }: { config: DemoConfig }) {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();
  const flow = config.architectureFlowByRoute?.[pathname] || config.architectureFlow || [];
  // Standard B12, sharpened 17 Aug 2026 (GM correction): the reveal is a FAIL
  // if it's only a technical flow diagram - it must also say what this page
  // is doing and why it matters, per route, not once for the whole app.
  const pageContext = config.pageContextByRoute?.[pathname] || config.pageContext;

  return (
    <>
      {/*
        Fixed + mounted once at the App frame (see App.tsx) rather than left
        for each bespoke composition.tsx Shell to remember to place — table-
        stakes gate 11 requires it PRESENT ON EVERY ROUTE, and a per-Shell
        opt-in is exactly the kind of thing that silently regresses on the
        next archetype. top-right per the gate's own spec; `calc()` off the
        measured header height so it never straddles the header/body edge on
        any archetype, viewport or future header redesign.
      */}
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed right-4 z-40 inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium text-ink-700 shadow-sm backdrop-blur transition hover:-translate-y-0.5 dark:text-ink-100"
        style={{
          // Discreet but findable in BOTH schemes (Steve Jobs review, 17 Aug
          // 2026): a faint brand tint + a real border, so the reveal never
          // vanishes into the near-black dark default the way a bg-ink-900/90
          // chip did - while still staying unobtrusive (table-stakes gate 11).
          background: 'color-mix(in srgb, var(--brand) 14%, var(--surface-1))',
          borderColor: 'color-mix(in srgb, var(--brand) 45%, var(--hairline-strong))',
          // Compliance-co fix (17 Aug 2026): also add the disclaimer banner's own
          // published height (Disclaimer.tsx) - the banner sits BETWEEN the
          // header and the body, and offsetting only for the header left this
          // button visually straddling the banner's bottom edge (a real,
          // reproduced defect - see Disclaimer.tsx's comment on the fix).
          top: 'calc(var(--progress-header-h, 88px) + var(--disclaimer-banner-h, 0px) + 12px)',
        }}
        aria-haspopup="dialog"
        aria-label="How this works"
      >
        <Workflow size={14} />
        <span className="hidden sm:inline">How this works</span>
      </button>
      {open && createPortal(
        <ArchitectureModal config={config} flow={flow} pageContext={pageContext} onClose={() => setOpen(false)} />,
        document.body
      )}
    </>
  );
}

function ArchitectureModal({
  config,
  flow,
  pageContext,
  onClose,
}: {
  config: DemoConfig;
  flow: NonNullable<DemoConfig['architectureFlow']>;
  pageContext?: { whatItDoes: string; value: string };
  onClose: () => void;
}) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Solution architecture"
      className="fixed inset-0 z-[999] flex items-center justify-center p-4"
      style={{ background: 'rgba(0, 10, 30, 0.55)' }}
      onClick={onClose}
    >
      <div
        className="flex max-h-[85vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl dark:bg-ink-900"
        onClick={(e) => e.stopPropagation()}
      >
        {/* GM addendum: Progress at full prominence, deliberately unlike the discreet header/footer.
            Mobile fix (demo-tester finding 3, 28 Aug 2026 - first attempt insufficient, second
            attempt below is the real fix, both verified at genuine 390px before shipping). The
            first attempt added `min-w-0 flex-1` to the text's WRAPPER div, not the <span> itself -
            since neither the logo <img> nor the <span> had flex-grow, the span never claimed the
            row's leftover space; it collapsed toward its min-content width instead (measured live:
            15px wide, 280px tall - the title wrapping one word per line down a sliver, with the
            logo's own ~240px width squeezing everything else into that sliver). The actual fix:
            stack the header (logo row, then full-width title) below `sm`, so the title never has to
            share a cramped single row with a wide logo lockup on a phone; the close button is
            absolutely positioned in the corner so it's structurally impossible for wrapped text to
            run under it, at any title length or viewport width. Reverts to the original single-row
            layout at `sm` and up, where there's genuinely enough width for both. Same header is
            shared by every route (B12), so this fixes the collision everywhere at once. */}
        <div className="relative flex flex-col gap-2 px-6 py-4 pr-12 sm:flex-row sm:items-center sm:gap-3 sm:pr-6" style={{ background: '#00216B' }}>
          <img src="/brand/progress-arag-logo-alternate.svg" alt="Progress Agentic RAG" className="shrink-0" style={{ height: 28, width: 'auto' }} />
          <span className="text-sm font-medium text-white/85 sm:min-w-0 sm:flex-1">
            Powered by Progress Agentic RAG - real request/data flow for {config.title}
          </span>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="absolute right-4 top-4 shrink-0 rounded-full p-1.5 text-white/80 transition hover:bg-white/10 hover:text-white sm:static"
          >
            <X size={18} />
          </button>
        </div>

        <div className="overflow-y-auto scroll-slim p-6">
          <p className="mb-5 text-sm text-ink-600 dark:text-ink-300">
            This is the real path a request takes through {config.title} today - not a generic
            marketing diagram. Every stage below is either a genuine, live ARAG mechanism this
            demo calls, or an honestly disclosed gap naming which mechanism isn't available and
            why. This view is built to be complete on its own - you don't need to see the live
            ARAG admin console afterward for this to make sense.
          </p>

          {pageContext && (
            // Fix (17 Aug 2026): these two cards use a fixed light tint
            // (var(--brand-softer) / var(--accent-soft)) as background in
            // BOTH colour schemes - it is not dark-mode aware. The body copy
            // was using `text-ink-700 dark:text-ink-200`, which correctly
            // reads dark-on-light in light mode but rendered pale
            // near-invisible light-grey text on that same light card once the
            // app's dark scheme was active (the modal shell went dark, these
            // two inset cards did not) - a real, reproduced low-contrast
            // defect. Fixed dark ink text, same discipline as DocumentRecord's
            // "this is paper, not app chrome" cards.
            <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div
                className="flex items-start gap-2.5 rounded-lg p-3.5"
                style={{ background: 'var(--brand-softer)', border: '1px solid var(--hairline)' }}
              >
                <Eye size={16} className="mt-0.5 shrink-0" style={{ color: 'var(--brand)' }} />
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wide" style={{ color: 'var(--brand-strong)' }}>
                    What this page is doing
                  </p>
                  <p className="mt-1 text-[13px] leading-relaxed" style={{ color: '#1d2133' }}>{pageContext.whatItDoes}</p>
                </div>
              </div>
              <div
                className="flex items-start gap-2.5 rounded-lg p-3.5"
                style={{ background: 'var(--accent-soft)', border: '1px solid var(--hairline)' }}
              >
                <Gem size={16} className="mt-0.5 shrink-0" style={{ color: 'var(--accent-strong)' }} />
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wide" style={{ color: 'var(--accent-strong)' }}>
                    Why it matters
                  </p>
                  <p className="mt-1 text-[13px] leading-relaxed" style={{ color: '#1d2133' }}>{pageContext.value}</p>
                </div>
              </div>
            </div>
          )}

          <p className="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wide text-ink-400">
            The request, flowing through the stack
          </p>
          {/* Steve Jobs review, 17 Aug 2026: the flow doesn't just list stages,
              it MOVES - a bright pulse falls down the timeline while each stage
              lights up in turn as the request reaches it. */}
          <ol className="arag-flow relative ml-3 space-y-0 border-l-2 pl-6" style={{ borderColor: 'var(--hairline)', ['--arag-flow-ms' as string]: `${flow.length * 520}ms` }}>
            <span className="arag-flow-track" aria-hidden />
            <span className="arag-flow-comet" aria-hidden />
            {flow.map((stage, i) => (
              <li key={i} className="relative pb-7 last:pb-0 arag-reveal-stage" style={{ animationDelay: `${i * 200}ms` }}>
                <span
                  className="arag-flow-dot absolute -left-[calc(1.5rem+6px)] top-1 h-3 w-3 rounded-full ring-4"
                  style={{
                    background: stage.status === 'disclosed-gap' ? '#f59e0b' : 'var(--brand)',
                    ['--tw-ring-color' as string]: 'var(--surface-1)',
                    animationDelay: `${i * 520}ms`,
                  }}
                  aria-hidden
                />
                <div className="flex items-center gap-2">
                  <span className="font-display text-sm font-semibold text-ink-900 dark:text-ink-50">{stage.stage}</span>
                  {stage.status === 'disclosed-gap' && (
                    <span className="rounded-full border border-amber-300 bg-amber-50 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-amber-700 dark:border-amber-800/70 dark:bg-amber-950/40 dark:text-amber-300">
                      Disclosed gap
                    </span>
                  )}
                </div>
                <p className="mt-1 text-xs text-ink-500">{stage.detail}</p>
              </li>
            ))}
          </ol>

          <a
            href="https://www.progress.com/agentic-rag"
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-ink-500 hover:text-ink-800 dark:hover:text-ink-100"
          >
            Learn about Progress Agentic RAG <ExternalLink size={12} />
          </a>
        </div>

        <style>{`
          @keyframes arag-reveal-in {
            from { opacity: 0; transform: translateX(-6px); }
            to { opacity: 1; transform: translateX(0); }
          }
          .arag-reveal-stage {
            animation: arag-reveal-in 420ms ease-out both;
          }
          /* The growing brand line that fills the timeline top-to-bottom as the
             request flows through it. */
          .arag-flow-track {
            position: absolute;
            left: -2px;
            top: 0;
            width: 2px;
            height: 100%;
            transform-origin: top;
            background: linear-gradient(to bottom, var(--brand), color-mix(in srgb, var(--brand) 55%, var(--accent)));
            animation: arag-flow-grow var(--arag-flow-ms, 2600ms) cubic-bezier(0.4, 0, 0.2, 1) both;
          }
          @keyframes arag-flow-grow { from { transform: scaleY(0); } to { transform: scaleY(1); } }
          /* The bright pulse ("comet") that falls down the line ahead of the fill. */
          .arag-flow-comet {
            position: absolute;
            left: -5px;
            top: 0;
            height: 8px;
            width: 8px;
            border-radius: 9999px;
            background: color-mix(in srgb, var(--accent) 70%, white);
            box-shadow: 0 0 12px 3px color-mix(in srgb, var(--accent) 70%, transparent);
            animation: arag-comet-fall var(--arag-flow-ms, 2600ms) cubic-bezier(0.4, 0, 0.2, 1) both;
          }
          @keyframes arag-comet-fall {
            0% { top: 0; opacity: 0; }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% { top: 100%; opacity: 0; }
          }
          /* Each stage dot pops as the request reaches it. */
          .arag-flow-dot { animation: arag-dot-pop 520ms cubic-bezier(0.22, 1, 0.36, 1) both; }
          @keyframes arag-dot-pop {
            0% { transform: scale(0.4); opacity: 0.3; }
            60% { transform: scale(1.35); opacity: 1; }
            100% { transform: scale(1); opacity: 1; }
          }
          @media (prefers-reduced-motion: reduce) {
            .arag-reveal-stage, .arag-flow-dot { animation: none; }
            .arag-flow-track { animation: none; transform: scaleY(1); }
            .arag-flow-comet { display: none; }
          }
        `}</style>
      </div>
    </div>
  );
}
