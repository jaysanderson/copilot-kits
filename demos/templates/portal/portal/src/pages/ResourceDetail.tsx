import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft, Play, Pause, FileText, Film, Sparkles, SendHorizontal,
  Square, Clock, ExternalLink, ListVideo, Volume2,
} from 'lucide-react';
import { Button, Chip } from '@progress/kendo-react-buttons';
import { Card, CardBody } from '@progress/kendo-react-layout';
import { Input } from '@progress/kendo-react-inputs';
import {
  getResource, catalog, ask,
  type Citation, type CatalogCard,
} from '../lib/arag';
import type { DemoConfig } from '../lib/config';
import { renderMarkdown } from '../lib/markdown';
import { Citations } from '../components/Citations';
import { ClickableCard } from '../components/ClickableCard';
import { Spinner, ErrorBanner, TypingDots, UngroundedWarning } from '../components/States';

// ── shape a raw Nuclia resource into what the watch page renders ────────────────
// Kept deliberately generic: it derives doc type, media type, duration and chips
// from whatever labelsets / metadata the resource carries, so it works for any
// blueprint (space, legal, retail…) without hardcoding a corpus's field names.

interface Derived {
  title: string;
  summary: string;
  body: string;
  sourceUrl: string | null;
  docType: string;
  mediaType: string | null;
  durationMinutes: number | null;
  otherChips: string[];
  isMedia: boolean;
  labels: Record<string, string[]>;
  /** Real DA-Generator/KV-schema fields mirrored onto extra.metadata at ingest — same source server/index.mjs's toCard() reads for the Bulletins catalogue chips. Never fabricated here. */
  structuredFields: Record<string, string | number | boolean>;
}

function deriveResource(data: any): Derived {
  const extra = data?.extra?.metadata || {};
  const classifications: { labelset: string; label: string }[] = data?.usermetadata?.classifications || [];
  const labels: Record<string, string[]> = {};
  for (const { labelset, label } of classifications) (labels[labelset] ||= []).push(label);
  const firstLabel = (...names: string[]) => {
    for (const n of names) if (labels[n]?.length) return labels[n][0];
    return null;
  };

  const docType = firstLabel('doc_type', 'type') || extra.doc_type || 'Document';
  const mediaType = firstLabel('media_type') || extra.media_type || null;
  const durationMinutes = extra.duration_minutes ?? null;

  // Compliance-co fix (17 Aug 2026): a resource can carry MORE than one text
  // field — the real extracted content under `body`, plus a DA task's own
  // auxiliary output field (`da-<destination>-t-body`, CLAUDE.md's documented
  // field-key naming gotcha) storing a plain "TITLE: … SUMMARY: … HIGHLIGHTS:
  // …" digest meant to feed the catalogue card (extra.metadata.da_title etc),
  // never to be read verbatim. Concatenating every text field indiscriminately
  // prepended that raw digest before the real body on every record view. Only
  // read genuine source-content fields (never a `da-`-prefixed key).
  const bodies: string[] = [];
  for (const [key, field] of Object.entries<any>(data?.data?.texts || {})) {
    if (key.startsWith('da-')) continue;
    if (field?.value?.body) bodies.push(field.value.body);
  }
  const body = (bodies.join('\n\n') || data?.summary || '').trim();

  // Every classification label becomes a chip, minus the one already shown as the
  // primary doc-type chip. Deduped, capped, generic across corpora.
  // Fix (Steve Jobs review, 17 Aug 2026): the `media_type` labelset (value
  // "text" for every document in an all-text corpus) is an internal tell, not a
  // classification a buyer should ever read - it rendered as "Classification:
  // text" on the record. Skip that labelset (and the generic `classification`
  // labelset) when building the human-facing chips.
  const SKIP_CHIP_LABELSETS = new Set(['media_type', 'classification']);
  const seen = new Set<string>([docType.toLowerCase()]);
  const otherChips: string[] = [];
  for (const { labelset, label } of classifications) {
    if (SKIP_CHIP_LABELSETS.has(labelset)) continue;
    const key = label.toLowerCase();
    if (!label || seen.has(key)) continue;
    seen.add(key);
    otherChips.push(label);
  }

  const isMedia =
    (!!mediaType && /audio|video/i.test(mediaType)) ||
    /voice|video|podcast|call|webinar|audio|episode|recording|interview/i.test(docType);

  // Mirrors server/index.mjs's toCard() field filter exactly, so the record
  // view and the Bulletins catalogue chips are reading the same real fields
  // the same way — never a second, differently-shaped parse of the same data.
  const RESERVED = new Set(['da_title', 'da_summary', 'da_highlights', 'da_pull_quote', 'source_url', 'doc_type', 'media_type', 'duration_minutes', 'authors']);
  const structuredFields: Record<string, string | number | boolean> = {};
  for (const [key, value] of Object.entries(extra)) {
    if (RESERVED.has(key) || value === null || value === undefined || value === '') continue;
    structuredFields[key] = value as string | number | boolean;
  }

  return {
    title: data?.title || 'Untitled',
    summary: data?.summary || '',
    body,
    sourceUrl: data?.origin?.url || extra.source_url || null,
    docType,
    mediaType,
    durationMinutes,
    otherChips: otherChips.slice(0, 8),
    isMedia,
    labels,
    structuredFields,
  };
}

function fmtClock(totalMinutes: number | null, fraction = 1): string {
  if (totalMinutes == null) return '';
  const totalSec = Math.round(totalMinutes * 60 * fraction);
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

export function ResourceDetail({ config }: { config: DemoConfig }) {
  const { id = '' } = useParams();
  const navigate = useNavigate();

  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let live = true;
    setLoading(true);
    setError(null);
    setData(null);
    getResource(id)
      .then((d) => { if (live) setData(d); })
      .catch((e) => { if (live) setError(e.message); })
      .finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [id]);

  const r = useMemo(() => (data ? deriveResource(data) : null), [data]);

  useEffect(() => {
    if (r) document.title = `${r.title} · ${config?.theme?.brandName || 'Portal'}`;
  }, [r, config]);

  const goBack = () => (window.history.length > 1 ? navigate(-1) : navigate('/'));

  return (
    <div className="reveal is-visible">
      <Button fillMode="flat" onClick={goBack} startIcon={<ArrowLeft size={16} />} className="mb-5 -ml-2">
        Back
      </Button>

      {loading && <Spinner label="Loading resource…" />}
      {error && <ErrorBanner>{error}</ErrorBanner>}

      {r && (
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-[minmax(0,1fr)_20rem]">
          <MainColumn resource={r} id={id} navigate={navigate} brandName={config?.theme?.brandName || 'Publisher Mutual'} />
          <UpNextRail seedId={id} seedTitle={r.title} labels={r.labels} navigate={navigate} />
        </div>
      )}
    </div>
  );
}

// ── main column ("the player") ─────────────────────────────────────────────────

function MainColumn({
  resource,
  navigate,
  brandName,
}: {
  resource: Derived;
  id: string;
  navigate: (to: string) => void;
  brandName: string;
}) {
  return (
    <div className="min-w-0 space-y-6">
      {resource.isMedia ? (
        <>
          <MediaPlayer title={resource.title} durationMinutes={resource.durationMinutes} />
          <header className="space-y-3">
            <h1 className="font-display text-[1.9rem] font-semibold leading-tight tracking-tight text-ink-900 dark:text-ink-50">
              {resource.title}
            </h1>
            <MetaChips resource={resource} />
            {resource.sourceUrl && (
              <a
                href={resource.sourceUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-sm hover:underline"
                style={{ color: 'var(--brand)' }}
              >
                <ExternalLink size={14} /> Open original source
              </a>
            )}
          </header>
          <Transcript body={resource.body} />
        </>
      ) : (
        // The record IS the hero here — a genuine letterhead-styled document,
        // not a dark-chrome title bar over plain prose. Title/chips/source
        // link live inside the record itself (see DocumentRecord below).
        <DocumentRecord resource={resource} brandName={brandName} />
      )}

      <AskAboutThis title={resource.title} navigate={navigate} />
    </div>
  );
}

function MetaChips({ resource }: { resource: Derived }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Chip
        text={resource.docType}
        size="small"
        rounded="full"
        style={{ background: 'var(--brand-soft)', color: 'var(--brand-strong)', borderColor: 'transparent' }}
      />
      {resource.mediaType && !resource.otherChips.some((c) => c.toLowerCase() === resource.mediaType!.toLowerCase()) && (
        <Chip text={resource.mediaType} size="small" fillMode="outline" rounded="full" />
      )}
      {resource.durationMinutes != null && (
        <Chip text={`${resource.durationMinutes} min`} size="small" fillMode="outline" rounded="full" />
      )}
      {resource.otherChips.map((c) => (
        <Chip key={c} text={c} size="small" fillMode="outline" rounded="full" />
      ))}
    </div>
  );
}

// A cinematic, demo-only "player": it does not stream real media, but it reads
// like a real transport (play/pause, moving scrubber, elapsed / total time).
function MediaPlayer({ title, durationMinutes }: { title: string; durationMinutes: number | null }) {
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0); // 0..100

  useEffect(() => {
    if (!playing) return;
    const t = setInterval(() => {
      setProgress((p) => {
        const next = p + 0.5;
        return next >= 100 ? 100 : next;
      });
    }, 120);
    return () => clearInterval(t);
  }, [playing]);

  useEffect(() => {
    if (progress >= 100) setPlaying(false);
  }, [progress]);

  return (
    <div
      className="ring-hairline relative overflow-hidden rounded-2xl"
      style={{
        aspectRatio: '16 / 9',
        background:
          'radial-gradient(120% 120% at 15% 10%, color-mix(in srgb, var(--brand) 60%, black) 0%, transparent 60%),' +
          'radial-gradient(120% 120% at 90% 20%, color-mix(in srgb, var(--accent) 45%, black) 0%, transparent 55%),' +
          'linear-gradient(160deg, color-mix(in srgb, var(--brand) 30%, #05050a), #05050a)',
      }}
    >
      <div className="bg-grid absolute inset-0 opacity-40" />

      {/* Centre play / pause */}
      <button
        type="button"
        onClick={() => setPlaying((p) => !p)}
        aria-label={playing ? 'Pause' : 'Play'}
        className="group absolute inset-0 z-10 flex items-center justify-center outline-none"
      >
        <span
          className="flex h-20 w-20 items-center justify-center rounded-full text-white shadow-2xl transition-transform duration-200 group-hover:scale-105 group-active:scale-95"
          style={{
            background: 'color-mix(in srgb, var(--brand) 78%, black)',
            boxShadow: '0 0 0 1px rgba(255,255,255,0.18) inset, 0 24px 60px -20px color-mix(in srgb, var(--brand) 90%, transparent)',
          }}
        >
          {playing ? <Pause size={34} /> : <Play size={34} className="ml-1" />}
        </span>
      </button>

      {/* Transport bar */}
      <div className="absolute inset-x-0 bottom-0 z-10 space-y-2 bg-gradient-to-t from-black/70 to-transparent px-5 pb-4 pt-10">
        <div className="flex items-center gap-2 text-[13px] font-medium text-white/90">
          <Volume2 size={15} className="shrink-0" />
          <span className="truncate">{title}</span>
          {durationMinutes != null && (
            <span className="ml-auto shrink-0 tabular-nums text-white/70">
              {fmtClock(durationMinutes, progress / 100)} / {fmtClock(durationMinutes)}
            </span>
          )}
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/20">
          <div
            className="h-full rounded-full transition-[width] duration-150"
            style={{ width: `${progress}%`, background: 'linear-gradient(90deg, var(--brand-contrast), var(--accent))' }}
          />
        </div>
      </div>
    </div>
  );
}

function Transcript({ body }: { body: string }) {
  // The transcript body is markdown (bold speaker/timestamp labels, headings),
  // so render it through the same markdown pipeline as the reader rather than as
  // raw text — otherwise the `**`/`#` markers show literally.
  const html = useMemo(() => renderMarkdown(body), [body]);
  if (!body) return <EmptyBody />;
  return (
    <Card>
      <CardBody className="p-5 sm:p-6">
        <div className="mb-4 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--brand)' }}>
          <FileText size={14} /> Transcript
        </div>
        <article className="answer-prose max-w-prose" dangerouslySetInnerHTML={{ __html: html }} />
      </CardBody>
    </Card>
  );
}

const FIELD_LABELS: Record<string, string> = {
  published: 'Published',
  effective: 'Effective',
  status: 'Status',
  fund: 'Product',
  product: 'Product',
};

function formatFieldLabel(key: string): string {
  return FIELD_LABELS[key] || key.replace(/[_-]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

const DOC_TYPE_ACRONYMS = new Set(['tmd', 'apl', 'afsl', 'smsf']);
function formatDocType(docType: string): string {
  return docType
    .split(/[-_]+/)
    .map((w) => (DOC_TYPE_ACRONYMS.has(w.toLowerCase()) ? w.toUpperCase() : w.charAt(0).toUpperCase() + w.slice(1)))
    .join(' ');
}

// ── DocumentRecord — the "content is the hero" centrepiece ──────────────────────
// A real compliance record renders as a genuine letterhead document — Compliance-co's
// own masthead, a metadata table of the REAL fields the KB actually holds (never
// invented: docType/labels come from Nuclia classifications, `published` etc. are
// DA-Generator KV-schema extractions mirrored onto extra.metadata at ingest, same
// source the Bulletins catalogue chips read) — not a bare markdown scroll on a
// plain card. It reads as paper: a crisp light surface even in the app's dark
// mode, so the real content is the one bright, physical-feeling object on the
// page, deliberately set apart from the surrounding navy chrome.
function DocumentRecord({ resource, brandName }: { resource: Derived; brandName: string }) {
  const html = useMemo(() => renderMarkdown(resource.body || resource.summary), [resource.body, resource.summary]);
  const fieldEntries = Object.entries(resource.structuredFields).filter(([k]) => k !== 'title' && k !== 'summary');
  if (!resource.body && !resource.summary) return <EmptyBody />;

  return (
    <div
      className="overflow-hidden rounded-2xl"
      style={{
        background: '#fdfcfa',
        boxShadow: '0 1px 0 0 rgba(255,255,255,0.6) inset, 0 40px 80px -30px rgba(0,0,0,0.55), 0 0 0 1px rgba(15,42,61,0.08)',
      }}
    >
      {/* Masthead */}
      <div className="flex flex-wrap items-start justify-between gap-4 px-6 pb-5 pt-6 sm:px-8 sm:pt-8" style={{ borderBottom: '3px solid var(--brand)' }}>
        <div className="flex items-center gap-3">
          <span
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-white"
            style={{ background: 'linear-gradient(155deg, var(--brand-strong), var(--brand))' }}
            aria-hidden
          >
            <FileText size={20} />
          </span>
          <div className="leading-tight">
            <p className="font-display text-base font-bold tracking-tight" style={{ color: 'var(--brand-strong)' }}>
              {brandName.toUpperCase()}
            </p>
            <p className="text-[11px] uppercase tracking-wide text-slate-500">Claim file archive</p>
          </div>
        </div>
        <div className="text-right text-[11px] leading-relaxed text-slate-500">
          <p className="font-semibold uppercase tracking-wide" style={{ color: 'var(--accent-strong)' }}>Claim file</p>
          <p>General insurer · synthetic demonstration file</p>
        </div>
      </div>

      {/* Title + metadata table */}
      <div className="px-6 pb-2 pt-6 sm:px-8">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">{formatDocType(resource.docType)}</p>
        <h1 className="mt-1 font-display text-[1.65rem] font-semibold leading-tight tracking-tight text-slate-900">
          {resource.title}
        </h1>

        <dl className="mt-5 divide-y divide-slate-200 overflow-hidden rounded-lg border border-slate-200 text-sm">
          <FieldRow label="Document type" value={formatDocType(resource.docType)} />
          {fieldEntries.map(([k, v]) => (
            <FieldRow key={k} label={formatFieldLabel(k)} value={String(v)} />
          ))}
          {resource.otherChips.length > 0 && (
            <FieldRow label="Classification" value={resource.otherChips.join(', ')} />
          )}
        </dl>

        {resource.sourceUrl && (
          <a
            href={resource.sourceUrl}
            target="_blank"
            rel="noreferrer"
            className="mt-4 inline-flex items-center gap-1.5 text-sm hover:underline"
            style={{ color: 'var(--brand)' }}
          >
            <ExternalLink size={14} /> Open original source
          </a>
        )}
      </div>

      {/* Body — deliberately NOT theme-reactive: this is paper, not app chrome,
          so it stays readable-dark-on-light regardless of the app's own
          light/dark toggle. .answer-prose's spacing rules are reused; its
          dark-mode COLOUR rules are neutralised with the scoped style below
          (higher specificity than the shared `html.dark .answer-prose …`
          selectors, which would otherwise wash the text out on this page). */}
      <style>{`
        .doc-paper-prose, .doc-paper-prose p, .doc-paper-prose li { color: #334155; }
        .doc-paper-prose h1, .doc-paper-prose h2, .doc-paper-prose h3, .doc-paper-prose strong { color: #0f172a; }
        .doc-paper-prose a { color: var(--brand-strong); }
      `}</style>
      <article
        className="answer-prose doc-paper-prose max-w-none px-6 pb-8 pt-4 sm:px-8"
        dangerouslySetInnerHTML={{ __html: html }}
      />

      {/* Honesty footer — the record's own provenance line, same discipline as
          the app-wide disclaimer, restated where the "wow" content actually is. */}
      <div className="flex items-center gap-2 border-t border-slate-200 px-6 py-3 text-[11px] text-slate-400 sm:px-8">
        <Sparkles size={12} />
        Retrieved live from {brandName}'s claim file system via Progress Agentic RAG - never invented.
      </div>
    </div>
  );
}

function FieldRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-[9rem_1fr] gap-3 bg-white px-4 py-2.5 odd:bg-slate-50/60">
      <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">{label}</dt>
      <dd className="text-slate-700">{value}</dd>
    </div>
  );
}

function EmptyBody() {
  return (
    <Card>
      <CardBody className="p-6">
        <p className="text-sm text-ink-500">No text body available for this resource.</p>
      </CardBody>
    </Card>
  );
}

// ── "Ask about this" — grounded, streamed, cited, on the watch page ─────────────

function AskAboutThis({ title, navigate }: { title: string; navigate: (to: string) => void }) {
  const prefill = `About "${title}": summarise the key points`;
  const [query, setQuery] = useState(prefill);
  const [answer, setAnswer] = useState('');
  const [citations, setCitations] = useState<Citation[] | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<null | (() => void)>(null);

  // Reset the prefill when navigating between resources.
  useEffect(() => {
    setQuery(prefill);
    setAnswer('');
    setCitations(null);
    setError(null);
    abortRef.current?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [title]);

  const run = (q: string) => {
    const text = q.trim();
    if (!text || streaming) return;
    abortRef.current?.();
    setAnswer('');
    setCitations(null);
    setError(null);
    setStreaming(true);
    abortRef.current = ask(
      { query: text },
      {
        onToken: (t) => setAnswer((a) => a + t),
        onCitations: (c) => setCitations(c),
        onDone: () => setStreaming(false),
        onError: (e) => { setError(e.message); setStreaming(false); },
      }
    );
  };

  const done = !streaming && !!answer;
  const ungrounded = done && citations !== null && citations.length === 0;

  return (
    <Card>
      <CardBody className="p-5">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold" style={{ color: 'var(--brand)' }}>
          <Sparkles size={16} /> Ask about this
        </div>
        <form onSubmit={(e) => { e.preventDefault(); run(query); }} className="flex flex-col gap-2 sm:flex-row">
          <Input
            value={query}
            onChange={(e) => setQuery(String(e.value))}
            placeholder="Ask a grounded question about this resource…"
            className="flex-1"
          />
          {streaming ? (
            <Button type="button" fillMode="outline" onClick={() => abortRef.current?.()} startIcon={<Square size={15} />}>
              Stop
            </Button>
          ) : (
            <Button type="submit" themeColor="primary" disabled={!query.trim()} startIcon={<SendHorizontal size={16} />}>
              Ask
            </Button>
          )}
        </form>

        {error && <div className="mt-4"><ErrorBanner>{error}</ErrorBanner></div>}

        {(answer || streaming) && (
          <div className="mt-5 grid grid-cols-1 gap-6 lg:grid-cols-[1fr_16rem]">
            <div>
              <div
                className="answer-prose"
                dangerouslySetInnerHTML={{ __html: renderMarkdown(answer) }}
              />
              {streaming && <div className="mt-2"><TypingDots /></div>}
              {ungrounded && <div className="mt-4"><UngroundedWarning /></div>}
            </div>
            <aside>
              {citations && citations.length > 0 ? (
                <Citations citations={citations} onOpen={(rid) => navigate(`/r/${rid}`)} />
              ) : streaming ? (
                <p className="text-sm text-ink-400">Resolving sources…</p>
              ) : null}
            </aside>
          </div>
        )}
      </CardBody>
    </Card>
  );
}

// ── side rail ("Up next") ───────────────────────────────────────────────────────

type RelatedItem = CatalogCard & { via: string };

function UpNextRail({
  seedId,
  labels,
  navigate,
}: {
  seedId: string;
  seedTitle: string;
  labels: Record<string, string[]>;
  navigate: (to: string) => void;
}) {
  const [items, setItems] = useState<RelatedItem[] | null>(null);
  const labelsKey = JSON.stringify(labels);

  useEffect(() => {
    let live = true;
    setItems(null);

    (async () => {
      const seen = new Set<string>([seedId]);
      const out: RelatedItem[] = [];

      // "Up next" = other resources that share this one's classifications.
      // /catalog is a metadata query, so filtering by the doc's own labels
      // (subsystem, topic, doc type…) returns real neighbours — where a query
      // on the full title would only ever match the doc itself. Broad/among-all
      // labelsets like media_type are skipped so recommendations stay meaningful.
      const SKIP = new Set(['media_type', 'classification', 'state']);
      const PRIORITY = ['subsystem', 'topic', 'crop', 'crops', 'vertical', 'doc_type', 'type', 'mission_phase', 'season'];
      const entries = Object.entries(labels || {})
        .filter(([ls]) => !SKIP.has(ls))
        .sort((a, b) => {
          const ia = PRIORITY.indexOf(a[0]); const ib = PRIORITY.indexOf(b[0]);
          return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
        });

      for (const [labelset, labelList] of entries) {
        for (const label of labelList) {
          if (out.length >= 12) break;
          try {
            const c = await catalog({
              filters: [`/classification.labels/${labelset}/${label}`],
              pageSize: 8,
            });
            for (const item of c.items || []) {
              if (seen.has(item.id)) continue;
              seen.add(item.id);
              out.push({ ...item, via: label });
            }
          } catch { /* try the next label */ }
        }
        if (out.length >= 12) break;
      }

      if (live) setItems(out.slice(0, 12));
    })();

    return () => { live = false; };
  }, [seedId, labelsKey]);

  return (
    <aside className="space-y-3 lg:sticky lg:top-4 lg:self-start">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-ink-500">
        <ListVideo size={14} /> Up next
      </div>

      {items === null && <Spinner label="Finding related…" />}
      {items?.length === 0 && <p className="text-sm text-ink-400">No related resources found.</p>}

      <div className="space-y-2.5">
        {items?.map((c) => {
          const Icon = c.mediaType && /audio|video/i.test(c.mediaType) ? Film : FileText;
          return (
            <ClickableCard
              key={c.id}
              ariaLabel={`Open ${c.title}`}
              onClick={() => navigate(`/r/${c.id}`)}
              className="hover:-translate-y-0.5"
            >
              <Card className="card-hover h-full">
                <CardBody className="flex gap-3 p-3">
                  <span
                    className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg"
                    style={{ background: 'var(--brand-soft)', color: 'var(--brand)' }}
                  >
                    <Icon size={18} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="line-clamp-2 text-sm font-semibold text-ink-900 dark:text-ink-100">{c.title}</p>
                    <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                      <Chip text={c.docType} size="small" fillMode="outline" rounded="full" />
                      {c.durationMinutes != null && (
                        <span className="inline-flex items-center gap-1 text-[11px] text-ink-400">
                          <Clock size={10} /> {c.durationMinutes}m
                        </span>
                      )}
                    </div>
                    {c.via !== 'Similar' && (
                      <p className="mt-1 truncate text-[11px] text-ink-400">shares “{c.via}”</p>
                    )}
                  </div>
                </CardBody>
              </Card>
            </ClickableCard>
          );
        })}
      </div>
    </aside>
  );
}
