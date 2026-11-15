#!/usr/bin/env node
'use strict';

// GM standard 1 (17 Aug 2026): "no demo may ship rendering as the default
// Hero+Section skeleton, and the QA/lint should flag it." create-app.js reports
// this once at scaffold time (checkArchetypeDistinctness); this is the same
// check, standalone, so it re-runs on every deploy (module 4.5's
// scripts/deploy.sh calls this BEFORE flyctl deploy) - a builder can't scaffold
// clean, then let composition.tsx quietly rot back to nothing before shipping.
//
// Usage: node scripts/lint-composition.mjs [path-to-app-root]   (default: cwd)
// Exit 0 = pass, exit 1 = fail (loud, with a reason - never a silent narrow).

import { existsSync, readFileSync } from 'fs';
import { join, resolve } from 'path';

const appRoot = resolve(process.argv[2] || '.');
const compositionFile = join(appRoot, 'portal', 'src', 'demo', 'composition.tsx');

function fail(reason) {
  console.error(`\n  ✗ Anti-sameness gate FAILED: ${reason}\n`);
  console.error('  A demo without a bespoke composition.tsx renders the config-shell default');
  console.error('  (Hero + Section) — the documented root cause of estate sameness');
  console.error('  (demo-estate-audit.md Part D). Author a real Shell for the chosen');
  console.error('  archetype before this deploys.\n');
  process.exit(1);
}

if (!existsSync(compositionFile)) {
  fail('portal/src/demo/composition.tsx does not exist');
}

const src = readFileSync(compositionFile, 'utf8');
const meaningfulLines = src
  .split('\n')
  .map((l) => l.trim())
  .filter((l) => l && !l.startsWith('//') && !l.startsWith('*') && !l.startsWith('/*'));

if (!/export\s+(const|function)\s+Shell\b/.test(src) && !/Shell\s*[:=]/.test(src)) {
  fail('composition.tsx exists but does not export a Shell');
}

if (meaningfulLines.length < 20) {
  fail(`composition.tsx only has ${meaningfulLines.length} non-comment lines — too thin to be a real bespoke Shell`);
}

console.log(`  ✓ Anti-sameness gate passed — bespoke composition.tsx found (${meaningfulLines.length} lines).`);
process.exit(0);
