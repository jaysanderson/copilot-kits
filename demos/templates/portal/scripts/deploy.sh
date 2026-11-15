#!/usr/bin/env bash
# Module 4.5 (flagship rebuild): wires the QA gate INTO the deploy loop instead
# of leaving it a manual step run after the fact. Run from the app root
# (alongside fly.toml / portal/fly.toml, demo.config.json, qa_flow.json).
#
#   scripts/deploy.sh
#
# Any FAIL exits non-zero and stops here - a red gate is never discovered
# later by a reviewer opening the live URL cold (CLAUDE.md's binding
# independent-QA-gate rule, 8 Aug 2026).
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

echo "== Module 4.5: pre-deploy gates =="

echo "-- Anti-sameness gate (GM standard 1, 17 Aug 2026) --"
node scripts/lint-composition.mjs "$APP_DIR"

echo "-- Deploying --"
if [ -f fly.toml ]; then
  flyctl deploy
elif [ -f portal/fly.toml ]; then
  (cd portal && flyctl deploy)
else
  echo "No fly.toml found (checked $APP_DIR and $APP_DIR/portal) - cannot deploy." >&2
  exit 1
fi

echo "-- Independent functional QA gate (scripts/demo_qa_gate.py) --"
PYTHON_BIN="${PYTHON_BIN:-python3}"
CONFIG_FILE="demo.config.json"
[ -f "$CONFIG_FILE" ] || CONFIG_FILE="portal/demo.config.json"
INTERACTIONS_FLAG=()
[ -f qa_flow.json ] && INTERACTIONS_FLAG=(--interactions qa_flow.json)

"$PYTHON_BIN" scripts/demo_qa_gate.py \
  --app-dir "$APP_DIR" \
  --config "$CONFIG_FILE" \
  "${INTERACTIONS_FLAG[@]}" \
  --json qa_gate_report.json

echo "== All pre-ship gates passed =="
