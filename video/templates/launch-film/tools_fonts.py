#!/usr/bin/env python3
"""Wire real Progress Sans into every frame.

HyperFrames rewrites system font names through a hardcoded alias map, so
`font-family: Arial` silently renders Inter from Google Fonts. The only way to
get the real typeface is a local @font-face under a family name the alias map
does not know (brand/fonts/README.md). Files are copied into assets/ so the
build does not reach outside the project.

Display vs Text is the canon's split (progress-hyperframes-brand.md s5): Display
for headlines and short titles, Text for body, UI, captions and labels, never
mixed inside one string. That is applied from the canon's own size scale -
subhead starts at 40px - so every rule resolving to >= 40px takes
Display and everything else inherits Text. Monospace rules are left alone.
"""
import pathlib, re, sys

FR = pathlib.Path(__file__).parent / "compositions/frames"

FACE = """
  /* Real Progress Sans - local files, family names outside the HyperFrames alias map */
  @font-face {
    font-family: "ProgressSansDisplay";
    src: url("assets/ProgressSansDisplayVF.woff2") format("woff2");
    font-weight: 100 900; font-style: normal; font-display: block;
  }
  @font-face {
    font-family: "ProgressSansText";
    src: url("assets/ProgressSansTextVF.woff2") format("woff2");
    font-weight: 100 900; font-style: normal; font-display: block;
  }
  :root, #root {
    --pg-display: "ProgressSansDisplay", Arial, Helvetica, sans-serif;
    --pg-text: "ProgressSansText", Arial, Helvetica, sans-serif;
  }
"""

SYS = 'system-ui, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif'
RULE = re.compile(r"(\n\s*)([^\n{}]+)\{([^{}]*)\}")


def main():
    files = sorted(FR.glob("*.html"))
    tot_face = tot_disp = tot_sys = 0
    for f in files:
        s = f.read_text()
        if "ProgressSansDisplay" in s:
            sys.exit(f"{f.name}: fonts already wired")
        # 1) the system stack becomes the Text face
        n = s.count(SYS)
        if n == 0:
            sys.exit(f"{f.name}: expected the system font stack at least once, found 0")
        s = s.replace(SYS, 'var(--pg-text)')
        tot_sys += n
        # 2) @font-face + tokens at the top of the first <style>
        i = s.index("<style")
        j = s.index(">", i) + 1
        s = s[:j] + FACE + s[j:]
        tot_face += 1
        # 3) Display on any rule whose own font-size clears the canon's subhead floor
        def add_display(m):
            lead, sel, body = m.groups()
            if "@font-face" in sel or "@keyframes" in sel or "monospace" in body:
                return m.group(0)
            fs = re.search(r"font-size:\s*([0-9.]+)(px|cqw)", body)
            if not fs or "font-family" in body:
                return m.group(0)
            # cqw is a share of the 1920px container; .f02-h2 and .f12-line are both
            # sized that way and a px-only threshold silently walked past them.
            px = float(fs.group(1)) * (19.2 if fs.group(2) == "cqw" else 1.0)
            if px < 40:
                return m.group(0)
            indent = re.search(r"\n(\s*)", "\n" + body.lstrip("\n")).group(1) or "    "
            return f"{lead}{sel}{{{body.rstrip()}\n{indent}font-family: var(--pg-display);\n{indent[:-2]}}}"
        s, k = RULE.subn(add_display, s)
        n_disp = s.count("var(--pg-display)")
        tot_disp += n_disp
        f.write_text(s)
        print(f"  {f.name:28s} text-stack {n:2d}  display rules {n_disp:2d}")
    print(f"\n@font-face blocks {tot_face}, system stacks replaced {tot_sys}, display rules {tot_disp}")
    if tot_disp == 0:
        sys.exit("no rule took the Display face - the size threshold found nothing, which cannot be right")


if __name__ == "__main__":
    main()
