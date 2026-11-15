#!/usr/bin/env python3
"""Two checks the regex sweeps cannot make.

(1) FIGURE SCOPE. Every on-screen or spoken figure is listed with whether it
    carries a scope token. Sweep for the CLAIM (a figure) and then test the hit
    for the qualifier - never sweep for the qualifier, which finds the ones that
    already qualify themselves and misses the one that does not. Unscoped hits
    are printed for a read; this does not auto-pass them.
(2) NARRATION INTEGRITY. The script is salvage-locked, so every line in
    audio_request.json must still be byte-identical to SCRIPT.md.
"""
import json, re, sys, pathlib

P = pathlib.Path(__file__).parent
FIG = re.compile(r"\d+(\.\d+)?\s*%|\bF1\b|\b\d+\.\d{2}\b|\b\d+(\.\d+)?\s*s\b|"
                 r"\b(ninety|eighty|seventy|sixty|fifty)[- ](two|three|four|five|six|seven|eight|nine)\b|"
                 r"\bseventy-five\b|\btwenty-eight\b")
SCOPE = re.compile(r"(?i)chatgpt|claude|gemini|azure|sonnet|flash|\bmodels?\b|sample pack|"
                   r"four pages|same scan|this scan|run|bake[- ]?off|page|applicant|batch|"
                   r"account|checkbox|measured|scoreboard|time")


def main():
    vt = json.loads((P / "visible_text.json").read_text())
    req = json.load(open(P / "audio_request.json"))
    rows = []
    for fn, d in vt.items():
        for t in d.get("texts", []):
            if FIG.search(t):
                rows.append((fn.replace(".html", ""), t))
    for l in req["lines"]:
        for sent in re.split(r"(?<=[.!?])\s+", l["text"]):
            if FIG.search(sent):
                rows.append((f"narration {l['id']}", sent))

    unscoped = [(w, t) for w, t in rows if not SCOPE.search(t)]
    print(f"(1) FIGURE SCOPE - {len(rows)} figure-bearing strings, "
          f"{len(rows)-len(unscoped)} carry a scope token\n")
    for w, t in rows:
        mark = "scoped  " if SCOPE.search(t) else "UNSCOPED"
        print(f"  {mark}  {w:22s} {t!r}")
    print("\n  Unscoped strings are bare values inside a table or a stat block whose\n"
          "  heading carries the scope; read them against their frame, do not auto-pass.")

    # (2) narration integrity against the locked script
    script = (P / "SCRIPT.md").read_text()
    bad = []
    for l in req["lines"]:
        if l["text"] not in script:
            bad.append(l["id"])
    print(f"\n(2) NARRATION INTEGRITY: {len(req['lines'])} lines, "
          f"{len(req['lines'])-len(bad)} byte-identical to SCRIPT.md")
    if bad:
        print(f"  *** lines differing from the locked script: {bad}")
    # control: a mutated line must be detected
    probe = req["lines"][0]["text"].replace("Fin-demo", "Umvuso")
    print(f"  CONTROL: a one-character mutation is "
          f"{'DETECTED' if probe not in script else 'NOT DETECTED - CHECK IS DECORATION'}")
    sys.exit(1 if bad or probe in script else 0)


if __name__ == "__main__":
    main()
