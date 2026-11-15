// ─────────────────────────────────────────────────────────────────────────────
// moments.ts — turns a raw /find (SearchResult) payload into moment-level
// video hits: real transcript text at a real timestamp (position.start_seconds
// from Nuclia's own video transcription), never a synthesized/guessed one. A
// video's title-card / OCR paragraphs are dropped in favour of the spoken
// transcript, since those are what a viewer actually wants to jump to.
// ─────────────────────────────────────────────────────────────────────────────
import { cleanTitle } from '../lib/util';

export interface Moment {
  resourceId: string;
  slug: string | null;
  title: string;
  speaker: string | null;
  track: string | null;
  text: string;
  startSeconds: number | null;
  endSeconds: number | null;
  /** 1-indexed page/slide number, for a hit inside a PDF or PPTX-family
   * session — the document analogue of startSeconds, from the same
   * `position.page_number` Nuclia returns on every retrieved paragraph. */
  page: number | null;
  score: number;
}

// Nuclia's video processing also runs vision captioning on the static title
// card, which produces real paragraphs with a real timestamp too - but they
// describe the frame ("A blue background with white text on it...") rather
// than what the speaker actually said, and would otherwise out-rank real
// transcript by matching the query text almost verbatim (title cards repeat
// the session title). Filtered out so search surfaces what was spoken.
const CAPTION_MARKERS = ['background with', 'the text reads', 'gradient background', 'solid background', 'text overlay'];
function isLikelyCaption(text: string, title: string): boolean {
  const t = text.toLowerCase();
  if (CAPTION_MARKERS.some((m) => t.includes(m))) return true;
  const normText = text.replace(/\s+/g, ' ').trim().toLowerCase();
  const normTitle = title.replace(/\s+/g, ' ').trim().toLowerCase();
  // The title-card OCR re-renders the title/speaker/track as near-verbatim
  // lines - if the paragraph is mostly just the title text, it's the slide.
  return normTitle.length > 0 && (normText === normTitle || normText.includes(normTitle));
}

function classificationsOf(usermetadata: any) {
  const out: Record<string, string[]> = {};
  for (const c of usermetadata?.classifications || []) (out[c.labelset] ||= []).push(c.label);
  return out;
}

/** All moments across every matched resource, richest (has real timestamp) first. */
export function extractMoments(raw: any, excludeResourceId?: string): Moment[] {
  const resources = raw?.resources || {};
  const out: Moment[] = [];
  for (const [rid, r] of Object.entries<any>(resources)) {
    if (excludeResourceId && rid === excludeResourceId) continue;
    const cls = classificationsOf(r.usermetadata);
    const extra = r.extra?.metadata || {};
    const speaker = extra.speaker || cls.speaker?.[0] || null;
    const track = extra.track || cls.track?.[0] || null;
    // The Generator DA agent's polished title (server/insights.mjs), when this
    // resource has finished processing — same title shown on cards/listings.
    const niceTitle: string | null = r.insights?.title || null;
    for (const field of Object.values<any>(r.fields || {})) {
      for (const p of Object.values<any>(field.paragraphs || {})) {
        const text = String(p?.text || '').replace(/\s+/g, ' ').trim();
        if (!text || text.length < 20) continue;
        if (isLikelyCaption(text, r.title || '')) continue;
        const startArr = p?.position?.start_seconds;
        const endArr = p?.position?.end_seconds;
        const startSeconds = Array.isArray(startArr) && startArr.length ? Number(startArr[0]) : null;
        const endSeconds = Array.isArray(endArr) && endArr.length ? Number(endArr[0]) : null;
        const pageNum = p?.position?.page_number;
        // 1-indexed, same convention as server/sessions.mjs's /pages route.
        const page = pageNum != null ? Number(pageNum) + 1 : null;
        out.push({
          resourceId: rid,
          slug: r.slug || null,
          // B10 — never let a raw upload extension reach the screen, even
          // on the pre-insights fallback (niceTitle absent).
          title: cleanTitle(niceTitle || r.title || rid),
          speaker,
          track,
          text,
          startSeconds,
          endSeconds,
          page,
          score: Number(p?.score) || 0,
        });
      }
    }
  }
  // A locatable moment (a real timestamp OR a real page) beats plain metadata
  // text with neither; within that, by score.
  const hasPosition = (m: Moment) => m.startSeconds != null || m.page != null;
  out.sort((a, b) => (Number(hasPosition(b)) - Number(hasPosition(a))) || b.score - a.score);
  return out;
}

/** One best moment per video (for row/grid display), preserving rank order. */
export function bestMomentPerResource(moments: Moment[]): Moment[] {
  const seen = new Set<string>();
  const out: Moment[] = [];
  for (const m of moments) {
    if (seen.has(m.resourceId)) continue;
    seen.add(m.resourceId);
    out.push(m);
  }
  return out;
}
