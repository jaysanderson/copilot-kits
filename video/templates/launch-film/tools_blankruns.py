#!/usr/bin/env python3
"""Find every run of near-bare stage in the delivered film, and name its cause.

Population is FRAMES decoded at a fixed rate, not shot openings and not shot
boundaries - both of those samplings have missed runs in this factory before,
because a run can start anywhere. Ink is the share of pixels far enough from the
Progress navy stage to be content.

The threshold carries its measured pair rather than a description: printed below
with the busiest and emptiest frames in the film, so a reader can see the stage
and the content separated rather than take 0.012 on trust.
"""
import subprocess, sys, pathlib, json
import numpy as np

FPS = 4                      # 250ms resolution; a run shorter than that is not a run
NAVY = np.array([0, 33, 107], float)
TOL = 26                     # per-channel distance that counts as "not the stage"
INK_FLOOR = 0.012            # below this the frame is bare; measured pair printed


def main(film):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", film, "-vf", f"fps={FPS},scale=320:180",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    buf = np.frombuffer(r.stdout, dtype=np.uint8)
    n = buf.size // (320 * 180 * 3)
    if n == 0:
        sys.exit("decoded no frames - a blank sweep over nothing is not a pass")
    fr = buf[: n * 320 * 180 * 3].reshape(n, 180, 320, 3).astype(float)
    d = np.abs(fr - NAVY).max(axis=3)
    ink = (d > TOL).mean(axis=(1, 2))
    t = np.arange(n) / FPS

    order = np.argsort(ink)
    print(f"{film}\n  {n} frames at {FPS}fps, ink = share of pixels >{TOL}/255 from #00216B")
    print(f"  emptiest {ink[order[0]]:.4f} at {t[order[0]]:.2f}s | "
          f"busiest {ink[order[-1]]:.4f} at {t[order[-1]]:.2f}s | median {np.median(ink):.4f}")
    print(f"  floor {INK_FLOOR} sits between them, not tuned to either")

    runs, start = [], None
    for i, v in enumerate(ink):
        if v < INK_FLOOR and start is None:
            start = i
        elif v >= INK_FLOOR and start is not None:
            if (i - start) / FPS >= 0.4:
                runs.append((t[start], t[i], (i - start) / FPS, float(ink[start:i].max())))
            start = None
    if start is not None and (n - start) / FPS >= 0.4:
        runs.append((t[start], t[n - 1], (n - start) / FPS, float(ink[start:].max())))

    # next to THIS script - the film may be read from any path
    tl = json.load(open(pathlib.Path(__file__).parent / "timeline.json"))
    names = ["01-powered-by", "02-sample-pack", "03-the-hard-page", "04-step-1-split",
             "05-step-2-identify", "06-step-3-ask", "07-step-4-score", "08-step-5-delete",
             "09-the-output", "10-measured", "11-messy-ones", "12-powered-by-close"]

    def where(x):
        hits = [names[i] for i in range(12)
                if tl["scene_start"][i] <= x <= tl["scene_start"][i] + tl["scene_dur"][i]]
        local = [f"{n_}@{x - tl['scene_start'][names.index(n_)]:.1f}s" for n_ in hits]
        spoken = any(tl["voice_start"][i] <= x <= tl["voice_start"][i] + tl["takes"][i]
                     for i in range(12))
        return ", ".join(local) + ("  [OVER NARRATION]" if spoken else "  (silent)")

    print(f"\n{len(runs)} run(s) below the floor for >=0.4s:")
    for a, b, dur, mx in runs:
        print(f"  {a:7.2f} - {b:7.2f}  {dur:4.1f}s  peak ink {mx:.4f}   {where((a + b) / 2)}")
    tot = sum(x[2] for x in runs)
    print(f"\n  total {tot:.1f}s of bare stage, {tot / (n / FPS) * 100:.1f}% of the film")
    return runs


if __name__ == "__main__":
    main(sys.argv[1])
