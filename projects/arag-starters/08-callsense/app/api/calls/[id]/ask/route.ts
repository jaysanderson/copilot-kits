import { NextRequest } from "next/server";
import { askResourceStream, getResourceFullText, scoreRemi } from "@/lib/arag";
import { isDeclinedAnswer } from "@/lib/confidence";

export const dynamic = "force-dynamic";

/**
 * Proxy a resource-scoped ask. Streams the upstream NDJSON straight back to
 * the browser unchanged (so the answer still renders incrementally) while
 * also tapping the same bytes server-side to capture the full answer text.
 * Once the upstream stream ends, this scores the finished answer against the
 * CITED RESOURCE'S FULL EXTRACTED TEXT BODY (fetched fresh, not the
 * accumulated retrieval-event paragraphs) with a real `/predict/remi` call
 * and appends one more NDJSON line - `{"item":{"type":"quality",...}}` - so
 * the client's confidence badge is a genuine REMi-derived read (standard
 * B34/B39), never a raw-score proxy.
 *
 * Why the full body and not the scored paragraphs: this is a short-record
 * corpus (one call per resource) queried via resource_filters, so every
 * question is already scoped to exactly one resource - `id`. A resource can
 * genuinely ground an answer through a sentence that never surfaces as a
 * scored paragraph in the retrieval event (CLAUDE.md relational-sync finding
 * #7); scoring against only those paragraphs can structurally omit the
 * grounding sentence and pin groundedness to 0 on a correct answer. Fetching
 * the resource's full extracted text sidesteps that failure mode entirely
 * instead of relying on the retrieval strategy happening to surface the
 * right paragraph. Best-effort and time-capped: the answer itself is never
 * held hostage by the scorer, and a scoring failure degrades silently (the
 * client falls back to its citation-coverage floor, never a visible error -
 * standard B38).
 */
export async function POST(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const { question } = await req.json();
  if (!question || typeof question !== "string") {
    return new Response(JSON.stringify({ error: "question required" }), { status: 400 });
  }

  const upstream = await askResourceStream(id, question);
  if (!upstream.body || !upstream.ok) {
    return new Response(upstream.body, {
      status: upstream.status,
      headers: { "content-type": "application/x-ndjson; charset=utf-8", "cache-control": "no-store" },
    });
  }

  const encoder = new TextEncoder();
  const decoder = new TextDecoder();

  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const reader = upstream.body!.getReader();
      let buf = "";
      let fullAnswer = "";
      let citedRangeCount = 0; // marker-bearing citations seen in the stream

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done || !value) break;
          controller.enqueue(value); // unchanged passthrough - client streaming UX is untouched
          buf += decoder.decode(value, { stream: true });
          const lines = buf.split("\n");
          buf = lines.pop() ?? "";
          for (const line of lines) {
            const t = line.trim();
            if (!t) continue;
            let obj: any;
            try { obj = JSON.parse(t); } catch { continue; }
            const item = obj.item ?? obj;
            if (item.type === "answer") {
              fullAnswer += item.text ?? "";
            } else if (item.type === "citations") {
              // Same filter the client renders markers from: a field-level
              // key ("/" present) carrying at least one answer range.
              const cmap: Record<string, [number, number][]> = item.citations ?? {};
              citedRangeCount = Object.entries(cmap).filter(
                ([key, ranges]) => key.includes("/") && (ranges ?? []).length > 0
              ).length;
            }
          }
        }
      } catch {
        // Upstream read failed mid-stream - still close cleanly below rather
        // than leave the client's reader hanging.
      }

      // Never score (or badge) a decline - REMi rates the retrieved context's
      // topical relevance to the question, not whether the model actually
      // answered, so it can score a genuine refusal as "High confidence"
      // (found live by demo-tester, reproduced 2/2). Skipping the call here
      // also means a decline never pays for a REMi round-trip it can't use.
      //
      // Also never score an answer with ZERO marker-bearing citations - the
      // badge may never read High/Moderate over an answer showing no visible
      // citation markers (demo-tester, 1 Oct 2026: metadata-synthesized
      // answers like "Was the member satisfied?" came back uncited, REMi
      // scored them 5/5, badge read High - 4/4 reproduction). The client
      // gates this too (lib/confidence.ts), but withholding the quality
      // event server-side is the stronger guarantee - no consumer of the
      // NDJSON stream ever sees a scoring input the UI would have to
      // suppress - and it saves a pointless REMi round-trip.
      if (fullAnswer.trim() && !isDeclinedAnswer(fullAnswer) && citedRangeCount > 0) {
        try {
          const fullText = await getResourceFullText(id);
          if (fullText.trim()) {
            const quality = await Promise.race([
              scoreRemi(question, fullAnswer, [fullText]),
              new Promise<null>((resolve) => setTimeout(() => resolve(null), 12000)),
            ]);
            if (quality) {
              controller.enqueue(encoder.encode(`${JSON.stringify({ item: { type: "quality", ...quality } })}\n`));
            }
          }
        } catch {
          // REMi unreachable, or the full-text fetch failed - skip silently,
          // client keeps its citation-coverage floor
        }
      }
      controller.close();
    },
  });

  return new Response(stream, {
    status: upstream.status,
    headers: { "content-type": "application/x-ndjson; charset=utf-8", "cache-control": "no-store" },
  });
}
