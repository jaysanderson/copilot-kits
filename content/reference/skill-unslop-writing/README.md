# unslop-writing

Claude Code skill for improving prose by removing AI-shaped writing habits without forcing a named-author style.

## What it does

- cuts common AI tells
- reduces over-explanation
- repairs mechanical cadence
- improves local clarity through objects, actions, and concrete detail
- helps endings land once instead of twice
- diagnoses paragraph-level slop before sentence-level fixes

## Best for

- fiction
- essays
- newsletters
- articles
- revision passes on drafts that feel generic or machine-written

## Files

- `SKILL.md` — the skill itself (workflow + worldview)
- `references/anti_tells.md` — line-level patterns and rewrite tactics
- `references/paragraphing.md` — paragraph and structure-level diagnostics
- `references/rhythm.md` — sentence shapes, prosody, the Provost passage
- `references/word_watchlist.md` — empirically over-represented LLM vocabulary

## Install

Clone into your Claude Code skills directory:

```bash
git clone https://github.com/Apolotary/unslop-writing.git ~/.claude/skills/unslop-writing
```

Or for a specific project only:

```bash
git clone https://github.com/Apolotary/unslop-writing.git .claude/skills/unslop-writing
```

Then use it as `/unslop-writing` in Claude Code.

## Notes

This skill is intentionally style-agnostic. It is for making writing better, not for copying authors.

The reference files draw on:

- empirical LLM stylometry (Kobak et al. 2025; Reinhart et al. 2025)
- contemporary editor and critic tactics (Hollis Robbins, Brandon Taylor, Lincoln Michel, Henrik Karlsson)
- canonical writing-craft sources (Klinkenborg, Le Guin, Saunders, McPhee, Provost, Lanham, Burroway, Zinsser)
