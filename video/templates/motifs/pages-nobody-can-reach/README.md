# Motif: pages nobody can reach (`m-nv`)

287 small page tiles already filling the frame in a loose drifting grid, each carrying one ruled title line, with one tile near the centre lit

**Performs:** Fourteen lit tiles as a tiny island in a field of 287. The ratio is seen rather than stated, and the pain STOPS here - the 213 and the 58-page hole belong to the live relief, so the animation never performs the solution.

**When to use:** Any coverage, reach or recall measurement where a ratio has to be FELT rather than stated. Swap the two counters and it carries a different measure unchanged.

**Built 9 Oct 2026** for `videos/university` segment S6, on the Progress navy
stage with the Progress palette. Eye-read at preview resolution before use; frames under
`videos/university/preview/pages-nobody-can-reach/`.

## What it performs

A 287 counter sets and the field ripples outward from the lit tile; menu links draw out in two steps and fourteen tiles light, one per 40ms, counted on screen as they go; the remaining 273 go dead grey at once

## Interior (591 child elements)

| id | kind | count | must read |
|---|---|---|---|
| `page_tiles` | page tile | 287 | texture |
| `tile_title_lines` | ruled line | 287 | texture |
| `lit_tile` | page tile, lit | 1 | texture |
| `menu_links` | svg stroke | 14 | texture |
| `counters` | counter 72px and 54px | 2 | **yes** |

**Must read at or above 54px authored:** counters
**Texture, exempt by name:** tile_title_lines
**Subject present at t=0** (GRAMMAR rule 7): page_tiles, tile_title_lines, lit_tile

**Timing:** internal timeline 10.5s, read from the composition's own
`data-duration` and NOT from the storyboard - the storyboard carries the beat's planned
window, the composition carries the fact. Event constants are at the top of the script;
re-derive them from the host's own narration alignment when reusing.

## Things that are the argument, not the styling

1. The reached tiles are CLUSTERED around the home tile, not scattered. A menu reaches its own neighbourhood; scattering them would make the island look like coverage.

2. The pain STOPS at the island. The larger number that the product achieves belongs to the live footage - if this animation also performed the solution, the segment would have no relief left to show.

3. The reached state is set with tl.set(), not a classList callback. Same seek-safety class as m-bl's counter: anything that must be TRUE AT A TIME is a tween or a set, never a callback. Verified by sampling the rendered pixel, not by eye: home rgb(0,181,99), reached rgb(22,115,78), dead navy.

## Grammar

`videos/_motifs/GRAMMAR.md` is canonical. This motif inherits its structural rules - rule 4
(a broken stroke is a broken thing), rule 5 (things TRAVEL, they do not fade), rule 7 (the
subject is on screen from t=0) and the banned set. It does NOT use rule 2's three reserved
strokes: no motif in this film uses a dashed state stroke, so a dashed line here can never
be mistaken for an architecture state.
