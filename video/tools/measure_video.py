#!/usr/bin/env python3
"""Measure a video the way this factory measures its own films.

Instruments, each proven on a planted control BEFORE any real file is trusted:
  1. shot boundaries + shot lengths   (per-frame mean-abs-diff at 480x270, 0-255 units)
  2. per-shot MEDIAN per-frame motion (same decode, 0-255 grey levels)
  3. audio presence / silence gaps    (ffmpeg -loglevel info, silencedetect)
  4. narration words per minute       (from the VTT caption track)

Usage: measure_video.py --selftest
       measure_video.py <file.mp4> [<file.mp4> ...]
"""
import json, os, re, subprocess, sys, tempfile
import numpy as np

W, H = 480, 270
SHOT_THRESHOLD = 12.0     # 0-255 mean-abs-diff; a cut is a large single-frame jump
MIN_SHOT_FRAMES = 8

def ffprobe(path):
    r = subprocess.run(["ffprobe","-v","error","-show_entries",
        "format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate,channels,sample_rate",
        "-of","json",path],capture_output=True,text=True)
    return json.loads(r.stdout)

def grey_frames(path, w=W, h=H):
    """Decode the whole file to raw grey at w x h. Returns (n, h, w) uint8."""
    cmd = ["ffmpeg","-v","error","-i",path,"-vf",f"scale={w}:{h}","-pix_fmt","gray",
           "-f","rawvideo","-"]
    p = subprocess.run(cmd, capture_output=True)
    buf = np.frombuffer(p.stdout, dtype=np.uint8)
    n = len(buf)//(w*h)
    return buf[:n*w*h].reshape(n,h,w)

def frame_diffs(frames):
    """Mean absolute difference between consecutive frames, in 0-255 grey levels."""
    a = frames.astype(np.int16)
    return np.abs(a[1:]-a[:-1]).mean(axis=(1,2))   # length n-1

def shots(diffs, fps, thr=SHOT_THRESHOLD, minf=MIN_SHOT_FRAMES):
    cuts = [0]
    for i,d in enumerate(diffs):
        if d >= thr and (i+1 - cuts[-1]) >= minf:
            cuts.append(i+1)
    cuts.append(len(diffs)+1)
    out=[]
    for a,b in zip(cuts[:-1],cuts[1:]):
        seg = diffs[a:max(a+1,b-1)]
        out.append({"start_s": round(a/fps,2), "end_s": round(b/fps,2),
                    "dur_s": round((b-a)/fps,2),
                    "median_motion_0_255": round(float(np.median(seg)),4) if len(seg) else 0.0,
                    "mean_motion_0_255": round(float(seg.mean()),4) if len(seg) else 0.0,
                    "frames": int(b-a)})
    return out

def audio_report(path):
    """silencedetect at INFO level - at -v error ffmpeg prints nothing and it reads clean."""
    r = subprocess.run(["ffmpeg","-hide_banner","-loglevel","info","-i",path,
        "-af","silencedetect=noise=-50dB:d=0.6,volumedetect","-f","null","-"],
        capture_output=True,text=True)
    log = r.stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.\-]+)", log)]
    ends   = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    durs   = [float(x) for x in re.findall(r"silence_duration: ([\d.]+)", log)]
    mean   = re.search(r"mean_volume: ([\-\d.]+) dB", log)
    mx     = re.search(r"max_volume: ([\-\d.]+) dB", log)
    return {"silence_gaps": len(durs), "longest_silence_s": round(max(durs),2) if durs else 0.0,
            "silence_total_s": round(sum(durs),2),
            "mean_volume_dB": float(mean.group(1)) if mean else None,
            "max_volume_dB": float(mx.group(1)) if mx else None,
            "log_had_output": bool(mean or starts)}

def vtt_wpm(vtt, duration):
    if not os.path.exists(vtt): return None
    txt = open(vtt, encoding="utf-8", errors="replace").read()
    body = [l for l in txt.splitlines()
            if l.strip() and "-->" not in l and not l.strip().isdigit()
            and not l.startswith(("WEBVTT","NOTE","STYLE","Kind:","Language:"))]
    words = " ".join(body).split()
    # speaking time = sum of cue durations, not wall clock
    cues = re.findall(r"(\d+):(\d+):([\d.]+)\s*-->\s*(\d+):(\d+):([\d.]+)", txt)
    def s(h,m,sec): return int(h)*3600+int(m)*60+float(sec)
    speak = sum(s(*c[3:6])-s(*c[0:3]) for c in cues)
    return {"words": len(words), "cues": len(cues),
            "speaking_s": round(speak,2),
            "wpm_over_duration": round(len(words)/(duration/60),1) if duration else None,
            "wpm_over_speaking": round(len(words)/(speak/60),1) if speak else None}

def measure(path):
    pr = ffprobe(path)
    vs = next((s for s in pr["streams"] if s["codec_type"]=="video"), {})
    a_s = next((s for s in pr["streams"] if s["codec_type"]=="audio"), None)
    num,den = (vs.get("r_frame_rate","30/1").split("/")+["1"])[:2]
    fps = float(num)/float(den or 1)
    dur = float(pr["format"]["duration"])
    fr = grey_frames(path)
    diffs = frame_diffs(fr)
    sh = shots(diffs, fps)
    rec = {
      "file": os.path.basename(path),
      "duration_s": round(dur,2), "fps": round(fps,3),
      "resolution": f"{vs.get('width')}x{vs.get('height')}",
      "bytes": int(pr["format"]["size"]),
      "frames_decoded": int(len(fr)), "diff_samples": int(len(diffs)),
      "audio": {"present": a_s is not None, "codec": a_s and a_s.get("codec_name"),
                "channels": a_s and a_s.get("channels"), "rate": a_s and a_s.get("sample_rate")},
      "shot_count": len(sh),
      "shot_len_median_s": round(float(np.median([s["dur_s"] for s in sh])),2),
      "shot_len_min_s": round(min(s["dur_s"] for s in sh),2),
      "shot_len_max_s": round(max(s["dur_s"] for s in sh),2),
      "whole_film_median_motion_0_255": round(float(np.median(diffs)),4),
      "pct_frames_identical": round(float((diffs==0).mean()*100),2),
      "distinct_frames_pct": round(float((diffs>0).mean()*100),2),
      "stillest_shot": min(sh, key=lambda s: s["median_motion_0_255"]),
      "liveliest_shot": max(sh, key=lambda s: s["median_motion_0_255"]),
      "shots": sh,
    }
    rec["audio"].update(audio_report(path))
    vtt = os.path.splitext(path)[0]+".vtt"
    rec["narration"] = vtt_wpm(vtt, dur)
    return rec

# ---------------- selftests: prove each instrument can produce the answer I don't want
def selftest():
    td = tempfile.mkdtemp()
    ok = True
    # (a) planted FREEZE: a single still held 6s, with a tone
    still = os.path.join(td,"still.png")
    subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i","color=c=navy:s=1920x1080",
                    "-frames:v","1",still],check=True)
    frozen = os.path.join(td,"frozen.mp4")
    subprocess.run(["ffmpeg","-v","error","-y","-loop","1","-i",still,"-f","lavfi",
                    "-i","sine=f=440:d=6","-t","6","-r","30","-pix_fmt","yuv420p",
                    "-c:v","libx264","-c:a","aac","-shortest",frozen],check=True)
    f = measure(frozen)
    a = f["whole_film_median_motion_0_255"] < 0.01 and f["shot_count"] == 1 and f["pct_frames_identical"] > 90
    print(f"  [a] planted FREEZE -> shots={f['shot_count']} medianMotion={f['whole_film_median_motion_0_255']} "
          f"identical={f['pct_frames_identical']}%  {'PASS' if a else 'FAIL'}")
    ok &= a
    # (b) planted CUTS: four 2s solid GREYS = 3 hard cuts.
    # Named colours are the wrong control here: red/green/blue collapse to only two
    # distinct luma levels once decoded to grey, so the clip carries one visual cut,
    # not two, and the detector was right. MEASURE THE CONTROL before trusting it.
    cuts = os.path.join(td,"cuts.mp4")
    subprocess.run(["ffmpeg","-v","error","-y",
        "-f","lavfi","-i","color=c=0x000000:s=640x360:d=2","-f","lavfi","-i","color=c=0x555555:s=640x360:d=2",
        "-f","lavfi","-i","color=c=0xAAAAAA:s=640x360:d=2","-f","lavfi","-i","color=c=0xFFFFFF:s=640x360:d=2",
        "-filter_complex","[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0[v]","-map","[v]","-r","30",
        "-pix_fmt","yuv420p","-c:v","libx264",cuts],check=True)
    ctrl_levels = np.unique(np.round(grey_frames(cuts).mean(axis=(1,2))/8).astype(int))
    c = measure(cuts)
    b = (len(ctrl_levels) == 4) and c["shot_count"] == 4
    print(f"  [b] planted 4 SHOTS (control carries {len(ctrl_levels)} distinct luma levels) "
          f"-> detected {c['shot_count']}  {'PASS' if b else 'FAIL'}")
    ok &= b
    # (b2) NEGATIVE control for the cut detector: a continuous slow pan must NOT
    # register as a cut, or every real camera move would be counted as a shot change.
    pan = os.path.join(td,"pan.mp4")
    subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi",
        "-i","testsrc=s=640x360:d=6:r=30","-vf","scale=1280:720,crop=640:360:'(iw-ow)*t/6':0",
        "-pix_fmt","yuv420p","-c:v","libx264",pan],check=True)
    pc = measure(pan)
    b2 = pc["shot_count"] == 1
    print(f"  [b2] NEGATIVE control, continuous pan -> shots={pc['shot_count']} "
          f"(must be 1) medianMotion={pc['whole_film_median_motion_0_255']}  {'PASS' if b2 else 'FAIL'}")
    ok &= b2
    # (c) planted SILENCE: 2s tone, 3s silence, 2s tone -> must find exactly 1 gap >=0.6s
    sil = os.path.join(td,"sil.mp4")
    subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i","color=c=gray:s=320x180:d=7",
        "-f","lavfi","-i","aevalsrc='sin(440*2*PI*t)*between(t,0,2)+sin(440*2*PI*t)*between(t,5,7)':d=7",
        "-r","30","-pix_fmt","yuv420p","-c:v","libx264","-c:a","aac","-shortest",sil],check=True)
    s = audio_report(sil)
    d = s["silence_gaps"] >= 1 and 2.0 <= s["longest_silence_s"] <= 3.6 and s["log_had_output"]
    print(f"  [c] planted 3s SILENCE -> gaps={s['silence_gaps']} longest={s['longest_silence_s']}s "
          f"logOutput={s['log_had_output']}  {'PASS' if d else 'FAIL'}")
    ok &= d
    # (c2) NEGATIVE control: continuous tone must report ZERO gaps (prove it stays quiet)
    cont = os.path.join(td,"cont.mp4")
    subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i","color=c=gray:s=320x180:d=5",
        "-f","lavfi","-i","sine=f=440:d=5","-r","30","-pix_fmt","yuv420p","-c:v","libx264",
        "-c:a","aac","-shortest",cont],check=True)
    s2 = audio_report(cont)
    e = s2["silence_gaps"] == 0 and s2["log_had_output"]
    print(f"  [c2] NEGATIVE control, continuous tone -> gaps={s2['silence_gaps']} "
          f"meanVol={s2['mean_volume_dB']}dB  {'PASS' if e else 'FAIL'}")
    ok &= e
    # (d) prove -v error DESTROYS the silence measurement (the documented trap)
    r = subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-i",sil,
        "-af","silencedetect=noise=-50dB:d=0.6,volumedetect","-f","null","-"],capture_output=True,text=True)
    f2 = "silence_start" not in r.stderr
    print(f"  [d] control: at -loglevel error the same file reports NO silence "
          f"(trap reproduced = {f2})  {'PASS' if f2 else 'FAIL'}")
    ok &= f2
    print(f"\n  SELFTEST {'PASS - instruments can produce the answer I do not want' if ok else 'FAIL'}")
    return ok

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 2)
    if not selftest():
        print("selftest failed; refusing to measure"); sys.exit(2)
    out=[]
    for p in sys.argv[1:]:
        print(f"\nmeasuring {os.path.basename(p)} ...")
        out.append(measure(p))
    dst="/Users/user/Claude/ARAG-PMK-1/content/audits/bt-quality-bar-evidence/data/video_measures.json"
    prev = json.load(open(dst)) if os.path.exists(dst) else []
    names={r["file"] for r in out}
    json.dump([r for r in prev if r["file"] not in names]+out, open(dst,"w"), indent=2)
    for r in out:
        n=r["narration"] or {}
        print(f"\n{r['file']}")
        print(f"  {r['duration_s']}s @{r['fps']}fps {r['resolution']}  shots={r['shot_count']} "
              f"median={r['shot_len_median_s']}s range {r['shot_len_min_s']}-{r['shot_len_max_s']}s")
        print(f"  motion median {r['whole_film_median_motion_0_255']} (0-255 @480x270), "
              f"identical frames {r['pct_frames_identical']}%")
        print(f"  stillest shot {r['stillest_shot']['start_s']}-{r['stillest_shot']['end_s']}s "
              f"median {r['stillest_shot']['median_motion_0_255']}; liveliest "
              f"{r['liveliest_shot']['median_motion_0_255']}")
        print(f"  audio {r['audio']['codec']} {r['audio']['channels']}ch mean {r['audio']['mean_volume_dB']}dB "
              f"gaps={r['audio']['silence_gaps']} longest={r['audio']['longest_silence_s']}s")
        if n: print(f"  narration {n['words']}w over {n['speaking_s']}s speaking = {n['wpm_over_speaking']} wpm "
                    f"({n['wpm_over_duration']} wpm over full duration), {n['cues']} cues")
