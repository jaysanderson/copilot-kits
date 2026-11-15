import { useEffect } from 'react';
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, FileInput, MessagesSquare, Scale, ShieldAlert, BarChart3, Bot, Moon, Sun, RotateCcw, Waves, Play,
  ClipboardCheck, Handshake,
} from 'lucide-react';
import type { CompositionContext, DemoComposition } from '../palette/compose';
import { useIsDesktop } from '../lib/useMediaQuery';
import { useIsDark, setColorScheme } from '../lib/theme';
import { StatusChip } from '../components/StatusChip';
import { AmbientBackground } from '../components/AmbientBackground';
import { openGuidedTour } from '../components/GuidedTourLauncher';
import { ResourceDetail } from '../pages/ResourceDetail';
import { ClaimsDeskProvider, useClaimsDesk, CLAIMS } from './store';
import { ClaimQueue } from './ui';
import { DeskPage } from './pages/DeskPage';
import { IntakePage } from './pages/IntakePage';
import { CoveragePage } from './pages/CoveragePage';
import { DecisionPage } from './pages/DecisionPage';
import { ExceptionsPage } from './pages/ExceptionsPage';
import { PortfolioPage } from './pages/PortfolioPage';
import { CopilotPage } from './pages/CopilotPage';
import { UnderwritingPage } from './pages/UnderwritingPage';
import { BrokerCopilotPage } from './pages/BrokerCopilotPage';

// ─────────────────────────────────────────────────────────────────────────────
// Publisher Mutual Claims Desk - a bespoke "claims workbench" shell (Standard
// B1/B9: its own layout, not the exemplar's and not the parallel demos').
//
// The archetype is a queue + reading room: a navy module rail on the far left
// (the product's own navigation), a bright claims-queue pane on the claim-scoped
// routes, and the reading room where the selected claim is worked. The Progress
// Agentic RAG header (App.tsx) frames the whole thing from above; this is the
// app BODY beneath it (Standard B2), and the Progress-blue brand carries all the
// way through the body - navy chrome, the claim documents as bright paper against
// it (Standard B21), never a generic dark-mode app.
//
// Desk / Portfolio / Copilot are desk-level (full width, no queue pane); Intake
// / Coverage / Decision / Exceptions are claim-scoped (queue pane + the active
// claim). On a phone the module rail becomes a bottom tab bar and the queue
// becomes a horizontal claim selector inside each claim-scoped page.
// ─────────────────────────────────────────────────────────────────────────────

interface NavItem { to: string; label: string; short: string; icon: typeof Bot }
const NAV: NavItem[] = [
  { to: '/', label: 'Claims Desk', short: 'Desk', icon: LayoutDashboard },
  { to: '/intake', label: 'Claim Intake', short: 'Intake', icon: FileInput },
  { to: '/coverage', label: 'Coverage Q&A', short: 'Coverage', icon: MessagesSquare },
  { to: '/decision', label: 'Coverage Decision', short: 'Decision', icon: Scale },
  { to: '/exceptions', label: 'Exception Check', short: 'Exceptions', icon: ShieldAlert },
  { to: '/reports', label: 'Portfolio', short: 'Portfolio', icon: BarChart3 },
  { to: '/copilot', label: 'Claims Copilot', short: 'Copilot', icon: Bot },
  { to: '/underwriting', label: 'Underwriting Risk Summary', short: 'Underwrite', icon: ClipboardCheck },
  { to: '/broker-copilot', label: 'Broker Copilot', short: 'Broker', icon: Handshake },
];

const CLAIM_SCOPED = new Set(['/intake', '/coverage', '/decision', '/exceptions']);
const EXCEPTION_COUNT = CLAIMS.filter((c) => c.angle === 'exception' || c.status === 'Under investigation').length;

function BrandLockup() {
  return (
    <div className="flex items-center gap-2.5">
      <span
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white"
        style={{ background: 'linear-gradient(150deg, var(--accent), color-mix(in srgb, var(--accent) 55%, #b45309))', boxShadow: '0 6px 16px -8px color-mix(in srgb, var(--accent) 80%, transparent)' }}
        aria-hidden
      >
        <Waves size={19} />
      </span>
      <div className="min-w-0 leading-tight">
        <p className="truncate font-display text-sm font-semibold text-white">Publisher Mutual</p>
        <p className="text-[11px] text-white/60">Claims Desk</p>
      </div>
    </div>
  );
}

function DarkToggle({ onDark = false }: { onDark?: boolean }) {
  const dark = useIsDark();
  const cls = onDark
    ? 'flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-sm font-medium text-white/70 transition hover:bg-white/10'
    : 'flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-medium text-ink-500 transition hover:bg-ink-100 dark:hover:bg-white/5';
  return (
    <button type="button" onClick={() => setColorScheme(!dark)} aria-label="Toggle colour scheme" title="Toggle colour scheme" className={cls}>
      {dark ? <Sun size={16} className="shrink-0" /> : <Moon size={16} className="shrink-0" />}
      <span className="truncate">{dark ? 'Light mode' : 'Dark mode'}</span>
    </button>
  );
}

function ResetButton({ onDark = false }: { onDark?: boolean }) {
  const { clear } = useClaimsDesk();
  const cls = onDark
    ? 'flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-sm font-medium text-white/70 transition hover:bg-white/10'
    : 'flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-medium text-ink-500 transition hover:bg-ink-100 dark:hover:bg-white/5';
  return (
    <button type="button" onClick={() => clear()} title="Reset the desk to its seeded state" className={cls}>
      <RotateCcw size={15} className="shrink-0" />
      <span className="truncate">Reset desk</span>
    </button>
  );
}

function ModuleRail() {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  return (
    <aside
      className="flex w-60 shrink-0 flex-col px-3 py-4"
      style={{ background: 'linear-gradient(185deg, var(--brand-strong), color-mix(in srgb, var(--brand-strong) 82%, black))', borderRight: '1px solid rgba(255,255,255,0.08)' }}
    >
      <div className="mb-5 px-2"><BrandLockup /></div>
      <nav className="flex-1 space-y-1">
        {NAV.map((n) => {
          const active = n.to === pathname;
          const Icon = n.icon;
          const badge = n.to === '/exceptions' ? EXCEPTION_COUNT : 0;
          return (
            <button
              key={n.to}
              onClick={() => navigate(n.to)}
              aria-current={active ? 'page' : undefined}
              className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-sm font-medium transition"
              style={{
                background: active ? 'color-mix(in srgb, var(--accent) 20%, transparent)' : 'transparent',
                color: active ? '#fff' : 'rgba(255,255,255,0.68)',
                boxShadow: active ? 'inset 0 0 0 1px color-mix(in srgb, var(--accent) 45%, transparent)' : 'none',
              }}
            >
              <span className="relative inline-flex shrink-0">
                <Icon size={17} />
                {!!badge && (
                  <span className="absolute -right-2 -top-1.5 inline-flex h-4 min-w-4 items-center justify-center rounded-full px-1 text-[9px] font-bold text-white" style={{ background: '#dc2626' }}>{badge}</span>
                )}
              </span>
              <span className="truncate">{n.label}</span>
            </button>
          );
        })}
      </nav>
      <div className="mt-3 space-y-1 border-t border-white/10 pt-3">
        <div className="px-1"><StatusChip /></div>
        <ResetButton onDark />
        <DarkToggle onDark />
      </div>
    </aside>
  );
}

function MobileTabBar({ config }: { config: CompositionContext['config'] }) {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const isDesktop = useIsDesktop();
  const hasTour = (config.demoScript?.length || 0) > 0;
  const tabbarRef = (el: HTMLElement | null) => {
    if (!el) return;
    const publish = () => document.documentElement.style.setProperty('--mobile-tabbar-h', `${el.offsetHeight}px`);
    publish();
    new ResizeObserver(publish).observe(el);
  };
  useEffect(() => { if (isDesktop) document.documentElement.style.setProperty('--mobile-tabbar-h', '0px'); }, [isDesktop]);
  if (isDesktop) return null;
  // Finding 4 fix, THIRD attempt (demo-tester, 28 Aug 2026) - the first two
  // attempts (a trailing spacer, then a separate scroll lane) both left a real
  // geometric overlap: `getBoundingClientRect()` reports a flex item's full
  // layout box regardless of an ancestor's `overflow-x-auto` clipping it
  // visually, so a horizontally-scrolling lane can NEVER make a raw box query
  // report zero overlap for whichever tab straddles the visible/clipped
  // boundary - re-measured live and it was still x:268-332 for "Exceptions"
  // against Tour's x:322-386, byte-for-byte the same as before either "fix".
  // No amount of overflow/clip CSS changes a child's own box geometry.
  // The actual fix: stop scrolling. A 2-row CSS grid (5 columns) fits all 9
  // NAV items plus Tour as a genuine 10th cell - grid cells are mutually
  // exclusive regions by construction, so this is not visually-probably
  // non-overlapping, it is STRUCTURALLY impossible for any two cells to
  // intersect, satisfying a raw bounding-box check the same way a visual one.
  return (
    <nav
      ref={tabbarRef}
      className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 gap-0.5 px-1 py-1.5"
      style={{ background: 'var(--brand-strong)', borderTop: '1px solid rgba(255,255,255,0.1)' }}
    >
      {NAV.map((n) => {
        const active = n.to === pathname;
        const Icon = n.icon;
        return (
          <button
            key={n.to}
            onClick={() => navigate(n.to)}
            aria-current={active ? 'page' : undefined}
            className="flex min-w-0 flex-col items-center justify-center gap-0.5 rounded-lg px-1 py-1.5 text-[10px] font-medium transition"
            style={{ color: active ? '#fff' : 'rgba(255,255,255,0.6)', background: active ? 'color-mix(in srgb, var(--accent) 22%, transparent)' : 'transparent' }}
          >
            <Icon size={17} />
            <span className="w-full truncate text-center">{n.short}</span>
          </button>
        );
      })}
      {/* B32 fix (18 Aug 2026): the guided-tour trigger docks HERE, in this
          bar's own permanent chrome, instead of floating over page content -
          see GuidedTourLauncher.tsx. Now the 10th grid cell (row 2, column 5)
          - a real cell like any nav tab, not an overlay - so it is
          structurally guaranteed never to sit on top of one. Styled in the
          accent colour + a real shadow so it reads as distinct/prominent
          (Standard B18). */}
      {hasTour && (
        <button
          type="button"
          onClick={() => openGuidedTour()}
          aria-label="Start the guided tour"
          className="flex min-w-0 flex-col items-center justify-center gap-0.5 rounded-lg px-1 py-1.5 text-[10px] font-bold shadow-lg transition"
          style={{ color: '#fff', background: 'var(--accent)' }}
        >
          <Play size={18} />
          <span className="truncate">Tour</span>
        </button>
      )}
    </nav>
  );
}

function InnerShell({ config }: CompositionContext) {
  const dark = useIsDark();
  const isDesktop = useIsDesktop();
  const { pathname } = useLocation();
  const claimScoped = CLAIM_SCOPED.has(pathname);

  const routes = (
    <Routes>
      <Route path="/" element={<DeskPage config={config} />} />
      <Route path="/intake" element={<IntakePage config={config} />} />
      <Route path="/coverage" element={<CoveragePage config={config} />} />
      <Route path="/decision" element={<DecisionPage config={config} />} />
      <Route path="/exceptions" element={<ExceptionsPage config={config} />} />
      <Route path="/reports" element={<PortfolioPage config={config} />} />
      <Route path="/copilot" element={<CopilotPage config={config} />} />
      <Route path="/underwriting" element={<UnderwritingPage config={config} />} />
      <Route path="/broker-copilot" element={<BrokerCopilotPage config={config} />} />
      <Route
        path="/r/:id"
        element={<div className="mx-auto max-w-6xl px-4 py-8 sm:px-6"><ResourceDetail config={config} /></div>}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );

  if (!isDesktop) {
    return (
      <>
        <AmbientBackground dark={dark} />
        {/* The 2-row grid tab bar (finding 4 fix, 28 Aug 2026) is taller than
            the old single scrolling row - pb-24 (96px) was sized for that and
            under-clears the new ~106px bar. Use the actual measured height
            (published live by MobileTabBar's ResizeObserver) plus a small
            margin instead of a guessed constant, so this never drifts out of
            sync with the bar's real height again. */}
        <div className="min-h-full" style={{ paddingBottom: 'calc(var(--mobile-tabbar-h, 96px) + 0.75rem)' }}>{routes}</div>
        <MobileTabBar config={config} />
      </>
    );
  }

  return (
    <>
      <AmbientBackground dark={dark} />
      <div className="flex min-h-full">
        <ModuleRail />
        {claimScoped ? (
          <div className="grid min-w-0 flex-1" style={{ gridTemplateColumns: '19rem minmax(0,1fr)' }}>
            <div className="min-h-0 overflow-y-auto border-r px-4 py-5" style={{ borderColor: 'var(--hairline)', background: 'var(--surface-2)' }}>
              <ClaimQueue />
            </div>
            <main className="min-w-0 overflow-y-auto">{routes}</main>
          </div>
        ) : (
          <main className="min-w-0 flex-1 overflow-y-auto">{routes}</main>
        )}
      </div>
    </>
  );
}

function Shell(ctx: CompositionContext) {
  return (
    <ClaimsDeskProvider>
      <InnerShell {...ctx} />
    </ClaimsDeskProvider>
  );
}

export const composition: DemoComposition = { Shell };
