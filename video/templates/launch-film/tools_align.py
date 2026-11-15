#!/usr/bin/env python3
"""Phrase -> time lookup over the ElevenLabs character alignment.

Every beat time in every frame composition is DERIVED through this, from the
measured take, never hand-typed. `at("07", "the South African ID checksum")`
returns the time the phrase STARTS in take 07.

Blind class, stated: alignment is character-level over the NORMALIZED text the
model actually spoke, so a phrase whose spelling the normaliser changed will not
be found. find() RAISES on a miss rather than returning 0.0 - a silent 0.0 would
put a beat at the top of the scene and look deliberate.
"""
import json, pathlib, sys, unicodedata

AL = pathlib.Path(__file__).parent / "assets/voice-el"

def _norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    return "".join(c for c in s.lower() if c.isalnum() or c == "'")

class Take:
    def __init__(self, lid):
        self.lid = lid
        d = json.load(open(AL / f"{lid}.align.json"))
        self.chars = d["characters"]
        self.starts = d["character_start_times_seconds"]
        self.ends = d["character_end_times_seconds"]
        # map normalised-string index -> original char index
        self.flat = []
        self.idx = []
        for i, c in enumerate(self.chars):
            n = _norm(c)
            for _ in n:
                self.flat.append(n)
                self.idx.append(i)
        self.flat = "".join(self.flat)
    @property
    def duration(self):
        return self.ends[-1]
    def find(self, phrase, occurrence=1):
        p = _norm(phrase)
        if not p:
            raise ValueError("empty phrase")
        pos, seen = -1, 0
        while seen < occurrence:
            pos = self.flat.find(p, pos + 1)
            if pos < 0:
                raise LookupError(f"take {self.lid}: phrase {phrase!r} occurrence {occurrence} not found")
            seen += 1
        a = self.idx[pos]
        b = self.idx[min(pos + len(p) - 1, len(self.idx) - 1)]
        return self.starts[a], self.ends[b]

_cache = {}
def take(lid):
    if lid not in _cache:
        _cache[lid] = Take(lid)
    return _cache[lid]

def at(lid, phrase, occurrence=1):
    """Start time of `phrase` within take `lid`."""
    return round(take(lid).find(phrase, occurrence)[0], 3)

def after(lid, phrase, occurrence=1):
    """End time of `phrase` within take `lid`."""
    return round(take(lid).find(phrase, occurrence)[1], 3)

if __name__ == "__main__":
    lid = sys.argv[1]
    t = take(lid)
    print(f"take {lid}: duration {t.duration:.3f}s, {len(t.chars)} chars")
    for ph in sys.argv[2:]:
        s, e = t.find(ph)
        print(f"  {ph!r:46s} {s:7.3f} -> {e:7.3f}")
