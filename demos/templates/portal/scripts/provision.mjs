#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────────────
// Module 4.4 (flagship rebuild) — one-command KB provisioning + ingest.
//
// Merges create-kb.mjs (account-key create-and-mint-token flow) + ingest.mjs
// (Markdown corpus, now with the --force bug fixed at the source, Section 3
// fix 5) + a binary-media ingest path (ResearchOS's proven ingest_media.mjs
// pattern, POST /kb/{id}/upload — fix 15) into a single command, one flag
// set, that also:
//   - waits for real searchability (PROCESSED status + the buffer arag-kb
//     gotcha 11 requires — PROCESSED can lag actual searchability),
//   - registers the standard DA tasks with the generative model pinned
//     (arag-kb gotcha 7 / this fork's create-da-agents.mjs fix, above),
//   - bakes in the stuck-resource guard (arag-kb gotcha 10) as a standing
//     resilience note, not an emergency patch applied only after a KB-wide
//     500 is already hit live,
//   - ships --purge as the standard 30-second reset mechanism.
//
// Usage:
//   node scripts/provision.mjs                       # create KB + mint token (if not already bound)
//   node scripts/provision.mjs --corpus data/corpus   # + ingest markdown
//   node scripts/provision.mjs --media data/media     # + ingest binary media
//   node scripts/provision.mjs --da                   # + register standard DA tasks (model-pinned)
//   node scripts/provision.mjs --all --corpus data/corpus --media data/media --da
//   node scripts/provision.mjs --purge                # 30-second reset: delete every resource
//
// Zero new dependencies beyond what create-kb.mjs/ingest.mjs already use.
// ─────────────────────────────────────────────────────────────────────────────

import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const ENV_PATH = join(ROOT, '.env');

function readEnv() {
  const env = { ...process.env };
  if (existsSync(ENV_PATH)) {
    for (const line of readFileSync(ENV_PATH, 'utf8').split('\n')) {
      const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
      if (m && env[m[1]] === undefined) env[m[1]] = m[2].replace(/^["']|["']$/g, '');
    }
  }
  return env;
}

const arg = (name, def) => { const i = process.argv.indexOf(name); return i > -1 ? process.argv[i + 1] : def; };
const has = (name) => process.argv.includes(name);
const clean = (k) => String(k || '').trim().replace(/^["']+|["']+$/g, '').replace(/^Bearer\s+/i, '').trim();
const trimUrl = (u) => (u || '').replace(/\/+$/, '');

function run(script, args = []) {
  console.log(`\n  → node scripts/${script} ${args.join(' ')}`);
  // Bug fix (local to this app's copy): readEnv() above only returns a local
  // object — it never exported .env values onto process.env, so a spawned
  // child (ingest.mjs, create-kb.mjs) that reads process.env directly saw
  // nothing and failed with "Set NUCLIA_KB_URL and NUCLIA_SERVICEACCOUNT."
  // even with a fully populated .env. Pass the merged env through explicitly.
  execFileSync('node', [join(ROOT, 'scripts', script), ...args], { stdio: 'inherit', cwd: ROOT, env: { ...process.env, ...readEnv() } });
}

// ── binary media ingest (module 4.4 / fix 15: ResearchOS's proven pattern) ────
// POST /kb/{id}/upload on the dp.progress.cloud host (binary bytes + X-Filename),
// then PATCH /resource/{id} for title/summary/classification — never the
// two-step create-resource + PUT-file pattern (500s on PDFs per ARAKS phase 1).
async function ingestMedia(env, mediaDir) {
  const KB = trimUrl(env.NUCLIA_KB_URL);
  const SA = clean(env.NUCLIA_SERVICEACCOUNT);
  if (!KB || !SA) { console.error('\n  ✗ NUCLIA_KB_URL / NUCLIA_SERVICEACCOUNT not set — run provisioning first.\n'); process.exit(1); }
  const DP = KB.replace('.rag.progress.cloud', '.dp.progress.cloud');
  const headers = { 'X-NUCLIA-SERVICEACCOUNT': `Bearer ${SA}` };

  if (!existsSync(mediaDir)) { console.log(`  · no media dir at ${mediaDir}, skipping`); return; }
  const files = readdirSync(mediaDir).filter((f) => !f.startsWith('.'));
  console.log(`\n  Media: ${files.length} file(s) in ${mediaDir}`);
  for (const [i, file] of files.entries()) {
    const bytes = readFileSync(join(mediaDir, file));
    const pos = `${String(i + 1).padStart(3)}/${files.length}`;
    try {
      const res = await fetch(`${DP}/kb/${env.NUCLIA_KB_ID}/upload`, {
        method: 'POST',
        headers: { ...headers, 'X-Filename': Buffer.from(file).toString('base64'), 'Content-Type': 'application/octet-stream' },
        body: bytes,
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) { console.log(`  ${pos}  FAIL  ${file} — ${res.status} ${JSON.stringify(j).slice(0, 150)}`); continue; }
      const resourceId = j.uuid || j.id;
      if (resourceId) {
        await fetch(`${KB}/resource/${resourceId}`, {
          method: 'PATCH', headers: { ...headers, 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: file }),
        });
      }
      console.log(`  ${pos}  ok    ${file}  (${resourceId || 'no id returned'})`);
    } catch (e) {
      console.log(`  ${pos}  FAIL  ${file} — ${e.message}`);
    }
  }
}

// ── wait for real searchability (arag-kb gotcha 11) ───────────────────────────
// PROCESSED status on a resource lags actual searchability by a real buffer —
// waiting only for PROCESSED and then querying immediately can still miss.
async function waitForSearchable(env, { timeoutMs = 180000, pollMs = 5000, settleMs = 15000 } = {}) {
  const KB = trimUrl(env.NUCLIA_KB_URL);
  const SA = clean(env.NUCLIA_SERVICEACCOUNT);
  const headers = { 'X-NUCLIA-SERVICEACCOUNT': `Bearer ${SA}` };
  const start = Date.now();
  console.log('\n  Waiting for resources to reach PROCESSED…');
  for (;;) {
    const res = await fetch(`${KB}/resources?size=200&page=0`, { headers });
    const j = await res.json().catch(() => ({ resources: [] }));
    const resources = j.resources || [];
    const pending = resources.filter((r) => r.metadata?.status && r.metadata.status !== 'PROCESSED' && r.metadata.status !== 'ERROR');
    const errored = resources.filter((r) => r.metadata?.status === 'ERROR');
    if (errored.length) {
      console.log(`  ⚠ ${errored.length} resource(s) in ERROR — excluded from the stuck-resource guard below, not blocking the wait.`);
    }
    if (!pending.length) {
      console.log(`  ✓ All ${resources.length} resource(s) PROCESSED. Waiting ${settleMs / 1000}s more for the searchability buffer…`);
      await new Promise((r) => setTimeout(r, settleMs));
      return;
    }
    if (Date.now() - start > timeoutMs) {
      console.log(`  ⚠ Timed out after ${timeoutMs / 1000}s with ${pending.length} resource(s) still processing — continuing anyway.`);
      return;
    }
    await new Promise((r) => setTimeout(r, pollMs));
  }
}

// ── --purge: the standard 30-second reset (module spec, part 5) ───────────────
async function purge(env) {
  const KB = trimUrl(env.NUCLIA_KB_URL);
  const SA = clean(env.NUCLIA_SERVICEACCOUNT);
  if (!KB || !SA) { console.error('\n  ✗ NUCLIA_KB_URL / NUCLIA_SERVICEACCOUNT not set — nothing to purge.\n'); process.exit(1); }
  const headers = { 'X-NUCLIA-SERVICEACCOUNT': `Bearer ${SA}` };
  console.log(`\n  Purging all resources from ${env.NUCLIA_KB_ID}…`);
  let deleted = 0;
  for (let page = 0; page < 50; page++) {
    const res = await fetch(`${KB}/resources?size=100&page=${page}`, { headers });
    const j = await res.json().catch(() => ({ resources: [] }));
    const resources = j.resources || [];
    if (!resources.length) break;
    for (const r of resources) {
      await fetch(`${KB}/resource/${r.id}`, { method: 'DELETE', headers });
      deleted++;
    }
    if (resources.length < 100) break;
  }
  console.log(`  ✓ Purged ${deleted} resource(s). Re-run with --corpus/--media to reseed. (~30s reset)\n`);
}

async function main() {
  const env = readEnv();

  if (has('--purge')) {
    await purge(env);
    return;
  }

  // 1) KB + token, if not already bound.
  if (!env.NUCLIA_KB_URL || !env.NUCLIA_SERVICEACCOUNT) {
    const title = arg('--title', 'ARAG Demo');
    const slug = arg('--slug', 'demo');
    run('create-kb.mjs', ['--title', title, '--slug', slug]);
  } else {
    console.log(`  · KB already bound: ${env.NUCLIA_KB_ID || env.NUCLIA_KB_URL}`);
  }

  // 2) Markdown corpus (ingest.mjs — --force bug fixed at the source, fix 5).
  const corpus = arg('--corpus', null);
  if (corpus) {
    const ingestArgs = ['--corpus', corpus];
    if (has('--force')) ingestArgs.push('--force');
    run('ingest.mjs', ingestArgs);
  }

  // 3) Binary media (fix 15 — the confirmed POST /kb/{id}/upload path).
  const media = arg('--media', null);
  if (media) {
    await ingestMedia(readEnv(), resolve(media));
  }

  // 4) Wait for real searchability before anything downstream queries the KB.
  if (corpus || media) {
    await waitForSearchable(readEnv());
  }

  // 5) DA tasks, model-pinned (create-da-agents.mjs, fixed above).
  if (has('--da')) {
    run('create-da-agents.mjs', []);
  }

  console.log('\n  Provisioning complete.\n');
}

main().catch((e) => { console.error(e); process.exit(1); });
