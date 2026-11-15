# The university demo - design

Work item `a38313a61e0e47bfa9eef47392f3eef3`. Started 9 October 2026.

One deployment, two surfaces: a prospective-student front door that looks like
university.edu.au, and a CorpusKit portal branded for one faculty behind it.

---

## 1. The two lead decisions, and what grounds them

Both were expertise calls rather than questions for the GM. Both are grounded in the
corpus and the live site rather than in what University is famous for, because what the demo
can ANSWER is a different question from what the university is known for.

### Faculty for surface 2: VETERINARY STUDIES

**Evidence, from the knowledge box itself rather than memory:** asked what schools and
disciplines University has, the corpus returns six founding schools with Veterinary Studies
among them, and states the university "continues to have strengths in today". Eleven
citations. The corpus also names the School of Medical, Molecular and Forensic Sciences,
the School of Mathematics, Statistics, Chemistry and Physics, University Law School, and
Engineering and Energy.

Veterinary Studies wins on three counts: it is corpus-confirmed as a founding school and a
continuing strength; it is the discipline a Perth audience associates with University; and it
has the richest demonstrable corpus SHAPE for CorpusKit - clinical case notes, species and
procedure protocols, teaching material and research outputs are visibly different kinds of
document, which is what makes a taxonomy and a knowledge graph worth looking at. A law
school corpus is mostly one kind of document.

### Languages for surface 1: ENGLISH, MANDARIN, ARABIC, BAHASA INDONESIA

**Grounded in the campuses the corpus names, not in a guess at the student mix.** The
corpus states five campuses across three countries, with international campuses in
**Singapore** and **Dubai**, and "more than 25,000 students and 2,400 staff from 90
different countries". It does NOT list recruitment countries, and the model said so
plainly rather than inventing them - that honest decline is itself worth showing.

So: Mandarin for Singapore, Arabic for Dubai, Bahasa Indonesia for the nearest large
market to Western Australia, English as the base.

**Two of the four are already PROVED live against this corpus** (9 Oct 2026): a Mandarin
question returned a cited answer in Chinese, an Indonesian question returned a cited
answer in Indonesian with eleven citations. Arabic is NOT yet probed and must be before it
appears in any picker - **a language that degrades to English is a no-fake violation.**

**Arabic is right-to-left.** That is a real layout constraint, not a translation one, and
it is named here so it is designed for rather than discovered at the gate.

---

## 2. What makes this buildable, verified 9 October 2026

| Fact | Evidence |
|---|---|
| Knowledge box is real and on the right account | `universityuni`, `c92a4d9d-1264-4e2c-9834-148f6313be26`, zone `<zone>`, account `progress-jay-geo`. Listed 200 with the NUA key. Hard rule 14 satisfied without provisioning. |
| It holds real content | 343 resources, crawled from university.edu.au. Titles read back from the catalogue, paginated, never faceted. |
| The corpus suits the STUDENT surface | It is institutional rather than academic: admissions, policy, campuses, fees, safety, contact. That is what a prospective student asks about. |
| The budget block is lifted | A real generative call returned 200 in 13.4s with a grounded, cited answer. |
| Cross-lingual retrieval genuinely works | `semantic_model` is `multilingual-2024-05-06`, and two live probes answered in the asked language from the English corpus. |
| Token is long-lived | Service account `university-demo-owner`, SOWNER, expires 2029-10-07, 1095 days. `exp` decoded from the file without the secret leaving it (hard rule 15b). |

### COST SAFETY ACTION ALREADY TAKEN

The knowledge box's default generative model was **`chatgpt-azure-5.6-terra`**, a premium
model. Every query-time call that forgets to pin inherits it, and the per-answer quality
score **cannot be pinned at all**, so it inherits the default by construction. That is the
mechanism that budget-blocked this account on 5 October.

Patched to `gemini-3.1-flash-lite` for both `generative_model` and `summary_model`,
verified by read-back. `semantic_model` untouched - changing it would re-index the corpus
and is both expensive and unnecessary.

---

## 3. CorpusKit: what it is, and what the licence permits

**It is not a generic app we are bending to fit.** Its own README: "The open source
research portal for Progress Agentic RAG." It is the engine behind
`frdc.corpuskit.org`, which is this factory's named UI polish bar.

- **Licence: Apache 2.0**, with a `NOTICE` file present. Branding, modifying and
  redistributing are permitted. Conditions we must meet: retain `LICENSE` and `NOTICE`,
  retain attribution notices, and **state the changes we made**. All cheap; recorded here
  and in the fork's own README.
- **Multi-tenant by design** - `apps/api/src/tenants.ts`, `tenant-copy.ts`,
  `tenant-aliases.ts`, and a worked tenant fixture. Branding for University is a first-class
  operation in this codebase, not a fork-and-hack.
- **Its Dockerfile already targets Fly** ("Fly's remote builder is linux/amd64") and
  deliberately avoids the npm CLI.

**Stack divergence, flagged rather than hidden:** CorpusKit runs on **Deno 2**, not Python.
Hard rule 1's npm exception covers the `arag-demo-factory` template and not this. The GM
named the repository, so the stack comes with it, and he has been told in one line that
this demo carries a different stack from the rest of the estate.

---

## 4. Brand, captured not approximated (Field Rule 8)

Captured from the live site with a real browser, 9 October 2026. Computed styles ranked by
element count; `brand/capture.json` holds the full ranking.

| Token | Value | Why this value |
|---|---|---|
| `--mu-crimson` | `#E12744` | The logo, headings and every primary CTA |
| `--mu-teal` | `#008481` | Secondary, links, the live-chat tab |
| `--mu-ink` | `#212529` | Body text - 573 elements, the dominant colour on the page |
| `--mu-font` | Poppins | 403 elements. The site is Poppins; it is a Google font, so loadable from a sanctioned host |

**Real logo:** `brand/mu-logo.svg`, 6,434 bytes, fetched from University's own CDN. The MU
monogram plus wordmark, not a redraw.

**Real page structure**, read off the capture: a utility bar (Current Students, Alumni,
Staff, Library, Contact, Search), a main nav (Study, Research, Collaborate, Explore), a
full-bleed hero photograph with a magenta-to-crimson card over it, and four quick cards -
Courses, How to apply, Scholarships, About us.

**Those last cards are the conversion paths** (Field Rule 10, B48). The student surface
feeds them and links OUT to University's own real flows. It never fakes or processes an
application.

---

## 5. Architecture: one deployment, two tenants, two knowledge boxes

**Settled by reading CorpusKit's own binding layer rather than by assuming.**
`apps/api/src/bindings.ts` keys knowledge-box credentials **per tenant slug** -
`get(slug): KbBinding`, over a `Record<string, KbBinding>`. So one deployment binds a
DIFFERENT knowledge box per tenant, which is exactly what "one demo, two surfaces"
requires, as a first-class supported operation rather than a fork.

| Tenant | Knowledge box | Surface |
|---|---|---|
| `university` | `universityuni` - the real 343-page institutional crawl | Prospective-student front door, styled as the University homepage, four languages |
| `university-vet` | a new box holding the synthetic veterinary corpus | The faculty portal, disclosed as synthetic |

Credentials are described in that file as "server-only knowledge box credentials, sealed at
rest when a key is configured", so hard rule 6 - never an ARAG key in client-side code - is
the codebase's existing design rather than something to retrofit.

### A documented silent-failure mode to design around

CorpusKit's own comment, worth repeating because it is exactly the class this factory has
been chasing: Explore intersects a tenant's topic ids with the knowledge box's facet
counts, so **"an id that is not a real label silently yields an empty portal."** A
mis-typed topic id produces a working-looking portal with nothing in it and no error.
Assert the tenant's topic ids against the box's real labels at build time, and make a
missing label fail loudly rather than render empty.

---

## 6. Language probes: ALL FOUR PROVED LIVE

Against the real corpus, 9 October 2026, cheapest model pinned. A language ships only once
it has answered IN that language from the English corpus, with citations.

| Language | Result | Evidence |
|---|---|---|
| English | PASS | Cited answer, 4 citations |
| Mandarin | PASS | Answered in Chinese, 260 non-ascii characters, cited |
| Bahasa Indonesia | PASS | Answered in Indonesian, 11 citations |
| Arabic | PASS | Two separate questions. 995 Arabic against 63 Latin characters, and 227 against 41. The Latin residue is proper nouns in parentheses - "بيرث (Perth)" - which is correct behaviour, not fallback |

**Two questions per language, not one**, because citation presence varies per question and
per run rather than by language, so a single clean result is not evidence.

The script check is the gate: an answer whose Latin characters outnumber its Arabic ones
is a fallback to English and a no-fake FAIL. It is written as a comparison rather than an
eyeball so it can run on every build.

---

## 7. Still open

- The synthetic veterinary corpus itself: written, disclosed as synthetic on the surface
  that serves it, and ingested to a new box on the same account.
- Ingest cost for that box, estimated before the run rather than after (hard rule 15).
- Whether the student front door is a CorpusKit tenant with a custom homepage, or a thin
  separate route in the same deployment. The binding layer supports either.

## University name in non-Latin languages (chat, 9 Oct 2026)
Pinned: Arabic جامعة مردوخ, Simplified Chinese 大学, Indonesian Universitas University. The Arabic form is the title of Arabic Wikipedia's article (via the English article's interlanguage link); it is NOT confirmed as University's own official form. Confirm with the customer. Chrome strings, the chat system prompt (chat.py SYSTEM) and a server-side replace all use it.

## Enforcement is not the same in every language (chat)
Australian English and the university-name form are enforced two ways in English (system prompt plus a server-side whole-word respell in `chat.py` that skips proper names such as "World Health Organization"). Arabic, Chinese and Indonesian rest on the system prompt alone, except the Arabic name, which also has a server-side replace. Model prose is unreviewed output.

## Retry on an uncited answer (chat.py, 9 Oct 2026)
When `/ask` returns an answer with no citations, a non-English question is retried ONCE with `rephrase: true`. This silently reformulates the user's query for the second attempt; the answer still addresses what they asked and still must cite real sources, and a second uncited result is a decline. Why non-English only, measured: the compound Arabic question "which scholarships are available and how do I apply" came back uncited on about half of direct calls (and 3 of 3 through the app before the retry); the English equivalent answered with citations 5 of 5 (n=5, no retry in the path). If English ever shows the same pattern, widen the retry. After the fix, Arabic answered 6 of 6; the baseline succeeded some runs anyway, so a residual decline rate is likely.

## Spelling map controls (answers.py)
Run with the proper-name guard disabled, "World Health Organization", the "Centers for Disease Control" sentence and "Organization of American States" are all mangled (3 of 7 cases fail); with it enabled all 7 pass, including "Organization membership is required." (corrected to Organisation, as intended) and title-case headings.

## Em dashes reach the screen through model prose (filed from the film, 9 Oct 2026)
The vet portal's answer to "which antimicrobial classes need senior approval before
dispensing" renders **"cephalosporins—specifically ceftriaxone and cefovecin—and
fluoroquinolones"**: two true em dashes, from the model, on a customer-facing surface.
Invisible at the film's old framing and legible once the beat was punched, which is how
it was found - a reminder that **framing changes what a compliance scan has to cover.**

This is the same layer as the Australian-English respell in `chat.py` and the proper-name
guard in `answers.py`: a server-side pass over rendered answer text. The fix is to
replace ` — `, `—` and ` – ` with a spaced hyphen in the same place, with the same
proper-name/code exclusions, and a control proving it fires on a planted em dash and
stays quiet on a hyphenated compound and on a minus sign inside a figure.

**Not urgent and NOT a reason to deploy out of band** (lead ruling, 9 Oct 2026): deploys
are frozen with eight verified changes queued and this is the ninth. The film ships with
the dashes on tape because they are the product's genuine output and the asset is
internal. If the app redeploys before any later re-cut, re-record `vet_ask2` and the
fixed product is on tape for free.
