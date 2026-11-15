import { NextResponse } from 'next/server';
import { aragFetch, getKbInfo, getGenerativeModel } from '@/lib/aragFetch';

export async function POST() {
  try {
    const { kbId } = getKbInfo();
    const result = await aragFetch('', { timeout: 15000 });

    if (!result.ok) {
      return NextResponse.json(
        { ok: false, error: 'Could not reach the knowledge base with the configured credentials.' },
        { status: 502 }
      );
    }

    // Deliberately omits the base URL from the response - see app/api/arag/env
    // for why a live host/region string is never returned to the browser.
    return NextResponse.json({ ok: true, kbId, generativeModel: getGenerativeModel() });
  } catch {
    return NextResponse.json(
      { ok: false, error: 'The connection is not configured. Check the server environment variables.' },
      { status: 500 }
    );
  }
}
