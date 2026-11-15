---
name: demo-capture
description: Capture deck- and doc-quality screenshots of a live web app or demo with Playwright - waiting for real content (not the loading shimmer), cropping nav and any region/host strings, dodging the tall-page duplicate-sidebar artifact, and re-capturing when the underlying data changed. Use whenever an artifact needs app screenshots. Encodes the stale-shot, half-render and crop lessons that repeatedly bit real builds. Self-contained.
---

# Capture demo-quality app screenshots

**Prerequisites (set up once):** a browser automation tool (Playwright + a Chromium browser is
the reference here; any equivalent works) and an image tool for cropping (Pillow, or the OS
tools). The app you're capturing must be running and reachable (local or deployed).

## Capture reliably
- Drive a headed/headless browser (Playwright) at a fixed size (1920x1080 for deck use). Log in
  with the app's own demo credentials, navigate to the route, trigger the state you want, then
  screenshot.
- **Wait for the REAL content to render, not the loading placeholder.** For anything AI-generated
  or async, wait on the actual result element (e.g. `.ai-answer`, the answer text, the populated
  table row) - NOT `networkidle` and NOT a fixed sleep. A screenshot taken during the
  "Working..." / shimmer / spinner state is the #1 stale-shot failure; you get a frozen
  placeholder instead of the answer.
- For a streamed/agentic UI, decide up front: capture MID-STREAM (steps + spinner + timer, to
  show "it's working") OR the completed state (the answer + any expand-the-trace) - and wait for
  the corresponding element before the shot.

## The tall-page duplicate-sidebar artifact
- Full-page screenshots of tall pages can trigger a Chromium stitching bug that DUPLICATES a
  fixed sidebar/header down the image. Mitigations: capture the viewport (or a bounded element)
  rather than `fullPage`, or crop the artifact out afterwards, or screenshot the content region
  by its selector. Always VIEW the result and re-take if the sidebar is duplicated.

## Crop for the artifact
- Crop the nav sidebar/switcher when it tightens the story and isn't the point.
- **Crop or neutralise any hosting-region / infra / host string** (footer, sidebar, URL bar,
  header pill) - a visible `aws-*` / zone / `*.cloud` string fails the artifact's region gate.
- **Anonymise other customers' names/identifiers**; blur stray real names or drop the shot.
- Never capture a real personal email/login or a real third-party brand used as if owned.
- For decks: give the final crop a thin neutral border + a subtle shadow + an 11pt muted caption.

## Stale-shot discipline (a repeat offender)
- Screenshots go stale the moment the app's data or logic changes. A figure captured before a fix
  will silently contradict the live product on the slide.
- **Before reusing ANY shot, verify its key figures against the live app/API** (query the endpoint
  or reload the page). If a number, verdict or state differs, RECAPTURE. Reset the demo to its
  clean seeded state first if the flow you're capturing depends on starting data.
- View every shot you keep at full size; discard anything half-rendered, placeholder, mismatched,
  or artifact-corrupted.

## Verify
- Every kept shot: real content (no shimmer), no region/host string, no real identifiers, no
  duplicated-sidebar artifact, figures current vs the live app, legible at slide/doc scale.
