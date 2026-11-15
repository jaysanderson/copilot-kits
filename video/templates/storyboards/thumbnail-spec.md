# Meaningful thumbnails for every DAM resource - spec + SOP draft

Work item: `4492e682f4f54bf3bc741e3fbc6c308c` (claimed by PMK-1).
GM directive, 2 Sep 2026: "there should be no excuse for a resource not having a meaningful
thumbnail." Drafted by demo-engineer for the lead's review - lead handles developer
communication and any SOP encoding into CLAUDE.md/skills.

Status: **research + spec draft only**. Not submitted to the developer, not filed as feedback,
not submitted as work. Australian English, no em dashes throughout.

---

## 1. Existing feedback check

`dam_list_feedback` (no status filter returns all statuses - confirmed by checking `new` +
`planned` + `done` + `declined` separately) currently holds 9 items: Kitforge branding
remnants, a Coca-Cola cleanup item, a performance item, and four MCP tool gaps (news
visibility, battlecard tools, base64 truncation, work-status reset, `source_url` on update).
**None mention thumbnails, placeholders, card images, or asset images.** This is a genuinely
new gap, not a duplicate of standing feedback.

---

## 2. How Nuclia/ARAG actually stores a per-resource thumbnail (confirmed, cited)

This is the KB-native mechanism our own demo apps already rely on for the B10 "real
thumbnail, never a placeholder bar" standard - directly reusable for Kitforge, because
Kitforge's own asset library is itself backed by a Knowledge Box.

**The field.** Every Nuclia resource carries a top-level `thumbnail: string | null` field.
Confirmed in the schema catalog on `Resource`, `ResourceUpdated`, and both the
create-resource and `PATCH /kb/{kbid}/resource/{rid}` payload shapes (Appendix A/F of the
agentic-rag-guide reference, e.g. `apps/bioscience-demo/reference/agentic-rag-guide/Part 7 -
Reference Appendix/Appendix A - NucliaDB REST API Reference.md:5178,5431,5575` and
`Appendix F - Complete Schema Catalog.md:435,1019,1918,2488`).

**What populates it automatically, and what does not.** Live resource dumps in the same
reference guide show the real shape:
- A **link** resource gets a real path automatically: `"thumbnail":
  "/kb/$KB/resource/<id>/link/home/download/extracted/link_thumbnail"` (Appendix A:771-772).
- A **plain text** resource has `"thumbnail": ""` - genuinely empty, Nuclia extracts nothing
  to show (Appendix A:561-579, 1043-1061, 1787-1805, 5107-5125 - every text/plain example in
  the guide has an empty thumbnail).
- **Video** gets a real extracted frame the same way, confirmed live in our own build:
  `apps/mediaportal-video/portal/src/components/Thumbnail.tsx` comment - "Nuclia's own video
  processing extracts a real JPEG frame for every resource at ingest time (no per-video
  setup)". But this is not universal even for uploaded files: the same build found **25 of
  885 resources with no `thumbnail` field at all** - mostly PUG Challenge slide decks and
  zips, i.e. file types Nuclia has no frame-extraction path for
  (`apps/mediaportal-video/portal/server/sessions.mjs:43-53`).
- **PDF/PPTX** have a separate, distinct mechanism Nuclia already computes but that no build
  in this estate currently reads: `file_pages_previews` (`FilePages`, an array of `CloudLink`
  page images - Appendix F:837-838, 4409). This is a genuine unexploited resource: the first
  entry in that array is a natural first-page thumbnail for any document resource, and no app
  in the estate uses it yet.

**How to read it back.** `GET /kb/{kbid}/resource/{rid}?show=basic` returns `.thumbnail` as a
relative API path (not a full URL, not raw bytes). To get the actual image you fetch
`{origin}/api/v1{thumbnail_path}` with the KB service-account token - proven live in
`apps/mediaportal-video/portal/server/sessions.mjs:403-426` and mirrored in
`apps/intel-co-intel/portal/server/index.mjs:763-787` (`/api/kb-file`, a generic
passthrough for any Nuclia-relative media path). **This must be a server-side proxy call**
(hard rule 6 / the KB-token-never-in-the-browser rule): the browser cannot hit the Nuclia URL
directly, both because it needs the SA token and because the path is host-relative.

**How to write/select it.** `PATCH /kb/{kbid}/resource/{rid}` accepts `thumbnail` in the
request body as that same relative-path string. Every live example of the field being
non-empty is Nuclia's own auto-generated path pointing at a field it already extracted
(a link preview, a video frame) - **no example in the reference guide or any of our own
builds shows setting `thumbnail` to a genuinely external/uploaded image path.** This is worth
flagging as unverified rather than asserted: the field type (`string | null`, not a file
upload) strongly suggests it is a "point at an already-extracted CloudLink" selector, not a
raw-bytes upload target. The Kitforge developer should treat this as **needs a live test
against a real KB** before building on the assumption that any arbitrary image can be pushed
directly into `thumbnail` - the safer, proven path is: upload the desired thumbnail image as
its own file field on the resource (or reference an existing extracted field), then `PATCH`
`thumbnail` to that field's own download path.

**Auth pattern (matches hard rule 6 and Kitforge's own architecture exactly).** Every proven
read/write in this estate uses the KB service-account token, header
`X-NUCLIA-SERVICEACCOUNT`, attached server-side only - never the account NUA key (which 403s
on KB-scoped writes per the CLAUDE.md "Auto-co evolution phase 1" lesson) and never in
client code.

**The proven guaranteed-fallback pattern (no blank cards, ever).** Two working approaches
already live in this estate, chosen by corpus shape:
1. **Media-heavy corpora** (video, links): a static branded SVG poster, served as a real
   `200` with its own `Cache-Control`, whenever the resource genuinely has no extracted
   frame - never a `404` (which the browser renders as a broken-image glyph plus a console/
   network error). `apps/mediaportal-video/portal/server/sessions.mjs:43-71` (`sendFallbackThumbnail`)
   is the reference implementation, reused verbatim in
   `apps/compliance-co-compliance-desk`'s equivalent route.
2. **Document-heavy corpora** (text/PDF/battlecard-shaped content with no natural frame): a
   **generated, per-resource card** built client-side from the resource's own real title +
   doc type + brand colour - never a generic icon repeated on every card. Reference
   implementation: `apps/publisher-claims/portal/src/components/LetterheadPreview.tsx` - a
   miniature "letterhead" render (masthead, brand rule, doc-type label, the item's own title,
   deterministic body-line bars) used as the card thumbnail whenever `card.thumbnail` is
   null (`apps/publisher-claims/portal/src/palette/CatalogGrid.tsx:223-233`). This was itself
   a GM correction (17 Aug 2026, Standard B10) after a bare file-type glyph shipped as the
   fallback on every card in a text-only corpus.

---

## 3. The confirmed current gap on the Kitforge/DAM side

Checked directly against the live MCP tool schemas (not assumed):

- **`dam_create_asset`** - fields: `title`, `asset_type`, `description`, `tags`, `collection`,
  `era`, `source_url`. **No thumbnail/preview-image field of any kind.**
- **`dam_submit_work`** - fields: `title`, `text_body`, `file_url`, `file_base64`, `mime`,
  `filename`, `source_url`, `description`, `tags`, `collection`, `asset_type`, `note`,
  `battlecard`. **No thumbnail/preview-image field.**
- **`dam_update_asset`** - `title`, `description`, `collection`, `era`, `tags`, plus the
  governance axes (`source`/`visibility`/`tier`/`play`/`product`/`clearance`). **No
  thumbnail field.**
- **`dam_upload_from_url`** - `url` or `file_base64`+`mime`, `title`, `asset_type`,
  `collection`. Stores the fetched/provided bytes as **the asset binary** and computes a
  SHA-256 - i.e. for an `image`-typed asset the uploaded file IS the visual, but there is
  still no separate preview/card-thumbnail concept distinct from the master file. **No
  thumbnail field.**
- **`dam_create_battlecard`** - structured JSON only (competitor, summary, comparison rows,
  objections, etc). There is **no visual representation possible for a battlecard at all**
  today - not even a generated one - because the asset has no bound file and no thumbnail
  field.

So the gap is total and structural, not a rendering bug: **the write path (asset creation)
has no way to supply or trigger a thumbnail, and nothing in the schema suggests Kitforge
currently derives one from the underlying KB resource either.** For a `document`,
`presentation`, `demo`, `course`, `campaign`, `product`, `history`, `slogan`, `guideline`, or
`battlecard` asset type - the majority of what PMK-1 actually ships - there is structurally
no card image today unless the platform starts writing one at creation time.

---

## 4. SPEC to give the Kitforge developer

### 4.1 Write path - populate `thumbnail` at asset creation, every time

Whichever of `dam_create_asset` / `dam_submit_work` / `submit-file` created the underlying KB
resource must, as part of that same creation flow, ensure the resource's Nuclia `thumbnail`
field resolves to something real before the item leaves draft/in_review. Concretely, in
priority order:

1. **The asset genuinely IS an image** (`asset_type: image/illustration/logo/icon/
   color-palette` uploaded via `file_base64`/`file_url`) - the uploaded file itself is the
   thumbnail source. No extraction needed; reference/crop it directly.
2. **Video** - use Nuclia's own auto-extracted frame (`resource.thumbnail` populates without
   any extra call, per section 2 above). Verify it landed post-processing rather than assume
   it did - the mediaportal-video build found a real ~3% miss rate even on video-shaped uploads.
3. **PDF/PPTX/document-family files** - read `file_pages_previews.pages[0]` (the `FilePages`
   CloudLink array Nuclia already computes, section 2) and `PATCH thumbnail` to that page
   image's path. This is a genuinely new capability for Kitforge - no build in the estate
   currently reads this field, so it closes a real gap rather than duplicating existing work.
4. **A link/URL-sourced asset** - Nuclia's `link_thumbnail` auto-populates the same way
   (section 2); use it directly.
5. **Everything else with no natural image** (plain text, copy, a battlecard, a slogan, a
   guideline, structured JSON content) - **generate a branded card thumbnail server-side at
   creation time** from the asset's own real title + `asset_type` + a brand motif (colour,
   wordmark). This is the guaranteed fallback (section 2, pattern 2) - render it once, store
   it as an image (either as the resource's own `thumbnail`-referenced field, or as a
   deterministic client-render driven off `title`/`asset_type`/`play` the same way
   `LetterheadPreview.tsx` does it live, no storage needed). Either approach satisfies "never
   blank" - a stored generated image is more portable across future viewers/exports; a
   live-rendered card is cheaper and always current if the title changes later. **Recommend
   the live-rendered approach** (matches the proven, cheaper pattern) unless Kitforge needs
   thumbnails to survive outside the app itself (e.g. in an export or an email preview), in
   which case render once and store.

**Never leave `thumbnail` empty by default and call it done.** An empty/`""` thumbnail on a
plain-text resource is Nuclia's own honest signal that nothing was extracted - it is not
Kitforge's cue to show a blank card, it is Kitforge's cue to run step 5.

### 4.2 Read path - Kitforge's own resource display

Mirror the proven proxy pattern exactly (section 2, "How to read it back"):
- `GET /kb/{kbid}/resource/{rid}?show=basic` server-side, using the KB service-account token
  (`X-NUCLIA-SERVICEACCOUNT`), read `.thumbnail`.
- If present, proxy `{origin}/api/v1{thumbnail_path}` through Kitforge's own server (never
  expose the SA token or the raw Nuclia URL to the browser).
- If absent, or the upstream fetch fails for any reason, serve the generated branded fallback
  as a real `200` image response - never a `404`/broken-image glyph, and never a blank div.
- This is exactly `apps/mediaportal-video/portal/server/sessions.mjs`'s
  `/api/sessions/:id/thumbnail` route and `apps/intel-co-intel/portal/server/
  index.mjs`'s `/api/kb-file` passthrough - both are ready-to-adapt reference
  implementations, not just prose.

### 4.3 Architecture constraints (respect what Kitforge already does correctly)

- **KB service-account token only, server-side, for every read and write against the KB** -
  never the account NUA key, which is confirmed to 403 on KB-scoped writes (CLAUDE.md,
  Auto-co evolution phase 1 lesson). Kitforge's own asset library is itself KB-backed, so
  this is the same credential it already uses elsewhere - no new credential surface.
- **GET, not POST, for anything resembling facet/catalogue reads** - unrelated to thumbnails
  directly, but worth restating alongside any new KB call: `POST /catalog` facet aggregation
  is a confirmed cross-tenant leak on this platform (CLAUDE.md, 26 Aug 2026 finding); the
  thumbnail read above is a plain resource `GET`, which is unaffected, but any new endpoint
  the developer adds nearby should stay on `GET`.
- **A resource's `title` is not searchable body text** (CLAUDE.md, Auto-co phase 1) -
  irrelevant to thumbnails specifically, noted only because the generated-card fallback
  (4.1.5) pulls the title straight from the asset record, which is safe and correct here
  since the card is a visual, not a grounding source.

---

## 5. Draft PMK SOP addition

Proposed wording, for the lead to place and adapt (candidate locations: hard rule 12's "DAM
file-delivery rules", or a new short binding rule near it; alternatively a line in the
`arag-demo-app` skill's B10 section extended to cover DAM submissions generally, since B10
already states the identical "never a placeholder bar" principle for demo apps):

> **Every asset PMK-1 delivers to the DAM carries a meaningful thumbnail (binding).** Before
> `dam_submit_work` / `dam_create_asset` / `submit-file`, confirm the resulting asset will
> render a real, resource-specific preview, not a blank card or a generic icon - the image
> itself for an image/video/logo asset; the extracted first-page/frame for a document or
> video once the Kitforge platform supports it (see `content/platform/thumbnail-spec.md`);
> otherwise a generated card carrying the asset's own real title, type and Progress brand
> motif. This is the DAM-delivery equivalent of Standard B10 in the `arag-demo-app` skill
> ("a real thumbnail, never a placeholder bar") applied to every submission this factory
> makes, not only demo-app catalogue cards.

---

## 6. Summary for the lead

- **Confirmed Nuclia mechanism (cited):** `resource.thumbnail` (a relative CloudLink path),
  auto-populated for video/link resources, empty for plain text and some file types; read via
  `GET /resource/{id}?show=basic`, proxied server-side with the KB SA token; writable via
  `PATCH thumbnail`, though setting it to a genuinely external image needs a live test (no
  proven example in the estate - flagged, not asserted). `file_pages_previews` (PDF/PPTX
  first-page images) is a real, unexploited resource worth using for document thumbnails.
- **Confirmed gap:** `dam_create_asset`, `dam_submit_work`, `dam_update_asset`,
  `dam_upload_from_url` and `dam_create_battlecard` all lack any thumbnail/preview-image
  field today - the gap is structural (no write path), not a display bug, and is total for
  battlecards specifically (no bound file exists at all).
- **Existing feedback:** none of the 9 items in `dam_list_feedback` cover this - genuinely
  new.
- **Draft spec + SOP:** written to `content/platform/thumbnail-spec.md` (this file), ready
  for the lead to hand to the developer and encode into CLAUDE.md/the relevant skill.
