#!/usr/bin/env node
'use strict';

// ─────────────────────────────────────────────────────────────────────────────
// GM binding standard 5 (17 Aug 2026): a mandatory pre-build research phase.
//
// PHASE 2 IMPLEMENTATION (real, not the Phase 1 stub). What a static Node
// script genuinely cannot do is go read the web itself - the actual research
// (real vocabulary, real workflow shapes, real document examples) is gathered
// by the builder using real search/fetch tools BEFORE calling this script.
// This script's real job: take that research as structured input, validate it
// is genuinely substantive (not a thin placeholder), and emit two artifacts
// the rest of the pipeline consumes:
//   - <out>.md   - a human-readable research brief (for the README / brief)
//   - <out>.json - a machine-readable version scripts/generate-corpus.mjs
//                  reads directly when building the seeded corpus, and that
//                  demo.config.json's researchPhase.status references.
//
// Usage:
//   node scripts/research-vertical.mjs --vertical "wealth management compliance" \
//        --input research/wealth-mgmt-compliance.input.json \
//        --out research/wealth-mgmt-compliance
//
// Input JSON shape (all sections required, each must clear a minimum bar so a
// thin/generic stub can't sneak through):
// {
//   "vocabulary": ["term", ...],                 // >= 12 real, vertical-specific terms
//   "workflows": [{ "name": "...", "steps": ["...", ...] }, ...],   // >= 3, each >= 3 steps
//   "docTypes": ["...", ...],                     // >= 5 real document/data types
//   "roles": [{ "title": "...", "seniority": "...", "asks": ["...", ...] }, ...], // >= 3
//   "edgeCases": ["...", ...],                    // >= 5 lived-in imperfections
//   "entities": { "<kind>": ["...", ...], ... },  // named recurring entities to reuse in corpus
//   "sources": ["...", ...]                       // >= 2 real sources the research drew on
// }
// ─────────────────────────────────────────────────────────────────────────────

import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

function parseArgs(argv) {
  const a = {};
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === '--vertical') a.vertical = argv[++i];
    else if (argv[i] === '--input') a.input = argv[++i];
    else if (argv[i] === '--out') a.out = argv[++i];
  }
  return a;
}

const MIN = {
  vocabulary: 12,
  workflows: 3,
  workflowSteps: 3,
  docTypes: 5,
  roles: 3,
  roleAsks: 2,
  edgeCases: 5,
  sources: 2,
};

function fail(msg) {
  console.error(`\n  ✗ ${msg}\n`);
  process.exit(1);
}

function validate(vertical, data) {
  const errs = [];
  const need = (cond, msg) => { if (!cond) errs.push(msg); };

  need(Array.isArray(data.vocabulary) && data.vocabulary.length >= MIN.vocabulary,
    `vocabulary needs >= ${MIN.vocabulary} real terms (got ${data.vocabulary?.length ?? 0})`);
  need(Array.isArray(data.workflows) && data.workflows.length >= MIN.workflows,
    `workflows needs >= ${MIN.workflows} entries (got ${data.workflows?.length ?? 0})`);
  (data.workflows || []).forEach((w, i) => {
    need(w && typeof w.name === 'string' && w.name.length > 0, `workflows[${i}] missing a name`);
    need(Array.isArray(w?.steps) && w.steps.length >= MIN.workflowSteps,
      `workflows[${i}] ("${w?.name || '?'}") needs >= ${MIN.workflowSteps} real steps`);
  });
  need(Array.isArray(data.docTypes) && data.docTypes.length >= MIN.docTypes,
    `docTypes needs >= ${MIN.docTypes} real document/data types (got ${data.docTypes?.length ?? 0})`);
  need(Array.isArray(data.roles) && data.roles.length >= MIN.roles,
    `roles needs >= ${MIN.roles} named-role personas (got ${data.roles?.length ?? 0})`);
  (data.roles || []).forEach((r, i) => {
    need(r && typeof r.title === 'string' && r.title.length > 0, `roles[${i}] missing a title`);
    need(Array.isArray(r?.asks) && r.asks.length >= MIN.roleAsks,
      `roles[${i}] ("${r?.title || '?'}") needs >= ${MIN.roleAsks} realistic things they'd actually ask`);
  });
  need(Array.isArray(data.edgeCases) && data.edgeCases.length >= MIN.edgeCases,
    `edgeCases needs >= ${MIN.edgeCases} realistic imperfections/edge cases (got ${data.edgeCases?.length ?? 0})`);
  need(data.entities && typeof data.entities === 'object' && Object.keys(data.entities).length >= 2,
    `entities needs >= 2 named-entity kinds (e.g. people, accounts, products) with real-sounding names`);
  need(Array.isArray(data.sources) && data.sources.length >= MIN.sources,
    `sources needs >= ${MIN.sources} real sources the research actually drew on (got ${data.sources?.length ?? 0})`);

  // Reject generic/placeholder-flavoured vocabulary - a cheap sniff test, not
  // a substitute for a human/agent judgement call, but catches the laziest
  // failure mode (AI-product words standing in for the vertical's own jargon).
  const banned = ['ai-powered', 'seamless', 'cutting-edge', 'game-changing', 'unlock', 'leverage', 'delve'];
  const flatVocab = (data.vocabulary || []).join(' ').toLowerCase();
  banned.forEach((b) => { if (flatVocab.includes(b)) errs.push(`vocabulary contains AI-marketing-flavoured term "${b}" - use the vertical's own real jargon instead`); });

  return errs;
}

function renderMarkdown(vertical, data) {
  const lines = [];
  lines.push(`# Vertical research brief - ${vertical}`);
  lines.push('');
  lines.push(`Generated by \`scripts/research-vertical.mjs\` (Standard B5, GM directive 17 Aug 2026).`);
  lines.push(`This is the researched-not-improvised basis for the seeded demo corpus - every`);
  lines.push(`document, name and edge case in the seeded content should trace back to something here.`);
  lines.push('');
  lines.push('## Real vocabulary and jargon');
  lines.push(data.vocabulary.map((v) => `- ${v}`).join('\n'));
  lines.push('');
  lines.push('## Real workflows');
  data.workflows.forEach((w) => {
    lines.push(`### ${w.name}`);
    lines.push(w.steps.map((s, i) => `${i + 1}. ${s}`).join('\n'));
    lines.push('');
  });
  lines.push('## Document / data types genuinely produced in this vertical');
  lines.push(data.docTypes.map((d) => `- ${d}`).join('\n'));
  lines.push('');
  lines.push('## Named-role personas - what they would actually ask');
  data.roles.forEach((r) => {
    lines.push(`### ${r.title}${r.seniority ? ` (${r.seniority})` : ''}`);
    lines.push(r.asks.map((a) => `- "${a}"`).join('\n'));
    lines.push('');
  });
  lines.push('## Realistic edge cases and imperfections (the lived-in texture standard)');
  lines.push(data.edgeCases.map((e) => `- ${e}`).join('\n'));
  lines.push('');
  lines.push('## Recurring named entities (reuse these across the seeded corpus)');
  Object.entries(data.entities).forEach(([kind, list]) => {
    lines.push(`- **${kind}**: ${(list || []).join(', ')}`);
  });
  lines.push('');
  lines.push('## Sources this research drew on');
  lines.push(data.sources.map((s) => `- ${s}`).join('\n'));
  lines.push('');
  return lines.join('\n');
}

function main() {
  const { vertical, input, out } = parseArgs(process.argv);
  if (!vertical) fail('--vertical "<name>" is required (must match the value passed to create-app.js --vertical).');
  if (!input) fail('--input <path-to-research.json> is required - see this file\'s header for the schema. Gather the real research first (web search / real sources), write it as JSON, then run this script to validate + render it.');
  if (!existsSync(input)) fail(`--input file not found: ${input}`);
  if (!out) fail('--out <path-without-extension> is required (writes <out>.md and <out>.json).');

  let data;
  try {
    data = JSON.parse(readFileSync(input, 'utf8'));
  } catch (e) {
    fail(`--input is not valid JSON: ${e.message}`);
  }

  const errs = validate(vertical, data);
  if (errs.length) {
    console.error(`\n  ✗ Research input for "${vertical}" is not substantive enough yet:\n`);
    errs.forEach((e) => console.error(`    - ${e}`));
    console.error('\n  This gate exists so a placeholder corpus never ships under the "researched" label.\n');
    process.exit(1);
  }

  const outDir = dirname(resolve(out));
  if (!existsSync(outDir)) mkdirSync(outDir, { recursive: true });

  const md = renderMarkdown(vertical, data);
  writeFileSync(`${out}.md`, md, 'utf8');
  writeFileSync(`${out}.json`, JSON.stringify({ vertical, ...data }, null, 2), 'utf8');

  console.log(`\n  ✓ Research brief validated and written for "${vertical}":`);
  console.log(`    ${out}.md   (human-readable brief)`);
  console.log(`    ${out}.json (consumed by scripts/generate-corpus.mjs)`);
  console.log(`\n  Vocabulary: ${data.vocabulary.length}  Workflows: ${data.workflows.length}  DocTypes: ${data.docTypes.length}`);
  console.log(`  Roles: ${data.roles.length}  EdgeCases: ${data.edgeCases.length}  Sources: ${data.sources.length}\n`);
}

main();
