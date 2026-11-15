// ─────────────────────────────────────────────────────────────────────────────
// ARAG Portal server.
//
//   1. Holds the KB service-account token (NUCLIA_SERVICEACCOUNT). It NEVER
//      reaches the browser, demo.config.json, /api/config, or the logs.
//   2. Proxies exactly the ARAG surface the portal needs, applying the grounding
//      policy (server/retrieval.mjs) so answers arrive cited by default.
//   3. In production also serves the built SPA (dist/) — one process, one port.
//
// Every KB call authenticates with a single header:
//   X-NUCLIA-SERVICEACCOUNT: Bearer <token>
// (sending more than one authorization header makes Nuclia reject the request).
// ─────────────────────────────────────────────────────────────────────────────

import express from 'express';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { existsSync, readFileSync } from 'node:fs';
import { askBody } from './retrieval.mjs';
import { shapeGraph } from './graph.mjs';
import { catalogFilterExpression, fieldFilterExpression } from './filters.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// ── env (no dotenv dependency) ───────────────────────────────────────────────
// Read portal/.env first, then the factory-root .env (the location the docs tell
// you to fill in). Real environment variables always win over both.
try {
  for (const envPath of [join(ROOT, '.env'), join(ROOT, '..', '.env')]) {
    if (!existsSync(envPath)) continue;
    for (const line of readFileSync(envPath, 'utf8').split('\n')) {
      const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
      if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, '');
    }
  }
} catch { /* ignore */ }

const PORT = process.env.PORT || 4000;
const GEN_MODEL = process.env.NUCLIA_GENERATIVE_MODEL || '';
const TIMEOUT_MS = Number(process.env.NUCLIA_TIMEOUT_MS || 60000);

const trimUrl = (u) => (u || '').replace(/\/+$/, '');
// Sanitise a pasted token: drop surrounding quotes/whitespace and a stray
// "Bearer " prefix (a common copy-paste mistake that yields "JWT decoding error").
const cleanKey = (k) =>
  String(k || '').trim().replace(/^["']+|["']+$/g, '').replace(/^Bearer\s+/i, '').trim();

const KB_BASE = trimUrl(process.env.NUCLIA_KB_URL);
const KB_TOKEN = cleanKey(process.env.NUCLIA_SERVICEACCOUNT || process.env.NUCLIA_API_KEY);

// ── demo config (runtime source of truth for surfaces, theme, safety) ─────────
function loadConfig() {
  for (const p of [join(ROOT, 'demo.config.json'), join(ROOT, 'portal', 'demo.config.json')]) {
    try { if (existsSync(p)) return JSON.parse(readFileSync(p, 'utf8')); } catch { /* try next */ }
  }
  return null;
}
const CONFIG = loadConfig();
const PERSONA = CONFIG?.persona || null;

// The client copy of the config carries NO secrets and NO residency string. The
// `kb` block (env-var names) is dropped, and the zone is never emitted anywhere
// (Hard Rule 4). Everything left is safe to render.
function publicConfig() {
  if (!CONFIG) return { title: 'Agentic RAG Portal', surfaces: [], safety: {}, theme: {} };
  const { kb, ...rest } = CONFIG; // eslint-disable-line no-unused-vars
  return rest;
}

// ── Nuclia client ────────────────────────────────────────────────────────────
function headers(extra = {}) {
  return {
    'X-NUCLIA-SERVICEACCOUNT': `Bearer ${KB_TOKEN}`,
    'Content-Type': 'application/json',
    ...extra,
  };
}

async function kbFetch(pathname, { method = 'GET', body, accept, signal } = {}) {
  if (!KB_BASE || !KB_TOKEN) {
    const err = new Error('Knowledge Box is not configured on the server (set NUCLIA_KB_URL and NUCLIA_SERVICEACCOUNT).');
    err.status = 503;
    throw err;
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(`${KB_BASE}${pathname}`, {
      method,
      headers: headers(accept ? { Accept: accept } : {}),
      body: body ? JSON.stringify(body) : undefined,
      signal: signal || controller.signal,
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      const err = new Error(`Nuclia ${res.status} ${res.statusText}: ${text.slice(0, 400)}`);
      err.status = res.status;
      throw err;
    }
    return res;
  } finally {
    clearTimeout(timer);
  }
}

const jsonOf = async (pathname, opts) => (await kbFetch(pathname, opts)).json();

// ── labelset / facet discovery (cached) ──────────────────────────────────────
// A config-driven portal does not know a KB's taxonomy ahead of time, so facet
// paths are discovered from the KB's own labelsets and cached briefly.
// Cache the KB's declared labelsets AND their declared labels. Nuclia's /catalog
// faceting can surface classification labels that belong to OTHER Knowledge
// Boxes in the same account (observed: a space KB whose doc_type facet returned
// another demo's doc types). A KB must only ever show its own taxonomy, so we
// keep the set of labels each labelset actually declares and filter facets to it.
let facetCache = { paths: null, allowed: {}, ts: 0 };
async function facetPaths() {
  if (facetCache.paths && Date.now() - facetCache.ts < 300000) return facetCache.paths;
  try {
    const data = await jsonOf('/labelsets');
    const sets = data.labelsets || {};
    const ids = Object.keys(sets);
    const paths = ids.map((id) => `/classification.labels/${id}`);
    const allowed = {};
    for (const id of ids) allowed[id] = new Set((sets[id].labels || []).map((l) => l.title));
    facetCache = { paths, allowed, ts: Date.now() };
    return paths;
  } catch {
    return facetCache.paths || [];
  }
}

/**
 * Normalises Nuclia's facet payload into `{ labelset: [{label, count}] }`,
 * keeping only labels this KB declares (see facetPaths). `allowed` is the map
 * of labelset id → Set of declared label titles.
 */
function normaliseFacets(raw, allowed = {}) {
  const source = raw?.fulltext?.facets || raw?.facets || {};
  const out = {};
  for (const [path, entries] of Object.entries(source)) {
    const labelset = path.split('/').filter(Boolean).pop();
    if (!labelset) continue;
    const declared = allowed[labelset];
    const pairs = Array.isArray(entries)
      ? entries.map((e) => [e.facet ?? e.tag ?? '', e.total ?? e.count ?? 0])
      : Object.entries(entries).map(([key, value]) => [
          key,
          typeof value === 'number' ? value : value?.total ?? value?.count ?? 0,
        ]);
    const list = pairs
      .map(([key, count]) => ({ label: String(key).split('/').pop(), count }))
      // Only labels the KB actually declares — drops any cross-KB phantom labels.
      .filter((entry) => entry.label && (!declared || declared.size === 0 || declared.has(entry.label)))
      .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));
    if (list.length) out[labelset] = list;
  }
  return out;
}

/** Flattens a catalog resource into a generic, render-ready card. */
// Standard B10 (arag-demo-app skill, 17 Aug 2026): a catalogue card is
// thumbnail + DA-GENERATED title/summary + structured chips - never a
// hardcoded listing. This is the one place that contract lives, so every
// listing surface built on `catalog()` gets it for free.
//
// The Generator DA task (scripts/create-da-agents.mjs, see docs/DATA-
// AUGMENTATION.md) writes typed fields onto the resource as a native
// key_value field; Nuclia serialises DA output as `da-<destination>-f-
// <fieldId>` (CLAUDE.md's own documented gotcha), so this app's ingest
// script also mirrors the generated title/summary/highlights into
// `extra.metadata` under the fixed keys below (the same place hand-authored
// `extra` metadata already lives) so this card builder never has to know the
// destination/field-id naming for a given KB. Until the Generator is wired
// up for a resource, these keys are simply absent and the card gracefully
// falls back to Nuclia's own native title/summary - the app works before AND
// after the agent runs, never a blank card either way.
const GENERATED_KEYS = new Set(['da_title', 'da_summary', 'da_highlights', 'da_pull_quote']);

function toCard(id, resource) {
  const extra = resource.extra?.metadata || {};
  const classifications = resource.usermetadata?.classifications || [];
  const labels = {};
  for (const { labelset, label } of classifications) (labels[labelset] ||= []).push(label);
  const firstLabel = (...names) => {
    for (const n of names) if (labels[n]?.length) return labels[n][0];
    return null;
  };

  // Structured chips: every OTHER extra.metadata key (i.e. not the generated-
  // copy keys above, not internal bookkeeping) is exactly the "unstructured
  // turned structured" data the Generator/KV-schema pipeline produces - a
  // status, an amount, a date, an entity. Render whatever the schema put there.
  const structuredFields = {};
  for (const [key, value] of Object.entries(extra)) {
    if (GENERATED_KEYS.has(key) || key === 'source_url' || key === 'doc_type' || key === 'media_type' || key === 'duration_minutes' || key === 'authors') continue;
    if (value === null || value === undefined || value === '') continue;
    structuredFields[key] = value;
  }

  return {
    id,
    slug: resource.slug || null,
    title: extra.da_title || resource.title || id,
    summary: extra.da_summary || resource.summary || '',
    highlights: Array.isArray(extra.da_highlights) ? extra.da_highlights : [],
    generated: Boolean(extra.da_title || extra.da_summary),
    // Platform-native thumbnail/frame (Nuclia extracts one automatically for
    // video especially) - prefer this over ever generating or hand-authoring
    // a per-item image; it works for every future upload with zero extra work.
    thumbnail: resource.thumbnail || null,
    icon: resource.icon || null,
    created: resource.created || null,
    sourceUrl: resource.origin?.url || extra.source_url || null,
    docType: firstLabel('doc_type', 'type') || extra.doc_type || 'Document',
    mediaType: firstLabel('media_type') || extra.media_type || null,
    durationMinutes: extra.duration_minutes ?? null,
    labels, // full labelset → [labels] map, for chips
    authors: extra.authors || [],
    structuredFields, // arbitrary KV-schema output → scannable chips
  };
}

// ── app ──────────────────────────────────────────────────────────────────────
const app = express();
app.disable('x-powered-by');
app.use(express.json({ limit: '1mb' }));

/** GET /api/health — cheapest reachability probe (also powers the status chip). */
app.get('/api/health', async (_req, res) => {
  if (!KB_BASE || !KB_TOKEN) {
    return res.json({ ok: false, kb: 'unconfigured' });
  }
  try {
    const counters = await jsonOf('/counters');
    res.json({ ok: true, kb: 'connected', resources: counters.resources ?? null });
  } catch (err) {
    res.json({ ok: false, kb: 'unreachable', error: err.message });
  }
});

/** GET /api/config — the portal's render contract, stripped of anything sensitive. */
app.get('/api/config', (_req, res) => {
  res.set('Cache-Control', 'no-store');
  res.json(publicConfig());
});

/**
 * POST /api/answer — grounded, streamed answer. Relays Nuclia's NDJSON straight
 * through so the UI renders tokens as they arrive; grounding policy (neighbouring
 * paragraphs + citations) is applied here, server-side.
 */
// Fix (team-lead finding, 28 Aug 2026 - the insurance video QA catch): Coverage
// Q&A and Coverage Decision were never scoped, so an unscoped semantic match
// could pull ANOTHER claimant's policy schedule into the source grid alongside
// the queried claim's own documents - a real cross-claim leak on the already-
// approved routes, the same class of bug closed on Exceptions (finding 1) but
// missed there because those two routes also genuinely need the general policy
// wording (PDS) and claims manual, which carry no claim_number label at all -
// naive claim_number-only scoping (as used on Exceptions) would have silently
// dropped the PDS and broken coverage reasoning. This constant names exactly
// the non-claim-specific reference material a coverage/decision question is
// allowed to ground on, in addition to the queried claim's own documents.
const COVERAGE_REFERENCE_DOC_TYPES = ['Policy Wording', 'Claims Manual'];

// Canonical path is /api/answer; /api/ask kept as an alias so nothing
// that already bookmarked it 404s (hard rule: avoid naming a route
// after a real ARAG endpoint - this is this app's OWN proxy route).
app.post(['/api/answer', '/api/ask'], async (req, res) => {
  const { query, filters, searchConfig, resourceId, claimScope } = req.body || {};
  if (!query || !String(query).trim()) return res.status(400).json({ error: 'query is required' });

  const body = { query, ...askBody({ persona: PERSONA, generativeModel: GEN_MODEL }) };
  if (claimScope) {
    // OR across labelsets (claim_number OR doc_type) - fieldFilterExpression's
    // generic helper only ANDs across labelsets, which would wrongly require
    // BOTH conditions on the same document at once. Built directly here since
    // this exact shape is specific to claim-scoped coverage/decision asks.
    body.filter_expression = {
      field: {
        or: [
          { prop: 'label', labelset: 'claim_number', label: String(claimScope) },
          ...COVERAGE_REFERENCE_DOC_TYPES.map((label) => ({ prop: 'label', labelset: 'doc_type', label })),
        ],
      },
    };
  } else {
    // Standard B19 fix - see server/filters.mjs for the empirically-verified
    // reasoning: the legacy `filters` array either 412s ("must start with /")
    // or silently returns zero results depending on path shape; `filter_expression`
    // (field-keyed on /ask) is the one shape that's both documented and proven live.
    const askFilterExpr = fieldFilterExpression(filters);
    if (askFilterExpr) body.filter_expression = askFilterExpr;
  }
  // Scope the answer to a single resource — used by the "journey through the
  // context" walk to ask each source how it relates, grounded only in itself.
  if (resourceId) body.resource_filters = [String(resourceId)];
  // Standard B22 (arag-demo-app skill, 17 Aug 2026): every /api/ask call
  // defaults to the KB's own registered ASK search configuration (see
  // scripts/configure-refusal.mjs), which carries a friendly, on-brand
  // system-prompt instruction for the no-answer case - warm wording, same
  // honest-decline behaviour, configured on the ARAG search configuration
  // itself rather than a hardcoded string in this file. A caller can still
  // name a different configuration explicitly (e.g. for A/B'ing strategies).
  const effectiveSearchConfig = searchConfig || process.env.NUCLIA_ASK_SEARCH_CONFIG || '';
  // A named search configuration is authoritative — it carries its own strategy
  // and prompt, so local overrides would silently fight it.
  if (effectiveSearchConfig) {
    delete body.rag_strategies;
    delete body.prompt;
    delete body.top_k;
    body.search_configuration = effectiveSearchConfig;
  }

  // Abort the upstream only if the CLIENT disconnects before we finish
  // streaming. Watching req.on('close') is wrong — it fires as soon as the POST
  // body is consumed, aborting the upstream mid-answer and yielding an empty
  // (silently swallowed) response.
  const controller = new AbortController();
  res.on('close', () => { if (!res.writableEnded) controller.abort(); });

  try {
    const upstream = await kbFetch('/ask', {
      method: 'POST',
      body,
      accept: 'application/x-ndjson',
      signal: controller.signal,
    });
    res.setHeader('Content-Type', 'application/x-ndjson');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    const reader = upstream.body.getReader();
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      res.write(Buffer.from(value));
      if (typeof res.flush === 'function') res.flush();
    }
    res.end();
  } catch (err) {
    if (controller.signal.aborted) return;
    if (res.headersSent) return res.end();
    res.status(err.status || 502).json({ error: err.message });
  }
});

/**
 * Module 4.1 — POST /api/remi — the REAL RAG-triad score for one answer, via
 * POST {kb}/predict/remi. This is NOT the template's old citation-count proxy
 * (RemiSurface.tsx used to score "grounded" purely on citations.length > 0 -
 * fix 9, Section 3.A).
 *
 * Two load-bearing facts, both confirmed live and ported verbatim from the
 * one proven implementation in the estate (apps/researchos, matching
 * rwa-intel-demo):
 *   1. Auth is the KB SERVICE-ACCOUNT token alone (X-NUCLIA-SERVICEACCOUNT) -
 *      NOT the account-level NUA key, correcting an earlier build-plan
 *      assumption.
 *   2. Score against the FULL retrieved context (up to 8 paragraphs by score,
 *      concatenated into one block), never just the cited excerpt - scoring
 *      against a single thin excerpt made groundedness swing wildly (0/5 then
 *      5/5 on the same accurate, well-cited answer) because the comparison
 *      context was too narrow. The client captures this via `onContexts` on
 *      the same /ask stream (lib/arag.ts) - no second retrieval call needed.
 */
app.post('/api/remi', async (req, res) => {
  const { question, answer, contexts } = req.body || {};
  if (!question || !answer) return res.status(400).json({ error: 'question and answer are required' });
  const ctxs = (Array.isArray(contexts) ? contexts : []).filter((c) => c && String(c).trim()).slice(0, 8);
  const payload = {
    user_id: 'flagship-demo',
    question: String(question),
    answer: String(answer),
    contexts: ctxs.length ? [ctxs.join('\n\n')] : [],
  };
  try {
    const d = await jsonOf('/predict/remi', { method: 'POST', body: payload });
    const ctx = d.context_relevance || [];
    const gnd = d.groundedness || [];
    res.json({
      answerRelevance: d.answer_relevance?.score ?? null,
      answerRelevanceReason: d.answer_relevance?.reason || '',
      contextRelevance: ctx.length ? Math.max(...ctx) : null,
      groundedness: gnd.length ? Math.max(...gnd) : null,
      raw: d,
    });
  } catch (err) {
    res.status(err.status || 502).json({ error: err.message });
  }
});

/**
 * POST /api/extract — Claim Intake's structured extraction, via the WORKING
 * query-time answer_json_schema path (arag-kb skill): POST {kb}/ask with an
 * `answer_json_schema` returns a schema-conformant object grounded in real
 * retrieved content. This is NOT the broken ingest-time DA Generator task.
 *
 * Hard constraint (arag-kb gotcha 4): never send citations:true AND
 * answer_json_schema together (crashes 500/503). So citations is false here;
 * the source documents come from the retrieval_results block instead, which is
 * populated even with citations off.
 */
const INTAKE_FIELDS = [
  ['claim_number', 'Claim number'],
  ['claimant_name', 'Claimant'],
  ['policy_number', 'Policy number'],
  ['product_line', 'Product line'],
  ['peril', 'Peril'],
  ['date_of_loss', 'Date of loss'],
  ['incident_location', 'Incident location'],
  ['loss_description', 'Loss description'],
  ['estimated_amount', 'Estimated amount'],
  ['excess', 'Excess'],
];
const INTAKE_SCHEMA = {
  name: 'claim_intake',
  description: "Structured intake fields extracted from a general-insurance claim's First Notice of Loss and policy schedule.",
  parameters: {
    type: 'object',
    // arag-kb gotcha 6: a strict schema needs every property in `required`.
    properties: Object.fromEntries(INTAKE_FIELDS.map(([k]) => [k, { type: 'string', description: `The ${k.replace(/_/g, ' ')} exactly as the documents state it, or "not stated".` }])),
    required: INTAKE_FIELDS.map(([k]) => k),
  },
};

app.post('/api/extract', async (req, res) => {
  const { claimNumber, claimant } = req.body || {};
  if (!claimNumber) return res.status(400).json({ error: 'claimNumber is required' });
  const who = claimant ? ` (${claimant})` : '';
  const body = {
    query: `From the First Notice of Loss and the policy schedule for claim ${claimNumber}${who}, extract the structured claim intake fields. Use only what those documents actually state; where a field is not stated, return "not stated".`,
    answer_json_schema: INTAKE_SCHEMA,
    citations: false,
    top_k: 20,
    rag_strategies: [{ name: 'neighbouring_paragraphs', before: 2, after: 2 }],
    features: ['keyword', 'semantic'],
    ...(GEN_MODEL ? { generative_model: GEN_MODEL } : {}),
  };
  // Scope the extraction to THIS claim's own documents (claim_number labelset)
  // so retrieval can't bleed another claim's facts (e.g. a different claim's
  // date of loss) into the structured fields.
  const scoped = fieldFilterExpression([`/classification.labels/claim_number/${claimNumber}`]);
  if (scoped) body.filter_expression = scoped;
  try {
    const upstream = await kbFetch('/ask', { method: 'POST', body, accept: 'application/x-ndjson' });
    const text = await upstream.text();
    let answerJson = null;
    const sources = [];
    const seen = new Set();
    for (const line of text.split('\n')) {
      const t = line.trim();
      if (!t) continue;
      let ev;
      try { ev = JSON.parse(t.startsWith('data:') ? t.slice(5) : t); } catch { continue; }
      // The structured object arrives as an ndjson item of type "answer_json"
      // with the object under `item.object` (confirmed live 17 Aug 2026); older
      // shapes used a flat `answer_json` key - accept both.
      if (ev.item?.type === 'answer_json' && ev.item.object && typeof ev.item.object === 'object') answerJson = ev.item.object;
      const aj = ev.answer_json ?? ev.item?.answer_json;
      if (aj && typeof aj === 'object') answerJson = aj;
      // Source documents from the retrieval block (populated even with citations:false).
      const resources = ev.item?.results?.resources || ev.item?.resources || ev.retrieval_results?.resources;
      if (resources && typeof resources === 'object') {
        for (const [rid, r] of Object.entries(resources)) {
          if (seen.has(rid)) continue;
          seen.add(rid);
          sources.push({ resourceId: rid, title: r.title || rid });
        }
      }
    }
    const fields = INTAKE_FIELDS.map(([key, label]) => ({
      key, label,
      value: answerJson && answerJson[key] != null ? answerJson[key] : null,
    }));
    const grounded = !!answerJson && fields.some((f) => f.value && String(f.value).toLowerCase() !== 'not stated');
    res.json({ fields, sources: sources.slice(0, 4), grounded });
  } catch (err) {
    res.status(err.status || 502).json({ error: err.message });
  }
});

/**
 * POST /api/underwriting-summary — Underwriting Risk Summary's structured
 * synthesis, via the same WORKING query-time answer_json_schema path /api/extract
 * uses (arag-kb skill), applied to a different document triad: an underwriting
 * application, its inspection report and its risk-data summary, scoped to that
 * application's own documents via the application_number label (never citations
 * + answer_json_schema together — arag-kb gotcha 4).
 */
const UNDERWRITING_SCHEMA = {
  name: 'underwriting_risk_summary',
  description: "A structured underwriting risk summary synthesised from an insurance application, its inspection report and risk-data summary.",
  parameters: {
    type: 'object',
    properties: {
      applicant_name: { type: 'string', description: 'The applicant name exactly as the documents state it.' },
      product_line: { type: 'string', description: 'The product line, e.g. Home & Contents, Motor, Commercial Property.' },
      overall_risk_rating: { type: 'string', description: 'One of: Low, Medium, High.' },
      key_risk_factors: {
        type: 'array', items: { type: 'string' },
        description: '2 to 5 short phrases naming the specific risk factors identified from the application, inspection and risk data.',
      },
      recommended_action: {
        type: 'string',
        description: 'One of: Accept at standard terms, Accept with loading, Accept with conditions, Refer to senior underwriter, Decline.',
      },
      rationale: { type: 'string', description: '2-3 sentence explanation citing the specific facts that drove the rating and recommendation.' },
    },
    // arag-kb gotcha 6: a strict schema needs every property in `required`, array fields included.
    required: ['applicant_name', 'product_line', 'overall_risk_rating', 'key_risk_factors', 'recommended_action', 'rationale'],
  },
};

app.post('/api/underwriting-summary', async (req, res) => {
  const { applicationNumber, applicant } = req.body || {};
  if (!applicationNumber) return res.status(400).json({ error: 'applicationNumber is required' });
  const who = applicant ? ` (${applicant})` : '';
  const body = {
    query: `From the underwriting application, inspection report and risk data summary for application ${applicationNumber}${who}, synthesise a structured underwriting risk summary. Use only what those documents actually state.`,
    answer_json_schema: UNDERWRITING_SCHEMA,
    citations: false,
    top_k: 20,
    rag_strategies: [{ name: 'neighbouring_paragraphs', before: 2, after: 2 }],
    features: ['keyword', 'semantic'],
    ...(GEN_MODEL ? { generative_model: GEN_MODEL } : {}),
  };
  // Scope to THIS application's own documents so retrieval can't bleed another
  // application's risk facts into the structured summary.
  const scoped = fieldFilterExpression([`/classification.labels/application_number/${applicationNumber}`]);
  if (scoped) body.filter_expression = scoped;
  try {
    const upstream = await kbFetch('/ask', { method: 'POST', body, accept: 'application/x-ndjson' });
    const text = await upstream.text();
    let answerJson = null;
    const sources = [];
    const seen = new Set();
    for (const line of text.split('\n')) {
      const t = line.trim();
      if (!t) continue;
      let ev;
      try { ev = JSON.parse(t.startsWith('data:') ? t.slice(5) : t); } catch { continue; }
      if (ev.item?.type === 'answer_json' && ev.item.object && typeof ev.item.object === 'object') answerJson = ev.item.object;
      const aj = ev.answer_json ?? ev.item?.answer_json;
      if (aj && typeof aj === 'object') answerJson = aj;
      const resources = ev.item?.results?.resources || ev.item?.resources || ev.retrieval_results?.resources;
      if (resources && typeof resources === 'object') {
        for (const [rid, r] of Object.entries(resources)) {
          if (seen.has(rid)) continue;
          seen.add(rid);
          sources.push({ resourceId: rid, title: r.title || rid });
        }
      }
    }
    const summary = answerJson ? {
      applicantName: answerJson.applicant_name ?? null,
      productLine: answerJson.product_line ?? null,
      overallRiskRating: answerJson.overall_risk_rating ?? null,
      keyRiskFactors: Array.isArray(answerJson.key_risk_factors) ? answerJson.key_risk_factors : [],
      recommendedAction: answerJson.recommended_action ?? null,
      rationale: answerJson.rationale ?? null,
    } : null;
    const grounded = !!summary && !!summary.overallRiskRating;
    res.json({ summary, sources: sources.slice(0, 4), grounded });
  } catch (err) {
    res.status(err.status || 502).json({ error: err.message });
  }
});

/** POST /api/search — semantic retrieval (/find), for the results list. */
app.post('/api/search', async (req, res) => {
  const { query, filters, pageSize = 20, searchConfig, features } = req.body || {};
  if (!query || !String(query).trim()) return res.status(400).json({ error: 'query is required' });
  const body = { query, page_size: pageSize };
  const searchFilterExpr = fieldFilterExpression(filters);
  if (searchFilterExpr) body.filter_expression = searchFilterExpr;
  if (searchConfig) body.search_configuration = searchConfig;
  if (features && features.length) body.features = features;
  const started = Date.now();
  try {
    const result = await jsonOf('/find', { method: 'POST', body });
    res.json({ ...result, latencyMs: Date.now() - started });
  } catch (err) {
    res.status(err.status || 502).json({ error: err.message });
  }
});

// Nuclia relevance scores come back 0–5 (sometimes already 0–1). Fold to 0–1.
const norm01 = (v) => {
  const n = Number(v) || 0;
  const s = n > 1 ? n / 5 : n;
  return Math.max(0, Math.min(1, s));
};
const tidyQuote = (t) => String(t || '').replace(/\s+/g, ' ').replace(/^[•\-–\s]+/, '').trim();

/** Rank a /find payload into ordered "journey" stops (strongest match first). */
function journeyStops(raw, cited) {
  const resources = raw.resources || {};
  const stops = [];
  for (const [rid, r] of Object.entries(resources)) {
    const paras = [];
    for (const field of Object.values(r.fields || {})) {
      for (const p of Object.values(field.paragraphs || {})) {
        if (p && typeof p.text === 'string') paras.push({ text: p.text, score: Number(p.score) || 0 });
      }
    }
    paras.sort((a, b) => b.score - a.score);
    const card = toCard(rid, r);
    const labels = Object.values(card.labels || {}).flat().slice(0, 4);
    // Skip the title-as-paragraph (Nuclia indexes the title as its own, often
    // top-scoring, paragraph) so the quote is real supporting prose.
    const titleNorm = tidyQuote(card.title).toLowerCase();
    const isTitle = (t) => { const q = tidyQuote(t).toLowerCase(); return q === titleNorm || q.length < 25; };
    const quote = tidyQuote((paras.find((p) => !isTitle(p.text)) || paras[0])?.text || r.summary || '');
    stops.push({
      resourceId: rid,
      title: card.title,
      url: card.sourceUrl,
      quote,
      labels,
      cited: cited.has(rid),
      _raw: Number(r.score ?? paras[0]?.score ?? 0),
    });
  }
  // The answer's OWN citations are the real grounding — lead with them, then the
  // rest of the retrieved context by strength.
  stops.sort((a, b) => (Number(b.cited) - Number(a.cited)) || (b._raw - a._raw));
  const top = stops.slice(0, 8);
  // Confidence is shown in two bands so the display matches the ordering: the
  // answer's actual sources (cited) read as strong and lead; the rest of the
  // retrieved context reads moderate/weak and follows. Within each band the score
  // is relative to that band's strongest, so the leader is highest and the trail
  // descends — instead of the flat, tiny absolute scores /find returns.
  const band = (items, lo, hi) => {
    const max = Math.max(1e-6, ...items.map((s) => s._raw));
    for (const s of items) s.score = lo + (hi - lo) * Math.max(0, Math.min(1, s._raw / max));
  };
  band(top.filter((s) => s.cited), 0.78, 0.97);
  band(top.filter((s) => !s.cited), 0.35, 0.68);
  for (const s of top) delete s._raw;
  return top;
}

/** POST /api/journey — ranked grounding for the "journey through the context" walk. */
app.post('/api/journey', async (req, res) => {
  const { query, filters, citedIds = [], pageSize = 8 } = req.body || {};
  if (!query || !String(query).trim()) return res.status(400).json({ error: 'query is required' });
  // Retrieve a bit wider than we display so the answer's cited records are
  // captured even if /find ranks them below the top few; journeyStops leads with
  // the cited ones and trims to 8.
  const body = { query, page_size: Math.max(pageSize, 12), features: ['keyword', 'semantic', 'relations'], show: ['basic', 'origin'] };
  const journeyFilterExpr = fieldFilterExpression(filters);
  if (journeyFilterExpr) body.filter_expression = journeyFilterExpr;
  try {
    const raw = await jsonOf('/find', { method: 'POST', body });
    res.json({ stops: journeyStops(raw, new Set((citedIds || []).filter(Boolean))) });
  } catch (err) {
    res.status(err.status || 502).json({ error: err.message });
  }
});

/** POST /api/catalog — faceted browse over the whole corpus (metadata, not semantic). */
app.post('/api/catalog', async (req, res) => {
  const { query = '', filters, pageSize = 60, page = 0 } = req.body || {};
  try {
    const facets = await facetPaths();
    const body = {
      query,
      page_size: pageSize,
      page_number: page,
      show: ['basic', 'origin', 'extra'],
    };
    const catalogFilterExpr = catalogFilterExpression(filters);
    if (catalogFilterExpr) body.filter_expression = catalogFilterExpr;
    if (facets.length) body.faceted = facets;

    const raw = await jsonOf('/catalog', { method: 'POST', body });
    const resources = raw.resources || {};
    const items = Object.entries(resources).map(([id, r]) => toCard(id, r));
    res.json({
      items,
      facets: normaliseFacets(raw, facetCache.allowed),
      total: raw.fulltext?.total ?? items.length,
      page,
      pageSize,
    });
  } catch (err) {
    res.status(err.status || 502).json({ error: err.message });
  }
});

/** POST /api/graph — knowledge-graph path search, shaped for the explorer. */
app.post('/api/graph', async (req, res) => {
  const { entity = '', topK = 200, includeAllGroups = false } = req.body || {};
  const query = { prop: 'path' };
  const seed = String(entity).trim();
  if (seed) {
    query.undirected = true;
    query.source = { value: seed };
  }
  try {
    const raw = await jsonOf('/graph', { method: 'POST', body: { query, top_k: topK } });
    res.json(shapeGraph(raw, { includeAllGroups }));
  } catch (err) {
    res.status(err.status || 502).json({ error: err.message });
  }
});

/** GET /api/entities — entities Nuclia extracted, by group (graph suggestions). */
app.get('/api/entities', async (_req, res) => {
  try {
    const listing = await jsonOf('/entitiesgroups');
    const ids = Object.keys(listing.groups || {});
    const groups = await Promise.all(
      ids.map(async (id) => {
        try {
          const g = await jsonOf(`/entitiesgroup/${encodeURIComponent(id)}`);
          const entities = Object.keys(g.entities || {}).sort();
          return { id, title: g.title || id, count: entities.length, entities };
        } catch {
          return { id, title: id, count: 0, entities: [] };
        }
      })
    );
    res.json({ groups: groups.filter((g) => g.count > 0).sort((a, b) => b.count - a.count) });
  } catch (err) {
    res.status(err.status || 502).json({ error: err.message });
  }
});

/** GET /api/resource/:id — full document when chunks aren't enough. */
app.get('/api/resource/:id', async (req, res) => {
  try {
    const data = await jsonOf(
      `/resource/${encodeURIComponent(req.params.id)}?show=basic&show=values&show=origin&show=extra`
    );
    res.json(data);
  } catch (err) {
    res.status(err.status || 502).json({ error: err.message });
  }
});

// ── Data-augmentation agents (live, via Nuclia predict) ───────────────────────
// The enrichment side of ARAG: the same models Nuclia's Labeler / Graph /
// Generator augmentation agents run at ingest, exposed here so a demo can show
// content being enriched live. All KB-scoped, server-side token only.

// predict/chat streams plain text and appends a status byte; return clean text.
async function predictChat(question, context) {
  const res = await kbFetch('/predict/chat', {
    method: 'POST',
    body: { question, query_context: (context || []).slice(0, 8), user_id: 'augment-demo' },
  });
  const raw = await res.text();
  return raw.replace(/\s*\d\s*$/, '').trim();
}

const firstTextOf = (resource) => {
  const fields = resource?.data?.texts || {};
  let best = '';
  for (const f of Object.values(fields)) {
    const body = f?.value?.body || '';
    if (body.length > best.length) best = body;
  }
  return best || resource?.summary || '';
};

/** POST /api/augment/source {id} → the resource's extracted text (the "extract" step). */
app.post('/api/augment/source', async (req, res) => {
  try {
    const { id } = req.body || {};
    if (!id) return res.status(400).json({ error: 'id required' });
    const data = await jsonOf(`/resource/${encodeURIComponent(id)}?show=basic&show=values`);
    res.json({ title: data.title || id, text: firstTextOf(data).slice(0, 6000) });
  } catch (err) {
    res.status(err.status || 502).json({ error: err.message });
  }
});

/** POST /api/augment/label {text, candidates[]} → Labeler agent: applicable labels. */
app.post('/api/augment/label', async (req, res) => {
  try {
    const { text, candidates } = req.body || {};
    if (!text) return res.status(400).json({ error: 'text required' });
    const list = (candidates || []).map((c) => `${c.labelset}/${c.label}`);
    const q = list.length
      ? `You are a content classifier. From ONLY this candidate label list, return the labels that clearly apply to the content, one per line, exactly as written (format labelset/label). Do not invent labels.\nCandidates:\n${list.join('\n')}`
      : 'Suggest up to 6 concise topical labels for this content, one per line.';
    const out = await predictChat(q, [text]);
    const wanted = new Set(list.map((s) => s.toLowerCase()));
    const labels = out
      .split('\n').map((l) => l.replace(/^[-*\d.\s]+/, '').trim()).filter(Boolean)
      .map((l) => {
        const [ls, ...rest] = l.split('/');
        return rest.length ? { labelset: ls.trim(), label: rest.join('/').trim() } : { labelset: 'topic', label: l };
      })
      .filter((x) => !wanted.size || wanted.has(`${x.labelset}/${x.label}`.toLowerCase()))
      .slice(0, 8);
    res.json({ labels });
  } catch (err) {
    res.status(err.status || 502).json({ error: err.message });
  }
});

/** POST /api/augment/graph {text} → Graph agent: entities (NER) + relation triples. */
app.post('/api/augment/graph', async (req, res) => {
  try {
    const { text } = req.body || {};
    if (!text) return res.status(400).json({ error: 'text required' });
    const snippet = text.slice(0, 1500);
    const [tok, triples] = await Promise.all([
      jsonOf(`/predict/tokens?text=${encodeURIComponent(snippet)}`).catch(() => ({ tokens: [] })),
      predictChat(
        'Extract up to 6 factual subject | relation | object triples from the content. One per line, pipe-separated. Use only entities present in the text.',
        [snippet]
      ).catch(() => ''),
    ]);
    const seen = new Set();
    const entities = (tok.tokens || [])
      .map((t) => ({ text: t.text, type: t.ner }))
      .filter((e) => { const k = e.text.toLowerCase(); if (seen.has(k)) return false; seen.add(k); return true; })
      .slice(0, 24);
    const relations = triples
      .split('\n').map((l) => l.replace(/^[-*\d.)\s]+/, '').split('|').map((s) => s.trim()))
      .filter((p) => p.length === 3 && p[0] && p[2])
      .map(([s, r, o]) => ({ s, r, o })).slice(0, 6);
    res.json({ entities, relations });
  } catch (err) {
    res.status(err.status || 502).json({ error: err.message });
  }
});

/** POST /api/augment/generate {text} → Generator agent: synthetic Q&A pairs. */
app.post('/api/augment/generate', async (req, res) => {
  try {
    const { text } = req.body || {};
    if (!text) return res.status(400).json({ error: 'text required' });
    const out = await predictChat(
      'Generate 3 question-and-answer pairs a reader could ask about this content, answerable from it alone. Format strictly as lines "Q: …" then "A: …".',
      [text]
    );
    const qa = [];
    let cur = null;
    for (const line of out.split('\n')) {
      const q = line.match(/^\s*Q[:.)-]\s*(.+)/i);
      const a = line.match(/^\s*A[:.)-]\s*(.+)/i);
      if (q) { if (cur) qa.push(cur); cur = { q: q[1].trim(), a: '' }; }
      else if (a && cur) cur.a = a[1].trim();
      else if (cur && cur.a) cur.a += ' ' + line.trim();
    }
    if (cur) qa.push(cur);
    res.json({ qa: qa.filter((p) => p.q).slice(0, 4) });
  } catch (err) {
    res.status(err.status || 502).json({ error: err.message });
  }
});

// ── Module 4.3 — RAO: ARAG's own Retrieval Agent calling this app's /mcp ──────
// Registers the honest streaming proxy at POST /api/agent/session (disclosed-
// gap mode automatically when ARAG_AGENT_* env is unset — see rao.mjs). Apps
// built with the `rao-agent` capability additionally call registerMcpServer()
// with their own domain tools (see portal/server/mcp.mjs) to expose /mcp for
// ARAG to call back into.
import { registerRaoProxy } from './rao.mjs';
import { registerMcpServer } from './mcp.mjs';
import { matchPolicies, matchHistories, matchClaims } from './claimsData.mjs';
import { recordKbSources } from './kbTap.mjs';
registerRaoProxy(app);

// Standard B26 (GM review, 18 Aug 2026): the KB-retrieval tool the Retrieval
// Agent calls to ground on the UNSTRUCTURED policy/claim documents, alongside
// the structured live-data tools below. It runs a scoped /find against this
// demo's own Knowledge Box and returns cited document passages; the passages it
// grounds on are tapped (kbTap) so the RAO proxy can render them beside the
// tool trail. Compact by design (top 3, short excerpts) so it survives the
// agent's trace and the answer blends live data AND the wording in one reply.
async function searchClaimDocuments({ question }) {
  const q = String(question || '').trim();
  if (!q) return { found: false, message: 'No question supplied.' };
  const raw = await jsonOf('/find', {
    method: 'POST',
    body: { query: q, page_size: 6, features: ['keyword', 'semantic'], show: ['basic'] },
  });
  const resources = raw.resources || {};
  const ranked = Object.entries(resources).map(([rid, r]) => {
    let best = '';
    let bestScore = -Infinity;
    for (const field of Object.values(r.fields || {})) {
      for (const p of Object.values(field.paragraphs || {})) {
        const s = Number(p.score) || 0;
        if (typeof p.text === 'string' && s > bestScore) { bestScore = s; best = p.text; }
      }
    }
    const clean = (s) => String(s || '').replace(/\s+/g, ' ').replace(/["\\]/g, "'").trim();
    return {
      resourceId: rid,
      title: clean(r.title || rid).slice(0, 120),
      excerpt: clean(best || r.summary || '').slice(0, 220),
      score: Number(r.score ?? bestScore) || 0,
    };
  });
  ranked.sort((a, b) => b.score - a.score);
  const passages = ranked.slice(0, 3).map(({ resourceId, title, excerpt }) => ({ resourceId, title, excerpt }));
  if (passages.length) recordKbSources(passages);
  return { found: passages.length > 0, passages };
}

// ── Module 4.3 — this app's own /mcp exposure, so ARAG's Retrieval Agent
// (the Claims Copilot) can plan and call back OUT to the insurer's live
// operational data (policy master, claimant-history register, claim record)
// AND search the unstructured policy/claim documents in the Knowledge Box
// (search_claim_documents, Standard B26) - blending structured and unstructured
// in one grounded answer, never a homegrown planner narrating a DB lookup.
// Standard B29 (realism): resolve a lookup like a competent claims handler -
// a single hit returns it; MULTIPLE hits return an honest disambiguation
// (never pick one and fabricate certainty); zero hits declines and says what
// identifier is needed. The agent's summarize prompt (setup_rao.py) is told to
// relay an `ambiguous` result by asking which record, not choosing one.
function resolveOne(term, matches, { kind, need, shape }) {
  if (matches.length === 0) {
    return { found: false, message: `No ${kind} matching "${term}". Provide ${need} to look one up.` };
  }
  if (matches.length > 1) {
    return {
      found: false,
      ambiguous: true,
      message: `"${term}" matches ${matches.length} ${kind}s - it is not specific enough to resolve one. Ask which specific record is meant.`,
      candidates: matches.map(shape),
    };
  }
  return { found: true, ...matches[0] };
}

registerMcpServer(app, {
  tools: {
    get_policy_status: {
      description: 'Look up a policy by policy number or policyholder name: product line, whether it is in force, premium status (current or in arrears), excess, endorsements, and whether optional flood cover was selected. If the name or term matches more than one policy it returns an ambiguous result with candidates - ask which one; it never guesses a single policy.',
      inputSchema: { type: 'object', properties: { policy: { type: 'string', description: 'A policy number (e.g. THP-55190) or the policyholder name.' } }, required: ['policy'] },
      handler: async ({ policy }) => resolveOne(policy, matchPolicies(policy), {
        kind: 'policy', need: 'a policy number or the full policyholder name',
        shape: (p) => ({ policyNumber: p.policyNumber, holder: p.holder, productLine: p.productLine }),
      }),
    },
    get_claimant_history: {
      description: "Look up a claimant's prior claims history by name: prior claim numbers, perils, years and outcomes. If the name matches more than one claimant it returns an ambiguous result with candidates - ask which one.",
      inputSchema: { type: 'object', properties: { claimant: { type: 'string' } }, required: ['claimant'] },
      handler: async ({ claimant }) => {
        const r = resolveOne(claimant, matchHistories(claimant), {
          kind: 'claimant', need: 'the full claimant name',
          shape: (h) => ({ claimant: h.claimant }),
        });
        return r.found ? { ...r, totalPriorClaims: r.priorClaims.length } : r;
      },
    },
    get_claim: {
      description: 'Look up a claim record by claim number or claimant name: peril, date of loss, amount and current status. If the term matches more than one claim it returns an ambiguous result with candidates - ask which one; it never guesses a single claim.',
      inputSchema: { type: 'object', properties: { claim: { type: 'string', description: 'A claim number (e.g. CLM-2026-0466) or the claimant name.' } }, required: ['claim'] },
      handler: async ({ claim }) => resolveOne(claim, matchClaims(claim), {
        kind: 'claim', need: 'a claim number or the full claimant name',
        shape: (c) => ({ claimNumber: c.claimNumber, claimant: c.claimant, peril: c.peril, status: c.status }),
      }),
    },
    // Standard B26: the UNSTRUCTURED retrieval source, alongside the three
    // structured live-data tools above. The agent blends both in one answer.
    search_claim_documents: {
      description: "Search Publisher's policy wording and claim documents - the product disclosure statements (PDS), the claims-handling manual, adjuster reports, First Notice of Loss narratives and decision letters - for the clauses and passages relevant to a question. Returns cited document passages. Use this to ground an answer in the ACTUAL policy or claim wording (e.g. whether a peril is covered, what a sub-limit or endorsement says), alongside the live-data tools; blend both when a question needs the live status AND the wording that governs it.",
      inputSchema: { type: 'object', properties: { question: { type: 'string', description: 'A natural-language question about the policy wording or claim documents.' } }, required: ['question'] },
      handler: async ({ question }) => searchClaimDocuments({ question }),
    },
  },
});

// ── static SPA (production) ───────────────────────────────────────────────────
const DIST = join(ROOT, 'dist');
if (existsSync(DIST)) {
  app.use('/assets', express.static(join(DIST, 'assets'), { immutable: true, maxAge: '365d' }));
  app.use(express.static(DIST, { index: false, maxAge: '1h' }));
  app.get('*', (req, res, next) => {
    if (req.path.startsWith('/api/')) return next();
    res.set('Cache-Control', 'no-cache, no-store, must-revalidate');
    res.sendFile(join(DIST, 'index.html'));
  });
}

app.listen(PORT, () => {
  const kb = KB_BASE ? 'configured' : 'NOT configured (set NUCLIA_KB_URL + NUCLIA_SERVICEACCOUNT)';
  console.log(`[arag-portal] listening on :${PORT}  ·  KB ${kb}`);
});
