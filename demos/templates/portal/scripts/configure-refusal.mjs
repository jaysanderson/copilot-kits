#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────────────
// configure-refusal.mjs — registers the KB's own ASK search configuration that
// carries a friendly, on-brand no-answer / not-enough-data message.
//
// GM correction (17 Aug 2026, arag-demo-app skill Standard B22): ARAG's
// default no-context reply ("Not enough data to answer this.") is blunt.
// Behaviour must not change - an ungrounded question must still be honestly
// declined, never invented - but the WORDING must be warm and on-brand, and
// it must be configured on the ARAG search configuration itself (so it is
// genuine, and shows up in the live admin console), never hardcoded as a
// string swap in app code.
//
// Mechanism (verified against reference/agentic-rag-guide's Appendix F
// AskConfig schema - working spec, not a guess): a `kind: "ask"` search
// configuration stores a full AskConfig, including `prompt` (string |
// CustomPrompt). A CustomPrompt's `system` field is honoured exactly like the
// system prompt on a normal /ask call, so instructing the model there to
// phrase an unsupported-question decline warmly (while still never inventing
// an answer) is the sanctioned, working mechanism -
// POST {KB}/search_configurations/{name}   body { kind: "ask", config: {...} }
// authenticated with the KB service-account token (X-NUCLIA-SERVICEACCOUNT).
//
// Reads from .env: NUCLIA_KB_URL, NUCLIA_SERVICEACCOUNT.
// Zero dependencies — Node 20+.
//
//   node scripts/configure-refusal.mjs
// ─────────────────────────────────────────────────────────────────────────────
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

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
function writeEnvVars(vars) {
  let text = existsSync(ENV_PATH) ? readFileSync(ENV_PATH, 'utf8') : '';
  for (const [k, v] of Object.entries(vars)) {
    if (v == null || v === '') continue;
    const re = new RegExp(`^${k}=.*$`, 'm');
    text = re.test(text) ? text.replace(re, `${k}=${v}`) : text.replace(/\n?$/, '\n') + `${k}=${v}\n`;
  }
  writeFileSync(ENV_PATH, text);
}
const clean = (k) => String(k || '').trim().replace(/^["']+|["']+$/g, '').replace(/^Bearer\s+/i, '').trim();

const CONFIG_NAME = 'publisher-friendly-refusal';

// The same grounding rules AdvisorDeskPage/SuitabilityPage already rely on
// (server/retrieval.mjs's systemPrompt), PLUS the warm-refusal instruction -
// so switching to this named configuration doesn't quietly change grounding
// behaviour, only the wording of an honest decline.
const SYSTEM_PROMPT = `You are the claims assistant for Publisher Mutual's claims desk, answering from the claim files, policy wordings and claims manuals.

Rules:
- Answer ONLY from the provided context. If the context does not fully support an answer, never invent facts, figures or sources - decline honestly, every time.
- NEVER write the phrase "not enough data" (in any capitalisation, anywhere in your reply, including as an opening line before other content) and NEVER write "the context does not" as your opening words. These are banned strings - a reply containing either of them, in whole or in part, is wrong, even if the rest of the reply is otherwise good. This applies whether you are declining completely or only partially answering.
- Instead, when you cannot fully answer, decline or hedge warmly and helpfully, the way a knowledgeable claims colleague would: open by stating whatever you DO know from the claim files (if anything), then say plainly that the claim files and policy wordings do not cover the remaining part of the question, and suggest one concrete next step (rephrasing the question against a specific claim or policy, or opening the relevant policy wording or claim document). Two to three sentences, plain language, never templated or robotic-sounding.
- Be specific and quantitative. Quote figures (dates, amounts, excesses, sub-limits, policy and claim numbers) exactly as the source gives them.
- Attribute claim-specific or policy-specific findings to their source document; do not generalise a single claim's facts beyond what it supports.
- Where sources disagree, or a finding is preliminary, say so rather than presenting it as settled.
- Prefer Australian English and spelling conventions.`;

async function main() {
  const env = readEnv();
  const KB = (env.NUCLIA_KB_URL || '').replace(/\/+$/, '');
  const TOKEN = clean(env.NUCLIA_SERVICEACCOUNT);
  if (!KB || !TOKEN) {
    console.error('\n  ✗ Set NUCLIA_KB_URL and NUCLIA_SERVICEACCOUNT in .env first (run create-kb.mjs).\n');
    process.exit(1);
  }
  const DP = KB.replace('.rag.progress.cloud', '.dp.progress.cloud');
  const headers = { 'X-NUCLIA-SERVICEACCOUNT': `Bearer ${TOKEN}`, 'Content-Type': 'application/json' };

  const body = {
    kind: 'ask',
    config: {
      top_k: 20,
      rag_strategies: [{ name: 'neighbouring_paragraphs', before: 2, after: 2 }],
      citations: true,
      citation_threshold: 0.25,
      prompt: { system: SYSTEM_PROMPT },
    },
  };

  console.log(`\n  Registering "${CONFIG_NAME}" ask search configuration on the Knowledge Box…`);
  let res = await fetch(`${DP}/search_configurations/${encodeURIComponent(CONFIG_NAME)}`, {
    method: 'POST', headers, body: JSON.stringify(body),
  });
  if (res.status === 409) {
    // Already registered (e.g. re-running after refining the prompt wording) —
    // PATCH updates it in place rather than treating "already exists" as a failure.
    console.log('  (already exists — updating in place via PATCH)');
    res = await fetch(`${DP}/search_configurations/${encodeURIComponent(CONFIG_NAME)}`, {
      method: 'PATCH', headers, body: JSON.stringify(body),
    });
  }
  if (res.ok) {
    console.log(`  ✓ ${CONFIG_NAME} (ask)`);
    writeEnvVars({ NUCLIA_ASK_SEARCH_CONFIG: CONFIG_NAME });
    console.log(`\n  Done. Written to .env as NUCLIA_ASK_SEARCH_CONFIG=${CONFIG_NAME}.`);
    console.log('  server/index.mjs defaults every /api/ask call to this configuration unless');
    console.log('  the caller names a different one - the friendly refusal is genuine, not a');
    console.log('  hardcoded string swap, and it is visible on the KB in the live admin console.\n');
    process.exit(0);
  } else {
    const text = await res.text().catch(() => '');
    console.log(`  ✗ HTTP ${res.status} ${text.slice(0, 300)}`);
    process.exit(2);
  }
}
main().catch((e) => { console.error(`\n  ✗ ${e.message}\n`); process.exit(1); });
