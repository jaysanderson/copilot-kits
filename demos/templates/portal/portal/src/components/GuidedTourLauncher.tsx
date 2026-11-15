import { useEffect, useState } from 'react';
import { Play } from 'lucide-react';
import type { DemoConfig, Surface } from '../lib/config';
import { GuidedTour } from './GuidedTour';
import { useIsDesktop } from '../lib/useMediaQuery';

const OPEN_EVENT = 'arag:open-guided-tour';

/** Dispatch this from any inline chrome trigger (a header/tab-bar button) to
 * open the tour without needing a ref/context back to this component - see
 * the mobile-dock fix below. */
export function openGuidedTour() {
  window.dispatchEvent(new Event(OPEN_EVENT));
}

/**
 * Self-managed guided-tour affordance: a floating launch pill + the GuidedTour
 * itself, owning its own open/close state. Drop it in ONCE and a demo has the
 * guided walkthrough — no wiring required. The universal App frame mounts this
 * for every bespoke Shell so EVERY build ships the tour (the config shell keeps
 * its own in-bar "Guided tour" button instead). Renders nothing when the demo
 * has no demoScript, but every build should generate one.
 *
 * B32 fix (18 Aug 2026, GM correction - reproduced live at 390px on all three
 * flagship demos): a `position:fixed` pill anchored to the viewport corner
 * WILL sit on top of whatever content (product/KPI cards, a grid row) happens
 * to be there at that screen position, at any scroll depth, on a busy mobile
 * page — reserving end-of-scroll padding doesn't fix this, since the overlap
 * happens well before the true end of a page (reproduced on first load, no
 * scrolling at all). And it can't just be shrunk to dodge content — Standard
 * B18 rules out icon-only-by-default as too easy to miss, so it has to stay a
 * real icon+label pill. The only fix that's actually airtight is to stop
 * floating it over scrollable content at all on mobile: this component now
 * shows the pill ONLY on desktop (where the reference layouts have margin
 * around it and no defect was found); on mobile each bespoke Shell docks a
 * compact trigger of its own into its PERMANENT chrome instead (the header
 * bar / bottom tab bar - the same non-scrolling real estate the hamburger and
 * dark-mode toggle already live in, so it can never overlap page content) and
 * calls `openGuidedTour()` to fire it - see composition.tsx's mobile nav.
 */
export function GuidedTourLauncher({
  config,
  surfaces,
  floating = true,
}: {
  config: DemoConfig;
  surfaces: Surface[];
  floating?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const isDesktop = useIsDesktop();
  const hasTour = (config.demoScript?.length || 0) > 0;

  useEffect(() => {
    const onOpen = () => setOpen(true);
    window.addEventListener(OPEN_EVENT, onOpen);
    return () => window.removeEventListener(OPEN_EVENT, onOpen);
  }, []);

  if (!hasTour) return null;

  return (
    <>
      {floating && isDesktop && !open && (
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Start the guided tour"
          // B18 fix (17 Aug 2026, GM correction): the previous fill
          // (--brand-strong, a DARKENED navy on this app's dark theme) nearly
          // disappeared against the app's own near-black background - exactly
          // the "barely visible" defect. A guided tour must be PROMINENT: a
          // brighter, higher-contrast Progress accent fill, a visible glow
          // ring that pulses so it reads as "notice me", and real weight
          // (icon + label together, not icon-only) even on a narrow phone -
          // Standard B18 rules out icon-only-by-default as too easy to miss.
          className="fixed bottom-5 right-5 z-30 flex items-center gap-2 rounded-lg px-4 py-3 text-sm font-bold shadow-2xl transition hover:brightness-110 active:scale-[0.98]"
          style={{
            background: 'var(--accent)',
            color: 'var(--accent-contrast, #fff)',
            boxShadow:
              '0 0 0 1px color-mix(in srgb, white 25%, transparent) inset, 0 12px 32px -10px color-mix(in srgb, var(--accent) 80%, transparent), 0 0 0 5px color-mix(in srgb, var(--accent) 22%, transparent)',
          }}
        >
          <span className="relative flex h-2 w-2 shrink-0">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full" style={{ background: 'var(--accent-contrast, #fff)', opacity: 0.6 }} />
            <span className="relative inline-flex h-2 w-2 rounded-full" style={{ background: 'var(--accent-contrast, #fff)' }} />
          </span>
          <Play size={15} />
          <span>Guided tour</span>
        </button>
      )}
      <GuidedTour config={config} surfaces={surfaces} open={open} onClose={() => setOpen(false)} />
    </>
  );
}
