#!/usr/bin/env python3
"""Run every pre-render check over a film project. One command, one verdict.

    .venv/bin/python scripts/filmkit/gate.py <project-dir> [-v]

WHAT THIS IS FOR. The cost of a film in this factory is not hours, it is
ROUNDS - render, gate, cold viewer, fix list, re-render. The research portal
walkthrough took seven of them to reach a viewer's YES. The Fin-demo showcase
carries a ten-item cold-viewer list and every one of those ten items was
reachable before a frame existed: hand-authored markers over a plate, a figure
on a capture contradicting the narration, a plate enlarged 1.27x, callout pills
over the text beneath, claims with no proof frame, evidence text below any
legibility floor. Finding those after a render costs a whole round. Finding them
here costs a minute, and the fix is free because nothing has been rendered yet.

WHAT IT IS NOT FOR. It cannot tell you whether a film is any good. Pacing, drift,
whether the idea lands, whether a room would keep watching - those need a
finished cut and a fresh pair of eyes, and that is exactly what a cold viewer
should be spent on. This gate exists so a viewer never spends a round on a crop.

CONTRACT FOR A CHECK MODULE. Anything in checks/ exposing `run(project_root,
**kw)` is discovered and run. Its return should carry `fails`, and may carry
`candidates`, `warns` and `holes`. A module that cannot be run is reported as a
HOLE BY NAME and never silently skipped: a gate assembled partly from checks
that could not fire is how 457 green checks once hid an unmeasured deploy-
critical path. Read the hole count before trusting the pass.

A DECLARED HOLE STATES THE CAUSE IT HAS EVIDENCE FOR. "unreachable by
configuration" and "unmeasurable in principle" are different findings, and a
hole with a plausible-sounding cause is worse than a bare one, because the
stated reason closes the question.
"""
from __future__ import annotations

import importlib
import pathlib
import pkgutil
import sys
import traceback

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

CHECKS_DIR = HERE.parent / "checks"


def discover() -> list[str]:
    if not CHECKS_DIR.is_dir():
        return []
    return sorted(
        m.name for m in pkgutil.iter_modules([str(CHECKS_DIR)])
        if not m.name.startswith("_")
    )


def _bucket(v, name: str) -> list[str]:
    got = getattr(v, name, None)
    return list(got) if isinstance(got, (list, tuple)) else []


def main(project: str, verbose: bool = False) -> int:
    # Line-buffer: a gate that prints nothing for two minutes looks hung, and a
    # producer who thinks it hung will stop running it.
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass
    project_path = pathlib.Path(project)
    if not project_path.is_dir():
        print(f"no such project directory: {project}")
        return 2

    names = discover()
    print(f"filmkit pre-render gate")
    print(f"project : {project_path.resolve()}")
    print(f"checks  : {len(names)} discovered - {', '.join(names) if names else 'NONE'}")
    print("=" * 78)
    if not names:
        print("\nno checks discovered - a gate over an empty population is not a pass")
        return 2

    fails: list[tuple[str, str]] = []
    cands: list[tuple[str, str]] = []
    warns: list[tuple[str, str]] = []
    holes: list[tuple[str, str]] = []
    ran = 0

    for n in names:
        print(f"\n--- {n} " + "-" * max(0, 70 - len(n)))
        try:
            mod = importlib.import_module(f"filmkit.checks.{n}")
        except Exception as e:
            holes.append((n, f"import failed: {e.__class__.__name__}: {e}"))
            print(f"  HOLE  import failed: {e.__class__.__name__}: {e}")
            if verbose:
                traceback.print_exc()
            continue
        fn = getattr(mod, "run", None)
        if not callable(fn):
            holes.append((n, "no run(project_root) entry point - nothing was measured"))
            print("  HOLE  no run(project_root) entry point - nothing was measured")
            continue
        try:
            try:
                v = fn(str(project_path), verbose=verbose)
            except TypeError:
                v = fn(str(project_path))
        except Exception as e:
            holes.append((n, f"raised {e.__class__.__name__}: {e}"))
            print(f"  HOLE  raised {e.__class__.__name__}: {e}")
            if verbose:
                traceback.print_exc()
            continue
        ran += 1
        if v is None:
            holes.append((n, "returned nothing - no verdict to read"))
            print("  HOLE  returned nothing - no verdict to read")
            continue
        for m in _bucket(v, "fails"):
            fails.append((n, m))
        for m in _bucket(v, "candidates"):
            cands.append((n, m))
        for m in _bucket(v, "warns"):
            warns.append((n, m))
        for m in _bucket(v, "holes"):
            holes.append((n, m))

    print("\n" + "=" * 78)
    print(f"{ran} of {len(names)} checks produced a verdict")
    print(f"{len(fails)} FAIL   {len(cands)} candidates   "
          f"{len(warns)} warn   {len(holes)} holes")

    if fails:
        print("\nFAIL - fix before rendering:")
        for n, m in fails:
            print(f"  [{n}] {m}")
    if cands:
        print("\nCANDIDATES - arithmetic cannot settle these; look at the frame:")
        for n, m in cands:
            print(f"  [{n}] {m}")
    if holes:
        print("\nHOLES - these were NOT measured. A pass above does not cover them:")
        for n, m in holes:
            print(f"  [{n}] {m}")
    if warns:
        print(f"\nwarnings ({len(warns)}):")
        for n, m in warns:
            print(f"  [{n}] {m}")

    print("\nThis gate reads the storyboard, the compositions and the captures. "
          "It does not\nread a rendered film, and it cannot judge whether the film "
          "is any good.")
    return 1 if fails else 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    sys.exit(main(args[0] if args else "fin-demo-showcase", verbose="-v" in sys.argv))
