"""Assemble a multi-segment narrated demo video: title card + N (clip, voice) segment
pairs, each held to its own voiceover length + CTA card. Segment-per-beat sibling to
assemble.py's single-clip flow - use this when a demo walkthrough is narrated as several
short beats (one recording + one TTS pass per app/scene) rather than one continuous take,
the same idea as narrate_deck.py's per-slide model applied to video.

Usage:
    python scripts/assemble_segments.py \
        --segments videos/work/seg-01.mp4:videos/work/vo-01.mp3 \
                   videos/work/seg-02.mp4:videos/work/vo-02.mp3 \
        --brand brand --title "..." --cta "..." --out videos/out.mp4
"""
import argparse
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assemble import card_segment, concat, demo_segment, load_brand, make_card, probe_dur


def main():
    parser = argparse.ArgumentParser(description="Assemble a multi-segment narrated demo video")
    parser.add_argument("--segments", nargs="+", required=True,
                         help="clip.mp4:voice.mp3 pairs, in play order")
    parser.add_argument("--brand", default="brand", help="Brand kit name in brand/")
    parser.add_argument("--title", required=True, help="Title-card text")
    parser.add_argument("--cta", default="Let's talk.", help="CTA end-card text")
    parser.add_argument("--card-seconds", type=float, default=3.0, help="Card hold time")
    parser.add_argument("--out", required=True, help="Output mp4 to videos/")
    args = parser.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"{tool} not found. brew install ffmpeg.")

    pairs = []
    for spec in args.segments:
        clip, _, voice = spec.partition(":")
        if not voice:
            sys.exit(f"Bad --segments entry (need clip.mp4:voice.mp3): {spec}")
        pairs.append((clip, voice))

    brand = load_brand(args.brand)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        title_png, cta_png = tmp / "title.png", tmp / "cta.png"
        make_card(args.title, brand, title_png)
        make_card(args.cta, brand, cta_png)

        segs = [tmp / "s_title.mp4"]
        card_segment(title_png, args.card_seconds, segs[0])
        for i, (clip, voice) in enumerate(pairs, start=1):
            seg_out = tmp / f"s_{i:02d}.mp4"
            demo_segment(clip, voice, seg_out)
            segs.append(seg_out)
        cta_seg = tmp / "s_cta.mp4"
        card_segment(cta_png, args.card_seconds, cta_seg)
        segs.append(cta_seg)

        concat(segs, out_path)

    print(f"Saved {out_path} ({probe_dur(out_path):.1f}s)")


if __name__ == "__main__":
    main()
