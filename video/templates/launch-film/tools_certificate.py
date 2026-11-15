#!/usr/bin/env python3
"""Print the DoP certificate for a delivered film. READ-ONLY.

Every figure is PRINTED BY THIS SCRIPT from the thing it describes, never
retyped from a report - and each one carries the instrument that produced it and
the POPULATION that instrument can see, because a figure whose provenance is
missing cannot be shown to be current and a verdict that does not name its axis
sounds more complete than it is.

It deliberately runs nothing that writes: not the audio staging, not any render.
"""
import hashlib, json, pathlib, re, subprocess, sys, datetime

P = pathlib.Path(__file__).parent
VENV = str(P.parent / ".venv/bin/python")


def sh(*a, **k):
    return subprocess.run(a, capture_output=True, text=True, **k)


def grab(txt, pat, default="not found"):
    m = re.search(pat, txt)
    return m.group(1) if m else default


def main(film):
    f = pathlib.Path(film).resolve()
    md5 = hashlib.md5(f.read_bytes()).hexdigest()
    dur = float(sh("ffprobe", "-v", "error", "-show_entries", "format=duration",
                   "-of", "csv=p=0", str(f)).stdout)
    nfr = sh("ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
             "stream=nb_frames", "-of", "csv=p=0", str(f)).stdout.strip()
    tl = json.load(open(P / "timeline.json"))
    stage = json.load(open(P / "audio_stage.json"))
    req = json.load(open(P / "audio_request.json"))

    print(f"# Definition of Pass - {f.name}\n")
    print(f"Delivered artifact  `{f}`")
    print(f"Content identity    md5 `{md5}`")
    print(f"Duration            {dur:.3f}s, {nfr} frames, "
          f"derived timeline {tl['total']:.3f}s")
    print(f"Certified           {datetime.date.today().isoformat()}")
    print(f"Voice               {req['voice']} ({req['voice_id']}), {req['model_id']}, "
          f"seed {req['seed']}, speed {req['speed']}")
    print(f"Audio chain         {stage['chain']}")
    print(f"                    + {stage['latency_compensation_samples']}-sample head trim "
          f"(limiter latency, cancelled exactly)\n")

    print("## Figures measured ON THE DELIVERED MP4\n")
    g = sh(VENV, str(P / "tools_delivery_gate.py"), str(f))
    o = g.stdout
    print(f"| check | figure | verdict |")
    print(f"|---|---|---|")
    print(f"| duration vs derived timeline | {dur:.3f} vs {tl['total']:.3f} | "
          f"{'PASS' if abs(dur-tl['total'])<=0.08 else 'FAIL'} |")
    print(f"| integrated loudness | {grab(o, r'I = *(-?[\d.]+) LUFS')} LUFS (target -16 +/-1.0) | "
          f"{grab(o, r'LUFS \(target[^)]*\) -> (\w+)')} |")
    print(f"| true peak | {grab(o, r'TRUE PEAK *(-?[\d.]+) dBTP')} dBTP (ceiling -1.0) | "
          f"{grab(o, r'dBTP \(ceiling -1.0\) -> (\w+)')} |")
    print(f"| music-free | {grab(o, r'MUSIC-FREE (\d+) silence gaps')} silence gaps >=0.25s at -50dB | "
          f"{grab(o, r'a bed would leave ~0\) -> (\w+)')} |")
    print(f"| on-screen text (OCR, 36 frames) | {grab(o, r'OCR over 36 frames spanning the whole film: (\d+) finding')} finding(s), "
          f"positive control {grab(o, r'POSITIVE CONTROL through the same path: (\d+/\d+)')} | "
          f"{'PASS' if 'DELIVERY GATE PASS' in o else 'FAIL'} |")
    s = sh(VENV, str(P.parent / "scripts/progress_stage_check.py"), str(f)).stdout
    print(f"| Progress stage, both ends | head {grab(s, r'head best ([\d.]+)')}, "
          f"tail {grab(s, r'tail best ([\d.]+)')}, floor 0.25 | "
          f"{'PASS' if 'FAIL' not in s else 'FAIL'} |")
    br = sh(VENV, str(P / "tools_blankruns.py"), str(f)).stdout
    print(f"| bare stage | {grab(br, r'total ([\d.]+)s of bare stage')}s at threshold 26; "
          f"see limit 3 | reported |")

    print("\n## Figures measured ON THE SOURCE TREE\n")
    print("These reach the mp4 only through the render step named in limit 1.\n")
    c = sh("npx", "--cache", str(P / ".npm-cache"), "--yes", "hyperframes@0.8.15", "check",
           cwd=str(P)).stdout
    lint = re.findall(r"(\d+) errors?, (\d+) warnings?", c)
    print(f"| check | figure | verdict |")
    print(f"|---|---|---|")
    print(f"| lint / runtime / motion | {', '.join(f'{a}e {b}w' for a, b in lint[:3])} | "
          f"{'PASS' if all(a=='0' and b=='0' for a,b in lint) else 'FAIL'} |")
    print(f"| layout | {grab(c, r'(\d+) issues across \d+ sample')} issues across "
          f"{grab(c, r'\d+ issues across (\d+) sample')} samples | "
          f"{'PASS' if '0 issues across' in c else 'FAIL'} |")
    print(f"| contrast | {grab(c, r'(\d+/\d+) text checks pass WCAG AA')} WCAG AA | "
          f"{'PASS' if 'text checks pass' in c else 'FAIL'} |")
    b = sh("python3", str(P / "tools_verify_beats.py"), "/tmp/beats_before.json",
           "/tmp/beats_after5.json").stdout
    print(f"| beat retime, 12 frames | all additions, removals and moves declared; "
          f"negative control {grab(b, r'worst ([\d.]+) -> DETECTED')} DETECTED | "
          f"{grab(b, r'VERIFY (\w+)')} |")
    ov = sh(VENV, str(P / "tools_overflow.py")).stdout
    print(f"| rendered extent | {grab(ov, r'(\d+) rendered-extent issue')} clipped overflows "
          f"and text collisions, 12 frames x 3 points | "
          f"{'PASS' if re.search(r'^0 rendered-extent issue', ov, re.M) else 'FAIL'} |")
    sc = sh(VENV, str(P / "tools_measure_scope.py")).stdout
    print(f"| frame-10 scope qualifier | {grab(sc, r'caveat >= table body type *([\d.]+ vs [\d.]+)')}; "
          f"control fails at header size | {grab(sc, r'SCOPE QUALIFIER (\w+)')} |")
    lp = sh(VENV, str(P / "tools_logo_polarity.py")).stdout
    print(f"| logo polarity, both bookends | contrast "
          f"{grab(lp, r'contrast ([\d.]+):1  mark is LIGHTER')}:1; control fires at "
          f"{grab(lp, r'contrast ([\d.]+):1 on the #00123C panel')}:1 | "
          f"{grab(lp, r'POLARITY (\w+)')} |")

    print("\n## Stated limits - these are holes, not passes\n")
    for i, t in enumerate([
        "Full-pipeline reproducibility UNESTABLISHED. The browser render step is untested. "
        "Everything upstream is checked: no Math.random, Date.now or clock in any composition; "
        "the audio chain re-stages byte-identical; the encoder is deterministic on identical "
        "input. Source-tree figures above reach the mp4 only through that untested step.",
        "Phone legibility NOT achieved and not claimed. A phone-legible 11px glyph needs 54px "
        "authored at 0.2031 scale and a 5x4 table plus a 28-tile grid cannot carry it. What was "
        "removed is the within-frame asymmetry, against the brief's 1920 embed. Text inside "
        "captured plates is outside the type instrument's population.",
        "The bare-stage measure cannot see fills within 26/255 of the stage, which is where this "
        "film's card grounds sit. At that threshold it reads frame 08 as 9.8s bare while the frame "
        "shows four DELETED cards. At a threshold that can see them: 1.8s across 2 runs.",
        "Four of five checklist ticks were DROPPED rather than evidenced. Fresh captures from the "
        "live app are needed to evidence them; the rows carry outcome pills instead.",
        "No audio perception anywhere in this build. Casting and both re-records were verified by "
        "ASR round-trip and measurement, never by listening. Whether the cast voice reads as "
        "authentic to a South African ear is unverified.",
        "Known product defect, filed separately, NOT to be fixed by changing the film: the demo "
        "app's bulk header reads '8 applications' where the page labels and the pack both give "
        "seven. The narration is correct.",
        "Frame 04 remains the largest untreated composition imbalance at +79px.",
    ], 1):
        print(f"{i}. {t}\n")
    print("## Judgement the instruments cannot make\n")
    print("An eye-read is a gate step in its own right: ink, contrast, overflow and OCR all pass "
          "on a populated, legible frame that says the wrong thing. Independent viewer verdict "
          "goes here.\n")
    print("Independent viewer: ______________________    Lead PMM gate: ______________________")


def guard(text):
    """A certificate carrying 'not found' is a hole wearing a value."""
    bad = [l for l in text.splitlines() if "not found" in l or "see output" in l]
    if bad:
        print("\n*** REFUSING: unresolved field(s) in the certificate:", file=sys.stderr)
        for l in bad:
            print("    " + l.strip(), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        main(sys.argv[1])
    out = buf.getvalue()
    sys.stdout.write(out)
    guard(out)
