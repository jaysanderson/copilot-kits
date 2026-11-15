"""Burned-in captions from ElevenLabs character-level timestamps.

Why this exists: LinkedIn and most feeds autoplay muted, so an uncaptioned
narrated video is dead weight there. And why it is built this way: the ffmpeg on
this machine is compiled WITHOUT libass/freetype/fontconfig, so `drawtext`,
`subtitles` and `ass` do not exist (`brew deps ffmpeg` lists no text-rendering
dependency at all). Text is therefore rendered with Pillow - which also gives
real kerning, wrapping and Progress Sans - and composited with `overlay`.

Timing comes from the TTS call itself (`/with-timestamps` returns per-character
start/end times), so no speech-to-text and no guesswork is involved.

Flow:
    alignment  -> words_from_alignment()  -> cues_from_words()
              -> render_cue()  (Pillow, one PNG per cue)
              -> build_strip() (alpha video, qtrle/argb)
              -> burn()        (single ffmpeg overlay)
"""
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from assemble import ENCODE, _font, probe_dur

W, H = 1920, 1080
BAND_W, BAND_H = 1920, 260
# Sit captions in the lower-third safe zone, NOT hard against the frame edge: a
# video player's scrubber/control bar overlays the bottom ~10% and clips a caption
# placed there (it reads as "no subtitles"). 132px clears typical player chrome.
MARGIN_BOTTOM = 132

PLATE = (8, 12, 30, 236)      # near-black, near-opaque so text never washes out
PLATE_PAD = (40, 22)
TEXT_COL = (255, 255, 255, 255)
STROKE_COL = (0, 0, 0, 235)   # dark stroke keeps text legible over any scene
STROKE_W = 3


def words_from_alignment(alignment, offset=0.0):
    """Character alignment -> [(word, start, end)].

    ElevenLabs v3 audio tags (`[pause]`, `[serious]`, ...) are stage directions in
    the source script, not spoken content - but the character alignment still
    reports positions for their literal bracket text, so a naive space-split turns
    "[pause]" into a caption word and burns it into the video. Every char inside a
    `[...]` span is dropped before word-building, not just skipped as whitespace,
    so a multi-word tag like "[long pause]" can't leak out as two stray words.
    """
    chars = alignment["characters"]
    starts = alignment["character_start_times_seconds"]
    ends = alignment["character_end_times_seconds"]

    words, buf, w_start, depth = [], "", None, 0
    for ch, cs, ce in zip(chars, starts, ends):
        if ch == "[":
            if buf:
                words.append((buf, w_start + offset, ce + offset))
                buf, w_start = "", None
            depth += 1
            continue
        if ch == "]" and depth > 0:
            depth -= 1
            continue
        if depth > 0:
            continue
        if ch.isspace():
            if buf:
                words.append((buf, w_start + offset, ce + offset))
                buf, w_start = "", None
            continue
        if not buf:
            w_start = cs
        buf += ch
    if buf:
        words.append((buf, w_start + offset, ends[-1] + offset))
    return words


def cues_from_words(words, max_chars=46, max_dur=3.2, max_gap=0.7, soft_at=0.6):
    """Group words into readable cues.

    Break points, in order of preference: sentence end, a clause boundary once
    the cue is past `soft_at` of its budget, a long pause, then the hard budget.
    Preferring clause boundaries stops cues snapping mid-phrase, and trailing
    separators are trimmed so a caption never ends on a dangling comma.
    """
    cues, cur, start = [], [], None
    for i, (w, ws, we) in enumerate(words):
        if not cur:
            start = ws
        cur.append((w, ws, we))
        text = " ".join(x[0] for x in cur)

        ends_sentence = w.endswith((".", "!", "?", ":"))
        ends_clause = w.endswith((",", ";", "-"))
        next_gap = (words[i + 1][1] - we) if i + 1 < len(words) else 0.0
        over_budget = len(text) >= max_chars or (we - start) >= max_dur
        soft_ready = len(text) >= max_chars * soft_at
        last = i == len(words) - 1

        if (last or ends_sentence or over_budget or next_gap >= max_gap
                or (ends_clause and soft_ready)):
            cues.append({"text": text.rstrip(",;- "),
                         "start": round(start, 3), "end": round(we, 3)})
            cur, start = [], None
    return cues


def _wrap(draw, text, font, max_w):
    words, lines, line = text.split(), [], ""
    for w in words:
        trial = f"{line} {w}".strip()
        if draw.textlength(trial, font=font) <= max_w or not line:
            line = trial
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def render_cue(text, out_png, size=52):
    """One caption plate as a transparent-background PNG band.

    Progress Sans Text (not Display) - branding rule 4 puts captions in the Text
    face, and never mixes the two.
    """
    img = Image.new("RGBA", (BAND_W, BAND_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _font(size, "Text", "Md")

    max_text_w = int(BAND_W * 0.78)
    lines = _wrap(draw, text, font, max_text_w)
    while len(lines) > 2 and size > 30:
        size -= 3
        font = _font(size, "Text", "Md")
        lines = _wrap(draw, text, font, max_text_w)

    line_h = int(size * 1.32)
    text_w = max(draw.textlength(l, font=font) for l in lines)
    block_w = int(text_w) + PLATE_PAD[0] * 2
    block_h = line_h * len(lines) + PLATE_PAD[1] * 2
    x0 = (BAND_W - block_w) // 2
    y0 = BAND_H - block_h

    draw.rounded_rectangle([x0, y0, x0 + block_w, y0 + block_h], radius=14, fill=PLATE)
    y = y0 + PLATE_PAD[1]
    for line in lines:
        lw = draw.textlength(line, font=font)
        draw.text(((BAND_W - lw) / 2, y), line, font=font, fill=TEXT_COL,
                  stroke_width=STROKE_W, stroke_fill=STROKE_COL)
        y += line_h

    img.save(out_png)


def build_strip(cues, total_dur, work, fps=30):
    """All cues as one alpha video, so compositing is a single overlay input.

    One ffmpeg input per cue would mean hundreds of inputs on a long piece; a
    single pre-rendered alpha strip stays flat regardless of length.
    """
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    blank = work / "cue-blank.png"
    Image.new("RGBA", (BAND_W, BAND_H), (0, 0, 0, 0)).save(blank)

    entries, t = [], 0.0
    for i, cue in enumerate(cues):
        if cue["start"] > t + 1e-3:
            entries.append((blank, cue["start"] - t))
        png = work / f"cue-{i:04d}.png"
        render_cue(cue["text"], png)
        entries.append((png, max(0.2, cue["end"] - cue["start"])))
        t = cue["end"]
    if total_dur > t:
        entries.append((blank, total_dur - t))

    listing = "".join(
        f"file '{p.resolve()}'\nduration {d:.3f}\n" for p, d in entries
    ) + f"file '{entries[-1][0].resolve()}'\n"   # concat demuxer needs the tail repeated
    lst = work / "cues.txt"
    lst.write_text(listing)

    strip = work / "caption-strip.mov"
    # -t pins the strip to the video's length. The concat demuxer needs the tail
    # file repeated with no duration, which otherwise runs the strip past the end.
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-vf", f"fps={fps},format=argb", "-t", f"{total_dur}",
         "-c:v", "qtrle", str(strip)],
        check=True, capture_output=True,
    )
    return strip


def burn(video, cues, out, work):
    """Composite the caption strip onto the video, audio untouched."""
    dur = probe_dur(video)
    strip = build_strip(cues, dur, work)
    # `overlay` runs to whichever input is longer, so a strip even slightly longer
    # than the source stretched the VIDEO track past the audio - a captioned cut
    # silently gained a 0.9s mute tail and its streams no longer matched. -t makes
    # the source's own duration authoritative.
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video), "-i", str(strip),
         "-filter_complex",
         f"[0:v][1:v]overlay=x=0:y=H-h-{MARGIN_BOTTOM}:format=auto[v]",
         "-map", "[v]", "-map", "0:a", "-t", f"{dur}", *ENCODE, str(out)],
        check=True, capture_output=True,
    )


def save_cues(cues, path):
    Path(path).write_text(json.dumps(cues, indent=2))


def load_cues(path):
    return json.loads(Path(path).read_text())
