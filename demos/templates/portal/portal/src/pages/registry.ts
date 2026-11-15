import type { ComponentType } from 'react';
import type { SurfaceProps } from './types';

// ─────────────────────────────────────────────────────────────────────────────
// qa-reviewer fix (28 Aug 2026): this app's entire UI is rendered by its own
// bespoke Shell (portal/src/demo/composition.tsx, per the "paint a bespoke
// shell" rule in CLAUDE.md) - none of the generic template's stock Surface
// components below are ever actually mounted. App.tsx's fallback config-shell
// path, which is the only code that would render one, is unreachable whenever
// composition.Shell exists (it does here), and composition.tsx imports its
// own page implementations from demo/pages/, never from here.
//
// The only real purpose SURFACES still serves for this app: App.tsx checks
// `SURFACES[s.component]` truthiness to decide which demo.config.json
// surfaces count as "known" - that list feeds the guided-tour beat matcher
// (lib/nav.ts), which only ever reads a surface's label/icon/id, never its
// component. Previously this file eagerly imported all fifteen real Surface
// components anyway, which pulled their full JSX text into the shipped
// bundle regardless of use - including two this app never uses at all
// (Knowledge Graph, Workflows), whose copy carried banned em dashes (hard
// rule 2) and leaked "Knowledge Graph" wording, visible to a technical
// prospect via view-source even though nothing ever rendered them. A
// lightweight stub satisfies the truthiness check and the
// ComponentType<SurfaceProps> type the (dead) fallback path expects, without
// shipping any real Surface's copy.
// ─────────────────────────────────────────────────────────────────────────────

const Stub: ComponentType<SurfaceProps> = () => null;

export const SURFACES: Record<string, ComponentType<SurfaceProps>> = Object.fromEntries(
  [
    'AskSurface',
    'SearchSurface',
    'GraphSurface',
    'DocStudioSurface',
    'CallQaSurface',
    'WorkflowsSurface',
    'RemiSurface',
    'McpSurface',
    'PersonalizeSurface',
    'VisibilitySurface',
    'VoiceSurface',
    'AssetsSurface',
    'RelatedSurface',
    'AugmentSurface',
    'RaoAgentSurface',
  ].map((name) => [name, Stub])
);
