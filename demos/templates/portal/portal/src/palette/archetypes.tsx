import { useEffect, type ReactNode } from 'react';
import { useIsDesktop } from '../lib/useMediaQuery';

// ─────────────────────────────────────────────────────────────────────────────
// Standard B9 (arag-demo-app skill, 17 Aug 2026) — layout variety. Before this
// file, the palette's only layout medium was Section/Hero/Panel/TileGrid
// (layout.tsx) — one archetype's worth of primitives (a top-nav editorial
// page). These five SHELL scaffolds are the parts bin `catalog/archetypes.json`
// already names conceptually (ops-console, media-archive, evaluation-lab,
// command-centre, voice-first-assistant, …) turned into real, composable,
// theme-token-driven React — so "pick a different archetype" is an actual
// import choice, not just an idea in a spec file a builder has to invent from
// scratch every time.
//
// Every scaffold here:
//   - is Kendo-free (plain elements + Tailwind + the brand/accent/ink tokens),
//     so it works identically in `kendo` and `opensource` UI_MODE;
//   - gates its own responsive structure in JS via `useIsDesktop()`, never CSS
//     `lg:`/`hidden` (Kendo's unlayered stylesheet beats Tailwind display
///     utilities — see useMediaQuery.ts);
//   - is a STRUCTURE only — no ARAG calls, no fixed content — a builder wires
//     real surfaces/pages into the slots.
//   - The Progress header (ProgressHeader, mounted once at the App frame) is
//     a SEPARATE layer above all of these — none of these scaffolds render
//     their own top brand band; they ARE the app body beneath it (Standard B2).
// ─────────────────────────────────────────────────────────────────────────────

/* ── 1. Sidebar / rail shell ─────────────────────────────────────────────── */

export interface SidebarNavItem {
  key: string;
  label: string;
  icon?: ReactNode;
  active?: boolean;
  onClick?: () => void;
}

/**
 * A left rail of icon+label nav + a content pane — the standard "internal
 * tool" skeleton (an ops console, an admin surface, a knowledge workspace).
 * Collapses to a bottom tab bar on mobile (touch-sized, app-like — Standard
 * B6), never a squeezed desktop rail.
 */
export function SidebarShell({
  brand, nav, children, footer,
}: {
  brand?: ReactNode; nav: SidebarNavItem[]; children: ReactNode; footer?: ReactNode;
}) {
  const isDesktop = useIsDesktop();

  // Compliance-co fix (17 Aug 2026): this bar and GuidedTourLauncher's floating
  // "Guided tour" pill both fix themselves to the viewport bottom - without
  // publishing this bar's real height, the pill sat on top of / collided
  // with the last tab on a genuine narrow phone viewport (a reproduced
  // defect, not a desktop-only assumption). Publish it the same way
  // ProgressHeader/DisclaimerBanner do; cleared to 0px on unmount (desktop,
  // or a shell not using SidebarShell) so the pill snaps back down.
  useEffect(() => {
    if (isDesktop) document.documentElement.style.setProperty('--mobile-tabbar-h', '0px');
  }, [isDesktop]);
  const tabbarRef = (el: HTMLElement | null) => {
    if (!el) return;
    const publish = () => document.documentElement.style.setProperty('--mobile-tabbar-h', `${el.offsetHeight}px`);
    publish();
    const ro = new ResizeObserver(publish);
    ro.observe(el);
  };

  if (!isDesktop) {
    return (
      <div className="flex min-h-full flex-col">
        <div className="min-h-0 flex-1 overflow-y-auto pb-20">{children}</div>
        <nav
          ref={tabbarRef}
          className="fixed inset-x-0 bottom-0 z-30 flex items-stretch justify-around border-t px-1 py-1.5"
          style={{ background: 'var(--surface-1)', borderColor: 'var(--hairline)' }}
        >
          {nav.map((item) => (
            <button
              key={item.key}
              onClick={item.onClick}
              className="flex min-w-0 flex-1 flex-col items-center gap-0.5 rounded-lg px-1 py-1.5 text-[10px] font-medium transition"
              style={{ color: item.active ? 'var(--brand)' : 'var(--ink-400, #9ba0b8)' }}
              aria-current={item.active ? 'page' : undefined}
            >
              <span className="text-[18px] leading-none">{item.icon}</span>
              <span className="truncate">{item.label}</span>
            </button>
          ))}
        </nav>
      </div>
    );
  }

  return (
    <div className="flex min-h-full">
      <aside
        className="flex w-60 shrink-0 flex-col border-r px-3 py-4"
        style={{ background: 'var(--surface-2)', borderColor: 'var(--hairline)' }}
      >
        {brand && <div className="mb-4 px-2">{brand}</div>}
        <nav className="flex-1 space-y-0.5">
          {nav.map((item) => (
            <button
              key={item.key}
              onClick={item.onClick}
              // Fix (17 Aug 2026): the inactive colour used to be an inline
              // `var(--ink-600, #4b5170)` - that CSS custom property is never
              // actually defined anywhere, so it always fell through to its
              // fixed dark-slate fallback. Against this aside's dark-mode
              // background (near-black) that measured ~2.5:1 contrast, well
              // under WCAG AA - legible-but-faint nav labels a reviewer would
              // read as "hard to read". `text-ink-600 dark:text-ink-300` uses
              // Tailwind's real, scheme-aware ink ramp instead.
              className={`flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-sm font-medium transition ${item.active ? '' : 'text-ink-600 dark:text-ink-300'}`}
              style={{
                background: item.active ? 'var(--brand-soft)' : 'transparent',
                color: item.active ? 'var(--brand)' : undefined,
              }}
              aria-current={item.active ? 'page' : undefined}
            >
              {item.icon && <span className="shrink-0">{item.icon}</span>}
              <span className="truncate">{item.label}</span>
            </button>
          ))}
        </nav>
        {footer && <div className="mt-3 px-2">{footer}</div>}
      </aside>
      <main className="min-w-0 flex-1 overflow-y-auto">{children}</main>
    </div>
  );
}

/* ── 2. Console shell (queue + detail + context) ─────────────────────────── */

/**
 * The ops-console/triage archetype: a queue rail, a detail pane, and an
 * optional context/status rail. On mobile, shows exactly one pane at a time
 * (queue OR detail) with a back affordance — never three panes squeezed onto
 * a phone.
 */
export function ConsoleShell({
  queue, queueTitle, detail, context, showingDetail = false, onBack,
}: {
  queue: ReactNode; queueTitle?: ReactNode; detail: ReactNode; context?: ReactNode;
  /** Mobile only: true once a queue item is selected — swaps the single visible pane to `detail`. */
  showingDetail?: boolean;
  onBack?: () => void;
}) {
  const isDesktop = useIsDesktop();

  if (!isDesktop) {
    return (
      <div className="flex min-h-full flex-col">
        {showingDetail ? (
          <>
            <button onClick={onBack} className="flex items-center gap-1.5 px-4 py-3 text-sm font-medium" style={{ color: 'var(--brand)' }}>
              ← Back
            </button>
            <div className="min-h-0 flex-1 overflow-y-auto">{detail}</div>
          </>
        ) : (
          <div className="min-h-0 flex-1 overflow-y-auto">
            {queueTitle && <div className="px-4 pb-2 pt-4 text-xs font-semibold uppercase tracking-wide text-ink-500">{queueTitle}</div>}
            {queue}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="grid min-h-full" style={{ gridTemplateColumns: context ? '19rem minmax(0,1fr) 18rem' : '19rem minmax(0,1fr)' }}>
      <div className="min-h-0 overflow-y-auto border-r" style={{ borderColor: 'var(--hairline)', background: 'var(--surface-2)' }}>
        {queueTitle && <div className="px-4 pb-2 pt-4 text-xs font-semibold uppercase tracking-wide text-ink-500">{queueTitle}</div>}
        {queue}
      </div>
      <div className="min-h-0 min-w-0 overflow-y-auto">{detail}</div>
      {context && (
        <div className="min-h-0 overflow-y-auto border-l px-4 py-4" style={{ borderColor: 'var(--hairline)', background: 'var(--surface-2)' }}>
          {context}
        </div>
      )}
    </div>
  );
}

/* ── 3. Split pane (list + detail) ───────────────────────────────────────── */

/** A simpler two-pane list+detail (search results + a reading pane, a matter list + a matter view). Stacks on mobile. */
export function SplitPane({
  list, detail, listWidth = '22rem', showDetailOnMobile = false,
}: {
  list: ReactNode; detail: ReactNode; listWidth?: string; showDetailOnMobile?: boolean;
}) {
  const isDesktop = useIsDesktop();
  if (!isDesktop) {
    return <div className="min-h-0 flex-1 overflow-y-auto">{showDetailOnMobile ? detail : list}</div>;
  }
  return (
    <div className="flex min-h-full">
      <div className="min-h-0 shrink-0 overflow-y-auto border-r" style={{ width: listWidth, borderColor: 'var(--hairline)' }}>
        {list}
      </div>
      <div className="min-h-0 min-w-0 flex-1 overflow-y-auto">{detail}</div>
    </div>
  );
}

/* ── 4. Dashboard / command-centre grid ──────────────────────────────────── */

/** A 12-col bento grid for KPI tiles, charts and panels. Use <DashboardTile span={n}> to size a child. */
export function DashboardGrid({ children, gap = 4 }: { children: ReactNode; gap?: number }) {
  return (
    <div
      className="grid grid-cols-4 sm:grid-cols-8 lg:grid-cols-12"
      style={{ gap: `${gap * 0.25}rem` }}
    >
      {children}
    </div>
  );
}

/** A tile inside DashboardGrid — `span` is out of 12 at the desktop breakpoint, halved on tablet, full width on mobile. */
export function DashboardTile({ span = 4, children, className = '' }: { span?: 3 | 4 | 6 | 8 | 12; children: ReactNode; className?: string }) {
  const colSpanClass: Record<number, string> = {
    3: 'col-span-4 sm:col-span-4 lg:col-span-3',
    4: 'col-span-4 sm:col-span-4 lg:col-span-4',
    6: 'col-span-4 sm:col-span-8 lg:col-span-6',
    8: 'col-span-4 sm:col-span-8 lg:col-span-8',
    12: 'col-span-4 sm:col-span-8 lg:col-span-12',
  };
  return <div className={`${colSpanClass[span]} ${className}`}>{children}</div>;
}

/* ── 5. Phone / call console ─────────────────────────────────────────────── */

/**
 * The voice-first / call-console archetype (Standard B16: ONE voice use case
 * by default) — a centred device-style column with a caller header, a scrolling
 * transcript/timeline body, and a fixed action bar. Reads as a softphone, not
 * a web page with a phone icon on it.
 */
export function PhoneConsole({
  header, children, actions,
}: {
  header: ReactNode; children: ReactNode; actions?: ReactNode;
}) {
  return (
    <div className="mx-auto flex min-h-full w-full max-w-md flex-col">
      <div
        className="shrink-0 rounded-b-2xl px-5 pb-5 pt-4 text-white shadow-lg"
        style={{ background: 'linear-gradient(160deg, var(--brand-strong), color-mix(in srgb, var(--brand) 60%, var(--accent)))' }}
      >
        {header}
      </div>
      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-4">{children}</div>
      {actions && (
        <div className="shrink-0 border-t px-4 py-3" style={{ borderColor: 'var(--hairline)', background: 'var(--surface-1)' }}>
          {actions}
        </div>
      )}
    </div>
  );
}
