// GM standard (17 Aug 2026, folded into the flagship rebuild): every scaffolded
// demo carries a discreet, standing "Built on Progress Agentic RAG" attribution
// in the ambient view - WITHOUT breaking table-stakes gate 2 (the hero still
// reads as the customer's own system; no ARAG chrome in the header/hero, no
// exposed endpoint names in the default customer-facing view).
//
// Placement discipline: this renders ONLY in the universal footer frame
// (alongside <DisclaimerFooter>, itself already outside the hero/header on
// both the config-shell and any bespoke composition.tsx Shell) - never in the
// AppBar, hero, or nav. Small, quiet, unmissable to anyone who looks, invisible
// to the ambient read. The louder, explicit Progress branding lives in the
// solution-architecture reveal (<ArchitectureReveal />) instead, which is the
// deliberate opt-in place ARAG/Progress chrome is shown at full prominence.
export function ProgressBadge() {
  return (
    <a
      href="https://www.progress.com/agentic-rag"
      target="_blank"
      rel="noreferrer"
      className="inline-flex items-center gap-1.5 text-[11px] font-medium text-ink-400 opacity-70 transition hover:opacity-100 dark:text-ink-500"
      title="This system runs on Progress Agentic RAG"
    >
      <span
        aria-hidden
        className="inline-block h-2 w-2 rounded-sm"
        style={{ background: 'linear-gradient(135deg, #00216B, #00B563)' }}
      />
      Built on Progress Agentic RAG
    </a>
  );
}
