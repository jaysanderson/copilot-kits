# Motif: a language it cannot hear (`m-lg`)

A populated page plate - header, wordmark block, five nav items, a search field with a visible text cursor, three content cards with ruled lines - and four question pills in English, Mandarin, Arabic and Bahasa Indonesia already at rest in the margin

**Performs:** Three of four people end up outside the page, and the Arabic one visibly cannot even be typed into it.

**When to use:** Any multilingual or accessibility pain. The RTL detail transfers to any film that needs to show a surface excluding somebody.

**Built 9 Oct 2026** for `videos/university` segment S2, on the Progress navy
stage with the Progress palette. Eye-read at preview resolution before use; frames under
`videos/university/preview/a-language-it-cannot-hear/`.

## What it performs

The English pill seats and four result lines slide up; the Mandarin pill seats and the results collapse to one empty ruled line; the Arabic pill CANNOT seat, because the field's cursor is on the left while the glyphs run right to left, and the field's stroke goes alarm; all three non-English pills drift out of the plate into dead space

## Interior (31 child elements)

| id | kind | count | must read |
|---|---|---|---|
| `page_plate` | boundary | 1 | texture |
| `header_bar` | bar | 1 | texture |
| `wordmark_block` | mark | 1 | texture |
| `nav_items` | ruled label | 5 | texture |
| `search_field` | field | 1 | texture |
| `text_cursor` | caret | 1 | texture |
| `content_cards` | card | 3 | texture |
| `card_lines` | ruled line | 9 | texture |
| `result_lines` | ruled result row | 4 | texture |
| `empty_result` | ruled row, empty | 1 | texture |
| `question_pills` | pill with script text 54px | 4 | **yes** |

**Must read at or above 54px authored:** question_pills
**Texture, exempt by name:** nav_items, card_lines, result_lines
**Subject present at t=0** (GRAMMAR rule 7): page_plate, header_bar, wordmark_block, nav_items, search_field, text_cursor, content_cards, card_lines, question_pills

**Timing:** internal timeline 9.0s, read from the composition's own
`data-duration` and NOT from the storyboard - the storyboard carries the beat's planned
window, the composition carries the fact. Event constants are at the top of the script;
re-derive them from the host's own narration alignment when reusing.

## Things that are the argument, not the styling

1. ENGLISH SEATS FIRST AND THE PAGE ANSWERS. Showing what working looks like is not throat-clearing - the failure has nothing to be measured against without it.

2. The Arabic pill CANNOT SEAT because the caret is on the LEFT while the glyphs run right to left. That specific, true, unglamorous mechanism is the whole motif. A generic 'it fails' gesture would be worth nothing.

3. The pills rest OUTSIDE the plate, in dead stage. Pass one had three of four sitting on top of the page they are locked out of, which destroyed the only idea the shot has. Check the margin arithmetic before rendering: longest pill plus padding must clear the plate's left edge.

## Grammar

`videos/_motifs/GRAMMAR.md` is canonical. This motif inherits its structural rules - rule 4
(a broken stroke is a broken thing), rule 5 (things TRAVEL, they do not fade), rule 7 (the
subject is on screen from t=0) and the banned set. It does NOT use rule 2's three reserved
strokes: no motif in this film uses a dashed state stroke, so a dashed line here can never
be mistaken for an architecture state.
