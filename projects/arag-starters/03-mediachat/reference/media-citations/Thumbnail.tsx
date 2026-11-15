// ─────────────────────────────────────────────────────────────────────────────
// Thumbnail — the video's real title-card frame. Nuclia's own video processing
// extracts a real JPEG frame for every resource at ingest time (no per-video
// setup, works identically for the seeded sessions and any bulk-uploaded real
// conference footage), proxied server-side at /api/sessions/:id/thumbnail — see
// server/sessions.mjs. That route itself never errors (it 200s a branded SVG
// placeholder — FALLBACK_THUMBNAIL_SVG — whenever a resource has no extracted
// frame yet), but a client-side load can still fail for reasons the server
// can't see (a genuine network hiccup, a card rendered with no id at all).
//
// PRIOR BUG (found live, 19 Aug 2026): the old fallback here was a generic
// translucent-black block, painted only AFTER an <img> failed — so any card
// showed a blank/washed-out grey box for the gap between "nothing painted
// yet" and "the real image (or the fallback) arrived", and a genuinely
// failed load looked like a dead card, not a designed one. Fixed by mirroring
// server/sessions.mjs's own FALLBACK_THUMBNAIL_SVG pixel-for-pixel as the
// BASE layer under every thumbnail, always — the real <img> paints on top of
// it once loaded; on any failure the <img> just never covers it. One brand
// placeholder, used everywhere, never a bare grey box.
//
// Lives in components/ (not demo/) because it's used everywhere a resource is
// displayed, including components/Citations.tsx's source cards — not just the
// demo/ video-product pages.
// ─────────────────────────────────────────────────────────────────────────────
import { useState } from 'react';
import { Play } from 'lucide-react';
import { thumbnailUrl } from '../lib/content';

/** Pixel-for-pixel the same design as server/sessions.mjs's
 * FALLBACK_THUMBNAIL_SVG — one visual language for "no real frame available
 * yet", whether the server itself had to fall back or the client's own
 * image load failed for an unrelated reason. */
function BrandPlaceholder() {
  return (
    <svg viewBox="0 0 320 180" className="absolute inset-0 h-full w-full" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <defs>
        <linearGradient id="pugtube-fallback-bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#00216B" />
          <stop offset="100%" stopColor="#0B2E86" />
        </linearGradient>
      </defs>
      <rect width="320" height="180" fill="url(#pugtube-fallback-bg)" />
      <circle cx="160" cy="82" r="30" fill="#FFFFFF" fillOpacity="0.12" />
      <path d="M150 66 L182 82 L150 98 Z" fill="#CDFFCA" />
      <text x="160" y="140" textAnchor="middle" fontFamily="Helvetica, Arial, sans-serif" fontSize="13" fontWeight="700" fill="#FFFFFF" fillOpacity="0.85" letterSpacing="1">
        PUG TUBE
      </text>
    </svg>
  );
}

export function Thumbnail({ id, size = 'md', badge }: {
  id: string | null | undefined;
  size?: 'sm' | 'md';
  /** A track/category label, corner-badged in a bracketed tag over the frame —
   * progress.com's own media-card pattern ("[VIDEO]", "[WEBINAR]" over its
   * "Latest from Progress" thumbnails, getComputedStyle'd 2026-08-06), not a
   * plain caption line below the image. */
  badge?: string | null;
}) {
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);
  const src = thumbnailUrl(id);
  const iconSize = size === 'sm' ? 16 : 28;

  const badgeEl = badge && (
    <span
      className="absolute left-1.5 top-1.5 rounded px-1.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wide text-white"
      style={{ background: 'rgba(0,0,0,0.65)', border: '1px solid rgba(255,255,255,0.25)' }}
    >
      [{badge}]
    </span>
  );

  return (
    <div className="relative h-full w-full overflow-hidden rounded-lg">
      {/* Always painted, always first — the real frame (or the hover
          scrim/play icon below) layers on top of it, so there is never a
          blank/grey moment. */}
      <BrandPlaceholder />
      {src && !failed && (
        <img
          src={src}
          alt=""
          className="absolute inset-0 h-full w-full object-cover transition-opacity duration-200"
          style={{ opacity: loaded ? 1 : 0 }}
          onLoad={() => setLoaded(true)}
          onError={() => setFailed(true)}
        />
      )}
      {loaded && !failed && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/10 opacity-0 transition-opacity group-hover:opacity-100">
          <Play size={iconSize} className="text-white drop-shadow" />
        </div>
      )}
      {badgeEl}
    </div>
  );
}
