# Build order (two weeks, half a day each, one Copilot chat per BRIEF step)

| Order | Folder | Why here |
|---|---|---|
| 1 | `_chassis/` | Run it once against any KB. Every chassis starter inherits it; fix anything here first. |
| 2 | `10-valuecase` | Finished app; the finishing touch is one route and one button. Warms up the pattern. |
| 3 | `07-graphbuilder` | Finished app; one new route, one panel. |
| 4 | `09-truthbench` | Chassis; `arag.py` already has the scoring. Small. |
| 5 | `05-triagedesk` | Finished app; mostly renames and a reseed. |
| 6 | `02-searchplus` | Chassis; seed corpus included. |
| 7 | `04-evidencereader` | Chassis; upload plus pdf.js. |
| 8 | `06-opsagent` | Chassis; needs the console step for the agent. |
| 9 | `03-mediachat` | Chassis; media cards, a streaming route and the embed tag. Needs a quirks check. |
| 10 | `08-callsense` | Finished app; needs five synthetic recordings. |
| 11 | `01-answergap` | Chassis; the biggest and the day-one post. Do it when the pattern is fluent. |

Per project, in this order
1. `/finish-starter` once per BRIEF.md step (section 0 of STANDARD.md).
2. `/audit-standard` once: the ranked gap report.
3. `/raise-standard` once per open (B) line, blockers first.
4. `/qa-gate` on the live URL; a FAIL goes back to 3.
5. `/write-article`, `/capture-shots`, marketing sign-off (R6), post.

Rules that save tokens
- New chat per BRIEF step. Paste nothing from earlier chats; point at files.
- Cheapest model for renames, copy, seeds. Premium model only for the step each `README.md` calls hardest.
- Stop when the Done when lines pass. No polishing pass without a failing line.
- Deploy each to its own Fly app (`CHANGE-ME-<slug>` in `fly.toml` must be renamed), region `syd`, then stop the machine until recording day.

Before any post
- Sign-off from Progress marketing or the social team for public code and content.
- Leak sweep from a clean clone: no `.env`, no token, no KB id, no zone host, no customer name.
- Remove or regenerate anything that still names the source demo's fictional customer.
