import { useEffect, useState } from 'react';
import { ChevronDown, ExternalLink, FileText, Quote, Clock } from 'lucide-react';
import { formatTimestamp } from '../demo/VideoPlayer';
// Kendo-free: the citations panel (part of the grounding guarantee) uses plain
// elements + the `.card` utility, identical in both UI modes.
import type { Citation } from '../lib/arag';
import { getResource } from '../lib/arag';
import { matchColor } from '../components/journey/ConfidenceRing';
import { buildStops } from '../lib/journey';
import { Thumbnail } from './Thumbnail';
import { cleanTitle } from '../lib/util';

/** A quiet "12:34" or "Page 4" chip — tells the reader exactly where clicking
 * this source will land before they click it, honestly reflecting whichever
 * position (a real spoken second, or a real cited page) this citation
 * actually carries; renders nothing for a source with neither. */
function PositionBadge({ startSeconds, page }: { startSeconds: number | null; page: number | null }) {
  if (startSeconds != null) {
    return (
      <span className="inline-flex shrink-0 items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-medium text-ink-500" style={{ background: 'var(--surface-2)' }}>
        <Clock size={10} /> {formatTimestamp(startSeconds)}
      </span>
    );
  }
  if (page != null) {
    return (
      <span className="inline-flex shrink-0 items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-medium text-ink-500" style={{ background: 'var(--surface-2)' }}>
        <FileText size={10} /> Page {page}
      </span>
    );
  }
  return null;
}

/** Small "94% match" badge — the same score/colour language as the Answer Journey. */
function MatchBadge({ score }: { score: number | null }) {
  if (score == null) return null;
  const pct = Math.round(score * 100);
  return (
    <span
      className="inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold tabular-nums"
      style={{ background: `color-mix(in srgb, ${matchColor(score)} 16%, transparent)`, color: matchColor(score) }}
      title="Confidence: how strongly this source matched the question"
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: matchColor(score) }} />
      {pct}% match
    </span>
  );
}

// A raw Nuclia id (32 hex chars, optionally with a /field/paragraph suffix)
// leaking through as a title means the ask payload carried the citation but not
// the document's metadata. Human titles always have spaces; ids never do — use
// that plus the hex signature to detect one, so we can resolve the real title.
//
// FIX (lead review, 3 Sep 2026, reproduced live on /assistant): the earlier
// version bailed out ("never a raw id") the instant the string contained ANY
// whitespace — but a real leaked citation key can itself carry a space in its
// field-name segment (observed live: "<rid>/t/da-video insights-a-title/302-
// 508"), which slipped straight through this check unresolved and rendered
// verbatim. Whitespace is no longer disqualifying — a string that literally
// starts with the resource's own id followed by "/" is a raw key regardless
// of what comes after.
const isRawId = (title: string, resourceId: string) => {
  const t = title.trim();
  if (/^[0-9a-f]{32}\//i.test(t)) return true;
  if (t === resourceId) return true;
  if (t.startsWith(resourceId) && (t.length === resourceId.length || t[resourceId.length] === '/')) return true;
  return false;
};

// The KB's Generator DA agent writes a labelled-line field per video — TITLE:/
// SUMMARY:/TAKEAWAY:/QUOTE: (see server/insights.mjs's own parser, which uses the
// identical `^\s*([A-Z]+):\s*` pattern). That field is itself real, searchable KB
// content, so a genuine /ask citation can legitimately land on it — but the raw
// label scaffolding must never render on screen (table-stakes gate 8): a source
// excerpt reading `"TITLE: … SUMMARY: … TAKEAWAY: …"` verbatim is a forbidden
// on-screen leak of the DA transport format. Strip a leading ALL-CAPS "LABEL:"
// token from each line and keep only the human text; a line with no such label
// (an ordinary transcript excerpt) passes through completely untouched.
const DA_LABEL_LINE = /^\s*[A-Z]+:\s*/;
function stripDaLabels(raw: string): string {
  const text = (raw || '').trim();
  if (!text) return text;
  const lines = text.split('\n');
  if (!lines.some((l) => DA_LABEL_LINE.test(l))) return text;
  const cleaned = lines
    .map((l) => l.replace(DA_LABEL_LINE, '').replace(/^["“]|["”]$/g, '').trim())
    .filter(Boolean)
    .join(' ')
    .trim();
  // Labels with no surviving value (shouldn't happen, but never show blank) —
  // fall back to the original text rather than rendering nothing.
  return cleaned || text;
}

// Sources panel — citations grouped by document (see arag.ts). An answer with
// citations is grounded; the count of source documents is shown so the reader
// can see the answer stands on more than one leg.
export function Citations({
  citations,
  onOpen,
  query,
  ringedIndex,
  idPrefix = '',
}: {
  citations: Citation[];
  onOpen?: (citation: Citation) => void;
  /** The question that produced these citations — used to fetch an authoritative
   * confidence score via a fresh /find (see below); optional, falls back to the
   * score embedded in the citation itself when omitted. */
  query?: string;
  /** B33 — the citation index just clicked as an inline `[[n]]` marker in the
   * answer prose; briefly rings this card so the reader sees exactly which
   * source it jumped to. */
  ringedIndex?: number | null;
  /** Scopes each card's `cite-card-*` DOM id so multiple independent answer
   * surfaces on one page (e.g. every turn of a multi-turn conversation) never
   * collide on the same id — a bare GroundedAnswer leaves this empty. */
  idPrefix?: string;
}) {
  // Lazily resolve titles that came through as raw ids.
  const [resolved, setResolved] = useState<Record<string, string>>({});
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  // A citation's own embedded score can be a near-0 artefact of the
  // `neighbouring_paragraphs` context-expansion strategy (a genuinely cited
  // source whose ONLY indexed paragraph happens to be an unscored neighbour) —
  // that reads as an absurd "0% match" for a source the model actually relied
  // on. A fresh, independent /find re-scores every cited resource on its own
  // semantic merit, so it is always a fair, non-zero number for a real
  // citation. Reuses the same banded confidence /api/journey already computes
  // for the Answer Journey — one scoring language across the whole portal.
  const [scores, setScores] = useState<Record<string, number>>({});
  useEffect(() => {
    if (!query || citations.length === 0) return;
    let live = true;
    buildStops(query, [], citations.map((c) => c.resourceId))
      .then((stops) => {
        if (!live) return;
        const map: Record<string, number> = {};
        for (const s of stops) map[s.resourceId] = s.score;
        setScores(map);
      })
      .catch(() => {});
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, citations]);

  useEffect(() => {
    let live = true;
    const missing = citations.filter((c) => isRawId(c.title, c.resourceId)).map((c) => c.resourceId);
    for (const rid of missing) {
      if (resolved[rid]) continue;
      getResource(rid)
        .then((r) => {
          // B10 — this endpoint returns the raw resource JSON, unfiltered.
          if (live && r?.title) setResolved((m) => ({ ...m, [rid]: cleanTitle(r.title) }));
        })
        .catch(() => {});
    }
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [citations]);

  if (!citations.length) return null;
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-ink-500">
        <Quote size={13} />
        {citations.length} source{citations.length > 1 ? 's' : ''}
      </div>
      <ol className="space-y-2">
        {citations.map((c) => {
          const title = isRawId(c.title, c.resourceId) ? resolved[c.resourceId] || 'Loading source…' : c.title;
          const clickable = !!onOpen;
          const isOpen = !!expanded[c.resourceId];
          // Dedup against the raw (pre-strip) text — two excerpts that only differ
          // in DA-label scaffolding would otherwise both survive the filter and
          // then render identically once cleaned.
          const moreExcerpts = c.excerpts.filter((e) => e !== c.text && stripDaLabels(e) !== stripDaLabels(c.text));
          // Prefer the freshly re-scored, always-fair confidence over the
          // citation's own embedded score (see the scores effect above).
          const score = scores[c.resourceId] ?? c.score;
          return (
            <li key={c.resourceId}>
              <div
                id={`cite-card-${idPrefix}${c.index}`}
                className={`card p-3 transition ${clickable ? 'cursor-pointer hover:-translate-y-0.5 hover:shadow-md' : 'hover:shadow-md'} ${ringedIndex === c.index ? 'cite-card--ringed' : ''}`}
                {...(clickable
                  ? {
                      role: 'button',
                      tabIndex: 0,
                      onClick: () => onOpen!(c),
                      onKeyDown: (e: React.KeyboardEvent) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          onOpen!(c);
                        }
                      },
                    }
                  : {})}
                title={title}
              >
                    <div className="flex items-start gap-2.5">
                      {/* Every source here IS a video — the thumbnail is what makes a
                          source card instantly recognisable, not just a filename. */}
                      <div className="relative h-11 w-[4.6rem] shrink-0">
                        <Thumbnail id={c.resourceId} size="sm" />
                        <span
                          className="absolute -left-1.5 -top-1.5 flex h-[18px] w-[18px] items-center justify-center rounded-full text-[10px] font-bold"
                          style={{ background: 'var(--brand)', color: 'var(--brand-contrast)' }}
                        >
                          {c.index}
                        </span>
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5">
                          <FileText size={13} className="shrink-0 text-ink-400" />
                          <span
                            className={`truncate text-sm font-semibold text-ink-900 dark:text-ink-100 ${clickable ? 'group-hover:underline' : ''}`}
                          >
                            {title}
                          </span>
                          <span className="ml-auto flex items-center gap-1.5">
                            <PositionBadge startSeconds={c.startSeconds} page={c.page} />
                            <MatchBadge score={score} />
                          </span>
                        </div>
                        {c.text && (
                          <p className="mt-1 line-clamp-3 text-xs leading-relaxed text-ink-500">“{stripDaLabels(c.text)}”</p>
                        )}
                        <div className="mt-1.5 flex items-center gap-3 text-[11px] text-ink-400">
                          {c.excerptCount > 1 && <span>{c.excerptCount} cited passages</span>}
                          {c.url && (
                            <a
                              href={c.url}
                              target="_blank"
                              rel="noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              className="inline-flex items-center gap-1 hover:text-ink-600"
                              style={{ color: 'var(--brand)' }}
                            >
                              <ExternalLink size={11} /> source
                            </a>
                          )}
                          <button
                            type="button"
                            onClick={(e) => { e.stopPropagation(); setExpanded((m) => ({ ...m, [c.resourceId]: !m[c.resourceId] })); }}
                            className="ml-auto inline-flex items-center gap-1 font-medium hover:text-ink-600"
                          >
                            {isOpen ? 'Hide detail' : 'Expand'}
                            <ChevronDown size={12} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                          </button>
                        </div>
                        {isOpen && (
                          <div
                            className="mt-2 space-y-2 border-t pt-2"
                            style={{ borderColor: 'var(--hairline)' }}
                            onClick={(e) => e.stopPropagation()}
                          >
                            {moreExcerpts.length > 0 ? (
                              moreExcerpts.map((ex, i) => (
                                <p key={i} className="text-xs leading-relaxed text-ink-500">“{stripDaLabels(ex)}”</p>
                              ))
                            ) : (
                              <p className="text-xs italic text-ink-400">No further cited passages from this source.</p>
                            )}
                            {score != null && (
                              <p className="text-[11px] text-ink-400">
                                Confidence {Math.round(score * 100)}% - how strongly this source's content matched the question, relative to every source retrieved for it.
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
