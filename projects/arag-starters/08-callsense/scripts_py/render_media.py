"""
ElevenLabs voice-cast media renderer for the call-analysis demo corpus.
Replaces the original macOS `say` (Samantha/Alex) placeholder pipeline
(scripts/lib/media.ts) with real ElevenLabs per-character voices, per-line
RMS/loudness normalisation (so agent/member turns sit at one consistent
level within each call - the ElevenLabs per-render level trap), and
explicit STEREO output on every render (the original `say`+ffmpeg mono
chain is the disclosed gap this reseed fixes; audio duration/format lessons
in CLAUDE.md make ">=20s stereo" necessary but NOT sufficient, so every
render here still needs the post-ingest TRANSCRIPT-paragraph count check).

Python only (hard rule 1 - this bespoke Next.js app is not the
arag-demo-factory template, so no npm/npx exception applies); ffmpeg via
brew, requests already in .venv.

Usage: .venv/bin/python apps/call-analysis/scripts_py/render_media.py --out <dir>
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from scenarios import SCENARIOS  # noqa: E402
from voice_cast import ELEVEN_MODEL, voice_for_turn  # noqa: E402

ELEVEN_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
SAMPLE_RATE = 44100
GAP_SEC = 0.4
LOUDNORM_TARGET = "loudnorm=I=-19:TP=-1.5:LRA=11:print_format=summary"


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, **kw)


def ffprobe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return round(float(out), 2)


def ffprobe_channels(path: Path) -> int:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=channels", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return int(out) if out else 0


def synthesize_line(api_key: str, voice_id: str, text: str, out_mp3: Path, retries: int = 3):
    body = {
        "text": text,
        "model_id": ELEVEN_MODEL,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True},
    }
    headers = {"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"}
    last_err = None
    for attempt in range(retries):
        try:
            r = requests.post(ELEVEN_TTS_URL.format(voice_id=voice_id), json=body, headers=headers, timeout=60)
            if r.status_code == 200 and r.content:
                out_mp3.write_bytes(r.content)
                return
            last_err = f"HTTP {r.status_code}: {r.text[:300]}"
        except requests.RequestException as e:
            last_err = str(e)
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"TTS failed for voice {voice_id} after {retries} attempts: {last_err}")


def render_line_normalized(api_key: str, voice_id: str, text: str, work: Path, idx: int) -> Path:
    """Synthesize one line, then loudness-normalize + resample to stereo WAV."""
    raw_mp3 = work / f"line_{idx:02d}_raw.mp3"
    norm_wav = work / f"line_{idx:02d}_norm.wav"
    synthesize_line(api_key, voice_id, text, raw_mp3)
    run([
        "ffmpeg", "-y", "-i", str(raw_mp3),
        "-af", LOUDNORM_TARGET,
        "-ar", str(SAMPLE_RATE), "-ac", "2", "-c:a", "pcm_s16le",
        str(norm_wav),
    ])
    return norm_wav


def build_silence(work: Path) -> Path:
    silence = work / "silence.wav"
    run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r={SAMPLE_RATE}:cl=stereo",
        "-t", str(GAP_SEC), "-c:a", "pcm_s16le", str(silence),
    ])
    return silence


def concat_wavs(parts: list[Path], work: Path, out_name: str) -> Path:
    list_file = work / "concat_list.txt"
    list_file.write_text("\n".join(f"file '{p.resolve()}'" for p in parts))
    combined = work / out_name
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(combined)])
    return combined


def render_scenario(api_key: str, scenario: dict, out_dir: Path, work_root: Path) -> dict:
    slug = scenario["slug"]
    fmt = scenario["format"]
    work = work_root / f".work_{slug}"
    work.mkdir(parents=True, exist_ok=True)

    parts = []
    silence = build_silence(work)
    for i, (speaker, text) in enumerate(scenario["turns"]):
        voice_id = voice_for_turn(scenario["agentName"], scenario["memberId"], speaker)
        line_wav = render_line_normalized(api_key, voice_id, text, work, i)
        parts.append(line_wav)
        if i < len(scenario["turns"]) - 1:
            parts.append(silence)

    combined_wav = concat_wavs(parts, work, "combined_stereo.wav")
    duration = ffprobe_duration(combined_wav)
    channels = ffprobe_channels(combined_wav)

    result = {"slug": slug, "duration": duration, "channels": channels}

    if fmt == "mp3":
        out_path = out_dir / f"{slug}.mp3"
        run(["ffmpeg", "-y", "-i", str(combined_wav), "-codec:a", "libmp3lame", "-q:a", "2", "-ac", "2", str(out_path)])
        result["path"] = str(out_path)
    elif fmt == "mp4":
        out_path = out_dir / f"{slug}.mp4"
        wave = "showwaves=s=1280x720:mode=cline:rate=25:colors=0x38bdf8|0x6366f1"
        filt = f"[0:a]{wave}[w];color=c=0x0b1220:s=1280x720:r=25[bg];[bg][w]overlay=0:0[v]"
        run([
            "ffmpeg", "-y", "-i", str(combined_wav),
            "-filter_complex", filt,
            "-map", "[v]", "-map", "0:a",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-shortest", str(out_path),
        ])
        result["path"] = str(out_path)
    else:
        result["path"] = None  # transcript-only, no media to render

    import shutil
    shutil.rmtree(work, ignore_errors=True)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="Output directory for rendered media")
    ap.add_argument("--only", nargs="*", default=None, help="Optional: only render these slugs (retry mode)")
    args = ap.parse_args()

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        # fall back to reading factory root .env directly
        root_env = Path(__file__).resolve().parents[2] / ".env"
        for line in root_env.read_text().splitlines():
            if line.startswith("ELEVENLABS_API_KEY="):
                api_key = line.split("=", 1)[1].split("#")[0].strip()
                break
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not found", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    work_root = out_dir / "_work"
    work_root.mkdir(exist_ok=True)

    media_scenarios = [s for s in SCENARIOS if s["format"] in ("mp3", "mp4")]
    if args.only:
        media_scenarios = [s for s in media_scenarios if s["slug"] in args.only]

    results = []
    for i, sc in enumerate(media_scenarios, 1):
        print(f"[{i}/{len(media_scenarios)}] rendering {sc['slug']} ({sc['format']}) ...")
        r = render_scenario(api_key, sc, out_dir, work_root)
        status = "OK" if r["duration"] >= 20 and r["channels"] == 2 else "CHECK"
        print(f"  -> {status} duration={r['duration']}s channels={r['channels']}")
        results.append(r)

    import shutil
    shutil.rmtree(work_root, ignore_errors=True)

    print("\n=== SUMMARY ===")
    bad = [r for r in results if r["duration"] < 20 or r["channels"] != 2]
    for r in results:
        print(f"{r['slug']:45s} dur={r['duration']:6.1f}s ch={r['channels']}")
    if bad:
        print(f"\n{len(bad)} FILE(S) FAILED THE >=20s/stereo FLOOR:")
        for r in bad:
            print(" -", r["slug"], r["duration"], r["channels"])
        sys.exit(2)
    print(f"\nAll {len(results)} media files rendered, all >=20s and stereo.")


if __name__ == "__main__":
    main()
