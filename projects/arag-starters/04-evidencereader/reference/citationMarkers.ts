// ─────────────────────────────────────────────────────────────────────────────
// Standard B33 — inline citation markers AT THE CLAIM, not listed in a block
// underneath. Reuses the estate-wide pattern (CLAUDE.md systemic finding 1,
// the VR server-side `[[n]]` injection): match each citation's own retrieved
// excerpt against the sentence in the answer it actually supports, and stamp
// a small superscript marker there — never a guess, never every sentence.
//
// This runs CLIENT-SIDE, after the answer has finished streaming and the full
// citation set is known (never mid-stream — a marker placed against a partial
// answer/citation set would be a guess dressed as ground truth). It is a
// best-effort match: a citation with no confident textual overlap against any
// sentence gets NO marker rather than a wrong one. That is the deliberate
// trade-off — an answer with a couple of unmarked (but still listed-below)
// sources is honest; a marker on the wrong sentence is not.
// ─────────────────────────────────────────────────────────────────────────────

const STOPWORDS = new Set([
  'the', 'a', 'an', 'and', 'or', 'but', 'of', 'to', 'in', 'on', 'for', 'with',
  'is', 'are', 'was', 'were', 'that', 'this', 'it', 'its', 'as', 'at', 'by',
  'from', 'their', 'they', 'be', 'has', 'have', 'had', 'not', 'than', 'into',
  'what', 'which', 'who', 'been', 'will', 'does', 'did', 'about', 'over',
]);

function tokenize(s: string): string[] {
  return (s.toLowerCase().match(/[a-z0-9']+/g) || []).filter((w) => w.length > 2 && !STOPWORDS.has(w));
}

// Split on sentence-ending punctuation while keeping it attached. Deliberately
// naive (this is prose from a streamed answer, not arbitrary markdown).
function splitSentences(text: string): string[] {
  const parts = text.match(/[^.!?]+[.!?]*(\s+|$)/g);
  return (parts || [text]).map((s) => s.trim()).filter(Boolean);
}

// A word every citation shares (the brand name, the product, a common verb)
// is worthless for telling citations apart — without down-weighting it, every
// citation piles onto whichever sentence happens to repeat that one common
// word, which is exactly the "all six markers stacked on sentence one" defect
// found live testing this. Down-weight by how many citations a word appears
// in (a cheap inverse-document-frequency), so a match only counts for much
// when the shared word is actually distinctive to that citation.
function buildWordWeights(citeTokenSets: Set<string>[]): Map<string, number> {
  const df = new Map<string, number>();
  for (const set of citeTokenSets) {
    for (const w of set) df.set(w, (df.get(w) || 0) + 1);
  }
  const n = citeTokenSets.length || 1;
  const weights = new Map<string, number>();
  for (const [w, count] of df) weights.set(w, Math.log(1 + n / count));
  return weights;
}

// Weighted cosine similarity between the sentence and the citation excerpt,
// restricted to the vocabulary that actually matters (only words the citation
// set shares get a weight at all). Cosine — not "fraction of the citation
// covered" — deliberately: a long citation excerpt (a full trademark filing,
// legal boilerplate and all) shouldn't be marked down just because most of
// its bulk goes unechoed in a short generated sentence; what matters is
// whether the WORDS THAT DO OVERLAP are a confident, distinctive match.
function overlapScore(sentenceTokens: string[], citeTokens: Set<string>, weights: Map<string, number>): number {
  if (!sentenceTokens.length || !citeTokens.size) return 0;
  const sentenceSet = new Set(sentenceTokens);
  let dot = 0;
  let citeNormSq = 0;
  let sentenceNormSq = 0;
  for (const w of citeTokens) {
    const wt = weights.get(w) || 0;
    citeNormSq += wt * wt;
    if (sentenceSet.has(w)) dot += wt * wt;
  }
  for (const w of sentenceSet) {
    const wt = weights.get(w) || 0; // 0 for a word no citation shares — irrelevant to this comparison
    sentenceNormSq += wt * wt;
  }
  if (citeNormSq <= 0 || sentenceNormSq <= 0) return 0;
  return dot / Math.sqrt(citeNormSq * sentenceNormSq);
}

const MATCH_THRESHOLD = 0.3;
const MIN_CITATION_SIGNAL = 3; // fewer than 3 meaningful words = too little to match on
const MAX_MARKERS_PER_SENTENCE = 3; // never let every citation pile onto one short sentence

export interface MarkerSource {
  index: number;
  text: string | null | undefined;
}

/**
 * Only ever ADDS `<sup>` markers to plain prose — never rewrites content, so
 * it's safe to run before markdown parsing. A block that already looks like
 * markdown structure (heading, list item, table row, code fence) is left
 * completely untouched, so a naive sentence split can never corrupt syntax.
 */
export function insertCitationMarkers(answer: string, citations: MarkerSource[]): string {
  if (!answer || !citations?.length) return answer;

  const citeTokenSets = citations
    .map((c) => ({ index: c.index, tokens: new Set(tokenize(c.text || '')) }))
    .filter((c) => c.tokens.size >= MIN_CITATION_SIGNAL);
  if (!citeTokenSets.length) return answer;
  const weights = buildWordWeights(citeTokenSets.map((c) => c.tokens));

  // Process paragraph by paragraph so a marker never crosses a blank-line
  // boundary into unrelated text, and structural lines are skipped whole.
  const blocks = answer.split(/\n{2,}/);
  const processed = blocks.map((block) => {
    const trimmed = block.trim();
    const isStructural =
      /^#{1,6}\s/.test(trimmed) ||
      /^[-*+]\s/.test(trimmed) ||
      /^\d+\.\s/.test(trimmed) ||
      /^\|/.test(trimmed) ||
      /```/.test(trimmed) ||
      trimmed.length === 0;
    if (isStructural) return block;

    const sentences = splitSentences(block);
    if (sentences.length === 0) return block;
    const sentenceTokens = sentences.map(tokenize);

    const bySentence = new Map<number, { index: number; score: number }[]>();
    for (const cite of citeTokenSets) {
      let bestIdx = -1;
      let bestScore = 0;
      sentenceTokens.forEach((toks, si) => {
        const score = overlapScore(toks, cite.tokens, weights);
        if (score > bestScore) {
          bestScore = score;
          bestIdx = si;
        }
      });
      if (bestIdx >= 0 && bestScore >= MATCH_THRESHOLD) {
        const arr = bySentence.get(bestIdx) || [];
        arr.push({ index: cite.index, score: bestScore });
        bySentence.set(bestIdx, arr);
      }
    }

    if (bySentence.size === 0) return block;

    return sentences
      .map((s, i) => {
        const marks = bySentence.get(i);
        if (!marks) return s;
        // Cap per sentence so a short answer can't pile every citation onto
        // one line — keep only the strongest-matching few.
        const uniq = Array.from(new Set(marks.sort((a, b) => b.score - a.score).slice(0, MAX_MARKERS_PER_SENTENCE).map((m) => m.index))).sort(
          (a, b) => a - b
        );
        const trailingSpace = /\s$/.test(s) ? ' ' : '';
        const core = s.trimEnd();
        const markup = uniq
          .map((n) => `<sup class="cite-mark" data-cite="${n}" role="button" tabindex="0" aria-label="Open source ${n}">${n}</sup>`)
          .join('');
        return core + markup + trailingSpace;
      })
      .join('');
  });

  return processed.join('\n\n');
}
