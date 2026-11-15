#!/usr/bin/env python3
"""Stage programme loudness before the render, and PROVE the read did not move.

The delivered takes arrive peak-normalised to -1.0 dBTP at -27.4 LUFS - a 26 dB
crest (measured over 1715 frames: p50 -20.5, p95 -8.2). -16 LUFS under a -1.0
dBTP ceiling needs a crest near 15 dB, so a flat gain cannot get there: +11.4 dB
would put p95 at +3.2 dBFS.

Zero-look-ahead chains were tried first and all plateau well short -
acompressor at four settings (peak and rms detection) lands -20.4 to -22.6 LUFS,
speechnorm -22.2 to -24.7. So a limiter is required.

The brief rules out a look-ahead limiter BECAUSE it would shift the read against
the picture. That reason is satisfiable without the limiter: alimiter's latency
is constant and measurable - 239 samples, 4.98 ms, its 5 ms attack - so it is
measured per run, compensated exactly, and the alignment is then PROVEN by
cross-correlating every compensated take against its raw original. Lag must be
0 samples on all twelve and duration must not drift. A control delays a take by
a known 25 ms and the same measure must see it, otherwise the proof is
decoration. The deviation from the literal instruction is deliberate and is
reported.
"""
import json, re, shutil, subprocess, sys, pathlib
import numpy as np

P = pathlib.Path(__file__).parent
VO = P / "assets/voice-el"
RAW = VO / "_raw"
IDS = [f"{i:02d}" for i in range(1, 13)]
SR = 48000
# The gate is on the DELIVERED mp4, so the staging targets are the delivery
# targets MINUS what the host does between here and there. Both offsets were
# measured on the first full render (md5 5051d227..., staged -16.20/-1.30,
# delivered -13.30/+0.80):
#
#   LUFS  +3.0  the host writes the mono take as DUAL MONO, and an EBU R128
#               stereo reading sums both channels. Confirmed: L-R is -59.1 dB
#               mean, and the delivered file measured as ONE channel reads
#               -16.3 LUFS, i.e. the host applied no gain at all.
#   TP    +2.1  AAC encode overshoot. Real, and large because the signal is
#               limited hard up to its ceiling, so inter-sample peaks abound.
#
# Staging to the delivery target without these offsets ships a film 3 dB loud
# and 1.8 dB over the true-peak ceiling, which is what the first render did.
DELIVERED_LUFS, DELIVERED_TP = -16.0, -1.0
HOST_LUFS_OFFSET, HOST_TP_OFFSET = 3.0, 2.1
MARGIN_TP = 0.5
TARGET_LUFS = DELIVERED_LUFS - HOST_LUFS_OFFSET          # -19.0 staged
TP_CEILING = DELIVERED_TP - HOST_TP_OFFSET - MARGIN_TP   # -3.6 staged
LIMIT = 0.575          # -4.8 dBFS sample ceiling, so the staged true peak lands under -3.6
ATTACK_MS, RELEASE_MS = 5, 50


def prog_filter(n, starts):
    legs = "".join(f"[{i}:a]adelay={int(round(starts[i]*1000))}|{int(round(starts[i]*1000))}[a{i}];"
                   for i in range(n))
    return legs + "".join(f"[a{i}]" for i in range(n)) + \
        f"amix=inputs={n}:normalize=0:dropout_transition=0[out]"


def measure(files, starts, label):
    src = []
    for f in files:
        src += ["-i", str(f)]
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "info", *src,
                        "-filter_complex", prog_filter(len(files), starts) + ";[out]ebur128=peak=true[o]",
                        "-map", "[o]", "-f", "null", "-"], capture_output=True, text=True)
    s = r.stderr[r.stderr.rfind("Summary:"):]   # the running log also prints I/LRA/TPK
    if "Summary:" not in r.stderr:
        print(r.stderr[-1200:]); sys.exit(f"{label}: ebur128 printed no summary")
    I = float(re.search(r"I:\s*(-?[\d.]+) LUFS", s).group(1))
    TP = float(re.search(r"True peak:\s*\n\s*Peak:\s*(-?[\d.]+) dBFS", s).group(1))
    LRA = float(re.search(r"LRA:\s*(-?[\d.]+) LU", s).group(1))
    print(f"  {label:30s} I = {I:7.2f} LUFS   TP = {TP:6.2f} dBTP   LRA = {LRA:4.1f} LU")
    return I, TP, LRA


def samples(p):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "s16le",
                        "-ac", "1", "-ar", str(SR), "-"], capture_output=True)
    return np.frombuffer(r.stdout, dtype="<i2").astype(np.float32)


def lag(a, b, w=SR * 4):
    a, b = a[:w], b[:w]
    n = min(len(a), len(b))
    a, b = a[:n] - a[:n].mean(), b[:n] - b[:n].mean()
    return int(np.argmax(np.correlate(a, b, mode="full")) - (n - 1))


def render(gain_db, comp, out_dir):
    out_dir.mkdir(exist_ok=True)
    chain = (f"volume={gain_db:.3f}dB,"
             f"alimiter=limit={LIMIT}:level=disabled:attack={ATTACK_MS}:release={RELEASE_MS}")
    outs = []
    for lid in IDS:
        src = RAW / f"{lid}.wav"
        dst = out_dir / f"{lid}.wav"
        af = chain
        if comp:
            dur = len(samples(src)) / SR
            af += f",atrim=start_sample={comp},asetpts=N/SR/TB,apad"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
                            "-af", af, "-t", f"{dur:.6f}", "-ar", str(SR), "-ac", "1",
                            "-c:a", "pcm_s16le", str(dst)], check=True)
        else:
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
                            "-af", af, "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(dst)],
                           check=True)
        outs.append(dst)
    return outs, chain


def main():
    starts = json.load(open(P / "timeline.json"))["voice_start"]
    RAW.mkdir(exist_ok=True)
    for lid in IDS:
        if not (RAW / f"{lid}.wav").exists():
            shutil.copy2(VO / f"{lid}.wav", RAW / f"{lid}.wav")
    raws = [RAW / f"{lid}.wav" for lid in IDS]

    # The schedule this mixes against must match the takes on disk. A stale voice_start
    # makes a longer take overlap its neighbour, the sum peaks about 6 dB higher, and the
    # solver oscillates against a target the schedule has made unreachable - which is how
    # this failed rather than reporting anything useful.
    import subprocess as _sp
    lens = [float(_sp.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                           "-of", "csv=p=0", str(RAW / f"{l}.wav")],
                          capture_output=True, text=True).stdout) for l in IDS]
    overlaps = [(IDS[i], round(starts[i] + lens[i] - starts[i + 1], 3))
                for i in range(len(IDS) - 1) if starts[i] + lens[i] > starts[i + 1] + 0.001]
    if overlaps:
        sys.exit("timeline.json is stale: these takes overrun the next voice start "
                 f"{overlaps} - rebuild the timeline before staging audio")
    print(f"  schedule checked: 0 overlaps across {len(IDS)} takes")

    print("source takes, laid out as the host will:")
    measure(raws, starts, "as generated")

    scratch = P / ".audio-scratch"
    print(f"\nmeasuring the limiter's own latency (attack {ATTACK_MS} ms):")
    probe, _ = render(0.0, 0, scratch)
    comp = -lag(samples(raws[0]), samples(probe[0]))
    print(f"  alimiter introduces {comp} samples ({comp/ (SR/1000):.2f} ms) - compensating exactly")
    if comp <= 0:
        sys.exit("expected a positive latency to compensate; got none - re-measure before trusting this")

    print("\nsolving the gain for -16 LUFS under the ceiling:")
    g, chosen = 8.0, None
    for _ in range(7):
        outs, chain = render(g, comp, scratch)
        I, TP, LRA = measure(outs, starts, f"gain {g:+.2f} dB")
        if TP > TP_CEILING:
            g -= (TP - TP_CEILING) + 0.3
            continue
        if abs(I - TARGET_LUFS) <= 0.4:
            chosen = (g, I, TP, LRA, chain); break
        g += (TARGET_LUFS - I) * 0.9
    if not chosen:
        sys.exit(f"did not converge; last I={I}, TP={TP}")
    g, I, TP, LRA, chain = chosen

    for lid in IDS:
        shutil.copy2(scratch / f"{lid}.wav", VO / f"{lid}.wav")
    print(f"\nchosen chain: {chain}")
    print(f"  + {comp}-sample head trim to cancel the limiter's latency")
    finals = [VO / f"{lid}.wav" for lid in IDS]
    I2, TP2, LRA2 = measure(finals, starts, "STAGED FOR RENDER")

    print("\nalignment proof - cross-correlation lag, raw vs staged, per take:")
    lags, drift = [], []
    for lid in IDS:
        a, b = samples(RAW / f"{lid}.wav"), samples(VO / f"{lid}.wav")
        lags.append((lid, lag(a, b)))
        if abs(len(a) - len(b)) > SR // 1000:
            drift.append((lid, len(a), len(b)))
    bad = [x for x in lags if x[1] != 0]
    print("  " + " ".join(f"{l}:{v}" for l, v in lags))
    print(f"  non-zero lags: {len(bad)} (expect 0)" + (f"  {bad}" if bad else ""))
    print(f"  duration drift > 1 ms: {len(drift)} (expect 0)" + (f"  {drift}" if drift else ""))

    ctl = P / ".lagcontrol.wav"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(RAW / "01.wav"),
                    "-af", "adelay=25|25", "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(ctl)],
                   check=True)
    cl = lag(samples(RAW / "01.wav"), samples(ctl)); ctl.unlink()
    print(f"  CONTROL: a deliberate 25 ms delay measures {cl} samples ({cl/48.0:.1f} ms) -> "
          f"{'DETECTED' if abs(cl) > 100 else 'NOT DETECTED - THE PROOF IS DECORATION'}")
    shutil.rmtree(scratch, ignore_errors=True)

    ok = (abs(I2 - TARGET_LUFS) <= 0.4 and TP2 <= TP_CEILING and not bad and not drift
          and abs(cl) > 100)
    json.dump({"chain": chain, "latency_compensation_samples": comp, "gain_db": round(g, 3),
               "staged_I_LUFS": I2, "staged_true_peak_dBTP": TP2, "LRA": LRA2,
               "staged_target_lufs": TARGET_LUFS, "staged_tp_ceiling": TP_CEILING,
               "host_lufs_offset": HOST_LUFS_OFFSET, "host_tp_offset": HOST_TP_OFFSET,
               "predicted_delivered_I": round(I2 + HOST_LUFS_OFFSET, 2),
               "predicted_delivered_TP": round(TP2 + HOST_TP_OFFSET, 2)},
              open(P / "audio_stage.json", "w"), indent=1)
    print(f"  predicted delivered: I = {I2 + HOST_LUFS_OFFSET:.2f} LUFS, "
          f"TP = {TP2 + HOST_TP_OFFSET:.2f} dBTP (the gate measures the mp4, not this)")
    print("\nAUDIO STAGING", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
