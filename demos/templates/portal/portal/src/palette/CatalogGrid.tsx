import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Sparkles, X } from 'lucide-react';
import type { CatalogCard, CatalogResult } from '../lib/arag';
import { catalog } from '../lib/arag';
import { Pill } from '../components/Pill';
import { ClickableCard } from '../components/ClickableCard';
import { EmptyState } from '../components/States';
import { LetterheadPreview } from '../components/LetterheadPreview';
import { cleanTitle } from '../lib/util';
import { useReveal } from '../lib/motion';

// ─────────────────────────────────────────────────────────────────────────────
// Standard B10 (arag-demo-app skill, 17 Aug 2026) — the reusable catalogue/
// listing module. Every listing surface should be built from THIS component,
// not a hand-rolled grid, so the contract holds everywhere:
//   (a) a THUMBNAIL — the platform-native extracted frame when Nuclia produced
//       one, else a designed on-brand gradient tile (never a bare icon/blank);
//   (b) a title + description that render whatever a DA Generator agent wrote
//       (server/index.mjs's toCard(), see the GENERATED_KEYS contract) with a
//       quiet "AI-enriched" mark, falling back to Nuclia's native fields when
//       no Generator is registered yet — never hardcoded copy either way;
//   (c) STRUCTURED chips — the KV-schema fields the pipeline actually
//       extracted from unstructured source, scannable at a glance;
//   (d) working facet filters, built on the fixed `catalog()` helper (Standard
///      B19 — one call, `filter_expression`, never the legacy array).
//
// Kendo-free by design (plain elements + Tailwind), matching the rest of the
// palette (Pill, ClickableCard, States) — this module works identically in
// `kendo` and `opensource` UI_MODE and never needs to know which one it's in.
// ─────────────────────────────────────────────────────────────────────────────

// Metadata keys the server already promotes to first-class card fields
// (docType, mediaType, durationMinutes, authors) — never re-shown as a
// generic chip, that would just be noisy duplication.
const PROMOTED_LABELSETS = new Set(['doc_type', 'type', 'media_type']);

// Facets that must never surface as a filter row. `media_type` is single-valued
// ("text") for an all-document corpus - it offers zero filtering value AND its
// Nuclia facet count is a field/paragraph count, not a resource count, so it
// reads as a contradiction next to the resource total (e.g. "media type · text ·
// 181" beside "21 items"). Steve Jobs review, 17 Aug 2026: remove the tell.
const HIDDEN_FACETS = new Set(['media_type', 'classification']);

function formatChipValue(v: string | number | boolean): string {
  if (typeof v === 'boolean') return v ? 'Yes' : 'No';
  if (typeof v === 'number') return Number.isInteger(v) ? String(v) : v.toFixed(1);
  return String(v);
}

function formatChipKey(k: string): string {
  return k.replace(/[_-]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

// Prettify a raw slug LABEL value for display (facet pills, doc-type chips) so a
// buyer never sees an internal slug like "tmd-summary" or "compliance-bulletin"
// (Steve Jobs review, 17 Aug 2026). Domain acronyms stay upper-case. The raw
// value is still used for filtering — only the displayed string changes.
const LABEL_ACRONYMS = new Set(['tmd', 'apl', 'afsl', 'smsf', 'soa', 'roa', 'fsg']);
function formatLabelValue(v: string): string {
  return String(v)
    .split(/[-_\s]+/)
    .filter(Boolean)
    .map((w) => (LABEL_ACRONYMS.has(w.toLowerCase()) ? w.toUpperCase() : w.charAt(0).toUpperCase() + w.slice(1)))
    .join(' ');
}

export interface CatalogGridProps {
  /** Placeholder for the free-text query box. */
  searchPlaceholder?: string;
  /** How many structured chips to surface per card before truncating. */
  maxChips?: number;
  /** Page size per fetch. */
  pageSize?: number;
  /** Grid density at the widest breakpoint. */
  cols?: 3 | 4 | 5;
  /** Override the default `/r/:id` navigation on card click. */
  onOpen?: (card: CatalogCard) => void;
  /** Shown above the grid when there are zero results for the current query/filters. */
  emptyLabel?: string;
}

/**
 * A premium, reusable catalogue/listing grid over `catalog()` — thumbnails,
 * DA-generated copy, structured chips, and working multi-select facet filters
 * in one component. Drop into any surface that lists KB-backed items.
 */
export function CatalogGrid({
  searchPlaceholder = 'Search by meaning…',
  maxChips = 4,
  pageSize = 60,
  cols = 4,
  onOpen,
  emptyLabel = 'Nothing matches yet - try a different search or clear a filter.',
}: CatalogGridProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [activeFilters, setActiveFilters] = useState<string[]>([]);
  const [result, setResult] = useState<CatalogResult | null>(null);
  const [loading, setLoading] = useState(true);
  const requestId = useRef(0);

  useEffect(() => {
    const id = ++requestId.current;
    setLoading(true);
    catalog({ query, filters: activeFilters.length ? activeFilters : undefined, pageSize })
      .then((r) => { if (requestId.current === id) setResult(r); })
      .catch(() => { if (requestId.current === id) setResult({ items: [], facets: {}, total: 0, page: 0, pageSize }); })
      .finally(() => { if (requestId.current === id) setLoading(false); });
  }, [query, activeFilters, pageSize]);

  const facetGroups = useMemo(
    () => Object.entries(result?.facets || {}).filter(([labelset]) => !HIDDEN_FACETS.has(labelset)),
    [result]
  );

  const toggleFilter = (labelset: string, label: string) => {
    const path = `/classification.labels/${labelset}/${label}`;
    setActiveFilters((prev) => (prev.includes(path) ? prev.filter((f) => f !== path) : [...prev, path]));
  };
  const isActive = (labelset: string, label: string) => activeFilters.includes(`/classification.labels/${labelset}/${label}`);

  const cards = result?.items || [];
  const total = result?.total ?? cards.length;

  return (
    <div className="space-y-5">
      {/* search */}
      <div className="relative">
        <Search size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-400" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={searchPlaceholder}
          className="field w-full pl-9"
        />
      </div>

      {/* facets */}
      {facetGroups.length > 0 && (
        <div className="flex flex-wrap items-start gap-x-5 gap-y-2">
          {facetGroups.map(([labelset, entries]) => (
            <div key={labelset} className="flex flex-wrap items-center gap-1.5">
              <span className="mr-0.5 text-[11px] font-semibold uppercase tracking-wide text-ink-400">
                {formatChipKey(labelset)}
              </span>
              {entries.slice(0, 8).map((e) => (
                <Pill
                  key={e.label}
                  text={`${formatLabelValue(e.label)} · ${e.count}`}
                  selected={isActive(labelset, e.label)}
                  onClick={() => toggleFilter(labelset, e.label)}
                />
              ))}
            </div>
          ))}
          {activeFilters.length > 0 && (
            <button
              type="button"
              onClick={() => setActiveFilters([])}
              className="inline-flex items-center gap-1 text-xs font-medium text-ink-400 hover:text-ink-700 dark:hover:text-ink-200"
            >
              <X size={12} /> Clear filters
            </button>
          )}
        </div>
      )}

      <div className="text-xs uppercase tracking-wide text-ink-400">
        {loading ? 'Loading…' : `${total} item${total === 1 ? '' : 's'}`}
      </div>

      {/* grid */}
      {loading && cards.length === 0 ? (
        <div className={`grid grid-cols-2 gap-4 sm:grid-cols-3 ${cols === 5 ? 'lg:grid-cols-5' : cols === 4 ? 'lg:grid-cols-4' : 'lg:grid-cols-3'}`}>
          {Array.from({ length: 8 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      ) : cards.length === 0 ? (
        <EmptyState title="No results" hint={emptyLabel} />
      ) : (
        <div className={`grid grid-cols-2 gap-4 sm:grid-cols-3 ${cols === 5 ? 'lg:grid-cols-5' : cols === 4 ? 'lg:grid-cols-4' : 'lg:grid-cols-3'}`}>
          {cards.map((c, i) => (
            <CatalogCardTile
              key={c.id}
              card={c}
              index={i}
              maxChips={maxChips}
              onOpen={() => (onOpen ? onOpen(c) : navigate(`/r/${c.id}`))}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function CardSkeleton() {
  return (
    <div className="card overflow-hidden">
      <div className="h-28 animate-pulse" style={{ background: 'var(--surface-2, var(--brand-softer))' }} />
      <div className="space-y-2 p-3">
        <div className="h-3 w-3/4 animate-pulse rounded" style={{ background: 'var(--hairline-strong)' }} />
        <div className="h-3 w-1/2 animate-pulse rounded" style={{ background: 'var(--hairline-strong)' }} />
      </div>
    </div>
  );
}

function CatalogCardTile({ card, index, maxChips, onOpen }: { card: CatalogCard; index: number; maxChips: number; onOpen: () => void }) {
  const { ref, visible } = useReveal<HTMLDivElement>();
  const chips = Object.entries(card.structuredFields || {})
    .filter(([k]) => !PROMOTED_LABELSETS.has(k))
    .slice(0, maxChips);

  return (
    <div
      ref={ref}
      className={`reveal${visible ? ' is-visible' : ''}`}
      style={{ transitionDelay: `${Math.min(index, 8) * 35}ms` }}
    >
      <ClickableCard ariaLabel={`Open ${card.title}`} onClick={onOpen} className="card-hover h-full">
        <div className="card overflow-hidden">
          {/* thumbnail: the platform-native extracted frame when Nuclia produced one
              (video), else a REAL per-resource visual preview — a miniature of this
              item's own letterhead record (title, doc type, brand) — never a bare
              icon (Standard B10, GM correction 17 Aug 2026: a generic placeholder
              glyph repeated on every card is a FAIL). */}
          <div className="relative h-28 overflow-hidden">
            {card.thumbnail ? (
              <img src={card.thumbnail} alt="" className="h-full w-full object-cover" loading="lazy" />
            ) : (
              <LetterheadPreview title={cleanTitle(card.title)} docType={card.docType} size="thumb" />
            )}
            {card.mediaType === 'video' && card.durationMinutes ? (
              <span className="absolute bottom-1.5 right-1.5 rounded bg-black/70 px-1.5 py-0.5 text-[10px] font-semibold text-white">
                {card.durationMinutes}m
              </span>
            ) : null}
            {card.generated && (
              <span
                title="Title and summary generated by a DA agent from this item's own content"
                className="absolute left-1.5 top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-black/55 text-white backdrop-blur-sm"
              >
                <Sparkles size={11} />
              </span>
            )}
          </div>

          <div className="space-y-1.5 p-3">
            <div className="flex flex-wrap items-center gap-1">
              <span
                className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
                style={{ background: 'var(--brand-soft)', color: 'var(--brand)' }}
              >
                {formatLabelValue(card.docType)}
              </span>
            </div>
            <div className="line-clamp-2 text-sm font-semibold leading-snug text-ink-900 dark:text-ink-50">
              {cleanTitle(card.title)}
            </div>
            {card.summary && <p className="line-clamp-2 text-xs leading-relaxed text-ink-500">{card.summary}</p>}

            {chips.length > 0 && (
              <div className="flex flex-wrap gap-1 pt-0.5">
                {chips.map(([k, v]) => (
                  <span
                    key={k}
                    className="rounded-md px-1.5 py-0.5 text-[10px] font-medium text-ink-600 dark:text-ink-300"
                    style={{ background: 'var(--surface-2, var(--hairline))' }}
                    title={formatChipKey(k)}
                  >
                    {formatChipValue(v)}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </ClickableCard>
    </div>
  );
}
