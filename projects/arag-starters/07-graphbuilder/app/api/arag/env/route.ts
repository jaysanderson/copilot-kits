import { NextResponse } from 'next/server';

// Without this, Next.js statically pre-renders this bodyless GET route at
// build time and bakes the response in forever - the real env vars are
// only present at container runtime, not in the Docker build stage.
export const dynamic = 'force-dynamic';

// Deliberately does NOT return the base URL: it is a live host/region
// string, and this factory's demo QA gate treats any such string rendered
// into a page as a leak, internal tool or not. Only the knowledge base ID
// (an opaque identifier, not a hostname) is safe to surface in the UI.
export async function GET() {
  const kbId = process.env.KB_ID ?? '';
  return NextResponse.json({ kbId, configured: Boolean(kbId) });
}
