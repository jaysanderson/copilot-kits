---
name: grounded-artifact
description: The quality gate that makes any go-to-market artifact (deck, demo, video, blog, battle card, email, report) credible in a CIO/CMO/Solutions-Architect room instead of reading as generic AI. A runnable Definition-of-Pass checklist - verify every product claim against the knowledge base, hold the locked facts, no fabricated numbers, stat hygiene, a de-AI pass - walked line by line with PASS/FAIL and evidence. Use before ANY artifact is called done. Self-contained; adapt the locked-facts list to your own product.
---

# Grounded artifact - the credibility gate

Run EVERY deliverable through this before it ships. A reviewer walks each applicable line and
records an explicit **PASS or FAIL** with evidence attached ("a PASS without evidence is a
FAIL"). One FAIL on a truth or safety line = not done. The reviewer reports findings; the owner
fixes and re-gates.

## 1. Truth gates (apply to everything)
- **Every product claim traces to the knowledge base / an authoritative source.** Nothing from
  memory. Unconfirmable claims are flagged, never silently kept.
- **No fabricated numbers.** No invented accuracy %, adoption %, ROI figure or benchmark. Prove
  quality with real measured signals (e.g. groundedness scores, cited answers), never a made-up
  percentage. Demo figures are labelled as demo figures, on-slide, not as product performance.
- **Certifications only as verified** - name a specific cert (SOC 2 / ISO / etc.) only if verified
  outside the KB and only where the artifact needs it.
- **Locked facts hold everywhere** - keep a short LOCKED FACTS list (acquisition figures, analyst
  positions, headline stats) and use the exact same values across deck, video and posts. Analyst
  results stated precisely (e.g. a "Leader in X criterion" is not "a Leader overall"). Zero drift.
- **Statistics: authoritative independent sources, cited on-slide or in-text.** Vendor numbers
  labelled as vendor numbers. Anything older than ~5 years dated or replaced. Market sizing =
  named provider + range. NEVER the target account's direct competitor as a proof source.
- **Cross-artifact consistency** - every number matches the account brief / messaging house
  exactly, across every artifact in the kit.

## 2. Safety + hygiene gates
- No secrets/keys/tokens anywhere client-side or in any artifact.
- No hosting-region / infra string visible in any screenshot or view, checked against the
  customer's residency.
- Other customers' names and identifiers anonymised in every screenshot.
- No real third-party brand used as if owned; no real personal identifiers - fictional entities,
  neutral logins.
- All pricing in the agreed currency; no legible geo-localised price in a crop.
- Outbound = DRAFT until signed off; nothing publishes/sends without owner approval.

## 3. Language + voice gates
- The house spelling standard (e.g. AU English); no em dashes if that's the rule (spaced hyphen).
- Banned words absent (keep your own list - e.g. delve, leverage, unlock, seamless, game-changing).
- **De-AI pass**: remove hedging, filler, symmetrical triads, corporate fluff. First person,
  humble-practitioner, punchy where the voice calls for it.
- **The room test**: would this survive a CIO / CMO / Solutions-Architect room? If not, it's not
  finished.

## 4. Per-type gates
- **Decks**: exec discipline (<=25 words/slide, one idea, outcome-led titles, one clear ask);
  template path + safe fonts (no faked brand fonts); screenshots bordered/captioned/vertical-matched;
  the render-QA loop completed with every slide viewed.
- **Demo apps**: the demo table-stakes gates (seeded, own-system framing, one route per use case,
  cited answer reachable, no region strings, discreet synthetic disclosure, no real identifiers,
  polish, server-side-proxy round-trip, 30-second reset).
- **Videos**: script approved before recording; narration timed to playback; frames viewed at
  start/middle/end for defects.
- **Written content**: hook in line one for social; battle cards = claim/proof/trap/counter, each
  claim verified; blogs/one-pagers/emails consume the locked brief with no drift.

## 5. The evidence rule
A PASS is only a PASS with evidence attached: the rendered slide images viewed, the grep/scan
output for region strings and banned words, the KB query that confirmed a claim, the live
round-trip response, the screenshot cross-checked against the live app. "Looks fine" is a FAIL.

## Screenshot-currency check (a repeat offender)
Reused screenshots go stale - a figure that changed after a code/data fix will silently
contradict the live product. Before trusting any reused shot, verify its key figures against the
live app/API; recapture if they differ. A stale number in a screenshot is a FAIL.
