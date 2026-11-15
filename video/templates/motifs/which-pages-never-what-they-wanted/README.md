# Motif: which pages, never what they wanted (`m-bl`)

A competent ordinary analytics chart already drawn: twelve bars, twelve page labels, an axis, four gridlines, a heading block and a visit counter

**Performs:** The chart got bigger and the knowledge got smaller, in one picture, with eleven ghosts of dissolved questions littering the upper frame.

**When to use:** Any analytics-blindness or measurement-gap pain: the instrument is working and is measuring the wrong thing.

**Built 9 Oct 2026** for `videos/university` segment S5, on the Progress navy
stage with the Progress palette. Eye-read at preview resolution before use; frames under
`videos/university/preview/which-pages-never-what-they-wanted/`.

## What it performs

The bars rise and the counter increments; a visitor disc arrives at the tallest bar and a thought pill forms above it carrying a real question in words; the pill does NOT enter the chart, it rises and dissolves at the frame edge; ten more discs arrive and ten more pills dissolve the same way while the bars grow taller

## Interior (64 child elements)

| id | kind | count | must read |
|---|---|---|---|
| `bars` | bar | 12 | texture |
| `page_labels` | ruled label | 12 | texture |
| `axis` | axis | 1 | texture |
| `gridlines` | rule | 4 | texture |
| `heading_block` | block | 1 | texture |
| `visit_counter` | counter 54px | 1 | **yes** |
| `visitor_discs` | disc | 11 | texture |
| `question_pills` | pill with text 54px | 11 | **yes** |
| `ghost_traces` | faint trace | 11 | texture |

**Must read at or above 54px authored:** visit_counter, question_pills
**Texture, exempt by name:** page_labels, gridlines
**Subject present at t=0** (GRAMMAR rule 7): bars, page_labels, axis, gridlines, heading_block, visit_counter

**Timing:** internal timeline 10.0s, read from the composition's own
`data-duration` and NOT from the storyboard - the storyboard carries the beat's planned
window, the composition carries the fact. Event constants are at the top of the script;
re-derive them from the host's own narration alignment when reusing.

## Things that are the argument, not the styling

1. THE CHART MUST BE ORDINARY AND HEALTHY. The pain is that the chart is fine, so drawing it as broken inverts the motif.

2. The question pills DO NOT ENTER THE CHART. They rise, thin and dissolve, and the ghosts they leave accumulate in the upper frame while the bars grow taller. The chart getting BIGGER as the knowledge gets smaller is the single picture.

3. Each pill has its own lane. Pass one started all eleven at the same x and four stacked into unreadable mush.

4. The view counter is driven by stepped tl.set() calls, NOT by a tween's onUpdate. A callback closure does not re-run when a paused timeline is seeked, so the counter read its start value on every sampled frame - alive in the source, dead on screen.

## Grammar

`videos/_motifs/GRAMMAR.md` is canonical. This motif inherits its structural rules - rule 4
(a broken stroke is a broken thing), rule 5 (things TRAVEL, they do not fade), rule 7 (the
subject is on screen from t=0) and the banned set. It does NOT use rule 2's three reserved
strokes: no motif in this film uses a dashed state stroke, so a dashed line here can never
be mistaken for an architecture state.

## TRAP: the counter is a FABRICATED STATISTIC (found 9 Oct 2026, suppressed not fixed)

`#bl-count` animates **18,402 to 23,915 "PAGE VIEWS"** (markup line 59, arithmetic line
136). Nobody measured either number. On the University film it sat on a beat about that
customer's own insights surface and read as **their** figure - a fabricated statistic on
screen, which is hard rule 3 whether or not the narration says it.

**The University film SUPPRESSES it with a host CSS override (`#bl-count {display:none}`),
it does not fix it.** The numbers are still here and the next film to use this motif
inherits them. Decide deliberately rather than by default: either supply a real measured
figure through a variable, or delete the counter.

**Why nothing caught it:** a placeholder that looks like DATA is more dangerous than one
that looks like a placeholder, because nobody flags it. No gate check covers invented
numerals and no viewer reported it.

**And it is only half visible to the obvious scan.** A sweep of rendered HTML text nodes
across all 18 motifs finds 11 numerals and catches `18,402` - but `23915` lives in JS
arithmetic, so the scan found this one by luck, through its start value. **The blind
class is any numeral computed or injected at run time.** The other ten are dates or real
measured figures (`343`, `287`, `14` are University's verified crawl counts), except
`the-joins-are-yours`' "15 applied patterns / 1 / 13 / 1 / 2 / 3", which belongs to
another film and whose provenance this sweep did not establish.
