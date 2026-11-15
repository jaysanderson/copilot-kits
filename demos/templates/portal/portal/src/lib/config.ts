// The demo.config.json contract, typed. The shell renders itself entirely from
// this — adding or removing a surface is a config change, never a code change.
// The client copy is served by /api/config, already stripped of anything
// sensitive (no KB token, no zone/residency string).

export interface ThemeTokens {
  brandName: string;
  primary: string;
  accent: string;
  mood?: string;
  /** Default colour scheme for the demo ('dark' for cinematic blueprints). */
  scheme?: 'light' | 'dark';
}

export interface Surface {
  id: string;
  route: string;
  label: string;
  component: string; // must match a component name in src/pages
  icon?: string | null;
  /** Capability area this surface belongs to — drives the grouped nav + bento. */
  group?: 'Converse' | 'Explore' | 'Analyze' | 'Extend' | string | null;
  /** One-line, product-facing description of the surface. */
  tagline?: string | null;
  /** The executive value line — why this surface matters to a buyer. */
  sells?: string | null;
  capabilities?: string[];
  enabled: boolean;
}

export interface Safety {
  syntheticOnly: boolean;
  noRealBrands?: boolean;
  disclaimer: string;
}

export interface DemoStep {
  step: number;
  say: string;
  show?: string;
}

export interface DemoConfig {
  blueprint?: string;
  title: string;
  persona?: string | null;
  /**
   * Fixes 1-2 (flagship rebuild, Section 3.A): the vertical noun this demo's
   * own default copy uses in place of the literal "Knowledge Box" (e.g.
   * "Catalogue", "Library", "Case File System"). `create-app.js` fills this
   * from the blueprint; components must never fall back to a literal
   * "Knowledge Box" default - see `getDomainNoun()` below.
   */
  domainNoun?: string;
  /** Section 2 / GM standard 1: the required composition archetype (no default). */
  archetype?: { id: string; name: string; demonstrates: string };
  /** GM standard 4 (17 Aug 2026): >= 5 named use cases within the vertical. */
  useCases?: string[];
  /** GM standard 2 + header addendum (17 Aug 2026): standing Progress attribution - always on. */
  progressAttribution?: { header: boolean; footerBadge: boolean; architectureRevealProminent: boolean };
  /** Module 4.2: the declarative real request/data flow <ArchitectureReveal /> renders. */
  architectureFlow?: { stage: string; detail: string; status: 'real' | 'disclosed-gap' }[];
  /** Standard B12 - per-route flow (route path -> its own stages), keyed by the surface's `route`. Falls back to `architectureFlow` when a route has no specific entry (home, /r/:id, etc). */
  architectureFlowByRoute?: Record<string, { stage: string; detail: string; status: 'real' | 'disclosed-gap' }[]>;
  /**
   * Standard B12 (sharpened 17 Aug 2026, GM correction): the reveal must cover
   * three things, not just the technical flow - what THIS page is doing in
   * plain terms, and the value it brings to the buyer. Keyed by route, same
   * pattern as architectureFlowByRoute; `pageContext` is the fallback for a
   * route with no specific entry.
   */
  pageContextByRoute?: Record<string, { whatItDoes: string; value: string }>;
  pageContext?: { whatItDoes: string; value: string };
  /** GM standard 5 (17 Aug 2026): pre-build vertical-research step tracking. */
  researchPhase?: { required: boolean; script: string; status: string; note: string };
  /** Sub-copy under the hero headline. */
  tagline?: string | null;
  /** The large display headline on the command-center landing. */
  elevatorPitch?: string | null;
  /** Eyebrow context above the hero (industry / showcase framing). */
  vertical?: string | null;
  theme: ThemeTokens;
  surfaces: Surface[];
  safety: Safety;
  demoScript?: DemoStep[];
  /** Real starter questions (answerable) + out-of-scope probes (refusal). */
  probes?: { answerable?: string[]; refusal?: string[] };
  provenance?: { demo?: string | null; reference?: string | null };
  generatedBy?: string;
}

const FALLBACK: DemoConfig = {
  title: 'Agentic RAG Portal',
  domainNoun: 'system',
  theme: { brandName: 'Agentic RAG', primary: '#14543F', accent: '#D9A441' },
  surfaces: [],
  safety: { syntheticOnly: true, disclaimer: 'Demonstration data - synthetic content for evaluation only.' },
};

// Fixes 1-2 (flagship rebuild, Section 3.A): a process-wide cache of the demo's
// domain noun so leaf components (StatusChip, UngroundedWarning, GroundedAnswer)
// can build honest default copy WITHOUT prop-drilling the whole config through
// every bespoke Shell a builder might author. Never read as "Knowledge Box".
let domainNounCache = FALLBACK.domainNoun as string;
export function getDomainNoun(): string {
  return domainNounCache;
}

/** Loads the runtime config from the server. Never throws — falls back safely. */
export async function loadConfig(): Promise<DemoConfig> {
  try {
    const res = await fetch('/api/config');
    if (!res.ok) throw new Error(String(res.status));
    const data = (await res.json()) as Partial<DemoConfig>;
    const merged = {
      ...FALLBACK,
      ...data,
      theme: { ...FALLBACK.theme, ...(data.theme || {}) },
      safety: { ...FALLBACK.safety, ...(data.safety || {}) },
      surfaces: (data.surfaces || []).filter((s) => s.enabled !== false),
    } as DemoConfig;
    domainNounCache = merged.domainNoun || FALLBACK.domainNoun as string;
    return merged;
  } catch {
    return FALLBACK;
  }
}
