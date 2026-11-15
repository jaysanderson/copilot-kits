// ─────────────────────────────────────────────────────────────────────────────
// OtherResourceCard — the honest treatment for a session neither the video
// player nor the deck viewers can render: a zip, a Word doc, a spreadsheet, a
// .rar — 36+ real files in this KB's own catalog. Never a broken player;
// a clean, designed card with the real title, the KB-grounded insight panel
// (still real for these — the Generator DA agent runs over every resource's
// extracted text where Nuclia produced any) and a genuine download action.
// ─────────────────────────────────────────────────────────────────────────────
import { FileArchive, Download } from 'lucide-react';
import type { SessionMeta } from './sessions-lib';
import { sessionDownloadUrl } from './sessions-lib';

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

export function OtherResourceCard({ meta }: { meta: SessionMeta }) {
  const ext = (meta.filename || '').split('.').pop()?.toUpperCase() || null;
  const sizeLabel = meta.fileSize != null ? formatBytes(meta.fileSize) : null;
  const detail = [ext ? `.${ext.toLowerCase()} file` : null, sizeLabel].filter(Boolean).join(' · ');

  return (
    <div className="card flex flex-col items-center gap-4 p-10 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl" style={{ background: 'var(--brand-soft)' }}>
        <FileArchive size={28} style={{ color: 'var(--brand)' }} />
      </div>
      <div>
        <p className="text-sm font-semibold text-ink-900 dark:text-ink-50">
          This file type can&rsquo;t be previewed in the browser
        </p>
        <p className="mt-1 text-xs text-ink-400">{detail || 'No further file details recorded.'}</p>
      </div>
      <a href={sessionDownloadUrl(meta.id)} className="btn btn-brand">
        <Download size={14} /> Download original
      </a>
    </div>
  );
}
