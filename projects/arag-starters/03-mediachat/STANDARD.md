# MediaChat - the product standard

What "high standard" means for this starter, line by line. Copilot works this file with `/audit-standard` (report) and `/raise-standard` (fix the top open line). A line marked (B) is a blocker: the product does not ship or post with one open. A PASS needs evidence in the reply (a response body, grep output, a screenshot you viewed, a URL you opened). "Looks fine" is a FAIL.

Status values: `chassis` = built into the chassis - verify once with evidence; `verify` = the base app should already do this - verify with evidence; `todo` = not done - do it; `done (evidence)` = set by `/raise-standard` with the evidence in brackets.

## 0. This product (from BRIEF.md, all blockers)

| Id | Line | Status |
|---|---|---|
| D1 (B) | A question asked in Japanese is answered in Japanese with a video card that starts at the cited second. | todo |
| D2 (B) | An image card and a PDF page card each open the source. | todo |
| D3 (B) | No thumbnail URL in the page points at the ARAG host; all go through this app. | todo |
| D4 (B) | 390 px render clean; zero raw markdown. | todo |

## 1. Product

| Id | Line | Status |
|---|---|---|
| P1 (B) | One job, one screen. A first-time visitor gets a real result inside 30 seconds without reading anything. | todo |
| P2 (B) | First paint is useful: the suggested questions all return grounded answers on the seeded KB (none withheld, none empty). | todo |
| P3 (B) | Every state is designed: loading, withheld answer, upstream error (502), rate limit (429), empty results. No raw error page, no stack trace, no silent spinner. | chassis |
| P4 (B) | Every route renders clean at 390x844 and 1440x900; `scrollWidth === 390`; no control floats over content. | chassis |
| P5 (B) | Every citation is clickable and opens the source at the cited passage, page or second. Inline markers are placed server-side. | chassis |
| P6 (B) | Confidence is a qualitative badge with a one-line meaning on hover; never a raw numeral; a withheld answer carries no badge and no sources. | chassis |
| P7 (B) | All AI text renders through the markdown renderer. Literal `**`, `#` or `- ` on screen is a FAIL. Tested with a multi-item numbered answer. | chassis |
| P8 (B) | Copy is Australian English, no em dashes, none of delve, leverage, unlock, seamless, game-changing. No `/ask`, `/find`, `Knowledge Box` or zone string anywhere a user reads; How this works is the only place mechanics appear. | todo |
| P9 | Accessibility floor: every control has a label, visible focus ring, 4.5:1 contrast on text, the whole flow works on keyboard alone, the answer's `dir` and `lang` follow its language. | todo |
| P10 (B) | The three items under Where to take it next are listed in the README and visibly not built. Nothing else half-built is left in the UI. | todo |

## 2. Trust (the ARAG test)

| Id | Line | Status |
|---|---|---|
| T1 (B) | ARAG is load-bearing: the README states the capability that would break without it and the running app proves it (the capability is a real ARAG call at run time, never mocked, cached or pre-canned). | todo |
| T2 (B) | A withheld answer is the model's own decline (the decline contract), surfaced warmly; the app never invents an answer when retrieval is empty. | chassis |
| T3 (B) | No fabricated numbers: no accuracy, adoption, ROI or benchmark figure anywhere in UI, README or ARTICLE. Demo figures are labelled demo figures. | todo |
| T4 (B) | Synthetic content is disclosed in the footer; fictional people and organisations only; no real customer name, demo codename or third-party brand used as if owned (`grep -rniE` the list in BRIEF.md). | chassis |
| T5 | The How this works panel names the real mechanisms used (find, ask, groundedness, upload, graph, agent) and nothing else. | todo |

## 3. Code

| Id | Line | Status |
|---|---|---|
| C1 (B) | ARAG is called server-side only. The token never reaches the browser, logs, README, ARTICLE or git. `.env.example` has empty values. | chassis |
| C2 (B) | Every outbound HTTP call has an explicit timeout; an upstream failure becomes a JSON 502 with a human message. | chassis |
| C3 (B) | Every request body is validated (length limits, enums); the generating route has a per-IP budget (429) and the question text is never logged. | chassis |
| C4 (B) | The generative model, reranker and host come from env vars on every call; no literal model, zone or KB id in code. | chassis |
| C5 (B) | `python smoke_test.py` passes with no Knowledge Box attached (boot, page, config, validation, 502 path, 429 path). For a base app, add the equivalent test. | chassis |
| C6 | No dead code: every module in the repo is imported or named in the README; `reference/` is documentation, not imported at run time. | todo |
| C7 | Every route has a one-line docstring; public functions have type hints; `ruff check .` is clean (or `npm run lint` for a Node base). | todo |
| C8 | Starter-grade size: product code stays in the hundreds of lines; anything bigger is a sign a deliberately unbuilt extension crept in. | chassis |
| C9 (B) | Dependencies pinned (`requirements.txt` or lockfile); the Dockerfile builds from a clean clone and the container answers `/healthz`. | chassis |

## 4. Operate

| Id | Line | Status |
|---|---|---|
| O1 (B) | `fly.toml` app name changed from `CHANGE-ME-*`; `min_machines_running = 1`; secrets set with `fly secrets set`, never in the image. | todo |
| O2 (B) | `/healthz` answers 200 and is wired as the Fly health check; the access log shows method, path, status and latency only. | chassis |
| O3 | Cost guard: the model pinned in env is the cheapest capable one; any script that loops over a corpus prints its call estimate first and stops above a few dollars. | todo |
| O4 | Reset path documented: how to reseed the KB in about 30 seconds (`/provision-kb`), and how to rotate the token. | todo |

## 5. Release (public code)

| Id | Line | Status |
|---|---|---|
| R1 (B) | README has, in order: the problem line, a screenshot, a five-step run, an env table, the ARAG section, Where to take it next, licence line. A stranger can run it in ten minutes. | todo |
| R2 (B) | Licence chosen and `LICENSE` present (MIT unless Progress legal or marketing says otherwise; record the decision in BRIEF.md). | todo |
| R3 (B) | Leak sweep from a fresh clone passes: no secret, JWT, zone host, KB id, personal path, live demo hostname, customer name or codename (`git clone` then grep; paste the output). | todo |
| R4 (B) | Two screenshots in `docs/` (1440 and 390) captured from the running app with `/capture-shots`; the README embeds the first. | todo |
| R5 | A tag `v0.1` on the commit that ships; CHANGELOG or release notes with three lines. | todo |
| R6 (B) | Progress marketing or social-team sign-off recorded in BRIEF.md before the repo goes public or the post goes out. | todo |

## 6. Series assets

| Id | Line | Status |
|---|---|---|
| S1 (B) | `ARTICLE.md` complete: problem line first, under 800 words, the ARAG section names the mechanism, the three extensions match the README. | todo |
| S2 (B) | A 45-second clip script in `ARTICLE.md`: the problem in one line, the result in five seconds, the pattern in four lines, the tag line. | todo |
| S3 | The post text ends with who to tag and the series line; the article link goes in the first comment. | todo |

## Order of work

1. `/finish-starter` once per BRIEF.md step until section 0 is done.
2. `/audit-standard` - one report, ranked, no fixes.
3. `/raise-standard` once per open (B) line, blockers first, then the rest while budget allows.
4. `/qa-gate` against the live URL. A FAIL goes back to step 3.
5. `/write-article`, `/capture-shots`, sign-off (R6), then post.
