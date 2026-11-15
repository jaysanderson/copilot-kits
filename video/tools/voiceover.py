"""Turn a script into a voiceover mp3 via ElevenLabs TTS.

Reads ELEVENLABS_API_KEY from .env (never from args). The voice is chosen from
brand/voices.json via --voice (default: hope). Uses `requests` only. Supports
ElevenLabs v3 inline audio tags in the script text (e.g. [warm], [pause]).

Usage:
    python scripts/voiceover.py --text "G'day, this is the GTM factory speaking." \
        --voice john --out videos/vo.mp3
    python scripts/voiceover.py --file content/script.txt --voice jay --out videos/vo.mp3
"""
import argparse
import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
VOICES = ROOT / "brand" / "voices.json"
API = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
API_TS = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"

# 192 kbps instead of the 128 kbps default: the voice is re-encoded to AAC during
# assembly, so the default cost us a second lossy generation for nothing.
OUTPUT_FORMAT = "mp3_44100_192"

# v3 stability is a three-preset system, not a free dial: 0.0 Creative (expressive
# but hallucination-prone), 0.5 Natural, 1.0 Robust (stable, ignores audio tags).
# Natural keeps directional tags working.
VOICE_SETTINGS = {"stability": 0.5, "similarity_boost": 0.75, "use_speaker_boost": True}

# MEASURED against the live API, 2026-08-07 - the endpoint docs do not flag any
# of this, and two of these were wrong in our own earlier write-up:
#
#   previous_text / next_text        -> HTTP 400 on eleven_v3, "not yet supported"
#   previous_request_ids / next_...  -> HTTP 400 on eleven_v3, "not yet supported"
#   seed                             -> accepted, but NOT reproducible on v3:
#                                       the same seed twice returned different
#                                       audio (identical byte length, different
#                                       content hash)
#   style / use_speaker_boost        -> accepted and audibly change the output
#   speed                            -> accepted but appears inert on v3
#                                       (byte-identical to baseline)
#   apply_text_normalization         -> accepted and changes output, despite the
#                                       model docs saying v3 has no normalisation
#
# So cross-segment prosody continuity is simply unavailable on v3 today. When a
# long narration genuinely needs it, run eleven_multilingual_v2 instead - it
# supports the continuity params and is documented as the most stable model for
# long-form - and accept losing v3's audio tags in exchange.
MODELS_WITHOUT_CONTINUITY = ("eleven_v3",)
DEFAULT_SEED = 20260807


def load_env(root):
    """Minimal .env reader - no extra dependency. Values already in the real
    environment win, so `.env` is a fallback, not an override."""
    env_path = root / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())


def resolve_voice(name):
    if not VOICES.exists():
        sys.exit(f"No voice registry at {VOICES}")
    registry = json.loads(VOICES.read_text())
    entry = registry.get(name)
    if not entry:
        known = [k for k in registry if not k.startswith("_") and k != "default"]
        sys.exit(f"Unknown voice '{name}'. Known: {', '.join(known)}")
    voice_id = entry.get("voice_id", "").strip()
    if not voice_id:
        sys.exit(
            f"Voice '{name}' has no voice_id yet in {VOICES}. "
            f"Populate it before running a voiceover."
        )
    return voice_id


def resolve_pool():
    """The Jay-approved rotation pool from voices.json, as voice_ids.

    voices.json has mandated alternating through this pool across multi-segment
    narration since 2026-07-06, but the pipeline resolved one voice and used it
    for every segment - which is what made long narrations feel monotone.
    """
    registry = json.loads(VOICES.read_text())
    names = registry.get("pool") or []
    ids = [(n, registry[n]["voice_id"]) for n in names
           if n in registry and registry[n].get("voice_id", "").strip()]
    return ids


def _payload(text, model, previous_text=None, next_text=None, seed=DEFAULT_SEED,
             speed=None):
    settings = dict(VOICE_SETTINGS)
    if speed is not None:
        if model.startswith("eleven_v3"):
            raise SystemExit(
                "speed is inert on eleven_v3 (measured: byte-identical to baseline). "
                "Use --model eleven_multilingual_v2, or drop --speed, rather than "
                "passing a parameter the model ignores.")
        settings["speed"] = speed
    body = {"text": text, "model_id": model, "voice_settings": settings}
    # Sending these to v3 is a hard 400, not a soft ignore, so they are gated on
    # the model rather than always included.
    if not model.startswith(MODELS_WITHOUT_CONTINUITY):
        if previous_text:
            body["previous_text"] = previous_text[-500:]
        if next_text:
            body["next_text"] = next_text[:500]
    if seed is not None:
        body["seed"] = int(seed)
    return body


def synth(text, voice_id, api_key, out, model="eleven_v3",
          previous_text=None, next_text=None, seed=DEFAULT_SEED, speed=None):
    """Text to an mp3 on disk. Shared by voiceover.py and narrate_deck.py."""
    resp = requests.post(
        API.format(voice_id=voice_id),
        headers={"xi-api-key": api_key, "accept": "audio/mpeg"},
        params={"output_format": OUTPUT_FORMAT},
        json=_payload(text, model, previous_text, next_text, seed, speed),
        timeout=180,
    )
    if resp.status_code != 200:
        sys.exit(f"ElevenLabs error {resp.status_code}: {resp.text[:400]}")
    Path(out).write_bytes(resp.content)


def synth_timed(text, voice_id, api_key, out, model="eleven_v3",
                previous_text=None, next_text=None, seed=DEFAULT_SEED, speed=None):
    """Same, but returns character-level alignment for caption timing.

    This is why captions need no speech-to-text: the TTS call itself reports
    exactly when each character is spoken.
    """
    resp = requests.post(
        API_TS.format(voice_id=voice_id),
        headers={"xi-api-key": api_key, "accept": "application/json"},
        params={"output_format": OUTPUT_FORMAT},
        json=_payload(text, model, previous_text, next_text, seed, speed),
        timeout=180,
    )
    if resp.status_code != 200:
        sys.exit(f"ElevenLabs error {resp.status_code}: {resp.text[:400]}")
    data = resp.json()
    import base64
    Path(out).write_bytes(base64.b64decode(data["audio_base64"]))
    return data.get("normalized_alignment") or data.get("alignment")


def main():
    parser = argparse.ArgumentParser(description="ElevenLabs TTS voiceover")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", help="Script text inline")
    src.add_argument("--file", help="Path to a script text file")
    parser.add_argument("--voice", default="hope", help="Voice name in brand/voices.json")
    parser.add_argument("--out", required=True, help="Output mp3 path")
    parser.add_argument("--model", default="eleven_v3", help="ElevenLabs model id")
    # Speed is INERT on eleven_v3 (measured, see the note above) and live on
    # eleven_multilingual_v2. Default None keeps every existing caller
    # byte-identical; pass it only with a model that honours it.
    parser.add_argument("--speed", type=float, default=None,
                        help="Delivery speed, v2 only (1.0 = normal, <1 slower)")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help="Pinned sampling seed for reproducible takes")
    args = parser.parse_args()

    load_env(ROOT)
    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        sys.exit("ELEVENLABS_API_KEY not set. Populate .env (see .env.example).")

    text = Path(args.file).read_text() if args.file else args.text
    voice_id = resolve_voice(args.voice)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    synth(text, voice_id, api_key, out_path, model=args.model, seed=args.seed,
          speed=args.speed)
    print(f"Saved {out_path} ({out_path.stat().st_size} bytes, voice={args.voice}, "
          f"format={OUTPUT_FORMAT}, seed={args.seed})")


if __name__ == "__main__":
    main()
