"""The shared video gate. One instrument for every film, replacing the per-film
gate/sweep/measure/motion_rank scripts the last five films each re-invented.

    .venv/bin/python scripts/video_gate.py <master.mp4> [--design DESIGN.md]
        [--segments timeline.json] [--reference-strings ref.txt] [--social]
        --out report.json

DESIGN RULES, all learned at full cost and consolidated from
videos/{holidayisle-kiosk,tourism-experience,clinic-announcements,
real-account-showcase,vr-hyperframes}:

* EVERY VERDICT GOES THROUGH ONE `check()` THAT PRINTS AND REGISTERS IN THE SAME
  CALL. A threshold that appears only in a format string is not a check - a real
  measure.py printed seven floors beside separately computed values, compared
  nothing, and ended in an unconditional return 0.
* EVERY CHECK RUNS ITS OWN POSITIVE AND NEGATIVE CONTROL ON EVERY INVOCATION.
  A detector proven only to fire and one proven only to stay quiet are both
  unproven. A check whose control cannot run is reported as a HOLE, never PASS.
  Pure-arithmetic comparators (a band test on a measured number) carry
  arithmetic controls; detectors carry measurement controls on planted media.
* EVERY FIGURE IS STAMPED with the md5 and duration it was measured against,
  because an instrument reports on the artifact it was handed and can never
  tell you it was handed the wrong one.
* UNITS ARE STATED IN THE FIGURE. "0.25" without "@390px grey levels 0-255" had
  an agent reproduce "100% of the film is static" off a unit mismatch.
* ZERO OF ZERO IS NOT A PASS. A check that examined nothing FAILS; the run can
  never exit 0 having measured nothing.
* `-loglevel info` IS LOAD-BEARING on every measuring ffmpeg filter
  (freezedetect, loudnorm): `-v error` swallows their output and the empty
  result reads as a clean pass. The music-free check does not use silencedetect
  at all - it computes silence from decoded PCM in numpy, which has no
  verbosity flag to get wrong.

Exit codes: 0 all checks PASS (HOLEs allowed, each named); 1 any FAIL;
2 any control/selftest failure (the run's own instruments are unproven, so no
verdict it printed is worth anything).

Provenance of each check is noted beside it. Report: one JSON (--out) plus a
one-screen text summary.
"""
import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SR = 48000

# ---------------------------------------------------------------- report state
CHECKS = []          # {name, status, figures, detail, controls, stamp}
CONTROL_FAILS = []   # names of controls that did not behave
STAMP = ""           # "md5 xxxx / 140.199s", set once the master is read


def new_check(name):
    c = {"name": name, "status": "HOLE", "figures": {}, "detail": "",
         "controls": [], "stamp": STAMP}
    CHECKS.append(c)
    return c


def verdict(c, ok, detail=""):
    """One call prints AND registers - a check cannot report a failure without
    failing the run."""
    c["status"] = "PASS" if ok else "FAIL"
    c["detail"] = detail
    print(f"  [{c['status']}] {c['name']}: {detail}  [{c['stamp']}]", flush=True)
    return ok


def hole(c, why):
    c["status"] = "HOLE"
    c["detail"] = why
    print(f"  [HOLE] {c['name']}: {why}", flush=True)


def control(c, name, ok, detail=""):
    """A control that misbehaves fails the RUN (exit 2), not merely the check -
    a verdict off an unproven instrument is worth nothing."""
    c["controls"].append({"name": name, "ok": bool(ok), "detail": detail})
    tag = "ok" if ok else "CONTROL FAILED"
    print(f"      control {name}: {tag}  {detail}", flush=True)
    if not ok:
        CONTROL_FAILS.append(f"{c['name']}/{name}")
    return bool(ok)


def fig(c, key, value):
    c["figures"][key] = value
    return value


# ---------------------------------------------------------------- media helpers
def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=kw.pop("text", False),
                          stdin=subprocess.DEVNULL, **kw)


def probe_json(path, entries, stream=None):
    cmd = ["ffprobe", "-v", "error"]
    if stream:
        cmd += ["-select_streams", stream]
    cmd += ["-show_entries", entries, "-of", "json", str(path)]
    return json.loads(run(cmd, text=True).stdout or "{}")


def duration_of(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "csv=p=0", str(path)], text=True).stdout.strip()
    return float(out)


def pcm(path):
    raw = run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-ac", "1",
               "-ar", str(SR), "-f", "s16le", "-"]).stdout
    return np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0


def grey_frames_390(path, fps=10):
    """Whole-film grey decode at PHONE WIDTH (390px), 10 samples/second.

    Phone width because a sub-pixel move at 1080p is genuine pixel change that
    does not survive the downscale a viewer actually sees (holidayisle-kiosk
    gate.py:motion_map). Returns (frames int16 array, fps)."""
    w = 390
    # Aspect from the stream, never a hardcoded 16:9 box - a 9:16 master decoded
    # into a 16:9 box compresses vertical motion into a handful of rows and the
    # detector fires on an ordinary scroll (tourism measure.py:_scan_scale).
    st = probe_json(path, "stream=width,height", "v:0")["streams"][0]
    h = int(round(w * st["height"] / st["width"] / 2) * 2)
    raw = run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path),
               "-vf", f"fps={fps},scale={w}:{h}:flags=area",
               "-pix_fmt", "gray", "-f", "rawvideo", "-"]).stdout
    n = len(raw) // (w * h)
    fr = np.frombuffer(raw, dtype=np.uint8)[: n * w * h].reshape(n, h, w)
    return fr.astype(np.int16), fps, w, h


def longest_run_seconds(mask, fps):
    best, runlen, at = 0, 0, 0
    for i, s in enumerate(mask):
        if s:
            runlen += 1
            if runlen > best:
                best, at = runlen, i - runlen + 1
        else:
            runlen = 0
    return best / fps, at / fps


# ---------------------------------------------------------------- design + segments
FLOOR_KEYS = ("lufs-target", "lufs-tol", "tp-max", "music-free-gap-floor",
              "frozen-share-ceiling", "still-run-ceiling", "shot-median-floor",
              "grey-frac-ceiling", "type-only-share-ceiling",
              "type-only-run-ceiling", "social-type-only-share-ceiling",
              "social-type-only-run-ceiling", "ocr-langs", "ocr-fps",
              # Added 9 Oct 2026 (university). eval_storyboard() has read these two
              # since 4 Oct but they were never in this tuple, so parse_design()
              # dropped them and a DESIGN.md declaring either was a SILENT NO-OP:
              # the film's author believed a floor was enforced and the default
              # was used instead. Found by running parse_design() against a new
              # film's own DESIGN.md rather than assuming it was read.
              "illustration-share-floor", "type-run-ceiling")


BASELINE_FORBIDDEN = [
    # Every film's DESIGN.md used to supply this list from scratch, so each one had to
    # independently remember the same handful of strings - which is the shape of defect
    # this estate keeps rediscovering: a remedy that lives in one project's folder is not
    # shared, it is merely written down somewhere. These are the terms CLAUDE.md already
    # bans outright on ANY film, unioned with whatever the film declares for itself.
    #
    # Kept deliberately short. A baseline that over-fires gets excluded by its users and
    # then protects nothing, so nothing goes in here unless a hit is wrong on every film:
    # "offline" and "hybrid", for instance, are NOT here, because both have legitimate
    # product meanings on screen.

    # Internal platform names. The product is "Progress Agentic RAG" to a customer.
    "NucliaDB", "Nuclia", "Knowledge Box", "nuclia.cloud", "rag.progress.cloud",

    # Deployment-mode claims. CLAUDE.md: no deployment-mode claim may appear anywhere.
    "self-hosted", "on-premises", "air-gapped",

    # Self-annotation and self-grading (GM kickback, 20 Oct 2026, Kuraray). Seven scenes
    # carried a "WOW MOMENT n" badge that had followed the storyboard onto the screen.
    # His words: "This is for presentation to a partner or customer, so that doesn't fly."
    #
    # This is the internal-VOICE class, not the internal-VOCABULARY one, and that is why
    # it reached a customer-facing cut: the words are plain English and no product-name,
    # hostname or competitor sweep could ever match them. What makes them internal is the
    # grammar - a film annotating its own highlights, addressing the people who built it
    # rather than the room. Sibling of the showreel that printed its own gate result: a
    # passing mark you awarded yourself is a boast whatever its provenance, and telling a
    # customer which bits are meant to impress them is the same move in another notation.
    "WOW MOMENT",
]

# "Back office" was in the list above and is REMOVED, by the list's own stated bar:
# nothing belongs here unless a hit is wrong on EVERY film. It was added to catch a
# demo's dark utility strip, whose "Back office" link is a backend door. But it is
# also ordinary business English - a dealer-management film's own manual page reads
# "Sales is the sales back office for the Harbourline Toyota group", which is the
# product describing a dealership, and the token matcher is case-insensitive so it
# cannot tell the two apart.
#
# What replaces it is stronger than a string check, not weaker: the strip is removed
# GEOMETRICALLY, by a per-source measurement of how many leading rows it occupies,
# and the build prints the row count for every source it crops. A measured crop
# cannot be defeated by casing, by OCR silence, or by the label being renamed, and a
# film that needs the string check anyway can still declare it in its own DESIGN.md.


def parse_design(path):
    """DESIGN.md conventions this gate reads (documented in video_gate_README.md):

    * a line containing "must not appear" (any case, hyphens allowed) starts a
      list; the following `- item` lines are the forbidden strings.
    * floor overrides anywhere in the file: `<key>: <value>` at line start for
      the keys in FLOOR_KEYS.
    """
    txt = Path(path).read_text()
    forbidden, in_list = [], False
    # A "must not appear" heading that yields ZERO items is almost always a
    # MALFORMED LIST, not a deliberate absence: parse_design stops collecting at
    # the first non-item line, so one sentence of prose between the heading and
    # the items empties it silently. Three films hit this in one day - both
    # concept films and this parser's own author - and in every case the report
    # read "no must-not-appear list in --design", which says "you did not write
    # one" to someone who had. So the trigger is recorded separately from the
    # items and the gate says which case it is.
    saw_trigger, first_blocker = False, None
    for line in txt.splitlines():
        if re.search(r"must[- ]not[- ]appear", line, re.I):
            in_list, saw_trigger = True, True
            continue
        if in_list:
            m = re.match(r"\s*[-*]\s+(.+?)\s*$", line)
            if m:
                forbidden.append(m.group(1))
            elif line.strip():
                in_list = False
                if not forbidden and first_blocker is None:
                    first_blocker = line.strip()[:120]
    floors, unreadable = {}, {}
    for key in FLOOR_KEYS:
        m = re.search(rf"^\s*(?:[-*]\s*)?{re.escape(key)}\s*:\s*(\S+)",
                      txt, re.M | re.I)
        if m:
            v = m.group(1)
            if key in ("ocr-langs",):
                floors[key] = v
                continue
            try:
                floors[key] = float(v)
            except ValueError:
                # A floor declared WITH ITS UNIT ("3.0s", "-14 LUFS", "2.5 s") is
                # correct practice - the SOP requires the unit to be stated in the
                # figure - so the parser reads it rather than the DESIGN.md being
                # wrong. Before 9 Oct 2026 float("3.0s") raised, and because both
                # in-flight concept films declare `type-only-run-ceiling: 3.0s`,
                # `video_gate.py --design <either DESIGN.md>` died on a traceback
                # before a single check ran. A crash is better than a silent no-op
                # and far worse than a named verdict, so anything still
                # unparseable is reported as a FAILED check and never dropped.
                stripped = re.sub(r"(?i)\s*(ms|s|%|px|fps|lufs|lu|db|x)$", "", v)
                try:
                    floors[key] = float(stripped)
                except ValueError:
                    unreadable[key] = v
    if saw_trigger and not forbidden:
        # Surfaced through the floors dict so no caller signature changes.
        unreadable["_forbidden_list_empty"] = (
            "a 'must not appear' heading was found but parsed to ZERO items"
            + (f"; the first line that ended the list was: {first_blocker!r}"
               if first_blocker else "; no '- item' lines followed it")
            + ". parse_design stops at the first line that is not a '- item', so "
              "prose between the heading and the list empties it. Put the prose "
              "ABOVE the heading.")
    return forbidden, floors, unreadable


def load_segments(path):
    """Normalise the three timeline shapes the estate actually uses:
    clinic timeline.json (shots: start/duration/kind/source/audio[].text),
    real-account timeline.json (shots: start/seconds/id/kind),
    holidayisle crops.json (segment_starts for timing; shots carry crop windows
    with clip-relative start), vr timeline.json (lines: in/out/text)."""
    data = json.loads(Path(path).read_text())
    segdir = Path(path).resolve().parent

    def norm_entry(s):
        start = s.get("start", s.get("in"))
        dur = s.get("duration", s.get("dur", s.get("seconds")))
        if dur is None and "out" in s and "in" in s:
            dur = s["out"] - s["in"]
        texts = []
        for k in ("text", "caption"):
            if s.get(k):
                texts.append(s[k])
        for a in s.get("audio") or []:
            if a.get("text"):
                texts.append(a["text"])
        return {"source": s.get("source") or s.get("id") or s.get("key") or "?",
                "kind": s.get("kind", "?"), "start": start, "dur": dur,
                "texts": texts, "motion_exempt": s.get("motion_exempt")}

    timing = []
    for key in ("segment_starts", "shots", "lines"):
        rows = data.get(key) if isinstance(data, dict) else None
        if rows:
            cand = [norm_entry(s) for s in rows]
            cand = [c for c in cand if c["start"] is not None and c["dur"]]
            if cand:
                timing = cand
                break

    crops = []
    for s in (data.get("shots") or []) if isinstance(data, dict) else []:
        if not s.get("window"):
            continue
        src = None
        if s.get("still"):
            for p in (segdir / s["still"], segdir / "shots" / f"{s['still']}.png"):
                if p.exists():
                    src = ("still", p)
                    break
        elif s.get("clip"):
            for p in (segdir / s["clip"], segdir / "clips" / f"{s['clip']}.mp4"):
                if p.exists():
                    src = ("clip", p)
                    break
        if src:
            crops.append({"source": s.get("source", "?"),
                          "window": s["window"], "media": src,
                          "start": s.get("start"), "dur": s.get("dur"),
                          "amount": s.get("amount"), "motion": s.get("motion"),
                          "anchor": s.get("anchor", "centre"),
                          "photographic": bool(s.get("photographic"))})
    # Static reading windows (holidayisle crops.json "windows": still+window).
    for w in (data.get("windows") or []) if isinstance(data, dict) else []:
        if not (w.get("window") and w.get("still")):
            continue
        for p in (segdir / w["still"], segdir / "shots" / f"{w['still']}.png"):
            if p.exists():
                crops.append({"source": f"{w['still']}:{w.get('key', '?')}",
                              "window": w["window"], "media": ("still", p),
                              "start": None, "dur": None, "amount": None,
                              "motion": None, "anchor": "centre",
                              "photographic": bool(w.get("photographic"))})
                break
    return timing, crops


# ---------------------------------------------------------------- CHECK: identity
def check_identity(master, dur, timing):
    c = new_check("identity")
    st = probe_json(master, "stream=codec_type,codec_name,width,height,"
                            "sample_rate,channels,r_frame_rate,nb_frames,duration")
    v = [s for s in st["streams"] if s["codec_type"] == "video"]
    a = [s for s in st["streams"] if s["codec_type"] == "audio"]
    nf = int(v[0].get("nb_frames") or 0) if v else 0
    if v and not nf:
        nf = int(run(["ffprobe", "-v", "error", "-count_frames",
                      "-select_streams", "v:0", "-show_entries",
                      "stream=nb_read_frames", "-of", "csv=p=0", str(master)],
                     text=True).stdout.strip() or 0)
    fps = 0.0
    if v:
        num, den = v[0]["r_frame_rate"].split("/")
        fps = float(num) / float(den)
    fig(c, "duration_s", round(dur, 3))
    fig(c, "frames", nf)
    fig(c, "fps", round(fps, 3))
    if v:
        fig(c, "video", f"{v[0]['width']}x{v[0]['height']} {v[0]['codec_name']}")
    if a:
        fig(c, "audio", f"{a[0]['codec_name']} {a[0]['sample_rate']}Hz "
                        f"{a[0]['channels']}ch")
    vd = float(v[0].get("duration") or 0) if v else 0
    ad = float(a[0].get("duration") or 0) if a else 0
    fig(c, "stream_duration_delta_s", round(abs(vd - ad), 3))
    ok = (len(v) == 1 and len(a) == 1 and nf > 0 and abs(vd - ad) < 0.3)
    detail = (f"{c['figures'].get('video')} + {c['figures'].get('audio')}, "
              f"{nf} frames @ {fps:.3f}fps, {dur:.3f}s, "
              f"v/a stream delta {abs(vd - ad):.3f}s")

    if timing:
        seg_sum = sum(s["dur"] for s in timing)
        span = (max(s["start"] + s["dur"] for s in timing)
                - min(s["start"] for s in timing))
        d_sum, d_span = abs(seg_sum - dur), abs(span - dur)
        method = "sum" if d_sum <= d_span else "span"
        delta = min(d_sum, d_span)
        fig(c, "segment_sum_s", round(seg_sum, 3))
        fig(c, "segment_span_s", round(span, 3))
        fig(c, "currency_delta_s", round(delta, 3))
        fig(c, "currency_method", method)
        # Controls on the comparator itself, perturbed against the MASTER
        # duration, not against the fixture's own sum - a sum already short by
        # 2s plus a 2.6s phantom lands back inside tolerance and the control
        # reads the comparator as broken (found by this gate's own first echo
        # demo). A total of dur+2.6 must fail closure; dur+0.2 must pass it.
        control(c, "currency fires on a planted 2.6s phantom (dur+2.6)",
                abs((dur + 2.6) - dur) > 1.0)
        control(c, "currency stays quiet on an honest total (dur+0.2)",
                abs((dur + 0.2) - dur) <= 1.0)
        ok = ok and delta <= 1.0
        detail += (f"; currency: {len(timing)} segments, {method} delta "
                   f"{delta:.3f}s (tolerance 1.0s)")
    else:
        detail += "; currency NOT checked - no --segments (declared, not a pass)"
    verdict(c, ok, detail)
    # The one structural guarantee the exit path needs: zero frames is a FAIL
    # here, so the run can never exit 0 over an empty decode.
    return nf > 0


# ---------------------------------------------------------------- CHECK: audio
def check_audio(master, dur, floors, work):
    # loudnorm reports at INFO level; `-v error` would swallow the JSON.
    c = new_check("audio.loudness")
    meas = run(["ffmpeg", "-nostdin", "-loglevel", "info", "-i", str(master),
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                "-f", "null", "-"], text=True).stderr
    j = json.loads(meas[meas.rfind("{"): meas.rfind("}") + 1])
    li, tp = float(j["input_i"]), float(j["input_tp"])
    target = floors.get("lufs-target", -14.0)
    tol = floors.get("lufs-tol", 1.5)
    tpmax = floors.get("tp-max", -1.0)
    fig(c, "integrated_LUFS", li)
    fig(c, "true_peak_dBTP", tp)
    # Arithmetic controls on the band comparators.
    control(c, "LUFS band fires on a -30 LUFS reading", abs(-30.0 - target) > tol)
    control(c, "TP ceiling fires on a -0.2 dBTP reading", -0.2 > tpmax)
    verdict(c, abs(li - target) <= tol and tp <= tpmax,
            f"{li:.2f} LUFS (target {target} +/-{tol}), true peak {tp:.2f} dBTP "
            f"(ceiling {tpmax})")

    audio = pcm(master)

    c = new_check("audio.head")
    head_db = 20 * math.log10(max(1e-9, float(np.sqrt(
        np.mean(audio[: int(SR * 0.25)] ** 2)))))
    # Time to first sound: informational figure, not a verdict.
    hop = int(SR * 0.02)
    k = len(audio) // hop
    rms = np.sqrt((audio[: k * hop].reshape(k, hop) ** 2).mean(axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    loudish = np.where(db > -45.0)[0]
    first = float(loudish[0] * 0.02) if len(loudish) else dur
    fig(c, "head_250ms_dBFS", round(head_db, 1))
    fig(c, "first_sound_s", round(first, 2))
    zero_runs = int(sum(1 for i in range(k)
                        if np.all(audio[i * hop:(i + 1) * hop] == 0)))
    fig(c, "digital_zero_20ms_windows", zero_runs)  # figure only; a pause should
    # be a floor not a void, but assembly styles differ per film - reported, not
    # gated (holidayisle gate.py gated it; tourism's assembly legitimately differs).
    control(c, "head test fires on a digital-zero head", not (-120.0 > -70.0))
    verdict(c, head_db > -70.0,
            f"first 250ms at {head_db:.1f} dBFS (floor -70: not digital zero); "
            f"first sound at {first:.2f}s; {zero_runs} bit-exact-zero 20ms "
            f"window(s) [figure only]")

    # Music-free. NOT silencedetect (writes to the log; `-v error` returns a
    # confident zero which is the exact signature of a music bed). Decoded PCM
    # in numpy, structurally immune. -45dB / 0.4s gap at 20ms resolution.
    c = new_check("audio.music_free")
    quiet = db < -45.0
    gaps, start = [], None
    for i, q in enumerate(quiet):
        if q and start is None:
            start = i
        elif not q and start is not None:
            if (i - start) * 0.02 >= 0.4:
                gaps.append((start * 0.02, (i - start) * 0.02))
            start = None
    if start is not None and (k - start) * 0.02 >= 0.4:
        gaps.append((start * 0.02, (k - start) * 0.02))
    floor = int(floors.get("music-free-gap-floor", max(3, int(dur / 20))))
    fig(c, "silent_gaps_045dB_04s", len(gaps))
    fig(c, "longest_gap_s", round(max((g[1] for g in gaps), default=0.0), 2))
    fig(c, "gap_floor", floor)

    # POSITIVE control: a silent clip must yield gaps.
    def gaps_of(x):
        kk = len(x) // hop
        if kk == 0:
            return []
        r = np.sqrt((x[: kk * hop].reshape(kk, hop) ** 2).mean(axis=1) + 1e-12)
        qq = 20 * np.log10(r) < -45.0
        out, st2 = [], None
        for i, q in enumerate(qq):
            if q and st2 is None:
                st2 = i
            elif not q and st2 is not None:
                if (i - st2) * 0.02 >= 0.4:
                    out.append(1)
                st2 = None
        if st2 is not None and (kk - st2) * 0.02 >= 0.4:
            out.append(1)
        return out
    control(c, "fires on 4s of digital silence",
            len(gaps_of(np.zeros(SR * 4))) >= 1)
    # NEGATIVE control: the SAME master with a measured-level bed mixed under
    # must return zero gaps. The bed's own level is asserted first - a control
    # below the threshold it must mask proves nothing (holidayisle gate.py lesson:
    # a -47 dBFS "bed" was inaudible and the control reported the gate blind).
    t = np.arange(len(audio)) / SR
    bed = 0.06 * np.sin(2 * np.pi * 180 * t)
    bed_db = 20 * math.log10(float(np.sqrt(np.mean(bed ** 2))))
    bed_ok = bed_db > -35.0
    control(c, "planted bed measures above the -45 threshold", bed_ok,
            f"bed at {bed_db:.1f} dBFS")
    mixed_gaps = gaps_of(np.clip(audio + bed, -1, 1))
    control(c, "same scan over the same film with a bed under it finds 0 gaps",
            len(mixed_gaps) == 0, f"{len(mixed_gaps)} gap(s) with bed")
    verdict(c, len(gaps) >= floor,
            f"{len(gaps)} silent gap(s) >=0.4s at -45dBFS (floor {floor}; a "
            f"music bed leaves ~0, proven by the bed control)")
    return audio


# ---------------------------------------------------------------- CHECK: motion
def planted_clips(work):
    frozen = work / "_ctl_frozen.mp4"
    moving = work / "_ctl_moving.mp4"
    if not frozen.exists():
        run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "lavfi",
             "-i", "color=c=navy:s=320x180:d=6:r=30",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", str(frozen)])
    if not moving.exists():
        # NOT testsrc: a test CARD's only moving parts are a thin sweep and a
        # counter, measuring 0.355 - a control that weak reported a working
        # detector broken (clinic motion_rank.py). This oscillates the whole
        # frame and measures ~80.
        run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "lavfi",
             "-i", "color=c=gray:s=320x180:d=3:r=30",
             "-vf", "geq=lum='128+100*sin(2*PI*T*4)'",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", str(moving)])
    return frozen, moving


def frozen_runs(path, db=-60, d=1.5):
    """freezedetect reports at INFO level - `-v error` returns an empty result
    with exit 0, the exact false negative this check exists to prevent. A
    freeze running to end-of-file never emits freeze_duration, so the open run
    is closed at the file duration (real-account gate.py, found by its own
    selftest)."""
    r = run(["ffmpeg", "-nostdin", "-loglevel", "info", "-i", str(path),
             "-vf", f"freezedetect=n={db}dB:d={d}", "-map", "0:v",
             "-f", "null", "-"], text=True)
    runs, start = [], None
    for line in r.stderr.splitlines():
        if "freeze_start" in line:
            start = float(line.rsplit(":", 1)[1].strip())
        elif "freeze_duration" in line and start is not None:
            runs.append((start, float(line.rsplit(":", 1)[1].strip())))
            start = None
    if start is not None:
        runs.append((start, max(0.0, duration_of(path) - start)))
    return runs


def check_motion(master, dur, timing, floors, work):
    frozen_clip, moving_clip = planted_clips(work)

    # --- literally-frozen share, freezedetect n=-60dB d=1.5
    c = new_check("motion.frozen_share")
    ctl = frozen_runs(frozen_clip)
    control(c, "freezedetect fires on a planted 6s frozen clip",
            len(ctl) >= 1 and ctl[0][1] > 4.0,
            f"{len(ctl)} run(s) {'%.2fs' % ctl[0][1] if ctl else ''}")
    ctl_neg = frozen_runs(moving_clip)
    control(c, "freezedetect stays quiet on a planted moving clip",
            len(ctl_neg) == 0, f"{len(ctl_neg)} run(s)")
    runs = frozen_runs(master)
    frozen_s = sum(r[1] for r in runs)
    ceil = floors.get("frozen-share-ceiling", 0.25)
    fig(c, "frozen_runs", len(runs))
    fig(c, "frozen_seconds", round(frozen_s, 2))
    fig(c, "frozen_share", round(frozen_s / dur, 4))
    if runs:
        fig(c, "runs_detail", [f"{a:.2f}s+{b:.2f}s" for a, b in runs[:8]])
    verdict(c, frozen_s / dur < ceil,
            f"{len(runs)} frozen run(s) totalling {frozen_s:.1f}s of {dur:.1f}s "
            f"= {frozen_s / dur * 100:.1f}% (freezedetect n=-60dB d=1.5, "
            f"ceiling {ceil * 100:.0f}%)")

    # --- perceptual motion at 390px. A binary freeze detector cannot see
    # "technically moving, perceptually still" (tourism, 1 Oct) - this measures
    # what the room experiences. Unit stated in every figure: mean absolute
    # frame-to-frame difference in 0-255 GREY LEVELS @390px width, 10fps.
    c = new_check("motion.perceptual")
    fr, fps, w, h = grey_frames_390(master)
    n = len(fr)
    if n < 2:
        verdict(c, False, f"decoded only {n} frame(s) at 390px - zero of zero "
                          f"is not a pass")
        return None
    expect = int(dur * fps)
    d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
    # Controls on the measure itself, on planted media.
    cf, _, _, _ = grey_frames_390(frozen_clip)
    cm, _, _, _ = grey_frames_390(moving_clip)
    fmed = float(np.median(np.abs(np.diff(cf, axis=0)).mean(axis=(1, 2))))
    mmed = float(np.median(np.abs(np.diff(cm, axis=0)).mean(axis=(1, 2))))
    control(c, "frozen clip measures ~0", fmed < 0.01,
            f"{fmed:.4f} grey levels 0-255 @390px")
    control(c, "moving clip measures high", mmed > 2.0,
            f"{mmed:.2f} grey levels 0-255 @390px")
    thr = 0.25
    still = d < thr
    longest, at = longest_run_seconds(still, fps)
    ceil = floors.get("still-run-ceiling", 2.5)
    fig(c, "samples", n)
    fig(c, "unit", f"mean abs frame diff, grey levels 0-255 @{w}x{h} {fps}fps")
    fig(c, "median_delta", round(float(np.median(d)), 3))
    fig(c, "still_share_lt_0.25", round(float(still.mean()), 4))
    fig(c, "longest_still_run_s", round(longest, 2))
    fig(c, "longest_still_run_at_s", round(at, 1))
    sample_ok = abs(n - expect) <= max(3, expect * 0.02)
    verdict(c, sample_ok and longest < ceil,
            f"{n} samples ({expect} expected - a scan that quietly resamples "
            f"reports every timestamp wrong); longest perceptually-still run "
            f"{longest:.2f}s at {at:.1f}s (<0.25 grey levels 0-255 @390px, "
            f"ceiling {ceil}s); still {still.mean() * 100:.1f}% of runtime; "
            f"median {float(np.median(d)):.3f}")

    # --- per-shot ranking; read the TOP of the list, not the average. A
    # whole-film aggregate is the one statistic a relocated defect is invisible
    # in (kiosk re-cut planted a fresh 4.93s hold the aggregates all missed).
    c = new_check("motion.per_shot")
    if not timing:
        hole(c, "no --segments, so no shot boundaries: the per-shot ranking "
                "did not run. A relocated defect is invisible to the whole-film "
                "aggregates above.")
        return d
    rows, unmeasured = [], []
    exempt = {s["source"]: s["motion_exempt"] for s in timing
              if s.get("motion_exempt")}
    for s in timing:
        i0 = max(0, int(s["start"] * fps))
        i1 = min(len(d), int((s["start"] + s["dur"]) * fps))
        if i1 - i0 < 2:
            unmeasured.append(f"{s['source']} ({s['dur']:.2f}s)")
            continue
        seg = d[i0:i1]
        srun, _ = longest_run_seconds(seg < thr, fps)
        rows.append({"source": s["source"], "kind": s["kind"],
                     "dur": round(s["dur"], 2),
                     "median": round(float(np.median(seg)), 3),
                     "still_run_s": round(srun, 2),
                     "still_share": round(float((seg < thr).mean()), 3)})
    rows.sort(key=lambda r: r["median"])
    floor = floors.get("shot-median-floor", 0.05)
    fig(c, "shots_measured", len(rows))
    fig(c, "shots_unmeasured", unmeasured)
    fig(c, "unit", f"median abs frame diff per shot, grey levels 0-255 @{w}px {fps}fps")
    fig(c, "top3_stillest", rows[:3])
    control(c, "ranking fires on a planted zero-motion shot",
            0.0 < floor, "a shot of median 0.000 would fail the floor")
    control(c, "ranking stays quiet on a planted moving shot",
            mmed >= floor, f"moving control at {mmed:.2f} passes the floor")
    # A motion_exempt shot is a declared HOLE, never folded into the pass
    # count - and the exemption list keeps its own positive control: an
    # exclusion naming a source the cut does not contain is indistinguishable
    # from one wired up wrong (holidayisle gate.py MOTION_EXEMPT).
    stale = [k for k in exempt if k not in {r["source"] for r in rows}]
    if exempt:
        control(c, "every motion exemption names a source this cut contains",
                not stale, f"stale: {stale}" if stale else
                f"{len(exempt)} exemption(s), each naming a real shot")
    holes_m = [r for r in rows if r["source"] in exempt]
    if holes_m:
        fig(c, "motion_exempt_holes",
            [{**r, "why": exempt[r["source"]]} for r in holes_m])
        print(f"      declared HOLEs (not passes): "
              f"{[r['source'] for r in holes_m]}")
    dead = [r for r in rows
            if r["source"] not in exempt and r["median"] < floor]
    for r in rows[:3]:
        tag = "  HOLE" if r["source"] in exempt else ""
        print(f"      stillest: {r['median']:7.3f}  still-run {r['still_run_s']:5.2f}s"
              f"  {r['dur']:6.2f}s  {r['kind']:7s} {r['source']}{tag}")
    judged = [r for r in rows if r["source"] not in exempt]
    verdict(c, bool(rows) and bool(judged) and not dead and not stale,
            f"{len(judged)} non-exempt shot(s) judged of {len(rows)} measured, "
            f"{len(unmeasured)} too short to carry 2 samples (named, not folded "
            f"in), {len(holes_m)} declared motion HOLE(s); stillest judged "
            + (f"{judged[0]['source']} at {judged[0]['median']:.3f} " if judged
               else "(none) ")
            + f"(floor {floor} grey levels 0-255 @390px); "
            + ("; ".join(f"{r['source']} {r['median']:.3f}" for r in dead)
               if dead else "no judged shot within the floor"))
    return d


# ---------------------------------------------------------------- CHECK: grey/blank
# (vr-hyperframes grey_scan.py: half-painted browser frames are FLAT grey at
# RGB ~(122,124,124). Band and tolerances are the lead's measured values.)
G_FLAT_STD, G_LO, G_HI, G_CHAN_TOL, G_FRAC, G_CELL = 3.0, 110, 135, 6, 0.10, 16


def grey_fraction(f):
    h, w, _ = f.shape
    gh, gw = h // G_CELL, w // G_CELL
    blk = (f[: gh * G_CELL, : gw * G_CELL]
           .reshape(gh, G_CELL, gw, G_CELL, 3).swapaxes(1, 2).astype(float))
    mean = blk.mean(axis=(2, 3))
    flat = blk.std(axis=(2, 3)).max(axis=2) < G_FLAT_STD
    inband = ((mean.min(axis=2) >= G_LO) & (mean.max(axis=2) <= G_HI)
              & ((mean.max(axis=2) - mean.min(axis=2)) <= G_CHAN_TOL))
    m = flat & inband
    if not m.any():
        return 0.0
    lab = np.zeros_like(m, dtype=int)
    nxt, best = 0, 0
    for y in range(gh):
        for x in range(gw):
            if not m[y, x] or lab[y, x]:
                continue
            nxt += 1
            stack, size = [(y, x)], 0
            lab[y, x] = nxt
            while stack:
                cy, cx = stack.pop()
                size += 1
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx_ = cy + dy, cx + dx
                    if 0 <= ny < gh and 0 <= nx_ < gw and m[ny, nx_] \
                            and not lab[ny, nx_]:
                        lab[ny, nx_] = nxt
                        stack.append((ny, nx_))
            best = max(best, size)
    return best / (gh * gw)


def stream_rgb(path, w=480, h=270, fps=10):
    """Yield (index, HxWx3 uint8) at the sample rate, streaming - a whole-film
    RGB load does not fit politely in memory."""
    p = subprocess.Popen(
        ["ffmpeg", "-nostdin", "-v", "error", "-i", str(path),
         "-vf", f"fps={fps},scale={w}:{h}", "-pix_fmt", "rgb24",
         "-f", "rawvideo", "-"], stdout=subprocess.PIPE,
        stdin=subprocess.DEVNULL)
    n = w * h * 3
    i = 0
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield i, np.frombuffer(b, np.uint8).reshape(h, w, 3)
        i += 1
    p.stdout.close()
    p.wait()


def top2bin_share(grey):
    """Share of the frame in its two dominant 16-level luminance bins - the
    measured flat-versus-continuous-tone discriminator (kiosk: photo 0.435-0.638,
    buttons 0.896-0.925, type 0.955-0.990; gate at 0.78)."""
    hist = np.bincount((grey.ravel() >> 4), minlength=16)
    return float(np.sort(hist)[-2:].sum()) / grey.size


def text_bands_present(grey, min_bands=2):
    """Thin horizontal ink bands = lines of type. Ink is distance from the
    row's own median (polarity-aware: dark-on-light and light-on-dark both)."""
    g = grey.astype(np.int16)
    med = np.median(g, axis=1, keepdims=True)
    ink = np.abs(g - med) > 40
    rows = ink.sum(axis=1) >= max(3, int(0.02 * g.shape[1]))
    bands, start = 0, None
    for i, on in enumerate(rows):
        if on and start is None:
            start = i
        elif not on and start is not None:
            if 2 <= i - start <= g.shape[0] // 4:
                bands += 1
            start = None
    if start is not None and 2 <= len(rows) - start <= g.shape[0] // 4:
        bands += 1
    return bands >= min_bands


def check_grey_and_type(master, dur, floors, social, design_given, work):
    # One streaming RGB pass feeds both the grey-artefact scan and the
    # typography-on-bare-stage classifier.
    fps = 10
    c_grey = new_check("artefact.flat_grey")
    c_type = new_check("typography.bare_stage")

    # Grey controls (grey_scan.py selftest, arrays - no video needed): a planted
    # block fires; the nearest legitimate look-alikes stay quiet, including a
    # TINTED mid-grey, which a luma-only band could not reject.
    base = np.full((270, 480, 3), (0, 23, 34), dtype=np.uint8)
    pos = base.copy()
    pos[:, int(480 * 0.66):] = (122, 124, 124)
    control(c_grey, "fires on a planted right-third grey block",
            grey_fraction(pos) > G_FRAC, f"{grey_fraction(pos):.3f}")
    quiet_ok = True
    for label, val in (("navy stage", (0, 23, 34)), ("white field", (250, 250, 250)),
                       ("tinted grey (118,124,131)", (118, 124, 131))):
        v = grey_fraction(np.full((270, 480, 3), val, dtype=np.uint8))
        quiet_ok &= v <= G_FRAC
    control(c_grey, "stays quiet on navy/white/tinted-grey look-alikes", quiet_ok)

    # Type-only classifier controls, synthetic frames through the real classifier.
    typo = np.full((270, 480), 30, dtype=np.uint8)
    for y in (60, 100, 140):   # three crisp "lines of type"
        typo[y:y + 10, 60:420:3] = 230
    rng = np.random.default_rng(7)
    photo = (np.linspace(40, 215, 480)[None, :].repeat(270, 0)
             + rng.normal(0, 18, (270, 480))).clip(0, 255).astype(np.uint8)
    blank = np.full((270, 480), 30, dtype=np.uint8)
    control(c_type, "classifies planted type-on-flat-stage as type-only",
            top2bin_share(typo) >= 0.78 and text_bands_present(typo),
            f"top2bin {top2bin_share(typo):.2f}")
    control(c_type, "does NOT classify continuous-tone frame as type-only",
            top2bin_share(photo) < 0.78, f"top2bin {top2bin_share(photo):.2f}")
    control(c_type, "blank flat frame counts as bare stage, not type",
            top2bin_share(blank) >= 0.78 and not text_bands_present(blank))

    grey_hits, type_mask, blank_count, n = [], [], 0, 0
    worst_grey = 0.0
    for i, f in stream_rgb(master, fps=fps):
        n += 1
        gf = grey_fraction(f)
        worst_grey = max(worst_grey, gf)
        if gf > G_FRAC:
            grey_hits.append(i / fps)
        g = (0.299 * f[..., 0] + 0.587 * f[..., 1]
             + 0.114 * f[..., 2]).astype(np.uint8)
        flat = top2bin_share(g) >= 0.78
        has_type = flat and text_bands_present(g)
        type_mask.append(has_type)
        if flat and not has_type:
            blank_count += 1

    ceilf = floors.get("grey-frac-ceiling", G_FRAC)
    fig(c_grey, "frames_examined", n)
    fig(c_grey, "worst_flat_grey_fraction", round(worst_grey, 3))
    fig(c_grey, "hit_times_s", [round(t, 1) for t in grey_hits[:10]])
    verdict(c_grey, n > 0 and not grey_hits,
            f"{n} frames @ {fps}fps examined; worst flat-grey connected region "
            f"{worst_grey * 100:.1f}% of frame (ceiling {ceilf * 100:.0f}%); "
            f"{len(grey_hits)} hit(s)" if n else "zero frames decoded")

    tm = np.array(type_mask, dtype=bool)
    share = float(tm.mean()) if n else 0.0
    longest, at = longest_run_seconds(tm, fps)
    fig(c_type, "frames_examined", n)
    fig(c_type, "type_only_share", round(share, 3))
    fig(c_type, "longest_type_only_run_s", round(longest, 2))
    fig(c_type, "longest_type_only_run_at_s", round(at, 1))
    fig(c_type, "blank_flat_share", round(blank_count / max(1, n), 3))
    fig(c_type, "method", "top2bin16 >= 0.78 (flat) + text bands @480px grey")
    key_s = "social-type-only-share-ceiling" if social else "type-only-share-ceiling"
    key_r = "social-type-only-run-ceiling" if social else "type-only-run-ceiling"
    declared = design_given and (key_s in floors or key_r in floors)
    blind = ("BLIND CLASS: flat-UI app footage is indistinguishable from "
             "typography by this measure - the classifier's domain is "
             "explainer/typographic films; on an app-footage film read the "
             "figures as 'flat frames carrying text', not as a verdict on "
             "kinetic typography.")
    if not declared:
        hole(c_type, f"measured (share {share * 100:.1f}%, longest run "
                     f"{longest:.2f}s at {at:.1f}s) but NO floors declared in "
                     f"--design ({key_s}/{key_r}) - figures only. {blind}")
    else:
        cs = floors.get(key_s, 0.55 if social else 0.40)
        cr = floors.get(key_r, 4.5 if social else 3.0)
        verdict(c_type, share <= cs and longest <= cr,
                f"type-on-bare-stage {share * 100:.1f}% of runtime (ceiling "
                f"{cs * 100:.0f}%), longest type-only run {longest:.2f}s at "
                f"{at:.1f}s (ceiling {cr}s). {blind}")


# ---------------------------------------------------------------- CHECK: OCR sweep
def _ocr_norm_latin(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return [w for w in re.sub(r"[^a-z0-9]+", " ", s.lower()).split() if w]


def _is_cjk(s):
    return any("぀" <= ch <= "鿿" or "＀" <= ch <= "￯" for ch in s)


CELLS_PAD = 6   # shared with narrower_than_block()'s edge-margin test, so
                # the two can never silently drift apart.


def _cells(img, min_h=9, join=6, gap=26, pad=CELLS_PAD):
    """Text cells by polarity-aware ink (holidayisle sweep.py): tesseract on a
    whole composed frame merges widely-spaced words into nonsense; the same
    word cropped alone reads at every psm."""
    g = np.asarray(img.convert("L"), dtype=np.int16)
    h, w = g.shape
    mode = np.array([np.bincount(r.clip(0, 255).astype(np.uint8)).argmax()
                     for r in g], dtype=np.int16)[:, None]
    ink = np.abs(g - mode) > 40
    rows = ink.sum(axis=1) > 3
    out, y = [], 0
    while y < h:
        if not rows[y]:
            y += 1
            continue
        y0, blank = y, 0
        while y < h and blank <= join:
            blank = 0 if rows[y] else blank + 1
            y += 1
        y1 = y - blank
        if y1 - y0 < min_h:
            continue
        cols = ink[y0:y1].sum(axis=0) > 0
        x = 0
        while x < w:
            if not cols[x]:
                x += 1
                continue
            x0, b = x, 0
            while x < w and b <= gap:
                b = 0 if cols[x] else b + 1
                x += 1
            if (x - b) - x0 >= 10:
                out.append((max(0, x0 - pad), max(0, y0 - pad),
                            min(w, x - b + pad), min(h, y1 + pad)))
    return out


def _ocr_frame(path, langs):
    img = Image.open(path)
    got = []
    for box in _cells(img):
        crop = img.crop(box)
        if crop.width < 12 or crop.height < 10:
            continue
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as fh:
            p = fh.name
        crop.save(p)
        r = run(["tesseract", p, "stdout", "-l", langs, "--psm", "7"], text=True)
        os.unlink(p)
        t = " ".join(r.stdout.split())
        if t:
            got.append(t)
    # SECOND READER, whole frame at default page segmentation. MEASURED 24 Oct
    # 2026 (sales-enablement how-to, frame 41.0 s): a white punch card over a
    # DIMMED plate made the row segmenter fuse card and plate into one cell,
    # --psm 7 read that blob as noise, and the cell reader returned nothing on a
    # frame plain tesseract read as "knowledge box". The forbidden-string hit
    # that frame carried was found only by a separate whole-frame sweep. Union
    # the two reads: this can only ADD text, so it widens detection and cannot
    # quiet a hit the cells found. The planted control still runs through both.
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as fh:
        p = fh.name
    img.convert("RGB").save(p)
    r = run(["tesseract", p, "stdout", "-l", langs, "--psm", "3"], text=True)
    os.unlink(p)
    t = " ".join(r.stdout.split())
    if t:
        got.append(t)
    return "  ".join(got)


def check_ocr_sweep(master, dur, forbidden, floors, work):
    c = new_check("ocr.forbidden_strings")
    if not forbidden:
        hole(c, "no must-not-appear list in --design, so the OCR sweep did not "
                "run. The frames were not read; this is not a pass.")
        return
    if run(["which", "tesseract"], text=True).returncode != 0:
        hole(c, "tesseract is not installed - the sweep CANNOT run. Not a pass.")
        return
    langs = floors.get("ocr-langs", "eng")
    fps = float(floors.get("ocr-fps", 2.0))
    latin = [(s, _ocr_norm_latin(s)) for s in forbidden if not _is_cjk(s)]
    cjk = [s for s in forbidden if _is_cjk(s)]
    fig(c, "forbidden_latin", len(latin))
    fig(c, "forbidden_cjk_declared_blind", cjk)
    # BLIND CLASS, measured not chosen (holidayisle sweep.py CJK_IN_SWEEP table):
    # no OCR matcher setting was both sensitive and specific on CJK - every CJK
    # string is a declared HOLE here, never a quiet pass.
    if cjk:
        print(f"      HOLE: {len(cjk)} CJK forbidden string(s) are NOT covered "
              f"by OCR (measured limit, holidayisle sweep CJK_IN_SWEEP) - verify "
              f"them source-side.")

    # Extract frames.
    fdir = work / "ocr_frames"
    fdir.mkdir(parents=True, exist_ok=True)
    for old in fdir.glob("f_*.png"):
        old.unlink()
    run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(master),
         "-vf", f"fps={fps}", str(fdir / "f_%05d.png")])
    frames = sorted(fdir.glob("f_*.png"))

    def _token_match(sig, T):
        """Is `sig` a contiguous TOKEN subsequence of `T`?"""
        n = len(sig)
        return any(T[j:j + n] == sig for j in range(len(T) - n + 1))

    def hits_in(txt, soft=None):
        """WORD BOUNDARIES, NOT CONTAINMENT.

        This compared `" ".join(sig) in " ".join(tokens)`, which is substring
        containment, so the forbidden token "ARR" matched inside the ordinary word
        "arrives" and reported 25 hits against a film whose frame says "where the
        request arrives". Containment silently downgrades what the check tests: any
        short forbidden token is a substring of ordinary English.

        Containment was catching one real thing - a forbidden string rendered
        CONCATENATED into a longer token, which tokenising cannot see. That is not
        dropped, it is DEMOTED: token matches are the verdict, substring-only matches
        are reported as a separate figure and a declared blind class, so nothing leaves
        the operator's view and a false alarm can no longer fail a clean film.
        """
        T = _ocr_norm_latin(txt)
        out = []
        for s, toks in latin:
            if not toks:
                continue
            n = min(3, len(toks))   # 3-word signature floor; shorter = whole string
            sigs = [toks[i:i + n] for i in range(len(toks) - n + 1)]
            if any(_token_match(sig, T) for sig in sigs):
                out.append(s)
            elif soft is not None:
                L = " ".join(T)
                if any(" ".join(sig) in L for sig in sigs):
                    soft.append(s)
        return out

    # POSITIVE control: the first Latin forbidden string rendered onto a real
    # extracted frame must be read back and hit; the SAME frame unplanted must
    # stay quiet (the paired control - a hit on both would prove nothing).
    if not frames:
        verdict(c, False, "zero frames extracted - zero of zero is not a pass")
        return
    if latin:
        fnt = None
        for cand in ("/System/Library/Fonts/Supplemental/Arial.ttf",
                     "/System/Library/Fonts/Supplemental/Arial Bold.ttf"):
            if Path(cand).exists():
                fnt = ImageFont.truetype(cand, 44)
                break
        if fnt is None:
            hole(c, "no system TTF found to plant the positive control - the "
                    "sweep is unproven on this machine. Not a pass.")
            return
        # The paired control wants a REAL frame of this film - but if the film
        # genuinely carries the forbidden string, the unplanted half fires as a
        # DETECTION, not an instrument fault (found by this gate's own planted
        # demo). So the base frame is the mid frame when it is clean, else a
        # synthetic neutral frame carrying an innocuous sentence - still read
        # through the full cells+OCR+match pipeline.
        mid = frames[len(frames) // 2]
        base_src = "real mid frame"
        if hits_in(_ocr_frame(mid, langs)):
            im0 = Image.new("RGB", (1280, 720), (11, 40, 54))
            d0 = ImageDraw.Draw(im0)
            d0.rectangle([100, 280, 1180, 420], fill=(255, 245, 226))
            d0.text((130, 320), "An ordinary sentence with nothing forbidden",
                    font=fnt, fill=(11, 40, 54))
            mid = work / "_ocr_base.png"
            im0.save(mid)
            base_src = ("synthetic neutral frame - the real mid frame already "
                        "carries a forbidden string, which the sweep reports "
                        "as a hit")
        # Full-width, bottom-anchored band. _cells() segments by ROW first,
        # across the FULL width of the image - a row only counts as "blank"
        # if NOTHING in it differs from that row's own dominant colour,
        # anywhere. A band with untouched side margins (the old [60, w-60]
        # inset) leaves whatever the real frame drew in those margins intact,
        # and on a dense frame (no genuine blank-row gap anywhere) that ink
        # keeps every row "non-blank" top to bottom - the planted caption
        # fuses into one giant cell with the rest of the frame's content,
        # and tesseract's --psm 7 (single text line) reads a multi-line
        # blob as empty. Reproduced on opax-record's 960x540 master: a
        # single (0,84)-(960,517) cell swallowed the plant, OCR'd ''.
        # Full width removes the untouched-margin leak; anchoring to the
        # frame's bottom edge removes the "below" boundary (nothing there
        # to merge with) - the only remaining boundary is the inset's own
        # blank margin above the text, which this band now fully controls.
        im = Image.open(mid).convert("RGB")
        band_h = min(80, im.height)
        dr = ImageDraw.Draw(im)
        dr.rectangle([0, im.height - band_h, im.width, im.height],
                     fill=(255, 245, 226))
        dr.text((20, im.height - band_h + 12), latin[0][0], font=fnt,
                 fill=(11, 40, 54))
        planted = work / "_ocr_planted.png"
        im.save(planted)
        ptxt = _ocr_frame(planted, langs)
        utxt = _ocr_frame(mid, langs)
        control(c, "fires on the first forbidden string planted on a frame",
                bool(hits_in(ptxt)), f"base: {base_src}; read: {ptxt[:70]!r}")
        control(c, "stays quiet on the same frame unplanted",
                not hits_in(utxt), f"base: {base_src}")

        # DISCRIMINATION control: a legitimate look-alike that shares one
        # word with a multi-word forbidden name (a person or party) but is
        # not the name itself - e.g. an institution name - must NOT fire.
        # Proves the n-gram match (hits_in) requires the whole adjacent
        # phrase, not a bare single-word substring, for any entry of 2+
        # words. Built from the same planting pipeline so a fix to one path
        # cannot silently diverge from the other.
        # BUILD THE LOOK-ALIKE FROM THE NORMALISED FIRST TOKEN, not from .split() on the
        # raw entry. An entry whose words are separated by a DOT rather than a space -
        # "nuclia.cloud" - has one .split() field, so this produced the look-alike
        # "nuclia.cloud University", which contains the WHOLE forbidden string. The
        # control then demanded the check stay quiet on a genuine violation, so a
        # correctly-firing matcher failed its own discrimination control. The intended
        # test is one token of a multi-token name, which toks[0] gives for both
        # separators.
        # THE SPECIMEN MUST BE VALID FOR THIS LIST, and choosing it blindly made the
        # control demand a FALSE verdict twice over. First it took .split()[0] of a
        # dot-separated entry and produced the whole forbidden string. Then, fixed to
        # use the normalised first token, it produced "nuclia University" - and
        # "nuclia" is ALSO a single-token forbidden entry here, so a correct matcher
        # fires and the control reads as a failure. A discrimination control is only
        # meaningful when its look-alike is genuinely NOT a violation, so the specimen
        # is chosen to satisfy that, and where no such specimen exists the control is
        # declared UNRUNNABLE rather than failed.
        singles = {t[0] for _, t in latin if len(t) == 1}
        multiword = [(s, toks) for s, toks in latin
                     if len(toks) >= 2 and toks[0] not in singles]
        if not multiword:
            control(c, "discrimination look-alike is UNRUNNABLE on this list",
                    True, "every multi-token entry's first token is itself a forbidden "
                          "single-token entry, so no non-violating look-alike exists. "
                          "Declared, not silently skipped, and not a pass for the "
                          "discrimination property.")
        if multiword:
            lookalike = f"{multiword[0][1][0]} University"
            im2 = Image.open(mid).convert("RGB")
            dr2 = ImageDraw.Draw(im2)
            dr2.rectangle([0, im2.height - band_h, im2.width, im2.height],
                          fill=(255, 245, 226))
            dr2.text((20, im2.height - band_h + 12), lookalike, font=fnt,
                      fill=(11, 40, 54))
            lookalike_path = work / "_ocr_lookalike.png"
            im2.save(lookalike_path)
            ltxt = _ocr_frame(lookalike_path, langs)
            control(c, "stays quiet on a one-word look-alike "
                        f"({lookalike!r}) of a multi-word forbidden name",
                    not hits_in(ltxt), f"base: {base_src}; read: {ltxt[:70]!r}")
    # TOKEN-BOUNDARY CONTROLS, pure-function so they cost no OCR and cannot be skipped.
    # Each case declares FIRE or QUIET up front. The look-alikes are real English words
    # that CONTAIN a forbidden token - which is the defect that produced 25 false hits.
    _probe = [t for s_, t in latin if len(t) == 1 and len(t[0]) <= 4]
    if _probe:
        tok = _probe[0][0]
        control(c, f"FIRES on the standalone token {tok!r}",
                bool(hits_in(f"a line containing {tok} on its own")),
                f"positive control for the token path")
        # the nearest legitimate look-alike: an ordinary word that CONTAINS the token
        _look = f"{tok}ives and {tok}ay and c{tok}ies"
        control(c, f"STAYS QUIET on ordinary words containing {tok!r} ({_look!r})",
                not hits_in(_look),
                "this is the exact false positive that failed a clean film: "
                "'ARR' matched inside 'arrives'")
        _soft = []
        hits_in(f"the word {tok}ives", soft=_soft)
        control(c, "a substring-only match is DEMOTED, not silent",
                bool(_soft), f"soft={_soft[:3]} - reported as a figure, never a FAIL")

    all_hits, soft_hits, readable = [], [], 0
    for fp in frames:
        txt = _ocr_frame(fp, langs)
        if len(txt) >= 20:
            readable += 1
        idx = int(fp.stem.split("_")[1]) - 1
        for h in hits_in(txt, soft=soft_hits):
            all_hits.append((idx / fps, h))
    fig(c, "frames_examined", len(frames))
    fig(c, "frames_with_readable_text", readable)
    fig(c, "substring_only_matches", sorted(set(soft_hits)))
    fig(c, "substring_blind_class",
        "A forbidden string rendered CONCATENATED inside a longer token is not a token "
        "match and does not FAIL. Any such case is listed in substring_only_matches for "
        "an operator to read. Demoted rather than dropped, because the containment test "
        "that would catch it also matched 'ARR' inside 'arrives'.")
    fig(c, "hits", [[round(t, 1), s[:60]] for t, s in all_hits[:10]])
    fig(c, "blind_classes", "CJK strings (measured); small stylised "
                            "low-light text (Bay-co brand-scanner lesson) - "
                            "every clean run is 'OCR clean, not eye-verified'")
    verdict(c, len(frames) > 0 and not all_hits,
            f"{len(frames)} frames @ {fps}fps, {readable} with readable text; "
            f"{len(all_hits)} forbidden-string hit(s); {len(cjk)} CJK string(s) "
            f"declared uncovered (HOLE). OCR clean, not eye-verified.")


# ---------------------------------------------------------------- CHECK: crop edges
def _ink_mask(img, x0, y0, x1, y1, tol=46):
    """Ink = far enough from the region's own MODAL luminance, either polarity.
    The ground is the mode over coarse 16-level bins refined inside the winning
    bin - a single-level mode is decided by flatness, not coverage, and comes
    back inverted on a gradient stage (holidayisle measure.py)."""
    reg = img[y0:y1, x0:x1]
    lum = (0.299 * reg[..., 0] + 0.587 * reg[..., 1] + 0.114 * reg[..., 2])
    hist = np.bincount(np.clip(lum, 0, 255).astype(np.uint8).ravel(),
                       minlength=256)
    coarse = hist.reshape(16, 16).sum(axis=1)
    cb = int(np.argmax(coarse))
    bg = cb * 16 + int(np.argmax(hist[cb * 16:(cb + 1) * 16]))
    return np.abs(lum - bg) > tol


def edge_crossings(img, rect, reach=5, lo=2, hi=60):
    """Does a crop edge pass THROUGH type? A slice is ink within `reach` px on
    BOTH sides of the edge in the SAME columns; a crossed border is ONE run
    hundreds of px wide, a sliced line is many glyph-sized ones (measured:
    historical positive 10 runs, shipped good 0, border look-alikes <=4, real
    slices 115-118 - holidayisle gate.py)."""
    x0, y0, x1, y1 = (int(v) for v in rect)
    H = img.shape[0]
    best = (0, None)
    for edge, ey in (("top", y0), ("bottom", y1)):
        a, b = ey - reach, ey + reach
        if a < 0 or b > H or x1 <= x0:
            continue
        m = _ink_mask(img, x0, a, x1, b)
        inside = m[reach:, :].any(axis=0) if edge == "top" else m[:reach, :].any(axis=0)
        outside = m[:reach, :].any(axis=0) if edge == "top" else m[reach:, :].any(axis=0)
        cross = inside & outside
        runs, n = [], 0
        for v in cross:
            if v:
                n += 1
            elif n:
                runs.append(n)
                n = 0
        if n:
            runs.append(n)
        glyphy = sum(1 for r in runs if lo <= r <= hi)
        if glyphy > best[0]:
            best = (glyphy, edge)
    return best


def resolve_window(win, where=""):
    """A crop window's shape is ambiguous BY CONSTRUCTION: (x,y,w,h) and
    (x0,y0,x1,y1) are the same four numbers whenever w>x and h>y, which is
    the ordinary case (a window rarely starts near the frame's right/bottom
    edge). Guessing from the values - "corners if win[2]>win[0]" - picked
    the wrong rectangle on opax-record's fitted_windows.json and measured
    edges that do not exist, a clean-looking FAIL-free run that proved
    nothing (found 5 Oct 2026). The form is DECLARED, never inferred: a
    window is a dict `{"form": "corners"|"xywh", "box": [a, b, c, d]}`. A
    bare list/tuple, or any other form string, is ambiguous input and is
    refused - not guessed - by raising."""
    tag = f" ({where})" if where else ""
    if not isinstance(win, dict) or "form" not in win or "box" not in win:
        raise ValueError(
            f"window{tag} does not declare its form - expected "
            f"{{'form': 'corners'|'xywh', 'box': [a,b,c,d]}}, got {win!r}. "
            f"(x,y,w,h) and (x0,y0,x1,y1) are indistinguishable by shape "
            f"when w>x and h>y - declare which one this is, never guess it.")
    box = win["box"]
    if len(box) != 4:
        raise ValueError(f"window{tag} box must have 4 values, got {box!r}")
    form = win["form"]
    if form == "corners":
        x0, y0, x1, y1 = box
    elif form == "xywh":
        x0, y0, w, h = box
        x1, y1 = x0 + w, y0 + h
    else:
        raise ValueError(f"window{tag} form {form!r} not recognised - "
                          f"expected 'corners' or 'xywh'")
    return (x0, y0, x1, y1)


def visible_rect(win, amount, z_frac, anchor="centre"):
    """THE RECT ACTUALLY ON SCREEN, not the authored window: a zoom crops
    h*a/(2(1+a)) off each edge and the edge SWEEPS as the move runs. `win`
    is already resolved to (x0,y0,x1,y1) by resolve_window() - this
    function does no shape-guessing of its own."""
    x0, y0, x1, y1 = win
    w, h = x1 - x0, y1 - y0
    z = 1.0 + (amount or 0.0) * z_frac
    vw, vh = w / z, h / z
    dx = (w - vw) / 2
    dy_top = 0.0 if anchor == "top" else (h - vh) / 2
    return (int(round(x0 + dx)), int(round(y0 + dy_top)),
            int(round(x0 + w - dx)), int(round(y0 + dy_top + vh)))


def clip_frame(path, t, dims_cache={}):
    if path not in dims_cache:
        st = probe_json(path, "stream=width,height", "v:0")["streams"][0]
        dims_cache[path] = (st["width"], st["height"])
    w, h = dims_cache[path]
    p = run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{t:.4f}",
             "-i", str(path), "-frames:v", "1", "-f", "rawvideo",
             "-pix_fmt", "rgb24", "-"])
    return np.frombuffer(p.stdout, dtype=np.uint8).reshape(h, w, 3).astype(np.int16)


SLICE_RUNS = 8
BLOCK_TOL = 10   # px slack above _cells()'s own pad=6, for rounding only -
                 # not a dial tuned against any one film's footage.


def narrower_than_block(img, rect, tol=BLOCK_TOL, edge_margin=CELLS_PAD):
    """Does the window's own WIDTH cut into a line it is supposed to be
    showing whole, or does it land clear? Geometric, not statistical: a
    fitter can satisfy edge_crossings() by shrinking the window until its
    top/bottom edges land clear of ink - but edge_crossings() never looks
    at the LEFT/RIGHT edges, so a window narrower than the lines it
    contains slices every line mid-word at both sides and reports zero
    crossings (found live: a citation beat's window was shrunk to pass
    top/bottom and sliced every line mid-word; caught by eye, not by the
    gate).

    The measure is PER-CELL STRADDLE, not a union of everything nearby: a
    line the window slices starts inside the window and runs past its
    edge, so the cell carrying that line has the window's edge landing
    STRICTLY INSIDE it (with `tol` margin either side, to absorb _cells()'s
    own 6px pad). A cell the window deliberately excludes - a second
    column, a sidebar - does not straddle either edge: the window's edge
    sits in the gap before or after it, outside the cell entirely. An
    earlier union-of-everything-overlapping-in-y version of this measure
    got this wrong on opax-record's s2b: a clean punch-in on the LEFT
    column of a two-column stat panel was flagged, because the RIGHT
    column's cell - never touched by the window - still widened the
    unioned "block" past the window's own edge.

    A second class is excluded outright: a ROW that carries ink touching
    BOTH the source frame's left and right edge (within `edge_margin`,
    _cells()'s own pad) is not usable evidence, whether that ink is one
    fused cell or several. _cells() pads every box it finds, so a genuine
    line of body text sized to sit inside a page's own margins never
    legitimately touches both the frame's left AND right edge - that
    pattern is what a page-width UI row looks like, fused into one cell
    when nothing clears the column gap, or split into several when it
    does (a logo on the left, a menu on the right, with page padding
    between them is still one navigation ROW, not two text lines). Found
    on opax-record: s3's search-bar-and-buttons row fused into one (0,
    frame_width) cell; s4's top nav split into a left cell touching x=0
    and a separate right cell touching the far edge, with nothing between
    them - a window sitting inside that gap, on BOTH sides, read as
    identical geometry to a genuine mid-line slice in both cases, though
    the actual crops (checked by eye) were clean. This check cannot tell
    "page-width chrome" from "one long line of prose" from the ink alone,
    so it declines to judge any window whose y-range's only evidence
    includes edge-touching content on both sides, rather than guess.

    Returns (narrower: bool | None, extent: tuple | None, blind: str |
    None). `blind` is None when a verdict was reached; otherwise it names
    WHY no verdict could be reached ("no ink cell overlapped this window's
    y-range" or "ink touches both frame edges in this row - not usable
    evidence of a single line") - the caller must report that, never
    silently pass it."""
    x0, y0, x1, y1 = (int(v) for v in rect)
    pil = img if isinstance(img, Image.Image) else \
        Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    img_w = pil.size[0]
    cells = _cells(pil)
    overlapping = [b for b in cells if max(b[1], y0) < min(b[3], y1)]
    if not overlapping:
        return None, None, "no ink cell overlapped this window's y-range"
    touches_left = any(b[0] <= edge_margin for b in overlapping)
    touches_right = any(b[2] >= img_w - edge_margin for b in overlapping)
    if touches_left and touches_right:
        return None, None, ("ink touches both frame edges in this row - "
                             "not usable evidence of a single line")

    def edge_inside(cell, edge_x):
        return cell[0] + tol < edge_x < cell[2] - tol

    hits = [b for b in overlapping if edge_inside(b, x0) or edge_inside(b, x1)]
    if not hits:
        return False, None, None
    return True, (min(b[0] for b in hits), max(b[2] for b in hits)), None


def check_crop_edges(crops, work):
    c = new_check("crop.edges")
    # CONTROLS, synthetic but through the real instrument: a window edge
    # through a line of type must fire; the same window with its edge in the
    # inter-line gap must stay quiet.
    ctl = np.full((400, 900, 3), 245, dtype=np.uint8)
    im = Image.fromarray(ctl)
    dr = ImageDraw.Draw(im)
    fnt = None
    for cand in ("/System/Library/Fonts/Supplemental/Arial.ttf",):
        if Path(cand).exists():
            fnt = ImageFont.truetype(cand, 30)
    if fnt is None:
        hole(c, "no system TTF to build the controls - unproven, not a pass")
        return
    sentence = "The quick brown fox jumps over the lazy dog"
    for y in (80, 140, 200, 260):
        dr.text((60, y), sentence, font=fnt, fill=(20, 20, 20))
    short_word, short_y = "Fox", 340
    dr.text((60, short_y), short_word, font=fnt, fill=(20, 20, 20))
    line_box = dr.textbbox((60, 80), sentence, font=fnt)        # (l, t, r, b)
    word_box = dr.textbbox((60, short_y), short_word, font=fnt)
    arr = np.asarray(im, dtype=np.int16)
    bad_rect = (40, 20, 860, 95)    # bottom edge y=95, through the y=80 line's glyphs
    good_rect = (40, 20, 860, 125)  # bottom edge y=125, in the gap between lines
    gb, _ = edge_crossings(arr, bad_rect)
    gg, _ = edge_crossings(arr, good_rect)
    control(c, "fires on an edge through a line of type", gb >= SLICE_RUNS,
            f"{gb} glyph runs")
    control(c, "stays quiet on an edge in the inter-line gap", gg < SLICE_RUNS,
            f"{gg} glyph runs")

    # WINDOW-FORM controls: the two accepted declarations must resolve to
    # the identical rect, a crop placed through type in EITHER declared
    # form must still FAIL through the real check_crop_edges path (not just
    # edge_crossings() directly, which the two controls above already
    # cover), the look-alike landing in the whitespace gap must PASS, and
    # an undeclared/bare window must be refused, never guessed.
    corners_win = {"form": "corners", "box": [40, 20, 860, 95]}
    xywh_win = {"form": "xywh", "box": [40, 20, 820, 75]}
    try:
        same_rect = (resolve_window(corners_win) == resolve_window(xywh_win)
                     == (40, 20, 860, 95))
    except ValueError:
        same_rect = False
    control(c, "corners and xywh declarations of the same window resolve "
                "to the identical rect", same_rect,
            f"corners={resolve_window(corners_win)} xywh={resolve_window(xywh_win)}")
    raised = False
    try:
        resolve_window([40, 20, 860, 95])   # bare list: form not declared
    except ValueError:
        raised = True
    control(c, "a bare/undeclared window is refused, not guessed", raised,
            "resolve_window([40,20,860,95]) without a 'form'")

    ctl_png = work / "_crop_edges_ctl.png"
    im.save(ctl_png)
    bad_win_corners = {"source": "ctl:bad-corners", "media": ("still", ctl_png),
                        "window": {"form": "corners", "box": [40, 20, 860, 95]},
                        "start": None, "dur": None, "amount": None,
                        "motion": None, "anchor": "centre", "photographic": False}
    bad_win_xywh = {"source": "ctl:bad-xywh", "media": ("still", ctl_png),
                     "window": {"form": "xywh", "box": [40, 20, 820, 75]},
                     "start": None, "dur": None, "amount": None,
                     "motion": None, "anchor": "centre", "photographic": False}
    good_win_corners = {"source": "ctl:good-corners", "media": ("still", ctl_png),
                         "window": {"form": "corners", "box": [40, 20, 860, 125]},
                         "start": None, "dur": None, "amount": None,
                         "motion": None, "anchor": "centre", "photographic": False}

    def _still_glyphy(entry):
        img = np.asarray(Image.open(entry["media"][1]).convert("RGB"), dtype=np.int16)
        rect = resolve_window(entry["window"], entry["source"])
        g, _ = edge_crossings(img, rect)
        return g

    control(c, "the real check path FAILs a corners-declared window through type",
            _still_glyphy(bad_win_corners) >= SLICE_RUNS,
            f"{_still_glyphy(bad_win_corners)} glyph runs")
    control(c, "the real check path FAILs the SAME window declared as xywh",
            _still_glyphy(bad_win_xywh) >= SLICE_RUNS,
            f"{_still_glyphy(bad_win_xywh)} glyph runs")
    control(c, "the real check path PASSes the look-alike window in the "
                "inter-line whitespace",
            _still_glyphy(good_win_corners) < SLICE_RUNS,
            f"{_still_glyphy(good_win_corners)} glyph runs")

    # NARROW-CROP-WIDTH controls: edge_crossings() only ever looks at the
    # top/bottom edges, so a window shrunk narrower than its own text block
    # slices every line mid-word at the left/right edges and reports zero
    # crossings - a fitter shrinks to green. Prove narrower_than_block()
    # catches exactly that, on the block's REAL measured extent (line_box),
    # not a guessed one.
    l, t, r, b = line_box
    narrow_rect = (int(l + (r - l) * 0.3), 20, int(l + (r - l) * 0.7), 310)
    wide_rect = (l - 20, 20, r + 20, 310)
    n_narrow, extent_narrow, blind_narrow = narrower_than_block(arr, narrow_rect)
    n_wide, extent_wide, blind_wide = narrower_than_block(arr, wide_rect)
    control(c, "FAILs a window narrower than the text block it frames "
                "(slices every line mid-word)",
            n_narrow is True,
            f"window x[{narrow_rect[0]},{narrow_rect[2]}] vs block "
            f"x{extent_narrow}")
    control(c, "PASSes the same window widened to contain the block",
            n_wide is False,
            f"window x[{wide_rect[0]},{wide_rect[2]}] vs block x{extent_wide}")
    wl, wt, wr, wb = word_box
    tight_rect = (wl - 4, short_y - 4, wr + 4, short_y + 40)
    n_tight, extent_tight, blind_tight = narrower_than_block(arr, tight_rect)
    control(c, "PASSes the look-alike: a deliberately tight crop on a "
                "short single line that genuinely fits",
            n_tight is False,
            f"window x[{tight_rect[0]},{tight_rect[2]}] vs block x{extent_tight}")

    # TWO-COLUMN discrimination control (GM, found live on opax-record s2b):
    # the union-of-everything-overlapping approach flagged a clean punch-in
    # on column 1 because column 2's cell - never touched by the window -
    # still widened the unioned extent past the window's own edge. Prove
    # the per-cell-straddle rewrite tells "frames column 1 cleanly" from
    # "slices into column 1" apart, on a real two-column layout.
    two_col = Image.new("RGB", (900, 200), (245, 245, 245))
    dr2 = ImageDraw.Draw(two_col)
    col1_text, col2_text = "Alpha Beta Gamma", "Delta Epsilon Zeta Eta"
    dr2.text((60, 80), col1_text, font=fnt, fill=(20, 20, 20))
    dr2.text((500, 80), col2_text, font=fnt, fill=(20, 20, 20))
    col1_box = dr2.textbbox((60, 80), col1_text, font=fnt)
    col2_box = dr2.textbbox((500, 80), col2_text, font=fnt)
    two_col_arr = np.asarray(two_col, dtype=np.int16)
    gap_mid = (col1_box[2] + col2_box[0]) // 2
    frame_clean = (40, 60, gap_mid, 140)                       # edge in the gap
    slice_into_col2 = (40, 60, col2_box[0] + 20, 140)          # edge inside col 2
    n_clean, ext_clean, _ = narrower_than_block(two_col_arr, frame_clean)
    n_slice, ext_slice, _ = narrower_than_block(two_col_arr, slice_into_col2)
    control(c, "PASSes a window framing one column of a two-column layout "
                "cleanly (edge lands in the gap, not in column 2)",
            n_clean is False,
            f"window x[{frame_clean[0]},{frame_clean[2]}] col1={col1_box[:1]+col1_box[2:3]} "
            f"col2={col2_box[:1]+col2_box[2:3]}")
    control(c, "FAILs a window whose edge falls inside column 2's own line "
                "(same two-column layout)",
            n_slice is True,
            f"window x[{slice_into_col2[0]},{slice_into_col2[2]}] vs hit "
            f"x{ext_slice}")

    # FULL-SPAN EXCLUSION control (found live on opax-record s3): a search
    # box, its buttons and a full-width rule failed to clear the column gap
    # anywhere across their shared row and fused into one cell spanning the
    # whole 1920px frame. A window sitting inside that cell on both sides is
    # geometrically identical to a genuine mid-line slice, but this check
    # cannot tell "merged UI chrome" from "one long line of prose" from the
    # ink alone - it must decline to judge, not guess FAIL.
    chrome = Image.new("RGB", (900, 120), (245, 245, 245))
    dr3 = ImageDraw.Draw(chrome)
    # Several short labels packed with <26px gaps - same mechanism as the
    # real s3 row (a search box's text plus two button labels, none of
    # them individually touching an edge) - fuse into ONE cell that DOES
    # span edge-to-edge once unioned, exactly as _cells() produced on the
    # real asset. A single solid outline/rule does not reproduce this: a
    # row that is ONE uniform colour has no ink by _cells()'s own
    # mode-deviation definition (confirmed while building this control -
    # a flat rule is invisible to it, not a false FAIL risk).
    x, gap = 4, 18
    for seg in ("Search the whole record archive here today", "Ask",
                "Options", "More", "X"):
        dr3.text((x, 45), seg, font=fnt, fill=(20, 20, 20))
        x += dr3.textlength(seg, font=fnt) + gap
    chrome_arr = np.asarray(chrome, dtype=np.int16)
    swallowed = (300, 30, 600, 95)   # inside the fused row on both sides
    n_chrome, ext_chrome, blind_chrome = narrower_than_block(chrome_arr, swallowed)
    control(c, "declines to judge a window swallowed by an edge-to-edge "
                "cell (merged UI chrome, not a provable text line)",
            n_chrome is None and blind_chrome is not None
            and "both frame edges" in (blind_chrome or ""),
            f"narrower={n_chrome} blind={blind_chrome!r}")

    # SPLIT NAV-ROW control (found live on opax-record s4, a second real
    # instance of the same class): the single-cell exclusion above does not
    # cover a page-width row that splits into TWO cells - a logo hugging
    # the left edge, a menu hugging the right, nothing between them wide
    # enough to merge - because neither cell alone spans edge-to-edge. A
    # window sitting in the gap between them, straddling into both, must
    # still be declined, not flagged, for the same reason: this check
    # cannot tell a navigation row from two lines of prose that happen to
    # frame the window on both sides.
    nav = Image.new("RGB", (900, 120), (245, 245, 245))
    dr4 = ImageDraw.Draw(nav)
    dr4.text((2, 45), "LOGO", font=fnt, fill=(20, 20, 20))
    menu_w = dr4.textlength("Menu", font=fnt)
    dr4.text((898 - menu_w, 45), "Menu", font=fnt, fill=(20, 20, 20))
    nav_arr = np.asarray(nav, dtype=np.int16)
    between = (300, 30, 600, 95)   # in the gap, but straddling toward both
    n_nav, ext_nav, blind_nav = narrower_than_block(nav_arr, between)
    control(c, "declines to judge a window between a left-edge logo and a "
                "right-edge menu (split nav row, not a provable text line)",
            n_nav is None and blind_nav is not None
            and "both frame edges" in (blind_nav or ""),
            f"narrower={n_nav} blind={blind_nav!r}")

    # REACHABILITY ON A CONTENT CLASS, measured 9 Oct 2026 (university) so the next
    # person meets it rather than re-deriving it. On a DENSELY SET CONTINUOUS
    # PAGE - a streaming answer, a question log, a list of rows - there is no
    # horizontal band of whitespace at any height, so NO window height puts the
    # bottom edge in a row gap at every sample of a move. Twelve window and
    # in-point combinations across three beats, windows derived from the ink
    # UNION across all nine samples: none clear. With anchor="top" the zoom eats
    # upward into text as it runs, so the failure is structural rather than a
    # tuning problem.
    # DO NOT "fix" it by shrinking the window. Doing that on that film narrowed
    # one punch to 1004px and sliced the beat's own evidence mid-phrase at the
    # RIGHT edge - a bottom edge crossing a line of a dense page shows no partial
    # glyph in the delivered plate, while a right edge through a word is visible
    # and wrong. Trading a measured defect for a visible one is optimising the
    # statistic. Crop and LOOK at the flagged timestamp before deciding.
    if not crops:
        hole(c, "no crop windows in --segments, so no edge was checked. The "
                "defect this exists for (an edge slicing glyphs keeps full "
                "glyph height, so legibility gates cannot see it) is unmeasured.")
        return
    sliced, holes, undeclared, narrow, narrow_blind, examined = \
        [], [], [], [], [], 0
    for s in crops:
        kind, path = s["media"]
        try:
            win = resolve_window(s["window"], s["source"])
        except ValueError as e:
            undeclared.append(f"{s['source']}: {e}")
            continue
        worst = (0, None, None)
        narrow_hit, narrow_extent, narrow_rect, measured, last_blind = \
            False, None, None, False, None
        if kind == "still":
            img = np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)
            g, edge = edge_crossings(img, win)
            worst = (g, edge, None)
            n, ext, blind = narrower_than_block(img, win)
            if n is None:
                last_blind = blind
            else:
                measured = True
                if n:
                    narrow_hit, narrow_extent, narrow_rect = True, ext, win
            examined += 1
        else:
            if s["start"] is None or not s.get("dur"):
                continue
            amount = s.get("amount") or 0.0
            direction = s.get("motion") or "none"
            samples = 9
            examined += 1
            for i in range(samples):
                u = i / (samples - 1)
                t = s["start"] + u * s["dur"]
                if direction == "none" or not amount:
                    zf = 0.0
                else:
                    sm = u * u * (3 - 2 * u)
                    zf = sm if direction == "in" else 1 - sm
                img = clip_frame(path, t)
                vrect = visible_rect(win, amount, zf, s.get("anchor", "centre"))
                g, edge = edge_crossings(img, vrect)
                if g > worst[0]:
                    worst = (g, edge, round(t, 2))
                n, ext, blind = narrower_than_block(img, vrect)
                if n is None:
                    last_blind = blind
                else:
                    measured = True
                    if n and not narrow_hit:
                        narrow_hit, narrow_extent, narrow_rect = True, ext, vrect
        if worst[0] >= SLICE_RUNS:
            tgt = holes if s["photographic"] else sliced
            tgt.append(f"{s['source']} {worst[1]} edge ({worst[0]} glyph runs"
                       + (f" @ {worst[2]}s" if worst[2] is not None else "") + ")")
        if narrow_hit:
            tgt = holes if s["photographic"] else narrow
            tgt.append(f"{s['source']} window x[{narrow_rect[0]},{narrow_rect[2]}] "
                        f"narrower than its own text block x{narrow_extent}")
        elif not measured:
            narrow_blind.append(f"{s['source']}: {last_blind}")
    fig(c, "windows_examined", examined)
    fig(c, "photographic_holes", holes)
    fig(c, "undeclared_window_form", undeclared)
    fig(c, "narrow_crop_holes", narrow_blind)
    fig(c, "narrow_crop_blind_class",
        "a window is unmeasured for narrow-width slicing, named above with "
        "a reason, when (a) its y-range overlaps no detected ink cell - "
        "nothing to compare against - or (b) the only cell(s) overlapping "
        "span edge-to-edge of the source frame, which this check treats as "
        "merged UI chrome (a search box, its buttons, a full-width rule "
        "failing to clear the column gap anywhere in their shared row) "
        "rather than a single provable line of prose, because the two look "
        "geometrically identical from ink alone and a wrong guess either "
        "way is worse than an admitted hole. The measure judges each ink "
        "cell against the window individually (does an edge land strictly "
        "inside it) rather than unioning everything nearby, specifically "
        "so a column or sidebar the window correctly excludes cannot "
        "inflate a false FAIL.")
    if undeclared:
        print(f"      HOLE: {len(undeclared)} window(s) do not declare their "
              f"form (corners/xywh) - NOT measured, not guessed, not a "
              f"pass: {undeclared}")
    if holes:
        print(f"      HOLE: {len(holes)} crossing(s) over declared photographic "
              f"texture, which this check cannot tell from type: {holes}")
    if narrow_blind:
        print(f"      HOLE: {len(narrow_blind)} window(s) had no ink cell to "
              f"compare against for narrow-width slicing - unmeasured, not "
              f"a pass: {narrow_blind}")
    verdict(c, examined > 0 and not sliced and not narrow,
            f"{examined} window(s) examined (swept band, 9 samples per move); "
            f"{len(sliced)} edge(s) through type"
            + (": " + "; ".join(sliced[:4]) if sliced else "")
            + f"; {len(narrow)} window(s) narrower than their own text block"
            + (": " + "; ".join(narrow[:4]) if narrow else "")
            + (f"; {len(holes)} photographic HOLE(s), not passes" if holes else "")
            + (f"; {len(undeclared)} window(s) with no declared form, "
               f"NOT examined" if undeclared else "")
            + (f"; {len(narrow_blind)} window(s) with no ink cell to compare "
               f"narrow-width against, NOT measured" if narrow_blind else ""))


# ---------------------------------------------------------------- CHECK: reference echo
# (tourism reference_echo.py: CJK-aware normalisation - the obvious
# `[^a-z0-9 ]` normaliser strips every Japanese codepoint and reports any two
# Japanese strings as a VERBATIM match at overlap 1.00.)
_CJK = r"぀-ヿ㐀-䶿一-鿿ｦ-ﾟ"
_CJK_RE = re.compile(rf"[{_CJK}]")
ECHO_STOP = {"the", "a", "an", "of", "it", "its", "to", "is", "in", "on", "and",
             "as", "you", "your", "that", "this", "for", "at", "by", "with", "not"}
RUN_WORDS, RUN_CJK = 4, 10   # 4 words; Japanese runs 2-3 chars/word, so 10 chars
                             # - a unit CONVERSION, never a tuned dial.


def echo_norm(s):
    s = s.lower()
    s = re.sub(rf"([{_CJK}])", r" \1 ", s)
    return re.sub(rf"[^a-z0-9 {_CJK}]", " ", s).split()


def echo_overlap(a, b):
    A = {w for w in echo_norm(a) if w not in ECHO_STOP}
    B = {w for w in echo_norm(b) if w not in ECHO_STOP}
    return len(A & B) / len(A | B) if A and B else 0.0


def echo_longest_run(a, b):
    A, B = echo_norm(a), echo_norm(b)
    best, best_cjk = 0, False
    for i in range(len(A)):
        for j in range(len(B)):
            k = 0
            while i + k < len(A) and j + k < len(B) and A[i + k] == B[j + k]:
                k += 1
            if k > best:
                best, best_cjk = k, bool(A[i] and _CJK_RE.match(A[i]))
    return best, best_cjk


def echo_findings(mine, corpus):
    out = []
    for m in mine:
        for ref in corpus:
            if echo_norm(m) == echo_norm(ref):
                out.append(("VERBATIM", m, ref, 1.0))
                continue
            n, cjk = echo_longest_run(m, ref)
            ov = echo_overlap(m, ref)
            if n >= (RUN_CJK if cjk else RUN_WORDS) or ov >= 0.6:
                out.append(("NEAR", m, ref, ov))
    return out


def check_reference_echo(ref_path, timing):
    c = new_check("reference.echo")
    corpus = []
    for line in Path(ref_path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        corpus.append(line.split("\t", 1)[-1])
    mine = [t for s in (timing or []) for t in s["texts"]]
    fig(c, "reference_strings", len(corpus))
    fig(c, "own_strings", len(mine))

    # Controls: fire on a verbatim plant; CJK discrimination in BOTH directions
    # (unrelated Japanese must NOT match - the stripped-normaliser failure; a
    # real substring lift must; a shared subject noun must not - the unit rule).
    if corpus:
        control(c, "fires on a planted verbatim lift of a reference string",
                any(k == "VERBATIM" for k, *_ in
                    echo_findings([corpus[0]], corpus)))
    ja_a = "モンクアザラシはどこで見られますか。"
    ja_b = "季節限定ワイルドライフツアーは五月から十月まで運航します。"
    ja_topic = "モンクアザラシは、海洋保護区の洞窟付近で見られる可能性があります。"
    ja_lift = "宿の予約はモンクアザラシはどこで見られますかと同じ画面で。"
    control(c, "two unrelated Japanese strings do NOT normalise identically",
            echo_norm(ja_a) != echo_norm(ja_b))
    control(c, "unrelated Japanese pair stays quiet",
            not echo_findings([ja_a], [ja_b]))
    control(c, "a shared 8-char subject noun stays quiet (unit conversion)",
            not echo_findings([ja_a], [ja_topic]))
    control(c, "a genuine >=10-char Japanese lift fires",
            bool(echo_findings([ja_a], [ja_lift])))

    if not corpus:
        hole(c, "--reference-strings file is empty - nothing to diff against")
        return
    if not mine:
        hole(c, "the --segments file carries no text/caption/audio strings, so "
                "the film's own copy could not be diffed. Supply segments with "
                "text fields; this is not a pass.")
        return
    found = echo_findings(mine, corpus)
    fig(c, "echoes", [[k, m[:60], r[:60], round(ov, 2)] for k, m, r, ov in found[:8]])
    verdict(c, not found,
            f"{len(mine)} own string(s) diffed against {len(corpus)} reference "
            f"string(s); {len(found)} echo(es)"
            + ("" if not found else ": " + "; ".join(
                f"{k} {m[:40]!r}" for k, m, _, _ in found[:3])))


# ---------------------------------------------------------------- main
# ---------------------------------------------------------------- CHECK: storyboard
# Concept-film rule (video-production skill 0c, GM 4 Oct 2026): a film with no demo
# site must be ILLUSTRATED, not typeset. The RAG explainer rejected 30 Sep 2026
# passed every gate above because none of them reads whether the IDEA is shown.
# This check reads the storyboard's own declaration per beat and holds it to the
# concept-film floors, then cross-checks each declared illustration beat against
# the measured per-shot motion so the label cannot stand in for the motion.
#
# STORYBOARD.json: {"film_type": "concept|demo|hybrid",
#                   "beats": [{"id","start","dur","kind": "illustration|plate|type|card",
#                              "mechanism": bool, "line": "..."}]}
def check_design_floors(design_path, floors, unreadable):
    """Every floor the author DECLARED was read, and the ones that were not are
    named. A declared floor the gate cannot parse used to kill the whole run on a
    traceback; before that it would have been the worse failure, a silent drop."""
    c = new_check("design.floors")
    if not design_path:
        hole(c, "no --design supplied: no floor was declared, so none was applied. "
                "Not a pass.")
        return
    fig(c, "floors_read", {k: floors[k] for k in sorted(floors)})
    fig(c, "floors_unreadable", unreadable)
    # Controls: a unit-suffixed value must be READ, and a genuine typo must be NAMED.
    import tempfile as _tf
    probe = Path(_tf.mkdtemp()) / "d.md"
    probe.write_text("- still-run-ceiling: 2.5s\n- lufs-target: abc\n")
    f2, u2 = parse_design(probe)[1:]
    control(c, "a floor declared with its unit (2.5s) is read as a number",
            f2.get("still-run-ceiling") == 2.5, f"read {f2.get('still-run-ceiling')!r}")
    control(c, "a genuinely unparseable floor is NAMED, not dropped and not fatal",
            u2.get("lufs-target") == "abc", f"unreadable {u2}")
    # A heading whose list is emptied by prose must be DISTINGUISHED from no
    # heading at all. Both previously reported identically, which is how three
    # films ran an OCR sweep over zero strings without knowing.
    bad = Path(_tf.mkdtemp()) / "d.md"
    bad.write_text("## Must not appear\n\nOn screen or in the narration:\n\n"
                   "- Knowledge Box\n- nuclia\n")
    f3, _, u3 = parse_design(bad)
    control(c, "a must-not-appear list emptied by prose is NAMED, not silently "
               "reported as absent",
            f3 == [] and "_forbidden_list_empty" in u3
            and "On screen" in u3["_forbidden_list_empty"],
            f"{len(f3)} parsed; {str(u3.get('_forbidden_list_empty'))[:70]}")
    good = Path(_tf.mkdtemp()) / "g.md"
    good.write_text("## Must not appear\n\n- Knowledge Box\n- nuclia\n")
    f4, _, u4 = parse_design(good)
    control(c, "a well-formed list stays quiet (negative control)",
            f4 == ["Knowledge Box", "nuclia"] and "_forbidden_list_empty" not in u4,
            f"{f4}")
    nohead = Path(_tf.mkdtemp()) / "n.md"
    nohead.write_text("## Floors\n\n- lufs-target: -14\n")
    f5, _, u5 = parse_design(nohead)
    control(c, "a file with NO heading is not reported as malformed "
               "(discriminates absence from malformation)",
            f5 == [] and "_forbidden_list_empty" not in u5, f"{f5}, {list(u5)}")
    empty = unreadable.pop("_forbidden_list_empty", None)
    if empty:
        fig(c, "forbidden_list_empty", True)
    verdict(c, not unreadable and not empty,
            f"{len(floors)} floor(s) declared and read from {design_path}"
            + (f"; UNREADABLE and therefore NOT APPLIED: {unreadable}"
               if unreadable else "")
            + (f"; MALFORMED must-not-appear list - {empty}" if empty else ""))


# Element kinds that are a shot's OUTLINE rather than its interior. A beat whose
# only declared children are these is the rejected-concept-film shape in its own
# words: "I authored boundaries and labels, and in about a third of the shots I
# never authored the interiors." It is the nearest legitimate look-alike to a
# populated beat, so it gets its own control.
INERT_ELEMENT_KINDS = re.compile(r"boundary|label|tab|\bmark\b|title|caption|heading",
                                 re.I)


def eval_interiors(beats):
    """STATIC interior check (video-production skill 0c; GM 4 Oct 2026 concept-film
    directive). Reads a storyboard's own per-beat element inventory, so it can fail
    a STORYBOARD BEFORE ANYTHING IS RENDERED - the cheapest instrument of the set
    and the earliest. Returns (problems, holes, figures).

    A beat that declares no inventory is a HOLE, never a pass and never a FAIL:
    storyboards authored before this schema (4 Oct) carry no `elements`, and
    reporting them as failures would be a false FAIL about the schema rather than
    a finding about the film.
    """
    problems, holes = [], []
    examined = 0
    for b in beats:
        if b.get("kind") != "illustration":
            continue
        bid = b.get("id", "?")
        el = b.get("elements")
        ce = b.get("child_elements")
        if el is None and ce is None:
            holes.append(bid)
            continue
        examined += 1
        counted = sum(int(e.get("count", 0)) for e in (el or []))
        # 1. zero interior: the defect this check exists for.
        if not counted and not ce:
            problems.append(f"{bid}: declared illustration with ZERO child elements")
            continue
        # 2. a declared total that does not match its own inventory. Caught three
        #    hand-typed counts on the university storyboard (38 as 41, 184 as 159,
        #    31 as 30) - every error made an interior look differently populated
        #    than it was, which is the direction these defects lean.
        if el is not None and ce is not None and counted != int(ce):
            problems.append(f"{bid}: child_elements {ce} != sum of its own "
                            f"element counts {counted}")
        # 3. outline only: boundaries and labels are not an interior.
        if el:
            interior = [e for e in el
                        if not INERT_ELEMENT_KINDS.search(str(e.get("kind", "")))]
            if not interior:
                problems.append(f"{bid}: every declared child is a boundary or a "
                                f"label - no authored interior")
        # 4. GRAMMAR rule 7: the subject is on screen from the beat's own t=0.
        t0 = b.get("subject_at_t0")
        if t0 is None:
            holes.append(f"{bid}(no subject_at_t0)")
        elif not t0:
            problems.append(f"{bid}: empty subject_at_t0 - the beat opens on a bare "
                            f"stage (GRAMMAR rule 7)")
    figures = {"interiors_examined": examined,
               "interiors_unmeasured": holes,
               "interior_problems": problems}
    return problems, holes, figures


def eval_storyboard(sb, floors):
    """Pure evaluation so it can be run on planted controls. Returns
    (ok, detail, figures). Floors: illustration-share-floor (concept 0.60),
    type-run-ceiling (3.0s)."""
    beats = [b for b in sb.get("beats", []) if b.get("dur")]
    ftype = (sb.get("film_type") or "unknown").lower()
    total = sum(float(b["dur"]) for b in beats) or 1.0
    illus = sum(float(b["dur"]) for b in beats if b.get("kind") == "illustration")
    share = illus / total
    # Longest run of consecutive type-only beats (type/card), in seconds.
    run = best = 0.0
    for b in sorted(beats, key=lambda x: float(x.get("start", 0))):
        if b.get("kind") in ("type", "card"):
            run += float(b["dur"])
            best = max(best, run)
        else:
            run = 0.0
    # A mechanism beat must be ILLUSTRATED on a concept film. On a HYBRID the
    # correct treatment for a mechanism beat is often real footage - that is what
    # makes it a hybrid - so a `plate` is permitted and only type/card fail.
    # Before 9 Oct 2026 this assertion had no hybrid branch, so a hybrid
    # storyboard declaring the truth about its own footage beats failed it, and
    # the only way to a green gate was to mis-declare `mechanism: false`.
    mech_ok = ("illustration", "plate") if ftype == "hybrid" else ("illustration",)
    mech_bad = [b.get("id", "?") for b in beats
                if b.get("mechanism") and b.get("kind") not in mech_ok]
    declared_share_floor = "illustration-share-floor" in floors
    share_floor = floors.get("illustration-share-floor",
                             0.60 if ftype == "concept" else 0.0)
    type_ceiling = floors.get("type-run-ceiling", 3.0)
    problems = []
    # Assert the share whenever a floor is DECLARED, whatever the film type. It
    # was previously asserted only for film_type == "concept", so a hybrid film's
    # share was reported and never held to anything - which is exactly the hole on
    # a film whose illustrated halves are the risk.
    if (ftype == "concept" or declared_share_floor) and share < share_floor:
        problems.append(f"illustration-led share {share:.2f} < floor {share_floor:.2f}")
    if best > type_ceiling:
        problems.append(f"longest type-only run {best:.1f}s > ceiling {type_ceiling:.1f}s")
    if mech_bad:
        problems.append(f"mechanism beat(s) not illustration-led: {mech_bad}")
    int_problems, int_holes, int_figures = eval_interiors(beats)
    figures = {"film_type": ftype, "beats": len(beats),
               "illustration_share": round(share, 3),
               "illustration_share_floor": share_floor,
               "illustration_share_floor_declared": declared_share_floor,
               "longest_type_run_s": round(best, 2),
               "mechanism_kinds_allowed": list(mech_ok),
               "mechanism_not_illustrated": mech_bad}
    figures.update(int_figures)
    detail = (f"{ftype} film, {len(beats)} beats; illustration-led {share * 100:.0f}% "
              f"of {total:.1f}s (floor {share_floor * 100:.0f}%"
              + ("" if declared_share_floor else ", default") + "); longest type-only run "
              f"{best:.1f}s (ceiling {type_ceiling:.1f}s); interiors measured on "
              f"{int_figures['interiors_examined']} of "
              f"{sum(1 for b in beats if b.get('kind') == 'illustration')} "
              f"illustration beat(s)"
              + (f", UNMEASURED {int_holes}" if int_holes else "") + "; "
              + ("; ".join(problems) if problems else "all mechanism beats illustrated"))
    figures["interior_verdict"] = eval_interior_verdict(beats, int_problems, int_holes)
    return (not problems), detail, figures


def eval_interior_verdict(beats, int_problems, int_holes):
    """FAIL / HOLE / PASS for the static interior check alone. It gets its own
    verdict because 'interiors examined on 0 of 18 illustration beats' folded into
    a PASS reads as green, and zero of eighteen is further from a pass than zero of
    zero. Both concept films in flight on 9 Oct 2026 are exactly that case."""
    pop = sum(1 for b in beats if b.get("kind") == "illustration")
    examined = pop - len([h for h in int_holes if "(" not in h])
    if int_problems:
        return ("FAIL", "; ".join(int_problems))
    if pop and examined <= 0:
        return ("HOLE", f"no element inventory on any of {pop} illustration beat(s), "
                        f"so whether any of them has an authored interior was NOT "
                        f"measured. Not a pass. Add `elements` / `child_elements` / "
                        f"`subject_at_t0` per beat (see videos/university/STORYBOARD.json)")
    if not pop:
        return ("HOLE", "no illustration beats to examine")
    return ("PASS", f"interiors authored and self-consistent on {examined} of {pop} "
                    f"illustration beat(s)"
                    + (f"; UNMEASURED {int_holes}" if int_holes else ""))


def check_storyboard(path, dur, d, floors):
    c = new_check("storyboard.illustrated")
    if not path:
        hole(c, "no --storyboard supplied: whether the IDEA is shown (concept-film "
                "rule 0c) was not measured. Not a pass.")
        return
    # Positive control: a 5s type-only run and a 40% illustration share must FAIL.
    bad = {"film_type": "concept", "beats": [
        {"id": "a", "start": 0, "dur": 4, "kind": "illustration", "mechanism": True},
        {"id": "b", "start": 4, "dur": 3, "kind": "type"},
        {"id": "c", "start": 7, "dur": 2, "kind": "card"},
        {"id": "d", "start": 9, "dur": 1, "kind": "plate", "mechanism": True}]}
    ok_b, det_b, _ = eval_storyboard(bad, {})
    control(c, "evaluator FAILS a planted 5s type run / 40% share / typeset mechanism",
            not ok_b and "5.0s" in det_b and "mechanism" in det_b, det_b[:90])
    # Negative control: a compliant concept storyboard must PASS.
    good = {"film_type": "concept", "beats": [
        {"id": "a", "start": 0, "dur": 7, "kind": "illustration", "mechanism": True},
        {"id": "b", "start": 7, "dur": 2, "kind": "type"},
        {"id": "c", "start": 9, "dur": 6, "kind": "illustration", "mechanism": True}]}
    ok_g, det_g, fig_g = eval_storyboard(good, {})
    control(c, "evaluator PASSES a compliant storyboard", ok_g, det_g[:90])
    # Backward compatibility is a CONTROL, not an assumption: a storyboard with no
    # element inventory (every one authored before 4 Oct 2026) must report its
    # interiors UNMEASURED and still pass, never fail for want of the schema.
    control(c, "a storyboard with no element inventory reports interiors UNMEASURED, "
               "not FAILED",
            ok_g and fig_g["interiors_examined"] == 0 and fig_g["interiors_unmeasured"],
            f"examined {fig_g['interiors_examined']}, "
            f"unmeasured {fig_g['interiors_unmeasured']}")
    # --- hybrid controls (mechanism branch and declared share floor) ---
    hyb = {"film_type": "hybrid", "beats": [
        {"id": "a", "start": 0, "dur": 4, "kind": "illustration", "mechanism": True},
        {"id": "b", "start": 4, "dur": 6, "kind": "plate", "mechanism": True}]}
    ok, det, _ = eval_storyboard(hyb, {"illustration-share-floor": 0.35})
    control(c, "hybrid: a mechanism beat carried by a live PLATE passes", ok, det[-80:])
    ok, det, _ = eval_storyboard(hyb, {"illustration-share-floor": 0.60})
    control(c, "hybrid: a DECLARED share floor is asserted (it was previously read "
               "and never applied off a concept film)",
            not ok and "share 0.40" in det, det[-90:])
    hyb_t = {"film_type": "hybrid", "beats": [
        {"id": "a", "start": 0, "dur": 6, "kind": "illustration", "mechanism": True},
        {"id": "b", "start": 6, "dur": 2, "kind": "type", "mechanism": True}]}
    ok, det, _ = eval_storyboard(hyb_t, {})
    control(c, "hybrid: a TYPESET mechanism beat still fails",
            not ok and "mechanism" in det, det[-80:])
    try:
        sb = json.loads(Path(path).read_text())
    except Exception as e:
        verdict(c, False, f"could not read {path}: {e}")
        return
    ok, detail, figures = eval_storyboard(sb, floors)
    for k, v in figures.items():
        fig(c, k, v)
    # Cross-check: a beat DECLARED illustration must also MOVE. The label is a
    # claim; the frames are the fact (motion floor shared with motion.per_shot).
    fps = 10
    floor = floors.get("shot-median-floor", 0.05)
    still_illus = []
    if d is not None:
        for b in sb.get("beats", []):
            if b.get("kind") != "illustration" or not b.get("dur"):
                continue
            i0 = max(0, int(float(b.get("start", 0)) * fps))
            i1 = min(len(d), int((float(b.get("start", 0)) + float(b["dur"])) * fps))
            if i1 - i0 < 2:
                continue
            med = float(np.median(d[i0:i1]))
            if med < floor:
                still_illus.append(f"{b.get('id', '?')} median {med:.3f}")
        fig(c, "declared_illustration_but_still", still_illus)
        if still_illus:
            detail += f"; declared-illustration beats measuring still: {still_illus}"
    else:
        detail += "; motion cross-check NOT run (no per-frame motion available)"
    verdict(c, ok and not still_illus, detail)

    ci = new_check("storyboard.interiors")

    def _iv(**beat):
        b = dict({"id": "z", "kind": "illustration", "dur": 3}, **beat)
        probs, holes, _ = eval_interiors([b])
        return eval_interior_verdict([b], probs, holes)

    POP = {"elements": [{"kind": "tile", "count": 9}], "child_elements": 9,
           "subject_at_t0": ["tile"]}
    # NEGATIVE control first: the shape that must stay quiet.
    v = _iv(**POP)
    control(ci, "a populated, self-consistent beat PASSES (negative control)",
            v[0] == "PASS", v[1][:90])
    # POSITIVE controls: each must FIRE, and each plant must differ from POP.
    v = _iv(elements=[], child_elements=0, subject_at_t0=["a"])
    control(ci, "a declared illustration beat with ZERO child elements FAILS",
            v[0] == "FAIL" and "ZERO child elements" in v[1], v[1][:90])
    v = _iv(elements=[{"kind": "boundary", "count": 1},
                      {"kind": "ruled label", "count": 6}],
            child_elements=7, subject_at_t0=["boundary"])
    control(ci, "a beat whose only children are a boundary and labels FAILS - the "
                "nearest legitimate look-alike to a populated beat",
            v[0] == "FAIL" and "no authored interior" in v[1], v[1][:90])
    v = _iv(elements=[{"kind": "tile", "count": 4}], child_elements=9,
            subject_at_t0=["tile"])
    control(ci, "a child_elements total contradicting its own inventory FAILS",
            v[0] == "FAIL" and "!= sum" in v[1], v[1][:90])
    v = _iv(elements=[{"kind": "tile", "count": 9}], child_elements=9,
            subject_at_t0=[])
    control(ci, "an empty subject_at_t0 FAILS (GRAMMAR rule 7)",
            v[0] == "FAIL" and "bare stage" in v[1], v[1][:90])
    # HOLE control: no inventory at all is unmeasured, never a pass and never a FAIL.
    v = _iv()
    control(ci, "a beat with no inventory at all is a HOLE, not a pass and not a FAIL",
            v[0] == "HOLE" and "NOT" in v[1], v[1][:90])
    iv = figures.get("interior_verdict")
    for k in ("interiors_examined", "interiors_unmeasured", "interior_problems"):
        if k in figures:
            fig(ci, k, figures[k])
    if not iv:
        hole(ci, "interior verdict not produced")
    elif iv[0] == "HOLE":
        hole(ci, iv[1])
    else:
        verdict(ci, iv[0] == "PASS", iv[1])


def main():
    global STAMP
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("master", nargs="?")
    ap.add_argument("--design")
    ap.add_argument("--segments")
    ap.add_argument("--storyboard", help="STORYBOARD.json with per-beat kind "
                    "(illustration|plate|type|card) - the concept-film check (skill 0c)")
    ap.add_argument("--storyboard-only", action="store_true",
                    help="Run ONLY the storyboard checks (illustration share, type-only "
                         "run, mechanism kind, and the static interior check) with no "
                         "master file. This is how a storyboard is failed BEFORE anything "
                         "is rendered, which is the whole point of the interior check.")
    ap.add_argument("--reference-strings")
    ap.add_argument("--social", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--work", help="work dir (default: a temp dir)")
    a = ap.parse_args()

    if a.storyboard_only:
        if not a.storyboard:
            print("--storyboard-only needs --storyboard")
            return 2
        sbp = Path(a.storyboard)
        if not sbp.exists():
            print(f"{sbp} does not exist - nothing to gate")
            return 2
        sb_md5 = hashlib.md5(sbp.read_bytes()).hexdigest()
        STAMP = f"storyboard md5 {sb_md5[:12]} / no master"
        print(f"VIDEO GATE  {sbp.name}  (storyboard only, pre-render)")
        print(f"  (every figure below is a claim about THIS file: {STAMP})\n")
        floors, unreadable = ({}, {})
        if a.design:
            floors, unreadable = parse_design(a.design)[1:]
        check_design_floors(a.design, floors, unreadable)
        # d=None: the motion cross-check cannot run with no master and says so.
        check_storyboard(a.storyboard, None, None, floors)
        fails = [c for c in CHECKS if c["status"] == "FAIL"]
        holes = [c for c in CHECKS if c["status"] == "HOLE"]
        passes = [c for c in CHECKS if c["status"] == "PASS"]
        print(f"\n{len(passes)} PASS, {len(fails)} FAIL, {len(holes)} HOLE "
              f"(a HOLE is unmeasured, never a pass)")
        for c in fails + holes:
            print(f"  {c['status']} {c['name']}: {c['detail'][:400]}")
        if CONTROL_FAILS:
            print(f"\nCONTROL FAILURES (the instrument is unproven): {CONTROL_FAILS}")
        Path(a.out).write_text(json.dumps(
            {"file": str(sbp), "md5": sb_md5, "stamp": STAMP,
             "storyboard_only": True,
             "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
             "args": {"design": a.design},
             "checks": CHECKS,
             "summary": {"pass": len(passes), "fail": len(fails),
                         "hole": len(holes), "control_failures": CONTROL_FAILS}},
            indent=2, ensure_ascii=False))
        print(f"\nreport written to {a.out}")
        if CONTROL_FAILS:
            return 2
        if fails:
            return 1
        if not passes:
            print("ZERO checks produced a PASS verdict - zero of zero is not a pass")
            return 1
        return 0

    if not a.master:
        ap.error("master is required unless --storyboard-only is given")
    master = Path(a.master)
    if not master.exists():
        print(f"{master} does not exist - nothing to gate")
        return 2
    work = Path(a.work) if a.work else Path(tempfile.mkdtemp(prefix="video_gate_"))
    work.mkdir(parents=True, exist_ok=True)

    b = master.read_bytes()
    md5 = hashlib.md5(b).hexdigest()
    dur = duration_of(master)
    STAMP = f"md5 {md5[:12]} / {dur:.3f}s / {len(b):,}B"
    print(f"VIDEO GATE  {master.name}")
    print(f"  md5 {md5}   {dur:.3f}s   {len(b):,} bytes")
    print(f"  (every figure below is a claim about THIS file: {STAMP})\n")

    forbidden, floors = ([], {})
    if a.design:
        forbidden, floors, unreadable = parse_design(a.design)
        # Union the baseline HERE rather than inside parse_design: that function's
        # return value is what three of this gate's own controls assert on, and it must
        # keep meaning "what the DESIGN.md declares".
        declared = len(forbidden)
        forbidden = list(dict.fromkeys(BASELINE_FORBIDDEN + forbidden))
        print(f"  forbidden strings: {declared} declared + "
              f"{len(forbidden) - declared} inherited from the shared baseline "
              f"= {len(forbidden)}\n")
        check_design_floors(a.design, floors, unreadable)
    timing, crops = ([], [])
    if a.segments:
        timing, crops = load_segments(a.segments)
        print(f"  segments: {len(timing)} timed shot(s), {len(crops)} crop "
              f"window(s) from {a.segments}\n")

    check_identity(master, dur, timing)
    check_audio(master, dur, floors, work)
    motion_d = check_motion(master, dur, timing, floors, work)
    check_storyboard(a.storyboard, dur, motion_d, floors)
    check_grey_and_type(master, dur, floors, a.social, bool(a.design), work)
    check_ocr_sweep(master, dur, forbidden, floors, work)
    check_crop_edges(crops, work)
    if a.reference_strings:
        check_reference_echo(a.reference_strings, timing)
    else:
        hole(new_check("reference.echo"),
             "no --reference-strings supplied, so no echo diff ran. Not a pass.")

    # ------------------------------------------------------------- summary
    fails = [c for c in CHECKS if c["status"] == "FAIL"]
    holes = [c for c in CHECKS if c["status"] == "HOLE"]
    passes = [c for c in CHECKS if c["status"] == "PASS"]
    print("\n" + "=" * 72)
    print(f"SUMMARY   {master.name}   [{STAMP}]")
    for c in CHECKS:
        key = next(iter(c["figures"].items()), ("", ""))
        print(f"  {c['status']:4s}  {c['name']:28s} "
              f"{key[0]}={key[1]}" if key[0] else f"  {c['status']:4s}  {c['name']}")
    print(f"\n{len(passes)} PASS, {len(fails)} FAIL, {len(holes)} HOLE "
          f"(a HOLE is unmeasured, never a pass)")
    for c in fails:
        print(f"  FAIL {c['name']}: {c['detail'][:140]}")
    for c in holes:
        print(f"  HOLE {c['name']}: {c['detail'][:120]}")
    if CONTROL_FAILS:
        print(f"\nCONTROL FAILURES (the instrument is unproven - no verdict "
              f"above is worth anything): {CONTROL_FAILS}")

    report = {
        "file": str(master), "md5": md5, "bytes": len(b),
        "duration_s": round(dur, 3), "stamp": STAMP,
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "args": {"design": a.design, "segments": a.segments,
                 "reference_strings": a.reference_strings, "social": a.social},
        "checks": CHECKS,
        "summary": {"pass": len(passes), "fail": len(fails),
                    "hole": len(holes), "control_failures": CONTROL_FAILS},
    }
    Path(a.out).write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nreport written to {a.out}")

    if CONTROL_FAILS:
        return 2
    if fails:
        return 1
    if not passes:
        # Never exit 0 having measured nothing.
        print("ZERO checks produced a PASS verdict - zero of zero is not a pass")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
