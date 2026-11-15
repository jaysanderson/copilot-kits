---
mode: agent
description: Capture deck-quality screenshots of a live demo - real content, cropped host strings, stale-shot check, naming
---

# Capture shots

## Capture
1. Reset the demo to its seeded state first if the flow depends on starting data.
2. `python tools/shot.py --url <url> --out shots/<slug>/<route>-<state>-<width>.png`; 1920x1080 for decks, 390x844 for mobile. Add `--click "<selector>"` to trigger a state; `--auth` or `--session-storage` for logged-in apps.
3. Wait for the real result element (the answer text, the populated row), never `networkidle` or a fixed sleep. A shot of a spinner, shimmer or "Working..." state is discarded.
4. For a streamed answer decide up front: mid-stream (steps and timer) or completed (answer and sources). Wait for that element.
5. Prefer a viewport or element shot over `--full`. A full-page shot of a tall page can duplicate a fixed sidebar; if it does, retake.

## Crop and clean
6. Crop browser chrome, URL bar and any nav that is not the point.
7. Crop or neutralise every host, zone or region string (footer, header pill, URL). Grep the page text for `rag.progress.cloud`, `aws-`, `europe-` before keeping a shot.
8. Anonymise other customers' names. Drop any shot with a real personal email or login.
9. For decks: thin neutral border, subtle shadow, 11 pt muted caption.

## Stale-shot check
10. Before reusing any existing shot, reload the route or query the endpoint and compare the key figures. If any number, verdict or state differs, recapture. A stale figure is a FAIL.
11. View every kept shot at full size. Discard anything half-rendered, placeholder, mismatched or with a duplicated sidebar.

## Naming and report
- `shots/<slug>/<route>-<state>-<width>.png`, lower case, hyphens, no spaces. Mark the final set with a `FINAL-` prefix or a `shots/<slug>/ROUNDS.md` naming the current round.
- Report: a table of kept shots with route, state, width, the key figure shown, and the live value you compared it to.
