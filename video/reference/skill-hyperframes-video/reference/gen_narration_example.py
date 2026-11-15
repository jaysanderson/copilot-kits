#!/usr/bin/env python3
import os, sys, json, subprocess, pathlib

ENV = "/Users/user/Claude/ARAG-PMK-1/.env"
key = None
for line in open(ENV):
    if line.startswith("ELEVENLABS_API_KEY="):
        key = line.split("=", 1)[1].split("#", 1)[0].strip()
        break
if not key:
    print("NO KEY"); sys.exit(1)

VOICE = "WZlYpi1yf6zJhNWXih74"  # Hope
OUT = pathlib.Path("/Users/user/Claude/ARAG-PMK-1/videos/hyperframes_arag/build/assets")
OUT.mkdir(parents=True, exist_ok=True)

segments = {
    "s1": "Most AI hands you an answer and asks you to trust it.",
    "s2": "Progress Agentic RAG earns it. Ingestion agents enrich your content, and a retrieval agent plans multi step retrieval to reach the real answer.",
    "s3": "Every answer is grounded in your sources and cited. And REMi scores trust on every query. Answer relevance, context relevance, groundedness.",
    "s4": "Run it where your data must live. Cloud, hybrid, or on premise. Usage based, and self serve to start.",
    "s5": "Progress Agentic RAG. Retrieval you can trust.",
}

import urllib.request
durations = {}
for name, text in segments.items():
    body = json.dumps({
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.42, "similarity_boost": 0.8, "style": 0.0, "use_speaker_boost": True},
    }).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_44100_128",
        data=body, method="POST",
        headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
    )
    dest = OUT / f"vo_{name}.mp3"
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    dest.write_bytes(data)
    dur = subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(dest)]).decode().strip()
    durations[name] = float(dur)
    print(f"{name}: {len(data)} bytes, {dur}s -> {dest.name}")

print("DURATIONS_JSON=" + json.dumps(durations))
