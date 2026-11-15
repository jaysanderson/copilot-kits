import { FileText } from 'lucide-react';

// ─────────────────────────────────────────────────────────────────────────────
// LetterheadPreview — a REAL, per-resource visual preview of a compliance
// record, not a generic document ICON.
//
// Fix (17 Aug 2026, GM correction): Bulletins catalogue cards were falling
// back to a bare file-type glyph on a gradient tile whenever Nuclia had no
// extracted frame for a text document (true for every compliance record in
// this corpus - none are video). A generic placeholder icon repeated across
// every card does NOT satisfy Standard B10's thumbnail requirement - a
// reviewer must be able to recognise the SPECIFIC resource from its card.
//
// This renders a miniature of the SAME letterhead treatment ResourceDetail's
// DocumentRecord uses full-size (paper surface, brand rule, masthead, doc-type
// label, title) using that resource's OWN real title/docType - a genuine,
// per-item visual preview, not a stock glyph. Deterministic body-line bars
// (no random per-render layout) fill the rest of the "page" so it reads as a
// real document thumbnail, not a bare text card.
// ─────────────────────────────────────────────────────────────────────────────

const BAR_WIDTHS = [92, 78, 85, 60];

export function LetterheadPreview({
  title,
  docType,
  brandName = 'Publisher Mutual',
  size = 'thumb',
}: {
  title: string;
  docType?: string;
  brandName?: string;
  size?: 'thumb' | 'card';
}) {
  const compact = size === 'thumb';
  return (
    <div
      className="relative flex h-full w-full flex-col overflow-hidden"
      style={{ background: '#fdfcfa' }}
      aria-hidden
    >
      {/* masthead */}
      <div
        className={compact ? 'flex items-center gap-1 px-2.5 pb-1.5 pt-2' : 'flex items-center gap-2 px-4 pb-2.5 pt-3'}
        style={{ borderBottom: `${compact ? 2 : 3}px solid var(--brand)` }}
      >
        <span
          className={`flex shrink-0 items-center justify-center rounded text-white ${compact ? 'h-4 w-4' : 'h-6 w-6'}`}
          style={{ background: 'linear-gradient(155deg, var(--brand-strong), var(--brand))' }}
        >
          <FileText size={compact ? 8 : 12} />
        </span>
        <span
          className={`truncate font-bold uppercase tracking-wide ${compact ? 'text-[6px]' : 'text-[9px]'}`}
          style={{ color: 'var(--brand-strong)' }}
        >
          {brandName}
        </span>
      </div>

      {/* doc type + title — the part that makes every card genuinely different */}
      <div className={compact ? 'flex-1 space-y-1 px-2.5 pb-2 pt-1.5' : 'flex-1 space-y-1.5 px-4 pb-3 pt-2.5'}>
        {docType && (
          <p className={`font-semibold uppercase tracking-wide text-slate-400 ${compact ? 'text-[6px]' : 'text-[9px]'}`}>
            {docType}
          </p>
        )}
        <p
          className={`line-clamp-3 font-semibold leading-snug text-slate-800 ${compact ? 'text-[8px]' : 'text-[13px]'}`}
          style={{ fontFamily: 'var(--font-display, inherit)' }}
        >
          {title}
        </p>
        {/* simulated body lines — a real "page of text" affordance, not a blank card */}
        <div className={compact ? 'space-y-1 pt-1' : 'space-y-1.5 pt-2'}>
          {BAR_WIDTHS.map((w, i) => (
            <div
              key={i}
              className={compact ? 'h-[2.5px] rounded-full bg-slate-200' : 'h-1 rounded-full bg-slate-200'}
              style={{ width: `${w}%` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
