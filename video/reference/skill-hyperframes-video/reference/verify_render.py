#!/usr/bin/env python3
"""
verify_render.py - the HyperFrames delivery gate the factory could not previously pass.

Why this exists: `hyperframes render` exits 0 and writes a valid, correct-duration MP4
even when every frame is identical (measured 29 Sep 2026: a composition whose GSAP failed
to load rendered 90 valid frames, 3 of them distinct, exit code 0). `hyperframes check`
catches a WHOLE-composition freeze via `sweep_static`, but it cannot see a single dead
section, and it never looks at the encoded file at all. This script looks at the encoded
file.

It is deliberately hostile: a frozen, blank, silent, truncated or dead-air render must FAIL
here. Run it on the delivered MP4, every time, before the DoP cert.

Usage
  .venv/bin/python verify_render.py OUT.mp4 \
      --expect-duration 57 \
      --sections "0:12,12:28,28:45,45:57" \
      --expect-audio \
      --render-log /tmp/render.log

  .venv/bin/python verify_render.py --selftest     # prove the scanner can fail

Every check prints PASS or FAIL with the measured number. Exit code 1 on any FAIL.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from hashlib import md5

# Signatures that appear in a `hyperframes render` log when the timeline never ran.
# All three were observed live on a composition whose GSAP CDN was unreachable.
LOG_FAILURE_SIGNATURES = [
    "no GSAP tweens (non-GSAP animation)",
    "sub_timeline_script_failure",
    "sub_timeline_readiness_timeout",
    "Failed to download CDN script",
    "timelines not registered after",
]

results = []


def record(name, ok, detail):
    results.append((name, ok, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path, stream, fields):
    out = run([
        "ffprobe", "-v", "error", "-select_streams", stream,
        "-show_entries", f"stream={fields}", "-of", "json", path,
    ])
    try:
        streams = json.loads(out.stdout).get("streams", [])
        return streams[0] if streams else {}
    except (ValueError, IndexError):
        return {}


def container_duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "csv=p=0", path])
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


SAMPLE_FPS = 5  # 0.2s quanta - fine enough to measure a static run, cheap enough to run often


def frame_stats(path, start, dur, fps=SAMPLE_FPS):
    """Sample a window at full resolution and hash each frame.

    Returns (distinct, total, longest_static_seconds).

    WHY HASHING AND NOT AN INTER-FRAME DIFF. The factory's usual motion instrument - mean
    absolute inter-frame difference on a downscaled greyscale decode, built for the tourism
    film's footage motion floor - CANNOT tell these two apart, and measured 29 Sep 2026 it
    ranks them the wrong way round:

        render            median diff @192x108   max diff   unique frames
        frozen (no tl)    0.0000                 0.0145     2 of 90
        working           0.0000                 0.0029     84 of 90

    Both medians are zero, and the FROZEN render has the LARGER maximum - so a max-diff
    threshold scores the broken file as the more animated of the two. Resolution is not the
    cause: at 480x270 the medians are still 0.0000 and the ordering is unchanged. A mean over
    the whole frame is dominated by the unchanged brand ground, and authored typographic
    motion only ever touches a small fraction of it. Counting distinct frames separates the
    two cleanly and needs no threshold tuning.

    A HELD end state is legitimately static, so the question is never "is every frame
    different" - it is "how many distinct frames exist" (freeze) and "how long is the
    longest unbroken static run" (dead air). Those are two different defects with two
    different thresholds.
    """
    tmp = tempfile.mkdtemp(prefix="hfverify_")
    try:
        run(["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(dur), "-i", path,
             "-vf", f"fps={fps}", "-f", "image2", os.path.join(tmp, "f_%04d.png"), "-y"])
        seq = []
        for fn in sorted(os.listdir(tmp)):
            with open(os.path.join(tmp, fn), "rb") as fh:
                seq.append(md5(fh.read()).hexdigest())
        if not seq:
            return 0, 0, 0.0
        longest = run_len = 1
        for i in range(1, len(seq)):
            run_len = run_len + 1 if seq[i] == seq[i - 1] else 1
            longest = max(longest, run_len)
        return len(set(seq)), len(seq), longest / fps
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def mean_volume(path, start, dur):
    """Windowed loudness in dB. -91 means digital silence, None means no audio.

    CRITICAL: -ss MUST come BEFORE -i. With output seeking (-i then -ss) volumedetect
    sees every frame and reports the WHOLE-FILE level for every window - measured
    29 Sep 2026, it reported -26 dB on a window that was genuinely -91 dB silent.
    A silent video passes a per-scene audio check written the wrong way round.
    """
    out = run(["ffmpeg", "-hide_banner", "-nostats",
               "-ss", str(start), "-t", str(dur), "-i", path,
               "-af", "volumedetect", "-f", "null", "-"])
    m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", out.stderr)
    return float(m.group(1)) if m else None


def frame_luma(path, start, count=1):
    out = run(["ffmpeg", "-v", "error", "-ss", str(start), "-i", path,
               "-frames:v", str(count),
               "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-",
               "-f", "null", "-"])
    return [float(v) for v in re.findall(r"YAVG=([\d.]+)", out.stdout + out.stderr)]


def tail_luma(path):
    """Mean luma of each of the last 6 frames, in order."""
    out = run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
               "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", path])
    try:
        n = int(out.stdout.strip())
    except ValueError:
        return []
    out = run(["ffmpeg", "-v", "error", "-i", path,
               "-vf", f"select='gte(n,{max(0, n - 6)})',signalstats,"
                      "metadata=print:key=lavfi.signalstats.YAVG:file=-",
               "-f", "null", "-"])
    return [float(v) for v in re.findall(r"YAVG=([\d.]+)", out.stdout + out.stderr)]


def parse_sections(spec):
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        a, b = part.split(":")
        out.append((float(a), float(b)))
    return out


def verify(path, expect_duration, sections, expect_audio, render_log,
           min_distinct_frames, max_static_run, min_bytes_per_sec, tail_tolerance):
    print(f"\nVerifying {path}\n" + "-" * 70)

    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        record("file exists and is non-empty", False, "missing or zero bytes")
        return

    size = os.path.getsize(path)
    dur = container_duration(path)

    # A. render log - the loudest and cheapest signal, if it was kept
    if render_log and os.path.isfile(render_log):
        with open(render_log, "r", errors="replace") as fh:
            log = fh.read()
        hits = [s for s in LOG_FAILURE_SIGNATURES if s in log]
        record("render log carries no timeline-failure signature", not hits,
               "clean" if not hits else f"found {hits}")

    # B. container and streams
    record("duration is plausible", dur > 0.5, f"{dur:.2f}s")
    if expect_duration:
        delta = abs(dur - expect_duration)
        record("duration matches the intended cut", delta <= 0.25,
               f"{dur:.2f}s vs expected {expect_duration}s (delta {delta:.2f}s)")

    v = probe(path, "v:0", "codec_name,width,height,duration")
    record("video stream present", bool(v.get("codec_name")),
           f"{v.get('codec_name')} {v.get('width')}x{v.get('height')}")

    # C. bytes per second - a frozen render is dramatically smaller than a live one
    bps = size / dur if dur else 0
    record("file size is not freeze-sized", bps >= min_bytes_per_sec,
           f"{size} bytes, {bps:,.0f} bytes/s (floor {min_bytes_per_sec:,})")

    # D. GLOBAL freeze catch - an ABSOLUTE distinct-frame floor, not a ratio.
    #    A ratio is the wrong instrument here because a legitimate held end card drags it
    #    down: measured, a 6s piece with a deliberate 4s hold scored 62% against a 50%
    #    floor, so a slightly longer hold would have false-failed. A frozen render sits at
    #    1-2 distinct frames however long it is, so an absolute floor separates the two
    #    with no tuning. Dead air is caught by the static-run check below instead.
    d, n, longest = frame_stats(path, 0, dur)
    record("timeline is not frozen (distinct frames)",
           d >= min_distinct_frames,
           f"{d} distinct of {n} sampled (floor {min_distinct_frames})")

    # E. GLOBAL dead-air catch - the longest unbroken static run.
    #    This is the encoded-file mirror of the motion sidecar's `keepsMoving`, and it is
    #    the check that a 'clean but boring' render fails.
    record("no dead-air hold longer than the limit",
           longest <= max_static_run,
           f"longest static run {longest:.1f}s (limit {max_static_run:.1f}s)")

    # F. PER-SECTION - a whole-timeline figure stays healthy while ONE section is frozen,
    #    which is exactly the defect that has reached the GM before.
    if sections:
        for (a, b) in sections:
            sd, sn, slong = frame_stats(path, a, b - a)
            ok = sd >= max(2, min_distinct_frames // 2) and slong <= max_static_run
            record(f"section {a:g}-{b:g}s is alive",
                   ok,
                   f"{sd} distinct of {sn}, longest static run {slong:.1f}s")

    # F. audio
    a = probe(path, "a:0", "codec_name,sample_rate,channels,duration")
    if expect_audio:
        record("audio stream present", bool(a.get("codec_name")),
               f"{a.get('codec_name')} {a.get('sample_rate')}Hz "
               f"{a.get('channels')}ch")
        whole = mean_volume(path, 0, dur)
        record("audio is not silent overall", whole is not None and whole > -60,
               f"mean {whole} dB" if whole is not None else "no reading")
        if sections:
            for (aa, bb) in sections:
                mv = mean_volume(path, aa, min(bb - aa, 4.0))
                # -91 dB is digital silence; speech typically lands -30 to -15 dB.
                record(f"section {aa:g}-{bb:g}s carries audio",
                       mv is not None and mv > -60,
                       f"mean {mv} dB" if mv is not None else "no reading")
        if a.get("duration"):
            drift = abs(float(a["duration"]) - dur)
            record("audio and video end together", drift <= 0.15,
                   f"drift {drift:.3f}s")
    else:
        record("no audio expected", True, "skipped")

    # G. tail frame - the renderer has been seen to drop the root background on the
    #    final emitted frame. It did NOT reproduce on 0.8.15 (29 Sep 2026), so this is
    #    a per-build check rather than an assumed defect.
    tl = tail_luma(path)
    if len(tl) >= 2:
        held = sorted(tl[:-1])[len(tl[:-1]) // 2]
        last = tl[-1]
        drop = (held - last) / held if held else 0
        record("final frame matches the held frame",
               drop <= tail_tolerance,
               f"last {last:.2f} vs held {held:.2f} ({drop:+.1%}, "
               f"tolerance {tail_tolerance:.0%})")


def selftest():
    """Prove the scanner can fail. A gate you have never seen fail is not a gate."""
    print("\nSELFTEST - planting a frozen, silent render and confirming it FAILS")
    print("=" * 70)
    tmp = tempfile.mkdtemp(prefix="hfselftest_")
    bad = os.path.join(tmp, "frozen.mp4")
    good = os.path.join(tmp, "moving.mp4")
    try:
        # A genuinely frozen 4s clip: one still colour, no audio.
        run(["ffmpeg", "-v", "error", "-f", "lavfi",
             "-i", "color=c=0x0b1424:s=1920x1080:d=4:r=30",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", bad, "-y"])
        # A moving 4s clip for contrast.
        run(["ffmpeg", "-v", "error", "-f", "lavfi",
             "-i", "testsrc2=s=1920x1080:d=4:r=30",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", good, "-y"])

        print("\n[1] the frozen file - every check below that says PASS is a bug")
        results.clear()
        verify(bad, 4, [(0, 2), (2, 4)], False, None, 8, 3.0, 20000, 0.10)
        froze = [r for r in results if not r[1]]
        print(f"\n  -> frozen file produced {len(froze)} FAIL(s). "
              f"{'Scanner works.' if froze else 'SCANNER IS BROKEN - it passed a frozen file.'}")

        print("\n[2] the moving file - should be clean on the motion checks")
        results.clear()
        verify(good, 4, [(0, 2), (2, 4)], False, None, 8, 3.0, 20000, 0.10)
        moved = [r for r in results if not r[1]]
        print(f"\n  -> moving file produced {len(moved)} FAIL(s) "
              f"(size/luma checks may legitimately fire on synthetic footage).")
        return 0 if froze else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mp4", nargs="?", help="the rendered file to verify")
    p.add_argument("--expect-duration", type=float, default=None)
    p.add_argument("--sections", default="",
                   help='per-section windows, e.g. "0:12,12:28,28:45"')
    p.add_argument("--expect-audio", action="store_true")
    p.add_argument("--render-log", default=None,
                   help="the saved `hyperframes render` log, scanned for failure signatures")
    p.add_argument("--min-distinct-frames", type=int, default=8,
                   help="absolute floor on distinct frames across the timeline (default 8). "
                        "A frozen render sits at 1-2 however long it is. "
                        "CAUTION: this value is ALSO applied per --sections window, "
                        "halved. A section only samples about 5 frames per second, so "
                        "on a 2.5s section that is 13 samples - and any floor above 26 "
                        "false-FAILS it even at 13 distinct of 13, which is 100%% alive. "
                        "Size the floor to the SMALLEST section, or run twice: once "
                        "whole-timeline with a high floor and no --sections, once with "
                        "--sections at the default.")
    p.add_argument("--max-static-run", type=float, default=3.0,
                   help="longest permitted unbroken static run, in seconds (default 3.0). "
                        "Raise it only for a deliberately long end-card hold, and say so "
                        "in the build report.")
    p.add_argument("--min-bytes-per-sec", type=int, default=20000,
                   help="freeze floor; a frozen 1080p second encodes far below this")
    p.add_argument("--tail-tolerance", type=float, default=0.10,
                   help="allowed luma drop on the final frame (default 10%%)")
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()

    if args.selftest:
        sys.exit(selftest())
    if not args.mp4:
        p.error("give a file to verify, or --selftest")

    verify(args.mp4, args.expect_duration, parse_sections(args.sections),
           args.expect_audio, args.render_log, args.min_distinct_frames,
           args.max_static_run, args.min_bytes_per_sec, args.tail_tolerance)

    fails = [r for r in results if not r[1]]
    print("-" * 70)
    print(f"{len(results) - len(fails)} passed, {len(fails)} failed")
    if fails:
        print("\nFAILED:")
        for name, _, detail in fails:
            print(f"  - {name}: {detail}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
