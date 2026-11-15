// ─────────────────────────────────────────────────────────────────────────────
// Standard B14 (arag-demo-app skill, 17 Aug 2026) — a person is ALWAYS shown as
// name + role/persona, never a bare name. Use this everywhere a demo renders a
// signed-in user chip, an author byline, an assignee, a caller, a reviewer, a
// comment, or a record owner — "Dana Whitfield (Fleet Operations Manager)",
// never just "Dana Whitfield". By-construction guarantee, same spirit as
// GroundedAnswer/CitedMetric: the component signature itself requires a role,
// so it's structurally hard to regress to a bare name.
// ─────────────────────────────────────────────────────────────────────────────

export interface Person {
  name: string;
  role: string;
}

/** "Dana Whitfield (Fleet Operations Manager)" — the one canonical text form. */
export function formatPerson({ name, role }: Person): string {
  return role ? `${name} (${role})` : name;
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return '?';
  return (parts[0][0] + (parts[parts.length - 1]?.[0] || '')).toUpperCase();
}

/** Inline "name (role)" text — the lightest-weight option, drops into a sentence or a table cell. */
export function PersonLine({ name, role, className = '' }: Person & { className?: string }) {
  return (
    <span className={className}>
      <span className="font-medium text-ink-900 dark:text-ink-100">{name}</span>{' '}
      <span className="text-ink-500">({role})</span>
    </span>
  );
}

/** An avatar-style badge — initials + name stacked over role. For a signed-in chip, an assignee slot, a caller card. */
export function PersonTag({
  name,
  role,
  size = 'md',
  className = '',
}: Person & { size?: 'sm' | 'md'; className?: string }) {
  const dims = size === 'sm' ? 'h-7 w-7 text-[10px]' : 'h-9 w-9 text-xs';
  return (
    <span className={`inline-flex min-w-0 items-center gap-2 ${className}`}>
      <span
        className={`flex shrink-0 items-center justify-center rounded-full font-semibold ${dims}`}
        style={{ background: 'var(--brand-soft)', color: 'var(--brand)' }}
        aria-hidden
      >
        {initials(name)}
      </span>
      <span className="min-w-0 leading-tight">
        <span className={`block truncate font-medium text-ink-900 dark:text-ink-100 ${size === 'sm' ? 'text-xs' : 'text-sm'}`}>
          {name}
        </span>
        <span className="block truncate text-[11px] text-ink-500">{role}</span>
      </span>
    </span>
  );
}
