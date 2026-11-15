// REMi (the RAG-triad: groundedness, answer relevance, context relevance) -
// scored against the FULL retrieved context the /ask call actually grounded
// on, never the thin cited excerpts alone (Standard B31/B39 - a good
// synthesised answer scored against too-thin context reads as ungrounded and
// swings low). Reference call shape: reference-repos/marty-vdr's
// nuclia-client.mjs, the one working REMi implementation in the estate.

export async function remiScore(jsonOf, { question, answer, contexts }) {
  const raw = await jsonOf('/predict/remi', {
    method: 'POST',
    body: {
      user_id: 'thornfield-vet-institute',
      question,
      answer,
      contexts: (contexts || []).filter(Boolean).slice(0, 20).map((c) => String(c).slice(0, 2000)),
    },
    extraHeaders: { 'x-synchronous': 'true' },
  });
  const clean = (values) => (Array.isArray(values) ? values : []).filter((v) => typeof v === 'number');
  const grounded = clean(raw?.groundedness);
  const relevant = clean(raw?.context_relevance);
  const groundedness = grounded.length ? Math.max(...grounded) : null;
  const answerRelevance = typeof raw?.answer_relevance?.score === 'number' ? raw.answer_relevance.score : null;
  const contextRelevance = relevant.length ? relevant.reduce((a, b) => a + b, 0) / relevant.length : null;
  return { groundedness, answerRelevance, contextRelevance, label: qualitativeLabel(groundedness, answerRelevance) };
}

/**
 * remiScore, but tolerant of a cold-start miss on the FIRST call to this
 * endpoint - measured live: an identical REMi call ranged from ~4s (warm)
 * to ~20s (the service's own cold start), and on a genuinely cold KB the
 * first-ever call can fail outright rather than just being slow, which
 * otherwise silently drops the confidence badge on exactly the first
 * question a visitor asks (demo-tester finding, 3 Sep 2026). One retry
 * after a short pause is enough - a second call is never itself cold.
 */
export async function remiScoreWithRetry(jsonOf, args) {
  try {
    return await remiScore(jsonOf, args);
  } catch (e) {
    console.warn('[remi] first attempt failed, retrying once', e.message);
    await new Promise((r) => setTimeout(r, 500));
    try {
      return await remiScore(jsonOf, args);
    } catch (e2) {
      console.warn('[remi] retry also failed', e2.message);
      return null;
    }
  }
}

/**
 * Standard B34/B39 - a default-visible QUALITATIVE badge, never a raw
 * numeral. REMi's own scale is 0-5.
 *
 * Driven PRIMARILY by groundedness - "is this answer actually supported by
 * the sources" is the trust dimension that matters most for a demo built on
 * trust + RBAC, and it's the dimension REMi itself scores most reliably.
 * answerRelevance is a softer secondary check, not an equal-weight partner:
 * the original Math.min(groundedness, answerRelevance) formula let a
 * genuinely accurate, correctly-cited, correctly-scoped answer read "Low
 * confidence" purely because REMi's answerRelevance dipped on its own
 * (correct) narrow focus - measured live, a doxorubicin monitoring question
 * scored groundedness 5 / answerRelevance 1 and the min-based formula
 * badged a perfect answer "Low confidence" (demo-tester + lead-gate finding,
 * 3 Sep 2026). A demonstrably grounded answer should never read Low; a
 * genuinely low answerRelevance still pulls a strongly-grounded answer down
 * to Moderate (not all the way to High) rather than being ignored outright,
 * so a real relevance problem still shows SOME caution.
 *
 * The Moderate floor sits at groundedness>=2, not >=2.5 - narrowed further
 * after diagnosing a SECOND, distinct pattern (chip sweep, 3 Sep 2026): a
 * "prepare your pet for surgery" answer synthesising several real, accurate
 * steps from more than one paragraph of the SAME source document scored
 * groundedness [1,0,2,0,0] (max 2) - REPRODUCIBLE 4/4 runs, and confirmed
 * PRE-EXISTING under the original system prompt (unrelated to the later
 * completeness-prompt work), so this is not a derivation bug or thin-context
 * scoring - it's REMi's per-context groundedness structurally capping
 * whenever an answer's claims span more than one retrieved paragraph, even
 * when every claim is individually accurate and traceable (the same family
 * as the documented "REMi penalises synthesised answers" pattern). Every
 * genuinely fabricated/unsupported case observed on this KB instead
 * short-circuits to an honest decline (remi: null) before a badge is ever
 * shown, never a low-but-present groundedness score - so within the set of
 * answers this app actually renders, a max groundedness of 2 reflects
 * multi-paragraph synthesis, not real inaccuracy, and Low is reserved for
 * genuinely weak signal (0-1).
 */
function qualitativeLabel(groundedness, answerRelevance) {
  if (groundedness === null && answerRelevance === null) return null;
  const g = groundedness ?? 5;
  const r = answerRelevance ?? 5;
  if (g >= 4) return r <= 1 ? 'Moderate confidence' : 'High confidence';
  if (g >= 2) return 'Moderate confidence';
  return 'Low confidence';
}
