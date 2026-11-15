#!/usr/bin/env python3
"""Gate the DELIVERED mp4 - the file that ships, not an upstream proxy.

Every figure here is read off the file named on the command line, and the file's
md5 and duration are printed in the same block as the figures they describe.

Checks: identity, container shape, duration against the derived timeline,
loudness and true peak, music-free (a bed shows up as an absence of silence),
and OCR over frames sampled across the whole film for anything that must not be
on screen - the authored sweep reads source, and text burned into a recorded
plate is invisible to it.
"""
import hashlib, json, re, subprocess, sys, pathlib, tempfile
import numpy as np
from PIL import Image

P = pathlib.Path(__file__).parent
FORBIDDEN = [
    ("fly.dev host",       r"[A-Za-z0-9_-]+\.fly\.dev"),
    ("fly.io host",        r"fly\.io"),
    ("localhost:port",     r"localhost:\d+"),
    ("bearer token",       r"[Bb]earer\s+[A-Za-z0-9._\-]{12,}"),
    ("JWT",                r"eyJ[A-Za-z0-9_\-]{10,}"),
    ("api key label",      r"(?i)\b(api[_ -]?key|admin[_ -]?token|x-api-key|service[_ -]?account)\b"),
    ("nuclia",             r"(?i)\bnuclia\b"),
    ("rag.progress.cloud", r"(?i)rag\.progress\.cloud"),
    ("hosting region",     r"(?i)\baws-[a-z]+-[a-z]+-\d+-\d+\b"),
    ("real person name",   r"(?i)\bjohan\b|\bdelport\b|\bkelly\b|o[''\u2019]?donnell"),
    # An em dash that matters sits between WORDS. A bare run of dashes is OCR
    # reading a horizontal rule or a bar: the first run flagged 59 of them across
    # 12 frames and every one decoded as '------', '-' or '_-' with no adjacent
    # text, while the authored-copy sweep found 0 em dashes in 200 visible
    # strings. Narrow the pattern, not the population.
    # \s matches a NEWLINE, so a rule on its own line between two lines of text
    # still matched - 11 of them did. An em dash in prose sits on the SAME line as
    # the words it joins, so the whitespace class is horizontal only.
    # Third narrowing, each from a real emission. OCR over the 28-thumbnail grid in
    # frame 11 invents dash-and-letter noise - the two hits were '-k-eEqeees' and
    # '-eE-EeEees' - so a single flanking character is not enough. An em dash in COPY
    # joins words, so require an alphabetic run of 3+ on each side. The authored-text
    # sweep remains the authoritative instrument here: it reads the real strings and
    # finds 0 across 172. This one guards against a dash burned into a plate.
    ("em dash in text",    "[A-Za-z]{3,}[^\\S\\n]*\\u2014[^\\S\\n]*[A-Za-z]{3,}"),
    ("banned word",        r"(?i)\b(delve|delves|delved|delving|leverage|leverages|leveraged|"
                           r"leveraging|unlock|unlocks|unlocked|unlocking|seamless|seamlessly|"
                           r"game[- ]chang(ing|er))\b"),
]


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True).stdout.strip()


def main(path):
    f = pathlib.Path(path)
    md5 = hashlib.md5(f.read_bytes()).hexdigest()
    dur = float(sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)))
    v = sh("ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
           "stream=width,height,r_frame_rate,nb_frames,codec_name", "-of", "default=nw=1", str(f))
    a = sh("ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
           "stream=codec_name,sample_rate,channels", "-of", "default=nw=1", str(f))
    print(f"FILE      {f}")
    print(f"  md5     {md5}")
    print(f"  duration {dur:.3f}s")
    for line in v.splitlines() + a.splitlines():
        print(f"  {line}")

    tl = json.load(open(P / "timeline.json"))
    d_ok = abs(dur - tl["total"]) <= 0.08
    print(f"\nDURATION vs the derived timeline: {dur:.3f} vs {tl['total']:.3f} -> "
          f"{'PASS' if d_ok else 'FAIL'}")

    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "info", "-i", str(f),
                        "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    s = r.stderr[r.stderr.rfind("Summary:"):]
    I = float(re.search(r"I:\s*(-?[\d.]+) LUFS", s).group(1))
    TP = float(re.search(r"True peak:\s*\n\s*Peak:\s*(-?[\d.]+) dBFS", s).group(1))
    LRA = float(re.search(r"LRA:\s*(-?[\d.]+) LU", s).group(1))
    l_ok, t_ok = abs(I + 16.0) <= 1.0, TP <= -1.0
    print(f"LOUDNESS  I = {I:.2f} LUFS (target -16 +/-1.0) -> {'PASS' if l_ok else 'FAIL'}")
    print(f"TRUE PEAK {TP:.2f} dBTP (ceiling -1.0) -> {'PASS' if t_ok else 'FAIL'}   LRA {LRA} LU")

    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "info", "-i", str(f),
                        "-af", "silencedetect=noise=-50dB:d=0.25", "-f", "null", "-"],
                       capture_output=True, text=True)
    gaps = len(re.findall(r"silence_start", r.stderr))
    m_ok = gaps >= 8
    print(f"MUSIC-FREE {gaps} silence gaps >=0.25s at -50dB (a bed would leave ~0) -> "
          f"{'PASS' if m_ok else 'FAIL'}")

    with tempfile.TemporaryDirectory() as tmp:
        t = pathlib.Path(tmp)
        n = 36
        times = [dur * i / (n - 1) for i in range(n)]
        times[-1] = max(0.0, dur - 0.2)
        hits = []
        for i, ts in enumerate(times):
            p = t / f"f{i:03d}.png"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{ts:.3f}",
                            "-i", str(f), "-frames:v", "1", str(p)], check=True)
            txt = subprocess.run(["tesseract", str(p), "stdout", "--psm", "11"],
                                 capture_output=True, text=True).stdout
            for name, pat in FORBIDDEN:
                for m in re.finditer(pat, txt):
                    hits.append((round(ts, 2), name, m.group(0)[:50]))
        # positive control through the same OCR path
        img = Image.new("RGB", (1600, 140), "white")
        from PIL import ImageDraw, ImageFont
        d = ImageDraw.Draw(img)
        try:
            fo = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 38)
        except OSError:
            fo = ImageFont.load_default()
        d.text((20, 20), "your-app.fly.dev  Johan Delport  nuclia", fill="black", font=fo)
        d.text((20, 75), "x-api-key  <zone>  seamless", fill="black", font=fo)
        cp = t / "control.png"; img.save(cp)
        ct = subprocess.run(["tesseract", str(cp), "stdout", "--psm", "11"],
                            capture_output=True, text=True).stdout
        fired = [n for n, pat in FORBIDDEN if re.search(pat, ct)]
    print(f"\nOCR over {n} frames spanning the whole film: {len(hits)} finding(s)")
    for h in hits:
        print(f"  t={h[0]}s {h[1]} -> {h[2]!r}")
    print(f"  POSITIVE CONTROL through the same path: {len(fired)}/6 planted patterns "
          f"recognised {fired}")
    o_ok = not hits and len(fired) >= 5

    ok = d_ok and l_ok and t_ok and m_ok and o_ok
    print(f"\nDELIVERY GATE {'PASS' if ok else 'FAIL'} for md5 {md5}")
    print("  States: duration, container, loudness, true peak, music-free, on-screen text.")
    print("  It does NOT read brand (progress_stage_check.py) or judge the picture (eye-read).")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
