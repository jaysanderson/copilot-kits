# Using the kits with GitHub Copilot

Four kits (`demos`, `content`, `decks`, `video`) and the starters (`projects/arag-starters/*`). Prospect-specific projects live in their own private repos, not here. Each is a self-contained folder whose `.github/` teaches Copilot how to work in it. You never paste the rules into chat; opening the folder is enough.

## 1. Get them onto the work PC (once)
1. Clone this repo. Then add the two things it does not carry: the Progress Sans fonts into each `brand/fonts/` (see `FONTS-README.md`) and the corporate deck template into `decks/templates/` (see the README there). Both are gitignored.
2. Clone it on the work PC.
3. In VS Code, install GitHub Copilot and GitHub Copilot Chat. Update VS Code to the current release; custom agents need a recent build.
4. Settings (search each in Settings): `Use Instruction Files` on, `Prompt Files` on. If an `.agent.md` does not show in the agent picker, add `.github/agents` under `Chat: Agent Files Locations`.

## 2. Open the right folder
Open one project or kit folder as the VS Code workspace (`File > Open Folder`), not the `copilot-kits` root. Copilot reads the `.github/` of the workspace root only.

- A new demo, piece, deck or video: open the kit folder, or copy a template out of it first.
- A prospect project: clone its private repo and open that folder.
- A starter: open `projects/arag-starters/<nn-name>`.

## 3. What the four file types do
| File | When it loads | What it is |
|---|---|---|
| `.github/copilot-instructions.md` | every chat, always | the rulebook: secrets, gates, language, working style (under 60 lines) |
| `.github/instructions/*.instructions.md` | when you touch a file matching its `applyTo` glob | ARAG REST rules for server code; UI rules for front-end files |
| `.github/prompts/*.prompt.md` | when you type `/name` in Copilot Chat | a recipe: inputs, steps, evidence, stop |
| `.github/agents/*.agent.md` | when you pick it in the agent dropdown | a reviewer or tester that judges and never edits |

## 4. Every chat, the same way
1. Copilot Chat panel, mode **Agent**.
2. Type `/` and pick the prompt. Answer its inputs one at a time.
3. Model: cheapest for renames, copies and mechanical edits; the strongest only for the step the README calls hardest, and for QA judgment.
4. One step per chat. Read the evidence it shows. Start a **new chat** for the next step so the last one's context is not billed again.
5. `.env` is filled by you, locally, from `.env.example`. Never in chat.

## 5. The run order per kit
| Kit or project | Order | Gate |
|---|---|---|
| `demos` | `/new-demo` → `/provision-kb` → build steps → `/capture-shots` → `/locked-brief` | `/qa-gate`, agent `qa-reviewer`, agent `demo-tester` |
| `content` | `/new-piece` → `/de-ai-pass` (and `/battlecard` for a battlecard) → `/locked-brief` | `/content-gate` |
| `decks` | `/new-deck` or `/renovate-deck` → `/brand-audit` | `/deck-gate` |
| `video` | `/produce-video`, `/narrate-deck`, `/demo-walkthrough` or `/repurpose-video` | `/video-gate`, agent `video-reviewer` |
| a prospect project (private repo) | `/locked-brief` first, then `/new-demo` (pre-filled) | `/qa-gate` |
| `projects/arag-starters/*` | `/finish-starter` per BRIEF step → `/audit-standard` once → `/raise-standard` per open (B) line → `/write-article`, `/capture-shots` | `/qa-gate`; the bar is `STANDARD.md` |

## 6. Reading a project before the first chat
`BRIEF.md` is the plan (read it, two minutes). `README.md` is the promise. For a starter, `STANDARD.md` is what finished means and `BUILD-ORDER.md` at the series root says which project first. `reference/` is copy-from material, never edited, never imported at run time.

## 7. If Copilot drifts
- It generates a client, renderer or Dockerfile: stop it. Point at the file in `reference/` or the chassis and say copy.
- It invents an ARAG endpoint: it must stop by itself (the rulebook says so). If it does not, open `.github/instructions/arag-api.instructions.md` and paste the relevant line.
- It says "looks fine": that is a FAIL under the rulebook. Ask for the evidence (response body, grep, screenshot).
- Context feels heavy or answers slow: new chat.
