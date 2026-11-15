import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Droplets, Waves, Car, Flame, ShieldOff, DoorOpen, CloudLightning, Package, ShieldAlert, MapPin, CalendarClock,
} from 'lucide-react';
import { PersonLine } from '../components/Person';
import {
  CLAIMS, statusTone, formatMoney, type Claim, type ClaimStatus, useClaimsDesk,
} from './store';

// ─────────────────────────────────────────────────────────────────────────────
// Shared claims-desk UI - the parts every page reuses: the peril glyph, the
// status pill, the claim "file" card, the claims queue, and the active-claim
// header that anchors every claim-scoped reading room. Kept bespoke to this
// demo (its own identity, Standard B1) but built entirely from the design-system
// tokens (var(--brand)/var(--accent)/--ink-*), never arbitrary values.
// ─────────────────────────────────────────────────────────────────────────────

const PERIL_ICON: Record<string, typeof Droplets> = {
  'Water damage': Droplets,
  'Flood': Waves,
  'Collision': Car,
  'Fire': Flame,
  'Theft': ShieldOff,
  'Burglary': DoorOpen,
  'Storm': CloudLightning,
  'Windscreen': Car,
  'Impact': Package,
};

export function PerilIcon({ peril, size = 16 }: { peril: string; size?: number }) {
  const Icon = PERIL_ICON[peril] || Package;
  return <Icon size={size} />;
}

export function StatusPill({ status, className = '' }: { status: ClaimStatus; className?: string }) {
  const tone = statusTone(status);
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-[11px] font-semibold ${className}`}
      style={{ color: tone, background: `color-mix(in srgb, ${tone} 15%, transparent)`, border: `1px solid color-mix(in srgb, ${tone} 35%, transparent)` }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: tone }} />
      {status}
    </span>
  );
}

// A miniature claim "file" object - a bright paper card against the navy chrome
// (Standard B8: the content is the hero). Peril glyph, claim number, claimant,
// peril, amount and a status pill. Deliberately tactile: hover-to-lift.
export function ClaimCard({
  claim, active, onClick, compact = false,
}: {
  claim: Claim; active?: boolean; onClick?: () => void; compact?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group block w-full text-left transition-transform duration-150 hover:-translate-y-0.5 focus:outline-none"
      aria-current={active ? 'true' : undefined}
    >
      <div
        className="overflow-hidden rounded-xl"
        style={{
          background: 'var(--surface-1)',
          border: active ? '1.5px solid var(--accent)' : '1px solid var(--hairline)',
          boxShadow: active
            ? '0 10px 28px -14px color-mix(in srgb, var(--accent) 60%, transparent)'
            : '0 6px 18px -14px rgba(0,0,0,0.55)',
        }}
      >
        {/* paper masthead - a claim-file top edge */}
        <div className="flex items-center gap-2 px-3 pt-2.5" >
          <span
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-white"
            style={{ background: `linear-gradient(155deg, var(--brand-strong), var(--brand))` }}
          >
            <PerilIcon peril={claim.peril} size={14} />
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate font-mono text-[11px] font-semibold text-ink-500">{claim.claimNumber}</p>
            <p className="truncate font-display text-sm font-semibold text-ink-900 dark:text-ink-50">{claim.claimant.name}</p>
            <p className="truncate text-[10px] text-ink-400">{claim.claimant.role}</p>
          </div>
        </div>
        <div className="px-3 pb-2.5 pt-2">
          <div className="mb-2 flex items-center justify-between gap-2">
            <span className="inline-flex items-center gap-1.5 text-xs text-ink-500">
              <PerilIcon peril={claim.peril} size={12} /> {claim.peril}
            </span>
            <span className="font-mono text-xs font-semibold text-ink-700 dark:text-ink-200">{formatMoney(claim.amount)}</span>
          </div>
          {!compact && (
            <p className="mb-2 line-clamp-2 text-[11px] leading-relaxed text-ink-500">{claim.summary}</p>
          )}
          <div className="flex items-center justify-between gap-2">
            <StatusPill status={claim.status} />
            <span className="text-[10px] uppercase tracking-wide text-ink-400">{claim.productLine}</span>
          </div>
        </div>
      </div>
    </button>
  );
}

// The claims queue - the spine of the workbench. Selecting a card sets the
// active claim in the store; a per-page onSelect can navigate as well.
export function ClaimQueue({
  onSelect, className = '', title = 'Claims queue',
}: {
  onSelect?: (claim: Claim) => void; className?: string; title?: string;
}) {
  const { activeClaimId, setActiveClaim } = useClaimsDesk();
  return (
    <div className={className}>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wide text-ink-400">{title}</p>
        <span className="rounded-md px-1.5 py-0.5 text-[11px] font-semibold text-ink-500" style={{ background: 'var(--surface-2)' }}>
          {CLAIMS.length}
        </span>
      </div>
      <div className="space-y-2.5">
        {CLAIMS.map((c) => (
          <ClaimCard
            key={c.id}
            claim={c}
            active={c.id === activeClaimId}
            onClick={() => { setActiveClaim(c.id); onSelect?.(c); }}
          />
        ))}
      </div>
    </div>
  );
}

// The active-claim header that anchors every claim-scoped reading room, so the
// handler always knows which file they are working. Name + role (Standard B14).
export function ClaimHeader({ claim, kicker }: { claim: Claim; kicker?: string }) {
  return (
    <div
      className="overflow-hidden rounded-2xl"
      style={{ background: `linear-gradient(155deg, var(--brand-strong), var(--brand))`, boxShadow: '0 16px 40px -22px rgba(0,0,0,0.7)' }}
    >
      <div className="flex flex-col gap-3 p-5 text-white sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          {kicker && <p className="text-[11px] font-semibold uppercase tracking-wide text-white/60">{kicker}</p>}
          <div className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/15">
              <PerilIcon peril={claim.peril} size={18} />
            </span>
            <div className="min-w-0">
              <p className="truncate font-display text-lg font-semibold leading-tight">{claim.claimant.name} <span className="text-sm font-normal text-white/70">({claim.claimant.role})</span></p>
              <p className="font-mono text-xs text-white/70">{claim.claimNumber} &middot; {claim.policyNumber}</p>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-md bg-white/12 px-2.5 py-1 text-xs font-medium">
            <PerilIcon peril={claim.peril} size={12} /> {claim.peril}
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-md bg-white/12 px-2.5 py-1 text-xs font-medium">
            {formatMoney(claim.amount)}
          </span>
          <StatusPillOnDark status={claim.status} />
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 border-t border-white/10 px-5 py-2.5 text-[11px] text-white/70">
        <span className="inline-flex items-center gap-1.5"><MapPin size={12} /> {claim.incidentLocation}</span>
        <span className="inline-flex items-center gap-1.5"><CalendarClock size={12} /> Date of loss {claim.dateOfLoss}</span>
        <span className="inline-flex items-center gap-1.5">
          <ShieldAlert size={12} /> Handler
          <span className="text-white/90"><PersonLine name={claim.assignedTo.name} role={claim.assignedTo.role} className="text-[11px] text-white/90" /></span>
        </span>
      </div>
    </div>
  );
}

function StatusPillOnDark({ status }: { status: ClaimStatus }) {
  const tone = statusTone(status);
  return (
    <span className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-semibold text-white" style={{ background: `color-mix(in srgb, ${tone} 55%, rgba(255,255,255,0.12))` }}>
      <span className="h-1.5 w-1.5 rounded-full bg-white" /> {status}
    </span>
  );
}

// A small hook a claim-scoped page uses to jump to another module for the same
// claim (keeps the active claim, changes the route).
export function useOpenClaim() {
  const navigate = useNavigate();
  const { setActiveClaim } = useClaimsDesk();
  return (claimId: string, route: string) => { setActiveClaim(claimId); navigate(route); };
}

// A mobile-only horizontal claim selector - the desktop queue pane isn't shown
// on a phone (Standard B6: real reflow, not a squeezed desktop grid), so a
// claim-scoped page carries this strip to switch the active claim by touch.
function MobileClaimStrip() {
  const { activeClaimId, setActiveClaim } = useClaimsDesk();
  return (
    <div className="lg:hidden">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-400">Claims queue</p>
      <div className="-mx-4 flex snap-x gap-2.5 overflow-x-auto px-4 pb-1">
        {CLAIMS.map((c) => {
          const active = c.id === activeClaimId;
          return (
            <button
              key={c.id}
              type="button"
              onClick={() => setActiveClaim(c.id)}
              className="w-52 shrink-0 snap-start"
              aria-current={active ? 'true' : undefined}
            >
              <ClaimCard claim={c} active={active} compact />
            </button>
          );
        })}
      </div>
    </div>
  );
}

// The wrapper every claim-scoped reading room uses: the mobile claim strip, the
// active-claim header, then the page's own content - so all four claim-scoped
// pages share one consistent, on-brand frame.
export function ClaimWorkbench({
  kicker, children,
}: {
  kicker?: string; children: ReactNode;
}) {
  const { activeClaim } = useClaimsDesk();
  return (
    <div className="mx-auto max-w-5xl space-y-5 px-4 py-6 sm:px-6">
      <MobileClaimStrip />
      <ClaimHeader claim={activeClaim} kicker={kicker} />
      {children}
    </div>
  );
}
