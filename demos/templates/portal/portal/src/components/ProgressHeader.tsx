// GM binding standard (17 Aug 2026): every demo carries a brand-compliant
// PROGRESS AGENTIC RAG header, built to the `progress-arag-branding` skill,
// as a standing scaffold slot — never per-build discretion. This is deliberate
// evolution of table-stakes gate 2, not a conflict with it (GM's own framing,
// 17 Aug 2026): this band openly frames the page as a Progress Agentic RAG
// demo; the customer/vertical experience (the own-system realism gate 2 still
// requires) renders BENEATH it, in the app body. The discreet
// "Built on Progress Agentic RAG" footer credit (<ProgressBadge />) and the
// full Progress presence inside <ArchitectureReveal /> both still stand
// unchanged — this header is additive and always-on, not a replacement.
//
// Brand-compliance notes (progress-arag-branding skill), so a future editor
// doesn't accidentally break these:
//   - Logo: the REAL bundled lockup (portal/public/brand/*.svg), never redrawn
//     or approximated. `primary-horizontal-alternate.svg` (white wordmark) on
//     this dark Blue P1 bar, per the skill's byBackground:dark rule.
//   - Colour: bar background is Blue P1 (#00216B) — the skill's own
//     "invert to a Blue P1 section, white headings" pattern. Never Agentic RAG
//     green as a background field here; green is accent/data only.
//   - Type: Progress Sans Display for the wordmark fallback text, Text for the
//     small "Agentic RAG Demo" eyebrow — Arial is the only approved substitute
//     (no Helvetica/Inter/system stack) when Progress Sans isn't loaded.
//   - Minimum size / clear space: the logo renders at >=75px height on desktop
//     per the skill's audit checklist ("Rendered at >= 75px (screen)... at the
//     smallest breakpoint"); this necessarily makes the band tall. Below the
//     640px breakpoint it steps down to 56px, a deliberate, documented
//     trade-off against on-screen real estate on a phone — flagged here for
//     qa-reviewer rather than silently shrunk without a note.
//   - The Hex Loop device is NOT used here (it bleeds off a full-bleed edge,
//     not a slim nav band) — that stays reserved for hero/title treatments
//     elsewhere, per the skill's cropping guidance.
export function ProgressHeader() {
  // Standard B12 (arag-demo-app skill, 17 Aug 2026): the "How this works"
  // trigger (ArchitectureReveal) must sit cleanly below this band, never
  // straddling the header/body boundary. This band's own height is NOT fixed —
  // it steps from ~64px (mobile) to ~120px (desktop, >=640px: 76px logo +
  // 22px*2 padding) — so a hardcoded pixel offset on the reveal button drifts
  // out of sync with real, resizable/responsive height (a real, reproduced
  // defect: a 100px hardcoded offset against a 120px desktop band left the
  // button 20px INSIDE it). Publish the real measured height as a CSS custom
  // property every render/resize so ArchitectureReveal can position off it
  // instead of guessing.
  const ref = (el: HTMLDivElement | null) => {
    if (!el) return;
    const publish = () => document.documentElement.style.setProperty('--progress-header-h', `${el.offsetHeight}px`);
    publish();
    const ro = new ResizeObserver(publish);
    ro.observe(el);
    // Not disconnected on unmount — this header is mounted once for the life
    // of the app shell (App.tsx), same lifetime as the CSS var it publishes.
  };
  return (
    <div
      ref={ref}
      role="banner"
      aria-label="Progress Agentic RAG"
      className="arag-progress-header flex w-full items-center justify-center gap-3 px-4 py-3 sm:py-4"
      style={{ background: '#00216B' }}
    >
      <a
        href="https://www.progress.com/agentic-rag"
        target="_blank"
        rel="noreferrer"
        className="flex items-center gap-3"
        aria-label="Progress Agentic RAG"
      >
        <img
          src="/brand/progress-arag-logo-alternate.svg"
          alt="Progress Agentic RAG"
          className="arag-progress-header__logo block"
          style={{ height: 40, width: 'auto' }}
        />
      </a>
      <span
        className="hidden text-[11px] font-medium uppercase tracking-wide text-white/70 sm:inline"
        style={{ fontFamily: '"Progress Sans Text", Arial, sans-serif' }}
      >
        Agentic RAG Demo
      </span>
      <style>{`
        /* Brand-compliant minimum-size step: >=75px logo height at desktop
           widths (skill audit checklist), stepping down at the sm breakpoint
           so a phone viewport doesn't lose most of its screen to the band. */
        @media (min-width: 640px) {
          .arag-progress-header { padding-top: 22px; padding-bottom: 22px; }
          .arag-progress-header__logo { height: 76px !important; }
        }
      `}</style>
    </div>
  );
}
