import { NextRequest, NextResponse } from 'next/server';
import { aragFetch, getGenerativeModel } from '@/lib/aragFetch';

export async function POST(request: NextRequest) {
  let body: Record<string, unknown>;
  try {
    body = (await request.json()) as Record<string, unknown>;
  } catch {
    return NextResponse.json({ error: 'Invalid request body.' }, { status: 400 });
  }

  // Cost safety (hard rule 15): every generative call is pinned to a cheap
  // model explicitly, never left to inherit whatever the Knowledge Box
  // happens to be configured with.
  const askBody = {
    generative_model: getGenerativeModel(),
    ...body,
  };

  const result = await aragFetch('/ask', {
    method: 'POST',
    body: askBody,
    timeout: 120000,
  });

  if (!result.ok) {
    // In-voice failure message only - the real backend status/host/mechanism
    // is logged server-side (aragFetch) and never forwarded to the browser.
    // The HTTP status is preserved so client-side retry logic can still tell
    // a transient (5xx) failure from a permanent one.
    return NextResponse.json(
      { error: 'The knowledge base did not return an answer for this request.' },
      { status: result.status || 502 }
    );
  }

  return NextResponse.json(result.data);
}
