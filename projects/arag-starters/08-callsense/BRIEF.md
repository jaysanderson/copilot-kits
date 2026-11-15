# BRIEF: CallSense (day 8 of the series)

> "Hundreds of recorded calls a month and the only person who knows what customers are saying is the one who was on the call."

**Who shares this.** Sales leader, customer success lead.

**Promise.** Upload the recordings. Ask what customers are actually saying. Get answers with the timestamp to prove it.

**The one job.** A calls explorer with categories, a per-call ask with timestamps, a dashboard of themes, and (new) upload through the app.

**Why ARAG is load-bearing.** Native audio ingestion and transcription through `/upload`; per-call `/ask` scoped with resource filters; REMi confidence (`lib/confidence.ts`); category labelsets via `/labelsets`. Remove ARAG and this is a transcript search box.

**Base.** The app is the Next.js call-analysis demo, copied whole (minus node_modules, media, staging env files). Explorer, per-call ask, confidence and dashboard already work. Nothing that already works is rewritten.

**Knowledge Box.** New KB; recordings uploaded through the app. Writer token.

**Finishing steps, in order (one Copilot chat each).**
1. Identity purge: `grep -rniE "insur|dental|medicare|enrol" .` and make the category set generic (`lib/calls.ts`); fictional callers only.
2. Recordings: the source demo's mp4 files were excluded on purpose (size). Record or generate five short synthetic calls (text to speech is fine) and upload them.
3. Upload: add `app/api/upload/route.ts` streaming the file to `/upload`; list state until PROCESSED.
4. Keep explorer, per-call ask, dashboard. `npm install` first; secrets in `.env.local` (gitignored).
5. Brand from `brand/`; footer disclosure that calls are synthetic.

**Done when** (these lines are section 0 of `STANDARD.md`; every (B) line there must also be done):
- Five recordings uploaded through the app, transcribed, categorised.
- One question across calls answered with timestamps that open the moment.
- Confidence badge present on every answer; no raw numeral.
- 390 px render clean.

**Deliberately not built (the article's "where to take it next").**
- Call libraries per team
- Speaker tags and talk-time
- Push themes to the CRM

**Copilot prompts.** `/finish-starter` for each step above, `/qa-gate` at the end, `/write-article` last. Cheapest model for renames and copy; the premium model only for the step marked hardest in `README.md`.

**Token rule.** Copy from `reference/` and the chassis; never generate a client, a renderer or a Dockerfile. If a step needs a mechanism not confirmed in `.github/instructions/arag-api.instructions.md` or `reference/arag-platform-quirks.md`, stop and flag it; do not invent an endpoint.
