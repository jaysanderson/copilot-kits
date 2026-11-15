"""Generate an original, royalty-free ambient music bed and mix it under a
video's narration with sidechain ducking.

The bed is synthesised from scratch (summed sine tones forming a slow warm
chord progression), so there is no licensing risk - safe for customer-facing
video. It is mixed LOW and ducks automatically whenever the voice is present,
so narration always stays clear. Swap in a supplied track later by passing it
to --track instead of synthesising.

Usage:
    # synthesise a bed and mix it under a narrated video
    python scripts/music_bed.py --video videos/talk.mp4 --out videos/talk-music.mp4

    # use a supplied licensed track instead of the synth bed
    python scripts/music_bed.py --video videos/talk.mp4 --track music/bed.mp3 \
        --out videos/talk-music.mp4
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from assemble import probe_dur  # sibling helper

# I - vi - IV - V in C: a warm, unobtrusive loop. Each chord = root/third/fifth,
# kept in a low-mid octave so it sits under speech.
CHORDS = [
    (130.81, 164.81, 196.00),   # C major
    (110.00, 130.81, 164.81),   # A minor
    (87.31, 110.00, 130.81),    # F major
    (98.00, 123.47, 146.83),    # G major
]


def chord_wav(freqs, seconds, out):
    """One soft, warm chord: summed sines, gentle swell, lowpass + a little air."""
    expr = "+".join(f"0.30*sin(2*PI*{f}*t)" for f in freqs)
    aev = f"aevalsrc={expr}:d={seconds}:s=44100:c=stereo"
    af = (f"afade=t=in:d=0.6,afade=t=out:st={seconds-0.8}:d=0.8,"
          f"lowpass=f=1600,aecho=0.8:0.7:70:0.30,volume=0.9")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", aev, "-af", af,
         "-c:a", "pcm_s16le", str(out)],
        check=True, capture_output=True,
    )


def build_bed(duration, bar, gain, tmp):
    """Crossfade the chords into a loop, tile it to cover `duration`, top & tail
    with long fades, and set the overall (low) level."""
    chords = []
    for i, freqs in enumerate(CHORDS):
        w = tmp / f"chord-{i}.wav"
        chord_wav(freqs, bar, w)
        chords.append(w)

    # Chain acrossfades so the progression flows rather than blocks.
    prog = tmp / "prog.wav"
    xf = 0.5
    inputs = []
    for w in chords:
        inputs += ["-i", str(w)]
    n = len(chords)
    parts, prev = [], "0:a"
    for i in range(1, n):
        label = f"x{i}"
        parts.append(f"[{prev}][{i}:a]acrossfade=d={xf}:c1=tri:c2=tri[{label}]")
        prev = label
    fc = ";".join(parts)
    subprocess.run(
        ["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", f"[{prev}]",
         "-c:a", "pcm_s16le", str(prog)],
        check=True, capture_output=True,
    )

    bed = tmp / "bed.wav"
    # Loop the progression to cover the whole video, then global fade + low gain.
    af = (f"afade=t=in:d=2.5,afade=t=out:st={max(0.0, duration-5)}:d=5,"
          f"volume={gain}")
    subprocess.run(
        ["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(prog),
         "-t", f"{duration}", "-af", af, "-c:a", "pcm_s16le", str(bed)],
        check=True, capture_output=True,
    )
    return bed


def mix(video, bed, out):
    """Duck the bed under the voice (sidechain), then mix; copy video untouched."""
    fc = (
        "[1:a]aformat=channel_layouts=stereo[bed];"
        "[0:a]aformat=channel_layouts=stereo[voc];"
        "[bed][voc]sidechaincompress=threshold=0.02:ratio=8:attack=5:"
        "release=400[bedduck];"
        "[voc][bedduck]amix=inputs=2:duration=first:normalize=0[a]"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video), "-i", str(bed),
         "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", str(out)],
        check=True, capture_output=True,
    )


def main():
    p = argparse.ArgumentParser(description="Ambient music bed under a narrated video")
    p.add_argument("--video", required=True, help="Input narrated mp4")
    p.add_argument("--out", required=True, help="Output mp4 with music")
    p.add_argument("--track", help="Supplied licensed track (skips the synth bed)")
    p.add_argument("--gain", type=float, default=0.11,
                   help="Bed level, 0-1 (default 0.11 ~ subtle)")
    p.add_argument("--bar", type=float, default=9.0, help="Seconds per chord")
    args = p.parse_args()

    dur = probe_dur(args.video)
    if dur <= 0:
        sys.exit(f"Could not read duration of {args.video}")

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        if args.track:
            # Loop/trim the supplied track to length, apply fades + gain.
            bed = tmp / "bed.wav"
            af = (f"afade=t=in:d=2.5,afade=t=out:st={max(0.0, dur-5)}:d=5,"
                  f"volume={args.gain}")
            subprocess.run(
                ["ffmpeg", "-y", "-stream_loop", "-1", "-i", args.track,
                 "-t", f"{dur}", "-af", af, "-c:a", "pcm_s16le", str(bed)],
                check=True, capture_output=True,
            )
        else:
            bed = build_bed(dur, args.bar, args.gain, tmp)

        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        mix(args.video, bed, out)

    print(f"Saved {out} ({probe_dur(out):.1f}s, bed gain={args.gain}, "
          f"{'supplied track' if args.track else 'synth bed'})")


if __name__ == "__main__":
    main()
