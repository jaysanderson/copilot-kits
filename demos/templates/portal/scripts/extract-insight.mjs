#!/usr/bin/env node
// Standard B28 integrity (hard rule 3): the Portfolio insight charts claim
// "extracted by ARAG from the adjuster free-text / FNOL narrative / the whole
// claim file". That claim must be backed by a REAL ARAG extraction, not authored
// or synthetic values under an "ARAG extracted this" chip. This script runs the
// genuine query-time answer_json_schema /ask (the same working structured-JSON
// path Claim Intake uses) over each DOCUMENTED claim's own unstructured files
// (FNOL narrative, adjuster report, decision letter), scoped by the claim_number
// label, and prints the extracted insight per claim. The verified output is baked
// into the store as the source of truth for those claims (so every charted value
// is a real ARAG extraction, attributable), and the charts are scoped to exactly
// the claims genuinely extracted here.
//
//   node scripts/extract-insight.mjs            # print JSON for all documented claims
//
// Reads .env: NUCLIA_KB_URL, NUCLIA_SERVICEACCOUNT, NUCLIA_GENERATIVE_MODEL.

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
function env() {
  const d = {};
  for (const p of [join(ROOT, '.env'), join(ROOT, 'portal', '.env')]) {
    try {
      for (const line of readFileSync(p, 'utf8').split('\n')) {
        const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
        if (m && !(m[1] in d)) d[m[1]] = m[2].replace(/^["']|["']$/g, '').replace(/\s+#.*$/, '').trim();
      }
    } catch { /* next */ }
  }
  return d;
}
const E = env();
const KB = (E.NUCLIA_KB_URL || '').replace(/\/+$/, '');
const TOKEN = (E.NUCLIA_SERVICEACCOUNT || E.NUCLIA_API_KEY || '').replace(/^Bearer\s+/i, '');
const GEN = E.NUCLIA_GENERATIVE_MODEL || '';
if (!KB || !TOKEN) { console.error('Missing NUCLIA_KB_URL / NUCLIA_SERVICEACCOUNT'); process.exit(1); }

// The eight documented claims (claim_number label = the value used to scope).
const CLAIMS = [
  ['CLM-2026-0501', 'The Delacroix Family'],
  ['CLM-2026-0466', 'Tomas Ruiz'],
  ['CLM-2026-0473', 'Helena Vaughn'],
  ['CLM-2026-0492', 'Priya Anand'],
  ['CLM-2026-0488', 'Raj Malhotra'],
  ['CLM-2026-0510', 'George Mensah'],
  ['CLM-2026-0455', 'Brightwater Cafe Pty Ltd'],
  ['CLM-2026-0480', 'Sofia Bianchi'],
];

const SCHEMA = {
  name: 'claim_insight',
  description: "Insight obtained by READING a claim's unstructured documents (the adjuster report free-text, the First Notice of Loss narrative, the decision letter) - the structure a coded claim record does not carry.",
  parameters: {
    type: 'object',
    properties: {
      cause_theme: { type: 'string', description: "The specific cause of loss in the adjuster's own terms, finer than the coded peril - e.g. 'Sudden escape of water' vs 'Gradual deterioration', 'Riverine flood (overtopping)', 'Forced-entry burglary', 'Electrical fire'. A short noun phrase." },
      claimant_sentiment: { type: 'string', enum: ['Calm', 'Concerned', 'Distressed'], description: "The claimant's emotional tone as conveyed by the First Notice of Loss narrative." },
      integrity_signals: { type: 'array', items: { type: 'string', enum: ['Date-of-loss mismatch', 'Premium in arrears', 'Value over sub-limit', 'Inconsistent damage cause', 'Prior-claims pattern'] }, description: 'Integrity / fraud-risk indicators actually evident from reading this file; an empty array if the file is consistent.' },
      coverage_complexity: { type: 'string', enum: ['Straightforward', 'Moderate', 'Complex'], description: 'How many policy clauses must be reasoned across to decide the claim: a single covered peril is Straightforward; a multi-clause exclusion or sub-limit call is Complex.' },
    },
    required: ['cause_theme', 'claimant_sentiment', 'integrity_signals', 'coverage_complexity'],
  },
};

async function extract(claimNumber, claimant) {
  const body = {
    query: `Read every document on file for claim ${claimNumber} (${claimant}) - the First Notice of Loss narrative, the adjuster report and any decision letter - and extract the claim insight fields from what those documents actually say. Judge the claimant's sentiment from the FNOL narrative's tone, the cause theme from the adjuster's own words, and the integrity signals from the whole file. Use only what the documents state.`,
    answer_json_schema: SCHEMA,
    citations: false,
    top_k: 20,
    features: ['keyword', 'semantic'],
    rag_strategies: [{ name: 'neighbouring_paragraphs', before: 2, after: 2 }],
    filter_expression: { field: { prop: 'label', labelset: 'claim_number', label: claimNumber } },
    ...(GEN ? { generative_model: GEN } : {}),
  };
  const res = await fetch(`${KB}/ask`, {
    method: 'POST',
    headers: { 'X-NUCLIA-SERVICEACCOUNT': `Bearer ${TOKEN}`, 'Content-Type': 'application/json', Accept: 'application/x-ndjson' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${claimNumber}: ${res.status} ${(await res.text()).slice(0, 300)}`);
  const text = await res.text();
  let obj = null;
  for (const line of text.split('\n')) {
    const t = line.trim(); if (!t) continue;
    let ev; try { ev = JSON.parse(t.startsWith('data:') ? t.slice(5) : t); } catch { continue; }
    if (ev.item?.type === 'answer_json' && ev.item.object) obj = ev.item.object;
    const aj = ev.answer_json ?? ev.item?.answer_json; if (aj && typeof aj === 'object') obj = aj;
  }
  return obj;
}

const out = {};
for (const [num, who] of CLAIMS) {
  try {
    const r = await extract(num, who);
    out[num] = r;
    console.error(`${num} ${who} -> ${r ? 'OK' : 'NO JSON'}`);
  } catch (e) { console.error(String(e.message)); out[num] = null; }
}
console.log(JSON.stringify(out, null, 2));
