# Progress Agentic RAG - Field Portal intro video

**Status:** VO script LOCKED (2026-08-31). Render on HOLD until the Kitforge sidebar
branding fix lands (logo lockup + "How this portal works" nav label). Re-scout for zero
Kitforge in-frame, then shoot-and-cut.

**Audience:** Progress SEs and sellers already working Progress Agentic RAG. Register:
confident, professional, internal enablement. Frame: THEIR field portal.

**Production:** narration-only (NO music bed), single voice **Hope**
(voice_id WZlYpi1yf6zJhNWXih74), eleven_multilingual_v2 for long-form stability.
1920x1080, EBU R128 -14 LUFS, stereo 48k. AU English, no em dashes, no banned words.
Target ~2:00-2:10.

**Login for capture:** navigate to the app, account picker -> click "Quinton" (Seller),
password pre-filled -> "Log in". Warm-up nav first. Start visible footage INSIDE the
logged-in workspace (workspace name reads "Progress Agentic RAG"). NEVER show the
account-picker / any Kitforge lockup.

**Leave OUT of frame:** the asset-detail "Brief" panel and the "Work Queue" breadcrumb
(use a Demo asset with no brief, or scope asset-detail to header + Lifecycle/Approval +
Delivery). No other-customer names/logos, no region/host strings, no ARAG endpoint names.

---

## LOCKED narration (spoken text is canon)

**B1 - HOOK** (~8s) - screen: Ask the Archive, question typed, cited answer landing.
> How do we beat Elastic on pricing predictability? Ask your field portal, and it answers.
> Grounded in your own material, every claim cited. This is the home for selling Progress
> Agentic RAG.

**B2 - PROBLEM** (~15s) - screen: home "Hi Quinton - what's the deal?" + Browse-for-your-deal facets.
> Every seller knows the hunt. The right deck is buried in someone's inbox, the battlecard
> is three versions old, and you are not sure it is even cleared to send. This portal fixes
> that. One governed library. Everything on brand, everything current.

**B3 - FIND FAST** (~20s) - screen: home facets, then Asset Library meaning-search + type/collection facets.
> So start with your deal. Browse by your prospect's industry, by who you are selling to,
> by where the deal sits. Or open the asset library and search by meaning, not just
> keywords. Decks, one-pagers, videos, demos, filtered by play, vertical, persona and
> stage. You find the right asset in seconds.

**B4 - ASK THE BOX (hero)** (~22s) - screen: #/ask, type a seller question, grounded answer + cited sources + relevance badge. ANCHOR: "The answer comes back" lands as the answer renders.
> When you would rather just ask, ask the archive. Put your question in plain language.
> The answer comes back written from your governed assets, with the sources listed
> underneath, and a relevance rating you can trust. No hunting. The proof and the source,
> in one place.

**B5 - TRUST / GOVERNANCE (proof)** (~20s) - screen: a Demo/Presentation asset detail; header (published + Added date), CLEARANCE Cleared, Lifecycle & Approval, then Delivery/Download.
> And you can trust what you grab. Every asset shows its status, the date it was added, and
> whether it is cleared for outbound. Behind it sits an approval lifecycle. Draft, review,
> approved, published. When it is ready, download the real file or copy a link. On brand,
> and ready to send.

**B6 - COMPETE** (~16s) - screen: #/battlecards grid, confidence badges, "Site changed" flag; brief hover on a card.
> For a competitive deal, open the battlecards. Real intelligence on the names you meet,
> the hyperscalers, the search incumbents, the specialists, each with a confidence rating.
> And when a rival changes their site, the card flags it. So you are never briefing from
> yesterday.

**B7 - ENABLEMENT + DEMO ESTATE** (~18s) - screen: Pricing & ROI glimpse, sales-stage objection content, then Asset Library "Demo kits" tab / open a per-vertical demo.
> The enablement is here too. Objection handling, discovery, pricing and value. And when a
> prospect wants to see it work, open a live demo from the estate, matched to their
> industry. If something is genuinely missing, request it.

**B8 - CTA + DEAL MAP close** (~15s) - screen: #/map interactive graph re-centres; hold on the graph for the close.
> It all connects on the deal map. Competitors, verticals, personas and assets, in one
> view. This is your field portal for Progress Agentic RAG. Open it before your next call,
> and walk in with the right answer already in hand.

---

## Shot list (shoot order = beat order; record generously, trim heads to anchors)

| Beat | Route | On-screen action | Notes / anchor |
|---|---|---|---|
| B1 | #/ask | type "How do we beat Elastic on pricing predictability?" (type delay 55), submit, hold on answer+sources | hero-ish; open cold on the answer for the hook |
| B2 | # (home) | land on "Hi Quinton", hold; reveal Browse-for-your-deal facets | no scroll jolt; single settle |
| B3 | # -> #/library | facets on home, then Library: type a meaning query, show type tabs + collection facets | type on camera (delay), don't over-scroll |
| B4 | #/ask | type a second seller question (e.g. "Which demo should I show a manufacturing prospect?"), submit | ANCHOR phrase "The answer comes back", lead 1.0, explicit `at` = measured answer-render frame; push in on the cited sources + relevance badge |
| B5 | #/library -> asset detail (Demo asset, no brief) | open asset, hold on header (published + Added date + Cleared), Lifecycle & Approval, Delivery/Download | keep Brief panel + "Work Queue" breadcrumb OUT of frame |
| B6 | #/battlecards | land on grid, hover one card; frame a "Site changed" flag + confidence badge | anonymise nothing needed (competitors are the subject); no region strings |
| B7 | #/pricing then #/library Demo tab | glimpse Pricing & ROI, then Library Demo-kits tab, open a vertical demo card | "request it" is the single half-line only |
| B8 | #/map | let graph render, click a node to re-centre, hold | close hero; confirm renders clean + zero Kitforge before using |

## Title + end card (Progress-branded, via assemble.py brand cards)
- Title card: "Your Progress Agentic RAG field portal" (Progress Sans Display, brand palette).
- End card: "Open it before your next call." + Progress Agentic RAG lockup.

## QA checklist (from video-production skill)
- Leak scan (selftest first): no ARAG_* / rag.progress.cloud / region strings / JWT / "Kitforge" / "Knowledge Box" / "nuclia" / /ask /find /graph endpoint names / other-customer names on screen.
- VO-only: silencedetect (-45dB/0.4s) shows real gaps in narration pauses; -14 LUFS +/-0.5; stereo 48k; no head silence; explicit -map 0:a:0 to confirm single audio track / no music bed.
- Per-beat sync gap measured in the finished file (screen leads voice 0-3.5s), esp. B4.
- View frames start/middle/end + at each proof-beat name.
- AU English, no em dashes, no banned words (delve, leverage, unlock, seamless, game-changing).
