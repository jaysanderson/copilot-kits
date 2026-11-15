import { useEffect, useState } from 'react';
import { Info, X } from 'lucide-react';
import { ProgressBadge } from './ProgressBadge';

// Persistent synthetic-data disclaimer (Hard Rule 5). Rendered from
// demo.config.json's safety.disclaimer — every generated portal must show it.
// Refined to a slim, theme-tinted glass strip: present and honest, never a
// loud yellow bar. Dismissible for the session so it stays out of the way.
//
// Standard B12 fix (Compliance-co flagship-bar pass, 17 Aug 2026): ArchitectureReveal
// positions its trigger off `--progress-header-h` alone, but this banner sits
// BETWEEN the ProgressHeader and the app body — a real, reproduced defect: the
// "How this works" pill visually straddled this banner's own bottom edge on
// every route, because nothing published this strip's height for the reveal
// to add in. Publish it the same way ProgressHeader does (0px once dismissed,
// so the reveal snaps back up), so the two components can never drift apart.
export function DisclaimerBanner({ text }: { text: string }) {
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (!text || dismissed) {
      document.documentElement.style.setProperty('--disclaimer-banner-h', '0px');
    }
  }, [text, dismissed]);

  if (!text || dismissed) return null;

  const ref = (el: HTMLDivElement | null) => {
    if (!el) return;
    const publish = () => document.documentElement.style.setProperty('--disclaimer-banner-h', `${el.offsetHeight}px`);
    publish();
    const ro = new ResizeObserver(publish);
    ro.observe(el);
  };

  return (
    <div
      ref={ref}
      className="relative z-40 flex items-center justify-center gap-2 border-b px-4 py-1 text-center text-[11px] font-medium tracking-wide text-[color:var(--accent-strong)] dark:text-[color:var(--accent)]"
      style={{
        background: 'color-mix(in srgb, var(--accent) 8%, var(--glass))',
        borderColor: 'var(--glass-border)',
        WebkitBackdropFilter: 'blur(8px)',
        backdropFilter: 'blur(8px)',
      }}
      role="note"
    >
      <span
        className="h-1.5 w-1.5 shrink-0 rounded-full"
        style={{ background: 'var(--accent)' }}
        aria-hidden
      />
      <Info size={12} className="shrink-0 opacity-70" aria-hidden />
      <span className="truncate opacity-90">{text}</span>
      <button
        onClick={() => setDismissed(true)}
        aria-label="Dismiss notice"
        className="ml-1 shrink-0 rounded p-0.5 opacity-60 transition hover:opacity-100"
      >
        <X size={12} />
      </button>
    </div>
  );
}

export function DisclaimerFooter({ text, brand }: { text: string; brand: string }) {
  return (
    <footer className="relative mt-8 border-t px-6 py-6 text-xs text-ink-500" style={{ borderColor: 'var(--hairline)' }}>
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 sm:flex-row">
        <span className="inline-flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full" style={{ background: 'var(--brand)' }} aria-hidden />
          <span className="font-medium text-ink-600 dark:text-ink-300">{brand}</span>
        </span>
        <span className="flex-1 text-center text-ink-400">{text}</span>
        {/* GM standard (17 Aug 2026): standing, discreet Progress attribution -
            footer only, never the header/hero, so gate 2's "customer's own
            system" framing holds while the attribution is still always present. */}
        <ProgressBadge />
      </div>
    </footer>
  );
}
