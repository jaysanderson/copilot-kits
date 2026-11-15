"""Turn a deck's speaker notes into a narrated MP4 (slide-synced explainer video).

For each slide it: cleans the speaker note into a spoken talk track, sends it to
ElevenLabs TTS, holds that slide's image for the length of the narration (plus a
short breath), then concatenates every slide into one 1920x1080 MP4. The talk
track is the deck's own speaker notes, so the voice stays consistent with the
deck - the video is just the deck, narrated.

Notes are cleaned before speaking: the leading "[0:00-0:45] LABEL. direction"
line is dropped, any trailing "Source: ... - URL" line is dropped, and
parenthetical stage directions "(Wait. Let it breathe.)" are removed - none of
those are meant to be read aloud.

Usage:
    python scripts/narrate_deck.py \
        --deck decks/imedia-fomau-progress-v2-2026-07-03.pptx \
        --slides "videos/slides/s-%02d.jpg" \
        --voice hope \
        --out videos/john-ai-that-delivers.mp4
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from pptx import Presentation

# Sibling helpers (this script's dir is on sys.path when run directly).
from voiceover import (DEFAULT_SEED, ROOT, load_env, resolve_pool, resolve_voice,
                       synth, synth_timed)
from assemble import concat, normalise_audio, probe_dur
from motion import kenburns_chain, amount_for_duration, pick_motion

W, H = 1920, 1080

TIMING_RE = re.compile(r"^\s*\[\d+:\d+")   # "[0:00-0:45] OPEN. ..."
PAREN_RE = re.compile(r"\([^)]*\)")

# Only parentheticals built purely from this vocabulary are treated as stage
# directions. The old rule stripped EVERY parenthetical, which silently deleted
# legitimate spoken content - "(capped at the statutory percentage of the
# purchase price)" is exactly the shape that used to vanish from the talk track.
STAGE_WORDS = {
    "a", "an", "and", "aside", "beat", "breath", "breathe", "brief", "briefly",
    "camera", "click", "crisp", "cut", "direction", "down", "dry", "emphasis",
    "emphasise", "emphasize", "faster", "firmly", "gesture", "hold", "hover",
    "in", "it", "let", "long", "look", "louder", "note", "on", "pause", "point",
    "quietly", "screen", "scroll", "short", "slower", "smile", "softer", "stop",
    "the", "then", "to", "up", "wait", "warmly",
}


def _is_stage_direction(inner):
    """True only when every word is stage vocabulary and no figures appear."""
    if any(ch.isdigit() for ch in inner):     # numbers are content, never direction
        return False
    words = re.findall(r"[A-Za-z']+", inner)
    return bool(words) and all(w.lower() in STAGE_WORDS for w in words)


def clean_note(note):
    """Strip stage directions, the timing/label line and the Source line so only
    the spoken talk track survives."""
    lines = note.splitlines()
    kept = []
    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue
        if i == 0 and TIMING_RE.match(s):        # timing + label + direction
            continue
        if s.lower().startswith("source:"):       # citation, on-slide not spoken
            continue
        kept.append(s)
    text = " ".join(kept)
    text = PAREN_RE.sub(
        lambda m: "" if _is_stage_direction(m.group(0)[1:-1]) else m.group(0), text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def slide_segment(img, voice, gap, out, motion="in", amount=None, fps=30,
                  anchor=None):
    """One slide held for the narration length + a breath, with a slow push.

    A deck slide previously sat as a dead still for its whole narration - on one
    shipped video that averaged ~18 seconds of motionless frame per slide. A
    subtle Ken Burns move keeps it alive without turning into a slideshow
    effect. Motion is delegated to scripts/motion.py, which renders the pan at
    3x the output resolution and lanczos-downscales it (killing the integer-crop
    judder the old 2x zoompan shimmered with on fine slide text), eases the move
    in and out instead of ramping linearly, and gentles the amount on longer
    holds. amount=None lets that helper pick a duration-aware default.
    """
    adur = probe_dur(voice)
    dur = adur + gap
    frames = max(2, int(round(dur * fps)))
    if amount is None:
        amount = amount_for_duration(dur)

    chain = kenburns_chain(motion, amount, frames, fps, W, H, anchor=anchor)
    vf = (f"[0:v]{chain}[v];"
          f"[1:a]apad=pad_dur={gap},"
          f"aformat=sample_rates=48000:channel_layouts=stereo[a]")
    subprocess.run(
        ["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-i", str(voice),
         "-filter_complex", vf, "-map", "[v]", "-map", "[a]", "-t", f"{dur}",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", str(out)],
        check=True, capture_output=True,
    )
    return dur


def mix_music(video, music, gain_db, out):
    """Lay a music bed under a narrated video, ducked when the voice is present.

    The bed sits at `gain_db` below unity and a sidechain compressor pulls it down
    further whenever the narration is speaking, so the voice always stays on top.
    """
    gain = 10 ** (gain_db / 20.0)   # dB -> linear
    fc = (
        f"[1:a]volume={gain:.4f}[bed];"
        f"[bed][0:a]sidechaincompress=threshold=0.02:ratio=8:attack=5:release=350[duck];"
        f"[0:a][duck]amix=inputs=2:duration=first:normalize=0[a]"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video),
         "-stream_loop", "-1", "-i", str(music),
         "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-shortest", str(out)],
        check=True,
    )


def main():
    p = argparse.ArgumentParser(description="Narrate a deck into a slide-synced MP4")
    p.add_argument("--deck", required=True, help="Source .pptx (for speaker notes)")
    p.add_argument("--slides", required=True,
                   help="printf pattern for slide images, e.g. videos/slides/s-%%02d.jpg")
    p.add_argument("--voice", default=None,
                   help="Single voice name; omit to rotate the approved pool")
    p.add_argument("--rotate", action="store_true",
                   help="Force pool rotation even when --voice is given")
    p.add_argument("--out", required=True, help="Output mp4 path")
    p.add_argument("--model", default="eleven_v3", help="ElevenLabs model id")
    p.add_argument("--seed", type=int, default=DEFAULT_SEED,
                   help="Pinned sampling seed for reproducible takes")
    p.add_argument("--gap", type=float, default=0.8, help="Breath after each slide (s)")
    p.add_argument("--xfade", type=float, default=0.5,
                   help="Cross-dissolve between slides (0 = hard cuts)")
    p.add_argument("--motion", choices=["in", "out", "alternate", "none"],
                   default="alternate", help="Ken Burns move on each slide")
    p.add_argument("--captions", action="store_true",
                   help="Burn word-timed captions (for muted autoplay feeds)")
    p.add_argument("--no-normalise", action="store_true",
                   help="Skip the final EBU R128 loudness pass")
    p.add_argument("--music", help="Optional music-bed audio file, ducked under the voice")
    p.add_argument("--music-gain", type=float, default=-18.0,
                   help="Music-bed level below unity in dB (default -18)")
    p.add_argument("--work", default="videos/narrate-work", help="Scratch dir")
    p.add_argument("--reuse", action="store_true",
                   help="Reuse existing per-slide mp3s instead of re-synthesising")
    args = p.parse_args()

    load_env(ROOT)
    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        sys.exit("ELEVENLABS_API_KEY not set. Populate .env (see .env.example).")

    # voices.json has mandated rotating the approved pool across multi-segment
    # narration since 2026-07-06; a single voice throughout is what made long
    # pieces feel monotone. Rotation is now the default, not an opt-in.
    pool = resolve_pool()
    if args.voice and not args.rotate:
        voices = [(args.voice, resolve_voice(args.voice))]
    elif pool:
        voices = pool
    else:
        voices = [("hope", resolve_voice("hope"))]

    prs = Presentation(args.deck)
    n = len(prs.slides)
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)

    # Collect every talk track first, so each synth call can be given the
    # neighbouring text for prosody continuity.
    notes = []
    for i, slide in enumerate(prs.slides, 1):
        img = Path(args.slides % i)
        if not img.exists():
            sys.exit(f"Missing slide image: {img}")
        raw = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
        text = clean_note(raw)
        if not text:
            sys.exit(f"Slide {i} has no speaker note to narrate.")
        notes.append((img, text))

    segments, durations, alignments = [], [], []
    for i, (img, text) in enumerate(notes, 1):
        vname, vid = voices[(i - 1) % len(voices)]
        vo = work / f"vo-{i:02d}.mp3"
        al_path = work / f"al-{i:02d}.json"

        if args.reuse and vo.exists() and (not args.captions or al_path.exists()):
            alignment = json.loads(al_path.read_text()) if al_path.exists() else None
        else:
            print(f"[{i:02d}/{n}] synth {len(text)} chars, voice={vname}...", flush=True)
            prev_text = notes[i - 2][1] if i >= 2 else None
            next_text = notes[i][1] if i < len(notes) else None
            if args.captions:
                alignment = synth_timed(text, vid, api_key, vo, model=args.model,
                                        previous_text=prev_text, next_text=next_text,
                                        seed=args.seed)
                al_path.write_text(json.dumps(alignment))
            else:
                synth(text, vid, api_key, vo, model=args.model,
                      previous_text=prev_text, next_text=next_text, seed=args.seed)
                alignment = None
        alignments.append(alignment)

        motion = args.motion
        anchor = None
        if motion == "alternate":
            # Vary push-in / push-out / gentle drift / hold across the deck so
            # the move never reads as the same mechanical zoom on every slide.
            motion, anchor = pick_motion(i - 1)
        seg = work / f"seg-{i:02d}.mp4"
        dur = slide_segment(img, vo, args.gap, seg, motion=motion, anchor=anchor)
        durations.append(dur)
        segments.append(seg)
        print(f"  slide {i:02d}: {dur:5.1f}s  voice={vname}  motion={motion}", flush=True)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    stage = work / "stage-joined.mp4"
    concat(segments, stage, xfade=args.xfade)

    if args.music:
        mixed = work / "stage-music.mp4"
        mix_music(stage, Path(args.music), args.music_gain, mixed)
        stage = mixed
        print(f"  mixed music bed ({args.music}) at {args.music_gain:.0f} dB, "
              f"ducked under voice")

    if args.captions:
        from captions import burn, cues_from_words, save_cues, words_from_alignment
        # xfade consumes overlap, so each slide starts earlier than a plain
        # concat would put it - caption offsets have to account for that or they
        # drift further out of sync with every slide.
        cues = []
        for i, alignment in enumerate(alignments):
            if not alignment:
                continue
            offset = sum(durations[:i]) - i * args.xfade
            cues += cues_from_words(words_from_alignment(alignment, offset=offset))
        captioned = work / "stage-captioned.mp4"
        burn(stage, cues, captioned, work / "cue-frames")
        save_cues(cues, work / "captions.json")
        stage = captioned
        print(f"  burned {len(cues)} caption cues")

    if args.no_normalise:
        Path(stage).replace(out)
    else:
        m = normalise_audio(stage, out)
        if m:
            print(f"  loudnorm -> was {float(m['input_i']):.1f} LUFS, target -14.0")

    used = ", ".join(sorted({voices[(i) % len(voices)][0] for i in range(len(notes))}))
    print(f"\nSaved {out} ({probe_dur(out):.1f}s over {len(segments)} slides, "
          f"voices={used})")


if __name__ == "__main__":
    main()
