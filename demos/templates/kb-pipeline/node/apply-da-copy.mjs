#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────────────
// apply-da-copy.mjs — Standard B10's DA-generated catalogue copy, via the
// KNOWN-WORKING plain-text path (hard rule 3's corollary in CLAUDE.md).
//
// The DA Generator's JSON-schema output path (ask + json:true +
// store_as_key_value + kv_schema_id) is a confirmed, disclosed platform bug
// (CLAUDE.md "Known live platform fragility" - 422s "Invalid JSON schema...
// Expecting value: line 1 column 1" even on Progress's own literal docs
// example). This script does NOT use that path. Instead:
//
//   1. Registers a LABELER DA task (`impact_area` labelset - a genuinely new
//      classification dimension, not a re-derivation of the doc_type already
//      set at ingest) - this is the real, working DA labeler.
//   2. Registers a plain-text `ask` Generator task (json:false - the
//      known-working path) with a strict labelled-line output format
//      (TITLE / SUMMARY / HIGHLIGHTS), destination "compliance_digest".
//   3. Polls GET {kb}/tasks until the ask task shows in `done`.
//   4. For each resource, reads the generated field back - Nuclia stores DA
//      output as `da-<destination>-f-<fieldId>` (CLAUDE.md's documented
//      gotcha), NEVER the plain destination string - parses the labelled-line
//      format server-side (real ARAG retrieval + generation did the work;
//      this script just relays it, per hard rule 3's corollary), and PATCHes
//      it into extra.metadata.da_title / da_summary / da_highlights - the
//      exact keys server/index.mjs's toCard() already reads.
//
// If the task doesn't finish inside the poll window, or a resource's field
// never appears, this script logs it and moves on - server/index.mjs's
// toCard() already falls back gracefully to Nuclia's native title/summary
// for any resource missing these keys (never a blank card either way), so a
// partial or failed run degrades honestly rather than breaking anything.
//
//   node scripts/apply-da-copy.mjs
// ─────────────────────────────────────────────────────────────────────────────
import { readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
function readEnv() {
  const env = { ...process.env };
  for (const p of [join(ROOT, '.env'), join(ROOT, '..', '.env')]) {
    if (!existsSync(p)) continue;
    for (const line of readFileSync(p, 'utf8').split('\n')) {
      const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*(#.*)?$/);
      if (m && env[m[1]] === undefined) env[m[1]] = m[2].replace(/^["']|["']$/g, '');
    }
  }
  return env;
}
const env = readEnv();
const clean = (k) => String(k || '').trim().replace(/^["']+|["']+$/g, '').replace(/^Bearer\s+/i, '').trim();
const KB = (env.NUCLIA_KB_URL || '').replace(/\/+$/, '');
const SA = clean(env.NUCLIA_SERVICEACCOUNT);
if (!KB || !SA) { console.error('  Set NUCLIA_KB_URL and NUCLIA_SERVICEACCOUNT in .env.'); process.exit(1); }
const DP = KB.replace('.rag.progress.cloud', '.dp.progress.cloud');
const headers = { 'X-NUCLIA-SERVICEACCOUNT': `Bearer ${SA}`, 'Content-Type': 'application/json' };
const GEN_MODEL = env.NUCLIA_GENERATIVE_MODEL || '';

const DESTINATION = 'compliance_digest';
const IMPACT_LABELS = [
  { label: 'Advice conduct', description: 'Best Interests Duty, SOA/ROA quality, advice appropriateness' },
  { label: 'Product governance', description: 'APL status, TMD consistency, product suspension/withdrawal' },
  { label: 'Disclosure & reporting', description: 'FSG/PDS accuracy, reportable situations, ASIC notifications' },
  { label: 'Conflicts & remuneration', description: 'Conflicted remuneration, conflicts-of-interest register entries' },
];

async function startTask(name, operations, extra = {}) {
  const parameters = { name: `compliance-co-${name}-${Date.now()}`, on: 1, operations };
  if (GEN_MODEL) parameters.llm = { model: GEN_MODEL };
  const body = { name, parameters, apply: 'ALL', enabled: true, ...extra };
  const res = await fetch(`${DP}/task/start`, { method: 'POST', headers, body: JSON.stringify(body) });
  const j = await res.json().catch(() => ({}));
  console.log(`  ${res.ok ? '✓' : '✗'} task/start ${name} — HTTP ${res.status} ${JSON.stringify(j).slice(0, 200)}`);
  return res.ok;
}

// Real gotcha found running this live (17 Aug 2026): a labeler DA task
// classifies resources directly but does NOT register a formal `/labelset`
// resource the way ingest.mjs's own syncLabelsets() does for front-matter
// labels - GET {kb}/labelsets came back WITHOUT impact_area even after the
// labeler task showed done and /catalog's own facet query proved the
// classifications were genuinely applied. server/index.mjs's facetPaths()
// (and therefore every facet chip / CatalogGrid filter) discovers labelsets
// via that SAME /labelsets call, so a labeler-only classification is
// invisible to the UI until the labelset is ALSO registered explicitly -
// same pattern ingest.mjs already uses for ingest-time labels, just needed
// here too for a DA-applied one.
async function registerImpactAreaLabelset() {
  const payload = {
    title: 'Impact area',
    color: '#22d3ee',
    multiple: true,
    kind: ['RESOURCES'],
    labels: IMPACT_LABELS.map((l) => ({ title: l.label })),
  };
  const res = await fetch(`${KB}/labelset/impact_area`, { method: 'POST', headers, body: JSON.stringify(payload) });
  console.log(`  ${res.ok ? '✓' : '✗'} labelset/impact_area — HTTP ${res.status}`);
  return res.ok;
}

async function registerLabeler() {
  const labelsetOk = await registerImpactAreaLabelset();
  const taskOk = await startTask('labeler', [{ label: { ident: 'impact_area', labels: IMPACT_LABELS } }]);
  return labelsetOk && taskOk;
}

async function registerGenerator() {
  const question =
    'You are labelling a compliance document for a wealth-management review desk. Respond in ' +
    'EXACTLY this three-line format, no extra commentary, no markdown: ' +
    'TITLE: <a specific, human-readable title, max 12 words, naming the actual product/client/policy involved> ' +
    'SUMMARY: <one plain-English sentence on what this document says and why a compliance officer should care, max 35 words> ' +
    'HIGHLIGHTS: <highlight one> | <highlight two> | <highlight three, each a short factual point from the document, pipe-separated>';
  return startTask('ask', [{ ask: { question, destination: DESTINATION, json: false } }]);
}

async function pollDone(timeoutMs = 90000, intervalMs = 5000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const res = await fetch(`${DP}/tasks`, { headers });
    const j = await res.json().catch(() => ({}));
    const running = (j.running || []).filter((t) => t.task?.name === 'ask' && !t.completed);
    const done = (j.done || []).filter((t) => t.task?.name === 'ask');
    console.log(`  · polling… running=${running.length} done=${done.length}`);
    if (done.length && !running.length) return true;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  return false;
}

function parseDigest(text) {
  const title = /TITLE:\s*(.+)/i.exec(text)?.[1]?.trim();
  const summary = /SUMMARY:\s*(.+)/i.exec(text)?.[1]?.trim();
  const highlightsLine = /HIGHLIGHTS:\s*(.+)/i.exec(text)?.[1]?.trim();
  const highlights = highlightsLine ? highlightsLine.split('|').map((h) => h.trim()).filter(Boolean) : [];
  if (!title && !summary) return null;
  return { title, summary, highlights };
}

async function listResourceIds() {
  const res = await fetch(`${KB}/catalog`, {
    method: 'POST', headers, body: JSON.stringify({ query: '', page_size: 60, show: ['basic', 'extra'] }),
  });
  const j = await res.json();
  return Object.keys(j.resources || {});
}

async function applyToResource(id) {
  const r = await fetch(`${KB}/resource/${id}?show=values&show=extra`, { headers });
  if (!r.ok) { console.log(`  ✗ ${id.slice(0, 8)} — read failed HTTP ${r.status}`); return false; }
  const resource = await r.json();
  const texts = resource.data?.texts || {};
  // CLAUDE.md's documented gotcha names the shape `da-<destination>-f-<fieldId>`,
  // but the live field key observed on this KB is `da-<destination>-t-<fieldId>`
  // ("t" for the source field's type, "text" here) - match the destination
  // prefix generically rather than hardcode the middle letter.
  const fieldKey = Object.keys(texts).find((k) => k.startsWith(`da-${DESTINATION}-`));
  if (!fieldKey) { console.log(`  · ${id.slice(0, 8)} — no ${DESTINATION} field yet (task may still be processing this resource)`); return false; }
  const raw = texts[fieldKey]?.value?.body || '';
  const digest = parseDigest(raw);
  if (!digest) { console.log(`  · ${id.slice(0, 8)} — field present but didn't parse (raw: ${raw.slice(0, 80)})`); return false; }

  const existingExtra = resource.extra?.metadata || {};
  const merged = { ...existingExtra, da_title: digest.title, da_summary: digest.summary, da_highlights: digest.highlights };
  const patchRes = await fetch(`${KB}/resource/${id}`, {
    method: 'PATCH', headers, body: JSON.stringify({ extra: { metadata: merged } }),
  });
  if (!patchRes.ok) { console.log(`  ✗ ${id.slice(0, 8)} — PATCH failed HTTP ${patchRes.status} ${(await patchRes.text()).slice(0, 150)}`); return false; }
  console.log(`  ✓ ${id.slice(0, 8)} — "${digest.title}"`);
  return true;
}

async function main() {
  console.log(`\n  Compliance-co DA copy pipeline (plain-text Generator path - the confirmed-working one)\n`);
  const skipRegister = process.argv.includes('--skip-register');
  const labelerOnly = process.argv.includes('--labeler-only');
  if (labelerOnly) { await registerLabeler(); process.exit(0); }
  if (!skipRegister) {
    await registerLabeler();
    const genOk = await registerGenerator();
    if (!genOk) { console.log('\n  Generator task failed to start - stopping. Cards fall back to native title/summary.\n'); process.exit(1); }
  } else {
    console.log('  · --skip-register: reusing an already-started task, polling only.');
  }

  console.log('\n  Waiting for the ask task to finish processing all resources…');
  const finished = await pollDone(180000, 8000);
  if (!finished) console.log('\n  ⚠ Poll window elapsed before the task reported done - applying to whatever has landed so far.\n');

  const ids = await listResourceIds();
  console.log(`\n  Applying generated copy to ${ids.length} resource(s)…`);
  let ok = 0;
  for (const id of ids) { if (await applyToResource(id)) ok++; }
  console.log(`\n  Done: ${ok}/${ids.length} resources now carry DA-generated title/summary/highlights.`);
  if (ok < ids.length) {
    console.log(`  ${ids.length - ok} resource(s) fall back to native title/summary in the UI - this is the`);
    console.log('  designed graceful fallback (toCard() in server/index.mjs), not a broken card.\n');
  }
}
main().catch((e) => { console.error(`\n  ✗ ${e.message}\n`); process.exit(1); });
