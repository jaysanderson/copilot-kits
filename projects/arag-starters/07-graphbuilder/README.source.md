# Progress Agentic RAG - Taxonomy Builder

An internal field tool for Progress Solutions Architects and Solutions Engineers. It
generates a hierarchical taxonomy from a Progress Agentic RAG knowledge base, lets you
review and edit the proposed tree, and exports it as governed SKOS-XL Turtle for
Progress Semaphore (or a JSON model you can re-import later).

This is not a customer-facing demo - it is a working utility that shows a genuine,
end-to-end integration pattern: a Next.js app driving retrieval-and-answer calls against
a knowledge base through the app's own server-side proxy, with no credential ever
reaching the browser.

## What it does

1. **Connect** - verify the app can reach the configured knowledge base.
2. **Settings** - name the taxonomy scheme, pick a language and base URI, describe what
   the taxonomy should cover, and set generation depth/breadth (capped for cost safety -
   see below).
3. **Generate** - the engine asks the knowledge base to propose top-level categories
   grounded in your actual content, then recurses into child categories down to the
   configured depth. Every proposal is returned as a schema-validated structured object,
   not free text, and is retried/repaired automatically if the model's output doesn't
   validate.
4. **Review** - browse the generated tree, edit any concept's label/definition/alt
   labels/seed queries, merge two concepts, move a concept to a new parent, or
   regenerate a concept's children from scratch.
5. **Export** - download SKOS-XL Turtle (`.ttl`) ready for Progress Semaphore, or a JSON
   model you can re-import to keep editing later.

## Architecture

```
Browser (this UI)
   -> this app's own Next.js API routes (/api/arag/*)
        -> Progress Agentic RAG /ask  (retrieval-and-answer, KB service-account token)
```

The knowledge base credential lives only in this app's server-side environment and is
attached via the `X-NUCLIA-SERVICEACCOUNT` header. It is never sent to, or readable
from, the browser. The in-app "How this works" button (top right) shows this same
diagram to anyone using the tool.

## Cost safety

Every generation run issues one retrieval-and-answer call per concept that is allowed
to have children. Depth and breadth are capped (depth 1-3, up to 8 children per
concept) so the worst case stays small and cheap - the Settings and Generate tabs both
show a live "up to N calls, up to M concepts" estimate before you run anything. The
generative model is pinned explicitly on every call (`ARAG_GENERATIVE_MODEL`, default
`gemini-2.5-flash-lite` - a cheap tier), rather than silently inheriting whatever the
knowledge base happens to be configured with.

## Environment variables

Set these in `.env` locally, or as Fly secrets in production. See `.env.example`.

| Variable | Required | Description |
| --- | --- | --- |
| `ARAG_BASE_URL` | yes | The Progress Agentic RAG API base URL for your zone. |
| `KB_ID` | yes | The knowledge base ID. |
| `ARAG_API_KEY` | yes | The knowledge base's own service-account token. Server-side only. |
| `ARAG_GENERATIVE_MODEL` | no | Generative model pinned on every call. Defaults to `gemini-2.5-flash-lite`. |

## Run locally

```bash
npm install
npm run dev
```

Open http://localhost:3000.

## Build and run in Docker

```bash
docker build -t arag-taxonomy-builder .
docker run -p 3000:3000 --env-file .env arag-taxonomy-builder
```

## Deploy to Fly.io

```bash
flyctl apps create arag-taxonomy-builder
flyctl secrets set ARAG_BASE_URL=... KB_ID=... ARAG_API_KEY=... ARAG_GENERATIVE_MODEL=gemini-2.5-flash-lite
flyctl deploy --ha=false
```

## Reset

This tool keeps at most one taxonomy project at a time, stored in the browser's own
`localStorage` (there is no shared database - it is a single-user tool with nothing to
keep in sync). To reset:

- Click **Reset this project** on the Settings tab, or
- Clear this site's local storage in your browser, or
- Open the app in a private/incognito window for a clean slate.

Resetting only clears data held in the browser - it never changes anything in the
knowledge base itself.

## Notes on the underlying stack

- Next.js 13 (App Router), TypeScript, Tailwind CSS, shadcn/ui components.
- No external database. An earlier prototype used Supabase purely to persist "the one
  current project" - that added a hosted dependency and two more secrets for something
  `localStorage` does just as well in a single-user tool, so it was removed.
- Dependencies are pruned to what the app actually imports (see `package.json`) - the
  original Bolt-generated scaffold shipped dozens of unused shadcn/radix components.
