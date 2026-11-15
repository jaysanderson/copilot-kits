"""Record a scripted demo walkthrough to video (Playwright, 1920x1080).

Drives a demo URL through a list of steps with deliberate pacing so a voiceover
fits over the top. Without a --steps file it does a slow scan: load, pause, scroll
down, scroll back, hold. Records webm; transcodes to mp4 if ffmpeg is on PATH.

Steps JSON is a list of actions:
    [{"action": "goto",   "url": "https://...", "wait": 2500},
     {"action": "click",  "selector": "button.ask", "wait": 2000},
     {"action": "type",   "selector": "input", "text": "How do I ...?", "wait": 800,
      "delay": 55},  # omit `delay` to set the value instantly instead of typing it
     {"action": "press",  "key": "Enter", "wait": 4000},
     {"action": "waitfor","selector": ".answer", "timeout": 120000, "wait": 500},
     {"action": "hover",  "selector": ".ge-chip", "wait": 900},
     {"action": "scroll", "y": 700, "wait": 1200},
     {"action": "evaluate", "expr": "() => document.title", "wait": 200},
     {"action": "wait",   "ms": 2000}]

Cold first-paint gotcha (found the hard way): a headless Chromium's very first
navigation to a JS-heavy app can sit on a blank white canvas for several real
seconds before anything paints - load_state fires long before pixels show up,
so that blank stretch gets recorded verbatim and shows up as a white-screen
defect right after the video opens. --warmup does a throwaway, unrecorded
navigation to the same URL in a separate page first (same browser context, so
network/JS caches and cookies carry over), then closes it and starts the real
recorded page - which now paints almost immediately. Always use --warmup for
the first goto of a fresh recording; skip it only for quick scratch tests.

Usage:
    python scripts/record_demo.py --url https://demo.example.com --seconds 20 \
        --out videos/demo.mp4 --warmup
    python scripts/record_demo.py --url https://demo.example.com \
        --steps content/walkthrough.json --out videos/demo.mp4 --auth brand/arag-auth.json \
        --warmup
"""
import argparse
import pathlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

W, H = 1920, 1080

# Playwright's recorder captures page pixels only - it draws no pointer at all,
# so recorded walkthroughs show UI reacting with nothing visibly driving it.
# There is nothing in the footage to track afterwards, so the cursor has to be
# real DOM that renders INTO the capture. pointer-events:none keeps it inert.
CURSOR_JS = r"""
(() => {
  const install = () => {
    if (!document.body || document.getElementById('__pmk_cursor')) return;
    const css = document.createElement('style');
    css.textContent = `
      #__pmk_cursor{position:fixed;left:0;top:0;width:26px;height:26px;
        z-index:2147483647;pointer-events:none;will-change:transform;
        transform:translate(-200px,-200px);
        transition:transform .18s cubic-bezier(.22,.61,.36,1)}
      #__pmk_cursor svg{filter:drop-shadow(0 2px 3px rgba(0,0,0,.45))}
      .__pmk_ripple{position:fixed;z-index:2147483646;pointer-events:none;
        width:16px;height:16px;margin:-8px 0 0 -8px;border-radius:50%;
        background:rgba(43,43,178,.40);border:2px solid rgba(43,43,178,.95);
        animation:__pmk_pop .55s ease-out forwards}
      @keyframes __pmk_pop{to{transform:scale(4.5);opacity:0}}
    `;
    document.head.appendChild(css);
    const c = document.createElement('div');
    c.id = '__pmk_cursor';
    c.innerHTML = '<svg width="26" height="26" viewBox="0 0 26 26">' +
      '<path d="M3 2l8.5 20 2.7-8.2 8.3-2.6z" fill="#fff" stroke="#111"' +
      ' stroke-width="1.6" stroke-linejoin="round"/></svg>';
    document.body.appendChild(c);
    addEventListener('mousemove', e => {
      c.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`;
    }, true);
    addEventListener('mousedown', e => {
      const r = document.createElement('div');
      r.className = '__pmk_ripple';
      r.style.left = e.clientX + 'px';
      r.style.top = e.clientY + 'px';
      document.body.appendChild(r);
      setTimeout(() => r.remove(), 600);
    }, true);
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', install);
  } else {
    install();
  }
})();
"""


def default_steps(url, seconds):
    """A calm scan when no scripted steps are given, paced to ~`seconds`."""
    hold = max(1000, int(seconds * 1000 / 5))
    return [
        {"action": "goto", "url": url, "wait": hold},
        {"action": "scroll", "y": 500, "wait": hold},
        {"action": "scroll", "y": 1000, "wait": hold},
        {"action": "scroll", "y": 0, "wait": hold},
        {"action": "wait", "ms": hold},
    ]


def run_step(page, step):
    action = step.get("action")
    if action == "goto":
        page.goto(step["url"], wait_until="load", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass  # SPAs may never idle
    elif action == "click":
        selector = step["selector"]
        # Glide the pointer to the target before clicking - `steps` emits real
        # intermediate mousemove events, so the overlay cursor travels on camera
        # instead of teleporting.
        try:
            box = page.wait_for_selector(selector, timeout=15000).bounding_box()
            if box:
                page.mouse.move(box["x"] + box["width"] / 2,
                                box["y"] + box["height"] / 2, steps=20)
                page.wait_for_timeout(240)
        except Exception:
            pass  # not fatal - fall through to the plain click
        # SVG/canvas targets (graph nodes, chart marks) often fail Playwright's
        # actionability check because a label or hit-area sits over them, so a
        # step can silently record a click that never landed. "force": true skips
        # the check - the pointer has already been moved onto the target above,
        # so the click is still visually honest.
        page.click(selector, timeout=15000, force=bool(step.get("force")))
    elif action == "waitfor":
        # Block until a selector exists before running the NEXT step. Without this
        # a scroll can fire while a live answer is still in flight: the page has
        # not grown yet, window.scrollTo() silently CLAMPS to the current maximum
        # (often 0), and the take records a beat that never scrolls - with every
        # hero region measured against the scrolled position now wrong. Found on
        # the OpenEdge climax beat, where a reconcile call ran 24s against a 14s
        # probe. Always gate a post-answer scroll on the answer's own selector
        # rather than on a fixed wait.
        page.wait_for_selector(step["selector"], timeout=step.get("timeout", 120000))
    elif action == "hover":
        # Glide the pointer onto a target without clicking, so a real CSS :hover
        # state fires on camera. Needed when the intended beat is "the suggested
        # chips highlight" but clicking one would fire an unwanted query.
        selector = step["selector"]
        try:
            box = page.wait_for_selector(selector, timeout=15000).bounding_box()
            if box:
                page.mouse.move(box["x"] + box["width"] / 2,
                                box["y"] + box["height"] / 2, steps=25)
        except Exception:
            pass  # a missed hover is cosmetic, never fatal to the take
    elif action == "type":
        # A plain fill() drops the whole query in as one frame, so the viewer never
        # sees the question being asked - the single most persuasive second in a
        # search demo. With "delay" the keystrokes land on camera instead.
        delay = step.get("delay")
        if delay:
            field = page.wait_for_selector(step["selector"], timeout=15000)
            box = field.bounding_box()
            if box:
                page.mouse.move(box["x"] + box["width"] / 2,
                                box["y"] + box["height"] / 2, steps=20)
                page.wait_for_timeout(200)
            field.click()
            field.fill("")
            page.keyboard.type(step["text"], delay=delay)
        else:
            page.fill(step["selector"], step["text"], timeout=15000)
    elif action == "press":
        page.keyboard.press(step["key"])
    elif action == "scroll":
        page.evaluate("y => window.scrollTo({top: y, behavior: 'smooth'})", step["y"])
    elif action == "evaluate":
        page.evaluate(step["expr"])  # arbitrary JS, e.g. neutralising a residency string
    elif action == "wait":
        pass  # the trailing wait below handles it
    else:
        print(f"unknown action '{action}', skipping", file=sys.stderr)
    page.wait_for_timeout(step.get("wait", step.get("ms", 1000)))



def apply_session_storage(context, path):
    """Seed sessionStorage before any page script runs.

    `storage_state` persists cookies and localStorage ONLY - Playwright has no
    sessionStorage equivalent. An SPA that keeps its auth token in sessionStorage
    is therefore uncapturable with --auth alone: the state file restores, the app
    finds no token and bounces to its login screen, and you get a folder of
    login-form screenshots that each look like a real page until someone reads
    them. Found on the Harbourline DMS, whose token lives in `dms.token`.

    The file is {"origin": "https://host", "items": {...}} as written by a film's
    own auth step. add_init_script runs before the app boots on EVERY navigation,
    which is what makes this survive the client-side routing an SPA does after
    the first load.
    """
    import json as _json
    blob = _json.loads(pathlib.Path(path).read_text())
    items = blob.get("items", blob)
    context.add_init_script(
        "(() => { const i = " + _json.dumps(items) + ";"
        " try { for (const k in i) sessionStorage.setItem(k, i[k]); } catch (e) {} })()")
    return len(items)


def main():
    parser = argparse.ArgumentParser(description="Record a scripted demo walkthrough")
    parser.add_argument("--url", required=True, help="Demo URL (start page)")
    parser.add_argument("--out", required=True, help="Output video path (.mp4 or .webm)")
    parser.add_argument("--steps", help="JSON file of walkthrough steps")
    parser.add_argument("--seconds", type=int, default=20,
                        help="Target length for the default scan (ignored with --steps)")
    parser.add_argument("--auth", help="Playwright storage_state JSON for auth")
    parser.add_argument("--session-storage",
                        help="JSON of sessionStorage items to seed before load "
                             "(storage_state cannot carry sessionStorage)")
    parser.add_argument("--warmup", action="store_true",
                        help="Throwaway unrecorded first navigation to avoid a "
                             "blank-canvas cold-paint delay in the real recording")
    parser.add_argument("--warmup-seconds", type=float, default=3.0,
                        help="Settle time for the warm-up navigation (default 3s)")
    parser.add_argument("--no-cursor", action="store_true",
                        help="Skip the on-camera cursor/click overlay")
    parser.add_argument("--prehide-css",
                        help="CSS injected via add_init_script so matching elements are "
                             "hidden from FIRST PAINT (e.g. a persistent footer with an "
                             "internal-mechanics string). Survives SPA hash navigation.")
    parser.add_argument("--prehide-text",
                        help="'||'-separated phrases; a persistent MutationObserver hides "
                             "any .card/.two/section panel whose text contains one of them, "
                             "as it renders (for LAZY-rendered panels a one-shot CSS/evaluate "
                             "can't catch, e.g. a production-brief or internal-metadata panel "
                             "that only mounts on scroll). Keeps leave-out UI out of frame.")
    parser.add_argument("--header-name",
                        help="Request header to add to SAME-ORIGIN requests matching "
                             "--header-routes (e.g. X-Insights-Source). Used to tag a "
                             "recording run's own API calls so the app can distinguish "
                             "them from real visitor traffic.")
    parser.add_argument("--header-from",
                        help="<envfile>:<KEY> - where to READ the header value from, file "
                             "to file. The value is NEVER accepted on the command line, "
                             "because an argv secret lands in shell history and in every "
                             "process listing on the box, and it is never printed or "
                             "logged. Requires --header-name.")
    parser.add_argument("--header-routes",
                        help="Regex matched against the request PATH. The header is added "
                             "only to requests whose origin equals --url's origin AND "
                             "whose path matches, so it can never reach a font CDN or any "
                             "other third party. Requires --header-name.")
    parser.add_argument("--autoframe", action="store_true",
                        help="Crop to the detected content region during transcode "
                             "(do not combine with assemble.py --autoframe)")
    args = parser.parse_args()

    steps = (json.loads(Path(args.steps).read_text())
             if args.steps else default_steps(args.url, args.seconds))
    # Ensure the first step opens the page even when a custom steps file omits it.
    if not steps or steps[0].get("action") != "goto":
        steps.insert(0, {"action": "goto", "url": args.url, "wait": 2000})

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    raw_dir = out_path.parent / "_rec_raw"
    raw_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": W, "height": H},
            record_video_dir=str(raw_dir),
            record_video_size={"width": W, "height": H},
            storage_state=args.auth if args.auth else None,
        )
        if args.session_storage:
            _n = apply_session_storage(context, args.session_storage)
            print(f"seeded {_n} sessionStorage item(s) from {args.session_storage}")
        if args.header_name:
            if not (args.header_from and args.header_routes):
                sys.exit("--header-name requires --header-from and --header-routes")
            _ef, _, _key = args.header_from.rpartition(":")
            if not _ef or not _key:
                sys.exit("--header-from must be <envfile>:<KEY>")
            _val = None
            for _line in Path(_ef).read_text().splitlines():
                if _line.startswith(_key + "="):
                    _val = _line.split("=", 1)[1].split("#")[0].strip().strip('"').strip("'")
            if not _val:
                sys.exit(f"{_key} not found in {_ef}")
            _origin = urlsplit(args.url)
            _origin = f"{_origin.scheme}://{_origin.netloc}"
            _pat = re.compile(args.header_routes)

            def _tag(route):
                # Same-origin AND path-matched. Either test alone is not enough: the
                # origin test alone would tag every asset request, and the path test
                # alone would send the value to a third party that happens to serve a
                # matching path.
                u = urlsplit(route.request.url)
                if f"{u.scheme}://{u.netloc}" == _origin and _pat.search(u.path):
                    route.continue_(headers={**route.request.headers,
                                             args.header_name: _val})
                else:
                    route.continue_()

            context.route("**/*", _tag)
            # Deliberately NOT printed with its value. Playwright HAR and tracing both
            # persist request headers to disk, so neither is ever enabled here; video
            # capture does not record headers and is unaffected.
            print(f"  tagging same-origin {args.header_routes} with {args.header_name} "
                  f"(value read from {_ef}, not shown)")
        if not args.no_cursor:
            context.add_init_script(CURSOR_JS)
        if args.prehide_css:
            # Inject a persistent <style> from first paint. A style tag on <head>
            # survives SPA hash-route changes (no full document reload), so one
            # injection hides the target for the whole recording - unlike an
            # `evaluate` step, which can flash the element for the first frames.
            css = json.dumps(args.prehide_css)
            context.add_init_script(
                "(()=>{const add=()=>{if(document.getElementById('__pmk_prehide'))return;"
                "const s=document.createElement('style');s.id='__pmk_prehide';"
                f"s.textContent={css};(document.head||document.documentElement)"
                ".appendChild(s);};if(document.readyState==='loading')"
                "document.addEventListener('DOMContentLoaded',add);else add();add();})()"
            )
        # Opt-in (RP_PREHIDE=1): hide raw-filename card sublines and stale "Processing"
        # badges from FIRST PAINT via an init script, so they never flash before an
        # in-steps observer can run. Harmless on pages without those elements.
        import os as _os
        if _os.environ.get("RP_PREHIDE"):
            context.add_init_script(
                "(()=>{const clean=()=>{try{document.querySelectorAll('p').forEach(e=>{"
                "const t=(e.textContent||'').trim();if(/\\.(pdf|docx)$/i.test(t))"
                "e.style.visibility='hidden';});document.querySelectorAll("
                "'span[class*=rp-badge-warn]').forEach(e=>{if(/^Processing$/i.test("
                "(e.textContent||'').trim()))e.style.visibility='hidden';});}catch(_){}}; "
                "const start=()=>{clean();new MutationObserver(clean).observe("
                "document.documentElement,{childList:true,subtree:true});}; "
                "if(document.readyState==='loading')document.addEventListener("
                "'DOMContentLoaded',start);else start();})()"
            )
        if args.prehide_text:
            phrases = json.dumps([s for s in args.prehide_text.split("||") if s])
            context.add_init_script(
                "(()=>{const P=" + phrases + ";"
                "const hide=()=>{try{document.querySelectorAll('.card,.two,section')"
                ".forEach(e=>{const t=e.textContent||'';"
                "if(P.some(p=>t.includes(p)))e.style.display='none';});}catch(_){}}; "
                "const start=()=>{hide();new MutationObserver(hide).observe("
                "document.documentElement,{childList:true,subtree:true});}; "
                "if(document.readyState==='loading')document.addEventListener("
                "'DOMContentLoaded',start);else start();})()"
            )
        if args.warmup:
            warmup_url = next((s["url"] for s in steps if s.get("action") == "goto"),
                               args.url)
            warm = context.new_page()
            warm.goto(warmup_url, wait_until="load", timeout=60000)
            warm.wait_for_timeout(int(args.warmup_seconds * 1000))
            warm.close()  # discards its own recorded video; only the real page's is kept
        page = context.new_page()
        for step in steps:
            run_step(page, step)
        video = page.video
        context.close()  # finalises every page's webm, including the warm-up page's
        webm = Path(video.path())
        browser.close()

    for stray in raw_dir.glob("*.webm"):  # the warm-up page's own recording, if any
        if stray.name != webm.name:  # compare names - webm may be absolute, stray relative
            stray.unlink(missing_ok=True)

    if out_path.suffix.lower() == ".mp4" and shutil.which("ffmpeg"):
        # Playwright's webm is already lossy VP8. Re-encoding at ffmpeg's default
        # CRF 23 stacked a second generation on top and measured ~390 kbps at
        # 1080p30, which visibly softens UI text. CRF 18 + slow costs bytes and
        # buys back legibility on the thing the video exists to show.
        vf = ["fps=30"]
        if args.autoframe:
            from autoframe import detect_crop
            crop = detect_crop(webm)
            print(f"  autoframe -> {crop or 'no crop needed'}")
            if crop:
                vf = [f"crop={crop}", f"scale={W}:{H}:flags=lanczos", "fps=30"]
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(webm), "-vf", ",".join(vf),
             "-c:v", "libx264", "-preset", "slow", "-crf", "18",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_path)],
            check=True, capture_output=True,
        )
        webm.unlink(missing_ok=True)
        print(f"Saved {out_path}")
    else:
        final = out_path.with_suffix(".webm")
        webm.replace(final)
        if out_path.suffix.lower() == ".mp4":
            print(f"ffmpeg not found; saved raw {final} (transcode later)")
        else:
            print(f"Saved {final}")
    try:
        raw_dir.rmdir()
    except OSError:
        pass  # leftover raw files; harmless


if __name__ == "__main__":
    main()
