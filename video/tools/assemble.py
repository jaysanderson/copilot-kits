"""Assemble a finished demo video: title card + demo (+ voiceover) + CTA card.

Renders brand-kit title and CTA cards with Pillow, then ffmpeg-stitches:
    [title card] -> [demo video with voiceover] -> [CTA card]
Everything is normalised to 1920x1080 / 30fps / stereo before concat. The demo
segment is held to the voiceover length so narration is never clipped. Outputs
mp4 to videos/.

Usage:
    python scripts/assemble.py --demo videos/demo.mp4 --voice videos/vo.mp3 \
        --brand tangerine --title "Agentic RAG for Tangerine" \
        --cta "Let's talk. progress.com/agentic-rag" --out videos/tangerine-demo.mp4
"""
import argparse
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "brand"
W, H = 1920, 1080

# Progress Sans is the brand face (branding skill rule 4): Display for headlines,
# Text for body/UI/captions, never swapped. Arial is the ONLY approved substitute
# and only when Progress Sans is genuinely absent. Filenames carry an install hash
# suffix, so glob the stem rather than hardcoding a path.
FONT_DIRS = [
    Path("/Library/Fonts/Managed"),
    Path("/Library/Fonts"),
    Path.home() / "Library/Fonts",
]
ARIAL_FALLBACK = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
]


def _find_face(face, weight):
    """Locate a Progress Sans TTF, e.g. face='Display', weight='Bd'."""
    for d in FONT_DIRS:
        if not d.is_dir():
            continue
        hits = sorted(d.glob(f"ProgressSans{face}-{weight}_*.ttf")) or \
               sorted(d.glob(f"ProgressSans{face}-{weight}.ttf"))
        if hits:
            return hits[0]
    return None


def _rgb(hexstr, default):
    if not hexstr:
        return default
    h = hexstr.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _font(size, face="Display", weight="Bd"):
    path = _find_face(face, weight)
    if path:
        return ImageFont.truetype(str(path), size)
    for p in ARIAL_FALLBACK:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def brand_face_report():
    """Which face actually resolved - surfaced at build time so a silent Arial
    fallback can never ship unnoticed again."""
    d, t = _find_face("Display", "Bd"), _find_face("Text", "Rg")
    return (f"Progress Sans Display Bold: {d.name if d else 'MISSING -> Arial'}\n"
            f"  Progress Sans Text Regular: {t.name if t else 'MISSING -> Arial'}")


def load_brand(name):
    path = BRAND / f"{name}.json"
    return json.loads(path.read_text()) if path.exists() else {}


def wrap(draw, text, font, max_w):
    words, lines, line = text.split(), [], ""
    for w in words:
        trial = f"{line} {w}".strip()
        if draw.textlength(trial, font=font) <= max_w:
            line = trial
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def _saturation(rgb):
    r, g, b = [c / 255 for c in rgb]
    mx = max(r, g, b)
    return 0.0 if mx == 0 else (mx - min(r, g, b)) / mx


def _luminance(rgb):
    r, g, b = [c / 255 for c in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def brand_colours(brand):
    """Resolve (background, text, accent) from a kit, deriving from the palette
    when explicit primary/ink are absent (older kits store only `palette`)."""
    pal = [c for c in (_rgb(h, None) for h in brand.get("palette", [])) if c]
    primary = _rgb(brand.get("primary"), None) or (
        max(pal, key=_saturation) if pal else (92, 229, 0))
    ink = _rgb(brand.get("ink"), None)
    if ink is None:
        darks = sorted(pal, key=_luminance)
        ink = darks[0] if darks and _luminance(darks[0]) < 0.4 else primary
    bg = ink
    text = (255, 255, 255) if _luminance(bg) < 0.6 else (20, 20, 20)
    accent = primary if primary != bg else next(
        (c for c in pal if c != bg), (255, 255, 255))
    return bg, text, accent


def load_logo(brand, target_w=260):
    """The kit's OWN mark at target_w, rasterising SVG via CairoSVG.

    Vector kits are the common case (brand_capture.py saves .svg), and the old
    PNG-only gate silently dropped them - a Revolution deliverable shipped with
    a blank title card because of exactly that. Returns None only when the kit
    genuinely has no usable mark; never substitutes another brand's logo.
    """
    name = brand.get("logo", "")
    if not name:
        return None
    path = BRAND / name
    if not path.exists():
        print(f"  ! logo declared but missing: {path}", file=sys.stderr)
        return None
    try:
        if path.suffix.lower() == ".svg":
            import cairosvg
            # Render 4x and downsample: real vector marks come out visibly
            # cleaner. Note this cannot rescue a bitmap-wrapped SVG (several
            # kits captured by brand_capture.py are a base64 <image> inside an
            # <svg>) - those are only as sharp as the bitmap inside them, and
            # the fix there is a genuine vector file from the brand owner.
            png_bytes = cairosvg.svg2png(url=str(path), output_width=target_w * 4)
            logo = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
            logo = logo.resize(
                (target_w, max(1, int(logo.height * target_w / logo.width))),
                Image.LANCZOS)
        else:
            logo = Image.open(path).convert("RGBA")
            logo = logo.resize((target_w, max(1, int(logo.height * target_w / logo.width))))
        return logo
    except Exception as exc:
        print(f"  ! logo unusable ({path.name}): {exc}", file=sys.stderr)
        return None


def fit_lines(draw, text, max_w, max_h, max_lines=3, hi=104, lo=40):
    """Largest Display size that fits the text in <=max_lines within the box.

    The old card hardcoded 84pt, so a long title silently ran wide or pushed the
    accent bar off the card.
    """
    best = None
    for size in range(hi, lo - 1, -4):
        font = _font(size, "Display", "Bd")
        lines = wrap(draw, text, font, max_w)
        line_h = int(size * 1.24)
        if len(lines) <= max_lines and line_h * len(lines) <= max_h:
            return font, lines, line_h
        best = (font, lines, line_h)
    return best


def make_card(text, brand, out_png, accent_bar=True):
    """A clean brand card: brand background, centred text, accent bar, own logo."""
    bg, text_col, accent = brand_colours(brand)
    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)

    logo = load_logo(brand, 260)
    logo_bottom = 90 + (logo.height if logo else 0)

    top = logo_bottom + 80
    font, lines, line_h = fit_lines(draw, text, int(W * 0.80), H - top - 200)
    total_h = line_h * len(lines)
    y = top + max(0, (H - top - 160 - total_h) // 2)
    for line in lines:
        tw = draw.textlength(line, font=font)
        draw.text(((W - tw) / 2, y), line, font=font, fill=text_col)
        y += line_h

    if accent_bar:
        bar_w = 220
        draw.rectangle([(W - bar_w) // 2, y + 24, (W + bar_w) // 2, y + 34], fill=accent)

    if logo:
        img.paste(logo, ((W - logo.width) // 2, 90), logo)
    img.save(out_png)


def probe_dur(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def _pad_source(dur):
    """A soft low ambient pad, as an lavfi source string.

    Cards used to be laid over `anullsrc` - literal digital silence - so every
    assembled video opened on 3 seconds of nothing, which reads as a broken
    file. A quiet lowpassed pad gives the card presence instead.
    """
    tones = "+".join(
        f"{amp}*sin(2*PI*{freq}*t)"
        for freq, amp in ((65.41, 0.16), (130.81, 0.13), (164.81, 0.10), (196.00, 0.08))
    )
    fade = min(1.2, dur / 3.0)
    return (f"aevalsrc='{tones}':d={dur}:s=48000:c=stereo,"
            f"lowpass=f=900,volume=0.5,"
            f"afade=t=in:st=0:d={fade},afade=t=out:st={max(0.0, dur - fade):.3f}:d={fade}")


def card_segment(png, dur, out, bed=None):
    """A brand card held for `dur`, over a music bed or the synthesised pad."""
    if bed:
        audio_in = ["-stream_loop", "-1", "-i", str(bed)]
        fade = min(1.2, dur / 3.0)
        afilter = (f"[1:a]atrim=0:{dur},asetpts=PTS-STARTPTS,volume=0.32,"
                   f"afade=t=in:st=0:d={fade},"
                   f"afade=t=out:st={max(0.0, dur - fade):.3f}:d={fade},"
                   f"aformat=sample_rates=48000:channel_layouts=stereo[a]")
    else:
        audio_in = ["-f", "lavfi", "-i", _pad_source(dur)]
        afilter = "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[a]"

    subprocess.run(
        ["ffmpeg", "-y", "-loop", "1", "-i", str(png), *audio_in,
         "-t", f"{dur}",
         "-filter_complex",
         f"[0:v]scale={W}:{H},fps=30,format=yuv420p[v];{afilter}",
         "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-tune", "stillimage", "-preset", "slow", "-crf", "18",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
         "-shortest", str(out)],
        check=True, capture_output=True,
    )


def demo_segment(demo, voice, out, crop=None):
    """The demo footage, optionally auto-framed, held to the voiceover length."""
    crop_f = f"crop={crop}," if crop else ""
    enc = ["-c:v", "libx264", "-preset", "slow", "-crf", "18",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
    if voice:
        adur, vdur = probe_dur(voice), probe_dur(demo)
        pad = max(0.0, adur - vdur)
        vf = (f"{crop_f}scale={W}:{H},fps=30,format=yuv420p,"
              f"tpad=stop_mode=clone:stop_duration={pad}")
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(demo), "-i", str(voice),
             "-filter_complex",
             f"[0:v]{vf}[v];"
             f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo[a]",
             "-map", "[v]", "-map", "[a]",
             "-t", f"{max(adur, vdur)}", *enc, str(out)],
            check=True, capture_output=True,
        )
    else:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(demo),
             "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
             "-vf", f"{crop_f}scale={W}:{H},fps=30,format=yuv420p",
             "-map", "0:v", "-map", "1:a", "-shortest", *enc, str(out)],
            check=True, capture_output=True,
        )


ENCODE = ["-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
          "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
          "-movflags", "+faststart"]


def concat(segments, out, xfade=0.0):
    """Join segments. With xfade>0 the joins cross-dissolve instead of hard-cutting.

    xfade consumes overlap, so each join's offset is the running length of
    everything already joined, minus one overlap.
    """
    inputs = []
    for seg in segments:
        inputs += ["-i", str(seg)]
    n = len(segments)

    if xfade <= 0 or n < 2:
        streams = "".join(f"[{i}:v][{i}:a]" for i in range(n))
        fc = f"{streams}concat=n={n}:v=1:a=1[v][a]"
        vmap, amap = "[v]", "[a]"
    else:
        durs = [probe_dur(s) for s in segments]
        parts, vlab, alab, acc = [], "0:v", "0:a", durs[0]
        for i in range(1, n):
            offset = max(0.0, acc - xfade)
            nv, na = f"vx{i}", f"ax{i}"
            parts.append(f"[{vlab}][{i}:v]xfade=transition=fade:"
                         f"duration={xfade}:offset={offset:.3f}[{nv}]")
            parts.append(f"[{alab}][{i}:a]acrossfade=d={xfade}:c1=tri:c2=tri[{na}]")
            vlab, alab, acc = nv, na, acc + durs[i] - xfade
        fc = ";".join(parts)
        vmap, amap = f"[{vlab}]", f"[{alab}]"

    subprocess.run(
        ["ffmpeg", "-y", *inputs, "-filter_complex", fc,
         "-map", vmap, "-map", amap, *ENCODE, str(out)],
        check=True, capture_output=True,
    )


def measure_loudness(path):
    """Pass 1 of loudnorm - the measured values feed the corrective pass."""
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    start, end = p.stderr.rfind("{"), p.stderr.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(p.stderr[start:end + 1])
    except json.JSONDecodeError:
        return None


def normalise_audio(src, out, target_i=-14.0, target_tp=-1.5, target_lra=11.0):
    """Two-pass EBU R128 normalisation to the streaming/social target.

    Untreated output measured -18 LUFS with an LRA of ~2.6 - about 4 LU quieter
    than everything around it in a feed. Also forces stereo 48k, which fixes the
    mono/stereo mismatch that made concat fragile.
    """
    m = measure_loudness(src)
    af = f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}"
    if m:
        af += (f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
               f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
               f":offset={m['target_offset']}:linear=true")
    af += ",aformat=sample_rates=48000:channel_layouts=stereo"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-af", af,
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
         "-movflags", "+faststart", str(out)],
        check=True, capture_output=True,
    )
    return m


def main():
    parser = argparse.ArgumentParser(description="Assemble a finished demo video")
    parser.add_argument("--demo", required=True, help="Demo video (mp4/webm)")
    parser.add_argument("--voice", help="Voiceover mp3 (overlaid on the demo)")
    parser.add_argument("--brand", default="brand", help="Brand kit name in brand/")
    parser.add_argument("--title", required=True, help="Title-card text")
    parser.add_argument("--cta", default="Let's talk.", help="CTA end-card text")
    parser.add_argument("--card-seconds", type=float, default=3.0, help="Card hold time")
    parser.add_argument("--music", help="Music bed laid under the title/CTA cards")
    parser.add_argument("--xfade", type=float, default=0.4,
                        help="Cross-dissolve on segment joins (0 = hard cuts)")
    parser.add_argument("--autoframe", action="store_true",
                        help="Detect the demo's content region and crop to it")
    parser.add_argument("--no-normalise", action="store_true",
                        help="Skip the final EBU R128 loudness pass")
    parser.add_argument("--out", required=True, help="Output mp4 to videos/")
    args = parser.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"{tool} not found. brew install ffmpeg.")

    brand = load_brand(args.brand)
    print(f"  fonts -> {brand_face_report()}")
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    crop = None
    if args.autoframe:
        from autoframe import detect_crop
        crop = detect_crop(args.demo)
        print(f"  autoframe -> crop={crop or 'no crop needed'}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        title_png, cta_png = tmp / "title.png", tmp / "cta.png"
        make_card(args.title, brand, title_png)
        make_card(args.cta, brand, cta_png)

        seg_title, seg_demo, seg_cta = tmp / "s0.mp4", tmp / "s1.mp4", tmp / "s2.mp4"
        card_segment(title_png, args.card_seconds, seg_title, bed=args.music)
        demo_segment(args.demo, args.voice, seg_demo, crop=crop)
        card_segment(cta_png, args.card_seconds, seg_cta, bed=args.music)

        joined = tmp / "joined.mp4" if not args.no_normalise else out_path
        concat([seg_title, seg_demo, seg_cta], joined, xfade=args.xfade)

        if not args.no_normalise:
            m = normalise_audio(joined, out_path)
            if m:
                print(f"  loudnorm -> was {float(m['input_i']):.1f} LUFS, "
                      f"target -14.0 LUFS")

    print(f"Saved {out_path} ({probe_dur(out_path):.1f}s)")


if __name__ == "__main__":
    main()
