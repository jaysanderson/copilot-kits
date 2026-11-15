#!/usr/bin/env python3
"""Sweep the AUTHORED text of the film: frame markup, JS string literals, narration.

Population is every string a viewer can READ - collected by seeking each frame's
timeline and unioning the rendered innerText (tools_visible_text.py) - plus the
narration. A line that only appears at t=9s is in scope; a CSS property name and
an em dash in a code comment are not.

Controls run every time: a planted specimen per rule (must FIRE) and a clean
specimen of real copy from this script (must stay QUIET). The possessive
apostrophe is matched in both the straight and typographic forms - builds here
convert one to the other and a straight-apostrophe pattern returns zero on a
rendered page.
"""
import json, re, sys, pathlib, html

P = pathlib.Path(__file__).parent

# ---- MACHINE BLOCK: (name, regex, must_not_appear) ----
RULES = [
    ("em dash",            r"—"),
    ("en dash as em",      r"\s–\s"),
    ("banned: delve",      r"(?i)\bdelv(e|es|ed|ing)\b"),
    ("banned: leverage",   r"(?i)\bleverag(e|es|ed|ing)\b"),
    ("banned: unlock",     r"(?i)\bunlock(s|ed|ing)?\b"),
    ("banned: seamless",   r"(?i)\bseamless(ly)?\b"),
    ("banned: game-changing", r"(?i)\bgame[- ]chang(ing|er)\b"),
    ("US spelling",        r"(?i)\b(organiz\w+|recogniz\w+|analyz\w+|optimiz\w+|summariz\w+|"
                           r"normaliz\w+|color|colors|center|centers|behavior|catalog|"
                           r"fulfill|enrollment|labeled|modeling|traveled)\b"),
    ("real person name",   r"(?i)\bjohan\b|\bdelport\b|\bkelly\b|o[''’]?donnell"),
    ("first person",       r"(?i)\b(I built|I made|your email|you asked|my demo)\b"),
    ("host/secret",        r"(?i)\.fly\.dev|fly\.io|nuclia|rag\.progress\.cloud|api[_ -]?key|admin[_ -]?token|aws-[a-z]+-[a-z]+-\d+-\d+"),
]
# ---- END MACHINE BLOCK ----

CLEAN = ("Step four. The pages regroup into one application by the ID number written on them. "
         "Here's what comes back. The schema, filled in. A confidence on every field. "
         "Anything under seventy percent goes on a review list. Progress Agentic RAG.")
PLANTED = {
    "em dash": "the model — and the schema",
    "en dash as em": "the model – and the schema",
    "banned: delve": "we delve into the pack",
    "banned: leverage": "leverage the schema",
    "banned: unlock": "unlock the value",
    "banned: seamless": "a seamless handover",
    "banned: game-changing": "a game-changing result",
    "US spelling": "the color of the organized catalog",
    "real person name": "sent to Johan Delport and Kelly O'Donnell",
    "first person": "I built this because you asked",
    "host/secret": "https://your-app.fly.dev with an api-key",
}



def visible_pairs():
    """Rendered text only. Source is the wrong population for a copy rule: the
    first version of this swept source and produced 42 findings, all of them CSS
    property names or em dashes inside code comments."""
    vt = json.loads((P / "visible_text.json").read_text())
    out = []
    for fname, d in vt.items():
        for t in d.get("texts", []):
            out.append((f"{fname} screen", t))
    return out


def scan(pairs):
    hits = []
    for where, text in pairs:
        for name, pat in RULES:
            for m in re.finditer(pat, text):
                hits.append((where, name, m.group(0), text[:90]))
    return hits


def main():
    pairs = visible_pairs()
    if not pairs:
        sys.exit("visible_text.json is empty - run tools_visible_text.py first")
    req = json.load(open(P / "audio_request.json"))
    for l in req["lines"]:
        pairs.append((f"narration {l['id']}", l["text"]))
    print(f"population: {len(pairs)} strings "
          f"({len(set(w.split()[0] for w, _ in pairs))} sources)")

    allfire = set()
    for n, _ in RULES:
        if any(h[1] == n for h in scan([("PLANT", PLANTED[n])])):
            allfire.add(n)
    quiet = scan([("CLEAN", CLEAN)])
    print(f"POSITIVE CONTROL: {len(allfire)}/{len(RULES)} rules fire on a planted specimen")
    miss = [n for n, _ in RULES if n not in allfire]
    if miss: print(f"  *** blind: {miss}")
    print(f"NEGATIVE CONTROL: {len(quiet)} hit(s) on real clean copy (expect 0)"
          + (f"  {[(h[1], h[2]) for h in quiet]}" if quiet else ""))

    hits = scan(pairs)
    print(f"\nFINDINGS: {len(hits)}")
    seen = set()
    for w, n, m, ctx in hits:
        k = (w, n, m)
        if k in seen: continue
        seen.add(k)
        print(f"  {w}: {n} -> {m!r}   in {ctx!r}")
    bad = bool(hits) or bool(quiet) or bool(miss)
    print("\nTEXT SWEEP", "FAIL" if bad else "PASS")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
